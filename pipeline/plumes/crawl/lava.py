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

from plumes.crawl.records import Records, now, sha256
from plumes.http import Polite
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


def index(since: str = FIRST, until: str | None = None) -> dict:
    """Append (volcano, date, bid) rows for every volcano and 15-day window."""
    rec = Records(OUT / "index.jsonl")
    if since == "auto":
        since = auto_since(rec)
        print(f"  indexing from {since}", flush=True)
    a0, end = dt.date.fromisoformat(since), dt.date.fromisoformat(until) if until else dt.date.today()
    n = 0
    with Polite() as c:
        for vid, vd in VDID.items():
            a = a0
            while a <= end:
                b = min(a + dt.timedelta(days=14), end)
                for row in search(c, vd, a, b):
                    rec.add({"volcano": vid, "vdId": vd, **row, "indexed": now()})
                    n += 1
                a = b + dt.timedelta(days=1)
            print(f"  {vid}: indexed to {end}", flush=True)
    return {"rows": n, "requests": c.requests}


def bid_map() -> dict[int, dict]:
    """bid -> index row (the latest one wins)."""
    return {r["bid"]: r for r in Records(OUT / "index.jsonl")}


def fetch(limit: int | None = None) -> dict:
    rec = Records(OUT / "pages.jsonl")
    done = rec.done("bid")
    todo = [r for b, r in sorted(bid_map().items()) if b not in done][:limit]
    print(f"{len(todo)} LAVA bulletins to fetch", flush=True)
    with Polite() as c:
        for k, r in enumerate(todo):
            url = f"{HOST}/bulletin/{r['path']}?bid={r['bid']}&lang=en"
            resp = c.get(url)
            rec.add({"bid": r["bid"], "volcano": r["volcano"], "date": r["date"], "url": url, "status": resp.status_code,
                     "fetched": now(), "sha256": sha256(resp.content), "html": resp.text if resp.status_code == 200 else ""})
            if k % 200 == 0:
                print(f"  {k}/{len(todo)} {resp.status_code} {url}", flush=True)
    return {"fetched": len(todo), "requests": c.requests}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["index", "fetch"])
    ap.add_argument("--since", default=FIRST, help="YYYY-MM-DD, or auto (from the last indexed date)")
    ap.add_argument("--until")
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    print(index(a.since, a.until) if a.step == "index" else fetch(a.limit))
