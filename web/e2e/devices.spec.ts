import { devices } from "@playwright/test";

import { expect, test } from "./fixtures";

// Rule 6b: the MapLibre map loads only with (min-width: 768px), (hover: hover) and (pointer: fine), and no Save-Data.
// Touch emulation in Chromium reports hover: none / pointer: coarse. Real touch laptops and iPads with a trackpad report a
// hovering fine primary pointer while also having touch, so `finePointer` answers that one query as such devices do.
const MATRIX = [
  { name: "iPhone", use: { ...devices["iPhone 15"] }, rich: false },
  { name: "Pixel", use: { ...devices["Pixel 7"] }, rich: false },
  { name: "touch-only iPad", use: { ...devices["iPad (gen 7) landscape"] }, rich: false },
  { name: "iPad with trackpad", use: { viewport: { width: 1180, height: 820 }, hasTouch: true }, rich: true, finePointer: true },
  { name: "touch laptop", use: { viewport: { width: 1366, height: 768 }, hasTouch: true }, rich: true, finePointer: true },
  { name: "narrow desktop", use: { viewport: { width: 700, height: 900 } }, rich: false },
  { name: "normal desktop", use: { viewport: { width: 1440, height: 900 } }, rich: true },
];

for (const d of MATRIX) {
  test.describe(d.name, () => {
    // Playwright's WebKit-only device descriptors run in Chromium here; only viewport, touch and mobile matter.
    const use: Record<string, unknown> = { ...d.use };
    delete use.defaultBrowserType;
    test.use(use);
    test(`map: ${d.rich ? "interactive" : "static picture"}`, async ({ page }) => {
      if ("finePointer" in d)
        await page.addInitScript(() => {
          const real = window.matchMedia.bind(window);
          window.matchMedia = (q: string) => (q === "(hover: hover) and (pointer: fine)" ? ({ ...real(q), matches: true, media: q, addEventListener() {}, removeEventListener() {} } as MediaQueryList) : real(q));
        });
      await page.goto("/");
      await expect(page.locator("li[data-volcano]")).toHaveCount(24);
      if (d.rich) {
        await expect(page.locator("[data-interactive-map]")).toBeVisible();
        await expect(page.locator(".volcano-marker")).toHaveCount(24);
      } else {
        await expect(page.locator("[data-static-map]")).toBeVisible();
        await expect(page.locator("[data-interactive-map]")).toHaveCount(0);
      }
    });
  });
}

test("Save-Data keeps the static map on a desktop", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.addInitScript(() => Object.defineProperty(navigator, "connection", { value: Object.assign(new EventTarget(), { saveData: true }) }));
  await page.goto("/");
  await expect(page.locator("[data-static-map]")).toBeVisible();
  await expect(page.locator("[data-interactive-map]")).toHaveCount(0);
});
