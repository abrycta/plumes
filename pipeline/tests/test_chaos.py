"""Chaos tests (audit 2026-10-23, P1-P17): malformed answers, moved or changed sources, dead sources. Mocked HTTP and
local git repositories only; nothing here touches live data."""

import datetime as dt
import json
import subprocess
import sys

import httpx
import pytest

from plumes import archive_tags, coverage, firms, freshness, health, nasa, publish, sources, stage, thermal_n20
from plumes.crawl import lava, records, vaac, wp
from plumes.deeptime import check_hazel
from plumes.sources import SchemaError

HEAD = "latitude,longitude,acq_date,acq_time,satellite,instrument,confidence,frp,daynight,type"


# ---------------------------------------------------------------- P2: hooks reject broken files (A1)

def _hazel(i, n=273030, y=1900):
    return {"id": i, "volcanoLocationNewNum": n, "year": y}


@pytest.mark.parametrize("body,match", [
    ("Volcano_Number,Volcano_Name,Eruption_Number,ExplosivityIndexMax\n999999,X,1,2\n", "Philippine range"),
    ("Volcano_Number,Volcano_Name,Eruption_Number,ExplosivityIndexMax\n273030,Taal,1,9\n", "VEI"),
    ("<html><body>Service unavailable</body></html>\n", "expected columns"),
    ("", "expected columns"),
])
def test_gvp_eruptions_hook_rejects(tmp_path, body, match):
    p = tmp_path / "e.csv"
    p.write_text(body)
    with pytest.raises(SchemaError, match=match):
        sources.check_gvp_eruptions(p, {})


def test_usgs_hook_rejects_foreign_events_and_renamed_columns(tmp_path):
    p = tmp_path / "u.csv"
    p.write_text("time,latitude,longitude,id\n2020-01-12T00:00:00Z,45,-100,us1\n")
    with pytest.raises(SchemaError, match="outside the Philippine box"):
        sources.check_usgs(p, {})
    p.write_text("time,lat,lon,id\n2020-01-12T00:00:00Z,14,121,us1\n")  # renamed columns (A3)
    with pytest.raises(SchemaError, match="expected columns"):
        sources.check_usgs(p, {})
    p.write_text("time,latitude,longitude,id\n2020-01-12T00:00:00Z,14,121,us1\n")
    assert sources.check_usgs(p, {}) == []


def test_hazel_hook_rejects_a_partial_page_and_a_non_page(tmp_path):
    p = tmp_path / "h.json"
    p.write_text(json.dumps({"items": [_hazel(i) for i in range(12)], "totalPages": 5, "totalItems": 50}))
    with pytest.raises(SchemaError, match="paged"):
        check_hazel(p, {})
    p.write_text("<html>maintenance</html>")
    with pytest.raises(SchemaError, match="not a HazEL page"):
        check_hazel(p, {})
    p.write_text(json.dumps({"items": {"a": 1}}))
    with pytest.raises(SchemaError, match="not a HazEL page"):
        check_hazel(p, {})


def test_kit_validate_file_rejects_through_the_hooks(tmp_path):
    """The kit contract itself (formats.validate_file): the hook's SchemaError rejects the file."""
    archivekit = pytest.importorskip("archivekit")
    from plumes.paths import PIPELINE, REGISTRY

    reg = archivekit.load_registry(REGISTRY, root=PIPELINE)
    p = tmp_path / "e.csv"
    p.write_text("Volcano_Number,Volcano_Name,Eruption_Number,ExplosivityIndexMax,StartDateYear,EndDateYear\n999999,X,1,9,2020,2020\n")
    src = reg.source("gvp-eruptions-ph") | {"checks": {}}
    with pytest.raises(archivekit.SchemaError):
        archivekit.validate_file(p, src)
    h = tmp_path / "h.json"
    h.write_text(json.dumps({"items": [_hazel(i) for i in range(12)], "totalPages": 5, "totalItems": 50}))
    with pytest.raises(archivekit.SchemaError):
        archivekit.validate_file(h, reg.source("noaa-hazel-volcanoes-ph") | {"checks": {}})


# ---------------------------------------------------------------- P4: FIRMS 200 answers that are not CSVs (A1, A3)

class _Resp:
    def __init__(self, text, status=200, headers=None):
        self.text, self.status_code, self.content, self.headers = text, status, text.encode(), headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(str(self.status_code), request=None, response=None)


class _Firms:
    def __init__(self, body, products="MODIS_SP"):
        self.body, self.products = body, products

    def __call__(self, *a, **k):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def get(self, url, **k):
        if "data_availability" in url:
            return _Resp("data_id,min_date,max_date\n" + "".join(f"{p},2000-11-01,2000-11-20\n" for p in self.products.split()))
        return _Resp(self.body)


