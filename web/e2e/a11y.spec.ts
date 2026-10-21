import AxeBuilder from "@axe-core/playwright";

import { expect, ROUTES, test } from "./fixtures";

const THEMES = [
  { name: "light", scheme: "light" as const, contrast: "no-preference" as const },
  { name: "dark", scheme: "dark" as const, contrast: "no-preference" as const },
  { name: "high-contrast", scheme: "light" as const, contrast: "more" as const },
  { name: "dark high-contrast", scheme: "dark" as const, contrast: "more" as const },
];

for (const theme of THEMES) {
  for (const r of ROUTES.filter((x) => x.name !== "volcano without a record")) {
    test(`axe: ${r.name} in ${theme.name}`, async ({ page }) => {
      await page.emulateMedia({ colorScheme: theme.scheme, contrast: theme.contrast, reducedMotion: "reduce" });
      await page.goto(r.path);
      await page.waitForLoadState("networkidle");
      const results = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
        // MapLibre's own canvas and controls are third-party; everything around them is checked.
        .exclude(".maplibregl-ctrl-attrib")
        .exclude(".maplibregl-canvas")
        // Volcano markers sit as close as the volcanoes do (Mayon and Bulusan are 30 km apart), so their 24px targets
        // can overlap at national zoom. WCAG 2.5.8's "equivalent" exception applies: the list beside the map links to
        // every volcano with full-size targets, and that list is checked.
        .exclude(".volcano-marker")
        .exclude("[data-static-map] a")
        .analyze();
      const summary = results.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(" ")).slice(0, 3).join(" | ")}`);
      expect(summary).toEqual([]);
    });
  }
}
