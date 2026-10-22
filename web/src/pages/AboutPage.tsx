import { Page, Prose, T, useLang, useT } from "@abrycta/akari/react";
import { use, useEffect } from "react";

import { ExtLink } from "@/app/Link";
import { PHIVOLCS_BULLETINS_URL, PHIVOLCS_URL } from "@/app/SafetyBanner";
import sources from "@/content/sources.json";
import { loadRoot } from "@/data/load";
import { formatDate } from "@/lib/dates";

interface SourceRow {
  id: string;
  milestone: string;
  title: string;
  verdict: string;
  licence: string;
  attribution: string;
  link: string | null;
}

const VERDICTS: Record<string, { en: string; ja: string }> = {
  open: { en: "Open", ja: "オープン" },
  "open-with-conditions": { en: "Open, with conditions", ja: "条件付きオープン" },
  "link-only": { en: "Linked and cited only", ja: "リンクと引用のみ" },
  "noncommercial-only": { en: "Non-commercial only", ja: "非営利のみ" },
};

const MILESTONE: Record<string, { en: string; ja: string }> = {
  M1: { en: "in this release", ja: "このリリース" },
  "M1.1": { en: "next (M1.1)", ja: "次回(M1.1)" },
  M2: { en: "later (M2)", ja: "後日(M2)" },
};

