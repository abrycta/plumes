"""Story generator (STORIES-PLAN Part B): one test per template rule, the absent-data rule, EN/JA parity, the checks,
the event windows and a generation run on the contract fixture."""

import copy
import json
import pathlib
import re

import pytest
import yaml

from plumes.contracts import errors
from plumes.stories import facts
from plumes.stories import render as rd
from plumes.stories import text as tx
from plumes.stories.events import Event, merge, windows
from plumes.stories.generate import generate, step_hash
from plumes.stories.render import V

FIXTURE = pathlib.Path(__file__).resolve().parents[2] / "contracts" / "fixtures" / "data" / "v0"
VERSION, CAT = rd.load()

# One sample value per placeholder type; the numbers are distinct so each can be found in the rendered text.
SAMPLE = {"date": "2020-01-12", "span": ("2020-01-01", "2020-01-11"), "dash": ("2020-01-15", "2020-01-21"), "month": "2020-01-12",
          "int": 4057, "num": 16.5, "level": 3, "km": 14, "year": 2020, "fl": 550, "share": 0.873, "time": (19, 30), "sensor": "TROPOMI",
          "dir": "toward", "agency": "PHIVOLCS", "name": {"en": "Taal", "ja": "タール火山"}}
NUMERIC = {"int", "num", "level", "km", "year", "fl"}


def sample(t: rd.Template) -> dict[str, V]:
    return {k: V(SAMPLE[kind], "test-source") for k, kind in t.types.items()}


@pytest.mark.parametrize("tid", sorted(CAT))
def test_template_renders_in_both_languages_with_every_value(tid):
    t = CAT[tid]
    out = rd.render(t, sample(t))
    assert out and out["en"] and out["ja"]
    assert not rd.check_sentence(t, out)
    for k, kind in t.types.items():  # EN/JA parity: every numeric value is in both texts
        if kind in NUMERIC:
            want = tx.num(SAMPLE[kind]) if kind not in ("year", "fl") else str(SAMPLE[kind])
            assert want in out["en"] and want in out["ja"], (tid, k)


@pytest.mark.parametrize("tid", sorted(t for t in CAT if CAT[t].types))
def test_a_missing_datum_omits_the_sentence(tid):
    t = CAT[tid]
    for k in t.types:
        vals = sample(t)
        vals[k] = None
        assert rd.render(t, vals) is None, k
        vals[k] = V(None, "test-source")
        assert rd.render(t, vals) is None, k


@pytest.mark.parametrize("tid", sorted(CAT))
def test_en_and_ja_use_the_same_placeholders_in_every_form(tid):
    t = CAT[tid]
    for form in [t.text, *t.variants]:
        assert set(re.findall(r"\{(\w+)\}", form["en"])) == set(re.findall(r"\{(\w+)\}", form["ja"]))


def test_a_value_without_a_source_is_refused():
    t = CAT["GVP-VEI"]
    with pytest.raises(rd.TemplateError):
        rd.render(t, {"vei": V(4, "")})


def test_no_free_text_type_exists_and_closed_lists_refuse_other_values():
    assert all("text" not in t.types.values() for t in CAT.values())
    with pytest.raises(rd.TemplateError):
        rd.render(CAT["HEAT-DAYS"], {**sample(CAT["HEAT-DAYS"]), "sensor": V("a sentence from a source", "x")})


def test_catalogue_refuses_an_unsourced_digit_and_mismatched_placeholders(tmp_path):
    bad = {"version": 1, "templates": [{"id": "X", "family": "alert", "types": {"n": "int"}, "en": "{n} earthquakes in 7 days.", "ja": "{n}回。"}]}
    p = tmp_path / "t.yaml"
    p.write_text(yaml.safe_dump(bad, allow_unicode=True))
    with pytest.raises(rd.TemplateError, match="digit"):
        rd.load(p)
    bad["templates"][0] |= {"en": "{n} earthquakes.", "ja": "地震。"}
    p.write_text(yaml.safe_dump(bad, allow_unicode=True))
    with pytest.raises(rd.TemplateError, match="placeholders"):
        rd.load(p)


def test_variants_plural_zero_single_day_and_continuation():
    t = CAT["BUL-VEQ-MAX"]
    span = V(("2020-01-01", "2020-01-11"), "s")
    assert "counted no volcanic earthquake from" in rd.render(t, {"n": V(0, "s"), "span": span})["en"]
    assert "up to 1 volcanic earthquake in a day" in rd.render(t, {"n": V(1, "s"), "span": span})["en"]
    one_day = rd.render(t, {"n": V(12, "s"), "span": V(("2020-01-18", "2020-01-18"), "s")})
    assert one_day["en"] == "PHIVOLCS bulletins counted 12 volcanic earthquakes on 18 January 2020, as reported by PHIVOLCS."
    assert rd.render(CAT["VAAC-COUNT"], {"n": V(5, "s"), "span": V(("2024-06-03", "2024-06-03"), "s")})["en"] == "Tokyo VAAC issued 5 ash advisories on 3 June 2024."
    h = CAT["HAZEL-HOUSES"]
    assert rd.render(h, {"n": V(12, "s")}, {"prev_family": "hazel"})["en"] == "It records 12 houses destroyed."
    assert rd.render(h, {"n": V(12, "s")})["en"].startswith("NOAA's Significant")


