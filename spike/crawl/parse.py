"""Spike parsers: measure fields recovered and parse rates on the fixtures."""
import glob, gzip, json, re, os, pathlib, collections, docx
RAW = pathlib.Path(__file__).resolve().parent.parent / "fixtures" / "raw"
NUM = r"(\d[\d,]*)"
WORDS = dict(zip("zero one two three four five six seven eight nine ten eleven twelve".split(), range(13)))
def text(html):
    html = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", html); t = re.sub(r"&nbsp;|&#8211;|&#8217;", " ", t); return re.sub(r"\s+", " ", t)
def ival(s): return int(s.replace(",", ""))

# --- PHIVOLCS WordPress prose bulletins ---
def wp_fields(t):
    f, app = {}, {}
    m = re.search(r"Alert Level (\d)", t, re.I); app["alert"] = True; f["alert"] = int(m.group(1)) if m else None
    app["eq"] = bool(re.search(r"(?:network|PSN|Seismic Network).{0,80}(?:earthquake|tremor)", t, re.I))
    m = re.search(r"(?:recorded|detected)\s+(?:a total of\s+)?(?:\w+\s+)?\(?(\d[\d,]*)\)?\s+(?:volcanic|low[- ]frequency|tectonic|volcano-tectonic)?\s*(?:volcanic\s+)?(?:earthquakes?|tremor)", t, re.I) \
        or re.search(r"(\w+) \((\d+)\) volcanic earthquakes?", t, re.I) or re.search(r"\((\d+)\) episodes of volcanic tremor", t, re.I) \
        or re.search(r"\b(no|zero|not detect any) volcanic earthquake", t, re.I)
    f["eq"] = (0 if m and m.group(1).lower() in ("no", "zero", "not detect any") else ival(m.groups()[-1])) if m else None
    app["so2"] = bool(re.search(r"sulfur dioxide|SO2|SO₂", t))
    m = re.search(r"(?:averaged|measured at|emission(?: rate)?(?: was)?(?: measured)?(?: at)?|flux of|was)\s+(?:an average of\s+)?" + NUM + r"\s*(?:tonnes|tons)(?:\s*/\s*|\s+per\s+)day(?:.{0,40}?on\s+(\d{1,2}\s+\w+\s+\d{4}|\w+\s+\d{1,2},?\s+\d{4}))?", t, re.I) \
        or re.search(NUM + r"\s*(?:tonnes|tons)(?:\s*/\s*|\s+per\s+)day", t, re.I)
    f["so2"] = ival(m.group(1)) if m else None
    f["so2_date"] = (m.group(2) if m and m.lastindex and m.lastindex >= 2 else None)
    app["plume"] = bool(re.search(r"plume|steam", t, re.I)) and bool(re.search(r"\d+\s*(?:meters|metres|m)\s+(?:tall|high)", t, re.I))
    m = re.search(r"(\d[\d,]*)\s*(?:meters|metres|m)\s+(?:tall|high)", t, re.I); f["plume_m"] = ival(m.group(1)) if m else None
    app["deform"] = bool(re.search(r"inflat|deflat|leveling|levelling|GPS|tilt|deformation", t, re.I))
    m = re.search(r"[^.]*(?:inflat|deflat|leveling|levelling|GPS|tilt|deformation)[^.]*\.", t, re.I); f["deform"] = m.group(0).strip()[:200] if m else None
    return f, app

def run_wp():
    rows = []
    for p in sorted(glob.glob(str(RAW / "wp/*.html"))):
        h = open(p, errors="ignore").read(); i = h.find("entry-content"); j = h.find("sharedaddy", i)
        body = text(h[i:j if j > 0 else i + 40000]).replace("entry-content -->", "")
        body = body.split("Latest Earthquakes")[0] if len(body) < 200 else body
        slug = os.path.basename(p)[:-5]; yr = re.findall(r"(20[12]\d)", slug)[-1]
        empty = len(body.strip()) < 200
        f, app = ({}, {}) if empty else wp_fields(body)
        rows.append({"slug": slug, "year": yr, "kind": "summary" if "summary" in slug else "bulletin", "bytes": os.path.getsize(p),
                     "gz": len(gzip.compress(open(p, "rb").read(), 9)), "text_chars": len(body), "empty": empty, "f": f, "app": app})
    return rows

