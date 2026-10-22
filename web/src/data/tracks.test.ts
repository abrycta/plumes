import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

import type { VolcanoReadModel } from "@contracts/readmodels";

import { periodsOf } from "./periods";
import { absentRecords, buildTracks, compact, dayOf, pickByRing, readAt, ringOptions, tracksForStep } from "./tracks";

const taal = JSON.parse(readFileSync(resolve(import.meta.dirname, "../../../contracts/fixtures/data/v0/volcano/taal.json"), "utf8")) as VolcanoReadModel;

describe("buildTracks (Taal fixture)", () => {
  const tracks = buildTracks(taal, 15);
  const byId = Object.fromEntries(tracks.map((t) => [t.id, t]));

  it("labels every track by instrument and links every PHIVOLCS, VAAC and DSWD point", () => {
    for (const t of tracks) expect(t.instrument.en.length, t.id).toBeGreaterThan(10);
    for (const id of ["alert", "advisories", "displacement"]) {
      expect(byId[id]!.linked).toBe(true);
      for (const p of byId[id]!.points) expect(p.url, `${id} ${p.date}`).toMatch(/^https:\/\//);
    }
  });

  it("alert levels are dated markers 'as reported', never extended past the last bulletin", () => {
    const a = byId.alert!;
    expect(a.kind).toBe("markers");
    expect(a.title.en).toContain("as reported by PHIVOLCS");
    expect(a.points.map((p) => [p.date, p.value])).toEqual([
      ["2020-01-12", 2],
      ["2020-01-13", 4],
    ]);
    expect(readAt(a, "2020-01-20")).toMatchObject({ status: "value", reportedOn: "2020-01-13" });
    expect(readAt(a, "2020-01-01").status).toBe("no-report");
  });

  it("keeps satellite gaps as null, never zero, and separates 'nothing detected' from 'not observed'", () => {
    const so2 = byId.so2_s5p_15km!;
    expect(so2.coverage).toBe("per-day");
    expect(readAt(so2, "2020-01-08").status).toBe("no-observation");
    expect(readAt(so2, "2019-12-15").status).toBe("outside");
    expect(readAt(byId.frp_modis_15km!, "2020-01-15").status).toBe("nothing-detected");
    expect(readAt(byId.fire_viirs_15km!, "2005-01-01").status).toBe("not-observed");
  });

  it("aggregates VAAC advisories to the day's highest ash top", () => {
    const p = byId.advisories!.points.find((x) => x.date === "2020-01-12")!;
    expect(p.value).toBe(550);
  });

  it("orders groups: alert, earthquakes, SO2, heat, eruptions, ash, people", () => {
    const order = [...new Set(tracks.map((t) => t.group))];
    expect(order).toEqual(["alert", "earthquakes", "so2", "thermal", "eruptions", "ash", "people"]);
  });

  it("picks one series per family by ring", () => {
    expect(ringOptions(taal)).toEqual([15, 30, 50]);
    expect(buildTracks(taal, 50).some((t) => t.id === "so2_s5p_50km")).toBe(true);
    expect(buildTracks(taal, 50).some((t) => t.id === "so2_s5p_15km")).toBe(false);
    expect(pickByRing([["eq_usgs_30km", { ringKm: 30 }]], 15).map((e) => e[0])).toEqual(["eq_usgs_30km"]);
  });

  it("maps story series names to tracks", () => {
    expect(tracksForStep({ series: ["bulletins", "so2_s5p_15km"] }, tracks).map((t) => t.id)).toEqual(["alert", "bulletin_eq", "so2_s5p_15km"]);
  });

  it("offers the whole record and each reading window as periods", () => {
    const ps = periodsOf(taal);
    expect(ps[0]).toMatchObject({ id: "all", from: "2019-12-01", to: "2020-02-15" });
    expect(ps[1]).toMatchObject({ from: "2020-01-05", to: "2020-02-02" });
  });
});

describe("small helpers", () => {
  it("dayOf turns partial GVP dates into days", () => {
    expect(dayOf("1911")).toBe("1911-01-01");
    expect(dayOf("2020-01")).toBe("2020-01-01");
    expect(dayOf("2020-01-12")).toBe("2020-01-12");
  });
  it("compact", () => {
    expect([compact(504265), compact(38203), compact(1500), compact(950)]).toEqual(["504k", "38k", "1.5k", "950"]);
  });
});

describe("absentRecords", () => {
  it("names every series a sparse volcano has nothing in, each with its specific reason", () => {
    const events = Object.fromEntries(Object.entries(taal.events).map(([k, v]) => [k, k.startsWith("eq") ? { ...v, rows: [] } : v]));
    const sparse = { ...taal, volcano: { ...taal.volcano, gvpNumber: null }, bulletins: null, advisories: null, displacement: null, events, episodes: [] } as unknown as VolcanoReadModel;
    const absent = absentRecords(sparse, buildTracks(sparse, 10));
    const ids = absent.map((a) => a.id);
    expect(ids).toEqual(expect.arrayContaining(["bulletins", "advisories", "eruptions", "displacement", "eq_usgs_30km"]));
    expect(absent.find((a) => a.id === "advisories")!.reason.en).toContain("GVP number");
    expect(absent.find((a) => a.id === "eq_usgs_30km")!.reason.en).toMatch(/^Nothing detected within 30 km from /);
    expect(absentRecords(taal, buildTracks(taal, 15)).map((a) => a.id)).not.toContain("bulletins");
  });
});
