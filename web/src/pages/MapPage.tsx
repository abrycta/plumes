import { Checkbox, Label, MapLegend, MapLegendKey, T, useLang, useT } from "@abrycta/akari/react";
import { lazy, Suspense, use, useEffect, useMemo, useState } from "react";

import { DataThrough } from "@/components/DataThrough";
import { VolcanoList } from "@/components/VolcanoList";
import { loadConfig, loadLayers, loadRoot, loadVolcanoes, resolveUrl } from "@/data/load";
import { useRichMedia } from "@/lib/richMedia";
import { framePath } from "@/map/deformation";
import { DeformationKey } from "@/map/DeformationKey";
import { HEX_BREAKS, quakesPerMonth, WINDOW_MONTHS, windowMonths, type Activity, type MonthCount } from "@/map/density";
import type { EmbedOptions, LayerToggles } from "@/map/InteractiveMap";
import { MapTimeline } from "@/map/MapTimeline";
import { LAYER_TOKENS, layerVar, legendFill } from "@/map/layerColors";
import { MapGlyph } from "@/map/MapGlyph";
import { StaticMap } from "@/map/StaticMap";
import { dataStamp } from "@/map/firstWindow";
import { recordMonths, recordQuakeCounts, toGeojson, useWindowData, type MapGeojson } from "@/map/windowData";

const InteractiveMap = lazy(() => import("@/map/InteractiveMap"));

const SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const LONG = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

function formatMonth(m: string, lang: "en" | "ja", style: "short" | "long" = "short"): string {
  const [y, mo] = m.split("-").map(Number) as [number, number];
  if (!y || !mo) return m;
  return lang === "ja" ? `${y}年${mo}月` : `${(style === "long" ? LONG : SHORT)[mo - 1]} ${y}`;
}

/** /embed (krtmtthw.dev's live picture): this page, with its window chosen and its data given by the embed's tour
 *  (src/embed/), the map non-interactive and no links. Compact frames (phones) get the map over the window summary. */
export interface MapPageEmbed {
  /** The window's last month. */
  end: string;
  /** The window's data, from the embed's build-time pack. */
  window: { geojson: MapGeojson; counts: MonthCount[]; activity: Map<string, Activity>; totals: { thermal: number; near: number; quakes: number } } | null;
  map: EmbedOptions;
  compact: boolean;
  /** The tour stop's volcano: the map zooms to it and the list shows it first. */
  focus: string | null;
}

