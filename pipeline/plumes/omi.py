"""OMI SO2 per volcano box, 2004-10 onward: the SO2 track before (and beside) TROPOMI (LAYERS-PLAN.md §7 step 2).

Collection: OMSO2e **v004** (`C3756242136-GES_DISC`, doi:10.5067/AURA/OMI/DATA3408). v003, named in the M1 registry,
stopped at 2026-03-22; v004 covers 2004-10-01 to now. Its `ColumnAmountSO2` is a "Vertical Column Amount SO2 (GEOS-5
Profile)" in DU: one column per pixel with a model profile, not the PBL/TRL/STL family of v003.

Route: one Harmony request per calendar year over the Philippine box (HOSS: bbox and variable subset, about 25 kB a day),
each daily file reduced at once to rows for all 24 volcanoes and then discarded. Only the reduced table
`data/tables/omi-so2/<year>.csv` is kept and adopted into the archive (registry id `omi-omso2e`).
Links (registry), in order: Harmony; the archive (restored by `plumes.state restore`, so a Harmony outage leaves the
previous table in place). OPeNDAP and the CMR record are health-checked only.

Reduction, per volcano and day: cells whose centres lie within a box of half-width 50 km; a cell is valid when it holds a
value in the product's valid range and its cloud radiance fraction is at most 0.3 (larger clouds hide the lower
troposphere). Row: mean and max column (DU) over valid cells, valid and total cell counts.

    EARTHDATA_TOKEN=… uv run python -m plumes.omi [--start 2020-01-10] [--end 2020-01-16]
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import glob
import json
import math
import os
import re
import sys
import tempfile
import time
import urllib.parse
from pathlib import Path

import httpx

from plumes.paths import TABLES

SOURCE = "omi-omso2e"
COLLECTION = "C3756242136-GES_DISC"
START = "2004-10-01"
HARMONY = "https://harmony.earthdata.nasa.gov"
GRID = "HDFEOS/GRIDS/OMI_Total_Column_Amount_SO2"
VARS = [f"{GRID}/Data_Fields/ColumnAmountSO2", f"{GRID}/Data_Fields/CloudRadianceFraction"]
BOX = (116, 4, 128, 22)  # W, S, E, N
HALF_KM = 50
CLOUD_MAX = 0.3
OUT = TABLES / "omi-so2"
COLS = ["volcano", "date", "so2_du_mean", "so2_du_max", "valid", "total"]
SERIES_ID = "so2_omi_box"


def _volcanoes() -> list[dict]:
    """The 24 volcanoes with coordinates (GVP where known, the crosswalk otherwise), as the read models use them."""
    from plumes.readmodels import load_volcanoes

    return [{"id": v["id"], "lat": v["lat"], "lon": v["lon"]} for v in load_volcanoes()]


def cells_for(vols: list[dict], lats, lons) -> dict[str, tuple]:
    """Row and column indices of the grid cells inside each volcano's box."""
    import numpy as np

    out = {}
    for v in vols:
        dlat = HALF_KM / 111.32
        dlon = HALF_KM / (111.32 * math.cos(math.radians(v["lat"])))
        rows = np.where(np.abs(lats - v["lat"]) <= dlat)[0]
        cols = np.where(np.abs(lons - v["lon"]) <= dlon)[0]
        out[v["id"]] = (rows, cols)
    return out


