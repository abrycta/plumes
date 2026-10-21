// Cloudflare Pages Function: the same-origin edge cache in front of the Java API (DATA-PLAN §8, Q20).
//   /api/v1/*      -> {API_ORIGIN}/v1/*   cached at the edge (s-maxage + stale-while-revalidate, revalidated by ETag)
//   /api/healthz, /api/readyz             passed through, never cached
// Render free sleeps after 15 minutes and its 5 GB of monthly egress is shared, so every read is served from the
// edge when possible. A cold origin gets a 503 "backend-waking" problem with Retry-After (as Replay's edge), while the
// request keeps running in the background to wake the service and fill the cache.
// Pages only invokes Functions for /api/* (the routes are generated from this folder); static assets never run it.
// Settings (Pages project variables): API_ORIGIN (default below), EDGE_SECRET (secret, also set on Render as
// PLUMES_EDGE_SECRET: the origin answers /v1 only to requests that carry it).

interface Env {
  API_ORIGIN?: string;
  EDGE_SECRET?: string;
}

interface Context {
  request: Request;
  env: Env;
  waitUntil(promise: Promise<unknown>): void;
}

const DEFAULT_ORIGIN = "https://plumes-java.onrender.com";
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
const FORWARD = ["accept", "accept-language", "user-agent"];

type Label = "HIT" | "MISS" | "STALE" | "BYPASS";

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
  const cached = await cache.match(key);
  const inm = request.headers.get("If-None-Match");

  if (cached) {
    const age = (Date.now() - Number(cached.headers.get(STORED_AT) || 0)) / 1000;
    const { fresh, stale } = lifetimes(cached.headers.get("Cache-Control"));
    if (age < fresh) return done(answer(cached, inm, request), "HIT");
    if (age < fresh + stale) {
      context.waitUntil(revalidate(cache, key, cached, target, request, env).catch(() => undefined));
      return done(answer(cached, inm, request, "revalidating"), "STALE");
    }
  }

  const pending = originFetch(target, request, env, BACKGROUND_TIMEOUT_MS);
  const first = await Promise.race([pending, sleep(ORIGIN_TIMEOUT_MS).then(() => "slow" as const)]);
  if (first === "slow") {
    // Cold start: keep going in the background (wakes Render, then fills the cache).
    context.waitUntil(pending.then((r) => (r instanceof Response ? store(cache, key, r) : undefined)).catch(() => undefined));
    if (cached) return done(answer(cached, inm, request, "origin-slow"), "STALE");
    return done(waking(), "MISS");
  }
  if (first === "timeout" || first instanceof Error) {
    if (cached) return done(answer(cached, inm, request, "origin-error"), "STALE");
    return done(first === "timeout" ? waking() : problem("bad-gateway", 502, "Bad gateway"), "MISS");
  }
  if (await isWaking(first)) {
    // Render is up but Neon is resuming: one background retry fills the cache.
    context.waitUntil(sleep(4000).then(() => originFetch(target, request, env, BACKGROUND_TIMEOUT_MS - 4000))
      .then((r) => (r instanceof Response ? store(cache, key, r) : undefined)).catch(() => undefined));
    if (cached) return done(answer(cached, inm, request, "origin-waking"), "STALE");
    return done(waking(), "MISS");
  }
  if (first.status >= 500 && cached) return done(answer(cached, inm, request, "origin-error"), "STALE");
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
  if (!(r instanceof Response)) return;
  if (r.status === 304) {
    const headers = new Headers(cached.headers);
    headers.set(STORED_AT, String(Date.now()));
    await cache.put(key, new Response(cached.body, { status: cached.status, headers }));
  } else if (r.status === 200 || r.status === 404) {
    await store(cache, key, r);
  } else {
    await r.body?.cancel();
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
