import { EventMarkerGroup, type EventMarker, eventMarkersSummary, layoutEventMarkers, useLang, useT } from "@abrycta/akari/react";
import { type PointerEvent, useEffect, useRef, useState } from "react";

import { DataThrough } from "@/components/DataThrough";
import { GROUPS, observedShare, type Track, valuesIn } from "@/data/tracks";
import { addDays, formatDate, fromDay, monthTicks, tickLabel, toDay, yearlyTicks } from "@/lib/dates";
import { formatNumber, formatPercent, unitLabel } from "@/lib/format";
import { safeHref } from "@/app/safeHref";
import { sourceLine } from "@/volcano/sourceLine";

import { markersFor } from "./markers";

const LINE_H = 56;
const BAR_H = 44;
const MARK_H = 30;

function heightOf(t: Track): number {
  return t.kind === "line" ? LINE_H + (t.coverage === "per-day" ? 8 : 0) : t.kind === "bars" ? BAR_H : MARK_H;
}

/** Width of an element, tracked with ResizeObserver. */
function useWidth<T extends HTMLElement>(): [React.RefObject<T | null>, number] {
  const ref = useRef<T>(null);
  const [w, setW] = useState(0);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver(([e]) => setW(Math.floor(e!.contentRect.width)));
    ro.observe(el);
    setW(Math.floor(el.getBoundingClientRect().width));
    return () => ro.disconnect();
  }, []);
  return [ref, w];
}

interface Scale {
  from: number;
  days: number;
  w: number;
  x: (iso: string) => number;
  dayW: number;
}

function makeScale(from: string, to: string, w: number): Scale {
  const a = toDay(from);
  const days = toDay(to) - a + 1;
  const dayW = w / days;
  return { from: a, days, w, dayW, x: (iso) => (toDay(iso) - a) * dayW };
}

