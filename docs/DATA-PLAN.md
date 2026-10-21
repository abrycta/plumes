# Data plan

Status: 2026-10-21, updated the same day for Kurt's decisions ([DECISIONS.md](DECISIONS.md): volcanoes, Plumes, architecture B from the start, Q5 = (ii), the shared `lgu-lights` Earth Engine account, no published dataset) and for the 77-source canvas Kurt approved. Facts were checked on the day ([RESEARCH.md](RESEARCH.md), [LICENCES.md](LICENCES.md), [`research/`](research/)); **[U]** marks an estimate to be replaced by the spike ([SPIKE-PLAN.md](SPIKE-PLAN.md)). The registry draft is [sources-draft.yaml](sources-draft.yaml) (90 entries, validated with `archivekit validate-registry`, kit v1.1.0).

## 0. Summary

| Decision | Choice | Why |
|---|---|---|
| Unit of analysis | volcano × day (and volcano × month for the map scrubber); 24 PHIVOLCS active volcanoes, coordinates from GVP, a hand-made crosswalk table | the series are event-driven and daily; 24 units keep every output small |
| Time span | 2000-01-01 → the snapshot date; each series starts when its instrument does (MODIS 2000-11, VIIRS 2012-01, USGS 1900, TROPOMI 2018-12, bulletins 2017-09, LAVA 2022, Tokyo VAAC 2010, DROMIC 2016) | an honest "since 2000" that says which years each series covers (Q7) |
| Sources | the canvas: a core record (7 rows) plus nine passes (70 rows), folded into 90 registry entries; 4 rows dropped after the licence check (WWLLN, OpenSky, LaMEVE unless permitted, PhilGEPS) | Kurt approved the passes; LICENCES.md has the verdicts |
| Milestone 1 | 11 canvas rows (25 registry entries) that make the Taal January 2020 story and the overview map work end to end (§9) | the smallest set that exercises every pipeline shape: Earth Engine reductions, archivekit files, two crawlers, a document parser, a reanalysis read |
| SO2 | TROPOMI OFFL L3 on Earth Engine: daily column mass (t) and valid-pixel fraction inside a 50 km box and in 5/10/15/30 km rings, both bands; monthly national mean mosaics at 1 km; MSVOLSO2L4 for eruptions before 2018 (M2) | open licence, the only daily SO2 source; column, not flux, labelled as such |
| Thermal | Earth Engine `FIRMS`, `MOD14A1`, `VNP14A1` daily counts and max FRP within 5/10/15 km; FIRMS archive CSV (with `type`) for the volcanic subset; MIROVA Dataset v2.5 (CC BY 4.0) for VRP | three independent views; the fire caveat shown |
| Earthquakes | USGS CSV for the Philippine box since 1900 (paged by period); PHIVOLCS monthly tables 2016 → crawled (M1.1); counts and max magnitude within 10/30 km per day | public domain backbone plus the national agency's locations |
| Ground reports | PHIVOLCS bulletins: WordPress prose 2017-09 → 2024, LAVA structured 2022 → ; parsed to daily fields; alert-level history reconstructed; shown as dated, linked markers | the official figures beside the satellites; Q5 = (ii): cite, no bulk file, no email |
| Plume | Tokyo VAAC advisories (JMA, open archive 2010 →) for plume height; ERA5 pressure-level winds for direction; Sentinel-5P aerosol index and layer height and Himawari event replays at M2 | the Philippines north of 10°N is Tokyo VAAC's area, not Darwin's (LICENCES.md) |
| People | DSWD DROMIC evacuee counts (docx reports) at M1; NDRRMC sitreps, OSM, HRSL, buildings, DOH, PSA barangay census, Lights poverty later | official counts with their links; exposure stays descriptive |
| Eruptions | GVP WFS (volcanoes and eruptions, Philippines filter); NCEI significant eruptions and tsunamis later | VEI and dated episodes with uncertainty |
| Exposure | WorldPop, GHSL, WorldCover, DEM reduced in Earth Engine per ring; COD-AB and PSGC for LGUs within rings | descriptive counts with CC BY attribution |
| Deformation | M1: links (COMET portal) and PHIVOLCS deformation sentences; M2: LiCSBAS crop at Taal; M3: NGL GNSS series (PTGY, PLEG) | tens of GB per frame cannot be mirrored or archived |
| Publishing | immutable `v<N>/` folders: per-volcano JSON, Parquet tables, PMTiles, raster tiles, story assets; `latest.json` pointer; **no published dataset, no Zenodo DOI** (Q15); files on GitHub Pages (primary) with a Hugging Face files-only mirror as hosting fallback (Q12; see §5 and OPEN-QUESTIONS Q19) | the Lights pattern without the dataset release |
| API | a read-only Java 17 Spring Boot (MyBatis) API on PostGIS (Neon free, Render free, Singapore) behind a same-origin Cloudflare Pages function with edge caching, loaded by a Java batch from the same data version (Q3); the static site works with the API deleted | the relational, spatial-temporal side of the data; Kurt's day job |
| Archiving | `archivekit` registry; private `abrycta/plumes-archive`; file sources snapshotted weekly; crawled HTML and hand-downloaded files bundled and adopted as releases; rasters never archived | the portfolio standard |
| Cadence | weekly: new bulletins, advisories, earthquakes, S5P and fire days; yearly: WorldPop/GHSL; on release: GVP, MIROVA | small deltas; one full backfill, chunked for the shared Earth Engine quota (§7) |

