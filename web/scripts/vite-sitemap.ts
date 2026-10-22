// Build-time sitemap.xml (src/app/sitemap.ts) from the published data version named by public/config.json: the
// fixed pages, every volcano and every reviewed story (drafts excluded). In CI a data read failure fails the build,
// so a deploy never ships a sitemap without its volcanoes; local offline builds warn and list the fixed pages only.
import { readFileSync } from "node:fs";

import type { Plugin } from "vite";

import type { StoriesIndex, VolcanoesIndex } from "../../contracts/ts/readmodels";
import { resolveRoot, resolveUrl, type AppConfig } from "../src/data/load";
import { sitemapUrls, sitemapXml } from "../src/app/sitemap";

const SITE_URL = "https://plumes.krtmtthw.dev";

export function sitemap(configPath: string): Plugin {
  return {
    name: "plumes-sitemap",
    apply: "build",
    async generateBundle() {
      const config = JSON.parse(readFileSync(configPath, "utf8")) as AppConfig;
      const siteUrl = config.siteUrl ?? SITE_URL;
      let volcanoes: VolcanoesIndex | null;
      let stories: StoriesIndex | null;
      try {
        const getJson = async <T>(url: string): Promise<T> => {
          const r = await fetch(url);
          if (!r.ok) throw Object.assign(new Error(`HTTP ${r.status} for ${url}`), { status: r.status });
          return (await r.json()) as T;
        };
        const root = await resolveRoot(config, getJson);
        volcanoes = await getJson<VolcanoesIndex>(resolveUrl(root.versionBase, "volcanoes.geojson"));
        // Versions made before the story generator have no stories.json: storyRefs then lists the known stories.
        stories = await getJson<StoriesIndex>(resolveUrl(root.versionBase, "stories.json")).catch((e: { status?: number }) => {
          if (e.status === 404) return null;
          throw e;
        });
        if (!volcanoes.features.length) throw new Error("volcanoes.geojson has no volcanoes");
      } catch (e) {
        if (process.env.CI) this.error(`sitemap: could not read the published data: ${String(e)}`);
        this.warn(`sitemap: fixed pages only (could not read the published data): ${String(e)}`);
        volcanoes = null;
        stories = null;
      }
      const urls = sitemapUrls(siteUrl, volcanoes, stories);
      this.emitFile({ type: "asset", fileName: "sitemap.xml", source: sitemapXml(urls) });
      this.info(`sitemap: ${urls.length} URLs`);
    },
  };
}
