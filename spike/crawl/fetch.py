"""Spike crawl: fetch a small, stratified sample at <=1 request/s into fixtures/raw."""
import json, random, re, sys, time, pathlib, httpx
RAW = pathlib.Path(__file__).resolve().parent.parent / "fixtures" / "raw"
UA = {"User-Agent": "plumes-spike/0.1 (retrospective volcano record; 1 req/s)"}
log = []
last = [0.0]
def get(client, url, dest):
    wait = 1.0 - (time.time() - last[0])
    if wait > 0: time.sleep(wait)
    t = time.time()
    try:
        r = client.get(url); code, body = r.status_code, r.content
    except Exception as e:
        code, body = repr(e)[:120], b""
    last[0] = time.time()
    if body: (RAW / dest).write_bytes(body)
    log.append({"url": url, "dest": dest, "status": code, "bytes": len(body), "s": round(time.time() - t, 2)})
    print(code, len(body), url, flush=True)

random.seed(20200112)
urls = [u.strip() for u in open(RAW / "wp_volc.txt")]
def year(u):
    y = re.findall(r"(20[12]\d)", u.rstrip("/").split("/")[-1]); return y[-1] if y else None
eng = [u for u in urls if not re.search(r"bulkang|ika-|alas-|buod", u) and re.search(r"bulletin|summary|advisory", u)]
quota = {"2017": 5, "2018": 3, "2019": 3, "2020": 5, "2021": 3, "2022": 3, "2023": 3, "2024": 3, "2025": 2}
wp = []
for y, n in quota.items():
    pool = [u for u in eng if year(u) == y]
    if y == "2020":  # include the Taal eruption week
        taal = [u for u in pool if "taal" in u and "january-2020" in u]
        wp += random.sample(taal, 2); n -= 2
    wp += random.sample(pool, n)
lava_ids = sorted(set(random.sample(range(1, 16921), 22) + [16917, 16918, 16919]))
vaac = [l.strip() for l in open(RAW / "vaac_taal.txt")][::2]
dromic = ["https://dromic.dswd.gov.ph/wp-content/uploads/2020/01/DSWD-DROMIC-Report-3-on-the-Taal-Volcano-Phreatic-Eruption-as-of-14-January-2020-6AM.docx",
          "https://dromic.dswd.gov.ph/wp-content/uploads/2020/01/DSWD-DROMIC-Report-17-on-the-Taal-Volcano-Phreatic-Eruption-as-of-21-January-2020-6PM.docx",
          "https://dromic.dswd.gov.ph/wp-content/uploads/2020/02/DSWD-DROMIC-Report-40-on-the-Taal-Volcano-Eruption-as-of-07-February-2020-6PM.docx"]
for d in ("wp", "lava", "vaac", "dromic"): (RAW / d).mkdir(exist_ok=True)
with httpx.Client(headers=UA, timeout=60, follow_redirects=True) as c:
    for u in wp: get(c, u, "wp/" + u.rstrip("/").split("/")[-1][:120] + ".html")
    for i in lava_ids: get(c, f"https://wovodat.phivolcs.dost.gov.ph/bulletin/activity-tvo?bid={i}&lang=en", f"lava/{i}.html")
    for v in vaac: get(c, "https://ds.data.jma.go.jp/svd/vaac/data/" + v, "vaac/" + v.split("/")[-1])
    for u in dromic: get(c, u, "dromic/" + u.split("/")[-1])
json.dump(log, open(RAW / "fetch_log.json", "w"), indent=0)
