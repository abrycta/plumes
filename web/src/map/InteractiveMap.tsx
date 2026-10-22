import "maplibre-gl/dist/maplibre-gl.css";

// MapLibre 6 derives its worker URL at runtime from import.meta.url, which bundlers cannot see, so the
// self-contained worker file is emitted as an asset and handed to MapLibre explicitly (as in Lights).
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?url";
import * as maplibregl from "maplibre-gl";

maplibregl.setWorkerUrl(workerUrl);

import { applyBasemapTheme, coastlineLayer, stepColor } from "@abrycta/akari/maps";
import { useContrast, useLang, useT, useTheme } from "@abrycta/akari/react";
import { flat } from "@abrycta/akari/tokens";
import type { ExpressionSpecification, GeoJSONSource, LayerSpecification, Map as MlMap, StyleSpecification } from "maplibre-gl";
import { useEffect, useRef, useState } from "react";

import type { VolcanoesIndex } from "@contracts/readmodels";

import { formatUrl, navigateHref } from "@/app/url";
import { formatNumber } from "@/lib/format";

import { HEX_BREAKS, type Activity } from "./density";
import { PH_BOUNDS } from "./geo";
import { LAYER_TOKENS, layerVar } from "./layerColors";
import { MapGlyph } from "./MapGlyph";
import { removeSo2, showSo2 } from "./so2Overlay";
import { type DeformationOverlay, useDeformation } from "./useDeformation";
import type { MapGeojson } from "./windowData";

type ThemeKey = "light" | "dark" | "light-hc" | "dark-hc";

function tokenColor(id: string, key: ThemeKey): string {
  const t = (flat as unknown as Record<string, Record<string, string>>)[id];
  return t?.[key] ?? t?.light ?? "#888888";
}

/** Offline fallback: the bundled Natural Earth coastline only (public domain). */
function fallbackStyle(coastUrl: string, key: ThemeKey): StyleSpecification {
  return {
    version: 8,
    sources: { coast: { type: "geojson", data: coastUrl, attribution: "Natural Earth" } },
    layers: [
      { id: "background", type: "background", paint: { "background-color": tokenColor("map.background", key) } },
      { id: "coastline", type: "line", source: "coast", paint: { "line-color": tokenColor("map.coast", key), "line-width": 0.8 } },
    ],
  };
}

export interface LayerToggles {
  hexes: boolean;
  thermal: boolean;
  quakes: boolean;
}

export interface InteractiveMapProps {
  index: VolcanoesIndex;
  styleUrl: string;
  coastUrl: string;
  /** The window's layers (null while the first window loads: the basemap and the volcanoes only). */
  data: MapGeojson | null;
  show?: LayerToggles;
  /** Per-volcano counts in the window, shown on the markers. */
  activity?: Map<string, Activity>;
  /** Volcanoes whose last eruption began inside the window, with its month. */
  eruptions?: Map<string, string>;
  /** Formats a month for the marker's eruption note. */
  formatMonth?: (m: string) => string;
  /** The deformation-velocity frames (drawn from the layer's minzoom, below the overlays). */
  deformation?: DeformationOverlay;
  /** The national SO₂ month (so2-monthly): its file URL and legend stops; drawn below every other data layer. */
  so2?: { url: string; stops: number[] };
  /** The /embed krtmtthw.dev frames: a non-interactive map with no links, controls or attribution box. */
  embed?: EmbedOptions;
  /** /embed tour stop: the map centred on a volcano at this zoom (null: the whole country). */
  focus?: { center: [number, number]; zoom: number } | null;
}

export interface EmbedOptions {
  /** Device pixels per CSS pixel for the canvas (`?pr=` from the parent, capped at 2). */
  pixelRatio: number;
  /** Padding around the Philippines when the map fits it. */
  padding: number;
  /** Marker and point size factor (the desktop frame is shown scaled down to about half). */
  scale: number;
  /** Called once, when the first full frame with its layers is drawn. */
  onReady: () => void;
  /** Called after every data change once the map has drawn it (the tour fades back in then). */
  onDrawn?: () => void;
}

