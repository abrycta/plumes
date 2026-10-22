import pathlib

from plumes.parse import parse_lava, parse_vaac, parse_wp, wp_slug_meta

FX = pathlib.Path(__file__).resolve().parents[2] / "spike" / "fixtures"


def entry(p):
    h = p.read_text(errors="ignore")
    i = h.find("entry-content")
    return h[i:h.find("sharedaddy", i)]


def test_wp_taal_13_january_2020():
    p = FX / "wp" / "taal-volcano-bulletin-13-january-2020-8-00-a-m.html"
    r = parse_wp("https://www.phivolcs.dost.gov.ph/" + p.stem + "/", entry(p))
    assert (r["volcano"], r["date"], r["hour"], r["alert"], r["eq"]) == ("taal", "2020-01-13", 8, 4, 75)


def test_wp_alert_change_notice_reports_the_new_level():
    # taal-volcano-bulletin-12-january-2020-07-30-pm and its 4:00 PM predecessor (crawled entry-content, shortened)
    url = "https://www.phivolcs.dost.gov.ph/taal-volcano-bulletin-12-january-2020-07-30-pm/"
    html = ('<p>This serves as notice for the raising of the alert status of Taal from <strong>Alert Level 3</strong> <strong>(magmatic '
            'unrest) to </strong><strong>Alert Level 4 (hazardous eruption imminent)</strong>. As of 5:30 PM PST (1730H), eruptive '
            'activity intensified.</p><p>DOST-PHIVOLCS is now raising the alert status of Taal from Alert Level 3 to Alert Level 4.</p>')
    r = parse_wp(url, html)
    assert (r["date"], r["hour"], r["minute"], r["alert"], r["filipino"]) == ("2020-01-12", 19, 30, 4, False)
    lowered = "PHIVOLCS is lowering the alert status of Taal from Alert Level 2 (increasing unrest) to Alert Level 1 (abnormal)."
    assert parse_wp("taal-volcano-bulletin-19-march-2020-8-00-a-m", f"<p>{lowered} {lowered}</p>")["alert"] == 1


def test_wp_running_total_is_not_a_bulletin_count():
    t = ("This is to notify the public and concerned authorities on the current activity of Taal Volcano. Since raising the alert level "
         "of Taal Volcano to Alert Level 1 last March 28, 2019, the Taal Volcano seismic network has recorded 4857 volcanic earthquakes "
         "as of today (December 1, 2019).")
    r = parse_wp("taal-volcano-advisory-01-december-2019-08-00-am", f"<p>{t}</p>")
    assert (r["alert"], r["eq"]) == (1, None)


def test_wp_bulusan_2017_and_empty_summary():
    p = FX / "wp" / "bulusan-volcano-bulletin-18-november-2017-8-00-a-m.html"
    r = parse_wp(p.stem, entry(p))
    assert (r["alert"], r["eq"]) == (1, 3) and "inflationary" in r["deform"]
    p = FX / "wp" / "taal-volcano-summary-of-24hr-observation-19-january-2022-5-00-am.html"
    assert parse_wp(p.stem, entry(p)) is None


def test_slug_meta_variants():
    assert wp_slug_meta("taal-volcano-bulletin-update-12-january-2020-04-00-pm-2")["date"] == "2020-01-12"
    assert wp_slug_meta("hibok-hibok-volcano-advisory-may-3-2018")["volcano"] == "hibok-hibok"
    assert wp_slug_meta("taal-volcano-bulletin-26-enero-2020-8-00-am")["date"] == "2020-01-26"
    assert wp_slug_meta("taal-volcano-bulletin-1-octobber-2019-8-00-a-m")["date"] == "2019-10-01"


def test_lava():
    r = parse_lava((FX / "lava" / "1259.html").read_text())
    assert r["date"] == "2022-07-02" and r["alert"] == 2 and r["so2"] == 1333 and r["so2_date"] == "2022-07-01" and r["plume_m"] == 900
    r = parse_lava((FX / "lava" / "16917.html").read_text())
    assert r["date"] == "2026-10-21" and r["so2"] == 1002


def test_vaac():
    r = parse_vaac((FX / "vaac" / "20200112_27307000_0003_Text.html").read_text())
    assert r["dtg"] == "2020-01-12T09:00:00Z" and r["top_fl"] == 550 and r["basis"] == "observed" and r["gvp"] == 273070
    r = parse_vaac((FX / "vaac" / "20200112_27307000_0001_Text.html").read_text())
    assert r["basis"] == "reported" and r["top_fl"] == 50
