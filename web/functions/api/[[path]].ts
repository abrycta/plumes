// Cloudflare Pages Function: the same-origin edge cache in front of the Java API (DATA-PLAN §8, Q20).
//   /api/v1/*      -> {API_ORIGIN}/v1/*   cached at the edge (s-maxage + stale-while-revalidate, revalidated by ETag)
//   /api/healthz, /api/readyz             cached at the edge for 30 s (200s only), so probes don't each reach Render
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
// Abuse guards (no Cloudflare zone, so no WAF rule can do this): every /api request takes a token from a per-IP
// bucket (RATE_PER_MINUTE, burst RATE_BURST; over it: 429 with Retry-After), only routes in contracts/openapi.yaml
// are proxied (others: 404 at the edge), and the query string is cut down to the parameters the contract lists for
// the route, in a fixed order, before it builds the cache key and the origin URL, so junk parameters can't miss the
// cache and wake Render. Point queries (lat and lon) are rounded to 2 decimals (about 1 km) the same way, so nearby
// requests share one cache entry; the answer is for the rounded point (its `query` echoes it). Every /api response carries X-Robots-Tag: noindex.
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
/** How long a 200 from /healthz or /readyz is served from the edge. */
const HEALTH_CACHE_S = 30;
const WAKE_RETRY_AFTER_S = 10;
/** Fallbacks when the origin sends no s-maxage / stale-while-revalidate. */
const DEFAULT_FRESH_S = 3600;
const DEFAULT_STALE_S = 86_400;
const STORED_AT = "X-Edge-Stored-At";
/** The origin's Cache-Control, kept on a stored copy whose own Cache-Control sets how long the Cache API keeps it. */
const ORIGIN_CC = "X-Edge-Origin-Cache-Control";
/** How often the published version is re-read, and how often an outdated copy is re-checked with the origin. */
const VERSION_TTL_S = 60;
const VERSION_TIMEOUT_MS = 1500;
const FORWARD = ["accept", "accept-language", "user-agent"];
/** Per-IP token bucket (as Replay's edge/src/ratelimit.ts): best effort, per isolate. */
const RATE_PER_MINUTE = 120;
const RATE_BURST = 60;
const RATE_MAX_KEYS = 10_000;
/** Decimals kept for lat/lon query parameters (0.01 degree is about 1.1 km), and their contract bounds. */
const COORD_DECIMALS = 2;
const COORD_BOUNDS: Readonly<Record<string, number>> = { lat: 90, lon: 180 };
/** The contract's routes (contracts/openapi.yaml) and the query parameters each one takes; first match wins. */
const ROUTES: ReadonlyArray<readonly [RegExp, readonly string[]]> = [
  [/^\/healthz$/, []],
  [/^\/readyz$/, []],
  [/^\/v1\/meta$/, []],
  [/^\/v1\/openapi\.yaml$/, []],
  [/^\/v1\/volcanoes$/, []],
  [/^\/v1\/volcanoes\/nearest$/, ["lat", "lon", "limit"]],
  [/^\/v1\/volcanoes\/[a-z0-9-]{1,64}$/, []],
  [/^\/v1\/events$/, ["volcano", "lat", "lon", "radiusKm", "from", "to", "kind", "limit"]],
  [/^\/v1\/eruptions\/precursors$/, ["minVei", "days", "radiusKm", "since"]],
];

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

  const ip = request.headers.get("CF-Connecting-IP");
  const rate = ip ? takeToken(ip, Date.now()) : 0;
  if (rate > 0) {
    return done(
      problem("rate-limited", 429, "Too many requests", {
        detail: "This address sent too many API requests in a short time. Wait a moment and try again.",
        headers: { "Retry-After": String(rate) },
      }),
      "BYPASS",
    );
  }
  if (request.method !== "GET" && request.method !== "HEAD") {
    return done(problem("method-not-allowed", 405, "Method not allowed", { headers: { Allow: "GET, HEAD" } }), "BYPASS");
  }
  const route = ROUTES.find(([re]) => re.test(rest));
  if (!route) return done(problem("not-found", 404, "Not found"), "BYPASS");
  const search = normalQuery(url.search, route[1]);
  const target = new URL(origin + rest + search);

  const cache = (caches as unknown as { default: Cache }).default;
  const key = new Request(target.toString(), { method: "GET" });
  if (rest === "/healthz" || rest === "/readyz") {
    const inm = request.headers.get("If-None-Match");
    const cached = await cache.match(key);
    if (cached && Date.now() - Number(cached.headers.get(STORED_AT) || 0) < HEALTH_CACHE_S * 1000) {
      return done(answer(cached, inm, request), "HIT");
    }
    const r = await originFetch(target, request, env, HEALTH_TIMEOUT_MS);
    if (r === "timeout") return done(waking(), "BYPASS");
    if (r instanceof Error) return done(problem("bad-gateway", 502, "Bad gateway"), "BYPASS");
    const out = passthrough(r);
    if (out.status !== 200) return done(out, "BYPASS");
    // Only a 200 is kept, for HEALTH_CACHE_S; a waking or failing origin is never pinned at the edge.
    const body = await out.arrayBuffer();
    const headers = new Headers(out.headers);
    headers.set(ORIGIN_CC, headers.get("Cache-Control") ?? "");
    headers.set("Cache-Control", `public, max-age=${HEALTH_CACHE_S}`);
    headers.set(STORED_AT, String(Date.now()));
    headers.delete("Set-Cookie");
    context.waitUntil(cache.put(key, new Response(body.slice(0), { status: 200, headers })).catch(() => undefined));
    return done(answer(new Response(body, { status: 200, headers }), inm, request), "MISS");
  }
  const [cached, published] = await Promise.all([cache.match(key), publishedVersion(env)]);
  const inm = request.headers.get("If-None-Match");
  const cold = async (fallback: Response) => {
    const file = await publishedFile(rest, search, published);
    return file ? done(file, "FALLBACK") : done(fallback, "MISS");
  };

  if (cached) {
    const age = (Date.now() - Number(cached.headers.get(STORED_AT) || 0)) / 1000;
    const { fresh, stale } = lifetimes(originCc(cached));
    const held = versionOf(cached.headers.get("ETag"));
    if (published && held && held !== published.current) {
      // Built from an older version: ask the origin below (it may not hold the new one yet; then ask again later).
      if (age < VERSION_TTL_S) return done(answer(cached, inm, request, "origin-not-loaded"), "STALE");
    } else {
      if (age < fresh) return done(answer(cached, inm, request), "HIT");
      if (age < fresh + stale) {
        context.waitUntil(fill(cache, key, cached, target, request, env).catch(() => undefined));
        return done(answer(cached, inm, request, "revalidating"), "STALE");
      }
    }
  }

  // One origin request per key at a time (per isolate): concurrent misses wait for the same answer, which also fills
  // the cache, instead of each waking Render.
  const pending = fill(cache, key, cached, target, request, env);
  context.waitUntil(pending.catch(() => undefined));
  const got = await Promise.race([pending, sleep(ORIGIN_TIMEOUT_MS).then(() => "slow" as const)]);
  if (got === "slow" || got === "timeout" || got instanceof Error) {
    // Cold start (the fill keeps going in the background, waking Render) or an origin failure: serve the stored copy.
    const note = got === "slow" ? "origin-slow" : "origin-error";
    if (cached) return done(answer(cached, inm, request, note), "STALE");
    return cold(got === "slow" || got === "timeout" ? waking() : problem("bad-gateway", 502, "Bad gateway"));
  }
  const first = toResponse(got);
  if (first.status === 304) {
    // The origin still holds the stored copy's version (the fill restarted its clock): keep serving it.
    const held = cached ?? (await cache.match(key));
    if (held) return done(answer(held, inm, request), "REVALIDATED");
    return cold(waking());
  }
  if (await isWaking(first)) {
    // Render is up but Neon is resuming: one background retry (shared too) fills the cache.
    context.waitUntil(
      sleep(4000)
        .then(() => fill(cache, key, undefined, target, request, env, BACKGROUND_TIMEOUT_MS - 4000))
        .catch(() => undefined),
    );
    if (cached) return done(answer(cached, inm, request, "origin-waking"), "STALE");
    return cold(waking());
  }
  if (first.status >= 500 && cached) return done(answer(cached, inm, request, "origin-error"), "STALE");
  if (first.status >= 500) return cold(passthrough(first));
  return done(answer(first, inm, request), "MISS");
};