def test_taal_sentences_match_the_reviewed_wording():
    held = rd.render(CAT["ALERT-HELD"], {"level": V(1, "s"), "span": V(("2019-12-01", "2020-01-11"), "s")})
    assert held == {"en": "PHIVOLCS bulletins reported Alert Level 1 on every day from 1 December 2019 to 11 January 2020, as reported by PHIVOLCS.",
                    "ja": "PHIVOLCSの火山情報は2019年12月1日から2020年1月11日まで毎日、警戒レベル1を発表していた（PHIVOLCS発表）。"}
    vaac = rd.render(CAT["VAAC-MAX"], {"fl": V(550, "s"), "date": V("2020-01-12", "s")})
    assert vaac == {"en": "Tokyo VAAC observed ash up to FL550 (about 16.8 km) on 12 January 2020.", "ja": "東京VAACは2020年1月12日に最高FL550（約16.8 km）の火山灰を観測した。"}


def test_checks_catch_advice_words_and_causal_rain_wording():
    assert rd.safety_words({"en": "Residents should stay away.", "ja": "危険です。"}) == ["should", "stay away", "危険"]
    assert rd.safety_words({"en": "A past record, not a hazard assessment.", "ja": "過去の記録であり、ハザード評価ではない。"}) == []
    assert rd.causal_words({"en": "Rain fell, which triggered a lahar.", "ja": "雨により"}) == ["triggered", "により"]


def test_span_and_dash_wording():
    assert tx.span_en("2020-01-01", "2020-01-11") == "1 to 11 January 2020"
    assert tx.span_ja("2024-06-03", "2024-09-09") == "2024年6月3日から9月9日まで"
    assert tx.span_en("2019-12-01", "2020-01-11") == "1 December 2019 to 11 January 2020"
    assert tx.dash_en("2020-01-12", "2020-01-13") == "12–13 January 2020"
    assert tx.dash_ja("2020-01-12", "2020-01-13") == "2020年1月12〜13日"
    assert tx.num(-1234.5) == "−1,234.5" and tx.num(170.0) == "170"


# ---------------------------------------------------------------- events and windows

def ep(i, kind, start, end):
    return {"id": i, "kind": kind, "start": start, "end": end}


def test_events_merge_overlapping_and_adjacent_episodes_and_flag_open_ones():
    eps = [ep("gvp-1", "gvp_eruption", "2024-06-03", "2024-06-03"), ep("alert-a", "alert_window", "2024-06-04", "2024-09-09"),
           ep("alert-b", "alert_window", "2024-09-20", "2026-10-21"), ep("gvp-0", "gvp_eruption", "1991-06-15", "1991-09-02")]
    evs = merge("kanlaon", eps, "2026-10-22")
    assert [(e.id, [x["id"] for x in e.episodes], e.open) for e in evs] == [("kanlaon-2024-06", ["gvp-1", "alert-a"], False), ("kanlaon-2024-09", ["alert-b"], True)]


def test_windows_keep_a_full_onset_for_a_one_day_eruption_and_stop_at_the_next_event():
    ev = Event("bulusan", "2016-02-22", "2016-02-22", [ep("gvp-2", "gvp_eruption", "2016-02-22", "2016-02-22")], "bulusan-2016-02")
    w = windows(ev, None, "2016-04-01")
    assert w == {"before": ("2015-11-24", "2016-02-21"), "onset": ("2016-02-22", "2016-02-28"), "after": ("2016-02-29", "2016-03-31")}
    assert windows(ev, "2016-01-01", None)["before"][0] == "2016-01-02"


# ---------------------------------------------------------------- adapters on a small model

def model(**kw):
    m = {"dataAsOf": "2026-10-22", "volcano": {"id": "taal", "name": {"en": "Taal", "ja": "タール火山"}, "lat": 14.0, "lon": 121.0},
         "daily": {}, "events": {}, "bulletins": None, "advisories": None, "displacement": None, "exposure": {"rings": []}, "episodes": []}
    return m | kw


def bul(date, level, eq=None, url=None):
    return [date, level, eq, None, None, None, None, None, url or f"https://wovodat.phivolcs.dost.gov.ph/bulletin/activity-tvo?bid={date}"]