export default function AboutPage() {
  const t = useT();
  const { lang } = useLang();
  const root = use(loadRoot());
  useEffect(() => {
    document.title = `${t("About & sources", "概要と出典")} · Plumes`;
  }, [t]);
  const rows = (sources as SourceRow[]).slice().sort((a, b) => a.milestone.localeCompare(b.milestone) || a.id.localeCompare(b.id));
  return (
    <Page
      title={t("About & sources", "概要と出典")}
      lede={t(
        "Plumes is a retrospective record of the 24 active Philippine volcanoes: a past record and visualisation only, never a hazard service.",
        "Plumesはフィリピンの24の活火山の過去の記録です。過去の記録と可視化のみで、防災情報サービスではありません。",
      )}
    >
      <Prose as="section" aria-labelledby="what">
        <h2 id="what">{t("What Plumes is, and is not", "Plumesとは何か、何ではないか")}</h2>
        <ul>
          <li>
            <T
              en="A retrospective record from 2000 to the data date. It is not a monitoring or warning service, has no live feeds and never shows a present alert level."
              ja="2000年からデータの最終日までの過去の記録です。監視・警報サービスではなく、リアルタイムのデータはなく、現時点の警戒レベルは表示しません。"
            />
          </li>
          <li>
            <T en="DOST-PHIVOLCS is the sole authority for alert levels and advisories in the Philippines:" ja="フィリピンの警戒レベルと火山情報を発表する唯一の機関はDOST-PHIVOLCSです:" />{" "}
            <ExtLink href={PHIVOLCS_URL}>phivolcs.dost.gov.ph</ExtLink>, <ExtLink href={PHIVOLCS_BULLETINS_URL}>{t("bulletin list", "火山情報の一覧")}</ExtLink>.
          </li>
          <li>
            <T
              en="Alert levels appear only as dated, linked markers, each labelled “as reported by PHIVOLCS on <date>”. Every PHIVOLCS, VAAC and DSWD figure links to its page; no PHIVOLCS data file is published."
              ja="警戒レベルは日付とリンク付きの印としてのみ示し、それぞれに「<日付>にPHIVOLCSが発表」と記します。PHIVOLCS・VAAC・DSWDの数値はすべて元のページにリンクし、PHIVOLCSのデータファイルは公開しません。"
            />
          </li>
          <li>
            <T en="Nothing here says what a volcano will do next." ja="ここには火山の今後については何も書かれていません。" />
          </li>
          <li>
            <T en="Hazard maps are linked, never embedded: " ja="ハザードマップは埋め込まず、リンクのみ:" />
            <ExtLink href="https://hazardhunter.georisk.gov.ph/">HazardHunterPH</ExtLink>.
          </li>
          <li>
            <T en="A non-commercial portfolio project; no dataset is redistributed." ja="非営利のポートフォリオ作品です。データセットは再配布していません。" />
          </li>
        </ul>
      </Prose>

      <Prose as="section" aria-labelledby="reading">
        <h2 id="reading">{t("How to read the records", "記録の読み方")}</h2>
        <ul>
          <li>
            <strong>{t("SO₂ from satellites", "衛星のSO₂")}</strong>:{" "}
            <T
              en="TROPOMI (from 2018) measures a column amount over an area on clear days at one overpass, not the flux a ground instrument measures. A low value on a cloudy day means “not enough data”, so coverage is shown beside every value."
              ja="TROPOMI(2018年から)は、晴天日の通過時に一定範囲のカラム量を測るもので、地上観測の放出量とは異なります。曇りの日の低い値は「データ不足」を意味するため、すべての値に被覆率を併記します。"
            />
          </li>
          <li>
            <strong>{t("Heat", "熱")}</strong>:{" "}
            <T
              en="MODIS and VIIRS thermal anomalies and radiative power within a ring around the summit. They can include vegetation fires and are not validated for volcanoes."
              ja="山頂周辺のMODISとVIIRSの熱異常と放射電力。植生火災を含むことがあり、火山向けに検証されたものではありません。"
            />
          </li>
          <li>
            <strong>{t("Earthquakes", "地震")}</strong>:{" "}
            <T en="USGS ComCat locates earthquakes from a global network and misses the small local events PHIVOLCS counts." ja="USGS ComCatは全球観測網による震源で、PHIVOLCSが数える小さな地元の地震は含まれません。" />
          </li>
          <li>
            <strong>{t("Gaps", "欠測")}</strong>:{" "}
            <T
              en="Each series starts when its instrument does. A day without a valid observation is a gap, never a zero; before an instrument's start and after the last day its record covers, it says “not observed”."
              ja="各系列は観測機器の開始日から始まります。有効な観測のない日は欠測でありゼロではなく、観測開始前と記録の最終日より後は「観測なし」と表示します。"
            />
          </li>
          <li>
            <strong>{t("People nearby", "周辺の人口")}</strong>:{" "}
            <T en="Population within N km (WorldPop 2020). Rings are distances, not hazard zones." ja="N km圏の人口(WorldPop 2020年)。距離の円はハザード区域ではありません。" />
          </li>
        </ul>
      </Prose>

      <section aria-labelledby="sources" className="flex min-w-0 flex-col gap-3">
        <h2 id="sources" className="m-0 font-heading text-2xl font-semibold">
          {t("Sources and licences", "出典とライセンス")}
        </h2>
        <p className="m-0 max-w-prose text-sm text-muted-foreground">
          <T
            en={`${rows.length} registry entries (24 sources; USGS and Landsat are each split in two, and three arrive later). Each verdict was checked on the publisher's own terms page; the attribution is the text the publisher asks for.`}
            ja={`登録数${rows.length}件(24の出典。USGSとLandsatはそれぞれ2件に分かれ、3件は今後追加)。各判定は公開元の利用規約ページで確認し、帰属表示は公開元が求める文言です。`}
          />
        </p>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] border-collapse text-sm">
            <thead>
              <tr className="text-left text-xs text-muted-foreground">
                <th className="py-1 pr-3 font-normal">{t("Source", "出典")}</th>
                <th className="py-1 pr-3 font-normal">{t("Licence", "ライセンス")}</th>
                <th className="py-1 font-normal">{t("Attribution", "帰属表示")}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id} className="border-t border-border align-top" id={`source-${r.id}`}>
                  <td className="py-2 pr-3">
                    <span className="block">{r.title}</span>
                    <span className="block font-mono text-[11px] text-muted-foreground">
                      {r.id} · {MILESTONE[r.milestone]?.[lang] ?? r.milestone}
                    </span>
                    {r.link ? <ExtLink href={r.link}>{t("publisher page", "公開元")}</ExtLink> : null}
                  </td>
                  <td className="py-2 pr-3">
                    <span className="block">{VERDICTS[r.verdict]?.[lang] ?? r.verdict}</span>
                    {/* The full terms one tap away (rule 28b). */}
                    <details className="text-xs text-muted-foreground">
                      <summary className="cursor-pointer">{t("Terms", "利用条件")}</summary>
                      <span className="block" lang="en">
                        {r.licence}
                      </span>
                    </details>
                  </td>
                  <td className="py-2 text-xs" lang="en">
                    {r.attribution}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <Prose as="section" aria-labelledby="notices">
        <h2 id="notices">{t("Required notices", "必要な表示")}</h2>
        {lang === "ja" ? <p>以下は公開元が求める原文(英語)です。</p> : null}
        <ul lang="en">
          <li>Contains modified Copernicus Sentinel data (2018–2026), processed by ESA. Processed in Google Earth Engine (noncommercial use).</li>
          <li>
            We acknowledge the use of data and/or imagery from NASA&apos;s Fire Information for Resource Management System (FIRMS) (https://earthdata.nasa.gov/firms), part of NASA&apos;s Earth Science Data and Information
            System (ESDIS). LANCE disclaimer: “The information presented through LANCE, GIBS, Worldview, and FIRMS are provided ‘as is’ and users bear all responsibility and liability for their use of data” and “Due to the
            spatial resolution and other characteristics of these data, their use for tactical decision-making or informing about conditions at a local scale are not advised.”
          </li>
          <li>Global Volcanism Program, 2026. [Database] Volcanoes of the World (v. 5.4.0). Distributed by Smithsonian Institution, compiled by Venzke, E. Used non-commercially, with citation.</li>
          <li>U.S. Geological Survey, ANSS Comprehensive Earthquake Catalog (ComCat).</li>
          <li>DOST-PHIVOLCS (Philippine Institute of Volcanology and Seismology): every figure is cited with its bulletin date and link.</li>
          <li>Source: Japan Meteorological Agency website, Tokyo VAAC volcanic ash advisories.</li>
          <li>DSWD DROMIC reports, https://dromic.dswd.gov.ph/, cited per report.</li>
          <li>WorldPop (www.worldpop.org), CC BY 4.0.</li>
          <li>Basemap: OpenFreeMap, © OpenMapTiles, © OpenStreetMap contributors (ODbL); offline coastline: Natural Earth (public domain).</li>
        </ul>
      </Prose>

      <Prose as="section" aria-labelledby="data">
        <h2 id="data">{t("Data version", "データ版")}</h2>
        <p>
          {t(
            `Version ${root.latest.current}, data through ${formatDate(root.latest.dataAsOf, "en")}, generated ${root.latest.generatedAt}.`,
            `版 ${root.latest.current}、データの最終日 ${formatDate(root.latest.dataAsOf, "ja")}、生成 ${root.latest.generatedAt}。`,
          )}{" "}
          {root.latest.fixture
            ? t(
                "This is the sample data version built from real Taal tables for December 2019 to February 2020; the full record arrives with the first published version.",
                "これは2019年12月〜2020年2月のタール火山の実データから作ったサンプル版です。全期間の記録は最初の公開版で加わります。",
              )
            : null}
        </p>
        <p>
          <T en="Code:" ja="コード:" /> <ExtLink href="https://github.com/abrycta/plumes">github.com/abrycta/plumes</ExtLink>
        </p>
      </Prose>
    </Page>
  );
}
