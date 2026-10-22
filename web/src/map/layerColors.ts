// The map layers' Akari data colours, in one place: the map paints with the token ids, legends and the /embed's
// swatches and bars with the matching Akari utilities. Change a layer's colour here and every view follows.

export const LAYER_TOKENS = {
  thermal: "data.cat.4",
  /** Earthquake depth classes: shallow, intermediate, deep. */
  depth: ["data.div.7", "data.div.6", "data.div.5"],
} as const;

/** Background utilities for the same tokens (shallow earthquakes stand for all in a swatch). */
export const LAYER_BG = {
  thermal: "bg-ak-cat-4",
  quakes: "bg-ak-div-7",
} as const;

/** Text-colour utilities for the same tokens (legend dots). */
export const LAYER_TEXT = {
  thermal: "text-ak-cat-4",
  quakes: "text-ak-div-7",
} as const;
