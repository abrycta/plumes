// Cloudflare Pages Function: the same-origin edge cache in front of the Java API (DATA-PLAN §8, Q20).
//   /api/v1/*      -> {API_ORIGIN}/v1/*   cached at the edge (s-maxage + stale-while-revalidate, revalidated by ETag)
//   /api/healthz, /api/readyz             passed through, never cached
// Render free sleeps after 15 minutes and its 5 GB of monthly egress is shared, so every read is served from the
// edge when possible. A cold origin gets a 503 "backend-waking" problem with Retry-After (as Replay's edge), while the
// request keeps running in the background to wake the service and fill the cache.
// A stored copy follows the published data version: its ETag names the version it was built from (`-d2"`), and the
// edge reads the published latest.json (DATA_ROOT, at most once a minute). A copy of an older version is not served as
// fresh: the edge asks the origin again (conditionally, at most once a minute while the origin still holds the old
// version), so a new version reaches every route within about a minute of the API load, with no purge.
// While the origin sleeps and nothing is stored, the list and the per-volcano files (equal to the published files by
// the contract) are answered from the published data root instead of a 503.
// Pages only invokes Functions for /api/* (the routes are generated from this folder); static assets never run it.
// Settings (Pages project variables): API_ORIGIN (default below), DATA_ROOT (the published data root, holds
// latest.json), EDGE_SECRET (secret, also set on Render as PLUMES_EDGE_SECRET: the origin answers /v1 only to
// requests that carry it).

interface Env {
  API_ORIGIN?: string;
  DATA_ROOT?: string;
  EDGE_SECRET?: string;
}

interface Context {
  request: Request;
  env: Env;
  waitUntil(promise: Promise<unknown>): void;
}

const DEFAULT_ORIGIN = "https://plumes-java.onrender.com";
const DEFAULT_DATA_ROOT = "https://krtmtthw.dev/plumes/data/";
const PROBLEM_BASE = "https://plumes.krtmtthw.dev/problems/";
/** How long a reader waits for the origin before getting "waking" (a warm origin answers in well under 1 s). */
const ORIGIN_TIMEOUT_MS = 8000;
/** Background work after the response is capped at 30 s by the runtime. */
const BACKGROUND_TIMEOUT_MS = 29_000;
const HEALTH_TIMEOUT_MS = 3000;
const WAKE_RETRY_AFTER_S = 10;
/** Fallbacks when the origin sends no s-maxage / stale-while-revalidate. */
const DEFAULT_FRESH_S = 3600;
const DEFAULT_STALE_S = 86_400;
const STORED_AT = "X-Edge-Stored-At";
/** How often the published version is re-read, and how often an outdated copy is re-checked with the origin. */
const VERSION_TTL_S = 60;
const VERSION_TIMEOUT_MS = 1500;
const FORWARD = ["accept", "accept-language", "user-agent"];

type Label = "HIT" | "MISS" | "STALE" | "BYPASS" | "REVALIDATED" | "FALLBACK";

interface Published {
  current: string;
  base: string;
}

