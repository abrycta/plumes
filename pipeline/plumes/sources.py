"""archivekit hooks (named in sources.yaml) and the fetch step for the file sources.

A hook gets the downloaded file and its registry entry. A broken file (wrong rows, foreign values, an unreadable body)
raises SchemaError, so archivekit rejects it and moves on to the next link (DATA-ARCHIVING §2); a returned list is only
drift notes, which the kit reports but accepts (kit contract, formats.run_hooks; audit P2).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from plumes.paths import CROSSWALK, PIPELINE, REGISTRY

try:
    from archivekit import SchemaError
except ImportError:  # the checks job runs without the private kit

    class SchemaError(ValueError):  # type: ignore[no-redef]
        pass


FILE_SOURCES = ["gvp-volcanoes-ph", "gvp-eruptions-ph", "usgs-comcat-ph-1900-2009", "usgs-comcat-ph-2010", "noaa-hazel-volcanoes-ph"]


def _rows(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def reject(probs: list[str]) -> None:
    """Raise SchemaError for hard problems: the kit rejects the file and tries the next link."""
    if probs:
        raise SchemaError("; ".join(probs[:20]))


def _read(path: Path, need: set[str]) -> list[dict]:
    """The CSV rows, or SchemaError when the body is not a CSV holding the `need` columns (an HTML page, another shape)."""
    try:
        rows = _rows(path)
    except (UnicodeDecodeError, csv.Error) as e:
        raise SchemaError(f"not a readable CSV: {e}") from None
    if not rows or not need <= set(rows[0]):
        raise SchemaError(f"expected columns {sorted(need)}, got {sorted(rows[0]) if rows else 'no rows'}")
    return rows


def check_gvp_volcanoes(path: Path, source: dict[str, Any]) -> list[str]:
    want = {int(r["gvp_number"]) for r in _rows(CROSSWALK) if r["gvp_number"]}
    got = set()
    for r in _read(path, {"Volcano_Number"}):
        try:
            got.add(int(r["Volcano_Number"]))
        except ValueError:
            reject([f"volcano number {r['Volcano_Number']!r}"])
    missing = sorted(want - got)
    if len(missing) > len(want) // 2:  # most of the crosswalk gone: a wrong or broken file, not drift
        reject([f"crosswalk GVP numbers missing from the WFS: {missing}"])
    if missing:  # a GVP renumbering or merge is drift, not a broken file; the registry's row bounds still gate the file (audit L1)
        print(f"::warning title=GVP drift::crosswalk GVP numbers missing from the WFS: {missing}; update plumes/data/volcanoes.csv", flush=True)
    if new := sorted(got - want):
        print(f"::notice title=GVP drift::Philippine GVP numbers not in the crosswalk: {new}", flush=True)
    return []


def check_gvp_eruptions(path: Path, source: dict[str, Any]) -> list[str]:
    probs = []
    for r in _read(path, {"Volcano_Number", "ExplosivityIndexMax", "Eruption_Number"}):
        n, vei = int(r["Volcano_Number"]) if r["Volcano_Number"].isdigit() else -1, r["ExplosivityIndexMax"]
        if not 271000 <= n <= 274999:
            probs.append(f"volcano number {n} outside the Philippine range")
        if vei and not (vei.isdigit() and 0 <= int(vei) <= 8):
            probs.append(f"eruption {r['Eruption_Number']}: VEI {vei!r}")
    reject(probs)
    return []


def check_usgs(path: Path, source: dict[str, Any]) -> list[str]:
    probs = []
    for r in _read(path, {"id", "time", "latitude", "longitude"}):
        try:
            lat, lon = float(r["latitude"]), float(r["longitude"])
        except ValueError:
            lat = lon = float("nan")
        if not (3.9 <= lat <= 22.1 and 115.9 <= lon <= 128.1):
            probs.append(f"{r['id']}: outside the Philippine box ({lat}, {lon})")
        if not r["time"][:4].isdigit():
            probs.append(f"{r['id']}: bad time {r['time']!r}")
    reject(probs)
    return []


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
