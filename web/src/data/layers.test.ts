import { describe, expect, it } from "vitest";

import type { Layer } from "@contracts/readmodels";

import { filtersByMonth, layerMonths, layerPath } from "./layers";

const base = { title: { en: "", ja: "" }, sources: [] as string[], attribution: "" };
const thermal = { ...base, id: "thermal-detections", format: "pmtiles", url: "layers/thermal/{year}.pmtiles", time: { step: "month", start: "2025-11", end: "2026-02" }, properties: { month: "YYYY-MM" } } as Layer;
const fixture = { ...base, id: "thermal-detections", format: "geojson", url: "layers/thermal/{month}.geojson", time: { step: "month", start: "2000-11", end: "2026-09", available: ["2020-01"] } } as Layer;

describe("layers", () => {
  it("lists the months of a published layer and of the fixture", () => {
    expect(layerMonths(thermal)).toEqual(["2025-11", "2025-12", "2026-01", "2026-02"]);
    expect(layerMonths(fixture)).toEqual(["2020-01"]);
  });
  it("finds the file for a month and filters yearly files by month", () => {
    expect(layerPath(thermal, "2020-01")).toBe("layers/thermal/2020.pmtiles");
    expect(filtersByMonth(thermal)).toBe(true);
    expect(layerPath(fixture, "2020-01")).toBe("layers/thermal/2020-01.geojson");
    expect(filtersByMonth(fixture)).toBe(false);
  });
});
