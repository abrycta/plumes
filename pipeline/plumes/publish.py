"""Publish a built data version: GitHub Pages (primary, the gh-pages branch under data/) and the public files-only
Hugging Face mirror permission-alluring/plumes (fallback; DECISIONS Q12, Q19). The version folder goes up first and
latest.json last, so readers never see a pointer to a missing version. The previous version is kept for rollback;
older ones leave Pages (DATA-PLAN §5 retention) but stay on the mirror's history.

    uv run python -m plumes.publish --version 1 [--pages] [--hf]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess

from plumes.paths import BUILD, DATA, REPO

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


def git(*args, cwd=PAGES_DIR, check=True):
    return subprocess.run(["git", *args], cwd=cwd, check=check, capture_output=True, text=True)


def pages(version: int) -> dict:
    site = BUILD / "site"
    remote = subprocess.run(["git", "remote", "get-url", "origin"], cwd=REPO, capture_output=True, text=True, check=True).stdout.strip()
    if not (PAGES_DIR / ".git").exists():
        PAGES_DIR.mkdir(parents=True, exist_ok=True)
        if subprocess.run(["git", "ls-remote", "--exit-code", "--heads", remote, "gh-pages"], capture_output=True).returncode == 0:
            subprocess.run(["git", "clone", "--depth", "1", "--branch", "gh-pages", remote, str(PAGES_DIR)], check=True, capture_output=True)
        else:
            git("init", "-q", "-b", "gh-pages")
            git("remote", "add", "origin", remote)
            (PAGES_DIR / ".nojekyll").write_text("")
    else:
        git("pull", "-q", "--ff-only", "origin", "gh-pages", check=False)
    data = PAGES_DIR / "data"
    data.mkdir(exist_ok=True)
    dst = data / f"v{version}"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(site / f"v{version}", dst)
    keep = {f"v{version}", f"v{version - 1}"}
    for old in data.glob("v*"):
        if old.is_dir() and old.name not in keep:
            shutil.rmtree(old)
    shutil.copy(site / "latest.json", data / "latest.json")
    usage = DATA / "state" / "ee-usage.json"
    if usage.exists():
        shutil.copy(usage, data / "ee-usage.json")
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