@pytest.mark.parametrize("body,status", [
    ("<!doctype html><html><body>FIRMS is down for maintenance</body></html>", "not-csv"),
    ('{"error": "quota"}', "not-csv"),
    ("lat,lon,acq_date,acq_time\n14,121,2000-11-01,100", "not-csv"),  # renamed columns
    ("", "empty"),
])
def test_firms_bad_answers_are_errors_not_zero_rows(tmp_path, monkeypatch, body, status):
    monkeypatch.setenv("FIRMS_MAP_KEY", "k")
    monkeypatch.setattr(firms, "OUT", tmp_path / "firms")
    monkeypatch.setattr(firms, "Polite", _Firms(body))
    firms.crawl(["MODIS_SP"])
    log = [json.loads(x) for x in (tmp_path / "firms" / "MODIS_SP" / "windows.jsonl").read_text().splitlines()]
    assert {r["status"] for r in log} == {status}
    assert firms.covered_to("MODIS_SP") is None  # never counted as covered, so fetched again


def test_firms_header_only_answer_is_a_complete_empty_window(tmp_path, monkeypatch):
    monkeypatch.setenv("FIRMS_MAP_KEY", "k")
    monkeypatch.setattr(firms, "OUT", tmp_path / "firms")
    monkeypatch.setattr(firms, "Polite", _Firms(HEAD))
    firms.crawl(["MODIS_SP"])
    assert firms.covered_to("MODIS_SP") == "2000-11-20"


def test_firms_retired_product_is_skipped_not_a_crash(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("FIRMS_MAP_KEY", "k")
    monkeypatch.setattr(firms, "OUT", tmp_path / "firms")
    monkeypatch.setattr(firms, "Polite", _Firms(HEAD, products="VIIRS_SNPP_SP"))
    stats = firms.crawl(["MODIS_SP", "VIIRS_SNPP_SP"])
    assert stats["MODIS_SP"]["windows_fetched"] == 0 and "FIRMS product not listed" in capsys.readouterr().out


def test_noaa20_tail_keeps_the_previous_file_on_a_non_csv_answer(tmp_path, monkeypatch):
    monkeypatch.setattr(thermal_n20, "NRT_FILE", tmp_path / "recent.csv")
    (tmp_path / "recent.csv").write_text("previous\n")
    res = thermal_n20.fetch_tail("k", _Firms("<html>oops</html>"), dt.date(2026, 10, 1), dt.date(2026, 9, 1), dt.date(2026, 10, 3))
    assert res["errors"] == 1 and (tmp_path / "recent.csv").read_text() == "previous\n"


# ---------------------------------------------------------------- P1, P3: publishing when Pages misbehaves (A2)

def _git(*a, cwd):
    return subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True, text=True).stdout


@pytest.fixture
def pages_remote(tmp_path):
    """A bare repository whose gh-pages branch holds data/v5 and data/v6 (the live state)."""
    bare, work = tmp_path / "remote.git", tmp_path / "seed"
    _git("init", "-q", "--bare", "-b", "gh-pages", str(bare), cwd=tmp_path)
    _git("init", "-q", "-b", "gh-pages", str(work), cwd=tmp_path)
    for v in (5, 6):
        (work / "data" / f"v{v}").mkdir(parents=True)
        (work / "data" / f"v{v}" / "manifest.json").write_text("{}")
    (work / "data" / "latest.json").write_text('{"current": "v6"}')
    _git("add", "-A", cwd=work)
    _git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "seed", cwd=work)
    _git("push", "-q", str(bare), "gh-pages", cwd=work)
    return bare


def test_next_version_comes_from_gh_pages_and_aborts_when_latest_is_unreadable(pages_remote, monkeypatch):
    state = pytest.importorskip("plumes.state")  # needs zstandard (sources group)
    monkeypatch.setattr(state, "origin", lambda: str(pages_remote))
    assert publish.remote_versions(str(pages_remote)) == [5, 6]
    monkeypatch.setattr(state.httpx, "get", lambda *a, **k: httpx.Response(503, text="Service Unavailable"))
    assert state.published() is None
    with pytest.raises(SystemExit, match="latest.json unreadable"):
        state.next_version()

    def boom(*a, **k):
        raise httpx.ConnectError("down")
    monkeypatch.setattr(state.httpx, "get", boom)
    with pytest.raises(SystemExit):
        state.next_version()
    monkeypatch.setattr(state.httpx, "get", lambda *a, **k: httpx.Response(200, json={"current": "v6"}))
    assert state.next_version() == 7


