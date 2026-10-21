import { test as base, expect } from "@playwright/test";

/** Every test runs offline: the OpenFreeMap basemap is unreachable, so the map falls back to the bundled coastline. */
export const test = base.extend({
  page: async ({ page }, provide) => {
    await page.route("https://tiles.openfreemap.org/**", (r) => r.abort());
    await provide(page);
  },
});
export { expect };

export const ROUTES = [
  { name: "map", path: "/" },
  { name: "volcanoes", path: "/volcanoes" },
  { name: "volcano", path: "/volcano/taal" },
  { name: "volcano without a record", path: "/volcano/mayon" },
  { name: "stories", path: "/stories" },
  { name: "story", path: "/story/taal-2020" },
  { name: "about", path: "/about" },
  { name: "not found", path: "/nope" },
] as const;
