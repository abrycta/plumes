"""Shared paths. data/ is gitignored: raw crawl records, fetched files, intermediate tables and built versions."""

import pathlib

PIPELINE = pathlib.Path(__file__).resolve().parents[1]
REPO = PIPELINE.parent
DATA = PIPELINE / "data"
RAW = DATA / "raw"
TABLES = DATA / "tables"
BUILD = DATA / "build"
REGISTRY = PIPELINE / "sources.yaml"
CROSSWALK = PIPELINE / "plumes" / "data" / "volcanoes.csv"
