"""Earth Engine run B (LAYERS-PLAN §7 steps 7 and 8): GPM IMERG daily rain per volcano ring, and the national monthly
TROPOMI SO2 map. Both follow ee_series: one interactive aggregation per month under the budget guard, a month already
in data/tables is skipped (resumable), and the first failure stops the run (fail-fast, workspace rule 18).

Gate (DECISIONS S8): Kurt reads the project's monthly EE total in the console first; then a one-month canary per step,
whose EECU-seconds land in ee-usage.json and size the backfill; only then the backfill.

    EE_KEY_FILE=… uv run python -m plumes.ee_run_b rain --canary 2020-01           # one month + a backfill estimate
    EE_KEY_FILE=… uv run python -m plumes.ee_run_b so2-map --canary 2020-01
    EE_KEY_FILE=… uv run python -m plumes.ee_run_b rain --start 2000-01 --end 2025-09 --max-eecu-h 4
    EE_KEY_FILE=… uv run python -m plumes.ee_run_b so2-map --start 2018-12 --end 2026-09 --max-eecu-h 2
"""

from __future__ import annotations

import argparse
import datetime as dt
import json

import ee

from plumes.ee_budget import Budget, BudgetExceeded, init
from plumes.ee_series import _write, months, ring_fc
from plumes.geotiff import NODATA, write_int16
from plumes.paths import DATA, TABLES
from plumes.run_b import SO2_BOUNDS, SO2_DEG, SO2_SCALE

IMERG = "NASA/GPM_L3/IMERG_V07"
IMERG_BAND = "precipitation"  # mm/hr, calibrated (gauge-adjusted in the Final run)
IMERG_FINAL = "permanent"  # image property `status`: "permanent" = Final run, "provisional" = Late/Early (checked 2026-10-22)
IMERG_SCALE = 11132  # 0.1 degree at the equator
RAIN_RINGS = [15]
RAIN_COLS = ["volcano", "ring", "date", "rain_mm", "halfhours"]
S5P = "COPERNICUS/S5P/OFFL/L3_SO2"
S5P_BAND = "SO2_column_number_density"  # planetary-boundary-layer a priori, as the volcano series (so2_s5p_15km)
DEFAULT_RANGE = {"rain": ("2000-01", None), "so2-map": ("2018-12", None)}


