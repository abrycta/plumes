import { Page, useT } from "@abrycta/akari/react";
import { use, useEffect } from "react";

import { DataThrough } from "@/components/DataThrough";
import { VolcanoList } from "@/components/VolcanoList";
import { loadRoot, loadVolcanoes } from "@/data/load";

export default function VolcanoesPage() {
  const t = useT();
  const index = use(loadVolcanoes());
  const root = use(loadRoot());
  useEffect(() => {
    document.title = `${t("Volcanoes", "火山")} · Plumes`;
  }, [t]);
  return (
    <Page
      eyebrow={<DataThrough date={root.latest.dataAsOf} />}
      title={t(`The ${index.features.length} active volcanoes`, `${index.features.length}の活火山`)}
      lede={t(
        "Four observatory volcanoes (Taal, Mayon, Kanlaon, Bulusan) have deep records with PHIVOLCS bulletins; the others have satellite and eruption-history records.",
        "観測所のある4火山(タール、マヨン、カンラオン、ブルサン)はPHIVOLCSの火山情報を含む詳細な記録があり、その他は衛星と噴火史の記録です。",
      )}
    >
      <VolcanoList index={index} />
    </Page>
  );
}
