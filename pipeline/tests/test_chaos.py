"""Chaos tests (audit 2026-10-23, P1-P17): malformed answers, moved or changed sources, dead sources. Mocked HTTP and
local git repositories only; nothing here touches live data."""

import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

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
    p.write_text("time,latitude,longitude,depth,mag,type,id\n2020-01-12T00:00:00Z,45,-100,10,4,earthquake,us1\n")
    with pytest.raises(SchemaError, match="outside the Philippine box"):
        sources.check_usgs(p, {})
    p.write_text("time,lat,lon,depth,mag,type,id\n2020-01-12T00:00:00Z,14,121,10,4,earthquake,us1\n")  # renamed columns (A3)
    with pytest.raises(SchemaError, match="expected columns"):
        sources.check_usgs(p, {})
    p.write_text("time,latitude,longitude,depth,mag,type,id\n2020-01-12T00:00:00Z,14,121,10,4,earthquake,us1\n")
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


def _pages_local(tmp_path, monkeypatch, remote):
    monkeypatch.setattr(publish, "PAGES_DIR", tmp_path / "pages")
    monkeypatch.setattr(publish, "origin", lambda: str(remote))


def test_next_version_comes_from_gh_pages_and_aborts_when_latest_is_unreadable(pages_remote, tmp_path, monkeypatch):
    state = pytest.importorskip("plumes.state")  # needs zstandard (sources group)
    _pages_local(tmp_path, monkeypatch, pages_remote)

    def boom(*a, **k):  # the live site is down: the run doesn't need it (audit A2)
        raise httpx.ConnectError("down")
    monkeypatch.setattr(state.httpx, "get", boom)
    assert publish.remote_versions(str(pages_remote)) == [5, 6]
    assert state.next_version() == 7
    (tmp_path / "pages" / "data" / "latest.json").write_text("<html>oops</html>")  # versions held, pointer unreadable
    with pytest.raises(SystemExit, match="latest.json unreadable"):
        state.next_version()


def test_next_version_starts_at_1_only_without_a_gh_pages_branch(tmp_path, monkeypatch):
    state = pytest.importorskip("plumes.state")  # needs zstandard (sources group)
    bare = tmp_path / "empty.git"
    _git("init", "-q", "--bare", str(bare), cwd=tmp_path)
    _pages_local(tmp_path, monkeypatch, bare)
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


# ================================================================ repair round: the verifier's gaps on PR #70

USGS_HEAD = "time,latitude,longitude,depth,mag,magType,id,place,type,status"


def _usgs(n, start=0, **over):
    rows = []
    for i in range(start, start + n):
        r = {"time": f"2020-01-{1 + i % 28:02d}T00:00:00.000Z", "latitude": "14", "longitude": "121", "depth": "10",
             "mag": "4.1", "magType": "mb", "id": f"us{i}", "type": "earthquake",
             "place": "12 km SSW of Somewhere Philippines " + "x" * 110, "status": "reviewed"} | over  # real rows are about 150 bytes (size bounds)
        rows.append(",".join(r[k] for k in USGS_HEAD.split(",")))
    return USGS_HEAD + "\n" + "\n".join(rows) + "\n"


def test_fetch_files_uses_the_archive_baseline_without_a_local_sidecar(tmp_path, monkeypatch):
    """A1: CI starts from a fresh checkout; the gate's baseline then comes from the newest good archive snapshot."""
    archivekit = pytest.importorskip("archivekit")
    seen = {}

    def fake_fetch(sid, reg, **k):
        seen[sid] = k["previous"]
        return type("P", (), {"link_id": "x", "rows": 1})()
    monkeypatch.setattr(archivekit, "fetch", fake_fetch)
    monkeypatch.setattr(sources, "archive_baseline", lambda reg, sid, client: {"rows": 11595, "archive_tag": f"{sid}-2026-10-21"})
    monkeypatch.setattr(archivekit, "load_registry", lambda *a, **k: _Reg(tmp_path))
    sources.fetch_files(["usgs-comcat-ph-2010"])
    assert seen["usgs-comcat-ph-2010"]["rows"] == 11595
    (tmp_path / "u.csv.provenance.json").write_text("{}")  # a local sidecar wins: the kit reads it itself
    sources.fetch_files(["usgs-comcat-ph-2010"])
    assert seen["usgs-comcat-ph-2010"] is None


class _Reg:
    def __init__(self, root):
        self.root, self.health = root, {}

    def source(self, sid):
        return {"local_path": "u.csv"}


