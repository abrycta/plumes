import { expect, ROUTES, test } from "./fixtures";

test.use({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });

for (const r of ROUTES) {
  test(`390 px: no horizontal page scroll on ${r.path}`, async ({ page }) => {
    await page.goto(r.path);
    await page.waitForLoadState("networkidle");
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow).toBeLessThanOrEqual(0);
  });
}

test("390 px: the scrubber's day buttons are usable by touch", async ({ page }) => {
  await page.goto("/volcano/taal");
  await page.getByRole("button", { name: "Next day" }).tap();
  await expect(page.locator("[data-readout] h3")).toHaveText("13 Jan 2020");
  const box = await page.getByRole("button", { name: "Next day" }).boundingBox();
  expect(box!.height).toBeGreaterThanOrEqual(24); // WCAG 2.2 target size (minimum)
});
