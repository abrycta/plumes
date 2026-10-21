<!-- Research notes gathered 2026-10-21 for docs/CANDIDATES.md. Kept as evidence: every claim has its URL and access date; [U] marks unverified items. The comparison and the plan are in the parent folder. -->

# Candidate topic dossier: rice and drought monitoring (Philippines)

Research date: 2026-10-21. All URLs accessed 2026-10-21 unless stated. Research only (WebSearch, WebFetch, small curl probes); no downloads beyond metadata probes, no accounts, no code. Claims that could not be verified from a fetched source are marked **[U]**.Scope: a national map plus multi-year time series of rice area/production/yield per province (official) and per municipality (satellite-derived), with planting calendars from Sentinel-1, drought/El Niño impacts (2015–16, 2019, 2023–24), rainfall and soil-moisture anomalies, irrigation, and rice prices.

---

## 1. Official statistics

### 1.1 PSA OpenSTAT (PX-Web): palay production, area harvested, yield

**What exists.** OpenSTAT folder `DB/2E/CS` ("Crops") holds, among others (probed via the PX-Web JSON API, 2026-10-21):

| Table id | Title (as served) | Last updated |
|---|---|---|
| `0012E4EVCP0.px` | Palay and Corn: Volume of Production in Metric Tons by Ecosystem/Croptype, Quarter, Semester, Region and Province, 1987-2026 | 2026-07-29 |
| `0022E4EAHC0.px` | Palay and Corn: Area Harvested in Hectares by Ecosystem/Croptype, Quarter, Semester, Region and Province, 1987-2026 | 2026-07-29 |
| `0032E4ECNV0.px` / `0048E4ECNV1.px` | Rice and Corn: Monthly Total Stocks Inventory by Sector (national, and by Region) | 2026-10-05 |
| `0042E4EPFU0.px` | Palay: Estimated Inorganic Fertilizer Use by Region, Grade and Year, 2003-2025 | 2026-06-30 |

Source: `https://openstat.psa.gov.ph/PXWeb/api/v1/en/DB/2E/CS` (JSON, HTTP 200 on 2026-10-21).

**Dimensions** of the production table (`.../DB/2E/CS/0012E4EVCP0.px`, metadata probe 2026-10-21): Ecosystem/Croptype (6: Irrigated Palay, Rainfed Palay, Palay, White Corn, Yellow Corn, Corn); Geolocation (109: Philippines, 17 regions, provinces incl. the new Maguindanao del Norte/del Sur split); Year (40: 1987–2026); Period (7: Q1, Q2, Semester 1, Q3, Q4, Semester 2, Annual). The area table has identical dimensions. Yield is not a separate table; it is production ÷ area (PhilRice's RiceLytics lists a derived "Estimated palay production, area harvested, and yield per hectare" dataset sourced from OpenSTAT: `https://ricelytics.philrice.gov.ph/data_catalog/dataset/c46baf71-15d7-4f79-ae2e-ba986360414c`, found via search; the page itself returned 404 to a direct fetch, and `/data_catalog` redirects to a login, so RiceLytics is not a public bulk source).

**Geographic floor is the province.** The Palay Production Survey's domain of estimation is the province (FAO microdata catalogue of PSA's PPS 2016: `https://microdata.fao.org/index.php/catalog/1027`). No official municipal palay statistics are published on OpenSTAT; not searched, so **[U]** whether PSA releases municipal figures elsewhere (eFOI requests for municipal corn/palay figures exist, e.g. `https://foi.gov.ph/agencies/psa/corn-production-per-citymunicipality-in-pangasinan`, which suggests municipal numbers are obtainable only on request).

**Machine readability.** The PX-Web API is fully machine-readable and did **not** present a Cloudflare challenge to a plain curl client on 2026-10-21:
- `GET https://openstat.psa.gov.ph/PXWeb/api/v1/en/DB/` → 200, JSON list of 26 databases (Agriculture, Prices, Poverty, …).
- `GET .../api/v1/en/DB/2E/CS/0012E4EVCP0.px` → 200, JSON metadata (variables, codes, labels).
- `POST .../api/v1/en/DB/2E/CS/0012E4EVCP0.px` with body `{"query":[{"code":"Ecosystem/Croptype","selection":{"filter":"item","values":["2"]}},{"code":"Geolocation","selection":{"filter":"item","values":["0","12"]}}],"response":{"format":"json-stat"}}` → 200, `application/json`, 6.5 kB JSON-stat with all years and periods for Philippines + Pangasinan (status ".." marks not-yet-available 2026 cells).
- URL pattern: the browse path `/PXWeb/pxweb/en/DB/DB__2E__CS/<table>.px/` maps to the API path `/PXWeb/api/v1/en/DB/2E/CS/<table>.px` (the `DB__2E__CS` form returns 404 on the API).
- Limits from the table page: on-screen view capped at 1,000 rows × 30 columns and a selection may not exceed 100,000 cells (`https://openstat.psa.gov.ph/PXWeb/pxweb/en/DB/DB__2E__CS/0022E4EAHC0.px`, via search). The palay tables are ~3 × 109 × 40 × 7 ≈ 92k cells each, so one or two queries per table.

**Cloudflare.** `https://psa.gov.ph/` returns 403 "Just a moment…" (Cloudflare managed challenge) to curl, as does `https://openstat.psa.gov.ph/Terms` (403, same challenge page) and the PSA technical-notes PDF (403 via WebFetch). The `openstat.psa.gov.ph/PXWeb/api/...` endpoints are **not** challenged (verified 2026-10-21). So: data via API works unattended; HTML pages, PDFs and bulletins on psa.gov.ph need a browser or a cached copy.

