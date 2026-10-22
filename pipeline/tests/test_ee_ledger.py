"""The Earth Engine ledger merges without double-counting (worktrees, the Pages copy, repeated merges)."""

from plumes.ee_ledger import merge, merge_into, read

A = {"date": "2026-10-22", "label": "so2 2018-12..2026-09", "eecu_s": 8197.2, "calls": 93}
B = {"id": "b1", "date": "2026-10-23", "label": "run B rain", "eecu_s": 5992.4, "calls": 308}
C = {"id": "c1", "date": "2026-11-01", "label": "fire", "eecu_s": 10.0, "calls": 1}


def test_union_counts_each_run_once():
    main = {"months": {"2026-10": 8197.2}, "runs": [A]}
    worktree = {"months": {"2026-10": 14189.6}, "runs": [A, B]}
    out = merge(main, worktree, worktree)
    assert out["runs"] == [A, B]
    assert out["months"] == {"2026-10": 14189.6}


def test_months_come_from_the_runs():
    stale = {"months": {"2026-10": 99999.0}, "runs": [A, C]}
    assert merge(stale)["months"] == {"2026-10": 8197.2, "2026-11": 10.0}


def test_merge_into_is_idempotent(tmp_path):
    path = tmp_path / "ee-usage.json"
    merge_into(path, {"runs": [A]})
    merge_into(path, {"runs": [A, B]}, {"runs": [B]})
    assert read(path) == merge({"runs": [A, B]})
