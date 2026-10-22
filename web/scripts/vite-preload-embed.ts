// Vite plugin: preload what /embed always needs from embed.html itself (same idea as lgu-lights' vite-preload-map).
// The embed always shows the MapLibre map (it is framed only on krtmtthw.dev's project page), but the map code is a
// lazy import that starts only after the data index has loaded, the worker starts only when the map is built, and
// the pack index (embed-pack/index.json) is fetched only after volcanoes.geojson and layers.json. Vite writes
// <link rel=modulepreload> only for static imports, so without this each of these is found one or more round trips
// late. The hashed names exist only at build time, hence a plugin. index.html does the same at run time, only on
// rich-media screens (src/app/prefetch.ts), because phones there get the static map instead.
import type { HtmlTagDescriptor, Plugin, Rollup } from "vite";

import { PACK_DIR } from "../src/embed/pack";

type OutputBundle = Rollup.OutputBundle;
type OutputChunk = Rollup.OutputChunk;

const MAP_MODULE = /\/src\/map\/InteractiveMap\.tsx$/;
const WORKER_ASSET = /(^|\/)maplibre-gl-worker-[^/]+\.mjs$/;

function chunkClosure(bundle: OutputBundle, root: OutputChunk): OutputChunk[] {
  const seen = new Map<string, OutputChunk>();
  const visit = (fileName: string) => {
    const c = bundle[fileName];
    if (seen.has(fileName) || !c || c.type !== "chunk") return;
    seen.set(fileName, c);
    c.imports.forEach(visit);
  };
  visit(root.fileName);
  return [...seen.values()];
}

export function preloadEmbed(): Plugin {
  let base = "/";
  return {
    name: "plumes-preload-embed",
    apply: "build",
    configResolved: (config) => void (base = config.base),
    transformIndexHtml: {
      order: "post",
      handler(html, ctx) {
        const bundle = ctx.bundle;
        if (!bundle || !ctx.filename.endsWith("embed.html")) return html;
        const map = Object.values(bundle).find((c): c is OutputChunk => c.type === "chunk" && !!c.facadeModuleId && MAP_MODULE.test(c.facadeModuleId));
        if (!map) throw new Error("preload-embed: InteractiveMap is no longer a separate chunk");
        const worker = Object.keys(bundle).find((f) => WORKER_ASSET.test(f));
        if (!worker) throw new Error("preload-embed: no maplibre-gl-worker asset in the bundle");
        const tags: HtmlTagDescriptor[] = [];
        // The pack index first: everything the embed shows hangs off it. (Built in generateBundle, after this hook;
        // an offline build has none, and the embed then falls back to browser-side windows: a wasted 404 only there.)
        tags.push({ tag: "link", attrs: { rel: "preload", as: "fetch", crossorigin: "anonymous", href: `${base}${PACK_DIR}/index.json` }, injectTo: "head" });
        const closure = chunkClosure(bundle, map);
        for (const { fileName } of closure) {
          if (html.includes(`${base}${fileName}"`)) continue;
          tags.push({ tag: "link", attrs: { rel: "modulepreload", crossorigin: true, href: `${base}${fileName}` }, injectTo: "head" });
        }
        for (const css of new Set(closure.flatMap((c) => [...(c.viteMetadata?.importedCss ?? [])]))) {
          if (html.includes(`${base}${css}"`)) continue;
          tags.push({ tag: "link", attrs: { rel: "preload", as: "style", crossorigin: true, href: `${base}${css}` }, injectTo: "head" });
        }
        tags.push({ tag: "link", attrs: { rel: "preload", as: "fetch", crossorigin: "anonymous", href: `${base}${worker}` }, injectTo: "head" });
        return { html, tags };
      },
    },
  };
}
