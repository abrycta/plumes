"""Materialise the read models (contracts/) from the fetched, crawled and reduced tables (DATA-PLAN §2 steps 6-8).

Writes data/build/site/v<N>/ (immutable) and, only if every check passes, data/build/site/latest.json. A failed
check leaves latest.json untouched, so the previous version keeps being served (archiving standard §5).

    uv run python -m plumes.readmodels --version 1 --as-of 2026-10-22
"""

from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import glob
import gzip
import hashlib
import json
import math
import re
import shutil
import subprocess

import yaml

from plumes import omi, run_b, thermal_n20
from plumes.contracts import errors
from plumes.crawl.records import Records
from plumes.parse import parse_lava, parse_vaac, parse_wp, wp_slug_meta
from plumes.paths import BUILD, CROSSWALK, DATA, RAW, REGISTRY, TABLES

SPAN_START = "2000-01-01"
REG = {e["id"]: e for e in yaml.safe_load(REGISTRY.read_text())["sources"]}
WP_HOME = "https://www.phivolcs.dost.gov.ph/"


def lt(en: str, ja: str) -> dict:
    return {"en": en, "ja": ja}


def km(lat1, lon1, lat2, lon2) -> float:
    p = math.pi / 180
    a = math.sin((lat2 - lat1) * p / 2) ** 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(a))


