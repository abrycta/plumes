import { describe, expect, it } from "vitest";

import { addDays, formatDate, formatRange, monthTicks, tickLabel, yearlyTicks } from "./dates";
import { flToKm, formatNumber } from "./format";

describe("dates", () => {
  it("formats full and partial dates in both languages", () => {
    expect(formatDate("2020-01-12", "en")).toBe("12 Jan 2020");
    expect(formatDate("2020-01-12", "ja")).toBe("2020年1月12日");
    expect(formatDate("2020-01", "en")).toBe("Jan 2020");
    expect(formatDate("1911", "ja")).toBe("1911年");
    expect(formatDate("-3580", "en")).toBe("3581 BCE");
  });
  it("formats ranges", () => {
    expect(formatRange("2020-01-12", "2020-01-26", "en")).toBe("12–26 Jan 2020");
    expect(formatRange("2020-01-12", "2020-01-26", "ja")).toBe("2020年1月12日〜26日");
    expect(formatRange("2019-12-01", "2020-02-15", "en")).toBe("1 Dec 2019 – 15 Feb 2020");
  });
  it("does day arithmetic across years", () => {
    expect(addDays("2019-12-31", 1)).toBe("2020-01-01");
    expect(addDays("2020-03-01", -1)).toBe("2020-02-29");
  });
  it("month ticks and labels", () => {
    expect(monthTicks("2019-12-01", "2020-02-15")).toEqual(["2019-12-01", "2020-01-01", "2020-02-01"]);
    expect(monthTicks("2000-01-15", "2026-10-21", 8).length).toBeLessThanOrEqual(8);
    expect(monthTicks("2000-01-01", "2026-10-22", 8)).toEqual(["2000-01-01", "2004-01-01", "2008-01-01", "2012-01-01", "2016-01-01", "2020-01-01", "2024-01-01"]);
    expect(yearlyTicks(monthTicks("2000-01-01", "2026-10-22", 8))).toBe(true);
    expect(yearlyTicks(monthTicks("2019-12-01", "2020-02-15"))).toBe(false);
    expect(tickLabel("2004-01-01", "ja", true, true)).toBe("2004年");
    expect(tickLabel("2020-02-01", "en", false)).toBe("Feb");
    expect(tickLabel("2020-01-01", "ja", false)).toBe("2020年1月");
  });
  it("numbers", () => {
    expect(formatNumber(318177, "en", 0)).toBe("318,177");
    expect(flToKm(550)).toBe(16.764);
  });
});
