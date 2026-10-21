import { describe, expect, it } from "vitest";

import { NotFoundError, resolveRoot } from "./load";

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
