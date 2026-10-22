// The national monthly SO₂ map (layers.json `so2-monthly`, format "cog"): one small int16 GeoTIFF per month, fetched
// whole (one GET, no Range request), decoded with `geotiff` and coloured here from Akari's sequential data ramp, so
// light, dark and high contrast follow the theme. Band 1 = mean SO₂ column (µmol/m²), band 2 = share of the month's
// days with a valid pixel (%). Pure functions apart from the decoder (unit-tested on a tiny fixture).

import { fromArrayBuffer } from "geotiff";

import type { Layer } from "@contracts/readmodels";

export interface So2Grid {
  width: number;
  height: number;
  /** [west, south, east, north] in degrees. */
  bounds: [number, number, number, number];
  so2: Int16Array;
  valid: Int16Array;
  nodata: number;
}

/** Fallback classes when the layer entry has no legend stops (µmol/m², lower bounds). */
export const SO2_STOPS = [25, 50, 100, 200, 400];
/** Pixels with fewer valid days than this (% of the month) are not drawn (layers.json note says so). */
export const MIN_VALID_PCT = 10;

export async function decodeSo2(buf: ArrayBuffer): Promise<So2Grid> {
  const tiff = await fromArrayBuffer(buf);
  const img = await tiff.getImage();
  const rasters = await img.readRasters({ interleave: false });
  const [so2, valid] = [rasters[0], rasters[1]];
  if (!(so2 instanceof Int16Array) || !(valid instanceof Int16Array)) throw new Error("so2-monthly: expected two int16 bands");
  const [w, s, e, n] = img.getBoundingBox();
  return { width: img.getWidth(), height: img.getHeight(), bounds: [w!, s!, e!, n!], so2, valid, nodata: img.getGDALNoData() ?? -32768 };
}

/** Legend class lower bounds from the layer entry, else the defaults. */
export function so2Stops(layer: Layer | undefined): number[] {
  const stops = layer?.legend?.stops?.map((s) => s[0]);
  return stops?.length ? stops : SO2_STOPS;
}

/** Index of the class a value falls in, or -1 when it is below the first stop. */
export function classOf(value: number, stops: number[]): number {
  let k = -1;
  for (let i = 0; i < stops.length; i++) if (value >= stops[i]!) k = i;
  return k;
}

function hexRgb(hex: string): [number, number, number] {
  const h = hex.replace("#", "");
  const full = h.length === 3 ? [...h].map((c) => c + c).join("") : h.slice(0, 6);
  return [parseInt(full.slice(0, 2), 16), parseInt(full.slice(2, 4), 16), parseInt(full.slice(4, 6), 16)];
}

/** RGBA pixels (row 0 = north) for an image source: transparent where nodata, too few valid days, or below the first stop. */
export function so2Rgba(grid: So2Grid, colours: string[], stops: number[], alpha = 200): Uint8ClampedArray {
  const rgb = colours.map(hexRgb);
  const out = new Uint8ClampedArray(grid.width * grid.height * 4);
  for (let i = 0; i < grid.width * grid.height; i++) {
    const v = grid.so2[i]!;
    if (v === grid.nodata || grid.valid[i]! < MIN_VALID_PCT) continue;
    const k = classOf(v, stops);
    if (k < 0) continue;
    const c = rgb[Math.min(k, rgb.length - 1)]!;
    out.set([c[0], c[1], c[2], alpha], i * 4);
  }
  return out;
}

/** Mean share of valid days over the grid (0..1): the month's coverage, shown beside the map. */
export function validShare(grid: So2Grid): number {
  let sum = 0;
  for (const v of grid.valid) sum += Math.max(0, v);
  return grid.valid.length ? sum / grid.valid.length / 100 : 0;
}

/** MapLibre image-source corners: top-left, top-right, bottom-right, bottom-left. */
export function corners(b: So2Grid["bounds"]): [[number, number], [number, number], [number, number], [number, number]] {
  const [w, s, e, n] = b;
  return [
    [w, n],
    [e, n],
    [e, s],
    [w, s],
  ];
}
