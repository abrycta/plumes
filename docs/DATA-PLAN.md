# Data plan

Status: 2026-10-21, proposal for the recommended candidate (volcanoes). Facts were checked on the day ([RESEARCH.md](RESEARCH.md), [`research/`](research/)); **[U]** marks an estimate to be replaced by the spike ([SPIKE-PLAN.md](SPIKE-PLAN.md)). The registry draft is [sources-draft.yaml](sources-draft.yaml).

## 0. Summary

| Decision (proposed) | Choice | Why |
|---|---|---|
| Unit of analysis | volcano × day (and volcano × month for the map scrubber); 24 PHIVOLCS active volcanoes, coordinates from GVP, a hand-made crosswalk table | the series are event-driven and daily; 24 units keep every output small |
| Time span | 2000-01-01 → the snapshot date; each series starts when its instrument does (MODIS 2000-11, VIIRS 2012-01, USGS 1900, TROPOMI 2018-12, bulletins 2017-09, LAVA 2022) | an honest "20 years" that says which years each series covers |
| SO2 | TROPOMI OFFL L3 on Earth Engine: daily column mass (t) and valid-pixel fraction inside a 50 km box and in 10/20/30 km rings, both bands; monthly national mean mosaics at 1 km | open licence, the only daily SO2 source; column, not flux, labelled as such |
| Thermal | Earth Engine `FIRMS`, `MOD14A1`, `VNP14A1` daily counts and max FRP within 5/10/20 km; FIRMS archive CSV (with `type`) for the volcanic subset; MIROVA Dataset v2.5 (CC BY 4.0) for VRP | three independent views; the fire caveat shown |
| Earthquakes | USGS CSV for the Philippine box since 1900 (paged by year); PHIVOLCS monthly tables 2016 → crawled; counts and max magnitude within 10/30 km per day | public domain backbone plus the national agency's locations |
| Ground reports | PHIVOLCS bulletins: WordPress prose 2017-09 → 2024, LAVA structured 2022 → ; parsed to daily fields; alert-level history reconstructed | the official figures beside the satellites |
| Eruptions | GVP WFS (volcanoes and eruptions, Philippines filter) | VEI and dated episodes with uncertainty |
| Exposure | WorldPop, GHSL, WorldCover, DEM reduced in Earth Engine per ring; COD-AB for LGUs within rings | descriptive counts with CC BY attribution |
| Deformation | milestone 1: links and bulletin statements; milestone 2: LiCSBAS crop at Taal | tens of GB per frame cannot be mirrored or archived |
| Publishing | immutable `v<N>/` folders: per-volcano JSON, Parquet tables, PMTiles, raster tiles; `latest.json` pointer; Hugging Face dataset `permission-alluring/<name>` with per-file licences; Zenodo DOI per release | the Lights pattern; small outputs |
| Archiving | `archivekit` registry; private `abrycta/<name>-archive`; file sources snapshotted weekly; crawled HTML bundled and adopted as releases; rasters never archived | the portfolio standard |
| Cadence | weekly: new bulletins, earthquakes, S5P and fire days; yearly: WorldPop/GHSL; on release: GVP, MIROVA | small deltas; one full backfill |

## 1. Sources, access, licences, volumes