export default function MapPage({ embed }: { embed?: MapPageEmbed } = {}) {
  const t = useT();
  const { lang } = useLang();
  const index = use(loadVolcanoes());
  const layers = use(loadLayers());
  const config = use(loadConfig());
  const root = use(loadRoot());
  const richMedia = useRichMedia();
  const rich = embed ? true : richMedia;
  const thermalLayer = layers.layers.find((l) => l.id === "thermal-detections");
  const quakeLayer = layers.layers.find((l) => l.id === "earthquakes-usgs");
  // COMET deformation velocity (LAYERS-PLAN §3.1): on by default, interactive map only, drawn from national zoom (z4).
  const defo = layers.layers.find((l) => l.id === "deformation-velocity" && l.frames?.length);
  const [showDefo, setShowDefo] = useState(true);
  const deformation = useMemo(
    () => (defo && showDefo ? { layer: defo, urlOf: (f: Parameters<typeof framePath>[1]) => resolveUrl(root.versionBase, framePath(defo, f)) } : undefined),
    [defo, showDefo, root.versionBase],
  );
  // Every month any national layer offers, up to the data's last day.
  const record = useMemo(() => recordMonths(layers, root.latest.dataAsOf), [layers, root]);
  // The default window: the 12 months up to the data's last month.
  const [ownEnd, setEnd] = useState(record.length - 1);
  const embedEnd = embed ? record.indexOf(embed.end) : -1;
  const end = embed ? (embedEnd >= 0 ? embedEnd : record.length - 1) : ownEnd;
  const months = useMemo(() => (record[end] ? windowMonths(record[end], WINDOW_MONTHS) : []), [record, end]);
  // The first window and the timeline strip come from the build-time pack when it matches this data version.
  const stamp = dataStamp(root.latest);
  // The embed brings its own window data: nothing to load here.
  const { data: ownData, loading: ownLoading } = useWindowData(layers, root.versionBase, index, embed ? [] : months, stamp);
  const data = embed ? embed.window : ownData;
  const loading = embed ? !embed.window : ownLoading;
  const ownGeojson = useMemo(() => (ownData ? toGeojson(ownData) : null), [ownData]);
  const geojson = embed ? (embed.window?.geojson ?? null) : ownGeojson;
  const [show, setShow] = useState<LayerToggles>({ hexes: true, thermal: true, quakes: true });
  const fmt = (m: string, style: "short" | "long" = "short") => formatMonth(m, lang, style);

  // The whole record's earthquakes per month (the timeline strip); the same cached file as the window's.
  const [recordQuakes, setRecordQuakes] = useState<number[] | null>(null);
  useEffect(() => {
    let live = true;
    if (quakeLayer)
      void recordQuakeCounts(layers, root.versionBase, record, stamp).then(
        (q) => live && setRecordQuakes(q),
        () => live && setRecordQuakes(quakesPerMonth(record, [])),
      );
    return () => {
      live = false;
    };
  }, [quakeLayer, layers, root, record, stamp]);

  // Volcanoes whose last eruption began inside the window.
  const eruptions = useMemo(() => {
    const set = new Set(months);
    return new Map(index.features.map((f) => [f.properties.id, (f.properties.lastEruption?.start ?? "").slice(0, 7)] as const).filter(([, m]) => set.has(m)));
  }, [index, months]);

  const totals = embed ? (embed.window?.totals ?? null) : ownData ? { thermal: ownData.thermal.length, near: ownData.thermal.filter((p) => p.near).length, quakes: ownData.quakes.length } : null;

  useEffect(() => {
    if (!embed) document.title = `${t("Map", "地図")} · Plumes`;
  }, [t, embed]);

  const toggle = (id: keyof LayerToggles, label: string) => (
    <div className="flex items-center gap-2">
      <Checkbox id={`layer-${id}`} checked={show[id]} onCheckedChange={(v) => setShow((s) => ({ ...s, [id]: v === true }))} />
      <Label htmlFor={`layer-${id}`} className="text-ak-sm font-normal">
        {label}
      </Label>
    </div>
  );

  // The embed's volcano: the map centred on it (its surroundings fill the map, as Lights zooms to a province).
  const focusFeature = embed?.focus ? index.features.find((f) => f.properties.id === embed.focus) : undefined;
  const focus = focusFeature ? { center: focusFeature.geometry.coordinates as [number, number], zoom: 6.5 } : null;

  const summary = (
    <p className="m-0 text-ak-sm tabular" aria-live="polite" data-window-summary>
      {totals ? (
        <T
          en={`${fmt(months[0]!)} – ${fmt(months.at(-1)!)}: ${totals.thermal.toLocaleString("en-GB")} thermal detections (${totals.near.toLocaleString("en-GB")} within 15 km of a volcano) and ${totals.quakes.toLocaleString("en-GB")} earthquakes.`}
          ja={`${fmt(months[0]!)}〜${fmt(months.at(-1)!)}:熱異常検知${totals.thermal.toLocaleString("ja-JP")}件(火山から15 km以内${totals.near.toLocaleString("ja-JP")}件)、地震${totals.quakes.toLocaleString("ja-JP")}件。`}
        />
      ) : (
        <span className="text-muted-foreground">{t("Loading the window's records…", "期間の記録を読み込み中…")}</span>
      )}
    </p>
  );
  const mapBox = (
    <div
      className={embed?.compact ? "relative h-full overflow-hidden bg-background" : embed ? "relative min-h-0 flex-1 overflow-hidden rounded-sm border border-border bg-background" : "relative h-[min(72vh,760px)] min-h-90 overflow-hidden rounded-sm border border-border bg-background max-md:h-auto"}
      aria-busy={loading}
      data-embed-fade={embed ? "" : undefined}
    >
      {rich ? (
        <Suspense fallback={<MapGlyph />}>
          <InteractiveMap
            index={index}
            styleUrl={config.basemap?.style ?? "https://tiles.openfreemap.org/styles/positron"}
            coastUrl={resolveUrl("/", config.basemap?.fallback ?? "/basemap/coast.geojson")}
            data={geojson}
            show={show}
            activity={data?.activity}
            eruptions={eruptions}
            formatMonth={(m) => formatMonth(m, lang)}
            deformation={deformation}
            embed={embed?.map}
            focus={focus}
          />
        </Suspense>
      ) : (
        <>
          <StaticMap index={index} data={ownData} />
          {ownData ? null : <MapGlyph />}
        </>
      )}
    </div>
  );

  // A phone-sized frame: the map over the window summary (as Lights' compact embed), never the page scaled down.
  if (embed?.compact)
    return (
      <div className="flex h-full flex-col bg-background">
        <div className="min-h-0 flex-1">{mapBox}</div>
        <div className="shrink-0 border-t border-border px-ak-1 py-ak-0-5">{summary}</div>
      </div>
    );

  return (
    // The desktop embed frame: the page at the frame's height, the map taking what the controls leave, no page title.
    <div className={embed ? "flex h-full overflow-hidden" : "flex flex-wrap"}>
      <section aria-labelledby="map-title" className={`relative flex min-w-0 flex-[999_1_640px] flex-col gap-3 border-border px-ak-gutter py-6 md:border-r ${embed ? "h-full" : ""}`}>
        <div className={embed ? "sr-only" : "flex flex-col gap-1"}>
          <p className="m-0 font-mono text-ak-2xs tracking-wide text-muted-foreground uppercase">
            <T en={`${index.features.length} volcanoes · since 2000`} ja={`${index.features.length}火山 · 2000年以降`} />
          </p>
          <h1 id="map-title" className="m-0 font-heading text-ak-title font-semibold">
            <T en="Every Philippine volcano, every record, one map." ja="フィリピンのすべての火山、すべての記録を一枚の地図に。" />
          </h1>
        </div>
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
          {thermalLayer ? toggle("hexes", t("Density", "密度")) : null}
          {thermalLayer ? toggle("thermal", t("Thermal detections", "熱異常検知")) : null}
          {quakeLayer ? toggle("quakes", t("Earthquakes", "地震")) : null}
          {defo && rich ? (
            <div className="flex items-center gap-2">
              <Checkbox id="layer-deformation" checked={showDefo} onCheckedChange={(v) => setShowDefo(v === true)} />
              <Label htmlFor="layer-deformation" className="text-ak-sm font-normal">
                {defo.title[lang]}
              </Label>
            </div>
          ) : null}
          <DataThrough date={root.latest.dataAsOf} />
        </div>
        {summary}
        {mapBox}
        {deformation && !embed ? <DeformationKey layer={deformation.layer} names={Object.fromEntries(index.features.map((f) => [f.properties.id, f.properties.name[lang]]))} /> : null}
        {record.length ? <MapTimeline record={record} recordQuakes={recordQuakes} end={end} span={WINDOW_MONTHS} onEnd={(i) => setEnd(Math.max(0, Math.min(record.length - 1, i)))} counts={data?.counts ?? null} formatMonth={fmt} /> : null}
        <div className="flex flex-wrap items-start gap-x-8 gap-y-3">
          {thermalLayer ? (
            <MapLegend
              scale="sequential"
              title={t("Thermal detections per hexagon (about 30 km across)", "六角形ごとの熱異常検知数(差し渡し約30 km)")}
              labels={[`1–${HEX_BREAKS[0] - 1}`, `${HEX_BREAKS[0]}–${HEX_BREAKS[1] - 1}`, `${HEX_BREAKS[1]}–${HEX_BREAKS[2] - 1}`, `${HEX_BREAKS[2]}–${HEX_BREAKS[3] - 1}`, `${HEX_BREAKS[3]}+`]}
            />
          ) : null}
          <MapLegendKey
            title={t("Points", "点")}
            items={[
              ...(thermalLayer
                ? [
                    { fill: legendFill(LAYER_TOKENS.thermal), label: t("Thermal detection within 15 km of a volcano, or flagged volcanic by FIRMS", "火山から15 km以内、またはFIRMSが火山と判定した熱異常") },
                    { fill: legendFill(LAYER_TOKENS.thermal), opacity: 0.5, label: t("Thermal detection farther away (mostly vegetation fires)", "それ以外の熱異常(多くは植生火災)") },
                  ]
                : []),
              ...(quakeLayer
                ? [
                    { fill: layerVar(LAYER_TOKENS.depth[0]), label: t("Earthquake, shallow (under 70 km); size by magnitude", "地震・浅発(70 km未満)、大きさはマグニチュード") },
                    { fill: layerVar(LAYER_TOKENS.depth[1]), label: t("Earthquake, intermediate (70–300 km)", "地震・やや深発(70〜300 km)") },
                    { fill: layerVar(LAYER_TOKENS.depth[2]), label: t("Earthquake, deep (300 km and more)", "地震・深発(300 km以上)") },
                  ]
                : []),
            ]}
          />
          {embed ? null : (
            <>
          <MapLegendKey
            title={t("Volcanoes", "火山")}
            items={[
              { fill: "var(--ak-map-track)", label: t("Deep record: PHIVOLCS bulletins, satellites, earthquakes", "詳細な記録:PHIVOLCS火山情報・衛星・地震") },
              { fill: "muted", label: t("Satellite and eruption-history record", "衛星と噴火史の記録") },
              { fill: "var(--ak-map-track)", opacity: 0.22, label: t("Halo: the window's thermal detections (15 km) and earthquakes (30 km); numbers on the label", "光輪:期間内の熱異常(15 km)と地震(30 km)、数はラベルに表示") },
              { fill: "none", label: t("Outlined: an eruption began in the window", "縁取り:期間内に噴火開始") },
            ]}
          />
          <p className="m-0 max-w-prose text-ak-xs text-muted-foreground">
            <T
              en="Thermal detections: NASA FIRMS. Earthquakes: USGS ComCat. Basemap: OpenFreeMap © OpenMapTiles © OpenStreetMap contributors, or the Natural Earth coastline. A past record only."
              ja="熱異常検知:NASA FIRMS。地震:USGS ComCat。背景地図:OpenFreeMap © OpenMapTiles © OpenStreetMap contributors、またはNatural Earthの海岸線。過去の記録のみ。"
            />
          </p>
            </>
          )}
        </div>
      </section>
      <aside aria-labelledby="list-title" className={`flex min-w-0 flex-[1_1_360px] flex-col gap-3 px-ak-gutter py-6 md:max-w-[440px] ${embed ? "h-full overflow-hidden" : "lg:max-h-[calc(100vh-5rem)] lg:overflow-y-auto"}`}>
        <h2 id="list-title" className="m-0 font-heading text-ak-subsection font-semibold">
          <T en="Volcanoes" ja="火山" />
        </h2>
        <VolcanoList index={index} compact links={!embed} first={embed?.focus ?? undefined} limit={embed ? 6 : undefined} />
      </aside>
    </div>
  );
}
