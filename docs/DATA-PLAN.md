# Data plan

Status: 2026-10-21, updated the same day for Kurt's decisions ([DECISIONS.md](DECISIONS.md): volcanoes, Plumes, architecture B from the start, Q5 = (ii), the shared `lgu-lights` Earth Engine account, no published dataset) and then for **Q19–Q31: 24 sources at M1, 25 at M1.1, queried in place where possible** ([NO-DOWNLOAD-ALTERNATIVES.md](NO-DOWNLOAD-ALTERNATIVES.md), [NASA-EE-CANDIDATES.md](NASA-EE-CANDIDATES.md)). The other entries of the 77-source canvas are out of scope (Q30) and stay in the registry and LICENCES.md as history. Facts were checked on the day ([RESEARCH.md](RESEARCH.md), [LICENCES.md](LICENCES.md), [`research/`](research/)); **[U]** marks an estimate to be replaced by the spike ([SPIKE-PLAN.md](SPIKE-PLAN.md)). The registry draft is [sources-draft.yaml](sources-draft.yaml) (92 entries, the chosen 27 marked `# chosen: true`, validated with `archivekit validate-registry`, kit v1.1.0).

## 0. Summary

| Decision | Choice | Why |
|---|---|---|
| Unit of analysis | volcano × day (and volcano × month for the map scrubber); 24 PHIVOLCS active volcanoes, coordinates from GVP, a hand-made crosswalk table | the series are event-driven and daily; 24 units keep every output small |
| Time span | 2000-01-01 → the snapshot date; each series starts when its instrument does (MODIS 2000-11, Landsat 2000 in this window, OMI SO2 2004-10, VIIRS 2012-01, Sentinel-1 2014-10, USGS 1900, TROPOMI 2018-12, bulletins 2017-09, LAVA 2022, Tokyo VAAC 2010, DROMIC 2016) | an honest "since 2000" that says which years each series covers (Q7) |
| Sources | **24 sources (26 registry entries; USGS and Landsat are each split in two), 25 with M1.1** (Q30, Q31): the 20 of NO-DOWNLOAD-ALTERNATIVES.md plus OMI SO2, MSVOLSO2L4, Landsat and Sentinel-1; Google Open Buildings Temporal at M1.1. Of these, Black Marble and the Lights poverty join are M1.1 and the S5P aerosol index and GPM IMERG are M2. The rest of the canvas is out of scope, kept as history | query in place, free, every story step covered; LICENCES.md has the verdicts |
| Milestone 1 | 20 sources (22 registry entries) that make the Taal January 2020 story and the overview map work end to end (§9) | every pipeline shape once: Earth Engine reductions, API queries, a range read, NASA Harmony, three crawlers, a document parser, a reanalysis read |
| SO2 | TROPOMI OFFL L3 on Earth Engine: daily column mass (t) and valid-pixel fraction inside a 50 km box and in 5/10/15/30 km rings, both bands; monthly national mean mosaics at 1 km; **OMI `OMSO2e` daily per volcano box through Harmony (2004-10 → )**; **MSVOLSO2L4 SO2 mass per eruption** (M1) | open licences; the track honours "since 2000" from 2004; column, not flux, labelled as such |
| Thermal | Earth Engine `FIRMS`, `MOD14A1`, `VNP14A1` daily counts and **max FRP** within 5/10/15 km (radiative power in place of MIROVA, which is out of scope); the FIRMS area API (`*_SP` CSV, 5 days per call, MAP_KEY) for the national detections layer | three independent views; the fire caveat shown |
| Earthquakes | USGS FDSN event API for the Philippine box since 1900 (paged by period); counts and max magnitude within 10/30 km per day; the bulletins' volcanic-earthquake counts beside them (the PHIVOLCS monthly tables are out of scope, Q24/Q30) | public domain backbone plus the agency's own counts |
| Ground reports | PHIVOLCS bulletins: WordPress prose 2017-09 → 2024, LAVA structured 2022 → ; parsed to daily fields; alert-level history reconstructed; shown as dated, linked markers | the official figures beside the satellites; Q5 = (ii): cite, no bulk file, no email |
| Plume | Tokyo VAAC advisories (JMA, open archive 2010 →) for plume height; MSVOLSO2L4 plume altitude per eruption; ERA5 pressure-level winds for direction; the Sentinel-5P aerosol index at M2 (layer height and Himawari out of scope) | the Philippines north of 10°N is Tokyo VAAC's area, not Darwin's (LICENCES.md) |
| People | DSWD DROMIC evacuee counts (docx reports, parsed and discarded) at M1; the Lights poverty join and Open Buildings Temporal at M1.1 | official counts with their links; exposure stays descriptive |
| Eruptions | GVP WFS (volcanoes and eruptions, Philippines filter); MSVOLSO2L4 SO2 mass beside VEI | VEI and dated episodes with uncertainty |
| Exposure | WorldPop (GP 100 m 2000–2020 plus the sat-io Global 2 asset 2015–2030) and DEM reduced in Earth Engine per ring; COD-AB admin-3 attributes by HTTP range read for LGUs within rings (PSGC-aligned pcodes); Open Buildings Temporal per ring per year at M1.1 | descriptive counts with CC BY attribution |
| Deformation | M1: links (COMET portal) and PHIVOLCS deformation sentences; M2: a Taal crop (Q8), preferably read in place from ARIA S1 GUNW (NASA-EE-CANDIDATES.md B6) rather than LiCSAR files | tens of GB per frame cannot be mirrored or archived |
| Publishing | immutable `v<N>/` folders: per-volcano JSON, Parquet tables, PMTiles, raster tiles, story assets; `latest.json` pointer; **no published dataset, no Zenodo DOI** (Q15); files on GitHub Pages (primary) with a Hugging Face files-only mirror as hosting fallback (Q12; see §5 and OPEN-QUESTIONS Q19) | the Lights pattern without the dataset release |
| API | a read-only Java 17 Spring Boot (MyBatis) API on PostGIS (Neon free, Render free, Singapore) behind a same-origin Cloudflare Pages function with edge caching, loaded by a Java batch from the same data version (Q3); the static site works with the API deleted | the relational, spatial-temporal side of the data; Kurt's day job |
| Archiving | `archivekit` registry; private `abrycta/plumes-archive`; file sources snapshotted weekly; crawled HTML and hand-downloaded files bundled and adopted as releases; rasters never archived | the portfolio standard |
| Cadence | weekly: new bulletins, advisories, earthquakes, S5P, OMI and fire days, new Landsat and S1 scenes for open events; yearly: WorldPop, MSVOLSO2L4; on release: GVP | small deltas; one full backfill, chunked for the shared Earth Engine quota (§7) |