function TrackPlot({ track, s, from, to, cursor, lang, highlight, markers }: { track: Track; s: Scale; from: string; to: string; cursor: string; lang: "en" | "ja"; highlight?: [string, string]; markers?: EventMarker[] }) {
  const h = heightOf(track);
  const fromD = toDay(from);
  const toD = toDay(to);
  const inRange = track.points.filter((p) => toDay(p.end ?? p.date) >= fromD && toDay(p.date) <= toD);
  const vals = valuesIn(track, from, to);
  const max = Math.max(0, ...vals);
  const min = Math.min(0, ...vals);
  const plotH = track.kind === "line" ? LINE_H - 6 : BAR_H - 4;
  const y = (v: number) => 3 + (max === min ? plotH : ((max - v) / (max - min)) * plotH);
  const cx = s.x(cursor) + s.dayW / 2;
  const els: React.ReactNode[] = [];

  // Days the series does not cover: shaded, never drawn as zero.
  const cover: [number, number][] = [];
  if (track.kind === "line" && track.start && track.end) {
    if (toDay(track.start) > fromD) cover.push([fromD, Math.min(toDay(track.start), toD + 1)]);
    if (toDay(track.end) < toD) cover.push([Math.max(toDay(track.end) + 1, fromD), toD + 1]);
  } else if (track.kind === "bars") {
    if (track.start && toDay(track.start) > fromD) cover.push([fromD, Math.min(toDay(track.start), toD + 1)]);
    if (track.end && toDay(track.end) < toD) cover.push([Math.max(toDay(track.end) + 1, fromD), toD + 1]);
  }
  if (highlight) {
    const a = Math.max(toDay(highlight[0]), fromD);
    const b = Math.min(toDay(highlight[1]), toD);
    if (b >= a) els.push(<rect key="hl" x={(a - fromD) * s.dayW} y={0} width={(b - a + 1) * s.dayW} height={h} fill="var(--primary)" opacity={0.1} />);
  }
  cover.forEach(([a, b], i) => els.push(<rect key={`c${i}`} x={(a - fromD) * s.dayW} y={0} width={(b - a) * s.dayW} height={h} fill="var(--muted)" opacity={0.7} />));

  if (track.kind === "line") {
    if (min < 0) els.push(<line key="zero" x1={0} x2={s.w} y1={y(0)} y2={y(0)} stroke="var(--border)" strokeWidth={1} />);
    let d = "";
    let run: [number, number][] = [];
    const flush = () => {
      if (run.length > 1) d += run.map(([px, py], i) => `${i ? "L" : "M"}${px.toFixed(1)} ${py.toFixed(1)}`).join("");
      else if (run.length === 1) els.push(<circle key={`p${run[0]![0]}`} cx={run[0]![0]} cy={run[0]![1]} r={2.5} fill="var(--chart-seq-4)" />);
      run = [];
    };
    for (const p of inRange) {
      if (p.value == null) flush();
      else run.push([s.x(p.date) + s.dayW / 2, y(p.value)]);
    }
    flush();
    if (d) els.push(<path key="line" d={d} fill="none" stroke="var(--chart-seq-4)" strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />);
    if (track.coverage === "per-day")
      for (const p of inRange)
        if (p.coverage != null) els.push(<rect key={`cv${p.date}`} x={s.x(p.date)} y={LINE_H + 2} width={Math.max(1, s.dayW - 0.5)} height={5} fill="var(--chart-seq-3)" opacity={Math.max(0.08, p.coverage)} />);
  } else if (track.kind === "bars") {
    const bw = Math.max(2, s.dayW - (s.dayW > 4 ? 2 : 0));
    for (const [i, p] of inRange.entries()) {
      if (p.value == null) continue;
      const top = y(p.value);
      els.push(<rect key={`${p.date}#${i}`} x={s.x(p.date) + (s.dayW - bw) / 2} y={top} width={bw} height={Math.max(1.5, y(0) - top)} rx={Math.min(2, bw / 2)} fill="var(--chart-seq-4)" />);
    }
    els.push(<line key="base" x1={0} x2={s.w} y1={y(0)} y2={y(0)} stroke="var(--border)" strokeWidth={1} />);
  } else if (track.kind === "spans") {
    for (const [i, p] of inRange.entries()) {
      const x0 = Math.max(0, s.x(p.date));
      const x1 = Math.min(s.w, s.x(p.end ?? p.date) + s.dayW);
      const label = `${p.mark ?? ""} · ${formatDate(p.date, lang)}${p.end ? ` – ${formatDate(p.end, lang)}` : ""}`;
      els.push(
        <a key={`${p.date}#${i}`} href={safeHref(p.url)} target="_blank" rel="noopener noreferrer" aria-label={`${label} (GVP)`}>
          <rect x={x0} y={7} width={Math.max(4, x1 - x0)} height={16} rx={2} fill="color-mix(in oklab, var(--seal) 18%, transparent)" stroke="var(--seal)" strokeWidth={1.5} />
          {x1 - x0 > 44 ? (
            <text x={x0 + 6} y={19} fontSize={11} fill="var(--foreground)">
              {p.mark}
            </text>
          ) : (
            <text x={Math.min(x1 + 4, s.w - 40)} y={19} fontSize={11} fill="var(--foreground)">
              {p.mark}
            </text>
          )}
        </a>,
      );
    }
  } else if (inRange.length * 18 > s.w) {
    // Too many dated markers to draw one by one (years of daily bulletins): one tick per pixel column, as tall as the
    // highest value there. Each marker stays dated and linked in the day readout beside the plot.
    const columns = new Map<number, number>();
    for (const p of inRange) {
      const c = Math.floor(s.x(p.date) + s.dayW / 2);
      columns.set(c, Math.max(columns.get(c) ?? 0, p.value ?? 0));
    }
    const top = Math.max(1, ...columns.values());
    for (const [c, v] of columns) {
      const th = 4 + (v / top) * (MARK_H - 8);
      els.push(<rect key={`d${c}`} x={c} y={MARK_H - 2 - th} width={1} height={th} fill="var(--foreground)" opacity={0.75} />);
    }
    els.push(<line key="base" x1={0} x2={s.w} y1={MARK_H - 2} y2={MARK_H - 2} stroke="var(--border)" strokeWidth={1} />);
  } else {
    // Dated markers; PHIVOLCS, VAAC and DROMIC markers link to their pages.
    let lastX = -Infinity;
    for (const [i, p] of inRange.entries()) {
      const px = s.x(p.date) + s.dayW / 2;
      const short = (p.mark ?? "").length <= 2;
      const label = `${p.mark ? `${p.mark}: ` : ""}${track.title[lang]}, ${p.value != null ? formatNumber(p.value, lang) : "–"}${track.unit ? ` ${unitLabel(track.unit, lang)}` : ""}, ${formatDate(p.date, lang)}`;
      const body = short ? (
        <>
          <circle cx={px} cy={MARK_H / 2} r={9} fill="var(--background)" stroke="var(--foreground)" strokeWidth={1.5} />
          <text x={px} y={MARK_H / 2 + 4} fontSize={11} textAnchor="middle" fill="var(--foreground)" fontWeight={600}>
            {p.mark}
          </text>
        </>
      ) : (
        <>
          <rect x={px - 4} y={MARK_H / 2 - 4} width={8} height={8} transform={`rotate(45 ${px} ${MARK_H / 2})`} fill="var(--foreground)" />
          {px - lastX > 70 && px < s.w - 50 ? (
            <text x={px + 8} y={MARK_H / 2 + 4} fontSize={10.5} fill="var(--muted-foreground)">
              {p.mark ?? (p.value != null ? formatNumber(p.value, lang) : "")}
            </text>
          ) : null}
        </>
      );
      if (!short && px - lastX > 70) lastX = px;
      els.push(
        safeHref(p.url) ? (
          <a key={`${p.date}#${i}`} href={safeHref(p.url)} target="_blank" rel="noopener noreferrer" aria-label={label}>
            {body}
          </a>
        ) : (
          <g key={`${p.date}#${i}`} role="img" aria-label={label}>
            {body}
          </g>
        ),
      );
    }
  }

  return (
    <svg width={s.w} height={h} className="block overflow-visible" role="group" aria-label={track.title[lang]}>
      {els}
      {markers?.length ? <EventMarkerGroup placed={placeMarkers(markers, s)} height={h} /> : null}
      {toDay(cursor) >= fromD && toDay(cursor) <= toD ? <line x1={cx} x2={cx} y1={0} y2={h} stroke="var(--primary)" strokeWidth={1.5} strokeDasharray="3 2" pointerEvents="none" /> : null}
    </svg>
  );
}

