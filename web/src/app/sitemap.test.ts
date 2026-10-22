import { describe, expect, it } from "vitest";

import type { StoriesIndex, VolcanoesIndex } from "@contracts/readmodels";

import { sitemapUrls, sitemapXml } from "./sitemap";

const volcanoes = {
  features: [{ properties: { id: "taal" } }, { properties: { id: "mayon" } }],
} as unknown as VolcanoesIndex;

const stories = {
  stories: [
    { id: "taal-2020", volcanoId: "taal", file: "story/taal-2020.json", status: "reviewed" },
    { id: "taal-2020", volcanoId: "taal", file: "story/drafts/taal-2020.json", status: "draft" },
    { id: "mayon-2018", volcanoId: "mayon", file: "story/drafts/mayon-2018.json", status: "draft" },
  ],
} as unknown as StoriesIndex;

describe("sitemap", () => {
  it("lists the fixed pages, reviewed stories and every volcano, never drafts", () => {
    expect(sitemapUrls("https://plumes.krtmtthw.dev/", volcanoes, stories)).toEqual([
      "https://plumes.krtmtthw.dev/",
      "https://plumes.krtmtthw.dev/volcanoes",
      "https://plumes.krtmtthw.dev/stories",
      "https://plumes.krtmtthw.dev/about",
      "https://plumes.krtmtthw.dev/story/taal-2020",
      "https://plumes.krtmtthw.dev/volcano/mayon",
      "https://plumes.krtmtthw.dev/volcano/taal",
    ]);
  });

  it("falls back to the known stories for versions without stories.json", () => {
    expect(sitemapUrls("https://x.test", null, null)).toContain("https://x.test/story/taal-2020");
  });

  it("writes a valid urlset", () => {
    const xml = sitemapXml(["https://x.test/a&b"]);
    expect(xml).toContain('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">');
    expect(xml).toContain("<loc>https://x.test/a&amp;b</loc>");
  });
});
