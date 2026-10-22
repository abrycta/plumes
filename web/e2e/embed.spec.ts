// /embed, the live picture krtmtthw.dev frames (served at /embed on Pages; vite preview serves it as /embed.html).
import { expect, test } from "./fixtures";

const ready = () => "embedReady" in document.documentElement.dataset;

test("desktop frame: map and caption, no chrome, no links, inert", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto("/embed.html?lang=en&pr=1&paused=1");
  await page.waitForFunction(ready, null, { timeout: 30_000 });
  await expect(page.getByTestId("embed-caption")).toBeVisible();
  expect(await page.locator("header, footer, a, button, .maplibregl-ctrl").count()).toBe(0);
  expect(await page.getByTestId("embed-frame").evaluate((e) => (e as HTMLElement).inert)).toBe(true);
  expect(await page.evaluate(() => document.documentElement.dataset.embedLayout)).toBe("desktop");
});

test("phone frame: its own compact layout at 14/12 px, nothing scrolls", async ({ page }) => {
  await page.setViewportSize({ width: 358, height: 224 });
  await page.goto("/embed.html?lang=en&pr=2&paused=1");
  await page.waitForFunction(ready, null, { timeout: 30_000 });
  const got = await page.evaluate(() => ({
    layout: document.documentElement.dataset.embedLayout,
    sizes: [...document.querySelectorAll('[data-testid="embed-caption"] p')].map((p) => getComputedStyle(p).fontSize),
    overflow: document.documentElement.scrollWidth > innerWidth || document.documentElement.scrollHeight > innerHeight,
    canvas: (document.querySelector("canvas")?.getBoundingClientRect().height ?? 0) > 100,
  }));
  expect(got).toEqual({ layout: "compact", sizes: ["14px", "12px"], overflow: false, canvas: true });
});
