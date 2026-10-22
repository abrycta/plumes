"""Earth Engine run A (LAYERS-PLAN §7 steps 4-6): crater-lake temperature (Landsat), crater-lake area and colour (JRC GSW
monthly, Sentinel-2), and the S5P UV aerosol index in eruption windows. Same pattern as plumes.ee_series: images are
reduced where they live, only small tables come back, every call runs under the budget guard (ee_budget), and chunks
already in data/tables are skipped so a backfill resumes.

Gate (S8): Kurt reads the project's monthly Earth Engine total in the Cloud console before the run. Until then only the
single-image smoke test may run.

    EE_KEY_FILE=… uv run python -m plumes.ee_run_a smoke                      # one GSW image, both lakes
    EE_KEY_FILE=… uv run python -m plumes.ee_run_a canary                     # 2019 lake temp + 2020 S2 + GSW + UVAI 2020-01
    EE_KEY_FILE=… uv run python -m plumes.ee_run_a laketemp --start 2000 --end 2026
    EE_KEY_FILE=… uv run python -m plumes.ee_run_a lakegsw
    EE_KEY_FILE=… uv run python -m plumes.ee_run_a lakes2 --start 2017 --end 2026
    EE_KEY_FILE=… uv run python -m plumes.ee_run_a uvai --windows --as-of 2026-09-30
    EE_KEY_FILE=… uv run python -m plumes.ee_run_a uvai --start 2020-01 --end 2020-01

`--stop-after-s N` stops a step after the chunk that takes this run past N EECU-seconds (a per-step guard under the
10 EECU-h run cap).
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json

import ee

from plumes import run_a
from plumes.ee_budget import Budget, init
from plumes.paths import CROSSWALK, DATA, RAW, TABLES

COLS = {
    "laketemp": ["lake", "volcano", "date", "time", "sensor", "scene", "st_c", "valid", "total", "st_qa_k"],
    "lakegsw": ["lake", "volcano", "month", "water_m2", "valid_m2", "total_m2"],
    "lakes2": ["lake", "volcano", "date", "scene", "water_m2", "clear_m2", "total_m2", "r", "g", "b"],
    "uvai": ["volcano", "ring", "date", "ai_mean", "ai_max", "valid", "total"],
}
S2_CLEAR_SCL = [2, 4, 5, 6, 7, 11]  # dark area, vegetation, bare, water, unclassified, snow; not shadow, cloud or cirrus


def _write(path, rows, cols):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def _disc(lake: dict, key: str) -> ee.Geometry:
    return ee.Geometry.Point([lake["lon"], lake["lat"]]).buffer(lake[key])


def _props(feats: list[dict]) -> list[dict]:
    return [f["properties"] for f in feats]


# ---------------------------------------------------------------- lake temperature (Landsat C2 L2 ST)

def laketemp_year(year: int, budget: Budget, lakes: list[dict]) -> list[dict]:
    """Every Landsat scene over each lake's core disc in `year`: median ST (°C) and median ST_QA (K) of the pixels that
    QA_PIXEL marks as water and not fill, dilated cloud, cirrus, cloud or cloud shadow; their count; the disc's count."""
    reducer = ee.Reducer.median().combine(ee.Reducer.count(), sharedInputs=True)
    out = ee.FeatureCollection([])
    for lake in lakes:
        core = _disc(lake, "coreM")
        for asset, band, sensor, a, b in run_a.LANDSAT_ST:
            lo, hi = max(a, f"{year}-01-01"), min(b, f"{year + 1}-01-01")
            if lo >= hi:
                continue

            def per(img, band=band, sensor=sensor, lake=lake, core=core):
                qa = img.select("QA_PIXEL")
                ok = qa.bitwiseAnd(0b11111).eq(0).And(qa.bitwiseAnd(1 << 7).neq(0))
                st = img.select(band).multiply(run_a.ST_SCALE).add(run_a.ST_OFFSET - 273.15).updateMask(ok).rename("st")
                qk = img.select("ST_QA").multiply(0.01).updateMask(ok).rename("qa")
                stack = st.addBands(qk).addBands(ee.Image.constant(1).rename("total"))
                r = stack.reduceRegion(reducer, core, 30, maxPixels=1e6)
                return ee.Feature(None, {"lake": lake["id"], "volcano": lake["volcano"], "sensor": sensor,
                                         "date": img.date().format("YYYY-MM-dd"), "time": img.date().format("HH:mm"),
                                         "scene": img.get("LANDSAT_PRODUCT_ID"), "st_c": r.get("st_median"), "valid": r.get("st_count"),
                                         "total": r.get("total_count"), "st_qa_k": r.get("qa_median")})
            out = out.merge(ee.ImageCollection(asset).filterBounds(core).filterDate(lo, hi).map(per))
    return _props(budget.get(out)["features"])