| Id | Source | Kind (registry) | Access | Licence and attribution | Raw volume | Published derivative |
|---|---|---|---|---|---|---|
| `gvp-volcanoes-ph`, `gvp-eruptions-ph` | Smithsonian GVP WFS, Philippines filter | `file` (CSV) | `webservices.volcano.si.edu` GetFeature CSV | Smithsonian terms (non-commercial, cite) [U wording]; `AccessConstraints NONE` | 23 rows; 233 rows | derived episode table with citation, in a separately licensed file |
| `mirova-vrp` | MIROVA Dataset v2.5, `VRP_GLOBAL_ARCHIVE_2025.csv` | `file` | OSF `https://osf.io/download/53zwm/` | CC BY 4.0 | 98.6 MB global | Philippine subset, daily VRP per volcano |
| `usgs-comcat-ph` | USGS FDSN CSV, 4–22°N 116–128°E, 1900 → | `file` (CSV), two links by period, plus a yearly delta link | `earthquake.usgs.gov/fdsnws/event/1/query?format=csv&...` | US public domain, credit USGS | 27k rows, about 5 MB | national catalogue Parquet; per-volcano counts |
| `gem-active-faults` | GEM Global Active Faults GeoJSON | `file` | GitHub raw | CC BY-SA 4.0 (`share_alike: true`) | 10.6 MB | the Philippine subset as its own PMTiles layer, credited |
| `cod-ab-phl` | OCHA COD-AB PHL v03 gdb | `file` | HDX (same entries as Lights) | CC BY-IGO | 361 MB | LGUs within rings; simplified boundaries |
| `phivolcs-bulletins` | PHIVOLCS daily and eruption bulletins (WordPress) | `update-input` (crawled; raw bundles adopted as archive releases) | `www.phivolcs.dost.gov.ph/category/volcano-bulletin/page/N/` | no stated terms; government work (RA 8293 §176); display with citation, no bulk file published pending PHIVOLCS's answer | about 15,000 pages [U], about 300 MB HTML [U] | daily fields per volcano (not published as a bulk file at v1) |
| `phivolcs-lava-bulletins` | PHIVOLCS-LAVA 24-hour bulletins | `update-input` (crawled by id) | `wovodat.phivolcs.dost.gov.ph/bulletin/activity-{tvo,mvo,kvo,bvo}?bid=N&lang=en` | portal data policy (cite DOST-PHIVOLCS; no redistribution of registered data; no public forecasting); public pages only | about 7,000 pages since 2022 [U], 15 kB each | same |
| `phivolcs-earthquakes` | PHIVOLCS monthly earthquake tables | `update-input` (crawled) | `earthquake.phivolcs.dost.gov.ph/EQLatest-Monthly/YYYY/YYYY_Month.html` | as above | about 130 months, 0.5–2.8 MB each, about 150k rows [U] | per-volcano counts; a national Parquet is published only after PHIVOLCS's answer |
| `s5p-so2` | `COPERNICUS/S5P/OFFL/L3_SO2` | `remote-dataset` (Earth Engine; STAC probe) | Earth Engine | Copernicus free, full, open; "Contains modified Copernicus Sentinel data [Year]" | about 6,000 orbit images over PH [U] | daily box/ring mass and coverage; monthly mosaics |
| `firms-modis`, `mod14a1`, `vnp14a1` | fire and thermal anomalies | `remote-dataset` (Earth Engine) | Earth Engine; FIRMS archive CSV by email for `type` | NASA open; LANCE disclaimer | 9,500 + 9,700 + 5,400 daily images | daily counts and FRP per ring; national monthly detections (PMTiles) |
| `worldpop`, `ghsl-pop`, `ghsl-built`, `worldcover`, `cop-dem` | exposure and context | `remote-dataset` (Earth Engine) | Earth Engine | CC BY 4.0; EU open; CC BY 4.0; free licence | reduced once per ring | exposure table (24 × rings × years) |
| `licsar-taal` (milestone 2) | LiCSAR frame `032D_07536_111313` | `remote-dataset` (≥ 2 links: CEDA and JASMIN) | HTTP | Copernicus derived works; acknowledgement | tens of GB [U] | a cropped LOS time series table and a velocity raster |

Not used: HazardHunterPH, GeoRiskPH, GISWEB KMZ (terms forbid republishing; link only); PHIVOLCS-LAVA registered downloads (policy); OMI/OMPS SO2 (not on GEE; later); MOUNTS (images only).

## 2. Processing path

