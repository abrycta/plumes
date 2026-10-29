#!/usr/bin/env node
// Render bandwidth guard for the Plumes API (.github/workflows/budget.yml; DATA-PLAN §7). No dependencies: Node 24.
//
// Render's workspace includes 5 GB of outbound bandwidth a month, shared by every service (Replay's too), and with a
// card on file the overage bills. This guard reads the month's bandwidth of the whole workspace, the same way as
// Replay's scripts/budget-check.mjs:
// - Pause: at PAUSE_AT (70 %) it suspends the Plumes API service (RENDER_SERVICE_ID, else the service named
//   plumes-java) and opens an issue. The site keeps working: the edge (web/functions/api) treats Render's 503 page as
//   a sleeping origin and answers from its cache, or from the published data files for the list and per-volcano
//   routes, and the static site works without the API.
// - Resume, with hysteresis: only while that issue is open, once it has been open for HOLD_H (24) hours and the
//   bandwidth is under RESUME_AT (50 %), which in practice means after the monthly reset. It resumes the service and
//   closes the issue. Between 50 % and 70 % nothing changes, so it cannot flap.
// - A service suspended by hand (no open guard issue) is never resumed. An open guard issue whose service was resumed
//   by hand is closed; if usage is still over PAUSE_AT, the service is paused again (raise the PAUSE_AT repository
//   variable, or disable the workflow, to keep it running).
//
// Env: RENDER_API_KEY (required for anything to happen), RENDER_SERVICE_ID, GITHUB_TOKEN + GITHUB_REPOSITORY,
// PAUSE_AT, RESUME_AT, HOLD_H. Flag: --dry-run plans the actions without suspending, resuming or writing issues.
// Exit: 0, or 1 when Render could not be read (a red run, so a guard that cannot see is noticed).

const RENDER = "https://api.render.com/v1";
const GITHUB = "https://api.github.com";
export const TITLE = "Render bandwidth guard: Plumes API paused";
const LIMIT_GB = 5;

/** The guard's decision (pure). `share` the month's workspace bandwidth / 5 GB; `issue` the open guard issue. */
export function decide({ share, suspended, issue, now, pauseAt = 0.7, resumeAt = 0.5, holdHours = 24 }) {
  const d = { suspend: false, resume: false, closeIssue: false, openIssue: false, waiting: undefined };
  if (issue && !suspended) d.closeIssue = true; // resumed by hand
  if (!suspended && share >= pauseAt) return { ...d, suspend: true, openIssue: true };
  if (!suspended || !issue) return d;
  if (share >= resumeAt) d.waiting = `bandwidth still at or over ${resumeAt * 100} %`;
  else if (now - new Date(issue.createdAt) < holdHours * 3_600_000) d.waiting = `paused for less than ${holdHours} h`;
  else return { ...d, resume: true, closeIssue: true };
  return d;
}

