"""ERA5 u/v at 250/300/500 hPa over Taal, 12-13 Jan 2020, from ARCO-ERA5 by HTTP range reads of only the Blosc blocks needed."""
import json, struct, time, sys, numpy as np, httpx, lz4.block, numcodecs
B = "https://storage.googleapis.com/gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3"
stats = {"requests": 0, "bytes": 0}
c = httpx.Client(timeout=60, limits=httpx.Limits(max_connections=16))
def get(url, rng=None):
    r = c.get(url, headers={"Range": f"bytes={rng[0]}-{rng[1]}"} if rng else {}); r.raise_for_status()
    stats["requests"] += 1; stats["bytes"] += len(r.content); return r.content
def coord(name, dtype):
    return np.frombuffer(numcodecs.Blosc().decode(get(f"{B}/{name}/0")), dtype=dtype)
levels = coord("level", "<i8"); lats = coord("latitude", "<f4"); lons = coord("longitude", "<f4")
NL, NY, NX = 37, 721, 1440
LAT, LON, HALF = 14.0, 121.0, 8                 # Taal, +-2 degrees
iy = int(np.argmin(abs(lats - LAT))); ix = int(np.argmin(abs(lons - LON)))
want_levels = [250, 300, 500]

def read_window(var, t):
    url = f"{B}/{var}/{t}.0.0.0"
    head = get(url, (0, 16 + 4 * 400 - 1))
    ver, verlz, flags, ts, nbytes, bsize, cbytes = struct.unpack("<BBBBIII", head[:16])
    nblocks = -(-nbytes // bsize); bstarts = struct.unpack(f"<{nblocks}I", head[16:16 + 4 * nblocks])
    split = not (flags & 0x10); shuffle = flags & 0x1
    out = {}
    for lev in want_levels:
        il = int(np.where(levels == lev)[0][0])
        e0 = (il * NY + iy - HALF) * NX; e1 = (il * NY + iy + HALF + 1) * NX   # element range (full lon rows)
        b0, b1 = (e0 * ts) // bsize, (e1 * ts - 1) // bsize
        raw = bytearray()
        for b in range(b0, b1 + 1):
            start = bstarts[b]; end = bstarts[b + 1] - 1 if b + 1 < nblocks else cbytes - 1
            blk = get(url, (start, end)); n = min(bsize, nbytes - b * bsize)
            streams = ts if (split and n == bsize) else 1; sub = n // streams; pos = 0; dec = bytearray()
            for _ in range(streams):
                cs = struct.unpack("<i", blk[pos:pos + 4])[0]; pos += 4
                dec += blk[pos:pos + cs] if cs == sub else lz4.block.decompress(bytes(blk[pos:pos + cs]), uncompressed_size=sub); pos += cs
            if shuffle:
                k = (n // ts) * ts; arr = np.frombuffer(bytes(dec[:k]), np.uint8).reshape(ts, -1).T.reshape(-1)
                dec = bytearray(arr.tobytes()) + dec[k:]
            raw += dec
        a = np.frombuffer(bytes(raw), "<f4"); off = e0 - b0 * bsize // ts
        win = a[off:off + (e1 - e0)].reshape(2 * HALF + 1, NX)[:, ix - HALF: ix + HALF + 1]
        out[lev] = win
    return out

t0 = int((np.datetime64("2020-01-12T00") - np.datetime64("1900-01-01T00")) / np.timedelta64(1, "h"))
step = int(sys.argv[1]) if len(sys.argv) > 1 else 1
start = time.time(); rows = []
from concurrent.futures import ThreadPoolExecutor
hours = list(range(0, 48, step))
with ThreadPoolExecutor(int(sys.argv[2]) if len(sys.argv) > 2 else 1) as ex:
    U = list(ex.map(lambda h: read_window("u_component_of_wind", t0 + h), hours)); V = list(ex.map(lambda h: read_window("v_component_of_wind", t0 + h), hours))
for h, u, v in zip(hours, U, V):
    for lev in want_levels:
        uu, vv = float(u[lev][HALF, HALF]), float(v[lev][HALF, HALF])
        rows.append({"time": str(np.datetime64("2020-01-12T00") + np.timedelta64(h, "h")), "hPa": lev, "u": round(uu, 2), "v": round(vv, 2),
                     "speed": round((uu**2 + vv**2) ** .5, 1), "dir_to_deg": round(float(np.degrees(np.arctan2(uu, vv))) % 360, 0),
                     "win_mean_u": round(float(u[lev].mean()), 2)})
res = {"seconds": round(time.time() - start, 1), **stats, "grid_point": [float(lats[iy]), float(lons[ix])], "window_cells": (2*HALF+1)**2, "rows": rows}
json.dump(res, open("out/era5_taal.json", "w"), indent=0)
print(json.dumps({k: v for k, v in res.items() if k != "rows"}), rows[:3], rows[-3:], sep="\n")
