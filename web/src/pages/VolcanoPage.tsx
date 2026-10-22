import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
  Button,
  Page,
  Prose,
  T,
  useLang,
  useT,
} from "@abrycta/akari/react";
import { use, useEffect, useMemo } from "react";

import type { VolcanoReadModel, VolcanoesIndex } from "@contracts/readmodels";

import { AppLink, ExtLink } from "@/app/Link";
import { navigate, useUrlState } from "@/app/url";
import { DataThrough } from "@/components/DataThrough";
import { DraftBadge, FigureList } from "@/components/FigureList";
import { loadVolcano, loadVolcanoes, STORIES } from "@/data/load";
import { periodsOf } from "@/data/periods";
import { absentRecords, buildTracks, ringOptions } from "@/data/tracks";
import { addDays, formatDate, formatRange, toDay } from "@/lib/dates";
import { formatNumber, volcanoType } from "@/lib/format";
import { DeepTimeStrip } from "@/volcano/DeepTimeStrip";
import { Readout } from "@/volcano/Readout";
import { Timeline } from "@/volcano/Timeline";

import NotFoundPage from "./NotFoundPage";

type Feature = VolcanoesIndex["features"][number];

function Breadcrumbs({ name }: { name: string }) {
  const t = useT();
  return (
    <Breadcrumb>
      <BreadcrumbList>
        <BreadcrumbItem>
          <BreadcrumbLink asChild>
            <AppLink to="volcanoes">{t("Volcanoes", "火山")}</AppLink>
          </BreadcrumbLink>
        </BreadcrumbItem>
        <BreadcrumbSeparator />
        <BreadcrumbItem>
          <BreadcrumbPage>{name}</BreadcrumbPage>
        </BreadcrumbItem>
      </BreadcrumbList>
    </Breadcrumb>
  );
}

function Facts({ f, model }: { f: Feature; model: VolcanoReadModel | null }) {
  const { lang } = useLang();
  const t = useT();
  const p = f.properties;
  const ring = model?.exposure.rings[0];
  const rows: [string, React.ReactNode][] = [
    [t("Type (GVP)", "種類(GVP)"), model?.volcano.type ? volcanoType(model.volcano.type, lang) : "–"],
    [t("Elevation", "標高"), p.elevationM != null ? `${formatNumber(p.elevationM, lang, 0)} m` : "–"],
    [t("Eruptions since 2000 (GVP)", "2000年以降の噴火(GVP)"), p.eruptionsSince2000 ?? "–"],
    [t("Last eruption (GVP)", "最後の噴火(GVP)"), p.lastEruption?.start ? `${formatDate(p.lastEruption.start, lang)}${p.lastEruption.vei != null ? ` · VEI ${p.lastEruption.vei}` : ""}` : "–"],
  ];
  if (ring) rows.push([t(`People within ${ring.radiusKm} km (WorldPop ${ring.year})`, `${ring.radiusKm} km圏の人口(WorldPop ${ring.year}年)`), `≈ ${formatNumber(ring.population, lang, 0)}`]);
  return (
    <dl className="m-0 grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-3 lg:grid-cols-5">
      {rows.map(([k, v]) => (
        <div key={k} className="flex flex-col gap-0.5">
          <dt className="text-xs text-muted-foreground">{k}</dt>
          <dd className="m-0 font-heading text-lg font-semibold tabular">{v}</dd>
        </div>
      ))}
    </dl>
  );
}

function Chip({ on, onClick, children }: { on: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <Button type="button" size="sm" variant={on ? "default" : "outline"} aria-pressed={on} onClick={onClick} className="rounded-full">
      {children}
    </Button>
  );
}

