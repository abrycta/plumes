"""NOAA-20 VIIRS thermal detections per volcano: the continuity series after S-NPP (LAYERS-PLAN.md §7 step 1, DECISIONS L5).

S-NPP deliveries end on 2026-11-02, so NOAA-20 is the primary VIIRS source from M2. It is published as its own series
(`fire_viirs_n20_15km`), never spliced into the S-NPP one; the sensor-change marker follows the Akari chart marker.

Links (registry id `firms-viirs-noaa20`), tried in order:
1. FIRMS area API `VIIRS_NOAA20_SP` (standard processing, 2018-04-01 onward, about 3-4 months behind), through the
   existing `plumes.firms` client: 5-day windows on its grid, recorded in `windows.jsonl`. Only windows whose last day
   the product already covers are fetched, so a window is never recorded as done while still partial.
2. The tail after the last complete standard window, rewritten whole on every run into `VIIRS_NOAA20_NRT/recent.csv`
   (kept from the previous run if any call fails): `VIIRS_NOAA20_SP` for the days it already covers, then
   `VIIRS_NOAA20_NRT` (provisional, no `type` column) up to today. A `product` column says which.
3. The archive: the adopted `firms-viirs-noaa20` bundle in `abrycta/plumes-archive`, restored by `plumes.state restore`
   before the crawl, so a failing API leaves the previous detections in place.
CMR `VJ114A1` v002 is listed as a health-checked, non-automatic link (swath-grid HDF, a different format).

    FIRMS_MAP_KEY=… uv run python -m plumes.thermal_n20 [--start 2018-04-01] [--end 2018-04-30] [--no-nrt]
"""

from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import glob
import json
import math
import os
import sys

from plumes import firms
from plumes.http import Polite
from plumes.paths import RAW

SOURCE = "firms-viirs-noaa20"
SP, NRT = "VIIRS_NOAA20_SP", "VIIRS_NOAA20_NRT"
START = "2018-04-01"
SNPP_END = "2026-11-02"
RING_KM = 15
SERIES_ID = f"fire_viirs_n20_{RING_KM}km"
NRT_FILE = RAW / "firms" / NRT / "recent.csv"
AREA_API = "https://firms.modaps.eosdis.nasa.gov/api/area/csv/{key}/{product}/116,4,128,22/{days}/{date}"

firms.START.setdefault(SP, START)


def _day(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


def sp_covered_to() -> str | None:
    """Last day covered by a successfully fetched standard window (window start + 4 days)."""
    log = RAW / "firms" / SP / "windows.jsonl"
    if not log.exists():
        return None
    ok = [json.loads(ln)["date"] for ln in log.read_text().splitlines() if ln.strip() and json.loads(ln).get("status") == 200]
    return (_day(max(ok)) + dt.timedelta(days=4)).isoformat() if ok else None


def fetch_tail(key: str, c: Polite, since: dt.date, sp_to: dt.date, until: dt.date) -> dict:
    """Detections from `since` to `until` (standard product up to `sp_to`, NRT after), written whole to recent.csv
    only when every call succeeded."""
    out, d, errors = [], since, 0
    while d <= until:
        product, last = (SP, min(sp_to, until)) if d <= sp_to else (NRT, until)
        days = min(5, (last - d).days + 1)
        r = c.get(AREA_API.format(key=key, product=product, days=days, date=d.isoformat()))
        if r.status_code != 200 or "Invalid" in r.text[:200] or "transaction limit" in r.text[:200]:
            errors += 1
        else:
            out += [row | {"product": product} for row in firms.rows_of(r.text)]
        d += dt.timedelta(days=days)
    if errors:
        return {"tail": "kept previous file", "errors": errors}
    NRT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with NRT_FILE.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[*firms.COLS, "product"], extrasaction="ignore")
        w.writeheader()
        w.writerows(out)
    return {"tail_rows": len(out), "from": since.isoformat(), "sp_to": sp_to.isoformat(), "to": until.isoformat()}


