"""Publish a built data version: GitHub Pages (primary, the gh-pages branch under data/) and the public files-only
Hugging Face mirror permission-alluring/plumes (fallback; DECISIONS Q12, Q19). The version folder goes up first and
latest.json last, so readers never see a pointer to a missing version. The previous version is kept for rollback;
older ones leave Pages (DATA-PLAN §5 retention) but stay on the mirror's history.

    uv run python -m plumes.publish --version 1 [--pages] [--hf]
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import tempfile

from plumes.paths import BUILD, DATA, EE_LEDGER, REPO

PAGES_DIR = DATA / "publish" / "gh-pages"
HF_REPO = "permission-alluring/plumes"
AUTHOR = ["-c", "user.name=Kurt", "-c", "user.email=73582015+abrycta@users.noreply.github.com"]
HF_README = """---
viewer: false
---
# Plumes: hosting mirror

This repository is the **hosting fallback** for [Plumes](https://github.com/abrycta/plumes), a retrospective record of
Philippine volcanoes. It holds the same files the app reads from GitHub Pages. **It is not a dataset release**: no
licence is granted here beyond each source's own terms, and nothing here is a hazard assessment or a current status.

Every file names its sources, attribution and licence in its `provenance` block; DOST-PHIVOLCS figures are shown only
with a link to the bulletin they come from. Layout: `latest.json` points to the current `v<N>/` folder.
"""


def auth() -> list[str]:
    """`git -c` arguments that authenticate github.com HTTPS with GITHUB_TOKEN (set by the Data workflow). The gh-pages
    clone is a repository of its own, so the checkout's credentials never reach it (audit P1); the header is passed per
    command and never written to a .git/config."""
    tok = os.environ.get("GITHUB_TOKEN")
    if not tok:
        return []
    basic = base64.b64encode(f"x-access-token:{tok}".encode()).decode()
    return ["-c", f"http.https://github.com/.extraheader=AUTHORIZATION: basic {basic}"]


_PAGES = object()  # git()'s default cwd: PAGES_DIR as it is at call time


def git(*args, cwd=_PAGES, check=True):
    return subprocess.run(["git", *auth(), *args], cwd=PAGES_DIR if cwd is _PAGES else cwd, check=check, capture_output=True, text=True)


def origin() -> str:
    return subprocess.run(["git", "remote", "get-url", "origin"], cwd=REPO, capture_output=True, text=True, check=True).stdout.strip()


def remote_versions(remote: str) -> list[int]:
    """The version numbers under data/ on the remote gh-pages branch; [] when the branch does not exist yet. Raises when
    the branch cannot be read, so a new version is never numbered blind (audit P3)."""
    r = git("ls-remote", "--exit-code", "--heads", remote, "gh-pages", cwd=None, check=False)
    if r.returncode == 2:
        return []
    if r.returncode != 0:
        raise RuntimeError(f"gh-pages on {remote} is not readable: {r.stderr.strip()[:200]}")
    with tempfile.TemporaryDirectory() as td:
        git("clone", "-q", "--depth", "1", "--filter=blob:none", "--no-checkout", "--branch", "gh-pages", remote, td, cwd=None)
        names = git("ls-tree", "--name-only", "HEAD", "data/", cwd=td).stdout.split()
    return sorted(int(m[1]) for n in names if (m := re.fullmatch(r"data/v(\d+)", n)))


def pages(version: int) -> dict:
    site = BUILD / "site"
    remote = origin()
    if not (PAGES_DIR / ".git").exists():
        PAGES_DIR.mkdir(parents=True, exist_ok=True)
        if git("ls-remote", "--exit-code", "--heads", remote, "gh-pages", cwd=None, check=False).returncode == 0:
            git("clone", "--depth", "1", "--branch", "gh-pages", remote, str(PAGES_DIR), cwd=None)
        else:
            git("init", "-q", "-b", "gh-pages")
            git("remote", "add", "origin", remote)
            (PAGES_DIR / ".nojekyll").write_text("")
    else:
        git("pull", "-q", "--ff-only", "origin", "gh-pages", check=False)
    data = PAGES_DIR / "data"
    data.mkdir(exist_ok=True)
    held = {int(m[1]): d for d in data.glob("v*") if d.is_dir() and (m := re.fullmatch(r"v(\d+)", d.name))}
    if max(held, default=0) > version:  # never move latest.json backwards or prune newer versions (audit P3)
        raise SystemExit(f"gh-pages already holds v{max(held)}, newer than v{version}: nothing is published")
    dst = data / f"v{version}"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(site / f"v{version}", dst)
    for n, old in held.items():  # keep this version and the previous one (rollback)
        if n < version - 1:
            shutil.rmtree(old)
    shutil.copy(site / "latest.json", data / "latest.json")
    if EE_LEDGER.exists():
        shutil.copy(EE_LEDGER, data / "ee-usage.json")
    (PAGES_DIR / "index.html").write_text('<!doctype html><meta charset="utf-8"><title>Plumes data</title>'
                                          '<p>Data files for <a href="https://github.com/abrycta/plumes">Plumes</a>. Start at <a href="data/latest.json">data/latest.json</a>.</p>\n')
    git("add", "-A")
    if git("diff", "--cached", "--quiet", check=False).returncode == 0:
        return {"pages": "unchanged"}
    git(*AUTHOR, "commit", "-q", "-m", f"Data version v{version}")
    git("push", "-q", "origin", "gh-pages")
    return {"pages": "pushed", "version": f"v{version}"}


def hf(version: int) -> dict:
    from huggingface_hub import HfApi

    api = HfApi(token=os.environ["HF_TOKEN"])
    api.create_repo(HF_REPO, repo_type="dataset", private=False, exist_ok=True)
    site = BUILD / "site"
    api.upload_file(path_or_fileobj=HF_README.encode(), path_in_repo="README.md", repo_id=HF_REPO, repo_type="dataset", commit_message="Mirror README")
    api.upload_folder(folder_path=str(site / f"v{version}"), path_in_repo=f"v{version}", repo_id=HF_REPO, repo_type="dataset",
                      commit_message=f"Data version v{version}")
    api.upload_file(path_or_fileobj=str(site / "latest.json"), path_in_repo="latest.json", repo_id=HF_REPO, repo_type="dataset",
                    commit_message=f"Point latest to v{version}")
    return {"hf": f"https://huggingface.co/datasets/{HF_REPO}"}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", type=int, required=True)
    ap.add_argument("--pages", action="store_true")
    ap.add_argument("--hf", action="store_true")
    a = ap.parse_args()
    if not (BUILD / "site" / "latest.json").exists() or json.loads((BUILD / "site" / "latest.json").read_text())["current"] != f"v{a.version}":
        raise SystemExit(f"latest.json does not point to v{a.version}: the checks did not pass, nothing is published")
    out = {}
    if a.pages:
        out |= pages(a.version)
    if a.hf:
        out |= hf(a.version)
    print(json.dumps(out))
