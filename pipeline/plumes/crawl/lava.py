"""PHIVOLCS-LAVA 24-hour bulletins, 2022 onward (DECISIONS S2).

**The id -> volcano map comes from LAVA's own archive search**, never from the URL path or page heading (the server does
not check them): `/bulletin/list-of-bulletin?vdId=<volcano>&type=bulletin&sdate=…&edate=…` returns a table of
(volcano, type, date, bid). This settles S2's open question for the history as well: every id since LAVA started is
attributed by the search, so no "fixed daily order" guess is needed, and the weekly delta only re-queries recent
windows (no daily list-page poll). The search returns at most 30 rows, so a full window is split in half.

    uv run python -m plumes.crawl.lava index [--since 2022-01-01 | auto]
    uv run python -m plumes.crawl.lava fetch [--limit N]
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys

from plumes.crawl.records import PARSE_FAILED, Records, now, sha256
from plumes.http import Polite
from plumes.parse import parse_lava
from plumes.paths import RAW

HOST = "https://wovodat.phivolcs.dost.gov.ph"
OUT = RAW / "phivolcs-lava-bulletins"
VDID = {"bulusan": 571, "hibok-hibok": 562, "kanlaon": 565, "mayon": 574, "pinatubo": 583, "taal": 580}
ROW = re.compile(r"<td>\s*([^<]+?)\s*</td>\s*<td>\s*([^<]+?)\s*</td>\s*<td>\s*(\d{4}-\d{2}-\d{2})\s*</td>\s*"
                 r"<td>\s*<a href=\"/bulletin/(activity-\w+)\?bid=(\d+)\"")
SPLIT_AT = 30  # the search returns at most 30 rows (newest first); a full window is split in half
FIRST = "2022-01-01"


def auto_since(rows, today: dt.date | None = None) -> str:
    """Delta window start: 7 days before the newest indexed bulletin date, and never later than 21 days ago, so a gap
    between successful runs (failures, a missing token) is re-indexed instead of lost (audit M7)."""
    today = today or dt.date.today()
    last = max((r["date"] for r in rows), default=None)
    if last is None:
        return FIRST
    return min(dt.date.fromisoformat(last) - dt.timedelta(days=7), today - dt.timedelta(days=21)).isoformat()


def search(c: Polite, vd: int, a: dt.date, b: dt.date) -> list[dict]:
    r = c.get(f"{HOST}/bulletin/list-of-bulletin", params={"vdId": vd, "type": "bulletin", "sdate": a.isoformat(), "edate": b.isoformat()})
    r.raise_for_status()
    rows = [{"volcano_label": m[0], "type": m[1], "date": m[2], "path": m[3], "bid": int(m[4])} for m in ROW.findall(r.text)]
    if len(rows) >= SPLIT_AT and a < b:
        mid = a + (b - a) / 2
        return search(c, vd, a, mid) + search(c, vd, mid + dt.timedelta(days=1), b)
    return rows


def unknown_volcanoes(html: str) -> dict[int, str]:
    """LAVA's volcano picker entries that VDID does not crawl (audit L3): reported, never fatal."""
    opts = {int(v): n.strip() for v, n in re.findall(r'<option value="(\d+)">([^<]+)</option>', html)}
    return {v: n for v, n in opts.items() if v not in VDID.values()}


def warn_unknown(c: Polite) -> None:
    try:
        r = c.get(f"{HOST}/bulletin/list-of-bulletin")
        new = unknown_volcanoes(r.text) if r.status_code == 200 else {}
    except Exception as e:  # the check is advisory; the crawl goes on
        print(f"::notice title=LAVA volcano list not checked::{e}", flush=True)
        return
    if new:
        print(f"::warning title=LAVA lists volcanoes not crawled::{new}; add them to crawl/lava.py VDID", flush=True)


def index(since: str = FIRST, until: str | None = None) -> dict:
    """Append (volcano, date, bid) rows for every volcano and 15-day window."""
    rec = Records(OUT / "index.jsonl")
    if since == "auto":
        since = auto_since(rec)
        print(f"  indexing from {since}", flush=True)
    a0, end = dt.date.fromisoformat(since), dt.date.fromisoformat(until) if until else dt.date.today()
    n = 0
    with Polite() as c:
        warn_unknown(c)
        for vid, vd in VDID.items():
            a = a0
            while a <= end:
                b = min(a + dt.timedelta(days=14), end)
                for row in search(c, vd, a, b):
                    rec.add({"volcano": vid, "vdId": vd, **row, "indexed": now()})
                    n += 1
                a = b + dt.timedelta(days=1)
            print(f"  {vid}: indexed to {end}", flush=True)
    return {"rows": n, "requests": c.requests, "days": (end - a0).days + 1}


# Taal and Mayon get a bulletin every day: no row for any volcano over this many days means the search answer changed
# (a new layout, a login or error page), not a quiet spell (audit P6).
EMPTY_INDEX_DAYS = 14


def require_rows(res: dict) -> None:
    """Fail the stage (soft: plumes.stage warns and files an issue) when a long index window listed nothing."""
    if res["rows"] == 0 and res["days"] >= EMPTY_INDEX_DAYS:
        sys.exit(f"LAVA search listed no bulletin for any volcano over {res['days']} days: the search answer changed")


def bid_map() -> dict[int, dict]:
    """bid -> index row (the latest one wins)."""
    return {r["bid"]: r for r in Records(OUT / "index.jsonl")}


def fetch(limit: int | None = None) -> dict:
    rec = Records(OUT / "pages.jsonl")
    done = rec.done("bid")
    gave_up = rec.given_up("bid")
    todo = [r for b, r in sorted(bid_map().items()) if b not in done and b not in gave_up][:limit]
    print(f"{len(todo)} LAVA bulletins to fetch", flush=True)
    unparsed = 0
    with Polite() as c:
        for k, r in enumerate(todo):
            url = f"{HOST}/bulletin/{r['path']}?bid={r['bid']}&lang=en"
            resp = c.get(url)
            status = resp.status_code
            if status == 200 and parse_lava(resp.text) is None:  # a 200 that is not a bulletin: fetched again next run
                status, unparsed = PARSE_FAILED, unparsed + 1
            rec.add({"bid": r["bid"], "volcano": r["volcano"], "date": r["date"], "url": url, "status": status,
                     "fetched": now(), "sha256": sha256(resp.content), "html": resp.text if status == 200 else ""})
            if k % 200 == 0:
                print(f"  {k}/{len(todo)} {resp.status_code} {url}", flush=True)
    if unparsed or gave_up:
        print(f"::warning title=LAVA bulletins not parsed::{unparsed} answered 200 but are not bulletins (retried next run); "
              f"{len(gave_up)} given up after repeated failures", flush=True)
    return {"fetched": len(todo), "unparsed": unparsed, "requests": c.requests}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["index", "fetch"])
    ap.add_argument("--since", default=FIRST, help="YYYY-MM-DD, or auto (from the last indexed date)")
    ap.add_argument("--until")
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    res = index(a.since, a.until) if a.step == "index" else fetch(a.limit)
    print(res)
    if a.step == "index":
        require_rows(res)
