<!-- Research notes gathered 2026-10-21 for docs/CANDIDATES.md. Kept as evidence: every claim has its URL and access date; [U] marks unverified items. The comparison and the plan are in the parent folder. -->

# Candidate topic dossier: Philippine coastal ecosystems (mangroves and coral reefs)

Research date: 2026-10-21. Research only (WebSearch/WebFetch, no downloads, no accounts, no code). Every claim carries a URL and access date; unverifiable or inferred claims are marked **[U]**. Figures I derived myself (grid arithmetic, size estimates) are labelled "derived".

2024 Philippine columns) could not be re-checked and are marked **[U]**.

---

## 1. Mangroves

### 1.1 Global Mangrove Watch (GMW)

**GMW v3.0 (1996–2020), Zenodo 10.5281/zenodo.6894273** (https://zenodo.org/records/6894273, accessed 2026-10-21)
- 11 epochs: 1996, 2007, 2008, 2009, 2010, 2015, 2016, 2017, 2018, 2019, 2020. Licence **CC BY 4.0**. Published 2022-07-24.
- Resolution 25 m (JAXA page: "GeoTIFF rasters are at 25 m resolution", https://www.eorc.jaxa.jp/ALOS/en/dataset/gmw_e.htm, accessed 2026-10-21). JAXA mirror requires e-mail registration; Zenodo does not.
- Stated accuracy: extent maps 87.4 % (95 % CI 86.2–88.6 %); **gain class 58.1 % (52.4–63.9 %), loss class 60.6 % (56.1–64.8 %)**. Global extent 152,604 km² (1996) → 147,359 km² (2020), –3.4 %.
- Files (5.3 GB total): per-epoch GeoTIFF zips 66–68 MB and vector zips 182–194 MB (global); "f1996_t20XX" change-period files 32–42 MB (GeoTIFF) / 117–173 MB (vector); core/union layers; 1° tile index (GeoJSON 424 kB); `gmw_v3_country_statistics_ha.xlsx` (243 kB).
- Error sources named by the authors: SAR mosaic mis-registration and confusion in fragmented mangroves next to aquaculture ponds (search summary of Bunting et al. 2022, https://zenodo.org/record/6894273, accessed 2026-10-21).
- Citation: Bunting, P. et al. (2022) "Global Mangrove Extent Change 1996–2020: Global Mangrove Watch Version 3.0", *Remote Sensing*.
- Also mirrored in the Awesome GEE Community Catalog ("Global Mangrove Project", https://gee-community-catalog.org/projects/mangrove/, accessed 2026-10-21) and by Digital Earth Africa (Africa only, https://registry.opendata.aws/deafrica-mangrove/, accessed 2026-10-21).

**GMW v4.0 (2020 baseline, 10 m):** the State of the World's Mangroves 2024 summary reports GMW v4.0 mapped 147,256 km² in 2020 with overall accuracy 95.3 % (https://drishtiias.com/summary-of-important-reports/the-state-of-mangroves-2024, accessed 2026-10-21; secondary source). An Aberystwyth seminar abstract says v4.0 adds a 10 m 2020 baseline and historical change layers back to 1985 (https://www.agi.org.uk/?p=16118, accessed 2026-10-21).

**GMW v4.1.12 (1985–2025), Zenodo 10.5281/zenodo.21346457** (https://zenodo.org/records/21346456, accessed 2026-10-21) — this is the one to use.
- Published 2026-07-13. Licence **CC BY 4.0**. Annual layers for every year 1985–2025; baselines classified for 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025; imagery is sparse before ~1999/2000 so some early years are infilled from neighbouring years (stated on the record).
- Method: XGBoost baselines + Markov-chain time-series filtering; 130 random-forest classifiers per Landsat/Sentinel-2 scene (<70 % cloud) run in Google Earth Engine; JAXA L-band SAR (JERS-1, ALOS PALSAR, ALOS-2) fused by likelihood ratio; Bayesian updating; visual QA. Builds on the v4.0 10 m baseline; output resolution not stated on the record **[U: presumably 10 m]**.
- Accuracy (global, averaged): F1 0.9276 (0.9220–0.9330); omission 6.36 %; commission 8.09 %; 32,569 reference points at 120 sites; "accuracy will vary by location and time". No per-class change accuracy is given on the record **[U]**.
- Files (12.0 GB total): per-year vector GPKG with country attribute (`gmw_v4112_YYYY_mng_ext_cntry_info_vec.gpkg.gz`, 152–190 MB each, global); raster stacks (`..._stack.tar.gz` 1.4 GB; change-class stacks by baseline 1985/1990/2000/2010, 0.49–1.2 GB); change stats (`gmw_mng_chng_stats_v4112_corrected.tar.gz`, 14.2 MB); country stats xlsx (243 kB); 1° tile index GeoJSON (445 kB). Issue tracker: github.com/globalmangrovewatch/gmw_mangrove_extent.
- **Philippines in GMW 4.1:** 3,037.78 km² in 2025, net gain of 473.43 km² between 1985 and 2025 (implies ~2,564 km² in 1985, derived); Siargao's Del Carmen reserve grew ~500 ha 2012–2025 (GMA News, 2026-10-19, https://www.gmanetwork.com/news/scitech/science/1006389/philippines-among-countries-where-mangrove-cover-has-increased-in-the-last-4-decades/story/, accessed 2026-10-21). GMW itself attributes part of the increase to afforestation/restoration (same article). The GMW v3 Philippine figure was not retrieved **[U]**.

**GMW platform (globalmangrovewatch.org)**
- Front end is open source (MIT): github.com/Vizzuality/mangrove-atlas (React/Next.js/Mapbox GL 3/Recharts; Google Cloud Functions `analysis/` for "habitat extent, net change, biomass", `fetch-alerts/` pulling deforestation alerts from Earth Engine; routes `/country/:id`, `/wdpa/:id`, `/custom-area/:id`; backend via `NEXT_PUBLIC_API_URL`) (https://github.com/Vizzuality/mangrove-atlas, accessed 2026-10-21). No public API documentation was found; the backend repo was not located **[U]**.
- Platform layers listed in the GMW leaflet: 25 m Mangrove Habitat Extent (updated yearly) and 20 m Mangrove Disturbance Alerts (monthly) (https://www.mangrovealliance.org/wp-content/uploads/2023/07/GMW_Leaflet_2023.pdf, accessed 2026-10-21). An FAO document says alerts cover "African continent + selected countries in Asia & Pacific"; Philippine alert coverage not confirmed **[U]** (https://openknowledge.fao.org/server/api/core/bitstreams/c8fae7f7-9945-41aa-8936-268cc2055e66/content, accessed 2026-10-21).
- The platform was recently upgraded to extent/change through 2025 (Wetlands International, https://www.wetlands.org/good-news-for-mangroves-globally-masks-big-losses-in-some-regions-according-to-updated-global-mangrove-watch/, accessed 2026-10-21).

### 1.2 Hamilton & Casey CGMFC-21
- 30 m, annual 2000–2012 (paper) / 2000–2014 (UNEP catalogue entries); licence **CC BY 4.0** (https://wesr-search.unep.org/ckan/dataset/811a9294-3257-4d1a-a09e-ddbde3bd1cee and https://mdsoar.org/handle/11603/1598, accessed 2026-10-21). Distributed as an ArcGIS file geodatabase: zipped `MFW_2000_2012_Master.gdb.zip` 2.72 GB, ~4.5 GB geodatabase, "~9 TB uncompressed" for the whole database (https://mdsoar.org/handle/11603/1584, accessed 2026-10-21). Citation: Hamilton & Casey (2016) *Global Ecology and Biogeography* 25(6):729–738, doi:10.1111/geb.12449. Derived from Hansen GFC tree-cover inside a 2000 mangrove mask, so it only measures loss within year-2000 mangroves. Superseded by GMW 4.1 for this project; keep as a cross-check only.

### 1.3 Murray et al. 2022 global tidal wetland change
- GEE `ee.ImageCollection("JCU/Murray/GIC/global_tidal_wetland_change/2019")`: 30 m, 1999-01-01 to 2019-12-31, bands loss/lossYear/lossType, gain/gainYear/gainType, twprobabilityStart/End; licence **CC BY 4.0**; citation Murray, N.J., Worthington, T.A., Bunting, P. et al. (2022) *Science*, doi:10.1126/science.abm9583 (https://developers.google.com/earth-engine/datasets/catalog/JCU_Murray_GIC_global_tidal_wetland_change_2019, accessed 2026-10-21). Independent of GMW's SAR approach, so useful as a second opinion on loss/gain.

### 1.4 ESA WorldCover
- v200 (2021), 10 m, 11 classes including **Mangroves = 95**; licence CC BY 4.0 (https://developers.google.com/earth-engine/datasets/catalog/ESA_WorldCover_v200, accessed 2026-10-21). Single year only; useful as a 2021 cross-check, not for change.

### 1.5 Philippine official statistics
- **PSA Mangrove Accounts of the Philippines** (SEEA, released 2025-12-22 per MindaNews 2026-01): 302,811 ha (2015) → **311,216 ha (2020)**, +2.8 %; MIMAROPA 69,709 ha (22.4 %), BARMM 17.2 %, Eastern Visayas 34,679 ha; NCR 133 ha; figures "preliminary" (https://mindanews.com/top-stories/2026/01/mangrove-forests-healthy-in-barmm-caraga-zamboanga-peninsula/, accessed 2026-10-21). The PSA release page itself was not retrieved **[U]**; PSA OpenSTAT tables are CC BY (see §6).
- **NAMRIA Coastal Resource Map 2020**: DENR says it results from fieldwork and imagery 2017–2021 and that the country has "around 300,000 hectares" (https://denr.gov.ph/?p=11355, accessed 2026-10-21). Public download of the 2020 mangrove layer **was not found**: a 2016 Luzon NAMRIA Coastal Resource Map (Landsat 8, 30 m, ground-validated 2013–2016, excludes Palawan) is served as an ArcGIS FeatureServer (https://services1.arcgis.com/RTK5Unh1Z71JKIiR/ArcGIS/rest/services/CoastalResourceMap_Luzon_NAMRIA_2016/FeatureServer, accessed 2026-10-21); an FOI request for the 2015 national mangrove shapefile was denied (https://foi.gov.ph/requests/national-mangrove-shp-from-the-philippine-2015-land-cover, accessed 2026-10-21) and NAMRIA routes shapefile requests through a formal letter to the Administrator (https://foi.gov.ph/requests/shapefiles-for-coastal-and-marine-areas-in-abra-de-ilog-mindoro-occidental, accessed 2026-10-21). Treat official vectors as **not public**.
- **PhilSA–DENR Nationwide Mangrove Map 2023** (Sentinel-2 + ALOS PALSAR-2), launched 2024-02-28, "will undergo validation"; no download location stated (https://philsa.gov.ph/?p=6884, accessed 2026-10-21). Validation uses ODK citizen science (ISPRS Annals X-5-2024, https://isprs-annals.copernicus.org/articles/X-5-2024/243/2024/isprs-annals-X-5-2024-243-2024.pdf, accessed 2026-10-21).
- Historical narrative: ~450,000–500,000 ha in 1918/1920 → 120,000 ha in 1994 (Primavera 2000, https://repository.seafdec.org.ph/handle/10862/711?show=full, accessed 2026-10-21); Oceana: ">50 % lost", mangroves and fishponds now ~250,000 ha each, 1:1 ratio (Manila Times 2024-02-24, https://www.pressreader.com/philippines/manila-times/20240224/282071986836465, accessed 2026-10-21). Note the different series disagree by 2–3× (120,000 ha 1994 vs 256,185 ha c.2000 vs 311,216 ha 2020): method differences dominate, not real change. Say so on the page.

### 1.6 Long et al. 2014 and Baloloy et al. 2020
- Long, Napton, Giri, Graesser (2014) *Journal of Coastal Research*: Landsat 30 m maps for 1990 and 2010, decision tree classifier, –10.5 % 1990–2010 (https://pubs.usgs.gov/publication/70187705, accessed 2026-10-21); earlier Long & Giri (2011) *Sensors*: ~256,185 ha c.2000 (https://pubs.usgs.gov/publication/70036930, accessed 2026-10-21). Datasets not located for download **[U]**.
- Long et al. (2016) *Marine Pollution Bulletin*: Haiyan damage mapped from satellite; damaged classes shrank 90 %/81 %/57 % within 18 months (https://www.usgs.gov/publications/damage-and-recovery-assessment-philippines-mangroves-following-super-typhoon-haiyan, accessed 2026-10-21).
- Baloloy, Blanco, Ana, Nadaoka (2020) "Development and application of a new mangrove vegetation index (MVI)", *ISPRS J. Photogramm. Remote Sens.* 166:95–117, doi:10.1016/j.isprsjprs.2020.06.001 (cited via UP BlueCARES data page, https://www.bluecaresproject.upd.edu.ph/resources/data, accessed 2026-10-21). BlueCARES hosts Philippine MVI/Sentinel-2 mangrove layers and a GEE mapper (same page; licence not stated **[U]**). Known MVI issues: threshold shifts with land cover, climate and tide; false positives in aquaculture, irrigated cropland and palm (Neri, Baloloy, Blanco 2021, https://isprs-archives.copernicus.org/articles/XLVI-4-W6-2021/235/2021/, accessed 2026-10-21). A 2021 Frontiers paper produced a 2020 nationwide zonation map from Sentinel-2 (https://www.frontiersin.org/journals/remote-sensing/articles/10.3389/frsen.2021.730238/text, accessed 2026-10-21).

---

## 2. Coral reefs

### 2.1 Allen Coral Atlas (ACA)
- GEE `ee.Image("ACA/reef_habitat/v2_0")`: 5 m, imagery 2018–2020, bands `geomorphic`, `benthic` (sand, rubble, rock, seagrass, coral/algae, microalgal mats), `reef_mask`; **Terms of Use: CC-BY-4.0**; citation "Allen Coral Atlas (2020). Imagery, maps and monitoring of the world's tropical coral reefs. Zenodo doi:10.5281/zenodo.3833242" (https://developers.google.com/earth-engine/datasets/catalog/ACA_reef_habitat_v2_0, accessed 2026-10-21).
- The Atlas's own data-attribution text (search snippet) says maps, bathymetry and map statistics are "© 2018-2023 Allen Coral Atlas Partnership and Arizona State University, licensed CC BY 4.0", while the **Satellite Coral Reef Mosaic is © Planet Labs, CC BY-SA-NC 4.0** (https://allencoralatlas.org/attribution/, accessed 2026-10-21; the licence paragraph sits in a part of the page WebFetch truncated, so the wording is from the search index **[U]**). The generic site Terms of Use (https://allencoralatlas.org/tou/, accessed 2026-10-21) say Site Content is for "personal and non-commercial use only" and may not be copied/distributed without ASU consent; this generic clause conflicts with the CC BY grant on the data. Practical reading: habitat maps and statistics are CC BY 4.0 (confirmed by the GEE catalogue); never redistribute the Planet mosaic.
- Download: registered users can download benthic and/or geomorphic data for any mapped area, free (ICRI, https://icriforum.org/allen-coral-atlas-four-newly-mapped-regions/, accessed 2026-10-21); exports are GeoJSON (regional examples on SPREP portals). Unofficial CLI `pycoral` exists, "not based on any official API" (https://pypi.org/project/pycoral, accessed 2026-10-21). WMS/WFS services are offered "subject to Terms of Use" (https://allencoralatlas.org/resources/, accessed 2026-10-21). Sizes for a Philippines export were not found **[U]**; see §7 for an estimate.
- Philippine figures: 6,320 km² coral/algae habitat (rank 2 globally) and 24,219 km² reef ecosystem within the EEZ (ACA blog 2023-08-15, https://allencoralatlas.org/blog/coral-reef-area-to-save, accessed 2026-10-21). Lyons et al. 2024 (*Cell Reports Sustainability*) gives global 348,361 km² shallow reef / 80,213 km² coral habitat and lists the Philippines at 19,863 in a column whose header was cut off **[U]** (https://reefresilience.org/article-summaries/new-global-area-estimates-for-coral-reefs-from-high-resolution-mapping/, accessed 2026-10-21).
- Limitations: maps to ~10–15 m depth, cannot map turbid water, excludes steep/deep reefs and >30° latitude; coral and algae are one class because they are spectrally near-identical (ACA blog above; EEA catalogue https://cis2.eea.europa.eu/data/893, accessed 2026-10-21). An independent New Caledonia evaluation found benthic overall accuracy 20–67 % depending on site and method (https://www.livingoceansfoundation.org/publication/evaluation-of-the-allen-coral-atlas-benthic-habitat-map-product-for-new-caledonia-using-representative-habitat-observations-from-a-multi‑species-fishery-assessment/, accessed 2026-10-21).
- Bleaching monitoring: launched 2021; triggered when NOAA CRW reaches Bleaching Alert Level 1, then Sentinel-2 brightness change processed in GEE; alerts per user area; events visible since 2019 (https://www.allencoralatlas.org/blog/new-alert-global-tracking-of-coral-bleaching-events and https://essic.umd.edu/?p=10581, accessed 2026-10-21). No bulk download of the monitoring product was found **[U]**.

### 2.2 NOAA Coral Reef Watch (CRW) 5 km v3.1
- Products: CoralTemp SST, SST anomaly, HotSpot, DHW, Bleaching Alert Area (single-day, 7-day max), SST trend, plus composites; 1985-01-01 to present (DHW archive from 1985-03-25, BAA from 1985-03-31); v3.1 released 2018-08-01; CoralTemp = OSTIA reanalysis 1985–2002 + Geo-Polar blended reanalysis 2002–2016 + near-real-time 2017→ (https://coralreefwatch.noaa.gov/product/5km/index.php, accessed 2026-10-21).
- Access: HTTPS/FTP at star.nesdis.noaa.gov `/pub/socd/mecb/crw/data/5km/v3.1_op/` (NetCDF4; directory listing returned 403 to WebFetch, so sizes are unverified **[U]**); NCEI archive with DOI 10.25921/6jgr-pt28 (https://www.ncei.noaa.gov/archive/accession/0251002, accessed 2026-10-21); ERDDAP: PacIOOS `dhw_5km` full series (https://pae-paha.pacioos.hawaii.edu/erddap/griddap/dhw_5km.fgdc, accessed 2026-10-21), NOAA CoastWatch `noaacrwsstDaily` 1985–present 0.05° (https://coastwatch.noaa.gov/erddap/griddap/noaacrwsstDaily, accessed 2026-10-21), OceanWatch `CRW_sst_v3_1` (https://oceanwatch.pifsc.noaa.gov/erddap/griddap/CRW_sst_v3_1.html, accessed 2026-10-21). The IOOS/data.gov entries hold only the latest 3 years (https://data.ioos.us/dataset/noaa-coral-reef-watch-operational-daily-near-real-time-global-5-km-satellite-coral-bleaching-mo, accessed 2026-10-21).
- Licence: CRW states its content is **public domain** and may be freely distributed with credit to "NOAA Coral Reef Watch" (https://coralreefwatch.noaa.gov/satellite/docs/recommendations_crw_citation.php, accessed 2026-10-21).
- **Not in the official Earth Engine catalogue** and not in the Awesome GEE Community Catalog (checked https://gee-community-catalog.org/projects/, accessed 2026-10-21: no coral/CRW entry). OISST is on GEE (`NOAA/CDR/OISST/V2_1`, 0.25°, 1981-09-01→, "no restrictions", https://developers.google.com/earth-engine/datasets/catalog/NOAA_CDR_OISST_V2_1, accessed 2026-10-21), and a 2024 tool (PyDHW) computes DHW from OISST in GEE (https://ouci.dntb.gov.ua/en/works/lm8ZO2o4, accessed 2026-10-21), but OISST-derived DHW is not the operational CRW product; label it as such if used.
- DHW thresholds: ≥4 °C-weeks significant bleaching, ≥8 widespread bleaching and mortality (https://data.commerce.gov/node/268905, accessed 2026-10-21).

### 2.3 UNEP-WCMC Global Distribution of Coral Reefs (WCMC-008, v4.1, 2021)
- Compiled from the Millennium Coral Reef Mapping Project and Spalding et al. 2001; data page https://data.unep-wcmc.org/datasets/1 (via Copernicus Marine entry https://data.marine.copernicus.eu/product/EXT_UNEP_WCMC_CORAL_REEFS/description, accessed 2026-10-21).
- Licence: **UNEP-WCMC General Data License (excluding WDPA)** (https://www.unep-wcmc.org/policies/general-data-license-excluding-wdpa, accessed 2026-10-21), confirmed. Verbatim terms: "You may not redistribute the Data in whole or in part by any means" (web downloads, web services, interactive maps with download access, KML, FTP named); no Commercial Use (which includes use on behalf of any entity other than a not-for-profit) without written permission from the Director; "The Data may not be sub-licensed in whole or in part including within Derivative Works"; derivative works carry the same restrictions; online publication allowed only if not downloadable and with a clear link to UNEP-WCMC; two free copies of publications; superseded versions must not be used. **Confirmed: non-commercial, no redistribution, no sub-licensing.** Several mirrors mislabel it (e.g. "CC NC" on a Turks & Caicos portal, "Other (Open)" on Open Net Zero) — ignore those.
- Verdict: do not host, archive-and-publish, or tile this layer. ACA `reef_mask` (CC BY 4.0) replaces it for the Philippines.

### 2.4 Reef Check / ReefBase / NACRE survey data
- Reef Check global database (17,700+ surveys since 1997) is now integrated into Aqualink, "completely free and open to the public", browsable per site (https://www.reefcheck.org/latest-reef-check-coral-reef-data-available-on-aqualink/, accessed 2026-10-21; https://www.reefcheck.org/reef-check-and-aqualink-partner-up-for-coral-reefs/, accessed 2026-10-21). Bulk licence for reuse not stated **[U]**; Reef Check Australia charges AUD 100 for its separate database (https://www.reefcheckaustralia.org/data, accessed 2026-10-21). Reef Check data were also contributed to the ACA (attribution page).
- **ReefBase: www.reefbase.org did not resolve (DNS failure) on 2026-10-21** — treat as defunct.
- Licuanan, Robles & Reyes (2019) *Marine Pollution Bulletin* 142:544–550: 206 stations 2014–2017 + 101 monitoring stations 2015–2018; weighted hard-coral cover 22.8 % ±1.2 SE; generic diversity 14.5; highest Sulu Sea, lowest eastern Philippines; ~one-third of reef corals lost over the last decade (https://animorepository.dlsu.edu.ph/faculty_research/1989, accessed 2026-10-21). Licuanan et al. 2017 *Phil. J. Sci.* 146(2): 166 stations, none "excellent", >90 % poor/fair, 22 % HCC (https://philjournalsci.dost.gov.ph/53-vol-146-no-2-june-2017/640-initial-findings-of-the-nationwide-assessment-of-philippine-coral-reefs, accessed 2026-10-21). **Station-level data: no public dataset found** **[U]**; only published summaries by biogeographic region.
- CCEF "Saving Philippine Reefs" expeditions since 1992 (https://www.coast.ph/?p=7567, accessed 2026-10-21); access not stated **[U]**.

### 2.5 Fourth global bleaching event (2023–2025) in the Philippines
- NOAA confirmed the event 2024-04-15; bleaching-level heat stress hit 84 % of global reef area early 2023 → mid 2025; 82–83 countries; likely ended 2025 (https://en.wikipedia.org/wiki/2023%E2%80%932025_global_coral_bleaching_event and https://www.downtoearth.org.in/climate-change/worlds-fourth-mass-coral-bleaching-event-fastest-and-widest-on-record-likely-ended-in-2025, accessed 2026-10-21). The Philippines is among the severely affected countries per UP scientists (Philstar 2025-04-25, https://www.philstar.com/headlines/2025/04/25/2438212/84-worlds-corals-impacted-heat-stress-scientists, accessed 2026-10-21).
- UP MSI monitoring 2022–2025: 60–77 % of hard corals bleached (mostly severe) at Bolinao/Anda (Pangasinan) and Iba (Zambales); milder 20–43 % at Lobo (Batangas, in the Verde Island Passage) and Puerto Galera; Lobo HCC +20 %, Puerto Galera –2 % (https://pcaarrd.dost.gov.ph/index.php/quick-information-dispatch-qid-articles/boosting-coral-reef-resilience-through-marine-heatwave-tracking-and-coral-reef-monitoring, accessed 2026-10-21). Escoda/Sabina Shoal June 2024: corals "almost 100 % dead" in dived areas (two-day survey, https://gmanetwork.com/news/topstories/nation/909361/sabina-shoal-s-corals-almost-100-dead-up-scientists/story, accessed 2026-10-21). Verde Island Passage resilience narrative (Seacology 2023, https://www.seacology.org/2023/01/island-communities-lead-the-way-to-coral-reef-conservation-in-the-philippines/, accessed 2026-10-21). These are point observations, enough to annotate a DHW map but not a national bleaching extent.

---

## 3. Drivers and context

| Source | What | Licence | Access | Note |
|---|---|---|---|---|
| IBTrACS v04r01 (2024-06) | typhoon tracks, netCDF/CSV/shapefile, updated 3×/week | no formal licence text; WDC-Meteorology "full and open access", RSMC data agreed open; WMO Res. 40 for commercial | https://www.ncei.noaa.gov/products/international-best-track-archive (accessed 2026-10-21) | reuse what typhoon-replay already archives |
| OISST v2.1 | 0.25° daily SST 1981-09→ | "no restrictions" | GEE `NOAA/CDR/OISST/V2_1` (accessed 2026-10-21) | coarser than CoralTemp; fine for context |
| Clark Labs pond aquaculture / coastal wetlands | 15 m land cover for 17 countries incl. Philippines; 1999, 2014, 2018, 2020, 2022; classes Mangroves, Other Coastal Wetlands, Pond Aquaculture, Open Water, Other; compressed GeoTIFF + metadata | page states "CC BY 4.0" **and** "non-commercial purposes only; all other applications require permission" — self-contradictory; treat as **CC BY-NC-like** | https://www.clarku.edu/geospatial-analytics/?p=1832 (accessed 2026-10-21); download page returned 404/redirect loops on 2026-10-21 **[U]** | best pond layer available; the only one that distinguishes ponds from mangroves |
| Murray tidal wetland change | 30 m loss/gain 1999–2019 | CC BY 4.0 | GEE (see §1.3) | |
| Goldberg et al. 2020 *GCB* | 62 % of 2000–2016 mangrove loss = land-use change (aquaculture/agriculture); up to 80 % of human-driven loss in six SE Asian nations | paper (open access PMC7540710) | https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7540710/ (accessed 2026-10-21) | the loss-driver layer itself was not located for download **[U]** |
| PSA OpenSTAT fisheries statistics | municipal/commercial/aquaculture production by province, quarterly | **CC BY 4.0** ("Open Data with Creative Commons Attribution License (cc-by)") | https://openstat.psa.gov.ph/Terms (accessed 2026-10-21) | |
| PSA basic-sector poverty | 2021: fisherfolk 30.6 % (prelim; 30.2 % revised), highest; 2023: IPs 32.4 %, **fisherfolk 27.4 %**, farmers 27.0 % | CC BY (PSA) | https://newsinfo.inquirer.net/1748408/..., https://rssocar.psa.gov.ph/system/files/attachment-dir/CAR-SSR-2025-29_%20Poverty_Incidence_Among_Marginalized_Sectors_CAR.pdf (accessed 2026-10-21) | fisherfolk were the poorest sector in 2015, 2018, 2021; second to IPs in 2023 (IPs newly added) |
| BFAR FishR | 2,297,727 registered fisherfolk (2022-05-31); 2,302,648 in 2022 per House bill | not stated | https://region5.bfar.da.gov.ph/fishr-and-boatr/ (accessed 2026-10-21) | municipality-level counts would need a request **[U]** |
| Fishpond conversion | ~994 ha reverted to DENR in 2023; 55 ha without FLA; FLA inventory last concrete figure 62,625 ha (1998) | news/FAO | https://ph.oceana.org/?p=14518 ; https://www.fao.org/3/x6943e/x6943e08.htm (accessed 2026-10-21) | no current FLA polygon layer public **[U]** |
| WorldPop | 100 m population | CC BY 4.0 (ODbL for OSM/MS-derived variants) | https://hub.worldpop.org/geodata/summary?id=6057 (accessed 2026-10-21) | |
| OCHA COD-AB Philippines (adm0–3, 2023-11-09, NAMRIA/PSA) | boundaries | licence field not retrieved (API 403) **[U]**; marked "indicative, not official" | https://data.humdata.org/dataset/philippines-administrative-levels-0-to-3 (accessed 2026-10-21) | reuse from existing projects |
| WDPA (marine protected areas) | polygons/points | **non-commercial only; no redistribution "by any means" (web downloads, web services, download-enabled maps, KML, FTP); no sub-licensing; derivative works same rules; must link to Protected Planet; two free copies of publications** | https://www.protectedplanet.net/en/legal (accessed 2026-10-21); GEE `WCMC/WDPA/current/polygons` carries the same restriction | can be shown as a non-downloadable overlay only; never put in tiles that can be downloaded |
| Mangrove rehabilitation record | 10–20 % long-term survival; wrong species (Rhizophora on exposed sandy shores) and wrong zone (lower intertidal, because the right zones are fishponds); 97 % survival in one community-run site | Primavera & Esteban 2008 *Wetl. Ecol. Manag.* | https://animorepository.dlsu.edu.ph/faculty_research/4038 ; https://verafiles.org/articles/vera-files-fact-sheet-what-happens-when-mangroves-are-not-properly-planted (accessed 2026-10-21) | strong narrative hook |
| Typhoon protection | villages with more mangrove cover suffered less Haiyan damage (384 villages, VSU/EEPSEA) | | https://www-archive.cseas.kyoto-u.ac.jp/newsletter/nl77/06_can_mangroves.html (accessed 2026-10-21) | correlation study; say so |

---

## 4. Scientific honesty

1. **Change-class accuracy is low.** GMW v3 extent is 87 % accurate but its loss and gain classes are only ~60 % (§1.1). GMW 4.1 reports F1 0.93 for extent with no per-class change figure. A pixel flagged "lost 2015" has roughly a coin-flip chance of being map noise at the pixel level; aggregate to municipality/decade before saying anything, and show the 95 % ranges.
2. **Early years are infilled.** GMW 4.1 says imagery is sparse before ~1999/2000 and some years are infilled from other years. Do not present 1985–1998 annual values as observations; show them as baselines (1985, 1990, 1995) with a visual flag.
3. **Tide, cloud and palms.** Low tide exposes mudflats and low mangroves; high tide submerges them (Guangxi "lowest-tide composite" workaround, https://0-doi-org.brum.beds.ac.uk/10.3390/rs13152909, accessed 2026-10-21). MVI thresholds shift with tide and climate and confuse aquaculture, irrigated cropland and palms (§1.6). Philippine mangroves are fragmented and mixed with nipa/coconut; the GMW authors name fragmented mangroves beside ponds as an error source.
4. **Series are not comparable.** PSA 311,216 ha (2020) vs GMW 4.1 ~303,800 ha (2025, derived from 3,037.78 km²) vs Long & Giri 256,185 ha (c.2000) vs Primavera 120,000 ha (1994). Differences in definition (nipa? sparse stands?), resolution and tide dominate. Never chart two sources on one axis without a method note.
5. **DHW is heat stress, not bleaching.** CRW alert levels predict bleaching risk; observed bleaching in 2024 ranged 20–77 % between sites 200 km apart (§2.5). Show DHW as "heat stress", overlay the few observed-bleaching points, and never colour reefs "bleached" from DHW alone.
6. **ACA maps habitat, not health.** Coral and algae are one class; depth cut-off 10–15 m; turbid reefs unmapped; independent benthic accuracy as low as 20–67 % in one test (§2.1). A reef polygon says "this is reef structure", not "there is live coral".
7. **Coral cover decline is from 206 stations.** Licuanan's "one-third lost in a decade" is a weighted station comparison across assessments with different designs; present it as the published national estimate with its SE, not as a map.
8. **Typhoon protection is correlational.** Haiyan village study is cross-sectional; the 2024 Yagi wave-attenuation study is from China.

**Safe claims:** "GMW maps a net gain of ~470 km² of Philippine mangrove 1985–2025 (CC BY 4.0, F1 0.93)"; "PSA accounts put mangroves at 311,216 ha in 2020, +2.8 % since 2015"; "NOAA CRW shows record heat stress over X % of Philippine reef cells in 2024"; "mangrove/fishpond ratio ~1:1"; "fisherfolk poverty 27.4 % (2023), second-highest sector".

---

## 5. Existing products and public interest

- **GMW platform** (globalmangrovewatch.org): extent/change to 2025, country and WDPA pages, custom-area analysis, alerts, species, blue carbon; open-source front end (§1.1). It already does "per-country mangrove time series". A Philippine app must go below country level (municipality) and add context (ponds, typhoons, poverty) to differ.
- **Allen Coral Atlas**: 5 m habitat maps, bleaching alerts, per-area downloads, WMS/WFS (§2.1).
- **Global Forest Watch** carries a "Mangrove Forests" layer sourced from GMW (CEOS/GFOI presentation, https://gfoi-rd.gfz.de/fileadmin/gfoird/documents/2025_02_RDExchange_TropicalWetlands/Presentation_Rosenqvist.pdf, accessed 2026-10-21).
- **UP BlueCARES** hosts Philippine MVI maps and a GEE mapper (§1.6). **MangroveWatch** (Philippine programme) not found in this session **[U]**.
- **UP NOAH** (UPRI): open hazard maps (flood, landslide, storm surge; shapefile downloads), ₱1 bn 2026 allocation for LiDAR/drone mapping (https://mb.com.ph/2026/08/27/up-resilience-institutes-noah-center-secures-1-billion-to-expand-science-based-disaster-climate-solutions and https://www.upou.edu.ph/faculty/from-environmental-information-to-life-saving-decisions, accessed 2026-10-21); no coastal-ecosystem layer.
- **Public interest hooks:** mangrove planting drives and their failures (Catanduanes 2023 wrong species, https://newsinfo.inquirer.net/1797438/mind-your-mangroves-green-groups-cite-wasteful-project, accessed 2026-10-21); Oceana's push to revert abandoned fishponds (Fisheries Code mandates reversion); the new salt-industry law feared to block reversion (https://www.eco-business.com/ms/news/filipino-conservationists-fear-new-law-rubs-salt-in-mangrove-wound/, accessed 2026-10-21); Boracay's nine wetlands (37.81 ha, 548 encroaching structures; island closed 2018-04-26 to 2018-10-25; ~5 of 9 recovered by 2019–2020, https://newsinfo.inquirer.net/1182173/land-rows-stalling-rehab-of-boracay-forest-wetlands and https://denr.gov.ph/?p=4187, accessed 2026-10-21); Verde Island Passage protection bills (https://newsinfo.inquirer.net/1766866/fwd/amp, accessed 2026-10-21); Ramon Magsaysay Award 2021 to Roberto Ballon for Zamboanga Sibugay mangrove restoration (GMA article §1.1); fisherfolk poverty (§3); Haiyan protection narrative (§3).

---

## 6. Licences and redistribution (fit with DATA-ARCHIVING.md)

| Source | Licence | Archive raw privately? | Publish processed? |
|---|---|---|---|
| GMW v3.0 / v4.1.12 (Zenodo) | CC BY 4.0 | yes | yes, with attribution |
| GMW platform API/tiles | undocumented; platform code MIT | do not scrape | no |
| Hamilton & Casey CGMFC-21 | CC BY 4.0 | yes | yes |
| Murray 2022 tidal wetlands (GEE) | CC BY 4.0 | yes (GEE export) | yes |
| ESA WorldCover v200 | CC BY 4.0 | yes | yes |
| PSA Mangrove Accounts, fisheries, poverty (OpenSTAT) | CC BY 4.0 | yes | yes |
| NAMRIA CRM 2020 / PhilSA 2023 mangrove map | not public | no (request by letter) | no |
| UP BlueCARES MVI layers | unstated **[U]** | ask | no until cleared |
| Allen Coral Atlas habitat/statistics | CC BY 4.0 (GEE catalogue; attribution page) | yes | yes, with the Zenodo citation |
| Allen Coral Atlas Planet mosaic | CC BY-SA-NC 4.0 (© Planet) | no | no |
| NOAA CRW 5 km v3.1 | public domain, credit "NOAA Coral Reef Watch" | yes | yes |
| NOAA OISST v2.1 | no restrictions | yes | yes |
| IBTrACS v04r01 | open (WDC/WMO Res. 40); no formal text | yes | yes |
| UNEP-WCMC coral reefs WCMC-008 | **General Data License: no redistribution, no sub-licensing, non-commercial** | **no** (archiving a copy in a private repo is itself a redistribution risk; do not) | **no** |
| WDPA | **same: no redistribution by any means, non-commercial, link to Protected Planet** | **no** | overlay only, non-downloadable, with citation "UNEP-WCMC and IUCN (year), Protected Planet…" |
| Clark Labs aquaculture | CC BY 4.0 text + "non-commercial only" clause (contradictory) | yes (private) | derived municipality stats probably fine for a non-commercial portfolio; ask Clark Labs before republishing rasters **[U]** |
| WorldPop | CC BY 4.0 (ODbL variants exist) | yes | yes |
| OCHA COD-AB PH | not retrieved **[U]**; HDX CODs are normally CC BY-IGO or similar | yes | check field first |
| Reef Check via Aqualink | viewable, bulk licence unstated **[U]** | no | cite, link |

Archiving standard fit: good for the CC BY / public-domain core (GMW, ACA, CRW, OISST, IBTrACS, PSA, WorldPop). The two UNEP-WCMC layers must be excluded from `sources.yaml` entirely or flagged `redistribute: false, archive: false`. Clark Labs needs an explicit `commercial: false` flag.

---

## 7. Volumes and free-tier feasibility (all estimates derived unless cited)

- **GMW raster, Philippine subset.** PH 2025 extent 3,037.78 km² = 303,778 ha ≈ 30.4 M pixels at 10 m. A nationwide 10 m COG of a coastal strip (0/1 byte, deflate) ≈ 10–40 MB per year **[U]**; 41 years ≈ 0.5–1.5 GB. Vector: global per-year GPKG 152–190 MB (cited §1.1); the Philippines is ~2 % of global mangrove area (3,038 / 147,256 km², derived), so per-year PH polygons ≈ 3–6 MB GPKG **[U]**. 41 years ≈ 150–250 MB GPKG, far less as simplified PMTiles. GMW v3 1° tile index: the Philippines spans roughly 50–60 tiles **[U]**.
- **Allen Coral Atlas, Philippine subset.** 24,219 km² reef ecosystem at 5 m ≈ 9.7 × 10⁸ pixels; benthic GeoJSON for the whole country will be hundreds of MB to a few GB **[U]**. Preferred route: GEE `ACA/reef_habitat/v2_0` → `reduceRegions` per reef polygon/municipality and a simplified `reef_mask` vector (tens of MB) → PMTiles.
- **CRW daily 5 km for a PH box** (lat 4–22 °N, lon 116–128 °E = 360 × 240 = 86,400 cells, derived): 1985-03-25 → 2026-10-21 ≈ 15,180 days; 86,400 × 15,180 ≈ 1.3 × 10⁹ values per variable ≈ 2.6 GB as int16 uncompressed (DHW only), 5 GB with SST. ERDDAP subsetting (PacIOOS `dhw_5km`) at ~170 kB/day per variable is the practical route; chunk by year. Global daily NetCDF4 files: 7200 × 3600 × int16 ≈ 52 MB uncompressed, perhaps 5–15 MB compressed **[U]**; pulling 15,180 of them is ~100–200 GB, so do not.
- **Per-reef time series rows.** Reef-bearing 5 km cells in the PH box: perhaps 3,000–6,000 **[U]**. Daily long-format rows = 5,000 × 15,180 ≈ 7.6 × 10⁷ (too many for a static site); weekly-max ≈ 1.1 × 10⁷; **annual max DHW + days ≥4/≥8 per cell ≈ 2 × 10⁵ rows** (fine as Parquet/CSV, a few MB). Per coastal municipality (~900 of 1,634 LGUs **[U]**) × 42 years ≈ 38,000 rows.
- **Vector tiles / Cloudflare Pages.** Limits: 20,000 files and 25 MiB per file on Free (https://developers.cloudflare.com/pages/platform/limits, accessed 2026-10-21). A single PMTiles for 41 years of 10 m mangrove polygons will exceed 25 MiB; split by epoch (9 baselines) or serve PMTiles from Cloudflare R2 (free tier from memory: 10 GB storage, 10 M Class B ops/month **[U]**) with range requests. Static JSON per municipality (900 files) is well under the file cap.
- **Earth Engine.** Since 2026-04-27 noncommercial projects get a monthly quota: Community 150 EECU-hours, Contributor 1,000 (billing account linked, not charged), Partner 100,000; exhausted quota drops to restricted mode, not a cutoff (https://developers.google.com/earth-engine/guides/noncommercial_tiers, accessed 2026-10-21). Zonal stats of a 10 m binary raster over ~1,600 municipalities for 41 years, or ACA 5 m habitat over reef polygons, is on the order of single-digit EECU-hours per full run **[U]** (the lgu-lights project's VIIRS runs are a usable yardstick). Hugging Face datasets (project standard) can hold the archived GMW/ACA/CRW subsets (GB scale) for free.

Verdict: comfortably within free tiers if the CRW archive is reduced to the PH box via ERDDAP and tiles are split or moved to R2.

---

## 8. Technical showcase (beyond night-lights poverty and typhoon replay)

- **Change-detection cartography:** GMW 4.1 change-class stacks by baseline (1985/1990/2000/2010) → "year of loss / year of gain" rasters coloured by decade; Murray 2022 as an independent second opinion rendered as agreement/disagreement.
- **Swipe comparisons:** 1985 vs 2025 extent; GMW vs ESA WorldCover 2021 vs Clark Labs ponds; before/after Haiyan (2013) for Eastern Samar/Leyte.
- **Raster → vector pipeline:** GEE export → GDAL polygonise → simplification (tolerance by zoom) → tippecanoe → PMTiles; municipality zonal stats in GEE; Parquet/DuckDB-WASM for in-browser aggregation.
- **Per-municipality time series:** mangrove ha 1985–2025 (with infilled-years shading), pond area 1999–2022, annual max DHW 1985→, typhoon passes (IBTrACS within 100 km), registered fisherfolk and poverty.
- **Heat-stress animation:** daily DHW over the PH box for 1998, 2010, 2016, 2024 with a scrubber; cell-level sparkline on hover.
- **Uncertainty UI:** per-class accuracy bands rendered beside each number; "map says / field says" panel pairing DHW with UP MSI bleaching observations.
- **Honest-comparison module:** the four Philippine extent series on separate axes with method cards.

---

## 9. Risks

1. **Re-display risk.** GMW's own platform already gives national and WDPA-level mangrove extent/change to 2025 with custom-area analysis; ACA gives reef habitat and bleaching alerts. Without municipality-level synthesis plus ponds/typhoons/poverty, the app is a reskin.
2. **Limited new computation.** The defensible original work is (a) LGU-level zonal statistics across 41 years, (b) joining CRW heat stress to ACA reef cells per LGU, (c) pond-vs-mangrove balance per LGU from Clark Labs, (d) cross-source agreement maps. None is scientifically novel; all are honest engineering.
3. **Licence traps.** UNEP-WCMC coral reefs and WDPA forbid redistribution and commercial use; Clark Labs contradicts itself; ACA's generic site TOU says "personal, non-commercial" while the data is CC BY; NAMRIA/PhilSA official maps are not public; Reef Check bulk terms unknown.
4. **Change-class accuracy ~60 %** (GMW v3) and early-year infilling (v4.1) make per-pixel "loss" stories fragile; a reviewer who knows the literature will check.
5. **GEE quota change (2026-04-27)** caps free compute at 150 EECU-hours/month; manageable but new.
6. **Narrative risk:** the headline "Philippine mangroves grew 473 km²" (GMW) sits against "lost half since 1918" (Primavera/Oceana); both are true at different scales and must be explained, or the page looks contradictory.

---

## Scored table (1–5; risk: 5 = low)

| Criterion | Score | Justification |
|---|---|---|
| Data availability / licences | 4 | Core stack (GMW 4.1, ACA habitat, CRW, OISST, IBTrACS, PSA, WorldPop) is CC BY or public domain; official PH maps and UNEP-WCMC layers are closed but replaceable |
| Volume / free-tier feasibility | 4 | PH subsets are GB-scale; CRW must be box-subset via ERDDAP; PMTiles need splitting or R2; GEE 150 EECU-h/month suffices |
| Scientific honesty | 3 | Extent is solid (F1 0.93) but change classes ~60 %, early years infilled, DHW ≠ bleaching, ACA habitat ≠ coral health; honest framing is possible but demanding |
| Public interest / portfolio appeal | 4 | Mangrove planting drives, fishpond reversion, Boracay, VIP, Haiyan, 2024 bleaching, fisherfolk poverty are live Philippine stories |
| Technical showcase | 4 | Change-detection, swipes, 41-year LGU series, raster→vector→PMTiles, DHW animation, uncertainty UI |
| Risk (5 = low) | 3 | Main hazards are re-display of GMW/ACA and licence traps; both are avoidable by design but need discipline |

**Top three risks**
1. Re-displaying GMW and ACA without a clear municipality-level, multi-source synthesis that those platforms do not offer.
2. Licence traps: UNEP-WCMC coral reefs and WDPA (no redistribution, non-commercial), Clark Labs (contradictory NC clause), ACA site TOU vs CC BY data.
3. Over-claiming change from ~60 %-accurate loss/gain classes and infilled 1985–1998 years, or implying observed bleaching from DHW.
