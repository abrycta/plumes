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


def test_wp_bulusan_2017_and_empty_summary():
    p = FX / "wp" / "bulusan-volcano-bulletin-18-november-2017-8-00-a-m.html"
    r = parse_wp(p.stem, entry(p))
    assert (r["alert"], r["eq"]) == (1, 3) and "inflationary" in r["deform"]
    p = FX / "wp" / "taal-volcano-summary-of-24hr-observation-19-january-2022-5-00-am.html"
    assert parse_wp(p.stem, entry(p)) is None


def test_slug_meta_variants():
    assert wp_slug_meta("taal-volcano-bulletin-update-12-january-2020-04-00-pm-2")["date"] == "2020-01-12"
    assert wp_slug_meta("hibok-hibok-volcano-advisory-may-3-2018")["volcano"] == "hibok-hibok"


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