export const onRequest = async (context: Context): Promise<Response> => {
  const t0 = Date.now();
  const { request, env } = context;
  const url = new URL(request.url);
  const rest = url.pathname.replace(/^\/api/, "") || "/";
  const origin = (env.API_ORIGIN || DEFAULT_ORIGIN).replace(/\/$/, "");
  const done = (r: Response, label: Label) => decorate(r, label, t0);

  if (request.method !== "GET" && request.method !== "HEAD") {
    return done(problem("method-not-allowed", 405, "Method not allowed", { headers: { Allow: "GET, HEAD" } }), "BYPASS");
  }
  const target = new URL(origin + rest + url.search);

  if (rest === "/healthz" || rest === "/readyz") {
    const r = await originFetch(target, request, env, HEALTH_TIMEOUT_MS);
    if (r === "timeout") return done(waking(), "BYPASS");
    if (r instanceof Error) return done(problem("bad-gateway", 502, "Bad gateway"), "BYPASS");
    return done(passthrough(r), "BYPASS");
  }
  if (!rest.startsWith("/v1/")) return done(problem("not-found", 404, "Not found"), "BYPASS");

  const cache = (caches as unknown as { default: Cache }).default;
  const key = new Request(target.toString(), { method: "GET" });
  const [cached, published] = await Promise.all([cache.match(key), publishedVersion(env)]);
  const inm = request.headers.get("If-None-Match");
  const cold = async (fallback: Response) => {
    const file = await publishedFile(rest, url.search, published);
    return file ? done(file, "FALLBACK") : done(fallback, "MISS");
  };

  if (cached) {
    const age = (Date.now() - Number(cached.headers.get(STORED_AT) || 0)) / 1000;
    const { fresh, stale } = lifetimes(cached.headers.get("Cache-Control"));
    const held = versionOf(cached.headers.get("ETag"));
    if (published && held && held !== published.current) {
      // Built from an older version: ask the origin below (it may not hold the new one yet; then ask again later).
      if (age < VERSION_TTL_S) return done(answer(cached, inm, request, "origin-not-loaded"), "STALE");
    } else {
      if (age < fresh) return done(answer(cached, inm, request), "HIT");
      if (age < fresh + stale) {
        context.waitUntil(revalidate(cache, key, cached, target, request, env).catch(() => undefined));
        return done(answer(cached, inm, request, "revalidating"), "STALE");
      }
    }
  }

  const pending = originFetch(target, request, env, BACKGROUND_TIMEOUT_MS, cached?.headers.get("ETag"));
  const first = await Promise.race([pending, sleep(ORIGIN_TIMEOUT_MS).then(() => "slow" as const)]);
  if (first === "slow") {
    // Cold start: keep going in the background (wakes Render, then fills the cache).
    context.waitUntil(pending.then((r) => settle(cache, key, cached, r)).catch(() => undefined));
    if (cached) return done(answer(cached, inm, request, "origin-slow"), "STALE");
    return cold(waking());
  }
  if (first === "timeout" || first instanceof Error) {
    if (cached) return done(answer(cached, inm, request, "origin-error"), "STALE");
    return cold(first === "timeout" ? waking() : problem("bad-gateway", 502, "Bad gateway"));
  }
  if (first.status === 304 && cached) {
    // The origin still holds the stored copy's version: keep it, and ask again after VERSION_TTL_S / its lifetime.
    const reply = answer(cached, inm, request);
    context.waitUntil(settle(cache, key, cached, first).catch(() => undefined));
    return done(reply, "REVALIDATED");
  }
  if (await isWaking(first)) {
    // Render is up but Neon is resuming: one background retry fills the cache.
    context.waitUntil(sleep(4000).then(() => originFetch(target, request, env, BACKGROUND_TIMEOUT_MS - 4000))
      .then((r) => settle(cache, key, undefined, r)).catch(() => undefined));
    if (cached) return done(answer(cached, inm, request, "origin-waking"), "STALE");
    return cold(waking());
  }
  if (first.status >= 500 && cached) return done(answer(cached, inm, request, "origin-error"), "STALE");
  if (first.status >= 500) return cold(passthrough(first));
  if (first.status === 200 || first.status === 404) {
    const copy = first.clone();
    context.waitUntil(store(cache, key, copy).catch(() => undefined));
  }
  return done(answer(first, inm, request), "MISS");
};

// -----------------------------------------------------------------------------------------------------------------

async function originFetch(target: URL, request: Request, env: Env, ms: number, etag?: string | null): Promise<Response | Error | "timeout"> {
  const headers = new Headers();
  for (const h of FORWARD) {
    const v = request.headers.get(h);
    if (v) headers.set(h, v);
  }
  headers.set("Accept-Encoding", "gzip"); // Render bills the bytes it sends
  headers.set("X-Forwarded-Host", new URL(request.url).host);
  const ip = request.headers.get("CF-Connecting-IP");
  if (ip) headers.set("X-Forwarded-For", ip);
  if (env.EDGE_SECRET) headers.set("X-Edge-Secret", env.EDGE_SECRET);
  if (etag) headers.set("If-None-Match", etag);
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), ms);
  try {
    return await fetch(target.toString(), { method: "GET", headers, redirect: "manual", signal: ctrl.signal });
  } catch (e) {
    return ctrl.signal.aborted ? "timeout" : (e as Error);
  } finally {
    clearTimeout(timer);
  }
}