def reduce_file(path: Path, vols: list[dict]) -> list[dict]:
    """Rows for one daily subset file."""
    import h5py
    import numpy as np

    m = re.search(r"_(\d{4})m(\d{2})(\d{2})_", path.name)
    if not m:
        return []
    date = f"{m[1]}-{m[2]}-{m[3]}"
    with h5py.File(path, "r") as f:
        g = f[GRID]
        lats, lons = g["YDim"][:], g["XDim"][:]
        so2 = g["Data_Fields/ColumnAmountSO2"]
        cf = g["Data_Fields/CloudRadianceFraction"][:]
        lo, hi = so2.attrs.get("ValidRange", [-10.0, 2000.0])
        x = so2[:]
    valid = np.isfinite(x) & (x >= lo) & (x <= hi) & np.isfinite(cf) & (cf >= 0) & (cf <= CLOUD_MAX)
    out = []
    for vid, (r, c) in cells_for(vols, lats, lons).items():
        if not len(r) or not len(c):
            continue
        vv, ok = x[np.ix_(r, c)], valid[np.ix_(r, c)]
        n = int(ok.sum())
        out.append({"volcano": vid, "date": date, "so2_du_mean": round(float(vv[ok].mean()), 3) if n else "",
                    "so2_du_max": round(float(vv[ok].max()), 3) if n else "", "valid": n, "total": int(ok.size)})
    return out


def _token() -> str:
    return os.environ.get("EARTHDATA_TOKEN") or sys.exit("EARTHDATA_TOKEN is not set")


def submit(c: httpx.Client, start: str, end: str) -> str:
    q = [("variable", v) for v in VARS] + [
        ("subset", f"lat({BOX[1]}:{BOX[3]})"), ("subset", f"lon({BOX[0]}:{BOX[2]})"),
        ("subset", f'time("{start}T00:00:00Z":"{end}T23:59:59Z")'), ("format", "application/x-netcdf4"), ("forceAsync", "true")]
    url = f"{HARMONY}/{COLLECTION}/ogc-api-coverages/1.0.0/collections/parameter_vars/coverage/rangeset?" + urllib.parse.urlencode(q)
    r = c.get(url, follow_redirects=False)
    if r.status_code in (301, 302, 303):
        return r.headers["location"].rstrip("/").rsplit("/", 1)[-1]
    r.raise_for_status()
    return r.json()["jobID"]


def wait(c: httpx.Client, job: str, timeout_s: int = 3600) -> list[str]:
    """Poll the job, then return every data link (following the status pages)."""
    t0 = time.monotonic()
    while True:
        st = c.get(f"{HARMONY}/jobs/{job}").raise_for_status().json()
        if st["status"] in ("successful", "complete_with_errors"):
            break
        if st["status"] in ("failed", "canceled"):
            raise RuntimeError(f"Harmony job {job}: {st['status']}: {st.get('message', '')[:200]}")
        if time.monotonic() - t0 > timeout_s:
            raise TimeoutError(f"Harmony job {job} still {st['status']} after {timeout_s} s")
        time.sleep(15)
    links, page = [], st
    while True:
        links += [lk["href"] for lk in page.get("links", []) if lk.get("rel") == "data"]
        nxt = next((lk["href"] for lk in page.get("links", []) if lk.get("rel") == "next"), None)
        if not nxt:
            return links
        page = c.get(nxt).raise_for_status().json()


def table(year: int) -> Path:
    return OUT / f"{year}.csv"


def last_date(year: int) -> str | None:
    p = table(year)
    if not p.exists():
        return None
    with p.open(newline="") as f:
        return max((r["date"] for r in csv.DictReader(f)), default=None)


def fetch(start: str | None = None, end: str | None = None, vols: list[dict] | None = None) -> dict:
    """New days only: each year from the day after its table's last date (or `start`) to `end` (default: yesterday)."""
    tok = _token()
    vols = vols or _volcanoes()
    d0 = dt.date.fromisoformat(start or START)
    d1 = dt.date.fromisoformat(end) if end else dt.date.today() - dt.timedelta(days=1)
    stats = {}
    OUT.mkdir(parents=True, exist_ok=True)
    with httpx.Client(headers={"Authorization": f"Bearer {tok}"}, timeout=120) as c:
        for year in range(d0.year, d1.year + 1):
            a = max(d0, dt.date(year, 1, 1))
            done = last_date(year)
            if done and not start:
                a = max(a, dt.date.fromisoformat(done) + dt.timedelta(days=1))
            b = min(d1, dt.date(year, 12, 31))
            if a > b:
                continue
            job = submit(c, a.isoformat(), b.isoformat())
            links = wait(c, job)
            rows = []
            with tempfile.TemporaryDirectory() as td:
                for href in links:
                    p = Path(td) / href.rsplit("/", 1)[-1]
                    with c.stream("GET", href, follow_redirects=True) as r:
                        r.raise_for_status()
                        with p.open("wb") as f:
                            for chunk in r.iter_bytes():
                                f.write(chunk)
                    rows += reduce_file(p, vols)
                    p.unlink()
            _merge(year, rows)
            stats[year] = {"job": job, "files": len(links), "rows": len(rows), "from": a.isoformat(), "to": b.isoformat()}
            print(year, stats[year], flush=True)
    return stats


