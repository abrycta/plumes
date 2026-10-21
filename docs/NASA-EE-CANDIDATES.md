# More query-in-place sources from NASA and Earth Engine

Status: 2026-10-21. This is a proposal for Kurt (OPEN-QUESTIONS.md **Q31**). Nothing is decided. [DECISIONS.md](DECISIONS.md) and the 20 in [NO-DOWNLOAD-ALTERNATIVES.md](NO-DOWNLOAD-ALTERNATIVES.md) are unchanged. Kurt's request: "can you query nasa and earth engine for more sources?" Every fact below comes from a catalogue query run on 2026-10-21, not from memory. **[U]** marks an estimate, and "unverified" marks what the catalogues could not confirm.

## Summary

- **Searched:**
  - NASA CMR: 25 keyword searches over the bounding box 116,4,127,21 with a 2000–2026 time window and `has_granules=true`. They returned **2,999 collections**. Of these, **1,081** start by 2016, run to at least 2022, and have cloud hosting or a Harmony service.
  - GIBS: the WMTS capabilities document (the layer ids and their time domains).
  - The Earth Engine STAC catalogue: **1,164 collections** in 133 provider catalogues.
  - The Earth Engine community catalogue: 4,398 rows.
- **Assessed:** 30 candidates that would be new beside the 20 and the existing plan.
  - (a) strong: **5**;
  - (b) nice to have: **9**;
  - (c) not useful: **16**.
- **Top (a) picks:**
  1. **OMI SO₂, daily L3 (`OMSO2e`), through Harmony subsetting:** pushes the SO₂ track back from 2018-12 to **2004-10**.
  2. **MEaSUREs volcanic SO₂ database (`MSVOLSO2L4`):** SO₂ mass per eruption, 1978 to 2026-05, in one 185 kB file.
  3. **Landsat Collection 2 L2 on Earth Engine (TM, ETM+, OLI, OLI-2):** before/after images and crater-lake temperature from **2000**, where Sentinel-2 only starts in 2017.
  4. **Sentinel-1 GRD on Earth Engine:** radar before/after that sees through the January 2020 ash and cloud.
  5. **Google Open Buildings 2.5D Temporal on Earth Engine:** buildings inside each ring for every year 2016–2023 (exposure and recovery).
- **Earth Engine quota [U]:** the three (a) picks on Earth Engine add about **1–2 EECU-hours to the backfill and under 0.1 a week**. The roadmap backfill goes from about 8–10 to about 10–12 EECU-hours, still far under the Plumes cap of 50 a month (10 per run). `OMSO2e` and `MSVOLSO2L4` use NASA, not Earth Engine.
- **Archive size [U]:** about **+3–5 MB** (daily OMI rows for 24 volcanoes, the MSVOLSO2L4 file, yearly building counts, the image request records). The archive stays under 100 MB.
- **Login:** `OMSO2e` and `MSVOLSO2L4` need the **Earthdata login**, which the 20 had removed. CI already mints short-lived tokens from it for Lights (`EARTHDATA_USERNAME`/`EARTHDATA_PASSWORD`). The three Earth Engine picks use the existing service account.
- **Not checked, because a permission was denied:** a test read of `MSVOLSO2L4` and `MSAQSO2L4` with the Earthdata token was refused by the session's permission check. So two things are still open: **which Philippine eruptions MSVOLSO2L4 lists**, and **which Philippine volcanoes MSAQSO2L4 lists as degassing sources**. Both are spike checks.

## Method (reproducible)

- **CMR:**
  - Query: `collections.json?keyword=<kw>&bounding_box=116,4,127,21&temporal[]=2000-01-01T00:00:00Z,2026-10-21T00:00:00Z&has_granules=true`.
  - Keywords: volcan*, sulfur dioxide, SO2, volcanic ash, aerosol optical depth, thermal anomal*, fire radiative power, land surface temperature, deformation, lava, plume height, cloud top height, lightning, precipitation, soil moisture, vegetation index, night lights, surface reflectance, brightness temperature, aerosol layer height, burned area, ocean color, sea surface temperature, digital elevation, SAR backscatter.
  - Each short-listed collection was then read in `collections.umm_json`: dates, provider, `UseConstraints`, and its associated UMM-S services by name.
  - Granule hits inside a small box around Taal (120.9–121.05 E, 13.95–14.1 N) were counted for the swath and tile products.
