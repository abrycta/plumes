import { describe, expect, it } from "vitest";

import { normalQuery, roundCoord } from "../../functions/api/[[path]].ts";

const NEAREST = ["lat", "lon", "limit"];
const EVENTS = [
  "volcano",
  "lat",
  "lon",
  "radiusKm",
  "from",
  "to",
  "kind",
  "limit",
];

describe("edge cache key: lat/lon rounding", () => {
  it("rounds to 2 decimals so nearby points share one key", () => {
    const a = normalQuery("?lat=14.0021&lon=120.9934", NEAREST);
    const b = normalQuery("?lon=120.99&lat=14.004&utm=x", NEAREST);
    expect(a).toBe("?lat=14&lon=120.99");
    expect(b).toBe(a);
  });

  it("keeps the other parameters and the fixed order", () => {
    expect(
      normalQuery(
        "?to=2020-02-15&lon=121.0049&from=2019-12-01&lat=14.009&radiusKm=30",
        EVENTS,
      ),
    ).toBe("?from=2019-12-01&lat=14.01&lon=121&radiusKm=30&to=2020-02-15");
    expect(
      normalQuery("?volcano=taal&from=2019-12-01&to=2020-01-01", EVENTS),
    ).toBe("?from=2019-12-01&to=2020-01-01&volcano=taal");
  });

  it("writes no negative zero and drops trailing zeros", () => {
    expect(roundCoord("-0.001", 90)).toBe("0");
    expect(roundCoord("14.00", 90)).toBe("14");
    expect(roundCoord("-13.256", 90)).toBe("-13.26");
    expect(roundCoord("+.5", 90)).toBe("0.5");
  });

  it("passes invalid or out-of-range values through, so the origin still answers 400", () => {
    for (const v of [
      "",
      "abc",
      "1e2",
      "0x10",
      "Infinity",
      "NaN",
      "14,5",
      " 14",
    ])
      expect(roundCoord(v, 90)).toBe(v);
    expect(roundCoord("90.004", 90)).toBe("90.004");
    expect(roundCoord("-180.001", 180)).toBe("-180.001");
    expect(roundCoord("89.996", 90)).toBe("90");
    expect(roundCoord("179.999", 180)).toBe("180");
  });

  it("leaves routes without coordinates untouched", () => {
    expect(
      normalQuery("?minVei=3&days=30&lat=14.123", [
        "minVei",
        "days",
        "radiusKm",
        "since",
      ]),
    ).toBe("?days=30&minVei=3");
  });
});
