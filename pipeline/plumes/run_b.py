"""Read models for Earth Engine run B (LAYERS-PLAN §7 steps 7 and 8): the IMERG daily rain series per volcano and the
national monthly SO2 map layer. Pure functions over the tables `plumes.ee_run_b` writes, so they are tested without
Earth Engine.

Tables (data/tables, gitignored; adopted into plumes-archive with the bundles in plumes.adopt):
  ee-rain/<YYYY-MM>.csv            volcano, ring, date, rain_mm, halfhours   (IMERG Final run only)
  ee-so2-monthly/<YYYY-MM>.tif     int16 GeoTIFF, band 1 = mean SO2 column (µmol/m², rounded), band 2 = valid days (% of the month)
"""

from __future__ import annotations

import datetime as dt
import pathlib
import shutil

RAIN_ID = "rain_imerg_15km"
RAIN_SOURCE = "gpm-imerg-v07"
RAIN_RING = "15km"
#: A day counts only when Earth Engine held at least this many of its 48 half-hourly Final images.
RAIN_MIN_HALFHOURS = 44

SO2_SOURCE = "s5p-offl-so2"
SO2_SCALE = 1  # stored value = µmol/m² (a monthly mean stays far below 32,767; single days can exceed it)
SO2_BOUNDS = (116.0, 4.0, 128.0, 22.0)
SO2_DEG = 0.1
#: Legend classes (µmol/m², lower bounds) for the five Akari sequential colours; below the first, nothing is drawn.
#: [U] Provisional: to be set from the canary month and checked against the backfill (98th percentile of volcanic pixels).
SO2_STOPS = [25, 50, 100, 200, 400]
#: A pixel is drawn only when at least this share of the month's days had a valid value there.
SO2_MIN_VALID_PCT = 10


def lt(en: str, ja: str) -> dict:
    return {"en": en, "ja": ja}


def _num(v) -> float | None:
    if v in (None, ""):
        return None
    try:
        return float(v)
    except ValueError:
        return None


def rain_series(vid: str, rows: list[dict]) -> dict:
    """The volcano file's `daily` entry `rain_imerg_15km`: mm a day (UTC days), mean over the 15 km ring.

    A day with too few Final half-hours is a gap (null), never zero. The span ends on the last Final day held."""
    by = {r["date"]: r for r in rows if r["volcano"] == vid and r["ring"] == RAIN_RING}
    if not by:
        return {}
    start, end = min(by), max(by)
    n = (dt.date.fromisoformat(end) - dt.date.fromisoformat(start)).days + 1
    values: list[float | None] = [None] * n
    for d, r in by.items():
        mm, hh = _num(r["rain_mm"]), _num(r["halfhours"])
        if mm is None or hh is None or hh < RAIN_MIN_HALFHOURS:
            continue
        values[(dt.date.fromisoformat(d) - dt.date.fromisoformat(start)).days] = round(max(mm, 0.0), 1)
    return {RAIN_ID: {
        "source": [RAIN_SOURCE], "unit": "mm", "ringKm": 15, "start": start,
        "label": lt("Rain, satellite estimate (GPM IMERG Final), mean within 15 km", "雨量の衛星推定(GPM IMERG Final)、15 km圏平均"),
        "values": values,
        "note": lt("A box average on a 0.1° grid (about 11 km), not a rain gauge; UTC days; Final run only, so the series ends "
                   "months before today (the Final run's own delay). Shown beside lahar dates for context, never as a threshold.",
                   "0.1°格子(約11 km)の範囲平均で、雨量計ではない。UTC日。Final版のみのため、数か月前で終わる(Final版の遅れ)。"
                   "ラハールの日付の参考として示すもので、基準値ではない。"),
    }}


def so2_months(tables: pathlib.Path) -> list[str]:
    return sorted(p.stem for p in (tables / "ee-so2-monthly").glob("*.tif"))


def so2_monthly_layer(tables: pathlib.Path, out_dir: pathlib.Path, attribution: str) -> dict | None:
    """Copy the monthly GeoTIFFs into the version (layers/so2/<YYYY-MM>.tif) and return the `so2-monthly` layer entry."""
    months = so2_months(tables)
    if not months:
        return None
    dst = out_dir / "layers" / "so2"
    dst.mkdir(parents=True, exist_ok=True)
    for m in months:
        shutil.copy(tables / "ee-so2-monthly" / f"{m}.tif", dst / f"{m}.tif")
    time = {"step": "month", "start": months[0], "end": months[-1]}
    every = list(_month_range(months[0], months[-1]))
    if every != months:
        time["available"] = months
    w, s, e, n = SO2_BOUNDS
    return {
        "id": "so2-monthly", "title": lt("SO₂, monthly mean (Sentinel-5P TROPOMI)", "SO₂月平均(Sentinel-5P TROPOMI)"), "format": "cog",
        "url": "layers/so2/{month}.tif", "time": time, "minzoom": 4, "maxzoom": 10, "bounds": [w, s, e, n],
        "legend": {"unit": "µmol/m²", "stops": [[v, f"≥ {v}"] for v in SO2_STOPS]},
        "sources": [SO2_SOURCE], "attribution": attribution,
        "note": lt("Monthly mean of the daily means on a 0.1° grid: single-day plumes are smoothed out, and cloudy days add nothing. "
                   "A column amount, not an emission rate. "
                   f"Pixels with fewer than {SO2_MIN_VALID_PCT} % valid days are not drawn. "
                   "File: band 1 = mean column in µmol/m² (nodata -32768), band 2 = share of the month's days with a valid pixel (%).",
                   "0.1°格子での日平均の月平均。1日だけの噴煙は平滑化され、曇りの日は含まれない。放出率ではなくカラム量。"
                   f"有効日が{SO2_MIN_VALID_PCT}%未満の画素は表示しない。バンド2は各画素の有効日の割合。"),
    }


def _month_range(a: str, b: str):
    y, m = map(int, a.split("-"))
    while f"{y:04d}-{m:02d}" <= b:
        yield f"{y:04d}-{m:02d}"
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def apply(models: dict, rain_rows: list[dict], registry: dict) -> int:
    """Add `rain_imerg_15km` to each volcano model that has rows, with its provenance record and EE asset. Returns how many."""
    n = 0
    e = registry[RAIN_SOURCE]
    rec = {"id": RAIN_SOURCE, "attribution": " ".join(e["attribution"].split()), "licence": " ".join(e["licence"].split()), "fromArchive": False}
    for vid, vm in models.items():
        s = rain_series(vid, rain_rows)
        if not s:
            continue
        vm["daily"] = {**vm.get("daily", {}), **s}
        prov = vm.setdefault("provenance", {})
        if not any(x["id"] == RAIN_SOURCE for x in prov.setdefault("sources", [])):
            prov["sources"].append(rec)
        assets = prov.setdefault("earthEngine", {}).setdefault("assets", [])
        if "NASA/GPM_L3/IMERG_V07" not in assets:
            assets.append("NASA/GPM_L3/IMERG_V07")
        n += 1
    return n
