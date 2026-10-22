import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

import type { SparseSeries, VolcanoReadModel } from "@contracts/readmodels";

import { lakeSwatches, RUN_A_COLUMNS, RUN_A_INSTRUMENTS, runAGroup } from "./craterLake";
import { eventsTrack } from "./tracks";

const taal = JSON.parse(readFileSync(resolve(import.meta.dirname, "../../../contracts/fixtures/data/v0/volcano/taal.json"), "utf8")) as VolcanoReadModel;

// The shape plumes.run_a.lake_area_series writes (pipeline/tests/test_run_a.py checks it against the contract).
const lakeS2: SparseSeries = {
  source: ["s2-sr-harmonized"],
  label: {
    en: "Taal Main Crater Lake: water area and colour (Sentinel-2)",
    ja: "タール火山主火口湖:水面積と色(Sentinel-2)",
  },
  cols: ["date", "areaKm2", "observed", "colour"],
  units: { areaKm2: "km²" },
  start: "2017-03-28",
  rows: [
    ["2019-12-01", 1.12, 1, "#3f6b4a"],
    ["2019-12-11", 1.1, 0.95, "#3f6b4b"],
    ["2020-02-10", 0, 1, null],
    ["2021-02-15", 0.25, 0.99, "#5a8a3c"],
    ["2021-03-01", 0.3, 0.99, "not-a-colour"],
  ],
};
const model: VolcanoReadModel = {
  ...taal,
  events: { ...taal.events, lake_area_s2: lakeS2 },
};

describe("crater lake (run A)", () => {
  it("one swatch a month, only days with a lake and a valid colour", () => {
    expect(lakeSwatches(model)).toEqual([
      { date: "2019-12-01", colour: "#3f6b4a", areaKm2: 1.12 },
      { date: "2021-02-15", colour: "#5a8a3c", areaKm2: 0.25 },
    ]);
    expect(lakeSwatches(taal)).toEqual([]);
  });

  it("groups run A series and leaves the others alone", () => {
    expect(["lake_temp_landsat", "lake_area_gsw", "lake_area_s2", "uvai_s5p_15km", "so2_s5p_15km"].map(runAGroup)).toEqual([
      "lake",
      "lake",
      "lake",
      "aerosol",
      null,
    ]);
  });

  it("every run A source and column has wording in both languages", () => {
    for (const x of [...Object.values(RUN_A_INSTRUMENTS), ...Object.values(RUN_A_COLUMNS)]) {
      expect(x.en.length).toBeGreaterThan(2);
      expect(x.ja.length).toBeGreaterThan(0);
    }
    for (const c of lakeS2.cols.slice(1)) expect(RUN_A_COLUMNS[c], c).toBeDefined();
  });

  it("the generic timeline draws the area and keeps the colour in the readout", () => {
    const tr = eventsTrack("lake_area_s2", lakeS2);
    expect(tr.unit).toBe("km²");
    expect(tr.points[0]!.value).toBe(1.12);
    expect(tr.points[0]!.extra?.map((e) => e.value)).toEqual(["1", "#3f6b4a"]);
  });
});
