// The /embed's volcano in focus for a window: the most recent eruption in it, otherwise the volcano with the most
// detections and earthquakes around it. Its own read model adds the facts the national layers can't give: SO₂ over
// the volcano (TROPOMI, weekly peaks for the sparkline) and the days with VIIRS heat near it. Pure and alias-free
// (the build plugin imports it in Node through pack.ts).

import type { VolcanoReadModel } from "@contracts/readmodels";

import { addMonths } from "../map/density";
import type { EmbedState } from "./states";

export interface Focus {
  id: string;
  /** TROPOMI SO₂ mass on clear pixels within 15 km (t): the window's weekly peaks, its peak day. */
  so2?: { weeks: (number | null)[]; peak: number; peakDate: string; ringKm: number };
  /** Days in the window with a VIIRS thermal detection within the ring. */
  viirs?: { days: number; ringKm: number };
  /** Week index of each eruption in the window (for the sparkline's markers). */
  eruptionWeeks: number[];
}

const DAY = 86_400_000;
const dayIndex = (iso: string) => Math.floor(Date.parse(`${iso.slice(0, 10)}T00:00:00Z`) / DAY);

/** The volcano in focus: the window's latest eruption, else the most active volcano (null when none is active). */
export function focusId(state: EmbedState, activity: readonly [string, number, number][]): string | null {
  const last = state.eruptions.at(-1);
  if (last) return last.id;
  const top = [...activity].sort((a, b) => b[1] + b[2] - (a[1] + a[2]))[0];
  return top ? top[0] : null;
}

/** The focus facts for the window ending `end` (12 months), from the volcano's read model; absent series are left out. */
export function focusFacts(id: string, model: VolcanoReadModel | null, state: EmbedState, months: number): Focus {
  const first = dayIndex(`${addMonths(state.end, -(months - 1))}-01`);
  const after = dayIndex(`${addMonths(state.end, 1)}-01`);
  const weekOf = (d: number) => Math.floor((d - first) / 7);
  const weeks = Math.ceil((after - first) / 7);
  const eruptionWeeks = state.eruptions.filter((e) => e.id === id).map((e) => weekOf(dayIndex(`${e.month}-15`)));
  const out: Focus = { id, eruptionWeeks };
  const so2 = model?.daily.so2_s5p_mass_15km;
  if (so2) {
    const s0 = dayIndex(so2.start);
    const w: (number | null)[] = Array.from({ length: weeks }, () => null);
    let peak = -1;
    let peakDay = 0;
    for (let d = Math.max(first, s0); d < after; d++) {
      const v = so2.values[d - s0];
      if (v == null) continue;
      const k = weekOf(d);
      w[k] = Math.max(w[k] ?? 0, v);
      if (v > peak) [peak, peakDay] = [v, d];
    }
    if (peak > 0) out.so2 = { weeks: w.map((v) => (v == null ? null : Math.round(v))), peak: Math.round(peak), peakDate: new Date(peakDay * DAY).toISOString().slice(0, 10), ringKm: so2.ringKm ?? 15 };
  }
  const viirs = model?.events.frp_viirs_15km;
  if (viirs) {
    const days = new Set(viirs.rows.map((r) => dayIndex(r[0])).filter((d) => d >= first && d < after)).size;
    if (days) out.viirs = { days, ringKm: viirs.ringKm ?? 15 };
  }
  return out;
}
