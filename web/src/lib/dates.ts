// ISO-day arithmetic in UTC (no time zones: every date in the read models is a calendar day).

export type Lang = "en" | "ja";

const DAY = 86_400_000;

export function toDay(iso: string): number {
  const [y, m, d] = iso.slice(0, 10).split("-").map(Number);
  return Math.round(Date.UTC(y ?? 1970, (m ?? 1) - 1, d ?? 1) / DAY);
}

export function fromDay(day: number): string {
  return new Date(day * DAY).toISOString().slice(0, 10);
}

export function addDays(iso: string, n: number): string {
  return fromDay(toDay(iso) + n);
}

export function daysBetween(a: string, b: string): number {
  return toDay(b) - toDay(a);
}

const MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** A full or partial date (YYYY, YYYY-MM, YYYY-MM-DD; negative years are BCE) in the reader's language. */
export function formatDate(iso: string, lang: Lang): string {
  const m = /^(-?\d{1,5})(?:-(\d{2}))?(?:-(\d{2}))?/.exec(iso);
  if (!m) return iso;
  const y = Number(m[1]);
  const mo = m[2] ? Number(m[2]) : null;
  const d = m[3] ? Number(m[3]) : null;
  if (y <= 0) return lang === "ja" ? `紀元前${1 - y}年` : `${1 - y} BCE`;
  if (lang === "ja") return `${y}年${mo ? `${mo}月` : ""}${mo && d ? `${d}日` : ""}`;
  if (!mo) return String(y);
  return d ? `${d} ${MONTHS_EN[mo - 1]} ${y}` : `${MONTHS_EN[mo - 1]} ${y}`;
}

/** "12–26 Jan 2020" / "2020年1月12日〜26日"; falls back to two full dates across months or years. */
export function formatRange(a: string, b: string, lang: Lang): string {
  if (a === b) return formatDate(a, lang);
  const [ya, ma] = a.split("-");
  const [yb, mb, db] = b.split("-");
  if (lang === "ja") {
    if (ya === yb && ma === mb) return `${formatDate(a, lang)}〜${Number(db)}日`;
    return `${formatDate(a, lang)}〜${formatDate(b, lang)}`;
  }
  if (ya === yb && ma === mb) return `${Number(a.slice(8, 10))}–${formatDate(b, lang)}`;
  return `${formatDate(a, lang)} – ${formatDate(b, lang)}`;
}

/** Month ticks (first of each month) inside [from, to], thinned to at most `max`. */
export function monthTicks(from: string, to: string, max = 8): string[] {
  const out: string[] = [];
  let [y, m] = from.split("-").map(Number) as [number, number];
  if (from.slice(8, 10) !== "01") m += 1;
  for (;;) {
    if (m > 12) {
      m = 1;
      y += 1;
    }
    const iso = `${y}-${String(m).padStart(2, "0")}-01`;
    if (iso > to) break;
    out.push(iso);
    m += 1;
  }
  if (out.length <= max) return out;
  const step = Math.ceil(out.length / max);
  return out.filter((_, i) => i % step === 0);
}

/** Axis label for a month tick: the year only on January and on the first tick. */
export function tickLabel(iso: string, lang: Lang, first: boolean): string {
  const y = iso.slice(0, 4);
  const m = Number(iso.slice(5, 7));
  const withYear = first || m === 1;
  if (lang === "ja") return withYear ? `${y}年${m}月` : `${m}月`;
  return withYear ? `${MONTHS_EN[m - 1]} ${y}` : MONTHS_EN[m - 1]!;
}
