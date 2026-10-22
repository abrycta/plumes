import { describe, expect, it } from "vitest";

import type { Layer, Layers, VolcanoesIndex } from "@contracts/readmodels";

import { defaultWindowMonths, deriveWindow, layerCoverage, recordMonths } from "./windowData";

const base = { title: { en: "", ja: "" }, sources: [] as string[], attribution: "" };
const thermal = { ...base, id: "thermal-detections", format: "pmtiles", url: "layers/thermal/{year}.pmtiles", time: { step: "month", start: "2025-01", end: "2026-03" } } as Layer;
const quakes = { ...base, id: "earthquakes-usgs", format: "pmtiles", url: "layers/earthquakes-usgs.pmtiles", time: { step: "month", start: "2024-12", end: "2026-02" } } as Layer;
const layers = { layers: [thermal, quakes] } as unknown as Layers;

describe("the map's first window (prefetched from main.tsx, then shown by MapPage)", () => {
  it("covers every layer's months up to the data's last day, oldest first", () => {
    const record = recordMonths(layers, "2026-02-14");
    expect(record[0]).toBe("2024-12");
    expect(record.at(-1)).toBe("2026-02");
    expect(new Set(record).size).toBe(record.length);
  });
  it("is the twelve months up to the record's last month", () => {
    const months = defaultWindowMonths(recordMonths(layers, "2026-02-14"));
    expect(months).toHaveLength(12);
    expect(months[0]).toBe("2025-03");
    expect(months.at(-1)).toBe("2026-02");
    expect(defaultWindowMonths([])).toEqual([]);
  });
});

describe("months outside a layer's record", () => {
  it("are not observed (a gap), never zero", () => {
    const index = { features: [] } as unknown as VolcanoesIndex;
    const d = deriveWindow(index, ["2024-12", "2025-01", "2026-03"], [], [], layerCoverage(layers));
    expect(d.counts.map((c) => [c.month, c.thermalObserved ?? true, c.quakesObserved ?? true])).toEqual([
      ["2024-12", false, true],
      ["2025-01", true, true],
      ["2026-03", true, false],
    ]);
  });
});
