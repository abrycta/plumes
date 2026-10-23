"""PHIVOLCS WordPress bulletins: the English prose bulletins, 2017-09 onward (DECISIONS S1).

The post list comes from the WordPress core sitemaps. Filipino posts and the 2021-10+ "Summary of 24hr Observation"
pages (empty shells; the data live in LAVA) are skipped. Each record keeps the extracted `entry-content` block and the
sha256 of the full page, not the 82 kB page. Polite: <= 1 request/s, resumable.

    uv run python -m plumes.crawl.wp            # list + crawl everything not yet fetched
    uv run python -m plumes.crawl.wp --limit 20
"""

from __future__ import annotations

import argparse
import re
import xml.etree.ElementTree as ET

from plumes.crawl.records import Records, now, sha256
from plumes.http import Polite
from plumes.paths import RAW

BASE = "https://www.phivolcs.dost.gov.ph/"
OUT = RAW / "phivolcs-bulletins"
VOLCANO = r"taal|mayon|kanlaon|bulusan|pinatubo|hibok|biliran|didicas|babuyan|cagua|iraya|smith|matutum|parker|ragang|musuan|camiguin|banahaw|iriga|isarog|makaturing|leonard|cabalian|bud-dajo"
FILIPINO = r"bulkang|ika-|alas-|buod|pang-araw|obserbasyon|abiso|paunawa|ulat"
KIND = r"bulletin|advisory|update|eruption|lowering|raising|alert"
NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def _recent(slug: str) -> bool:
    years = re.findall(r"(20\d\d)", slug)  # any 20xx year, so the crawl keeps matching from 2030 (audit L3)
    return bool(years) and int(years[-1]) >= 2017


def wanted(url: str) -> bool:
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    if not re.search(VOLCANO, slug) or not re.search(KIND, slug) or re.search(FILIPINO, slug) or "summary" in slug:
        return False
    return _recent(slug)


def unknown_volcano(url: str) -> bool:
    """A recent English volcano bulletin whose volcano is not in VOLCANO: reported, so the list is extended (audit L3)."""
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    return ("volcano" in slug and not re.search(VOLCANO, slug) and bool(re.search(KIND, slug)) and not re.search(FILIPINO, slug)
            and "summary" not in slug and _recent(slug))


def list_posts(c: Polite) -> list[tuple[str, str]]:
    idx = ET.fromstring(c.get(BASE + "wp-sitemap.xml").content)
    maps = [e.text for e in idx.findall("s:sitemap/s:loc", NS) if "posts-post" in e.text]
    out, unknown = [], []
    for m in maps:
        for u in ET.fromstring(c.get(m).content).findall("s:url", NS):
            loc, lastmod = u.findtext("s:loc", namespaces=NS), u.findtext("s:lastmod", namespaces=NS)
            if wanted(loc):
                out.append((loc, lastmod))
            elif unknown_volcano(loc):
                unknown.append(loc)
    if unknown:
        print(f"::warning title=PHIVOLCS bulletins for an unknown volcano::{len(unknown)} posts, e.g. {unknown[:3]}; add the volcano to crawl/wp.py VOLCANO", flush=True)
    return out


def extract(html: str) -> str:
    i = html.find("entry-content")
    if i < 0:
        return ""
    i = html.find(">", i) + 1
    j = html.find("sharedaddy", i)
    j = html.rfind("<div", i, j) if j > 0 else i + 40000
    return html[i:j].strip()


def crawl(limit: int | None = None) -> dict:
    rec = Records(OUT / "pages.jsonl")
    done = rec.done()
    with Polite() as c:
        posts = list_posts(c)
        (OUT / "list.tsv").write_text("".join(f"{u}\t{m}\n" for u, m in posts))
        todo = [(u, m) for u, m in posts if u not in done][:limit]
        print(f"{len(posts)} English bulletins listed, {len(done)} already fetched, {len(todo)} to fetch", flush=True)
        for k, (u, m) in enumerate(todo):
            r = c.get(u)
            body = r.text if r.status_code == 200 else ""
            rec.add({"url": u, "lastmod": m, "status": r.status_code, "fetched": now(), "sha256": sha256(r.content),
                     "bytes": len(r.content), "last_modified": r.headers.get("last-modified"), "entry": extract(body)})
            if k % 200 == 0:
                print(f"  {k}/{len(todo)} {r.status_code} {u}", flush=True)
    return {"listed": len(posts), "fetched": len(todo), "requests": c.requests}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    print(crawl(ap.parse_args().limit))
