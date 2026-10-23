import { expect, ROUTES, test } from "./fixtures";

// Safety rules (RESEARCH.md §9), checked on the rendered pages in both languages.
const FORBIDDEN = [/current(ly)?\s+(alert|status|level|activity)/i, /\b(forecast|predict(ion|ed|s)?|will erupt|likely to erupt|expected to erupt)\b/i, /現在の(警戒|状況|活動)|予測|予報/];

for (const lang of ["en", "ja"] as const) {
  for (const r of ROUTES) {
    test(`${r.name} (${lang}): one Akari header, the banner, no present-status or forecast words`, async ({ page }) => {
      await page.goto(`${r.path}${r.path.includes("?") ? "&" : "?"}lang=${lang}`);
      await page.waitForLoadState("networkidle");
      await expect(page.locator("header[data-akari-header]")).toHaveCount(1);
      await expect(page.getByRole("banner")).toHaveAttribute("data-akari-header", "");
      const banner = page.locator("[data-safety-banner]");
      await expect(banner).toHaveCount(1);
      await expect(banner).toContainText(lang === "en" ? "DOST-PHIVOLCS is the authority on alert levels" : "警戒レベルを発表するのはDOST-PHIVOLCSです");
      await expect(banner.getByRole("link", { name: /DOST-PHIVOLCS/ })).toHaveAttribute("href", "https://www.phivolcs.dost.gov.ph/");
      await expect(banner.getByRole("link", { name: /bulletins|火山情報/ })).toHaveAttribute("href", /phivolcs\.dost\.gov\.ph\/bulletin/);
      const text = await page.locator("body").innerText();
      for (const re of FORBIDDEN) expect(text.match(re)?.[0] ?? null, String(re)).toBeNull();
    });
  }
}

test("every chart on the volcano page says 'Data through' and names its instrument", async ({ page }) => {
  await page.goto("/volcano/taal");
  const tracks = page.locator("[data-track]");
  await expect(tracks.first()).toBeVisible();
  const n = await tracks.count();
  expect(n).toBeGreaterThanOrEqual(8);
  for (let i = 0; i < n; i++) {
    await expect(tracks.nth(i).locator("[data-data-through]")).toContainText("Data through 21 Oct 2026");
    await expect(tracks.nth(i).locator("figcaption")).toContainText(/Sentinel|MODIS|VIIRS|USGS|PHIVOLCS|VAAC|DSWD|Smithsonian|FIRMS/);
  }
});

test("alert levels are dated, linked and 'as reported'", async ({ page }) => {
  await page.goto("/volcano/taal?date=2020-01-20");
  const row = page.locator("[data-readout] tr", { hasText: "Alert level" });
  await expect(row).toContainText("Alert Level 4, as reported by PHIVOLCS on 13 Jan 2020");
  await expect(row.getByRole("link")).toHaveAttribute("href", /phivolcs\.dost\.gov\.ph\/taal-volcano-bulletin-13-january-2020/);
});
