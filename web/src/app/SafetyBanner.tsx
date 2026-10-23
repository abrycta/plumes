import { T } from "@abrycta/akari/react";

import { formatDate } from "@/lib/dates";

import { ExtLink } from "./Link";

export const PHIVOLCS_URL = "https://www.phivolcs.dost.gov.ph/";
export const PHIVOLCS_BULLETINS_URL = "https://wovodat.phivolcs.dost.gov.ph/bulletin/list-of-bulletin";

/**
 * The safety banner (RESEARCH.md §9 rule 1): a layout element on every route, never dismissable. It states what the
 * site is not, names DOST-PHIVOLCS as the sole authority and links to it. No present-tense status anywhere.
 */
export function SafetyBanner({ dataAsOf, fixture, lang }: { dataAsOf?: string; fixture?: boolean; lang: "en" | "ja" }) {
  const year = dataAsOf?.slice(0, 4);
  return (
    <div role="note" aria-label={lang === "ja" ? "この記録について" : "About this record"} data-safety-banner className="safety-banner">
      <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1 px-ak-gutter py-2 text-sm">
        <p className="m-0">
          <T
            en={`A record of 2000–${year ?? ""}, not a warning service.`.replace("–,", " onward,")}
            ja={year ? `2000〜${year}年の記録で、警報サービスではありません。` : "2000年以降の記録で、警報サービスではありません。"}
          />{" "}
          <T en="DOST-PHIVOLCS is the authority on alert levels." ja="警戒レベルを発表するのはDOST-PHIVOLCSです。" />
          {dataAsOf ? (
            <>
              {" "}
              <span className="whitespace-nowrap">
                <T en="Data through" ja="データの最終日:" /> <time dateTime={dataAsOf}>{formatDate(dataAsOf, lang)}</time>
                {lang === "ja" ? "。" : "."}
              </span>
            </>
          ) : null}
        </p>
        <span className="flex flex-wrap gap-x-4">
          <ExtLink href={PHIVOLCS_URL}>DOST-PHIVOLCS</ExtLink>
          <ExtLink href={PHIVOLCS_BULLETINS_URL}>
            <T en="PHIVOLCS bulletins" ja="PHIVOLCSの火山情報" />
          </ExtLink>
        </span>
        {fixture ? (
          <span className="rounded-sm border border-dashed border-border px-1.5 text-xs text-muted-foreground">
            <T en="Sample data version: Taal, Dec 2019 – Feb 2020 only" ja="サンプルデータ版:タール火山、2019年12月〜2020年2月のみ" />
          </span>
        ) : null}
      </div>
    </div>
  );
}
