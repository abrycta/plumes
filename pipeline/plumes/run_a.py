"""Earth Engine run A, the pure half (LAYERS-PLAN §7 steps 4-6): crater-lake temperature, crater-lake area and colour,
and the S5P UV aerosol index in eruption windows.

This module has no Earth Engine import, so CI tests it on tiny fixtures. `plumes.ee_run_a` does the reductions and writes
the tables below; the functions here turn those tables into read-model series (contracts/README.md: new series ids may
appear, and the UI renders any `daily`/`events` entry from its label and unit).

Tables (data/tables, gitignored, one CSV per chunk so a backfill resumes across runs):
    ee-laketemp/<year>.csv   lake, volcano, date, time, sensor, scene, st_c, valid, total, st_qa_k
    ee-lakegsw/all.csv       lake, volcano, month, water_m2, valid_m2, total_m2
    ee-lakes2/<year>.csv     lake, volcano, date, scene, water_m2, clear_m2, total_m2, r, g, b
    ee-uvai/<YYYY-MM>.csv    volcano, ring, date, ai_mean, ai_max, valid, total
"""

from __future__ import annotations

import collections
import datetime as dt
import json
import pathlib

LAKES_FILE = pathlib.Path(__file__).resolve().parent / "data" / "crater-lakes.json"

# Landsat Collection 2 Level-2 surface temperature (USGS): DN * 0.00341802 + 149.0 = K; ST_QA DN * 0.01 = K uncertainty.
ST_SCALE, ST_OFFSET = 0.00341802, 149.0
# (asset, ST band, sensor label, first day, day after the last day used). ETM+ is used only until OLI starts: after
# 2003-05-31 its scan-line corrector is off (stripes cut the lake), and from about 2017 its overpass time drifts.
LANDSAT_ST = [
    ("LANDSAT/LT05/C02/T1_L2", "ST_B6", "TM", "2000-01-01", "2012-05-06"),
    ("LANDSAT/LE07/C02/T1_L2", "ST_B6", "ETM+", "2000-01-01", "2013-04-11"),
    ("LANDSAT/LC08/C02/T1_L2", "ST_B10", "OLI/TIRS", "2013-04-11", "2100-01-01"),
    ("LANDSAT/LC09/C02/T1_L2", "ST_B10", "OLI-2/TIRS-2", "2021-10-31", "2100-01-01"),
]
S2 = "COPERNICUS/S2_SR_HARMONIZED"
S2_START = "2017-03-28"
GSW = "JRC/GSW1_4/MonthlyHistory"
GSW_END = "2021-12"
S5P_AER_AI = "COPERNICUS/S5P/OFFL/L3_AER_AI"
S5P_AER_AI_BAND = "absorbing_aerosol_index"
S5P_AER_AI_START = "2018-07-04"
UVAI_RINGS = [15]
UVAI_BOX_KM = 50

# Quality thresholds for what is published (the tables keep every scene).
MIN_TEMP_PIXELS = 10  # clear water pixels in the core disc (30 m grid; the thermal band is 100-120 m native)
MIN_TEMP_SHARE = 0.5  # share of the core disc that is clear water
MIN_AREA_CLEAR = 0.9  # report area only when this share of the crater disc is clear ("cloud-free dates only")
MIN_LAKE_M2 = 200_000  # below this the crater is treated as dry: pools on wet ash reach about 0.15 km² (Taal, 2020-01-28)

# Sentinel-2 water test (ee_run_a.s2_water applies the same thresholds in Earth Engine). NDWI > 0 alone counted wet ash
# and haze as water (Taal 2020-09-19: 3.9 km² against a lake of about 1 km²); those surfaces are spectrally flat, so a
# SWIR and a NIR ceiling remove them while dark and turquoise lake water both pass.
WATER_MNDWI = 0.3  # (B3 - B11) / (B3 + B11)
WATER_NDWI = 0.2  # (B3 - B8) / (B3 + B8)
WATER_MAX_B11 = 0.08
WATER_MAX_B8 = 0.15

WINDOW_BEFORE_DAYS = 30
WINDOW_AFTER_DAYS = 30
VAAC_PAD_DAYS = 7


def lt(en: str, ja: str) -> dict:
    return {"en": en, "ja": ja}


def load_lakes(path: pathlib.Path = LAKES_FILE) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["lakes"]


def fnum(x):
    return None if x in (None, "", "None") else float(x)


def d(iso: str) -> dt.date:
    return dt.date.fromisoformat(iso[:10])


def months_between(start: str, end: str) -> list[str]:
    y, m = map(int, start[:7].split("-"))
    ye, me = map(int, end[:7].split("-"))
    out = []
    while (y, m) <= (ye, me):
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


# ---------------------------------------------------------------- eruption windows (UVAI)

