"""COMET Volcano Portal LiCSBAS series: the per-volcano LOS chart and the `deformation-velocity` layer (LAYERS-PLAN §3.1).

COMET publishes, for each volcano and Sentinel-1 frame, a GACOS-corrected LiCSBAS time series on a 100 x 100 grid
(about 50 x 55 km around the volcano) as one JSON file, no login:

    https://comet-volcanodb.org/data/disp_data_gacos/<region>/<volcano>_<frame>_web_x100.json

Keys read here (checked on taal_032D_07536_111313, 2026-10-22): `dates` (ISO days), `x` (lon, ascending), `y` (lat,
ascending: row 0 is the southern edge), `data_raw[t][row][col]` cumulative LOS displacement in mm since the first date
("null" = no value), `mask` (1 = COMET kept the pixel), `coh` (mean coherence 0-1), `refarea` = [col0, col1, row0, row1]
(LiCSBAS x1:x2/y1:y2, half-open) and `timestamp` (when COMET last built the file). `data_raw` is not referenced: the
portal subtracts the reference area on the fly, and so does this module. Sign: positive = toward the satellite (LiCSBAS).

Outputs, per volcano and frame:
- a sparse series `los_comet_<frame>` (summit window minus reference area): cols date, los_mm, los_std_mm, where
  los_std_mm is the spread of the summit-window pixels on that date (not a formal error);
- a velocity grid: least-squares slope per pixel over the frame's whole span in mm/yr, masked with COMET's `mask` and a
  mean-coherence floor, written as an Int16 GeoTIFF (value = mm/yr x 10, nodata -32768, EPSG:4326, deflate + predictor).

Licence (DECISIONS L1a): published with attribution to COMET, "LiCSAR contains modified Copernicus Sentinel data
[years]" and the CC BY-NC 4.0 notice with its link. Raw JSON is adopted as `comet-licsbas-<date>` (plumes.adopt).

    uv run --group comet python -m plumes.comet fetch [--only taal] [--limit 1]     # discover + download changed frames
    uv run --group comet python -m plumes.comet reduce [--only taal] --out DIR      # canary: series + GeoTIFFs, no publish
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import struct
import time
import zlib
from pathlib import Path

from plumes.crawl.records import Records, now, sha256
from plumes.http import Polite
from plumes.paths import CROSSWALK, RAW

SOURCE_ID = "comet-licsbas"
PORTAL = "https://comet-volcanodb.org/data/"
FRAMES_JS = PORTAL + "volcanoes_frames/volcanoes_frames.js"
DISP_URL = PORTAL + "disp_data_gacos/{region}/{name}_{frame}_web_x100.json"
OUT = RAW / SOURCE_ID
LICENCE_URL = "https://creativecommons.org/licenses/by-nc/4.0/"

COH_FLOOR = 0.3  # LAYERS-PLAN §3.1 [U]: Taal 032D keeps 1,230 of 8,811 COMET-valid pixels at 0.3 (1,983 at 0.2)
SUMMIT_KM = (2.0, 3.0)  # summit window radius; the second is tried when the first holds fewer than MIN_PIXELS valid pixels
MIN_PIXELS = 3
MIN_DATES = 0.5  # a pixel needs values on at least half of the dates for a velocity
SCALE, NODATA = 10, -32768
DOMAIN_STEP = 5  # the legend domain is the 98th percentile of |velocity| over all frames, rounded up to this (mm/yr)


# ---------------------------------------------------------------- discovery and download

def comet_names(frames: dict) -> dict[str, str]:
    """Plumes volcano id -> COMET volcano name: the GVP name (lower case, `_` for spaces and hyphens), else the Plumes id."""
    out = {}
    with open(CROSSWALK, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            for k in ((r["gvp_name"] or "").lower().replace(" ", "_").replace("-", "_"), r["id"].replace("-", "_")):
                if k and k in frames:
                    out[r["id"]] = k
                    break
    return out


def parse_frames_js(text: str) -> dict:
    return json.loads(text[text.index("{"): text.rindex("}") + 1])


def discover(c: Polite) -> list[dict]:
    """Every (volcano, frame) with a GACOS series: COMET's frame list, then a HEAD per candidate (404 = no series)."""
    frames = parse_frames_js(c.get(FRAMES_JS).raise_for_status().text)
    out = []
    for vid, name in sorted(comet_names(frames).items()):
        region = frames[name]["region"]
        for fr in frames[name]["frames"]:
            url = DISP_URL.format(region=region, name=name, frame=fr["id"])
            time.sleep(c.min_interval)
            h = c.client.head(url)
            if h.status_code == 200:
                out.append({"volcano": vid, "cometName": name, "region": region, "frame": fr["id"], "url": url,
                            "lastModified": h.headers.get("last-modified"), "bytes": int(h.headers.get("content-length") or 0)})
    return out


