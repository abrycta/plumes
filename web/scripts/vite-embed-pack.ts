// Build-time /embed pack (src/embed/pack.ts): reads the published data version named by public/config.json and
// emits dist/embed-pack/{index.json, <end>.json, <end>-compact.json}. PLUMES_EMBED_PACK=0 skips it; any failure
// (offline build) only warns, and the embed then computes its windows in the browser as before.
import { readFileSync } from "node:fs";

import type { Plugin } from "vite";

import type { Layers, VolcanoesIndex, VolcanoReadModel } from "../../contracts/ts/readmodels";
import { resolveRoot, resolveUrl, type AppConfig } from "../src/data/load";
import { buildPack, PACK_DIR } from "../src/embed/pack";

export function embedPack(configPath: string): Plugin {
  return {
    name: "plumes-embed-pack",
    apply: "build",
    async generateBundle() {
      if (process.env.PLUMES_EMBED_PACK === "0") return;
      try {
        const config = JSON.parse(readFileSync(configPath, "utf8")) as AppConfig;
        const getJson = async <T>(url: string): Promise<T> => {
          const r = await fetch(url);
          if (!r.ok) throw new Error(`HTTP ${r.status} for ${url}`);
          return (await r.json()) as T;
        };
        const root = await resolveRoot(config, getJson);
        const [layers, index] = await Promise.all([getJson<Layers>(resolveUrl(root.versionBase, "layers.json")), getJson<VolcanoesIndex>(resolveUrl(root.versionBase, "volcanoes.geojson"))]);
        const pack = await buildPack(layers, root.versionBase, index, root.latest.current, root.latest.dataAsOf, (file) => getJson<VolcanoReadModel>(resolveUrl(root.versionBase, file)));
        this.emitFile({ type: "asset", fileName: `${PACK_DIR}/index.json`, source: JSON.stringify(pack.index) });
        for (const [name, body] of Object.entries(pack.files)) this.emitFile({ type: "asset", fileName: `${PACK_DIR}/${name}`, source: JSON.stringify(body) });
        const kb = (n: number) => `${Math.round(n / 1024)} kB`;
        this.info(`embed pack ${pack.index.dataVersion}: ${pack.index.states.map((s) => `${s.end} ${kb(s.bytes)} / phone ${kb(s.compactBytes)}`).join("; ")}`);
      } catch (e) {
        this.warn(`embed pack skipped (the embed falls back to browser-side windows): ${String(e)}`);
      }
    },
  };
}
