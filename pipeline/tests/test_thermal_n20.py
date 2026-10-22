"""NOAA-20 thermal series on small synthetic inputs."""

import csv
import json

from plumes import thermal_n20

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
