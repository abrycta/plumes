import { expect, test } from "./fixtures";

test("map: 24 volcanoes, a list that filters, links to volcano pages", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Every Philippine volcano");
  await expect(page.locator("li[data-volcano]")).toHaveCount(24);
  await page.getByLabel("Find a volcano").fill("taa");
  await expect(page.locator("li[data-volcano]")).toHaveCount(1);
  await page.locator("li[data-volcano='taal']").getByRole("link", { name: "Taal" }).click();
  await expect(page).toHaveURL(/\/volcano\/taal$/);
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Taal");
});

test("volcano: the scrubber moves one day across every track, and the URL keeps it", async ({ page }) => {
  await page.goto("/volcano/taal");
  const scrubber = page.getByTestId("scrubber");
  await expect(page.locator("[data-readout] h3")).toHaveText("12 Jan 2020");
  await scrubber.focus();
  await page.keyboard.press("ArrowRight");
  await expect(page.locator("[data-readout] h3")).toHaveText("13 Jan 2020");
  await expect(page).toHaveURL(/date=2020-01-13/);
  await expect(page.locator("[data-readout] tr", { hasText: "USGS earthquakes" })).toContainText("15 events");
  await page.getByRole("button", { name: "Next day" }).click();
  await expect(page.locator("[data-readout] tr", { hasText: "TROPOMI" })).toContainText("No valid observation");
  await page.getByRole("button", { name: "12–26 Jan 2020" }).click();
  await expect(page).toHaveURL(/from=2020-01-05&to=2020-02-02/);
  await page.getByRole("button", { name: "50 km" }).click();
  await expect(page.locator("[data-track='so2_s5p_50km']")).toBeVisible();
});

test("volcano without a record in this version says so", async ({ page }) => {
  await page.goto("/volcano/mayon");
  await expect(page.getByText("no per-volcano record for this volcano")).toBeVisible();
  await page.goto("/volcano/not-a-volcano");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Nothing recorded here");
});

test("story: steps in order, the visual follows keyboard focus, figures link to sources", async ({ page }) => {
  await page.goto("/story/taal-2020");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Taal, January 2020");
  const steps = page.getByRole("list", { name: "Story steps" }).getByRole("listitem");
  await expect(steps).toHaveCount(5);
  await steps.nth(3).focus();
  await expect(page.locator("[data-story-visual] img")).toHaveCount(2);
  await expect(page.getByRole("link", { name: /dswd-dromic-reports/ })).toHaveAttribute("href", /dromic\.dswd\.gov\.ph/);
});

test("about: licences and notices", async ({ page }) => {
  await page.goto("/about");
  await expect(page.locator("tr[id^='source-']")).toHaveCount(26);
  await expect(page.getByText(/^Contains modified Copernicus Sentinel data \(2018/)).toBeVisible();
  await expect(page.getByText(/provided ‘as is’/)).toBeVisible();
});

test("Japanese: the switch translates the page and the URL keeps ?lang=ja", async ({ page }) => {
  await page.goto("/volcano/taal");
  await page.getByRole("radio", { name: "日本語" }).click();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("タール火山");
  await expect(page.locator("html")).toHaveAttribute("lang", "ja");
  await expect(page.locator("[data-safety-banner]")).toContainText("警報サービスではありません");
});
