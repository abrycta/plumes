import { useLang, useT } from "@abrycta/akari/react";

import { ExtLink } from "@/app/Link";
import { readAt, type Track } from "@/data/tracks";
import { formatDate } from "@/lib/dates";
import { flToKm, formatNumber, formatPercent, unitLabel } from "@/lib/format";

/** The scrubber's day, read off every track in words: the table view of the timeline (and its screen-reader path). */
export function Readout({ tracks, date }: { tracks: Track[]; date: string }) {
  const t = useT();
  const { lang } = useLang();
  return (
    <div className="flex flex-col gap-2" data-readout>
      <h3 className="m-0 font-heading text-lg font-semibold" aria-live="polite">
        {formatDate(date, lang)}
      </h3>
      <table className="w-full border-collapse text-sm">
        <caption className="sr-only">{t(`Every record on ${formatDate(date, "en")}`, `${formatDate(date, "ja")}のすべての記録`)}</caption>
        <tbody>
          {tracks.map((tr) => {
            const r = readAt(tr, date);
            let cell: React.ReactNode;
            if (r.status === "value") {
              const p = r.point;
              const v = p.value == null ? "–" : tr.unit === "FL" ? `FL${p.value} (${formatNumber(flToKm(p.value), lang, 1)} km)` : `${formatNumber(p.value, lang)}${tr.unit ? ` ${unitLabel(tr.unit, lang)}` : ""}`;
              const main =
                tr.id === "alert"
                  ? t(`Alert Level ${p.value}, as reported by PHIVOLCS on ${formatDate(p.date, "en")}`, `警戒レベル${p.value}(${formatDate(p.date, "ja")}にPHIVOLCSが発表)`)
                  : tr.kind === "spans"
                    ? `${p.mark}${p.end ? ` · ${formatDate(p.date, lang)} – ${formatDate(p.end, lang)}` : ""}`
                    : v;
              cell = (
                <>
                  <span className="tabular">{main}</span>
                  {p.coverage != null ? <span className="text-muted-foreground"> · {t(`coverage ${formatPercent(p.coverage, "en")}`, `被覆率${formatPercent(p.coverage, "ja")}`)}</span> : null}
                  {p.extra?.length ? <span className="text-muted-foreground"> · {p.extra.map((x) => `${x.label[lang]} ${x.value}`).join(" · ")}</span> : null}
                  {p.url ? (
                    <>
                      {" "}
                      <ExtLink href={p.url}>{t("source", "出典")}</ExtLink>
                    </>
                  ) : null}
                </>
              );
            } else {
              const words = {
                "no-observation": t("No valid observation (cloud or no overpass), not zero", "有効な観測なし(雲・通過なし)。ゼロではない"),
                "nothing-detected": t("Nothing detected", "検知なし"),
                "not-observed": t("Not observed: before this instrument's record", "観測前(この観測機器の記録開始前)"),
                "no-report": t("No report on this day", "この日の報告なし"),
                outside: t("Outside this series", "この系列の範囲外"),
              } as const;
              cell = <span className="text-muted-foreground">{words[r.status]}</span>;
            }
            return (
              <tr key={tr.id} className="border-t border-border align-top">
                <th scope="row" className="w-2/5 py-1.5 pr-3 text-left font-normal text-muted-foreground">
                  {tr.title[lang]}
                </th>
                <td className="py-1.5">{cell}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
