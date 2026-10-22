# pipeline

Python (uv). Builds Plumes' data versions from the 22 M1 registry entries in [`sources.yaml`](sources.yaml) (validated with `archivekit validate-registry`). Outputs follow [`../contracts/`](../contracts/README.md). Everything under `data/` is gitignored.

| Step | Module | Source ids | Notes |
|---|---|---|---|
| File sources | `plumes.sources` | `gvp-*`, `usgs-comcat-*` | `archivekit.fetch` (primary → archive), project hooks in the same module |
| WordPress bulletins | `plumes.crawl.wp` | `phivolcs-bulletins` | 5,290 English prose bulletins from the sitemaps, ≤ 1 request/s, resumable (DECISIONS S1) |
| LAVA bulletins | `plumes.crawl.lava index`, `fetch` | `phivolcs-lava-bulletins` | id → volcano from the portal's archive search (B1); pinned intermediate (B2) |
| Tokyo VAAC | `plumes.crawl.vaac` | `vaac-tokyo-advisories` | Philippine advisories 2010 → from the yearly lists |
| DROMIC | `plumes.crawl.dromic` | `dswd-dromic-reports` | Taal 2020: grand totals from 69 `.docx` reports (Report #1 is `.doc`) |
| FIRMS area API | `plumes.firms` | `firms-modis` | MODIS_SP and VIIRS_SNPP_SP, 5-day windows (needs `FIRMS_MAP_KEY`) |
| FIRMS NOAA-20 (M2) | `plumes.thermal_n20` | `firms-viirs-noaa20` | `VIIRS_NOAA20_SP` windows, then the SP/NRT tail to today in `recent.csv`; the S-NPP successor, its own series |
| MSVOLSO2L4 | `plumes.nasa` | `nasa-msvolso2l4` | needs `EARTHDATA_TOKEN` |
| OMI SO₂ (M2) | `plumes.omi` | `omi-omso2e` | OMSO2e v004 via Harmony, one job per year, reduced per volcano box; needs `EARTHDATA_TOKEN` and `h5py` |
| COD-AB | `plumes.codab` | `cod-ab-phl-gdb` | range read of `phl_admin3.dbf` only (B3) |
| Earth Engine | `plumes.ee_series so2 / fire / exposure / thumbs-taal` | S5P, MOD14A1, VNP14A1, FIRMS, WorldPop, Sentinel-2 | one aggregation per month; Plumes cap 50 EECU-h a month, 10 a run (B4); needs `EE_SA_KEY` or `EE_KEY_FILE` |
| Earth Engine run A | `plumes.ee_run_a laketemp / lakegsw / lakes2 / uvai` | `landsat-surface-temperature`, `jrc-global-surface-water`, `s2-sr-harmonized`, `s5p-offl-aer-ai` | crater-lake temperature, area and colour (Taal, Pinatubo) and the UV aerosol index in eruption windows; `readmodels` adds them through `run_a.apply` when `ee-laketemp/`, `ee-lakegsw/`, `ee-lakes2/`, `ee-uvai/` exist; the tables are adopted into plumes-archive and come back with `plumes.state restore`. Not in `data.yml` (one-off backfill) |
| Earth Engine run B | `plumes.ee_run_b rain / so2-map [--canary YYYY-MM]` | `gpm-imerg-v07`, `s5p-offl-so2` | IMERG Final daily rain per 15 km ring (`ee-rain/`), national monthly SO₂ GeoTIFFs (`ee-so2-monthly/`); gated: Kurt checks the monthly EE total, then a one-month canary sizes the backfill (S8); `--max-eecu-h` stops a run early. Not in `data.yml` until the backfill is done |
| ERA5 | `plumes.era5` | `era5-pressure-levels` | point winds by Blosc block range reads; `--verify` (B6) |
| COMET LiCSBAS | `plumes.comet fetch`, `reduce` (canary) | `comet-licsbas` | 18 volcanoes, 31 frames; LOS series `los_comet_<frame>` and the `deformation-velocity` GeoTIFFs, built by `readmodels` when `data/raw/comet-licsbas/` exists; group `comet` (numpy). Not in `data.yml` yet |
| Deep time | `plumes.deeptime` (called by `plumes.readmodels`) | `gvp-eruptions-ph`, `noaa-hazel-volcanoes-ph` | `vN/deeptime.json`: GVP eruptions with NCEI HazEL deaths and damage; `--fixture` rewrites the contract fixture |
| Read models | `plumes.readmodels --version N` | — | writes `data/build/site/vN/`; `latest.json` only if every check passes |
| Publish | `plumes.publish --version N --pages --hf` | — | gh-pages `data/` (krtmtthw.dev/plumes/data/), then the HF mirror; latest.json last |
| Archive | `plumes.adopt [--changed-only]` | crawled and queried ids | releases in `abrycta/plumes-archive` (B8) |
| API reload | `.github/workflows/api-load.yml` | — | after every successful Data run: the API's Neon database from the published root (B16) |

CI: `.github/workflows/checks.yml` (lint, tests, registry) on every push; `.github/workflows/data.yml` weekly (Sundays 02:00 PHT) and by hand. It needs `ARCHIVE_READ_TOKEN` and, for adoption, `ARCHIVE_WRITE_TOKEN` (DECISIONS B9); without them it skips with a notice.

## Runbook

| Situation | What happens | What to do |
|---|---|---|
| A check fails | `latest.json` is not written; the previous version keeps being served | read `vN/manifest.json` → `checks.results`, fix, rebuild the same N |
| Bad data was published | — | point `data/latest.json` on gh-pages (and the HF mirror) back to the previous version; it is kept for rollback |
| Earth Engine cap reached | `BudgetExceeded`: the run stops, months already written are kept | wait for the next month or the next run; see `data/ee-usage.json` |
| A Lights data run is in progress | `data.yml` skips the Earth Engine steps | nothing |
| LAVA TLS fails after 2026-11-19 | the LAVA crawl errors | fetch the new issuer from the leaf's AIA URL into `plumes/certs/` (B2) |
| A crawler's page format changes | parsers return `None` for missing fields; the "1,500 bulletin days" and Taal checks fail | add a fixture under `tests/` and update `plumes/parse.py` |

Tests are lean: parsers against the spike fixtures, and the fixtures against the schemas (`uv run pytest -q`).