**Licence.** OpenSTAT Terms of Use: statistical tables, datasets and documents on the site are under Creative Commons Attribution (CC BY); users must credit PSA or the named source agency, link to the terms, note changes, not imply endorsement, incorporate technical notes needed to understand the data, and not add legal/technical restrictions; material is provided as-is (`https://openstat.psa.gov.ph/Terms`, content via search snippet because the page is Cloudflare-challenged; mirrored verbatim at `https://rsso09.psa.gov.ph/terms-use`). The About page: data "can be reused by anyone … without any restrictions other than proper source attribution" (`https://openstat.psa.gov.ph/About`, via search). The Open Data Product Agreement applies the same CC BY classification (`https://openstat.psa.gov.ph/Metadata/Open-Data-Product-Agreement`, via search).

### 1.2 PSA Palay and Corn Quarterly Bulletin

PDF bulletins per quarter drawing on the Palay and Corn Production Survey (PCPS) (`https://psa.gov.ph/system/files/main-publication/Palay%2520and%2520Corn%2520Quarterly%2520Bulletin%252C%2520July%25202018_0.pdf`, via search). They add forecasts (standing crop, planting intentions) that are not in OpenSTAT. Hosted on psa.gov.ph (Cloudflare-challenged for bots). PSA technical notes for PPS/CPS: `https://www.psa.gov.ph/statistics/technical-notes/1684062406` (via search; surveys are quarterly, aimed at national and sub-national estimates of production, area, yield; NCR excluded). Whether PSA publishes CVs: see section 4.

### 1.3 PSA rice prices

- **Retail prices, monthly, by province** (not weekly): OpenSTAT `DB/2M/2018NEW/0042M4ARN01.px` "Cereals: Retail Prices of Agricultural Commodities by Geolocation, Commodity, Year and Period" — Geolocation 119 (Philippines, NCR, regions, provinces, City of Cotabato), Commodity 14 incl. `RICE, WELL-MILLED, 1 KG`, `RICE, REGULAR-MILLED, 1 KG`, `RICE, SPECIAL, 1 KG`, Year 2018–2026, Period = 12 months + Annual (API metadata probe 2026-10-21; updated 2026-10-02). An older-geocode series (`2M/NRP`, 2012-based) and old series (`2M/RP`) extend further back.
- **Farmgate palay prices, monthly, by province**: `DB/2M/NFG/0032M4AFN01.px` "Cereals Farmgate Prices by Geolocation, Commodity, Year and Period" — 111 geolocations, `Palay [Paddy] Fancy, dry (conv. to 14% mc)` and `Palay [Paddy] Other Variety, dry`, 2010–2026, monthly (probe 2026-10-21; updated 2026-10-13). Also `0162M4ESAP0.px` seasonally adjusted farmgate price by quarter, 2016–2026.
- **Wholesale**: `DB/2M/NWSNEW/0052M4AWB01.px` "Cereals: Wholesale Selling Prices" (updated 2026-10-07).
- **Weekly** rice prices exist only as PSA's weekly "Updates on Palay, Rice and Corn Prices" PDFs (national averages for well-milled/regular-milled, e.g. `https://psa.gov.ph/system/files/main-publication/Updates%2520on%2520Palay%252C%2520Rice%2520and%2520Corn%2520Prices%252C%2520Week%25203%2520of%2520June%25202020.pdf`, via search). Regional weekly breakdowns inside those PDFs: **[U]**.
- **Daily/weekly retail prices from DA**: `https://www.da.gov.ph/price-monitoring/` (HTTP 200 to curl, 2026-10-21) lists "Weekly Average Retail Prices" PDFs from August 21–25, 2023 to the current week (Oct 12–18, 2026) and a "Daily Price Index" PDF per day (2025 and 2026), each 100–400 kB; these are NCR market surveys (the Sept 2025 Kadiwa report cites "DA's NCR public market monitoring", `https://malaya.com.ph/business/corporate/rice-cheaper-by-p3-kilo-at-kadiwa-from-today`). PDF-only; parsing needed; licence not stated (**[U]**, Philippine government works are generally not copyrighted under the IP Code but reuse conditions are not published on the page).

### 1.4 DA-BPI / PhilRice

PhilRice runs PRiSM and RiceLytics. RiceLytics' data catalogue requires login (`https://ricelytics.philrice.gov.ph/data_catalog` → Inertia `Auth/Login` component, 2026-10-21). PRiSM's "Data Request" link pops a notice: "For users not affiliated with PRiSM, file via the FOI portal" (JS on `https://prism.philrice.gov.ph/`, 2026-10-21). No DA-BPI rice dataset located (BPI handles plant industry/seeds; no probe done) **[U]**.

### 1.5 DA and NDRRMC El Niño damage reports