def _days(month: str) -> list[dt.date]:
    y, m = map(int, month.split("-"))
    first = dt.date(y, m, 1)
    nxt = (first.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
    return [first + dt.timedelta(days=i) for i in range((nxt - first).days)]


def rain_month(month: str, budget: Budget) -> list[dict]:
    """Daily rain (mm, UTC day) per volcano ring from the Final half-hourly images, and how many of the 48 were held.

    Daily images are stacked as bands (d<NN>_mm, d<NN>_n) of one image and reduced once over every ring (area-weighted
    mean at the native 0.1 degree), as so2_month does."""
    fc = ring_fc(RAIN_RINGS)
    col = ee.ImageCollection(IMERG).filter(ee.Filter.eq("status", IMERG_FINAL)).select(IMERG_BAND)
    days = _days(month)
    empty = ee.Image.constant(0).rename(IMERG_BAND).updateMask(ee.Image.constant(0))
    bands = []
    for i, d in enumerate(days):
        d0 = ee.Date(d.isoformat())
        c = col.filterDate(d0, d0.advance(1, "day"))
        mean = ee.Image(ee.Algorithms.If(c.size().gt(0), c.mean(), empty))
        bands.append(mean.multiply(24).rename(f"d{i:02d}_mm").addBands(ee.Image.constant(c.size()).toInt16().rename(f"d{i:02d}_n")))
    stack = ee.Image.cat(bands)
    feats = budget.get(stack.reduceRegions(fc, ee.Reducer.mean(), scale=IMERG_SCALE).map(lambda f: f.setGeometry(None)))["features"]
    rows = []
    for f in feats:
        p = f["properties"]
        for i, d in enumerate(days):
            mm, n = p.get(f"d{i:02d}_mm"), p.get(f"d{i:02d}_n")
            rows.append({"volcano": p["volcano"], "ring": p["ring"], "date": d.isoformat(),
                         "rain_mm": None if mm is None else round(mm, 2), "halfhours": None if n is None else round(n)})
    return rows


def so2_map_month(month: str, budget: Budget) -> list[list[list[int]]]:
    """National monthly SO2 on a 0.1 degree grid over SO2_BOUNDS: [mean column x SO2_SCALE in µmol/m², valid-day %].

    The month's daily means (as in so2_month) are averaged per pixel; pixels with no valid day are nodata."""
    days = _days(month)
    col = ee.ImageCollection(S5P).select(S5P_BAND)
    daily = []
    for d in days:
        d0 = ee.Date(d.isoformat())
        c = col.filterDate(d0, d0.advance(1, "day"))
        daily.append(ee.Image(ee.Algorithms.If(c.size().gt(0), c.mean(), ee.Image.constant(0).rename(S5P_BAND).updateMask(ee.Image.constant(0)))))
    stack = ee.ImageCollection(daily)
    mean = stack.mean().multiply(1e6 * SO2_SCALE).round().clamp(-32767, 32767).toInt16().rename("so2")
    valid = stack.count().multiply(100.0 / len(days)).round().toInt16().rename("valid")
    w, s, e, n = SO2_BOUNDS
    width, height = round((e - w) / SO2_DEG), round((n - s) / SO2_DEG)
    grid = mean.addBands(valid.unmask(0)).reproject(crs="EPSG:4326", crsTransform=[SO2_DEG, 0, w, 0, -SO2_DEG, n])
    region = ee.Geometry.Rectangle([w + SO2_DEG / 2, s + SO2_DEG / 2, e - SO2_DEG / 2, n - SO2_DEG / 2], "EPSG:4326", False)
    props = budget.get(grid.sampleRectangle(region=region, defaultValue=NODATA))["properties"]
    so2, vd = props["so2"], props["valid"]
    if len(so2) != height or len(so2[0]) != width:
        raise RuntimeError(f"so2-map {month}: got {len(so2)}x{len(so2[0])} pixels, expected {height}x{width}")
    return [so2, vd]


def run(step: str, todo: list[str], budget: Budget, max_eecu_h: float | None) -> dict:
    done = skipped = 0
    for m in todo:
        path = TABLES / ("ee-rain" if step == "rain" else "ee-so2-monthly") / (f"{m}.csv" if step == "rain" else f"{m}.tif")
        if path.exists():
            skipped += 1
            continue
        if max_eecu_h is not None and budget.run_s >= max_eecu_h * 3600:
            raise BudgetExceeded(f"{step}: this run reached its own cap of {max_eecu_h} EECU-h after {done} months")
        before = budget.run_s
        if step == "rain":
            _write(path, rain_month(m, budget), RAIN_COLS)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(write_int16(so2_map_month(m, budget), SO2_BOUNDS, ["so2_umol_m2", "valid_days_pct"]))
        done += 1
        print(f"  {step} {m}: {budget.run_s - before:.1f} EECU-s; run {budget.run_s:.0f} EECU-s", flush=True)
    return {"months_done": done, "months_skipped": skipped}


def estimate(step: str, eecu_s_month: float, start: str, end: str) -> dict:
    n = len(list(months(start, end)))
    return {"step": step, "canary_eecu_s": round(eecu_s_month, 1), "backfill_months": n, "backfill_range": f"{start}..{end}",
            "backfill_eecu_h_estimate": round(eecu_s_month * n / 3600, 2)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["rain", "so2-map"])
    ap.add_argument("--canary", metavar="YYYY-MM", help="run this one month and print the backfill estimate")
    ap.add_argument("--start")
    ap.add_argument("--end", help="default: rain 2025-09 (the last Final month seen 2026-10-22), so2-map the last whole month")
    ap.add_argument("--max-eecu-h", type=float, help="stop this run before a month once it has used this much (below the 10 EECU-h run cap)")
    a = ap.parse_args()
    start = a.start or DEFAULT_RANGE[a.step][0]
    end = a.end or ("2025-09" if a.step == "rain" else (dt.date.today().replace(day=1) - dt.timedelta(days=1)).strftime("%Y-%m"))
    init()
    budget = Budget(DATA / "state" / "ee-usage.json")
    label = f"run B {a.step} " + (f"canary {a.canary}" if a.canary else f"{start}..{end}")
    try:
        if a.canary:
            res = run(a.step, [a.canary], budget, None)
            res["estimate"] = estimate(a.step, budget.run_s, start, end)
        else:
            res = run(a.step, list(months(start, end)), budget, a.max_eecu_h)
    finally:
        print(json.dumps(budget.save(label)))
    print(json.dumps(res))
