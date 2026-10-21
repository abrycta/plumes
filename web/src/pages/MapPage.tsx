import { MapLegendKey, NativeSelect, NativeSelectOption, T, useLang, useT } from "@abrycta/akari/react";
import { lazy, Suspense, use, useEffect, useId, useState } from "react";

import type { Layer } from "@contracts/readmodels";

import { DataThrough } from "@/components/DataThrough";
import { VolcanoList } from "@/components/VolcanoList";
import { loadConfig, loadFile, loadLayers, loadRoot, loadVolcanoes, resolveUrl } from "@/data/load";
import { formatDate } from "@/lib/dates";
import { useRichMedia } from "@/lib/richMedia";
import { StaticMap, type ThermalPoint } from "@/map/StaticMap";

const InteractiveMap = lazy(() => import("@/map/InteractiveMap"));

interface PointCollection {
  features: { geometry: { coordinates: [number, number] }; properties: { frp?: number } }[];
}

function useThermalPoints(layer: Layer | undefined, month: string | null): ThermalPoint[] {
  const path = layer && month && layer.format === "geojson" ? layer.url.replace("{month}", month) : null;
  const [got, setGot] = useState<{ path: string; pts: ThermalPoint[] } | null>(null);
  useEffect(() => {
    if (!path) return;
    let live = true;
    loadFile<PointCollection>(path)
      .then((g) => g.features.map((f) => ({ lon: f.geometry.coordinates[0], lat: f.geometry.coordinates[1], frp: f.properties.frp })))
      .catch(() => [])
      .then((pts) => live && setGot({ path, pts }));
    return () => {
      live = false;
    };
  }, [path]);
  return path && got?.path === path ? got.pts : [];
}

export default function MapPage() {
  const t = useT();
  const { lang } = useLang();
  const index = use(loadVolcanoes());
  const layers = use(loadLayers());
  const config = use(loadConfig());
  const root = use(loadRoot());
  const rich = useRichMedia();
  const thermal = layers.layers.find((l) => l.id === "thermal-detections");
  const months = thermal?.time?.available ?? [];
  const [month, setMonth] = useState<string | null>(months.at(-1) ?? null);
  const [show, setShow] = useState(true);
  const selectId = useId();
  const staticPoints = useThermalPoints(thermal, show && !rich ? month : null);
  useEffect(() => {
    document.title = `${t("Map", "地図")} · Plumes`;
  }, [t]);

  return (
    <div className="flex flex-wrap">
      <section aria-labelledby="map-title" className="relative flex min-w-0 flex-[999_1_640px] flex-col gap-3 border-border px-ak-gutter py-6 md:border-r">
        <div className="flex flex-col gap-1">
          <p className="m-0 font-mono text-[11px] tracking-wide text-muted-foreground uppercase">
            <T en={`${index.features.length} volcanoes · since 2000`} ja={`${index.features.length}火山 · 2000年以降`} />
          </p>
          <h1 id="map-title" className="m-0 font-heading text-2xl leading-tight font-semibold md:text-3xl">
            <T en="Every Philippine volcano, every record, one map." ja="フィリピンのすべての火山、すべての記録を一枚の地図に。" />
          </h1>
        </div>
        <div className="flex flex-wrap items-end gap-x-6 gap-y-2 text-sm">
          {thermal && months.length ? (
            <>
              <label className="flex items-center gap-2">
                <input type="checkbox" checked={show} onChange={(e) => setShow(e.target.checked)} className="size-4 accent-[var(--primary)]" />
                {thermal.title[lang]}
              </label>
              <div className="flex items-center gap-2">
                <label htmlFor={selectId}>{t("Month", "月")}</label>
                <NativeSelect id={selectId} value={month ?? ""} onChange={(e) => setMonth(e.target.value)} disabled={!show}>
                  {months.map((m) => (
                    <NativeSelectOption key={m} value={m}>
                      {formatDate(m, lang)}
                    </NativeSelectOption>
                  ))}
                </NativeSelect>
              </div>
            </>
          ) : null}
          <DataThrough date={root.latest.dataAsOf} />
        </div>
        <div className="relative h-[min(72vh,760px)] min-h-[360px] overflow-hidden rounded-sm border border-border bg-background max-md:h-auto">
          {rich ? (
            <Suspense fallback={<StaticMap index={index} />}>
              <InteractiveMap
                index={index}
                styleUrl={config.basemap?.style ?? "https://tiles.openfreemap.org/styles/positron"}
                coastUrl={resolveUrl("/", config.basemap?.fallback ?? "/basemap/coast.geojson")}
                thermalUrl={thermal && show && month ? resolveUrl(root.versionBase, thermal.url.replace("{month}", month)) : null}
                thermalAttribution={thermal?.attribution}
                thermalSourceLayer={thermal?.sourceLayer}
              />
            </Suspense>
          ) : (
            <StaticMap index={index} thermal={staticPoints} />
          )}
        </div>
        <div className="flex flex-wrap items-start gap-x-8 gap-y-3">
          <MapLegendKey
            title={t("Legend", "凡例")}
            items={[
              { fill: "var(--seal)", label: t("Deep record: PHIVOLCS bulletins, satellites, earthquakes", "詳細な記録:PHIVOLCS火山情報・衛星・地震") },
              { fill: "var(--muted-foreground)", label: t("Satellite and eruption-history record", "衛星と噴火史の記録") },
              ...(thermal ? [{ fill: "var(--chart-4)", label: t("Thermal detection in the chosen month (may be a vegetation fire)", "選んだ月の熱異常検知(植生火災の場合あり)") }] : []),
            ]}
          />
          <p className="m-0 max-w-prose text-xs text-muted-foreground">
            <T
              en="Thermal detections: NASA FIRMS. Basemap: OpenFreeMap © OpenMapTiles © OpenStreetMap contributors, or the Natural Earth coastline. A past record only."
              ja="熱異常検知:NASA FIRMS。背景地図:OpenFreeMap © OpenMapTiles © OpenStreetMap contributors、またはNatural Earthの海岸線。過去の記録のみ。"
            />
          </p>
        </div>
      </section>
      <aside aria-labelledby="list-title" className="flex min-w-0 flex-[1_1_360px] flex-col gap-3 px-ak-gutter py-6 md:max-w-[440px] lg:max-h-[calc(100vh-5rem)] lg:overflow-y-auto">
        <h2 id="list-title" className="m-0 font-heading text-xl font-semibold">
          <T en="Volcanoes" ja="火山" />
        </h2>
        <VolcanoList index={index} compact />
      </aside>
    </div>
  );
}
