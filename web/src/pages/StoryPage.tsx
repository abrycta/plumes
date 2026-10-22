import {
  Alert,
  AlertDescription,
  AlertTitle,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
  Page,
  Scrollytelling,
  T,
  useLang,
  useT,
} from "@abrycta/akari/react";
import { use, useEffect, useMemo, useState, useSyncExternalStore } from "react";

import type { Story, StoryStep, VolcanoReadModel } from "@contracts/readmodels";

import { AppLink } from "@/app/Link";
import { DataThrough } from "@/components/DataThrough";
import { useUrlState } from "@/app/url";
import { DraftBadge, FigureList } from "@/components/FigureList";
import { assetUrl, loadRoot, loadStoriesIndex, loadStoryFile, loadVolcano, storyRefs } from "@/data/load";
import { buildTracks, type Track, tracksForStep } from "@/data/tracks";
import { formatDate, formatRange } from "@/lib/dates";
import { formatNumber } from "@/lib/format";
import { Timeline } from "@/volcano/Timeline";

import NotFoundPage from "./NotFoundPage";

/** A closing step built from the exposure rings (not in story.json): who lives nearby, as distances. */
function nearbyStep(model: VolcanoReadModel, story: Story): StoryStep | null {
  const ring = model.exposure.rings[0];
  if (!ring) return null;
  return {
    id: "nearby",
    start: story.span.start,
    end: story.span.end,
    title: { en: "Who lives nearby", ja: "周辺に住む人々" },
    text: {
      en: `About ${formatNumber(ring.population, "en", 0)} people lived within ${ring.radiusKm} km of the summit (WorldPop ${ring.year} estimate). Rings are distances, not hazard zones; hazard maps stay with PHIVOLCS.`,
      ja: `山頂から${ring.radiusKm} km圏には約${formatNumber(ring.population, "ja", 0)}人が住んでいた（WorldPop ${ring.year}年推計）。距離の円はハザード区域ではなく、ハザードマップはPHIVOLCSのものを参照。`,
    },
    series: [],
    figures: [],
  };
}

/** A generated step reads as a list, one short line per fact (and per missing record); a hand-built step stays one paragraph. */
function StepText({ step }: { step: StoryStep }) {
  const { lang } = useLang();
  const lines = [...(step.sentences ?? []).map((x) => ({ key: x.template, text: x.text, absent: false })), ...(step.absent ?? []).map((x) => ({ key: x.why, text: x.text, absent: true }))];
  if (!lines.length) return <p className="m-0">{step.text[lang]}</p>;
  return (
    <ul className="m-0 flex list-disc flex-col gap-1 pl-5" data-step-lines>
      {lines.map((l, i) => (
        <li key={`${l.key}-${i}`} className={l.absent ? "text-muted-foreground" : undefined}>
          {l.text[lang]}
        </li>
      ))}
    </ul>
  );
}

/** Akari's Scrollytelling breakpoint (md, 48rem): beside the text from here up, stacked inside each step below it. */
const WIDE = "(min-width: 48rem)";
const subscribeWide = (cb: () => void) => {
  const mq = window.matchMedia(WIDE);
  mq.addEventListener("change", cb);
  return () => mq.removeEventListener("change", cb);
};
const useWide = () => useSyncExternalStore(subscribeWide, () => window.matchMedia(WIDE).matches, () => true);

function StepVisual({ story, model, step, tracks }: { story: Story; model: VolcanoReadModel; step: StoryStep; tracks: Track[] }) {
  const { lang } = useLang();
  const root = use(loadRoot());
  // Keyed by step id (below), so the cursor starts at each step's first day.
  const [cursor, setCursor] = useState(step.start < story.span.start ? story.span.start : step.start);
  const shown = tracksForStep(step, tracks);
  return (
    <div className="flex flex-col gap-3 rounded-sm border border-border bg-background p-3" data-story-visual>
      <p className="m-0 font-mono text-[11px] tracking-wide text-muted-foreground uppercase">
        {formatRange(step.start, step.end, lang)} · {model.volcano.name[lang]}
      </p>
      {shown.length ? (
        <Timeline tracks={shown} from={story.span.start} to={story.span.end} cursor={cursor} onCursor={setCursor} dataAsOf={story.dataAsOf} highlight={[step.start, step.end]} compact />
      ) : null}
      {step.assets?.length ? (
        <div className="grid grid-cols-2 gap-2">
          {step.assets.map((a) => (
            <figure key={a.url} className="m-0 flex flex-col gap-1">
              <img src={assetUrl(root, a.url)} alt={a.caption?.[lang] ?? a.sensor ?? ""} width={a.width} height={a.height} className="h-auto w-full rounded-sm" loading="lazy" />
              <figcaption className="text-xs text-muted-foreground">
                {a.caption?.[lang]} · {a.credit}
              </figcaption>
            </figure>
          ))}
        </div>
      ) : null}
      {!shown.length && !step.assets?.length ? (
        <div className="flex flex-col gap-1">
          {model.exposure.rings.map((r) => (
            <p key={r.radiusKm} className="m-0">
              <span className="font-heading text-3xl font-semibold tabular">≈ {formatNumber(r.population, lang, 0)}</span>{" "}
              <span className="text-sm text-muted-foreground">{lang === "ja" ? `${r.radiusKm} km圏の人口（WorldPop ${r.year}年）` : `people within ${r.radiusKm} km (WorldPop ${r.year})`}</span>
            </p>
          ))}
          <DataThrough date={story.dataAsOf} />
        </div>
      ) : null}
    </div>
  );
}