def test_alert_adapter_holds_raises_with_the_bulletin_time_and_skips_one_day_blips():
    rows = [bul(f"2020-01-{d:02d}", 1) for d in range(1, 12)] + [bul("2020-01-12", 4, url="https://www.phivolcs.dost.gov.ph/taal-volcano-bulletin-12-january-2020-7-30-p-m/")]
    m = model(bulletins={"rows": copy.deepcopy(rows)})
    assert [c.template for c in facts.alert(m, "before", ("2020-01-01", "2020-01-11"))] == ["ALERT-HELD"]
    rows[5][1] = 3  # a one-day blip inside a run of level 1: not a change, and not a day of level 1 either
    m = model(bulletins={"rows": rows})
    before = facts.alert(m, "before", ("2020-01-01", "2020-01-11"))
    assert [c.template for c in before] == ["ALERT-HELD-GAPS"] and before[0].values["n"].value == 10
    onset = facts.alert(m, "onset", ("2020-01-12", "2020-01-18"))
    assert [c.template for c in onset] == ["ALERT-RAISED"]
    text = rd.render(CAT["ALERT-RAISED"], onset[0].values)
    assert text["en"] == "PHIVOLCS raised the alert from level 1 to level 4 on 12 January 2020 in its 7:30 PM bulletin, as reported by PHIVOLCS."
    assert onset[0].figures[0]["url"].startswith("https://www.phivolcs")


def test_series_that_do_not_exist_give_no_sentence_and_a_zero_count_is_a_fact():
    m = model(events={"eq_usgs_30km": {"start": "2000-01-01", "rows": [["2019-10-11", 2, 4.1]]}})
    ev = Event("taal", "2020-01-12", "2020-01-12", [], "taal-2020")
    w = ("2020-01-13", "2020-01-18")
    assert facts.so2(m, "onset", w) == [] and facts.vaac(m, "onset", w) == [] and facts.thermal(m, "onset", w) == []
    assert facts.bulletin_numbers(m, "onset", w) == [] and facts.dromic(m, "after", w, ev) == [] and facts.rain(m, "after", w) == []
    assert [c.template for c in facts.usgs(m, "onset", w, ev)] == ["EQ-NONE"]


def test_rain_needs_every_day_of_the_step():
    days = [1.0, 0.0, 12.5, 3.0]
    m = model(daily={"rain_imerg_15km": {"start": "2020-01-01", "values": days}})
    got = facts.rain(m, "course", ("2020-01-01", "2020-01-04"))
    assert [c.template for c in got] == ["RAIN-TOTAL", "RAIN-WETTEST"] and got[0].values["x"].value == 16.5
    m["daily"]["rain_imerg_15km"]["values"][1] = None
    assert facts.rain(m, "course", ("2020-01-01", "2020-01-04")) == []


# ---------------------------------------------------------------- generation on the contract fixture

def test_generation_on_the_fixture_writes_valid_drafts_and_an_index(tmp_path):
    res = generate(FIXTURE, tmp_path)
    assert all(c["passed"] for c in res["checks"]), [c for c in res["checks"] if not c["passed"]]
    idx = json.loads((tmp_path / "stories.json").read_text())
    assert not errors(idx)
    draft = next(s for s in idx["stories"] if s.get("file") == "story/drafts/taal-2020.json")
    assert draft["status"] == "draft" and draft["score"]["tier"] == "story"
    assert any(s.get("file") == "story/taal-2020.json" and "score" not in s for s in idx["stories"])  # the hand-built story stays listed
    story = json.loads((tmp_path / draft["file"]).read_text())
    assert not errors(story)
    for st in story["steps"]:
        assert st["status"] == "draft" and st["kind"] in ("before", "onset", "course", "after")
        assert st["text"]["en"] == " ".join(s["text"]["en"] for s in st["sentences"]) + (" " if st["sentences"] and st["absent"] else "") + " ".join(a["text"]["en"] for a in st["absent"])
        assert not tx.ja_leftovers(st["text"]["ja"] + st["title"]["ja"])
        for s in st["sentences"]:
            assert s["sources"] and all(0 <= i < len(st["figures"]) for i in s["figures"])
    assert [s["kind"] for s in story["steps"]][0] == "before" and story["steps"][-1]["kind"] == "after"


def test_a_matching_review_hash_publishes_the_story_and_a_changed_number_reopens_it(tmp_path):
    first = tmp_path / "a"
    generate(FIXTURE, first)
    story = json.loads((first / "story" / "drafts" / "taal-2020.json").read_text())
    review = tmp_path / "review.yaml"
    review.write_text(yaml.safe_dump({"reviews": [{"story": "taal-2020", "step": s["kind"], "sha256": step_hash(s), "reviewer": "Kurt", "date": "2026-10-23"}
                                                  for s in story["steps"]]}))
    second = tmp_path / "b"
    generate(FIXTURE, second, review_path=review)
    assert json.loads((second / "story" / "taal-2020.json").read_text())["status"] == "reviewed"
    changed = copy.deepcopy(story["steps"][0])
    changed["figures"].append({"label": {"en": "x", "ja": "x"}, "value": 1, "source": "x"})
    assert step_hash(changed) != step_hash(story["steps"][0])
