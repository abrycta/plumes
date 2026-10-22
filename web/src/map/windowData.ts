// One time window of the national layers, loaded and derived once: points tagged near/far, hexagonal density,
// per-volcano activity, per-month counts, and the GeoJSON the interactive map draws.

import { useEffect, useState } from "react";

import type { Layers, VolcanoesIndex } from "@contracts/readmodels";

import { layerMonths } from "../data/layers";
import { activityByVolcano, depthClass, hexbin, monthlyCounts, NEAR_KM, nearestKm, quakesPerMonth, WINDOW_MONTHS, windowMonths, type Activity, type Hex, type LayerCoverage, type MonthCount, type VolcanoPt } from "./density";
import { firstWindowFor, packQuakes, packThermal } from "./firstWindow";
import { loadAllQuakes, loadQuakes, loadThermal, type QuakePt, type ThermalPt } from "./points";

export type TaggedThermal = ThermalPt & { near: boolean };

export interface WindowData {
  months: string[];
  thermal: TaggedThermal[];
  quakes: QuakePt[];
  hexes: Hex[];
  counts: MonthCount[];
  activity: Map<string, Activity>;
}

export interface MapGeojson {
  hexes: GeoJSON.FeatureCollection;
  thermal: GeoJSON.FeatureCollection;
  quakes: GeoJSON.FeatureCollection;
}

export function volcanoPoints(index: VolcanoesIndex): VolcanoPt[] {
  return index.features.map((f) => ({ id: f.properties.id, lon: f.geometry.coordinates[0], lat: f.geometry.coordinates[1] }));
}

/** The months the thermal and earthquake layers cover (their `time` in layers.json). */
export function layerCoverage(layers: Layers): LayerCoverage {
  const months = (id: string) => {
    const m = layerMonths(layers.layers.find((l) => l.id === id));
    return m.length ? new Set(m) : null;
  };
  return { thermal: months("thermal-detections"), quakes: months("earthquakes-usgs") };
}

export async function loadWindow(layers: Layers, versionBase: string, index: VolcanoesIndex, months: string[]): Promise<WindowData> {
  const thermalLayer = layers.layers.find((l) => l.id === "thermal-detections");
  const quakeLayer = layers.layers.find((l) => l.id === "earthquakes-usgs");
  const [rawThermal, quakes] = await Promise.all([
    thermalLayer ? loadThermal(thermalLayer, versionBase, months).catch(() => []) : [],
    quakeLayer ? loadQuakes(quakeLayer, versionBase, months).catch(() => []) : [],
  ]);
  return deriveWindow(index, months, rawThermal, quakes, layerCoverage(layers));
}

/** Everything the map shows for a window, from its points. */
export function deriveWindow(index: VolcanoesIndex, months: string[], rawThermal: readonly ThermalPt[], quakes: QuakePt[], coverage?: LayerCoverage): WindowData {
  const volcanoes = volcanoPoints(index);
  // FIRMS's own active-volcano flag (type 1) also counts as near.
  const thermal = rawThermal.map((t) => ({ ...t, near: t.type === 1 || nearestKm(t.lon, t.lat, volcanoes) <= NEAR_KM }));
  return {
    months,
    thermal,
    quakes,
    hexes: hexbin(thermal),
    counts: monthlyCounts(months, thermal, quakes, coverage),
    activity: activityByVolcano(volcanoes, thermal, quakes),
  };
}

const point = (lon: number, lat: number, properties: Record<string, number>): GeoJSON.Feature => ({ type: "Feature", geometry: { type: "Point", coordinates: [lon, lat] }, properties });

export function toGeojson(d: WindowData): MapGeojson {
  return {
    hexes: { type: "FeatureCollection", features: d.hexes.map((h) => ({ type: "Feature", geometry: { type: "Polygon", coordinates: [h.ring] }, properties: { count: h.count } })) },
    // Far detections first, so near ones draw on top.
    thermal: { type: "FeatureCollection", features: [...d.thermal].sort((a, b) => Number(a.near) - Number(b.near)).map((t) => point(t.lon, t.lat, { near: t.near ? 1 : 0, frp: t.frp ?? 0 })) },
    // Small earthquakes first, so the largest draw on top.
    quakes: { type: "FeatureCollection", features: [...d.quakes].sort((a, b) => (a.mag ?? 0) - (b.mag ?? 0)).map((q) => point(q.lon, q.lat, { mag: q.mag ?? 3, depth: depthClass(q.depth) })) },
  };
}

/** Every month any national layer offers, up to the data's last month, oldest first (the map's timeline). */
export function recordMonths(layers: Layers, dataAsOf: string): string[] {
  const thermal = layers.layers.find((l) => l.id === "thermal-detections");
  const quakes = layers.layers.find((l) => l.id === "earthquakes-usgs");
  return [...new Set([...layerMonths(thermal), ...layerMonths(quakes)])].filter((m) => m <= dataAsOf.slice(0, 7)).sort();
}

/** The map's first window: the WINDOW_MONTHS months up to the record's last month. */
export function defaultWindowMonths(record: readonly string[]): string[] {
  const end = record.at(-1);
  return end ? windowMonths(end, WINDOW_MONTHS) : [];
}

// The window most recently asked for (one entry): the map page's first window is started from main.tsx before the
// page's chunk has arrived (app/prefetch.ts), and the page then picks up the same promise instead of loading again.
let lastWindow: { key: string; p: Promise<WindowData> } | null = null;

/** loadWindow, sharing the promise with the previous call for the same window. With the data version's `stamp`, the
 *  map's first window comes from the build-time pack (map/firstWindow.ts) when it matches, with the same points. */
export function loadWindowShared(layers: Layers, versionBase: string, index: VolcanoesIndex, months: string[], stamp?: string): Promise<WindowData> {
  const key = `${versionBase}|${months.join(",")}`;
  if (lastWindow?.key !== key) {
    const p = (stamp ? firstWindowFor(stamp, months) : Promise.resolve(null)).then((pack) =>
      pack ? deriveWindow(index, months, packThermal(pack), packQuakes(pack), layerCoverage(layers)) : loadWindow(layers, versionBase, index, months),
    );
    lastWindow = { key, p };
    p.catch(() => {
      if (lastWindow?.p === p) lastWindow = null;
    });
  }
  return lastWindow.p;
}

/** The record's earthquakes per month (the map's timeline strip): from the first-window pack when it matches. */
export async function recordQuakeCounts(layers: Layers, versionBase: string, record: string[], stamp?: string): Promise<number[]> {
  const pack = stamp ? await firstWindowFor(stamp, record, "record") : null;
  if (pack) return pack.recordQuakes;
  const quakeLayer = layers.layers.find((l) => l.id === "earthquakes-usgs");
  return quakesPerMonth(record, quakeLayer ? await loadAllQuakes(quakeLayer, versionBase, record) : []);
}

/** The window's data; null while the first window loads (the previous window stays while the next one loads). */
export function useWindowData(layers: Layers, versionBase: string, index: VolcanoesIndex, months: string[], stamp?: string): { data: WindowData | null; loading: boolean } {
  const key = months.join(",");
  const [got, setGot] = useState<{ key: string; data: WindowData } | null>(null);
  useEffect(() => {
    let live = true;
    void loadWindowShared(layers, versionBase, index, key ? key.split(",") : [], stamp).then((data) => live && setGot({ key, data }));
    return () => {
      live = false;
    };
  }, [layers, versionBase, index, key, stamp]);
  return { data: got?.data ?? null, loading: got?.key !== key };
}
