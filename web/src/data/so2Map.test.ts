import { readFileSync } from "node:fs";

import { describe, expect, it } from "vitest";

import type { Layer } from "@contracts/readmodels";

import { layerMonths, layerPath } from "./layers";
import { classOf, corners, decodeSo2, so2Rgba, so2Stops, SO2_STOPS, validShare } from "./so2Map";

// Written by the pipeline's own GeoTIFF writer (pipeline/plumes/geotiff.py): 3 x 2 pixels over 120.0-120.3 E, 10.0-10.2 N.
// so2 = [[10, 30, 60], [nodata, 450, 120]] µmol/m²; valid = [[100, 50, 5], [0, 80, 100]] %.
function fixture(): ArrayBuffer {
  const b = readFileSync(new URL("./fixtures/so2-tiny.tif", import.meta.url));
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength);
}

const layer = {
  id: "so2-monthly",
  title: { en: "", ja: "" },
  format: "cog",
  url: "layers/so2/{month}.tif",
  time: { step: "month", start: "2018-12", end: "2019-02" },
  legend: { unit: "µmol/m²", stops: [[25, "≥ 25"], [50, "≥ 50"], [100, "≥ 100"], [200, "≥ 200"], [400, "≥ 400"]] },
  sources: ["s5p-offl-so2"],
  attribution: "",
} as Layer;

describe("so2Map", () => {
  it("decodes the pipeline's GeoTIFF: size, bounds, both bands and nodata", async () => {
    const g = await decodeSo2(fixture());
    expect([g.width, g.height]).toEqual([3, 2]);
    g.bounds.forEach((v, i) => expect(v).toBeCloseTo([120, 10, 120.3, 10.2][i]!, 9));
    expect([...g.so2]).toEqual([10, 30, 60, -32768, 450, 120]);
    expect([...g.valid]).toEqual([100, 50, 5, 0, 80, 100]);
    expect(g.nodata).toBe(-32768);
  });

  it("colours by class and leaves nodata, low-coverage and below-scale pixels transparent", async () => {
    const g = await decodeSo2(fixture());
    const colours = ["#000001", "#000002", "#000003", "#000004", "#000005"];
    const px = so2Rgba(g, colours, so2Stops(layer));
    const alphaBlue = (i: number) => [px[i * 4 + 3], px[i * 4 + 2]];
    expect(alphaBlue(0)).toEqual([0, 0]); // 10 < 25
    expect(alphaBlue(1)).toEqual([200, 1]); // 30 -> class 0
    expect(alphaBlue(2)).toEqual([0, 0]); // 60 but only 5 % valid days
    expect(alphaBlue(3)).toEqual([0, 0]); // nodata
    expect(alphaBlue(4)).toEqual([200, 5]); // 450 -> top class
    expect(alphaBlue(5)).toEqual([200, 3]); // 120 -> class 2
  });

  it("reads classes from the layer, else the defaults; months and files from the contract url", () => {
    expect(so2Stops(layer)).toEqual([25, 50, 100, 200, 400]);
    expect(so2Stops(undefined)).toEqual(SO2_STOPS);
    expect(classOf(24, SO2_STOPS)).toBe(-1);
    expect(classOf(25, SO2_STOPS)).toBe(0);
    expect(classOf(9999, SO2_STOPS)).toBe(4);
    expect(layerMonths(layer)).toEqual(["2018-12", "2019-01", "2019-02"]);
    expect(layerPath(layer, "2019-01")).toBe("layers/so2/2019-01.tif");
  });

  it("reports the month's coverage and the image corners", async () => {
    const g = await decodeSo2(fixture());
    expect(validShare(g)).toBeCloseTo((100 + 50 + 5 + 0 + 80 + 100) / 6 / 100, 6);
    expect(corners([116, 4, 128, 22])).toEqual([
      [116, 22],
      [128, 22],
      [128, 4],
      [116, 4],
    ]);
  });
});
