import json, os, sys, time, ee
key = os.environ["EE_KEY_FILE"]
info = json.load(open(key))
ee.Initialize(ee.ServiceAccountCredentials(info["client_email"], key), project=info["project_id"])
taal = ee.Geometry.Point([120.993, 14.002])
rings = {"15km": taal.buffer(15000), "50km": taal.buffer(50000)}
start, end = "2020-01-01", "2020-02-01"
so2 = ee.ImageCollection("COPERNICUS/S5P/OFFL/L3_SO2").select("SO2_column_number_density").filterDate(start, end)
days = ee.List.sequence(0, 30)
def daily(d):
    d0 = ee.Date(start).advance(d, "day"); img = so2.filterDate(d0, d0.advance(1, "day")).mean()
    r = {}
    for name, g in rings.items():
        st = img.reduceRegion(ee.Reducer.mean().combine(ee.Reducer.count(), sharedInputs=True), g, 1113.2, maxPixels=1e9)
        r[name + "_mean"] = st.get("SO2_column_number_density_mean"); r[name + "_n"] = st.get("SO2_column_number_density_count")
    return ee.Feature(None, r).set("date", d0.format("YYYY-MM-dd"))
t = time.time()
so2_rows = ee.FeatureCollection(days.map(daily)).getInfo()["features"]
fire = ee.ImageCollection("MODIS/061/MOD14A1").filterDate(start, end).select("MaxFRP")
def fday(img):
    st = img.reduceRegion(ee.Reducer.max().combine(ee.Reducer.count(), sharedInputs=True), rings["15km"], 1000)
    return ee.Feature(None, {"date": img.date().format("YYYY-MM-dd"), "maxfrp": st.get("MaxFRP_max"), "n": st.get("MaxFRP_count")})
fire_rows = ee.FeatureCollection(fire.map(fday)).getInfo()["features"]
print(json.dumps({"seconds": round(time.time() - t, 1),
  "so2": [{k: f["properties"].get(k) for k in ("date", "15km_mean", "15km_n", "50km_mean")} for f in so2_rows],
  "fire": [f["properties"] for f in fire_rows if f["properties"].get("n")]}, indent=0))
