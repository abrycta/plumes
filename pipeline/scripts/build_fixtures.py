"""Build the contract fixtures in contracts/fixtures/data/ from the spike's real Taal tables (one-off, local).

Inputs are the spike outputs (spike/out, spike/fixtures/parsed.json; gitignored, on Kurt's laptop). The fixture is a
small, real window (2019-12-01 .. 2020-02-15) so the front end and the API can start before the pipeline publishes v1.
Run: cd pipeline && uv run python scripts/build_fixtures.py
"""
import csv
import datetime as dt
import json
import math
import pathlib
import subprocess

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
SPIKE = ROOT / "spike"
OUT = ROOT / "contracts" / "fixtures" / "data"
V = OUT / "v0"
AS_OF = "2026-10-21"
GEN = "2026-10-22T00:00:00Z"
SPAN = ("2019-12-01", "2020-02-15")
HDR = {"schemaVersion": "1", "dataVersion": "v0", "dataAsOf": AS_OF, "generatedAt": GEN, "fixture": True}
TAAL = (120.9975, 14.0106)

reg = {e["id"]: e for e in yaml.safe_load(open(ROOT / "pipeline" / "sources.yaml" if (ROOT / "pipeline" / "sources.yaml").exists() else ROOT / "docs" / "sources-draft.yaml"))["sources"]}


def prov(ids):
    return {"sources": [{"id": i, "attribution": reg[i]["attribution"], "licence": reg[i]["licence"], "snapshotDate": AS_OF, "fromArchive": False} for i in ids]}


def km(lon1, lat1, lon2, lat2):
    p = math.pi / 180
    a = math.sin((lat2 - lat1) * p / 2) ** 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(a))


def lt(en, ja):
    return {"en": en, "ja": ja}


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n")


# ---------- volcanoes.geojson ----------
gvp_v = {int(r["Volcano_Number"]): r for r in csv.DictReader(open(SPIKE / "out" / "gvp_volcanoes.csv"))}
gvp_e = list(csv.DictReader(open(SPIKE / "out" / "gvp_eruptions.csv")))
cw = list(csv.DictReader(open(ROOT / "pipeline" / "plumes" / "data" / "volcanoes.csv")))


def gvp_date(r, pre="StartDate"):
    y, m, d = r[pre + "Year"], r[pre + "Month"], r[pre + "Day"]
    if not y:
        return None
    s = y
    if m and m != "0":
        s += f"-{int(m):02d}"
        if d and d != "0":
            s += f"-{int(d):02d}"
    return s


feats = []
for c in cw:
    n = int(c["gvp_number"]) if c["gvp_number"] else None
    g = gvp_v.get(n)
    lat, lon = (float(g["Latitude"]), float(g["Longitude"])) if g else (float(c["lat"]), float(c["lon"]))
    er = sorted([e for e in gvp_e if n and int(e["Volcano_Number"]) == n and e["StartDateYear"]], key=lambda e: int(e["StartDateYear"]))
    last = er[-1] if er else None
    feats.append({"type": "Feature", "id": c["id"], "geometry": {"type": "Point", "coordinates": [lon, lat]}, "properties": {
        "id": c["id"], "name": lt(c["phivolcs_name"], c["name_ja"]), "gvpNumber": n,
        "elevationM": float(g["Elevation"]) if g and g["Elevation"] else None,
        "observatory": c["observatory"] == "true", "coverage": c["coverage"],
        "lastEruption": {"start": gvp_date(last), "vei": int(last["ExplosivityIndexMax"]) if last["ExplosivityIndexMax"] else None} if last else None,
        "eruptionsSince1900": sum(int(e["StartDateYear"]) >= 1900 for e in er),
        "eruptionsSince2000": sum(int(e["StartDateYear"]) >= 2000 for e in er),
        "file": f"volcano/{c['id']}.json"}})
dump(V / "volcanoes.geojson", {**HDR, "kind": "volcanoes", "type": "FeatureCollection", "features": feats})

