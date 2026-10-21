import type { VolcanoReadModel } from "@contracts/readmodels";

import { addDays, formatRange, toDay } from "@/lib/dates";

import { dayOf } from "./tracks";

export interface Period {
  id: string;
  from: string;
  to: string;
  label: { en: string; ja: string };
}

/** The whole record, then each reading window and alert window (padded a week each side, clipped to the span). */
export function periodsOf(model: VolcanoReadModel): Period[] {
  const { start, end } = model.span;
  const out: Period[] = [{ id: "all", from: start, to: end, label: { en: `Whole record, ${formatRange(start, end, "en")}`, ja: `記録全体(${formatRange(start, end, "ja")})` } }];
  const clip = (d: string) => (d < start ? start : d > end ? end : d);
  const windows = [...model.readings.map((r) => [r.start, r.end] as const), ...model.episodes.filter((e) => e.kind === "alert_window" && e.end).map((e) => [dayOf(e.start), dayOf(e.end!)] as const)];
  for (const [a, b] of windows) {
    const from = clip(addDays(a, -7));
    const to = clip(addDays(b, 7));
    if (toDay(to) - toDay(from) < 2 || out.some((p) => p.from === from && p.to === to)) continue;
    out.push({ id: `${a}`, from, to, label: { en: formatRange(a, b, "en"), ja: formatRange(a, b, "ja") } });
  }
  return out;
}

