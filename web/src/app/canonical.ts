// <link rel="canonical"> on the custom domain for every page (the Pages preview hosts and query-string view state
// fold into one URL per page). Set from the URL state at run time: index.html serves every route, so a static link
// there would point every page at one URL. The not-found page has none. /embed is noindex and carries none either.

import { useEffect } from "react";

import { pathOf, type UrlState } from "./url";

export const SITE_URL = "https://plumes.krtmtthw.dev";

/** The canonical URL of a page: its path on the custom domain; Japanese keeps ?lang=ja (its own language version). */
export function canonicalUrl(s: Pick<UrlState, "page" | "id" | "lang">): string | null {
  if (s.page === "notfound") return null;
  return `${SITE_URL}${pathOf(s.page, s.id)}${s.lang === "ja" ? "?lang=ja" : ""}`;
}

export function useCanonical(s: Pick<UrlState, "page" | "id" | "lang">) {
  const href = canonicalUrl(s);
  useEffect(() => {
    let link = document.head.querySelector<HTMLLinkElement>('link[rel="canonical"]');
    if (!href) {
      link?.remove();
      return;
    }
    if (!link) {
      link = document.createElement("link");
      link.rel = "canonical";
      document.head.append(link);
    }
    link.href = href;
  }, [href]);
}