export async function run({ env = process.env, now = new Date(), fetchImpl = fetch, dryRun = false, log = console.log } = {}) {
  const PAUSE_AT = Number(env.PAUSE_AT || 0.7);
  const RESUME_AT = Number(env.RESUME_AT || 0.5);
  const HOLD_H = Number(env.HOLD_H || 24);
  if (!env.RENDER_API_KEY) {
    log("Render bandwidth guard: not checked (RENDER_API_KEY not set).");
    return { ok: true, actions: [] };
  }
  async function call(url, init = {}) {
    const res = await fetchImpl(url, init);
    if (!res.ok) throw new Error(`${res.status} ${init.method ?? "GET"} ${url.split("?")[0]}`);
    const text = await res.text();
    return text ? JSON.parse(text) : {};
  }
  const write = (url, init) => (dryRun ? Promise.resolve({}) : call(url, init));
  const h = { Authorization: `Bearer ${env.RENDER_API_KEY}`, Accept: "application/json" };
  const start = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 1));

  let services;
  let gb = 0;
  try {
    services = (await call(`${RENDER}/services?limit=100`, { headers: h })).map((s) => s.service);
    const q = `startTime=${start.toISOString()}&endTime=${now.toISOString()}&resolutionSeconds=86400`;
    for (const s of services) {
      const bw = await call(`${RENDER}/metrics/bandwidth?resource=${s.id}&${q}`, { headers: h });
      gb += bw.flatMap((series) => series.values).reduce((sum, v) => sum + v.value, 0) / 1000;
    }
  } catch (e) {
    log(`::warning title=bandwidth guard::Render not read (${e.message}); nothing changed.`);
    return { ok: false, actions: [] };
  }
  const service = services.find((s) => (env.RENDER_SERVICE_ID ? s.id === env.RENDER_SERVICE_ID : s.name === "plumes-java"));
  if (!service) {
    log(`::warning title=bandwidth guard::the Plumes API service (${env.RENDER_SERVICE_ID || "plumes-java"}) is not in this Render workspace; nothing changed.`);
    return { ok: false, actions: [] };
  }
  const suspended = service.suspended === "suspended";

  const gh = env.GITHUB_TOKEN && env.GITHUB_REPOSITORY
    ? { headers: { Authorization: `Bearer ${env.GITHUB_TOKEN}`, Accept: "application/vnd.github+json" }, repo: `${GITHUB}/repos/${env.GITHUB_REPOSITORY}` }
    : undefined;
  let issue;
  if (gh) {
    const open = await call(`${gh.repo}/issues?state=open&per_page=100`, { headers: gh.headers });
    const i = open.find((x) => !x.pull_request && x.title.startsWith(TITLE));
    if (i) issue = { number: i.number, createdAt: i.created_at };
  }

  const share = gb / LIMIT_GB;
  const d = decide({ share, suspended, issue, now, pauseAt: PAUSE_AT, resumeAt: RESUME_AT, holdHours: HOLD_H });
  const usage = `${gb.toFixed(2)} GB of ${LIMIT_GB} GB (${(share * 100).toFixed(1)} %)`;
  const actions = [];
  const comment = (n, body) => write(`${gh.repo}/issues/${n}/comments`, { method: "POST", headers: gh.headers, body: JSON.stringify({ body }) });
  const close = (n) => write(`${gh.repo}/issues/${n}`, { method: "PATCH", headers: gh.headers, body: JSON.stringify({ state: "closed" }) });

  if (d.resume) {
    actions.push(`resume ${service.name}: bandwidth ${usage}, under ${RESUME_AT * 100} % (issue #${issue.number})`);
    await write(`${RENDER}/services/${service.id}/resume`, { method: "POST", headers: h });
  }
  if (d.closeIssue && gh) {
    if (!d.resume) actions.push(`close issue #${issue.number}: ${service.name} was resumed by hand`);
    await comment(issue.number, d.resume
      ? `Workspace bandwidth is ${usage}, under ${RESUME_AT * 100} %, so the guard resumed **${service.name}**.`
      : `**${service.name}** is running again (resumed by hand), so this issue is closed.`);
    await close(issue.number);
  }
  if (d.suspend) {
    actions.push(`suspend ${service.name}: bandwidth ${usage}, at or over ${PAUSE_AT * 100} %`);
    await write(`${RENDER}/services/${service.id}/suspend`, { method: "POST", headers: h });
    if (gh) {
      const body = [
        `The Render bandwidth guard (\`.github/workflows/budget.yml\`) suspended **${service.name}**: this month's outbound`,
        `bandwidth of the Render workspace (shared with Replay) reached ${usage}; the guard pauses at ${PAUSE_AT * 100} % so the`,
        "free 5 GB is never exceeded (an overage would bill the card on file).",
        "",
        "Meanwhile the edge answers from its cache, or from the published data files for the volcano list and each",
        "volcano, and other API routes get 503 `backend-waking`. The static site works without the API.",
        "",
        `**It resumes by itself** once the bandwidth is under ${RESUME_AT * 100} % and this issue has been open for ${HOLD_H} h,`,
        "normally after the monthly reset, and then closes this issue. Closing this issue by hand keeps the service",
        "suspended until it is resumed by hand (Render dashboard → plumes-java → Resume).",
      ].join("\n");
      await write(`${gh.repo}/issues`, { method: "POST", headers: gh.headers, body: JSON.stringify({ title: `${TITLE} (${now.toISOString().slice(0, 10)})`, body }) });
    }
  }

  const state = suspended && !d.resume ? (issue ? `suspended by this guard (issue #${issue.number})` : "suspended by hand (never resumed by the guard)") : "running";
  log([
    `## Render bandwidth guard, ${now.toISOString().slice(0, 10)}`,
    "",
    `- Workspace outbound bandwidth this month: ${usage}`,
    `- ${service.name}: ${state}${d.waiting ? `; waiting to resume: ${d.waiting}` : ""}`,
    ...(actions.length ? [`- Actions${dryRun ? " (dry run, nothing changed)" : ""}:`, ...actions.map((a) => `  - ${a}`)] : ["- Actions: none"]),
    `- Pause at ${PAUSE_AT * 100} %; resume under ${RESUME_AT * 100} % after ${HOLD_H} h.`,
  ].join("\n"));
  return { ok: true, actions };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const { ok } = await run({ dryRun: process.argv.includes("--dry-run") });
  process.exit(ok ? 0 : 1);
}