- **NDRRMC**: `https://ndrrmc.gov.ph/` returns 403 (Cloudflare challenge) to curl (2026-10-21). Situational reports for the 2023–24 El Niño were reported by the press with running totals: P865.16 M (28 Feb 2024, 15,341 farmers, 13,521 ha), P941.7 M (29 Feb), P1.23 B (11 Mar; Western Visayas P678.7 M; 11,276 ha totally damaged, 15,455 ha partially), P1.6 B (late April; 46,805 farmers, 44,437 ha) (`https://newsinfo.inquirer.net/1912233/...`, `https://alpha.pna.gov.ph/articles/1220474`, `https://newsinfo.inquirer.net/1916924/...`, `https://newsinfo.inquirer.net/1935039/...`). The NDRRMC provincial value breakdown for Western Visayas (Iloilo ≈ P470 M, Antique ≈ P120.6 M, Negros Occ. ≈ P55.1 M, Aklan ≈ P30.2 M, Capiz ≈ P2.7 M) was reported by `https://tribune.net.ph/2024/03/18/western-visayas-suffers-over-p600-m-agri-damage`. Sitreps are PDFs with tables per region/province; numbers change daily and differ between DA and NDRRMC (see below), so any time series must be versioned by report date.
- **DA-DRRM bulletins** (separate series, higher totals): P151.3 M (early Feb 2024; 3,923 farmers, 3,291 ha), P357.4 M (late Feb; 6,523 ha; 11,480 t palay lost), P1.31 B (12 Mar; ≈14,142 ha palay), P2.63 B (early Apr; 53,879 ha; 72,733 t palay), P6.3 B later (`https://alpha.pna.gov.ph/articles/1218535`, `https://newsinfo.inquirer.net/1909471/...`, `https://news.abs-cbn.com/news/2024/3/13/el-ni-o-damage-hits-p1-31-billion-1634`, `https://newsinfo.inquirer.net/?p=1925738`, `https://newsinfo.inquirer.net/1939590/...`). PDFs on da.gov.ph; format changes between events.
- **2015–16**: PSA attributed the H1 2016 palay decline (7.65 Mt vs 8.32 Mt, −6.1 % in Q2) to "prolonged dry spell due to El Niño", worst in SOCCSKSARGEN, ARMM, Caraga and the Visayas (`https://business.inquirer.net/213553/el-nino-pulls-h1-agri-production`; PSA Q2 2016 report `https://www.psa.gov.ph/system/files/main-publication/PerfomanceofAg_April%2520to%2520June2016_0.pdf`). Region XII palay −7.0 % in 2016 (`https://rsso12.psa.gov.ph/system/files/attachment-dir/R12-SR2017-10_0.pdf`).
- **2019**: PSA Q1 2019 palay forecast 4.62 Mt vs 4.88 Mt (`https://newsinfo.inquirer.net/1096645/...`); "Prolonged El Niño curbed third quarter palay output" (`https://business.inquirer.net/480553/...`).
- **2023–24**: PSA Q3 2024 palay 3.36 Mt, −11.4 % y/y; Q2 2024 est. −8.4 % to 3.89 Mt (`https://context.ph/2024/06/19/...`, via search). Note that typhoons (Carina, Kristine, etc.) overlap the 2024 drought signal — attribution to El Niño alone is not safe.
- **2026**: DA projects up to 700,000 t rice loss under a strong El Niño in Q4 2026 (`https://mb.com.ph/2026/05/28/strong-el-nino-may-slash-philippine-rice-output-by-700000-mt`), and PAGASA's 1 Oct 2026 assessment projects meteorological drought in CALABARZON/MIMAROPA provinces by Jan 2027 (`https://tribune.net.ph/2026/10/13/calabarzon-mimaropa-face-2027-drought-threat`). A live event is unfolding during the project window.

### 1.6 BSWM

No BSWM drought bulletin or soil-moisture map series was found. BSWM runs automatic weather stations whose readings feed a PhilSA agricultural-drought mapping project (NDVI, LST, rainfall) (`https://sentinel-asia.org/meetings/SA3JPTM9/agenda/Day1/1300_Philippine_Session/1300E_PhilSA_Oca.pdf`, via search). BSWM's public role in drought is workshops and advisories (`https://www.droughtmanagement.info/literature/UNW-DPC_NDMP_Country_Report_Philippines_2014.pdf`). Treat BSWM as not a data source **[U]**.

### 1.7 PAGASA

- **Advisories**: monthly El Niño/La Niña advisories as PDFs (full + "Simplified"), e.g. five El Niño advisories dated 2026-06-09 … 2026-10-07, plus a "Dry Spell / Drought Assessment and Outlook" PDF; no licence stated (`https://bagong.pagasa.dost.gov.ph/climate/el-nino-la-nina/advisories`). Seasonal outlooks are PDFs (`https://pubfiles.pagasa.dost.gov.ph/pagasaweb/files/climate/seasonalclimateoutlook/Seasonal Outlook_Jan-June 2024-FINAL.pdf`). The drought/dry-spell maps are province-level categorical maps inside PDFs; extracting a province × month table means scraping images or tables **[U]** on exact format per issue.
- **Definitions** (as reported): dry spell = three consecutive months below-normal rainfall or two months >60 % below average; drought = three consecutive months way-below-normal or five months below-normal (`https://tribune.net.ph/2026/10/13/calabarzon-mimaropa-face-2027-drought-threat`; `https://www.gulf-times.com/story/626806`).
- **Station data are request-based and non-redistributable.** CADS-07 Rev. 2 "Terms and Conditions of Use for Climatological Data" (`https://pubfiles.pagasa.dost.gov.ph/pagasaweb/files/climate/CADS-07-Rev-2-Terms-and-Conditions-of-Use-for-Climatological-Data-1.pdf`, text extracted 2026-10-21): data provided "free of charge or with applicable fees" depending on stated purpose; academic/non-commercial requests "are provided free of charge"; but "No part of the data shall be redistributed by the Recipient to other individuals nor published/made available on the internet, social networking sites, personal/institutional websites, and in any other forms of mass media". A public portfolio app therefore cannot republish PAGASA station series; use CHIRPS/ERA5-Land instead and cite PAGASA advisories as documents only. Older Citizen's Charter fee schedule: P36/yr/parameter monthly, P360/yr/parameter daily (`https://pubfiles.pagasa.dost.gov.ph/ppds/Cit_Charter.pdf`, via search).

---

## 2. Satellite rice mapping

### 2.1 PRiSM (IRRI / PhilRice / DA)

