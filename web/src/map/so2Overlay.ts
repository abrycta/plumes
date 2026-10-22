// Draws one month of the national SO₂ map (so2-monthly) on a MapLibre map as an image source below the volcano markers.
// Not wired into the map page yet (the map page is being reworked in parallel): the page calls showSo2() with the
// month's file URL and the theme key, and removeSo2() when the layer is switched off. The decoded grid is cached per
// URL, so a theme change only recolours.

import { flat } from "@abrycta/akari/tokens";
import type { ImageSource, Map as MlMap } from "maplibre-gl";

import { corners, decodeSo2, type So2Grid, so2Rgba } from "@/data/so2Map";

export type ThemeKey = "light" | "dark" | "light-hc" | "dark-hc";

const ID = "so2-monthly";
const cache = new Map<string, Promise<So2Grid>>();

/** Akari's five sequential data colours for the theme (low to high). */
export function so2Colours(key: ThemeKey): string[] {
  const tokens = flat as unknown as Record<string, Record<string, string>>;
  return [1, 2, 3, 4, 5].map((i) => tokens[`data.seq.${i}`]?.[key] ?? tokens[`data.seq.${i}`]?.light ?? "#888888");
}

export function loadSo2(url: string): Promise<So2Grid> {
  let p = cache.get(url);
  if (!p) {
    p = fetch(url).then((r) => {
      if (!r.ok) throw new Error(`so2-monthly: ${r.status} for ${url}`);
      return r.arrayBuffer().then(decodeSo2);
    });
    p.catch(() => cache.delete(url));
    cache.set(url, p);
  }
  return p;
}

function dataUrl(grid: So2Grid, colours: string[], stops: number[]): string {
  const canvas = document.createElement("canvas");
  canvas.width = grid.width;
  canvas.height = grid.height;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("so2-monthly: no 2D canvas");
  ctx.putImageData(new ImageData(so2Rgba(grid, colours, stops) as Uint8ClampedArray<ArrayBuffer>, grid.width, grid.height), 0, 0);
  return canvas.toDataURL("image/png");
}

/** Show (or update) the month at `url`; returns the decoded grid (for the coverage line). `beforeId` keeps it under point layers. */
export async function showSo2(map: MlMap, url: string, key: ThemeKey, stops: number[], beforeId?: string): Promise<So2Grid> {
  const grid = await loadSo2(url);
  const image = dataUrl(grid, so2Colours(key), stops);
  const coordinates = corners(grid.bounds);
  const src = map.getSource(ID) as ImageSource | undefined;
  if (src) src.updateImage({ url: image, coordinates });
  else {
    map.addSource(ID, { type: "image", url: image, coordinates });
    // Nearest-neighbour: each 0.1° cell stays a visible cell, never a smoothed blur that suggests finer detail.
    map.addLayer({ id: ID, type: "raster", source: ID, paint: { "raster-resampling": "nearest", "raster-opacity": 0.85 } }, beforeId && map.getLayer(beforeId) ? beforeId : undefined);
  }
  return grid;
}

export function removeSo2(map: MlMap): void {
  if (map.getLayer(ID)) map.removeLayer(ID);
  if (map.getSource(ID)) map.removeSource(ID);
}
