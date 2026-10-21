"""Parsers for crawled pages: PHIVOLCS WordPress prose bulletins, PHIVOLCS-LAVA bulletins, Tokyo VAAC advisories.

Ported from the spike (spike/crawl/parse.py; parse rates in SPIKE-RESULTS Run 2). Every parser returns None for a
field it cannot find; a missing value is never guessed.
"""

from __future__ import annotations

import datetime as dt
import html as htmllib
import re

NUM = r"(\d[\d,]*)"
WORDS = {w: i for i, w in enumerate(["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"])}
VOLCANO_SLUGS = {"taal": "taal", "mayon": "mayon", "kanlaon": "kanlaon", "bulusan": "bulusan", "pinatubo": "pinatubo",
                 "hibok": "hibok-hibok", "biliran": "biliran", "didicas": "didicas", "babuyan": "babuyan-claro",
                 "cagua": "cagua", "iraya": "iraya", "smith": "smith", "matutum": "matutum", "parker": "parker",
                 "ragang": "ragang", "musuan": "musuan", "camiguin": "camiguin-de-babuyanes", "banahaw": "banahaw",
                 "iriga": "iriga", "isarog": "isarog", "makaturing": "makaturing", "leonard": "leonard-kniaseff",
                 "cabalian": "cabalian", "bud-dajo": "bud-dajo"}
MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"], 1)}


def text(html: str) -> str:
    html = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.DOTALL)
    t = htmllib.unescape(re.sub(r"<[^>]+>", " ", html))
    return re.sub(r"\s+", " ", t.replace("\xa0", " ")).strip()


def ival(s: str) -> int:
    return int(s.replace(",", ""))


def parse_day(s: str | None) -> str | None:
    """'01 May 2021', 'May 1, 2021' -> '2021-05-01'."""
    if not s:
        return None
    for fmt in ("%d %B %Y", "%B %d, %Y", "%B %d %Y"):
        try:
            return dt.datetime.strptime(s.strip(), fmt).date().isoformat()
        except ValueError:
            pass
    return None


# ---------- WordPress prose bulletins (2017-09 -> 2023) ----------

def wp_slug_meta(url: str) -> dict:
    """Volcano id, date and hour from a bulletin slug such as taal-volcano-bulletin-13-january-2020-8-00-a-m."""
    slug = url.rstrip("/").rsplit("/", 1)[-1].lower()
    vid = next((v for k, v in VOLCANO_SLUGS.items() if slug.startswith(k) or f"-{k}-" in slug), None)
    m = re.search(r"(\d{1,2})-(" + "|".join(MONTHS) + r")-(20\d\d)", slug) or re.search(r"(" + "|".join(MONTHS) + r")-(\d{1,2})-(20\d\d)", slug)
    day = None
    if m:
        a, b, y = m.groups()
        d, mon = (a, b) if a.isdigit() else (b, a)
        try:
            day = dt.date(int(y), MONTHS[mon], int(d)).isoformat()
        except ValueError:
            day = None
    h = re.search(r"(\d{1,2})-(\d{2})-(a-m|p-m|am|pm)", slug)
    hour = None
    if h:
        hour = int(h.group(1)) % 12 + (12 if h.group(3).startswith("p") else 0)
    return {"volcano": vid, "date": day, "hour": hour, "slug": slug}


def wp_fields(t: str) -> dict:
    f: dict = {}
    m = re.search(r"Alert Level (\d)", t, re.IGNORECASE)
    f["alert"] = int(m.group(1)) if m else None
    m = (re.search(r"(?:recorded|detected)\s+(?:a total of\s+)?(?:\w+\s+)?\(?(\d[\d,]*)\)?\s+(?:volcanic|low[- ]frequency|volcano-tectonic)?\s*(?:volcanic\s+)?earthquakes?", t, re.IGNORECASE)
         or re.search(r"(\w+) \((\d+)\) volcanic earthquakes?", t, re.IGNORECASE)
         or re.search(r"\b(no|zero|not detect any) volcanic earthquake", t, re.IGNORECASE))
    f["eq"] = (0 if m.group(1).lower() in ("no", "zero", "not detect any") else ival(m.groups()[-1])) if m else None
    m = re.search(r"\((\d+)\)\s+(?:episodes? of\s+)?(?:volcanic\s+)?tremor", t, re.IGNORECASE)
    f["tremor"] = int(m.group(1)) if m else None
    m = (re.search(r"(?:averaged|measured at|emission(?: rate)?(?: was)?(?: measured)?(?: at)?|flux of|was)\s+(?:an average of\s+)?" + NUM
                   + r"\s*(?:tonnes|tons)(?:\s*/\s*|\s+per\s+)day(?:.{0,40}?on\s+(\d{1,2}\s+\w+\s+\d{4}|\w+\s+\d{1,2},?\s+\d{4}))?", t, re.IGNORECASE)
         or re.search(NUM + r"\s*(?:tonnes|tons)(?:\s*/\s*|\s+per\s+)day", t, re.IGNORECASE))
    f["so2"] = ival(m.group(1)) if m else None
    f["so2_date"] = parse_day(m.group(2)) if m and m.lastindex and m.lastindex >= 2 else None
    m = re.search(r"(\d[\d,]*)\s*(?:meters|metres|m)\s+(?:tall|high)", t, re.IGNORECASE)
    f["plume_m"] = ival(m.group(1)) if m else None
    m = re.search(r"[^.]*(?:inflat|deflat|leveling|levelling|GPS|tilt|deformation)[^.]*\.", t, re.IGNORECASE)
    f["deform"] = m.group(0).strip()[:300] if m else None
    return f


