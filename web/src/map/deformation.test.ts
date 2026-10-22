import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

import type { Layers } from "@contracts/readmodels";

import { colourise, decodeFrame, framePath, framesInView, imageCoordinates, NODATA, velocityDomain } from "./deformation";

const V = resolve(import.meta.dirname, "../../../contracts/fixtures/data/v0");
const layers = JSON.parse(readFileSync(resolve(V, "layers.json"), "utf8")) as Layers;
const layer = layers.layers.find((l) => l.id === "deformation-velocity")!;
const frame = layer.frames![0]!;

describe("deformation-velocity", () => {
  it("is in the fixture with one Taal frame and a symmetric domain", () => {
    expect(frame.volcanoId).toBe("taal");
    expect(framePath(layer, frame)).toBe("layers/deformation/taal-032D_07536_111313.tif");
    expect(velocityDomain(layer)).toBeGreaterThan(0);
    expect(imageCoordinates(frame)[0]).toEqual([frame.bounds[0], frame.bounds[3]]);
  });

  it("decodes the pipeline's GeoTIFF (deflate + predictor) to plausible mm/yr", async () => {
    const buf = readFileSync(resolve(V, framePath(layer, frame)));
    const d = await decodeFrame(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength));
    expect([d.width, d.height]).toEqual([100, 100]);
    const valid = [...d.values].filter((v) => v !== NODATA).map((v) => v / 10);
    expect(valid.length).toBeGreaterThan(500);
    expect(Math.max(...valid.map(Math.abs))).toBeLessThan(500);
  });

  it("selects frames in view", () => {
    expect(framesInView([frame], [120, 13, 122, 15])).toHaveLength(1);
    expect(framesInView([frame], [125, 10, 126, 11])).toHaveLength(0);
  });

  it("colours through the ramp, clamps, and leaves nodata transparent", () => {
    const ramp = ["#000000", "#111111", "#222222", "#808080", "#aaaaaa", "#cccccc", "#ffffff"];
    const px = colourise(
      {
        width: 4,
        height: 1,
        values: Int16Array.from([NODATA, -9999, 0, 9999]),
      },
      30,
      ramp,
    );
    expect([...px.slice(0, 4)]).toEqual([0, 0, 0, 0]);
    expect([...px.slice(4, 8)]).toEqual([0, 0, 0, 255]);
    expect([...px.slice(8, 12)]).toEqual([128, 128, 128, 255]);
    expect([...px.slice(12, 16)]).toEqual([255, 255, 255, 255]);
  });
});