Operational since 2014 (IRRI + DA; `https://www.cgiar.org/innovations/satellite-rice-monitoring-the-philippine-rice-information-system-prism/`). Core activities page: rice area maps "every cropping season" from "Synthetic Aperture Radar images from Sentinel 1A" using sarmap's MAPscape-Rice, planting dates and growth stages, drought-affected areas (optical) and flood-affected areas (SAR), yield via a crop model (ORYZA) (`https://prism.philrice.gov.ph/aboutus/core-activities/`). Data products listed on the home page: Rice Area, Planting Dates, Flooded Rice Area, Rice Yield, Rice Production (`https://prism.philrice.gov.ph/`). **Public outputs: none downloadable.** The site has a login; non-affiliated users are told to file via the FOI portal; PNA reports validated data go "to their registered stakeholders every seventh day of the succeeding month" (`https://alpha.pna.gov.ph/articles/1208259`). Reported accuracy "up to 95 percent" vs ground data (`https://archives.tribune.net.ph/?p=174268`). Setiyono et al. 2019 (IJRS, doi 10.1080/01431161.2018.1547457) report 81–92 % agreement between modelled and official yields across several countries (slide citing it: `https://events.development.asia/system/files/materials/2021/10/202110-integration-remote-sensing-and-crop-model-yield-estimation.pdf`); the paper itself returned 403 **[U]** for PH-specific numbers. Book chapter on PRiSM 2016–2018 data: `https://repository.lsu.edu/plantsoil_pubs/719` (abstract only). PRiSM is the benchmark the project would be compared against, and its maps can be requested via FOI (eFOI, `https://foi.gov.ph`), but relying on that is a risk.

### 2.2 Research rice maps that cover the Philippines

- **NESEA-Rice10** (Han et al. 2021, ESSD 13:5969): annual 10 m paddy-rice maps 2017–2019 for NE and SE Asia including the Philippines, MODIS + Sentinel-1 rule-based; R² vs PH provincial statistics 0.81–0.87 with some provinces underestimated; rain-fed/upland rice with weak flooding signal may be missed (`https://essd.copernicus.org/articles/13/5969/2021/`). Data on Zenodo `https://zenodo.org/records/5645344`, **CC BY 4.0**, 5°×5° GeoTIFF tiles, EPSG:4326. Philippines tiles (5–20 N, 115–130 E) are small: the 2017–2019 composite tiles sum to ≈58 MB; per-year tiles ≈23–27 MB per year. No 20–25 N tile is listed, so Batanes/northern Cagayan (≈20–21 N) are missing. Good as an independent baseline.
- **Rudiyanto et al. 2019** (Remote Sensing 11(14):1666): monthly 10 m rice growing-area and growth-stage maps from Sentinel-1 phenology in GEE, SE Asia (`https://mdpi-res.com/d_attachment/remotesensing/remotesensing-13-00990/article_deploy/remotesensing-13-00990.pdf` is a different 2021 paper; the Rudiyanto reference came via the search summary) **[U]** on code availability.
- **dela Torre et al. 2021** (Geo-spatial Information Science): Sentinel-2 in GEE for Iloilo, OA 68 % dry season, 75 % wet season (`https://doaj.org/article/6578d08930df4d6fbe54a0a0e2993fbb`).
- **Xiao et al. 2006**: MODIS 500 m paddy maps for 13 S/SE Asian countries, 2002 (`https://www.ceom.ou.edu/media/docs/upload/Xiao_2006_rice_asia.pdf`); a method, not a maintained product. A continuous 2000–2020 500 m Asian paddy dataset was not found **[U]**.
- Ratoon-rice study in four PH provinces: S1+S2 random forest OA 92 %; optical limited by wet-season cloud (`https://research.utwente.nl/en/publications/ratoon-rice-mapping-based-on-sentinel-1-and-sentinel-2-imagery/`).

### 2.3 WorldCereal (ESA, 2021)

Products: temporarycrops (tc-annual), maize (tc-maize-main, tc-maize-second), wintercereals, springcereals, irrigation, activecropland; 10 m; CC BY 4.0; on GEE as `ESA/WorldCereal/2021/MODELS/v100` and on Zenodo 10.5281/zenodo.7875105 (`https://developers.google.com/earth-engine/datasets/catalog/ESA_WorldCereal_2021_MODELS_v100`; `https://zenodo.org/records/7875105`). **Rice is not a WorldCereal class** ("cereals" = wheat, barley, rye). Zenodo files are global ZIPs by product (e.g. temporarycrops classification 15.5 GB, maize-main classification 18.2 GB, irrigation-main 17.2 GB; 236.9 GB total), tiled per agro-ecological zone (up to 106 AEZ GeoTIFFs per ZIP) — the PH subset must be clipped in GEE rather than downloaded. Useful only as a 2021 temporary-cropland/irrigation mask.

### 2.4 Land-cover cropland classes

- **ESA WorldCover** v100 (2020) and v200 (2021), 10 m, class 40 = cropland, CC BY 4.0 (`https://developers.google.com/earth-engine/datasets/catalog/ESA_WorldCover_v200`; `https://registry.opendata.aws/esa-worldcover-vito/index.html`).
- **Dynamic World** V1: 10 m, 2015-06-27 → present (catalogue shows availability to 2026-10-20), nine classes incl. crops (value 4), generated only for scenes ≤35 % cloud, CC BY 4.0 with attribution to Google/NGS/WRI and "contains modified Copernicus Sentinel data" (`https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1`).

### 2.5 Sentinel-1 GRD in GEE

