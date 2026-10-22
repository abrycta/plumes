// National map layers (layers.json): which months a layer offers and the file that holds one month. Pure functions.
// Published versions keep thermal detections as one PMTiles per year ({year}) and earthquakes as one PMTiles for the
// whole record, each feature carrying a `month` property; the contract fixture has one GeoJSON per month ({month}).

import type { Layer } from "@contracts/readmodels";

/** Months the layer can show, oldest first: `time.available` when listed, else every month from start to end. */
export function layerMonths(layer: Layer | undefined): string[] {
  if (!layer?.time || layer.time.step !== "month") return [];
  if (layer.time.available) return layer.time.available;
  const out: string[] = [];
  let [y, m] = layer.time.start.split("-").map(Number) as [number, number];
  const end = layer.time.end.slice(0, 7);
  for (;;) {
    const iso = `${y}-${String(m).padStart(2, "0")}`;
    if (iso > end) break;
    out.push(iso);
    m = m === 12 ? 1 : m + 1;
    if (m === 1) y += 1;
  }
  return out;
}

/** The layer file (relative to the version root) that holds `month`. */
export function layerPath(layer: Layer, month: string): string {
  return layer.url.replace("{month}", month).replace("{year}", month.slice(0, 4));
}

/** True when one file holds several months, so the map filters features on their `month` property. */
export function filtersByMonth(layer: Layer): boolean {
  return !layer.url.includes("{month}") && layer.properties?.month != null;
}