def _gvp_day(r: dict, pre: str, last: bool) -> str | None:
    """A GVP partial date as a day: the first day of the year or month at the start, the last at the end."""
    y, m, dd = r.get(pre + "Year"), r.get(pre + "Month"), r.get(pre + "Day")
    if not y or int(y) < 1:
        return None
    y = int(y)
    m = int(m) if m and m != "0" else (12 if last else 1)
    if dd and dd != "0":
        return dt.date(y, m, int(dd)).isoformat()
    if not last:
        return dt.date(y, m, 1).isoformat()
    nxt = dt.date(y + (m == 12), 1 if m == 12 else m + 1, 1)
    return (nxt - dt.timedelta(days=1)).isoformat()


def eruption_windows(volcanoes: list[dict], gvp_eruptions: list[dict], vaac_days: dict[int, list[str]] | None, as_of: str,
                     since: str = S5P_AER_AI_START) -> dict[str, list[tuple[str, str]]]:
    """volcano id -> merged [(start, end)] windows: each GVP eruption from 30 days before its start to 30 days after its
    end (GVP's ">" end modifier, "continuing", runs to `as_of`; no end date counts as a one-day or one-period eruption), and each Tokyo VAAC advisory day +-7 days. Clipped to
    [since, as_of]. `volcanoes` rows need `id` and `gvpNumber`."""
    by_gvp = {v["gvpNumber"]: v["id"] for v in volcanoes if v.get("gvpNumber")}
    raw: dict[str, list[tuple[dt.date, dt.date]]] = collections.defaultdict(list)
    lo, hi = d(since), d(as_of)
    for e in gvp_eruptions:
        vid = by_gvp.get(int(e["Volcano_Number"]))
        s = _gvp_day(e, "StartDate", last=False)
        if not vid or not s:
            continue
        if (e.get("EndDateYearModifier") or "").strip() == ">":
            en = as_of  # continuing when GVP last reported
        else:
            en = _gvp_day(e, "EndDate", last=True) or _gvp_day(e, "StartDate", last=True)
        raw[vid].append((d(s) - dt.timedelta(days=WINDOW_BEFORE_DAYS), d(en) + dt.timedelta(days=WINDOW_AFTER_DAYS)))
    for gvp, days in (vaac_days or {}).items():
        vid = by_gvp.get(gvp)
        if vid:
            raw[vid] += [(d(x) - dt.timedelta(days=VAAC_PAD_DAYS), d(x) + dt.timedelta(days=VAAC_PAD_DAYS)) for x in days]
    out = {}
    for vid, spans in raw.items():
        merged: list[list[dt.date]] = []
        for a, b in sorted(spans):
            a, b = max(a, lo), min(b, hi)
            if a > b:
                continue
            if merged and a <= merged[-1][1] + dt.timedelta(days=1):
                merged[-1][1] = max(merged[-1][1], b)
            else:
                merged.append([a, b])
        if merged:
            out[vid] = [(a.isoformat(), b.isoformat()) for a, b in merged]
    return out


def window_months(windows: dict[str, list[tuple[str, str]]]) -> list[str]:
    """Calendar months touched by any window: the months the UVAI reduction runs for (one aggregation a month)."""
    out = set()
    for spans in windows.values():
        for a, b in spans:
            out.update(months_between(a, b))
    return sorted(out)


def in_windows(day: str, spans: list[tuple[str, str]]) -> bool:
    return any(a <= day <= b for a, b in spans)


# ---------------------------------------------------------------- colour

def srgb_hex(r: float | None, g: float | None, b: float | None, white: float = 0.15) -> str | None:
    """Mean surface reflectance (0-1) to a display colour: linear stretch to `white`, then the sRGB transfer curve.
    Descriptive only (LAYERS-PLAN: colour is not water chemistry)."""
    if None in (r, g, b):
        return None

    def ch(x: float) -> int:
        x = min(max(x / white, 0.0), 1.0)
        x = 12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055
        return round(x * 255)

    return f"#{ch(r):02x}{ch(g):02x}{ch(b):02x}"


# ---------------------------------------------------------------- Sentinel-2 water test

def _nd(a: float, b: float) -> float:
    return (a - b) / (a + b) if a + b else 0.0


def is_water(b3: float, b8: float, b11: float) -> bool:
    """One clear Sentinel-2 pixel (surface reflectance 0-1): water or not. The reference for ee_run_a.s2_water."""
    return (_nd(b3, b11) > WATER_MNDWI or _nd(b3, b8) > WATER_NDWI) and b11 < WATER_MAX_B11 and b8 < WATER_MAX_B8


# ---------------------------------------------------------------- read-model series

