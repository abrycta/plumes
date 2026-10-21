"""NASA FIRMS area API: standard-processing detections over the Philippine box, 5 days per call (DECISIONS S-run 1 item 19).

Products: MODIS_SP (2000-11 ->) and VIIRS_SNPP_SP (2012-01-20 ->). Each call returns a CSV with no trailing newline, so
responses are split on the header, never concatenated raw. FIRMS `type`: 0 presumed vegetation fire, 1 active volcano,
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

from plumes.crawl.records import Records, now, sha256
from plumes.http import Polite
from plumes.paths import RAW

API = "https://firms.modaps.eosdis.nasa.gov/api/area/csv/{key}/{product}/116,4,128,22/5/{date}"
START = {"MODIS_SP": "2000-11-01", "VIIRS_SNPP_SP": "2012-01-20"}
OUT = RAW / "firms"
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


def crawl(products: list[str], start: str | None = None) -> dict:
    key = os.environ.get("FIRMS_MAP_KEY") or sys.exit("FIRMS_MAP_KEY is not set")
    stats = {}
    with Polite(min_interval=1.0) as c:
        avail = availability(c, key)
        for product in products:
            log = Records(OUT / product / "windows.jsonl")
            done = log.done("date")
            d, end = dt.date.fromisoformat(start or START[product]), dt.date.fromisoformat(avail[product])
            n = 0
            while d <= end:
                ds = d.isoformat()
                if ds not in done:
                    r = c.get(API.format(key=key, product=product, date=ds))
                    if r.status_code != 200 or "Invalid" in r.text[:200]:
                        log.add({"date": ds, "status": r.status_code, "fetched": now(), "error": r.text[:200].replace(key, "<MAP_KEY>")})
                    else:
                        rows = rows_of(r.text)
                        path = OUT / product / f"{d.year}.csv"
                        new = not path.exists()
                        with path.open("a", newline="") as f:
                            w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
                            if new:
                                w.writeheader()
                            w.writerows(rows)
                        log.add({"date": ds, "status": 200, "fetched": now(), "rows": len(rows), "sha256": sha256(r.content)})
                        n += 1
                d += dt.timedelta(days=5)
            stats[product] = {"windows_fetched": n, "available_to": avail[product]}
            print(product, stats[product], flush=True)
    return stats


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--product", action="append")
    ap.add_argument("--start")
    a = ap.parse_args()
    print(crawl(a.product or ["MODIS_SP", "VIIRS_SNPP_SP"], a.start))