- **GIBS:** `wmts/epsg4326/best/1.0.0/WMTSCapabilities.xml`, reading each layer's `<Dimension>` time values.
- **Earth Engine:**
  - `catalog.json`, then each provider catalogue, then each collection's STAC record: `license`, `extent`, `gsd`, `deprecated` and the terms link.
  - Records outside the Philippine box were dropped, as were records that end before 2018.
  - Then `community_datasets.csv` from awesome-gee-community-datasets.
  - No Earth Engine API call was made, and no compute was used.
- **Licence terms in this note:**
  - "EOSDIS open": CMR `UseConstraints` points to the EOSDIS data use policy (NASA open data, no restriction, citation requested).
  - "STAC proprietary": Earth Engine's flag for "see the provider's terms". It is not a restriction in itself, and the provider's terms are named in each row.

## (a) Strong additions

| # | Dataset and access route | Dates, resolution | Licence (catalogue record) | Auth | Feeds | Cost per volcano [U] |
|---|---|---|---|---|---|---|
| A1 | **OMI/Aura SO₂ daily L3 best pixel, `OMSO2e` v003** (GES DISC, cloud-hosted). Services in CMR: "Harmony OPeNDAP SubSetter (HOSS) Geographic", "Harmony OPeNDAP URL Service (HOUSe)", "OPeNDAP", "CloudGiovanniTimeSeries", "CloudGiovanniAveragingService". Route: a Harmony request per volcano box and date range, or Giovanni's area-averaged time series. GIBS also has `OMI_SO2_{Planetary_Boundary_Layer,Lower_Troposphere,Middle_Troposphere,Upper_Troposphere_and_Stratosphere}` tiles from 2004-10 / 2005-01 to now, for a map backdrop | 2004-10-01 → now (CMR); 0.25° daily; v004 also exists with HOSS (7,884 granules) | EOSDIS open ("EOSDIS data use and citation guidance") | Earthdata login (bearer token) | **The SO₂ track before TROPOMI**: Mayon 2006, 2009 and 2014, Bulusan 2006–2017, Kanlaon 2006–2016, and Taal 2020 cross-checked against TROPOMI. The track's start moves from 2018-12 to 2004-10 | no Earth Engine cost. One Harmony job per volcano box over 22 years: a few MB returned, about 8,000 daily rows per volcano, under 0.3 MB of rows |
| A2 | **MEaSUREs Multi-Satellite Volcanic SO₂ L4, `MSVOLSO2L4` v4** (GES DISC, cloud-hosted). One text granule `MSVOLSO2L4_v04-00-2026m0513.txt`, **0.18 MB**. No service is needed: the whole database is smaller than one crawled bulletin page bundle | 1978-10-31 → 2026-05-13; one row per eruption (SO₂ mass, plume altitude) | EOSDIS open | Earthdata login | **The eruptions band**: SO₂ mass beside VEI for each GVP eruption, the same for all 24 volcanoes. A satellite fact for the eruptions before TROPOMI, and a plume altitude next to the Tokyo VAAC heights | none; 0.18 MB, re-read once a year. **Unverified:** which Philippine eruptions it lists (the read was denied, see the summary) |
| A3 | **Landsat Collection 2 Level-2 on Earth Engine:** `LANDSAT/LT05/C02/T1_L2` (1984-03 → 2012-05), `LANDSAT/LE07/C02/T1_L2` (1999-05 → 2024-01), `LANDSAT/LC08/C02/T1_L2` (2013-03 →), `LANDSAT/LC09/C02/T1_L2` (2021-10 →). `getThumbURL` composites and an `ST_B10`/`ST_B6` reduction over each crater lake | 2000 → now; 30 m optical; thermal 100 m (OLI) / 120 m (TM) / 60 m (ETM+), resampled to 30 m | STAC "proprietary"; the terms link points to USGS: Landsat data are U.S. public domain | the existing Earth Engine service account | **Before/after imagery** for every event since 2000, where Sentinel-2 starts in 2017 (Mayon 2000/2006/2009/2014/2018, Bulusan, Kanlaon, Pinatubo's lake). Also **the Taal main crater lake's surface temperature** before it drained on 2020-01-12, and its return | thumbnails: under 0.01 EECU-h each, about 10 per volcano. Lake temperature: about 700 scenes × a few hundred pixels ≈ 0.02–0.05 EECU-h for Taal, about 0.5 for every lake volcano |
| A4 | **Sentinel-1 GRD on Earth Engine, `COPERNICUS/S1_GRD`** (IW, VV+VH, 10 m), as before/after backscatter and log-ratio change thumbnails | 2014-10 → now; repeats every 12 days (6 days in 2016–2021) | STAC "proprietary": the Copernicus Sentinel Data Legal Notice, already accepted for S5P and S2 | service account | **Before/after through cloud and ash**: the Taal Volcano Island ash blanket and the new crater on the first clear radar pass after 2020-01-12, when Sentinel-2 was clouded over. Also the Kanlaon 2024 deposits and the Mayon 2018 flows | under 0.01 EECU-h per thumbnail; about 0.05 per event. **The 20 had cut it** as a "second view"; it is listed again because it is the only view that sees through the cloud |
| A5 | **Google Open Buildings 2.5D Temporal, `GOOGLE/Research/open-buildings-temporal/v1`** (EE; covers "South-East Asia" according to the STAC description) | 2016-06-30 → 2023-06-30, annual; effective 4 m (building presence, fractional counts, heights) | **CC BY 4.0** (STAC `license`) | service account | **Exposure and recovery**: buildings inside the 7 / 14 km rings for each year. Shows the Taal Volcano Island settlements before the 2020 eruption, their decline and any return, and growth near Mayon and Kanlaon. It adds a building view to WorldPop's people count and leads into the Lights link | about 8 yearly images × a 14 km ring at 4 m ≈ 0.05–0.1 EECU-h per volcano; about 1–2 for all 24 (backfill once; the data ends in 2023) |

**Why these five, tied to the product:**
- The **SO₂ track** is the one series the 24-volcano map and the volcano pages show for every volcano. TROPOMI alone makes it start in 2018, which contradicts the "2000 to now" claim (Q7). A1 and A2 fix that, A1 per day and A2 per eruption.
- For the **Taal 2020 story**:
  - A4 makes step 5 (before/after) work in the eruption week itself, not on the first cloud-free Sentinel-2 day;
  - A3 adds the crater lake's pre-2020 temperature and the 2000+ images for the other volcanoes' pages;
  - A5 makes the exposure and recovery steps a visible change over time rather than one population number.

## (b) Nice to have

| # | Dataset and route | Dates, resolution | Licence | Auth | Feeds | Cost [U] / reason not (a) |
|---|---|---|---|---|---|---|
| B1 | **ECOSTRESS L2T LST, `NASA/ECOSTRESS/L2T_LSTE/V2`** (EE); also `ECO_L2T_LSTE` v002/v003 as LP DAAC cloud COGs | 2018-07-09 → now; 70 m; irregular overpasses (1,123 granules at Taal in CMR) | STAC "proprietary" → LP DAAC/EOSDIS open | service account | crater-scale heat, including night passes: Taal's lake and vents, Kanlaon's summit | about 0.05 EECU-h per volcano. Only from 2018, and the overpass times vary |
| B2 | **MODIS / VIIRS night LST, `MODIS/061/MOD21A1N`, `MODIS/061/MYD21A1N`, `NASA/VIIRS/002/VNP21A1N`** (EE) | 2000-02 / 2012-01 → now; 1 km daily | STAC "proprietary" → LP DAAC open | service account | a low-temperature thermal track (heating before eruptions) that FRP misses | about 0.1–0.2 EECU-h per volcano for the daily record. A 1 km pixel is coarse for a crater |
| B3 | **MAIAC AOD, `MODIS/061/MCD19A2_GRANULES`** (EE; GIBS has `MODIS_Combined_MAIAC_L2G_AerosolOpticalDepth`) | 2000-02 → 2026-10; 1 km | STAC "proprietary" → LP DAAC open | service account | ash and vog haze downwind (Batangas, Metro Manila) for every event since 2000; extends the S5P aerosol index back in time | about 0.1–0.3 EECU-h per volcano per decade of event windows. Cloud and ash are often mis-flagged |
| B4 | **S5P aerosol layer height, `COPERNICUS/S5P/OFFL/L3_AER_LH`** (EE) | 2018-07 → now; about 1.1 km grid | Copernicus Sentinel legal notice | service account | a satellite plume height beside the Tokyo VAAC heights (story step 3) | under 0.05 EECU-h per event. Cut in the 20 as a second view; VAAC already carries step 3 |
| B5 | **OMPS/NPP PCA SO₂ L2, `OMPS_NPP_NMSO2_PCA_L2` v2** (GES DISC; CMR service: OPeNDAP) | 2012-01-26 → now; 50 × 50 km swath | EOSDIS open | Earthdata login | a second SO₂ sensor across the 2012–2018 gap, if OMI's row anomaly leaves holes | small OPeNDAP subsets, but swath-level, so more code than A1 |
| B6 | **ARIA Sentinel-1 GUNW interferograms, `ARIA_S1_GUNW`** (ASF, cloud-hosted netCDF; **5,111 granules over Taal**, 2014-12 → 2025-09; about 100 MB each, read by HTTP range on the HDF5 chunks) | 2014 → 2025; about 90 m unwrapped phase | EOSDIS open (ASF) | Earthdata login | **deformation** (story step 1): Taal's inflation before 2020, read in place instead of from LiCSAR files | **the best M2 route for Q8's Taal crop**; a range-read crop is about 1–5 MB per pair [U]. Not (a) because InSAR is M2 by decision |
| B7 | **JRC Global Surface Water monthly history, `JRC/GSW1_4/MonthlyHistory`** (EE) | 1984-03 → 2022-01; 30 m monthly | STAC "proprietary" → JRC/Copernicus "free of charge, without restriction" | service account | water present or absent in Taal's main crater lake (gone in 2020, back in 2021) and Pinatubo's lake level | under 0.01 EECU-h per volcano. Ends 2021-12 |
| B8 | **GIBS MODIS true colour, `MODIS_Terra_CorrectedReflectance_TrueColor`** (WMTS tiles, no key) | 2000-02-24 → now, daily (9 time segments) | NASA open (GIBS/EOSDIS) | none | a "what the satellite saw that day" image of the plume for eruptions before 2017 | no Earth Engine cost; a few tiles per event. Cut in the 20 as "GIBS gallery"; it returns only as one image per eruption |
| B9 | **MEaSUREs SO₂ point-source catalogue, `MSAQSO2L4` v2** (GES DISC, one netCDF, **1.7 MB**) | 2005 → 2025, annual emissions per source (OMI, OMPS, TROPOMI) | EOSDIS open | Earthdata login | yearly passive degassing per volcano: a calm-year layer for the map | none. **Unverified:** whether it lists any Philippine volcano (read denied). It moves to (a) if Taal, Mayon or Bulusan are listed |

## (c) Not useful for Plumes

| # | Dataset | Why not (from the catalogue facts) |
|---|---|---|
| C1 | Himawari on GIBS (`Himawari_AHI_Band13_Clean_Infrared`, `Band3`, `Air_Mass`) | Rolling window only: the time domain starts 2026-09-08. Confirms the earlier cut |
| C2 | AIRS SO₂ (`AIRS_Prata_SO2_Index_*`, `AIRS_L2_Sulfur_Dioxide_Brightness_Temperature_Difference_*` on GIBS; `AIRICRAD` L1C) | Only imagery layers or L1 radiances; no gridded SO₂ product with a subsetting service |
| C3 | CALIPSO L2 (`CAL_LID_L2_05kmAPro`, `CAL_LID_L2_VFM` V4-51) | Ends 2023-06-30; a single-track curtain that crosses a volcano only by chance; no Harmony service. Kept as a link at most |
| C4 | CATS-ISS L2 | 2015–2017 only |
| C5 | MISR L2/L3 cloud height (`MIL2TCSP`, `MIL3DCOD`) | No volcanic plume product in CMR (`MISR_PLUME` returned nothing); cloud-top heights are generic |
| C6 | DSCOVR EPIC SO₂ (`DSCOVR_EPIC_L2_SO2`) | 2016+, no service; TROPOMI and OMI already cover it |
| C7 | MERRA-2 aerosol and SO₂ (`NASA/GSFC/MERRA/aer/2`, `M2T1NXAER`; GIBS `MERRA2_SO2_Column_Mass_Density_Monthly`) | Model reanalysis at 0.5°, with volcanic emissions taken from an inventory: it is not an observation of these volcanoes |
| C8 | MCD64A1 burned area (`MODIS/061/MCD64A1`) | 500 m fire scars; base surges and lahars are not fires |
| C9 | LandScan Global (`projects/sat-io/open-datasets/ORNL/LANDSCAN_GLOBAL`, CC BY 4.0, 2000–2023) | Repeats WorldPop |
| C10 | GPW v4.11, GHSL P2023A | Repeat WorldPop (GHSL already cut in the 20) |
| C11 | CHIRPS v3, JAXA GSMaP v8 | Repeat GPM IMERG; GSMaP has JAXA terms |
| C12 | VIIRS DNB monthly (`NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG`) | Black Marble daily already covers it |
| C13 | HLS (`NASA/HLS/HLSL30/v002`, `HLSS30`) | 2013/2015+; repeats Sentinel-2 plus A3 |
| C14 | GDIS (`projects/sat-io/open-datasets/gdis_1960-2018`, CC BY 4.0) | A geocoded list of disasters to 2018; repeats GVP eruptions |
| C15 | NASA Global Landslide Catalog (community, 1970–2019) | Ends 2019; few lahar records |
| C16 | GOES, TEMPO, S5P NO₂/CO/HCHO/O₃, GCOM-C LST, TOMS ozone, GLDAS/SMAP/FLDAS | GOES and TEMPO do not cover the Philippines (TEMPO is North America). The rest are not volcanic signals, or were already cut as M4 context |

## Effect on the budgets [U]

| Budget | With the 20 (NO-DOWNLOAD-ALTERNATIVES.md) | With the 20 + all five (a) picks | With the (b) picks as well |
|---|---|---|---|
| Earth Engine backfill (cap 50 EECU-h a month, 10 per run) | about 4–5 (M1), 8–10 (roadmap) | **about 6–7 (M1), 10–12 (roadmap)**: A3 + A4 + A5 add about 1–2.5 | about 13–16 (roadmap): B1–B4 and B7 add about 3–4 |
| Earth Engine weekly | under 0.5 | under 0.6 (only A3 and A4 receive new scenes) | under 0.8 |
| Private archive | about 70–80 MB | **about 75–85 MB** (OMI rows about 7 MB at most uncompressed, MSVOLSO2L4 0.18 MB, building counts and image request records under 1 MB) | about 90 MB (ARIA crops excluded; M2) |
| Data version on GitHub Pages | about 250 MB (M1) | about 255–260 MB (about 20 extra thumbnails per volcano at 50–100 kB) | about 265 MB |
| Registrations | FIRMS MAP_KEY only | **plus the Earthdata login** (Kurt has it; CI tokens are already minted for Lights) | the same |
| Source count | 20 | **25** (OMI SO₂, MSVOLSO2L4, Landsat, S1 GRD, Open Buildings) | up to 34 |

## Recommendation

**Add A1–A4 now (24 sources) and A5 at M1.1 with the Lights link.**
- A1 (OMI SO₂) and A2 (MSVOLSO2L4) are the only way the SO₂ track honours "2000 to now" without a bulk download.
- A3 (Landsat) and A4 (Sentinel-1) make before/after work for pre-2017 events and for the eruption week itself.
- A5 (Open Buildings) is a recovery and exposure layer, so it belongs with Black Marble and the Lights poverty join.
- The cost is a return of the Earthdata login, about 2 EECU-hours of backfill and about 5 MB of archive.

**Hold the (b) list.** B6 (ARIA GUNW) is the recommended route when the M2 InSAR crop (Q8) starts. B9 moves to (a) if the spike shows Philippine sources in it.

**Spike checks to add** (SPIKE-PLAN.md, if Q31 is accepted):
1. Read MSVOLSO2L4 and MSAQSO2L4 and list their Philippine rows. This needs the Earthdata token, whose use was denied in this session.
2. Run one Harmony HOSS subset of `OMSO2e` for Taal, January 2020, and compare it with TROPOMI.
3. Make one Sentinel-1 log-ratio thumbnail for Taal, 2020-01-06 against 2020-01-18.
4. Read the 2016 and 2023 building counts inside Taal's 14 km ring.