# --- PHIVOLCS-LAVA ---
LAVA_KEYS = ["Eruption", "Seismicity", "Acidity", "Temperature", "Sulfur Dioxide Flux", "Plume", "Ground Deformation"]
def run_lava():
    rows = []
    for p in sorted(glob.glob(str(RAW / "lava/*.html")), key=lambda s: int(os.path.basename(s)[:-5])):
        h = open(p, errors="ignore").read(); t = text(h); bid = int(os.path.basename(p)[:-5])
        if "PARAMETERS" not in t: rows.append({"bid": bid, "ok": False, "bytes": len(h)}); continue
        d = re.search(r"Date: (\d{1,2} \w+ \d{4}) \(([^)]*)\)", t); a = re.search(r"ALERT LEVEL (\d)", t)
        par = t[t.find("PARAMETERS") + 10: t.find("Earthquake Location")]
        secs = {}
        for k in LAVA_KEYS:
            m = re.search(re.escape(k) + r"(?: Main Crater Lake)?\s*(.*?)(?=\s*(?:" + "|".join(map(re.escape, LAVA_KEYS)) + r")\b|$)", par)
            if m: secs[k] = m.group(1).strip()
        so2 = re.search(NUM + r" tonnes / day \((\d{1,2} \w+ \d{4})\)", secs.get("Sulfur Dioxide Flux", ""))
        eq = re.search(r"(\d+) volcanic earthquakes?", secs.get("Seismicity", "")) or re.search(r"^(No|\d+)", secs.get("Seismicity", ""))
        plume = re.search(r"(\d[\d,]*) meters", secs.get("Plume", ""))
        f = {"date": d.group(1) if d else None, "alert": int(a.group(1)) if a else None,
             "eq": (0 if eq and eq.group(1) == "No" else int(eq.group(1))) if eq else None,
             "so2": ival(so2.group(1)) if so2 else None, "so2_date": so2.group(2) if so2 else None,
             "plume_m": ival(plume.group(1)) if plume else None, "deform": secs.get("Ground Deformation")}
        app = {"date": True, "alert": True, "eq": bool(secs.get("Seismicity")), "so2": "tonnes" in secs.get("Sulfur Dioxide Flux", ""),
               "plume_m": "meters" in secs.get("Plume", ""), "deform": "Ground Deformation" in secs}
        rows.append({"bid": bid, "ok": True, "bytes": len(h), "gz": len(gzip.compress(h.encode(), 9)), "sections": list(secs), "f": f, "app": app})
    return rows

# --- Tokyo VAAC ---
def run_vaac():
    rows = []
    for p in sorted(glob.glob(str(RAW / "vaac/*.html"))):
        t = text(open(p, errors="ignore").read())
        dtg = re.search(r"DTG: (\d{8}/\d{4}Z)", t); nr = re.search(r"ADVISORY NR: (\d{4}/\d+)", t)
        obs = re.search(r"OBS VA CLD: (.*?)(?:FCST|RMK|$)", t); erup = re.search(r"ERUPTION DETAILS: (.*?)(?:OBS VA DTG|$)", t)
        fls = [int(x) for x in re.findall(r"(?:SFC|FL\d{3})/FL(\d{3})", obs.group(1) if obs else "")]
        efl = [int(x) for x in re.findall(r"FL(\d{3})", erup.group(1) if erup else "")]
        top = max(fls) if fls else (max(efl) if efl else None)
        rows.append({"file": os.path.basename(p), "bytes": os.path.getsize(p), "dtg": dtg.group(1) if dtg else None, "nr": nr.group(1) if nr else None,
                     "obs_top_fl": max(fls) if fls else None, "eruption_fl": max(efl) if efl else None, "top_fl": top,
                     "not_identifiable": bool(obs and "NOT IDENTIFIABLE" in obs.group(1))})
    return rows

