"""Reviewed stories stay public, keep their id and never change silently across data updates (DECISIONS, "Reviewed
stories stay stable"). One test per failure mode, on a copy of the contract fixture whose generated Taal 2020 story is
reviewed (review.yaml hashes + reviewed/<id>.json)."""

import json
import pathlib
import shutil

import yaml

from plumes.contracts import errors
from plumes.stories.generate import generate, step_hash

FIXTURE = pathlib.Path(__file__).resolve().parents[2] / "contracts" / "fixtures" / "data" / "v0"
SID = "taal-2020"


def setup(tmp: pathlib.Path) -> tuple[pathlib.Path, dict]:
    """A version without the hand-built Taal story, and review files that approve the generated one as it is now."""
    v = tmp / "v"
    shutil.copytree(FIXTURE, v)
    (v / "story" / f"{SID}.json").unlink()
    first = tmp / "first"
    generate(v, first, review_path=tmp / "none.yaml", reviewed_dir=tmp / "none")
    story = json.loads((first / "story" / "drafts" / f"{SID}.json").read_text())
    (tmp / "review.yaml").write_text(yaml.safe_dump({"reviews": [{"story": SID, "step": s["kind"], "sha256": step_hash(s), "reviewer": "Kurt",
                                                                  "date": "2026-10-23"} for s in story["steps"]]}))
    (tmp / "reviewed").mkdir()
    (tmp / "reviewed" / f"{SID}.json").write_text(json.dumps(story))
    return v, story


def run(tmp: pathlib.Path, v: pathlib.Path) -> tuple[dict, dict, pathlib.Path]:
    out = tmp / "out"
    shutil.rmtree(out, ignore_errors=True)
    res = generate(v, out, review_path=tmp / "review.yaml", reviewed_dir=tmp / "reviewed")
    idx = json.loads((out / "stories.json").read_text())
    assert not errors(idx)
    return res, idx, out


def public(idx: dict, out: pathlib.Path, sid: str = SID) -> dict:
    e = [s for s in idx["stories"] if s["id"] == sid and s["status"] == "reviewed"]
    assert len(e) == 1 and e[0]["file"] == f"story/{sid}.json"
    return json.loads((out / e[0]["file"]).read_text())


def edit(v: pathlib.Path, fn) -> None:
    p = v / "volcano" / "taal.json"
    m = json.loads(p.read_text())
    fn(m)
    p.write_text(json.dumps(m))


def texts(story: dict) -> list:
    return [s["text"] for s in story["steps"]]


def test_unchanged_data_publishes_the_new_text_with_nothing_pending(tmp_path):
    v, story = setup(tmp_path)
    res, idx, out = run(tmp_path, v)
    assert texts(public(idx, out)) == texts(story) and res["pendingReview"] == []
    assert all(c["passed"] for c in res["checks"]), [c for c in res["checks"] if not c["passed"]]


def test_an_alert_window_that_merges_and_stays_open_keeps_the_story_and_its_reviewed_windows(tmp_path):
    v, story = setup(tmp_path)  # a gap filled later: the event now runs into an alert window that is still open
    edit(v, lambda m: m["episodes"].append({"id": "alert-2020-01-30", "kind": "alert_window", "start": "2020-01-30", "end": m["dataAsOf"],
                                            "maxAlert": 2, "source": ["phivolcs-bulletins"]}))
    res, idx, out = run(tmp_path, v)
    pub = public(idx, out)
    assert texts(pub) == texts(story) and [(s["start"], s["end"]) for s in pub["steps"]] == [(s["start"], s["end"]) for s in story["steps"]]
    assert SID not in {e["id"] for e in idx["excluded"]} and res["pendingReview"] == []


def test_a_new_event_in_the_same_year_does_not_rename_the_reviewed_story(tmp_path):
    v, story = setup(tmp_path)  # derived ids would become taal-2020-01 and taal-2020-11
    edit(v, lambda m: m["episodes"].append({"id": "gvp-x", "kind": "gvp_eruption", "start": "2020-11-01", "end": "2020-11-02", "vei": 1,
                                            "source": ["gvp-eruptions-ph"]}))
    res, idx, out = run(tmp_path, v)
    assert texts(public(idx, out)) == texts(story)
    ids = {e["id"] for e in idx["stories"]} | {e["id"] for e in idx["excluded"]}
    assert "taal-2020-11" in ids and "taal-2020-01" not in ids


def test_a_changed_number_keeps_the_reviewed_text_public_and_reports_the_step(tmp_path):
    v, story = setup(tmp_path)
    edit(v, lambda m: m["bulletins"]["rows"].__setitem__(1, [*m["bulletins"]["rows"][1][:2], 80, *m["bulletins"]["rows"][1][3:]]))
    res, idx, out = run(tmp_path, v)
    assert texts(public(idx, out)) == texts(story)
    pend = res["pendingReview"]
    assert len(pend) == 1 and pend[0]["id"] == SID and pend[0]["steps"] and "before" not in pend[0]["steps"]
    draft = [e for e in idx["stories"] if e["id"] == SID and e["status"] == "draft"]
    assert len(draft) == 1 and draft[0]["file"] == f"story/drafts/{SID}.json"
    assert "80" in json.dumps(json.loads((out / draft[0]["file"]).read_text())["steps"], ensure_ascii=False)
    assert all(c["passed"] for c in res["checks"]) and any(SID in c["detail"] for c in res["checks"] if c["check"] == "reviewed stories pending re-review")


def test_an_event_gone_from_the_data_keeps_the_story_and_no_other_event_takes_its_id(tmp_path):
    v, story = setup(tmp_path)

    def move(m):
        m["episodes"] = [e for e in m["episodes"] if not e["start"].startswith("2020-01")]
        m["episodes"].append({"id": "gvp-y", "kind": "gvp_eruption", "start": "2020-06-01", "end": "2020-06-03", "vei": 1, "source": ["gvp-eruptions-ph"]})
    edit(v, move)
    res, idx, out = run(tmp_path, v)
    assert texts(public(idx, out)) == texts(story)
    assert res["pendingReview"] == [{"id": SID, "steps": ["no separate event in this version"]}]
    assert "taal-2020-06-01" in {e["id"] for e in idx["stories"]} | {e["id"] for e in idx["excluded"]}


def test_a_missing_or_altered_reviewed_text_fails_the_build(tmp_path):
    v, story = setup(tmp_path)
    altered = {**story, "steps": [{**story["steps"][0], "text": {"en": "x", "ja": "x"}}, *story["steps"][1:]]}
    (tmp_path / "reviewed" / f"{SID}.json").write_text(json.dumps(altered))
    res, _, _ = run(tmp_path, v)
    assert [c for c in res["checks"] if not c["passed"] and SID in c["check"]]
    (tmp_path / "reviewed" / f"{SID}.json").unlink()
    res, _, _ = run(tmp_path, v)
    assert [c for c in res["checks"] if not c["passed"] and "missing" in c["detail"]]


def test_every_reviewed_story_has_its_reviewed_text_in_the_repo():
    here = pathlib.Path(__file__).resolve().parents[1] / "plumes" / "stories"
    rows = yaml.safe_load((here / "review.yaml").read_text())["reviews"]
    snaps = {p.stem: json.loads(p.read_text()) for p in (here / "reviewed").glob("*.json")}
    assert {r["story"] for r in rows} == set(snaps)
    for r in rows:
        assert step_hash(next(s for s in snaps[r["story"]]["steps"] if s["kind"] == r["step"])) == r["sha256"], (r["story"], r["step"])
