"""FIRMS (MODIS_SP, VIIRS_SNPP_SP) and Earth Engine fire series: partial windows stay gaps, never zero."""

import csv
import datetime as dt
import json

from plumes import coverage, firms, readmodels

HEAD = "latitude,longitude,acq_date,acq_time,satellite,instrument,confidence,frp,daynight,type"


class _Resp:
    def __init__(self, text):
        self.text, self.status_code, self.content = text, 200, text.encode()


class _Fake:
    """FIRMS stand-in: product available to `max_date`; each window returns one detection on its first and last day."""

    def __init__(self, max_date):
        self.max_date, self.asked = max_date, []

    def __call__(self, *a, **k):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def get(self, url):
        if "data_availability" in url:
            return _Resp(f"data_id,min_date,max_date\nMODIS_SP,2000-11-01,{self.max_date}\n")
        d = dt.date.fromisoformat(url.rsplit("/", 1)[1])
        self.asked.append(d.isoformat())
        days = [x for x in (d, d + dt.timedelta(days=4)) if x.isoformat() <= self.max_date]
        return _Resp("\n".join([HEAD, *(f"14.0,121.0,{x},100,T,MODIS,80,5.0,D,0" for x in days)]))


def _setup(tmp_path, monkeypatch, max_date):
    fake = _Fake(max_date)
    monkeypatch.setenv("FIRMS_MAP_KEY", "k")
    monkeypatch.setattr(firms, "OUT", tmp_path / "firms")
    monkeypatch.setattr(firms, "Polite", fake)
    return fake


def _dates(path):
    with path.open() as f:
        return [r["acq_date"] for r in csv.DictReader(f)]


def test_crawl_skips_a_window_the_product_only_partly_covers(tmp_path, monkeypatch):
    fake = _setup(tmp_path, monkeypatch, "2001-01-06")
    firms.crawl(["MODIS_SP"], "2000-12-20")
    # 2001-01-05 ends on 2001-01-09, after the product's last day: never fetched, never recorded as done
    assert fake.asked == ["2000-12-21", "2000-12-26", "2000-12-31"]
    assert firms.covered_to("MODIS_SP") == "2001-01-04"


def test_crawl_files_rows_by_acquisition_year(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, "2001-01-06")
    firms.crawl(["MODIS_SP"], "2000-12-30")
    out = tmp_path / "firms" / "MODIS_SP"
    assert _dates(out / "2000.csv") == ["2000-12-31"]
    assert _dates(out / "2001.csv") == ["2001-01-04"]


def test_crawl_refetches_a_legacy_partial_window_without_doubling_rows(tmp_path, monkeypatch):
    out = tmp_path / "firms" / "MODIS_SP"
    out.mkdir(parents=True)
    (out / "2000.csv").write_text(f"{HEAD}\n14.0,121.0,2000-12-31,100,T,MODIS,80,5.0,D,0\n14.0,121.0,2000-12-01,100,T,MODIS,80,5.0,D,0\n")
    # recorded by the old crawler on 2001-01-02, when the product reached only 2000-12-31
    (out / "windows.jsonl").write_text(json.dumps({"date": "2000-12-31", "status": 200, "fetched": "2001-01-02T00:00:00Z", "rows": 1}) + "\n")
    fake = _setup(tmp_path, monkeypatch, "2001-01-06")
    firms.crawl(["MODIS_SP"], "2000-12-30")
    assert fake.asked == ["2000-12-31"]
    assert sorted(_dates(out / "2000.csv")) == ["2000-12-01", "2000-12-31"]
    assert _dates(out / "2001.csv") == ["2001-01-04"]


def test_ee_fire_month_complete_only_when_every_source_covers_it():
    full = {s: ["2026-08-01", "2026-08-31"] for s in coverage.FIRE_SOURCES}
    today = dt.date(2026, 10, 23)
    assert coverage.fire_month_complete("2026-08", full, today)
    assert not coverage.fire_month_complete("2026-08", full | {"modis-mod14a1": ["2026-08-01", "2026-08-10"]}, today)
    assert not coverage.fire_month_complete("2026-08", None)  # legacy table, recent: re-run
    assert coverage.fire_month_complete("2020-01", None)  # legacy table, long settled


def test_fire_series_end_where_coverage_ends(tmp_path):
    t = tmp_path / "ee-fire"
    t.mkdir()
    for m in ("2020-01", "2026-08", "2026-09"):
        (t / f"{m}.csv").write_text("volcano,ring,date,source,n,max_frp_mw\n")
    (t / "2026-08.coverage.json").write_text(json.dumps({"modis-mod14a1": ["2026-08-01", "2026-08-10"], "viirs-vnp14a1": ["2026-08-01", "2026-08-31"], "firms-modis": []}))
    rows = [{"volcano": "taal", "ring": "15km", "date": "2026-09-09", "source": "viirs-vnp14a1", "n": "1", "max_frp_mw": "4"}]
    ends = coverage.fire_ends(t, rows)
    # MODIS stops on its last covered day; a legacy month without coverage counts only up to its last detection
    assert ends == {"modis-mod14a1": "2026-08-10", "viirs-vnp14a1": "2026-09-09", "firms-modis": "2020-01-31"}
    s = readmodels.fire_series("taal", rows, ends)
    assert s["frp_modis_15km"]["end"] == "2026-08-10" and s["frp_viirs_15km"]["end"] == "2026-09-09"


def test_thermal_layer_months_follow_the_detections_not_the_yearly_files():
    by_year = {"2000": [("MODIS_SP", {"acq_date": "2000-11-02"})], "2026": [("MODIS_SP", {"acq_date": "2026-07-31"})]}
    assert readmodels.thermal_time(by_year, "2026-10-22") == {"step": "month", "start": "2000-11", "end": "2026-07"}
