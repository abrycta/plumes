"""NOAA-20 thermal series and OMI SO2 reduction on small synthetic inputs."""

import csv
import json

import h5py
import numpy as np

from plumes import omi, thermal_n20

TAAL = {"id": "taal", "lat": 14.002, "lon": 120.993}


def _csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["latitude", "longitude", "acq_date", "acq_time", "frp", "type"])
        w.writeheader()
        w.writerows(rows)


def test_n20_series_standard_then_nrt(tmp_path, monkeypatch):
    raw = tmp_path / "raw"
    monkeypatch.setattr(thermal_n20, "RAW", raw)
    monkeypatch.setattr(thermal_n20, "NRT_FILE", raw / "firms" / thermal_n20.NRT / "recent.csv")
    sp = raw / "firms" / thermal_n20.SP
    _csv(sp / "2026.csv", [
        {"latitude": 14.01, "longitude": 120.99, "acq_date": "2026-06-28", "acq_time": "500", "frp": "3.5", "type": "1"},
        {"latitude": 14.01, "longitude": 120.99, "acq_date": "2026-06-28", "acq_time": "500", "frp": "3.5", "type": "1"},  # duplicate
        {"latitude": 14.05, "longitude": 121.00, "acq_date": "2026-06-28", "acq_time": "501", "frp": "9.0", "type": "0"},
        {"latitude": 15.00, "longitude": 121.00, "acq_date": "2026-06-28", "acq_time": "502", "frp": "50", "type": "0"},  # far away
    ])
    (sp / "windows.jsonl").write_text(json.dumps({"date": "2026-06-26", "status": 200}) + "\n")
    _csv(thermal_n20.NRT_FILE, [
        {"latitude": 14.01, "longitude": 120.99, "acq_date": "2026-06-30", "acq_time": "500", "frp": "1", "type": ""},  # covered by SP
        {"latitude": 14.01, "longitude": 120.99, "acq_date": "2026-07-02", "acq_time": "500", "frp": "2", "type": ""},
    ])
    s = thermal_n20.series_by_volcano([TAAL])["taal"][thermal_n20.SERIES_ID]
    assert s["source"] == ["firms-viirs-noaa20"] and s["start"] == "2018-04-01"
    assert s["rows"] == [["2026-06-28", 2, 1, 9.0], ["2026-07-02", 1, None, 2.0]]
    assert "provisional" in s["note"]["en"]
    assert s["end"] == "2026-07-02"  # no recent.json yet: the tail file's newest day
    (thermal_n20.NRT_FILE.with_name("recent.json")).write_text(json.dumps({"from": "2026-07-01", "sp_to": "2026-06-30", "to": "2026-07-05"}))
    assert thermal_n20.series_by_volcano([TAAL])["taal"][thermal_n20.SERIES_ID]["end"] == "2026-07-05"
    thermal_n20.NRT_FILE.unlink()
    thermal_n20.NRT_FILE.with_name("recent.json").unlink()
    assert thermal_n20.series_by_volcano([TAAL])["taal"][thermal_n20.SERIES_ID]["end"] == "2026-06-30"  # standard coverage only


def test_omi_reduce_and_series(tmp_path, monkeypatch):
    p = tmp_path / "OMSO2e.004_OMI-Aura_L3-OMSO2e_2020m0112_v004-2025m0926t155820_subsetted.nc4"
    lats = np.arange(13.125, 15.0, 0.25)
    lons = np.arange(120.125, 122.0, 0.25)
    so2 = np.full((len(lats), len(lons)), 0.5, dtype="f4")
    cf = np.zeros_like(so2)
    so2[3, 3] = 2.5
    cf[3, 4] = 0.8  # cloudy: excluded
    so2[4, 3] = -1.2676506e30  # fill
    with h5py.File(p, "w") as f:
        g = f.create_group(omi.GRID)
        g["YDim"], g["XDim"] = lats, lons
        d = g.create_dataset("Data_Fields/ColumnAmountSO2", data=so2)
        d.attrs["ValidRange"] = np.array([-10.0, 2000.0], dtype="f4")
        g.create_dataset("Data_Fields/CloudRadianceFraction", data=cf)
    rows = omi.reduce_file(p, [TAAL])
    assert len(rows) == 1
    r = rows[0]
    assert r["date"] == "2020-01-12" and r["total"] == 16 and r["valid"] == 14 and r["so2_du_max"] == 2.5

    monkeypatch.setattr(omi, "OUT", tmp_path / "omi")
    omi._merge(2020, rows)
    s = omi.series_by_volcano("2026-10-22")["taal"][omi.SERIES_ID]
    assert s["start"] == "2020-01-12" and s["unit"] == "DU" and s["coverage"] == [0.875]
    assert s["values"] == [round(r["so2_du_mean"], 2)]