/** Store a copy with the time it was stored; the cache keeps it for the fresh + stale window. */
async function store(cache: Cache, key: Request, response: Response): Promise<void> {
  if (response.status !== 200 && response.status !== 404) {
    await response.body?.cancel();
    return;
  }
  const headers = new Headers(response.headers);
  const { fresh, stale } = lifetimes(headers.get("Cache-Control"));
  headers.set(STORED_AT, String(Date.now()));
  headers.set("Cloudflare-CDN-Cache-Control", `max-age=${fresh + stale}`);
  headers.delete("Set-Cookie");
  await cache.put(key, new Response(response.body, { status: response.status, headers }));
}

async function revalidate(cache: Cache, key: Request, cached: Response, target: URL, request: Request, env: Env) {
  const r = await originFetch(target, request, env, BACKGROUND_TIMEOUT_MS, cached.headers.get("ETag"));
  await settle(cache, key, cached, r);
}

/** File an origin answer: a 304 restarts the stored copy's clock, a 200 or 404 replaces it, anything else is dropped. */
async function settle(cache: Cache, key: Request, cached: Response | undefined, r: Response | Error | "timeout") {
  if (!(r instanceof Response)) return;
  if (r.status === 304 && cached) {
    const headers = new Headers(cached.headers);
    headers.set(STORED_AT, String(Date.now()));
    await cache.put(key, new Response(cached.body, { status: cached.status, headers }));
  } else if (r.status === 200 || r.status === 404) {
    await store(cache, key, r);
  } else {
    await r.body?.cancel();
  }
}

/** The data version a stored copy was built from, read from its weak ETag (`W/"c1.0.0-java-0.1.0-d2"` -> "v2"). */
function versionOf(etag: string | null): string | null {
  const m = /-d([0-9A-Za-z.]+)"$/.exec(etag ?? "");
  return m ? "v" + m[1] : null;
}

let publishedMemo: { at: number; value: Published | null } | undefined;

/** The published version (latest.json under DATA_ROOT), re-read at most once a minute; null when unknown. */
async function publishedVersion(env: Env): Promise<Published | null> {
  if (publishedMemo && Date.now() - publishedMemo.at < VERSION_TTL_S * 1000) return publishedMemo.value;
  const root = (env.DATA_ROOT || DEFAULT_DATA_ROOT).replace(/\/?$/, "/");
  let value: Published | null = null;
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), VERSION_TIMEOUT_MS);
  try {
    const init = { signal: ctrl.signal, cf: { cacheTtl: VERSION_TTL_S, cacheEverything: true } } as RequestInit;
    const r = await fetch(root + "latest.json", init);
    if (r.ok) {
      const j = (await r.json()) as { current?: unknown; base?: unknown };
      if (typeof j.current === "string" && /^v[0-9]+$/.test(j.current)) {
        const base = typeof j.base === "string" ? j.base : j.current + "/";
        value = { current: j.current, base: new URL(base, root).toString() };
      }
    } else {
      await r.body?.cancel();
    }
  } catch {
    // unknown this time; keep the last known value below
  } finally {
    clearTimeout(timer);
  }
  publishedMemo = { at: Date.now(), value: value ?? publishedMemo?.value ?? null };
  return publishedMemo.value;
}

/**
 * The published file a route equals by the contract (`/v1/volcanoes` = volcanoes.geojson, `/v1/volcanoes/{id}` =
 * volcano/{id}.json), for a cold origin with nothing stored; null for any other route or when the file is missing.
 */
