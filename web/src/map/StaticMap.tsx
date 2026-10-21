import { useLang, useT } from "@abrycta/akari/react";
import { use } from "react";

import type { VolcanoesIndex } from "@contracts/readmodels";

import { AppLink } from "@/app/Link";
import { loadConfig } from "@/data/load";

import { linesToPath, PH_BOUNDS, project, svgSize } from "./geo";

export interface ThermalPoint {
  lon: number;
  lat: number;
  frp?: number;
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
 * The static map (rule 6b's picture, and the whole map on phones and touch devices): the coastline and the 24
 * volcanoes as links, drawn in SVG. No WebGL, no tiles.
 */
export function StaticMap({ index, thermal, selected }: { index: VolcanoesIndex; thermal?: ThermalPoint[]; selected?: string | null }) {
  const t = useT();
  const { lang } = useLang();
  const coast = use(loadCoast());
  const W = 600;
  const [, H] = svgSize(PH_BOUNDS, W);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} role="group" aria-label={t("Map of the 24 volcanoes (static picture)", "24火山の地図(静止画)")} className="block h-auto w-full max-h-[78vh]" data-static-map>
      <path d={linesToPath(coast, PH_BOUNDS, W)} fill="none" stroke="var(--muted-foreground)" strokeWidth={0.8} strokeLinejoin="round" aria-hidden="true" />
      {thermal?.map((p, i) => {
        const [x, y] = project(p.lon, p.lat, PH_BOUNDS, W);
        return <circle key={i} cx={x} cy={y} r={2} fill="var(--chart-4)" opacity={0.8} aria-hidden="true" />;
      })}
      {index.features.map((f) => {
        const [lon, lat] = f.geometry.coordinates;
        const [x, y] = project(lon, lat, PH_BOUNDS, W);
        const deep = f.properties.coverage === "deep";
        const name = f.properties.name[lang];
        const on = selected === f.properties.id;
        return (
          <AppLink key={f.properties.id} to="volcano" id={f.properties.id} aria-label={name}>
            <circle cx={x} cy={y} r={deep ? 7 : 5} fill={deep ? "var(--seal)" : "var(--muted-foreground)"} stroke={on ? "var(--foreground)" : "var(--background)"} strokeWidth={on ? 2.5 : 1.5} />
            {deep || on ? (
              <text x={x + 10} y={y + 4} fontSize={13} fontWeight={600} fill="var(--foreground)" stroke="var(--background)" strokeWidth={3} paintOrder="stroke">
                {name}
              </text>
            ) : null}
          </AppLink>
        );
      })}
    </svg>
  );
}