def _merge(year: int, rows: list[dict]) -> None:
    """Write the year's table, replacing any earlier row for the same volcano and day."""
    p = table(year)
    p.parent.mkdir(parents=True, exist_ok=True)
    have = {}
    if p.exists():
        with p.open(newline="") as f:
            have = {(r["volcano"], r["date"]): r for r in csv.DictReader(f)}
    have |= {(r["volcano"], r["date"]): r for r in rows}
    tmp = p.with_suffix(".tmp")
    with tmp.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(sorted(have.values(), key=lambda r: (r["date"], r["volcano"])))
    tmp.replace(p)


# ---------------------------------------------------------------- read model


def _lt(en: str, ja: str) -> dict:
    return {"en": en, "ja": ja}


def series_by_volcano(end: str) -> dict[str, dict]:
    """`so2_omi_box` per volcano id: daily mean column (DU) and the valid-cell fraction."""
    by: dict[str, dict[str, dict]] = {}
    for p in sorted(glob.glob(str(OUT / "*.csv"))):
        with open(p, newline="") as f:
            for r in csv.DictReader(f):
                by.setdefault(r["volcano"], {})[r["date"]] = r
    out = {}
    note = _lt(
        "OMI on Aura (OMSO2e v4): column amount with a model (GEOS-5) profile, averaged over 0.25° cells within 50 km on the "
        "day's clear cells (cloud radiance fraction at most 0.3). Cells are larger than most volcanoes; rows of the sensor "
        "have been blocked since 2008 (row anomaly), so many days have partial coverage. Not an emission rate. Shown "
        "separately from TROPOMI, never joined.",
        "Aura衛星OMI(OMSO2e v4):モデル(GEOS-5)鉛直分布によるカラム量を、50 km以内の0.25°格子のうち晴天の格子"
        "(雲放射率0.3以下)で平均。格子は多くの火山より大きく、2008年以降はセンサーの一部の列が使えない(行異常)ため被覆率が"
        "低い日が多い。放出率ではない。TROPOMIとは別に表示し、接続しない。",
    )
    for vid, days in by.items():
        start = min(days)
        last = min(end, max(days))
        n = (dt.date.fromisoformat(last) - dt.date.fromisoformat(start)).days + 1
        values, coverage = [None] * n, [None] * n
        for d, r in days.items():
            i = (dt.date.fromisoformat(d) - dt.date.fromisoformat(start)).days
            if not 0 <= i < n:
                continue
            t = int(r["total"])
            values[i] = round(float(r["so2_du_mean"]), 2) if r["so2_du_mean"] not in ("", None) else None
            coverage[i] = round(int(r["valid"]) / t, 3) if t else None
        out[vid] = {SERIES_ID: {"source": [SOURCE], "unit": "DU", "ringKm": HALF_KM, "start": start,
                                "label": _lt("OMI SO₂ column, mean within the 50 km box", "OMI SO₂カラム量(50 km範囲平均)"),
                                "values": values, "coverage": coverage, "note": note}}
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start")
    ap.add_argument("--end")
    a = ap.parse_args()
    print(json.dumps(fetch(a.start, a.end)))
