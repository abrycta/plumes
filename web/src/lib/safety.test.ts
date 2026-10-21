// Safety rules as code (RESEARCH.md §9): no "current" alert level and no forecasting language, in either language,
// anywhere in the app's source text or the bundled content. The e2e suite checks the rendered pages too.
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, resolve } from "node:path";

import { describe, expect, it } from "vitest";

export const FORBIDDEN: RegExp[] = [
  /current(ly)?\s+(alert|status|level|activity)/i,
  /\b(forecast|predict(ion|ed|s)?|will erupt|likely to erupt|expected to erupt|eruption is imminent)\b/i,
  /現在の(警戒|状況|活動)|予測|予報|噴火する見込み|噴火の恐れ/,
];

function files(dir: string): string[] {
  return readdirSync(dir).flatMap((f) => {
    const p = join(dir, f);
    return statSync(p).isDirectory() ? files(p) : /\.(tsx?|json)$/.test(f) && !f.endsWith(".test.ts") && !f.endsWith(".test.tsx") ? [p] : [];
  });
}

describe("safety language", () => {
  const src = resolve(import.meta.dirname, "..");
  it.each(files(src).map((f) => [f.slice(src.length + 1), f]))("%s", (_, f) => {
    const text = readFileSync(f, "utf8");
    for (const re of FORBIDDEN) expect(text.match(re)?.[0] ?? null, String(re)).toBeNull();
  });
  it("the patterns catch what they should", () => {
    for (const bad of ["Current alert level: 3", "We forecast", "現在の警戒レベル", "噴火の予測"]) expect(FORBIDDEN.some((re) => re.test(bad)), bad).toBe(true);
    for (const ok of ["as reported by PHIVOLCS on 13 Jan 2020", "Data through 21 Oct 2026"]) expect(FORBIDDEN.some((re) => re.test(ok)), ok).toBe(false);
  });
});