## 1. Sources, access, licences, volumes

The full list is the registry ([sources-draft.yaml](sources-draft.yaml)), one entry per source with publisher, access URL or API pattern, format, size per volcano and in total, cadence, auth and the licence verdict; the evidence per verdict (quoted clause, URL, attribution text) is [LICENCES.md](LICENCES.md), whose summary table maps the 77 canvas rows to registry ids and milestones. This section keeps only the shape of each family and what reaches the browser.

| Family (registry kinds) | Entries | Raw volume (never served) | What reaches the browser |
|---|---|---|---|
| Earth Engine reductions (`remote-dataset`, `ee://`) | 27: S5P SO2/AER_AI/AER_LH, FIRMS, MOD14A1, VNP14A1, WorldPop, GHSL, WorldCover, DEM, S2, Landsat ×2, S1, GPM, MCD19A2, MOD11A1/MYD11A1, SMAP, JRC GSW, HydroSHEDS, Hansen, MERRA-2, Allen Coral Atlas, Google Open Buildings (within Overture) | nothing downloaded; about 55,000 daily images × 24 small geometries over the roadmap | per-volcano daily rows (kB), monthly mosaics (under 1 MB each), thumbnails (about 300 kB each), small event GeoTIFF tiles |
| Files via `archivekit.fetch()` (`file`) | 17: GVP ×2, MIROVA, USGS ×2, COD-AB, PSGC, GEM, NCEI ×2, GLIDE, OurAirports, NGL, eVolv2k, GISTEMP, IGRA, WRI | about 700 MB in all (COD-AB 361 MB, MIROVA 99 MB, IGRA zips about 80 MB, OurAirports 13 MB, GEM 11 MB, USGS 5 MB, WRI 4 MB, the rest kB–MB) | Parquet tables and PMTiles derived from them (§4) |
| Crawled or hand-collected pages and documents (`update-input`) | 23: PHIVOLCS ×3, Tokyo VAAC, DROMIC, NDRRMC, DA, PSA census, DOH, OpenAQ, Wikimedia pageviews, Commons, Chronicling America, OpenAlex, FTS, DOT, HazardHunterPH (link), CALIPSO, GloSSAC, MSVOLSO2L4, CAMS, GloFAS, Slab2, GEBCO, EMSR418, DAHITI, IOC, CMEMS, declassified imagery | PHIVOLCS HTML about 500 MB **[U]**; DROMIC docx about 170 MB for Taal 2020; the rest MB each; all adopted as private archive releases | dated linked figures inside the per-volcano JSON and story JSON; never a consolidated PHIVOLCS table |
| Buckets read by range (`remote-dataset`, `s3://`, `gs://`, `https://`) | 7: Himawari, ERA5, GDELT, OISST, ISD, OSM/Overture, Black Marble, LiCSAR | tens of GB streamed through Actions for event windows only (Himawari about 5 GB per 12-hour event; GDELT GKG about 15 GB per story-month **[U]**); nothing kept raw | per-event animations (a few MB), wind arrows (kB), attention curves (kB), pressure-jump and SST indicators (kB), ring counts (kB) |
| Dropped after the licence check | 4 (`status: retired`): WWLLN (paid), OpenSky (unusable), LaMEVE (permission needed), PhilGEPS (link-only, portal down) | — | a sentence on the About page saying why |

Not used: HazardHunterPH, GeoRiskPH, GISWEB KMZ (terms forbid republishing; link only); PHIVOLCS-LAVA registered downloads (policy); the COMET portal images (CC BY-NC; linked); BoM Darwin VAAC pages (no scraping; linked); the GDELT BigQuery route and USGS frame scanning (paid).

## 2. Processing path

