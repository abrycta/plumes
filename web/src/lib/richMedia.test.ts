import { describe, expect, it } from "vitest";

import { richMediaAllowed } from "./richMedia";

// Rule 6b device matrix, as media-query answers: width >= 768, hover + fine pointer, no Save-Data.
const env = (wide: boolean, fine: boolean, saveData = false) => ({ matches: (q: string) => (q.includes("min-width") ? wide : fine), saveData });

describe("richMediaAllowed", () => {
  it.each([
    ["iPhone", env(false, false), false],
    ["Pixel", env(false, false), false],
    ["touch-only iPad", env(true, false), false],
    ["iPad with trackpad", env(true, true), true],
    ["touch laptop (mouse primary)", env(true, true), true],
    ["narrow desktop", env(false, true), false],
    ["normal desktop", env(true, true), true],
    ["normal desktop with Save-Data", env(true, true, true), false],
  ])("%s", (_, e, want) => {
    expect(richMediaAllowed(e)).toBe(want);
  });
});