function StoryView({ story }: { story: Story }) {
  const t = useT();
  const { lang } = useLang();
  const model = use(loadVolcano(story.volcanoFile ?? `volcano/${story.volcanoId}.json`));
  const tracks = useMemo(() => (model ? buildTracks(model, 15) : []), [model]);
  const steps = useMemo(() => {
    const extra = model ? nearbyStep(model, story) : null;
    return extra ? [...story.steps, extra] : story.steps;
  }, [model, story]);
  // Phones: the story visual (several timelines, or two pictures) is far taller than the 45svh panel Scrollytelling
  // pins above the text, so pinned it covered every step while scrolling. Below md each step carries its own visual
  // inline, after its text, and the pinned panel is not rendered.
  const wide = useWide();
  useEffect(() => {
    document.title = `${story.title[lang]} · Plumes`;
  }, [story, lang]);
  if (!model) return <NotFoundPage />;
  return (
    <Page
      eyebrow={
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink asChild>
                <AppLink to="stories">{t("Stories", "ストーリー")}</AppLink>
              </BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbPage>{story.title[lang]}</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
      }
      title={story.title[lang]}
      lede={story.summary?.[lang]}
    >
      {story.status === "draft" ? (
        <Alert data-story-draft>
          <AlertTitle>{t("Draft, not yet reviewed", "下書き（未レビュー）")}</AlertTitle>
          <AlertDescription>
            {t(
              "Generated from the data with fixed sentence templates. It is shown only with the preview link until Kurt has reviewed it.",
              "データから固定の文型で生成した下書きです。レビューが済むまで、プレビュー用のリンクでのみ表示されます。",
            )}
          </AlertDescription>
        </Alert>
      ) : null}
      <p className="m-0 text-sm text-muted-foreground">
        {t(`Story · ${steps.length} steps · scroll, or move through the steps with Tab`, `ストーリー · ${steps.length}段階 · スクロールまたはTabキーで移動`)}
      </p>
      <Scrollytelling
        idPrefix="step"
        className={wide ? undefined : "[&_[data-slot=scrollytelling-step]]:scroll-mt-[calc(var(--scrolly-top)+1rem)] [&>[data-slot=scrollytelling-visual]]:hidden"}
        stepsLabel={t("Story steps", "ストーリーの段階")}
        steps={steps.map((s) => ({
          id: s.id,
          content: (
            <div className="flex flex-col gap-2">
              <p className="m-0 font-mono text-[11px] tracking-wide text-muted-foreground uppercase">{formatRange(s.start, s.end, lang)}</p>
              <h2 className="m-0 font-heading text-xl font-semibold">{s.title[lang]}</h2>
              <StepText step={s} />
              {wide ? null : <StepVisual story={story} model={model} step={s} tracks={tracks} />}
              <DraftBadge status={s.status} />
              <FigureList figures={s.figures} />
            </div>
          ),
        }))}
        visual={({ step }) => {
          if (!wide) return null;
          const s = steps[step] ?? steps[0]!;
          return <StepVisual key={s.id} story={story} model={model} step={s} tracks={tracks} />;
        }}
      />
      <p className="m-0 max-w-prose text-sm text-muted-foreground">
        <T
          en="Every number in this story links to its source and date. Nothing here describes the volcano today; for that, DOST-PHIVOLCS is the sole authority."
          ja="このストーリーのすべての数値には出典と日付のリンクがあります。ここに今日の火山の状態は書かれていません。それについてはDOST-PHIVOLCSが唯一の機関です。"
        />
      </p>
      <p className="m-0">
        <AppLink to="volcano" id={story.volcanoId} query={{ from: null, to: null }} className="underline underline-offset-4">
          {t(`Every record for ${model.volcano.name.en} on one time axis →`, `${model.volcano.name.ja}のすべての記録を見る →`)}
        </AppLink>
      </p>
      <p className="m-0 text-xs text-muted-foreground">
        {t("Story span", "期間")}: {formatDate(story.span.start, lang)} – {formatDate(story.span.end, lang)}
      </p>
    </Page>
  );
}

/** Reviewed stories for everyone; drafts only with ?preview (ST1). In preview a draft replaces the reviewed file. */
export default function StoryPage({ id }: { id: string }) {
  const { preview } = useUrlState();
  const ref = storyRefs(use(loadStoriesIndex()), Boolean(preview)).find((s) => s.id === id);
  if (!ref) return <NotFoundPage />;
  return <StoryLoader file={ref.file} />;
}

function StoryLoader({ file }: { file: string }) {
  const story = use(loadStoryFile(file));
  return story ? <StoryView story={story} /> : <NotFoundPage />;
}