1. **Earth Engine (Python client, service account):** for each of the 24 volcanoes, a FeatureCollection of 50 km boxes and 5/10/20/30 km rings; `reduceRegions` per image over S5P (sum of column × area, valid-pixel count, mean cloud fraction, for both bands), `FIRMS`/`MOD14A1`/`VNP14A1` (count of fire pixels by confidence class, max FRP), exported as batch tables to Drive, picked up by the Actions job. National monthly S5P mean mosaics exported as GeoTIFF at 1 km. WorldPop/GHSL/WorldCover/DEM reduced per ring once. Every call pins the asset id, the reducer, the scale and the ring geometry hash; these land in the output as columns. Estimated one-off cost: a few EECU-hours [U]; weekly deltas: minutes.
2. **Files via `archivekit.fetch()`:** GVP, MIROVA, USGS, GEM, COD-AB, with `checks` and hooks; provenance into the run manifest.
3. **Crawlers (pipeline code, polite):** ≤ 1 request/s, `If-Modified-Since`, resumable by page or id, raw HTML written to a dated bundle (`phivolcs-bulletins-<date>.tar.zst`) that the archive repo adopts as a release (as Lights did for the hand-downloaded PSA file). A full first crawl of about 15,000 WordPress pages takes about 4–5 hours at 1 request/s [U], run once, chunked by year to fit the 6-hour job limit; weekly deltas are tens of pages.
4. **Parsers:** per era (WordPress prose 2017–2024; LAVA sections 2022 → ; eruption bulletins), each with committed fixtures and tests; output one row per (volcano, bulletin date) with typed fields and the source URL. Disagreements between the two channels on overlapping dates are logged, not silently resolved.
5. **Join and derive:** a `volcano_day` table (volcano, date, fields from every series with coverage flags); episodes (GVP eruption windows; alert-level windows; "strong degassing" windows defined by a documented rule over PHIVOLCS flux, never over satellite columns alone); baselines (rolling 365-day median per series) and anomaly flags; exposure rings.
6. **Data-quality checks (block publishing):** row counts per series within bounds; no duplicate (volcano, date); every PHIVOLCS value carries a URL; TROPOMI coverage fraction in [0, 1]; GVP volcano count = 23 and the crosswalk covers all 24; the Taal 2020-01-12 and Kanlaon 2024-06-03 fixtures reproduce known values (regression tests on real events).
7. **Materialise:** per-volcano JSON (series, bins, episodes, readings EN/JA, sources), Parquet (`volcano_day`, `thermal_detections`, `earthquakes_usgs`, `exposure`), PMTiles (volcanoes, rings, thermal detections by month, USGS earthquakes, GEM faults), raster tiles (monthly SO2), `provenance.json` (archivekit `data_version_metadata`, EE asset ids, snapshot date).

## 3. PHIVOLCS posture (the licence gate)

- Only public pages are read; no registered account is used in the pipeline.
- Every PHIVOLCS-derived number on the site carries "DOST-PHIVOLCS, bulletin of <date>" and the link.
- No bulk PHIVOLCS-derived file (bulletin fields, earthquake catalogue) is published in the Hugging Face dataset or the repo at v1; those tables stay inside the app's per-volcano JSON (display) until PHIVOLCS answers an email (draft on request) asking whether a derived daily table may be published with attribution. If the answer is no, the JSON keeps the values as displayed figures with links, or they are withdrawn and the satellite and GVP series stand alone; the site says which.
- Nothing on the site forecasts; the Japanese text is checked against the same rule.
- The raw HTML bundles live only in the private archive (archiving standard §6: archived copies are never redistributed).

## 4. Data model (published)

- `volcano` (24): `volcano_id` (PHIVOLCS name slug), `gvp_number`, names EN/JA, lat, lon, elevation, type, province, observatory (bool), `series_available` (list).
- `volcano_day`: `volcano_id`, `date`, `so2_mass_pbl_t`, `so2_mass_15km_t`, `so2_valid_frac`, `so2_cloud_frac`, `fire_modis_n`, `fire_viirs_n`, `fire_max_frp_mw`, `vrp_mw` (MIROVA), `eq_usgs_n_30km`, `eq_usgs_max_mag_30km`, `eq_ph_n_30km`, `ph_alert_level`, `ph_vt_count`, `ph_tremor_count`, `ph_so2_flux_tpd`, `ph_so2_flux_date`, `ph_plume_m`, `ph_deformation_text`, `ph_source_url`, and `*_source_version` per family.
- `volcano_bins`: `volcano_id`, `date`, `ring` (0–5, 0–10, 10–20, 20–30 km), per-ring sums and counts for SO2 and fire, for the in-browser recompute.
- `episode`: `volcano_id`, `kind` (gvp_eruption, alert_window, strong_degassing), start, end, `vei`, `max_alert`, uncertainty fields from GVP, `source`.
- `exposure`: `volcano_id`, `ring_km`, `year`, `population`, `built_m2`, land-cover shares, `lgus_within` (PSGC list).
- `earthquakes_usgs` (national), `thermal_detections` (national, from FIRMS archive with `type`), `faults_gem` (share-alike, separate).

