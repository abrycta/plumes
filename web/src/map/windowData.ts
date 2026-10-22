// One time window of the national layers, loaded and derived once: points tagged near/far, hexagonal density,
// per-volcano activity, per-month counts, and the GeoJSON the interactive map draws.

import { useEffect, useState } from "react";

import type { Layers, VolcanoesIndex } from "@contracts/readmodels";

import { activityByVolcano, depthClass, hexbin, monthlyCounts, NEAR_KM, nearestKm, type Activity, type Hex, type MonthCount, type VolcanoPt } from "./density";
import { loadQuakes, loadThermal, type QuakePt, type ThermalPt } from "./points";

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

export async function loadWindow(layers: Layers, versionBase: string, index: VolcanoesIndex, months: string[]): Promise<WindowData> {
  const thermalLayer = layers.layers.find((l) => l.id === "thermal-detections");
  const quakeLayer = layers.layers.find((l) => l.id === "earthquakes-usgs");
  const [rawThermal, quakes] = await Promise.all([
    thermalLayer ? loadThermal(thermalLayer, versionBase, months).catch(() => []) : [],
    quakeLayer ? loadQuakes(quakeLayer, versionBase, months).catch(() => []) : [],
  ]);
  const volcanoes = volcanoPoints(index);
  // FIRMS's own active-volcano flag (type 1) also counts as near.
  const thermal = rawThermal.map((t) => ({ ...t, near: t.type === 1 || nearestKm(t.lon, t.lat, volcanoes) <= NEAR_KM }));
  return {
    months,
    thermal,
    quakes,
    hexes: hexbin(thermal),
    counts: monthlyCounts(months, thermal, quakes),
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

/** The window's data; null while the first window loads (the previous window stays while the next one loads). */
export function useWindowData(layers: Layers, versionBase: string, index: VolcanoesIndex, months: string[]): { data: WindowData | null; loading: boolean } {
  const key = months.join(",");
  const [got, setGot] = useState<{ key: string; data: WindowData } | null>(null);
  useEffect(() => {
    let live = true;
    void loadWindow(layers, versionBase, index, key ? key.split(",") : []).then((data) => live && setGot({ key, data }));
    return () => {
      live = false;
    };
  }, [layers, versionBase, index, key]);
  return { data: got?.data ?? null, loading: got?.key !== key };
}