def gone_spans(lake: dict, s2_rows: list[dict]) -> list[tuple[str, str | None]]:
    """The lake's 'gone' spans; an open end is closed at the first publishable Sentinel-2 scene after the start that
    sees at least MIN_LAKE_M2 of water. Still open (None) if no such scene exists yet."""
    out = []
    for g in lake.get("gone", []):
        end = g.get("end")
        if end is None:
            back = sorted(r["date"] for r in s2_rows if r["lake"] == lake["id"] and r["date"] > g["start"] and _s2_ok(r)
                          and (fnum(r["water_m2"]) or 0) >= MIN_LAKE_M2)
            end = back[0] if back else None
        out.append((g["start"], end))
    return out


def _gone(day: str, spans: list[tuple[str, str | None]]) -> bool:
    return any(a <= day and (b is None or day < b) for a, b in spans)


def _s2_ok(r: dict) -> bool:
    t = fnum(r["total_m2"]) or 0
    return t > 0 and (fnum(r["clear_m2"]) or 0) / t >= MIN_AREA_CLEAR


def lake_temp_series(lake: dict, temp_rows: list[dict], s2_rows: list[dict]) -> dict:
    """events.lake_temp_landsat: one row per clear Landsat scene, the median surface temperature of the clear water
    pixels in the core disc. Several scenes on one day (overlapping paths) keep the one with the most valid pixels."""
    gone = gone_spans(lake, s2_rows)
    best: dict[str, dict] = {}
    for r in temp_rows:
        if r["lake"] != lake["id"]:
            continue
        valid, total, st = int(float(r["valid"] or 0)), int(float(r["total"] or 0)), fnum(r["st_c"])
        if st is None or valid < MIN_TEMP_PIXELS or not total or valid / total < MIN_TEMP_SHARE or _gone(r["date"], gone):
            continue
        if r["date"] not in best or valid > int(float(best[r["date"]]["valid"])):
            best[r["date"]] = r
    rows = [[day, round(fnum(r["st_c"]), 1), int(float(r["valid"])), None if fnum(r["st_qa_k"]) is None else round(fnum(r["st_qa_k"]), 1), r["sensor"]]
            for day, r in sorted(best.items())]
    gone_txt = "; ".join(f"{a} to {b or 'the lake’s return'}" for a, b in gone)
    gone_ja = "、".join(f"{a}〜{b or '湖の回復'}" for a, b in gone)
    note = lt("Satellite skin temperature of the lake surface (top millimetres), not PHIVOLCS's in-lake readings; clear scenes only, "
              "the lake edge left out. ETM+ scenes from June 2003 have stripes of missing pixels." + (f" No lake: {gone_txt}." if gone else ""),
              "湖面の表皮温度(衛星)で、PHIVOLCSの湖水測定値ではない。晴天時のみ、湖岸は除外。2003年6月以降のETM+には欠測の縞がある。"
              + (f"湖なし:{gone_ja}。" if gone else ""))
    return {"lake_temp_landsat": {"source": ["landsat-surface-temperature"], "label": lt(f"{lake['name']['en']}: surface temperature (Landsat)",
                                                                                         f"{lake['name']['ja']}:表面温度(Landsat)"),
                                  "cols": ["date", "tempC", "validPx", "uncertaintyK", "sensor"],
                                  "units": {"tempC": "°C", "validPx": "pixels", "uncertaintyK": "K"},
                                  "start": LANDSAT_ST[0][3], "rows": rows, "note": note}}