def raw_path(rec: dict) -> Path:
    return OUT / f"{rec['cometName']}_{rec['frame']}.json"


def fetch(only: list[str] | None = None, limit: int | None = None) -> dict:
    """Download the frames whose Last-Modified changed since the last fetch (the weekly run re-downloads only those)."""
    log = Records(OUT / "fetch.jsonl")
    seen = {(r["url"], r.get("lastModified")) for r in log if r.get("status") == 200}
    with Polite(min_interval=1.0, timeout=180) as c:
        found = discover(c)
        (OUT / "frames.json").write_text(json.dumps({"discovered": now(), "frames": found}, indent=1))
        todo = [r for r in found if (not only or r["volcano"] in only) and ((r["url"], r["lastModified"]) not in seen or not raw_path(r).exists())]
        n = 0
        for rec in todo[:limit]:
            r = c.get(rec["url"])
            if r.status_code != 200:
                log.add({**rec, "status": r.status_code, "fetched": now()})
                continue
            problems = check_raw(r.json())
            if problems:
                log.add({**rec, "status": "rejected", "fetched": now(), "problems": problems})
                continue
            raw_path(rec).write_bytes(r.content)
            log.add({**rec, "status": 200, "fetched": now(), "sha256": sha256(r.content), "bytes": len(r.content)})
            n += 1
    return {"frames": len(found), "volcanoes": len({r["volcano"] for r in found}), "downloaded": n, "pending": max(len(todo) - n, 0)}


def check_raw(j: dict) -> list[str]:
    """Shape checks before a file is kept: a changed COMET format must fail loudly, not draw a wrong map."""
    probs = []
    for k in ("dates", "x", "y", "data_raw", "mask", "coh", "refarea", "timestamp"):
        if k not in j:
            probs.append(f"missing key {k}")
    if probs:
        return probs
    nt, ny, nx = len(j["dates"]), len(j["y"]), len(j["x"])
    if len(j["data_raw"]) != nt or any(len(t) != ny or len(t[0]) != nx for t in j["data_raw"][:3]):
        probs.append("data_raw is not dates x y x x")
    if len(j["mask"]) != ny or len(j["mask"][0]) != nx:
        probs.append("mask shape")
    if len(j["refarea"]) != 4:
        probs.append("refarea is not 4 numbers")
    if j["dates"] != sorted(j["dates"]) or nt < 10:
        probs.append("dates unsorted or fewer than 10")
    if not (j["x"][0] < j["x"][-1] and j["y"][0] < j["y"][-1]):
        probs.append("x or y not ascending")
    return probs


# ---------------------------------------------------------------- reduction

def _arrays(j: dict):
    import numpy as np

    d = np.array([[[np.nan if v in ("null", None) else v for v in row] for row in t] for t in j["data_raw"]], dtype=float)
    return d, np.asarray(j["mask"]) == 1, np.asarray(j["coh"], dtype=float)


