"""Earth Engine reductions for the 24 volcanoes (DATA-PLAN §2 step 1). Nothing is downloaded: images are reduced where
they live and only small tables come back (one interactive call per volcano set and month, each under EE's 5,000-element
limit). Chunks already in data/tables are skipped, so a backfill can be resumed across runs and months.

    EE_KEY_FILE=… uv run python -m plumes.ee_series so2 --start 2018-12 --end 2026-09
    EE_KEY_FILE=… uv run python -m plumes.ee_series fire --start 2000-11 --end 2026-09
    EE_KEY_FILE=… uv run python -m plumes.ee_series exposure
    EE_KEY_FILE=… uv run python -m plumes.ee_series thumbs-taal
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import urllib.request

import ee

from plumes import coverage
from plumes.ee_budget import Budget, init
from plumes.paths import BUILD, CROSSWALK, DATA, TABLES

S5P = "COPERNICUS/S5P/OFFL/L3_SO2"
S5P_BANDS = ["SO2_column_number_density", "SO2_column_number_density_15km"]
FIRE = {"modis-mod14a1": ("MODIS/061/MOD14A1", "MaxFRP", "FireMask"), "viirs-vnp14a1": ("NASA/VIIRS/002/VNP14A1", "MaxFRP", "FireMask")}
FIRMS = "FIRMS"
SO2_RINGS = [5, 10, 15, 30]
FIRE_RINGS = [5, 10, 15]
MOLAR_SO2 = 64.066  # g/mol


def volcanoes() -> list[dict]:
    """The 24, with GVP coordinates where they exist (data/raw/gvp), else the crosswalk's."""
    gvp = {}
    path = DATA / "raw" / "gvp" / "gvp-volcanoes-ph.csv"
    if path.exists():
        gvp = {int(r["Volcano_Number"]): r for r in csv.DictReader(open(path))}
    out = []
    for c in csv.DictReader(open(CROSSWALK)):
        g = gvp.get(int(c["gvp_number"])) if c["gvp_number"] else None
        lat, lon = (float(g["Latitude"]), float(g["Longitude"])) if g else (float(c["lat"]), float(c["lon"]))
        out.append({"id": c["id"], "lat": lat, "lon": lon})
    return out


def ring_fc(radii: list[int], box_km: int | None = None) -> ee.FeatureCollection:
    feats = []
    for v in volcanoes():
        p = ee.Geometry.Point([v["lon"], v["lat"]])
        for r in radii:
            feats.append(ee.Feature(p.buffer(r * 1000), {"volcano": v["id"], "ring": f"{r}km"}))
        if box_km:
            feats.append(ee.Feature(p.buffer(box_km * 1000).bounds(), {"volcano": v["id"], "ring": f"box{box_km}km"}))
    return ee.FeatureCollection(feats)


