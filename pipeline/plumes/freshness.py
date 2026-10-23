"""How recent each crawled or queried input is (audit P5): the newest record per source, against its cadence.

Internal only. Nothing here goes into the published files or the app: a source whose newest record is older than its
cadence prints a ::warning and opens (or updates) its `stale <source>` health issue; a fresh one closes it. Sources
without a regular cadence (VAAC advisories come only with eruptions, WordPress bulletins are now mostly notices) are
listed without a limit.
"""

from __future__ import annotations

import datetime as dt
import json
import os

from plumes import coverage, health
from plumes.crawl.records import Records
from plumes.paths import RAW

# Days a source's newest record may lag the run date before it counts as stale. Standard-processing FIRMS lags the
# calendar by up to about four months; the Earth Engine tables are monthly and wait for the collection to catch up.
CADENCE = {
    "phivolcs-lava-bulletins": 14,
    "firms-viirs-noaa20-nrt": 7,
    "firms-viirs-noaa20-sp": 200,
    "firms-modis-sp": 200,
    "ee-fire-modis-mod14a1": 120,
    "ee-fire-firms-modis": 120,
    "ee-so2": 100,
    "usgs-comcat-ph-2010": 45,
}
# Sources with a known end: never stale after it (S-NPP deliveries end on 2026-11-02).
ENDED = {"firms-viirs-snpp-sp", "ee-fire-viirs-vnp14a1"}


def _max(xs) -> str | None:
    xs = [x for x in xs if x]
    return max(xs) if xs else None


def newest(usgs: list[dict], so2: list[dict], fire_end: dict[str, str]) -> dict[str, str | None]:
    """Newest record date (YYYY-MM-DD) per input, from what the build loaded and the crawl records."""
    from plumes import firms, thermal_n20  # local: firms pulls the HTTP client

    def ok(path, field):
        return _max(str(r.get(field) or "")[:10] for r in Records(path) if r.get("status") == 200)

    vaac = ok(RAW / "vaac-tokyo-advisories" / "pages.jsonl", "date")
    tail = thermal_n20.NRT_FILE.with_name("recent.json")
    out = {
        "phivolcs-lava-bulletins": ok(RAW / "phivolcs-lava-bulletins" / "pages.jsonl", "date"),
        "phivolcs-bulletins": ok(RAW / "phivolcs-bulletins" / "pages.jsonl", "lastmod"),
        "vaac-tokyo-advisories": f"{vaac[:4]}-{vaac[4:6]}-{vaac[6:8]}" if vaac else None,
        "firms-modis-sp": firms.covered_to("MODIS_SP"),
        "firms-viirs-snpp-sp": firms.covered_to("VIIRS_SNPP_SP"),
        "firms-viirs-noaa20-sp": thermal_n20.sp_covered_to(),
        "firms-viirs-noaa20-nrt": json.loads(tail.read_text()).get("to") if tail.exists() else None,
        "ee-so2": _max(r["date"] for r in so2 if r.get("so2_pbl_mol_m2") not in (None, "")),
        "usgs-comcat-ph-2010": _max(r["t"][:10] for r in usgs),
    }
    out |= {f"ee-fire-{s}": fire_end.get(s) for s in coverage.FIRE_SOURCES}
    return out


def assess(latest: dict[str, str | None], today: dt.date | None = None) -> dict[str, dict]:
    today = today or dt.date.today()
    res = {}
    for sid, last in sorted(latest.items()):
        limit = None if sid in ENDED else CADENCE.get(sid)
        age = (today - dt.date.fromisoformat(last)).days if last else None
        res[sid] = {"newest": last, "ageDays": age, "maxAgeDays": limit, "stale": limit is not None and (age is None or age > limit)}
    return res


def alert(res: dict[str, dict]) -> list[str]:
    """::warning + health issue per stale source; closes the issue of a source that is fresh again. Returns the stale ids."""
    if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(summary, "a") as f:
            f.write("### Input freshness\n\n| source | newest record | age (days) | limit |\n|---|---|---:|---:|\n")
            f.writelines(f"| {sid} | {r['newest'] or '-'} | {r['ageDays'] if r['ageDays'] is not None else '-'} | "
                         f"{r['maxAgeDays'] or '-'}{' **stale**' if r['stale'] else ''} |\n" for sid, r in res.items())
    stale = []
    for sid, r in res.items():
        if r["maxAgeDays"] is None:
            continue
        key = f"stale {sid}"
        if r["stale"]:
            stale.append(sid)
            health.report(key, f"stale since {r['newest']}",
                          f"`{sid}`: newest record {r['newest'] or 'none'} ({r['ageDays']} days old; limit {r['maxAgeDays']}). "
                          "The pipeline keeps building from the records it has; check the source and its crawler.")
        else:
            health.resolve(key, f"`{sid}` has a record from {r['newest']} again.")
    return stale
