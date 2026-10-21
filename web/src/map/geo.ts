// Geometry helpers shared by the static SVG map and the interactive map.

export const PH_BOUNDS: [number, number, number, number] = [116.4, 4.4, 127.2, 21.4];

/** Equirectangular projection scaled by cos(latitude) at the middle of the Philippines (12°N). */
export function project(lon: number, lat: number, bounds = PH_BOUNDS, width = 600): [number, number] {
  const k = Math.cos((12 * Math.PI) / 180);
  const [w, s, e, n] = bounds;
  const scale = width / ((e - w) * k);
  void s;
  return [(lon - w) * k * scale, (n - lat) * scale];
}

export function svgSize(bounds = PH_BOUNDS, width = 600): [number, number] {
  const [, h] = project(bounds[0], bounds[1], bounds, width);
  return [width, Math.round(h)];
}

/** An SVG path for MultiLineString coordinates. */
export function linesToPath(lines: number[][][], bounds = PH_BOUNDS, width = 600): string {
  return lines
    .map((line) =>
      line
        .map(([lon, lat], i) => {
          const [x, y] = project(lon!, lat!, bounds, width);
          return `${i ? "L" : "M"}${x.toFixed(1)} ${y.toFixed(1)}`;
        })
        .join(""),
    )
    .join("");
}
