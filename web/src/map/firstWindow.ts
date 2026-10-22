// The map page's first window, precomputed at build time (scripts/vite-map-pack.ts) like the embed's pack: the points
// of the default twelve months and the record's earthquakes per month (the timeline strip), in one small file. The
// first view then needs neither the two yearly thermal files (about 1.5 MB, of which most months are outside the
// window) nor the whole-record earthquake file. Moving the window loads the published layers as before.
// The points are exactly the ones the browser would decode from the published PMTiles: each is stored as its integer
// tile coordinate (zoom, extent, global x and y), from which the same formula as @mapbox/vector-tile's toGeoJSON gives
// back the same numbers bit for bit; the build checks every point and skips the pack if one differs.
// The pack is used only when it was built from the data version the page reads (`stamp`), else nothing changes.
// Alias-free: the build plugin imports it in Node.

import type { Latest, Layer, Layers } from "@contracts/readmodels";

import { quakesPerMonth } from "./density";
import { filesFor, loadAllQuakes, loadQuakes, loadThermal, pmtilesZooms, type QuakePt, type ThermalPt } from "./points";
import { defaultWindowMonths, recordMonths } from "./windowData";

export const MAP_PACK_PATH = "map-pack/first.json";

/** Points of one source file at one zoom: delta-encoded global tile coordinates and two attributes. */
interface Cols {
  z: number;
  extent: number;
  /** Global x (tile x × extent + x in tile), delta-encoded. */
  x: number[];
  y: number[];
  /** Index into `months`. */
  m: number[];
  /** Thermal: FRP; earthquakes: magnitude. */
  a: (number | null)[];
  /** Thermal: FIRMS type; earthquakes: depth. */
  b: (number | null)[];
}

export interface FirstWindowPack {
  v: 1;
  stamp: string;
  months: string[];
  record: string[];
  recordQuakes: number[];
  thermal: Cols[];
  quakes: Cols[];
}

/** Which published data a pack was built from: the version and the moment it was generated. */
export function dataStamp(latest: Pick<Latest, "current" | "generatedAt">): string {
  return `${latest.current}|${latest.generatedAt}`;
}

// The projection of @mapbox/vector-tile's VectorTileFeature.toGeoJSON, on the global coordinate.
const lonOf = (gx: number, size: number) => (gx * 360) / size - 180;
const latOf = (gy: number, size: number) => (360 / Math.PI) * Math.atan(Math.exp((1 - (gy * 2) / size) * Math.PI)) - 90;
const gxOf = (lon: number, size: number) => Math.round(((lon + 180) * size) / 360);
const gyOf = (lat: number, size: number) => Math.round(((1 - Math.log(Math.tan(((lat + 90) * Math.PI) / 360)) / Math.PI) * size) / 2);

const EXTENTS = [4096, 8192, 512, 1024, 2048, 16384];

/** Encodes points read at zoom `z`, or null when no tile extent reproduces every point exactly. */
function encode<T extends { lon: number; lat: number; month: string }>(pts: readonly T[], z: number, months: readonly string[], a: (p: T) => number | null, b: (p: T) => number | null): Cols | null {
  const mi = new Map(months.map((m, i) => [m, i]));
  for (const extent of EXTENTS) {
    const size = extent * 2 ** z;
    const gx = pts.map((p) => gxOf(p.lon, size));
    const gy = pts.map((p) => gyOf(p.lat, size));
    if (!pts.every((p, i) => lonOf(gx[i]!, size) === p.lon && latOf(gy[i]!, size) === p.lat)) continue;
    const delta = (v: number[]) => v.map((n, i) => (i ? n - v[i - 1]! : n));
    return { z, extent, x: delta(gx), y: delta(gy), m: pts.map((p) => mi.get(p.month) ?? -1), a: pts.map(a), b: pts.map(b) };
  }
  return null;
}

