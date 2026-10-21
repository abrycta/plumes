"""Re-fetch the LAVA sample with (a) the OS trust store, (b) certifi + the pinned GlobalSign intermediate."""
import json, random, ssl, sys, time, pathlib, httpx, truststore, certifi
RAW = pathlib.Path(__file__).resolve().parent.parent / "fixtures" / "raw"
mode = sys.argv[1]
if mode == "truststore":
    ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
else:
    ctx = ssl.create_default_context(cafile=certifi.where()); ctx.load_verify_locations(cafile=sys.argv[2])
random.seed(20200112)
ids = [int(x) for x in sys.argv[3:]] if len(sys.argv) > 3 else None
log = json.load(open(RAW / "fetch_log.json"))
if ids is None:
    ids = sorted(int(e["dest"].split("/")[1][:-5]) for e in log if e["dest"].startswith("lava/"))
out = []
with httpx.Client(verify=ctx, timeout=60, headers={"User-Agent": "plumes-spike/0.1 (1 req/s)"}) as c:
    for i in ids:
        t = time.time()
        try:
            r = c.get(f"https://wovodat.phivolcs.dost.gov.ph/bulletin/activity-tvo?bid={i}&lang=en"); code, body = r.status_code, r.content
        except Exception as e: code, body = repr(e)[:100], b""
        if body: (RAW / f"lava/{i}.html").write_bytes(body)
        out.append({"id": i, "status": code, "bytes": len(body), "s": round(time.time() - t, 2)}); print(code, len(body), i, flush=True)
        time.sleep(max(0, 1 - (time.time() - t)))
json.dump(out, open(RAW / f"lava_log_{mode}.json", "w"))
