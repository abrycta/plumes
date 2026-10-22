// The national point layers (thermal detections, earthquakes) as plain arrays, so the map page and the embed can
// count, bin and filter a whole time window in the browser instead of drawing one month of tiles.
// Published versions keep thermal detections as one PMTiles per year (tippecanoe thins the low zooms, so every point
// is read from the archive's highest zoom, the whole file in one request) and earthquakes as one PMTiles for the
// record (kept whole at every zoom, so its lowest zoom is read with a few range requests). The contract fixture has
// one GeoJSON per month. Nothing here touches the DOM; results are cached per file.

import { VectorTile } from "@mapbox/vector-tile";
import { PbfReader } from "pbf";
import { FetchSource, PMTiles, type RangeResponse, type Source } from "pmtiles";

import type { Layer } from "@contracts/readmodels";

import { resolveUrl } from "../data/load";
import { layerMonths, layerPath } from "../data/layers";

export interface ThermalPt {
  lon: number;
  lat: number;
  month: string;
  frp: number | null;
  /** FIRMS type: 0 vegetation fire, 1 active volcano, 2 other static source, 3 offshore. */
  type: number | null;
}

export interface QuakePt {
  lon: number;
  lat: number;
  month: string;
  mag: number | null;
  depth: number | null;
}

const PH = [116, 4, 128, 22] as const;

/** A PMTiles source over bytes already in memory (the whole yearly thermal file is one request). */
class BufferSource implements Source {
  constructor(
    private readonly key: string,
    private readonly buf: ArrayBuffer,
  ) {}
  getKey() {
    return this.key;
  }
  async getBytes(offset: number, length: number): Promise<RangeResponse> {
    return { data: this.buf.slice(offset, offset + length) };
  }
}

function tileRange(z: number): { x0: number; x1: number; y0: number; y1: number } {
  const x = (lon: number) => Math.floor(((lon + 180) / 360) * 2 ** z);
  const y = (lat: number) => {
    const r = (lat * Math.PI) / 180;
    return Math.floor(((1 - Math.log(Math.tan(r) + 1 / Math.cos(r)) / Math.PI) / 2) * 2 ** z);
  };
  return { x0: x(PH[0]), x1: x(PH[2]), y0: y(PH[3]), y1: y(PH[1]) };
}

/** Every feature of `layer` at zoom `z` over the Philippines, de-duplicated (tiles repeat points in their buffers). */
async function readPmtiles<T>(archive: PMTiles, layer: string, z: number, map: (lon: number, lat: number, p: Record<string, unknown>) => T, key: (t: T, p: Record<string, unknown>) => string): Promise<T[]> {
  const { x0, x1, y0, y1 } = tileRange(z);
  const seen = new Set<string>();
  const out: T[] = [];
  for (let x = x0; x <= x1; x++)
    for (let y = y0; y <= y1; y++) {
      const tile = await archive.getZxy(z, x, y);
      if (!tile) continue;
      const vl = new VectorTile(new PbfReader(new Uint8Array(tile.data))).layers[layer];
      if (!vl) continue;
      for (let i = 0; i < vl.length; i++) {
        const f = vl.feature(i);
        const g = f.toGeoJSON(x, y, z).geometry;
        if (g.type !== "Point") continue;
        const [lon, lat] = g.coordinates as [number, number];
        const props = f.properties as Record<string, unknown>;
        const pt = map(lon, lat, props);
        const k = key(pt, props);
        if (seen.has(k)) continue;
        seen.add(k);
        out.push(pt);
      }
    }
  return out;
}

const num = (v: unknown): number | null => (typeof v === "number" && Number.isFinite(v) ? v : typeof v === "string" && v !== "" && Number.isFinite(Number(v)) ? Number(v) : null);
const monthOf = (p: Record<string, unknown>, fallback = ""): string => String(p.month ?? (typeof p.date === "string" ? p.date.slice(0, 7) : typeof p.time === "string" ? p.time.slice(0, 7) : fallback));

