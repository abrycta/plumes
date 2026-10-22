// Earth Engine run A on the volcano page (LAYERS-PLAN §7 steps 4-6): crater-lake temperature, crater-lake area and
// colour, and the TROPOMI UV aerosol index in eruption windows. The series arrive as ordinary `events` entries, so the
// timeline already draws them; this module adds their instrument wording, column labels, groups and the lake-colour
// strip's data. Pure functions (unit-tested). Wiring into tracks.ts is a follow-up (two spreads and one group check),
// kept out of this change so other M2 work on tracks.ts does not conflict.

import type { LocalText, SparseSeries, VolcanoReadModel } from "@contracts/readmodels";

export type RunAGroupId = "lake" | "aerosol";

export const RUN_A_GROUPS: { id: RunAGroupId; title: LocalText }[] = [
  { id: "lake", title: { en: "Crater lake", ja: "火口湖" } },
  {
    id: "aerosol",
    title: {
      en: "Ash and haze around eruptions",
      ja: "噴火前後の火山灰ともや",
    },
  },
];

/** Instrument wording per source id (RESEARCH.md §9 rule 3), for sources run A adds. */
export const RUN_A_INSTRUMENTS: Record<string, LocalText> = {
  "jrc-global-surface-water": {
    en: "JRC Global Surface Water, monthly water map from Landsat (30 m; ends Dec 2021)",
    ja: "JRC全球地表水、Landsatによる月別水域図(30 m、2021年12月まで)",
  },
  "s2-sr-harmonized": {
    en: "Sentinel-2 (satellite, every 5 days, cloud-free days only); colour is descriptive, not water chemistry",
    ja: "Sentinel-2(衛星、5日ごと、雲のない日のみ)。色は見た目で、水質ではない",
  },
  "s5p-offl-aer-ai": {
    en: "Sentinel-5P TROPOMI UV aerosol index (satellite, daily, no signal under cloud); ash, smoke and dust all score",
    ja: "Sentinel-5P TROPOMI 紫外吸収性エアロゾル指数(衛星、日別、雲の下は不可)。火山灰・煙・砂塵のいずれも反応する",
  },
};

/** Readout labels of run A's extra columns. */
export const RUN_A_COLUMNS: Record<string, LocalText> = {
  tempC: { en: "lake surface temperature", ja: "湖面温度" },
  validPx: { en: "clear water pixels", ja: "有効な水面画素" },
  uncertaintyK: { en: "uncertainty", ja: "不確かさ" },
  sensor: { en: "sensor", ja: "センサー" },
  areaKm2: { en: "water area", ja: "水面積" },
  observed: { en: "share of the crater observed", ja: "観測できた火口の割合" },
  colour: { en: "colour", ja: "色" },
  aiMax: { en: "highest index", ja: "最大指数" },
  aiMean: { en: "mean index", ja: "平均指数" },
  coverage: { en: "coverage", ja: "被覆率" },
};

/** The group of a run A series id, or null for any other series. */
export function runAGroup(id: string): RunAGroupId | null {
  if (id.startsWith("lake_")) return "lake";
  if (id.startsWith("uvai_")) return "aerosol";
  return null;
}

export interface LakeSwatch {
  date: string;
  colour: string;
  areaKm2: number;
}

/** The lake-colour strip: one swatch per cloud-free Sentinel-2 day with a lake, at most one per month (the first). */
export function lakeSwatches(model: VolcanoReadModel): LakeSwatch[] {
  const s: SparseSeries | undefined = model.events.lake_area_s2;
  if (!s) return [];
  const ci = s.cols.indexOf("colour");
  const ai = s.cols.indexOf("areaKm2");
  if (ci < 1 || ai < 1) return [];
  const seen = new Set<string>();
  const out: LakeSwatch[] = [];
  for (const r of s.rows) {
    const colour = r[ci];
    const area = r[ai];
    const date = String(r[0]);
    if (typeof colour !== "string" || !/^#[0-9a-f]{6}$/i.test(colour) || typeof area !== "number") continue;
    if (seen.has(date.slice(0, 7))) continue;
    seen.add(date.slice(0, 7));
    out.push({ date, colour, areaKm2: area });
  }
  return out;
}