1. **Earth Engine (Python client, the shared `lgu-lights` service account; §7 for the quota rule):** for each of the 24 volcanoes, a FeatureCollection of 50 km boxes and 5/10/15/30 km rings; `reduceRegions` per image over S5P (sum of column × area, valid-pixel count, mean cloud fraction, for both bands), `FIRMS`/`MOD14A1`/`VNP14A1` (count of fire pixels by confidence class, max FRP), later GPM, MCD19A2, LST, SMAP, exported as batch tables to Drive and picked up by the Actions job (fallback: `computeFeatures` under 100 MiB). National monthly S5P mean mosaics exported as GeoTIFF at 1 km. WorldPop/GHSL/WorldCover/DEM/HydroSHEDS/Hansen/Allen reduced per ring once. Sentinel-2 and Landsat least-cloudy composites as `getThumbURL` images for the before/after strip and NDVI differences per story. Every call pins the asset id, the reducer, the scale and the ring geometry hash; these land in the output as columns.
2. **Files via `archivekit.fetch()`:** the 17 `file` entries, with `checks` and hooks; provenance into the run manifest.
3. **Crawlers (pipeline code, polite):** ≤ 1 request/s, `If-Modified-Since`, resumable by page or id, raw HTML written to a dated bundle (`<id>-<date>.tar.zst`) that the archive repo adopts as a release. PHIVOLCS WordPress (about 15,000 pages, 4–5 h at 1 request/s **[U]**, chunked by year), LAVA by id, the earthquake monthly tables (M1.1), the Tokyo VAAC yearly lists and advisories (2010 →, a few thousand pages), DROMIC event posts and their docx files, Wikimedia pageviews and OpenAlex counts (API calls, kB).
4. **Document parsers:** DROMIC docx tables (`python-docx`; evacuation centres, families and persons per province per report), NDRRMC PDF tables at M2 (`pdfplumber`), VAAC text (flight level, dates, polygon), each with committed fixtures and tests. Disagreements between channels on overlapping dates are logged, not silently resolved.
5. **Bucket readers:** ERA5 pressure-level winds from the ARCO Zarr by HTTP range (Replay's pattern); Himawari HSD segments for event windows with `satpy` (M2), streamed and discarded; GDELT 15-minute files for event windows (M2); OISST, ISD, Black Marble, OSM/Overture at M3–M4.
6. **Join and derive:** a `volcano_day` table (volcano, date, fields from every series with coverage flags); episodes (GVP eruption windows; alert-level windows; "strong degassing" windows defined by a documented rule over PHIVOLCS flux, never over satellite columns alone); baselines (rolling 365-day median per series) and anomaly flags; exposure rings; story steps as dated JSON with every figure's source URL.
7. **Data-quality checks (block publishing):** row counts per series within bounds; no duplicate (volcano, date); every PHIVOLCS, VAAC and DROMIC value carries a URL; TROPOMI coverage fraction in [0, 1]; GVP volcano count = 23 and the crosswalk covers all 24; the Taal 2020-01-12 and Kanlaon 2024-06-03 fixtures reproduce known values.
8. **Materialise:** per-volcano JSON (series, bins, episodes, readings EN/JA, sources), story JSON, Parquet (`volcano_day`, `thermal_detections`, `earthquakes_usgs`, `exposure`, `advisories`, `displacement`), PMTiles (volcanoes, rings, thermal detections by month, USGS earthquakes, GEM faults, airports at M2), raster tiles (monthly SO2, hillshade), story assets (thumbnails; animations at M2), `provenance.json` (archivekit `data_version_metadata`, EE asset ids, snapshot date).
9. **Load the API (Java batch, Actions):** the same data version is loaded into the Neon PostGIS schema (volcanoes, eruptions, bulletin fields, advisories, USGS events, thermal detections, SO2 days, episodes, exposure) with a contract test that the API's JSON for a volcano equals the static JSON; the static site never waits for this step.

## 3. PHIVOLCS posture (the licence gate; Q5 = ii)

- Only public pages are read; no registered account is used in the pipeline; no email is sent.
- Every PHIVOLCS-derived number on the site carries "DOST-PHIVOLCS, bulletin of <date>" and the link; alert-level changes are dated, linked markers; no "current" level is ever shown (Q14).
- No consolidated PHIVOLCS-derived file (bulletin fields, earthquake catalogue) is offered anywhere: the values live inside the per-volcano display JSON and the API's per-volcano endpoints, each row with its URL. Because every static file the browser fetches is public, "no bulk file" means no table whose purpose is redistribution, not that the display JSON is hidden.
- Nothing on the site forecasts; the Japanese text is checked against the same rule.
- The raw HTML bundles live only in the private archive (archiving standard §6).

## 4. Data model (published)

- `volcano` (24): `volcano_id` (PHIVOLCS name slug), `gvp_number`, names EN/JA, lat, lon, elevation, type, province, observatory (bool), `series_available` (list).
- `volcano_day`: `volcano_id`, `date`, `so2_mass_pbl_t`, `so2_mass_15km_t`, `so2_valid_frac`, `so2_cloud_frac`, `fire_modis_n`, `fire_viirs_n`, `fire_max_frp_mw`, `vrp_mw` (MIROVA), `eq_usgs_n_30km`, `eq_usgs_max_mag_30km`, `eq_ph_n_30km` (M1.1), `ph_alert_level`, `ph_vt_count`, `ph_tremor_count`, `ph_so2_flux_tpd`, `ph_so2_flux_date`, `ph_plume_m`, `ph_deformation_text`, `ph_source_url`, `vaac_max_fl`, `vaac_n`, `vaac_source_url`, `evacuees_n`, `evacuees_source_url`, `rain_mm` (M2), and `*_source_version` per family.
- `volcano_bins`: `volcano_id`, `date`, `ring` (0–5, 5–10, 10–15, 15–30 km), per-ring sums and counts for SO2 and fire, for the in-browser recompute.
- `episode`: `volcano_id`, `kind` (gvp_eruption, alert_window, strong_degassing), start, end, `vei`, `max_alert`, uncertainty fields from GVP, `source`.
- `exposure`: `volcano_id`, `ring_km`, `year`, `population`, `built_m2`, land-cover shares, `lgus_within` (PSGC list); later `schools_n`, `health_facilities_n`, `buildings_n` as produced-work counts.
- `story`: `story_id`, `volcano_id`, steps (date range, text EN/JA, series shown, figures with URLs), assets (thumbnails, wind arrows, animation).
- `earthquakes_usgs` (national), `thermal_detections` (national, from FIRMS archive with `type`), `faults_gem` (share-alike, separate), `advisories` (Tokyo VAAC), `displacement` (DROMIC rows).

Sizes **[U]**: `volcano_day` 24 × 9,800 days ≈ 235k rows, under 20 MB Parquet; bins about 1 M rows, under 30 MB; detections up to 400k rows, under 20 MB; USGS 27k rows, 3 MB; advisories and displacement under 1 MB; per-volcano JSON under 80 kB gz each (the four deep volcanoes about 120 kB).

## 5. Versions, hosting, provenance, rollback (Q12, Q15)

- Each full run builds `v<N>/`; `latest.json` is flipped only when every check passes; rollback is a pointer flip (archiving standard §5). The app shows "data through <snapshot date>" and "data as of <date>" when an archived copy was used.
- `provenance.json` records the archivekit run manifest, Earth Engine asset ids and date ranges, crawl ranges and bundle release tags, the GVP and MIROVA versions, the commit SHA.
- **No published dataset:** no Hugging Face dataset release, no dataset card as a product, no Zenodo DOI (Q15). The About page lists every source with its attribution and links to the publishers.
- **Hosting:** the app and per-volcano JSON on Cloudflare Pages (static requests free and unlimited, 25 MiB per file, 20,000 files per deployment); tiles, Parquet and story assets on GitHub Pages (primary; 1 GB site, 100 GB per month soft) with a Hugging Face mirror as the fallback base URL (Q12).
- **Private or public Hugging Face repo?** A private repo cannot serve files to an anonymous browser: "Other users who visit the URL of your private repo will receive a 404 - Repo not found error." (https://huggingface.co/docs/hub/repositories-settings), and gated repos need a logged-in account. So the fallback must be a **public** repo. A public repo may be files-only (a dataset card and licence tag are optional: "Each dataset may be documented by the README.md file in the repository", https://huggingface.co/docs/hub/datasets-cards), but public free storage is "Best-effort" beyond "the first few gigabytes" (https://huggingface.co/docs/hub/storage-limits), anonymous resolver requests are capped at 3,000 per 5 minutes per IP, and CORS with Range on the Xet CDN host was only fixed in February 2026 (verify in a browser). Licence implication: whatever is on a public mirror is publicly downloadable, so the mirror holds the same files as GitHub Pages, every file already carries its attribution, and nothing that may not be redistributed (ISD station files, OSM-derived tables, PHIVOLCS consolidated tables) is ever in a data version in the first place. The choice (public files-only HF mirror, or a second GitHub Pages repo, or Cloudflare Pages static assets as the fallback) is OPEN-QUESTIONS Q19.
- **Retention on GitHub Pages:** a data version is about 250 MB at M1 (§10), so at most three versions fit under 1 GB; the previous version is kept for rollback and older ones are deleted from Pages (they stay in the GitHub release that built them).

## 6. InSAR at milestone 2 (outline)

Crop the Taal frame `032D_07536_111313` to a 60 × 60 km window; download only unwrapped phase and coherence for pairs 2019-07 → 2020-07 (about 150 pairs × 2 files **[U]**) in staged Actions jobs; run LiCSBAS (GPL-3, run as a tool, not linked) to a LOS time series with `vstd`; publish the series at a few hundred points plus a velocity raster; show the reference point, LOS geometry and the atmospheric caveat. Acknowledgement "LiCSAR contains modified Copernicus Sentinel data [year]" and the LiCSBAS citation. At M3 the NGL GNSS series for PTGY (Tagaytay) and PLEG (Legazpi) sit beside it.

## 7. Cadence, the shared Earth Engine quota, CI budget [U]

**Earth Engine (Q11: the `lgu-lights` project's 150 EECU-hours per month, shared).** The quota is per Cloud project and "can't be transferred"; exceeding it puts the whole project in restricted mode (slower, not stopped); a Quota Administrator's per-day cap is also per project, so it would throttle Lights too (https://developers.google.com/earth-engine/guides/usage). Lights' data run is manual (`workflow_dispatch`, no cron) and estimated at a few EECU-hours per full rebuild (`../../lgu-lights/docs/DATA-PLAN.md`). Plumes therefore budgets itself in software:

| Rule | Value |
|---|---|
| Plumes' monthly ceiling | 50 EECU-hours (one third of the project quota); the pipeline reads `batch_eecu_usage_seconds` from every task's status, sums the month in a small state file in the data release, and refuses to start a new Earth Engine job above the ceiling (the run fails clearly; nothing else is affected) |
| Per-run cap | 10 EECU-hours; the backfill is chunked by year and by collection so each chunk stays under it |
| Backfill plan | M1: about 5 EECU-hours **[U]** (S5P about 6,000 orbit images, three fire collections about 24,600 daily images, exposure once, a handful of thumbnails) spread over two calendar months if the spike (items 1, 2, 16) measures more than 25; the full roadmap about 25 EECU-hours **[U]** (GPM half-hourly since 1998 is the heavy one and is reduced from the daily product instead) |
| Weekly delta | under 0.5 EECU-hours (seven new days per collection) |
| Run window | Plumes' scheduled job runs Sundays 02:00 PHT; Lights' manual runs are started by Kurt, who sees Plumes' month-to-date figure in the data release before starting one |
| Safety net | a per-day cap of about 20 EECU-hours in the Cloud console, set by Kurt, only to stop a runaway job; it throttles both projects, so it is not the budgeting mechanism |
| Credentials | the existing key `earth-engine-sa-key` at first; a second service account in the same project (free, "Any number of service accounts on a project can be configured to use Earth Engine") with its own key `earth-engine-sa-key-plumes` is recommended so either repo's key can be rotated alone (OPEN-QUESTIONS Q22) |

**GitHub Actions.**

| Trigger | Job | Where | Minutes |
|---|---|---|---|
| one-off | backfill: EE exports (batch, 1–3 h wall, little runner time), PHIVOLCS crawl in yearly chunks (4–5 h), VAAC crawl (under 1 h), DROMIC Taal 2020 (minutes), parse, join, materialise, Java load | public repo (free minutes; 6 h per job, 20 concurrent) | about 8–10 h of runner time once |
| weekly | archivekit health and snapshots (17 file sources) | private archive repo (2,000 shared minutes a month, with Replay's and Lights' archive repos and Akari's CI) | 5–8 a week, about 30 a month, plus a first snapshot of about 15 (COD-AB at zstd 15) |
| weekly | deltas: new bulletins, advisories and earthquake pages, new S5P and fire days, rebuild v<N>, load the API | public repo | 15–25 |
| on push | pipeline tests, web build, Java build and tests, the API-equals-static contract test | public repo | 5–10 per push |
| yearly | WorldPop/GHSL/WorldCover refresh | public repo | 5 |
| M2 events | Himawari event replays: about 5 GB streamed per 12-hour event, under the 14 GB runner disk, one job per event | public repo | 20–40 per event |

Scheduled workflows stop after 60 days without repository activity in a public repo; the weekly job's own commits (the data pointer) count as activity.

## 8. The Java API on free tiers (Q3; verified 2026-10-21)

| Platform | Rule (quoted in [SPIKE-PLAN.md](SPIKE-PLAN.md) sources and `../../typhoon-replay/docs/architecture/SYSTEM-ARCHITECTURE-RESEARCH.md` §7) | Consequence for Plumes |
|---|---|---|
| Render free instance hours | "Render grants 750 Free instance hours to each workspace per calendar month"; spun-down services consume none; exhausted means Render "suspends all of your Free web services until the start of the next month" (https://render.com/docs/free) | Replay's `typhoon-replay-java` already lives in the workspace. Two services fit only if both sleep most of the month: Replay's planned about 6 h per day awake (about 180 h) plus Plumes at 1–3 h per day awake (30–90 h) leaves headroom; but exhaustion suspends **both** projects, so Plumes runs no uptime pinger, lets the service sleep after 15 minutes, and wakes it only from real cache misses and one nightly contract check |
| Render outbound bandwidth | Hobby workspaces get 5 GB per month, shared; with a card on file overage is billed at $0.15 per GB (https://render.com/docs/outbound-bandwidth) | the Pages function in front of the API caches every public read (`Cache-Control: public, s-maxage=86400, stale-while-revalidate`); responses are gzip and 2–20 kB; the target is under 500 MB of origin egress a month for Plumes; spike item 15 measures it |
| Render build minutes | Hobby: 500 Starter minutes a month; exhaustion auto-buys more when a card is on file (https://render.com/docs/build-pipeline) | the Java image is built in GitHub Actions and pushed to GHCR; Render deploys the prebuilt image, so Render build minutes stay near zero |
| Render free Postgres | one per workspace, expires after 30 days | not used; the database is Neon |
| Neon Free | 100 projects; "1 GB/project, 20 GB account total"; 100 CU-hours per project per month; scale to zero after 5 minutes, cannot be disabled; 5 GB public network transfer per project; PostGIS on all plans (https://neon.com/docs/introduction/plans) | Plumes gets its own free project (Singapore) beside Replay's; the M1 catalogue is 100–300 MB with indexes **[U]** (spike item 14 keeps it under 500 MB); API reads are small, so compute and egress stay far under the caps; the Java batch loads a data version in one connection session |
| Cloudflare Pages Functions | 100,000 requests a day shared with Workers on the Free plan; static assets free and unlimited; the Cache API works on Pages Functions, per data centre (https://developers.cloudflare.com/pages/functions/pricing/) | only `/api/*` invokes the function; everything else is static; the function also sets `cf: { cacheEverything, cacheTtl }` on the origin fetch so the standard CDN cache (tiered) serves most hits |

Options if the two Render services do not fit (OPEN-QUESTIONS Q20): co-host Plumes' endpoints inside Replay's Java service (one JVM, two schemas; saves hours, couples the projects), or move Plumes' read API to a Cloudflare Worker with Hyperdrive to Neon (no Java). The recommendation is the second free service with the caps above, revisited if Replay deploys its other three engines.

## 9. Milestone 1 cut and the roadmap

**Milestone 1: the Taal January 2020 story and the overview map, end to end.** Eleven canvas rows, 25 registry entries, chosen because each is needed by a story step or the map, and together they exercise every pipeline shape once (Earth Engine reductions, archivekit files, two crawlers, a document parser, a bucket read):

| # | Canvas row | Registry entries | Why at M1 |
|---|---|---|---|
| 1 | Sentinel-5P TROPOMI SO2 | `s5p-offl-so2` | the SO2 track and the monthly map; story step 2 ("Sentinel-5P sees an SO2 cloud") |
| 2 | NASA FIRMS (VIIRS, MODIS) | `firms-modis`, `modis-mod14a1`, `viirs-vnp14a1` | the thermal track and the national detections layer; step 2 ("thermal sensors light up") |
| 3 | MIROVA v2.5 | `mirova-vrp` | the radiative-power track; one archivekit file with a hook |
| 4 | USGS ComCat | `usgs-comcat-ph-1900-2009`, `usgs-comcat-ph-2010` | the earthquake track; step 2 ("earthquakes per day jump") |
| 5 | Smithsonian GVP | `gvp-volcanoes-ph`, `gvp-eruptions-ph` | the 24 points, facts and the eruption band (VEI 4) |
| 6 | WorldPop, GHSL, WorldCover, DEM, with COD-AB and PSGC | `worldpop-100m`, `ghsl-r2023a`, `esa-worldcover-v200`, `copernicus-dem-glo30`, `cod-ab-phl-gdb`, `psgc-cities-municipalities` | step 6 ("about 459,000 people within 14 km"), the rings, the hillshade basemap, LGU names |
| 7 | PHIVOLCS public bulletins | `phivolcs-bulletins`, `phivolcs-lava-bulletins` (+ `hazardhunterph` as the link) | the dated alert markers of steps 2 and 4 (1 → 4 on 12 January, 4 → 3 on 26 January), earthquake counts, SO2 flux, deformation sentences for step 1 |
| 8 | VAAC advisories (Tokyo) | `vaac-tokyo-advisories` | step 3 ("aviation advisories report the plume height"); 45 advisories for Taal 2020, open JMA archive, small |
| 9 | DSWD DROMIC | `dswd-dromic-reports` | step 3 ("DSWD reports count evacuees"); 70 docx reports for Taal 2020; the one document parser at M1 |
| 10 | Sentinel-2 and Landsat | `s2-sr-harmonized`, `landsat-c2-l2` | step 5 ("before-and-after satellite images show the crater lake gone"); four thumbnails and an NDVI difference per story |
| 11 | ERA5 winds | `era5-pressure-levels` | the story canvas's wind arrows (why vog went where it did); Replay's reader pattern; a few MB per story day |

Plus `gem-active-faults` (a one-file map layer already in the draft; kept at M1 because it costs nothing) and the InSAR row as links (`licsar-taal-032d` is listed so the health check watches the paths). Deferred from the core: the PHIVOLCS monthly earthquake tables (`phivolcs-earthquakes`) to **M1.1**, because the bulletins already carry the volcanic-earthquake counts the story needs and the monthly tables add a second crawler and 150k rows (OPEN-QUESTIONS Q24). The Kanlaon 2024 story follows at M1.1 on the same machinery (Q29).

**Roadmap** (registry entries tagged `[M2]`, `[M3]`, `[M4]`; each milestone ends with the §7 review in WORKFLOW.md):

| Milestone | Theme | Sources | Notes |
|---|---|---|---|
| M1.1 | second story, national counts | PHIVOLCS earthquake tables; the Kanlaon 2024 story on the M1 sources; national layers if deferred by the spike | no new source shapes |
| M2 | the plume and the ground; the Java API's second iteration | Himawari event replays (5 events × 12 h), Sentinel-5P AER_AI and AER_LH, GIBS gallery, GPM IMERG, Landsat lake temperature, S1 change detection, LiCSAR Taal crop, EMSR418, NDRRMC sitreps (hand-collected), NCEI significant eruptions, OpenAQ + MCD19A2 (if Philippine stations exist), Wikipedia pageviews + GDELT, MSVOLSO2L4 (pre-2018 SO2), JRC GSW, MODIS LST, OurAirports, Commons photos | the first bucket streaming (Himawari, GDELT) and the first PDF parser; one new registration (OpenAQ) |
| M3 | people, response, deep earth, the coast | OSM, HRSL, Overture/Google/Microsoft buildings, DOH, PSA barangay census (hand), Lights poverty, Black Marble daily, FTS, ReliefWeb (appname) + GLIDE, NGL GNSS, Slab2 (hand), GloSSAC, eVolv2k, GISTEMP, NCEI tsunamis, GEBCO (hand), Allen Coral Atlas, Hansen, Raspberry Shake, EarthScope, CALIPSO, OpenAlex | the ODbL produced-work rule and the hand-download checklist (Q27) |
| M4 | water, the long air record, archives, the economy | DAHITI, Sentinel-3 OLCI, HydroSHEDS, GloFAS, SMAP, CAMS EAC4, MERRA-2, IASI, IGRA, ISD (indicators only), IOC sea level, CMEMS, OISST, Chronicling America, declassified imagery (scanned frames only), WRI power plants, DOT arrivals, DA figures (links), Global Fishing Watch if Q25 allows | most registrations fall here (ECMWF ADS/EWDS, Copernicus Marine, IOC, DAHITI, EROS) |
| dropped | — | WWLLN (paid), OpenSky (unusable), LaMEVE (permission needed), PhilGEPS (link-only, portal down) | listed on the About page with the reason |

## 10. Size and quota totals [U]

| Where | M1 | Full roadmap | Limit | Notes |
|---|---|---|---|---|
| A data version on GitHub Pages (tiles, Parquet, story assets) | about 250 MB: Parquet 75 MB, PMTiles 20 MB, SO2 mosaic tiles under 100 MB (split per year for the 25 MiB cap), hillshade tiles about 30 MB, story assets about 2 MB | about 400 MB: plus event animations (5 × 5 MB), GIBS galleries (about 15 MB), S1 event tiles, the InSAR crop (about 10 MB), GEBCO tiles (about 20 MB), small tables | 1 GB per site; 100 GB a month soft | at most two or three versions kept on Pages; older ones stay in the release that built them |
| Cloudflare Pages (app + per-volcano and story JSON) | about 300 kB gz app bundle + 24 JSON files (about 3 MB) + story JSON | plus 24 × more fields; still under 10 MB | 25 MiB per file; 20,000 files; static requests unlimited | nothing near the limits |
| Hugging Face mirror (if Q19 keeps it) | the same about 250 MB per version | about 400 MB per version | public storage "best-effort" beyond "the first few gigabytes"; 3,000 anonymous resolver requests per 5 minutes per IP | two versions mirrored at most |
| Private archive releases (`abrycta/plumes-archive`) | about 0.9 GB: COD-AB 361 MB, MIROVA 99 MB, PHIVOLCS HTML bundles about 500 MB raw → about 50 MB zstd, DROMIC docx 170 MB, GEM 11 MB, USGS 5 MB, VAAC pages under 5 MB | about 2 GB: plus IGRA 80 MB, HRSL 56 MB, Slab2 about 50 MB, GEBCO box tens of MB, EMSR418 under 100 MB, PSA census about 30 MB, DOH a few MB, small files | 2 GiB per asset; 1,000 assets per release; total unlimited | weekly snapshots only re-upload changed files |
| Earth Engine (shared project) | backfill about 5 EECU-hours; weekly under 0.5 | backfill about 25 EECU-hours over several months; weekly under 1 | 150 EECU-hours a month per project, shared with Lights | Plumes' own ceiling 50 a month, 10 per run (§7) |
| GitHub Actions, public repo | one-off 8–10 h; weekly 15–25 min; CI 5–10 min per push | plus 20–40 min per Himawari event (M2), yearly refreshes | free on standard runners; 6 h per job | the crawl is chunked by year |
| GitHub Actions, private archive repo | about 30 min a month plus a 15-minute first snapshot | about 45 min a month | 2,000 min a month shared across the account's private repos | Replay's and Lights' archive repos use about 20 each |
| Neon (own free project) | 100–300 MB catalogue; API compute minutes a day | under 500 MB | 1 GB per project, 20 GB account; 100 CU-hours; 5 GB egress | spike item 14 |
| Render (shared workspace) | Plumes awake 30–90 h a month; origin egress under 500 MB | same | 750 instance hours and 5 GB a month per workspace, shared with Replay | spike items 13 and 15 |
| Browser, first view | app 300 kB gz + volcano points and rings under 50 kB + basemap tiles | same | — | under 1 s warm from Manila (Lights measured 36–50 ms p50 to Pages from PH) |
| Browser, volcano page | one JSON under 80 kB gz (120 kB for Taal, Mayon, Kanlaon, Bulusan) + tiles by viewport | plus story assets on demand | — | the Web Worker recomputes rings from bins; nothing is fetched at interaction time |

What stays server-side (never reaches the browser): every raw raster and bucket read, the PHIVOLCS HTML, the DROMIC and NDRRMC documents, the OSM/Overture/building extracts (ODbL derivative databases), the ISD station files (WMO Resolution 40), the full MIROVA and USGS CSVs, the PostGIS catalogue. What reaches the browser: the per-volcano and story JSON, PMTiles and raster tiles by viewport, Parquet only through the API or a future table view, thumbnails and animations.

## 11. Resources to create (after the spike; none created now)

- Public repo `abrycta/plumes`; private `abrycta/plumes-archive` (`archivekit init plumes`); `ARCHIVE_READ_TOKEN` in both; `health.token_expires` set.
- Earth Engine: the existing `lgu-lights` service account key as a GitHub secret on `abrycta/plumes` (Q11); optionally a second service account in the same project (Q22).
- FIRMS MAP_KEY (free, email) as a GitHub secret; the Earthdata login (exists) for the FIRMS archive tool, CALIPSO, GloSSAC and MSVOLSO2L4.
- Cloudflare Pages project with the `/api/*` function; CNAME `plumes.krtmtthw.dev` at Porkbun (listed before any DNS change); GitHub Pages for tiles; the Hugging Face mirror per Q19.
- Neon project `plumes` (free, Singapore, PostGIS); Render free web service `plumes-java` in the existing workspace deploying a GHCR image; GHCR package on the public repo.
- Later registrations per milestone (OPEN-QUESTIONS Q28): OpenAQ (M2), ReliefWeb appname and OpenAlex key (M3), ECMWF ADS/EWDS, Copernicus Marine, IOC, DAHITI, EROS (M4).