## 1. Sources, access, licences, volumes

The full list is the registry ([sources-draft.yaml](sources-draft.yaml)), one entry per source with publisher, access URL or API pattern, format, size per volcano and in total, cadence, auth and the licence verdict; the evidence per verdict (quoted clause, URL, attribution text) is [LICENCES.md](LICENCES.md), whose summary table maps the 77 canvas rows to registry ids and milestones. This section keeps only the shape of each family and what reaches the browser.

| Family (registry kinds) | Entries (in scope) | Raw volume (never served) | What reaches the browser |
|---|---|---|---|
| Earth Engine reductions (`remote-dataset`, `ee://`) | 12: S5P SO2 and AER_AI (M2), FIRMS, MOD14A1, VNP14A1, WorldPop, Copernicus DEM, Sentinel-2, Landsat C2 L2, Sentinel-1 GRD, GPM IMERG (M2), Black Marble VNP46A2 (M1.1); Open Buildings Temporal (M1.1) makes 13 | nothing downloaded | per-volcano daily rows (kB), monthly mosaics (under 1 MB each), thumbnails (50–300 kB each) |
| API queries and range reads (`file`, `remote-dataset`) | 7: GVP ×2 (WFS), USGS ×2 (FDSN), the FIRMS area API, COD-AB (range read of one `.dbf`, 119 kB), ERA5 (ARCO Zarr range reads); OMI `OMSO2e` through Harmony makes 8 | under 30 MB of query results in all | Parquet tables and PMTiles derived from them (§4) |
| Crawled pages and documents (`update-input`) | 4: PHIVOLCS WordPress and LAVA, Tokyo VAAC, DSWD DROMIC docx; plus MSVOLSO2L4 (one 0.18 MB text file, Earthdata) | PHIVOLCS: about 5,300 WordPress prose pages, archived as the extracted bulletin block plus page hash (about 20 MB raw, a few MB zstd), and LAVA pages at 13.6 kB (2.9 kB gzip) each (spike S1, S2); VAAC under 5 MB; DROMIC docx parsed and discarded (only rows and hashes archived) | dated linked figures inside the per-volcano JSON and story JSON; never a consolidated PHIVOLCS table |
| Own data | 1: the Lights poverty estimates (M1.1) | a few kB per volcano | the "who lives nearby" panel |
| Out of scope (Q30) | every other registry entry (MIROVA, GHSL, WorldCover, PSGC, GEM, Himawari, InSAR files, the attention track, the M3/M4 context sources, hand downloads) and the 4 retired at the licence check | — | the About page lists the retired four with the reason |

Not used: HazardHunterPH, GeoRiskPH, GISWEB KMZ (terms forbid republishing; link only); PHIVOLCS-LAVA registered downloads (policy); the COMET portal images (CC BY-NC; linked); BoM Darwin VAAC pages (no scraping; linked); the GDELT BigQuery route and USGS frame scanning (paid).

## 2. Processing path