def ref_series(j: dict, d):
    import numpy as np

    c0, c1, r0, r1 = (int(v) for v in j["refarea"])
    sub = d[:, r0:max(r1, r0 + 1), c0:max(c1, c0 + 1)]
    return np.nanmean(sub.reshape(len(d), -1), axis=1), ((j["x"][c0] + j["x"][max(c1 - 1, c0)]) / 2, (j["y"][r0] + j["y"][max(r1 - 1, r0)]) / 2)


def years_since(dates: list[str]):
    import numpy as np

    d0 = dt.date.fromisoformat(dates[0])
    return np.array([(dt.date.fromisoformat(d) - d0).days / 365.25 for d in dates])


def velocity(d, t):
    """Least-squares slope per pixel (units of d per unit of t), ignoring missing dates; NaN with too few dates."""
    import numpy as np

    w = np.isfinite(d)
    n = w.sum(0)
    tt = np.where(w, t[:, None, None], 0.0)
    y = np.where(w, d, 0.0)
    st, sy, stt, sty = tt.sum(0), y.sum(0), (tt * tt).sum(0), (tt * y).sum(0)
    with np.errstate(invalid="ignore", divide="ignore"):
        v = (sty - st * sy / n) / (stt - st * st / n)
    v[n < MIN_DATES * len(t)] = np.nan
    return v


def km(lat1, lon1, lat2, lon2) -> float:
    p = math.pi / 180
    a = math.sin((lat2 - lat1) * p / 2) ** 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(a))


def summit_series(j: dict, d, mask, ref, lon: float, lat: float) -> tuple[list, float | None, int]:
    """Mean of the valid pixels within SUMMIT_KM of (lon, lat), minus the reference area, per date."""
    import numpy as np

    for radius in SUMMIT_KM:
        sel = [(i, k) for i, y in enumerate(j["y"]) for k, x in enumerate(j["x"]) if mask[i, k] and km(lat, lon, y, x) <= radius]
        if len(sel) >= MIN_PIXELS:
            break
    else:
        return [], None, 0
    ii, kk = zip(*sel, strict=True)
    win = d[:, list(ii), list(kk)] - ref[:, None]
    rows = []
    for date, vals in zip(j["dates"], win, strict=True):
        ok = vals[np.isfinite(vals)]
        if len(ok) >= MIN_PIXELS:
            rows.append([date, round(float(ok.mean()), 1), round(float(ok.std()), 1)])
    return rows, radius, len(sel)


def frame_meta(frame: str) -> dict:
    tr = frame.split("_")[0]
    return {"track": int(tr[:-1]), "pass": {"A": "ascending", "D": "descending"}[tr[-1]]}


def reduce_frame(j: dict, lon: float | None = None, lat: float | None = None) -> dict:
    """Series and velocity grid of one COMET file. lon/lat default to the crop centre (COMET centres crops on the volcano)."""
    import numpy as np

    d, mask, coh = _arrays(j)
    ref, ref_ll = ref_series(j, d)
    dref = d - ref[:, None, None]
    lon = lon if lon is not None else (j["x"][0] + j["x"][-1]) / 2
    lat = lat if lat is not None else (j["y"][0] + j["y"][-1]) / 2
    rows, radius, npx = summit_series(j, d, mask, ref, lon, lat)
    v = velocity(dref, years_since(j["dates"]))
    v[~mask | (coh < COH_FLOOR)] = np.nan
    nx, ny = len(j["x"]), len(j["y"])
    dx, dy = (j["x"][-1] - j["x"][0]) / (nx - 1), (j["y"][-1] - j["y"][0]) / (ny - 1)
    bounds = [j["x"][0] - dx / 2, j["y"][0] - dy / 2, j["x"][-1] + dx / 2, j["y"][-1] + dy / 2]
    return {"rows": rows, "summitRadiusKm": radius, "summitPixels": npx, "velocity": v, "bounds": [round(b, 5) for b in bounds],
            "reference": [round(ref_ll[0], 4), round(ref_ll[1], 4)], "start": j["dates"][0], "end": j["dates"][-1], "dates": len(j["dates"]),
            "built": j["timestamp"][:10], "validPixels": int(np.isfinite(v).sum())}


