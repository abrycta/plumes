import { AppShell, Header, HEADER_PORTFOLIO, T, useLang, useT } from "@abrycta/akari/react";
import { type ReactNode, Suspense, use, useEffect } from "react";

import { loadRoot } from "@/data/load";

import { AppLink } from "./Link";
import { SafetyBanner } from "./SafetyBanner";
import { formatUrl, navigate, navigateHref, type UrlState, useUrlState } from "./url";

/** Keeps ?lang= in shared links in step with the language switch (as in Lights). */
function useLangParam() {
  const { lang, setLang } = useLang();
  const url = useUrlState();
  useEffect(() => {
    if (url.lang && url.lang !== lang) setLang(url.lang);
    // Only on load / history navigation.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url.lang]);
  useEffect(() => {
    document.documentElement.lang = lang;
    if (url.lang && url.lang !== lang) navigate({ lang }, { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lang]);
}

const blank = { id: null, date: null, from: null, to: null, ring: null } as const;

/** Akari's Header, the same menu bar as krtmtthw.dev and every other app: data only; client-side navigation on plain clicks. */
export function PlumesHeader({ url }: { url: UrlState }) {
  const t = useT();
  const href = (page: "map" | "volcanoes" | "stories" | "about") => formatUrl({ ...blank, page, lang: url.lang });
  return (
    <Header
      brand={{ name: "Plumes", glyph: "噴", href: href("map"), srSuffix: t("home", "ホーム") }}
      navLabel={t("Main", "メイン")}
      nav={[
        { href: href("map"), label: t("Map", "地図"), match: "exact" },
        { href: href("volcanoes"), label: t("Volcanoes", "火山"), match: "section", also: ["/volcano/"] },
        { href: href("stories"), label: t("Stories", "ストーリー"), match: "section", also: ["/story/"] },
        { href: href("about"), label: t("About & sources", "概要と出典"), match: "section" },
      ]}
      location={url.page === "notfound" ? undefined : { pathname: formatUrl({ ...url, lang: null, date: null, from: null, to: null, ring: null }) }}
      portfolioLink
      languages
      width="full"
      renderLink={(p) => (
        <a
          {...p}
          onClick={(e) => {
            if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
            if (!p.href.startsWith("/")) return;
            e.preventDefault();
            navigateHref(p.href);
            window.scrollTo(0, 0);
          }}
        />
      )}
    />
  );
}

function BannerWithData({ lang }: { lang: "en" | "ja" }) {
  const root = use(loadRoot());
  return <SafetyBanner lang={lang} dataAsOf={root.latest.dataAsOf} fixture={root.latest.fixture} />;
}

function FooterData() {
  const root = use(loadRoot());
  return (
    <>
      <span>
        <T en="Data version" ja="データ版" /> <span className="font-mono">{root.latest.current}</span>
      </span>
      <span>
        <T en="data through" ja="データの最終日" /> <span className="font-mono">{root.latest.dataAsOf}</span>
      </span>
      <span>
        <T en="generated" ja="生成" /> <span className="font-mono">{root.latest.generatedAt}</span>
      </span>
    </>
  );
}

export function Shell({ children }: { children: ReactNode }) {
  const t = useT();
  const { lang } = useLang();
  const url = useUrlState();
  useLangParam();
  return (
    <AppShell
      header={<PlumesHeader url={url} />}
      footer={
        <footer className="border-t border-border">
          <div className="grid gap-2 px-ak-gutter py-6 text-xs text-muted-foreground">
            <div className="flex flex-wrap gap-x-4 gap-y-1">
              <Suspense fallback={null}>
                <FooterData />
              </Suspense>
              <span>
                <T en="app" ja="アプリ" /> <span className="font-mono">{__COMMIT_SHA__.slice(0, 7)}</span>
              </span>
            </div>
            <p>
              <T
                en="A non-commercial retrospective record. Sources: DOST-PHIVOLCS (linked, not redistributed), Smithsonian GVP, Copernicus Sentinel, NASA, USGS, JMA Tokyo VAAC, DSWD, WorldPop."
                ja="非営利の過去の記録。出典:DOST-PHIVOLCS(リンクのみ、再配布なし)、スミソニアン博物館GVP、Copernicus Sentinel、NASA、USGS、気象庁東京VAAC、DSWD、WorldPop。"
              />{" "}
              <AppLink to="about" className="underline underline-offset-4">
                <T en="Sources and licences" ja="出典とライセンス" />
              </AppLink>
            </p>
            <p>
              <T en="A project by" ja="制作:" />{" "}
              <a href={HEADER_PORTFOLIO.href} className="underline underline-offset-4 hover:text-foreground">
                Kurt · krtmtthw.dev
              </a>
            </p>
          </div>
        </footer>
      }
    >
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:bg-background focus:p-2">
        {t("Skip to content", "本文へ移動")}
      </a>
      <Suspense fallback={<SafetyBanner lang={lang} />}>
        <BannerWithData lang={lang} />
      </Suspense>
      <div id="main" tabIndex={-1} className="outline-none">
        {children}
      </div>
    </AppShell>
  );
}
