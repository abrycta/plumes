// The /embed's precomputed pack: the chosen windows (states.ts), each reduced at build time to what the embed draws
// (density hexagons, thermal detections near a volcano, earthquakes, counts and caption figures), so krtmtthw.dev
// never makes the frame download whole yearly files. One small index plus one file per window, and a compact variant
// per window for phones (Luzon to the Visayas, decision P1, coarser coordinates). Alias-free: the build plugin
// (scripts/vite-embed-pack.ts) imports it in Node.

import type { Layers, VolcanoesIndex } from "@contracts/readmodels";

import { layerMonths } from "../data/layers";
import { depthClass, hexRing, WINDOW_MONTHS, windowMonths, type Activity, type MonthCount } from "../map/density";
import { loadAllQuakes } from "../map/points";
import { loadWindow, type MapGeojson, type WindowData } from "../map/windowData";
import { chooseStates, type EmbedState } from "./states";

export const PACK_DIR = "embed-pack";
/** Phones keep only this latitude band (Luzon to the Visayas) and two decimals (about 1 km). */
const COMPACT_SOUTH = 8.5;

export interface PackIndex {
  v: 1;
  dataVersion: string;
  /** Time order. */
  states: { end: string; file: string; compact: string; points: number; bytes: number; compactBytes: number }[];
}

export interface PackState {
  v: 1;
  state: EmbedState;
  totals: { thermal: number; near: number; quakes: number; maxMag: number };
  /** [month, thermal near, thermal far, quakes] */
  counts: [string, number, number, number][];
  /** [volcano id, thermal within 15 km, earthquakes within 30 km] */
  activity: [string, number, number][];
  /** [lon, lat, count] hexagon centres */
  hexes: [number, number, number][];
  /** [lon, lat] thermal detections near a volcano */
  near: [number, number][];
  /** [lon, lat, magnitude, depth class] */
  quakes: [number, number, number, number][];
}

/** What the embed shows for one window, whether from the pack or computed in the browser. */
export interface ShownWindow {
  state: EmbedState;
  geojson: MapGeojson;
  counts: MonthCount[];
  activity: Map<string, Activity>;
  totals: PackState["totals"];
  points: number;
}

const round = (v: number, d: number) => Math.round(v * 10 ** d) / 10 ** d;

export function packState(state: EmbedState, d: WindowData, compact: boolean): PackState {
  const dp = compact ? 2 : 3;
  const keep = (lat: number) => !compact || lat >= COMPACT_SOUTH;
  const near = d.thermal.filter((t) => t.near);
  return {
    v: 1,
    state,
    totals: { thermal: d.thermal.length, near: near.length, quakes: d.quakes.length, maxMag: d.quakes.reduce((m, q) => Math.max(m, q.mag ?? 0), 0) },
    counts: d.counts.map((c) => [c.month, c.thermalNear, c.thermalFar, c.quakes]),
    activity: [...d.activity].filter(([, a]) => a.thermal || a.quakes).map(([id, a]) => [id, a.thermal, a.quakes]),
    hexes: d.hexes.filter((h) => keep(h.center[1])).map((h) => [round(h.center[0], 4), round(h.center[1], 4), h.count]),
    near: [...new Set(near.filter((t) => keep(t.lat)).map((t) => `${round(t.lon, dp)},${round(t.lat, dp)}`))].map((k) => k.split(",").map(Number) as [number, number]),
    quakes: d.quakes.filter((q) => keep(q.lat)).map((q) => [round(q.lon, dp), round(q.lat, dp), round(q.mag ?? 3, 1), depthClass(q.depth)]),
  };
}

const pt = (lon: number, lat: number, properties: Record<string, number>): GeoJSON.Feature => ({ type: "Feature", geometry: { type: "Point", coordinates: [lon, lat] }, properties });

export function fromPack(p: PackState): ShownWindow {
  return {
    state: p.state,
    geojson: {
      hexes: { type: "FeatureCollection", features: p.hexes.map(([lon, lat, count]) => ({ type: "Feature", geometry: { type: "Polygon", coordinates: [hexRing([lon, lat])] }, properties: { count } })) },
      thermal: { type: "FeatureCollection", features: p.near.map(([lon, lat]) => pt(lon, lat, { near: 1, frp: 0 })) },
      quakes: { type: "FeatureCollection", features: [...p.quakes].sort((a, b) => a[2] - b[2]).map(([lon, lat, mag, depth]) => pt(lon, lat, { mag, depth })) },
    },
    counts: p.counts.map(([month, thermalNear, thermalFar, quakes]) => ({ month, thermalNear, thermalFar, quakes })),
    activity: new Map(p.activity.map(([id, thermal, quakes]) => [id, { thermal, quakes, maxMag: null }])),
    totals: p.totals,
    points: p.totals.thermal + p.totals.quakes,
  };
}

/** Builds the pack from a published data version (Node or browser): the index and its files. */
export async function buildPack(layers: Layers, versionBase: string, index: VolcanoesIndex, dataVersion: string, dataAsOf: string): Promise<{ index: PackIndex; files: Record<string, PackState> }> {
  const thermal = layers.layers.find((l) => l.id === "thermal-detections");
  const quakes = layers.layers.find((l) => l.id === "earthquakes-usgs");
  const record = [...new Set([...layerMonths(thermal), ...layerMonths(quakes)])].filter((m) => m <= dataAsOf.slice(0, 7)).sort();
  const all = quakes ? await loadAllQuakes(quakes, versionBase, record) : [];
  const files: Record<string, PackState> = {};
  const states: PackIndex["states"] = [];
  for (const s of chooseStates(index, record, all)) {
    const d = await loadWindow(layers, versionBase, index, windowMonths(s.end, WINDOW_MONTHS));
    const full = packState(s, d, false);
    const compact = packState(s, d, true);
    const file = `${s.end}.json`;
    const small = `${s.end}-compact.json`;
    files[file] = full;
    files[small] = compact;
    states.push({ end: s.end, file, compact: small, points: full.totals.thermal + full.totals.quakes, bytes: JSON.stringify(full).length, compactBytes: JSON.stringify(compact).length });
  }
  return { index: { v: 1, dataVersion, states }, files };
}