# ---------------------------------------------------------------- GeoTIFF (no GDAL: one small tiled Int16 file)

def geotiff_bytes(grid, bounds: list[float], tile: int = 128) -> bytes:
    """Int16 GeoTIFF, EPSG:4326, tiled (IFD first, then tiles), Adobe deflate with horizontal predictor.

    `grid` is north-up (row 0 = northern edge), int16, NODATA where empty. bounds = [w, s, e, n] of the pixel edges.
    """
    import numpy as np

    g = np.asarray(grid, dtype="<i2")
    h, w = g.shape
    tx, ty = -(-w // tile), -(-h // tile)
    tiles = []
    for r in range(ty):
        for c in range(tx):
            t = np.full((tile, tile), NODATA, dtype="<i2")
            blk = g[r * tile:(r + 1) * tile, c * tile:(c + 1) * tile]
            t[: blk.shape[0], : blk.shape[1]] = blk
            u = t.view("<u2")
            pred = u.copy()
            pred[:, 1:] = u[:, 1:] - u[:, :-1]  # predictor 2, wraps modulo 2^16
            tiles.append(zlib.compress(pred.astype("<u2").tobytes(), 9))
    sx, sy = (bounds[2] - bounds[0]) / w, (bounds[3] - bounds[1]) / h
    nodata = f"{NODATA}\0".encode()
    geokeys = [1, 1, 0, 3, 1024, 0, 1, 2, 1025, 0, 1, 1, 2048, 0, 1, 4326]
    n = len(tiles)
    # (tag, type, count, value(s)); types: 2 ASCII, 3 SHORT, 4 LONG, 12 DOUBLE
    entries = [(256, 4, 1, [w]), (257, 4, 1, [h]), (258, 3, 1, [16]), (259, 3, 1, [8]), (262, 3, 1, [1]), (277, 3, 1, [1]),
               (284, 3, 1, [1]), (317, 3, 1, [2]), (322, 3, 1, [tile]), (323, 3, 1, [tile]), (324, 4, n, None), (325, 4, n, [len(t) for t in tiles]),
               (339, 3, 1, [2]), (33550, 12, 3, [sx, sy, 0.0]), (33922, 12, 6, [0.0, 0.0, 0.0, bounds[0], bounds[3], 0.0]),
               (34735, 3, len(geokeys), geokeys), (42113, 2, len(nodata), nodata)]
    fmt = {2: "s", 3: "H", 4: "I", 12: "d"}
    size = {2: 1, 3: 2, 4: 4, 12: 8}
    ifd_len = 2 + 12 * len(entries) + 4
    extra_at = 8 + ifd_len
    extra = b""
    placed = {}
    for tag, typ, cnt, _val in entries:
        if cnt * size[typ] > 4:
            placed[tag] = extra_at + len(extra)
            extra += b"\0" * (cnt * size[typ] + (cnt * size[typ]) % 2)
    data_at = extra_at + len(extra)
    offsets, pos = [], data_at
    for t in tiles:
        offsets.append(pos)
        pos += len(t)
    extra = bytearray(extra)
    ifd = struct.pack("<H", len(entries))
    for tag, typ, cnt, val in entries:
        val = offsets if tag == 324 else val
        payload = val if typ == 2 else struct.pack(f"<{cnt}{fmt[typ]}", *val)
        if tag in placed:
            o = placed[tag] - extra_at
            extra[o:o + len(payload)] = payload
            ifd += struct.pack("<HHII", tag, typ, cnt, placed[tag])
        else:
            ifd += struct.pack("<HHI", tag, typ, cnt) + payload.ljust(4, b"\0")
    ifd += struct.pack("<I", 0)
    return b"II*\0" + struct.pack("<I", 8) + ifd + bytes(extra) + b"".join(tiles)


def velocity_tif(v):
    """North-up Int16 grid (mm/yr x 10) of a velocity array whose row 0 is the southern edge."""
    import numpy as np

    g = np.where(np.isfinite(v), np.clip(np.round(v * SCALE), -32767, 32767), NODATA).astype("<i2")[::-1]
    return g


# ---------------------------------------------------------------- read models

def frame_id(vid: str, frame: str) -> str:
    return f"{vid}-{frame}"


def years_text(start: str, end: str) -> str:
    return start[:4] if start[:4] == end[:4] else f"{start[:4]}–{end[:4]}"


def attribution(start: str, end: str) -> str:
    return (f"COMET LiCSBAS (processed by COMET, University of Leeds; not by Plumes); LiCSAR contains modified Copernicus Sentinel data "
            f"{years_text(start, end)}. CC BY-NC 4.0 ({LICENCE_URL})")


def lt(en: str, ja: str) -> dict:
    return {"en": en, "ja": ja}


def build(v_dir: Path, vols: list[dict], raw_dir: Path = OUT) -> tuple[dict[str, dict], dict | None]:
    """Series per volcano (events) and the `deformation-velocity` layer entry; writes v_dir/layers/deformation/*.tif.

    Nothing is produced when no raw file exists (the layer is then simply absent from layers.json).
    """
    import numpy as np

    listing = raw_dir / "frames.json"
    if not listing.exists():
        return {}, None
    coords = {v["id"]: (v["lon"], v["lat"]) for v in vols}
    series: dict[str, dict] = {}
    frames, grids = [], []
    for rec in json.loads(listing.read_text())["frames"]:
        p = raw_dir / f"{rec['cometName']}_{rec['frame']}.json"
        if not p.exists() or rec["volcano"] not in coords:
            continue
        j = json.loads(p.read_text())
        if check_raw(j):
            continue
        red = reduce_frame(j, *coords[rec["volcano"]])
        meta = frame_meta(rec["frame"])
        fid = frame_id(rec["volcano"], rec["frame"])
        if red["rows"]:
            series.setdefault(rec["volcano"], {})[f"los_comet_{rec['frame']}"] = {
                "source": [SOURCE_ID],
                "label": lt(f"Ground motion along the satellite's line of sight, Sentinel-1 track {meta['track']} {meta['pass']} (COMET LiCSBAS)",
                            f"衛星視線方向の地表変位(Sentinel-1 トラック{meta['track']}・{'南行' if meta['pass'] == 'descending' else '北行'}軌道、COMET LiCSBAS)"),
                "cols": ["date", "los_mm", "los_std_mm"], "units": {"los_mm": "mm", "los_std_mm": "mm"}, "start": red["start"], "rows": red["rows"],
                "note": lt(f"Summit area (pixels within {red['summitRadiusKm']:g} km) minus COMET's reference area, relative to the first date. "
                           "Positive = toward the satellite, negative = away; line-of-sight motion mixes vertical and east-west movement, so it is "
                           "not uplift or subsidence by itself. los_std_mm is the spread of the summit pixels, not a formal error. "
                           f"Processed by COMET, not by Plumes. {attribution(red['start'], red['end'])}",
                           f"山頂付近({red['summitRadiusKm']:g} km以内の画素)からCOMETの参照域を差し引いた値で、初回観測日を基準とする。"
                           "正は衛星に近づく向き、負は遠ざかる向き。視線方向の変位は上下と東西の動きを含むため、それだけで隆起や沈降とは言えない。"
                           "los_std_mm は山頂付近の画素のばらつきで、正式な誤差ではない。解析はCOMETによる(Plumesではない)。"
                           f"{attribution(red['start'], red['end'])}")}
        if red["validPixels"]:
            dst = v_dir / "layers" / "deformation" / f"{fid}.tif"
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(geotiff_bytes(velocity_tif(red["velocity"]), red["bounds"]))
            grids.append(red["velocity"][np.isfinite(red["velocity"])])
            frames.append({"id": fid, "volcanoId": rec["volcano"], "track": meta["track"], "pass": meta["pass"], "bounds": red["bounds"],
                           "reference": red["reference"], "start": red["start"], "end": red["end"], "dates": red["dates"]})
    if not frames:
        return series, None
    p98 = float(np.percentile(np.abs(np.concatenate(grids)), 98))
    dom = max(DOMAIN_STEP, int(math.ceil(p98 / DOMAIN_STEP) * DOMAIN_STEP))
    start, end = min(f["start"] for f in frames), max(f["end"] for f in frames)
    layer = {"id": "deformation-velocity", "title": lt("Ground motion, line of sight (COMET LiCSBAS)", "地表変位・衛星視線方向(COMET LiCSBAS)"),
             "format": "cog", "url": "layers/deformation/{frame}.tif", "time": {"step": "none", "start": start, "end": end}, "minzoom": 7,
             "bounds": [round(min(f["bounds"][0] for f in frames), 3), round(min(f["bounds"][1] for f in frames), 3),
                        round(max(f["bounds"][2] for f in frames), 3), round(max(f["bounds"][3] for f in frames), 3)],
             "legend": {"unit": "mm/yr", "stops": [[-dom, f"≤ −{dom}"], [0, "0"], [dom, f"≥ {dom}"]]},
             "properties": {"value": f"mean line-of-sight velocity, mm/yr x {SCALE} (Int16; nodata {NODATA}); positive = toward the satellite"},
             "sources": [SOURCE_ID], "attribution": attribution(start, end), "frames": sorted(frames, key=lambda f: f["id"]),
             "note": lt("Mean ground velocity along the satellite's line of sight over each frame's whole span, not a hazard map. Ascending and "
                        "descending frames see the same ground differently; neither is uplift or subsidence by itself. Grey = no measurable motion. "
                        "Processed by COMET, not by Plumes.",
                        "各フレームの全期間における衛星視線方向の平均変位速度で、ハザードマップではない。北行と南行の軌道では同じ地表の見え方が異なり、"
                        "どちらもそれだけで隆起や沈降とは言えない。灰色は測定できる動きがないことを示す。解析はCOMETによる(Plumesではない)。")}
    return series, layer


# ---------------------------------------------------------------- CLI

def reduce_cli(only: list[str] | None, out: Path) -> dict:
    """Canary: reduce the downloaded frames into `out` (a scratch version folder), print what a build would publish."""
    vols = []
    listing = json.loads((OUT / "frames.json").read_text())["frames"]
    for rec in listing:
        if (not only or rec["volcano"] in only) and raw_path(rec).exists():
            j = json.loads(raw_path(rec).read_text())
            vols.append({"id": rec["volcano"], "lon": (j["x"][0] + j["x"][-1]) / 2, "lat": (j["y"][0] + j["y"][-1]) / 2})
    vols = list({v["id"]: v for v in vols}.values())
    series, layer = build(out, vols)
    (out / "deformation-canary.json").write_text(json.dumps({"series": series, "layer": layer}, ensure_ascii=False, indent=1))
    files = sorted((out / "layers" / "deformation").glob("*.tif"))
    return {"volcanoes": sorted(series), "series": {v: {k: len(s["rows"]) for k, s in d.items()} for v, d in series.items()},
            "frames": [f["id"] for f in (layer or {}).get("frames", [])], "legend": (layer or {}).get("legend"),
            "tif_bytes": {f.name: f.stat().st_size for f in files}}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["fetch", "reduce"])
    ap.add_argument("--only", action="append", help="Plumes volcano id (repeatable)")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    if a.cmd == "fetch":
        print(json.dumps(fetch(a.only, a.limit), indent=1))
    else:
        print(json.dumps(reduce_cli(a.only, a.out or (RAW.parent / "build" / "comet-canary")), indent=1))
