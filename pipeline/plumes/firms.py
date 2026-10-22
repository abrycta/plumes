"""NASA FIRMS area API: standard-processing detections over the Philippine box, 5 days per call (DECISIONS S-run 1 item 19).

Products: MODIS_SP (2000-11 ->) and VIIRS_SNPP_SP (2012-01-20 ->). Each call returns a CSV with no trailing newline, so
responses are split on the header, never concatenated raw. Only windows whose last day the product already covers are
fetched, so a window is never recorded as done while partial (its days would read as "nothing detected" for good); rows
are filed by acquisition year, so a window across New Year splits between the two yearly files. FIRMS `type`: 0 presumed vegetation fire, 1 active volcano,
2 other static land source, 3 offshore. Needs FIRMS_MAP_KEY (never logged: URLs are recorded with the key masked).

    FIRMS_MAP_KEY=… uv run python -m plumes.firms [--product VIIRS_SNPP_SP] [--start 2012-01-20]
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import os
import sys
import time

from plumes.crawl.records import Records, now, sha256
from plumes.http import Polite
from plumes.paths import RAW

API = "https://firms.modaps.eosdis.nasa.gov/api/area/csv/{key}/{product}/116,4,128,22/5/{date}"
START = {"MODIS_SP": "2000-11-01", "VIIRS_SNPP_SP": "2012-01-20"}
OUT = RAW / "firms"
WINDOW_DAYS = 5
# Records written before windows carried "to" may be partial: trusted only when fetched this long after the window
# ended (standard products lag the calendar by up to about four months); anything newer is fetched again.
LEGACY_SETTLED_DAYS = 180
COLS = ["latitude", "longitude", "acq_date", "acq_time", "satellite", "instrument", "confidence", "frp", "daynight", "type"]


def availability(c: Polite, key: str) -> dict[str, str]:
    r = c.get(f"https://firms.modaps.eosdis.nasa.gov/api/data_availability/csv/{key}/ALL")
    return {row["data_id"]: row["max_date"] for row in csv.DictReader(io.StringIO(r.text))}


def rows_of(text: str) -> list[dict]:
    text = text.strip()
    if not text or not text.startswith("latitude"):
        return []
    head = text.split("\n", 1)[0]
    lines = [ln for ln in text.replace(head, "\n" + head).splitlines() if ln and ln != head]
    return list(csv.DictReader([head, *lines]))


def _end(d: dt.date) -> dt.date:
    return d + dt.timedelta(days=WINDOW_DAYS - 1)


def complete(rec: dict) -> bool:
    """A successful window record that covers all five days."""
    if rec.get("status") != 200:
        return False
    if "to" in rec:
        return True
    fetched = dt.date.fromisoformat(rec["fetched"][:10])
    return _end(dt.date.fromisoformat(rec["date"])) <= fetched - dt.timedelta(days=LEGACY_SETTLED_DAYS)


def covered_to(product: str) -> str | None:
    """Last day covered by a complete window of `product`."""
    ok = [d for d, r in Records(OUT / product / "windows.jsonl").latest("date").items() if complete(r)]
    return _end(dt.date.fromisoformat(max(ok))).isoformat() if ok else None


def _write_window(product: str, d: dt.date, rows: list[dict], replace: bool) -> None:
    """Append a window's rows to the yearly file of each row's acquisition date; `replace` first drops the rows an
    earlier (partial) fetch of the same window left there."""
    a, b = d.isoformat(), _end(d).isoformat()
    by_year: dict[str, list[dict]] = {}
    for r in rows:
        by_year.setdefault((r.get("acq_date") or a)[:4], []).append(r)
    for y in sorted(set(by_year) | ({a[:4], b[:4]} if replace else set())):
        path = OUT / product / f"{y}.csv"
        add = by_year.get(y, [])
        if replace and path.exists():
            with path.open(newline="") as f:
                keep = [r for r in csv.DictReader(f) if not a <= r["acq_date"] <= b]
            mode, add = "w", keep + add
        elif not add:
            continue
        else:
            mode = "a" if path.exists() else "w"
        with path.open(mode, newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
            if mode == "w":
                w.writeheader()
            w.writerows(add)


def crawl(products: list[str], start: str | None = None, end: str | None = None) -> dict:
    key = os.environ.get("FIRMS_MAP_KEY") or sys.exit("FIRMS_MAP_KEY is not set")
    stats = {}
    with Polite(min_interval=1.0) as c:
        avail = availability(c, key)
        for product in products:
            log = Records(OUT / product / "windows.jsonl")
            latest = log.latest("date")
            done = {ds for ds, r in latest.items() if complete(r)}
            # windows stay on the product's 5-day grid, so parallel ranges never overlap or leave gaps
            d0 = dt.date.fromisoformat(START[product])
            d = d0 if not start else d0 + dt.timedelta(days=-(-(dt.date.fromisoformat(start) - d0).days // 5) * 5)
            last = dt.date.fromisoformat(avail[product])
            # the last window fetched must end on or before the product's last day
            last_start = last - dt.timedelta(days=WINDOW_DAYS - 1)
            end_ = min(last_start, dt.date.fromisoformat(end)) if end else last_start
            n = 0
            while d <= end_:
                ds = d.isoformat()
                if ds not in done:
                    r = c.get(API.format(key=key, product=product, date=ds))
                    for _ in range(3):  # FIRMS weighs transactions by size: wait out the 10-minute window and retry
                        if "transaction limit" not in r.text[:200]:
                            break
                        time.sleep(600)
                        r = c.get(API.format(key=key, product=product, date=ds))
                    if r.status_code != 200 or "Invalid" in r.text[:200]:
                        log.add({"date": ds, "status": r.status_code, "fetched": now(), "error": r.text[:200].replace(key, "<MAP_KEY>")})
                    else:
                        rows = rows_of(r.text)
                        _write_window(product, d, rows, replace=latest.get(ds, {}).get("status") == 200)
                        log.add({"date": ds, "to": _end(d).isoformat(), "status": 200, "fetched": now(), "rows": len(rows), "sha256": sha256(r.content)})
                        n += 1
                d += dt.timedelta(days=WINDOW_DAYS)
            stats[product] = {"windows_fetched": n, "available_to": avail[product]}
            print(product, stats[product], flush=True)
    return stats


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--product", action="append")
    ap.add_argument("--start")
    ap.add_argument("--end")
    a = ap.parse_args()
    print(crawl(a.product or ["MODIS_SP", "VIIRS_SNPP_SP"], a.start, a.end))