`COPERNICUS/S1_GRD`: 2014-10-03 → present (daily ingest, ≤2 days latency), IW/EW/SM modes, VV/VH etc., 10 m pixels, `orbitProperties_pass` = ASCENDING/DESCENDING, preprocessed with S1 Toolbox (thermal noise removal, radiometric calibration, terrain correction, dB), governed by the Copernicus Sentinel Data Terms (`https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S1_GRD`). Revisit: ≈6 days with two satellites. Constellation history: S1A launched 2014-04-03; S1B launched 2016-04-25, lost after the 2021-12-23 power anomaly, mission ended Aug 2022 (`https://www.esa.int/Applications/Observing_the_Earth/Copernicus/Sentinel-1/Mission_ends_for_Copernicus_Sentinel-1B_satellite`); S1C launched 2024-12-05 (Vega-C); S1D launched 2025-11-04 (Ariane 6); ESA ran "Time to say goodbye to Sentinel-1A" on 2026-06-30 (`https://www.esa.int/Applications/Observing_the_Earth/Copernicus/Sentinel-1`). Consequence: over the Philippines the 2022–early 2025 record is single-satellite (12-day revisit per orbit) and the 2026 record transitions to S1C/S1D; a phenology method must tolerate a change in revisit and in platform. Whether both ascending and descending IW tracks cover all of the Philippines, and the exact per-orbit cadence, was not verified **[U]** (standard S1 IW land coverage should include PH on both passes, but check with a GEE footprint count before committing).

---

## 3. Drought and climate indicators

| Indicator | Source / GEE id | Resolution, period | Licence | Notes |
|---|---|---|---|---|
| Rainfall | CHIRPS v2.0 daily/pentad (`UCSB-CHG/CHIRPS/DAILY`) | 0.05°, 1981→ | Public domain (CC0-style waiver by P. Peterson; GEE: "in the public domain") `https://registry.opendata.aws/deafrica-chirps/`, `https://developers.google.com/earth-engine/datasets/catalog/UCSB-CHG_CHIRPS_DAILY` | ERDDAP note: free use/redistribution, "not intended for legal use" |
| Reanalysis (temp, precip, soil moisture layers) | ERA5-Land (`ECMWF/ERA5_LAND/*`) | 0.1°, 1950→ | Copernicus/C3S licence: any lawful use incl. reproduction, distribution, adaptation; ECMWF says CC-BY applies to ERA5-Land; derived products must say "Contains modified Copernicus Climate Change Service information [year]" and that EC/ECMWF are not responsible (`https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_STATIC`; `https://confluence.ecmwf.int/spaces/CKB/pages/222493842/...`) | |
| Soil moisture | SMAP L4 (`NASA/SMAP/SPL4SMGP/008`; 007 deprecated) | 9 km EASE-grid (11 km in GEE), 3-hourly, 2015-03-31→ | NASA: "public domain and available without restriction on use and distribution" (`https://developers.google.com/earth-engine/datasets/catalog/NASA_SMAP_SPL4SMGP_007`) | bands sm_surface, sm_rootzone, *_pctl; starts 2015, so cannot cover a 20-year baseline; SMOS not probed **[U]** |
| NDVI/EVI | MODIS MOD13Q1 v6.1 (`MODIS/061/MOD13Q1`) | 250 m, 16-day, 2000→ | LP DAAC: "no restrictions on subsequent use, sale, or redistribution" (`https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD13Q1`) | Terra ageing; check end date |
| VHI/VCI/TCI | NOAA STAR Blended-VHP | 4 km weekly, 1981→ (AVHRR 1981–2012, VIIRS 2013→); 1 km since 2019 via NOAA CLASS | No licence text; STAR says products "provided for experimental use only" and the 4 km product is "for demonstration purposes only" (`https://www.star.nesdis.noaa.gov/smcd/emb/vci/VH/vh_ftp.php`) | US federal work, so public domain in practice **[U]**; GeoTIFF weekly files, annual .gz for earlier years; wget only |
| SPEI | Global SPEI database v2.10 (`CSIC/SPEI/2_9` on GEE) | 0.5°, monthly, 1901–2023 | CSIC: Open Database License (ODbL) + DbCL; GEE catalogue says CC-BY 4.0 — conflict (`https://spei.csic.es/database.html`; `https://developers.google.com/earth-engine/datasets/catalog/CSIC_SPEI_2_9`) | 0.5° ≈ 55 km: too coarse for municipalities; better to compute SPI/SPEI from CHIRPS + ERA5-Land PET in-house |
| ENSO | NOAA CPC ONI (ERSST v6 table; RONI now official for monitoring) | 3-month seasons, 1950→ | US government work; no restriction stated (`https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ONI_v5.php` now redirects to an ERSSTv6 table; `https://psl.noaa.gov/data/correlation/oni.data` copy) | Peak ONI values for 2015–16, 2018–19, 2023–24 not fetched **[U]** (commonly cited ≈2.6, ≈0.9, ≈2.0) |
| ASAP (JRC) | `https://agricultural-production-hotspots.ec.europa.eu/download.php` | GAUL level 1–2 warnings every 10 days since May 2001; hotspots monthly since Oct 2016; phenology (SOS/EOS), rainfall, SPI-1/3, FPAR anomalies, soil moisture rasters | "Reuse is authorised, provided the source is acknowledged" (EC Decision 2011/833/EU) | PH coverage not confirmed on the page ("all countries at level 1") **[U]**; v4.0 uses CHIRPS between 50 N/S |

