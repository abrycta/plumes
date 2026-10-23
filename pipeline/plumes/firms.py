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
# A stage's time budget: FIRMS answering "transaction limit" on every call would otherwise wait 3 x 10 min per window
# until the job's timeout cancels the whole run (audit A2). Windows not fetched stay undone and are asked again next run.
BUDGET_S = float(os.environ.get("FIRMS_BUDGET_MIN", "45")) * 60
MAX_LIMITED = 2  # consecutive windows still rate-limited after their retries
COLS = ["latitude", "longitude", "acq_date", "acq_time", "satellite", "instrument", "confidence", "frp", "daynight", "type"]


def availability(c: Polite, key: str) -> dict[str, str]:
    r = c.get(f"https://firms.modaps.eosdis.nasa.gov/api/data_availability/csv/{key}/ALL")
    return {row["data_id"]: row["max_date"] for row in csv.DictReader(io.StringIO(r.text))}


# Columns every FIRMS area CSV carries (SP and NRT; NRT has no `type`): a body without them is not an answer.
NEED = {"latitude", "longitude", "acq_date", "acq_time"}


class NotFirmsCsv(ValueError):
    """A 200 answer that is not a FIRMS CSV (a maintenance page, a JSON error, renamed columns): an error, never 0 rows."""


def rows_of(text: str) -> list[dict]:
    """Detections in a FIRMS answer: [] for an empty body or a header-only CSV (no detections); NotFirmsCsv otherwise."""
    text = text.strip()
    if not text:
        return []
    head = text.split("\n", 1)[0].strip()
    if not NEED.issubset(c.strip() for c in head.split(",")):
        raise NotFirmsCsv(f"not a FIRMS CSV: {head[:120]!r}")
    lines = [ln for ln in text.replace(head, "\n" + head).splitlines() if ln and ln != head]
    out = list(csv.DictReader([head, *lines]))
    for r in out:  # a body cut mid-row: missing fields (None) or extra ones (key None) mean a partial answer (audit A1)
        if None in r or None in r.values() or not _is_date(r["acq_date"]):
            raise NotFirmsCsv(f"incomplete FIRMS row: {','.join(str(v) for v in r.values())[:120]!r}")
    return out


def _is_date(s: str) -> bool:
    try:
        dt.date.fromisoformat(s)
    except (TypeError, ValueError):
        return False
    return True


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
    deadline = time.monotonic() + BUDGET_S
    limited = 0
    with Polite(min_interval=1.0) as c:
        avail = availability(c, key)
        for product in products:
            if product not in avail:  # a retired product (MODIS end of mission) or a renamed one: skip it, never crash the run
                print(f"::warning title=FIRMS product not listed::{product} is missing from FIRMS data_availability; its windows are kept as they are", flush=True)
                stats[product] = {"windows_fetched": 0, "available_to": None}
                continue
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
            n = bad = 0
            stopped = None
            while d <= end_:
                ds = d.isoformat()
                if ds not in done:
                    if time.monotonic() > deadline or limited >= MAX_LIMITED:
                        stopped = "rate-limited" if limited >= MAX_LIMITED else "time budget spent"
                        break
                    r = c.get(API.format(key=key, product=product, date=ds))
                    for _ in range(3):  # FIRMS weighs transactions by size: wait out the 10-minute window and retry
                        if "transaction limit" not in r.text[:200] or time.monotonic() + 600 > deadline:
                            break
                        time.sleep(600)
                        r = c.get(API.format(key=key, product=product, date=ds))
                    limited = limited + 1 if "transaction limit" in r.text[:200] else 0
                    rows, status = None, r.status_code
                    if r.status_code == 200 and "Invalid" not in r.text[:200]:
                        try:
                            rows = rows_of(r.text)
                        except NotFirmsCsv:
                            status = "not-csv"
                        if rows == [] and not r.text.strip():
                            rows, status = None, "empty"  # no header at all: provisional, fetched again (a no-detection answer is a header line)
                    if rows is None:
                        log.add({"date": ds, "status": status, "fetched": now(), "error": r.text[:200].replace(key, "<MAP_KEY>")})
                        bad += 1
                    else:
                        _write_window(product, d, rows, replace=latest.get(ds, {}).get("status") == 200)
                        log.add({"date": ds, "to": _end(d).isoformat(), "status": 200, "fetched": now(), "rows": len(rows), "sha256": sha256(r.content)})
                        n += 1
                d += dt.timedelta(days=WINDOW_DAYS)
            if stopped:  # the windows left are not logged as done, so the next run asks for them again
                print(f"::warning title=FIRMS stopped early::{product}: {stopped} at window {ds}; the remaining windows are fetched next run", flush=True)
            if bad:  # logged as errors (not done), so the next run asks again
                print(f"::warning title=FIRMS answers not usable::{product}: {bad} windows answered with an error, an empty body or not a FIRMS CSV", flush=True)
            stats[product] = {"windows_fetched": n, "windows_failed": bad, "available_to": avail[product]} | ({"stopped": stopped} if stopped else {})
            print(product, stats[product], flush=True)
    return stats


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--product", action="append")
    ap.add_argument("--start")
    ap.add_argument("--end")
    a = ap.parse_args()
    print(crawl(a.product or ["MODIS_SP", "VIIRS_SNPP_SP"], a.start, a.end))
