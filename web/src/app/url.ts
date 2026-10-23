// URL state without a router library (as in Lights): the page in the path, view state in the query string, so
// every view is a shareable link. Pages: / (map), /volcanoes, /volcano/<id>, /stories, /story/<id>, /about.

import { useSyncExternalStore } from "react";

export type Page = "map" | "volcanoes" | "volcano" | "stories" | "story" | "about" | "notfound";

export interface UrlState {
  page: Page;
  /** Volcano or story id. */
  id: string | null;
  lang: "en" | "ja" | null;
  /** Volcano page: the scrubber day, the period and the ring. */
  date: string | null;
  from: string | null;
  to: string | null;
  ring: number | null;
  /** ?preview: show story drafts that have not passed the automated checks yet (ST1, ST15). Never linked from the site. */
  preview?: boolean;
}

const ID = /^[a-z0-9-]{1,64}$/;
const DAY = /^\d{4}-\d{2}-\d{2}$/;

export function parseUrl(pathname: string, search: string): UrlState {
  const q = new URLSearchParams(search);
  const parts = pathname
    .replace(/(^|\/)index\.html$/, "")
    .split("/")
    .filter(Boolean)
    .map((p) => decodeURIComponent(p));
  let page: Page = "notfound";
  let id: string | null = null;
  if (parts.length === 0) page = "map";
  else if (parts.length === 1 && ["volcanoes", "stories", "about"].includes(parts[0]!)) page = parts[0] as Page;
  else if (parts.length === 2 && (parts[0] === "volcano" || parts[0] === "story") && ID.test(parts[1]!)) {
    page = parts[0] as Page;
    id = parts[1]!;
  }
  const lang = q.get("lang");
  const day = (k: string) => {
    const v = q.get(k);
    return v && DAY.test(v) ? v : null;
  };
  const ring = Number(q.get("ring"));
  return {
    page,
    id,
    lang: lang === "en" || lang === "ja" ? lang : null,
    date: day("date"),
    from: day("from"),
    to: day("to"),
    ring: Number.isInteger(ring) && ring > 0 && ring <= 200 ? ring : null,
    preview: q.has("preview"),
  };
}

export function pathOf(page: Exclude<Page, "notfound">, id?: string | null): string {
  switch (page) {
    case "map":
      return "/";
    case "volcano":
    case "story":
      return `/${page}/${encodeURIComponent(id ?? "")}`;
    default:
      return `/${page}`;
  }
}

export function formatUrl(s: UrlState): string {
  const q = new URLSearchParams();
  if (s.page === "volcano") {
    if (s.from) q.set("from", s.from);
    if (s.to) q.set("to", s.to);
    if (s.date) q.set("date", s.date);
    if (s.ring) q.set("ring", String(s.ring));
  }
  if (s.lang) q.set("lang", s.lang);
  if (s.preview) q.set("preview", "1");
  const qs = q.toString();
  const path = s.page === "notfound" ? (typeof location !== "undefined" ? location.pathname : "/") : pathOf(s.page, s.id);
  return `${path}${qs ? `?${qs}` : ""}`;
}

const listeners = new Set<() => void>();
let current: UrlState | null = null;
let currentKey = "";

function snapshot(): UrlState {
  const key = location.pathname + location.search;
  if (!current || key !== currentKey) {
    current = parseUrl(location.pathname, location.search);
    currentKey = key;
  }
  return current;
}

function subscribe(fn: () => void) {
  listeners.add(fn);
  window.addEventListener("popstate", fn);
  return () => {
    listeners.delete(fn);
    window.removeEventListener("popstate", fn);
  };
}

export function useUrlState(): UrlState {
  return useSyncExternalStore(subscribe, snapshot, snapshot);
}

/** Change the URL. A new page pushes a history entry and resets the view state; view changes replace by default. */
export function navigate(patch: Partial<UrlState>, opts: { replace?: boolean } = {}) {
  const prev = snapshot();
  const pageChange = (patch.page != null && patch.page !== prev.page) || (patch.id !== undefined && patch.id !== prev.id);
  const base: UrlState = pageChange ? { ...prev, date: null, from: null, to: null, ring: null } : prev;
  const next = formatUrl({ ...base, ...patch });
  if (next === location.pathname + location.search) return;
  if (opts.replace ?? !pageChange) history.replaceState(null, "", next);
  else history.pushState(null, "", next);
  for (const fn of listeners) fn();
}

/** Follow an in-app href (from formatUrl) with client-side navigation. */
export function navigateHref(href: string) {
  const u = new URL(href, location.href);
  const s = parseUrl(u.pathname, u.search);
  navigate({ ...s, lang: s.lang ?? snapshot().lang }, { replace: false });
}
