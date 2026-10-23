"""Deep-time strip (LAYERS-PLAN §7 step 3): GVP Holocene eruptions with NOAA NCEI HazEL impacts, as `<version>/deeptime.json`.

One file for all 24 volcanoes (contracts/schemas/deeptime.schema.json). Every GVP eruption keeps GVP's date
uncertainty fields; a HazEL event (deaths, damage, houses destroyed) is attached to the GVP eruption whose dates
contain it (one eruption can hold several, e.g. Hibok-hibok 1948-1953), or listed under `otherImpacts` when none does (for example a lahar years after the eruption). HazEL
figures are compiled estimates, so each one keeps its NCEI event link.

    uv run python -m plumes.deeptime            # build into data/build/deeptime-preview.json and print the checks
    uv run python -m plumes.deeptime --fixture  # (re)write contracts/fixtures/data/v0/deeptime.json from the same inputs
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

from plumes.sources import duplicates, reject

SOURCE_ID = "noaa-hazel-volcanoes-ph"
GVP_ID = "gvp-eruptions-ph"
SATELLITE_ERA_START = "2000-01-01"
HAZEL_EVENT_URL = "https://www.ngdc.noaa.gov/hazel/view/hazards/volcano/event-more-info/{id}"
GVP_VOLCANO_URL = "https://volcano.si.edu/volcano.cfm?vn={n}"


def lt(en: str, ja: str) -> dict:
    return {"en": en, "ja": ja}


# NCEI's own definitions (the HazEL event page help, read 2026-10-22).
AGENTS = {
    "A": lt("Avalanche (debris and landslides)", "岩屑なだれ・地すべり"),
    "E": lt("Electrical (lightning)", "雷"),
    "F": lt("Floods (and jökulhlaups)", "洪水"),
    "G": lt("Gas", "火山ガス"),
    "I": lt("Indirect deaths (disease, starvation, exposure)", "間接的な死(病気・飢餓・寒さなど)"),
    "L": lt("Lava flows", "溶岩流"),
    "M": lt("Mudflows (lahars)", "泥流(ラハール)"),
    "m": lt("Secondary (post-eruption) mudflows", "噴火後の二次泥流"),
    "P": lt("Pyroclastic flows, surges and direct blasts", "火砕流・火砕サージ・爆風"),
    "S": lt("Seismic or volcanic earthquake", "火山性地震"),
    "T": lt("Tephra (ash, bombs, lapilli, steam blasts)", "テフラ(火山灰・火山弾・火山礫・水蒸気爆発)"),
    "W": lt("Waves or tsunami", "波・津波"),
}
ORDERS = {
    "people": {
        "1": lt("few (about 1 to 50)", "少数(約1〜50)"),
        "2": lt("some (about 51 to 100)", "数十(約51〜100)"),
        "3": lt("many (about 101 to 1,000)", "多数(約101〜1,000)"),
        "4": lt("very many (over 1,000)", "非常に多数(1,000超)"),
    },
    "damage": {
        "1": lt("limited (under about US$1 million)", "限定的(約100万米ドル未満)"),
        "2": lt("moderate (about US$1 to 5 million)", "中程度(約100万〜500万米ドル)"),
        "3": lt("severe (about US$5 to 25 million)", "深刻(約500万〜2,500万米ドル)"),
        "4": lt("extreme (about US$25 million or more)", "甚大(約2,500万米ドル以上)"),
    },
}

# HazEL field -> read-model field. "Total" figures include secondary effects (tsunami, earthquake) per NCEI.
FIELDS = [
    ("deaths", "deaths"), ("deathsAmountOrder", "deathsOrder"), ("deathsTotal", "deathsTotal"), ("deathsAmountOrderTotal", "deathsTotalOrder"),
    ("injuries", "injuries"), ("injuriesAmountOrder", "injuriesOrder"), ("injuriesTotal", "injuriesTotal"), ("injuriesAmountOrderTotal", "injuriesTotalOrder"),
    ("missing", "missing"), ("missingAmountOrder", "missingOrder"), ("missingTotal", "missingTotal"), ("missingAmountOrderTotal", "missingTotalOrder"),
    ("damageMillionsDollars", "damageMusd"), ("damageAmountOrder", "damageOrder"), ("damageMillionsDollarsTotal", "damageMusdTotal"),
    ("damageAmountOrderTotal", "damageTotalOrder"), ("housesDestroyed", "housesDestroyed"), ("housesDestroyedAmountOrder", "housesDestroyedOrder"),
    ("housesDestroyedTotal", "housesDestroyedTotal"), ("housesDestroyedAmountOrderTotal", "housesDestroyedTotalOrder"),
]


# ---------------------------------------------------------------- archivekit hook

def hazel_items(path: Path) -> list[dict]:
    return json.loads(Path(path).read_text())["items"]


def check_hazel(path: Path, source: dict[str, Any]) -> list[str]:
    """Reject (SchemaError) a HazEL page that is incomplete or holds rows that are not Philippine volcano events."""
    try:
        d = json.loads(Path(path).read_text())
        items = d["items"]
        if not isinstance(items, list) or not all(isinstance(it, dict) for it in items):
            raise TypeError("items is not a list of objects")
    except (ValueError, KeyError, TypeError) as e:
        reject([f"not a HazEL page: {e}"])
    probs = []
    if d.get("totalPages") != 1 or d.get("totalItems") != len(items):
        probs.append(f"paged answer: {len(items)} items of {d.get('totalItems')} in {d.get('totalPages')} pages")
    if not 30 <= len(items) <= 200:
        probs.append(f"{len(items)} items (expected 30-200)")
    for it in items:
        n, y = it.get("volcanoLocationNewNum"), it.get("year")
        if not isinstance(n, int) or not 271000 <= n <= 274999:
            probs.append(f"event {it.get('id')}: volcano number {n!r} outside the Philippine range")
        if not isinstance(y, int) or not -12000 <= y <= 2100:
            probs.append(f"event {it.get('id')}: year {y!r}")
        for f in ("deaths", "deathsTotal", "injuries", "missing", "housesDestroyed", "damageMillionsDollars"):
            # bool is an int; inf >= 0 holds, so finiteness is checked too (audit A1)
            if it.get(f) is not None and not (isinstance(it[f], int | float) and not isinstance(it[f], bool) and math.isfinite(it[f]) and it[f] >= 0):
                probs.append(f"event {it.get('id')}: {f} {it[f]!r}")
    probs += duplicates(it.get("id") for it in items)  # a repeated event would attach its impacts several times
    reject(probs)  # SchemaError: the kit rejects the page and tries the next link (audit P2)
    return []


# ---------------------------------------------------------------- dates

def _int(x) -> int | None:
    return int(x) if x not in (None, "", "0") else None


def iso_partial(y: int, m: int | None, d: int | None) -> str:
    s = str(y)  # GVP and HazEL write BCE years as negative numbers without a year 0: -3580 is 3580 BCE
    if m:
        s += f"-{m:02d}"
        if d:
            s += f"-{d:02d}"
    return s


def _gvp_window(e: dict) -> tuple[tuple, tuple, int]:
    """(lo, hi, year uncertainty) for a GVP eruption; tuples are (year, month, day) with missing parts widened."""
    sy, sm, sd = int(e["StartDateYear"]), _int(e["StartDateMonth"]), _int(e["StartDateDay"])
    ey, em, ed = _int(e["EndDateYear"]) if e["EndDateYear"] else None, _int(e["EndDateMonth"]), _int(e["EndDateDay"])
    unc = _int(e["StartDateYearUncertainty"]) or 0
    lo = (sy, sm or 1, sd or 1)
    # no end date: a month's grace, since HazEL dates the peak of activity (deaths, damage), not the start
    grace = (sy, min(12, sm + 1), 31) if sm else (sy, 12, 31)
    hi = (ey, em or 12, ed or 31) if ey is not None else grace
    return lo, hi, unc


def _contains(e: dict, y: int, m: int | None, d: int | None) -> bool:
    lo, hi, unc = _gvp_window(e)
    if unc:
        return lo[0] - unc <= y <= hi[0] + unc
    h_lo, h_hi = (y, m or 1, d or 1), (y, m or 12, d or 31)
    return lo <= h_hi and h_lo <= hi


# ---------------------------------------------------------------- build

def impact_of(it: dict) -> dict:
    out = {"id": f"hazel-{it['id']}", "date": iso_partial(it["year"], it.get("month"), it.get("day"))}
    if it.get("vei") is not None:
        out["vei"] = it["vei"]
    for src, dst in FIELDS:
        v = it.get(src)
        if v is not None:
            out[dst] = v if not dst.endswith("Order") else int(v)
    if it.get("agent"):
        out["agents"] = [a for a in it["agent"].split(",") if a]
    if it.get("tsunamiEventId"):
        out["tsunami"] = True
    if it.get("earthquakeEventId"):
        out["earthquake"] = True
    out["url"] = HAZEL_EVENT_URL.format(id=it["id"])
    return out


def eruption_of(e: dict, n: int) -> dict:
    sy = int(e["StartDateYear"])
    out = {"id": f"gvp-{e['Eruption_Number']}",
           "start": iso_partial(sy, _int(e["StartDateMonth"]), _int(e["StartDateDay"])),
           "end": iso_partial(int(e["EndDateYear"]), _int(e["EndDateMonth"]), _int(e["EndDateDay"])) if e["EndDateYear"] else None,
           "certainty": "uncertain" if e["Activity_Type"].startswith("Uncertain") else "confirmed",
           "vei": int(e["ExplosivityIndexMax"]) if e["ExplosivityIndexMax"] else None}
    for col, key, conv in (("StartDateYearUncertainty", "startYearUncertainty", int), ("StartDateDayUncertainty", "startDayUncertainty", int),
                           ("StartDateYearModifier", "startYearModifier", str), ("ExplosivityIndexModifier", "veiModifier", str),
                           ("StartEvidenceMethod", "evidence", str)):
        if e[col]:
            out[key] = conv(e[col])
    out["url"] = GVP_VOLCANO_URL.format(n=n)
    return out


def _year(iso: str) -> int:
    return -int(iso[1:].split("-")[0]) if iso.startswith("-") else int(iso.split("-")[0])


def build_model(hdr: dict, vols: list[dict], gvp_e: list[dict], hazel: list[dict], provenance: dict) -> tuple[dict, list[dict]]:
    """Return (deeptime read model, unmatched HazEL rows outside the 24 volcanoes)."""
    by_num: dict[int, list[dict]] = {}
    for e in gvp_e:
        if e["StartDateYear"]:
            by_num.setdefault(int(e["Volcano_Number"]), []).append(e)
    num_to_id = {v["gvpNumber"]: v["id"] for v in vols if v["gvpNumber"]}
    attached: dict[str, list[dict]] = {}
    other: dict[str, list[dict]] = {}
    outside = []
    for it in sorted(hazel, key=lambda i: (i["year"], i.get("month") or 0, i.get("day") or 0)):
        n = it["volcanoLocationNewNum"]
        if n not in num_to_id:
            outside.append(it)
            continue
        y, m, d = it["year"], it.get("month"), it.get("day")
        cands = [e for e in by_num.get(n, []) if _contains(e, y, m, d)]
        if not cands:  # same start year and the only GVP eruption that year: accept (HazEL dates the peak)
            same = [e for e in by_num.get(n, []) if int(e["StartDateYear"]) == y]
            cands = same if len(same) == 1 else []
        if cands:
            best = max(cands, key=lambda e: _gvp_window(e)[0])
            attached.setdefault(best["Eruption_Number"], []).append(impact_of(it))
        else:
            other.setdefault(num_to_id[n], []).append(impact_of(it))
    volcanoes = []
    for v in vols:
        n = v["gvpNumber"]
        ers = []
        for e in by_num.get(n, []) if n else []:
            er = eruption_of(e, n)
            if e["Eruption_Number"] in attached:
                er["impacts"] = attached[e["Eruption_Number"]]
            ers.append(er)
        ers.sort(key=lambda e: (_year(e["start"]), e["start"]))
        volcanoes.append({"id": v["id"], "gvpNumber": n, "eruptions": ers, "otherImpacts": other.get(v["id"], [])})
    years = [_year(e["start"]) for vv in volcanoes for e in vv["eruptions"]]
    doc = {**hdr, "kind": "deeptime", "span": {"startYear": min(years) if years else 2000, "satelliteEraStart": SATELLITE_ERA_START},
           "glossary": {"agents": AGENTS, "orders": ORDERS},
           "notes": {"impacts": lt("Deaths, injuries, damage and houses destroyed are NOAA NCEI's compiled estimates from published reports, not official counts; "
                                   "each links to its NCEI event page. 'Total' figures include secondary effects such as tsunamis.",
                                   "死者・負傷者・被害額・全壊家屋はNOAA NCEIが文献から集めた推定値で、公式の集計ではない。各値はNCEIの事象ページにリンクする。"
                                   "「合計」は津波などの二次的な影響を含む。"),
                     "dates": lt("Dates and their uncertainty are GVP's. Radiocarbon dates carry ± years; '?' marks an uncertain year.",
                                 "日付とその不確かさはGVPによる。放射性炭素年代には±年が付き、「?」は不確かな年を示す。")},
           "volcanoes": volcanoes, "provenance": provenance}
    return doc, outside


def run_checks(doc: dict) -> list[dict]:
    res = []

    def check(name, ok, detail=""):
        res.append({"check": name, "passed": bool(ok), "detail": detail})

    vols = {v["id"]: v for v in doc["volcanoes"]}

    def deaths(vid: str, year: str) -> int | None:
        imp = [i for e in vols[vid]["eruptions"] for i in e.get("impacts", []) if i["date"].startswith(year)]
        return imp[0].get("deaths") if imp else None

    check("deep time: 24 volcanoes", len(vols) == 24, str(len(vols)))
    for vid, year, want in (("taal", "1911", 1335), ("taal", "1965", 355), ("mayon", "1814", 1200), ("mayon", "1993", 75),
                             ("pinatubo", "1991", 350), ("hibok-hibok", "1951", 500)):
        got = deaths(vid, year)
        check(f"deep time: {vid} {year}: a GVP eruption carries HazEL deaths {want}", got == want, str(got))
    n_imp = sum(len(e.get("impacts", [])) for v in vols.values() for e in v["eruptions"]) + sum(len(v["otherImpacts"]) for v in vols.values())
    check("deep time: at least 40 HazEL events placed", n_imp >= 40, str(n_imp))
    size = len(json.dumps(doc, separators=(",", ":"), ensure_ascii=False).encode())
    check("deep time: file under 100 kB", size < 100_000, f"{size / 1000:.1f} kB")
    return res


def write(v_dir: Path, hdr: dict, vols: list[dict], gvp_e: list[dict], hazel_path: Path, provenance: dict) -> list[dict]:
    """Write <version>/deeptime.json and return its checks (merged into the manifest by plumes.readmodels)."""
    doc, _ = build_model(hdr, vols, gvp_e, hazel_items(hazel_path), provenance)
    (v_dir / "deeptime.json").write_text(json.dumps(doc, separators=(",", ":"), ensure_ascii=False))
    return run_checks(doc)


if __name__ == "__main__":
    import datetime as dt
    import sys

    from plumes.contracts import errors
    from plumes.paths import BUILD, RAW, REPO
    from plumes.readmodels import file_provenance, load_volcanoes, provenance

    fixture = "--fixture" in sys.argv
    with open(RAW / "gvp" / "gvp-eruptions-ph.csv", newline="", encoding="utf-8") as f:
        gvp = list(csv.DictReader(f))
    hdr = ({"schemaVersion": "1", "dataVersion": "v0", "dataAsOf": "2026-10-21", "generatedAt": "2026-10-22T00:00:00Z", "fixture": True} if fixture else
           {"schemaVersion": "1", "dataVersion": "v0", "dataAsOf": dt.date.today().isoformat(), "generatedAt": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")})
    doc, outside = build_model(hdr, load_volcanoes(), gvp, hazel_items(RAW / "hazel" / f"{SOURCE_ID}.json"), provenance([GVP_ID, SOURCE_ID], file_provenance()))
    if fixture:
        out = REPO / "contracts" / "fixtures" / "data" / "v0" / "deeptime.json"
        out.write_text(json.dumps(doc, separators=(",", ":"), ensure_ascii=False) + "\n")
    else:
        BUILD.mkdir(parents=True, exist_ok=True)
        (BUILD / "deeptime-preview.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False))
    print(json.dumps({"schemaErrors": errors(doc)[:5], "outside24": [f"{i['name']} {i['year']}" for i in outside],
                      "failed": [c for c in run_checks(doc) if not c["passed"]]}, indent=1, ensure_ascii=False))