# ---------- volcano/taal.json ----------
ee = json.load(open(SPIKE / "out" / "taal_ee.json"))
parsed = json.load(open(SPIKE / "fixtures" / "parsed.json"))
so2 = ee["so2"]
nmax = max(r["15km_n"] for r in so2)
daily = {
    "so2_s5p_15km": {
        "source": ["s5p-offl-so2"], "unit": "µmol/m²", "ringKm": 15, "start": so2[0]["date"],
        "label": lt("TROPOMI SO₂ column, mean within 15 km", "TROPOMI SO₂カラム量(15 km圏平均)"),
        "values": [None if r["15km_mean"] is None else round(r["15km_mean"] * 1e6) for r in so2],
        "coverage": [round(r["15km_n"] / nmax, 3) for r in so2],
        "note": lt("Fixture: coverage approximated as valid pixels / the month's maximum.", "フィクスチャ:被覆率は当月最大の有効画素数に対する比で近似。"),
    },
    "so2_s5p_50km": {
        "source": ["s5p-offl-so2"], "unit": "µmol/m²", "ringKm": 50, "start": so2[0]["date"],
        "label": lt("TROPOMI SO₂ column, mean within the 50 km box", "TROPOMI SO₂カラム量(50 km範囲平均)"),
        "values": [None if r["50km_mean"] is None else round(r["50km_mean"] * 1e6) for r in so2],
    },
}
d0 = dt.date.fromisoformat(SPAN[0])
usgs = {}
for r in csv.DictReader(open(SPIKE / "out" / "usgs_taal.csv")):
    if km(TAAL[0], TAAL[1], float(r["longitude"]), float(r["latitude"])) <= 30:
        usgs.setdefault(r["time"][:10], []).append(float(r["mag"] or "nan"))
def firms_rows(path):
    """The FIRMS area API returns one CSV per 5-day call with no trailing newline; the spike concatenated them."""
    text = path.read_text()
    head = text.split("\n", 1)[0]
    lines = [ln for ln in text.replace(head, "\n" + head).splitlines() if ln and ln != head]
    return list(csv.DictReader([head, *lines]))


firms = {}
for r in firms_rows(SPIKE / "out" / "firms_VIIRS_SNPP_SP.csv"):
    if km(TAAL[0], TAAL[1], float(r["longitude"]), float(r["latitude"])) <= 15:
        a = firms.setdefault(r["acq_date"], [0, 0.0])
        a[0] += 1
        a[1] = max(a[1], float(r["frp"]))
events = {
    "frp_modis_15km": {"source": ["modis-mod14a1"], "label": lt("MODIS max fire radiative power within 15 km", "MODIS 最大放射電力(15 km圏)"),
                       "cols": ["date", "maxFrpMw", "n"], "units": {"maxFrpMw": "MW", "n": "pixels"}, "ringKm": 15, "start": "2000-11-01",
                       "rows": [[r["date"], r["maxfrp"], r["n"]] for r in ee["fire"]]},
    "fire_viirs_15km": {"source": ["firms-modis"], "label": lt("VIIRS (S-NPP) detections within 15 km, FIRMS", "VIIRS(S-NPP)熱異常検知数(15 km圏、FIRMS)"),
                        "cols": ["date", "n", "maxFrpMw"], "units": {"n": "detections", "maxFrpMw": "MW"}, "ringKm": 15, "start": "2012-01-20",
                        "rows": [[d, v[0], round(v[1], 1)] for d, v in sorted(firms.items())]},
    "eq_usgs_30km": {"source": ["usgs-comcat-ph-2010"], "label": lt("USGS earthquakes within 30 km", "USGS 地震(30 km圏)"),
                     "cols": ["date", "n", "maxMag"], "units": {"n": "events", "maxMag": "M"}, "ringKm": 30, "start": "1900-01-01",
                     "rows": [[d, len(v), max(v)] for d, v in sorted(usgs.items())]},
}
WP = "https://www.phivolcs.dost.gov.ph/"
bul_rows = []
for r in parsed["wp"]:
    if r["slug"] in ("taal-volcano-bulletin-update-12-january-2020-04-00-pm-2", "taal-volcano-bulletin-13-january-2020-8-00-a-m"):
        f = r["f"]
        day = "2020-01-12" if "12-january" in r["slug"] else "2020-01-13"
        bul_rows.append([day, f["alert"], f["eq"], None, f["so2"], None, f["plume_m"], f["deform"], WP + r["slug"] + "/"])
