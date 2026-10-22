import "maplibre-gl/dist/maplibre-gl.css";

// MapLibre 6 derives its worker URL at runtime from import.meta.url, which bundlers cannot see, so the
// self-contained worker file is emitted as an asset and handed to MapLibre explicitly (as in Lights).
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?url";
import * as maplibregl from "maplibre-gl";
import { Protocol } from "pmtiles";

maplibregl.setWorkerUrl(workerUrl);
// Published versions serve national layers as PMTiles (range requests against GitHub Pages / Hugging Face).
maplibregl.addProtocol("pmtiles", new Protocol().tile);

import { applyBasemapTheme } from "@abrycta/akari/maps";
import { useContrast, useLang, useT, useTheme } from "@abrycta/akari/react";
import { flat } from "@abrycta/akari/tokens";
import type { Map as MlMap, StyleSpecification } from "maplibre-gl";
import { useEffect, useRef, useState } from "react";

import type { VolcanoesIndex } from "@contracts/readmodels";

import { formatUrl, navigateHref } from "@/app/url";

import { PH_BOUNDS } from "./geo";

type ThemeKey = "light" | "dark" | "light-hc" | "dark-hc";

/** Akari data colours of the overlays (the legend on the map page uses the same ones). */
const OVERLAY_COLOR = { thermal: "data.cat.4", earthquakes: "data.cat.2" } as const;

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
      { id: "background", type: "background", paint: { "background-color": tokenColor("color.bg", key) } },
      { id: "coastline", type: "line", source: "coast", paint: { "line-color": tokenColor("color.text-muted", key), "line-width": 0.8 } },
    ],
  };
}

/** A national layer drawn over the basemap for one month (thermal detections, earthquakes). */
export interface Overlay {
  id: "thermal" | "earthquakes";
  /** Absolute URL of a GeoJSON file or a PMTiles archive. */
  url: string;
  /** Source layer inside a PMTiles archive. */
  sourceLayer?: string;
  /** Keep only features whose `month` property equals this (files holding several months). */
  month?: string;
  attribution: string;
}

export interface InteractiveMapProps {
  index: VolcanoesIndex;
  styleUrl: string;
  coastUrl: string;
  /** Layers to draw, bottom first; an empty list shows the basemap and the volcanoes only. */
  overlays: Overlay[];
  lang: "en" | "ja";
}

/** The interactive overview map (loaded only when rule 6b allows): basemap, thermal detections, volcano links. */
export default function InteractiveMap({ index, styleUrl, coastUrl, overlays }: Omit<InteractiveMapProps, "lang">) {
  const t = useT();
  const { lang } = useLang();
  const { resolvedTheme } = useTheme();
  const { active: hc } = useContrast();
  const key: ThemeKey = hc ? `${resolvedTheme}-hc` : resolvedTheme;
  const box = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MlMap | null>(null);
  const [ready, setReady] = useState(false);
  const fallback = useRef(false);

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
      fitBoundsOptions: { padding: 24 },
      attributionControl: { compact: true },
      fadeDuration: reduced ? 0 : 300,
      dragRotate: false,
      pitchWithRotate: false,
    });
    map.touchZoomRotate.disableRotation();
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    let loaded = false;
    const toFallback = () => {
      if (loaded || fallback.current) return;
      fallback.current = true;
      map.setStyle(fallbackStyle(coastUrl, key));
    };
    const timer = window.setTimeout(toFallback, 6000);
    map.on("error", () => toFallback());
    map.on("load", () => {
      loaded = true;
      window.clearTimeout(timer);
      setReady(true);
    });
    mapRef.current = map;
    return () => {
      window.clearTimeout(timer);
      map.remove();
      mapRef.current = null;
    };
    // Theme changes are applied below without recreating the map.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [styleUrl, coastUrl]);

  // Basemap colours follow the theme.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    if (fallback.current) {
      if (map.getLayer("background")) map.setPaintProperty("background", "background-color", tokenColor("color.bg", key));
      if (map.getLayer("coastline")) map.setPaintProperty("coastline", "line-color", tokenColor("color.text-muted", key));
    } else applyBasemapTheme(map, resolvedTheme);
    for (const id of ["thermal", "earthquakes"] as const)
      if (map.getLayer(id)) {
        map.setPaintProperty(id, "circle-stroke-color", tokenColor("color.bg", key));
        map.setPaintProperty(id, "circle-color", tokenColor(OVERLAY_COLOR[id], key));
      }
  }, [ready, key, resolvedTheme]);

  // National layers for the chosen month (re-added when the month or the layer set changes).
  const overlayKey = JSON.stringify(overlays);
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    for (const id of ["earthquakes", "thermal"] as const) {
      if (map.getLayer(id)) map.removeLayer(id);
      if (map.getSource(id)) map.removeSource(id);
    }
    for (const o of overlays) {
      const pm = o.url.endsWith(".pmtiles");
      map.addSource(o.id, pm ? { type: "vector", url: `pmtiles://${o.url}`, attribution: o.attribution } : { type: "geojson", data: o.url, attribution: o.attribution });
      map.addLayer({
        id: o.id,
        type: "circle",
        source: o.id,
        ...(pm ? { "source-layer": o.sourceLayer ?? o.id } : {}),
        ...(o.month ? { filter: ["==", ["get", "month"], o.month] } : {}),
        paint: {
          "circle-radius":
            o.id === "earthquakes"
              ? ["interpolate", ["linear"], ["coalesce", ["get", "mag"], 4], 3, 2, 5, 4, 7, 9]
              : ["interpolate", ["linear"], ["zoom"], 5, 2.5, 10, 5],
          "circle-color": tokenColor(OVERLAY_COLOR[o.id], key),
          "circle-opacity": o.id === "earthquakes" ? 0.6 : 0.85,
          "circle-stroke-width": 1,
          "circle-stroke-color": tokenColor("color.bg", key),
        },
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, overlayKey]);

  // Volcano markers: real links (keyboard reachable), deep-record volcanoes labelled.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const markers = index.features.map((f) => {
      const el = document.createElement("a");
      const href = formatUrl({ page: "volcano", id: f.properties.id, lang: null, date: null, from: null, to: null, ring: null });
      el.href = href;
      el.className = "volcano-marker";
      el.dataset.coverage = f.properties.coverage;
      el.setAttribute("aria-label", f.properties.name[lang]);
      const dot = document.createElement("span");
      dot.className = "dot";
      el.append(dot);
      if (f.properties.coverage === "deep") {
        const name = document.createElement("span");
        name.className = "name";
        name.textContent = f.properties.name[lang];
        el.append(name);
      } else el.title = f.properties.name[lang];
      el.addEventListener("click", (e) => {
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
        e.preventDefault();
        navigateHref(href);
        window.scrollTo(0, 0);
      });
      return new maplibregl.Marker({ element: el, anchor: "left", offset: [-12, 0] }).setLngLat(f.geometry.coordinates.slice(0, 2) as [number, number]).addTo(map);
    });
    return () => markers.forEach((m) => m.remove());
  }, [index, lang]);

  return <div ref={box} className="h-full min-h-[360px] w-full" role="region" aria-label={t("Interactive map of the 24 volcanoes", "24火山のインタラクティブ地図")} data-interactive-map />;
}
