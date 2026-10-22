import { Checkbox, Label, MapLegend, MapLegendKey, T, useLang, useT } from "@abrycta/akari/react";
import { lazy, Suspense, use, useEffect, useMemo, useState } from "react";

import { DataThrough } from "@/components/DataThrough";
import { VolcanoList } from "@/components/VolcanoList";
import { loadConfig, loadLayers, loadRoot, loadVolcanoes, resolveUrl } from "@/data/load";
import { layerMonths } from "@/data/layers";
import { useRichMedia } from "@/lib/richMedia";
import { framePath } from "@/map/deformation";
import { DeformationKey } from "@/map/DeformationKey";
import { HEX_BREAKS, quakesPerMonth, WINDOW_MONTHS, windowMonths } from "@/map/density";
import type { LayerToggles } from "@/map/InteractiveMap";
import { MapTimeline } from "@/map/MapTimeline";
import { loadAllQuakes, type QuakePt } from "@/map/points";
import { StaticMap } from "@/map/StaticMap";
import { toGeojson, useWindowData } from "@/map/windowData";

const InteractiveMap = lazy(() => import("@/map/InteractiveMap"));

const SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const LONG = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

function formatMonth(m: string, lang: "en" | "ja", style: "short" | "long" = "short"): string {
  const [y, mo] = m.split("-").map(Number) as [number, number];
  if (!y || !mo) return m;
  return lang === "ja" ? `${y}年${mo}月` : `${(style === "long" ? LONG : SHORT)[mo - 1]} ${y}`;
}