def test_next_version_starts_at_1_only_without_a_gh_pages_branch(tmp_path, monkeypatch):
    state = pytest.importorskip("plumes.state")  # needs zstandard (sources group)
    bare = tmp_path / "empty.git"
    _git("init", "-q", "--bare", str(bare), cwd=tmp_path)
    monkeypatch.setattr(state, "origin", lambda: str(bare))
    monkeypatch.setattr(state.httpx, "get", lambda *a, **k: httpx.Response(404))
    assert state.next_version() == 1


def test_publish_never_moves_backwards_or_prunes_newer_versions(pages_remote, tmp_path, monkeypatch):
    build = tmp_path / "build"
    for v in (1, 7):
        (build / "site" / f"v{v}").mkdir(parents=True)
        (build / "site" / f"v{v}" / "manifest.json").write_text("{}")
    monkeypatch.setattr(publish, "BUILD", build)
    monkeypatch.setattr(publish, "PAGES_DIR", tmp_path / "pages")
    monkeypatch.setattr(publish, "EE_LEDGER", tmp_path / "none.json")
    monkeypatch.setattr(publish, "origin", lambda: str(pages_remote))
    (build / "site" / "latest.json").write_text('{"current": "v1"}')
    with pytest.raises(SystemExit, match="newer than v1"):
        publish.pages(1)
    held = _git("ls-tree", "--name-only", "gh-pages", "data/", cwd=pages_remote).split()
    assert held == ["data/latest.json", "data/v5", "data/v6"]
    (build / "site" / "latest.json").write_text('{"current": "v7"}')
    assert publish.pages(7)["pages"] == "pushed"
    held = _git("ls-tree", "--name-only", "gh-pages", "data/", cwd=pages_remote).split()
    assert held == ["data/latest.json", "data/v6", "data/v7"]


