import { describe, expect, it } from "vitest";

import type { DeepTimeVolcano } from "@contracts/deeptime";

import { deathsForBar, formatPartialDate, formatYear, impactRows, ticks, timeScale, yearOf } from "./deeptime";

describe("deep-time strip data", () => {
  it("reads and writes BCE years the GVP way (no year 0)", () => {
    expect(yearOf("-3580")).toBe(-3580);
    expect(yearOf("1911-01-27")).toBe(1911);
    expect(formatYear(-3580, "en")).toBe("3580 BCE");
    expect(formatYear(-3580, "ja")).toBe("紀元前3580年");
    expect(formatPartialDate("1911-01-27", "en")).toBe("27 Jan 1911");
    expect(formatPartialDate("1949-06", "ja")).toBe("1949年6月");
  });

  it("compresses deep time but keeps recent centuries apart", () => {
    const s = timeScale(-7460, 2026, 1000);
    expect(s.x(-7460)).toBeCloseTo(0);
    expect(s.x(2026)).toBeCloseTo(1000);
    expect(1000 - s.x(2000)).toBeLessThan(100); // the satellite era is a short tail
    expect(s.x(1965) - s.x(1911)).toBeGreaterThan(20); // Taal 1911 and 1965 are distinct marks
    const t = ticks(s, 48);
    expect(t).toContain(2000);
    for (let i = 1; i < t.length; i++) expect(s.x(t[i]!) - s.x(t[i - 1]!)).toBeGreaterThanOrEqual(48);
  });

  it("lists impacts oldest first, with their eruption or none", () => {
    const v: DeepTimeVolcano = {
      id: "mayon",
      gvpNumber: 273030,
      eruptions: [{ id: "gvp-1", start: "1814-02-01", end: null, certainty: "confirmed", vei: 4, url: "https://x", impacts: [{ id: "hazel-1", date: "1814-02-01", deaths: 1200, url: "https://n" }] }],
      otherImpacts: [{ id: "hazel-2", date: "1875", deathsOrder: 4, url: "https://n" }],
    };
    const rows = impactRows(v);
    expect(rows.map((r) => [r.impact.id, r.eruption?.id ?? null])).toEqual([
      ["hazel-1", "gvp-1"],
      ["hazel-2", null],
    ]);
    expect(deathsForBar(rows[1]!.impact)).toBe(1001);
  });
});