/** Dated rules and spans (Akari event markers) on the shared x scale; a span covers its last day too. One label row. */
function placeMarkers(markers: EventMarker[], s: Scale) {
  const drawn = markers.map((m) => (m.end === undefined ? m : { ...m, end: addDays(String(m.end), 1) }));
  return layoutEventMarkers(drawn, (at) => (typeof at === "string" ? s.x(at) : null), { width: s.w, rows: 1 });
}

function coverageText(track: Track, from: string, to: string, lang: "en" | "ja"): string | null {
  if (track.kind !== "line") return null;
  const share = observedShare(track, from, to);
  const days = share == null ? "" : lang === "ja" ? `有効観測日 ${formatPercent(share, lang)}` : `valid observations on ${formatPercent(share, lang)} of days`;
  const per = track.coverage === "per-day" ? (lang === "ja" ? "下の帯:各日の有効画素率" : "band below: each day's valid-pixel share") : lang === "ja" ? "画素単位の被覆率はこの版では未報告" : "per-pixel coverage not reported in this version";
  return [days, per].filter(Boolean).join(" · ");
}

export interface TimelineProps {
  tracks: Track[];
  from: string;
  to: string;
  cursor: string;
  onCursor: (iso: string) => void;
  dataAsOf: string;
  /** Story steps: shade this window on every row. */
  highlight?: [string, string];
  /** Story visual: labels always above the plot. */
  compact?: boolean;
}