def months(start: str, end: str):
    y, m = map(int, start.split("-"))
    ye, me = map(int, end.split("-"))
    while (y, m) <= (ye, me):
        yield f"{y:04d}-{m:02d}"
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def _write(path, rows, cols):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def so2_month(month: str, budget: Budget) -> list[dict]:
    """Daily TROPOMI SO2 per volcano ring: mean column (both bands), valid-pixel count, total pixels, mass (t, valid pixels only).

    One aggregation per month: the daily mean images are stacked as bands (d<NN>_pbl, d<NN>_c15, d<NN>_mass) of one
    image and reduced once over every ring (EE refuses many concurrent reduceRegions)."""
    fc = ring_fc(SO2_RINGS, box_km=50)
    col = ee.ImageCollection(S5P).select(S5P_BANDS)
    y, m = map(int, month.split("-"))
    first = dt.date(y, m, 1)
    ndays = ((first.replace(day=28) + dt.timedelta(days=4)).replace(day=1) - first).days
    empty = ee.Image.constant([0, 0]).rename(S5P_BANDS).updateMask(ee.Image.constant(0))
    bands = []
    for d in range(ndays):
        d0 = ee.Date((first + dt.timedelta(days=d)).isoformat())
        c = col.filterDate(d0, d0.advance(1, "day"))
        img = ee.Image(ee.Algorithms.If(c.size().gt(0), c.mean(), empty))
        mass = img.select(S5P_BANDS[0]).multiply(ee.Image.pixelArea()).multiply(MOLAR_SO2 / 1e6)
        bands.append(img.select(S5P_BANDS, [f"d{d:02d}_pbl", f"d{d:02d}_c15"]).addBands(mass.rename(f"d{d:02d}_mass")))
    stack = ee.Image.cat(bands).addBands(ee.Image.constant(1).rename("total"))
    reducer = ee.Reducer.mean().combine(ee.Reducer.count(), sharedInputs=True).combine(ee.Reducer.sum(), sharedInputs=True)
    feats = budget.get(stack.reduceRegions(fc, reducer, scale=1113.2).map(lambda f: f.setGeometry(None)))["features"]
    rows = []
    for f in feats:
        p = f["properties"]
        for d in range(ndays):
            k = f"d{d:02d}"
            rows.append({"volcano": p["volcano"], "ring": p["ring"], "date": (first + dt.timedelta(days=d)).isoformat(),
                         "so2_pbl_mol_m2": p.get(f"{k}_pbl_mean"), "so2_15km_mol_m2": p.get(f"{k}_c15_mean"),
                         "valid": p.get(f"{k}_pbl_count") or 0, "total": p.get("total_count") or 0, "mass_pbl_t": p.get(f"{k}_mass_sum")})
    return rows


def _days(col) -> ee.List:
    return col.aggregate_array("system:time_start").map(lambda t: ee.Date(t).format("YYYY-MM-dd")).distinct().sort()


def fire_month(month: str, budget: Budget) -> tuple[list[dict], dict]:
    """Daily fire pixels (FireMask >= 7) and max FRP per volcano ring for MOD14A1 and VNP14A1; FIRMS T21 detections.
    Also the days each collection has an image (plumes.coverage): a day without one is a gap, not "nothing detected"."""
    fc = ring_fc(FIRE_RINGS)
    a, b = month + "-01", ee.Date(month + "-01").advance(1, "month")
    out = ee.FeatureCollection([])
    days = {}
    for sid, (asset, frp, mask) in FIRE.items():
        col = ee.ImageCollection(asset).filterDate(a, b)
        days[sid] = _days(col)

        def per(img, sid=sid, frp=frp, mask=mask):
            fire = img.select(mask).gte(7)
            stack = img.select(frp).updateMask(fire).rename("frp").addBands(fire.selfMask().rename("n"))
            st = stack.reduceRegions(fc, ee.Reducer.max().combine(ee.Reducer.count(), sharedInputs=True), scale=1000)
            return st.filter(ee.Filter.gt("n_count", 0)).map(lambda f: f.set({"date": img.date().format("YYYY-MM-dd"), "source": sid}))
        out = out.merge(col.map(per).flatten())
    firms = ee.ImageCollection(FIRMS).filterDate(a, b).select("T21")
    days["firms-modis"] = _days(firms)

    def per_firms(img):
        st = img.gt(0).selfMask().rename("n").addBands(img.rename("frp")).reduceRegions(fc, ee.Reducer.count(), scale=1000)
        return st.filter(ee.Filter.gt("n", 0)).map(lambda f: f.set({"date": img.date().format("YYYY-MM-dd"), "source": "firms-modis"}))
    out = out.merge(firms.map(per_firms).flatten())
    feats = budget.get(out.select(["volcano", "ring", "date", "source", "frp_max", "n_count", "n"], retainGeometry=False))["features"]
    rows = []
    for f in feats:
        p = f["properties"]
        rows.append({"volcano": p["volcano"], "ring": p["ring"], "date": p["date"], "source": p["source"],
                     "n": p.get("n_count", p.get("n")), "max_frp_mw": p.get("frp_max")})
    return rows, budget.get(ee.Dictionary(days))