def test_git_auth_header_comes_from_github_token_and_is_never_stored(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    assert publish.auth() == []
    monkeypatch.setenv("GITHUB_TOKEN", "tok")
    a = publish.auth()
    assert a[0] == "-c" and a[1].startswith("http.https://github.com/.extraheader=AUTHORIZATION: basic ") and "tok" not in a[1]


# ---------------------------------------------------------------- P6: crawlers on changed or broken answers (A1-A3)

class _Pages:
    """A site stand-in: url substring -> (status, body)."""

    def __init__(self, routes):
        self.routes, self.requests = routes, 0

    def __call__(self, *a, **k):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def get(self, url, params=None, **k):
        self.requests += 1
        for frag, (status, body) in self.routes.items():
            if frag in url:
                return _Resp(body, status)
        return _Resp("not found", 404)


def test_lava_error_page_is_retried_then_given_up(tmp_path, monkeypatch):
    monkeypatch.setattr(lava, "OUT", tmp_path)
    (tmp_path / "index.jsonl").write_text(json.dumps({"volcano": "taal", "vdId": 580, "date": "2026-10-01", "path": "activity-vb", "bid": 7}) + "\n")
    monkeypatch.setattr(lava, "Polite", _Pages({"bid=7": (200, "<html>Please log in</html>")}))
    assert lava.fetch()["unparsed"] == 1
    for _ in range(records.PARSE_RETRIES - 1):
        assert lava.fetch()["fetched"] == 1  # retried on the next runs
    assert lava.fetch()["fetched"] == 0  # given up after PARSE_RETRIES, with a warning


def test_lava_index_with_a_changed_search_page_fails_the_stage(tmp_path, monkeypatch):
    monkeypatch.setattr(lava, "OUT", tmp_path)
    monkeypatch.setattr(lava, "Polite", _Pages({"list-of-bulletin": (200, "<html>new layout</html>")}))
    res = lava.index("2026-09-01", "2026-09-30")
    assert res["rows"] == 0 and res["days"] >= lava.EMPTY_INDEX_DAYS
    with pytest.raises(SystemExit, match="search answer changed"):
        lava.require_rows(res)


def test_wp_empty_sitemap_keeps_the_previous_list(tmp_path, monkeypatch):
    monkeypatch.setattr(wp, "OUT", tmp_path)
    (tmp_path / "list.tsv").write_text("https://x/taal-volcano-bulletin-2026/\t2026-10-01\n")
    idx = '<?xml version="1.0"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><sitemap><loc>https://x/wp-sitemap-pages-1.xml</loc></sitemap></sitemapindex>'
    monkeypatch.setattr(wp, "Polite", _Pages({"wp-sitemap.xml": (200, idx)}))
    with pytest.raises(SystemExit, match="listed no English bulletin"):
        wp.crawl()
    assert (tmp_path / "list.tsv").read_text().startswith("https://x/taal")


def test_wp_page_without_a_post_body_is_retried(tmp_path, monkeypatch):
    monkeypatch.setattr(wp, "OUT", tmp_path)
    post = "https://x/taal-volcano-bulletin-12-january-2026-0800-am/"
    idx = '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><sitemap><loc>https://x/wp-sitemap-posts-post-1.xml</loc></sitemap></sitemapindex>'
    sm = f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{post}</loc><lastmod>2026-01-12</lastmod></url></urlset>'
    monkeypatch.setattr(wp, "Polite", _Pages({"wp-sitemap.xml": (200, idx), "posts-post-1": (200, sm), "taal-volcano": (200, "<html>Just a moment...</html>")}))
    assert wp.crawl()["unparsed"] == 1
    assert wp.crawl()["fetched"] == 1  # not stored as done


def test_vaac_year_list_404_is_read_again(tmp_path, monkeypatch):
    monkeypatch.setattr(vaac, "OUT", tmp_path)
    monkeypatch.setattr(vaac, "Polite", _Pages({"_vaac_list": (404, "gone")}))
    assert 2024 in vaac.crawl(2024, refresh_lists_from=2100)["bad_lists"]
    good = '<a href="TextData/2024/20240101_27307000_0001_Text.html">Taal</a>'
    pages = _Pages({"2024_vaac_list": (200, good), "_vaac_list": (200, '<a href="TextData/x/1_25000000_0001_Text.html">'),
                    "_Text.html": (200, "DTG: 20240101/0000Z")})
    monkeypatch.setattr(vaac, "Polite", pages)
    res = vaac.crawl(2024, refresh_lists_from=2100)
    assert res["bad_lists"] == [] and res["listed"] == 1


# ---------------------------------------------------------------- P7: one dead source never stops the run (A4)

def test_stage_failure_warns_and_goes_on(capsys, monkeypatch):
    monkeypatch.setattr(health, "_reporter", lambda: None)
    assert stage.run("dead-source", ["plumes.nonexistent_module"]) != 0
    assert "::warning title=stage dead-source::" in capsys.readouterr().out
    assert stage.run("ok", ["json.tool", "--help"]) == 0


def test_stage_cli_exits_zero_on_a_failing_stage(tmp_path):
    from plumes.paths import PIPELINE
    r = subprocess.run([sys.executable, "-m", "plumes.stage", "dead", "plumes.nonexistent_module"], cwd=PIPELINE,
                       capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", "ARCHIVEKIT_REPORT_ISSUES": "0"})
    assert r.returncode == 0 and "::warning title=stage dead::" in r.stdout


def test_budget_exceeded_is_a_planned_stop(monkeypatch, capsys):
    ee_series = pytest.importorskip("plumes.ee_series")  # needs the ee group
    from plumes.ee_budget import BudgetExceeded

    def over(*a, **k):
        raise BudgetExceeded("month at 50 EECU-h")
    monkeypatch.setattr(ee_series, "init", lambda: None)
    monkeypatch.setattr(ee_series, "run_monthly", over)
    monkeypatch.setattr(ee_series.Budget, "save", lambda self, label: {})
    ee_series.main(["so2"])  # no exception
    assert "Earth Engine budget reached" in capsys.readouterr().out


# ---------------------------------------------------------------- P8, P11: newest archive snapshot (A3, A4)

def test_newest_tag_by_date_and_sequence():
    tags = ["firms-modis-2026-10-23", "firms-modis-2026-10-22", "firms-modis-2026-10-23.10", "firms-modis-2026-10-23.2",
            "firms-modis-x-2027-01-01", "staging-firms-modis-2028-01-01"]
    assert archive_tags.newest(tags, "firms-modis") == "firms-modis-2026-10-23.10"
    assert archive_tags.newest(tags[:2], "firms-modis") == "firms-modis-2026-10-23"
    assert archive_tags.newest(tags, "worldpop-100m") is None


def test_restore_fails_when_a_bundle_is_missing(monkeypatch):
    state = pytest.importorskip("plumes.state")  # needs zstandard (sources group)
    monkeypatch.setattr(state, "list_tags", lambda repo: ["phivolcs-bulletins-2026-10-21"])
    with pytest.raises(SystemExit, match="archive bundles missing"):
        state.restore()


def test_api_load_picks_the_newest_snapshot():
    """The api-load workflow's shell selection (grep + sort -V) agrees with archive_tags.newest."""
    tags = "firms-modis-2026-10-23\nfirms-modis-2026-10-22\nfirms-modis-2026-10-23.10\nfirms-modis-2026-10-23.2\nfirms-modis-x-2027-01-01\n"
    sh = r'grep -E "^firms-modis-[0-9]{4}-[0-9]{2}-[0-9]{2}(\.[0-9]+)?$" | sort -V | tail -n 1'
    out = subprocess.run(["bash", "-c", sh], input=tags, capture_output=True, text=True, check=True).stdout.strip()
    assert out == archive_tags.newest(tags.split(), "firms-modis")


# ---------------------------------------------------------------- P10, P12: stopped collections and late days (A3, A4)

def test_a_stopped_fire_collection_settles_instead_of_rerunning_forever():
    no_modis = {"modis-mod14a1": [], "viirs-vnp14a1": [], "firms-modis": ["2027-03-01", "2027-03-31"]}
    assert not coverage.fire_month_complete("2027-03", no_modis, dt.date(2027, 4, 15))  # may still arrive
    assert coverage.fire_month_complete("2027-03", no_modis, dt.date(2027, 9, 1))  # settled: MOD14A1 has ended


def test_so2_month_reruns_until_late_days_arrive():
    part = {"s5p-offl-so2": ["2026-09-01", "2026-09-27"]}
    assert not coverage.so2_month_complete("2026-09", part, dt.date(2026, 10, 23))
    assert coverage.so2_month_complete("2026-09", {"s5p-offl-so2": ["2026-09-01", "2026-09-30"]}, dt.date(2026, 10, 23))
    assert coverage.so2_month_complete("2026-09", part, dt.date(2027, 3, 1))
    assert coverage.so2_month_complete("2026-09", None)  # tables from before the sidecar are kept


def test_reruns_are_capped(tmp_path, monkeypatch):
    ee_series = pytest.importorskip("plumes.ee_series")
    monkeypatch.setattr(ee_series, "TABLES", tmp_path)
    (tmp_path / "ee-fire").mkdir()
    for m in ee_series.months("2026-01", "2026-09"):
        (tmp_path / "ee-fire" / f"{m}.csv").write_text("volcano\n")
        (tmp_path / "ee-fire" / f"{m}.coverage.json").write_text(json.dumps({s: [] for s in coverage.FIRE_SOURCES}))
    monkeypatch.setattr(coverage, "settled", lambda m, today=None: False)
    calls = []
    monkeypatch.setattr(ee_series, "fire_month", lambda m, b: (calls.append(m), ([], {}))[1])
    res = ee_series.run_monthly("fire", "2026-01", "2026-09", type("B", (), {"run_s": 0.0})())
    assert len(calls) == ee_series.MAX_RERUNS and res["months_deferred"] == 9 - ee_series.MAX_RERUNS


# ---------------------------------------------------------------- P13: Earthdata token minted from the login (A2)

def test_earthdata_token_is_minted_then_falls_back(monkeypatch):
    monkeypatch.setenv("EARTHDATA_USERNAME", "u")
    monkeypatch.setenv("EARTHDATA_PASSWORD", "p")
    monkeypatch.setenv("EARTHDATA_TOKEN", "static")
    monkeypatch.setattr(nasa.httpx, "post", lambda *a, **k: httpx.Response(200, json={"access_token": "fresh"}))
    assert nasa.token() == "fresh"
    monkeypatch.setattr(nasa.httpx, "post", lambda *a, **k: httpx.Response(401, text="bad login"))
    assert nasa.token() == "static"


# ---------------------------------------------------------------- P5: stale sources surface internally only (A4)

def test_stale_sources_warn_and_file_an_issue(capsys, monkeypatch):
    filed = []

    class _R:
        def report_problem(self, key, state, summary):
            filed.append(key)
            return "opened"

        def resolve(self, key, note):
            return "none"
    monkeypatch.setattr(health, "_reporter", lambda: _R())
    res = freshness.assess({"phivolcs-lava-bulletins": "2026-08-01", "firms-viirs-noaa20-nrt": "2026-10-22", "vaac-tokyo-advisories": "2025-01-01",
                            "ee-fire-viirs-vnp14a1": "2026-11-02", "usgs-comcat-ph-2010": None}, dt.date(2026, 10, 23))
    assert freshness.alert(res) == ["phivolcs-lava-bulletins", "usgs-comcat-ph-2010"]
    assert filed == ["stale phivolcs-lava-bulletins", "stale usgs-comcat-ph-2010"]
    assert "::warning title=stale phivolcs-lava-bulletins::" in capsys.readouterr().out
