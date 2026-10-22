import { describe, expect, it } from "vitest";

import type { VolcanoReadModel } from "@contracts/readmodels";

import { focusFacts, focusId } from "./focus";

const state = {
  end: "2024-12",
  eruptions: [
    { id: "taal", month: "2024-04" },
    { id: "kanlaon", month: "2024-10" },
  ],
  quakes: 0,
};
// Daily SO₂ from 2023-12-25: nulls before the window (2024-01 … 2024-12), a peak on 2024-10-03, one value after it.
const so2 = Array.from({ length: 400 }, (_, i) => (i === 7 + 276 ? 50 : i >= 7 && i < 7 + 366 ? 1 : 999));
const model = {
  daily: {
    so2_s5p_mass_15km: {
      source: ["s5p"],
      unit: "t",
      label: { en: "", ja: "" },
      start: "2023-12-25",
      ringKm: 15,
      values: so2,
    },
  },
  events: {
    frp_viirs_15km: {
      source: ["viirs"],
      label: { en: "", ja: "" },
      cols: ["date", "maxFrpMw", "n"],
      units: {},
      ringKm: 15,
      rows: [
        ["2023-12-31", 1, 1],
        ["2024-06-01", 2, 1],
        ["2024-06-01", 3, 2],
        ["2024-11-30", 4, 1],
        ["2025-01-01", 5, 1],
      ],
    },
  },
} as unknown as VolcanoReadModel;

describe("focus", () => {
  it("is the window's latest eruption, else the most active volcano", () => {
    expect(focusId(state, [])).toBe("kanlaon");
    expect(
      focusId({ ...state, eruptions: [] }, [
        ["mayon", 3, 1],
        ["taal", 1, 9],
      ]),
    ).toBe("taal");
    expect(focusId({ ...state, eruptions: [] }, [])).toBeNull();
  });
  it("keeps only the window: SO₂ weekly peaks and the peak day, VIIRS days", () => {
    const f = focusFacts("kanlaon", model, state, 12);
    expect(f.so2?.peak).toBe(50);
    expect(f.so2?.peakDate).toBe("2024-10-03");
    expect(f.so2?.weeks).toHaveLength(53);
    expect(Math.max(...(f.so2?.weeks ?? []).map((v) => v ?? 0))).toBe(50);
    expect(f.viirs?.days).toBe(2);
    expect(f.eruptionWeeks).toEqual([41]);
  });
  it("leaves out what the read model lacks", () => {
    expect(focusFacts("x", null, state, 12)).toEqual({
      id: "x",
      eruptionWeeks: [],
    });
  });
});