def run_monthly(kind: str, start: str, end: str, budget: Budget) -> dict:
    fn, cols = {"so2": (so2_month, ["volcano", "ring", "date", "so2_pbl_mol_m2", "so2_15km_mol_m2", "valid", "total", "mass_pbl_t"]),
                "fire": (fire_month, ["volcano", "ring", "date", "source", "n", "max_frp_mw"])}[kind]
    done = skipped = 0
    for m in months(start, end):
        path = TABLES / f"ee-{kind}" / f"{m}.csv"
        # a fire month is run again until every collection covers it (a partial month must not freeze as zeros)
        if path.exists() and (kind != "fire" or coverage.fire_month_complete(m, coverage.read_coverage(path))):
            skipped += 1
            continue
        rows = fn(m, budget)
        if kind == "fire":
            rows, cov = rows
            path.parent.mkdir(parents=True, exist_ok=True)
            path.with_suffix(".coverage.json").write_text(json.dumps(cov, sort_keys=True))
        _write(path, rows, cols)
        done += 1
        print(f"  {kind} {m}: {len(rows)} rows; run {budget.run_s:.0f} EECU-s", flush=True)
    return {"months_done": done, "months_skipped": skipped}


def exposure(budget: Budget) -> dict:
    """WorldPop population per volcano within 5/10/14/15/30 km: GP 100 m (2000-2020) every 5 years and 2020."""
    radii = [5, 10, 14, 15, 30]
    fc = ring_fc(radii)
    rows = []
    for year in (2000, 2005, 2010, 2015, 2020):
        img = ee.ImageCollection("WorldPop/GP/100m/pop").filter(ee.Filter.eq("country", "PHL")).filter(ee.Filter.eq("year", year)).first()
        st = budget.get(img.select("population").reduceRegions(fc, ee.Reducer.sum(), scale=100).select(["volcano", "ring", "sum"], retainGeometry=False))
        rows += [{"volcano": f["properties"]["volcano"], "ring_km": int(f["properties"]["ring"][:-2]), "year": year,
                  "population": round(f["properties"].get("sum") or 0)} for f in st["features"]]
    _write(TABLES / "ee-exposure.csv", rows, ["volcano", "ring_km", "year", "population"])
    return {"rows": len(rows)}


def thumbs_taal(budget: Budget) -> dict:
    """Sentinel-2 before/after thumbnails for the Taal 2020 story (least-cloudy scene in each window)."""
    box = ee.Geometry.Point([120.9975, 14.0106]).buffer(12000).bounds()
    out = BUILD / "assets"
    out.mkdir(parents=True, exist_ok=True)
    res = {}
    for name, (a, b) in {"taal-s2-2019-11": ("2019-11-01", "2019-12-15"), "taal-s2-2020-01": ("2020-01-16", "2020-02-15"),
                         "taal-s2-2020-03": ("2020-03-01", "2020-04-15")}.items():
        img = ee.Image(ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(box).filterDate(a, b).sort("CLOUDY_PIXEL_PERCENTAGE").first())
        date = budget.get(img.date().format("YYYY-MM-dd"))
        url = img.getThumbURL({"region": box, "dimensions": 768, "bands": ["B4", "B3", "B2"], "min": 0, "max": 3000, "format": "jpg"})
        urllib.request.urlretrieve(url, out / f"{name}.jpg")
        res[name] = date
    (out / "taal-s2.json").write_text(json.dumps(res))
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["so2", "fire", "exposure", "thumbs-taal"])
    ap.add_argument("--start")
    ap.add_argument("--end", default=(dt.date.today().replace(day=1) - dt.timedelta(days=1)).strftime("%Y-%m"))
    a = ap.parse_args()
    init()
    budget = Budget()
    try:
        if a.step in ("so2", "fire"):
            res = run_monthly(a.step, a.start or {"so2": "2018-12", "fire": "2000-11"}[a.step], a.end, budget)
        elif a.step == "exposure":
            res = exposure(budget)
        else:
            res = thumbs_taal(budget)
    finally:
        print(json.dumps(budget.save(f"{a.step} {a.start or ''}..{a.end}")))
    print(json.dumps(res))
