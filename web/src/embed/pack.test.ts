import { describe, expect, it } from "vitest";

import { fromPack, type PackState } from "./pack";

describe("pack", () => {
  it("keeps months outside a layer's record as not observed (a gap), never zero", () => {
    const p = {
      v: 1,
      state: { end: "2024-12", eruptions: [], quakes: 0 },
      totals: { thermal: 0, near: 0, quakes: 0, maxMag: 0 },
      counts: [
        ["2024-11", 1, 2, 3],
        ["2024-12", 0, 0, 0, 1],
        ["2025-01", 0, 0, 0, 3],
      ],
      activity: [],
      hexes: [],
      near: [],
      quakes: [],
    } as PackState;
    const c = fromPack(p).counts;
    expect(c[0]).toEqual({ month: "2024-11", thermalNear: 1, thermalFar: 2, quakes: 3 });
    expect(c[1]).toEqual({ month: "2024-12", thermalNear: 0, thermalFar: 0, quakes: 0, thermalObserved: false });
    expect(c[2]).toMatchObject({ thermalObserved: false, quakesObserved: false });
  });
});
