// Draws the deformation-velocity frames on the interactive map: from the layer's minzoom, only frames in view, each
// fetched once (one GET of a ~5-15 kB file), decoded, coloured from the theme's diverging ramp and shown as a MapLibre
// image source at the frame's bounds. COMET's reference areas are drawn as small rings.

import type { GeoJSONSource, ImageSource, Map as MlMap } from "maplibre-gl";
import { useEffect, useRef } from "react";

import { type ThemeKey, tokenColour } from "@/lib/tokens";
import type { DeformationFrame, Layer } from "@contracts/readmodels";

import { colourise, decodeFrame, type DecodedFrame, framesInView, imageCoordinates, velocityDomain } from "./deformation";


export interface DeformationOverlay {
  layer: Layer;
  /** Absolute URL of each frame's file. */
  urlOf: (frame: DeformationFrame) => string;
}

const REF = "deformation-ref";
const PREFIX = "deformation-";

function token(id: string, key: ThemeKey): string {
  return tokenColour(id, key);
}

export function rampFor(key: ThemeKey): string[] {
  return [1, 2, 3, 4, 5, 6, 7].map((i) => token(`data.div.${i}`, key));
}

function toDataUrl(d: DecodedFrame, domain: number, ramp: string[]): string {
  const canvas = document.createElement("canvas");
  canvas.width = d.width;
  canvas.height = d.height;
  canvas.getContext("2d")!.putImageData(new ImageData(colourise(d, domain, ramp), d.width, d.height), 0, 0);
  return canvas.toDataURL("image/png");
}

/** Adds, recolours and removes the frame images; `overlay` undefined removes everything. */
export function useDeformation(map: MlMap | null, ready: boolean, overlay: DeformationOverlay | undefined, key: ThemeKey) {
  const decoded = useRef(new Map<string, Promise<DecodedFrame | null>>());
  const shown = useRef(new Map<string, string>()); // frame id -> theme key it was coloured with
  const owner = useRef<MlMap | null>(null);

  useEffect(() => {
    if (!map || !ready) return;
    if (owner.current !== map) {
      shown.current.clear(); // a new map instance starts empty
      owner.current = map;
    }
    const clear = () => {
      for (const id of shown.current.keys()) {
        if (map.getLayer(PREFIX + id)) map.removeLayer(PREFIX + id);
        if (map.getSource(PREFIX + id)) map.removeSource(PREFIX + id);
      }
      shown.current.clear();
      if (map.getLayer(REF)) map.removeLayer(REF);
      if (map.getSource(REF)) map.removeSource(REF);
    };
    if (!overlay?.layer.frames?.length) {
      clear();
      return;
    }
    const { layer, urlOf } = overlay;
    const frames = layer.frames!;
    const domain = velocityDomain(layer);
    const ramp = rampFor(key);
    const minzoom = layer.minzoom ?? 7;
    let live = true;

    // Below the density and circle layers (hexes, thermal, quakes) when they exist; the volcano markers are DOM and stay on top.
    const beforeId = () => ["hexes", "thermal", "quakes"].find((id) => map.getLayer(id));

    const refData = {
      type: "FeatureCollection" as const,
      features: frames.map((f) => ({
        type: "Feature" as const,
        properties: { id: f.id },
        geometry: { type: "Point" as const, coordinates: f.reference },
      })),
    };
    if (map.getSource(REF)) (map.getSource(REF) as GeoJSONSource).setData(refData);
    else map.addSource(REF, { type: "geojson", data: refData });
    if (map.getLayer(REF)) map.removeLayer(REF);
    map.addLayer(
      {
        id: REF,
        type: "circle",
        source: REF,
        minzoom,
        paint: {
          "circle-radius": 4,
          "circle-color": "transparent",
          "circle-stroke-width": 1.5,
          "circle-stroke-color": token("color.text", key),
        },
      },
      beforeId(),
    );

    const draw = async (f: DeformationFrame) => {
      let p = decoded.current.get(f.id);
      if (!p) {
        p = fetch(urlOf(f))
          .then((r) => (r.ok ? r.arrayBuffer() : Promise.reject(new Error(String(r.status)))))
          .then(decodeFrame)
          .catch(() => null);
        decoded.current.set(f.id, p);
      }
      const d = await p;
      if (!live || !d) return;
      const url = toDataUrl(d, domain, ramp);
      const src = map.getSource(PREFIX + f.id) as ImageSource | undefined;
      if (src) src.updateImage({ url, coordinates: imageCoordinates(f) });
      else {
        map.addSource(PREFIX + f.id, {
          type: "image",
          url,
          coordinates: imageCoordinates(f),
        });
        map.addLayer(
          {
            id: PREFIX + f.id,
            type: "raster",
            source: PREFIX + f.id,
            minzoom,
            paint: {
              "raster-opacity": 0.85,
              "raster-resampling": "nearest",
              "raster-fade-duration": 0,
            },
          },
          REF,
        );
      }
      shown.current.set(f.id, key);
    };

    const update = () => {
      if (map.getZoom() < minzoom) return;
      const b = map.getBounds();
      for (const f of framesInView(frames, [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()])) if (shown.current.get(f.id) !== key) void draw(f);
    };
    // Recolour what is already shown when the theme changed.
    for (const id of [...shown.current.keys()]) {
      const f = frames.find((x) => x.id === id);
      if (f && shown.current.get(id) !== key) void draw(f);
    }
    update();
    map.on("moveend", update);
    return () => {
      live = false;
      map.off("moveend", update);
    };
  }, [map, ready, overlay, key]);
}
