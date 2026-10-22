// sitemap.xml, built from the published data (scripts/vite-sitemap.ts): the fixed pages, every volcano in
// volcanoes.geojson and every reviewed story in stories.json (drafts never; storyRefs without preview).

import type { StoriesIndex, VolcanoesIndex } from "@contracts/readmodels";

import { storyRefs } from "../data/load";
import { pathOf } from "./url";

/** The pages every version has, in sitemap order. */
export const SITEMAP_PAGES = ["map", "volcanoes", "stories", "about"] as const;

const escapeXml = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

/** Absolute URLs of the public pages: the fixed pages, then stories, then volcanoes (each sorted, no duplicates). */
export function sitemapUrls(siteUrl: string, volcanoes: VolcanoesIndex | null, stories: StoriesIndex | null): string[] {
  const site = siteUrl.replace(/\/+$/, "");
  const storyIds = [...new Set(storyRefs(stories, false).map((s) => s.id))].sort();
  const volcanoIds = [...new Set((volcanoes?.features ?? []).map((f) => f.properties.id))].sort();
  const paths = [...SITEMAP_PAGES.map((p) => pathOf(p)), ...storyIds.map((id) => pathOf("story", id)), ...volcanoIds.map((id) => pathOf("volcano", id))];
  return paths.map((p) => `${site}${p}`);
}

export function sitemapXml(urls: string[]): string {
  const rows = urls.map((u) => `  <url><loc>${escapeXml(u)}</loc></url>`).join("\n");
  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${rows}\n</urlset>\n`;
}
