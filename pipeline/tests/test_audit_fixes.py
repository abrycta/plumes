"""Audit 2026-10-23 fixes: delta windows that survive gaps (M7), revisable facts warn (M6), GVP drift is not a reject (L1)."""

import datetime as dt

from plumes import readmodels, sources
from plumes.crawl import lava, vaac


def test_lava_window_reaches_back_over_a_gap():
    today = dt.date(2026, 12, 20)
    assert lava.auto_since([{"date": "2026-10-23"}, {"date": "2026-10-01"}], today) == "2026-10-16"  # 58-day gap: re-indexed
    assert lava.auto_since([{"date": "2026-12-19"}], today) == "2026-11-29"  # weekly run: the usual 21 days
    assert lava.auto_since([], today) == lava.FIRST


def test_vaac_refreshes_last_year_in_january():
    assert vaac.refresh_from(dt.date(2027, 1, 4)) == 2026
    assert vaac.refresh_from(dt.date(2027, 2, 1)) == 2027


def test_warning_checks_never_block():
    checks = [{"check": "Taal 2020-01-12: GVP VEI 4", "passed": False, "severity": "warning"}, {"check": "schema", "passed": True}]
    assert readmodels.blocking(checks) == []
    assert readmodels.blocking(checks + [{"check": "schema x", "passed": False}]) == [{"check": "schema x", "passed": False}]


def test_gvp_drift_warns_but_a_wrong_file_is_rejected(tmp_path, monkeypatch):
    xwalk = tmp_path / "volcanoes.csv"
    xwalk.write_text("id,gvp_number\na,273010\nb,273020\nc,273030\nd,\n")
    monkeypatch.setattr(sources, "CROSSWALK", xwalk)
    wfs = tmp_path / "gvp.csv"
    wfs.write_text("Volcano_Number\n273010\n273020\n273099\n")
    assert sources.check_gvp_volcanoes(wfs, {}) == []  # one renumbered: drift
    wfs.write_text("Volcano_Number\n273010\n")
    assert sources.check_gvp_volcanoes(wfs, {}) != []


def test_wp_slugs_match_after_2029():
    from plumes.crawl import wp

    assert wp.wanted("https://www.phivolcs.dost.gov.ph/taal-volcano-bulletin-14-march-2031/")
    assert wp.wanted("https://www.phivolcs.dost.gov.ph/taal-volcano-bulletin-13-january-2020/")
    assert not wp.wanted("https://www.phivolcs.dost.gov.ph/taal-volcano-bulletin-13-january-2016/")


def test_unknown_crawler_terms_are_reported_not_dropped_silently():
    from plumes.crawl import lava, wp

    assert wp.unknown_volcano("https://www.phivolcs.dost.gov.ph/apo-volcano-bulletin-2-may-2031/")
    assert not wp.unknown_volcano("https://www.phivolcs.dost.gov.ph/taal-volcano-bulletin-2-may-2031/")
    html = '<option value="571">Bulusan</option><option value="580">Taal</option><option value="599">Apo</option>'
    assert lava.unknown_volcanoes(html) == {599: "Apo"}