# ---------------------------------------------------------------- lake area and colour

def lakegsw(budget: Budget, lakes: list[dict], start: str = "2000-01", end: str = run_a.GSW_END) -> list[dict]:
    """JRC GSW MonthlyHistory (band water: 0 no data, 1 not water, 2 water) over each crater disc, every month."""
    col = ee.ImageCollection(run_a.GSW).filterDate(start + "-01", ee.Date(end + "-01").advance(1, "month"))
    out = ee.FeatureCollection([])
    for lake in lakes:
        crater = _disc(lake, "craterM")

        def per(img, lake=lake, crater=crater):
            w = img.select("water")
            px = ee.Image.pixelArea()
            stack = px.updateMask(w.eq(2)).rename("water").addBands(px.updateMask(w.gt(0)).rename("valid")).addBands(px.rename("total"))
            r = stack.reduceRegion(ee.Reducer.sum(), crater, 30, maxPixels=1e7)
            return ee.Feature(None, {"lake": lake["id"], "volcano": lake["volcano"], "month": img.date().format("YYYY-MM"),
                                     "water_m2": r.get("water"), "valid_m2": r.get("valid"), "total_m2": r.get("total")})
        out = out.merge(col.map(per))
    return _props(budget.get(out)["features"])


def lakes2_year(year: int, budget: Budget, lakes: list[dict]) -> list[dict]:
    """Every Sentinel-2 L2A granule over each crater disc in `year`: water area (NDWI = (B3 - B8) / (B3 + B8) > 0 on clear
    pixels), clear area (SCL not cloud, shadow, cirrus or no data), disc area, and the mean B4/B3/B2 reflectance of the
    water (as area-weighted sums divided here)."""
    lo, hi = max(run_a.S2_START, f"{year}-01-01"), f"{year + 1}-01-01"
    out = ee.FeatureCollection([])
    for lake in lakes:
        crater = _disc(lake, "craterM")

        def per(img, lake=lake, crater=crater):
            scl = img.select("SCL")
            clear = scl.remap(S2_CLEAR_SCL, [1] * len(S2_CLEAR_SCL), 0)
            refl = img.select(["B4", "B3", "B2", "B8"]).divide(10000)
            water = refl.normalizedDifference(["B3", "B8"]).gt(0).And(clear)
            px = ee.Image.pixelArea()
            wpx = px.updateMask(water)
            stack = (wpx.rename("water").addBands(px.updateMask(clear).rename("clear")).addBands(px.rename("total"))
                     .addBands(refl.select(["B4", "B3", "B2"]).multiply(wpx).rename(["r", "g", "b"])))
            r = stack.reduceRegion(ee.Reducer.sum(), crater, 10, maxPixels=1e7)
            return ee.Feature(None, {"lake": lake["id"], "volcano": lake["volcano"], "date": img.date().format("YYYY-MM-dd"),
                                     "scene": img.get("system:index"), "water_m2": r.get("water"), "clear_m2": r.get("clear"),
                                     "total_m2": r.get("total"), "r": r.get("r"), "g": r.get("g"), "b": r.get("b")})
        out = out.merge(ee.ImageCollection(run_a.S2).filterBounds(crater).filterDate(lo, hi).map(per))
    rows = _props(budget.get(out)["features"])
    for r in rows:  # area-weighted sums -> mean reflectance of the water pixels
        w = r.get("water_m2") or 0
        for k in ("r", "g", "b"):
            r[k] = (r[k] / w) if w and r.get(k) is not None else None
    return rows