export default function MapPage() {
  const t = useT();
  const { lang } = useLang();
  const index = use(loadVolcanoes());
  const layers = use(loadLayers());
  const config = use(loadConfig());
  const root = use(loadRoot());
  const rich = useRichMedia();
  const thermalLayer = layers.layers.find((l) => l.id === "thermal-detections");
  const quakeLayer = layers.layers.find((l) => l.id === "earthquakes-usgs");
  // COMET deformation velocity (LAYERS-PLAN §3.1): off by default, interactive map only, drawn from zoom 7.
  const defo = layers.layers.find((l) => l.id === "deformation-velocity" && l.frames?.length);
  const [showDefo, setShowDefo] = useState(false);
  const deformation = useMemo(
    () => (defo && showDefo ? { layer: defo, urlOf: (f: Parameters<typeof framePath>[1]) => resolveUrl(root.versionBase, framePath(defo, f)) } : undefined),
    [defo, showDefo, root.versionBase],
  );
  // Every month any national layer offers, up to the data's last day.
  const record = useMemo(() => [...new Set([...layerMonths(thermalLayer), ...layerMonths(quakeLayer)])].filter((m) => m <= root.latest.dataAsOf.slice(0, 7)).sort(), [thermalLayer, quakeLayer, root]);
  // The default window: the 12 months up to the data's last month.
  const [end, setEnd] = useState(record.length - 1);
  const months = useMemo(() => (record[end] ? windowMonths(record[end], WINDOW_MONTHS) : []), [record, end]);
  const { data, loading } = useWindowData(layers, root.versionBase, index, months);
  const geojson = useMemo(() => (data ? toGeojson(data) : null), [data]);
  const [show, setShow] = useState<LayerToggles>({ hexes: true, thermal: true, quakes: true });
  const fmt = (m: string, style: "short" | "long" = "short") => formatMonth(m, lang, style);

  // The whole record's earthquakes per month (the timeline strip); the same cached file as the window's.
  const [allQuakes, setAllQuakes] = useState<QuakePt[] | null>(null);
  useEffect(() => {
    let live = true;
    if (quakeLayer) void loadAllQuakes(quakeLayer, root.versionBase, record).then((q) => live && setAllQuakes(q), () => live && setAllQuakes([]));
    return () => {
      live = false;
    };
  }, [quakeLayer, root, record]);
  const recordQuakes = useMemo(() => (allQuakes ? quakesPerMonth(record, allQuakes) : null), [allQuakes, record]);

  // Volcanoes whose last eruption began inside the window.
  const eruptions = useMemo(() => {
    const set = new Set(months);
    return new Map(index.features.map((f) => [f.properties.id, (f.properties.lastEruption?.start ?? "").slice(0, 7)] as const).filter(([, m]) => set.has(m)));
  }, [index, months]);

  const totals = data
    ? { thermal: data.thermal.length, near: data.thermal.filter((p) => p.near).length, quakes: data.quakes.length }
    : null;

  useEffect(() => {
    document.title = `${t("Map", "地図")} · Plumes`;
  }, [t]);

  const toggle = (id: keyof LayerToggles, label: string) => (
    <div className="flex items-center gap-2">
      <Checkbox id={`layer-${id}`} checked={show[id]} onCheckedChange={(v) => setShow((s) => ({ ...s, [id]: v === true }))} />
      <Label htmlFor={`layer-${id}`} className="text-ak-sm font-normal">
        {label}
      </Label>
    </div>
  );

  return (
    <div className="flex flex-wrap">
      <section aria-labelledby="map-title" className="relative flex min-w-0 flex-[999_1_640px] flex-col gap-3 border-border px-ak-gutter py-6 md:border-r">
        <div className="flex flex-col gap-1">
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
        <div className="relative h-[min(72vh,760px)] min-h-90 overflow-hidden rounded-sm border border-border bg-background max-md:h-auto" aria-busy={loading}>
          {rich ? (
            <Suspense fallback={<StaticMap index={index} data={data} />}>
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
              />
            </Suspense>
          ) : (
            <StaticMap index={index} data={data} />
          )}
        </div>
        {deformation ? <DeformationKey layer={deformation.layer} names={Object.fromEntries(index.features.map((f) => [f.properties.id, f.properties.name[lang]]))} /> : null}
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
                    { fill: "cat-4", label: t("Thermal detection within 15 km of a volcano, or flagged volcanic by FIRMS", "火山から15 km以内、またはFIRMSが火山と判定した熱異常") },
                    { fill: "cat-4", opacity: 0.25, label: t("Thermal detection farther away (mostly vegetation fires)", "それ以外の熱異常(多くは植生火災)") },
                  ]
                : []),
              ...(quakeLayer
                ? [
                    { fill: "div-7", label: t("Earthquake, shallow (under 70 km); size by magnitude", "地震・浅発(70 km未満)、大きさはマグニチュード") },
                    { fill: "div-6", label: t("Earthquake, intermediate (70–300 km)", "地震・やや深発(70〜300 km)") },
                    { fill: "div-5", label: t("Earthquake, deep (300 km and more)", "地震・深発(300 km以上)") },
                  ]
                : []),
            ]}
          />
          <MapLegendKey
            title={t("Volcanoes", "火山")}
            items={[
              { fill: "var(--seal)", label: t("Deep record: PHIVOLCS bulletins, satellites, earthquakes", "詳細な記録:PHIVOLCS火山情報・衛星・地震") },
              { fill: "muted", label: t("Satellite and eruption-history record", "衛星と噴火史の記録") },
              { fill: "var(--seal)", opacity: 0.35, label: t("Halo: the window's thermal detections (15 km) and earthquakes (30 km); numbers on the label", "光輪:期間内の熱異常(15 km)と地震(30 km)、数はラベルに表示") },
              { fill: "none", label: t("Outlined: an eruption began in the window", "縁取り:期間内に噴火開始") },
            ]}
          />
          <p className="m-0 max-w-prose text-ak-xs text-muted-foreground">
            <T
              en="Thermal detections: NASA FIRMS. Earthquakes: USGS ComCat. Basemap: OpenFreeMap © OpenMapTiles © OpenStreetMap contributors, or the Natural Earth coastline. A past record only."
              ja="熱異常検知:NASA FIRMS。地震:USGS ComCat。背景地図:OpenFreeMap © OpenMapTiles © OpenStreetMap contributors、またはNatural Earthの海岸線。過去の記録のみ。"
            />
          </p>
        </div>
      </section>
      <aside aria-labelledby="list-title" className="flex min-w-0 flex-[1_1_360px] flex-col gap-3 px-ak-gutter py-6 md:max-w-[440px] lg:max-h-[calc(100vh-5rem)] lg:overflow-y-auto">
        <h2 id="list-title" className="m-0 font-heading text-ak-subsection font-semibold">
          <T en="Volcanoes" ja="火山" />
        </h2>
        <VolcanoList index={index} compact />
      </aside>
    </div>
  );
}
