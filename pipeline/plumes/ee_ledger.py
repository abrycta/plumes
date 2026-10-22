"""The one Earth Engine ledger (`paths.EE_LEDGER`): a list of runs, each with an id; month totals are derived from the
runs, so merging ledgers (worktrees, the Pages copy, repeated merges) never double-counts. No Earth Engine import, so
`plumes.state restore` can merge the published copy without the ee extra.

    uv run python -m plumes.ee_ledger show                  # where the ledger is and its month totals
    uv run python -m plumes.ee_ledger merge FILE [FILE...]  # fold other ledgers into it (idempotent)
"""

from __future__ import annotations

import contextlib
import fcntl
import json
import pathlib
import sys

from plumes.paths import EE_LEDGER


def _key(rec: dict) -> str:
    """A run's identity: its id, or for runs logged before ids existed, its contents."""
    return rec.get("id") or f"{rec['date']}|{rec['label']}|{rec['eecu_s']}|{rec['calls']}"


def merge(*ledgers: dict) -> dict:
    """The union of the runs of every ledger (each run once), with the month totals recomputed from the runs."""
    runs: dict[str, dict] = {}
    for led in ledgers:
        for rec in led.get("runs", []):
            runs.setdefault(_key(rec), rec)
    ordered = sorted(runs.values(), key=lambda r: r["date"])  # stable: keeps each ledger's order within a day
    months: dict[str, float] = {}
    for rec in ordered:
        months[rec["date"][:7]] = round(months.get(rec["date"][:7], 0.0) + rec["eecu_s"], 1)
    return {"months": months, "runs": ordered}


def read(path: pathlib.Path = EE_LEDGER) -> dict:
    return json.loads(path.read_text()) if path.exists() else {"months": {}, "runs": []}


@contextlib.contextmanager
def _locked(path: pathlib.Path):
    """Serialise read-merge-write of the ledger across concurrent runs and worktrees."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path.with_name(path.name + ".lock"), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def merge_into(path: pathlib.Path, *ledgers: dict) -> dict:
    """Fold ledgers into the one at path (under the lock) and return the result."""
    with _locked(path):
        out = merge(read(path), *ledgers)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(json.dumps(out, indent=1))
        tmp.replace(path)
    return out


if __name__ == "__main__":
    cmd, files = (sys.argv[1] if len(sys.argv) > 1 else "show"), sys.argv[2:]
    if cmd == "merge":
        led = merge_into(EE_LEDGER, *(json.loads(pathlib.Path(f).read_text()) for f in files))
    elif cmd == "show":
        led = read()
    else:
        raise SystemExit("usage: python -m plumes.ee_ledger [show | merge FILE...]")
    print(json.dumps({"ledger": str(EE_LEDGER), "runs": len(led["runs"]),
                      "months_eecu_s": led["months"], "months_eecu_h": {m: round(v / 3600, 2) for m, v in led["months"].items()}}))
