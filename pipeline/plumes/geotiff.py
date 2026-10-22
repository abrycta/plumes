"""A small, dependency-free writer (and reader, for tests) of int16 GeoTIFFs on a regular EPSG:4326 grid.

Used for the national monthly SO2 map (LAYERS-PLAN §3, `so2-monthly`): about 120 x 180 pixels and two bands, small
enough that the web app fetches a whole file in one GET and decodes it with `geotiff` (no tile pyramid, no Range
requests). Layout: little-endian, one tile covering the image, chunky samples, Adobe deflate with horizontal
differencing (predictor 2), the IFD before the image data (a valid single-tile COG layout), GDAL_NODATA set.
"""

from __future__ import annotations

import struct
import zlib
from array import array

NODATA = -32768

# TIFF field types
_SHORT, _ASCII, _LONG, _DOUBLE = 3, 2, 4, 12
_SIZE = {_SHORT: 2, _ASCII: 1, _LONG: 4, _DOUBLE: 8}
_FMT = {_SHORT: "H", _LONG: "I", _DOUBLE: "d"}


def _ceil16(n: int) -> int:
    return (n + 15) // 16 * 16


def _predict(values: array, width: int, height: int, samples: int) -> array:
    """Horizontal differencing per row and sample (TIFF predictor 2), wrapping at 16 bits."""
    out = array("h", values)
    row = width * samples
    for y in range(height):
        base = y * row
        for i in range(row - 1, samples - 1, -1):
            d = values[base + i] - values[base + i - samples]
            out[base + i] = (d + 32768) % 65536 - 32768
    return out


def write_int16(bands: list[list[list[int]]], bounds: tuple[float, float, float, float], band_names: list[str] | None = None) -> bytes:
    """bands[b][row][col] (row 0 = north) as an int16 GeoTIFF covering bounds (west, south, east, north).

    None or NODATA is nodata; other values are clamped to -32767..32767."""
    nb = len(bands)
    height, width = len(bands[0]), len(bands[0][0])
    if any(len(b) != height or any(len(r) != width for r in b) for b in bands):
        raise ValueError("every band must have the same shape")
    w, s, e, n = bounds
    tw, th = _ceil16(width), _ceil16(height)
    tile = array("h", [NODATA]) * (tw * th * nb)
    for y in range(height):
        for x in range(width):
            for b in range(nb):
                v = bands[b][y][x]
                tile[(y * tw + x) * nb + b] = NODATA if v is None or v == NODATA else max(-32767, min(32767, int(v)))
    raw = _predict(tile, tw, th, nb)
    if struct.pack("=h", 1) != struct.pack("<h", 1):
        raw.byteswap()
    data = zlib.compress(raw.tobytes(), 9)

    geokeys = [1, 1, 0, 3, 1024, 0, 1, 2, 1025, 0, 1, 1, 2048, 0, 1, 4326]  # geographic, PixelIsArea, WGS 84
    nodata = f"{NODATA}\0".encode()
    desc = ("\n".join(band_names) + "\0").encode() if band_names else None
    tags: list[tuple[int, int, list | bytes]] = [
        (256, _SHORT, [width]), (257, _SHORT, [height]), (258, _SHORT, [16] * nb), (259, _SHORT, [8]), (262, _SHORT, [1]),
        (277, _SHORT, [nb]), (284, _SHORT, [1]), (317, _SHORT, [2]), (322, _SHORT, [tw]), (323, _SHORT, [th]),
        (324, _LONG, [0]), (325, _LONG, [len(data)]), (339, _SHORT, [2] * nb),
        (33550, _DOUBLE, [(e - w) / width, (n - s) / height, 0.0]), (33922, _DOUBLE, [0.0, 0.0, 0.0, w, n, 0.0]),
        (34735, _SHORT, geokeys), (42113, _ASCII, nodata),
    ]
    if nb > 1:
        tags.append((338, _SHORT, [0] * (nb - 1)))
    if desc:
        tags.append((270, _ASCII, desc))
    tags.sort(key=lambda t: t[0])

    ifd_size = 2 + 12 * len(tags) + 4
    extra_at = 8 + ifd_size

    def payload(typ, vals) -> bytes:
        return vals if typ == _ASCII else struct.pack("<" + _FMT[typ] * len(vals), *vals)

    extra = b""
    for typ_vals in tags:
        p = payload(typ_vals[1], typ_vals[2])
        if len(p) > 4:
            extra += p + (b"\0" if len(p) % 2 else b"")
    data_at = extra_at + len(extra)
    entries, extra, cursor = b"", b"", extra_at
    for tag, typ, vals in tags:
        if tag == 324:
            vals = [data_at]
        p = payload(typ, vals)
        count = len(vals)
        if len(p) <= 4:
            entries += struct.pack("<HHI", tag, typ, count) + p.ljust(4, b"\0")
        else:
            entries += struct.pack("<HHII", tag, typ, count, cursor)
            pad = p + (b"\0" if len(p) % 2 else b"")
            extra += pad
            cursor += len(pad)
    head = b"II" + struct.pack("<HI", 42, 8) + struct.pack("<H", len(tags)) + entries + struct.pack("<I", 0)
    return head + extra + data


def read_int16(buf: bytes) -> dict:
    """Read a file written by write_int16 (tests and checks only): bands, bounds and nodata."""
    if buf[:4] != b"II*\0":
        raise ValueError("not a little-endian TIFF")
    (ifd,) = struct.unpack_from("<I", buf, 4)
    (n,) = struct.unpack_from("<H", buf, ifd)
    tags = {}
    for i in range(n):
        tag, typ, count, val = struct.unpack_from("<HHI4s", buf, ifd + 2 + 12 * i)
        size = _SIZE[typ] * count
        raw = val[:size] if size <= 4 else buf[struct.unpack("<I", val)[0]:][:size]
        tags[tag] = raw.rstrip(b"\0").decode() if typ == _ASCII else list(struct.unpack("<" + _FMT[typ] * count, raw))
    width, height, nb, tw, th = tags[256][0], tags[257][0], tags[277][0], tags[322][0], tags[323][0]
    tile = array("h")
    tile.frombytes(zlib.decompress(buf[tags[324][0]:tags[324][0] + tags[325][0]]))
    if struct.pack("=h", 1) != struct.pack("<h", 1):
        tile.byteswap()
    row = tw * nb
    for y in range(th):
        for i in range(nb, row):
            tile[y * row + i] = (tile[y * row + i] + tile[y * row + i - nb] + 32768) % 65536 - 32768
    sx, sy = tags[33550][0], tags[33550][1]
    w, nn = tags[33922][3], tags[33922][4]
    bands = [[[tile[(y * tw + x) * nb + b] for x in range(width)] for y in range(height)] for b in range(nb)]
    return {"bands": bands, "bounds": (w, nn - sy * height, w + sx * width, nn), "nodata": int(tags[42113]),
            "names": tags.get(270, "").split("\n") if 270 in tags else None}