def rows(path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fnum(x):
    return None if x in (None, "") else float(x)


def days_between(a: str, b: str) -> int:
    return (dt.date.fromisoformat(b) - dt.date.fromisoformat(a)).days


# ---------------------------------------------------------------- inputs

def load_volcanoes() -> list[dict]:
    gvp = {int(r["Volcano_Number"]): r for r in rows(RAW / "gvp" / "gvp-volcanoes-ph.csv")}
    out = []
    for c in rows(CROSSWALK):
        n = int(c["gvp_number"]) if c["gvp_number"] else None
        g = gvp.get(n)
        out.append({"id": c["id"], "name": lt(c["phivolcs_name"], c["name_ja"]), "gvpNumber": n, "gvpName": c["gvp_name"] or None,
                    "lat": float(g["Latitude"]) if g else float(c["lat"]), "lon": float(g["Longitude"]) if g else float(c["lon"]),
                    "elevationM": float(g["Elevation"]) if g and g["Elevation"] else None,
                    "type": g["Primary_Volcano_Type"] if g else None, "observatory": c["observatory"] == "true", "coverage": c["coverage"],
                    "coordSource": c["coord_source"]})
    return out


def gvp_date(r, pre="StartDate") -> str | None:
    y, m, d = r[pre + "Year"], r[pre + "Month"], r[pre + "Day"]
    if not y:
        return None
    s = y if int(y) >= 0 else str(y)
    if m and m != "0":
        s += f"-{int(m):02d}"
        if d and d != "0":
            s += f"-{int(d):02d}"
    return s


def load_bulletins() -> dict[str, dict[str, list]]:
    """volcano -> date -> schema row. One row a day, all fields from one page (each value cites its own page): LAVA when it
    exists, else the latest WordPress page that day reporting an alert level, else the latest page that day."""
    out: dict[str, dict[str, tuple]] = collections.defaultdict(dict)
    for r in Records(RAW / "phivolcs-bulletins" / "pages.jsonl").latest().values():
        if r.get("status") != 200:
            continue
        p = parse_wp(r["url"], r["entry"])
        if not p or not p["volcano"] or not p["date"]:
            continue
        # latest page that reports an alert level, else the latest page; the English edition over the Filipino one
        key = (0, p["alert"] is not None, p["hour"] or 0, p["minute"] or 0, not p["filipino"])
        cur = out[p["volcano"]].get(p["date"])
        if cur is None or key >= cur[0]:
            out[p["volcano"]][p["date"]] = (key, [p["date"], p["alert"], p["eq"], p["tremor"], p["so2"], p["so2_date"], p["plume_m"], p["deform"], p["url"]])
    for r in Records(RAW / "phivolcs-lava-bulletins" / "pages.jsonl").latest("bid").values():
        if r.get("status") != 200:
            continue
        p = parse_lava(r["html"])
        if not p:
            continue
        date = p["date"] or r["date"]
        key = (1, p["alert"] is not None, r["bid"])
        cur = out[r["volcano"]].get(date)
        if cur is None or key >= cur[0]:
            out[r["volcano"]][date] = (key, [date, p["alert"], p["eq"], p["tremor"], p["so2"], p["so2_date"], p["plume_m"], p["deform"],
                                             r["url"].replace("&lang=en", "")])
    return {v: {d: row for d, (_, row) in sorted(days.items())} for v, days in out.items()}


def load_vaac() -> dict[int, list]:
    out = collections.defaultdict(list)
    for r in Records(RAW / "vaac-tokyo-advisories" / "pages.jsonl").latest().values():
        if r.get("status") != 200:
            continue
        p = parse_vaac(r["html"])
        if p["dtg"]:
            out[r["gvp"]].append([p["dtg"], p["nr"] or "", p["top_fl"], p["basis"], r["url"]])
    return {k: sorted(v) for k, v in out.items()}


def load_dromic() -> list:
    rs = []
    for r in Records(RAW / "dswd-dromic-reports" / "taal-2020.jsonl").latest().values():
        t = r.get("totals") or {}
        if r.get("status") != 200 or not t.get("affected_persons") or not r.get("as_of_text"):
            continue
        as_of = dt.datetime.strptime(r["as_of_text"], "%d %B %Y").date().isoformat()
        rs.append([as_of, str(r["report"]), t.get("affected_persons"), t.get("inside_persons_now"), t.get("inside_persons_cum"),
                   t.get("outside_persons_now"), t.get("outside_persons_cum"), r["url"]])
    return sorted(rs, key=lambda x: (x[0], int(x[1])))


def load_usgs() -> list[dict]:
    out = []
    for f in ("usgs-comcat-ph-1900-2009.csv", "usgs-comcat-ph-2010.csv"):
        for r in rows(RAW / "usgs" / f):
            if r["type"] != "earthquake":
                continue
            out.append({"t": r["time"], "lat": float(r["latitude"]), "lon": float(r["longitude"]), "mag": fnum(r["mag"]), "depth": fnum(r["depth"]), "id": r["id"]})
    return out


def load_ee(kind: str) -> list[dict]:
    out = []
    for p in sorted(glob.glob(str(TABLES / f"ee-{kind}" / "*.csv"))):
        out += rows(p)
    return out


# ---------------------------------------------------------------- builders

def dense(start: str, end: str, values: dict[str, float | None]) -> list:
    n = days_between(start, end) + 1
    out = [None] * n
    for d, v in values.items():
        i = days_between(start, d)
        if 0 <= i < n:
            out[i] = v
    return out


def so2_series(vid: str, so2: list[dict], end: str) -> dict:
    by = collections.defaultdict(dict)
    for r in so2:
        if r["volcano"] == vid:
            by[r["ring"]][r["date"]] = r
    if not by:
        return {}
    start = min(by["15km"])
    end = min(end, max(by["15km"]))

    def col(ring, f):
        return dense(start, end, {d: f(r) for d, r in by[ring].items()})

    def umol(r, k="so2_pbl_mol_m2"):
        v = fnum(r[k])
        return None if v is None or int(r["valid"]) == 0 else round(v * 1e6)

    def cov(r):
        t = int(r["total"])
        return round(int(r["valid"]) / t, 3) if t else None

    note = lt("Column amount on the day's clear pixels, not an emission rate (flux). Coverage = share of the ring with a valid pixel.",
              "その日の有効画素でのカラム量で、放出率(フラックス)ではない。被覆率=有効画素のある範囲の割合。")
    src = ["s5p-offl-so2"]
    return {
        "so2_s5p_15km": {"source": src, "unit": "µmol/m²", "ringKm": 15, "start": start, "label": lt("TROPOMI SO₂ column, mean within 15 km", "TROPOMI SO₂カラム量(15 km圏平均)"),
                         "values": col("15km", umol), "coverage": col("15km", cov), "note": note},
        "so2_s5p_mass_15km": {"source": src, "unit": "t", "ringKm": 15, "start": start, "label": lt("TROPOMI SO₂ mass on clear pixels within 15 km", "TROPOMI SO₂量(15 km圏の有効画素)"),
                              "values": col("15km", lambda r: None if int(r["valid"]) == 0 else round(fnum(r["mass_pbl_t"]) or 0, 2)), "coverage": col("15km", cov),
                              "note": lt("A lower bound when coverage is partial: cloudy pixels add nothing.", "被覆率が低い日は下限値(雲の画素は加算されない)。")},
        "so2_s5p_50km": {"source": src, "unit": "µmol/m²", "ringKm": 50, "start": start, "label": lt("TROPOMI SO₂ column, mean within the 50 km box", "TROPOMI SO₂カラム量(50 km範囲平均)"),
                         "values": col("box50km", umol), "coverage": col("box50km", cov)},
    }


FIRE_SERIES = {"modis-mod14a1": ("frp_modis_15km", lt("MODIS (Terra) max fire radiative power within 15 km", "MODIS(Terra)最大放射電力(15 km圏)"), "2000-11-01"),
               "viirs-vnp14a1": ("frp_viirs_15km", lt("VIIRS (S-NPP) max fire radiative power within 15 km", "VIIRS(S-NPP)最大放射電力(15 km圏)"), "2012-01-19"),
               "firms-modis": ("fire_firms_15km", lt("FIRMS MODIS fire detections within 15 km", "FIRMS MODIS 熱異常検知(15 km圏)"), "2000-11-01")}


def fire_series(vid: str, fire: list[dict]) -> dict:
    out = {}
    note = lt("Thermal anomalies include vegetation fires; a detection is not proof of volcanic heat.", "熱異常には植生火災も含まれ、検知が火山の熱を意味するとは限らない。")
    for src, (sid, label, start) in FIRE_SERIES.items():
        rs = sorted((r for r in fire if r["volcano"] == vid and r["ring"] == "15km" and r["source"] == src), key=lambda r: r["date"])
        if src == "firms-modis":
            out[sid] = {"source": [src], "label": label, "cols": ["date", "n"], "units": {"n": "pixels"}, "ringKm": 15, "start": start,
                        "rows": [[r["date"], int(float(r["n"]))] for r in rs], "note": note}
        else:
            out[sid] = {"source": [src], "label": label, "cols": ["date", "maxFrpMw", "n"], "units": {"maxFrpMw": "MW", "n": "pixels"}, "ringKm": 15, "start": start,
                        "rows": [[r["date"], round(float(r["max_frp_mw"]), 1) if r["max_frp_mw"] else None, int(float(r["n"]))] for r in rs], "note": note}
    return out


def eq_series(v: dict, usgs: list[dict]) -> dict:
    out = {}
    for ring in (10, 30):
        by = collections.defaultdict(list)
        for e in usgs:
            if e["t"][:10] >= SPAN_START and abs(e["lat"] - v["lat"]) < 0.3 and km(v["lat"], v["lon"], e["lat"], e["lon"]) <= ring:
                by[e["t"][:10]].append(e["mag"])
        out[f"eq_usgs_{ring}km"] = {"source": ["usgs-comcat-ph-1900-2009", "usgs-comcat-ph-2010"], "label": lt(f"USGS earthquakes within {ring} km", f"USGS 地震({ring} km圏)"),
                                    "cols": ["date", "n", "maxMag"], "units": {"n": "events", "maxMag": "M"}, "ringKm": ring, "start": SPAN_START,
                                    "rows": [[d, len(m), max((x for x in m if x is not None), default=None)] for d, m in sorted(by.items())],
                                    "note": lt("Global network: small local volcanic earthquakes are below its detection threshold; PHIVOLCS counts are in the bulletins.",
                                               "全球観測網のため小さな火山性地震は検知されない。PHIVOLCSの回数は火山情報を参照。")}
    return out


def episodes_for(v: dict, gvp_e: list[dict], msvol: list[dict], bulletins: dict) -> list[dict]:
    eps = []
    for e in gvp_e:
        if not v["gvpNumber"] or int(e["Volcano_Number"]) != v["gvpNumber"] or not e["StartDateYear"]:
            continue
        s = gvp_date(e)
        ep = {"id": f"gvp-{e['Eruption_Number']}", "kind": "gvp_eruption", "start": s, "end": gvp_date(e, "EndDate"),
              "startUncertaintyDays": int(e["StartDateDayUncertainty"]) if e["StartDateDayUncertainty"] else None,
              "vei": int(e["ExplosivityIndexMax"]) if e["ExplosivityIndexMax"] else None, "source": ["gvp-eruptions-ph"],
              "url": f"https://volcano.si.edu/volcano.cfm?vn={v['gvpNumber']}"}
        if len(s) == 10:
            m = next((m for m in msvol if m["volcano"].lower() == (v["gvpName"] or "").lower() and abs(days_between(s, m["date"])) <= 3), None)
            if m:
                ep.update(so2MassKt=m["so2_kt"], plumeAltKm=m["plume_km_obs"], source=["gvp-eruptions-ph", "nasa-msvolso2l4"])
        eps.append(ep)
    eps.sort(key=lambda e: int(e["start"].split("-")[0]) if not e["start"].startswith("-") else -int(e["start"].split("-")[1]))
    # alert windows: runs of bulletins reporting level >= 2, merged across gaps of up to 7 days
    run = None
    for d, row in sorted(bulletins.items()):
        a = row[1]
        if a is not None and a >= 2:
            if run and days_between(run["end"], d) <= 7:
                run["end"], run["maxAlert"] = d, max(run["maxAlert"], a)
            else:
                if run:
                    eps.append(run)
                run = {"id": f"alert-{d}", "kind": "alert_window", "start": d, "end": d, "maxAlert": a, "source": ["phivolcs-bulletins", "phivolcs-lava-bulletins"], "url": row[8]}
    if run:
        eps.append(run)
    return eps


def exposure_for(v: dict, expo: list[dict], lgus: list[dict]) -> dict:
    rings = [{"radiusKm": int(r["ring_km"]), "population": int(r["population"]), "year": int(r["year"]), "source": "worldpop-100m"}
             for r in expo if r["volcano"] == v["id"] and r["year"] == "2020"]
    near = sorted(({"pcode": g["adm3_pcode"], "name": g["adm3_name"], "province": g["adm2_name"],
                    "distanceKm": round(km(v["lat"], v["lon"], float(g["center_lat"]), float(g["center_lon"])), 1)} for g in lgus),
                  key=lambda x: x["distanceKm"])
    return {"rings": rings, "lgus": [x for x in near if x["distanceKm"] <= 30]}


def provenance(ids: list[str], prov: dict) -> dict:
    out = []
    for i in dict.fromkeys(ids):
        e = REG[i]
        p = prov.get(i, {})
        rec = {"id": i, "attribution": " ".join(e["attribution"].split()), "licence": " ".join(e["licence"].split())}
        if p.get("link"):
            rec["link"] = p["link"]
        if p.get("snapshotDate"):
            rec["snapshotDate"] = p["snapshotDate"]
        rec["fromArchive"] = bool(p.get("fromArchive"))
        out.append(rec)
    return {"sources": out}


def file_provenance() -> dict:
    out = {}
    for path in glob.glob(str(RAW / "*" / "*.provenance.json")):
        d = json.loads(open(path).read())
        sid = d.get("source_id") or path.rsplit("/", 1)[-1].replace(".csv.provenance.json", "")
        out[sid] = {"link": d.get("link_id"), "snapshotDate": (d.get("data_as_of") or d.get("fetched_at") or "")[:10] or None,
                    "fromArchive": d.get("served_by") == "archive"}
    return out


# ---------------------------------------------------------------- story

MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def date_en(iso: str) -> str:
    """'2020-09-07' -> '7 September 2020' (the story's date style)."""
    d = dt.date.fromisoformat(iso[:10])
    return f"{d.day} {MONTHS_EN[d.month - 1]} {d.year}"


def fl_gloss(fl: int) -> dict:
    """A flight level with its height in km: EN "FL550 (about 16.8 km)", JA "FL550（約16.8 km）" (full-width brackets)."""
    km = fl * 30.48 / 1000
    return lt(f"FL{fl} (about {km:.1f} km)", f"FL{fl}（約{km:.1f} km）")


# English words, ISO dates and half-width brackets that should not be left in Japanese text.
_JA_LEFTOVERS = re.compile(r"\b(?:about|the|and|by|on|from|to|in|of|n/a)\b|\d{4}-\d{2}-\d{2}|[()]")


def ja_leftovers(text: str) -> list[str]:
    return _JA_LEFTOVERS.findall(text)


def date_ja(iso: str) -> str:
    """'2020-09-07' -> '2020年9月7日'."""
    d = dt.date.fromisoformat(iso[:10])
    return f"{d.year}年{d.month}月{d.day}日"


def neg(x) -> str:
    """A number with a typographic minus."""
    return str(x).replace("-", "−")


def share_txt(c: float) -> str:
    """A coverage share that never rounds a non-zero share to 0%."""
    return f"{c:.0%}" if c >= 0.01 or c == 0 else f"{c:.1%}"


def story_taal(v: dict, vm: dict, as_of: str, hdr: dict) -> tuple[dict, dict]:
    """The Taal January 2020 story (text reviewed by Kurt on 2026-10-22) and the Taal reading (reviewed by Kurt on 2026-10-22).

    Every number in the text is read from the volcano read model, so a rebuild with other data restates it."""
    b = vm["bulletins"]["rows"] if vm["bulletins"] else []
    bd = {r[0]: r for r in b}
    adv = vm["advisories"]["rows"] if vm["advisories"] else []
    jan = [r for r in adv if r[0][:10] in ("2020-01-12", "2020-01-13") and r[3] == "observed" and r[2]]
    top = max(jan, key=lambda r: r[2]) if jan else None
    s5 = vm["daily"].get("so2_s5p_15km")
    eq_rows = vm["events"]["eq_usgs_30km"]["rows"]
    eq = {r[0]: r for r in eq_rows}
    disp = vm["displacement"]["rows"] if vm["displacement"] else []

    def so2_at(iso):
        i = days_between(s5["start"], iso)
        return (s5["values"][i], s5["coverage"][i]) if 0 <= i < len(s5["values"]) else (None, None)

    # PHIVOLCS: the bulletin of 12 January 2020 that reports the level, with its time from the page's slug
    a12 = bd.get("2020-01-12")
    t12 = wp_slug_meta(a12[8]) if a12 else {}
    figs_erupt = []
    if a12 and a12[1] is not None:
        figs_erupt.append({"label": lt("Alert level (as reported)", "警戒レベル(発表値)"), "value": a12[1], "source": "phivolcs-bulletins", "asOf": "2020-01-12", "url": a12[8]})
    if top:
        figs_erupt.append({"label": lt("Ash top (Tokyo VAAC, observed)", "火山灰の高度(東京VAAC観測)"), "value": top[2], "unit": "FL", "source": "vaac-tokyo-advisories",
                           "asOf": top[0][:10], "url": top[4]})
    if s5:
        so2_13, cov_13 = so2_at("2020-01-13")
        if so2_13 is not None:
            figs_erupt.append({"label": lt("TROPOMI SO₂ column within 15 km", "TROPOMI SO₂カラム量(15 km圏)"), "value": so2_13, "unit": "µmol/m²",
                               "source": "s5p-offl-so2", "asOf": "2020-01-13", "note": lt(f"coverage {share_txt(cov_13)}", f"被覆率 {share_txt(cov_13)}")})
    eq12 = eq.get("2020-01-12")
    if eq12:
        figs_erupt.append({"label": lt("USGS earthquakes within 30 km", "USGS 地震(30 km圏)"), "value": eq12[1], "source": "usgs-comcat-ph-2010", "asOf": "2020-01-12"})
    gvp = next((e for e in vm["episodes"] if e["kind"] == "gvp_eruption" and e["start"] == "2020-01-12"), None)
    if gvp:
        figs_erupt.append({"label": lt("SO₂ mass (MSVOLSO2L4)", "SO₂量(MSVOLSO2L4)"), "value": gvp.get("so2MassKt"), "unit": "kt", "source": "nasa-msvolso2l4", "asOf": "2020-01-12"})
    last = disp[-1] if disp else None
    pop14 = next((r["population"] for r in vm["exposure"]["rings"] if r["radiusKm"] == 14), None)
    thumbs = json.loads((BUILD / "assets" / "taal-s2.json").read_text())
    assets = [{"kind": "image", "url": f"assets/{k}.jpg", "date": d, "sensor": "Sentinel-2 MSI", "source": "s2-sr-harmonized",
               "caption": lt(f"Sentinel-2, {date_en(d)}", f"Sentinel-2、{date_ja(d)}"), "credit": f"Contains modified Copernicus Sentinel data {d[:4]}"}
              for k, d in thumbs.items()]
    winds = json.loads((TABLES / "era5-story-taal-2020.json").read_text())

    # Step 1: what each record shows from 1 December 2019 to 11 January 2020
    before_en, before_ja = [], []
    pre = [r for d, r in bd.items() if "2019-12-01" <= d <= "2020-01-11" and r[1] is not None]
    levels = sorted({r[1] for r in pre})
    if len(levels) == 1:
        before_en.append(f"PHIVOLCS bulletins reported Alert Level {levels[0]} on every day from {date_en(pre[0][0])} to {date_en(pre[-1][0])}, as reported by PHIVOLCS.")
        before_ja.append(f"PHIVOLCSの火山情報は{date_ja(pre[0][0])}から{date_ja(pre[-1][0])}まで毎日、警戒レベル{levels[0]}を発表していた（PHIVOLCS発表）。")
    if s5:
        dec = sorted(x for x in (so2_at(f"2019-12-{d:02d}")[0] for d in range(1, 32)) if x is not None)
        if dec:
            med = dec[len(dec) // 2] if len(dec) % 2 else round((dec[len(dec) // 2 - 1] + dec[len(dec) // 2]) / 2)
            wk = [x for x in (so2_at(f"2020-01-{d:02d}")[0] for d in range(1, 12)) if x is not None]
            before_en.append(f"The TROPOMI SO₂ column within 15 km had a December median of {med} µmol/m² ({len(dec)} of 31 days with a clear view); "
                             f"from 1 to 11 January 2020 it read between {neg(min(wk))} and {neg(max(wk))} µmol/m² on the {len(wk)} clear days.")
            before_ja.append(f"15 km圏のTROPOMI SO₂カラム量は12月の中央値が{med} µmol/m²（31日中{len(dec)}日が観測可能）で、"
                             f"2020年1月1日から11日までは観測できた{len(wk)}日で{neg(min(wk))}〜{neg(max(wk))} µmol/m²だった。")
    quiet = [r for r in eq_rows if r[0] < "2020-01-12"]
    if eq12 and quiet:
        before_en.append(f"The USGS catalogue lists no earthquake within 30 km after {date_en(quiet[-1][0])} until 12 January 2020, "
                         f"when it lists {eq12[1]}, the largest M{eq12[2]}.")
        before_ja.append(f"USGSのカタログには{date_ja(quiet[-1][0])}の後、2020年1月12日まで30 km圏の地震がなく、"
                         f"同日には{eq12[1]}回（最大M{eq12[2]}）が記録されている。")

    # Step 2: the alert level as reported, with the bulletin's time
    def time_en(h, m):
        return f"{h % 12 or 12}:{m:02d} {'AM' if h < 12 else 'PM'}"

    erupt_en, erupt_ja = [], []
    if a12 and a12[1] is not None:
        when_en = f" in its {time_en(t12['hour'], t12['minute'])} bulletin" if t12.get("hour") is not None else ""
        when_ja = f"{'午前' if t12['hour'] < 12 else '午後'}{t12['hour'] % 12 or 12}時{t12['minute']:02d}分の火山情報で" if t12.get("hour") is not None else ""
        erupt_en.append(f"PHIVOLCS raised the alert to level {a12[1]} on 12 January 2020{when_en}, as reported by PHIVOLCS.")
        erupt_ja.append(f"PHIVOLCSは2020年1月12日{when_ja}警戒レベルを{a12[1]}に引き上げた（PHIVOLCS発表）。")
    if top:
        erupt_en.append(f"Tokyo VAAC observed ash up to {fl_gloss(top[2])['en']} on {date_en(top[0])}.")
        erupt_ja.append(f"東京VAACは{date_ja(top[0])}に最高{fl_gloss(top[2])['ja']}の火山灰を観測した。")
    if gvp and gvp.get("vei") is not None:
        erupt_en.append(f"GVP records the eruption as VEI {gvp['vei']}.")
        erupt_ja.append(f"GVPはこの噴火をVEI {gvp['vei']}としている。")

    steps = [
        {"id": "before", "start": "2019-12-01", "end": "2020-01-11", "status": "reviewed", "title": lt("Before", "噴火前"),
         "text": lt(" ".join(before_en), "".join(before_ja)),
         "series": ["bulletins", "so2_s5p_15km", "eq_usgs_30km"], "figures": [], "map": {"center": [v["lon"], v["lat"]], "zoom": 10}},
        {"id": "eruption", "start": "2020-01-12", "end": "2020-01-13", "status": "reviewed", "title": lt("12–13 January 2020", "2020年1月12〜13日"),
         "text": lt(" ".join(erupt_en), "".join(erupt_ja)),
         "series": ["bulletins", "advisories", "so2_s5p_15km", "eq_usgs_30km", "frp_modis_15km"], "figures": figs_erupt,
         "map": {"center": [v["lon"], v["lat"]], "zoom": 9, "layers": ["thermal-detections"], "month": "2020-01"}},
        {"id": "people", "start": "2020-01-12", "end": "2020-03-12", "status": "reviewed", "title": lt("People", "人々"),
         "text": lt((f"DSWD DROMIC reports counted {last[2]:,} people affected by {date_en(last[0])}. " if last else "") +
                    (f"WorldPop estimates {pop14:,} people lived within 14 km in 2020." if pop14 else ""),
                    (f"DSWD DROMIC報告は{date_ja(last[0])}までに{last[2]:,}人の被災者を数えた。" if last else "") +
                    (f"WorldPopの推計では2020年に14 km圏内に{pop14:,}人が住んでいた。" if pop14 else "")),
         "series": ["displacement"],
         "figures": ([{"label": lt("Persons affected", "被災者数"), "value": last[2], "source": "dswd-dromic-reports", "asOf": last[0], "url": last[7]}] if last else [])
         + ([{"label": lt("People within 14 km (WorldPop 2020)", "14 km圏内の人口（WorldPop 2020）"), "value": pop14, "source": "worldpop-100m"}] if pop14 else [])},
        {"id": "crater", "start": "2019-11-19", "end": "2020-03-23", "status": "reviewed", "title": lt("The crater lake", "火口湖"),
         "text": lt("Sentinel-2 before and after: the main crater lake on Volcano Island drained during the eruption.", "Sentinel-2の前後比較:火山島の主火口湖は噴火中に干上がった。"),
         "series": [], "figures": [], "assets": assets},
    ]
    story = {**hdr, "kind": "story", "id": "taal-2020", "volcanoId": "taal", "volcanoFile": "volcano/taal.json",
             "title": lt("Taal, January 2020", "タール火山 2020年1月"),
             "summary": lt("What the instruments recorded before, during and after the 12 January 2020 eruption. A past record, not a hazard assessment.",
                           "2020年1月12日の噴火の前後に観測機器が記録したこと。過去の記録であり、ハザード評価ではない。"),
             "span": {"start": "2019-12-01", "end": "2020-03-31"}, "steps": steps,
             "winds": {"source": ["era5-pressure-levels"], "point": winds["point"], "cols": winds["cols"], "rows": winds["rows"]},
             "provenance": provenance(["phivolcs-bulletins", "vaac-tokyo-advisories", "dswd-dromic-reports", "s5p-offl-so2", "usgs-comcat-ph-2010",
                                       "gvp-eruptions-ph", "nasa-msvolso2l4", "worldpop-100m", "s2-sr-harmonized", "era5-pressure-levels"], {})}
    # The volcano page's reading, reviewed by Kurt on 2026-10-22 (JA height gloss in full-width brackets).
    top_txt = fl_gloss(top[2]) if top else lt("n/a", "不明")
    reading = {"id": "taal-2020-01", "start": "2020-01-12", "end": "2020-01-26", "status": "reviewed",
               "text": lt(f"PHIVOLCS raised the alert within hours. Tokyo VAAC observed ash up to {top_txt['en']}. GVP records the eruption as VEI 4.",
                          f"PHIVOLCSは数時間のうちに警戒レベルを引き上げた。東京VAACは最高{top_txt['ja']}の火山灰を観測した。GVPはこの噴火をVEI 4としている。"),
               "limits": lt("Satellite SO₂ is a column amount on clear pixels only, not a flux; the record is retrospective, not a hazard assessment.",
                            "衛星SO₂は有効画素のみのカラム量で、フラックスではない。過去の記録であり、ハザード評価ではない。"),
               "figures": figs_erupt}
    return story, reading


# ---------------------------------------------------------------- layers

def thermal_layers(out_dir, as_of: str) -> dict | None:
    """National FIRMS detections (area API) as one PMTiles per year, a `month` property for the scrubber."""
    if not shutil.which("tippecanoe"):
        return None
    years = []
    tmp = BUILD / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    by_year = collections.defaultdict(list)
    seen = set()
    n20_to = thermal_n20.sp_covered_to() or ""  # NRT only after the standard NOAA-20 product ends
    for product in ("MODIS_SP", "VIIRS_SNPP_SP", "VIIRS_NOAA20_SP", "VIIRS_NOAA20_NRT"):
        for p in sorted(glob.glob(str(RAW / "firms" / product / "*.csv"))):
            for r in rows(p):
                if product == "VIIRS_NOAA20_NRT" and r["acq_date"] <= n20_to:
                    continue
                k = (product, r["latitude"], r["longitude"], r["acq_date"], r["acq_time"], r["satellite"])
                if k not in seen:  # a re-fetched window must not double a detection
                    seen.add(k)
                    by_year[r["acq_date"][:4]].append((product, r))
    for y, rs in sorted(by_year.items()):
        src = tmp / f"thermal-{y}.geojsonl"
        with open(src, "w") as f:
            for product, r in rs:
                f.write(json.dumps({"type": "Feature", "geometry": {"type": "Point", "coordinates": [float(r["longitude"]), float(r["latitude"])]},
                                    "properties": {"month": r["acq_date"][:7], "date": r["acq_date"], "frp": fnum(r["frp"]), "sensor": r.get("product") or product,
                                                   "type": int(r["type"]) if r.get("type") not in (None, "") else None}}) + "\n")
        dst = out_dir / "layers" / "thermal" / f"{y}.pmtiles"
        dst.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["tippecanoe", "-q", "-f", "-o", str(dst), "-l", "thermal", "-Z", "4", "-z", "10", "--drop-densest-as-needed",
                        "--extend-zooms-if-still-dropping", "-P", str(src)], check=True)
        years.append(y)
    if not years:
        return None
    return {"id": "thermal-detections", "title": lt("Thermal detections (NASA FIRMS)", "熱異常検知(NASA FIRMS)"), "format": "pmtiles",
            "url": "layers/thermal/{year}.pmtiles", "sourceLayer": "thermal",
            "time": {"step": "month", "start": f"{years[0]}-01", "end": as_of[:7]}, "minzoom": 4, "maxzoom": 10, "bounds": [116, 4, 128, 22],
            "properties": {"month": "YYYY-MM", "date": "acquisition date", "frp": "MW", "sensor": "FIRMS product", "type": "FIRMS type: 0 vegetation fire, 1 active volcano, 2 other static source, 3 offshore"},
            "sources": ["firms-modis", "firms-viirs-noaa20"], "attribution": " ".join(" ".join(REG[i]["attribution"].split()) for i in ("firms-modis", "firms-viirs-noaa20")),
            "note": lt("All thermal detections in the Philippines, most of them vegetation fires; filter by type = 1 for FIRMS's active-volcano flag.",
                       "フィリピン全域の熱異常検知(多くは植生火災)。FIRMSの活火山フラグは type = 1。")}


def quake_layer(out_dir, usgs: list[dict]) -> dict:
    src = BUILD / "tmp" / "usgs.geojsonl"
    src.parent.mkdir(parents=True, exist_ok=True)
    with open(src, "w") as f:
        for e in usgs:
            if e["t"][:4] >= "2000":
                f.write(json.dumps({"type": "Feature", "geometry": {"type": "Point", "coordinates": [e["lon"], e["lat"]]},
                                    "properties": {"month": e["t"][:7], "time": e["t"], "mag": e["mag"], "depth": e["depth"], "id": e["id"]}}) + "\n")
    dst = out_dir / "layers" / "earthquakes-usgs.pmtiles"
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["tippecanoe", "-q", "-f", "-o", str(dst), "-l", "earthquakes", "-Z", "4", "-z", "9", "-r1", "-P", str(src)], check=True)
    return {"id": "earthquakes-usgs", "title": lt("Earthquakes (USGS ComCat)", "地震(USGS ComCat)"), "format": "pmtiles", "url": "layers/earthquakes-usgs.pmtiles",
            "sourceLayer": "earthquakes", "time": {"step": "month", "start": "2000-01", "end": max(e["t"] for e in usgs)[:7]}, "minzoom": 4, "maxzoom": 9,
            "bounds": [116, 4, 128, 22], "properties": {"month": "YYYY-MM", "time": "UTC", "mag": "magnitude", "depth": "km", "id": "USGS event id"},
            "sources": ["usgs-comcat-ph-1900-2009", "usgs-comcat-ph-2010"], "attribution": REG["usgs-comcat-ph-2010"]["attribution"]}


