"""Earth Engine run B read models (IMERG rain, national monthly SO2) on tiny fixtures: no Earth Engine needed."""

import copy
import json
import pathlib

import yaml

from plumes import run_b
from plumes.contracts import errors
from plumes.geotiff import NODATA, read_int16, write_int16

FIX = pathlib.Path(__file__).resolve().parents[2] / "contracts" / "fixtures" / "data" / "v0"
REGISTRY = {e["id"]: e for e in yaml.safe_load((pathlib.Path(__file__).resolve().parents[1] / "sources.yaml").read_text())["sources"]}
HDR = {"schemaVersion": "1", "dataVersion": "v0", "dataAsOf": "2025-10-01", "generatedAt": "2025-10-01T00:00:00Z"}


def _rain(date, mm, hh, vid="taal", ring="15km"):
    return {"volcano": vid, "ring": ring, "date": date, "rain_mm": "" if mm is None else str(mm), "halfhours": "" if hh is None else str(hh)}


def test_geotiff_round_trip_keeps_values_nodata_and_bounds():
    so2 = [[0, -5, 32767], [NODATA, 120, -32767]]
    valid = [[100, 0, 3], [0, 50, 97]]
    buf = write_int16([so2, valid], (116.0, 4.0, 128.0, 22.0), ["so2_umol_m2", "valid_days_pct"])
    got = read_int16(buf)
    assert got["bands"] == [so2, valid]
    assert got["bounds"] == (116.0, 4.0, 128.0, 22.0)
    assert got["nodata"] == NODATA
    assert got["names"] == ["so2_umol_m2", "valid_days_pct"]


def test_geotiff_clamps_and_treats_none_as_nodata():
    got = read_int16(write_int16([[[None, 99999, -99999]]], (0.0, 0.0, 3.0, 1.0)))
    assert got["bands"] == [[[NODATA, 32767, -32767]]]


def test_rain_series_is_daily_with_gaps_for_missing_or_incomplete_days():
    rows = [_rain("2020-01-01", 3.14, 48), _rain("2020-01-02", 0, 48), _rain("2020-01-03", 12.0, 30), _rain("2020-01-05", None, None),
            _rain("2020-01-04", 1.0, 48, ring="30km"), _rain("2020-01-04", 9.9, 48, vid="mayon")]
    s = run_b.rain_series("taal", rows)[run_b.RAIN_ID]
    assert s["start"] == "2020-01-01"
    # day 3: too few Final half-hours; day 4: no row for this ring; day 5: masked -> gaps, never zero
    assert s["values"] == [3.1, 0.0, None, None, None]
    assert s["source"] == ["gpm-imerg-v07"] and s["unit"] == "mm" and s["ringKm"] == 15
    assert run_b.rain_series("kanlaon", rows) == {}


def test_apply_adds_rain_and_its_provenance_and_keeps_the_volcano_file_valid():
    taal = json.loads((FIX / "volcano" / "taal.json").read_text())
    models = {"taal": copy.deepcopy(taal)}
    assert run_b.apply(models, [_rain("2020-01-12", 40.5, 48), _rain("2020-01-13", 2.0, 48)], REGISTRY) == 1
    vm = models["taal"]
    assert vm["daily"]["rain_imerg_15km"]["values"] == [40.5, 2.0]
    assert set(taal["daily"]) < set(vm["daily"])
    assert [s["id"] for s in vm["provenance"]["sources"]].count("gpm-imerg-v07") == 1
    assert errors(vm) == []


def test_so2_monthly_layer_copies_months_and_matches_the_layers_contract(tmp_path):
    tables, out = tmp_path / "tables", tmp_path / "v9"
    (tables / "ee-so2-monthly").mkdir(parents=True)
    tif = write_int16([[[1, 2]], [[100, 50]]], run_b.SO2_BOUNDS)
    for m in ("2019-01", "2019-02", "2019-04"):
        (tables / "ee-so2-monthly" / f"{m}.tif").write_bytes(tif)
    layer = run_b.so2_monthly_layer(tables, out, "attribution")
    assert layer["time"] == {"step": "month", "start": "2019-01", "end": "2019-04", "available": ["2019-01", "2019-02", "2019-04"]}
    assert (out / "layers" / "so2" / "2019-04.tif").read_bytes() == tif
    assert errors({**HDR, "kind": "layers", "layers": [layer]}) == []
    assert run_b.so2_monthly_layer(tmp_path / "none", out, "a") is None