const EMPTY: GeoJSON.FeatureCollection = { type: "FeatureCollection", features: [] };
const LAYERS = ["hexes", "thermal", "quakes"] as const;

/** The interactive overview map (loaded only when rule 6b allows): basemap, density, points, volcano links. */
export default function InteractiveMap({ index, styleUrl, coastUrl, data, show = { hexes: true, thermal: true, quakes: true }, activity, eruptions, formatMonth, deformation, so2, embed, focus = null }: InteractiveMapProps) {
  const focusRef = useRef(focus);
  useEffect(() => {
    focusRef.current = focus;
  });
  const t = useT();
  const { lang } = useLang();
  const { resolvedTheme } = useTheme();
  const { active: hc } = useContrast();
  const key: ThemeKey = hc ? `${resolvedTheme}-hc` : resolvedTheme;
  const box = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MlMap | null>(null);
  const [ready, setReady] = useState(0);
  const [map, setMap] = useState<MlMap | null>(null);
  const fallback = useRef(false);
  const signalled = useRef(false);
  // The glyph still covers the map until its first full frame with data (MapGlyph).
  const [drawn, setDrawn] = useState(false);
  const k = embed?.scale ?? 1;

  useEffect(() => {
    if (!box.current) return;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const map = new maplibregl.Map({
      container: box.current,
      style: styleUrl,
      bounds: [
        [PH_BOUNDS[0], PH_BOUNDS[1]],
        [PH_BOUNDS[2], PH_BOUNDS[3]],
      ],
      fitBoundsOptions: { padding: embed?.padding ?? 24 },
      // The embed names its sources in its own caption (no links out of the frame).
      attributionControl: embed ? false : { compact: true },
      fadeDuration: reduced || embed ? 0 : 300,
      dragRotate: false,
      pitchWithRotate: false,
      // A phone-sized frame would fit the islands at a zoom too low to read: the embed never goes under 4, so a phone
      // shows Luzon to the Visayas (decision P1: Taal, Mayon, Bulusan, Kanlaon); larger frames fit the whole country.
      ...(embed ? { interactive: false, pixelRatio: embed.pixelRatio, minZoom: 4 } : {}),
    });
    if (embed)
      // A rotation or a mode change resizes the frame: fit the Philippines again (never a cropped or scaled view).
      map.on("resize", () => {
        const f = focusRef.current;
        if (f) map.jumpTo({ center: f.center, zoom: f.zoom });
        else
          map.fitBounds(
            [
              [PH_BOUNDS[0], PH_BOUNDS[1]],
              [PH_BOUNDS[2], PH_BOUNDS[3]],
            ],
            { padding: embed.padding, animate: false },
          );
      });
    else {
      map.touchZoomRotate.disableRotation();
      map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    }
    let loaded = false;
    const toFallback = () => {
      if (loaded || fallback.current) return;
      fallback.current = true;
      map.setStyle(fallbackStyle(coastUrl, key));
    };
    const timer = window.setTimeout(toFallback, 6000);
    map.on("error", () => toFallback());
    // Every (re)loaded style gets the data layers again; `ready` counts styles so the effects below re-run.
    map.on("style.load", () => {
      loaded = true;
      window.clearTimeout(timer);
      for (const id of LAYERS) if (!map.getSource(id)) map.addSource(id, { type: "geojson", data: EMPTY, ...(id === "thermal" ? { attribution: "NASA FIRMS" } : id === "quakes" ? { attribution: "USGS" } : {}) });
      map.addLayer({ id: "hexes", type: "fill", source: "hexes", paint: { "fill-opacity": ["interpolate", ["linear"], ["zoom"], 5, 0.7, 9, 0.45] } });
      map.addLayer({
        id: "thermal",
        type: "circle",
        source: "thermal",
        paint: {
          "circle-radius": ["*", k, ["interpolate", ["linear"], ["zoom"], 5, ["case", ["==", ["get", "near"], 1], 2.5, 1.4], 10, ["case", ["==", ["get", "near"], 1], 5, 3]]],
          "circle-opacity": ["case", ["==", ["get", "near"], 1], 0.9, 0.5],
          "circle-stroke-width": ["case", ["==", ["get", "near"], 1], 0.75 * k, 0.5 * k],
        },
      });
      // A halo ring under each quake ring (Akari map.halo), so the rings read on the density hexagons too.
      map.addLayer({
        id: "quakes-halo",
        type: "circle",
        source: "quakes",
        paint: {
          "circle-radius": ["*", k, ["interpolate", ["linear"], ["get", "mag"], 2.5, 1.2, 4, 1.75, 5, 3, 6, 5, 7.5, 8]],
          "circle-opacity": 0,
          "circle-stroke-width": 2.25 * k,
        },
      });
      map.addLayer({
        id: "quakes",
        type: "circle",
        source: "quakes",
        paint: {
          "circle-radius": ["*", k, ["interpolate", ["linear"], ["get", "mag"], 2.5, 1.2, 4, 1.75, 5, 3, 6, 5, 7.5, 8]],
          "circle-opacity": 0.25,
          "circle-stroke-width": 0.75 * k,
          "circle-stroke-opacity": 0.9,
        },
      });
      setReady((n) => n + 1);
      setMap(map);
    });
    mapRef.current = map;
    return () => {
      window.clearTimeout(timer);
      map.remove();
      mapRef.current = null;
      setMap(null);
    };
    // Theme changes are applied below without recreating the map.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [styleUrl, coastUrl]);

  // Colours follow the theme (basemap and data layers).
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    if (fallback.current) {
      if (map.getLayer("background")) map.setPaintProperty("background", "background-color", tokenColor("map.background", key));
      if (map.getLayer("coastline")) map.setPaintProperty("coastline", "line-color", tokenColor("map.coast", key));
    } else {
      applyBasemapTheme(map, key);
      // A coastline on the water polygons' edges (OpenMapTiles "water"), above the water fill.
      const coast = coastlineLayer({ id: "akari-coastline", source: "openmaptiles", theme: key });
      if (map.getSource("openmaptiles") && !map.getLayer(coast.id)) {
        const layers = map.getStyle().layers ?? [];
        const i = layers.map((l) => l.id).lastIndexOf("water");
        map.addLayer(coast as unknown as LayerSpecification, i >= 0 ? layers[i + 1]?.id : undefined);
      } else if (map.getLayer(coast.id)) map.setPaintProperty(coast.id, "line-color", coast.paint["line-color"]);
    }
    const bg = tokenColor("map.halo", key);
    const depth = ["match", ["get", "depth"], 1, tokenColor(LAYER_TOKENS.depth[1], key), 2, tokenColor(LAYER_TOKENS.depth[2], key), tokenColor(LAYER_TOKENS.depth[0], key)] as ExpressionSpecification;
    map.setPaintProperty("hexes", "fill-color", stepColor("count", HEX_BREAKS, { scale: "seq", theme: resolvedTheme }) as ExpressionSpecification);
    map.setPaintProperty("hexes", "fill-outline-color", bg);
    map.setPaintProperty("thermal", "circle-color", tokenColor(LAYER_TOKENS.thermal, key));
    map.setPaintProperty("thermal", "circle-stroke-color", bg);
    map.setPaintProperty("quakes", "circle-color", depth);
    map.setPaintProperty("quakes", "circle-stroke-color", depth);
    map.setPaintProperty("quakes-halo", "circle-stroke-color", bg);
  }, [ready, key, resolvedTheme]);

  // The embed's tour stop: centre on its volcano (before the window's data, so the next idle has both).
  const focusKey = focus ? `${focus.center.join(",")}@${focus.zoom}` : "";
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready || !embed) return;
    if (focus) map.jumpTo({ center: focus.center, zoom: focus.zoom });
    // embed is fixed for the map's life.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, focusKey]);

  // The window's data.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    for (const id of LAYERS) (map.getSource(id) as GeoJSONSource | undefined)?.setData(data?.[id] ?? EMPTY);
    // The first idle with the window's data drawn: the glyph still lifts, and the embed is ready.
    if (data && !signalled.current) {
      signalled.current = true;
      map.once("idle", () => {
        setDrawn(true);
        embed?.onReady();
      });
    } else if (embed?.onDrawn && data) map.once("idle", embed.onDrawn);
  }, [ready, data, embed]);

  useDeformation(map, ready > 0, deformation, key);

  // SO₂ month: below the deformation frames, hexagons, fires and quakes, so they stay readable.
  const so2Key = so2 ? `${so2.url}|${so2.stops.join()}` : "";
  const so2Want = useRef("");
  useEffect(() => {
    const map = mapRef.current;
    so2Want.current = so2Key;
    if (!map || !ready) return;
    if (!so2) {
      removeSo2(map);
      return;
    }
    const below = map.getStyle().layers.find((l) => l.id.startsWith("deformation-") || (LAYERS as readonly string[]).includes(l.id) || l.id === "quakes-halo")?.id;
    showSo2(map, so2.url, key, so2.stops, below)
      .then(() => {
        // Switched off while this month was loading: take it away again.
        if (!so2Want.current) removeSo2(map);
      })
      .catch(() => removeSo2(map));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, so2Key, key]);

  // Layer toggles.
  const showKey = `${show.hexes}${show.thermal}${show.quakes}`;
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    for (const id of LAYERS) if (map.getLayer(id)) map.setLayoutProperty(id, "visibility", show[id] ? "visible" : "none");
    if (map.getLayer("quakes-halo")) map.setLayoutProperty("quakes-halo", "visibility", show.quakes ? "visible" : "none");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, showKey]);

  // Volcano markers: real links (keyboard reachable), with the window's counts and an eruption ring.
  const activityKey = activity ? [...activity].map(([id, a]) => `${id}:${a.thermal}:${a.quakes}`).join() : "";
  const eruptionKey = eruptions ? [...eruptions].join() : "";
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const markers = index.features.map((f) => {
      const id = f.properties.id;
      const name = f.properties.name[lang];
      const a = activity?.get(id);
      const erupted = eruptions?.get(id);
      const total = (a?.thermal ?? 0) + (a?.quakes ?? 0);
      // The embed's markers are plain labels: live embeds carry no links (workspace rule 6c).
      const el: HTMLElement = document.createElement(embed ? "span" : "a");
      const href = formatUrl({ page: "volcano", id, lang: null, date: null, from: null, to: null, ring: null });
      if (el instanceof HTMLAnchorElement) el.href = href;
      el.className = "volcano-marker";
      // The count marks use the layers' own tokens, so they follow layerColors.ts.
      el.style.setProperty("--mk-thermal", layerVar(LAYER_TOKENS.thermal));
      el.style.setProperty("--mk-quakes", layerVar(LAYER_TOKENS.depth[0]));
      el.dataset.coverage = f.properties.coverage;
      if (erupted) el.dataset.erupted = erupted;
      el.dataset.total = String(total);
      // Activity halo: 0 to 4 steps, by the order of magnitude of the window's counts around the volcano.
      el.dataset.activity = String(total ? Math.min(4, 1 + Math.floor(Math.log10(total))) : 0);
      const said = [
        name,
        erupted && formatMonth ? t(`eruption began ${formatMonth(erupted)}`, `${formatMonth(erupted)}に噴火開始`) : "",
        a && total ? t(`${a.thermal} thermal detections within 15 km, ${a.quakes} earthquakes within 30 km in the window`, `期間内に15 km以内の熱異常${a.thermal}件、30 km以内の地震${a.quakes}件`) : "",
      ].filter(Boolean);
      el.setAttribute("aria-label", said.join(", "));
      const dot = document.createElement("span");
      dot.className = "dot";
      el.append(dot);
      const labelled = f.properties.coverage === "deep" || !!erupted || total >= 100;
      if (labelled) {
        const label = document.createElement("span");
        label.className = "label";
        const n = document.createElement("span");
        n.className = "name";
        n.textContent = name;
        label.append(n);
        // One short mono line: "104 fires · 1 quake · erupted Mar 2024", each count led by a legend-coloured mark.
        const parts: HTMLElement[] = [];
        const stat = (kind: string, text: string) => {
          const sp = document.createElement("span");
          sp.className = `stat ${kind}`;
          sp.textContent = text;
          parts.push(sp);
        };
        if (a && total) {
          stat("thermal", t(`${formatNumber(a.thermal, lang)} ${a.thermal === 1 ? "fire" : "fires"}`, `熱異常 ${formatNumber(a.thermal, lang)}`));
          stat("quakes", t(`${formatNumber(a.quakes, lang)} ${a.quakes === 1 ? "quake" : "quakes"}`, `地震 ${formatNumber(a.quakes, lang)}`));
        }
        if (erupted && formatMonth) stat("erupted", t(`erupted ${formatMonth(erupted)}`, `${formatMonth(erupted)}噴火`));
        if (parts.length) {
          const s = document.createElement("span");
          s.className = "stats";
          parts.forEach((sp, i) => {
            if (i) s.append(" · ");
            s.append(sp);
          });
          label.append(s);
        }
        el.append(label);
      } else el.title = said.join(", ");
      if (!embed)
        el.addEventListener("click", (e) => {
          if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
          e.preventDefault();
          navigateHref(href);
          window.scrollTo(0, 0);
        });
      return new maplibregl.Marker({ element: el, anchor: "left", offset: [-12, 0] }).setLngLat(f.geometry.coordinates.slice(0, 2) as [number, number]).addTo(map);
    });
    // Labels never overlap: on a collision the lower-priority label hides (its dot stays, with a hover title).
    // Priority: the most recent eruption first, then the highest activity, then deep coverage.
    const els = markers.map((m) => m.getElement());
    const ranked = els
      .filter((e) => e.querySelector(".label"))
      .sort((x, y) => (y.dataset.erupted ?? "").localeCompare(x.dataset.erupted ?? "") || Number(y.dataset.total) - Number(x.dataset.total) || Number(y.dataset.coverage === "deep") - Number(x.dataset.coverage === "deep"));
    let frame = 0;
    const declutter = () => {
      frame = 0;
      const kept: DOMRect[] = [];
      for (const e of ranked) {
        const label = e.querySelector<HTMLElement>(".label")!;
        const r = label.getBoundingClientRect();
        const hit = kept.some((k) => r.left < k.right + 2 && r.right + 2 > k.left && r.top < k.bottom + 2 && r.bottom + 2 > k.top);
        label.style.visibility = hit ? "hidden" : "";
        if (hit) e.title = e.getAttribute("aria-label") ?? "";
        else {
          e.removeAttribute("title");
          kept.push(r);
        }
      }
    };
    const schedule = () => {
      if (!frame) frame = requestAnimationFrame(declutter);
    };
    schedule();
    map.on("move", schedule);
    map.on("resize", schedule);
    void document.fonts?.ready.then(schedule);
    return () => {
      cancelAnimationFrame(frame);
      map.off("move", schedule);
      map.off("resize", schedule);
      markers.forEach((m) => m.remove());
    };
    // embed and formatMonth are fixed for the map's life; activity and eruptions are compared by value.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [index, lang, activityKey, eruptionKey]);

  return (
    <>
      <div ref={box} className={embed ? "h-full w-full" : "h-full min-h-90 w-full"} role="region" aria-label={t("Interactive map of the 24 volcanoes", "24火山のインタラクティブ地図")} data-interactive-map />
      {drawn ? null : <MapGlyph />}
    </>
  );
}
