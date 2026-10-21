"""ERA5 pressure-level winds at one grid point, read from ARCO-ERA5 by HTTP range (DECISIONS S4; spike era5_range.py).

An ARCO chunk is one hour x 37 levels x the globe (117 MB per variable-hour). The reader range-reads the Blosc header,
then only the compressed block(s) holding the wanted level's latitude row, and decodes them (LZ4 + byte-unshuffle).
That depends on Blosc1's internal layout, so `--verify` decodes one whole chunk with numcodecs and compares (S4).

    uv run --group era5 python -m plumes.era5 --start 2020-01-11 --end 2020-01-15 --lat 14.0106 --lon 120.9975 --out story-taal-2020
"""

from __future__ import annotations

import argparse
import json
import struct
from concurrent.futures import ThreadPoolExecutor

import httpx
import lz4.block
import numcodecs
import numpy as np

from plumes.paths import TABLES

B = "https://storage.googleapis.com/gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3"
NL, NY, NX = 37, 721, 1440
LEVELS = [250, 300, 500, 700]
c = httpx.Client(timeout=60, limits=httpx.Limits(max_connections=8))
stats = {"requests": 0, "bytes": 0}


def get(url, rng=None) -> bytes:
    r = c.get(url, headers={"Range": f"bytes={rng[0]}-{rng[1]}"} if rng else {})
    r.raise_for_status()
    stats["requests"] += 1
    stats["bytes"] += len(r.content)
    return r.content


def coord(name, dtype):
    return np.frombuffer(numcodecs.Blosc().decode(get(f"{B}/{name}/0")), dtype=dtype)


def read_row(var: str, t: int, levels_idx: dict[int, int], iy: int) -> dict[int, np.ndarray]:
    """One latitude row (all longitudes) per wanted level for hour index t."""
    url = f"{B}/{var}/{t}.0.0.0"
    head = get(url, (0, 16 + 4 * 400 - 1))
    _, _, flags, ts, nbytes, bsize, cbytes = struct.unpack("<BBBBIII", head[:16])
    nblocks = -(-nbytes // bsize)
    bstarts = struct.unpack(f"<{nblocks}I", head[16:16 + 4 * nblocks])
    split, shuffle = not (flags & 0x10), flags & 0x1
    out = {}
    for lev, il in levels_idx.items():
        e0, e1 = (il * NY + iy) * NX, (il * NY + iy + 1) * NX
        b0, b1 = (e0 * ts) // bsize, (e1 * ts - 1) // bsize
        raw = bytearray()
        for b in range(b0, b1 + 1):
            start, end = bstarts[b], (bstarts[b + 1] - 1 if b + 1 < nblocks else cbytes - 1)
            blk, n = get(url, (start, end)), min(bsize, nbytes - b * bsize)
            streams = ts if (split and n == bsize) else 1
            sub, pos, dec = n // streams, 0, bytearray()
            for _ in range(streams):
                cs = struct.unpack("<i", blk[pos:pos + 4])[0]
                pos += 4
                dec += blk[pos:pos + cs] if cs == sub else lz4.block.decompress(bytes(blk[pos:pos + cs]), uncompressed_size=sub)
                pos += cs
            if shuffle:
                k = (n // ts) * ts
                dec = bytearray(np.frombuffer(bytes(dec[:k]), np.uint8).reshape(ts, -1).T.reshape(-1).tobytes()) + dec[k:]
            raw += dec
        a = np.frombuffer(bytes(raw), "<f4")
        off = e0 - b0 * bsize // ts
        out[lev] = a[off:off + NX]
    return out


def hour_index(ts: str) -> int:
    return int((np.datetime64(ts) - np.datetime64("1900-01-01T00")) / np.timedelta64(1, "h"))


def winds(start: str, end: str, lat: float, lon: float, step: int = 6) -> dict:
    levels, lats, lons = coord("level", "<i8"), coord("latitude", "<f4"), coord("longitude", "<f4")
    iy, ix = int(np.argmin(abs(lats - lat))), int(np.argmin(abs(lons - lon % 360)))
    lidx = {lv: int(np.where(levels == lv)[0][0]) for lv in LEVELS}
    t0, t1 = hour_index(start + "T00"), hour_index(end + "T18")
    hours = list(range(t0, t1 + 1, step))
    with ThreadPoolExecutor(8) as ex:
        U = list(ex.map(lambda t: read_row("u_component_of_wind", t, lidx, iy), hours))
        V = list(ex.map(lambda t: read_row("v_component_of_wind", t, lidx, iy), hours))
    rows = []
    for t, u, v in zip(hours, U, V, strict=True):
        ts = str(np.datetime64("1900-01-01T00") + np.timedelta64(t, "h")) + ":00Z"
        for lv in LEVELS:
            uu, vv = float(u[lv][ix]), float(v[lv][ix])
            rows.append([ts, lv, round(uu, 2), round(vv, 2), round((uu**2 + vv**2) ** 0.5, 1), round(float(np.degrees(np.arctan2(uu, vv))) % 360)])
    return {"point": [float(lons[ix]), float(lats[iy])], "cols": ["time", "hPa", "u", "v", "speedMs", "dirToDeg"], "rows": rows, **stats}


def verify(t: str = "2020-01-12T06") -> dict:
    """S4 check: the block reader equals a full numcodecs decode of the same chunk (one 117 MB read)."""
    levels, lats = coord("level", "<i8"), coord("latitude", "<f4")
    iy = int(np.argmin(abs(lats - 14.0)))
    lidx = {lv: int(np.where(levels == lv)[0][0]) for lv in LEVELS}
    h = hour_index(t)
    part = read_row("u_component_of_wind", h, lidx, iy)
    full = np.frombuffer(numcodecs.Blosc().decode(get(f"{B}/u_component_of_wind/{h}.0.0.0")), "<f4").reshape(NL, NY, NX)
    ok = all(np.array_equal(part[lv], full[il, iy]) for lv, il in lidx.items())
    return {"verified": ok, "hour": t}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start")
    ap.add_argument("--end")
    ap.add_argument("--lat", type=float)
    ap.add_argument("--lon", type=float)
    ap.add_argument("--out")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    if a.verify:
        print(verify())
    else:
        res = winds(a.start, a.end, a.lat, a.lon)
        TABLES.mkdir(parents=True, exist_ok=True)
        (TABLES / f"era5-{a.out}.json").write_text(json.dumps(res))
        print({k: v for k, v in res.items() if k != "rows"}, len(res["rows"]), "rows")