# ---------------------------------------------------------------- UV aerosol index

def uvai_month(month: str, budget: Budget) -> list[dict]:
    """Daily TROPOMI UV aerosol index per volcano (15 km ring and 50 km box): mean, max and valid-pixel count of the day's
    mean image. One aggregation a month (the B4 pattern of plumes.ee_series.so2_month): the daily images are bands of one
    image, reduced once over every ring."""
    from plumes.ee_series import ring_fc  # shared helper, read-only use

    fc = ring_fc(run_a.UVAI_RINGS, box_km=run_a.UVAI_BOX_KM)
    col = ee.ImageCollection(run_a.S5P_AER_AI).select(run_a.S5P_AER_AI_BAND)
    y, m = map(int, month.split("-"))
    first = dt.date(y, m, 1)
    ndays = ((first.replace(day=28) + dt.timedelta(days=4)).replace(day=1) - first).days
    empty = ee.Image.constant(0).rename(run_a.S5P_AER_AI_BAND).updateMask(ee.Image.constant(0))
    bands = []
    for i in range(ndays):
        d0 = ee.Date((first + dt.timedelta(days=i)).isoformat())
        c = col.filterDate(d0, d0.advance(1, "day"))
        bands.append(ee.Image(ee.Algorithms.If(c.size().gt(0), c.mean(), empty)).rename(f"d{i:02d}"))
    stack = ee.Image.cat(bands).addBands(ee.Image.constant(1).rename("total"))
    reducer = ee.Reducer.mean().combine(ee.Reducer.max(), sharedInputs=True).combine(ee.Reducer.count(), sharedInputs=True)
    feats = budget.get(stack.reduceRegions(fc, reducer, scale=1113.2).map(lambda f: f.setGeometry(None)))["features"]
    rows = []
    for f in feats:
        p = f["properties"]
        for i in range(ndays):
            k = f"d{i:02d}"
            rows.append({"volcano": p["volcano"], "ring": p["ring"], "date": (first + dt.timedelta(days=i)).isoformat(),
                         "ai_mean": p.get(f"{k}_mean"), "ai_max": p.get(f"{k}_max"), "valid": p.get(f"{k}_count") or 0, "total": p.get("total_count") or 0})
    return rows


def windows_from_raw(as_of: str) -> dict[str, list[tuple[str, str]]]:
    """Eruption windows from the archived GVP tables (and VAAC advisories when crawled)."""
    from plumes.readmodels import load_vaac, rows

    vols = [{"id": c["id"], "gvpNumber": int(c["gvp_number"]) if c["gvp_number"] else None} for c in rows(CROSSWALK)]
    gvp_e = rows(RAW / "gvp" / "gvp-eruptions-ph.csv")
    vaac = {}
    if (RAW / "vaac-tokyo-advisories" / "pages.jsonl").exists():
        vaac = {g: sorted({a[0][:10] for a in adv}) for g, adv in load_vaac().items()}
    return run_a.eruption_windows(vols, gvp_e, vaac, as_of)


# ---------------------------------------------------------------- runs

def _chunks(kind: str, keys: list[str], fn, budget: Budget, stop_after_s: float | None) -> dict:
    done = skipped = 0
    for k in keys:
        path = TABLES / f"ee-{kind}" / f"{k}.csv"
        if path.exists():
            skipped += 1
            continue
        rows = fn(k)
        _write(path, rows, COLS[kind])
        done += 1
        print(f"  {kind} {k}: {len(rows)} rows; run {budget.run_s:.0f} EECU-s", flush=True)
        if stop_after_s is not None and budget.run_s >= stop_after_s:
            print(f"  stopped: run passed {stop_after_s:.0f} EECU-s", flush=True)
            break
    return {"chunks_done": done, "chunks_skipped": skipped, "eecu_s": round(budget.run_s, 1)}


