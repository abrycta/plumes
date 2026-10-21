# Spike results

Status: 2026-10-21. **The spike has not run.** Kurt said "go ahead with everything" the same day, but the first spike step (creating the throwaway Python environment in `spike/`: `earthengine-api`, `httpx`, `python-docx`, `xarray`, `zarr`) was refused by the session's permission check, and the rule for this work is to stop a refused step, not to work around it. No measurement was taken, no Earth Engine compute was used, no page was crawled, no NASA file was read. The table below records what each item needs, so the spike can start as soon as the permission is granted. Item numbers follow [SPIKE-PLAN.md](SPIKE-PLAN.md).

Checked before stopping (no secret printed):
- No Lights data run was in progress (`gh run list -R abrycta/lgu-lights`: the last runs were Web, Rust and Pipeline jobs, all finished).
- The Keychain has `earth-engine-sa-key`; it has **no** `firms-map-key`.

| # | Item | Result | Needs |
|---|---|---|---|
| 1–3, 11, 16, 18 (EE part), 20, 22, 25–27 | Earth Engine reductions, mosaic, Taal 2020 signal, WorldPop, quota accounting, thumbnails, Open Buildings | not run | permission to install the spike environment (or run Python with `earthengine-api`) in `spike/` |
| 4, 5, 17 | PHIVOLCS WordPress and LAVA bulletins, Tokyo VAAC and DROMIC (at most about 100 pages at 1 request/s) | not run | the same permission |
| 6 | PHIVOLCS earthquake tables | removed (Q30) | — |
| 7 | MapLibre frame time while scrubbing | not run | a browser session on the laptop and a mid-range phone |
| 8 | Taal per-volcano JSON size | not run | the item 1–3 tables |
| 9, 10 | GVP WFS and USGS CSVs through `archivekit fetch` | not run | the same permission |
| 12 | Taal and Kanlaon readings in EN and JA | not run | the item 1–5 tables, then Kurt's review |
| 13, 15 | Java API cold start on Render free; edge cache in front | **needs Kurt's go-ahead**: one Render web service, `plan: free`, in the existing workspace (Singapore), deploying a prebuilt GHCR image of a Spring Boot skeleton, deleted the same day; one throwaway Cloudflare Pages project with a `/api/*` function (free plan), deleted the same day | Kurt's go-ahead |
| 14 | PostGIS catalogue size on Neon free | **needs Kurt's go-ahead**: one Neon project `plumes-spike` (free, Singapore, PostGIS), or a branch, deleted the same day | Kurt's go-ahead |
| 18 (ERA5 part) | ARCO-ERA5 winds over Taal, 12–13 January 2020 | not run | the same permission |
| 19 | FIRMS area API `type` column | **blocked** | a FIRMS MAP_KEY in the Keychain as `firms-map-key` (Kurt's action, free) |
| 21 | COD-AB `.dbf` range read | not run | the same permission |
| 23, 24 | MSVOLSO2L4 / MSAQSO2L4 Philippine rows; OMI `OMSO2e` Harmony subset for Taal | not run (Kurt approved the Earthdata reads later the same day, but the spike had already stopped) | the same permission |

No DECISIONS.md addendum (S1…) is written until there are measurements.

## Run 1 (2026-10-21, in Kurt's session, with his approval)

| # | Measurement | Result | Verdict |
|---|---|---|---|
| 3 | Taal 2020-01-12 in Sentinel-5P SO₂ (OFFL L3, daily mean within 15 km) | Background about 0.02–0.08 mmol/m² in early January; **6.2 mmol/m² on 13 January (about 80× background) but from only 5 valid pixels**; 14–15 January no valid pixels (ash and cloud) | **Pass**, with the caveat that coverage must be shown beside every value (planned coverage bar confirmed as essential) |
| 3 | MODIS MOD14A1 MaxFRP within 15 km | Detections on 14, 17, 20 and 22 January 2020 (87–201 MW) | **Pass**: the thermal track shows the eruption |
| 3 | USGS ComCat within 30 km, 2019-12-01 to 2020-02-15 | 56 events: 35 on 12 January, 15 on 13th, 5 on 14th, 1 on 19th; none before | **Pass** for the spike itself; USGS sees no precursor swarm (PHIVOLCS bulletins carry the local counts) |
| 1 | Earth Engine cost of the above | One month, two rings, two collections: 2.5 s interactive `getInfo`, negligible EECU | **Pass**: well inside the Plumes cap |
| 23 | MSVOLSO2L4 read (GES DISC) | **Blocked**: HTTP 403 "EULA Acceptance Failure". Kurt must approve the GES DISC application once in Earthdata (urs.earthdata.nasa.gov, Applications → Authorized Apps, "NASA GESDISC DATA ARCHIVE"). The same approval covers OMSO2e (item 22) | Blocked on Kurt |

Not yet run: crawl parse rates (4, 5, 17), sizes (8), Render/Neon/edge (13–15), ERA5 Zarr (18), Landsat/S1 thumbnails (20, 21), FIRMS API (19, no MAP_KEY).

### Run 1, continued (Earth Engine story items)

| # | Measurement | Result | Verdict |
|---|---|---|---|
| 18 | Sentinel-2 SR least-cloudy scene over Taal | Before: 2019-11-19 (32.8 % cloud, 10 scenes); after: 2020-01-28 (5.4 %, 6 scenes); later: 2020-03-23 (2.4 %) | **Pass** for scene availability |
| 18 | `getThumbURL` from the service account | **Denied**: `earthengine.thumbnails.create` is not granted to `lgu-lights-ci` | **Change**: either grant the thumbnail permission on the Cloud project (Kurt) or export small images with `Export.image.toDrive`/`toCloudStorage` in the pipeline |
| 21 | Sentinel-1 GRD IW scenes over Taal, 12–20 January 2020 | 2 scenes | **Pass**: radar sees the eruption week when optical is clouded |
| 21 | Landsat 8 C2 L2 surface temperature of the crater lake before draining | 29.9 °C on 2019-02-05 (least-cloudy 2019 scene) | **Pass**: the lake-temperature series is feasible |
| 20 | WorldPop 2020 within 14 km of Taal (`WorldPop/GP/100m/pop`) | about 318,000 | Differs from OCHA's about 459,000 (vintage and method); state both, as planned |
| 20 | Community asset `projects/sat-io/open-datasets/WORLDPOP/pop` | Release R2025A, constrained, 100 m, annual from 2015 | Identified; use it for 2021+ |

### Run 1, continued (NASA, after Kurt approved the GES DISC application)

| # | Measurement | Result | Verdict |
|---|---|---|---|
| 23 | MSVOLSO2L4 v4 (2026-05-13 file, 193,575 bytes, bearer token) | 18 Philippine eruptions: Mayon 1984; Kanlaon 1985, 2016, 2024, 2025 (×2), 2026; Pinatubo 1991 (×3, 15,000 kt on 15 June, plume 25 km); Bulusan 2006–2025 (×7); **Taal 2020-01-12: 170 kt SO₂, observed plume 17 km, VEI 4** | **Pass**: feeds the eruptions band with SO₂ mass and plume height |
| 22 | OMSO2e via OPeNDAP (DAP4 CSV, 9×9 cells around Taal, 2020-01-13) | HTTP 200, 1,855 bytes, no download; **all cells are fill values** that day (likely OMI row-anomaly gaps) | **Pass for access**; the OMI track needs the same coverage display as TROPOMI, and its usable days must be counted in the backfill |
| 19 | FIRMS area API | Not run: MAP_KEY not yet in the Keychain | Pending |
| 19 | FIRMS area API (standard processing, 5-day windows, Taal box) | MODIS_SP: detections 14, 17, 20, 22 January; VIIRS_SNPP_SP: 46 detections on 12 days, 13–26 January; **the `type` column is present** (2 = active volcano in FIRMS' coding); the API accepts at most 5 days per request | **Pass**: no archive request needed; batch requests in 5-day windows. The Keychain value currently has curly quotes and needs re-saving clean |
