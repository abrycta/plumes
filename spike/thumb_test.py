import json, os, ee, urllib.request
key = os.environ["EE_KEY_FILE"]; info = json.load(open(key))
ee.Initialize(ee.ServiceAccountCredentials(info["client_email"], key), project=info["project_id"])
box = ee.Geometry.Point([120.993, 14.002]).buffer(12000).bounds()
for name, (a, b) in {"before-2019-11": ("2019-11-01", "2019-12-15"), "after-2020-01": ("2020-01-16", "2020-02-15")}.items():
    img = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(box).filterDate(a, b).sort("CLOUDY_PIXEL_PERCENTAGE").first()
    url = img.getThumbURL({"region": box, "dimensions": 768, "bands": ["B4", "B3", "B2"], "min": 0, "max": 3000, "format": "jpg"})
    out = f"out/taal-{name}.jpg"; urllib.request.urlretrieve(url, out); print(name, os.path.getsize(out), "bytes")
