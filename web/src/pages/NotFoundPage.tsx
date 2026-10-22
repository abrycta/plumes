import { Button, Page, useT } from "@abrycta/akari/react";
import { useEffect } from "react";

import { AppLink } from "@/app/Link";

/** Unknown paths and unknown volcanoes: a real "not found" page (the Header marks nothing). */
export default function NotFoundPage() {
  const t = useT();
  useEffect(() => {
    const before = document.title;
    document.title = `${t("Not found", "ページが見つかりません")} · Plumes`;
    const robots = document.createElement("meta");
    robots.name = "robots";
    robots.content = "noindex";
    document.head.append(robots);
    return () => {
      document.title = before;
      robots.remove();
    };
  }, [t]);
  return (
    <Page eyebrow="404" title={t("Nothing recorded here", "このページは見つかりません")} lede={t("There is nothing at this address. The link may be mistyped or out of date.", "このアドレスには何もありません。リンクの誤りか、古いリンクの可能性があります。")}>
      <div className="flex flex-wrap gap-3">
        <Button asChild>
          <AppLink to="map">{t("Go to the map", "地図へ")}</AppLink>
        </Button>
        <Button asChild variant="outline">
          <AppLink to="volcanoes">{t("All volcanoes", "すべての火山")}</AppLink>
        </Button>
      </div>
    </Page>
  );
}
