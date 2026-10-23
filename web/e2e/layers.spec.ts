import { devices, type Locator, type Page } from "@playwright/test";

import { expect, test } from "./fixtures";

// Every layer checkbox must change what the map shows: the WebGL map on a desktop, the static picture on a phone.
// (The fixtures have no earthquake layer, so its checkbox is checked only where it exists.)
const LAYERS = ["hexes", "thermal", "quakes"] as const;

async function presentLayers(page: Page) {
  await expect(page.locator("#layer-thermal")).toBeVisible();
  const ids: string[] = [];
  for (const id of LAYERS) if (await page.locator(`#layer-${id}`).count()) ids.push(id);
  return ids;
}

async function changesAfter(map: Locator, act: () => Promise<void>) {
  const before = await map.screenshot();
  await act();
  await expect.poll(async () => (await map.screenshot()).equals(before), { timeout: 8_000 }).toBe(false);
}

test("desktop: each layer checkbox changes the interactive map", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator(".volcano-marker")).toHaveCount(24);
  const map = page.locator("canvas.maplibregl-canvas");
  await page.waitForTimeout(1_500); // the window's data drawn
  for (const id of await presentLayers(page)) {
    const box = page.locator(`#layer-${id}`);
    await changesAfter(map, () => box.click());
    await expect(box).toHaveAttribute("data-state", "unchecked");
    await changesAfter(map, () => box.click());
  }
});

test.describe("phone", () => {
  // The WebKit device descriptor runs in Chromium here (as devices.spec.ts): only viewport, touch and mobile matter.
  const iphone: Record<string, unknown> = { ...devices["iPhone 15"] };
  delete iphone.defaultBrowserType;
  test.use(iphone);
  test("each layer checkbox changes the static map", async ({ page }) => {
    await page.goto("/");
    const map = page.locator("[data-static-map]");
    await expect(map.locator("g[aria-hidden] > *").first()).toBeAttached();
    for (const id of await presentLayers(page)) {
      const shapes = await map.locator("g[aria-hidden] > *").count();
      await page.locator(`#layer-${id}`).click();
      await expect.poll(() => map.locator("g[aria-hidden] > *").count()).toBeLessThan(shapes);
      await page.locator(`#layer-${id}`).click();
      await expect(map.locator("g[aria-hidden] > *")).toHaveCount(shapes);
    }
  });
});
