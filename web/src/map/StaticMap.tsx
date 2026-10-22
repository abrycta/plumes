import { useLang, useT } from "@abrycta/akari/react";
import { use } from "react";

import type { VolcanoesIndex } from "@contracts/readmodels";

import { AppLink } from "@/app/Link";
import { loadConfig } from "@/data/load";

import { depthClass, HEX_BREAKS } from "./density";
import { linesToPath, PH_BOUNDS, project, svgSize } from "./geo";
import type { WindowData } from "./windowData";

const DEPTH_FILL = ["var(--ak-div-7)", "var(--ak-div-6)", "var(--ak-div-5)"] as const;

function hexFill(count: number): string {
  const i = HEX_BREAKS.findIndex((b) => count < b);
  return `var(--ak-seq-${(i < 0 ? HEX_BREAKS.length : i) + 1})`;
}

let coastP: Promise<number[][][]> | null = null;
function loadCoast(): Promise<number[][][]> {
  coastP ??= loadConfig()
    .then((c) => fetch(c.basemap?.fallback ?? "/basemap/coast.geojson"))
    .then((r) => (r.ok ? r.json() : { features: [] }))
    .then((g: { features: { geometry: { coordinates: number[][][] } }[] }) => g.features.flatMap((f) => f.geometry.coordinates))
    .catch(() => []);
  return coastP;
}

/**
 * The static map (rule 6b's picture, and the whole map on phones and touch devices): the coastline, the window's
 * thermal-detection density (hexagons), detections near a volcano, earthquakes by magnitude and depth, and the 24
 * volcanoes as links, drawn in SVG. No WebGL, no tiles. Detections far from a volcano are shown only through the
 * faint density hexagons here (thousands of dots would not draw well on a phone).
 */
export function StaticMap({ index, data, selected }: { index: VolcanoesIndex; data?: WindowData | null; selected?: string | null }) {
  const t = useT();
  const { lang } = useLang();
  const coast = use(loadCoast());
  const W = 600;
  const [, H] = svgSize(PH_BOUNDS, W);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} role="group" aria-label={t("Map of the 24 volcanoes (static picture)", "24火山の地図(静止画)")} className="block h-auto w-full max-h-[78vh]" data-static-map>
      <path d={linesToPath(coast, PH_BOUNDS, W)} fill="none" stroke="var(--muted-foreground)" strokeWidth={0.8} strokeLinejoin="round" aria-hidden="true" />
      {data ? (
        <g aria-hidden="true">
          {data.hexes.map((h, i) => (
            <path key={i} d={linesToPath([h.ring], PH_BOUNDS, W) + "Z"} fill={hexFill(h.count)} opacity={0.7} />
          ))}
          {data.thermal
            .filter((p) => p.near)
            .map((p, i) => {
              const [x, y] = project(p.lon, p.lat, PH_BOUNDS, W);
              return <circle key={i} cx={x} cy={y} r={1.8} fill="var(--chart-4)" opacity={0.9} />;
            })}
          {[...data.quakes]
            .sort((a, b) => (a.mag ?? 0) - (b.mag ?? 0))
            .map((q, i) => {
              const [x, y] = project(q.lon, q.lat, PH_BOUNDS, W);
              const c = DEPTH_FILL[depthClass(q.depth)];
              const r = Math.max(1.5, ((q.mag ?? 3) - 2) * 1.6);
              return <circle key={i} cx={x} cy={y} r={r} fill={c} fillOpacity={0.35} stroke={c} strokeWidth={0.8} />;
            })}
        </g>
      ) : null}
      {index.features.map((f) => {
        const [lon, lat] = f.geometry.coordinates;
        const [x, y] = project(lon, lat, PH_BOUNDS, W);
        const deep = f.properties.coverage === "deep";
        const name = f.properties.name[lang];
        const on = selected === f.properties.id;
        const a = data?.activity.get(f.properties.id);
        const total = (a?.thermal ?? 0) + (a?.quakes ?? 0);
        const level = total ? Math.min(4, 1 + Math.floor(Math.log10(total))) : 0;
        return (
          <AppLink key={f.properties.id} to="volcano" id={f.properties.id} aria-label={name}>
            {level ? <circle cx={x} cy={y} r={(deep ? 6 : 5) + 1.75 * level} fill="var(--seal)" opacity={0.3} aria-hidden="true" /> : null}
            <circle cx={x} cy={y} r={deep ? 6 : 5} fill={deep ? "var(--seal)" : "var(--muted-foreground)"} stroke={on ? "var(--foreground)" : "var(--background)"} strokeWidth={on ? 2.5 : 1.5} />
            {deep || on ? (
              <text x={x + 10} y={y + 4} fontSize={12} fontFamily="var(--font-mono)" fill="var(--foreground)" stroke="var(--background)" strokeWidth={3} paintOrder="stroke">
                {name}
              </text>
            ) : null}
          </AppLink>
        );
      })}
    </svg>
  );
}
