import { expect, test } from "./fixtures";

// Kurt, 2026-10-23: "stories on plumes dont load on safari mobile the first time, needs to go to other tabs first then
// go back to stories." Opening Stories from another page (no prefetch) loaded the story files one after another,
// because each card's use() suspended before the next card rendered: with v5's 19 stories that is 19 round trips of
// blank page on a phone. Runs in the "webkit-iphone" project (WebKit, iPhone 13, a fresh context per test).

const N = 8;
const DELAY_MS = 800;

/** Serve an index of N reviewed stories (copies of the fixture story) whose files answer slowly, like a phone network. */
async function slowStories(page: import("@playwright/test").Page) {
  const started: number[] = [];
  const finished: number[] = [];
  await page.route(/\/data\/v0\/stories\.json$/, async (route) => {
    const res = await route.fetch();
    const index = await res.json();
    const ref = index.stories.find((s: { status: string; file?: string }) => s.status === "reviewed" && s.file);
    index.stories = Array.from({ length: N }, (_, i) => ({
      ...ref,
      id: `s${i}`,
      file: `story/s${i}.json`,
    }));
    await route.fulfill({ response: res, json: index });
  });
  await page.route(/\/data\/v0\/story\/s\d+\.json$/, async (route) => {
    started.push(Date.now());
    const i = Number(/s(\d+)\.json$/.exec(route.request().url())![1]);
    const res = await route.fetch({
      url: route
        .request()
        .url()
        .replace(/s\d+\.json$/, "taal-2020.json"),
    });
    const story = await res.json();
    story.id = `s${i}`;
    story.title = { en: `Story ${i}`, ja: `Story ${i}` };
    await new Promise((r) => setTimeout(r, DELAY_MS));
    finished.push(Date.now());
    await route.fulfill({ response: res, json: story });
  });
  return { started, finished };
}

test("stories: opening Stories from the map loads every story file at once", async ({ page }) => {
  const net = await slowStories(page);
  await page.goto("/");
  await page
    .getByRole("link", { name: /^Stories$/ })
    .first()
    .click();
  await expect(page).toHaveURL(/\/stories$/);
  await expect(page.locator("[data-story-card]")).toHaveCount(N, {
    timeout: 2 * DELAY_MS + 3000,
  });
  // Every request started before the first one answered: in parallel, not a waterfall.
  expect(net.started.filter((t) => t < net.finished[0]).length).toBe(N);
});

test("stories: a first visit to /stories shows the story list", async ({ page }) => {
  await slowStories(page);
  await page.goto("/stories");
  await expect(page.locator("[data-story-card]")).toHaveCount(N, {
    timeout: 2 * DELAY_MS + 3000,
  });
});