**GEE compute for a 20-year monthly per-municipality reduction.** Earth Engine noncommercial projects get a monthly quota: Community tier 150 EECU-hours, Contributor tier 1,000, Partner tier 100,000 (by application); quota resets monthly, soft limits (restricted mode after exhaustion) (`https://developers.google.com/earth-engine/guides/noncommercial_tiers`). Google's benchmarks: a 12-month Sentinel-2 10 m composite export for Germany costs 3,349.54 EECU-h, Nigeria 3,539.28, Bay Area 105.09; at 30 m Germany 622.11; "high-volume extraction" of 1,000 samples over 12 months at 10 m ≈ 10–15 EECU-h (`https://developers.google.com/earth-engine/guides/computation_benchmarks`). Estimates for this project **[U]**: zonal monthly means of CHIRPS (0.05°), ERA5-Land (0.1°), SMAP (9 km) and MOD13Q1 (250 m) over ≈1,640 municipalities for 20 years are small (single-digit to low tens of EECU-h in total, since the rasters are coarse); the Sentinel-1 part dominates (see section 7).

---

## 4. Scientific honesty

- **Satellite rice *area* is defensible; satellite *yield* is not, in a portfolio setting.** PRiSM itself couples SAR area/phenology with a crop model and field surveys to get yield; published agreement with official yields is 81–92 % across countries (section 2.1), and NESEA-Rice10 area maps reach R² 0.81–0.87 against PH provincial statistics with systematic under-estimation of rain-fed/upland rice (`https://essd.copernicus.org/articles/13/5969/2021/`). Safe product: "flooded/transplanted rice signal per municipality per month" and "start-of-season date", explicitly not yield.
- **PSA figures are survey estimates with sampling error.** PPS design: replicated two-stage stratified sampling, barangays (PSU) then farming households (SSU), four replicate barangays per stratum, 4–25 households per barangay, frame from the 1991 Census of Agriculture with list updates in 2007 and 2011, domain = province, response ≈85 % (`https://microdata.fao.org/index.php/catalog/1027`; `https://psada.psa.gov.ph/catalog/112`). **Whether PSA publishes CVs per province: not confirmed** (the FAO catalogue does not say; the PSA technical-notes PDF is Cloudflare-blocked) **[U]**. Assume small provinces (e.g. Batanes, Siquijor) have wide errors; show province values with a caveat and never annualise municipal "shares".
- **Cloud cover**: optical sensors are "limited by cloud cover, especially during the wet season" in PH rice areas, and SAR "can solve the problem of cloud cover during rainy or wet seasons when more than 70 % of rice is produced" (`https://research.utwente.nl/en/publications/ratoon-rice-mapping-based-on-sentinel-1-and-sentinel-2-imagery/`; `https://a-a-r-s.org/proceeding/ACRS2023/Remote Sensing Applications/ACRS2023098.pdf`). Dynamic World only emits predictions for scenes ≤35 % cloud, so wet-season gaps are structural. Use SAR for phenology; use MODIS/VHI only as anomalies with explicit valid-observation counts.
- **Attribution**: 2024 Q2/Q3 palay declines coincide with El Niño *and* typhoons; DA vs NDRRMC damage totals differ by a factor of ~2 at the same date (section 1.5). Present "anomaly relative to 2015–2024 baseline" and "reported damage (agency, report date)", not "drought caused X".
- **Safe claims look like**: "Sentinel-1 flooding signal in Q1 2024 was 23 % below the 2017–2023 median in municipality M"; "CHIRPS rainfall Dec 2023–Mar 2024 was in the lowest decile since 1981"; "PSA Q2 2024 provincial palay −8 % y/y (survey estimate)". Avoid "forecast", "yield", "loss caused by El Niño".

---

## 5. Existing products and public interest

- **FAO GIEWS country brief, Philippines** (ref. date 2026-01-29): 2025/26 paddy forecast 19.7 Mt; rice prices fell from a record high in May 2024 through Aug 2025 after tariff cuts, a food-security emergency (Feb 2025), buffer-stock releases and a P43/kg MSRP (16 Jul 2025); imports 3.6 Mt in 2025 (`https://www.fao.org/giews/countrybrief/country.jsp?code=PHL`). National-level text and four charts; no sub-national series.
- **JRC ASAP**: 10-day GAUL-1/2 warnings and monthly hotspots, downloadable CSV/shapefile/GeoTIFF, reuse with acknowledgement (section 3). Coarse, global, not rice-specific.
- **FEWS NET**: does not cover the Philippines (brief states so; not re-verified) **[U]**.
- **DA**: Price Monitoring page (weekly retail PDFs since Aug 2023, daily price index PDFs) (`https://www.da.gov.ph/price-monitoring/`); Bantay Presyo regional task forces (`https://alpha.pna.gov.ph/articles/1209482`); no interactive dashboard found **[U]**.
- **PhilRice PRiSM / RiceLytics**: closed to the public (section 1.4, 2.1). DEPDev (ex-NEDA) is using PRiSM GIS staff to fill LGU data gaps (`https://prism.philrice.gov.ph/depdev-taps-prisms-gis-specialists-to-bridge-local-agricultural-data-gaps/`), i.e. a public per-LGU view does not exist.
- **Public interest is high and sustained**: P20/kg rice was Marcos's 2022 campaign pledge (`https://newsinfo.inquirer.net/1743750/...`); EO 39 price caps P41/P45 (Sept 2023) lifted by EO 42 (4 Oct 2023) (`https://alpha.pna.gov.ph/articles/1211082`); rice inflation 24.4 % in March 2024, a 15-year high (`https://gmanetwork.com/news/money/economy/902847/...`); 2024 SONA opened on rice prices (`https://gmanetwork.com/news/topstories/nation/914278/...`); EO 62 cut the tariff to 15 % (July 2024); EO 93 suspended imports from 1 Sept 2025 after farmgate palay fell to P8–10/kg in places (PSA: −27.8 % y/y to P17.11 in Aug 2025), extended to year-end (`https://newsinfo.inquirer.net/2133076/rice-import-ban-extended-until-year-end`; `https://www.da.gov.ph/president-marcos-eye-longer-rice-import-ban-higher-tariff-da-chief/`); May 2026: Middle-East war fertiliser shock and queues for P20 subsidised rice (`https://www.khaleejtimes.com/world/asia/philippine-rice-crisis-looms-...`). The 2016 Kidapawan protest (drought-hit farmers demanding rice, dispersal with fatalities, 1 April 2016) is the canonical drought-politics event **[U]** (Wikipedia fetch returned 404 under both titles; verify with news archives).

