"""DSWD DROMIC situation reports (Taal 2020 at M1): grand totals of affected and displaced persons per report.

The .docx files are parsed and discarded; only the extracted rows and each file's sha256 are kept (DATA-PLAN §1).
Report #1 is a .doc and is not parsed (DECISIONS S3: hand entry, recorded in plumes/data/dromic_manual.csv if needed).

    uv run python -m plumes.crawl.dromic [--event taal-2020]
"""

from __future__ import annotations

import argparse
import io
import re

import docx

from plumes.crawl.records import Records, now, sha256
from plumes.http import Polite
from plumes.paths import RAW

OUT = RAW / "dswd-dromic-reports"
EVENTS = {"taal-2020": "https://dromic.dswd.gov.ph/taal-volcano-phreatic-eruption-13-jan-2020/"}
LINK = re.compile(r'href="(https://dromic\.dswd\.gov\.ph/wp-content/uploads/[^"]+?Report[^"]*?\.docx?)"', re.IGNORECASE)


def num(s: str | None) -> int | None:
    s = (s or "").replace(",", "").strip()
    return int(s) if s.isdigit() else None


def grand_total(tbl) -> list[str] | None:
    for r in tbl.rows:
        cells = [c.text.strip() for c in r.cells]
        if cells and cells[0].upper().startswith("GRAND TOTAL"):
            return cells[2:]
    return None


def parse_docx(data: bytes) -> dict:
    """Grand totals: affected persons, persons inside evacuation centres (now, cumulative), outside (now, cumulative)."""
    d = docx.Document(io.BytesIO(data))
    out: dict = {}
    for tbl in d.tables:
        hdr = " ".join(c.text for r in tbl.rows[:4] for c in r.cells).upper()
        gt = grand_total(tbl)
        if not gt:
            continue
        if "AFFECTED" in hdr and "affected_persons" not in out:
            out["affected_families"], out["affected_persons"] = num(gt[-2]), num(gt[-1])
        elif "INSIDE EC" in hdr and "inside_persons_now" not in out:
            out.update(inside_ecs_now=num(gt[1]), inside_persons_cum=num(gt[4]), inside_persons_now=num(gt[5]))
        elif "OUTSIDE EC" in hdr and "outside_persons_now" not in out:
            out.update(outside_persons_cum=num(gt[2]), outside_persons_now=num(gt[3]))
    return out


def report_meta(url: str) -> dict:
    name = url.rsplit("/", 1)[-1]
    n = re.search(r"Report-(?:No-)?(\d+)", name, re.IGNORECASE)
    m = re.search(r"as-of-(\d{1,2})-([A-Za-z]+)-(\d{4})", name)
    return {"report": int(n.group(1)) if n else None, "as_of_text": " ".join(m.groups()) if m else None, "file": name}


def crawl(event: str = "taal-2020") -> dict:
    rec = Records(OUT / f"{event}.jsonl")
    done = rec.done()
    with Polite() as c:
        page = c.get(EVENTS[event])
        links = sorted(set(LINK.findall(page.text)))
        todo = [u for u in links if u not in done]
        print(f"{len(links)} report files linked, {len(todo)} to fetch", flush=True)
        for u in todo:
            r = c.get(u)
            row = {"url": u, "event": event, "status": r.status_code, "fetched": now(), "sha256": sha256(r.content), "bytes": len(r.content), **report_meta(u)}
            if r.status_code == 200 and u.lower().endswith(".docx"):
                try:
                    row["totals"] = parse_docx(r.content)
                except Exception as e:  # a malformed file is recorded, not fatal
                    row["error"] = repr(e)[:200]
            rec.add(row)
    return {"linked": len(links), "fetched": len(todo), "requests": c.requests}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--event", default="taal-2020")
    print(crawl(ap.parse_args().event))
