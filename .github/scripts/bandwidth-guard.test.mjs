// node --test .github/scripts/bandwidth-guard.test.mjs: the Render bandwidth guard against mocked Render and GitHub
// APIs (nothing real is called, suspended or written).
import assert from "node:assert/strict";
import { test } from "node:test";

import { run } from "./bandwidth-guard.mjs";

const NOW = new Date("2026-10-22T09:47:00Z");
const ISSUES = "https://api.github.com/repos/o/r/issues";
const SRV = "https://api.render.com/v1/services/srv-plumes";
const env = { RENDER_API_KEY: "test", RENDER_SERVICE_ID: "srv-plumes", GITHUB_TOKEN: "test", GITHUB_REPOSITORY: "o/r" };
const quiet = () => {};
const guardIssue = (createdAt = "2026-10-01T09:47:00Z") => ({ number: 5, title: "Render bandwidth guard: Plumes API paused (2026-10-01)", created_at: createdAt });

/** Workspace bandwidth `gb`, split over Replay's and Plumes' services; Plumes `suspended`; open `issues`. */
function mock({ gb = 0, suspended = false, issues = [], renderStatus = 200 }) {
  const calls = [];
  const fetchImpl = async (url, init = {}) => {
    calls.push(`${init.method ?? "GET"} ${url.split("?")[0]}`);
    if (url.startsWith("https://api.render.com") && renderStatus !== 200) return new Response("", { status: renderStatus });
    let body = {};
    if (url.includes("/v1/services?")) {
      body = [
        { service: { id: "srv-java", name: "typhoon-replay-java", suspended: "not_suspended" } },
        { service: { id: "srv-plumes", name: "plumes-java", suspended: suspended ? "suspended" : "not_suspended" } },
      ];
    } else if (url.includes("/metrics/bandwidth")) body = [{ values: [{ timestamp: "2026-10-02T00:00:00Z", value: (gb * 1000) / 2 }] }];
    else if (url.includes("/issues?")) body = issues;
    return new Response(JSON.stringify(body), { status: 200 });
  };
  return { calls, fetchImpl };
}
const writes = (calls) => calls.filter((c) => !c.startsWith("GET"));
const go = (m, o = {}) => run({ env, now: NOW, fetchImpl: m.fetchImpl, log: quiet, ...o });

test("normal state: under 70 % and running, nothing is written", async () => {
  for (const gb of [0, 0.4, 3.4]) {
    const m = mock({ gb });
    const r = await go(m);
    assert.deepEqual(writes(m.calls), []);
    assert.equal(r.ok, true);
  }
});

test("at 70 % of the workspace's 5 GB: suspends the Plumes API (never another service) and opens the issue", async () => {
  const m = mock({ gb: 3.5 });
  const r = await go(m);
  assert.deepEqual(writes(m.calls), [`POST ${SRV}/suspend`, `POST ${ISSUES}`]);
  assert.match(r.actions[0], /^suspend plumes-java: bandwidth 3\.50 GB of 5 GB \(70\.0 %\)/);
});

test("dry run plans the suspension without writing anything", async () => {
  const m = mock({ gb: 4.2 });
  const r = await go(m, { dryRun: true });
  assert.deepEqual(writes(m.calls), []);
  assert.match(r.actions[0], /^suspend plumes-java/);
});

test("after the monthly reset: under 50 % and paused 24 h resumes the service and closes the issue", async () => {
  const m = mock({ gb: 0.01, suspended: true, issues: [guardIssue()] });
  const r = await go(m, { now: new Date("2026-11-01T01:47:00Z") });
  assert.deepEqual(writes(m.calls), [`POST ${SRV}/resume`, `POST ${ISSUES}/5/comments`, `PATCH ${ISSUES}/5`]);
  assert.match(r.actions[0], /^resume plumes-java/);
});

test("hysteresis: between 50 % and 70 %, or paused under 24 h, it stays paused", async () => {
  for (const [gb, created] of [[3.0, undefined], [2.5, undefined], [0.1, "2026-10-22T01:47:00Z"]]) {
    const m = mock({ gb, suspended: true, issues: [guardIssue(created)] });
    const r = await go(m);
    assert.deepEqual(writes(m.calls), []);
    assert.deepEqual(r.actions, []);
  }
});

test("a service suspended by hand (no guard issue) is never resumed", async () => {
  const m = mock({ gb: 0, suspended: true });
  await go(m);
  assert.deepEqual(writes(m.calls), []);
});

test("resumed by hand: the issue is closed; still over 70 %, it is paused again with a new issue", async () => {
  const low = mock({ gb: 1, issues: [guardIssue()] });
  await go(low);
  assert.deepEqual(writes(low.calls), [`POST ${ISSUES}/5/comments`, `PATCH ${ISSUES}/5`]);
  const high = mock({ gb: 4, issues: [guardIssue()] });
  await go(high);
  assert.deepEqual(writes(high.calls), [`POST ${ISSUES}/5/comments`, `PATCH ${ISSUES}/5`, `POST ${SRV}/suspend`, `POST ${ISSUES}`]);
});

test("Render unreadable or the service missing: nothing changes and the run fails", async () => {
  const m = mock({ gb: 4.9, renderStatus: 500 });
  assert.equal((await go(m)).ok, false);
  assert.deepEqual(writes(m.calls), []);
  const other = mock({ gb: 4.9 });
  assert.equal((await go(other, { env: { ...env, RENDER_SERVICE_ID: "srv-gone" } })).ok, false);
  assert.deepEqual(writes(other.calls), []);
});

test("without RENDER_API_KEY nothing is called", async () => {
  const m = mock({ gb: 4.9 });
  assert.equal((await go(m, { env: {} })).ok, true);
  assert.deepEqual(m.calls, []);
});

test("full cycle: 72 % pauses, 60 % holds, the monthly reset resumes, then 72 % pauses again", async () => {
  let suspended = false;
  let issues = [];
  const step = async (gb, now) => {
    const m = mock({ gb, suspended, issues });
    await go(m, { now: new Date(now) });
    for (const c of writes(m.calls)) {
      if (c === `POST ${SRV}/suspend`) suspended = true;
      if (c === `POST ${SRV}/resume`) suspended = false;
      if (c === `POST ${ISSUES}`) issues = [guardIssue(now)];
      if (c === `PATCH ${ISSUES}/5`) issues = [];
    }
    return suspended;
  };
  assert.equal(await step(3.6, "2026-10-20T01:47:00Z"), true);
  assert.equal(await step(3.0, "2026-10-25T01:47:00Z"), true);
  assert.equal(await step(0.1, "2026-11-01T01:47:00Z"), false);
  assert.equal(await step(0.2, "2026-11-01T09:47:00Z"), false);
  assert.equal(await step(3.6, "2026-11-20T01:47:00Z"), true);
});
