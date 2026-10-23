"""Storage option A1: published files carry no local path, and unchanged tiles keep identical bytes across builds."""

import gzip
import hashlib
import json
import shutil
import struct

import pytest

from plumes import leaks, readmodels


def fake_pmtiles(meta: dict) -> bytes:
    body = gzip.compress(json.dumps(meta).encode())
    header = bytearray(127)
    header[:8] = b"PMTiles\x03"
    struct.pack_into("<QQQQ", header, 8, 127, 0, 127, len(body))
    header[97] = 2  # gzip internal compression
    return bytes(header) + body


def test_a_local_path_in_pmtiles_metadata_is_found(tmp_path):
    (tmp_path / "layers").mkdir()
    (tmp_path / "layers" / "bad.pmtiles").write_bytes(fake_pmtiles({"name": "/private/tmp/x/build/site/v6/layers/bad.pmtiles"}))
    (tmp_path / "layers" / "ok.pmtiles").write_bytes(fake_pmtiles({"name": "Plumes earthquakes", "generator_options": "tippecanoe -o usgs.pmtiles"}))
    assert list(leaks.scan(tmp_path)) == ["layers/bad.pmtiles"]


@pytest.mark.parametrize("text", ["/Users/someone/plumes/x.csv", "/home/runner/work/plumes/a", "C:\\Users\\me\\x", "/tmp/claude-501/x"])
def test_a_local_path_in_a_text_file_is_found(tmp_path, text):
    (tmp_path / "a.json").write_text(json.dumps({"source": text}))
    assert leaks.scan(tmp_path)


def test_urls_and_tile_paths_are_not_paths(tmp_path):
    (tmp_path / "a.json").write_text(json.dumps({"url": "https://krtmtthw.dev/plumes/data/v6/layers/thermal/{year}.pmtiles",
                                                 "u": "layers/earthquakes-usgs.pmtiles", "d": "2020/01/12"}))
    assert leaks.scan(tmp_path) == {}


@pytest.mark.skipif(not shutil.which("tippecanoe"), reason="tippecanoe not installed (the Data workflow installs it)")
def test_two_builds_give_identical_tiles_without_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(readmodels, "BUILD", tmp_path / "build")
    usgs = [{"t": "2020-01-12T06:00:00Z", "lon": 120.99, "lat": 14.0, "mag": 4.1, "depth": 5, "id": "a"},
            {"t": "2021-03-01T00:00:00Z", "lon": 121.5, "lat": 13.2, "mag": 5.0, "depth": 30, "id": "b"}]
    digests = []
    for run in ("v1", "v2"):  # different output folders, as two versions are
        readmodels.quake_layer(tmp_path / run, usgs)
        f = tmp_path / run / "layers" / "earthquakes-usgs.pmtiles"
        digests.append(hashlib.sha256(f.read_bytes()).hexdigest())
        assert leaks.scan(tmp_path / run) == {}
        assert b"Plumes earthquakes" in leaks.pmtiles_metadata(f.read_bytes())
    assert digests[0] == digests[1]
