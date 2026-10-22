# Layers plan: what to add after data v1

Status: 2026-10-22. **Final plan: Kurt answered the nine questions the same day** (§5; recorded as L1–L9 in [DECISIONS.md](DECISIONS.md)). Nothing here is built, registered or run yet; M2 starts when the checklist in §8 is complete. Kurt asked: "plan on what layers to add based on freely available data."

How this was checked:
- Earth Engine STAC records for every Earth Engine candidate (IDs, dates, licence field), read on 2026-10-22.
- NASA CMR collection and granule searches over small boxes around Taal, Mayon, Kanlaon, Pinatubo, Bulusan, Hibok-hibok and Ragang.
- The COMET Volcano Portal's own data files, read without a login.
- The licence ledger [LICENCES.md](LICENCES.md) where it already holds a verified quote; new licence checks are linked at the end.

**[U]** marks an estimate or something not confirmed. The Earth Engine costs scale from measured numbers: 87 EECU-seconds per month for S5P SO₂ over 24 volcanoes and 5 rings, and 64 for fire (DECISIONS B4).

## The big finding

**COMET already publishes ready-made InSAR time series for 18 of the 24 volcanoes.** Each one is a GACOS-corrected LiCSBAS series on a 100 × 100 grid, about 50 × 55 km. Taal frame `032D_07536_111313` holds 374 dates (2014-10-19 → 2026-08-12) and was last built on 2026-08-21. A file is 12–28 MB of JSON, with no login. This changes the plan for deformation:
- Q8 planned a Taal-only LiCSBAS crop at M2, preferably by ARIA GUNW range reads.
- ARIA GUNW turns out to cover only the Luzon frame: 5,111 granules at Taal and 4,939 at Pinatubo, but **0** at Mayon, Kanlaon, Bulusan, Hibok-hibok and Ragang. It also stops at 2025-09-15.
- COMET's series is cheaper (no InSAR processing), longer, and covers 18 volcanoes instead of 2.

Second finding: **OPERA DISP-S1 has 0 granules over the Philippines**, so it is not an option.

## 1. Summary of all candidates

Effort: S = under 2 days, M = 2–5 days, L = more than a week. EECU-h = Earth Engine compute hours for the one-off backfill, against Plumes' cap of 50 a month and 10 a run. "Reg." means the source is already in `sources.yaml`.