def parse_wp(url: str, entry_html: str) -> dict | None:
    """One WordPress bulletin -> fields, or None for an empty shell."""
    t = text(entry_html)
    if len(t) < 200:
        return None
    return {**wp_slug_meta(url), **wp_fields(t), "url": url}


# ---------- PHIVOLCS-LAVA (2022 ->) ----------

LAVA_KEYS = ["Eruption", "Seismicity", "Acidity", "Temperature", "Sulfur Dioxide Flux", "Plume", "Ground Deformation"]


def parse_lava(html: str) -> dict | None:
    t = text(html)
    if "PARAMETERS" not in t:
        return None
    d = re.search(r"Date: (\d{1,2} \w+ \d{4})", t)
    a = re.search(r"ALERT LEVEL (\d)", t)
    par = t[t.find("PARAMETERS") + 10: t.find("Earthquake Location") if "Earthquake Location" in t else None]
    secs = {}
    for k in LAVA_KEYS:
        m = re.search(re.escape(k) + r"(?: Main Crater Lake)?\s*(.*?)(?=\s*(?:" + "|".join(map(re.escape, LAVA_KEYS)) + r")\b|$)", par)
        if m:
            secs[k] = m.group(1).strip()
    so2 = re.search(NUM + r" tonnes / day \((\d{1,2} \w+ \d{4})\)", secs.get("Sulfur Dioxide Flux", ""))
    seis = secs.get("Seismicity", "")
    eq = re.search(r"(\d+) volcanic earthquakes?", seis) or re.search(r"^(No|\d+)", seis)
    tremor = re.search(r"(\d+) (?:episodes? of )?volcanic tremor", seis)
    plume = re.search(r"(\d[\d,]*) meters", secs.get("Plume", ""))
    return {"date": parse_day(d.group(1)) if d else None, "alert": int(a.group(1)) if a else None,
            "eq": (0 if eq.group(1) == "No" else int(eq.group(1))) if eq else None,
            "tremor": int(tremor.group(1)) if tremor else None,
            "so2": ival(so2.group(1)) if so2 else None, "so2_date": parse_day(so2.group(2)) if so2 else None,
            "plume_m": ival(plume.group(1)) if plume else None, "deform": (secs.get("Ground Deformation") or None), "sections": list(secs)}


# ---------- Tokyo VAAC ----------

def parse_vaac(html: str) -> dict:
    t = text(html)
    dtg = re.search(r"DTG: (\d{8})/(\d{4})Z", t)
    nr = re.search(r"ADVISORY NR: (\d{4}/\d+)", t)
    vol = re.search(r"VOLCANO: (.*?) (\d{6})", t)
    obs = re.search(r"OBS VA CLD: (.*?)(?:FCST|RMK|NXT ADVISORY|$)", t)
    erup = re.search(r"ERUPTION DETAILS: (.*?)(?:OBS VA DTG|OBS VA CLD|$)", t)
    fls = [int(x) for x in re.findall(r"(?:SFC|FL\d{3})/FL(\d{3})", obs.group(1) if obs else "")]
    efl = [int(x) for x in re.findall(r"FL(\d{3})", erup.group(1) if erup else "")]
    iso = f"{dtg.group(1)[:4]}-{dtg.group(1)[4:6]}-{dtg.group(1)[6:]}T{dtg.group(2)[:2]}:{dtg.group(2)[2:]}:00Z" if dtg else None
    top, basis = (max(fls), "observed") if fls else ((max(efl), "reported") if efl else (None, "none"))
    return {"dtg": iso, "nr": nr.group(1) if nr else None, "gvp": int(vol.group(2)) if vol else None, "top_fl": top, "basis": basis,
            "not_identifiable": bool(obs and "NOT IDENTIFIABLE" in obs.group(1))}
