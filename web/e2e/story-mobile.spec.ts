import { expect, test } from "./fixtures";

// Kurt, 2026-10-23: "stories are broken on mobile when scrolling". The story visual (timelines and pictures) is far
// taller than the 45svh panel pinned above the text on phones, so it covered every step while scrolling. Headless
// Linux Chromium ignores synthetic touch scrolls (CLAUDE.md rule 14), so the page is moved with window.scrollTo.

/** Scroll through the story; at each stop, every step card whose middle is on screen must be the topmost element there. */
async function coveredSteps(page: import("@playwright/test").Page): Promise<string[]> {
  await page.goto("/story/taal-2020");
  await page.waitForLoadState("networkidle");
  await expect(page.locator("[data-story-visual]").first()).toBeVisible();
  const max = await page.evaluate(() => document.documentElement.scrollHeight - window.innerHeight);
  const covered = new Set<string>();
  for (let y = 0; y <= max; y += 120) {
    await page.evaluate((top) => window.scrollTo(0, top), y);
    const hit = await page.evaluate(() => {
      const out: string[] = [];
      for (const li of document.querySelectorAll<HTMLElement>('[data-slot="scrollytelling-step"]')) {
        const text = li.querySelector("h2");
        if (!text) continue;
        const r = text.getBoundingClientRect();
        const cx = r.left + Math.min(r.width, 40) / 2;
        const cy = r.top + r.height / 2;
        if (cy < 140 || cy > window.innerHeight - 4) continue; // under the sticky site header, or off screen
        const top = document.elementFromPoint(cx, cy);
        if (!top || !li.contains(top)) out.push(li.dataset.step ?? "?");
      }
      return out;
    });
    hit.forEach((s) => covered.add(s));
  }
  return [...covered];
}

test.describe("phone", () => {
  test.use({ viewport: { width: 390, height: 664 }, hasTouch: true, isMobile: true, deviceScaleFactor: 3 });

  test("story: no step text is hidden under the visual while scrolling", async ({ page }) => {
    expect(await coveredSteps(page)).toEqual([]);
  });

  test("story: every step shows its own visual", async ({ page }) => {
    await page.goto("/story/taal-2020");
    const steps = page.locator('[data-slot="scrollytelling-step"]');
    await expect(steps.first()).toBeVisible();
    const n = await steps.count();
    expect(n).toBeGreaterThan(1);
    for (let i = 0; i < n; i++) await expect(steps.nth(i).locator("[data-story-visual]")).toHaveCount(1);
  });
});

test("desktop control: no step text is hidden under the visual while scrolling", async ({ page }) => {
  expect(await coveredSteps(page)).toEqual([]);
});
