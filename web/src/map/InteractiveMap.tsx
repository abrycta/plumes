import "maplibre-gl/dist/maplibre-gl.css";

// MapLibre 6 derives its worker URL at runtime from import.meta.url, which bundlers cannot see, so the
// self-contained worker file is emitted as an asset and handed to MapLibre explicitly (as in Lights).
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?url";
import * as maplibregl from "maplibre-gl";

maplibregl.setWorkerUrl(workerUrl);

import { applyBasemapTheme, stepColor } from "@abrycta/akari/maps";
import { useContrast, useLang, useT, useTheme } from "@abrycta/akari/react";
import type { ExpressionSpecification, GeoJSONSource, Map as MlMap, StyleSpecification } from "maplibre-gl";
import { useEffect, useRef, useState } from "react";

import { type ThemeKey, tokenColour } from "@/lib/tokens";
import type { VolcanoesIndex } from "@contracts/readmodels";

import { formatUrl, navigateHref } from "@/app/url";
import { formatNumber } from "@/lib/format";

import { HEX_BREAKS, type Activity } from "./density";
import { PH_BOUNDS } from "./geo";
import { type DeformationOverlay, useDeformation } from "./useDeformation";
import type { MapGeojson } from "./windowData";


/** Akari data colours of the layers (the legends use the same tokens). */
const LAYER_TOKENS = {
  thermal: "data.cat.4",
  /** Earthquake depth classes: shallow, intermediate, deep. */
  depth: ["data.div.7", "data.div.6", "data.div.5"],
} as const;

function tokenColor(id: string, key: ThemeKey): string {
  return tokenColour(id, key);
}

/** Offline fallback: the bundled Natural Earth coastline only (public domain). */
function fallbackStyle(coastUrl: string, key: ThemeKey): StyleSpecification {
  return {
    version: 8,
    sources: { coast: { type: "geojson", data: coastUrl, attribution: "Natural Earth" } },
    layers: [
      { id: "background", type: "background", paint: { "background-color": tokenColor("color.bg", key) } },
      { id: "coastline", type: "line", source: "coast", paint: { "line-color": tokenColor("color.text-muted", key), "line-width": 0.8 } },
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
  /** The /embed krtmtthw.dev frames: a non-interactive map with no links, controls or attribution box. */
  embed?: EmbedOptions;
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
}

const EMPTY: GeoJSON.FeatureCollection = { type: "FeatureCollection", features: [] };
const LAYERS = ["hexes", "thermal", "quakes"] as const;

/** The interactive overview map (loaded only when rule 6b allows): basemap, density, points, volcano links. */
export default function InteractiveMap({ index, styleUrl, coastUrl, data, show = { hexes: true, thermal: true, quakes: true }, activity, eruptions, formatMonth, deformation, embed }: InteractiveMapProps) {
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
      map.on("resize", () =>
        map.fitBounds(
          [
            [PH_BOUNDS[0], PH_BOUNDS[1]],
            [PH_BOUNDS[2], PH_BOUNDS[3]],
          ],
          { padding: embed.padding, animate: false },
        ),
      );
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
      map.addLayer({ id: "hexes", type: "fill", source: "hexes", paint: { "fill-opacity": ["interpolate", ["linear"], ["zoom"], 5, 0.7, 9, 0.2] } });
      map.addLayer({
        id: "thermal",
        type: "circle",
        source: "thermal",
        paint: {
          "circle-radius": ["*", k, ["interpolate", ["linear"], ["zoom"], 5, ["case", ["==", ["get", "near"], 1], 2.5, 1.4], 10, ["case", ["==", ["get", "near"], 1], 5, 3]]],
          "circle-opacity": ["case", ["==", ["get", "near"], 1], 0.9, 0.22],
          "circle-stroke-width": ["case", ["==", ["get", "near"], 1], 0.75 * k, 0],
        },
      });
      map.addLayer({
        id: "quakes",
        type: "circle",
        source: "quakes",
        paint: {
          "circle-radius": ["*", k, ["interpolate", ["linear"], ["get", "mag"], 2.5, 2, 4, 3.5, 5, 6, 6, 10, 7.5, 16]],
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
      if (map.getLayer("background")) map.setPaintProperty("background", "background-color", tokenColor("color.bg", key));
      if (map.getLayer("coastline")) map.setPaintProperty("coastline", "line-color", tokenColor("color.text-muted", key));
    } else applyBasemapTheme(map, resolvedTheme);
    const bg = tokenColor("color.bg", key);
    const depth = ["match", ["get", "depth"], 1, tokenColor(LAYER_TOKENS.depth[1], key), 2, tokenColor(LAYER_TOKENS.depth[2], key), tokenColor(LAYER_TOKENS.depth[0], key)] as ExpressionSpecification;
    map.setPaintProperty("hexes", "fill-color", stepColor("count", HEX_BREAKS, { scale: "seq", theme: resolvedTheme }) as ExpressionSpecification);
    map.setPaintProperty("hexes", "fill-outline-color", bg);
    map.setPaintProperty("thermal", "circle-color", tokenColor(LAYER_TOKENS.thermal, key));
    map.setPaintProperty("thermal", "circle-stroke-color", bg);
    map.setPaintProperty("quakes", "circle-color", depth);
    map.setPaintProperty("quakes", "circle-stroke-color", depth);
  }, [ready, key, resolvedTheme]);

  // The window's data.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    for (const id of LAYERS) (map.getSource(id) as GeoJSONSource | undefined)?.setData(data?.[id] ?? EMPTY);
    if (embed && data && !signalled.current) {
      signalled.current = true;
      map.once("idle", () => embed.onReady());
    }
  }, [ready, data, embed]);

  useDeformation(map, ready > 0, deformation, key);

  // Layer toggles.
  const showKey = `${show.hexes}${show.thermal}${show.quakes}`;
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    for (const id of LAYERS) if (map.getLayer(id)) map.setLayoutProperty(id, "visibility", show[id] ? "visible" : "none");
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
      el.dataset.coverage = f.properties.coverage;
      if (erupted) el.dataset.erupted = "";
      // Activity halo: 0 to 4 steps, by the order of magnitude of the window's counts around the volcano.
      el.dataset.activity = String(total ? Math.min(4, 1 + Math.floor(Math.log10(total))) : 0);
      const stats = a && total ? `${formatNumber(a.thermal, lang)} · ${formatNumber(a.quakes, lang)}` : "";
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
        if (stats || erupted) {
          const s = document.createElement("span");
          s.className = "stats";
          if (a && total) {
            const fire = document.createElement("span");
            fire.className = "stat thermal";
            fire.textContent = formatNumber(a.thermal, lang);
            const quake = document.createElement("span");
            quake.className = "stat quakes";
            quake.textContent = formatNumber(a.quakes, lang);
            s.append(fire, quake);
          }
          if (erupted && formatMonth) {
            const e = document.createElement("span");
            e.className = "stat erupted";
            e.textContent = t(`erupted ${formatMonth(erupted)}`, `${formatMonth(erupted)}噴火`);
            s.append(e);
          }
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
    return () => markers.forEach((m) => m.remove());
    // embed and formatMonth are fixed for the map's life; activity and eruptions are compared by value.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [index, lang, activityKey, eruptionKey]);

  return <div ref={box} className={embed ? "h-full w-full" : "h-full min-h-90 w-full"} role="region" aria-label={t("Interactive map of the 24 volcanoes", "24火山のインタラクティブ地図")} data-interactive-map />;
}
