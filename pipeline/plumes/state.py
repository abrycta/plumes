"""Pipeline state between CI runs: the previous data version, the Earth Engine ledger and the crawl records.

    GH_TOKEN=… uv run python -m plumes.state restore     # latest archive bundle per source -> data/; ledger + pointer from Pages
    uv run python -m plumes.state next-version           # 1 + the published version (1 if none)
    uv run python -m plumes.state built-version          # the version data/build/site/latest.json points to
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

import httpx
import zstandard

from plumes.adopt import BUNDLES, REPO
from plumes.ee_ledger import merge_into
from plumes.paths import BUILD, DATA, EE_LEDGER

PAGES = "https://krtmtthw.dev/plumes/data/"


def published() -> dict | None:
    r = httpx.get(PAGES + "latest.json", follow_redirects=True, timeout=30)
    return r.json() if r.status_code == 200 else None


def restore() -> dict:
    out = {}
    tags = subprocess.run(["gh", "release", "list", "-R", REPO, "-L", "1000", "--json", "tagName,isDraft", "-q", ".[] | select(.isDraft | not) | .tagName"],
                          capture_output=True, text=True, check=True).stdout.split()
    for sid in BUNDLES:
        mine = sorted(t for t in tags if t.startswith(sid + "-20"))
        if not mine:
            continue
        with tempfile.TemporaryDirectory() as td:
            subprocess.run(["gh", "release", "download", mine[-1], "-R", REPO, "-p", f"{sid}.tar.zst", "-D", td], check=True)
            raw = zstandard.ZstdDecompressor().stream_reader(open(Path(td) / f"{sid}.tar.zst", "rb")).read()
            with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
                tar.extractall(DATA, filter="data")
        out[sid] = mine[-1]
    r = httpx.get(PAGES + "ee-usage.json", follow_redirects=True, timeout=30)
    if r.status_code == 200:
        # merge, never overwrite: runs logged here but not yet published stay counted
        out["ee-usage"] = f"merged ({len(merge_into(EE_LEDGER, r.json())['runs'])} runs)"
    return out


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "restore":
        print(json.dumps(restore(), indent=1))
    elif cmd == "next-version":
        p = published()
        print(int(p["current"][1:]) + 1 if p else 1)
    elif cmd == "built-version":
        print(json.loads((BUILD / "site" / "latest.json").read_text())["current"][1:])