def lake_area_series(lake: dict, gsw_rows: list[dict], s2_rows: list[dict]) -> dict:
    """events.lake_area_gsw (monthly water area from JRC GSW, Landsat-based, 2000-01 to 2021-12) and events.lake_area_s2
    (water area and colour per clear Sentinel-2 day, 2017-03 onward). Only months or days with at least 90 % of the
    crater disc observed are published; a dry crater is a real 0, never a gap."""
    out = {}
    g = []
    for r in sorted((r for r in gsw_rows if r["lake"] == lake["id"]), key=lambda r: r["month"]):
        t, v = fnum(r["total_m2"]) or 0, fnum(r["valid_m2"]) or 0
        if t and v / t >= MIN_AREA_CLEAR:
            g.append([r["month"] + "-01", round((fnum(r["water_m2"]) or 0) / 1e6, 3), round(v / t, 2)])
    if g:
        out["lake_area_gsw"] = {"source": ["jrc-global-surface-water"], "label": lt(f"{lake['name']['en']}: water area, monthly (JRC Global Surface Water)",
                                                                                     f"{lake['name']['ja']}:水面積(月別、JRC全球地表水)"),
                                "cols": ["date", "areaKm2", "observed"], "units": {"areaKm2": "km²"},
                                "start": "2000-01-01", "rows": g,
                                "note": lt("Monthly water map from Landsat; ends December 2021. The date is the first day of the month.",
                                           "Landsatによる月別の水域図。2021年12月で終了。日付は月の初日。")}
    best: dict[str, dict] = {}
    for r in s2_rows:
        if r["lake"] != lake["id"] or not _s2_ok(r):
            continue
        if r["date"] not in best or (fnum(r["clear_m2"]) or 0) > (fnum(best[r["date"]]["clear_m2"]) or 0):
            best[r["date"]] = r
    s = []
    for day, r in sorted(best.items()):
        w = fnum(r["water_m2"]) or 0
        colour = srgb_hex(fnum(r["r"]), fnum(r["g"]), fnum(r["b"])) if w >= MIN_LAKE_M2 else None
        s.append([day, round(w / 1e6, 3), round((fnum(r["clear_m2"]) or 0) / (fnum(r["total_m2"]) or 1), 2), colour])
    if s:
        out["lake_area_s2"] = {"source": ["s2-sr-harmonized"], "label": lt(f"{lake['name']['en']}: water area and colour (Sentinel-2)",
                                                                          f"{lake['name']['ja']}:水面積と色(Sentinel-2)"),
                               "cols": ["date", "areaKm2", "observed", "colour"], "units": {"areaKm2": "km²"},
                               "start": S2_START, "rows": s,
                               "note": lt("Water found by the green and near-infrared bands on cloud-free days. The colour is the lake's mean "
                                          "true colour, for description only: it does not measure water chemistry.",
                                          "雲のない日に緑と近赤外のバンドで水域を判定。色は湖の平均的な見た目の色で、水質を示すものではない。")}
    return out


def uvai_series(vid: str, uvai_rows: list[dict], spans: list[tuple[str, str]]) -> dict:
    """events.uvai_s5p_15km and events.uvai_s5p_50km: the daily highest and mean UV aerosol index, eruption windows only."""
    if not spans:
        return {}
    out = {}
    note = lt("Shown only around eruptions (30 days either side of each GVP eruption, 7 days around each Tokyo VAAC advisory). "
              "Unitless; positive values mean UV-absorbing particles (ash, smoke or dust: not ash alone); no signal under cloud.",
              "噴火の前後のみ表示(GVPの各噴火の前後30日、東京VAACの各情報の前後7日)。無次元。正の値は紫外線を吸収する粒子"
              "(火山灰・煙・砂塵で、火山灰だけではない)を示す。雲の下は観測できない。")
    for ring, sid, label in ((f"{UVAI_RINGS[0]}km", f"uvai_s5p_{UVAI_RINGS[0]}km", lt("TROPOMI UV aerosol index within 15 km", "TROPOMI 紫外吸収性エアロゾル指数(15 km圏)")),
                             (f"box{UVAI_BOX_KM}km", f"uvai_s5p_{UVAI_BOX_KM}km", lt("TROPOMI UV aerosol index within the 50 km box", "TROPOMI 紫外吸収性エアロゾル指数(50 km範囲)"))):
        rows = []
        for r in sorted((r for r in uvai_rows if r["volcano"] == vid and r["ring"] == ring and in_windows(r["date"], spans)), key=lambda r: r["date"]):
            valid, total = int(float(r["valid"] or 0)), int(float(r["total"] or 0))
            if not valid or fnum(r["ai_max"]) is None:
                continue
            rows.append([r["date"], round(fnum(r["ai_max"]), 2), round(fnum(r["ai_mean"]), 2), round(valid / total, 3) if total else None])
        out[sid] = {"source": ["s5p-offl-aer-ai"], "label": label, "cols": ["date", "aiMax", "aiMean", "coverage"],
                    "units": {},
                    "ringKm": UVAI_BOX_KM if ring.startswith("box") else UVAI_RINGS[0],
                    "start": S5P_AER_AI_START, "rows": rows, "note": note}
    return out


def volcano_series(vid: str, lakes: list[dict], tables: dict[str, list[dict]], windows: dict[str, list[tuple[str, str]]]) -> dict:
    """Everything run A adds to one volcano's `events` (empty when its tables are absent: nothing changes before the run)."""
    out = {}
    for lake in (x for x in lakes if x["volcano"] == vid):
        s2 = tables.get("lakes2", [])
        if tables.get("laketemp"):
            out.update(lake_temp_series(lake, tables["laketemp"], s2))
        out.update(lake_area_series(lake, tables.get("lakegsw", []), s2))
    if tables.get("uvai"):
        out.update(uvai_series(vid, tables["uvai"], windows.get(vid, [])))
    return out


EE_ASSETS = [a for a, *_ in LANDSAT_ST] + [S2, GSW, S5P_AER_AI]
SOURCE_IDS = ["landsat-surface-temperature", "s2-sr-harmonized", "jrc-global-surface-water", "s5p-offl-aer-ai"]
