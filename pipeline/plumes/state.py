"""Pipeline state between CI runs: the previous data version, the Earth Engine ledger and the crawl records.

    GH_TOKEN=… uv run python -m plumes.state restore     # latest archive bundle per source -> data/; ledger + pointer from Pages
    uv run python -m plumes.state next-version           # 1 + the newest version on gh-pages (1 if none)
    uv run python -m plumes.state built-version          # the version data/build/site/latest.json points to
"""

from __future__ import annotations

import io
import json
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

import httpx
import zstandard

from plumes.adopt import BUNDLES, REPO
from plumes.archive_tags import list_tags, newest
from plumes.ee_ledger import merge_into
from plumes.paths import BUILD, DATA, EE_LEDGER
from plumes.publish import origin, remote_versions

PAGES = "https://krtmtthw.dev/plumes/data/"


def published() -> dict | None:
    """The live latest.json, or None when it can't be read as one (any status but 200, a network error, another body)."""
    try:
        r = httpx.get(PAGES + "latest.json", follow_redirects=True, timeout=30)
        p = r.json() if r.status_code == 200 else None
    except (httpx.HTTPError, ValueError):
        return None
    return p if isinstance(p, dict) and re.fullmatch(r"v\d+", str(p.get("current"))) else None


def next_version() -> int:
    """1 + the newest version on the gh-pages branch (or in the live latest.json, if newer). Exits non-zero when the
    branch holds versions but latest.json can't be read (a Pages outage or misconfiguration): numbering from 1 then
    would replace the live versions and leave no rollback (audit P3)."""
    held = remote_versions(origin())
    p = published()
    if held and p is None:
        sys.exit(f"::error title=latest.json unreadable::{PAGES}latest.json is not readable while gh-pages holds v{max(held)}; "
                 "no version is numbered or built")
    return max([int(p["current"][1:]) if p else 0, *held]) + 1


def restore() -> dict:
    out = {}
    tags = list_tags(REPO)
    missing = [sid for sid in BUNDLES if newest(tags, sid) is None]
    if missing:  # every bundle has been adopted at least once: a missing one means the listing or the archive is wrong
        sys.exit(f"::error title=archive bundles missing::no release found for {missing} in {REPO}; nothing is built from partial inputs")
    for sid in BUNDLES:
        tag = newest(tags, sid)
        with tempfile.TemporaryDirectory() as td:
            subprocess.run(["gh", "release", "download", tag, "-R", REPO, "-p", f"{sid}.tar.zst", "-D", td], check=True)
            raw = zstandard.ZstdDecompressor().stream_reader(open(Path(td) / f"{sid}.tar.zst", "rb")).read()
            with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
                tar.extractall(DATA, filter="data")
        out[sid] = tag
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
        print(next_version())
    elif cmd == "built-version":
        print(json.loads((BUILD / "site" / "latest.json").read_text())["current"][1:])