def smoke(budget: Budget, lakes: list[dict]) -> dict:
    """One image (JRC GSW, March 2019) reduced over both lakes' core and crater discs: checks the auth, the profiler and the
    lake geometry (the core should be nearly all water; the crater partly). Writes nothing to data/tables."""
    img = ee.Image(ee.ImageCollection(run_a.GSW).filterDate("2019-03-01", "2019-04-01").first())
    w = img.select("water")
    px = ee.Image.pixelArea()
    stack = px.updateMask(w.eq(2)).rename("water").addBands(px.updateMask(w.gt(0)).rename("valid")).addBands(px.rename("total"))
    feats = []
    for lake in lakes:
        for key in ("coreM", "craterM"):
            feats.append(ee.Feature(_disc(lake, key), {"lake": lake["id"], "disc": key}))
    fc = stack.reduceRegions(ee.FeatureCollection(feats), ee.Reducer.sum(), scale=30).map(lambda f: f.setGeometry(None))
    out = {}
    for p in _props(budget.get(fc)["features"]):
        out[f"{p['lake']}/{p['disc']}"] = {"water_km2": round((p.get("water") or 0) / 1e6, 3), "observed": round((p.get("valid") or 0) / (p.get("total") or 1), 2),
                                           "water_share": round((p.get("water") or 0) / (p.get("total") or 1), 2)}
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["smoke", "canary", "laketemp", "lakegsw", "lakes2", "uvai"])
    ap.add_argument("--start")
    ap.add_argument("--end")
    ap.add_argument("--windows", action="store_true", help="uvai: only the months touched by eruption windows")
    ap.add_argument("--as-of", default=(dt.date.today().replace(day=1) - dt.timedelta(days=1)).isoformat())
    ap.add_argument("--stop-after-s", type=float)
    a = ap.parse_args()
    lakes = run_a.load_lakes()
    init()
    budget = Budget(DATA / "state" / "ee-usage.json")
    stop = a.stop_after_s
    try:
        if a.step == "smoke":
            res = smoke(budget, lakes)
        elif a.step == "canary":
            res = {"laketemp": _chunks("laketemp", ["2019"], lambda k: laketemp_year(int(k), budget, lakes), budget, None),
                   "lakes2": _chunks("lakes2", ["2020"], lambda k: lakes2_year(int(k), budget, lakes), budget, None),
                   "lakegsw": _chunks("lakegsw", ["all"], lambda k: lakegsw(budget, lakes), budget, None),
                   "uvai": _chunks("uvai", ["2020-01"], lambda k: uvai_month(k, budget), budget, None)}
        elif a.step in ("laketemp", "lakes2"):
            y0 = int(a.start or (2000 if a.step == "laketemp" else 2017))
            y1 = int(a.end or dt.date.fromisoformat(a.as_of).year)
            fn = laketemp_year if a.step == "laketemp" else lakes2_year
            res = _chunks(a.step, [str(y) for y in range(y0, y1 + 1)], lambda k, fn=fn: fn(int(k), budget, lakes), budget, stop)
        elif a.step == "lakegsw":
            res = _chunks("lakegsw", ["all"], lambda k: lakegsw(budget, lakes), budget, stop)
        else:
            if a.windows:
                ms = run_a.window_months(windows_from_raw(a.as_of))
            else:
                ms = run_a.months_between(a.start or run_a.S5P_AER_AI_START[:7], a.end or a.as_of[:7])
            res = _chunks("uvai", ms, lambda k: uvai_month(k, budget), budget, stop) | {"months": len(ms)}
    finally:
        print(json.dumps(budget.save(f"run-a {a.step} {a.start or ''}..{a.end or ''}")))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
