import { describe, expect, it } from "vitest";

import type { VolcanoesIndex } from "@contracts/readmodels";

import { chooseStates } from "./states";

const volcano = (id: string, start: string) => ({ type: "Feature" as const, geometry: { type: "Point" as const, coordinates: [121, 14] as [number, number] }, properties: { id, name: { en: id, ja: id }, observatory: true, coverage: "deep" as const, lastEruption: { start }, file: "" } });
const index = { features: [volcano("taal", "2024-04-12"), volcano("kanlaon", "2024-10-19"), volcano("mayon", "2026-01-06"), volcano("old", "1911-01-30")] } as unknown as VolcanoesIndex;
const record = Array.from({ length: 34 }, (_, i) => `${2024 + Math.floor(i / 12)}-${String((i % 12) + 1).padStart(2, "0")}`);
const q = (month: string, n: number) => Array.from({ length: n }, () => ({ lon: 121, lat: 14, month, mag: 4, depth: 10 }));

describe("chooseStates", () => {
  it("picks eruption windows and the latest window, merged, ranked by earthquakes, in time order", () => {
    const states = chooseStates(index, record, [...q("2024-11", 50), ...q("2026-09", 5)], 2);
    expect(states.map((s) => s.end)).toEqual(["2025-01", "2026-10"]);
    expect(states[0]!.eruptions.map((e) => e.id)).toEqual(["taal", "kanlaon"]);
  });
  it("never returns an empty sequence when there is a record", () => {
    expect(chooseStates(index, ["2020-01"], [])).toHaveLength(1);
  });
});