const toThermal = (month?: string) => (lon: number, lat: number, p: Record<string, unknown>): ThermalPt => ({ lon, lat, month: monthOf(p, month), frp: num(p.frp), type: num(p.type) });
const toQuake = (month?: string) => (lon: number, lat: number, p: Record<string, unknown>): QuakePt => ({ lon, lat, month: monthOf(p, month), mag: num(p.mag), depth: num(p.depth) });
const thermalKey = (t: ThermalPt, p: Record<string, unknown>) => `${t.lon.toFixed(4)},${t.lat.toFixed(4)},${String(p.date ?? t.month)},${String(p.sensor ?? "")}`;
const quakeKey = (q: QuakePt, p: Record<string, unknown>) => String(p.id ?? `${q.lon.toFixed(3)},${q.lat.toFixed(3)},${String(p.time ?? q.month)}`);

const cache = new Map<string, Promise<unknown[]>>();
function cached<T>(url: string, load: () => Promise<T[]>): Promise<T[]> {
  let p = cache.get(url) as Promise<T[]> | undefined;
  if (!p) {
    p = load().catch((e: unknown) => {
      cache.delete(url);
      throw e;
    });
    cache.set(url, p);
  }
  return p;
}

async function geojsonPoints<T>(url: string, map: (lon: number, lat: number, p: Record<string, unknown>) => T): Promise<T[]> {
  const res = await fetch(url);
  if (!res.ok) return [];
  const g = (await res.json()) as { features: { geometry: { coordinates: [number, number] }; properties: Record<string, unknown> }[] };
  return g.features.map((f) => map(f.geometry.coordinates[0], f.geometry.coordinates[1], f.properties ?? {}));
}

/** The files of `layer` that hold `months` (one per year, one per month, or one for the record). */
export function filesFor(layer: Layer, months: readonly string[]): { path: string; month?: string }[] {
  const offered = new Set(layerMonths(layer));
  const wanted = months.filter((m) => offered.has(m));
  if (layer.url.includes("{month}")) return wanted.map((m) => ({ path: layerPath(layer, m), month: m }));
  return [...new Set(wanted.map((m) => layerPath(layer, m)))].map((path) => ({ path }));
}

/** Thermal detections of `layer` in `months` (any order), from every file that holds them. */
export async function loadThermal(layer: Layer, versionBase: string, months: readonly string[]): Promise<ThermalPt[]> {
  const want = new Set(months);
  const parts = await Promise.all(
    filesFor(layer, months).map(({ path, month }) => {
      const url = resolveUrl(versionBase, path);
      return cached(url, async () => {
        if (layer.format !== "pmtiles") return geojsonPoints(url, toThermal(month));
        const res = await fetch(url);
        if (!res.ok) return [];
        const archive = new PMTiles(new BufferSource(url, await res.arrayBuffer()));
        const header = await archive.getHeader();
        return readPmtiles(archive, layer.sourceLayer ?? "thermal", header.maxZoom, toThermal(), thermalKey);
      });
    }),
  );
  return parts.flat().filter((p) => want.has(p.month));
}

/** Earthquakes of `layer` in `months`. */
export async function loadQuakes(layer: Layer, versionBase: string, months: readonly string[]): Promise<QuakePt[]> {
  const all = await loadAllQuakes(layer, versionBase, months);
  const want = new Set(months);
  return all.filter((q) => want.has(q.month));
}

/** Every earthquake the files for `months` hold (for the whole-record layer: the whole record, for the timeline). */
export async function loadAllQuakes(layer: Layer, versionBase: string, months: readonly string[]): Promise<QuakePt[]> {
  const parts = await Promise.all(
    filesFor(layer, months).map(({ path, month }) => {
      const url = resolveUrl(versionBase, path);
      return cached(url, async () => {
        if (layer.format !== "pmtiles") return geojsonPoints(url, toQuake(month));
        const archive = new PMTiles(new FetchSource(url));
        const header = await archive.getHeader();
        return readPmtiles(archive, layer.sourceLayer ?? "earthquakes", header.minZoom, toQuake(), quakeKey);
      });
    }),
  );
  return parts.flat();
}

/** The zoom range of one PMTiles file of `layer` (build time: the map's first-window pack, map/firstWindow.ts). */
export async function pmtilesZooms(versionBase: string, path: string): Promise<{ min: number; max: number }> {
  const header = await new PMTiles(new FetchSource(resolveUrl(versionBase, path))).getHeader();
  return { min: header.minZoom, max: header.maxZoom };
}