/** Every record on one time axis: one row per track, a shared x scale, the scrubber's day drawn on every row. */
export function Timeline({ tracks, from, to, cursor, onCursor, dataAsOf, highlight, compact }: TimelineProps) {
  const t = useT();
  const { lang } = useLang();
  const [ref, w] = useWidth<HTMLDivElement>();
  const s = makeScale(from, to, Math.max(w, 1));
  const ticks = monthTicks(from, to, w < 500 ? 4 : 8);
  const yearly = yearlyTicks(ticks);
  const dragging = useRef(false);
  const cols = compact ? "" : "md:grid-cols-[220px_minmax(0,1fr)]";

  const dayAt = (e: PointerEvent<HTMLElement>) => {
    const box = e.currentTarget.getBoundingClientRect();
    const d = Math.floor(((e.clientX - box.left) / box.width) * s.days);
    return fromDay(s.from + Math.min(s.days - 1, Math.max(0, d)));
  };

  return (
    <div className="flex flex-col" data-timeline>
      {/* Axis: month ticks. The plot column starts after the label column on wide screens. */}
      <div className={`grid gap-x-4 ${cols}`}>
        {compact ? null : <div className="hidden md:block" />}
        <div ref={ref} className="relative h-5 min-w-0 text-[11px] text-muted-foreground" aria-hidden="true">
          {w > 0
            ? ticks.map((iso, i) => (
                <span key={iso} className="absolute top-0 -translate-x-1/2 font-mono whitespace-nowrap" style={{ left: Math.min(Math.max(s.x(iso), 18), s.w - 18) }}>
                  {tickLabel(iso, lang, i === 0, yearly)}
                </span>
              ))
            : null}
        </div>
      </div>
      {GROUPS.filter((g) => tracks.some((tr) => tr.group === g.id)).map((g) => (
        <section key={g.id} aria-label={g.title[lang]} className="border-t border-border pt-2">
          <h3 className="m-0 font-mono text-[11px] tracking-wide text-muted-foreground uppercase">{g.title[lang]}</h3>
          {tracks
            .filter((tr) => tr.group === g.id)
            .map((tr) => {
              const cov = coverageText(tr, from, to, lang);
              const mk = markersFor(tr, tracks, lang);
              return (
                <figure key={tr.id} className={`m-0 grid gap-x-4 gap-y-1 py-2 ${cols}`} data-track={tr.id}>
                  <figcaption className="flex flex-col gap-0.5">
                    <span className="text-sm font-medium">
                      {tr.title[lang]}
                      {tr.unit && tr.kind !== "spans" ? <span className="font-normal text-muted-foreground"> ({unitLabel(tr.unit, lang)})</span> : null}
                    </span>
                    {/* One short source line; the instrument wording, coverage and notes one tap away (rule 28b). "Data through" stays visible on every chart (RESEARCH.md §9). */}
                    <details className="text-xs text-muted-foreground" data-track-notes>
                      <summary className="cursor-pointer">{t(`Source: ${sourceLine(tr.sources, "en")}`, `出典:${sourceLine(tr.sources, "ja")}`)}</summary>
                      <div className="flex flex-col gap-0.5 pt-0.5">
                        <span>{tr.instrument[lang]}</span>
                        {cov ? <span>{cov}</span> : null}
                        {tr.start && tr.kind === "bars" ? (
                          <span>{t(`Instrument record from ${formatDate(tr.start, "en")}; an empty day means nothing detected`, `${formatDate(tr.start, "ja")}から観測。空白の日は検知なし`)}</span>
                        ) : null}
                        {tr.note ? <span className="italic">{tr.note[lang]}</span> : null}
                      </div>
                    </details>
                    {mk.length ? <span className="sr-only">{eventMarkersSummary(mk, { lang, format: (d) => formatDate(String(d), lang) })}</span> : null}
                    <DataThrough date={dataAsOf} />
                  </figcaption>
                  <div
                    className="min-w-0 cursor-crosshair touch-pan-y"
                    onPointerDown={(e) => {
                      if ((e.target as Element).closest("a")) return;
                      dragging.current = true;
                      onCursor(dayAt(e));
                    }}
                    onPointerMove={(e) => {
                      if (dragging.current) onCursor(dayAt(e));
                    }}
                    onPointerUp={() => (dragging.current = false)}
                    onPointerLeave={() => (dragging.current = false)}
                  >
                    {w > 0 ? <TrackPlot track={tr} s={s} from={from} to={to} cursor={cursor} lang={lang} highlight={highlight} markers={mk} /> : <div style={{ height: heightOf(tr) }} />}
                  </div>
                </figure>
              );
            })}
        </section>
      ))}
    </div>
  );
}