def fetch(start: str | None = None, end: str | None = None, nrt: bool = True) -> dict:
    key = os.environ.get("FIRMS_MAP_KEY") or sys.exit("FIRMS_MAP_KEY is not set")
    with Polite(min_interval=1.0) as c:
        avail = firms.availability(c, key)
    # the last window fetched must end on or before the product's last day (window start + 4 <= max_date)
    sp_end = _day(avail[SP]) - dt.timedelta(days=4)
    if end:
        sp_end = min(sp_end, _day(end))
    stats = firms.crawl([SP], start, sp_end.isoformat())
    if nrt:
        covered = sp_covered_to()
        since = _day(covered) + dt.timedelta(days=1) if covered else _day(avail[SP]) + dt.timedelta(days=1)
        until = min(_day(avail.get(NRT, avail[SP])), _day(end)) if end else _day(avail.get(NRT, avail[SP]))
        if since <= until:
            with Polite(min_interval=1.0) as c:
                stats[NRT] = fetch_tail(key, c, since, _day(avail[SP]), until)
    return stats


# ---------------------------------------------------------------- read model


def _km(lat1, lon1, lat2, lon2) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def _detections() -> tuple[list[dict], str | None]:
    """Standard detections, then NRT ones only for the days after the standard coverage ends. Duplicates dropped."""
    covered = sp_covered_to()
    seen, out = set(), []
    for p in sorted(glob.glob(str(RAW / "firms" / SP / "*.csv"))):
        with open(p, newline="") as f:
            for r in csv.DictReader(f):
                k = (r["latitude"], r["longitude"], r["acq_date"], r["acq_time"])
                if k not in seen:
                    seen.add(k)
                    out.append(r | {"_nrt": False})
    if NRT_FILE.exists():
        with open(NRT_FILE, newline="") as f:
            for r in csv.DictReader(f):
                if covered and r["acq_date"] <= covered:
                    continue
                k = (r["latitude"], r["longitude"], r["acq_date"], r["acq_time"])
                if k not in seen:
                    seen.add(k)
                    nrt = r.get("product", NRT) != SP
                    out.append(r | {"_nrt": nrt, "type": "" if nrt else r.get("type", "")})
    return out, covered


def _lt(en: str, ja: str) -> dict:
    return {"en": en, "ja": ja}


def series_by_volcano(vols: list[dict]) -> dict[str, dict]:
    """`fire_viirs_n20_15km` per volcano id: daily rows [date, n, nVolcano, maxFrpMw] within 15 km."""
    dets, covered = _detections()
    if not dets:
        return {}
    days: dict[str, dict[str, list]] = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0, None, False]))
    for r in dets:
        lat, lon = float(r["latitude"]), float(r["longitude"])
        for v in vols:
            if abs(lat - v["lat"]) > 0.2 or _km(v["lat"], v["lon"], lat, lon) > RING_KM:
                continue
            d = days[v["id"]][r["acq_date"]]
            d[0] += 1
            if r.get("type") == "1":
                d[1] += 1
            frp = float(r["frp"]) if r.get("frp") not in (None, "") else None
            if frp is not None and (d[2] is None or frp > d[2]):
                d[2] = frp
            d[3] = d[3] or r["_nrt"]
    note = _lt(
        "NOAA-20 VIIRS, its own series: not joined to the S-NPP record, whose deliveries end on "
        f"{SNPP_END}. Detections include vegetation fires; 'flagged volcanic' counts FIRMS type 1 (active volcano)."
        + " Days without a flagged count are near-real-time (provisional) detections, which carry no type flag.",
        "NOAA-20 VIIRSの独立した系列で、S-NPPの記録とは接続しない(S-NPPの配信は"
        f"{SNPP_END}に終了)。熱異常には植生火災も含まれる。「火山フラグ」はFIRMS type 1(活火山)の件数。"
        + "火山フラグの件数がない日は準リアルタイム(暫定)の検知で、typeフラグがない。",
    )
    out = {}
    for v in vols:
        by = days.get(v["id"], {})
        out[v["id"]] = {SERIES_ID: {
            "source": [SOURCE],
            "label": _lt(f"VIIRS (NOAA-20) thermal detections within {RING_KM} km", f"VIIRS(NOAA-20)熱異常検知({RING_KM} km圏)"),
            "cols": ["date", "n", "nVolcano", "maxFrpMw"],
            "units": {"n": "detections", "nVolcano": "detections", "maxFrpMw": "MW"},
            "ringKm": RING_KM, "start": START,
            "rows": [[d, x[0], None if x[3] else x[1], None if x[2] is None else round(x[2], 1)] for d, x in sorted(by.items())],
            "note": note}}
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start")
    ap.add_argument("--end")
    ap.add_argument("--no-nrt", action="store_true")
    a = ap.parse_args()
    print(json.dumps(fetch(a.start, a.end, not a.no_nrt)))
