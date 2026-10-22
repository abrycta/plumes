"""Earth Engine run A, pure half (plumes.run_a): tables -> read-model series, on tiny fixtures. No Earth Engine needed."""

import copy
import csv
import json
import pathlib

from plumes import run_a
from plumes.contracts import errors

FX = pathlib.Path(__file__).resolve().parent / "fixtures" / "run_a"
TAAL_V0 = pathlib.Path(__file__).resolve().parents[2] / "contracts" / "fixtures" / "data" / "v0" / "volcano" / "taal.json"
VOLS = [{"id": "taal", "gvpNumber": 273070}, {"id": "mayon", "gvpNumber": 273030}, {"id": "kanlaon", "gvpNumber": 272020}, {"id": "bud-dajo", "gvpNumber": None}]


def table(name):
    with open(FX / f"{name}.csv", newline="") as f:
        return list(csv.DictReader(f))


def tables():
    return {k: table(k) for k in ("laketemp", "lakes2", "lakegsw", "uvai")}


def lake(lake_id):
    return next(x for x in run_a.load_lakes() if x["id"] == lake_id)


def test_lakes_file_is_well_formed():
    lakes = run_a.load_lakes()
    assert {x["volcano"] for x in lakes} == {"taal", "pinatubo"}
    for x in lakes:
        assert 0 < x["coreM"] < x["craterM"] <= 2000
        assert x["name"]["en"] and x["name"]["ja"]


def test_gone_span_ends_at_the_first_clear_scene_that_sees_the_lake_again():
    assert run_a.gone_spans(lake("taal-main-crater"), table("lakes2")) == [("2020-01-12", "2021-02-15")]
    assert run_a.gone_spans(lake("taal-main-crater"), []) == [("2020-01-12", None)]


def test_lake_temperature_keeps_clear_scenes_outside_the_gone_span():
    s = run_a.lake_temp_series(lake("taal-main-crater"), table("laketemp"), table("lakes2"))["lake_temp_landsat"]
    # 03-26 has 5 pixels, 04-11 covers 35 % of the core, 05-13 is cloud, 2020-02-01 is while the lake was gone
    assert s["rows"] == [["2019-03-10", 31.5, 410, 1.2, "OLI/TIRS"], ["2021-06-20", 33.0, 400, 1.1, "OLI/TIRS"]]
    assert s["cols"][0] == "date" and s["units"]["tempC"] == "°C"
    assert "2020-01-12 to 2021-02-15" in s["note"]["en"]


def test_lake_area_publishes_only_cloud_free_dates_and_a_dry_crater_as_zero():
    out = run_a.lake_area_series(lake("taal-main-crater"), table("lakegsw"), table("lakes2"))
    assert out["lake_area_gsw"]["rows"] == [["2019-03-01", 1.124, 1.0], ["2020-02-01", 0.0, 1.0]]
    s2 = out["lake_area_s2"]["rows"]
    assert [r[0] for r in s2] == ["2019-12-01", "2020-02-10", "2020-11-05", "2021-02-15"]
    assert s2[0][1:3] == [1.12, 1.0] and s2[0][3].startswith("#")
    assert s2[1] == ["2020-02-10", 0.0, 1.0, None]  # dry: area 0, no colour
    assert s2[2][3] is None  # a puddle below the minimum gets no colour


def test_srgb_hex():
    assert run_a.srgb_hex(0, 0, 0) == "#000000"
    assert run_a.srgb_hex(0.15, 0.3, 1) == "#ffffff"
    assert run_a.srgb_hex(0.15, 0.0, 0.075) == "#ff00bc"
    assert run_a.srgb_hex(None, 0.1, 0.1) is None


