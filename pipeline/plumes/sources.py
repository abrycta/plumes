"""archivekit hooks (named in sources.yaml) and the fetch step for the file sources.

A hook gets the downloaded file and its registry entry and returns a list of problems; any problem rejects the file
and archivekit moves on to the next link (DATA-ARCHIVING §2).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from plumes.paths import CROSSWALK, PIPELINE, REGISTRY

FILE_SOURCES = ["gvp-volcanoes-ph", "gvp-eruptions-ph", "usgs-comcat-ph-1900-2009", "usgs-comcat-ph-2010", "noaa-hazel-volcanoes-ph"]


def _rows(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def check_gvp_volcanoes(path: Path, source: dict[str, Any]) -> list[str]:
    want = {int(r["gvp_number"]) for r in _rows(CROSSWALK) if r["gvp_number"]}
    got = {int(r["Volcano_Number"]) for r in _rows(path)}
    missing = sorted(want - got)
    if len(missing) > len(want) // 2:  # most of the crosswalk gone: a wrong or broken file, not drift
        return [f"crosswalk GVP numbers missing from the WFS: {missing}"]
    if missing:  # a GVP renumbering or merge is drift, not a broken file; the registry's row bounds still gate the file (audit L1)
        print(f"::warning title=GVP drift::crosswalk GVP numbers missing from the WFS: {missing}; update plumes/data/volcanoes.csv", flush=True)
    if new := sorted(got - want):
        print(f"::notice title=GVP drift::Philippine GVP numbers not in the crosswalk: {new}", flush=True)
    return []


def check_gvp_eruptions(path: Path, source: dict[str, Any]) -> list[str]:
    probs = []
    for r in _rows(path):
        n, vei = int(r["Volcano_Number"]), r["ExplosivityIndexMax"]
        if not 271000 <= n <= 274999:
            probs.append(f"volcano number {n} outside the Philippine range")
        if vei and not (vei.isdigit() and 0 <= int(vei) <= 8):
            probs.append(f"eruption {r['Eruption_Number']}: VEI {vei!r}")
    return probs[:20]


def check_usgs(path: Path, source: dict[str, Any]) -> list[str]:
    probs = []
    for r in _rows(path):
        lat, lon = float(r["latitude"]), float(r["longitude"])
        if not (3.9 <= lat <= 22.1 and 115.9 <= lon <= 128.1):
            probs.append(f"{r['id']}: outside the Philippine box ({lat}, {lon})")
        if not r["time"][:4].isdigit():
            probs.append(f"{r['id']}: bad time {r['time']!r}")
    return probs[:20]


def fetch_files(ids: list[str] | None = None) -> dict:
    """Fetch the file sources through archivekit (primary -> mirrors -> archive). Returns the run manifest dict."""
    import archivekit

    reg = archivekit.load_registry(REGISTRY, root=PIPELINE)
    run = archivekit.RunManifest()
    for sid in ids or FILE_SOURCES:
        p = archivekit.fetch(sid, reg, manifest=run)
        print(f"  {sid}: {p.link_id} rows={p.rows}", flush=True)
    return run.to_dict()


if __name__ == "__main__":
    print(json.dumps(fetch_files(), indent=1, default=str)[:2000])
