import { describe, expect, it } from "vitest";

import type { Layer, Layers } from "@contracts/readmodels";

import { defaultWindowMonths, recordMonths } from "./windowData";

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
