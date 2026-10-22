import { describe, expect, it } from "vitest";

import { activityByVolcano, depthClass, hexbin, monthlyCounts, nearestKm, windowMonths } from "./density";

describe("density helpers", () => {
  it("windows end on the given month and cross years", () => {
    expect(windowMonths("2026-02", 4)).toEqual(["2025-11", "2025-12", "2026-01", "2026-02"]);
    expect(windowMonths("2026-10")).toHaveLength(12);
  });
  it("bins nearby points together and far points apart", () => {
    const hexes = hexbin([
      { lon: 121, lat: 14 },
      { lon: 121.01, lat: 14.01 },
      { lon: 124, lat: 10 },
    ]);
    expect(hexes.map((h) => h.count).sort()).toEqual([1, 2]);
    expect(hexes[0]!.ring).toHaveLength(7);
  });
  it("classes depth and finds the nearest volcano", () => {
    expect([depthClass(null), depthClass(10), depthClass(100), depthClass(500)]).toEqual([0, 0, 1, 2]);
    expect(nearestKm(121, 14.1, [{ id: "taal", lon: 121, lat: 14 }])).toBeCloseTo(11.06, 1);
  });
  it("counts activity and months", () => {
    const v = [{ id: "taal", lon: 121, lat: 14 }];
    const thermal = [
      { lon: 121.05, lat: 14, month: "2020-01", frp: 1, type: 0, near: true },
      { lon: 123, lat: 14, month: "2020-01", frp: 1, type: 0, near: false },
    ];
    const quakes = [{ lon: 121.1, lat: 14.1, month: "2020-02", mag: 4.2, depth: 10 }];
    expect(activityByVolcano(v, thermal, quakes).get("taal")).toEqual({ thermal: 1, quakes: 1, maxMag: 4.2 });
    expect(monthlyCounts(["2020-01", "2020-02"], thermal, quakes)).toEqual([
      { month: "2020-01", thermalNear: 1, thermalFar: 1, quakes: 0 },
      { month: "2020-02", thermalNear: 0, thermalFar: 0, quakes: 1 },
    ]);
    // Months outside a layer's record are flagged not observed (a gap), never counted as zero.
    expect(monthlyCounts(["2020-01", "2020-02"], thermal, quakes, { thermal: new Set(["2020-01"]), quakes: null })).toEqual([
      { month: "2020-01", thermalNear: 1, thermalFar: 1, quakes: 0 },
      { month: "2020-02", thermalNear: 0, thermalFar: 0, quakes: 1, thermalObserved: false },
    ]);
  });
});
