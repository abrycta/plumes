"""Stories across data updates (DECISIONS ST15): stories publish when the automated checks pass, a previously public story
keeps its id and stays public unless the data gives a reason, and an open alert window never stretches an event. One
test per failure mode, on a copy of the contract fixture without the hand-built Taal story."""

import json
import pathlib
import shutil

from plumes.contracts import errors
from plumes.stories import generate as gen
from plumes.stories import previous
from plumes.stories.events import OPEN_ALERT_DAYS, add, merge
from plumes.stories.generate import generate

FIXTURE = pathlib.Path(__file__).resolve().parents[2] / "contracts" / "fixtures" / "data" / "v0"
SID = "taal-2020"
PREV = {SID: {"volcanoId": "taal", "onset": "2020-01-12"}}
NONE = pathlib.Path("/nonexistent")


def version(tmp: pathlib.Path, fn=None) -> pathlib.Path:
    v = tmp / "v"
    shutil.copytree(FIXTURE, v)
    (v / "story" / f"{SID}.json").unlink()
    if fn:
        p = v / "volcano" / "taal.json"
        m = json.loads(p.read_text())
        fn(m)
        p.write_text(json.dumps(m))
    return v


def run(tmp: pathlib.Path, v: pathlib.Path, prev: dict | None = PREV) -> tuple[dict, dict, set[str], pathlib.Path]:
    out = tmp / "out"
    res = generate(v, out, previous=prev)
    idx = json.loads((out / "stories.json").read_text())
    assert not errors(idx)
    public = {e["id"] for e in idx["stories"] if e["status"] == "reviewed" and e.get("file") == f"story/{e['id']}.json"}
    return res, idx, public, out


def kept(res: dict) -> bool:
    return next(c for c in res["checks"] if c["check"].startswith("previously public"))["passed"]


def test_a_story_that_passes_the_checks_publishes_without_review(tmp_path):
    res, _, public, out = run(tmp_path, version(tmp_path), prev=None)
    story = json.loads((out / "story" / f"{SID}.json").read_text())
    assert SID in public and story["status"] == "reviewed" and all(s["status"] == "reviewed" for s in story["steps"])
    assert all(c["passed"] for c in res["checks"]), [c for c in res["checks"] if not c["passed"]]


def test_an_open_alert_window_never_stretches_an_event(tmp_path):
    # a gap filled later: the event now runs into an alert window still open at the end of the data
    def fill(m):
        m["episodes"].append({"id": "alert-2020-01-30", "kind": "alert_window", "start": "2020-01-30", "end": m["dataAsOf"], "maxAlert": 2,
                              "source": ["phivolcs-bulletins"]})
    v = version(tmp_path, fill)
    m = json.loads((v / "volcano" / "taal.json").read_text())
    ev = next(e for e in merge("taal", m["episodes"], m["dataAsOf"]) if e.start == "2020-01-12")
    assert ev.end == add("2020-01-30", OPEN_ALERT_DAYS - 1) and not ev.open
    assert all(e["start"] < "2021" for e in ev.episodes)  # later eruptions are not pulled in through the open window
    res, _, public, _ = run(tmp_path, v)
    assert SID in public and kept(res)


def test_a_new_event_in_the_same_year_does_not_rename_a_public_story(tmp_path):
    v = version(tmp_path, lambda m: m["episodes"].append({"id": "gvp-x", "kind": "gvp_eruption", "start": "2020-11-01", "end": "2020-11-02",
                                                         "vei": 1, "source": ["gvp-eruptions-ph"]}))
    res, idx, public, _ = run(tmp_path, v)
    ids = {e["id"] for e in idx["stories"]} | {e["id"] for e in idx["excluded"]}
    assert SID in public and "taal-2020-11" in ids and "taal-2020-01" not in ids and kept(res)


def test_new_data_updates_the_public_text(tmp_path):
    def more(m):
        row = m["bulletins"]["rows"][1]
        m["bulletins"]["rows"][1] = [*row[:2], 80, *row[3:]]
    _, _, public, out = run(tmp_path, version(tmp_path, more))
    assert SID in public and "80" in json.dumps(json.loads((out / "story" / f"{SID}.json").read_text())["steps"])


def test_a_public_story_may_leave_only_with_a_data_driven_reason(tmp_path):
    def drop(m):
        m["episodes"] = [e for e in m["episodes"] if not e["start"].startswith("2020-01")]
        m["episodes"].append({"id": "gvp-y", "kind": "gvp_eruption", "start": "2020-06-01", "end": "2020-06-03", "vei": 1, "source": ["gvp-eruptions-ph"]})
    res, idx, public, _ = run(tmp_path, version(tmp_path, drop))
    assert SID not in public and kept(res) and res["left"] == [f"{SID}: no event at taal holds its onset (2020-01-12) in this data"]
    assert "taal-2020-06-01" in {e["id"] for e in idx["stories"]} | {e["id"] for e in idx["excluded"]}  # no other event takes the id


def test_a_public_story_that_fails_a_check_fails_the_build(tmp_path, monkeypatch):
    real = gen.schema_errors
    monkeypatch.setattr(gen, "schema_errors", lambda doc: real(doc) + (["broken"] if doc.get("id") == SID and doc.get("kind") == "story" else []))
    res, _, public, _ = run(tmp_path, version(tmp_path))
    assert SID not in public and not kept(res)


def test_previous_reads_the_public_stories_and_the_hand_built_onset():
    assert previous.load(FIXTURE) == {SID: {"volcanoId": "taal", "onset": "2020-01-12"}}
