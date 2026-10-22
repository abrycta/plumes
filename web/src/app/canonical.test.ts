import { describe, expect, it } from "vitest";

import { canonicalUrl } from "./canonical";

describe("canonicalUrl", () => {
  it.each([
    [{ page: "map", id: null, lang: null }, "https://plumes.krtmtthw.dev/"],
    [{ page: "volcano", id: "taal", lang: "en" }, "https://plumes.krtmtthw.dev/volcano/taal"],
    [{ page: "story", id: "taal-2020", lang: "ja" }, "https://plumes.krtmtthw.dev/story/taal-2020?lang=ja"],
    [{ page: "about", id: null, lang: null }, "https://plumes.krtmtthw.dev/about"],
    [{ page: "notfound", id: null, lang: null }, null],
  ] as const)("%o → %s", (s, want) => {
    expect(canonicalUrl(s)).toBe(want);
  });
});