bul_rows.sort()
VA = "https://ds.data.jma.go.jp/svd/vaac/data/TextData/2020/"
adv = []
for r in parsed["vaac"]:
    d, t = r["dtg"].split("/")
    iso = f"{d[:4]}-{d[4:6]}-{d[6:]}T{t[:2]}:{t[2:4]}:00Z"
    basis = "observed" if r["obs_top_fl"] else ("reported" if r["eruption_fl"] else "none")
    adv.append([iso, r["nr"], r["top_fl"], basis, VA + r["file"]])
DR = "https://dromic.dswd.gov.ph/wp-content/uploads/"
num = lambda s: int(s.replace(",", "")) if s else None  # noqa: E731
disp = []
for r in csv.DictReader(open(SPIKE / "fixtures" / "dromic" / "taal-2020-grand-totals.csv")):
    f = r["report_file"]
    rep = f.split("Report-")[1].split("-")[0]
    asof = dt.datetime.strptime(f.split("as-of-")[1].split(".")[0].rsplit("-", 1)[0], "%d-%B-%Y").date().isoformat()
    disp.append([asof, rep, num(r["affected_persons"]), num(r["inside_persons_now"]), num(r["inside_persons_cum"]),
                 num(r["outside_persons_now"]), num(r["outside_persons_cum"]), DR + ("2020/02/" if asof >= "2020-02" else "2020/01/") + f])
disp.sort()
episodes = []
for e in gvp_e:
    if e["Volcano_Name"] != "Taal" or not e["StartDateYear"]:
        continue
    s = gvp_date(e)
    ep = {"id": f"gvp-{e['Eruption_Number']}", "kind": "gvp_eruption", "start": s, "end": gvp_date(e, "EndDate"),
          "vei": int(e["ExplosivityIndexMax"]) if e["ExplosivityIndexMax"] else None, "source": ["gvp-eruptions-ph"],
          "url": "https://volcano.si.edu/volcano.cfm?vn=273070"}
    if s == "2020-01-12":
        ep.update(so2MassKt=170, plumeAltKm=17, source=["gvp-eruptions-ph", "nasa-msvolso2l4"])
    episodes.append(ep)
episodes.sort(key=lambda e: (len(e["start"].split("-")[0]), e["start"]))
episodes.append({"id": "alert-2020-01", "kind": "alert_window", "start": "2020-01-12", "end": "2020-01-26", "maxAlert": 4,
                 "source": ["phivolcs-bulletins"], "url": WP + "taal-volcano-bulletin-13-january-2020-8-00-a-m/"})
