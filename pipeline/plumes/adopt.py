"""Adopt crawled bundles and query results into the private archive as GitHub Releases (DATA-ARCHIVING §3, DECISIONS Q13).

The kit's snapshot job fetches `file` sources itself; the crawled pages and query-in-place results are produced by this
pipeline, so they are bundled here: one release per registry id, tag `<id>-<YYYY-MM-DD>` (`.2`, `.3` on the same day),
assets = `<id>.tar.zst` (level 19), `SHA256SUMS`, `manifest.json`; created as a draft, published after the upload.
Kept in the kit's tag and asset layout; a `collection` kind in the kit itself is the Q13 follow-up.

    GH_TOKEN=… uv run python -m plumes.adopt [ids…] [--dry-run]
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import hashlib
import io
import json
import subprocess
import tarfile
import tempfile
from pathlib import Path

import yaml
import zstandard

from plumes.paths import BUILD, DATA, RAW, REGISTRY, TABLES

REPO = "abrycta/plumes-archive"
BUNDLES = {
    "phivolcs-bulletins": [RAW / "phivolcs-bulletins" / "pages.jsonl", RAW / "phivolcs-bulletins" / "list.tsv"],
    "phivolcs-lava-bulletins": [RAW / "phivolcs-lava-bulletins" / "index.jsonl", RAW / "phivolcs-lava-bulletins" / "pages.jsonl"],
    "vaac-tokyo-advisories": [RAW / "vaac-tokyo-advisories" / "lists.jsonl", RAW / "vaac-tokyo-advisories" / "pages.jsonl"],
    "dswd-dromic-reports": [RAW / "dswd-dromic-reports" / "taal-2020.jsonl"],
    "nasa-msvolso2l4": sorted(Path(p) for p in glob.glob(str(RAW / "nasa-msvolso2l4" / "*"))),
    "cod-ab-phl-gdb": [RAW / "cod-ab" / "phl_admin3.csv"],
    "firms-modis": sorted(Path(p) for d in ("MODIS_SP", "VIIRS_SNPP_SP") for p in glob.glob(str(RAW / "firms" / d / "*"))),
    "firms-viirs-noaa20": sorted(Path(p) for p in glob.glob(str(RAW / "firms" / "VIIRS_NOAA20_*" / "*"))),
    "s5p-offl-so2": sorted(Path(p) for p in glob.glob(str(TABLES / "ee-so2" / "*.csv")) + glob.glob(str(TABLES / "ee-so2-monthly" / "*.tif"))),
    "gpm-imerg-v07": sorted(Path(p) for p in glob.glob(str(TABLES / "ee-rain" / "*.csv"))),
    "modis-mod14a1": sorted(Path(p) for g in ("*.csv", "*.coverage.json") for p in glob.glob(str(TABLES / "ee-fire" / g))),
    "worldpop-100m": [TABLES / "ee-exposure.csv"],
    "s2-sr-harmonized": sorted(Path(p) for p in glob.glob(str(BUILD / "assets" / "*")) + glob.glob(str(TABLES / "ee-lakes2" / "*.csv"))),
    "landsat-surface-temperature": sorted(Path(p) for p in glob.glob(str(TABLES / "ee-laketemp" / "*.csv"))),
    "jrc-global-surface-water": sorted(Path(p) for p in glob.glob(str(TABLES / "ee-lakegsw" / "*.csv"))),
    "s5p-offl-aer-ai": sorted(Path(p) for p in glob.glob(str(TABLES / "ee-uvai" / "*.csv"))),
    "era5-pressure-levels": sorted(Path(p) for p in glob.glob(str(TABLES / "era5-*.json"))),
    "comet-licsbas": sorted(Path(p) for p in glob.glob(str(RAW / "comet-licsbas" / "*"))),
}
NOTES = {
    "comet-licsbas": "COMET Volcano Portal LiCSBAS JSON (GACOS-corrected) per volcano and frame, the frame list and the fetch log.",
    "modis-mod14a1": "Earth Engine reductions per volcano ring and day for MOD14A1, VNP14A1 and the FIRMS collection (query results).",
    "firms-modis": "NASA FIRMS area API results (MODIS_SP, VIIRS_SNPP_SP) over the Philippine box, 5-day windows.",
    "s2-sr-harmonized": "Sentinel-2 thumbnails rendered by Earth Engine for the Taal 2020 story, and the run A crater-lake water and colour table per scene.",
    "landsat-surface-temperature": "Earth Engine run A: Landsat C2 L2 crater-lake surface temperature per lake and scene (query results).",
    "jrc-global-surface-water": "Earth Engine run A: JRC GSW monthly crater-lake water area per lake (query results).",
    "s5p-offl-aer-ai": "Earth Engine run A: TROPOMI UV aerosol index per volcano ring and day in eruption windows (query results).",
    "firms-viirs-noaa20": "NASA FIRMS area API results (VIIRS_NOAA20_SP 5-day windows; VIIRS_NOAA20_NRT recent days) over the Philippine box.",
    "s5p-offl-so2": "Earth Engine reductions of TROPOMI SO2 per volcano ring and day, and national monthly mean grids (query results).",
    "gpm-imerg-v07": "Earth Engine reductions of GPM IMERG V07 Final rain per volcano ring and UTC day (query results).",
}


def gh(*args, check=True) -> subprocess.CompletedProcess:
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=check)


def next_tag(sid: str, date: str) -> str:
    existing = set(gh("release", "list", "-R", REPO, "-L", "1000", "--json", "tagName", "-q", ".[].tagName").stdout.split())
    tag, k = f"{sid}-{date}", 1
    while tag in existing:
        k += 1
        tag = f"{sid}-{date}.{k}"
    return tag


def bundle(sid: str, files: list[Path]) -> tuple[bytes, dict]:
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w") as tar:
        for f in files:
            tar.add(f, arcname=str(f.relative_to(DATA)))
    raw_b = raw.getvalue()
    comp = zstandard.ZstdCompressor(level=19 if len(raw_b) < 150e6 else 15).compress(raw_b)
    return comp, {"raw_bytes": len(raw_b), "raw_sha256": hashlib.sha256(raw_b).hexdigest(), "compressed_bytes": len(comp),
                  "compressed_sha256": hashlib.sha256(comp).hexdigest(),
                  "members": [{"path": str(f.relative_to(DATA)), "bytes": f.stat().st_size, "sha256": hashlib.sha256(f.read_bytes()).hexdigest()} for f in files]}


def latest_manifest(sid: str) -> dict | None:
    tags = [t for t in gh("release", "list", "-R", REPO, "-L", "1000", "--json", "tagName,isDraft", "-q",
                          '.[] | select(.isDraft | not) | .tagName').stdout.split() if t.startswith(sid + "-20")]
    if not tags:
        return None
    r = gh("release", "download", sorted(tags)[-1], "-R", REPO, "-p", "manifest.json", "-O", "-", check=False)
    return json.loads(r.stdout) if r.returncode == 0 else None


def adopt(ids: list[str], dry_run: bool = False, changed_only: bool = False) -> list[dict]:
    reg = {e["id"]: e for e in yaml.safe_load(REGISTRY.read_text())["sources"]}
    date = dt.date.today().isoformat()
    out = []
    for sid in ids:
        files = [f for f in BUNDLES[sid] if f.exists() and f.stat().st_size > 0]
        if not files:
            out.append({"id": sid, "action": "skip", "reason": "nothing to adopt"})
            continue
        comp, meta = bundle(sid, files)
        if changed_only:
            prev = latest_manifest(sid)
            if prev and {m["path"]: m["sha256"] for m in prev.get("members", [])} == {m["path"]: m["sha256"] for m in meta["members"]}:
                out.append({"id": sid, "action": "skip", "reason": "unchanged"})
                continue
        e = reg[sid]
        manifest = {"manifest_version": 2, "source_id": sid, "adopted_by": "plumes.adopt", "snapshot_date": date,
                    "created": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"), "licence": " ".join(e["licence"].split()),
                    "attribution": " ".join(e["attribution"].split()), "note": NOTES.get(sid, "Crawled or queried by the Plumes pipeline."), **meta}
        if dry_run:
            out.append({"id": sid, "action": "would-release", "compressed_bytes": meta["compressed_bytes"], "files": len(files)})
            continue
        tag = next_tag(sid, date)
        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            (t / f"{sid}.tar.zst").write_bytes(comp)
            (t / "manifest.json").write_text(json.dumps(manifest, indent=1))
            sums = "".join(f"{hashlib.sha256((t / n).read_bytes()).hexdigest()}  {n}\n" for n in (f"{sid}.tar.zst", "manifest.json"))
            (t / "SHA256SUMS").write_text(sums)
            gh("release", "create", tag, "-R", REPO, "--draft", "--title", tag, "--notes", f"{sid}: {manifest['note']} Adopted {date}.",
               str(t / f"{sid}.tar.zst"), str(t / "manifest.json"), str(t / "SHA256SUMS"))
            gh("release", "edit", tag, "-R", REPO, "--draft=false")
        out.append({"id": sid, "action": "released", "tag": tag, "compressed_bytes": meta["compressed_bytes"]})
        print(out[-1], flush=True)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--changed-only", action="store_true")
    a = ap.parse_args()
    print(json.dumps(adopt(a.ids or list(BUNDLES), a.dry_run, a.changed_only), indent=1))
