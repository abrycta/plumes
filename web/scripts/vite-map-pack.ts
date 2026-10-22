// Build-time first window of the map page (src/map/firstWindow.ts): reads the published data version named by
// public/config.json and emits dist/map-pack/first.json. PLUMES_MAP_PACK=0 skips it; any failure (offline build, a
// point that would not come back identical) only warns, and the map then loads its first window from the layers.
import { readFileSync } from "node:fs";

import type { Plugin } from "vite";

import type { Layers } from "../../contracts/ts/readmodels";
import { resolveRoot, resolveUrl, type AppConfig } from "../src/data/load";
import { buildFirstWindow, MAP_PACK_PATH } from "../src/map/firstWindow";

export function mapPack(configPath: string): Plugin {
  return {
    name: "plumes-map-pack",
    apply: "build",
    async generateBundle() {
      if (process.env.PLUMES_MAP_PACK === "0") return;
      try {
        const config = JSON.parse(readFileSync(configPath, "utf8")) as AppConfig;
        const getJson = async <T>(url: string): Promise<T> => {
          const r = await fetch(url);
          if (!r.ok) throw new Error(`HTTP ${r.status} for ${url}`);
          return (await r.json()) as T;
        };
        const root = await resolveRoot(config, getJson);
        const layers = await getJson<Layers>(resolveUrl(root.versionBase, "layers.json"));
        const pack = await buildFirstWindow(layers, root.versionBase, root.latest);
        if (!pack) {
          this.warn("map pack skipped: the points would not come back identical (the map loads its first window from the layers)");
          return;
        }
        const source = JSON.stringify(pack);
        this.emitFile({ type: "asset", fileName: MAP_PACK_PATH, source });
        this.info(`map pack ${pack.stamp}: ${pack.months[0]}–${pack.months.at(-1)}, ${Math.round(source.length / 1024)} kB`);
      } catch (e) {
        this.warn(`map pack skipped (the map loads its first window from the layers): ${String(e)}`);
      }
    },
  };
}