function decode<T>(c: Cols, months: readonly string[], make: (lon: number, lat: number, month: string, a: number | null, b: number | null) => T): T[] {
  const size = c.extent * 2 ** c.z;
  const out: T[] = [];
  let gx = 0;
  let gy = 0;
  for (let i = 0; i < c.x.length; i++) {
    gx += c.x[i]!;
    gy += c.y[i]!;
    out.push(make(lonOf(gx, size), latOf(gy, size), months[c.m[i]!] ?? "", c.a[i] ?? null, c.b[i] ?? null));
  }
  return out;
}

export function packThermal(p: FirstWindowPack): ThermalPt[] {
  return p.thermal.flatMap((c) => decode(c, p.months, (lon, lat, month, frp, type) => ({ lon, lat, month, frp, type })));
}

export function packQuakes(p: FirstWindowPack): QuakePt[] {
  return p.quakes.flatMap((c) => decode(c, p.months, (lon, lat, month, mag, depth) => ({ lon, lat, month, mag, depth })));
}

/** Builds the pack from a published data version (Node). Null when the layers are not PMTiles or a point differs. */
export async function buildFirstWindow(layers: Layers, versionBase: string, latest: Latest): Promise<FirstWindowPack | null> {
  const thermal = layers.layers.find((l) => l.id === "thermal-detections");
  const quakes = layers.layers.find((l) => l.id === "earthquakes-usgs");
  if (!thermal || !quakes || thermal.format !== "pmtiles" || quakes.format !== "pmtiles") return null;
  const record = recordMonths(layers, latest.dataAsOf);
  const months = defaultWindowMonths(record);
  // Per file, in the order loadThermal reads them, so the concatenation is the browser's list in the browser's order.
  const parts = async <T extends { lon: number; lat: number; month: string }>(layer: Layer, zoom: "max" | "min", load: (ms: string[]) => Promise<T[]>, a: (p: T) => number | null, b: (p: T) => number | null) => {
    const out: Cols[] = [];
    for (const { path } of filesFor(layer, months)) {
      const own = months.filter((m) => filesFor(layer, [m]).some((f) => f.path === path));
      const z = (await pmtilesZooms(versionBase, path))[zoom];
      const cols = encode(await load(own), z, months, a, b);
      if (!cols) return null;
      out.push(cols);
    }
    return out;
  };
  const t = await parts(thermal, "max", (ms) => loadThermal(thermal, versionBase, ms), (p) => p.frp, (p) => p.type);
  const q = await parts(quakes, "min", (ms) => loadQuakes(quakes, versionBase, ms), (p) => p.mag, (p) => p.depth);
  if (!t || !q) return null;
  const pack: FirstWindowPack = { v: 1, stamp: dataStamp(latest), months, record, recordQuakes: quakesPerMonth(record, await loadAllQuakes(quakes, versionBase, record)), thermal: t, quakes: q };
  // The browser's own lists, compared point by point with what the pack gives back.
  const [wantT, wantQ] = await Promise.all([loadThermal(thermal, versionBase, months), loadQuakes(quakes, versionBase, months)]);
  const same = <T>(x: T[], y: T[]) => x.length === y.length && JSON.stringify(x) === JSON.stringify(y);
  return same(packThermal(pack), wantT) && same(packQuakes(pack), wantQ) ? pack : null;
}

let packP: Promise<FirstWindowPack | null> | null = null;

/** The deployed pack (cached), or null without one (offline builds, `vite dev`). */
export function loadFirstWindowPack(): Promise<FirstWindowPack | null> {
  packP ??= fetch(`/${MAP_PACK_PATH}`)
    .then((r) => (r.ok && (r.headers.get("content-type") ?? "").includes("json") ? (r.json() as Promise<FirstWindowPack>) : null))
    .catch(() => null);
  return packP;
}

/** The pack when it was built from this data version and holds exactly `months` (or the record, for the strip). */
export async function firstWindowFor(stamp: string, months: readonly string[], field: "months" | "record" = "months"): Promise<FirstWindowPack | null> {
  const p = await loadFirstWindowPack();
  return p?.v === 1 && p.stamp === stamp && p[field].join(",") === months.join(",") ? p : null;
}
