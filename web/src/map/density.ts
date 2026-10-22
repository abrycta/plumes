// Pure helpers for the data-dense map: time windows, distance to the nearest volcano, hexagonal density bins,
// per-volcano activity and per-month counts. No DOM, no MapLibre: unit-tested in density.test.ts.

import type { QuakePt, ThermalPt } from "./points";

/** Months in the map's default window. */
export const WINDOW_MONTHS = 12;
/** A thermal detection this close to a volcano is drawn at full strength; farther ones are faint (vegetation fires). */
export const NEAR_KM = 15;
/** Earthquakes counted on a volcano's marker. */
export const QUAKE_RING_KM = 30;
/** Hexagon size: centre to corner, km (about 30 km across). */
export const HEX_KM = 15;
/** Earthquake depth classes (km): shallow, intermediate, deep (the USGS convention). */
export const DEPTH_BREAKS = [70, 300] as const;
/** Thermal detections per hexagon: class breaks of the five-step sequential scale. */
export const HEX_BREAKS = [3, 10, 30, 100] as const;

const KM_LAT = 110.57;
const KM_LON = 111.32 * Math.cos((12 * Math.PI) / 180);

export function addMonths(month: string, n: number): string {
  const [y, m] = month.split("-").map(Number) as [number, number];
  const i = y * 12 + (m - 1) + n;
  return `${Math.floor(i / 12)}-${String((i % 12) + 1).padStart(2, "0")}`;
}

/** The `n` months ending at `end`, oldest first. */
export function windowMonths(end: string, n = WINDOW_MONTHS): string[] {
  return Array.from({ length: n }, (_, i) => addMonths(end, i - n + 1));
}

/** Approximate distance in km (equirectangular; fine at these distances and latitudes). */
export function distanceKm(lon1: number, lat1: number, lon2: number, lat2: number): number {
  const k = Math.cos((((lat1 + lat2) / 2) * Math.PI) / 180) * 111.32;
  return Math.hypot((lon1 - lon2) * k, (lat1 - lat2) * KM_LAT);
}

export interface VolcanoPt {
  id: string;
  lon: number;
  lat: number;
}

/** Distance in km to the nearest volcano. */
export function nearestKm(lon: number, lat: number, volcanoes: readonly VolcanoPt[]): number {
  let best = Infinity;
  for (const v of volcanoes) best = Math.min(best, distanceKm(lon, lat, v.lon, v.lat));
  return best;
}

/** 0 shallow (< 70 km), 1 intermediate (70–300 km), 2 deep (≥ 300 km); unknown depth counts as shallow. */
export function depthClass(depth: number | null): 0 | 1 | 2 {
  if (depth == null || depth < DEPTH_BREAKS[0]) return 0;
  return depth < DEPTH_BREAKS[1] ? 1 : 2;
}

export interface Hex {
  center: [number, number];
  /** Ring of [lon, lat], closed. */
  ring: [number, number][];
  count: number;
}

/** Pointy-top hexagonal bins of `points` (size `km`, centre to corner), only bins with at least one point. */
export function hexbin(points: readonly { lon: number; lat: number }[], km = HEX_KM): Hex[] {
  const w = Math.sqrt(3) * km;
  const bins = new Map<string, { q: number; r: number; count: number }>();
  for (const p of points) {
    const x = p.lon * KM_LON;
    const y = p.lat * KM_LAT;
    // Axial coordinates, rounded through cube coordinates.
    const qf = ((Math.sqrt(3) / 3) * x - y / 3) / km;
    const rf = ((2 / 3) * y) / km;
    let q = Math.round(qf);
    let r = Math.round(rf);
    const s = Math.round(-qf - rf);
    const dq = Math.abs(q - qf);
    const dr = Math.abs(r - rf);
    const ds = Math.abs(s - (-qf - rf));
    if (dq > dr && dq > ds) q = -r - s;
    else if (dr > ds) r = -q - s;
    const key = `${q},${r}`;
    const b = bins.get(key);
    if (b) b.count++;
    else bins.set(key, { q, r, count: 1 });
  }
  return [...bins.values()].map(({ q, r, count }) => {
    const center: [number, number] = [(w * (q + r / 2)) / KM_LON, (1.5 * km * r) / KM_LAT];
    return { center, ring: hexRing(center, km), count };
  });
}

/** The closed ring of the hexagon of size `km` centred on [lon, lat]. */
export function hexRing([lon, lat]: [number, number], km = HEX_KM): [number, number][] {
  const ring: [number, number][] = [];
  for (let i = 0; i <= 6; i++) {
    const a = ((60 * (i % 6) - 30) * Math.PI) / 180;
    ring.push([lon + (km * Math.cos(a)) / KM_LON, lat + (km * Math.sin(a)) / KM_LAT]);
  }
  return ring;
}

export interface Activity {
  /** Thermal detections within NEAR_KM. */
  thermal: number;
  /** Earthquakes within QUAKE_RING_KM. */
  quakes: number;
  /** Largest magnitude among them. */
  maxMag: number | null;
}

/** Per-volcano counts in the window. */
export function activityByVolcano(volcanoes: readonly VolcanoPt[], thermal: readonly ThermalPt[], quakes: readonly QuakePt[]): Map<string, Activity> {
  const out = new Map<string, Activity>(volcanoes.map((v) => [v.id, { thermal: 0, quakes: 0, maxMag: null }]));
  for (const v of volcanoes) {
    const a = out.get(v.id)!;
    for (const t of thermal) if (Math.abs(t.lat - v.lat) < 0.2 && distanceKm(t.lon, t.lat, v.lon, v.lat) <= NEAR_KM) a.thermal++;
    for (const q of quakes)
      if (Math.abs(q.lat - v.lat) < 0.4 && distanceKm(q.lon, q.lat, v.lon, v.lat) <= QUAKE_RING_KM) {
        a.quakes++;
        if (q.mag != null && (a.maxMag == null || q.mag > a.maxMag)) a.maxMag = q.mag;
      }
  }
  return out;
}

export interface MonthCount {
  month: string;
  thermalNear: number;
  thermalFar: number;
  quakes: number;
}

/** Counts per month of `months`, splitting thermal detections by distance to a volcano. */
export function monthlyCounts(months: readonly string[], thermal: readonly (ThermalPt & { near: boolean })[], quakes: readonly QuakePt[]): MonthCount[] {
  const by = new Map<string, MonthCount>(months.map((m) => [m, { month: m, thermalNear: 0, thermalFar: 0, quakes: 0 }]));
  for (const t of thermal) {
    const c = by.get(t.month);
    if (c) {
      if (t.near) c.thermalNear++;
      else c.thermalFar++;
    }
  }
  for (const q of quakes) {
    const c = by.get(q.month);
    if (c) c.quakes++;
  }
  return months.map((m) => by.get(m)!);
}

/** Earthquakes per month over `months` (the timeline's whole-record strip). */
export function quakesPerMonth(months: readonly string[], quakes: readonly QuakePt[]): number[] {
  const idx = new Map(months.map((m, i) => [m, i]));
  const out = months.map(() => 0);
  for (const q of quakes) {
    const i = idx.get(q.month);
    if (i != null) out[i]!++;
  }
  return out;
}
