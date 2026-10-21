import json, os, time, ee
key = os.environ["EE_KEY_FILE"]; info = json.load(open(key))
ee.Initialize(ee.ServiceAccountCredentials(info["client_email"], key), project=info["project_id"])
taal = ee.Geometry.Point([120.993, 14.002]); box = taal.buffer(12000).bounds()
def s2(a, b):
    c = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(box).filterDate(a, b)
    return c.sort("CLOUDY_PIXEL_PERCENTAGE").first(), c.size()
out = {}
for name, (a, b) in {"2019-11": ("2019-11-01", "2019-12-15"), "2020-01-after": ("2020-01-16", "2020-02-15"), "2020-03": ("2020-03-01", "2020-04-01")}.items():
    img, n = s2(a, b)
    out[name] = {"scenes": n.getInfo(), "cloud": img.get("CLOUDY_PIXEL_PERCENTAGE").getInfo(), "date": ee.Date(img.get("system:time_start")).format("YYYY-MM-dd").getInfo()}
s1 = ee.ImageCollection("COPERNICUS/S1_GRD").filterBounds(box).filterDate("2020-01-12", "2020-01-20").filter(ee.Filter.eq("instrumentMode", "IW"))
out["s1_scenes_12_20_jan"] = s1.size().getInfo()
ls = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").filterBounds(box).filterDate("2019-01-01", "2020-01-10").sort("CLOUD_COVER").first()
lake = ee.Geometry.Point([120.997, 14.010]).buffer(300)
st = ls.select("ST_B10").multiply(0.00341802).add(149.0 - 273.15).reduceRegion(ee.Reducer.mean(), lake, 30)
out["landsat_crater_lake_C"] = {"date": ee.Date(ls.get("system:time_start")).format("YYYY-MM-dd").getInfo(), "temp": st.getInfo()}
ring = taal.buffer(14000)
wp = ee.ImageCollection("WorldPop/GP/100m/pop").filter(ee.Filter.eq("country", "PHL")).filter(ee.Filter.eq("year", 2020)).first()
out["worldpop_2020_14km"] = wp.reduceRegion(ee.Reducer.sum(), ring, 100, maxPixels=1e9).getInfo()
try:
    alt = ee.ImageCollection("projects/sat-io/open-datasets/WORLDPOP/pop")
    out["sat_io_worldpop"] = {"first": alt.first().getInfo()["properties"], "size": alt.size().getInfo()}
except Exception as e:
    out["sat_io_worldpop"] = str(e)[:200]
print(json.dumps(out, indent=1, default=str))