// -----------------------------------------------------------------------------------------------------------------

const buckets = new Map<string, { tokens: number; at: number }>();

/** Take one token from this IP's bucket: 0 when allowed, else the seconds until a token is free (Retry-After). */
function takeToken(key: string, now: number): number {
  const perMs = RATE_PER_MINUTE / 60_000;
  const prev = buckets.get(key);
  let tokens = prev ? Math.min(RATE_BURST, prev.tokens + (now - prev.at) * perMs) : RATE_BURST;
  if (prev) buckets.delete(key); // re-inserted below: Map order doubles as LRU order
  if (tokens < 1) {
    buckets.set(key, { tokens, at: now });
    return Math.max(1, Math.ceil((1 - tokens) / perMs / 1000));
  }
  tokens -= 1;
  buckets.set(key, { tokens, at: now });
  if (buckets.size > RATE_MAX_KEYS) buckets.delete(buckets.keys().next().value!);
  return 0;
}

/**
 * Only the parameters the route takes, sorted by name, first value of each (as the origin reads them), with lat and
 * lon rounded to COORD_DECIMALS.
 */
export function normalQuery(search: string, allowed: readonly string[]): string {
  const q = new URLSearchParams(search);
  const out = new URLSearchParams();
  for (const name of [...allowed].sort()) {
    const v = q.get(name);
    const bound = COORD_BOUNDS[name];
    if (v !== null) out.set(name, bound === undefined ? v : roundCoord(v, bound));
  }
  const s = out.toString();
  return s ? "?" + s : "";
}

