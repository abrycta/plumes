// The deformation-velocity layer (LAYERS-PLAN §3.1): one small Int16 GeoTIFF per volcano and InSAR frame, fetched whole
// (one GET, no Range request), decoded with `geotiff` and coloured here from Akari's diverging ramp, so light, dark and
// high contrast follow the theme. Values are mm/yr x 10 along the satellite's line of sight; positive = toward it.

import type { DeformationFrame, Layer } from "@contracts/readmodels";

export const NODATA = -32768;
export const SCALE = 10;

/** A decoded frame: north-up rows, `values[row * width + col]` in mm/yr x SCALE, NODATA where empty. */
export interface DecodedFrame {
  width: number;
  height: number;
  values: Int16Array;
}

/** The file of one frame, relative to the version root. */
export function framePath(layer: Layer, frame: DeformationFrame): string {
  return layer.url.replace("{frame}", frame.id);
}

/** The symmetric legend domain in mm/yr, from the layer's end stops (falls back to 30). */
export function velocityDomain(layer: Layer): number {
  const stops = layer.legend?.stops ?? [];
  const d = Math.max(...stops.map(([v]) => Math.abs(v)), 0);
  return d > 0 ? d : 30;
}

/** Frames whose bounds meet the view [w, s, e, n]. */
export function framesInView(frames: DeformationFrame[], view: [number, number, number, number]): DeformationFrame[] {
  const [w, s, e, n] = view;
  return frames.filter((f) => f.bounds[0] < e && f.bounds[2] > w && f.bounds[1] < n && f.bounds[3] > s);
}

function hex(c: string): [number, number, number] {
  const m = /^#?([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})/i.exec(c.trim());
  return m ? [parseInt(m[1]!, 16), parseInt(m[2]!, 16), parseInt(m[3]!, 16)] : [136, 136, 136];
}

/**
 * RGBA pixels for a decoded frame: values clamped to ±domain and interpolated through the ramp (7 colours, away ->
 * toward the satellite); NODATA is transparent.
 */
export function colourise(frame: DecodedFrame, domain: number, ramp: string[]): Uint8ClampedArray<ArrayBuffer> {
  const rgb = ramp.map(hex);
  const out = new Uint8ClampedArray(new ArrayBuffer(frame.width * frame.height * 4));
  const last = rgb.length - 1;
  for (let i = 0; i < frame.values.length; i++) {
    const raw = frame.values[i]!;
    if (raw === NODATA) continue;
    const v = Math.max(-1, Math.min(1, raw / SCALE / domain));
    const pos = ((v + 1) / 2) * last;
    const k = Math.min(Math.floor(pos), last - 1);
    const t = pos - k;
    const a = rgb[k]!;
    const b = rgb[k + 1]!;
    out[i * 4] = a[0] + (b[0] - a[0]) * t;
    out[i * 4 + 1] = a[1] + (b[1] - a[1]) * t;
    out[i * 4 + 2] = a[2] + (b[2] - a[2]) * t;
    out[i * 4 + 3] = 255;
  }
  return out;
}

/** Decode one frame file (the pipeline's Int16 GeoTIFF). */
export async function decodeFrame(buf: ArrayBuffer): Promise<DecodedFrame> {
  const { fromArrayBuffer } = await import("geotiff");
  const tiff = await fromArrayBuffer(buf);
  const image = await tiff.getImage();
  const [band] = (await image.readRasters({
    interleave: false,
  })) as unknown as Int16Array[];
  return {
    width: image.getWidth(),
    height: image.getHeight(),
    values: Int16Array.from(band!),
  };
}

/** Corner coordinates for a MapLibre image source: top-left, top-right, bottom-right, bottom-left. */
export function imageCoordinates(f: DeformationFrame): [[number, number], [number, number], [number, number], [number, number]] {
  const [w, s, e, n] = f.bounds;
  return [
    [w, n],
    [e, n],
    [e, s],
    [w, s],
  ];
}