def test_kit_rejects_a_usgs_file_cut_at_a_row_boundary_against_the_baseline(tmp_path):
    """A1: 10,500 complete rows where the archive holds 11,595: inside the row bounds, but a >2% shrink."""
    archivekit = pytest.importorskip("archivekit")
    from plumes.paths import PIPELINE, REGISTRY

    reg = archivekit.load_registry(REGISTRY, root=PIPELINE)
    body = _usgs(10_500)
    client = httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(200, stream=httpx.ByteStream(body.encode()), headers={"content-type": "text/csv"})))
    kw = dict(dest=tmp_path / "u.csv", client=client, reporter=False, allow_archive=False)
    with pytest.raises(archivekit.AllLinksFailed, match="shrink|below"):
        archivekit.fetch("usgs-comcat-ph-2010", reg, previous={"rows": 11595}, **kw)
    assert archivekit.fetch("usgs-comcat-ph-2010", reg, previous={"rows": 10_400}, **kw).rows == 10_500


@pytest.mark.parametrize("over,match", [
    ({"mag": "NaN"}, "magnitude"), ({"mag": "42"}, "magnitude"), ({"depth": "inf"}, "depth"), ({"depth": "9000"}, "depth"),
    ({"time": "1577836800000"}, "bad time"),                    # A3: epoch milliseconds
    ({"type": "Earthquake"}, "type 'earthquake'"),             # A3: a renamed category value
    ({"type": "earthquake (tectonic)"}, "type 'earthquake'"),
])
def test_usgs_hook_rejects_absurd_values_epoch_times_and_renamed_types(tmp_path, over, match):
    p = tmp_path / "u.csv"
    p.write_text(_usgs(20, **over))
    with pytest.raises(SchemaError, match=match):
        sources.check_usgs(p, {})


def test_usgs_hook_rejects_duplicates_and_warns_on_a_new_type(tmp_path, capsys):
    p = tmp_path / "u.csv"
    p.write_text(_usgs(20) + _usgs(20).split("\n", 1)[1])  # every row twice (A1)
    with pytest.raises(SchemaError, match="duplicate ids"):
        sources.check_usgs(p, {})
    p.write_text(_usgs(20) + _usgs(1, start=99, type="sinkhole").split("\n", 1)[1])
    assert sources.check_usgs(p, {}) == []  # 95% earthquakes: accepted
    assert "new event type values ['sinkhole']" in capsys.readouterr().out
    p.write_text(_usgs(5, mag="") + _usgs(5, start=5, mag="-0.5", depth="-3").split("\n", 1)[1])  # magnitude not reported; shallow
    assert sources.check_usgs(p, {}) == []


def test_hazel_hook_rejects_infinite_damage_and_repeated_events(tmp_path):
    p = tmp_path / "h.json"
    items = [_hazel(i) for i in range(40)]
    p.write_text(json.dumps({"items": items[:39] + [items[0] | {"damageMillionsDollars": float("inf")}], "totalPages": 1, "totalItems": 40}))
    with pytest.raises(SchemaError, match="damageMillionsDollars"):
        check_hazel(p, {})
    p.write_text(json.dumps({"items": items[:1] * 40, "totalPages": 1, "totalItems": 40}))
    with pytest.raises(SchemaError, match="duplicate ids"):
        check_hazel(p, {})
    p.write_text(json.dumps({"items": items, "totalPages": 1, "totalItems": 40}))
    assert check_hazel(p, {}) == []


def test_gvp_eruptions_hook_rejects_repeated_eruptions(tmp_path):
    p = tmp_path / "e.csv"
    p.write_text("Volcano_Number,Volcano_Name,Eruption_Number,ExplosivityIndexMax\n273030,Taal,1,2\n273030,Taal,1,2\n")
    with pytest.raises(SchemaError, match="duplicate ids"):
        sources.check_gvp_eruptions(p, {})


def test_published_files_never_hold_nan(tmp_path):
    """A1: a NaN that slips past the hooks becomes null (fnum) or fails the build (dumps, strict JSON check)."""
    rm = pytest.importorskip("plumes.readmodels")
    assert rm.fnum("NaN") is None and rm.fnum("inf") is None and rm.fnum("4.5") == 4.5
    with pytest.raises(ValueError):
        rm.dumps({"maxMag": float("nan")})
    v = tmp_path / "v7"
    (v / "volcano").mkdir(parents=True)
    (v / "layers.json").write_text(json.dumps({"dataAsOf": "2001-06-01"}))
    (v / "layers" / "thermal").mkdir(parents=True)
    (v / "layers" / "thermal" / "2000.pmtiles").write_text("")
    (v / "volcano" / "taal.json").write_text('{"rows": [["2020-01-12", 3, NaN]]}')
    res = []
    rm.file_checks(lambda name, ok, detail="", warn=False: res.append((name, ok, warn)), v)
    assert ("strict JSON volcano/taal.json", False, False) in res