| # | Layer | Source and access | Span, cadence, resolution | Licence | Helps | Backfill cost | Effort | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | **SO₂ before TROPOMI** (`so2_omi_box`, already in the contract) | `OMSO2e` v003, GES DISC; Harmony HOSS subset (in place). Reg. `omi-omso2e` | 2004-10 →; daily; 0.25° | NASA open | all 24; Mayon 2006–14, Bulusan, Kanlaon | no EE; about 10–20 Actions min | S | **M2** |
| 2 | **Thermal after S-NPP ends** (S-NPP deliveries end 2026-11-01) | FIRMS area API `VIIRS_NOAA20_SP` (and `VIIRS_NOAA21_SP`), the existing client; CMR `VJ114A1` v002 as the second link | NOAA-20 2018 → (`VJ114A1` 2018-01-01 →); daily; 375 m / 1 km | NASA open (FIRMS) | all 24 | no EE; about 30–60 Actions min (rate limit) | S | **M2** |
| 3 | **Crater-lake temperature** (`lake_temp_landsat`, already in the contract) | Landsat C2 L2 `ST_B10` / `ST_B6` on EE. Reg. `landsat-surface-temperature` | 2000 →; 8–16 days; 30 m (100 m native) | US public domain | Taal Main Crater Lake (none from 2020-01-12 to its return), Pinatubo's crater lake | about 0.5 EECU-h | S–M | **M2** |
| 4 | **Ground deformation, LOS series** | COMET Volcano Portal LiCSBAS JSON `https://comet-volcanodb.org/data/disp_data_gacos/southeast_asia/<volcano>_<frame>_web_x100.json` (HTTP download) | 2014-10/2016 → 2026-08; 6–12 days; about 500 m grid (100 × 100 over 50 km) | LiCSAR: Copernicus-derived, OGL v3 on CEDA; portal: "CC BY-NC 4.0", treated as covering the JSON too (L1a) | 18 of 24 (not Babuyan Claro, Bud Dajo, Cagua, Hibok-hibok, Iraya, Smith) | no EE; about 0.7 GB downloaded once, about 15 Actions min | M (series) + M (velocity layer) | **M2 (L1)** |
| 5 | **Ash and aerosol on eruption days** (UV aerosol index) | `COPERNICUS/S5P/OFFL/L3_AER_AI` on EE (planned for M2, not yet in the registry) | 2018-07-04 →; daily; 1.1 km | Copernicus Sentinel notice | all 24, eruption windows | about 1–1.5 EECU-h (two rings) **[U]** | S | **M2** |
| 6 | **Rain before lahars** | `NASA/GPM_L3/IMERG_V07` on EE (half-hourly to daily sum); GES DISC `GPM_3IMERGDF` v07 as the second link | 1998 →; daily; 0.1° | NASA open (CC0) | Mayon (2006 Durian lahars), Pinatubo, Kanlaon, Bulusan, Taal | 1–3 EECU-h **[U; measure one month first]** | S | **M2 (Earth Engine route, L4)** |
| 7 | **Crater-lake area and colour** | Sentinel-2 L2A and Landsat on EE (Reg.); `JRC/GSW1_4/MonthlyHistory` (new) for water present/absent | GSW 1984-03 → 2021-12, monthly, 30 m; S2 2017 →, 10 m | GSW: "free of charge, without restriction"; Copernicus | Taal (gone in 2020, back in 2021), Pinatubo | under 0.5 EECU-h | S–M | **M2** |
| 8 | **Deep-time strip**: eruptions before 2000 with deaths and damage | `gvp-eruptions-ph` (Reg., already archived) plus NOAA NCEI HazEL API `.../hazel/hazard-service/api/v1/volcanoes?country=PHILIPPINES` | Holocene → now; per eruption | GVP non-commercial with citation; NCEI unrestricted | Taal 1911/1965, Mayon 1814/1993, Pinatubo 1991, Hibok-hibok 1951 | none; under 100 kB | S | **M2** |
| 9 | National monthly SO₂ map | S5P on EE (Reg.) plus OMI before 2018 | 2004-10 →; monthly | as 1 and S5P | map | about 1 EECU-h; tiles under 100 MB | S–M | M2 (last) |
| 10 | Night land-surface temperature (slow heating) | `MODIS/061/MOD21A1N`, `MYD21A1N`, `NASA/VIIRS/002/VNP21A1N` on EE | 2000 / 2012 →; daily; 1 km | LP DAAC: no restrictions | Taal, Kanlaon, Mayon, Bulusan | 2.5–5 EECU-h **[U]** | M | M3 |
| 11 | Crater heat at 70 m | `NASA/ECOSTRESS/L2T_LSTE/V2` on EE | 2018-07 →; irregular overpasses; 70 m | LP DAAC open | Taal, Kanlaon, Mayon | about 0.05 EECU-h a volcano | M | M3 |
| 12 | Aerosol index before 2018 | `OMAERUVd` v003, GES DISC, Harmony (same client as 1) | 2004-10 →; daily; 1° | NASA open | all 24 | no EE | S–M | M3 |
| 13 | Second SO₂ sensor (cross-check) | `OMPS_NPP_NMSO2_PCA_L3_DAILY` v1, GES DISC (one service in CMR) | 2012-01-26 →; daily | NASA open | Mayon, Bulusan, Kanlaon 2012–18 | no EE | S–M | M3 |
| 14 | Calm-year degassing per volcano | `MSAQSO2L4` v2, GES DISC, one 1.7 MB file | 2005–2025; yearly | NASA open | **lists Mayon, Bulusan, Kanlaon and "Taai" (L9)** | none | S | M3 |
| 15 | Land-cover change and burn around eruptions | `GOOGLE/DYNAMICWORLD/V1` (CC BY 4.0); Sentinel-2 dNBR / NDVI loss (Reg.) | 2015-06 →; per scene; 10 m | CC BY 4.0; Copernicus | Taal 2020, Kanlaon 2024, Mayon 2018 | about 1 EECU-h for about 20 event windows **[U]** | M | M3 |
| 16 | Built-up area since 1975 | `JRC/GHSL/P2023A/GHS_BUILT_S` on EE | 1975–2030 in 5-year epochs (2025/2030 are projections); 100 m | JRC open, reuse with acknowledgement | all 24 | under 0.2 EECU-h | S | M3 |
| 17 | Rivers that carried past lahars | HydroSHEDS v1 on EE (`WWF/HydroSHEDS/15ACC`, `03DIR`, `v1/Basins/hybas_12`) | static | free for non-commercial and commercial use | Mayon, Pinatubo, Kanlaon, Bulusan | under 0.1 EECU-h | S–M | **reject (L6, §4)** |
| 18 | Schools and hospitals inside each ring | OpenStreetMap via Overpass (per ring) or Geofabrik extract (611 MB); healthsites.io is OSM-derived | today only (no history) | ODbL 1.0 | all 24 | none; minutes | M | M3, labelled "as of <date>" (L7) |
| 19 | Rain cross-check | `ECMWF/ERA5_LAND/DAILY_AGGR` on EE | 1950 →; daily; 0.1° | CC BY 4.0 | as 6 | under 0.5 EECU-h | S | M3 (second link for 6) |
| 20 | Satellite plume height | `COPERNICUS/S5P/OFFL/L3_AER_LH` on EE | 2018-07 →; sparse | Copernicus | eruption days | under 0.05 EECU-h an event | S | M3 |
| 21 | Second earthquake catalogue (adds PHIVOLCS-reported small events) | ISC Bulletin (web search / FDSN); EMSC FDSN `seismicportal.eu` | ISC reviewed about 24 months behind | ISC **[U: site unreachable on 2026-10-22]**; EMSC service metadata says CC BY 4.0 for query results | all 24 | none | M | open: ISC licence checked by hand later, not needed for M2 (L8) |
| 22 | ARIA S1 GUNW interferograms | ASF, Earthdata | 2014-06 → 2025-09 | NASA open | Taal, Pinatubo, Banahaw only | — | L | reject (see §3) |
| 23 | OPERA DISP-S1 / RTC-S1 / DSWx-S1 | ASF / PO.DAAC | DISP: 0 granules over PH; RTC 2016 →; DSWx 2024-08 → | NASA open | — | — | — | reject |
| 24 | HyP3 on-demand InSAR | ASF HyP3, 8,000 free credits a month | — | Copernicus-derived | any | MintPy compute in Actions | L | reject |
| 25 | ASTER thermal `AST_08` | LP DAAC cloud | 2000-03 → 2026-01-16 (TIR switched off) | NASA open | Taal | — | M | reject |
| 26 | CALIPSO lidar | NASA ASDC | to 2023-08 | CC0 | chance overpasses | — | M | reject |
| 27 | S5P carbon monoxide | `COPERNICUS/S5P/OFFL/L3_CO` | 2018-06 → | Copernicus | — | — | S | reject |
| 28 | Himawari-8/9 ash RGB | NOAA NODD S3 (JMA data) | 2015-07 → | open with attribution | eruption days | 72 MB a scan for 3 bands | L | reject (Q26 stands) |
| 29 | GOSAT / OCO-2 CO₂ | — | — | open | — | — | — | reject |
| 30 | PHIL-LiDAR DEMs (LiPAD) | UP DREAM LiPAD | — | licence forbids distributable geospatial output | — | — | — | reject |
| 31 | PHIVOLCS hazard maps / HazardHunterPH | GeoRiskPH | — | "You must not: Republish material" | — | — | — | reject (link only) |
| 32 | PHIVOLCS earthquake catalogue | earthquake.phivolcs.dost.gov.ph (recent list only, no download) | — | government work | — | — | — | reject (Q24/Q30) |
| 33 | MODIS daytime LST (`MOD11A1`), MAIAC AOD, MERRA-2 | EE | — | open | — | — | — | reject |
| 34 | Smithsonian VOTW photos | volcano.si.edu | — | individual photo credits | — | — | — | link only |

