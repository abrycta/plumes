# Twenty sources, queried in place

**Decided 2026-10-21:** Kurt accepted the 20 (DECISIONS.md Q30), with Black Marble and the Lights poverty join at M1.1, and added four more from NASA-EE-CANDIDATES.md (Q31): 24 sources. The text below is kept as the proposal it was.

Status: 2026-10-21, a proposal for Kurt (OPEN-QUESTIONS.md **Q30**); nothing here is decided, and [DECISIONS.md](DECISIONS.md) is unchanged. Kurt's brief, in two steps the same day: first "look for alternative databases that do not require downloads", then **Plumes should have 20 sources in total**, chosen to prefer query-in-place access (Earth Engine, APIs, cloud-optimised remote reads), all free, with the Taal January 2020 story and the overview map of all 24 volcanoes still working end to end.

The 20 are marked in [sources-draft.yaml](sources-draft.yaml) with a `# proposed_keep: true` comment under their id. The registry schema allows no extra fields, so the mark is a comment, and the registry still validates (`archivekit validate-registry`: no problems). No other entry is changed or deleted. Every access route marked "tested" was probed live on 2026-10-21 with a small query; samples stay in the session scratchpad, not in the repo. **[U]** marks an estimate.

## The 20

USGS ComCat is one source kept as two registry entries (the FDSN service caps a query at 20,000 events), so the 20 sources are 21 entries.

