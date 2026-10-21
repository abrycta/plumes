"""Tokyo VAAC advisories for Philippine volcanoes, 2010 onward (JMA open archive; cite the source).

The yearly list pages link every advisory; Philippine ones carry the GVP number in the file name
(`<YYYYMMDD>_<GVP number>00_<seq>_Text.html`, e.g. Taal 27307000). Polite: <= 1 request/s, resumable.

    uv run python -m plumes.crawl.vaac [--since 2010]
"""

from __future__ import annotations

import argparse
import datetime as dt
import re

from plumes.crawl.records import Records, now, sha256
from plumes.http import Polite
from plumes.paths import RAW

BASE = "https://ds.data.jma.go.jp/svd/vaac/data/"
OUT = RAW / "vaac-tokyo-advisories"
PH = re.compile(r"TextData/(\d{4})/(\d{8})_(27[1-4]\d{3})(\d{2})_(\d{4})_Text\.html")


def crawl(since: int = 2010, refresh_lists_from: int | None = None) -> dict:
    lists, pages = Records(OUT / "lists.jsonl"), Records(OUT / "pages.jsonl")
    listed = {r["year"]: r for r in lists}
    done = pages.done()
    this_year = dt.date.today().year
    refresh = refresh_lists_from or this_year
    with Polite() as c:
        urls = []
        for y in range(since, this_year + 1):
            if y not in listed or y >= refresh:
                r = c.get(f"{BASE}Archives/{y}_vaac_list.html")
                found = sorted({m.group(0) for m in PH.finditer(r.text)}) if r.status_code == 200 else []
                listed[y] = {"year": y, "status": r.status_code, "fetched": now(), "urls": found}
                lists.add(listed[y])
            urls += [BASE + u for u in listed[y]["urls"]]
        todo = [u for u in urls if u not in done]
        print(f"{len(urls)} Philippine advisories listed, {len(todo)} to fetch", flush=True)
        for u in todo:
            r = c.get(u)
            m = PH.search(u)
            pages.add({"url": u, "gvp": int(m.group(3)), "date": m.group(2), "status": r.status_code, "fetched": now(),
                       "sha256": sha256(r.content), "html": r.text if r.status_code == 200 else ""})
    return {"listed": len(urls), "fetched": len(todo), "requests": c.requests}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", type=int, default=2010)
    print(crawl(ap.parse_args().since))
