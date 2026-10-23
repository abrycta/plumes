"""Storage of the published versions, measured every Data run (storage options §3 step 4, decision S2): the Hugging
Face mirror's counted storage (`usedStorage`) and the size of the abrycta/plumes repository (gh-pages history
included). Above a trigger, a ::warning and the `storage <name>` health issue: the cue to turn on C's pruning and
squash, or D. Internal only; reading a number that fails never fails the run.

    uv run python -m plumes.storage
"""

from __future__ import annotations

import json
import os
import subprocess

import httpx

from plumes import health
from plumes.publish import HF_REPO

PAGES_REPO = "abrycta/plumes"
HF_LIMIT = 2_000_000_000  # bytes counted by HF (usedStorage)
REPO_LIMIT = 500_000_000  # bytes (the GitHub API reports KiB)


def hf_used() -> int:
    r = httpx.get(f"https://huggingface.co/api/datasets/{HF_REPO}", params={"expand[]": "usedStorage"}, timeout=30)
    r.raise_for_status()
    return int(r.json()["usedStorage"])


def repo_size() -> int:
    out = subprocess.run(["gh", "api", f"repos/{PAGES_REPO}", "-q", ".size"], capture_output=True, text=True, check=True).stdout
    return int(out) * 1024


def assess(name: str, measure, limit: int) -> dict:
    try:
        n = measure()
    except Exception as e:  # a failed reading warns, never fails the run
        print(f"::warning title=storage {name}::not measured: {type(e).__name__}: {str(e)[:160]}", flush=True)
        return {"name": name, "bytes": None, "limit": limit}
    over = n > limit
    if over:
        health.report(f"storage {name}", "over trigger",
                      f"`{name}` holds {n / 1e6:,.0f} MB, above the {limit / 1e6:,.0f} MB trigger: time to turn on pruning and squash "
                      "(docs/architecture/STORAGE-OPTIONS.md §3 step 4).")
    else:
        health.resolve(f"storage {name}", f"`{name}` is back under the trigger: {n / 1e6:,.0f} MB.")
    return {"name": name, "bytes": n, "limit": limit, "over": over}


def main() -> list[dict]:
    res = [assess("hf-mirror", hf_used, HF_LIMIT), assess("pages-repo", repo_size, REPO_LIMIT)]
    for r in res:
        if r["bytes"] is not None:
            print(f"::notice title=storage {r['name']}::{r['bytes'] / 1e6:,.1f} MB of {r['limit'] / 1e6:,.0f} MB trigger", flush=True)
    if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(summary, "a") as f:
            f.write("### Storage\n\n| store | MB | trigger MB |\n|---|---:|---:|\n")
            for r in res:
                mb = "n/a" if r["bytes"] is None else f"{r['bytes'] / 1e6:,.1f}"
                f.write(f"| {r['name']} | {mb} | {r['limit'] / 1e6:,.0f} |\n")
    return res


if __name__ == "__main__":
    print(json.dumps(main()))
