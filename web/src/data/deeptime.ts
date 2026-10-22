// Deep-time strip data (<version>/deeptime.json): loading, the compressed time axis and year labels.
// Optional file: a version without it (older data) or any load error gives null, and the strip is not shown.

import type { DeepTime, DeepTimeEruption, DeepTimeImpact, DeepTimeVolcano } from "@contracts/deeptime";

import type { Lang } from "@/lib/dates";

import { loadFile } from "./load";

let deepP: Promise<DeepTime | null> | null = null;
export function loadDeepTime(): Promise<DeepTime | null> {
  deepP ??= loadFile<DeepTime>("deeptime.json").catch(() => null);
  return deepP;
}

/** Year of a partial date; BCE years are negative (GVP and NCEI: -3580 is 3580 BCE, no year 0). */
export function yearOf(iso: string): number {
  const m = /^(-?\d{1,5})/.exec(iso);
  return m ? Number(m[1]) : NaN;
}

/** "1911", "3580 BCE" / "1911年", "紀元前3580年". */
export function formatYear(y: number, lang: Lang): string {
  if (y < 0) return lang === "ja" ? `紀元前${-y}年` : `${-y} BCE`;
  if (y < 1000) return lang === "ja" ? `紀元${y}年` : `${y} CE`;
  return lang === "ja" ? `${y}年` : String(y);
}

/** Like formatDate, but with GVP's BCE convention for negative years. */
export function formatPartialDate(iso: string, lang: Lang): string {
  const m = /^(-?\d{1,5})(?:-(\d{2}))?(?:-(\d{2}))?$/.exec(iso);
  if (!m) return iso;
  const y = Number(m[1]);
  if (y < 0 || !m[2]) return formatYear(y, lang);
  const mo = Number(m[2]);
  const d = m[3] ? Number(m[3]) : null;
  if (lang === "ja") return `${y}年${mo}月${d ? `${d}日` : ""}`;
  const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return `${d ? `${d} ` : ""}${MONTHS[mo - 1]} ${y}`;
}

// Years-before-the-end on a shifted log scale: recent centuries get room, the Holocene still fits.
// With C = 50, 2000 → now takes under a tenth of the width and 1500 → 2000 about a third.
const C = 50;

export interface TimeScale {
  x: (year: number) => number;
  start: number;
  end: number;
  width: number;
}

export function timeScale(startYear: number, endYear: number, width: number): TimeScale {
  const span = Math.log(endYear - startYear + C) - Math.log(C);
  const x = (year: number) => {
    const age = Math.min(Math.max(endYear - year, 0), endYear - startYear);
    return width * (1 - (Math.log(age + C) - Math.log(C)) / span);
  };
  return { x, start: startYear, end: endYear, width };
}

const TICK_PRIORITY = [2000, 1500, 1, -5000, 1800, 1000, -2500, -7500, 1900, 1700, 1600, 500, -1000, -10000, 1950];

/** Tick years inside the scale, at least `minGap` px apart, most useful first. */
export function ticks(s: TimeScale, minGap: number): number[] {
  const kept: number[] = [];
  for (const y of TICK_PRIORITY) {
    if (y < s.start || y > s.end) continue;
    if (kept.every((k) => Math.abs(s.x(k) - s.x(y)) >= minGap)) kept.push(y);
  }
  return kept.sort((a, b) => a - b);
}

export interface ImpactRow {
  impact: DeepTimeImpact;
  eruption: DeepTimeEruption | null;
}

/** Every HazEL event for a volcano, oldest first, with the GVP eruption it belongs to (null for later lahars and the like). */
export function impactRows(v: DeepTimeVolcano): ImpactRow[] {
  const rows: ImpactRow[] = [
    ...v.eruptions.flatMap((e) => (e.impacts ?? []).map((impact) => ({ impact, eruption: e }))),
    ...v.otherImpacts.map((impact) => ({ impact, eruption: null })),
  ];
  return rows.sort((a, b) => yearOf(a.impact.date) - yearOf(b.impact.date) || a.impact.date.localeCompare(b.impact.date));
}

/** Deaths of an impact for the strip's bars: the number, else the lower bound of NCEI's order class. */
export function deathsForBar(i: DeepTimeImpact): number {
  if (i.deaths != null) return i.deaths;
  if (i.deathsTotal != null) return i.deathsTotal;
  const o = i.deathsOrder ?? i.deathsTotalOrder;
  return o ? [0, 1, 51, 101, 1001][o]! : 0;
}