def test_usgs_loader_counts_a_repeated_event_once(tmp_path, monkeypatch):
    rm = pytest.importorskip("plumes.readmodels")
    (tmp_path / "usgs").mkdir()
    (tmp_path / "usgs" / "usgs-comcat-ph-1900-2009.csv").write_text(_usgs(3))
    (tmp_path / "usgs" / "usgs-comcat-ph-2010.csv").write_text(_usgs(3) + _usgs(3).split("\n", 1)[1])
    monkeypatch.setattr(rm, "RAW", tmp_path)
    assert len(rm.load_usgs()) == 3


def _checks(fn, *a):
    res = []
    fn(lambda name, ok, detail="", warn=False: res.append({"check": name, "passed": bool(ok), "warn": warn}), *a)
    return {r["check"]: r for r in res}


def test_counts_may_not_shrink_from_the_previous_version():
    """A1/A3: a cut file or a renamed type drops records; blocked against the previous version's manifest counts."""
    rm = pytest.importorskip("plumes.readmodels")
    prev = {"checks": {"counts": {"USGS earthquakes": 27_333, "GVP eruptions": 233}}}
    r = _checks(rm.counts_check, {"USGS earthquakes": 19_000, "GVP eruptions": 233}, prev)
    assert not r["USGS earthquakes: at least 98% of the previous version"]["passed"]
    assert r["GVP eruptions: at least 98% of the previous version"]["passed"]
    r = _checks(rm.counts_check, {"USGS earthquakes": 0}, None)  # no previous counts yet (v6): only "not empty"
    assert list(r) == ["USGS earthquakes: not empty"] and not r["USGS earthquakes: not empty"]["passed"]


def test_thermal_years_after_every_firms_product_stopped_warn_instead_of_blocking(tmp_path):
    """A4: no detections at all in the last year(s) (every product gone) never blocks every later build."""
    rm = pytest.importorskip("plumes.readmodels")
    v = tmp_path / "v9"
    (v / "layers" / "thermal").mkdir(parents=True)
    (v / "layers.json").write_text(json.dumps({"dataAsOf": "2028-01-05"}))
    for y in [*range(2000, 2015), *range(2016, 2027)]:  # 2015 is a hole; 2027 has nothing
        (v / "layers" / "thermal" / f"{y}.pmtiles").write_text("")
    r = _checks(rm.file_checks, v)
    assert not r["thermal detections: one tileset per year 2000 onward"]["passed"]  # the hole still blocks
    tail = r["thermal detections: no year without any detection at the end"]
    assert not tail["passed"] and tail["warn"]
    (v / "layers" / "thermal" / "2015.pmtiles").write_text("")
    assert _checks(rm.file_checks, v)["thermal detections: one tileset per year 2000 onward"]["passed"]
    for p in (v / "layers" / "thermal").glob("*"):
        p.unlink()
    assert not _checks(rm.file_checks, v)["thermal detections: one tileset per year 2000 onward"]["passed"]  # no tileset at all


@pytest.mark.parametrize("body", [HEAD + "\n13.25,123.6", HEAD + "\n13.25,123.6,2000-11-0", HEAD + "\n13.2,123.6,2000-11-01,100,T,MODIS,80,5.1,D,0,extra"])
def test_firms_answer_cut_mid_row_is_an_error_and_fetched_again(tmp_path, monkeypatch, body):
    with pytest.raises(firms.NotFirmsCsv, match="incomplete"):
        firms.rows_of(body)
    monkeypatch.setenv("FIRMS_MAP_KEY", "k")
    monkeypatch.setattr(firms, "OUT", tmp_path / "firms")
    monkeypatch.setattr(firms, "Polite", _Firms(body))
    firms.crawl(["MODIS_SP"])
    assert firms.covered_to("MODIS_SP") is None
    ok = HEAD + "\n13.2,123.6,2000-11-01,100,T,MODIS,80,5.1,D,0"  # no trailing newline: FIRMS's normal answer
    assert firms.rows_of(ok)[0]["frp"] == "5.1"