## 2. Ranked shortlist

### Milestone 2: quick wins

Total cost of all nine: about **4–6.5 EECU-hours** of backfill (§7), in two runs of up to 10 each (one month's cap is 50). The weekly cost rises by about 0.2 EECU-h. GitHub Pages grows by about 15–25 MB, and the private archive by about 150–250 MB (COMET JSON, zstd) **[U]**. The rank below is the value order; the build order, which follows the gates, is §7.

| Rank | Layer | Why now | Honesty notes for the page |
|---|---|---|---|
| 1 | **OMI SO₂ daily** (`so2_omi_box`) | Already registered, already in the contract, no Earth Engine cost. Without it, the SO₂ track starts in 2018, which breaks the "2000 to now" promise (Q7). | 0.25° pixels are larger than most volcanoes; there are row-anomaly gaps from 2008; PBL column; label "OMI" and "TROPOMI" separately where they overlap; show coverage per day. |
| 2 | **NOAA-20 VIIRS thermal continuity** | S-NPP deliveries stop on 2026-11-01, so the VIIRS track would silently end. The FIRMS client already exists; adding the `VIIRS_NOAA20_SP` source name is a small change. | **Its own series (L5)**, never spliced into S-NPP, with a dated sensor-change marker at the switch (needs the Akari marker, §6). Counts include vegetation fires (FIRMS `type` 1 = active volcano). |
| 3 | **Landsat crater-lake temperature** (`lake_temp_landsat`) | Registered and in the contract. A distinctive "lake heated before 2020" story for Taal. Cheap. | Satellite skin temperature, not PHIVOLCS's in-lake readings. Show each PHIVOLCS bulletin value beside it, cited. Mask clouds and the lake edge. Show a gap while the lake was gone. The Landsat 7 stripe gap applies from 2003. |
| 4 | **COMET deformation: series and velocity map layer** (18 volcanoes; L2, L3) | The cheapest route to the deformation track Q8 wanted, for 18 volcanoes instead of only Taal (supersedes Q8's Taal crop). No InSAR processing. A per-volcano LOS chart plus a national `deformation-velocity` map layer (§3.1). Published under the portal's CC BY-NC 4.0 notice with attribution (L1a; no email). | Line-of-sight, not vertical. Movement is relative to COMET's reference area. Atmospheric noise remains after GACOS. Vegetated slopes lose coherence (Mayon, Kanlaon), so mask with COMET's `coh` and `mask`. Say "processed by COMET, not by Plumes". Show the frame and track. |
| 5 | **S5P aerosol index** | Already planned for M2. It shows the ash and haze on eruption days, which VAAC text only describes. | The index is unitless; it does not measure ash alone (smoke and dust also score); there is no signal under cloud. Eruption windows only, not a daily "ash level". |
| 6 | **GPM IMERG daily rain** | Already planned for M2, on Earth Engine (L4); one month is measured before the backfill. It puts rain beside the lahar dates found in bulletins and GVP. | Box-average rain on a 0.1° grid (about 11 km), not a gauge. Use Final-run values only. GES DISC's daily Final currently ends 2025-09-30, while Earth Engine's half-hourly runs later, so mark the run used. Never show "rain thresholds". |
| 7 | **Crater-lake area and colour** | Uses sources that are already registered, plus JRC GSW for the pre-2017 history. Shows Taal's lake vanish in January 2020 and refill. | GSW ends 2021-12. Report the area only on cloud-free dates. Colour is descriptive (RGB), not water chemistry. |
| 8 | **Deep-time strip and HazEL impacts** | No Earth Engine cost, under 100 kB, gives context before the satellite era (Taal 1911 and 1965, Mayon 1814, Pinatubo 1991). | Dates carry GVP's uncertainty fields. HazEL deaths and damage are compiled estimates: cite each one. |
| 9 | **National monthly SO₂ map** | Registered. The overview map gets a time slider for SO₂ like the thermal layer. | Monthly means smooth out single-day plumes. Show the valid-pixel fraction per month. |

### Milestone 3

| Rank | Layer | Reason | Blocker or caveat |
|---|---|---|---|
| 1 | Night LST (MOD21 / VNP21) | A heating track that FRP misses (Taal 2019, Kanlaon) | The 1 km pixel is coarse; cost 2.5–5 EECU-h |
| 2 | Dynamic World + S2 dNBR around eruptions | Shows deposit and burn areas after Taal 2020, Kanlaon 2024 and Mayon 2018 | Ash is often classed as "bare" or "built"; event windows only |
| 3 | OMI aerosol index `OMAERUVd` | Extends item 5 back to 2004 with the OMI Harmony client | 1° grid |
| 4 | GHSL built-up 1975–2030 | The long exposure trend beside WorldPop and Open Buildings (M1.1) | Hide the 2025 and 2030 epochs (projections) or label them "modelled" |
| 5 | ECOSTRESS 70 m crater heat | Sharper than MODIS for Taal and Kanlaon vents | Irregular overpass times; 2018 → only |
| 6 | OMPS SO₂ L3 and `MSAQSO2L4` | Cross-check of OMI; calm-year degassing | `MSAQSO2L4` lists four Philippine volcanoes (L9): Mayon, Bulusan, Kanlaon and "Taai" (presumably Taal) **[U: per-year values not yet read]** |
| 7 | OSM schools and hospitals per ring | People-facing exposure | **Only with a clear "as of <date>" label on every count (L7)**: a snapshot of today, not history; ODbL; counts only (a Produced Work), raw extracts private |
| 8 | ERA5-Land rain, S5P plume height | Second links and cross-checks | — |
| 9 | ISC / EMSC catalogue | Smaller PHIVOLCS-reported events than USGS | ISC licence unverified (open item, checked by hand later; L8); EMSC bulk-copy terms unclear |

## 3. How each M2 layer would be built

| Layer | Route | Archive strategy (rule 1) | New contract ids [U] |
|---|---|---|---|
| OMI SO₂ | Harmony HOSS subset per volcano box, Earthdata token minted in CI | Query results adopted into `plumes-archive`; links: Harmony, OPeNDAP, CMR | `so2_omi_box` (exists) |
| NOAA-20 thermal | FIRMS area API, `VIIRS_NOAA20_SP` (and `VIIRS_NOAA21_SP` later) | Adopted API results (as for S-NPP); `VJ114A1` in CMR as the second link | `fire_viirs_n20_15km` (own series; a `sensor_change` event dated at the switch) |
| Lake temperature | EE reduction over a lake polygon (repo file) | Remote dataset: EE plus USGS STAC (already 2 links) | `lake_temp_landsat` (exists) |
| COMET deformation | Download the GACOS JSON per volcano and frame; reduce to a summit-minus-reference LOS series and one velocity grid per frame (§3.1). Published with attribution to COMET plus "LiCSAR contains modified Copernicus Sentinel data [years]", and the notice "CC BY-NC 4.0" with a link to the licence (L1a) | Raw JSON adopted as a release (`comet-licsbas-<date>`); second link: the uncorrected `disp_data/` files (`automatic: false`, different correction); third: LiCSAR products on JASMIN (health check only) | series `los_comet_<frame>`; layer `deformation-velocity` (§3.1) |
| S5P UVAI | EE, one aggregation a month (B4 pattern) | EE plus CDSE STAC | `uvai_s5p_15km` |
| IMERG rain | EE daily sums per 15 km ring; a one-month canary first, its EECU-s recorded in `ee-usage.json` before the backfill is sized | EE plus GES DISC `GPM_3IMERGDF` | `rain_imerg_15km` |
| Lake area and colour | EE: S2/Landsat water mask; GSW monthly | EE (two links each) | `lake_area` |
| Deep time + HazEL | GVP already archived; HazEL JSON (needs a browser User-Agent) | HazEL file archived with archivekit | events table |
| National SO₂ map | EE monthly mosaics as raster tiles per year | EE (as S5P) | layer `so2-monthly` (exists) |

The layer ids in `contracts/schemas/layers.schema.json` are a closed `enum`, so each new map layer needs a contract change. **The `deformation-velocity` change below was approved by Kurt on 2026-10-22 (L3a); it is built with M2 step 9, not before.** Per-volcano series do not (contracts README: "New series ids may appear").

### 3.1 The deformation velocity map layer (L3)

What Kurt chose: a per-volcano LOS chart **and** a velocity map layer. The layer needs:

- **Contract change (approved 2026-10-22, L3a; built at M2 step 9).** Layer ids are a closed list in two places, which change together:
  - `contracts/schemas/layers.schema.json`: add `"deformation-velocity"` to the `id` enum; add `{frame}` to the url placeholders in the `description`; add an optional `frames` array, each item `{ id, volcanoId, track, pass: "ascending" | "descending", bounds: [w, s, e, n], reference: [lon, lat], start, end, dates }` (`dates` = number of acquisitions).
  - `contracts/ts/readmodels.ts`: add `"deformation-velocity"` to `LayerId` and `frames?: DeformationFrame[]` to `Layer`.
  - Follow-on files (same PR as the layer, not the contract change): the fixture `contracts/fixtures/data/v0/layers.json` and `pipeline/scripts/build_fixtures.py`, the producer `pipeline/plumes/readmodels.py`, the list in `contracts/README.md`, and the consumer `web/src/pages/MapPage.tsx`. The Java loader (`api/…/load/Loader.java`) reads only `thermal-detections` and is unaffected **[U: confirm with its contract test]**.
  - The per-volcano LOS chart needs no contract change: it is a sparse series `los_comet_<frame>` in the volcano file's `events` (`cols: ["date", "los_mm", "los_std_mm"]`), which the contracts README already allows ("New series ids may appear"). Note: the volcano file's existing `displacement` key is DROMIC's displaced *people*; the ground series is always called "deformation" to keep the two apart.
- **Layer entry:** `format: "cog"` (already in the enum), `url: "layers/deformation/{frame}.tif"`, `time.step: "none"` with the overall span, `legend.unit: "mm/yr"`, `sources: ["comet-licsbas"]` (registry id to be added), attribution "COMET LiCSBAS (processed by COMET, not Plumes); LiCSAR contains modified Copernicus Sentinel data [years]" plus the CC BY-NC 4.0 notice with its link (L1a; wording in LICENCES.md).
- **Data:** one file per frame: the mean LOS velocity over the frame's whole span, from COMET's GACOS-corrected cumulative displacement (least-squares slope per pixel), masked with COMET's `mask` and a mean-coherence floor of **0.2** (Kurt, 2026-10-22, DECISIONS L10; the canary at Taal 032D kept 1,983 of 8,811 COMET-valid pixels at 0.2, 1,230 at 0.3). Int16 GeoTIFF, EPSG:4326, deflate with predictor, value = mm/yr × 10, nodata −32768. At 100 × 100 pixels a file is about 20 kB raw, about 8–15 kB compressed.
- **Units and sign:** millimetres a year **along the satellite's line of sight**, positive = toward the satellite, negative = away. Never labelled "uplift" or "subsidence": LOS mixes vertical and east–west motion, and ascending and descending frames show the same ground differently. Each frame shows its track, pass, span, number of dates and COMET's reference area (a marker) in the legend note.
- **Colour scale:** Akari's diverging ramp (`--chart-div-1` … `--chart-div-7`) through `ContinuousLegend` with `scale="diverging"` (in `akari/react/components/akari/map-legend.tsx`; `MapLegend` is the stepped variant). One fixed symmetric domain for every frame so frames compare, about ±30 mm/yr **[U: set from the 98th percentile across all frames]**, values beyond it clamped and the legend's end ticks marked "≥". The neutral middle reads "no measurable motion". The ramp is Akari's, not a red-for-danger scale: this is not a hazard map.
- **Rendering and size budget:** no tile pyramid: the grid (about 500 m) is coarser than the zoom it is shown at. The web app fetches a frame's whole file (one GET, so no Range request and no CORS preflight; see B13), decodes it with `geotiff` (MIT; a new web dependency, about 40 kB gzip **[U]**), colours it client-side from the theme tokens (so light, dark and high contrast follow Akari), and draws it as a MapLibre `canvas`/`image` source at the frame's bounds, from zoom 7, only for frames in view. Budget: **under 0.5 MB per data version** for about 30 frames (18 volcanoes, one or two passes each) **[U: frame count]**.
- **Free tiers:** no Earth Engine and no server. GitHub Pages carries about 0.5 MB more per version (Pages' 1 GB site limit; the 100 GB a month bandwidth is not approached by 15 kB files); the Hugging Face mirror the same. Actions: about 15 minutes for the one-off download of about 0.7 GB; the weekly run reads each frame's "last built" date and re-downloads only changed frames. The raw JSON goes to `plumes-archive` once as a release (`comet-licsbas-<date>`, about 150–250 MB zstd **[U]**), well inside GitHub's 2 GB per release asset.

## 4. Rejected candidates and why

| Candidate | Reason |
|---|---|
| OPERA DISP-S1 | **Coverage:** 0 granules over Taal in CMR. It is a North America product. |
| OPERA RTC-S1 | Repeats `COPERNICUS/S1_GRD` on Earth Engine, which is already registered (747 granules at Taal from 2016). |
| OPERA DSWx-S1 | Starts 2024-08 at Taal; too short for a 2000 → record. |
| ARIA S1 GUNW (Q8's preferred route) | **Coverage:** Taal, Pinatubo and Banahaw only, and it ends 2025-09-15. COMET's series covers 18 volcanoes to 2026-08. |
| Own LiCSBAS or HyP3 InSAR | **Cost and effort:** HyP3 gives 8,000 free credits a month (10–15 per InSAR pair), but products expire after 14 days, the time series needs MintPy in Actions (4 vCPU, 14 GB disk, 6 h jobs), and overage is paid HyP3+ (about $0.05 a credit). COMET has already done this work. |
| ASTER `AST_08` / AST_L1T | **Coverage:** the ASTER thermal subsystem was switched off on 2026-01-16. Tasked, irregular scenes (432 at Taal). Landsat TM/ETM+/OLI thermal covers the same years. |
| CALIPSO | Ended 2023-08; a single curtain that crosses a volcano only by chance (NASA-EE-CANDIDATES C3). |
| S5P CO | Shows fires and pollution, not volcanoes; it would mislead a reader. |
| Himawari ash RGB | Q26 stands: no query route for past dates; the three ash bands are about 72 MB a full-disk scan. The licence is fine (JMA via NOAA, attribution). |
| GOSAT / OCO-2 CO₂ | Volcanic CO₂ is a few ppm above a 420 ppm background inside a 2 km footprint along sparse tracks. A reader would see noise. |
| PHIL-LiDAR DEMs (LiPAD) | **Licence:** "solely for the organization's use"; public posting only as a "non-downloadable, non-distributable image without geospatial information". |
| PHIVOLCS hazard maps / HazardHunterPH | **Licence:** "You must not: Republish material". **Honesty:** hazard zones read as a warning product. Keep as a link only. |
| PHIVOLCS earthquake catalogue | No download (recent bulletin list only); cut by Q24/Q30. Bulletins already carry the volcanic earthquake counts. |
| MODIS daytime LST, MAIAC AOD, MERRA-2 | Daytime solar heating swamps crater heat; MAIAC often mis-flags ash and cloud (UVAI is clearer); MERRA-2 is a model, not an observation. |
| Evacuation-centre locations, DepEd school list | No open national dataset with a reuse licence was found; DROMIC counts and OSM cover the need. |
| Smithsonian VOTW photos | Each photo has its own credit; link to them only. |
| HydroSHEDS lahar rivers (was M3) | **Honesty (Kurt, L6):** showing the channels that past lahars followed is too close to a hazard map for a site that is "not a warning service". Lahar dates stay as text events. |

## 5. Kurt's answers (2026-10-22)

The nine questions this plan asked, as answered by Kurt; recorded as L1–L9 in [DECISIONS.md](DECISIONS.md).

| # | Question | Answer |
|---|---|---|
| L1 | COMET licence | ~~Email COMET first~~. **Superseded the same day by L1a: no email.** The portal's CC BY-NC 4.0 notice is treated as covering the LiCSBAS data; Plumes publishes the derived files with attribution to COMET plus "LiCSAR contains modified Copernicus Sentinel data [years]", and the notice "CC BY-NC 4.0" with a link to the licence. The draft [research/comet-licence-email.md](research/comet-licence-email.md) is kept, marked "not sent" |
| L2 | Replace Q8's plan? | **Yes:** COMET LiCSBAS series for all 18 covered volcanoes at M2. Q8's Taal-only crop (preferably by ARIA GUNW) is superseded |
| L3 | Deformation display | **Both:** a LOS chart per volcano and a `deformation-velocity` map layer (§3.1) |
| L4 | Rain route | **IMERG on Earth Engine**, one month measured first |
| L5 | NOAA-20 series | **Its own series** with a sensor-change marker at the S-NPP → NOAA-20 switch (needs the Akari marker, §6) |
| L6 | Lahar rivers (M3) | **Excluded**: too close to a hazard map. Moved to §4 |
| L7 | OSM counts (M3) | **Only with a clear "as of <date>" label** on every count |
| L8 | Second earthquake catalogue | ISC licence **checked by hand later**; not needed for M2. Stays open |
| L9 | `MSAQSO2L4` read | **Allowed and done** (below) |
| L1a | COMET licence (revised) | **No email.** Treat the portal's CC BY-NC 4.0 notice as covering the LiCSBAS data; publish with attribution and the CC BY-NC notice |
| L3a | Contract change | **Approved**: `deformation-velocity` as in §3.1, built at M2 step 9 |
| L9a | `h5py` | **Agents may install `h5py`** in the plumes environment, for the `MSAQSO2L4` values at M3 |

**L9 result, 2026-10-22.** CMR lists one granule, `MSAQSO2L4_2005-2025_v02-00_20260814.nc` (1.7 MB, 2005-01-01 → 2025-12-31). Read once with the Earthdata token; nothing else downloaded. It lists **7 Philippine sources: the volcanoes Mayon ("the Philippines' most active volcano"), Bulusan, Kanlaon and "Taai"** (presumably Taal, spelt so in the file) **[U]**, and the power plants Sual, Masinloc and Mariveles. Read from the file's name, country and comment strings; the per-year emission values were not read, because installing a netCDF reader was refused in that session. **Kurt has since allowed agents to install `h5py` in the plumes environment** (L9a, 2026-10-22), so the M3 step reads the per-year values with it; nothing is run now. Item 14 is therefore an M3 layer for four volcanoes; the power plants are not shown (not volcanic).

## 6. Akari prerequisite: dated event markers on charts

Akari's chart primitives have no dated vertical marker: `akari/react/components/ui/chart.tsx` (the shadcn/Recharts wrapper) exposes no reference-line option, and `akari/react/components/akari/sparkline.tsx` has only `bands` (confidence ranges), `observations` (points with whiskers) and `marker: "last" | "none"`. Plumes' own `web/src/volcano/Timeline.tsx` draws its marker rows and cursor in app-level SVG, but M2's new charts need a dated rule across a value plot, and workspace rule 2 puts shared UI in Akari, not in a fork. So **an Akari addition is a prerequisite**, specified here and built in the Akari repo (not now):

- **What it draws:** a thin vertical rule at a date (or a shaded span for a start–end window) across the plot, with a short label or glyph at the top and the full text in the tooltip and in the chart's text summary (screen readers).
- **API sketch:** `markers?: { at: string | number; end?: string | number; label: string; kind: "event" | "sensor-change" | "gap" }[]` on `Sparkline`, and a `ChartEventMarker` part for `chart.tsx` charts (wrapping Recharts' `ReferenceLine` / `ReferenceArea`). Colours from tokens (`--border` strong for events, dashed for sensor changes); no pointer capture; labels collide gracefully (stagger, then tooltip only); works in light, dark and high contrast.
- **Used by M2:** the NOAA-20 sensor change (L5), GVP eruption dates on the deformation and rain charts, the "lake gone" span on the crater-lake charts, and OMI/TROPOMI overlap on the SO₂ chart.
- **Release:** an Akari PR with a changeset and a minor version; Plumes picks it up by version bump. Effort S (1–2 days with stories and tests).

## 7. Final M2 build order

The order follows the gates: ungated layers first, the S-NPP deadline first of all, COMET last (its gates are now cleared, L1a and L3a, so it may move up). EECU-h are one-off backfill hours; the two Earth Engine runs stay under the 10-per-run cap and together use about a tenth of the 50-a-month ceiling. Kurt reads the project's monthly total in the console before each run (S8).

| Step | Layer | Effort | EECU-h | Gate |
|---|---|---|---|---|
| 0 | Akari event marker (Akari repo, §6) | S | — | none; in parallel with steps 1–3 |
| 1 | NOAA-20 VIIRS thermal series (data first; the sensor-change marker once step 0 ships) | S | 0 | none for the data: S-NPP ends 2026-11-01 |
| 2 | OMI SO₂ daily (`so2_omi_box`) | S | 0 | none |
| 3 | Deep-time strip and HazEL impacts | S | 0 | none |
| 4 | Landsat crater-lake temperature | S–M | about 0.5 | EE run A |
| 5 | Crater-lake area and colour (S2/Landsat, JRC GSW) | S–M | about 0.3–0.5 | EE run A |
| 6 | S5P aerosol index (eruption windows) | S | about 1–1.5 | EE run A |
| 7 | GPM IMERG daily rain: one-month canary, then the backfill | S | about 1–3 (canary about 0.05) | EE run B, sized from the canary |
| 8 | National monthly SO₂ map | S–M | about 1 | EE run B |
| 9 | COMET deformation: LOS series and `deformation-velocity` layer (§3.1) | M + M | 0 | none left: licence settled (L1a), contract change approved (L3a) |

Totals: **about 4–6.5 EECU-hours** (run A about 2–2.5, run B about 2–4), about 3–4 weeks of build in all, of which the COMET step is about 1–1.5 weeks.

## 8. M2 is ready to start when…

- [x] ~~COMET's reply is recorded~~ **Done 2026-10-22 (L1a):** no email; published under the portal's CC BY-NC 4.0 notice with attribution.
- [ ] **The Akari event marker is released** (§6) and Plumes is on that version. Gates the markers on steps 1, 4, 5, 7 and 9; their data can land first.
- [x] **Kurt approved the contract change** (2026-10-22, L3a) of §3.1 (`deformation-velocity` in `layers.schema.json` and `readmodels.ts`, the `{frame}` placeholder, the `frames` array). Built with step 9.
- [ ] Kurt reads the Earth Engine monthly total in the console before runs A and B (S8), and the IMERG canary's EECU-s is in `ee-usage.json` before run B.
- [ ] Kurt gives the go-ahead for M2 (steps 0–3 can start on that alone).

## 9. Sources used

Plumes and portfolio docs: [DECISIONS.md](DECISIONS.md), [DATA-PLAN.md](DATA-PLAN.md), [LICENCES.md](LICENCES.md), [NASA-EE-CANDIDATES.md](NASA-EE-CANDIDATES.md), [research/subsidence-insar.md](research/subsidence-insar.md), [../pipeline/sources.yaml](../pipeline/sources.yaml), [../contracts/README.md](../contracts/README.md), `../../DATA-ARCHIVING.md`.

Earth Engine STAC records (read 2026-10-22), all under `https://earthengine-stac.storage.googleapis.com/catalog/`:
- `COPERNICUS/COPERNICUS_S5P_OFFL_L3_AER_AI.json`, `…_L3_AER_LH.json`, `…_L3_CO.json`
- `NASA/NASA_GPM_L3_IMERG_V07.json`, `NASA/NASA_GPM_L3_IMERG_MONTHLY_V07.json`
- `MODIS/MODIS_061_MOD11A1.json`, `MODIS/MODIS_061_MOD21A1N.json`, `MODIS/MODIS_061_MYD21A1N.json`, `NASA/NASA_VIIRS_002_VNP21A1N.json`, `NASA/NASA_ECOSTRESS_L2T_LSTE_V2.json`
- `GOOGLE/GOOGLE_DYNAMICWORLD_V1.json`, `JRC/JRC_GHSL_P2023A_GHS_BUILT_S.json`, `JRC/JRC_GSW1_4_MonthlyHistory.json`, `WWF/catalog.json` (HydroSHEDS)
- `ASTER/ASTER_AST_L1T_003.json`, `MODIS/MODIS_061_MCD19A2_GRANULES.json`, `ECMWF/ECMWF_ERA5_LAND_DAILY_AGGR.json`
- `NASA/NASA_LANCE_NOAA20_VIIRS_C2.json`, `NASA/NASA_VIIRS_002_VNP14A1.json`

NASA CMR (read 2026-10-22):
- Collections: https://cmr.earthdata.nasa.gov/search/collections.json?short_name= with `OPERA_L3_DISP-S1_V1`, `OPERA_L2_RTC-S1_V1`, `OPERA_L3_DSWX-S1_V1`, `ARIA_S1_GUNW`, `AST_08`, `VJ114A1`, `VNP21A1N`, `OMAERUVd`, `OMSO2e`, `OMPS_NPP_NMSO2_PCA_L2`, `OMPS_NPP_NMSO2_PCA_L3_DAILY`, `GPM_3IMERGDF`, `MSAQSO2L4`.
- Granule counts: `granules.json?short_name=<id>&bounding_box=<volcano box>`.
- `MSAQSO2L4` (L9): https://cmr.earthdata.nasa.gov/search/granules.json?short_name=MSAQSO2L4 and the one file https://data.gesdisc.earthdata.nasa.gov/data/SO2/MSAQSO2L4.2/MSAQSO2L4_2005-2025_v02-00_20260814.nc (read 2026-10-22).

Deformation:
- COMET Volcano Portal: https://comet.nerc.ac.uk/comet-volcano-portal/ ; frames list https://comet-volcanodb.org/data/volcanoes_frames/volcanoes_frames.js ; page code https://comet-volcanodb.org/static/js/s1_analysis.js ; copyright https://comet.nerc.ac.uk/comet-volcano-portal/copyright ; tools https://comet.nerc.ac.uk/comet-volcano-portal/about-tools
- LiCSAR licence: https://comet.nerc.ac.uk/comet-lics-portal/ , https://catalogue.ceda.ac.uk/uuid/52cda2e0e6c04272ae15ac836c1e8493/
- HyP3 credits: https://hyp3-docs.asf.alaska.edu/using/credits/ ; products: https://hyp3-docs.asf.alaska.edu/products/
- ARIA: https://www.earthdata.nasa.gov/data/projects/aria

Thermal and other:
- FIRMS area API sources: https://firms.modaps.eosdis.nasa.gov/api/area/
- ASTER TIR shutdown: https://www.earthdata.nasa.gov/data/instruments/aster/aster-transition-resources
- NOAA NCEI HazEL: https://www.ncei.noaa.gov/products/natural-hazards/tsunamis-earthquakes-volcanoes/volcanoes
- Himawari on AWS: https://registry.opendata.aws/noaa-himawari/
- HydroSHEDS: https://www.hydrosheds.org/products/hydrosheds

Licences:
- OpenStreetMap: https://www.openstreetmap.org/copyright ; ODbL: https://opendatacommons.org/licenses/odbl/1-0/
- healthsites.io: https://digitalpublicgoods.net/r/global-healthsites-mapping-project
- LiPAD: https://lipad-fmc.dream.upd.edu.ph/about/
- HazardHunterPH: https://hazardhunter.georisk.gov.ph/terms-of-use
- EMSC: https://seismicportal.eu/fdsn-wsevent.webapi.schema.org.jsonld , https://seismicportal.eu/webservices.html
- ISC: https://www.isc.ac.uk/iscbulletin/ (404 on 2026-10-22)
- PHIVOLCS earthquakes: https://earthquake.phivolcs.dost.gov.ph/
