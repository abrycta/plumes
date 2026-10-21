"""Crawl records: one JSON line per fetched page, append-only, resumable. A crawl's records are the bundle that is
adopted into the private archive (DATA-PLAN §2 step 3); only extracted blocks and hashes are kept (DECISIONS S1)."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
from collections.abc import Iterator


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def now() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class Records:
    def __init__(self, path: pathlib.Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)

    def __iter__(self) -> Iterator[dict]:
        if self.path.exists():
            with self.path.open() as f:
                for line in f:
                    if line.strip():
                        yield json.loads(line)

    def done(self, key: str = "url", ok_only: bool = True) -> set:
        return {r[key] for r in self if not ok_only or r.get("status") == 200}

    def latest(self, key: str = "url") -> dict:
        out = {}
        for r in self:
            out[r[key]] = r
        return out

    def add(self, rec: dict) -> None:
        with self.path.open("a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
