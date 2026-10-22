// The /embed's sequence (workspace rule 27): the richest 12-month windows of the record, chosen from the data.
// Candidates are the window ending three months after each volcano's last eruption since 2000 and the latest window;
// windows ending within three months of each other merge; candidates are ranked by their earthquake count (the whole
// earthquake record is one file, so ranking costs nothing more), and the top few are shown in time order. Pure.

import type { VolcanoesIndex } from "@contracts/readmodels";

import { addMonths, WINDOW_MONTHS } from "../map/density";
import type { QuakePt } from "../map/points";

export interface EmbedState {
  /** The window's last month. */
  end: string;
  /** Volcanoes whose last eruption began in the window, with its month (oldest first). */
  eruptions: { id: string; month: string }[];
  /** Earthquakes in the window (the ranking). */
  quakes: number;
}

/** States shown at most. */
export const MAX_STATES = 4;
/** Months after an eruption's start that its window runs on. */
const AFTER = 3;

const monthsBetween = (a: string, b: string): number => {
  const [ya, ma] = a.split("-").map(Number) as [number, number];
  const [yb, mb] = b.split("-").map(Number) as [number, number];
  return yb * 12 + mb - (ya * 12 + ma);
};

export function chooseStates(index: VolcanoesIndex, record: readonly string[], quakes: readonly QuakePt[], max = MAX_STATES): EmbedState[] {
  const last = record.at(-1);
  if (!last) return [];
  const first = record[0]!;
  const eruptions = index.features
    .map((f) => ({ id: f.properties.id, month: (f.properties.lastEruption?.start ?? "").slice(0, 7) }))
    .filter((e) => /^\d{4}-\d{2}$/.test(e.month) && e.month >= "2000-01" && e.month >= first && e.month <= last);
  const ends = [...new Set([last, ...eruptions.map((e) => (addMonths(e.month, AFTER) > last ? last : addMonths(e.month, AFTER)))])].sort();
  // Merge ends within three months of each other into the later one.
  const merged: string[] = [];
  for (const e of ends) {
    if (merged.length && monthsBetween(merged.at(-1)!, e) <= 3) merged[merged.length - 1] = e;
    else merged.push(e);
  }
  const perMonth = new Map<string, number>();
  for (const q of quakes) perMonth.set(q.month, (perMonth.get(q.month) ?? 0) + 1);
  const states = merged.map((end) => {
    const start = addMonths(end, -(WINDOW_MONTHS - 1));
    let n = 0;
    for (let m = start; m <= end; m = addMonths(m, 1)) n += perMonth.get(m) ?? 0;
    return { end, eruptions: eruptions.filter((e) => e.month >= start && e.month <= end).sort((a, b) => a.month.localeCompare(b.month)), quakes: n };
  });
  return states
    .sort((a, b) => b.quakes - a.quakes || b.eruptions.length - a.eruptions.length || b.end.localeCompare(a.end))
    .slice(0, max)
    .sort((a, b) => a.end.localeCompare(b.end));
}