# ---------------------------------------------------------------- checks

def run_checks(site_v, vols: list[dict], models: dict, gvp_v: list, gvp_e: list) -> list[dict]:
    res = []

    def check(name, ok, detail=""):
        res.append({"check": name, "passed": bool(ok), "detail": detail})

    for p in sorted(site_v.rglob("*.json")) + sorted(site_v.rglob("*.geojson")):
        doc = json.loads(p.read_text())
        if "kind" in doc:
            e = errors(doc)
            check(f"schema {p.relative_to(site_v)}", not e, "; ".join(e[:3]))
    check("24 volcanoes in the crosswalk", len(vols) == 24, str(len(vols)))
    years = {p.stem for p in (site_v / "layers" / "thermal").glob("*.pmtiles")}
    last = int(json.loads((site_v / "layers.json").read_text())["dataAsOf"][:4]) - 1
    missing = sorted({str(y) for y in range(2000, last + 1)} - years)
    check("thermal detections: one tileset per year 2000 onward", not missing, ",".join(missing))
    check("GVP lists 23 Philippine volcanoes", len(gvp_v) == 23, str(len(gvp_v)))
    check("GVP eruptions within bounds", 200 <= len(gvp_e) <= 400, str(len(gvp_e)))
    for vid, m in models.items():
        if m.get("bulletins"):
            ds = [r[0] for r in m["bulletins"]["rows"]]
            check(f"{vid}: one bulletin row a day", len(ds) == len(set(ds)))
        for t in ("bulletins", "advisories", "displacement"):
            if m.get(t):
                check(f"{vid}: every {t} row links its source", all(str(r[-1]).startswith("https://") for r in m[t]["rows"]))
        size = len(gzip.compress(json.dumps(m, separators=(",", ":"), ensure_ascii=False).encode(), 9))
        check(f"{vid}: size under 150 kB gzip", size < 150_000, f"{size / 1000:.1f} kB")
    t = models["taal"]
    gv = [e for e in t["episodes"] if e["kind"] == "gvp_eruption" and e["start"] == "2020-01-12"]
    check("Taal 2020-01-12: GVP VEI 4", gv and gv[0]["vei"] == 4)
    check("Taal 2020-01-12: MSVOLSO2L4 170 kt", gv and gv[0].get("so2MassKt") == 170)
    adv = [r for r in (t["advisories"] or {"rows": []})["rows"] if r[0].startswith("2020-01-12")]
    check("Taal 2020-01-12: VAAC observed FL550", any(r[2] == 550 and r[3] == "observed" for r in adv))
    s5 = t["daily"]["so2_s5p_15km"]
    i13 = days_between(s5["start"], "2020-01-13")
    base = sorted(x for x in s5["values"][i13 - 40: i13 - 2] if x is not None)
    check("Taal 2020-01-13: TROPOMI SO2 > 20x the December median", base and s5["values"][i13] > 20 * max(base[len(base) // 2], 1), f"{s5['values'][i13]} vs {base[len(base) // 2] if base else None}")
    k = [e for e in models["kanlaon"]["episodes"] if e["kind"] == "gvp_eruption" and e["start"] == "2024-06-03"]
    check("Kanlaon 2024-06-03 eruption present", bool(k))
    b = {r[0]: r for r in (t.get("bulletins") or {"rows": []})["rows"]}
    check("Taal 2020-01-13 bulletin: alert level 4", b.get("2020-01-13", [None, None])[1] == 4)
    check("Taal 2020-01-12 bulletin (7:30 PM, a notice of change): alert level 4", b.get("2020-01-12", [None, None])[1] == 4)
    story = json.loads((site_v / "story" / "taal-2020.json").read_text())
    ja = " ".join([story["title"]["ja"], story["summary"]["ja"]] + [x for st in story["steps"] for x in (st["title"]["ja"], st["text"]["ja"])]
                  + [a["caption"]["ja"] for st in story["steps"] for a in st.get("assets", [])])
    left = ja_leftovers(ja)
    check("story: no English words, ISO dates or half-width brackets left in the Japanese text", not left, ", ".join(left[:5]))
    check("story: every step reviewed", all(st.get("status") == "reviewed" for st in story["steps"]))
    rd = [x for x in t.get("readings", []) if x["id"] == "taal-2020-01"]
    check("Taal reading: reviewed, Japanese text clean", bool(rd) and rd[0]["status"] == "reviewed" and not ja_leftovers(rd[0]["text"]["ja"]),
          ", ".join(ja_leftovers(rd[0]["text"]["ja"])[:5]) if rd else "missing")
    for vid in ("taal", "mayon", "kanlaon", "bulusan"):
        n = len((models[vid].get("bulletins") or {"rows": []})["rows"])
        check(f"{vid}: at least 1,500 bulletin days (2017-09 onward)", n >= 1500, str(n))
    pop = next((r["population"] for r in t["exposure"]["rings"] if r["radiusKm"] == 14), 0)
    check("Taal WorldPop 2020 within 14 km about 318,000", 250_000 < pop < 400_000, str(pop))
    return res


# ---------------------------------------------------------------- main

def build(version: int, as_of: str) -> dict:
    site = BUILD / "site"
    v_dir = site / f"v{version}"
    if v_dir.exists():
        shutil.rmtree(v_dir)
    v_dir.mkdir(parents=True)
    hdr = {"schemaVersion": "1", "dataVersion": f"v{version}", "dataAsOf": as_of, "generatedAt": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")}
    vols = load_volcanoes()
    gvp_v = rows(RAW / "gvp" / "gvp-volcanoes-ph.csv")
    gvp_e = rows(RAW / "gvp" / "gvp-eruptions-ph.csv")
    msvol = json.loads((RAW / "nasa-msvolso2l4" / "philippines.json").read_text())["rows"]
    bulletins, vaac, dromic, usgs = load_bulletins(), load_vaac(), load_dromic(), load_usgs()
    so2, fire = load_ee("so2"), load_ee("fire")
    expo = rows(TABLES / "ee-exposure.csv")
    lgus = rows(RAW / "cod-ab" / "phl_admin3.csv")
    fprov = file_provenance()
    n20, omi_so2 = thermal_n20.series_by_volcano(vols), omi.series_by_volcano(as_of)
    models, feats = {}, []
    for v in vols:
        b = bulletins.get(v["id"], {})
        vm = {**hdr, "kind": "volcano",
              "volcano": {k: v[k] for k in ("id", "gvpNumber", "gvpName", "name", "lat", "lon", "elevationM", "type", "observatory", "coverage")}
              | {"links": {"phivolcs": WP_HOME, "hazardhunter": "https://hazardhunter.georisk.gov.ph/", "comet": "https://comet.nerc.ac.uk/comet-lics-portal/"}
                 | ({"gvp": f"https://volcano.si.edu/volcano.cfm?vn={v['gvpNumber']}"} if v["gvpNumber"] else {})},
              "span": {"start": SPAN_START, "end": as_of},
              "daily": {**so2_series(v["id"], so2, as_of), **omi_so2.get(v["id"], {})},
              "events": {**fire_series(v["id"], fire), **n20.get(v["id"], {}), **eq_series(v, usgs)},
              "bulletins": {"source": ["phivolcs-bulletins", "phivolcs-lava-bulletins"], "authority": "DOST-PHIVOLCS",
                            "cols": ["date", "alertLevel", "volcanicEq", "tremor", "so2FluxTpd", "so2FluxDate", "plumeM", "deformation", "url"],
                            "rows": list(b.values()),
                            "gaps": [{"start": "2021-10", "end": "2022-06", "reason": lt("The WordPress summaries are empty shells and LAVA had not started.", "WordPressの要約は本文がなく、LAVAは未開始。")}]} if b else None,
              "advisories": {"source": ["vaac-tokyo-advisories"], "cols": ["dtg", "advisoryNo", "topFl", "heightBasis", "url"], "rows": vaac[v["gvpNumber"]]}
              if v["gvpNumber"] in vaac else None,
              "displacement": {"source": ["dswd-dromic-reports"], "cols": ["asOf", "report", "affectedPersons", "insidePersonsNow", "insidePersonsCum",
                                                                             "outsidePersonsNow", "outsidePersonsCum", "url"], "rows": dromic} if v["id"] == "taal" and dromic else None,
              "episodes": episodes_for(v, gvp_e, msvol, b), "readings": [], "exposure": exposure_for(v, expo, lgus)}
        used = ["gvp-volcanoes-ph", "gvp-eruptions-ph", "usgs-comcat-ph-1900-2009", "usgs-comcat-ph-2010", "s5p-offl-so2", "modis-mod14a1", "viirs-vnp14a1",
                "firms-modis", "worldpop-100m", "cod-ab-phl-gdb"] + (["phivolcs-bulletins", "phivolcs-lava-bulletins"] if b else []) \
            + (["vaac-tokyo-advisories"] if vm["advisories"] else []) + (["dswd-dromic-reports"] if vm["displacement"] else []) \
            + (["nasa-msvolso2l4"] if any(e.get("so2MassKt") for e in vm["episodes"]) else []) \
            + (["firms-viirs-noaa20"] if v["id"] in n20 else []) + (["omi-omso2e"] if v["id"] in omi_so2 else [])
        vm["provenance"] = provenance(used, fprov) | {"earthEngine": {"assets": ["COPERNICUS/S5P/OFFL/L3_SO2", "MODIS/061/MOD14A1", "NASA/VIIRS/002/VNP14A1", "FIRMS", "WorldPop/GP/100m/pop"]}}
        models[v["id"]] = vm
        er = [e for e in vm["episodes"] if e["kind"] == "gvp_eruption"]
        yr = [int(e["start"].split("-")[0]) for e in er if not e["start"].startswith("-")]
        last = er[-1] if er else None
        feats.append({"type": "Feature", "id": v["id"], "geometry": {"type": "Point", "coordinates": [v["lon"], v["lat"]]},
                      "properties": {"id": v["id"], "name": v["name"], "gvpNumber": v["gvpNumber"], "elevationM": v["elevationM"], "observatory": v["observatory"],
                                     "coverage": v["coverage"], "lastEruption": {"start": last["start"], "vei": last["vei"]} if last else None,
                                     "eruptionsSince1900": sum(y >= 1900 for y in yr), "eruptionsSince2000": sum(y >= 2000 for y in yr), "file": f"volcano/{v['id']}.json"}})
    run_b.apply(models, load_ee("rain"), REG)  # EE run B: IMERG rain (only once its tables exist)
    story, reading = story_taal(next(v for v in vols if v["id"] == "taal"), models["taal"], as_of, hdr)
    models["taal"]["readings"] = [reading]
    for vid, vm in models.items():
        p = v_dir / "volcano" / f"{vid}.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(vm, separators=(",", ":"), ensure_ascii=False))
    (v_dir / "volcanoes.geojson").write_text(json.dumps({**hdr, "kind": "volcanoes", "type": "FeatureCollection", "features": feats}, separators=(",", ":"), ensure_ascii=False))
    (v_dir / "story").mkdir(exist_ok=True)
    (v_dir / "story" / "taal-2020.json").write_text(json.dumps(story, separators=(",", ":"), ensure_ascii=False))
    (v_dir / "assets").mkdir(exist_ok=True)
    for a in story["steps"][3]["assets"]:
        shutil.copy(BUILD / a["url"], v_dir / a["url"])
    so2_map = run_b.so2_monthly_layer(TABLES, v_dir, " ".join(REG["s5p-offl-so2"]["attribution"].split()))
    layers = [x for x in (thermal_layers(v_dir, as_of), quake_layer(v_dir, usgs), so2_map) if x]
    (v_dir / "layers.json").write_text(json.dumps({**hdr, "kind": "layers", "layers": layers}, ensure_ascii=False))
    checks = run_checks(v_dir, vols, models, gvp_v, gvp_e)
    passed = all(c["passed"] for c in checks)
    files = [{"path": str(p.relative_to(v_dir)), "bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
             for p in sorted(v_dir.rglob("*")) if p.is_file()]
    manifest = {**hdr, "kind": "manifest", "files": files, "checks": {"passed": passed, "results": checks}}
    usage = DATA / "state" / "ee-usage.json"
    if usage.exists():
        manifest["earthEngineUsage"] = json.loads(usage.read_text())
    (v_dir / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False))
    if passed:
        (site / "latest.json").write_text(json.dumps({"schemaVersion": "1", "kind": "latest", "current": f"v{version}", "base": f"v{version}/", "dataAsOf": as_of,
                                                       "generatedAt": hdr["generatedAt"], "previous": f"v{version - 1}" if version > 1 else None,
                                                       "mirrors": ["https://krtmtthw.dev/plumes/data/", "https://huggingface.co/datasets/permission-alluring/plumes/resolve/main/"]}, indent=1))
    return {"version": version, "passed": passed, "failed": [c for c in checks if not c["passed"]], "files": len(files),
            "bytes": sum(f["bytes"] for f in files)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", type=int, required=True)
    ap.add_argument("--as-of", default=dt.date.today().isoformat())
    a = ap.parse_args()
    print(json.dumps(build(a.version, a.as_of), indent=1))
