// The map layers' Akari data colours, in one place: the map paints with the token ids, legends and the /embed's
// swatches and bars with the matching Akari utilities. Change a layer's colour here and every view follows.
// Earthquakes use Akari's 藤 fuji depth steps (data.depth): they read over the 藍 ai density hexagons, and 朱 shu
// is the brand seal only, never a data colour.

export const LAYER_TOKENS = {
  thermal: "data.cat.4",
  /** Earthquake depth classes: shallow, intermediate, deep. */
  depth: ["data.depth.1", "data.depth.2", "data.depth.3"],
} as const;

/** Background utilities for the same tokens (shallow earthquakes stand for all in a swatch). */
export const LAYER_BG = {
  thermal: "bg-ak-cat-4",
  quakes: "bg-ak-depth-1",
} as const;

/** Text-colour utilities for the same tokens (legend dots). */
export const LAYER_TEXT = {
  thermal: "text-ak-cat-4",
  quakes: "text-ak-depth-1",
} as const;

/** A layer token's Akari scale name for MapLegendKey's `fill` ("data.cat.4" -> "cat-4"). */
export const legendFill = (token: string): string => token.replace(/^data\./, "").replace(".", "-");

/** A layer token as a CSS colour (for SVG fills): "data.div.7" -> "var(--ak-div-7)". */
export const layerVar = (token: string): string => `var(--ak-${legendFill(token)})`;