/**
 * A plain decimal coordinate within its contract bound, rounded to COORD_DECIMALS ("14.0042" -> "14", "121.0049" ->
 * "121", "-0.001" -> "0"). Anything else (not a plain number, out of range) is passed on unchanged, so the origin
 * still answers it with its own 400; rounding never turns an invalid value into a valid one.
 */
export function roundCoord(v: string, bound: number): string {
  if (!/^[+-]?(\d+(\.\d*)?|\.\d+)$/.test(v)) return v;
  const x = Number(v);
  if (!Number.isFinite(x) || Math.abs(x) > bound) return v;
  const r = Math.round(x * 10 ** COORD_DECIMALS) / 10 ** COORD_DECIMALS;
  return String(r === 0 ? 0 : r);
}

interface Fetched {
  status: number;
  headers: [string, string][];
  body: ArrayBuffer;
}

const inflight = new Map<string, Promise<Fetched | Error | "timeout">>();

/**
 * Ask the origin for a key once per isolate however many requests want it, file the answer in the cache, and hand
 * every waiting request the same buffered answer.
 */
function fill(cache: Cache, key: Request, cached: Response | undefined, target: URL, request: Request, env: Env, ms = BACKGROUND_TIMEOUT_MS) {
  let p = inflight.get(key.url);
  if (!p) {
    p = (async () => {
      const r = await originFetch(target, request, env, ms, cached?.headers.get("ETag"));
      if (!(r instanceof Response)) return r;
      const got: Fetched = { status: r.status, headers: [...r.headers], body: await r.arrayBuffer() };
      await settle(cache, key, cached, toResponse(got)).catch(() => undefined);
      return got;
    })().finally(() => inflight.delete(key.url));
    inflight.set(key.url, p);
  }
  return p;
}

function toResponse(f: Fetched): Response {
  const body = f.status === 304 || f.status === 204 ? null : f.body.slice(0);
  return new Response(body, { status: f.status, headers: f.headers });
}

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
  const headers = keepFor(new Headers(response.headers));
  headers.set(STORED_AT, String(Date.now()));
  headers.delete("Set-Cookie");
  await cache.put(key, new Response(response.body, { status: response.status, headers }));
}

/**
 * The Cache API keeps an entry for its Cache-Control lifetime (s-maxage first) and ignores stale-while-revalidate, so
 * a stored copy gets Cache-Control max-age = fresh + stale (the whole window this function serves it in) and the
 * origin's own value moves to ORIGIN_CC. Without this a copy vanished after s-maxage (10 minutes for /v1/meta) and a
 * sleeping origin left nothing to serve.
 */
function keepFor(headers: Headers): Headers {
  if (!headers.has(ORIGIN_CC)) headers.set(ORIGIN_CC, headers.get("Cache-Control") ?? "");
  const { fresh, stale } = lifetimes(headers.get(ORIGIN_CC));
  headers.set("Cache-Control", `public, max-age=${fresh + stale}`);
  headers.set("Cloudflare-CDN-Cache-Control", `max-age=${fresh + stale}`);
  return headers;
}

/** The origin's Cache-Control for a stored copy (copies stored before ORIGIN_CC existed carry it as Cache-Control). */
function originCc(r: Response): string | null {
  return r.headers.has(ORIGIN_CC) ? r.headers.get(ORIGIN_CC) : r.headers.get("Cache-Control");
}

/** File an origin answer: a 304 restarts the stored copy's clock, a 200 or 404 replaces it, anything else is dropped. */
async function settle(cache: Cache, key: Request, cached: Response | undefined, r: Response | Error | "timeout") {
  if (!(r instanceof Response)) return;
  if (r.status === 304 && cached) {
    const headers = keepFor(new Headers(cached.headers));
    headers.set(STORED_AT, String(Date.now()));
    await cache.put(key, new Response(cached.clone().body, { status: cached.status, headers }));
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
  if (headers.has(ORIGIN_CC)) {
    const cc = headers.get(ORIGIN_CC);
    if (cc) headers.set("Cache-Control", cc);
    else headers.delete("Cache-Control");
    headers.delete(ORIGIN_CC);
  }
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
    detail: "The API sleeps when idle and takes a few seconds to wake. The site does not need it.",
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
  headers.set("X-Robots-Tag", "noindex");
  headers.append("Server-Timing", `edge;dur=${Date.now() - t0}`);
  return new Response(r.body, { status: r.status, statusText: r.statusText, headers });
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
