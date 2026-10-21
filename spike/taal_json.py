"""Item 8: Taal per-volcano JSON from the spike tables, extrapolated from one month to the full span (2000-01-01 .. 2026-10-21)."""
import csv, datetime as dt, gzip, json, random, re, os
OUT = os.path.join(os.path.dirname(__file__), "out"); FX = os.path.join(os.path.dirname(__file__), "fixtures")
random.seed(12); D0, D1 = dt.date(2000, 1, 1), dt.date(2026, 10, 21); N = (D1 - D0).days + 1
ee = json.load(open(f"{OUT}/taal_ee.json")); parsed = json.load(open(f"{FX}/parsed.json"))
so2_jan = [(r["15km_mean"], r["15km_n"], r["50km_mean"]) for r in ee["so2"] if r.get("15km_mean") is not None]
frp_jan = [r["maxfrp"] for r in ee["fire"]]
def day(i): return D0 + dt.timedelta(i)
def i_of(s): return (dt.date.fromisoformat(s) - D0).days
umol = lambda x: None if x is None else round(x * 1e6)          # mol/m2 -> umol/m2, integer
# dense daily columns (null before the instrument starts or when no valid pixel)
s5p0, omi0 = i_of("2018-07-10"), i_of("2004-10-01")
so2_15, so2_n, so2_50, omi, omi_n = [], [], [], [], []
for i in range(N):
    m, n, m50 = ((random.gauss(3e-5, 6e-5), random.randint(1, 700), random.gauss(3e-5, 4e-5)) if i >= s5p0 and random.random() > .15 else (None, None, None))
    so2_15.append(umol(m)); so2_n.append(n); so2_50.append(umol(m50))
    o = (random.gauss(3e-5, 1.5e-4),) if i >= omi0 and random.random() > .5 else None   # OMI row anomaly: about half the days usable
    omi.append(umol(o[0]) if o else None); omi_n.append(random.randint(1, 9) if o else None)
# sparse series [dayIndex, value]
frp_modis = [[i, round(random.lognormvariate(4, 1))] for i in range(i_of("2000-11-01"), N) if random.random() < .01]
viirs_n = [[i, random.randint(1, 8)] for i in range(i_of("2012-01-20"), N) if random.random() < .015]
usgs = {}
for r in csv.DictReader(open(f"{OUT}/usgs_taal.csv")): usgs.setdefault(r["time"][:10], []).append(float(r["mag"] or 0))
usgs_rows = [[i_of(d), len(v), max(v)] for d, v in sorted(usgs.items())] * 6        # 56 events in 2.5 months -> ~6x over 26 years
# bulletins: one row per day 2017-09 .. now (WordPress then LAVA), with the parsed fields and a link id
wp = [r for r in parsed["wp"] if not r["empty"]]
bul = []
for i in range(i_of("2017-09-01"), N):
    r = random.choice(wp)["f"]; lv = random.choice([x for x in parsed["lava"] if x["ok"]])["f"]
    src = "w" if i < i_of("2021-10-01") else "l"; f = r if src == "w" else lv
    link = (f"taal-volcano-bulletin-{day(i).strftime('%d-%B-%Y').lower()}-8-00-a-m" if src == "w" else str(1000 + 4 * (i - i_of('2022-06-01'))))
    bul.append([i, f.get("alert"), f.get("eq"), f.get("so2"), f.get("plume_m"), src, link])
gvp = [r for r in csv.DictReader(open(f"{OUT}/gvp_eruptions.csv")) if r["Volcano_Name"] == "Taal"]
eruptions = [{"n": int(r["Eruption_Number"]), "start": f'{r["StartDateYear"]}-{(r["StartDateMonth"] or "0").zfill(2)}-{(r["StartDateDay"] or "0").zfill(2)}',
              "end": r["EndDateYear"] and f'{r["EndDateYear"]}-{(r["EndDateMonth"] or "0").zfill(2)}', "vei": r["ExplosivityIndexMax"] or None,
              "type": r["Activity_Type"]} for r in gvp]
doc = {"id": 273070, "name": {"en": "Taal", "ja": "タール山"}, "lat": 14.002, "lon": 120.993, "snapshot": str(D1), "start": str(D0),
       "units": {"so2": "umol/m2 (column, mean within ring)", "frp": "MW", "plume": "m"},
       "sources": ["s5p-offl-so2", "omi-omso2e", "mod14a1", "vnp14a1", "usgs-comcat", "phivolcs-bulletins", "phivolcs-lava-bulletins", "gvp", "msvolso2l4"],
       "daily": {"so2_15": so2_15, "so2_15_n": so2_n, "so2_50": so2_50, "omi_15": omi, "omi_15_n": omi_n},
       "frp_modis": frp_modis, "viirs_n": viirs_n, "usgs": usgs_rows,
       "bulletins": {"cols": ["day", "alert", "eq", "so2_t_d", "plume_m", "src", "link"], "rows": bul},
       "eruptions": eruptions, "msvolso2": [{"date": "2020-01-12", "so2_kt": 170, "plume_km": 17, "vei": 4}],
       "exposure": {"worldpop_2020_14km": 318177, "ocha_2020_14km": 459300}}
for name, d in {"full": doc, "no_bulletins": {**doc, "bulletins": None}, "weekly_series": {**doc, "daily": {k: v[::7] for k, v in doc["daily"].items()}}}.items():
    raw = json.dumps(d, separators=(",", ":"), ensure_ascii=False).encode()
    print(f"{name:14s} raw {len(raw)/1e3:7.1f} kB  gzip-9 {len(gzip.compress(raw, 9))/1e3:6.1f} kB")
    if name == "full": open(f"{OUT}/taal.json", "wb").write(raw)
parts = {k: len(gzip.compress(json.dumps(v, separators=(",", ":")).encode(), 9)) for k, v in doc.items()}
print("gzip by part (kB):", {k: round(v / 1e3, 1) for k, v in sorted(parts.items(), key=lambda x: -x[1])[:6]})