---

## 6. Licences and redistribution; fit with the archiving standard

| Source | Licence | Archive raw privately? | Publish processed? |
|---|---|---|---|
| PSA OpenSTAT (production, area, prices, stocks) | CC BY (attribution, link to terms, note changes, include technical notes) | Yes (JSON-stat snapshots per release date) | Yes, with PSA credit |
| PSA PDFs (bulletins, weekly prices), DA price PDFs, DA/NDRRMC sitreps, PAGASA advisories | Government documents; no explicit licence; PAGASA PDFs no terms | Yes (PDF copies; needed because psa.gov.ph/ndrrmc.gov.ph are Cloudflare-challenged) | Extracted tables yes, with source and report date; keep PDFs private or link |
| PAGASA station data | CADS-07: no redistribution, no internet publication | Do not acquire for this project | No |
| PRiSM maps | Not public; FOI request only | Only if obtained; terms unknown **[U]** | Not without written permission |
| Sentinel-1 GRD | Copernicus legal notice: free, full and open; reproduction, distribution, adaptation allowed; notice "Copernicus Sentinel data [Year]" / "contains modified Copernicus Sentinel data [Year]" (`https://sentinels.copernicus.eu/documents/247904/690755/Sentinel_Data_Legal_Notice`, text extracted) | Not needed (GEE is the archive); archive the derived per-municipality tables | Yes |
| Dynamic World, WorldCover, WorldCereal, NESEA-Rice10 | CC BY 4.0 | NESEA tiles yes (≈60 MB); others via GEE | Yes |
| CHIRPS | Public domain | Yes (derived) | Yes |
| ERA5-Land | Copernicus/CC-BY with required notice | Derived only | Yes with notice |
| SMAP, MODIS, NOAA VHI, ONI | Public domain / no restriction (VHI "experimental use only" disclaimer) | Derived only; VHI weekly GeoTIFFs for PH clip | Yes with disclaimer |
| SPEIbase | ODbL (share-alike) per CSIC; CC-BY per GEE | Avoid; compute SPI/SPEI in-house from CHIRPS/ERA5-Land | n/a |
| ASAP | Reuse with acknowledgement | Yes (CSV/GeoTIFF) | Yes |

Fit: every source goes in `sources.yaml` with primary → mirror (GEE / Zenodo / HF) → private `abrycta/rice-drought-archive` release. Raw PDFs and OpenSTAT JSON snapshots are the items that genuinely need the private archive, because the primaries are challenge-gated and the PX-Web tables are overwritten on each release (the production table was updated 2026-07-29 with 2026 cells marked ".."). PAGASA station data is excluded by licence; PRiSM by access.

---

## 7. Volumes and free-tier feasibility

- **Official tables**: production + area ≈ 2 × 92k cells; retail prices ≈ 119 × 3 × 9 × 13 ≈ 42k; farmgate ≈ 111 × 2 × 17 × 13 ≈ 49k; stocks small. Everything fits in a few MB of Parquet.
- **Per-municipality monthly tables**: ≈1,640 cities/municipalities **[U]** (exact count depends on the PSGC release used) × 12 × 20 years ≈ 394k rows per indicator; with ~8 indicators (CHIRPS, ERA5-Land T/P/soil, SMAP, NDVI, VHI, S1 VH/VV flooded fraction, SOS) ≈ 3 M rows, ≈ 30–80 MB Parquet **[U]**. Neon Free: 1 GB per project, 100 CU-hours/month, 20 GB across projects (`https://neon.com/pricing`) — fits, but the app should not need Postgres at all; static Parquet/JSON per province or per indicator keeps every file under the Cloudflare Pages 25 MiB per-asset limit (20,000 files/site, 500 builds/month, 20-min builds) (`https://developers.cloudflare.com/pages/platform/limits/`). HF datasets: free public storage "best-effort", no per-repo limit, Parquet recommended, <100k files (`https://huggingface.co/docs/hub/storage-limits`).
- **Rasters for the map**: NESEA-Rice10 PH tiles ≈ 60 MB total (CC BY). A Sentinel-1-derived annual rice-extent raster at 10 m for PH would be several hundred MB per year **[U]** — publish as vector tiles (PMTiles) aggregated to municipality, or COGs on HF, not on Pages.
- **Sentinel-1 processing in GEE** **[U]**: Philippines land ≈ 300k km²; S1 IW VV+VH at 10 m, ≈30 scenes/year/orbit (12-day) to ≈60 (6-day) per location, 2015→2026 ≈ 11 years. Google's benchmark for a 10 m 12-month Sentinel-2 composite export over Germany (357k km²) is ≈3,350 EECU-h; a Sentinel-1 per-pixel phenology (time-series smoothing + peak/flood detection) is heavier per pixel than a median composite, so a 10 m national annual rice map is plausibly 1,000–5,000 EECU-h per year **[U]** — beyond the 150 EECU-h Community tier and marginal on the 1,000 EECU-h Contributor tier even if staged over months. What is feasible on the free tiers: (a) per-municipality monthly zonal statistics of VH/VV backscatter at 100 m (≈100× fewer pixels; tens of EECU-h per year **[U]**), from which flooding/transplanting anomalies and a municipal start-of-season are derived; (b) a 10 m map for one or two showcase provinces (Nueva Ecija, Iloilo) per year; (c) use NESEA-Rice10 and Dynamic World crops as the fixed rice mask so the S1 reduction only touches rice pixels (cuts cost roughly in proportion to rice share of land, ≈15 % **[U]**). A multi-month, chunked batch plan with EECU-time daily caps set in Cloud Console is required (`https://developers.google.com/earth-engine/guides/noncommercial_tiers`).