# --- DSWD DROMIC docx ---
def grand_total(tbl):
    for r in tbl.rows:
        cells = [c.text.strip() for c in r.cells]
        if cells and cells[0].upper().startswith("GRAND TOTAL"):
            return [c for c in cells[2:]]
def run_dromic():
    rows = []
    for p in sorted(glob.glob(str(RAW / "dromic/*.docx"))):
        d = docx.Document(p); out = {"file": os.path.basename(p), "bytes": os.path.getsize(p), "tables": len(d.tables)}
        for tbl in d.tables:
            hdr = " ".join(c.text for r in tbl.rows[:4] for c in r.cells).upper(); gt = grand_total(tbl)
            if not gt: continue
            if "AFFECTED" in hdr and "affected" not in out: out["affected"] = {"families": gt[-2], "persons": gt[-1]}
            elif "INSIDE EC" in hdr and "inside" not in out: out["inside"] = {"ecs_now": gt[1], "families_now": gt[3], "persons_now": gt[5], "persons_cum": gt[4]}
            elif "OUTSIDE EC" in hdr and "outside" not in out: out["outside"] = {"families_now": gt[1], "persons_now": gt[3], "persons_cum": gt[2]}
        rows.append(out)
    return rows

def rate(rows, key):
    a = [r for r in rows if r.get("app", {}).get(key)]; ok = [r for r in a if r["f"].get(key) is not None]
    return f"{len(ok)}/{len(a)}" + (f" ({100*len(ok)/len(a):.0f} %)" if a else "")

if __name__ == "__main__":
    wp, lava, vaac, dromic = run_wp(), run_lava(), run_vaac(), run_dromic()
    json.dump({"wp": wp, "lava": lava, "vaac": vaac, "dromic": dromic}, open(RAW.parent / "parsed.json", "w"), indent=1, default=str)
    full = [r for r in wp if not r["empty"]]
    print("WP pages", len(wp), "empty shells", sum(r["empty"] for r in wp), "by year/kind/empty:",
          sorted(collections.Counter((r["year"], r["kind"], r["empty"]) for r in wp).items()))
    print("WP bytes median", sorted(r["bytes"] for r in wp)[len(wp)//2], "gz median", sorted(r["gz"] for r in wp)[len(wp)//2],
          "text chars median", sorted(r["text_chars"] for r in full)[len(full)//2])
    for k in ("alert", "eq", "so2", "plume", "deform"): print(" WP", k, rate(full, k if k != "plume" else "plume") if k != "plume" else rate([dict(r, f={**r["f"], "plume": r["f"]["plume_m"]}) for r in full], "plume"))
    ok = [r for r in lava if r["ok"]]
    print("LAVA ok", len(ok), "/", len(lava), "bytes median", sorted(r["bytes"] for r in ok)[len(ok)//2], "gz", sorted(r["gz"] for r in ok)[len(ok)//2])
    for k in ("date", "alert", "eq", "so2", "plume_m", "deform"): print(" LAVA", k, rate(ok, k))
    print("LAVA section sets", collections.Counter(tuple(r["sections"]) for r in ok).most_common())
    print("VAAC", len(vaac), "dtg", sum(1 for r in vaac if r["dtg"]), "top FL", sum(1 for r in vaac if r["top_fl"]), "obs FL", sum(1 for r in vaac if r["obs_top_fl"]),
          "not identifiable", sum(r["not_identifiable"] for r in vaac), "bytes", min(r["bytes"] for r in vaac), max(r["bytes"] for r in vaac))
    for r in vaac: print("  ", r["dtg"], r["nr"], r["obs_top_fl"], r["eruption_fl"])
    for r in dromic: print("DROMIC", r)
