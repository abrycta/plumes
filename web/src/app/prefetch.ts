// Start the first view's files as soon as the entry script runs, before React renders and before the page's lazy
// chunk arrives. Each page reads the same cached promises (data/load.ts, map/windowData.ts), so nothing is fetched
// twice and nothing is shown differently; the requests only start a few round trips earlier.
// The map page on rich-media screens (workspace rule 6b, lib/richMedia.ts) also starts the MapLibre chunk and its
// worker; phones and tablets, which get the static map, never fetch them.

import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?url";

import { loadLayers, loadRoot, loadStoryOrNull, loadVolcano, loadVolcanoes, STORIES } from "@/data/load";
import { snapshot as richMediaNow } from "@/lib/richMedia";

import { parseUrl } from "./url";

function preload(href: string, as: string) {
  const link = document.createElement("link");
  link.rel = "preload";
  link.as = as;
  link.href = href;
  link.crossOrigin = "anonymous";
  document.head.appendChild(link);
}

function preconnect(origin: string) {
  const link = document.createElement("link");
  link.rel = "preconnect";
  link.href = origin;
  link.crossOrigin = "anonymous";
  document.head.appendChild(link);
}

const quiet = (p: Promise<unknown>) => void p.catch(() => {});

export function prefetchFirstView(): void {
  const { page, id } = parseUrl(location.pathname, location.search);
  switch (page) {
    case "map": {
      if (richMediaNow()) {
        quiet(import("@/map/InteractiveMap"));
        // MapLibre starts this as a module worker; /assets/* is immutable, so the worker reads it from the HTTP cache.
        preload(workerUrl, "fetch");
        preconnect("https://tiles.openfreemap.org");
      }
      // The first window's pack (map/firstWindow.ts) does not depend on the data index: ask for it at once.
      quiet(import("@/map/firstWindow").then((f) => f.loadFirstWindowPack()));
      const index = loadVolcanoes();
      const layers = loadLayers();
      quiet(
        Promise.all([import("@/map/windowData"), import("@/map/firstWindow"), index, layers, loadRoot()]).then(([w, f, ix, ly, root]) => {
          const record = w.recordMonths(ly, root.latest.dataAsOf);
          const stamp = f.dataStamp(root.latest);
          return Promise.all([w.loadWindowShared(ly, root.versionBase, ix, w.defaultWindowMonths(record), stamp), w.recordQuakeCounts(ly, root.versionBase, record, stamp)]);
        }),
      );
      break;
    }
    case "volcanoes":
      quiet(loadVolcanoes());
      break;
    case "volcano":
      quiet(
        loadVolcanoes().then((ix) => {
          const f = ix.features.find((x) => x.properties.id === id);
          return f ? loadVolcano(f.properties.file) : null;
        }),
      );
      break;
    case "stories":
      for (const s of STORIES) quiet(loadStoryOrNull(s.id));
      break;
    case "story":
      if (id)
        quiet(
          loadStoryOrNull(id).then((story) => (story ? loadVolcano(story.volcanoFile ?? `volcano/${story.volcanoId}.json`) : null)),
        );
      break;
    default:
  }
}