---

## 8. Technical showcase

Distinct from the Lights (per-LGU annual night-light index vs poverty statistic) and Typhoon Replay apps:
- **SAR time series and phenology extraction**: per-municipality VH backscatter curves, flood-dip detection, start-of-season dating, double-cropping detection — a different sensor family (radar), a different cadence (sub-monthly) and a signal-processing problem rather than a brightness sum.
- **Anomaly detection with baselines**: SPI from CHIRPS, soil-moisture percentiles (SMAP provides `sm_rootzone_pctl` natively), VHI, compared with planting delays; compose an "agricultural drought" composite with explicit valid-observation counts.
- **Price-vs-supply joins**: monthly provincial farmgate palay and retail rice prices (OpenSTAT) against provincial production, stocks inventory and import/policy events (tariff cuts, price caps, import ban), with event markers.
- **Document pipeline**: versioned extraction of DA/NDRRMC damage tables by report date, showing how the "damage" number grows during an event.

**Overlap risk with Lights** is real and must be designed out: if the product collapses to "annual S1 rice index per municipality vs PSA provincial production", it is the same chart with a different raster. The differentiators are the intra-annual phenology (planting calendars, two seasons), the drought-event timeline, and prices. If those are cut for scope, the overlap becomes the headline.

---

## 9. Risks

1. **GEE compute**: a national 10 m Sentinel-1 phenology product is likely to exceed the free noncommercial quota; mitigation is coarser zonal statistics plus showcase provinces (section 7) **[U]** on exact EECU-h.
2. **No public ground truth for municipal rice**: PSA stops at province; PRiSM and RiceLytics are closed; validation relies on NESEA-Rice10 (2017–2019) and provincial aggregates. Municipal numbers will be unvalidated.
3. **Platform discontinuity in the S1 record** (S1B loss Dec 2021, single-satellite 2022–2025, S1C/S1D from 2025–26, S1A retired mid-2026): revisit and incidence-angle mix change across the series, which can masquerade as phenology change.
4. **Attribution and politics**: rice is a live political issue (price caps, tariff, import ban, 2026 El Niño). Charts can be read as policy claims; damage totals disagree across agencies.
5. **Scraping fragility**: psa.gov.ph, ndrrmc.gov.ph and openstat HTML pages are behind Cloudflare challenges; only the PX-Web API is open, and that could change.
6. **Licence traps**: PAGASA station data is non-redistributable; SPEIbase is ODbL share-alike; VHI is "experimental use only".
7. **Scope creep**: nine data families; the honest, feasible core is official statistics + prices + coarse drought indicators + a limited SAR phenology layer.

---

## Scored table (1–5; 5 = best / lowest risk)

| Criterion | Score | Justification |
|---|---|---|
| Data availability / licences | 4 | PSA OpenSTAT is CC BY and machine-readable via an un-challenged PX-Web API (prices, production, area, stocks by province); all climate/satellite inputs are PD or CC BY; PRiSM is closed and PAGASA stations are non-redistributable, but neither is essential. |
| Volume / free-tier feasibility | 3 | Tabular outputs are tiny and fit Pages/HF/Neon easily; the national 10 m Sentinel-1 phenology layer likely exceeds the 150–1,000 EECU-h/month noncommercial quota and must be downscaled to 100 m zonal stats or showcase provinces **[U]**. |
| Scientific honesty | 3 | Rice area and phenology anomalies from SAR are defensible; yield is not; municipal values have no public ground truth; PSA CVs not confirmed; drought vs typhoon attribution overlaps in 2024. Honest framing is possible but must be enforced in every chart. |
| Public interest / portfolio appeal | 5 | Rice prices were the top political issue 2023–2025 (24.4 % rice inflation, price caps, tariff cut, import ban) and a strong El Niño is forecast for Q4 2026; no public per-LGU rice/drought view exists. |
| Technical showcase | 4 | SAR time series, phenology extraction, anomaly baselines and price-supply joins are new relative to Lights/Typhoon; the risk is that scope cuts leave only an annual index vs statistic, which duplicates Lights. |
| Risk (5 = low) | 3 | Compute cost, closed validation data, S1 platform discontinuity and political attribution are each manageable but together material. |

**Top three risks**: (1) GEE EECU budget for national Sentinel-1 phenology; (2) no public municipal ground truth (PRiSM/RiceLytics closed) so municipal outputs stay unvalidated; (3) Sentinel-1 constellation discontinuities (2021 loss of S1B, 2024–26 S1C/S1D, 2026 S1A retirement) and typhoon/drought confounding that undermine anomaly claims.

---

## 10. Items not verified (2026-10-21)

Not searched/verified: NIA irrigation status report formats and years (nia.gov.ph lists "Status of Irrigation Development" and "Service and Irrigated Area of Irrigation Systems" pages, format unknown); exact municipality count per PSGC; ONI peak values; Kidapawan 2016 details; Sentinel-1 ascending/descending footprint counts over PH; Whitcraft-style cloud-frequency statistics for PH; DA-BPI datasets; FEWS NET non-coverage; PSA technical-notes CV statement (Cloudflare-blocked PDF); Setiyono et al. 2019 PH-specific yield accuracy (403).
