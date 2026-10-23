import json

import pytest

from plumes.contracts import errors
from plumes.deeptime import build_model, check_hazel
from plumes.sources import SchemaError

HDR = {"schemaVersion": "1", "dataVersion": "v0", "dataAsOf": "2026-10-21", "generatedAt": "2026-10-22T00:00:00Z", "fixture": True}
VOLS = [{"id": "hibok-hibok", "gvpNumber": 271080}, {"id": "taal", "gvpNumber": 273070}]
COLS = ["Volcano_Number", "Eruption_Number", "Activity_Type", "ExplosivityIndexMax", "ExplosivityIndexModifier", "StartEvidenceMethod",
        "StartDateYearModifier", "StartDateYear", "StartDateYearUncertainty", "StartDateMonth", "StartDateDay", "StartDateDayUncertainty",
        "EndDateYear", "EndDateMonth", "EndDateDay"]


def gvp(n, num, start, end=("", "", ""), unc="", vei="3"):
    return dict(zip(COLS, [str(n), str(num), "Confirmed Eruption", vei, "", "", "", *start[:1], unc, *start[1:], "", *end], strict=True))


def hazel(i, n, y, m=None, d=None, **kw):
    return {"id": i, "volcanoLocationNewNum": n, "year": y, "month": m, "day": d, **kw}


def test_impacts_attach_to_the_containing_eruption_and_the_rest_stay_separate():
    gvp_e = [gvp(271080, 1, ("1948", "9", "1"), ("1953", "7", "16")), gvp(273070, 2, ("-3580", "", ""), unc="200", vei="6"),
             gvp(273070, 3, ("1911", "1", "27"), ("1911", "2", "8"))]
    hz = [hazel(10, 271080, 1949, 6, deaths=2), hazel(11, 271080, 1951, 12, 4, deaths=500, agent="P"), hazel(12, 271080, 1954, deaths=2, agent="m"),
          hazel(13, 273070, -3500), hazel(14, 273070, 1911, 1, 30, deaths=1335, housesDestroyed=543, agent="P,W"), hazel(15, 273088, 1952)]
    doc, outside = build_model(HDR, VOLS, gvp_e, hz, {"sources": []})
    assert errors(doc) == []
    hib, taal = doc["volcanoes"]
    assert [i["id"] for i in hib["eruptions"][0]["impacts"]] == ["hazel-10", "hazel-11"]
    assert [i["date"] for i in hib["otherImpacts"]] == ["1954"]
    assert taal["eruptions"][0]["start"] == "-3580" and taal["eruptions"][0]["startYearUncertainty"] == 200
    assert taal["eruptions"][0]["impacts"][0]["id"] == "hazel-13"  # inside ±200 years
    imp = taal["eruptions"][1]["impacts"][0]
    assert (imp["deaths"], imp["housesDestroyed"], imp["agents"]) == (1335, 543, ["P", "W"])
    assert [o["id"] for o in outside] == [15]


def test_hook_rejects_a_paged_or_foreign_answer(tmp_path):
    p = tmp_path / "h.json"
    items = [hazel(i, 273030, 1900) for i in range(40)]
    p.write_text(json.dumps({"items": items, "page": 1, "totalPages": 1, "totalItems": 40}))
    assert check_hazel(p, {}) == []
    p.write_text(json.dumps({"items": items, "page": 1, "totalPages": 2, "totalItems": 80}))
    with pytest.raises(SchemaError, match="paged"):
        check_hazel(p, {})
    p.write_text(json.dumps({"items": items + [hazel(99, 284000, 1900)], "page": 1, "totalPages": 1, "totalItems": 41}))
    with pytest.raises(SchemaError, match="Philippine range"):
        check_hazel(p, {})