1. **Earth Engine (Python client, the shared `lgu-lights` service account; §7 for the quota rule):** for each of the 24 volcanoes, a FeatureCollection of 50 km boxes and 5/10/15/30 km rings; `reduceRegions` per image over S5P (sum of column × area, valid-pixel count, mean cloud fraction, for both bands), `FIRMS`/`MOD14A1`/`VNP14A1` (count of fire pixels by confidence class, max FRP), later GPM and Black Marble event windows, exported as batch tables to Drive and picked up by the Actions job (fallback: `computeFeatures` under 100 MiB). National monthly S5P mean mosaics exported as GeoTIFF at 1 km. WorldPop and the DEM reduced per ring once (Open Buildings Temporal per ring per year at M1.1). Sentinel-2 and Landsat least-cloudy composites and Sentinel-1 log-ratio change images as `getThumbURL` images for the before/after strip; Landsat `ST_B10`/`ST_B6` reduced over crater lakes. Every call pins the asset id, the reducer, the scale and the ring geometry hash; these land in the output as columns.
2. **Queries via `archivekit.fetch()` and fetch hooks:** GVP WFS, USGS FDSN, the FIRMS area API (5-day calls over the Philippine box), the COD-AB `.dbf` range read, the OMI `OMSO2e` Harmony subset per volcano box and `MSVOLSO2L4` (Earthdata token minted in CI). Each hook saves the request (URL, asset id, geometry hash, dates) and the returned rows; archivekit snapshots that file, so the fallback is "primary query → last good result".
3. **Crawlers (pipeline code, polite):** ≤ 1 request/s, `If-Modified-Since`, resumable by page or id, raw HTML written to a dated bundle (`<id>-<date>.tar.zst`) that the archive repo adopts as a release. PHIVOLCS WordPress (the English prose bulletins 2017-09 → 2023: about 5,300 pages, 1.5 h at 1 request/s, measured in spike S1; the 2021-10 → 2025 summary pages are empty shells and are skipped), LAVA by id (the id → volcano map from the daily list page, the GlobalSign intermediate pinned; S2), the Tokyo VAAC yearly lists and advisories (2010 →, a few thousand pages), DROMIC event posts and their docx files.
4. **Document parsers:** DROMIC docx tables (`python-docx`; evacuation centres, families and persons per province per report), VAAC text (flight level, dates, polygon), each with committed fixtures and tests. Disagreements between channels on overlapping dates are logged, not silently resolved.
5. **Range readers:** ERA5 pressure-level winds from the ARCO Zarr by HTTP range (Replay's pattern), a few MB per story day. No bucket streaming at any milestone.
6. **Join and derive:** a `volcano_day` table (volcano, date, fields from every series with coverage flags); episodes (GVP eruption windows; alert-level windows; "strong degassing" windows defined by a documented rule over PHIVOLCS flux, never over satellite columns alone); baselines (rolling 365-day median per series) and anomaly flags; exposure rings; story steps as dated JSON with every figure's source URL.
7. **Data-quality checks (block publishing):** row counts per series within bounds; no duplicate (volcano, date); every PHIVOLCS, VAAC and DROMIC value carries a URL; TROPOMI and OMI coverage fractions in [0, 1]; GVP volcano count = 23 and the crosswalk covers all 24; the Taal 2020-01-12 and Kanlaon 2024-06-03 fixtures reproduce known values.
8. **Materialise:** per-volcano JSON (series, bins, episodes, readings EN/JA, sources), story JSON, Parquet (`volcano_day`, `thermal_detections`, `earthquakes_usgs`, `exposure`, `advisories`, `displacement`), PMTiles (volcanoes, rings, thermal detections by month, USGS earthquakes), raster tiles (monthly SO2, hillshade), story assets (Sentinel-2, Landsat and Sentinel-1 thumbnails), `provenance.json` (archivekit `data_version_metadata`, EE asset ids, snapshot date).
9. **Load the API (Java batch, Actions):** the same data version is loaded into the Neon PostGIS schema (volcanoes, eruptions with SO2 mass, bulletin fields, advisories, USGS events, thermal detections, SO2 days, episodes, exposure) with a contract test that the API's JSON for a volcano equals the static JSON; the static site never waits for this step.

## 3. PHIVOLCS posture (the licence gate; Q5 = ii)

- Only public pages are read; no registered account is used in the pipeline; no email is sent.
- Every PHIVOLCS-derived number on the site carries "DOST-PHIVOLCS, bulletin of <date>" and the link; alert-level changes are dated, linked markers; no "current" level is ever shown (Q14).
- No consolidated PHIVOLCS-derived file (bulletin fields, earthquake catalogue) is offered anywhere: the values live inside the per-volcano display JSON and the API's per-volcano endpoints, each row with its URL. Because every static file the browser fetches is public, "no bulk file" means no table whose purpose is redistribution, not that the display JSON is hidden.
- Nothing on the site forecasts; the Japanese text is checked against the same rule.
- The raw HTML bundles live only in the private archive (archiving standard §6).

## 4. Data model (published)

- `volcano` (24): `volcano_id` (PHIVOLCS name slug), `gvp_number`, names EN/JA, lat, lon, elevation, type, province, observatory (bool), `series_available` (list).
- `volcano_day`: `volcano_id`, `date`, `so2_mass_pbl_t`, `so2_mass_15km_t`, `so2_valid_frac`, `so2_cloud_frac`, `omi_so2_pbl_du`, `omi_so2_valid` (OMSO2e, 2004-10 →), `fire_modis_n`, `fire_viirs_n`, `fire_max_frp_mw` (MOD14A1/VNP14A1 MaxFRP; replaces MIROVA's VRP), `eq_usgs_n_30km`, `eq_usgs_max_mag_30km`, `ph_alert_level`, `ph_vt_count`, `ph_tremor_count`, `ph_so2_flux_tpd`, `ph_so2_flux_date`, `ph_plume_m`, `ph_deformation_text`, `ph_source_url`, `vaac_max_fl`, `vaac_n`, `vaac_source_url`, `evacuees_n`, `evacuees_source_url`, `rain_mm` (M2), `nightlight_rad` (M1.1), and `*_source_version` per family.
- `volcano_bins`: `volcano_id`, `date`, `ring` (0–5, 5–10, 10–15, 15–30 km), per-ring sums and counts for SO2 and fire, for the in-browser recompute.
- `episode`: `volcano_id`, `kind` (gvp_eruption, alert_window, strong_degassing), start, end, `vei`, `so2_mass_kt` and `plume_alt_km` (MSVOLSO2L4), `max_alert`, uncertainty fields from GVP, `source`.
- `exposure`: `volcano_id`, `ring_km`, `year`, `population`, `lgus_within` (COD-AB pcodes, PSGC-aligned); at M1.1 `buildings_n` and `building_height_mean_m` per year (Open Buildings Temporal, 2016–2023) and `poverty_rate` (Lights).
- `story`: `story_id`, `volcano_id`, steps (date range, text EN/JA, series shown, figures with URLs), assets (thumbnails, wind arrows, animation).
- `earthquakes_usgs` (national), `thermal_detections` (national, from the FIRMS area API; `type` if the SP CSV carries it, spike item 19), `advisories` (Tokyo VAAC), `displacement` (DROMIC rows).

Sizes (**[U]** for Parquet; the PostGIS and JSON figures are measured, spike S5, S6): `volcano_day` 24 × 9,800 days ≈ 235k rows, under 20 MB Parquet; bins about 1 M rows, under 30 MB; detections up to 400k rows, under 20 MB; USGS 27k rows, 3 MB; advisories and displacement under 1 MB; per-volcano JSON under 80 kB gz each (the four deep volcanoes about 120 kB); Taal over the full span measured 389 kB raw, 49 kB gzip.

## 5. Versions, hosting, provenance, rollback (Q12, Q15)

- Each full run builds `v<N>/`; `latest.json` is flipped only when every check passes; rollback is a pointer flip (archiving standard §5). The app shows "data through <snapshot date>" and "data as of <date>" when an archived copy was used.
- `provenance.json` records the archivekit run manifest, Earth Engine asset ids and date ranges, crawl ranges and bundle release tags, the GVP and MSVOLSO2L4 versions, the commit SHA.
- **No published dataset:** no Hugging Face dataset release, no dataset card as a product, no Zenodo DOI (Q15). The About page lists every source with its attribution and links to the publishers.
- **Hosting:** the app and per-volcano JSON on Cloudflare Pages (static requests free and unlimited, 25 MiB per file, 20,000 files per deployment); tiles, Parquet and story assets on GitHub Pages (primary; 1 GB site, 100 GB per month soft) with a Hugging Face mirror as the fallback base URL (Q12).
- **Private or public Hugging Face repo?** A private repo cannot serve files to an anonymous browser: "Other users who visit the URL of your private repo will receive a 404 - Repo not found error." (https://huggingface.co/docs/hub/repositories-settings), and gated repos need a logged-in account. So the fallback must be a **public** repo. A public repo may be files-only (a dataset card and licence tag are optional: "Each dataset may be documented by the README.md file in the repository", https://huggingface.co/docs/hub/datasets-cards), but public free storage is "Best-effort" beyond "the first few gigabytes" (https://huggingface.co/docs/hub/storage-limits), anonymous resolver requests are capped at 3,000 per 5 minutes per IP, and CORS with Range on the Xet CDN host was only fixed in February 2026 (verify in a browser). Licence implication: whatever is on a public mirror is publicly downloadable, so the mirror holds the same files as GitHub Pages, every file already carries its attribution, and nothing that may not be redistributed (ISD station files, OSM-derived tables, PHIVOLCS consolidated tables) is ever in a data version in the first place. **Decided (Q19 = a):** a public, files-only Hugging Face repo `permission-alluring/plumes` whose README says it is the app's hosting mirror, not a dataset release (no licence tag, no DOI); it holds the same files as GitHub Pages and never anything that may not be redistributed. Cloudflare Pages static assets remain the fallback if Kurt later wants nothing on HF.
- **Retention on GitHub Pages:** a data version is about 250 MB at M1 (§10), so at most three versions fit under 1 GB; the previous version is kept for rollback and older ones are deleted from Pages (they stay in the GitHub release that built them).

## 6. InSAR at milestone 2 (outline)

**Superseded on 2026-10-22 (DECISIONS L2, L3):** M2 uses COMET's ready-made LiCSBAS series for all 18 covered volcanoes plus a `deformation-velocity` map layer, published under the portal's CC BY-NC 4.0 notice with attribution (L1a, no email); see [LAYERS-PLAN.md](LAYERS-PLAN.md) §3.1. The outline below is kept as history.

Crop the Taal frame `032D_07536_111313` to a 60 × 60 km window; download only unwrapped phase and coherence for pairs 2019-07 → 2020-07 (about 150 pairs × 2 files **[U]**) in staged Actions jobs; run LiCSBAS (GPL-3, run as a tool, not linked) to a LOS time series with `vstd`; publish the series at a few hundred points plus a velocity raster; show the reference point, LOS geometry and the atmospheric caveat. Acknowledgement "LiCSAR contains modified Copernicus Sentinel data [year]" and the LiCSBAS citation. At M3 the NGL GNSS series for PTGY (Tagaytay) and PLEG (Legazpi) sit beside it.

## 7. Cadence, the shared Earth Engine quota, CI budget [U]

**Earth Engine (Q11: the `lgu-lights` project's 150 EECU-hours per month, shared).** The quota is per Cloud project and "can't be transferred"; exceeding it puts the whole project in restricted mode (slower, not stopped); a Quota Administrator's per-day cap is also per project, so it would throttle Lights too (https://developers.google.com/earth-engine/guides/usage). Lights' data run is manual (`workflow_dispatch`, no cron) and estimated at a few EECU-hours per full rebuild (`../../lgu-lights/docs/DATA-PLAN.md`). Plumes therefore budgets itself in software:

| Rule | Value |
|---|---|
| Plumes' monthly ceiling | 50 EECU-hours (one third of the project quota); the pipeline reads `batch_eecu_usage_seconds` from every task's status, sums the month in a small state file in the data release, and refuses to start a new Earth Engine job above the ceiling (the run fails clearly; nothing else is affected) |
| Per-run cap | 10 EECU-hours; the backfill is chunked by year and by collection so each chunk stays under it |
| Backfill plan | M1: about 6–7 EECU-hours as first estimated; **the spike measured 3.0 EECU-seconds per volcano-month for S5P (two rings) plus MOD14A1, which puts the series at about 3 EECU-hours and M1 at about 4 with thumbnails and exposure** (S8) (S5P about 6,000 orbit images, three fire collections about 24,600 daily images, exposure once, Landsat lake temperature and thumbnails, S1 event thumbnails) spread over two calendar months if the spike (items 1, 2, 16) measures more than 25; the roadmap about 10–12 EECU-hours **[U]** (M1.1 Black Marble event windows and Open Buildings Temporal about 1–2; M2 GPM reduced from the daily product, AER_AI). OMI and MSVOLSO2L4 use NASA Harmony, not Earth Engine |
| Weekly delta | under 0.6 EECU-hours (seven new days per collection; new Landsat and S1 scenes) |
| Run window | Plumes' scheduled job runs Sundays 02:00 PHT; Lights' manual runs are started by Kurt, who sees Plumes' month-to-date figure in the data release before starting one |
| Safety net | a per-day cap of about 20 EECU-hours in the Cloud console, set by Kurt, only to stop a runaway job; it throttles both projects, so it is not the budgeting mechanism |
| Credentials | the existing key `earth-engine-sa-key` at first; a second service account in the same project (free, "Any number of service accounts on a project can be configured to use Earth Engine") with its own key `earth-engine-sa-key-plumes` is recommended so either repo's key can be rotated alone (OPEN-QUESTIONS Q22) |

**GitHub Actions.**

| Trigger | Job | Where | Minutes |
|---|---|---|---|
| one-off | backfill: EE exports (batch, 1–3 h wall, little runner time), PHIVOLCS crawl in yearly chunks (4–5 h), VAAC crawl (under 1 h), FIRMS area API (30–60 min), OMI Harmony jobs (minutes), DROMIC Taal 2020 (minutes), parse, join, materialise, Java load | public repo (free minutes; 6 h per job, 20 concurrent) | about 7–9 h of runner time once |
| weekly | archivekit health and snapshots (the query-result files and adopted crawl bundles) | private archive repo (2,000 shared minutes a month, with Replay's and Lights' archive repos and Akari's CI) | about 10 a month, plus a first snapshot of 2–3 |
| weekly | deltas: new bulletins, advisories, earthquakes, S5P, OMI and fire days, rebuild v<N>, load the API | public repo | 10–20 |
| on push | pipeline tests, web build, Java build and tests, the API-equals-static contract test | public repo | 5–10 per push |
| yearly | WorldPop and MSVOLSO2L4 refresh | public repo | 5 |

Scheduled workflows stop after 60 days without repository activity in a public repo; the weekly job's own commits (the data pointer) count as activity.

## 8. The Java API on free tiers (Q3; verified 2026-10-21)

| Platform | Rule (quoted in [SPIKE-PLAN.md](SPIKE-PLAN.md) sources and `../../typhoon-replay/docs/architecture/SYSTEM-ARCHITECTURE-RESEARCH.md` §7) | Consequence for Plumes |
|---|---|---|
| Render free instance hours | "Render grants 750 Free instance hours to each workspace per calendar month"; spun-down services consume none; exhausted means Render "suspends all of your Free web services until the start of the next month" (https://render.com/docs/free) | Replay's `typhoon-replay-java` already lives in the workspace. Two services fit only if both sleep most of the month: Replay's planned about 6 h per day awake (about 180 h) plus Plumes at 1–3 h per day awake (30–90 h) leaves headroom; but exhaustion suspends **both** projects, so Plumes runs no uptime pinger, lets the service sleep after 15 minutes, and wakes it only from real cache misses and one nightly contract check |
| Render outbound bandwidth | Hobby workspaces get 5 GB per month, shared; with a card on file overage is billed at $0.15 per GB (https://render.com/docs/outbound-bandwidth) | the Pages function in front of the API caches every public read (`Cache-Control: public, s-maxage=86400, stale-while-revalidate`); responses are gzip and 2–20 kB; the target is under 500 MB of origin egress a month for Plumes; spike item 15 measures it |
| Render build minutes | Hobby: 500 Starter minutes a month; exhaustion auto-buys more when a card is on file (https://render.com/docs/build-pipeline) | the Java image is built in GitHub Actions and pushed to GHCR; Render deploys the prebuilt image, so Render build minutes stay near zero |
| Render free Postgres | one per workspace, expires after 30 days | not used; the database is Neon |
| Neon Free | 100 projects; "1 GB/project, 20 GB account total"; 100 CU-hours per project per month; scale to zero after 5 minutes, cannot be disabled; 5 GB public network transfer per project; PostGIS on all plans (https://neon.com/docs/introduction/plans) | Plumes gets its own free project (Singapore) beside Replay's; the M1 catalogue measured 137 MB with a 10 % sample of detections, **about 220 MB with all of them** (spike S6); the three M1 queries run in under 0.3 ms on the server; API reads are small, so compute and egress stay far under the caps; the Java batch loads a data version in one connection session |
| Cloudflare Pages Functions | 100,000 requests a day shared with Workers on the Free plan; static assets free and unlimited; the Cache API works on Pages Functions, per data centre (https://developers.cloudflare.com/pages/functions/pricing/) | only `/api/*` invokes the function; everything else is static; the function also sets `cf: { cacheEverything, cacheTtl }` on the origin fetch so the standard CDN cache (tiered) serves most hits |

**Decided (Q20 = a, Q21 own project):** a second free Render web service `plumes-java` (`plan: free`, prebuilt GHCR image, no pinger, sleep after 15 minutes, one nightly contract check, edge cache in front) and an own free Neon project `plumes`, both created only after spike items 13–15 and Kurt's go-ahead. If the two Render services stop fitting (for example when Replay deploys its other three engines), the fallbacks are co-hosting Plumes' endpoints inside Replay's Java service or a Cloudflare Worker with Hyperdrive to Neon.

## 9. Milestone 1 cut and the roadmap (Q23, Q30, Q31)

**Milestone 1: the Taal January 2020 story and the overview map, end to end, on 20 sources (22 registry entries).** The 24 sources of Q30/Q31 less Black Marble and the Lights poverty join (M1.1) and the S5P aerosol index and GPM IMERG (M2):

| # | Source | Registry entries | Why at M1 |
|---|---|---|---|
| 1–2 | Smithsonian GVP volcanoes and eruptions (WFS) | `gvp-volcanoes-ph`, `gvp-eruptions-ph` | the 24 points (with the crosswalk), facts, the eruption band (VEI 4) |
| 3–4 | PHIVOLCS bulletins, WordPress 2017-09 → 2024 and LAVA 2022 → | `phivolcs-bulletins`, `phivolcs-lava-bulletins` | the dated alert markers of steps 2 and 4 (1 → 4 on 12 January, 4 → 3 on 26 January), earthquake counts, SO2 flux, deformation sentences for step 1 |
| 5 | USGS ComCat (FDSN) | `usgs-comcat-ph-1900-2009`, `usgs-comcat-ph-2010` | the earthquake track; step 2 |
| 6 | Sentinel-5P TROPOMI SO2 | `s5p-offl-so2` | the SO2 track and the monthly map; step 2 |
| 8–10 | FIRMS (EE and area API), MOD14A1, VNP14A1 | `firms-modis`, `modis-mod14a1`, `viirs-vnp14a1` | the thermal track, radiative power (MaxFRP) and the national detections layer; step 2 |
| 11 | Tokyo VAAC advisories | `vaac-tokyo-advisories` | step 3 (plume height); about 45 advisories for Taal 2020 |
| 12 | DSWD DROMIC reports | `dswd-dromic-reports` | step 3 (evacuees); about 70 docx reports for Taal 2020; the one document parser |
| 13–15 | WorldPop, COD-AB (range read), Copernicus DEM | `worldpop-100m`, `cod-ab-phl-gdb`, `copernicus-dem-glo30` | step 6 (about 459,000 people within 14 km), LGU names, the hillshade basemap |
| 16 | Sentinel-2 L2A | `s2-sr-harmonized` | step 5 (crater lake before and after) |
| 17 | ERA5 winds | `era5-pressure-levels` | wind arrows (where the plume and vog went) |
| 21 | OMI SO2 `OMSO2e` (Harmony) | `omi-omso2e` | the SO2 track back to 2004-10 for every volcano |
| 22 | MEaSUREs `MSVOLSO2L4` | `nasa-msvolso2l4` | SO2 mass and plume altitude per eruption beside VEI |
| 23 | Landsat C2 L2 (TM, ETM+, OLI, OLI-2) | `landsat-c2-l2`, `landsat-surface-temperature` | before/after since 2000 and the Taal crater-lake temperature before 2020 |
| 24 | Sentinel-1 GRD | `s1-grd` | step 5 in the eruption week itself, through the ash and cloud |

InSAR stays as links (COMET portal, PHIVOLCS deformation sentences; not counted as a source). HazardHunterPH stays a link on every page.

**Roadmap:**

| Milestone | Theme | Sources | Notes |
|---|---|---|---|
| M1.1 | the Lights link, the second story | Black Marble VNP46A2 on Earth Engine (19), the Lights poverty join (20), **Google Open Buildings 2.5D Temporal** (25, `open-buildings-temporal`); the Kanlaon 2024 story on the M1 sources (Q29); national layers if deferred by the spike (Q9) | 25 sources in all; no new registration |
| M2 | the plume and the ground ([LAYERS-PLAN.md](LAYERS-PLAN.md) §7) | nine layers: NOAA-20 VIIRS thermal (own series), OMI SO₂ daily, the deep-time strip with NCEI HazEL, Landsat crater-lake temperature, crater-lake area and colour (adds JRC GSW), the S5P aerosol index (7), GPM IMERG on Earth Engine (18), the national monthly SO₂ map, and **COMET LiCSBAS deformation for 18 volcanoes (series and a `deformation-velocity` layer)**, which supersedes the Taal InSAR crop of Q8 and the ARIA GUNW route (L2) | new sources: COMET LiCSBAS, NCEI HazEL, JRC GSW, FIRMS `VIIRS_NOAA20_SP`. Ready when the Akari event marker is released (§6 there); the COMET licence (L1a) and the contract change (L3a) are settled; about 4–6.5 EECU-h |
| M3 | context and slow signals ([LAYERS-PLAN.md](LAYERS-PLAN.md) §2) | night LST, Dynamic World and dNBR around eruptions, OMI aerosol index, GHSL built-up, ECOSTRESS, OMPS SO₂ and `MSAQSO2L4` (four Philippine volcanoes, L9), OSM schools and hospitals per ring labelled "as of <date>" (L7), ERA5-Land rain and S5P plume height; the ISC/EMSC catalogue only if its licence checks out (L8) | lahar rivers excluded (L6) |
| out of scope (Q30) | — | MIROVA, GHSL, WorldCover, PSGC, GEM faults, the PHIVOLCS earthquake tables, Himawari, the attention track, hand downloads and every former M3/M4 context source | kept in the registry and LICENCES.md as history; NO-DOWNLOAD-ALTERNATIVES.md lists query routes if one is wanted back |
| dropped at the licence check | — | WWLLN (paid), OpenSky (unusable), LaMEVE (permission needed), PhilGEPS (link-only, portal down) | listed on the About page with the reason |

## 10. Size and quota totals [U] (measured items marked; spike Run 2)

| Where | M1 | Roadmap (M1.1 + M2) | Limit | Notes |
|---|---|---|---|---|
| A data version on GitHub Pages (tiles, Parquet, story assets) | about 255–260 MB: Parquet about 75 MB, PMTiles 20 MB, SO2 mosaic tiles under 100 MB (split per year for the 25 MiB cap), hillshade tiles about 30 MB, thumbnails (Sentinel-2, Landsat, Sentinel-1, about 20 per volcano at 50–100 kB) | about 265 MB | 1 GB per site; 100 GB a month soft | at most two or three versions kept on Pages |
| Cloudflare Pages (app + per-volcano and story JSON) | about 300 kB gz app bundle + 24 JSON files (about 3 MB) + story JSON | under 10 MB | 25 MiB per file; 20,000 files; static requests unlimited | nothing near the limits |
| Hugging Face mirror (Q19 = a) | the same about 260 MB per version | about 265 MB | public storage "best-effort" beyond "the first few gigabytes"; 3,000 anonymous resolver requests per 5 minutes per IP | two versions mirrored at most |
| Private archive releases (`abrycta/plumes-archive`) | about 30–40 MB: PHIVOLCS bundles about 15–25 MB zstd (extracted blocks, S1, plus LAVA pages), FIRMS API results 10–20 MB, OMI rows up to 7 MB, USGS 5 MB, VAAC under 5 MB, GVP, COD-AB attributes 0.1 MB, MSVOLSO2L4 0.18 MB, DROMIC extracted rows and hashes | under 100 MB | 2 GiB per asset; 1,000 assets per release | weekly snapshots only re-upload changed files |
| Earth Engine (shared project) | backfill about 4 EECU-hours (measured per volcano-month, S8); weekly under 0.6 | backfill about 10–12 EECU-hours | 150 EECU-hours a month per project, shared with Lights | Plumes' own ceiling 50 a month, 10 per run (§7, Q22) |
| GitHub Actions, public repo | one-off about 7–8 h (WordPress 1.5 h, LAVA up to 4.7 h, FIRMS 0.5–1 h); weekly 10–20 min; CI 5–10 min per push | the same | free on standard runners; 6 h per job | the crawl is chunked by year |
| GitHub Actions, private archive repo | about 10 min a month plus a 2–3 minute first snapshot | the same | 2,000 min a month shared across the account's private repos | Replay's and Lights' archive repos use about 20 each |
| Neon (own free project, Q21) | about 220 MB catalogue (measured, S6); API compute minutes a day | under 300 MB | 1 GB per project, 20 GB account; 100 CU-hours; 5 GB egress | spike item 14 |
| Render (`plumes-java`, shared workspace, Q20) | awake 30–90 h a month; origin egress under 500 MB | same | 750 instance hours and 5 GB a month per workspace, shared with Replay | spike items 13 and 15; `plan: free` only |
| Browser, first view | app 300 kB gz + volcano points and rings under 50 kB + basemap tiles | same | — | under 1 s warm from Manila (Lights measured 36–50 ms p50 to Pages from PH) |
| Browser, volcano page | one JSON under 80 kB gz (120 kB for Taal, Mayon, Kanlaon, Bulusan; Taal measured 49 kB, S5) + tiles by viewport | plus story assets on demand | — | the Web Worker recomputes rings from bins; nothing is fetched at interaction time |

What stays server-side (never reaches the browser): every raw raster and range read, the PHIVOLCS HTML, the DROMIC documents, the raw FIRMS, OMI and USGS query results, the PostGIS catalogue. What reaches the browser: the per-volcano and story JSON, PMTiles and raster tiles by viewport, Parquet only through the API or a future table view, thumbnails.

## 11. Resources to create (after the spike; none created now)

- Public repo `abrycta/plumes`; private `abrycta/plumes-archive` (`archivekit init plumes`); `ARCHIVE_READ_TOKEN` in both; `health.token_expires` set.
- Earth Engine: the existing `lgu-lights` service account key as a GitHub secret on `abrycta/plumes` (Q11), then a second service account in the same project with its own key `earth-engine-sa-key-plumes` (Q22, Kurt's action).
- FIRMS MAP_KEY (free, email; Kurt's action, Keychain `firms-map-key`) as a GitHub secret; the Earthdata login (exists) as `EARTHDATA_USERNAME`/`EARTHDATA_PASSWORD` secrets so CI mints short-lived tokens for `OMSO2e` (Harmony) and `MSVOLSO2L4`, as Lights does.
- Cloudflare Pages project with the `/api/*` function; CNAME `plumes.krtmtthw.dev` at Porkbun (listed before any DNS change); GitHub Pages for tiles; the public files-only Hugging Face mirror `permission-alluring/plumes` (Q19).
- Neon project `plumes` (free, Singapore, PostGIS; Q21); Render free web service `plumes-java` in the existing workspace deploying a GHCR image (Q20); GHCR package on the public repo.
- No other registration (Q28): OpenAQ, ReliefWeb, OpenAlex, ECMWF, Copernicus Marine, IOC, DAHITI and EROS fall away with Q30.
