import { expect, test } from "./fixtures";

test("deep-time strip: Taal's eruptions on one axis, NCEI deaths cited per event", async ({ page }) => {
  await page.goto("/volcano/taal");
  const strip = page.locator("[data-deeptime]");
  await expect(strip.getByRole("heading", { name: "Deep time" })).toBeVisible();
  await expect(strip.getByRole("img")).toHaveAttribute("aria-label", /eruptions in the Smithsonian record, 3580 BCE to \d{4}; \d+ with deaths/);
  await strip.locator("summary").click();
  const row = strip.locator("li", { hasText: "30 Jan 1911" });
  await expect(row).toContainText("1,335");
  await expect(row.getByRole("link", { name: /NCEI/ })).toHaveAttribute("href", /ngdc\.noaa\.gov\/hazel\/view\/hazards\/volcano\/event-more-info\/\d+$/);
});

test("deep-time strip: absent for a volcano GVP does not list", async ({ page }) => {
  await page.goto("/volcano/smith");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await expect(page.locator("[data-deeptime]")).toHaveCount(0);
});