def test_eruption_windows_and_months():
    w = run_a.eruption_windows(VOLS, table("gvp-eruptions"), {273070: ["2021-08-25"]}, as_of="2023-07-15")
    assert w["taal"] == [("2019-12-13", "2020-02-21"), ("2021-06-01", "2021-09-01")]  # 2017 is before TROPOMI; VAAC day joins July 2021
    assert w["mayon"] == [("2023-05-02", "2023-07-15")]  # no end date: the start month, +30 days, clipped to as_of
    assert w["kanlaon"] == [("2023-03-13", "2023-07-15")]  # ">" end: continuing, open to as_of
    assert run_a.window_months(w) == ["2019-12", "2020-01", "2020-02", "2021-06", "2021-07", "2021-08", "2021-09", "2023-03", "2023-04", "2023-05", "2023-06", "2023-07"]


def test_uvai_only_inside_windows_and_valid_days():
    out = run_a.uvai_series("taal", table("uvai"), [("2019-12-13", "2020-02-21")])
    assert out["uvai_s5p_15km"]["rows"] == [["2020-01-12", 4.57, 1.23, 0.704]]
    assert out["uvai_s5p_50km"]["rows"] == [["2020-01-12", 4.9, 0.8, 0.988]]
    assert (out["uvai_s5p_15km"]["ringKm"], out["uvai_s5p_50km"]["ringKm"]) == (15, 50)
    assert run_a.uvai_series("taal", table("uvai"), []) == {}


def test_series_fit_the_volcano_contract():
    taal = json.loads(TAAL_V0.read_text())
    windows = {"taal": [("2019-12-13", "2020-02-21")]}
    doc = copy.deepcopy(taal)
    added = run_a.volcano_series("taal", run_a.load_lakes(), tables(), windows)
    assert set(added) == {"lake_temp_landsat", "lake_area_gsw", "lake_area_s2", "uvai_s5p_15km", "uvai_s5p_50km"}
    doc["events"].update(added)
    assert errors(doc) == []


def test_no_tables_adds_nothing():
    assert run_a.volcano_series("taal", run_a.load_lakes(), {}, {}) == {}
    assert run_a.volcano_series("mayon", run_a.load_lakes(), tables(), {}) == {}


# Real Sentinel-2 L2A pixels (B3, B8, B11) sampled inside Taal's crater disc on 2026-10-23.
LAKE_PIXELS = [(0.016, 0.001, 0.008), (0.028, 0.014, 0.015),  # 2019-12-24, dark lake before the eruption
               (0.187, 0.06, 0.074), (0.169, 0.034, 0.025), (0.106, 0.023, 0.023)]  # 2020-06/09, turquoise lake after it
NOT_WATER = [(0.116, 0.112, 0.115), (0.169, 0.158, 0.166),  # 2020-01-28, wet ash (old test: water)
             (0.117, 0.113, 0.107), (0.074, 0.07, 0.072)]  # 2020-09-19 and 2020-06-16, haze over the crater (old test: water)


def test_water_test_keeps_lake_water_and_drops_wet_ash_and_haze():
    assert all(run_a.is_water(*p) for p in LAKE_PIXELS)
    assert not any(run_a.is_water(*p) for p in NOT_WATER)
    assert all((p[0] - p[1]) / (p[0] + p[1]) > 0 for p in NOT_WATER)  # the old test (NDWI > 0) let every one through


def test_apply_adds_events_provenance_and_assets():
    from plumes.readmodels import REG

    models = {"taal": json.loads(TAAL_V0.read_text()), "mayon": {"events": {}, "provenance": {"sources": []}}}
    n = run_a.apply(models, tables(), {"taal": [("2019-12-13", "2020-02-21")]}, REG)
    assert n == 1 and models["mayon"] == {"events": {}, "provenance": {"sources": []}}
    taal = models["taal"]
    assert {"lake_temp_landsat", "uvai_s5p_15km"} <= set(taal["events"])
    ids = [s["id"] for s in taal["provenance"]["sources"]]
    assert {"landsat-surface-temperature", "s5p-offl-aer-ai"} <= set(ids) and len(ids) == len(set(ids))
    assert run_a.S5P_AER_AI in taal["provenance"]["earthEngine"]["assets"]
    assert errors(taal) == []
