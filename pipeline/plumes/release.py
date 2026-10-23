"""Published versions as release assets in the private archive (storage option C, decision S2): after each publish the
version folder is saved as release `data-v<N>` in abrycta/plumes-archive, then downloaded again and checked, so a
version stays recoverable without the gh-pages history or the Hugging Face mirror. Nothing is pruned here.

Assets of `data-v<N>`:
- `v<N>.tar.zst`: the folder exactly as published (`v<N>/…`; fixed order, times and owners, so equal files give an
  equal tar);
- `v<N>.tar.zst.sha256`: its hash, in `sha256sum -c` format;
- `manifest.json`: the hashes of the .tar.zst and the tar, and every file's path, size and sha256 (the same layout as
  the input bundles, so `state._members_ok` checks both).

    uv run python -m plumes.release save --version 7 [--trial run123]   # pack, upload, download again, verify
    uv run python -m plumes.release restore --version 7 --to DIR         # download, verify, unpack into DIR/v7/

`--trial` saves under `trial-data-v<N>-<label>` as a pre-release and deletes it after the check: a trial Data run proves
the step end to end without leaving a backup of a version that was never published.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import pathlib
import subprocess
import sys
import tarfile
import tempfile
import time

import zstandard

from plumes import health
from plumes.adopt import REPO
from plumes.paths import BUILD
from plumes.state import _members_ok


def tag_for(version: int, trial: str | None = None) -> str:
    return f"trial-data-v{version}-{trial}" if trial else f"data-v{version}"


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def pack(src: pathlib.Path, version: int, out: pathlib.Path) -> dict:
    """`out/v<N>.tar.zst`, its .sha256 and manifest.json from the version folder `src`; returns the manifest."""
    files = sorted(p for p in src.rglob("*") if p.is_file())
    if not files:
        raise SystemExit(f"{src} holds no files: nothing to save")
    buf = io.BytesIO()
    members = []
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.PAX_FORMAT) as tar:
        for p in files:
            data = p.read_bytes()
            name = f"v{version}/{p.relative_to(src).as_posix()}"
            info = tarfile.TarInfo(name)
            info.size, info.mtime, info.mode, info.uid, info.gid, info.uname, info.gname = len(data), 0, 0o644, 0, 0, "", ""
            tar.addfile(info, io.BytesIO(data))
            members.append({"path": name, "size": len(data), "sha256": sha256(data)})
    raw = buf.getvalue()
    blob = zstandard.ZstdCompressor(level=19).compress(raw)
    out.mkdir(parents=True, exist_ok=True)
    name = f"v{version}.tar.zst"
    (out / name).write_bytes(blob)
    (out / f"{name}.sha256").write_text(f"{sha256(blob)}  {name}\n")
    man = {"kind": "published-version", "version": f"v{version}", "asset": name, "files": len(members),
           "bytes": sum(m["size"] for m in members), "compressed_bytes": len(blob),
           "compressed_sha256": sha256(blob), "raw_sha256": sha256(raw), "members": members}
    (out / "manifest.json").write_text(json.dumps(man, indent=1) + "\n")
    return man


def gh(*args, check=True) -> subprocess.CompletedProcess:
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=check)


def download(tag: str, version: int, dest: pathlib.Path, tries: int = 3) -> tuple[pathlib.Path, dict]:
    """The release's .tar.zst and manifest.json, downloaded into `dest`."""
    err = ""
    for i in range(tries):
        r = gh("release", "download", tag, "-R", REPO, "-p", f"v{version}.tar.zst", "-p", "manifest.json", "-D", str(dest), "--clobber",
               check=False)
        asset, man_p = dest / f"v{version}.tar.zst", dest / "manifest.json"
        if r.returncode == 0 and asset.exists() and man_p.exists():
            return asset, json.loads(man_p.read_text())
        err = (r.stderr or "missing asset").strip()[:200]
        time.sleep(5 * (i + 1))
    raise SystemExit(f"::error title=release download failed::{tag}: {err}")


def check(asset: pathlib.Path, man: dict, want: dict) -> str | None:
    """None when the downloaded asset matches its manifest and the manifest matches `want` (the local pack)."""
    if bad := _members_ok(asset, man):
        return bad
    if man.get("compressed_sha256") != want["compressed_sha256"] or man.get("members") != want["members"]:
        return "the release does not hold this build's files"
    return None


def save(version: int, trial: str | None = None) -> dict:
    src = BUILD / "site" / f"v{version}"
    tag = tag_for(version, trial)
    with tempfile.TemporaryDirectory() as td:
        out, back = pathlib.Path(td) / "out", pathlib.Path(td) / "back"
        man = pack(src, version, out)
        assets = [str(out / f"v{version}.tar.zst"), str(out / f"v{version}.tar.zst.sha256"), str(out / "manifest.json")]
        if gh("release", "view", tag, "-R", REPO, "--json", "tagName", check=False).returncode == 0:
            # a re-run of the same version: replace the assets, so the backup matches what was published last
            gh("release", "upload", tag, "-R", REPO, "--clobber", *assets)
        else:
            notes = (f"Published data version v{version}: {man['files']} files, {man['bytes']} bytes "
                     f"({man['compressed_bytes']} as .tar.zst). Restore: `uv run python -m plumes.release restore --version {version} --to DIR`.")
            gh("release", "create", tag, "-R", REPO, "--title", f"{'Trial: ' if trial else ''}Published data v{version}", "--notes", notes,
               *(["--prerelease"] if trial else []), *assets)
        back.mkdir()
        asset, got = download(tag, version, back)
        bad = check(asset, got, man)
        url = f"https://github.com/{REPO}/releases/tag/{tag}"
        if trial:
            gh("release", "delete", tag, "-R", REPO, "--yes", "--cleanup-tag", check=False)
    res = {"tag": tag, "url": url, "files": man["files"], "bytes": man["bytes"], "compressed_bytes": man["compressed_bytes"],
           "sha256": man["compressed_sha256"], "verified": bad is None, **({"deleted": True} if trial else {})}
    key = f"release v{version}" if not trial else None
    if bad:
        if key:
            health.report(key, "not verified", f"`{tag}` in {REPO} does not verify after upload: {bad}")
        raise SystemExit(f"::error title=release not verified::{tag}: {bad}")
    if key:
        health.resolve(key, f"`{tag}` uploaded and verified.")
    return res


def restore(version: int, to: pathlib.Path) -> dict:
    """Download `data-v<N>`, check every hash, unpack into `to/v<N>/`."""
    tag = tag_for(version)
    with tempfile.TemporaryDirectory() as td:
        asset, man = download(tag, version, pathlib.Path(td))
        if bad := _members_ok(asset, man):
            raise SystemExit(f"::error title=release not verified::{tag}: {bad}")
        raw = zstandard.ZstdDecompressor().stream_reader(open(asset, "rb")).read()
        to.mkdir(parents=True, exist_ok=True)
        with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
            tar.extractall(to, filter="data")
    return {"tag": tag, "restored": str(to / f"v{version}"), "files": man["files"], "sha256": man["compressed_sha256"]}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["save", "restore"])
    ap.add_argument("--version", type=int, required=True)
    ap.add_argument("--trial", help="save under a trial tag and delete it after the check")
    ap.add_argument("--to", type=pathlib.Path, help="restore: the folder that receives v<N>/")
    a = ap.parse_args()
    if a.cmd == "save":
        print(json.dumps(save(a.version, a.trial)))
    else:
        if not a.to:
            sys.exit("restore needs --to DIR")
        print(json.dumps(restore(a.version, a.to)))
