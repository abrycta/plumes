import { useLang, useT } from "@abrycta/akari/react";

import type { VolcanoReadModel } from "@contracts/readmodels";

import { lakeSwatches } from "@/data/craterLake";
import { formatDate } from "@/lib/dates";
import { formatNumber } from "@/lib/format";

/** The crater lake's true colour on cloud-free Sentinel-2 days (one swatch a month), with its water area in the title and
 * in a screen-reader list. Descriptive only: colour is not water chemistry. Renders nothing without the series. */
export function LakeColours({ model }: { model: VolcanoReadModel }) {
  const t = useT();
  const { lang } = useLang();
  const swatches = lakeSwatches(model);
  if (!swatches.length) return null;
  const first = swatches[0]!;
  const last = swatches[swatches.length - 1]!;
  return (
    <figure className="m-0 flex flex-col gap-2" data-lake-colours>
      <figcaption className="text-sm text-muted-foreground">
        {t(
          `Crater-lake colour on cloud-free Sentinel-2 days, ${formatDate(first.date, "en")} to ${formatDate(last.date, "en")}. Descriptive only: the colour does not measure water chemistry.`,
          `雲のない日のSentinel-2による火口湖の色(${formatDate(first.date, "ja")}〜${formatDate(last.date, "ja")})。見た目の色で、水質を示すものではない。`,
        )}
      </figcaption>
      <ol className="m-0 flex list-none flex-wrap gap-px p-0" aria-label={t("Lake colour by date", "日付ごとの湖の色")}>
        {swatches.map((s) => (
          <li
            key={s.date}
            className="size-3 rounded-[2px] border border-border"
            style={{ backgroundColor: s.colour }}
            title={`${formatDate(s.date, lang)} · ${formatNumber(s.areaKm2, lang, 2)} km²`}
          >
            <span className="sr-only">{`${formatDate(s.date, lang)}: ${formatNumber(s.areaKm2, lang, 2)} km²`}</span>
          </li>
        ))}
      </ol>
    </figure>
  );
}
