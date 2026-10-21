"""OCHA COD-AB admin-3 attributes by HTTP range read (DECISIONS Q30, spike item 21): only the member phl_admin3.dbf of
HDX's shapefile zip is read (about 120 kB in a handful of Range requests), never the 900+ MB file.

    uv run python -m plumes.codab
"""

from __future__ import annotations

import csv
import io
import struct
import zipfile

import httpx

from plumes.crawl.records import now, sha256
from plumes.http import UA
from plumes.paths import RAW

URL = ("https://data.humdata.org/dataset/caf116df-f984-4deb-85ca-41b349d3f313/resource/"
       "4e4067d6-3fc8-4d2c-91ea-330c3d4f8e8e/download/phl_admin_boundaries.shp.zip")
OUT = RAW / "cod-ab"


class RangeFile(io.RawIOBase):
    """A read-only seekable file over HTTP Range requests (zipfile reads the central directory, then one member)."""

    def __init__(self, url: str):
        self.c = httpx.Client(follow_redirects=True, timeout=60, headers={"User-Agent": UA})
        r = self.c.get(url, headers={"Range": "bytes=0-0"})
        if r.status_code != 206:
            raise RuntimeError(f"range requests not honoured ({r.status_code})")
        self.url, self.size, self.pos, self.requests, self.bytes = str(r.url), int(r.headers["content-range"].split("/")[1]), 0, 1, 0

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else (self.pos + off if whence == 1 else self.size + off)
        return self.pos

    def read(self, n=-1):
        if n < 0:
            n = self.size - self.pos
        if n == 0 or self.pos >= self.size:
            return b""
        end = min(self.size, self.pos + n) - 1
        r = self.c.get(self.url, headers={"Range": f"bytes={self.pos}-{end}"})
        if r.status_code != 206:
            raise RuntimeError(f"range read failed ({r.status_code})")
        self.requests += 1
        self.bytes += len(r.content)
        self.pos += len(r.content)
        return r.content


def read_dbf(data: bytes) -> list[dict]:
    nrec, hlen, rlen = struct.unpack("<IHH", data[4:12])
    fields = [(data[i:i + 11].split(b"\0")[0].decode(), data[i + 16]) for i in range(32, hlen - 1, 32)]
    rows = []
    for k in range(nrec):
        rec, o, d = data[hlen + k * rlen + 1: hlen + (k + 1) * rlen], 0, {}
        for name, length in fields:
            d[name] = rec[o:o + length].decode("utf-8", "replace").strip()
            o += length
        rows.append(d)
    return rows


def fetch() -> dict:
    f = RangeFile(URL)
    z = zipfile.ZipFile(f)
    name = next(n for n in z.namelist() if n.endswith("admin3.dbf"))
    data = z.read(name)
    rows = read_dbf(data)
    OUT.mkdir(parents=True, exist_ok=True)
    keep = ["adm3_pcode", "adm3_name", "adm2_name", "adm1_name", "area_sqkm", "center_lat", "center_lon"]
    with open(OUT / "phl_admin3.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keep, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return {"url": URL, "member": name, "zip_bytes": f.size, "bytes_read": f.bytes, "requests": f.requests, "rows": len(rows),
            "sha256_member": sha256(data), "fetched": now()}


if __name__ == "__main__":
    print(fetch())
