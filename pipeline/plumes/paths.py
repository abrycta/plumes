"""Shared paths. data/ is gitignored: raw crawl records, fetched files, intermediate tables and built versions."""

import os
import pathlib
import subprocess

PIPELINE = pathlib.Path(__file__).resolve().parents[1]
REPO = PIPELINE.parent
DATA = PIPELINE / "data"
RAW = DATA / "raw"
TABLES = DATA / "tables"
BUILD = DATA / "build"
REGISTRY = PIPELINE / "sources.yaml"
CROSSWALK = PIPELINE / "plumes" / "data" / "volcanoes.csv"


def _ee_ledger() -> pathlib.Path:
    """The one Earth Engine ledger for every checkout of this clone (DECISIONS B4): $PLUMES_EE_LEDGER if set, else
    the main checkout's data/state/ee-usage.json, found through git's common dir so every worktree writes the same
    file, else (no git, e.g. an unpacked copy) this checkout's. In CI the main checkout is this checkout."""
    if env := os.environ.get("PLUMES_EE_LEDGER"):
        return pathlib.Path(env)
    try:
        common = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--path-format=absolute", "--git-common-dir"],
                                capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        common = ""
    if common and pathlib.Path(common).name == ".git":
        return pathlib.Path(common).parent / "pipeline" / "data" / "state" / "ee-usage.json"
    return DATA / "state" / "ee-usage.json"


EE_LEDGER = _ee_ledger()