reading = {
    "id": "taal-2020-01", "episodeId": "alert-2020-01", "start": "2020-01-12", "end": "2020-01-26", "status": "draft",
    "text": lt(
        "On 12 January 2020 PHIVOLCS raised Taal to Alert Level 4 within hours. Tokyo VAAC saw ash to about FL550 (16.8 km) on 12–13 January; "
        "TROPOMI measured an SO₂ column about 80 times the early-January background on 13 January, from only a few clear pixels. "
        "USGS located 35 earthquakes within 30 km on 12 January. GVP records the eruption as VEI 4.",
        "2020年1月12日、PHIVOLCSは数時間のうちにタール火山の警戒レベルを4に引き上げた。東京VAACは12〜13日に高度約FL550(16.8 km)の火山灰を観測し、"
        "13日のTROPOMI SO₂カラム量は1月初旬の背景値の約80倍だった(有効画素はわずか)。USGSは12日に30 km圏で35回の地震を観測した。GVPはこの噴火をVEI 4としている。"),
    "limits": lt(
        "Satellite SO₂ is a column amount on clear days only (14–15 January had no valid pixels), not a flux. This is a past record, not a hazard assessment.",
        "衛星SO₂は晴天日のみのカラム量で(1月14〜15日は有効画素なし)、放出量ではない。これは過去の記録であり、ハザード評価ではない。"),
    "figures": [
        {"label": lt("Alert level", "警戒レベル"), "value": 4, "source": "phivolcs-bulletins", "asOf": "2020-01-13", "url": WP + "taal-volcano-bulletin-13-january-2020-8-00-a-m/"},
        {"label": lt("Ash top (VAAC)", "火山灰の高度(VAAC)"), "value": 550, "unit": "FL", "source": "vaac-tokyo-advisories", "asOf": "2020-01-12", "url": VA + "20200112_27307000_0003_Text.html"},
        {"label": lt("SO₂ mass (MSVOLSO2L4)", "SO₂量(MSVOLSO2L4)"), "value": 170, "unit": "kt", "source": "nasa-msvolso2l4", "asOf": "2020-01-12"},
    ],
}
pop = json.load(open(SPIKE / "out" / "story_ee.json"))["worldpop_2020_14km"]["population"]
taal = {**HDR, "kind": "volcano",
        "volcano": {"id": "taal", "gvpNumber": 273070, "gvpName": "Taal", "name": lt("Taal", "タール火山"), "lat": TAAL[1], "lon": TAAL[0],
                    "elevationM": 311, "type": "Caldera", "observatory": True, "coverage": "deep",
                    "links": {"phivolcs": "https://www.phivolcs.dost.gov.ph/", "gvp": "https://volcano.si.edu/volcano.cfm?vn=273070",
                              "comet": "https://comet.nerc.ac.uk/comet-lics-portal/", "hazardhunter": "https://hazardhunter.georisk.gov.ph/"}},
        "span": {"start": SPAN[0], "end": SPAN[1]}, "daily": daily, "events": events,
        "bulletins": {"source": ["phivolcs-bulletins"], "authority": "DOST-PHIVOLCS",
                      "cols": ["date", "alertLevel", "volcanicEq", "tremor", "so2FluxTpd", "so2FluxDate", "plumeM", "deformation", "url"], "rows": bul_rows,
                      "gaps": [{"start": "2021-10", "end": "2022-06", "reason": lt("WordPress summaries are empty and LAVA had not started.", "WordPressの要約は空で、LAVAは未開始。")}]},
        "advisories": {"source": ["vaac-tokyo-advisories"], "cols": ["dtg", "advisoryNo", "topFl", "heightBasis", "url"], "rows": adv},
        "displacement": {"source": ["dswd-dromic-reports"], "cols": ["asOf", "report", "affectedPersons", "insidePersonsNow", "insidePersonsCum", "outsidePersonsNow", "outsidePersonsCum", "url"], "rows": disp},
        "episodes": episodes, "readings": [reading],
        "exposure": {"rings": [{"radiusKm": 14, "population": round(pop), "year": 2020, "source": "worldpop-100m"}]},
        "provenance": {**prov(["s5p-offl-so2", "modis-mod14a1", "firms-modis", "usgs-comcat-ph-2010", "phivolcs-bulletins", "vaac-tokyo-advisories",
                               "dswd-dromic-reports", "gvp-eruptions-ph", "nasa-msvolso2l4", "worldpop-100m"]),
                       "earthEngine": {"assets": ["COPERNICUS/S5P/OFFL/L3_SO2", "MODIS/061/MOD14A1", "WorldPop/GP/100m/pop"], "eecuSeconds": 3.0}}}
dump(V / "volcano" / "taal.json", taal)

# ---------- layers.json + thermal detections for 2020-01 ----------
det = []
for f, kind in (("firms_VIIRS_SNPP_SP.csv", "VIIRS_SNPP_SP"), ("firms_MODIS_SP.csv", "MODIS_SP")):
    for r in firms_rows(SPIKE / "out" / f):
        det.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [float(r["longitude"]), float(r["latitude"])]},
                    "properties": {"date": r["acq_date"], "frp": float(r["frp"]), "sensor": kind, "type": int(r["type"]) if r.get("type") else None}})
dump(V / "layers" / "thermal" / "2020-01.geojson", {"type": "FeatureCollection", "features": det})
dump(V / "layers.json", {**HDR, "kind": "layers", "layers": [
    {"id": "thermal-detections", "title": lt("Thermal detections (FIRMS)", "熱異常検知(FIRMS)"), "format": "geojson", "url": "layers/thermal/{month}.geojson",
     "time": {"step": "month", "start": "2000-11", "end": "2026-09", "available": ["2020-01"]},
     "properties": {"date": "acquisition date", "frp": "MW", "sensor": "FIRMS product", "type": "FIRMS type: 0 vegetation fire, 1 active volcano, 2 other static source, 3 offshore"},
     "sources": ["firms-modis"], "attribution": reg["firms-modis"]["attribution"],
     "note": lt("Fixture holds the Taal box only. Published versions use PMTiles with the same id.", "フィクスチャはタール周辺のみ。公開版は同じIDのPMTiles。")}]})

