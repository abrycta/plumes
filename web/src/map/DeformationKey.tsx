import { ContinuousLegend, T, useT } from "@abrycta/akari/react";

import type { Layer } from "@contracts/readmodels";

import { velocityDomain } from "./deformation";

const LICENCE = "https://creativecommons.org/licenses/by-nc/4.0/";

function month(iso: string): string {
  return iso.slice(0, 7);
}

/** Legend and notes of the deformation-velocity layer: diverging ramp, LOS sign, reference rings, frames, licence. */
export function DeformationKey({ layer, names }: { layer: Layer; names: Record<string, string> }) {
  const t = useT();
  const d = velocityDomain(layer);
  const frames = layer.frames ?? [];
  return (
    <div className="flex max-w-prose flex-col gap-2" data-deformation-key>
      <ContinuousLegend
        scale="diverging"
        title={t("Ground motion along the satellite's line of sight", "衛星視線方向の地表変位")}
        unit={t("mm/yr", "mm/年")}
        ticks={[
          { at: 0, label: `≤ −${d}` },
          { at: 0.5, label: "0" },
          { at: 1, label: `≥ ${d}` },
        ]}
        note={
          <T
            en="Left: away from the satellite. Right: toward it. The middle grey is no measurable motion. Line-of-sight motion mixes vertical and east–west movement, so it is not uplift or subsidence by itself, and this is not a hazard map. Zoom in on a volcano to see it; a ring marks COMET's reference area, which every value is relative to."
            ja="左は衛星から遠ざかる動き、右は近づく動き。中央の灰色は測定できる動きがないことを示す。視線方向の変位は上下と東西の動きを含むため、それだけで隆起や沈降とは言えず、これはハザードマップではない。火山に拡大すると表示される。輪はCOMETの参照域で、すべての値はそこからの相対値。"
          />
        }
      />
      {frames.length ? (
        <details className="text-xs text-muted-foreground">
          <summary className="cursor-pointer">
            <T en={`${frames.length} Sentinel-1 frames`} ja={`Sentinel-1 フレーム ${frames.length}件`} />
          </summary>
          <ul className="m-0 mt-1 list-none p-0">
            {frames.map((f) => (
              <li key={f.id}>
                {names[f.volcanoId] ?? f.volcanoId} · {t(`track ${f.track} ${f.pass}`, `トラック${f.track}・${f.pass === "descending" ? "南行" : "北行"}`)} · {month(f.start)} →{" "}
                {month(f.end)} · {t(`${f.dates} dates`, `${f.dates}回`)}
              </li>
            ))}
          </ul>
        </details>
      ) : null}
      <p className="m-0 text-xs text-muted-foreground">
        {layer.attribution.replace(/\s*CC BY-NC 4\.0.*$/, "")}{" "}
        <a href={LICENCE} className="underline" lang="en">
          CC BY-NC 4.0
        </a>
      </p>
    </div>
  );
}