async function publishedFile(rest: string, search: string, published: Published | null): Promise<Response | null> {
  if (!published || search) return null;
  let file: string | null = null;
  let type = "application/json";
  if (rest === "/v1/volcanoes") {
    file = "volcanoes.geojson";
    type = "application/geo+json";
  } else {
    const m = /^\/v1\/volcanoes\/([a-z0-9-]{1,60})$/.exec(rest);
    if (m && m[1] !== "nearest") file = `volcano/${m[1]}.json`;
  }
  if (!file) return null;
  try {
    const r = await fetch(published.base + file, { cf: { cacheTtl: 3600, cacheEverything: true } } as RequestInit);
    if (!r.ok) {
      await r.body?.cancel();
      return null;
    }
    const headers = new Headers({ "Content-Type": type, "Cache-Control": "no-store", "X-Edge-Fallback": "published-file" });
    return new Response(r.body, { status: 200, headers });
  } catch {
    return null;
  }
}

/** Seconds a stored copy is fresh, then may be served stale while revalidating. */
function lifetimes(cc: string | null): { fresh: number; stale: number } {
  const get = (name: string) => {
    const m = new RegExp(`(?:^|,)\\s*${name}=(\\d+)`).exec(cc ?? "");
    return m ? Number(m[1]) : undefined;
  };
  return { fresh: get("s-maxage") ?? get("max-age") ?? DEFAULT_FRESH_S, stale: get("stale-while-revalidate") ?? DEFAULT_STALE_S };
}

/** 304 when the client already holds this version (weak comparison), else the stored or fetched response. */
function answer(r: Response, ifNoneMatch: string | null, request: Request, stale?: string): Response {
  const etag = r.headers.get("ETag");
  const headers = new Headers(r.headers);
  headers.delete(STORED_AT);
  headers.delete("Cloudflare-CDN-Cache-Control");
  for (const h of ["x-render-origin-server", "rndr-id", "server"]) headers.delete(h);
  if (stale) headers.set("X-Edge-Stale", stale);
  if (r.status === 200 && etag && ifNoneMatch && matches(ifNoneMatch, etag)) {
    for (const h of ["Content-Type", "Content-Length", "Content-Encoding"]) headers.delete(h);
    return new Response(null, { status: 304, headers });
  }
  const body = request.method === "HEAD" ? null : r.clone().body;
  return new Response(body, { status: r.status, headers });
}

function matches(ifNoneMatch: string, etag: string): boolean {
  if (ifNoneMatch.trim() === "*") return true;
  const strip = (t: string) => t.trim().replace(/^W\//, "");
  return ifNoneMatch.split(",").some((t) => strip(t) === strip(etag));
}

async function isWaking(r: Response): Promise<boolean> {
  if (r.status !== 503) return false;
  if (!(r.headers.get("Content-Type") ?? "").includes("json")) return true; // Render's own 503 page
  try {
    const { code } = (await r.clone().json()) as { code?: string };
    return code === "not-ready";
  } catch {
    return false;
  }
}

function passthrough(r: Response): Response {
  if ([502, 503, 504].includes(r.status) && !(r.headers.get("Content-Type") ?? "").includes("json")) return waking();
  const headers = new Headers(r.headers);
  for (const h of ["x-render-origin-server", "rndr-id", "server"]) headers.delete(h);
  return new Response(r.body, { status: r.status, headers });
}

function waking(): Response {
  return problem("backend-waking", 503, "Backend is waking up", {
    detail: "The API runs on free hosting that sleeps when idle; it takes a few seconds to wake. The site does not need it.",
    headers: { "Retry-After": String(WAKE_RETRY_AFTER_S) },
  });
}

function problem(code: string, status: number, title: string, o: { detail?: string; headers?: Record<string, string> } = {}): Response {
  const body: Record<string, unknown> = { type: PROBLEM_BASE + code, title, status, code };
  if (o.detail) body.detail = o.detail;
  const headers = new Headers(o.headers);
  headers.set("Content-Type", "application/problem+json");
  headers.set("Cache-Control", "no-store");
  return new Response(JSON.stringify(body), { status, headers });
}

function decorate(r: Response, label: Label, t0: number): Response {
  const headers = new Headers(r.headers);
  headers.set("X-Edge-Cache", label);
  headers.append("Server-Timing", `edge;dur=${Date.now() - t0}`);
  return new Response(r.body, { status: r.status, statusText: r.statusText, headers });
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
