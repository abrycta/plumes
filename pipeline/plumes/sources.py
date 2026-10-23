"""archivekit hooks (named in sources.yaml) and the fetch step for the file sources.

A hook gets the downloaded file and its registry entry. A broken file (wrong rows, foreign values, an unreadable body)
raises SchemaError, so archivekit rejects it and moves on to the next link (DATA-ARCHIVING §2); a returned list is only
drift notes, which the kit reports but accepts (kit contract, formats.run_hooks; audit P2).
"""

from __future__ import annotations

import collections
import csv
import datetime as dt
import json
import math
import re
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
    rows = _read(path, {"Volcano_Number", "ExplosivityIndexMax", "Eruption_Number"})
    probs += duplicates(r["Eruption_Number"] for r in rows)
    for r in rows:
        n, vei = int(r["Volcano_Number"]) if r["Volcano_Number"].isdigit() else -1, r["ExplosivityIndexMax"]
        if not 271000 <= n <= 274999:
            probs.append(f"volcano number {n} outside the Philippine range")
        if vei and not (vei.isdigit() and 0 <= int(vei) <= 8):
            probs.append(f"eruption {r['Eruption_Number']}: VEI {vei!r}")
    reject(probs)
    return []


# USGS ComCat event types (https://earthquake.usgs.gov/fdsnws/event/1/application.json); anything else is a new
# category value: warned, and the file is rejected when it pushes "earthquake" below EQ_SHARE of the rows (audit A3).
USGS_TYPES = {"earthquake", "quarry blast", "explosion", "other event", "mining explosion", "chemical explosion",
              "experimental explosion", "accidental explosion", "nuclear explosion", "rock burst", "collapse", "mine collapse",
              "landslide", "rockslide", "volcanic eruption", "volcanic explosion", "induced or triggered event", "ice quake",
              "sonic boom", "acoustic noise", "not reported", "meteorite", "snow avalanche"}
EQ_SHARE = 0.9
MAG_RANGE, DEPTH_RANGE = (-2.0, 10.0), (-10.0, 800.0)


def _finite_in(x: str, lo: float, hi: float) -> bool:
    """An empty value (not reported) or a finite number in [lo, hi]; NaN, inf and absurd values are not (audit A1)."""
    if x == "":
        return True
    try:
        v = float(x)
    except ValueError:
        return False
    return math.isfinite(v) and lo <= v <= hi


def _iso_time(s: str) -> bool:
    """ISO 8601 with a 4-digit year (2020-01-12T06:50:00.000Z); epoch milliseconds or another format is not (audit A3)."""
    try:
        dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return False
    return bool(re.match(r"\d{4}-\d{2}-\d{2}", s))


def check_usgs(path: Path, source: dict[str, Any]) -> list[str]:
    probs = []
    rows = _read(path, {"id", "time", "latitude", "longitude", "mag", "depth", "type"})
    for r in rows:
        try:
            lat, lon = float(r["latitude"]), float(r["longitude"])
        except ValueError:
            lat = lon = float("nan")
        if not (3.9 <= lat <= 22.1 and 115.9 <= lon <= 128.1):
            probs.append(f"{r['id']}: outside the Philippine box ({lat}, {lon})")
        if not _iso_time(r["time"]):
            probs.append(f"{r['id']}: bad time {r['time']!r}")
        if not _finite_in(r["mag"], *MAG_RANGE):
            probs.append(f"{r['id']}: magnitude {r['mag']!r}")
        if not _finite_in(r["depth"], *DEPTH_RANGE):
            probs.append(f"{r['id']}: depth {r['depth']!r}")
    probs += duplicates(r["id"] for r in rows)
    types = collections.Counter(r["type"] for r in rows)
    if types["earthquake"] < EQ_SHARE * len(rows):
        probs.append(f"only {types['earthquake']} of {len(rows)} rows have type 'earthquake': {dict(types.most_common(5))}")
    if new := sorted(set(types) - USGS_TYPES):
        print(f"::warning title=USGS drift::new event type values {new[:10]}; plumes.readmodels keeps only 'earthquake'", flush=True)
    reject(probs)
    return []


def duplicates(ids) -> list[str]:
    """A problem per id seen more than once: a doubled answer would double every count built from it (audit A1)."""
    dup = [k for k, n in collections.Counter(ids).items() if n > 1]
    return [f"{len(dup)} duplicate ids, e.g. {dup[:5]}"] if dup else []


def archive_baseline(reg, sid: str, client) -> dict | None:
    """The newest good archive snapshot's manifest as the gate's baseline (rows, profile), for a CI run that starts from
    a fresh checkout: without it the shrink tolerance and the anomaly gate never run there, and a file cut at a row
    boundary would be accepted (audit A1). None when the archive can't be read: the absolute row bounds still apply."""
    import tempfile

    from archivekit.github import ArchiveClient, resolve_token
    from archivekit.snapshot import _baseline  # the kit's own manifest -> provenance-baseline mapping

    try:
        token = resolve_token(reg.archive.get("token_env", "ARCHIVE_READ_TOKEN"), reg.archive_repo)
        with tempfile.TemporaryDirectory() as td:
            good = ArchiveClient(reg.archive_repo, token, client).latest_good(sid, Path(td))
    except Exception as e:  # noqa: BLE001 - a baseline is a safeguard, never a reason to stop fetching
        print(f"::warning title=no archive baseline::{sid}: {type(e).__name__}: {str(e)[:200]}; only the row bounds gate this file", flush=True)
        return None
    if good is None:
        print(f"::warning title=no archive baseline::{sid}: no good snapshot in {reg.archive_repo}", flush=True)
        return None
    return _baseline(good[1] | {"tag": good[0]["tag_name"]})


def fetch_files(ids: list[str] | None = None) -> dict:
    """Fetch the file sources through archivekit (primary -> mirrors -> archive). Returns the run manifest dict.

    The baseline for the shrink and anomaly gates is the local provenance sidecar, or, when there is none (every CI
    run), the newest good archive snapshot's manifest."""
    import archivekit
    from archivekit.fetch import provenance_path
    from archivekit.http import make_client

    reg = archivekit.load_registry(REGISTRY, root=PIPELINE)
    run = archivekit.RunManifest()
    with make_client(reg.health.get("user_agent")) as client:
        for sid in ids or FILE_SOURCES:
            dest = reg.root / reg.source(sid)["local_path"]
            prev = None if provenance_path(dest).exists() else archive_baseline(reg, sid, client)
            p = archivekit.fetch(sid, reg, manifest=run, client=client, previous=prev)
            print(f"  {sid}: {p.link_id} rows={p.rows} baseline={(prev or {}).get('archive_tag') or 'local'}", flush=True)
    return run.to_dict()


if __name__ == "__main__":
    print(json.dumps(fetch_files(), indent=1, default=str)[:2000])