Sizes [U]: `volcano_day` 24 × 9,800 days ≈ 235k rows, under 20 MB Parquet; bins about 1 M rows, under 30 MB; detections up to 400k rows, under 20 MB; USGS 27k rows, 3 MB; per-volcano JSON under 80 kB gz each.

## 5. Versions, provenance, rollback

- Each full run builds `v<N>/`; `latest.json` is flipped only when every check passes; rollback is a pointer flip (archiving standard §5). The app shows "data through <snapshot date>" and "data as of <date>" when an archived copy was used.
- `provenance.json` records the archivekit run manifest, Earth Engine asset ids and date ranges, crawl ranges and bundle release tags, the GVP and MIROVA versions, the commit SHA.
- Releases are tagged `data-v<N>`; Zenodo mints a DOI; the Hugging Face dataset mirrors the Parquet with a card listing per-file licences (CC BY 4.0 for satellite-derived tables with the Copernicus and NASA notices; the GVP-derived episode file under the Smithsonian non-commercial terms with citation; the GEM file CC BY-SA 4.0; no PHIVOLCS bulk file at v1).

## 6. InSAR at milestone 2 (outline)

Crop the Taal frame `032D_07536_111313` to a 60 × 60 km window; download only unwrapped phase and coherence for pairs 2019-07 → 2020-07 (about 150 pairs × 2 files [U]) in staged Actions jobs; run LiCSBAS (GPL-3, run as a tool, not linked) to a LOS time series with `vstd`; publish the series at a few hundred points plus a velocity raster; show the reference point, LOS geometry and the atmospheric caveat. Acknowledgement "LiCSAR contains modified Copernicus Sentinel data [year]" and the LiCSBAS citation. The same tooling serves the subsidence runner-up if it is ever built.

## 7. Cadence and CI budget [U]

| Trigger | Job | Where | Minutes |
|---|---|---|---|
| one-off | backfill: EE exports (batch, 1–3 h wall, little runner time), crawl in yearly chunks (4–5 h total), parse, join, materialise | public repo (free minutes) | about 6–8 h of runner time once |
| weekly | archivekit health and snapshots (GVP, MIROVA, USGS, GEM) | private archive repo (2,000 shared minutes) | 3–5 |
| weekly | deltas: new bulletins and earthquake pages, new S5P and fire days, rebuild v<N> | public repo | 10–20 |
| yearly | WorldPop/GHSL/WorldCover refresh | public repo | 5 |

## 8. Resources to create (after decisions; none created now)

- Public repo `abrycta/<name>`; private `abrycta/<name>-archive` (`archivekit init`); `ARCHIVE_READ_TOKEN` in both; `health.token_expires` set.
- A Google Cloud project registered for noncommercial Earth Engine with its own service account (quota isolation from `lgu-lights`), key in the Keychain and as a GitHub secret; or reuse the Lights account (OPEN-QUESTIONS Q11).
- FIRMS MAP_KEY (free, email) as a GitHub secret; the Earthdata login (exists) for the FIRMS archive tool.
- Cloudflare Pages project; CNAME `<name>.krtmtthw.dev` at Porkbun (listed before any DNS change); GitHub Pages for tiles; Hugging Face dataset `permission-alluring/<name>`; Zenodo integration.
- For milestone 2+: Neon project `<name>` (free), Render free web service (Singapore), only if the Java API is built.
