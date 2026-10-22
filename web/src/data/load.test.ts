import { describe, expect, it } from "vitest";

import type { StoriesIndex } from "@contracts/readmodels";

import { NotFoundError, resolveRoot, storyRefs } from "./load";

const latest = { schemaVersion: "1", kind: "latest", current: "v3", base: "v3/", dataAsOf: "2026-09-30", generatedAt: "x", mirrors: ["https://huggingface.co/datasets/permission-alluring/plumes/resolve/main/"] };

describe("resolveRoot", () => {
  it("uses the first base that answers and keeps the others as mirrors", async () => {
    const seen: string[] = [];
    const fetchJson = async <T,>(url: string): Promise<T> => {
      seen.push(url);
      if (url.startsWith("https://abrycta.github.io")) throw new Error("HTTP 503");
      return latest as T;
    };
    const root = await resolveRoot({ data: { baseUrl: "https://abrycta.github.io/plumes/data/", fallbackBaseUrls: ["https://mirror.example/data/"] } }, fetchJson);
    expect(seen).toEqual(["https://abrycta.github.io/plumes/data/latest.json", "https://mirror.example/data/latest.json"]);
    expect(root.versionBase).toBe("https://mirror.example/data/v3/");
    expect(root.mirrors).toContain("https://huggingface.co/datasets/permission-alluring/plumes/resolve/main/v3/");
  });
  it("fails when no base answers", async () => {
    await expect(resolveRoot({ data: { baseUrl: "https://a.example/" } }, async () => Promise.reject(new NotFoundError("x")))).rejects.toThrow("x");
  });
});

describe("storyRefs (ST1: drafts hidden unless ?preview)", () => {
  const title = { en: "x", ja: "x" };
  const span = { start: "2020-01-01", end: "2020-03-31" };
  const index = {
    schemaVersion: "1",
    kind: "stories",
    dataVersion: "v3",
    dataAsOf: "2026-10-22",
    generatedAt: "x",
    stories: [
      { id: "taal-2020", volcanoId: "taal", title, span, status: "reviewed", file: "story/taal-2020.json" },
      { id: "kanlaon-2024-06", volcanoId: "kanlaon", title, span, status: "draft", rank: 1, file: "story/drafts/kanlaon-2024-06.json" },
      { id: "taal-2020", volcanoId: "taal", title, span, status: "draft", rank: 2, file: "story/drafts/taal-2020.json" },
      { id: "mayon-2001", volcanoId: "mayon", title, span, status: "draft", rank: 3 },
    ],
  } as StoriesIndex;
  it("lists only reviewed stories without the preview parameter", () => {
    expect(storyRefs(index, false)).toEqual([{ id: "taal-2020", volcanoId: "taal", file: "story/taal-2020.json", status: "reviewed" }]);
  });
  it("adds drafts in preview, by rank, a draft replacing the reviewed file of the same id; readings have no file", () => {
    expect(storyRefs(index, true).map((s) => s.file)).toEqual(["story/drafts/kanlaon-2024-06.json", "story/drafts/taal-2020.json"]);
  });
  it("falls back to the built-in list for versions without stories.json", () => {
    expect(storyRefs(null, true)).toEqual([{ id: "taal-2020", volcanoId: "taal", file: "story/taal-2020.json", status: "reviewed" }]);
  });
});