# ---------- story/taal-2020.json ----------
era5 = json.load(open(SPIKE / "out" / "era5_taal.json"))
thumbs = []
for name, date, cap in (("taal-before-2019-11.jpg", "2019-11-19", lt("Before: Sentinel-2, 19 Nov 2019", "噴火前:Sentinel-2、2019年11月19日")),
                        ("taal-after-2020-01.jpg", "2020-01-28", lt("After: Sentinel-2, 28 Jan 2020", "噴火後:Sentinel-2、2020年1月28日"))):
    dst = V / "assets" / name
    subprocess.run(["sips", "-Z", "640", "-s", "formatOptions", "70", str(SPIKE / "out" / name), "--out", str(dst)], check=True, capture_output=True)
    w, h = (int(x) for x in subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(dst)], capture_output=True, text=True).stdout.split()[-3::2])
    thumbs.append({"kind": "image", "url": f"assets/{name}", "date": date, "sensor": "Sentinel-2 MSI", "source": "s2-sr-harmonized", "caption": cap,
                   "credit": f"Contains modified Copernicus Sentinel data {date[:4]}", "width": w, "height": h})
step = lambda i, s, e, t, x, series, figs, **k: {"id": i, "start": s, "end": e, "title": t, "text": x, "status": "reviewed", "series": series, "figures": figs, **k}  # noqa: E731
story = {**HDR, "kind": "story", "id": "taal-2020", "volcanoId": "taal", "volcanoFile": "volcano/taal.json",
         "title": lt("Taal, January 2020", "タール火山 2020年1月"),
         "summary": lt("What the instruments recorded before, during and after the 12 January 2020 eruption.", "2020年1月12日の噴火の前後に観測機器が記録したこと。"),
         "span": {"start": SPAN[0], "end": SPAN[1]},
         "steps": [
             step("before", "2019-12-01", "2020-01-11", lt("Before", "噴火前"), lt("Alert Level 1. Satellite SO₂ near background; no USGS-located earthquakes within 30 km.", "警戒レベル1。衛星SO₂は背景値付近で、30 km圏にUSGSの震源はない。"),
                  ["so2_s5p_15km", "eq_usgs_30km", "bulletins"], [], map={"center": list(TAAL), "zoom": 10}),
             step("eruption", "2020-01-12", "2020-01-13", lt("12–13 January", "1月12〜13日"), reading["text"], ["so2_s5p_15km", "eq_usgs_30km", "advisories", "bulletins"], reading["figures"],
                  map={"center": list(TAAL), "zoom": 9, "layers": ["thermal-detections"], "month": "2020-01"}),
             step("people", "2020-01-14", "2020-02-07", lt("People displaced", "避難した人々"),
                  lt("DSWD DROMIC reports counted 504,265 people affected by 7 February 2020.", "DSWD DROMIC報告は2020年2月7日までに504,265人の被災者を数えた。"),
                  ["displacement"], [{"label": lt("Persons affected", "被災者数"), "value": 504265, "source": "dswd-dromic-reports", "asOf": "2020-02-07", "url": disp[-1][-1]}]),
             step("crater", "2019-11-19", "2020-01-28", lt("The crater lake", "火口湖"), lt("Sentinel-2 before and after: the main crater lake drained.", "Sentinel-2の前後比較:主火口湖は干上がった。"),
                  [], [], assets=thumbs),
         ],
         "winds": {"source": ["era5-pressure-levels"], "point": [era5["grid_point"][1], era5["grid_point"][0]], "cols": ["time", "hPa", "u", "v", "speedMs", "dirToDeg"],
                   "rows": [[r["time"] + ":00Z", r["hPa"], r["u"], r["v"], r["speed"], r["dir_to_deg"]] for r in era5["rows"]]},
         "provenance": prov(["phivolcs-bulletins", "vaac-tokyo-advisories", "dswd-dromic-reports", "s2-sr-harmonized", "era5-pressure-levels", "nasa-msvolso2l4", "s5p-offl-so2", "usgs-comcat-ph-2010"])}
dump(V / "story" / "taal-2020.json", story)

# ---------- stories.json and story/drafts/ (the generator, on the fixture's own read models) ----------
from plumes.stories.generate import generate  # noqa: E402

generate(V)

dump(OUT / "latest.json", {"schemaVersion": "1", "kind": "latest", "current": "v0", "base": "v0/", "dataAsOf": AS_OF, "generatedAt": GEN, "previous": None, "fixture": True})
print("fixtures written to", OUT)
