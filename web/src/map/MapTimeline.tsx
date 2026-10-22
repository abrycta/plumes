// The map's timeline strip: earthquakes per month over the whole record with the 12-month window marked, a range
// input that moves the window (native range: APG slider semantics, the app's scrubber pattern), and the window's
// months as paired bars (thermal detections near and far from a volcano, earthquakes). Token colours only.

import { Button, useLang, useT } from "@abrycta/akari/react";
import { useId } from "react";

import { formatNumber } from "@/lib/format";

import type { MonthCount } from "./density";
import { LAYER_BG, LAYER_TOKENS, layerVar } from "./layerColors";

const ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
function monthAbbr(m: string, lang: "en" | "ja"): string {
  const mo = Number(m.slice(5, 7));
  return lang === "ja" ? `${mo}月` : (ABBR[mo - 1] ?? m);
}

export interface MapTimelineProps {
  /** Every month of the record, oldest first. */
  record: string[];
  /** Earthquakes per month of `record` (null while loading). */
  recordQuakes: number[] | null;
  /** Index in `record` of the window's last month. */
  end: number;
  span: number;
  onEnd: (i: number) => void;
  /** The window's months (null while loading). */
  counts: MonthCount[] | null;
  formatMonth: (m: string, style?: "short" | "long") => string;
}

export function MapTimeline({ record, recordQuakes, end, span, onEnd, counts, formatMonth }: MapTimelineProps) {
  const t = useT();
  const { lang } = useLang();
  const id = useId();
  const n = record.length;
  const start = Math.max(0, end - span + 1);
  const qMax = Math.max(1, ...(recordQuakes ?? [0]));
  const cMax = Math.max(1, ...(counts ?? []).map((c) => Math.max(c.thermalObserved === false ? 0 : c.thermalNear + c.thermalFar, c.quakesObserved === false ? 0 : c.quakes)));
  // Months outside a layer's record: a shaded gap, never a zero bar (as on the volcano timeline).
  const notObserved = t("Not observed: outside this instrument's record", "観測なし(この観測機器の記録の範囲外)");
  const thermalGap = t("thermal detections not observed (outside this instrument's record)", "熱異常は観測なし(この観測機器の記録の範囲外)");
  const quakesGap = t("earthquakes not observed (outside this instrument's record)", "地震は観測なし(この観測機器の記録の範囲外)");
  const years = record.map((m, i) => [m, i] as const).filter(([m]) => m.endsWith("-01") && Number(m.slice(0, 4)) % 5 === 0);
  const windowLabel = `${formatMonth(record[start] ?? "", "short")} – ${formatMonth(record[end] ?? "", "short")}`;

  return (
    <figure className="m-0 flex flex-col gap-2" data-map-timeline>
      <figcaption className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <label htmlFor={id} className="text-ak-sm">
          {t("Window", "期間")}: <strong className="tabular">{windowLabel}</strong>
        </label>
        <span className="text-ak-xs text-muted-foreground">{t("Bars: earthquakes per month, whole record (USGS; square-root scale)", "棒:月ごとの地震数、全期間(USGS、平方根目盛)")}</span>
      </figcaption>
      <svg viewBox={`0 0 ${n} 40`} preserveAspectRatio="none" className="block h-10 w-full" aria-hidden="true">
        <rect x={start} y={0} width={end - start + 1} height={40} fill="var(--primary)" opacity={0.12} />
        {recordQuakes?.map((q, i) => (q ? <rect key={i} x={i + 0.1} y={40 - 36 * Math.sqrt(q / qMax)} width={0.8} height={36 * Math.sqrt(q / qMax)} fill={i >= start && i <= end ? layerVar(LAYER_TOKENS.depth[0]) : "var(--muted-foreground)"} /> : null))}
      </svg>
      <div className="relative h-4 text-ak-2xs text-muted-foreground" aria-hidden="true">
        {years.map(([m, i]) => (
          <span key={m} className="absolute top-0 -translate-x-1/2 font-mono" style={{ left: `${((i + 0.5) / n) * 100}%` }}>
            {m.slice(0, 4)}
          </span>
        ))}
      </div>
      <div className="flex items-center gap-2">
        <Button type="button" size="icon-sm" variant="outline" aria-label={t("One month earlier", "1か月前")} disabled={end <= span - 1} onClick={() => onEnd(end - 1)}>
          ‹
        </Button>
        <input
          id={id}
          type="range"
          className="range min-w-0 flex-1"
          min={Math.min(span - 1, n - 1)}
          max={n - 1}
          value={end}
          aria-valuetext={windowLabel}
          onChange={(e) => onEnd(Number(e.target.value))}
          data-testid="window-end"
        />
        <Button type="button" size="icon-sm" variant="outline" aria-label={t("One month later", "1か月後")} disabled={end >= n - 1} onClick={() => onEnd(end + 1)}>
          ›
        </Button>
      </div>
      <ol className="m-0 grid list-none grid-cols-12 gap-1 p-0" aria-label={t("The window, month by month", "期間の月ごとの件数")} data-window-months>
        {(counts ?? record.slice(start, end + 1).map((m): MonthCount => ({ month: m, thermalNear: 0, thermalFar: 0, quakes: 0 }))).map((c) => {
          const thermal = c.thermalNear + c.thermalFar;
          const thermalSeen = c.thermalObserved !== false;
          const quakesSeen = c.quakesObserved !== false;
          return (
            <li key={c.month} className="flex min-w-0 flex-col gap-1" data-not-observed={[!thermalSeen && "thermal", !quakesSeen && "quakes"].filter(Boolean).join(" ") || undefined}>
              <div className="flex h-12 items-end gap-0.5" aria-hidden="true">
                {thermalSeen ? (
                  <div className="flex h-full flex-1 flex-col justify-end">
                    <div className={`${LAYER_BG.thermal} opacity-30`} style={{ height: `${(100 * c.thermalFar) / cMax}%` }} />
                    <div className={LAYER_BG.thermal} style={{ height: `${(100 * c.thermalNear) / cMax}%` }} />
                  </div>
                ) : (
                  <div className="h-full flex-1 bg-muted opacity-70" title={notObserved} />
                )}
                {quakesSeen ? <div className={`flex-1 ${LAYER_BG.quakes}`} style={{ height: `${(100 * c.quakes) / cMax}%` }} /> : <div className="h-full flex-1 bg-muted opacity-70" title={notObserved} />}
              </div>
              <span className="truncate text-center font-mono text-ak-2xs text-muted-foreground">{monthAbbr(c.month, lang)}</span>
              <span className="sr-only">
                {t(
                  `${thermalSeen ? `${formatNumber(thermal, lang)} thermal detections (${formatNumber(c.thermalNear, lang)} near a volcano)` : thermalGap}, ${quakesSeen ? `${formatNumber(c.quakes, lang)} earthquakes` : quakesGap}`,
                  `${thermalSeen ? `熱異常${formatNumber(thermal, lang)}件(火山付近${formatNumber(c.thermalNear, lang)}件)` : thermalGap}、${quakesSeen ? `地震${formatNumber(c.quakes, lang)}件` : quakesGap}`,
                )}
              </span>
            </li>
          );
        })}
      </ol>
    </figure>
  );
}