function Record({ model, f }: { model: VolcanoReadModel; f: Feature }) {
  const t = useT();
  const { lang } = useLang();
  const url = useUrlState();
  const periods = useMemo(() => periodsOf(model), [model]);
  const rings = useMemo(() => ringOptions(model), [model]);
  const period = periods.find((p) => p.from === url.from && p.to === url.to) ?? periods[0]!;
  const ring = url.ring && rings.includes(url.ring) ? url.ring : (rings[0] ?? null);
  const tracks = useMemo(() => buildTracks(model, ring), [model, ring]);
  const absent = useMemo(() => absentRecords(model, tracks), [model, tracks]);
  const firstEvent = model.readings[0]?.start;
  const cursor = url.date && url.date >= period.from && url.date <= period.to ? url.date : firstEvent && firstEvent >= period.from && firstEvent <= period.to ? firstEvent : period.from;
  const days = toDay(period.to) - toDay(period.from) + 1;
  const idx = toDay(cursor) - toDay(period.from);
  const setCursor = (d: string) => navigate({ date: d });
  const story = STORIES.find((s) => s.volcanoId === model.volcano.id);

  return (
    <>
      <section aria-labelledby="record-title" className="flex flex-col gap-3">
        <div className="flex flex-col gap-1">
          <h2 id="record-title" className="m-0 font-heading text-2xl font-semibold">
            <T en="Every record on one time axis" ja="すべての記録を一つの時間軸に" />
          </h2>
          <p className="m-0 max-w-prose text-sm text-muted-foreground">
            <T
              en="Each series starts when its instrument does; gaps are shown, never filled. Drag across a row or use the slider to read every record on one day."
              ja="各系列は観測機器の開始日から始まり、欠測は埋めずにそのまま示します。行をドラッグするかスライダーで、ある一日のすべての記録を読めます。"
            />
          </p>
        </div>
        <div className="flex flex-col gap-2">
          <div role="group" aria-label={t("Period", "期間")} className="flex flex-wrap items-center gap-2">
            <span className="w-16 text-xs text-muted-foreground">{t("Period", "期間")}</span>
            {periods.map((p) => (
              <Chip key={p.id} on={p === period} onClick={() => navigate({ from: p.id === "all" ? null : p.from, to: p.id === "all" ? null : p.to, date: null })}>
                {p.label[lang]}
              </Chip>
            ))}
          </div>
          {rings.length > 1 ? (
            <div role="group" aria-label={t("Ring around the summit", "山頂からの距離")} className="flex flex-wrap items-center gap-2">
              <span className="w-16 text-xs text-muted-foreground">{t("Ring", "範囲")}</span>
              {rings.map((r) => (
                <Chip key={r} on={r === ring} onClick={() => navigate({ ring: r })}>
                  {r} km
                </Chip>
              ))}
              <span className="text-xs text-muted-foreground">{t("Series without this ring keep their own (stated in the title).", "この範囲のない系列は独自の範囲のまま(題に記載)。")}</span>
            </div>
          ) : null}
        </div>

        <div className="sticky top-[5rem] z-10 max-[639px]:top-[7rem] -mx-ak-gutter border-y border-border bg-background/95 px-ak-gutter py-2 backdrop-blur-sm">
          <div className="grid items-center gap-x-4 gap-y-1 md:grid-cols-[220px_minmax(0,1fr)]">
            <label htmlFor="scrubber" className="text-sm">
              <T en="Day" ja="日付" />: <strong className="tabular">{formatDate(cursor, lang)}</strong>
            </label>
            <div className="flex items-center gap-2">
              <Button type="button" size="icon-sm" variant="outline" aria-label={t("Previous day", "前の日")} disabled={idx <= 0} onClick={() => setCursor(addDays(cursor, -1))}>
                ‹
              </Button>
              <input
                id="scrubber"
                data-testid="scrubber"
                type="range"
                className="range min-w-0 flex-1"
                min={0}
                max={days - 1}
                value={idx}
                aria-valuetext={formatDate(cursor, lang)}
                onChange={(e) => setCursor(addDays(period.from, Number(e.target.value)))}
              />
              <Button type="button" size="icon-sm" variant="outline" aria-label={t("Next day", "次の日")} disabled={idx >= days - 1} onClick={() => setCursor(addDays(cursor, 1))}>
                ›
              </Button>
            </div>
          </div>
        </div>

        {/* In the 1120px column a side readout would leave the plots about 470px wide (772px before): the readout
            sits under the timeline at every width so the charts keep their width (rule 28c). */}
        <div className="grid items-start gap-6">
          <Timeline tracks={tracks} from={period.from} to={period.to} cursor={cursor} onCursor={setCursor} dataAsOf={model.dataAsOf} />
          <aside>
            <Readout tracks={tracks} date={cursor} />
          </aside>
        </div>
        {absent.length ? (
          <details data-absent-records>
            <summary className="cursor-pointer text-muted-foreground">
              <h3 className="m-0 inline font-mono text-[11px] tracking-wide text-muted-foreground uppercase">{t("Nothing to show, and why", "記録がない系列とその理由")}</h3>
            </summary>
            <dl className="m-0 mt-2 grid max-w-4xl gap-x-6 gap-y-2 text-sm md:grid-cols-[minmax(0,18rem)_minmax(0,1fr)]">
              {absent.map((a) => (
                <div key={a.id} className="contents" data-absent={a.id}>
                  <dt className="font-medium">{a.title[lang]}</dt>
                  <dd className="m-0 text-muted-foreground">{a.reason[lang]}</dd>
                </div>
              ))}
            </dl>
          </details>
        ) : null}
      </section>

      {model.readings.length ? (
        <section aria-labelledby="readings-title" className="flex flex-col gap-3">
          <h2 id="readings-title" className="m-0 font-heading text-2xl font-semibold">
            <T en="What the records show" ja="記録が示すこと" />
          </h2>
          {model.readings.map((r) => (
            <article key={r.id} className="flex flex-col gap-2 rounded-sm border border-border bg-card p-3">
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="m-0 font-heading text-lg font-semibold">{formatRange(r.start, r.end, lang)}</h3>
                <DraftBadge status={r.status} />
              </div>
              <Prose>
                <p>{r.text[lang]}</p>
                {r.limits ? (
                  <p className="text-sm text-muted-foreground">
                    <strong>{t("Limits:", "限界:")}</strong> {r.limits[lang]}
                  </p>
                ) : null}
              </Prose>
              <FigureList figures={r.figures} />
            </article>
          ))}
          {story ? (
            <p className="m-0">
              <AppLink to="story" id={story.id} className="underline underline-offset-4">
                {t("Read the story: Taal, January 2020 →", "ストーリーを読む:タール火山 2020年1月 →")}
              </AppLink>
            </p>
          ) : null}
        </section>
      ) : null}

      <section aria-labelledby="nearby-title" className="flex flex-col gap-3">
        <h2 id="nearby-title" className="m-0 font-heading text-2xl font-semibold">
          <T en="Who lives nearby" ja="周辺に住む人々" />
        </h2>
        {model.exposure.rings.length ? (
          <table className="w-full max-w-xl border-collapse text-sm">
            <caption className="text-left text-xs text-muted-foreground">
              <T en="Population within each distance of the summit" ja="山頂からの距離ごとの人口" /> · <DataThrough date={model.dataAsOf} />
            </caption>
            <thead>
              <tr className="text-left text-xs text-muted-foreground">
                <th className="py-1 font-normal">{t("Distance", "距離")}</th>
                <th className="py-1 font-normal">{t("People (estimate)", "人口(推計)")}</th>
                <th className="py-1 font-normal">{t("Source", "出典")}</th>
              </tr>
            </thead>
            <tbody>
              {model.exposure.rings.map((r) => (
                <tr key={r.radiusKm} className="border-t border-border">
                  <td className="py-1.5">{t(`within ${r.radiusKm} km`, `${r.radiusKm} km圏`)}</td>
                  <td className="py-1.5 tabular">≈ {formatNumber(r.population, lang, 0)}</td>
                  <td className="py-1.5 text-muted-foreground">WorldPop {r.year}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : null}
        <p className="m-0 max-w-prose text-sm text-muted-foreground">
          <T en="Rings are distances, not hazard zones. Hazard maps stay with PHIVOLCS:" ja="距離の円はハザード区域ではありません。ハザードマップはPHIVOLCSのものを参照してください:" />{" "}
          {model.volcano.links.hazardhunter ? <ExtLink href={model.volcano.links.hazardhunter}>HazardHunterPH</ExtLink> : null}
        </p>
      </section>

      <EruptionHistory model={model} />
      <SourcesForView model={model} f={f} />
    </>
  );
}

function EruptionHistory({ model }: { model: VolcanoReadModel }) {
  const t = useT();
  const { lang } = useLang();
  const eruptions = model.episodes.filter((e) => e.kind === "gvp_eruption").reverse();
  if (!eruptions.length) return null;
  return (
    <section aria-labelledby="history-title" className="flex flex-col gap-3">
      <h2 id="history-title" className="m-0 font-heading text-2xl font-semibold">
        <T en="Eruption history (GVP)" ja="噴火史(GVP)" />
      </h2>
      <details>
        <summary className="cursor-pointer text-sm">{t(`All ${eruptions.length} eruptions in the Smithsonian record`, `スミソニアン博物館の記録にある全${eruptions.length}回の噴火`)}</summary>
        <div className="mt-2 max-h-96 overflow-auto">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="text-left text-xs text-muted-foreground">
                <th className="py-1 font-normal">{t("Start", "開始")}</th>
                <th className="py-1 font-normal">{t("End", "終了")}</th>
                <th className="py-1 font-normal">VEI</th>
                <th className="py-1 font-normal">{t("SO₂ mass", "SO₂量")}</th>
              </tr>
            </thead>
            <tbody>
              {eruptions.map((e) => (
                <tr key={e.id} className="border-t border-border">
                  <td className="py-1 tabular">{formatDate(e.start, lang)}</td>
                  <td className="py-1 tabular">{e.end ? formatDate(e.end, lang) : "–"}</td>
                  <td className="py-1 tabular">{e.vei ?? "?"}</td>
                  <td className="py-1 tabular">{e.so2MassKt != null ? `${e.so2MassKt} kt` : "–"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </section>
  );
}

function SourcesForView({ model, f }: { model: VolcanoReadModel | null; f: Feature }) {
  const t = useT();
  const links = model?.volcano.links;
  return (
    <section aria-labelledby="sources-title" className="flex flex-col gap-3">
      <h2 id="sources-title" className="m-0 font-heading text-2xl font-semibold">
        <T en="Sources for this view" ja="このページの出典" />
      </h2>
      {model ? (
        <ul className="m-0 grid gap-2 pl-5 text-sm">
          {model.provenance.sources.map((s) => (
            <li key={s.id}>
              <span className="font-mono text-xs">{s.id}</span>: {s.attribution}
              {s.fromArchive && s.snapshotDate ? <span className="text-muted-foreground"> {t(`(data as of ${s.snapshotDate})`, `(${s.snapshotDate}時点のデータ)`)}</span> : null}
            </li>
          ))}
        </ul>
      ) : null}
      <p className="m-0 flex flex-wrap gap-x-4 gap-y-1 text-sm">
        <ExtLink href={links?.gvp ?? `https://volcano.si.edu/volcano.cfm?vn=${f.properties.gvpNumber ?? ""}`}>{t("Smithsonian GVP page", "スミソニアン博物館GVPのページ")}</ExtLink>
        <ExtLink href={links?.phivolcs ?? "https://www.phivolcs.dost.gov.ph/"}>DOST-PHIVOLCS</ExtLink>
        {links?.comet ? <ExtLink href={links.comet}>{t("Ground deformation (COMET LiCSAR portal)", "地殻変動(COMET LiCSARポータル)")}</ExtLink> : null}
        <AppLink to="about" className="underline underline-offset-4">
          {t("All sources and licences", "すべての出典とライセンス")}
        </AppLink>
      </p>
    </section>
  );
}

export default function VolcanoPage({ id }: { id: string }) {
  const t = useT();
  const { lang } = useLang();
  const index = use(loadVolcanoes());
  const f = index.features.find((x) => x.properties.id === id);
  const model = f ? use(loadVolcano(f.properties.file)) : null;
  useEffect(() => {
    if (f) document.title = `${f.properties.name[lang]} · Plumes`;
  }, [f, lang]);
  if (!f) return <NotFoundPage />;
  const p = f.properties;
  return (
    <Page
      eyebrow={<Breadcrumbs name={p.name[lang]} />}
      title={
        <>
          {p.name[lang]}
          {lang === "en" ? (
            <span lang="ja" className="ml-3 text-lg font-normal text-muted-foreground">
              {p.name.ja}
            </span>
          ) : null}
        </>
      }
      lede={
        p.coverage === "deep"
          ? t("A deep record: PHIVOLCS bulletins, satellites and earthquakes on one time axis.", "詳細な記録:PHIVOLCSの火山情報・衛星・地震を一つの時間軸に。")
          : t("A satellite and eruption-history record. PHIVOLCS publishes daily bulletins only for observatory volcanoes and during unrest.", "衛星と噴火史の記録。PHIVOLCSの日々の火山情報は観測所のある火山と活動時のみ。")
      }
    >
      <Facts f={f} model={model} />
      <DeepTimeStrip volcanoId={p.id} />
      {model ? (
        <Record model={model} f={f} />
      ) : (
        <>
          <section className="flex flex-col gap-2 rounded-sm border border-dashed border-border p-3">
            <p className="m-0">
              <T en="This data version has no per-volcano record for this volcano yet." ja="このデータ版には、この火山の個別の記録はまだありません。" />
            </p>
            <p className="m-0 text-sm text-muted-foreground">
              <T en="The overview figures above come from the Smithsonian Global Volcanism Program." ja="上の概要はスミソニアン博物館グローバル火山活動プログラムによるものです。" />
            </p>
          </section>
          <SourcesForView model={null} f={f} />
        </>
      )}
    </Page>
  );
}
