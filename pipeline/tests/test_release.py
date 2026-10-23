"""Storage option C: a published version packs into a verifiable, reproducible release asset."""

import json

import pytest

release = pytest.importorskip("plumes.release")  # needs zstandard (sources group)


def site(tmp_path):
    v = tmp_path / "v7"
    (v / "layers").mkdir(parents=True)
    (v / "manifest.json").write_text(json.dumps({"dataVersion": "v7"}))
    (v / "layers" / "a.pmtiles").write_bytes(b"PMTiles\x03" + bytes(200))
    return v


def test_pack_is_reproducible_and_verifies(tmp_path):
    v = site(tmp_path)
    a = release.pack(v, 7, tmp_path / "a")
    b = release.pack(v, 7, tmp_path / "b")
    assert a["compressed_sha256"] == b["compressed_sha256"]
    assert [m["path"] for m in a["members"]] == ["v7/layers/a.pmtiles", "v7/manifest.json"]
    assert release.check(tmp_path / "a" / "v7.tar.zst", a, a) is None
    assert (tmp_path / "a" / "v7.tar.zst.sha256").read_text().split() == [a["compressed_sha256"], "v7.tar.zst"]


def test_a_changed_or_foreign_asset_fails_the_check(tmp_path):
    v = site(tmp_path)
    a = release.pack(v, 7, tmp_path / "a")
    blob = tmp_path / "a" / "v7.tar.zst"
    blob.write_bytes(blob.read_bytes()[:-1] + b"\0")
    assert release.check(blob, a, a)
    (v / "manifest.json").write_text(json.dumps({"dataVersion": "v7", "x": 1}))
    b = release.pack(v, 7, tmp_path / "b")
    assert release.check(tmp_path / "b" / "v7.tar.zst", b, a) == "the release does not hold this build's files"


def test_trial_tags_never_look_like_published_versions():
    assert release.tag_for(7) == "data-v7"
    assert release.tag_for(7, "run1") == "trial-data-v7-run1"
