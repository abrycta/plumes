"""Pipeline state between CI runs: the previous data version, the Earth Engine ledger and the crawl records.

    GH_TOKEN=… uv run python -m plumes.state restore     # newest good archive bundle per source -> data/; EE ledger from gh-pages
    uv run python -m plumes.state next-version           # 1 + the newest version on gh-pages (1 if none)
    uv run python -m plumes.state built-version          # the version data/build/site/latest.json points to
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

import httpx
import zstandard

from plumes import health
from plumes.adopt import BUNDLES, REPO
from plumes.archive_tags import TAG, key, list_tags, newest
from plumes.ee_ledger import merge_into
from plumes.paths import BUILD, DATA, EE_LEDGER
from plumes.publish import checkout, current, held, read_json

PAGES = "https://krtmtthw.dev/plumes/data/"


def published() -> dict | None:
    """The live latest.json, or None when it can't be read as one (any status but 200, a network error, another body).
    Informational only: the run itself reads the gh-pages branch (audit A2)."""
    try:
        r = httpx.get(PAGES + "latest.json", follow_redirects=True, timeout=30)
        p = r.json() if r.status_code == 200 else None
    except (httpx.HTTPError, ValueError):
        return None
    return p if isinstance(p, dict) and re.fullmatch(r"v\d+", str(p.get("current"))) else None


def next_version() -> int:
    """1 + the newest version on the gh-pages branch (1 if the branch doesn't exist). Exits non-zero when the branch
    holds versions but its latest.json can't be read: numbering blind could replace the live versions (audit P3). The
    branch, not krtmtthw.dev, is the source, so a site outage doesn't stop a run (audit A2)."""
    root = checkout()
    vs = held(root)
    cur = current(root)
    if vs and cur is None:
        sys.exit(f"::error title=latest.json unreadable::data/latest.json on gh-pages is not readable while it holds v{max(vs)}; "
                 "no version is numbered or built")
    return max([cur or 0, *vs]) + 1


def _members_ok(path: Path, man: dict) -> str | None:
    """Why a downloaded bundle doesn't match its release manifest (sha256 of the archive and of each member), or None."""
    blob = path.read_bytes()
    if man.get("compressed_sha256") and hashlib.sha256(blob).hexdigest() != man["compressed_sha256"]:
        return "the .tar.zst does not match manifest.json"
    try:
        raw = zstandard.ZstdDecompressor().stream_reader(io.BytesIO(blob)).read()
    except zstandard.ZstdError as e:
        return f"corrupt zstd: {e}"
    if man.get("raw_sha256") and hashlib.sha256(raw).hexdigest() != man["raw_sha256"]:
        return "the tar does not match manifest.json"
    try:
        with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
            got = {m.name: hashlib.sha256(tar.extractfile(m).read()).hexdigest() for m in tar.getmembers() if m.isfile()}
    except tarfile.TarError as e:
        return f"corrupt tar: {e}"
    want = {m["path"]: m["sha256"] for m in man.get("members", [])}
    if want and got != want:
        return f"members differ from manifest.json: {sorted(set(want) ^ set(got) or [k for k in want if want[k] != got.get(k)])[:5]}"
    return None


def restore_bundle(sid: str, tags: list[str], dest: Path = DATA, tries: int = 5) -> str:
    """Extract the newest good release of bundle `sid`: tags newest-first, each checked against its manifest.json, so
    one corrupt or half-uploaded adoption never blocks every later run (audit A4). Exits when no recent tag is good."""
    mine = sorted((t for t in tags if (m := TAG.match(t)) and m["id"] == sid), key=key, reverse=True)[:tries]
    why = {}
    for tag in mine:
        with tempfile.TemporaryDirectory() as td:
            r = subprocess.run(["gh", "release", "download", tag, "-R", REPO, "-p", f"{sid}.tar.zst", "-p", "manifest.json", "-D", td],
                               capture_output=True, text=True)
            asset, man_p = Path(td) / f"{sid}.tar.zst", Path(td) / "manifest.json"
            if r.returncode != 0 or not asset.exists() or not man_p.exists():
                why[tag] = f"download failed: {(r.stderr or 'missing asset').strip()[:160]}"
                continue
            try:
                man = json.loads(man_p.read_text())
            except ValueError:
                why[tag] = "manifest.json is not JSON"
                continue
            if bad := _members_ok(asset, man):
                why[tag] = bad
                continue
            raw = zstandard.ZstdDecompressor().stream_reader(open(asset, "rb")).read()
            with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
                tar.extractall(dest, filter="data")
        if why:
            health.report(f"restore {sid}", "older tag used", f"Restore of `{sid}` skipped newer release(s) and used `{tag}`:\n\n"
                          + "\n".join(f"- `{t}`: {w}" for t, w in why.items()))
        else:
            health.resolve(f"restore {sid}", f"`{tag}` restored cleanly.")
        return tag
    health.report(f"restore {sid}", "no good tag", f"No good release of `{sid}` among {mine}: {why}")
    sys.exit(f"::error title=archive bundle unreadable::{sid}: no good release among the newest {len(mine)}: {why}")


def restore() -> dict:
    out = {}
    tags = list_tags(REPO)
    missing = [sid for sid in BUNDLES if newest(tags, sid) is None]
    if missing:  # every bundle has been adopted at least once: a missing one means the listing or the archive is wrong
        sys.exit(f"::error title=archive bundles missing::no release found for {missing} in {REPO}; nothing is built from partial inputs")
    for sid in BUNDLES:
        out[sid] = restore_bundle(sid, tags)
    out["ee-usage"] = restore_ledger()
    return out


def restore_ledger() -> str:
    """Merge the published Earth Engine ledger (gh-pages data/ee-usage.json) into the local one. When versions exist but
    the ledger can't be read, the month's usage is unknown: Earth Engine is switched off for this run (fail closed,
    audit A2) through the step output `ee_ledger=missing`."""
    root = checkout()
    led = read_json(root, "ee-usage.json")
    if isinstance(led, dict) and isinstance(led.get("runs"), list):
        # merge, never overwrite: runs logged here but not yet published stay counted
        _output("ee_ledger", "ok")
        return f"merged ({len(merge_into(EE_LEDGER, led)['runs'])} runs)"
    if not held(root):
        _output("ee_ledger", "ok")
        return "none published yet"
    print("::warning title=Earth Engine ledger unreadable::data/ee-usage.json on gh-pages is missing or not a ledger; "
          "Earth Engine steps are skipped this run so the monthly cap can't be overrun", flush=True)
    _output("ee_ledger", "missing")
    return "unreadable: Earth Engine off"


def _output(k: str, v: str) -> None:
    if p := os.environ.get("GITHUB_OUTPUT"):
        with open(p, "a") as f:
            f.write(f"{k}={v}\n")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "restore":
        print(json.dumps(restore(), indent=1))
    elif cmd == "next-version":
        print(next_version())
    elif cmd == "built-version":
        print(json.loads((BUILD / "site" / "latest.json").read_text())["current"][1:])
