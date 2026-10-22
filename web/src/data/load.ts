// Data loading: public/config.json names the data base URL (and fallbacks); latest.json there points at the
// current immutable version; every other file is fetched relative to that version's base. Promises are cached
// per path so React's use() can suspend on them. Nothing is fetched at interaction time beyond these files.

import type { Latest, Layers, StoriesIndex, Story, StoryIndexEntry, VolcanoesIndex, VolcanoReadModel } from "@contracts/readmodels";

export interface AppConfig {
  siteUrl?: string;
  data: { baseUrl: string; pointer?: string; fallbackBaseUrls?: string[] };
  basemap?: { style?: string; fallback?: string };
}

export interface DataRoot {
  latest: Latest;
  /** Absolute URL of the version folder, ending in "/". */
  versionBase: string;
  /** Other version bases to try when a file is missing (latest.mirrors + config fallbacks). */
  mirrors: string[];
}

export class NotFoundError extends Error {}

const DEFAULT_CONFIG: AppConfig = { data: { baseUrl: "/data/", pointer: "latest.json" } };

/** Join a base URL and a relative path; base may be relative to the page. */
export function resolveUrl(base: string, path: string): string {
  const origin = typeof location !== "undefined" ? location.href : "http://localhost/";
  return new URL(path, new URL(base, origin)).toString();
}

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url, { headers: { Accept: "application/json" } });
  if (res.status === 404) throw new NotFoundError(`Not found: ${url}`);
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  // Static hosts with an SPA fallback (Cloudflare Pages, vite preview) answer a missing file with index.html.
  if ((res.headers.get("content-type") ?? "").includes("text/html")) throw new NotFoundError(`Not found (HTML answer): ${url}`);
  return (await res.json()) as T;
}

let configP: Promise<AppConfig> | null = null;
export function loadConfig(): Promise<AppConfig> {
  configP ??= getJson<AppConfig>("/config.json").catch(() => DEFAULT_CONFIG);
  return configP;
}

/** Try each base for the pointer; the first that answers wins. */
export async function resolveRoot(config: AppConfig, fetchJson: <T>(url: string) => Promise<T> = getJson): Promise<DataRoot> {
  const pointer = config.data.pointer ?? "latest.json";
  const bases = [config.data.baseUrl, ...(config.data.fallbackBaseUrls ?? [])];
  let lastError: unknown = null;
  for (const base of bases) {
    try {
      const latest = await fetchJson<Latest>(resolveUrl(base, pointer));
      const versionBase = resolveUrl(base, latest.base.endsWith("/") ? latest.base : `${latest.base}/`);
      const mirrors = [...(latest.mirrors ?? []), ...bases.filter((b) => b !== base)].map((m) => resolveUrl(m, latest.base.endsWith("/") ? latest.base : `${latest.base}/`));
      return { latest, versionBase, mirrors };
    } catch (e) {
      lastError = e;
    }
  }
  throw lastError instanceof Error ? lastError : new Error("No data base URL answered");
}

let rootP: Promise<DataRoot> | null = null;
export function loadRoot(): Promise<DataRoot> {
  rootP ??= loadConfig().then((c) => resolveRoot(c));
  return rootP;
}

const cache = new Map<string, Promise<unknown>>();

/** A file of the current version (path relative to the version root), trying mirrors when the primary fails. */
export function loadFile<T>(path: string): Promise<T> {
  let p = cache.get(path) as Promise<T> | undefined;
  if (!p) {
    p = loadRoot().then(async (root) => {
      try {
        return await getJson<T>(resolveUrl(root.versionBase, path));
      } catch (e) {
        if (e instanceof NotFoundError) throw e;
        for (const m of root.mirrors) {
          try {
            return await getJson<T>(resolveUrl(m, path));
          } catch {
            /* next mirror */
          }
        }
        throw e;
      }
    });
    cache.set(path, p);
  }
  return p;
}

/** URL of an asset (image) in the current version. */
export function assetUrl(root: DataRoot, path: string): string {
  return resolveUrl(root.versionBase, path);
}

export const loadVolcanoes = () => loadFile<VolcanoesIndex>("volcanoes.geojson");
export const loadLayers = () => loadFile<Layers>("layers.json");
/** The per-volcano read model, or null when this version has none for the volcano. */
export function loadVolcano(file: string): Promise<VolcanoReadModel | null> {
  const key = `volcano:${file}`;
  let p = cache.get(key) as Promise<VolcanoReadModel | null> | undefined;
  if (!p) {
    p = loadFile<VolcanoReadModel>(file).catch((e) => {
      if (e instanceof NotFoundError) return null;
      throw e;
    });
    cache.set(key, p);
  }
  return p;
}
/** Stories known to versions without a stories.json (v1, v2): Taal January 2020, reviewed. */
export const STORIES = [{ id: "taal-2020", volcanoId: "taal" }] as const;

/** A story the site may show: its id, file and review status. */
export interface StoryRef {
  id: string;
  volcanoId: string;
  file: string;
  status: "draft" | "reviewed";
}

let indexP: Promise<StoriesIndex | null> | null = null;
/** <version>/stories.json, or null for versions made before the story generator. */
export function loadStoriesIndex(): Promise<StoriesIndex | null> {
  indexP ??= loadFile<StoriesIndex>("stories.json").catch((e) => {
    if (e instanceof NotFoundError) return null;
    throw e;
  });
  return indexP;
}

/**
 * The stories to list, in the index's order. Reviewed stories always; drafts only in preview (ST1), where a draft
 * replaces the reviewed file of the same id so Kurt reviews what the generator would publish.
 */
export function storyRefs(index: StoriesIndex | null, preview: boolean): StoryRef[] {
  if (!index) return STORIES.map((s) => ({ ...s, file: `story/${s.id}.json`, status: "reviewed" as const }));
  const out = new Map<string, StoryRef>();
  for (const e of index.stories as StoryIndexEntry[]) {
    if (!e.file) continue;
    if (e.status === "draft" && !preview) continue;
    const prev = out.get(e.id);
    if (!prev || (preview && e.status === "draft")) out.set(e.id, { id: e.id, volcanoId: e.volcanoId, file: e.file, status: e.status });
  }
  return [...out.values()];
}

const storyFiles = new Map<string, Promise<Story | null>>();
/** A story file, or null when this version has none. */
export function loadStoryFile(file: string): Promise<Story | null> {
  let p = storyFiles.get(file);
  if (!p) {
    p = loadFile<Story>(file).catch((e) => {
      if (e instanceof NotFoundError) return null;
      throw e;
    });
    storyFiles.set(file, p);
  }
  return p;
}
