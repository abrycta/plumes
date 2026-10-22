"""COMET reduction (plumes.comet): velocity, reference, summit series and the GeoTIFF writer, on a synthetic frame."""

import datetime as dt
import struct
import zlib

import pytest

np = pytest.importorskip("numpy")

from plumes import comet  # noqa: E402


def frame(rate=12.0, ny=8, nx=10, n=24):
    """A frame whose pixels move `rate` mm/yr toward the satellite, except the reference area (col 0-1, row 0-1)."""
    d0 = dt.date(2020, 1, 1)
    dates = [(d0 + dt.timedelta(days=12 * i)).isoformat() for i in range(n)]
    t = np.array([(dt.date.fromisoformat(d) - d0).days / 365.25 for d in dates])
    cube = np.repeat((rate * t)[:, None, None], ny, 1).repeat(nx, 2)
    cube[:, 0:2, 0:2] = 3.0 * t[:, None, None]  # the reference area itself moves 3 mm/yr: everything is relative to it
    data = [[["null" if (i == ny - 1 and k == nx - 1) else round(float(v), 3) for k, v in enumerate(row)] for i, row in enumerate(sl)] for sl in cube]
    mask = [[0 if (i == ny - 1 and k == nx - 1) else 1 for k in range(nx)] for i in range(ny)]
    return {"timestamp": "2026-08-21 11:58:58", "dates": dates, "x": [120.0 + 0.005 * k for k in range(nx)], "y": [14.0 + 0.006 * i for i in range(ny)],
            "data_raw": data, "mask": mask, "coh": [[0.5] * nx for _ in range(ny)], "refarea": [0, 2, 0, 2], "elev": [], "gaps": []}


def test_check_raw_accepts_the_shape_and_rejects_changes():
    j = frame()
    assert comet.check_raw(j) == []
    bad = dict(j, refarea=[1, 2])
    assert comet.check_raw(bad) == ["refarea is not 4 numbers"]
    assert "missing key mask" in comet.check_raw({k: v for k, v in j.items() if k != "mask"})


def test_velocity_is_relative_to_the_reference_and_masked():
    red = comet.reduce_frame(frame())
    v = red["velocity"]
    assert v[4, 4] == pytest.approx(9.0, abs=0.05)  # 12 - 3 mm/yr
    assert v[0, 0] == pytest.approx(0.0, abs=0.05)
    assert np.isnan(v[-1, -1])  # COMET mask 0
    assert red["reference"] == [pytest.approx(120.0025), pytest.approx(14.003)]
    assert red["bounds"][0] == pytest.approx(119.9975) and red["bounds"][3] == pytest.approx(14.045)


def test_coherence_floor_masks_velocity_but_not_the_series():
    j = frame()
    j["coh"] = [[0.1] * 10 for _ in range(8)]
    red = comet.reduce_frame(j)
    assert red["validPixels"] == 0
    assert red["rows"] and red["rows"][-1][1] > 0


def test_summit_series_starts_at_zero_and_grows():
    red = comet.reduce_frame(frame())
    assert red["rows"][0] == ["2020-01-01", 0.0, 0.0]
    last = red["rows"][-1]
    assert last[1] == pytest.approx(9.0 * 276 / 365.25, abs=0.2)


def read_tif(b: bytes):
    assert b[:4] == b"II*\0"
    (ifd,) = struct.unpack_from("<I", b, 4)
    (n,) = struct.unpack_from("<H", b, ifd)
    tags = {}
    for i in range(n):
        tag, typ, cnt, val = struct.unpack_from("<HHII", b, ifd + 2 + 12 * i)
        size = {2: 1, 3: 2, 4: 4, 12: 8}[typ] * cnt
        raw = b[ifd + 2 + 12 * i + 8: ifd + 2 + 12 * i + 12] if size <= 4 else b[val: val + size]
        tags[tag] = raw if typ == 2 else struct.unpack_from(f"<{cnt}{ {3: 'H', 4: 'I', 12: 'd'}[typ]}", raw)
    w, h, tw = tags[256][0], tags[257][0], tags[322][0]
    off, cnt = tags[324][0], tags[325][0]
    u = np.frombuffer(zlib.decompress(b[off: off + cnt]), dtype="<u2").reshape(tw, tw)
    u = np.cumsum(u, axis=1, dtype=np.uint16)  # undo predictor 2
    return tags, u.view("<i2")[:h, :w]


def test_geotiff_round_trip():
    g = np.arange(-50, 50, dtype="<i2").reshape(10, 10)
    g[0, 0] = comet.NODATA
    tags, back = read_tif(comet.geotiff_bytes(g, [120.0, 13.0, 121.0, 14.0]))
    assert (back == g).all()
    assert tags[259] == (8,) and tags[317] == (2,) and tags[339] == (2,)
    assert tags[33922][3:5] == (120.0, 14.0) and tags[33550][:2] == (0.1, 0.1)
    assert tags[42113].rstrip(b"\0") == b"-32768"
    assert 4326 in tags[34735]


def test_velocity_tif_is_north_up_and_scaled():
    v = np.array([[1.25, np.nan], [-2.0, 0.0]])  # row 0 = south
    g = comet.velocity_tif(v)
    assert g.tolist() == [[-20, 0], [12, comet.NODATA]]


def test_frame_meta():
    assert comet.frame_meta("032D_07536_111313") == {"track": 32, "pass": "descending"}
    assert comet.frame_meta("142A_07606_131313") == {"track": 142, "pass": "ascending"}


def test_coherence_floor_is_0_2():
    assert comet.COH_FLOOR == 0.2
    j = frame()
    j["coh"] = [[0.25] * 10 for _ in range(8)]
    assert comet.reduce_frame(j)["validPixels"] == 79  # 80 pixels, one masked by COMET


def test_attribution_names_comet_copernicus_licence_and_changes():
    a = comet.attribution("2014-10-19", "2026-08-12")
    assert "LiCSAR contains modified Copernicus Sentinel data 2014–2026" in a
    assert "CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/)" in a and "Changes made" in a
