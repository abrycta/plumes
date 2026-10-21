"""Item 21: read phl_admin3.dbf from HDX's shp zip by HTTP Range only."""
import io, json, struct, time, zipfile, httpx
URL = "https://data.humdata.org/dataset/caf116df-f984-4deb-85ca-41b349d3f313/resource/4e4067d6-3fc8-4d2c-91ea-330c3d4f8e8e/download/phl_admin_boundaries.shp.zip"
class RangeFile(io.RawIOBase):
    def __init__(s, url):
        s.c = httpx.Client(follow_redirects=True, timeout=60); s.reqs = 0; s.bytes = 0; s.pos = 0
        r = s.c.get(url, headers={"Range": "bytes=0-0"}); s.url = str(r.url); s.size = int(r.headers["content-range"].split("/")[1]); s.reqs += 1
    def seekable(s): return True
    def readable(s): return True
    def tell(s): return s.pos
    def seek(s, off, wh=0): s.pos = off if wh == 0 else (s.pos + off if wh == 1 else s.size + off); return s.pos
    def read(s, n=-1):
        if n < 0: n = s.size - s.pos
        if n == 0 or s.pos >= s.size: return b""
        end = min(s.size, s.pos + n) - 1; r = s.c.get(s.url, headers={"Range": f"bytes={s.pos}-{end}"})
        assert r.status_code == 206, r.status_code
        s.reqs += 1; s.bytes += len(r.content); s.pos += len(r.content); return r.content
t = time.time(); f = RangeFile(URL)
buf = f
z = zipfile.ZipFile(buf); name = [n for n in z.namelist() if n.endswith("admin3.dbf")][0]; info = z.getinfo(name)
data = z.read(name)
nrec, hlen, rlen = struct.unpack("<IHH", data[4:12]); fields = []
for i in range(32, hlen - 1, 32):
    fn = data[i:i + 11].split(b"\0")[0].decode(); fields.append((fn, data[i + 11:i + 12].decode(), data[i + 16]))
rows = []
for k in range(nrec):
    rec = data[hlen + k * rlen + 1: hlen + (k + 1) * rlen]; o = 0; d = {}
    for fn, ft, fl in fields: d[fn] = rec[o:o + fl].decode("utf-8", "replace").strip(); o += fl
    rows.append(d)
print(json.dumps({"zip_bytes": f.size, "member": name, "member_compressed": info.compress_size, "member_bytes": len(data), "requests": f.reqs,
                  "bytes_read": f.bytes, "seconds": round(time.time() - t, 1), "records": nrec, "fields": [x[0] for x in fields],
                  "sample": {k: rows[0][k] for k in list(rows[0])[:12]}}, indent=0))