def test_firms_rate_limit_stops_the_stage_within_its_budget(tmp_path, monkeypatch, capsys):
    """A2: 'transaction limit' on every call stops after 2 windows instead of 3 x 10 min per window."""
    clock = [0.0]
    monkeypatch.setattr(firms.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(firms.time, "sleep", lambda s: clock.__setitem__(0, clock[0] + s))
    monkeypatch.setenv("FIRMS_MAP_KEY", "k")
    monkeypatch.setattr(firms, "OUT", tmp_path / "firms")
    f = _Firms("Exceeding allowed transaction limit.")
    f.products = "MODIS_SP"
    monkeypatch.setattr(firms, "Polite", f)
    st = firms.crawl(["MODIS_SP"])["MODIS_SP"]
    assert st["stopped"] == "rate-limited" and st["windows_failed"] == 2
    assert clock[0] <= firms.BUDGET_S
    assert "FIRMS stopped early" in capsys.readouterr().out


def _bundle(sid, files: dict[str, bytes]):
    import hashlib
    import io
    import tarfile

    zstandard = pytest.importorskip("zstandard")
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w") as tar:
        for name, data in files.items():
            ti = tarfile.TarInfo(name)
            ti.size = len(data)
            tar.addfile(ti, io.BytesIO(data))
    comp = zstandard.ZstdCompressor().compress(raw.getvalue())
    man = {"raw_sha256": hashlib.sha256(raw.getvalue()).hexdigest(), "compressed_sha256": hashlib.sha256(comp).hexdigest(),
           "members": [{"path": n, "sha256": hashlib.sha256(d).hexdigest()} for n, d in files.items()]}
    return comp, man


def _fake_gh(releases):
    """`gh release download <tag> -p <sid>.tar.zst -p manifest.json -D <dir>` over {tag: (asset bytes|None, manifest)}."""
    def run(cmd, **k):
        tag, d = cmd[3], cmd[cmd.index("-D") + 1]
        asset, man = releases[tag]
        sid = cmd[cmd.index("-p") + 1]
        if asset is None:
            return subprocess.CompletedProcess(cmd, 1, "", "no assets match the file pattern")
        (Path(d) / sid).write_bytes(asset)
        (Path(d) / "manifest.json").write_text(json.dumps(man))
        return subprocess.CompletedProcess(cmd, 0, "", "")
    return run


def test_restore_falls_back_to_an_older_good_tag(tmp_path, monkeypatch):
    """A4: a corrupt or missing newest bundle no longer blocks every run; members are checked against manifest.json."""
    state = pytest.importorskip("plumes.state")
    good, gman = _bundle("x", {"raw/x/pages.jsonl": b'{"a": 1}\n'})
    newer, nman = _bundle("x", {"raw/x/pages.jsonl": b'{"a": 2}\n'})
    reports = []
    monkeypatch.setattr(state.health, "report", lambda key, st, summary: reports.append((key, st)))
    monkeypatch.setattr(state.health, "resolve", lambda key, note: None)
    tags = ["x-2026-10-01", "x-2026-10-08", "x-2026-10-08.2"]
    rel = {"x-2026-10-08.2": (newer[:-20] + b"\0" * 20, nman), "x-2026-10-08": (None, gman), "x-2026-10-01": (good, gman)}
    monkeypatch.setattr(state.subprocess, "run", _fake_gh(rel))
    assert state.restore_bundle("x", tags, dest=tmp_path) == "x-2026-10-01"
    assert (tmp_path / "raw/x/pages.jsonl").read_bytes() == b'{"a": 1}\n'
    assert reports == [("restore x", "older tag used")]
    rel["x-2026-10-01"] = (good, nman)  # the manifest doesn't match the bundle: not good either
    with pytest.raises(SystemExit, match="no good release"):
        state.restore_bundle("x", tags, dest=tmp_path)


def test_ee_ledger_comes_from_gh_pages_and_fails_closed(pages_remote, tmp_path, monkeypatch):
    """A2: the ledger is read from the gh-pages branch; versions without a readable ledger switch Earth Engine off."""
    state = pytest.importorskip("plumes.state")
    _pages_local(tmp_path, monkeypatch, pages_remote)
    monkeypatch.setattr(state, "EE_LEDGER", tmp_path / "ledger.json")
    out = tmp_path / "out"
    monkeypatch.setenv("GITHUB_OUTPUT", str(out))
    assert state.restore_ledger() == "unreadable: Earth Engine off"
    assert out.read_text() == "ee_ledger=missing\n"
    (tmp_path / "pages" / "data" / "ee-usage.json").write_text(json.dumps({"runs": [], "months": {}}))
    assert state.restore_ledger().startswith("merged")


def test_trial_runs_open_no_health_issues(monkeypatch):
    monkeypatch.setenv("PLUMES_TRIAL", "true")
    health._reporter.cache_clear()
    try:
        assert health._reporter() is None
    finally:
        health._reporter.cache_clear()
