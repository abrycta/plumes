"""The stories public in the previous data version, which keep their ids in the next one (DECISIONS ST15).

    previous.load("https://krtmtthw.dev/plumes/data/")   # the published version (latest.json), as CI and local builds see it
    previous.load(pathlib.Path("/tmp/v6"))                # or a version folder

Returns {id: {"volcanoId", "onset"}} for every story with a public file (status reviewed, story/<id>.json).
"""

from __future__ import annotations

import json
import pathlib

import httpx

PAGES = "https://krtmtthw.dev/plumes/data/"


def _onset(doc: dict) -> str:
    """The onset step's start; for a hand-built story (steps without a kind), the first step after "before"."""
    steps = doc["steps"]
    return next((s["start"] for s in steps if s.get("kind") == "onset"),
                next((s["start"] for s in steps if (s.get("kind") or s.get("id")) != "before"), doc["span"]["start"]))


def load(src: str | pathlib.Path = PAGES) -> dict[str, dict]:
    if isinstance(src, pathlib.Path):
        get = lambda rel: json.loads((src / rel).read_text())  # noqa: E731
    else:
        latest = httpx.get(src + "latest.json", follow_redirects=True, timeout=30)
        if latest.status_code == 404:
            return {}  # nothing published yet
        latest.raise_for_status()
        base = src + latest.json()["base"]

        def get(rel: str) -> dict:
            r = httpx.get(base + rel, follow_redirects=True, timeout=30)
            r.raise_for_status()
            return r.json()
    try:
        index = get("stories.json")
    except (FileNotFoundError, httpx.HTTPStatusError):
        return {}  # versions made before the story generator
    out = {}
    for e in index["stories"]:
        if e["status"] == "reviewed" and e.get("file") == f"story/{e['id']}.json":
            out[e["id"]] = {"volcanoId": e["volcanoId"], "onset": _onset(get(e["file"]))}
    return out
