// Deep-time strip (LAYERS-PLAN §7 step 3): every GVP eruption of one volcano on a compressed time axis, with
// NOAA NCEI HazEL deaths and damage as bars above it, and the cited events as a table. A past record only.

import { T, useLang, useT } from "@abrycta/akari/react";
import { use, useEffect, useRef, useState } from "react";

import type { AmountOrder, DeepTime, DeepTimeImpact } from "@contracts/deeptime";

import { ExtLink } from "@/app/Link";
import { deathsForBar, formatPartialDate, loadDeepTime, formatYear, impactRows, ticks, timeScale, yearOf } from "@/data/deeptime";
import type { Lang } from "@/lib/dates";
import { formatNumber } from "@/lib/format";

const H = 104;
const AXIS_Y = 80;
const DOT_Y = 62;
const BAR_BASE = 50;
const PAD = 10;

function useWidth<E extends HTMLElement>(): [React.RefObject<E | null>, number] {
  const ref = useRef<E>(null);
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

const barH = (deaths: number) => (deaths > 0 ? Math.min(40, 6 + 10 * Math.log10(deaths)) : 0);

function orderText(dt: DeepTime, scale: "people" | "damage", o: AmountOrder | undefined, lang: Lang): string | null {
  return o ? (dt.glossary.orders[scale][String(o)]?.[lang] ?? null) : null;
}

/** "350 (800 with secondary effects)", or NCEI's order class when there is no number. */
function people(dt: DeepTime, n: number | undefined, o: AmountOrder | undefined, total: number | undefined, oTotal: AmountOrder | undefined, lang: Lang): string {
  const main = n != null ? formatNumber(n, lang, 0) : orderText(dt, "people", o, lang);
  const tot = total != null ? formatNumber(total, lang, 0) : orderText(dt, "people", oTotal, lang);
  if (main && tot && total !== n) return lang === "ja" ? `${main}(二次的影響を含め${tot})` : `${main} (${tot} with secondary effects)`;
  return main ?? (tot ? (lang === "ja" ? `${tot}(二次的影響を含む)` : `${tot} (with secondary effects)`) : "–");
}

function damage(dt: DeepTime, i: DeepTimeImpact, lang: Lang): string {
  const v = i.damageMusd ?? i.damageMusdTotal;
  if (v != null) return lang === "ja" ? `${formatNumber(v, lang)}百万米ドル` : `US$${formatNumber(v, lang)} million`;
  return orderText(dt, "damage", i.damageOrder ?? i.damageTotalOrder, lang) ?? "–";
}

function Strip({ dt, volcanoId }: { dt: DeepTime; volcanoId: string }) {
  const t = useT();
  const { lang } = useLang();
  const [ref, w] = useWidth<HTMLDivElement>();
  const v = dt.volcanoes.find((x) => x.id === volcanoId);
  if (!v || !v.eruptions.length) return null;
  const end = yearOf(dt.dataAsOf);
  const s = timeScale(dt.span.startYear, end, Math.max(0, w - 2 * PAD));
  const x = (y: number) => PAD + s.x(y);
  const rows = impactRows(v);
  const deadly = rows.filter((r) => deathsForBar(r.impact) > 0).length;
  const first = yearOf(v.eruptions[0]!.start);
  const last = yearOf(v.eruptions[v.eruptions.length - 1]!.start);
  const summary = t(
    `${v.eruptions.length} eruptions in the Smithsonian record, ${formatYear(first, "en")} to ${formatYear(last, "en")}; ${deadly} with deaths recorded by NOAA NCEI.`,
    `スミソニアンの記録で${v.eruptions.length}回の噴火(${formatYear(first, "ja")}〜${formatYear(last, "ja")})。うちNOAA NCEIが死者を記録したもの${deadly}回。`,
  );
  const sat = yearOf(dt.span.satelliteEraStart);

  return (
    <section aria-labelledby="deeptime-title" className="flex flex-col gap-3" data-deeptime>
      <h2 id="deeptime-title" className="m-0 font-heading text-2xl font-semibold">
        <T en="Deep time" ja="長い時間軸" />
      </h2>
      <p className="m-0 max-w-prose text-sm text-muted-foreground">
        <T
          en="Every eruption in the Smithsonian record on one compressed axis: recent centuries get more room. Dot size is the VEI; bars above are deaths recorded by NOAA NCEI. The detailed record starts in 2000."
          ja="スミソニアンの記録にある全噴火を圧縮した時間軸に表示(最近の数世紀ほど広い)。点の大きさはVEI、上の棒はNOAA NCEIが記録した死者数。詳細な記録は2000年から。"
        />
      </p>
      <figure className="m-0 flex flex-col gap-1">
        <div ref={ref} className="w-full min-w-0" style={{ height: H }}>
          {w > 0 ? (
            <svg width={w} height={H} role="img" aria-label={summary} className="block overflow-visible">
              <rect x={x(sat)} y={4} width={Math.max(0, x(end) - x(sat))} height={AXIS_Y - 4} fill="var(--muted)" opacity={0.7} />
              <text x={x(end)} y={14} fontSize={10.5} textAnchor="end" fill="var(--muted-foreground)">
                {t("2000 →", "2000年〜")}
              </text>
              <line x1={PAD} x2={x(end)} y1={AXIS_Y} y2={AXIS_Y} stroke="var(--border)" strokeWidth={1} />
              {ticks(s, lang === "ja" ? 72 : 56).map((y) => (
                <g key={y}>
                  <line x1={x(y)} x2={x(y)} y1={AXIS_Y} y2={AXIS_Y + 4} stroke="var(--border)" strokeWidth={1} />
                  <text x={x(y)} y={AXIS_Y + 16} fontSize={11} textAnchor="middle" fill="var(--muted-foreground)">
                    {formatYear(y, lang)}
                  </text>
                </g>
              ))}
              {v.eruptions.map((e) => {
                const y = yearOf(e.start);
                const u = e.startYearUncertainty ?? 0;
                const r = e.vei != null ? 2.5 + e.vei * 1.1 : 2.5;
                const label = `${formatPartialDate(e.start, lang)}${u ? ` ±${u}` : ""} · VEI ${e.vei ?? "?"}${e.certainty === "uncertain" ? t(" · uncertain eruption", " · 不確かな噴火") : ""}`;
                return (
                  <g key={e.id}>
                    <title>{label}</title>
                    {u ? <line x1={x(y - u)} x2={x(y + u)} y1={DOT_Y} y2={DOT_Y} stroke="var(--chart-seq-4)" strokeWidth={1.5} opacity={0.6} /> : null}
                    <circle
                      cx={x(y)}
                      cy={DOT_Y}
                      r={r}
                      fill={e.vei != null && e.certainty === "confirmed" ? "color-mix(in oklab, var(--chart-seq-4) 55%, transparent)" : "var(--background)"}
                      stroke="var(--chart-seq-4)"
                      strokeWidth={1.25}
                      strokeDasharray={e.certainty === "uncertain" ? "2 1.5" : undefined}
                    />
                  </g>
                );
              })}
              {rows.map(({ impact: i }) => {
                const d = deathsForBar(i);
                const cx = x(yearOf(i.date));
                const label = `${formatPartialDate(i.date, lang)} · ${t("deaths", "死者")} ${people(dt, i.deaths, i.deathsOrder, i.deathsTotal, i.deathsTotalOrder, lang)} (NOAA NCEI)`;
                return d > 0 ? (
                  <rect key={i.id} x={cx - 1.5} y={BAR_BASE - barH(d)} width={3} height={barH(d)} rx={1} fill="var(--seal)">
                    <title>{label}</title>
                  </rect>
                ) : (
                  <rect key={i.id} x={cx - 2.5} y={BAR_BASE - 5} width={5} height={5} transform={`rotate(45 ${cx} ${BAR_BASE - 2.5})`} fill="none" stroke="var(--seal)" strokeWidth={1.25}>
                    <title>{`${formatPartialDate(i.date, lang)} · ${t("damage", "被害")} ${damage(dt, i, lang)} (NOAA NCEI)`}</title>
                  </rect>
                );
              })}
            </svg>
          ) : null}
        </div>
        <figcaption className="text-xs text-muted-foreground">
          {dt.notes.dates[lang]} <T en="Eruptions:" ja="噴火:" /> <ExtLink href={v.eruptions[0]!.url}>Smithsonian GVP</ExtLink>
          {". "}
          <T en="Deaths and damage:" ja="死者と被害:" /> <ExtLink href="https://doi.org/10.7289/V5JW8BSH">NOAA NCEI/WDS</ExtLink>
          {"."}
        </figcaption>
      </figure>
      {rows.length ? (
        <details>
          <summary className="cursor-pointer text-sm">
            {t(`${rows.length} events with deaths or damage recorded by NOAA NCEI`, `NOAA NCEIが死者や被害を記録した${rows.length}件`)}
          </summary>
          <p className="mt-2 mb-0 max-w-prose text-xs text-muted-foreground">{dt.notes.impacts[lang]}</p>
          <ul className="m-0 mt-2 flex max-h-[32rem] list-none flex-col overflow-auto p-0 text-sm">
            {rows.map(({ impact: i, eruption: e }) => (
              <li key={i.id} className="flex flex-col gap-0.5 border-t border-border py-2">
                <div className="flex flex-wrap items-baseline gap-x-2">
                  <strong className="tabular">{formatPartialDate(i.date, lang)}</strong>
                  <span className="text-xs text-muted-foreground">
                    {e ? t(`GVP eruption from ${formatPartialDate(e.start, "en")} · VEI ${e.vei ?? "?"}`, `GVPの噴火(${formatPartialDate(e.start, "ja")}〜)· VEI ${e.vei ?? "?"}`) : t("outside the GVP eruption dates", "GVPの噴火期間外")}
                  </span>
                  <span className="ml-auto whitespace-nowrap text-xs">
                    <ExtLink href={i.url}>NCEI</ExtLink>
                  </span>
                </div>
                <dl className="m-0 grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5 text-xs">
                  <dt className="text-muted-foreground">{t("Deaths", "死者")}</dt>
                  <dd className="m-0 tabular">{people(dt, i.deaths, i.deathsOrder, i.deathsTotal, i.deathsTotalOrder, lang)}</dd>
                  <dt className="text-muted-foreground">{t("Damage", "被害額")}</dt>
                  <dd className="m-0 tabular">{damage(dt, i, lang)}</dd>
                  <dt className="text-muted-foreground">{t("Houses destroyed", "全壊家屋")}</dt>
                  <dd className="m-0 tabular">{people(dt, i.housesDestroyed, i.housesDestroyedOrder, i.housesDestroyedTotal, i.housesDestroyedTotalOrder, lang)}</dd>
                  {i.agents?.length ? (
                    <>
                      <dt className="text-muted-foreground">{t("Cause", "原因")}</dt>
                      <dd className="m-0">{i.agents.map((a) => dt.glossary.agents[a]?.[lang] ?? a).join(t("; ", "、"))}</dd>
                    </>
                  ) : null}
                </dl>
              </li>
            ))}
          </ul>
        </details>
      ) : (
        <p className="m-0 text-sm text-muted-foreground">
          <T en="NOAA NCEI records no deaths or damage for this volcano." ja="NOAA NCEIはこの火山について死者や被害を記録していない。" />
        </p>
      )}
    </section>
  );
}

/** Renders nothing when the data version has no deeptime.json or the volcano has no GVP eruptions. */
export function DeepTimeStrip({ volcanoId }: { volcanoId: string }) {
  const dt = use(loadDeepTime());
  return dt ? <Strip dt={dt} volcanoId={volcanoId} /> : null;
}
