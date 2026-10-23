"""Tokyo VAAC advisories for Philippine volcanoes, 2010 onward (JMA open archive; cite the source).

The yearly list pages link every advisory; Philippine ones carry the GVP number in the file name
(`<YYYYMMDD>_<GVP number>00_<seq>_Text.html`, e.g. Taal 27307000). Polite: <= 1 request/s, resumable.

    uv run python -m plumes.crawl.vaac [--since 2010 | auto]
"""

from __future__ import annotations

import argparse
import datetime as dt
import re

from plumes.crawl.records import PARSE_FAILED, Records, now, sha256
from plumes.http import Polite
from plumes.parse import parse_vaac
from plumes.paths import RAW

BASE = "https://ds.data.jma.go.jp/svd/vaac/data/"
OUT = RAW / "vaac-tokyo-advisories"
ANY = re.compile(r"_Text\.html")  # any advisory link: Tokyo VAAC issues them nearly every day, so a list without one is not a list
PH = re.compile(r"TextData/(\d{4})/(\d{8})_(27[1-4]\d{3})(\d{2})_(\d{4})_Text\.html")


def refresh_from(today: dt.date | None = None) -> int:
    """First year whose list is re-read: last year's too in January, so late-December advisories are listed (audit M7)."""
    today = today or dt.date.today()
    return today.year - 1 if today.month == 1 else today.year


def crawl(since: int = 2010, refresh_lists_from: int | None = None) -> dict:
    lists, pages = Records(OUT / "lists.jsonl"), Records(OUT / "pages.jsonl")
    listed = {r["year"]: r for r in lists}
    done = pages.done()
    this_year = dt.date.today().year
    refresh = refresh_lists_from or refresh_from()
    bad_lists: list[int] = []
    with Polite() as c:
        urls = []
        for y in range(min(since, refresh), this_year + 1):
            # a year whose list did not answer as a list is read again (audit P6); before, a 404 stored urls [] for good
            if y not in listed or listed[y].get("status") != 200 or y >= refresh:
                r = c.get(f"{BASE}Archives/{y}_vaac_list.html")
                ok = r.status_code == 200 and bool(ANY.search(r.text))
                status = r.status_code if r.status_code != 200 or ok else PARSE_FAILED
                found = sorted({m.group(0) for m in PH.finditer(r.text)}) if ok else []
                if not ok:
                    bad_lists.append(y)
                    prev = listed.get(y, {}).get("urls", [])  # keep what an earlier good read listed
                    found = prev
                listed[y] = {"year": y, "status": status, "fetched": now(), "urls": found}
                lists.add(listed[y])
            urls += [BASE + u for u in listed[y]["urls"]]
        gave_up = pages.given_up()
        todo = [u for u in urls if u not in done and u not in gave_up]
        print(f"{len(urls)} Philippine advisories listed, {len(todo)} to fetch", flush=True)
        unparsed = 0
        for u in todo:
            r = c.get(u)
            m = PH.search(u)
            status = r.status_code
            if status == 200 and not parse_vaac(r.text)["dtg"]:  # not an advisory: fetched again next run
                status, unparsed = PARSE_FAILED, unparsed + 1
            pages.add({"url": u, "gvp": int(m.group(3)), "date": m.group(2), "status": status, "fetched": now(),
                       "sha256": sha256(r.content), "html": r.text if status == 200 else ""})
    if bad_lists or unparsed:
        print(f"::warning title=VAAC lists or advisories not read::year lists {bad_lists} did not answer as lists (read again next run); "
              f"{unparsed} advisories not parsed", flush=True)
    return {"listed": len(urls), "fetched": len(todo), "bad_lists": bad_lists, "unparsed": unparsed, "requests": c.requests}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2010", help="first year, or auto (the years whose lists are refreshed)")
    s = ap.parse_args().since
    print(crawl(refresh_from() if s == "auto" else int(s)))