| # | Source (registry id) | Access (no-download unless noted) | Licence (registry verdict, quoted where the publisher words it) | Feeds | Milestone |
|---|---|---|---|---|---|
| 1 | Smithsonian GVP volcanoes (`gvp-volcanoes-ph`) | GeoServer **WFS query** with `CQL_FILTER=Country='Philippines'` (23 rows) | open-with-conditions: Smithsonian terms (non-commercial with citation; the terms page is still to be re-read by hand); WFS capabilities "Fees NONE", "AccessConstraints NONE" | the 24 map points (with the crosswalk), facts | M1 |
| 2 | Smithsonian GVP eruptions (`gvp-eruptions-ph`) | the same **WFS**, filtered by volcano number (233 rows) | as above | the eruptions band, VEI, the episodes table | M1 |
| 3 | PHIVOLCS bulletins, WordPress 2017-09 → 2024 (`phivolcs-bulletins`) | **polite per-page crawl**: no API exists | government work (RA 8293 s.176.1); every figure cited with its link, no bulk file (Q5 ii) | alert-level markers, VT counts, SO₂ flux, deformation sentences (story steps 1, 2 and 4) | M1 |
| 4 | PHIVOLCS LAVA bulletins 2022 → (`phivolcs-lava-bulletins`) | **per-id crawl** of public pages (registered datasets not used) | as above | alert markers and fields after 2022 | M1 |
| 5 | USGS ComCat (`usgs-comcat-ph-1900-2009`, `usgs-comcat-ph-2010`) | **FDSN event API** with a bounding box and time window | open: "U.S. public domain (USGS-authored data)" | the earthquake track and map layer | M1 |
| 6 | Sentinel-5P TROPOMI SO₂ (`s5p-offl-so2`) | **Earth Engine** `COPERNICUS/S5P/OFFL/L3_SO2`, reduced per ring and day | open: Copernicus Sentinel Data Legal Notice (free, full and open) | the SO₂ track and the monthly national map | M1 |
| 7 | Sentinel-5P aerosol index (`s5p-offl-aer-ai`) | **Earth Engine** `COPERNICUS/S5P/OFFL/L3_AER_AI` | as above | the satellite ash and aerosol view beside the VAAC heights | M2 |
| 8 | NASA FIRMS (`firms-modis`) | **Earth Engine** `FIRMS` for per-ring counts; **FIRMS area API** `…/api/area/csv/<MAP_KEY>/{MODIS_SP,VIIRS_SNPP_SP}/116,4,128,22/5/<date>` ("1 .. 5 - number of days to query at one time") for the national detections layer, instead of the emailed archive download | open: NASA open data (LANCE/FIRMS), the LANCE disclaimer reproduced | the thermal track and the national detections layer | M1 |
| 9 | MODIS MOD14A1 (`modis-mod14a1`) | **Earth Engine** `MODIS/061/MOD14A1` (FireMask, **MaxFRP**) | open: "no restrictions on subsequent use, sale, or redistribution" (LP DAAC) | radiative power (max FRP) since 2000, in place of MIROVA | M1 |
| 10 | VIIRS VNP14A1 (`viirs-vnp14a1`) | **Earth Engine** `NASA/VIIRS/002/VNP14A1` | open: NASA open data (LP DAAC) | the second thermal sensor since 2012; continuity when Terra ends in 2027 | M1 |
| 11 | Tokyo VAAC advisories (`vaac-tokyo-advisories`) | **per-advisory crawl** of the open JMA text archive (1–3 kB pages; no API exists) | open-with-conditions: "The user must cite the source when using the Content." (JMA; compatible with CC BY 4.0) | plume height (story step 3) | M1 |
| 12 | DSWD DROMIC reports (`dswd-dromic-reports`) | **per-report fetch** of the docx, parsed and discarded (the one remaining document read; no API exists) | open: government work (RA 8293 s.176.1) | evacuee counts (story step 3) | M1 |
| 13 | WorldPop (`worldpop-100m`) | **Earth Engine** `WorldPop/GP/100m/pop` (2000–2020) plus the community-catalogue `projects/sat-io/open-datasets/WORLDPOP/pop` (Global 2, 2015–2030), so the 2021+ GeoTIFF download goes away | open: CC BY 4.0 ("This work is licensed under a Creative Commons Attribution 4.0 International License", https://gee-community-catalog.org/projects/worldpop/) | people within each ring (story step 6) | M1 |
| 14 | OCHA COD-AB (`cod-ab-phl-gdb`) | **HTTP range read** into HDX's `phl_admin_boundaries.shp.zip` (S3 answers `206`), fetching only the member `phl_admin3.dbf`: **119,401 bytes instead of 361 MB**. That gives 1,642 LGUs with `adm3_pcode` (PSGC-aligned), names, area and `center_lat`/`center_lon` (tested) | open-with-conditions: "Creative Commons Attribution for Intergovernmental Organisations (CC BY-IGO)" (HDX `package_show`) | LGU names within N km; the PSGC key for the Lights join | M1 |
| 15 | Copernicus DEM GLO-30 (`copernicus-dem-glo30`) | **Earth Engine** `COPERNICUS/DEM/GLO30_2024_1` | open-with-conditions: Copernicus DEM licence with its mandatory notice | hillshade for the overview map, ring terrain | M1 |
| 16 | Sentinel-2 L2A (`s2-sr-harmonized`) | **Earth Engine** `COPERNICUS/S2_SR_HARMONIZED`, `getThumbURL` composites | open: Copernicus Sentinel Data Legal Notice | before and after imagery (story step 5) | M1 |
| 17 | ERA5 winds (`era5-pressure-levels`) | **ARCO-ERA5 Zarr, HTTP range reads** of small windows (Replay's reader pattern) | open: CC BY 4.0 | wind arrows: where the plume and vog went | M1 |
| 18 | GPM IMERG (`gpm-imerg-v07`) | **Earth Engine** `NASA/GPM_L3/IMERG_V07`, reduced to daily rain per volcano box | open: "All NASA-produced data from the GPM mission is made freely available for the public to use." | the rainfall and lahar-context track | M2 |
| 19 | NASA Black Marble daily (`black-marble-vnp46a2`) | **Earth Engine** `NASA/VIIRS/002/VNP46A2` (2012-01-19 → 2026-10-11, catalogue page), instead of LAADS HDF5 tiles | open: "LP DAAC NASA data are freely accessible; … it is requested that the author cite the datasets" | the power-cut and recovery track; **the night-lights link to Lights** | M3 (recommended M1.1) |
| 20 | Lights poverty estimates (`lights-poverty-estimates`) | **the Lights data release**, read by PSGC (own data; a few kB per volcano) | open: CC BY 4.0 with Lights' attribution block | "who lives nearby": **the poverty link to Lights** | M3 (recommended M1.1) |

**Track coverage:** alert markers 3, 4; earthquakes 5; SO₂ 6; thermal and radiative power 8, 9, 10; eruptions 1, 2; exposure and population 13, 14, 15; ash and plume 11, 7; evacuees 12; before and after 16; winds 17; Lights 19, 20; lahar context 18.

**Taal January 2020 end to end:** step 1 (deformation sentences: 3), step 2 (SO₂, thermal, earthquakes: 6, 8–10, 5), step 3 (plume height and evacuees: 11, 12, with wind arrows from 17), step 4 (alert markers: 3), step 5 (crater lake before and after: 16), step 6 (people within 14 km and the LGUs: 13, 14). **The overview map:** 24 points (1 plus the crosswalk), hillshade (15), the monthly SO₂ layer (6), thermal detections (8) and earthquakes (5).

**What still downloads, and why it stays:** the three crawlers (3, 4, 11) and the DROMIC reports (12) are irreplaceable. They are the official alert levels, plume heights and evacuee counts, and none has an API. Each is fetched page by page or report by report, never as a bulk file. Their dated bundles are the query results that the archive keeps. Everything else is an Earth Engine reduction, an API query or a range read.

**Registrations:** only the free FIRMS MAP_KEY (M1, already in Q28). Plumes no longer needs the Earthdata login (Black Marble moves to Earth Engine), OpenAQ, ReliefWeb, OpenAlex, ECMWF, Copernicus Marine, IOC, DAHITI or EROS. Every source is free; nothing needs a card or billing.

## Notable cuts and why

The other 65 active entries leave the plan; 4 more were already retired. They stay in the registry, unmarked, as history.

- **MIROVA v2.5:** a 99 MB whole-file pull with no query route. Radiative power now comes from the MODIS and VIIRS MaxFRP on Earth Engine (9, 10). What is lost is MIROVA's volcano-tuned VRP algorithm, which could return as one small archived subset if Kurt wants it.
- **PHIVOLCS monthly earthquake tables:** a second crawler and 150k rows. USGS plus the bulletins' volcanic-earthquake counts carry the track (this was already deferred, Q24).
- **GHSL, WorldCover, Landsat, PSGC JSON, GEM faults:** they repeat what the 20 already cover (WorldPop for exposure, Sentinel-2 for every event since 2017, the COD-AB pcode for PSGC) or are map decoration (land cover, the share-alike fault layer).
- **Himawari event replays, LiCSAR InSAR, Sentinel-5P layer height, GIBS gallery, Sentinel-1 change:** Himawari has no query route for past dates (NASA GIBS serves Himawari tiles only for a recent rolling window: the capabilities start at 2026-09-08), and its HSD scans are 780 MB. InSAR is per-pair files. The rest are second views of tracks already covered. InSAR stays as plain links to the COMET portal and the PHIVOLCS deformation sentences, which are not counted as sources.
- **Hand downloads:** NDRRMC, DOH, the PSA barangay census, Slab2, GEBCO, EMSR418, declassified imagery.
- **The attention track:** GDELT, Wikipedia pageviews, OpenAlex, Commons, Chronicling America.
- **Every M4 context source:** CAMS, GloFAS, ocean colour, OISST, ISD, IGRA, IASI, IOC, DAHITI, MERRA-2, SMAP and the others.
- **HazardHunterPH:** stays a link on every page; it was never a data source.

If a cut source is wanted back later, these query-in-place routes were confirmed on 2026-10-21:

| Cut source | Route |
|---|---|
| OSM and DOH facilities | **Overpass** with `around:` and `[date:]`: 121 schools within 15 km of Taal on 2020-01-01; ODbL; policy "about 10000 requests per day … below about 1 GB per day" |
| HRSL | **COGs** at `s3://dataforgood-fb-data/hrsl-cogs/` (CC BY 4.0) |
| GloFAS | the **Open-Meteo Flood API** (CC BY 4.0, "free API services for non-commercial purposes") |
| ISD pressure | the **NCEI Access Data Service** (`dataset=global-hourly&dataTypes=SLP`) |
| CAMS, OISST, ocean colour | **Earth Engine** `ECMWF/CAMS/NRT` (2016-06 →), `NOAA/CDR/OISST/V2_1`, `NASA/OCEANDATA/MODIS-Aqua/L3SMI` |
| WRI power plants | **Earth Engine** `WRI/GPPD/power_plants` |
| GEBCO | **Earth Engine** `projects/sat-io/open-datasets/gebco/gebco_grid` |
| IOC | the **keyless v1 service** |
| GDELT | the **BigQuery sandbox** ("without providing a credit card or creating a billing account", 1 TiB a month), on a Cloud project that has no billing account |

## Net effect [U]

| Budget | Current plan (DATA-PLAN.md §10) | With the 20 | Why |
|---|---|---|---|
| Private archive (`abrycta/plumes-archive`) | about 0.9 GB at M1; about 2 GB for the roadmap | **about 70–80 MB, and under 100 MB for the roadmap** | no COD-AB gdb (361 MB), MIROVA (99 MB), DROMIC docx (170 MB: only the extracted rows and file hashes are archived), IGRA, HRSL, Slab2, GEBCO, EMSR418 or PSA files. What remains: the PHIVOLCS bundles (about 50 MB zstd), VAAC (under 5 MB), USGS (5 MB), GVP, the COD-AB attribute table (0.1 MB), and the FIRMS API results for the Philippine box (about 10–20 MB) |
| Archiving of query-based sources | n/a | **the query results, not the upstream** | each fetch hook saves the request (URL, asset id, geometry hash, dates) and the returned rows. archivekit snapshots that file, so the fallback is "primary query → last good result". Earth Engine outputs are archived as tables and rasters never are, as before |
| Actions, private archive repo | about 30 a month (45 for the roadmap), plus a 15-minute first snapshot | **about 10 min a month, plus a first snapshot of 2–3 minutes** | five small file entries plus the adopted crawl bundles |
| Actions, public repo | one-off 8–10 h; weekly 15–25 min; M2 Himawari 20–40 min per event | **one-off about 7–9 h** (the PHIVOLCS crawl dominates; FIRMS API calls about 30–60 min); **weekly 10–20 min; no bucket streaming at any milestone** | no MIROVA, COD-AB, Himawari, GDELT or LAADS pulls |
| Earth Engine (Plumes cap 50 EECU-h a month, 10 per run) | backfill about 5 (M1), about 25 (roadmap); weekly under 0.5–1 | **backfill about 4–5 (M1), about 8–10 (roadmap); weekly under 0.5** | GHSL, WorldCover, Landsat, LST, MCD19A2, S1, SMAP, MERRA-2, Hansen and the others leave. AER_AI, GPM (reduced from the daily product) and Black Marble event windows stay. Far under the shared `lgu-lights` quota |
| A data version on GitHub Pages | about 250 MB (M1), about 400 MB (roadmap) | **about 250 MB (M1), about 260 MB (roadmap)** | no event animations, GIBS galleries, InSAR crop or GEBCO tiles |
| Neon catalogue | 100–300 MB | **about 100–200 MB** | fewer tables |

## Recommendation

**Accept the 20** (OPEN-QUESTIONS Q30), with Black Marble and the Lights poverty join moved to M1.1 so the Lights link ships right after the first story. The M1 cut (DATA-PLAN.md §9) then loses MIROVA, GHSL, WorldCover, Landsat, PSGC, GEM faults and the HazardHunterPH entry (which stays a link). It keeps everything the Taal story and the map read, and swaps three downloads for queries: the COD-AB range read, the FIRMS area API, and WorldPop Global 2 on Earth Engine. If accepted, DATA-PLAN.md §1, §9 and §10, LICENCES.md's summary table and SPIKE-PLAN.md are updated to the 20. The spike adds four checks: whether the FIRMS API's SP CSV carries the `type` column (1 = active volcano; otherwise the rings define the volcanic subset), which WorldPop Global 2 release the sat-io asset holds, the COD-AB `.dbf` range read inside the pipeline, and FRP-based radiative power at Taal 2020 compared against MIROVA's published figure.
