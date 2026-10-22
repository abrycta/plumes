import { describe, expect, it } from "vitest";

import type { Track } from "@/data/tracks";

import { markersFor, SNPP_END } from "./markers";

const base = { title: { en: "", ja: "" }, instrument: { en: "", ja: "" }, unit: "", sources: [], coverage: "not-reported", linked: false } as const;
const line = (id: string, start: string, values: (number | null)[]): Track => ({
  ...base,
  id,
  group: "other",
  kind: "line",
  start,
  end: `${start.slice(0, 8)}${String(Number(start.slice(8)) + values.length - 1).padStart(2, "0")}`,
  points: values.map((value, i) => ({ date: `${start.slice(0, 8)}${String(Number(start.slice(8)) + i).padStart(2, "0")}`, value })),
});
const eruptions: Track = { ...base, id: "eruptions", group: "eruptions", kind: "spans", points: [{ date: "2020-01-12", end: "2020-01-22", value: null, mark: "VEI 4" }] };

describe("timeline event markers", () => {
  it("puts the NOAA-20 sensor change on VIIRS rows only", () => {
    const viirs = { ...line("fire_viirs_15km", "2026-10-01", [1]), kind: "bars" as const };
    expect(markersFor(viirs, [viirs], "en")).toEqual([expect.objectContaining({ at: SNPP_END, kind: "sensor-change", label: "NOAA-20" })]);
    expect(markersFor(line("frp_modis_15km", "2026-10-01", [1]), [], "en")).toEqual([]);
  });
  it("puts GVP eruption dates on deformation and rain rows, not on SO₂", () => {
    const rain = line("rain_imerg_15km", "2020-01-01", [1, 2]);
    expect(markersFor(rain, [rain, eruptions], "en")).toEqual([{ at: "2020-01-12", end: "2020-01-22", label: "Eruption", description: "Eruption (GVP), VEI 4" }]);
    expect(markersFor(line("so2_s5p_15km", "2020-01-01", [1]), [eruptions], "en")).toEqual([]);
  });
  it("shades the days the crater lake was gone on lake rows", () => {
    const area = line("lake_area", "2020-01-10", [5, 0, 0, null, 0, 2]);
    const temp = line("lake_temp_landsat", "2020-01-10", [30, null, null, null, null, 31]);
    expect(markersFor(temp, [temp, area], "en")).toEqual([expect.objectContaining({ at: "2020-01-11", end: "2020-01-14", kind: "gap", label: "Lake gone" })]);
  });
  it("marks the OMI / TROPOMI overlap on both SO₂ rows", () => {
    const omi = line("so2_omi_box", "2020-01-01", [1, 1, 1, 1, 1]);
    const s5p = line("so2_s5p_15km", "2020-01-03", [2, 2, 2, 2, 2]);
    for (const t of [omi, s5p]) expect(markersFor(t, [omi, s5p], "en")).toEqual([expect.objectContaining({ at: "2020-01-03", end: "2020-01-05", label: "OMI + TROPOMI" })]);
  });
});
