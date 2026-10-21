<!-- Research notes gathered 2026-10-21 for docs/CANDIDATES.md. Kept as evidence: every claim has its URL and access date; [U] marks unverified items. The comparison and the plan are in the parent folder. -->

# Candidate topic: Philippine air quality from satellites and ground stations

Research dossier, 2026-10-21. Research only (WebSearch, WebFetch, two small HTTP probes); no downloads, no accounts, no code. All URLs accessed 2026-10-21 unless stated. **[U]** marks claims I could not verify from a fetched page (search-snippet only, blocked page, or my own estimate).

---

## 1. Satellite sources

### 1.1 Sentinel-5P TROPOMI on Google Earth Engine (OFFL L3 collections)

All six collections share: 1,113.2 m pixel size (resampled from a native 3.5 x 5.5 km since 6 Aug 2019, 3.5 x 7 km before), one asset per orbit (no cross-product aggregation; products crossing the antimeridian are split into `_1`/`_2`), the GEE metadata says "revisit interval of 2 days" while the description text says daily global coverage (page inconsistency; in practice one or two orbits touch the Philippines each day), and "The use of Sentinel data is governed by the Copernicus Sentinel Data Terms and Conditions".

| Collection | Start (GEE) | Main bands | QA filter applied in L3 | Source |
|---|---|---|---|---|
| `COPERNICUS/S5P/OFFL/L3_NO2` | 2018-06-28 | `NO2_column_number_density`, `tropospheric_NO2_column_number_density`, `stratospheric_...`, slant column, `tropopause_pressure`, `absorbing_aerosol_index`, `cloud_fraction`, angles (mol/m²) | pixels removed below qa 75% for tropospheric NO2 (harpconvert `validity>50` in the example); keep negative values except outliers < -0.001 mol/m² | https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_NO2 |
| `..._SO2` | 2018-12-05 | `SO2_column_number_density`, `_amf`, slant, `SO2_column_number_density_15km`, `absorbing_aerosol_index` (340/380 nm), `cloud_fraction`, angles | snow_ice<0.5, AMF_polluted>0.1, VCD>-0.001, qa>0.5, cloud_fraction_crb<0.3, SZA<60; 15 km band only SZA<70; no detection limit stated | https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_SO2 |
| `..._CO` | 2018-06-28 | `CO_column_number_density`, `H2O_column_number_density`, `cloud_height`, angles | qa 50% | https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_CO |
| `..._AER_AI` | 2018-07-04 | `absorbing_aerosol_index` (354/388 nm UVAI, est. range -21..39), angles | qa 80% (`validity>50`); positive = UV-absorbing aerosol (smoke, dust, ash); can be computed under clouds | https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_AER_AI |
| `..._O3` | 2018-09-08 | `O3_column_number_density` (total column), `O3_effective_temperature`, `cloud_fraction`, angles | (total ozone; not a surface-AQ product) | https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_O3 |
| `..._HCHO` | 2018-12-05 | `tropospheric_HCHO_column_number_density`, `_amf`, slant, `cloud_fraction`, angles | qa 50% | https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_HCHO |

Availability end dates on the GEE pages read 2026-10-11 to 2026-10-18, i.e. the collections are current to within days.

Official product guidance (tropomi.eu): use `qa_value > 0.75` for NO2 "for optimal accuracy", 0.5 for cloud-covered scenes; the page gives no numeric accuracy but says precision estimates are in the files. https://www.tropomi.eu/data-products/nitrogen-dioxide

**Copernicus licence text** (extracted from the PDF at https://sentinels.copernicus.eu/documents/247904/690755/Sentinel_Data_Legal_Notice; the PDF downloaded, text inflated locally): "users shall have a free, full and open access to Copernicus Sentinel Data and Service Information without any express or implied warranty"; free access is granted for "(a) reproduction; (b) distribution; (c) communication to the public; (d) adaptation, modification and combination with other data and information; (e) any combination". Required notices: `'Copernicus Sentinel data [Year]'` when distributing unmodified data, and `'Contains modified Copernicus Sentinel data [Year]'` for adapted/modified data (Regulation (EU) 377/2014 and Delegated Regulation (EU) 1159/2013, Art. 7-8). The user also "renounces to any claims for damages". Commercial use is not excluded. (Beware: the ESA *website* terms page at https://sentinels.copernicus.eu/web/sentinel/terms-conditions is about site content, "non-commercial use", "no derivative works"; it does not govern the data. The Copernicus Data Space terms page https://dataspace.copernicus.eu/terms-and-conditions likewise defers to the Legal Notice.)

### 1.2 MODIS MAIAC AOD, `MODIS/061/MCD19A2_GRANULES`

1 km, daily, 2000-02-24 onward (GEE lists availability to 2026-10-16, summary text says 2025-10-12; inconsistent). Bands `Optical_Depth_047`, `Optical_Depth_055`, `AOD_Uncertainty`, `FineModeFraction`, `Column_WV`, `AOD_QA` bitmask (bits 0-2 cloud mask, 3-4 land/water/snow, 5-7 adjacency, 8-11 AOD QA level 0=best..5=no retrieval, 12 glint, 13-14 aerosol model 0 background/1 smoke/2 dust), `Injection_Height`, Angstrom exponent, angles. Terms: "MODIS data and products acquired through the LP DAAC have no restrictions on subsequent use, sale, or redistribution." DOI 10.5067/MODIS/MCD19A2.061. https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD19A2_GRANULES

### 1.3 VIIRS AOD

NASA Deep Blue `AERDB_L2_VIIRS_SNPP` is a Level-2 6-minute swath product, 6 x 6 km at nadir (growing off-nadir), SNPP record from 1 March 2012 (collection 1.1; v2.0 also listed), NOAA-20 from 17 Feb 2018; archived at LAADS. https://www.earthdata.nasa.gov/data/catalog/laads-aerdb-l2-viirs-snpp-2 and https://catalog.data.gov/dataset/viirs-snpp-deep-blue-aerosol-l2-6-min-swath-6-km-v2-0 . I found no GEE asset for VIIRS AOD **[U]**; it would need a LAADS/Earthdata-token pipeline (the project already holds an EDL token). NASA data policy: "full and open sharing of Earth science data", "no period of exclusive access", "non-discriminatory data access"; distribution charged at no more than the cost of dissemination. https://www.earthdata.nasa.gov/engage/open-data-services-software-policies/data-information-policy . Note the FIRMS FAQ warns "Delivery of new Suomi NPP data ceases on November 2, 2026" (section 3), which affects SNPP-based aerosol as well **[U]** (the notice is on the FIRMS page; I did not confirm it for AERDB).

### 1.4 CAMS

- **EAC4 global reanalysis** (ADS): 2003-2025, 0.75° x 0.75°, 3-hourly, variables include PM2.5, NO2, SO2, CO, total AOD at 469/550/670/865/1240 nm plus component AODs; licence "CC-BY"; updated "Twice a year with 4-6 month delay", last update 2026-08-24. https://ads.atmosphere.copernicus.eu/datasets/cams-global-reanalysis-eac4?tab=overview . Download needs an ADS account (not created; no probing).
- **`ECMWF/CAMS/NRT` on GEE**: from 2016-06-22, 44,528 m pixels, daily; bands PM1/PM2.5/PM10 (kg/m³), total and component AOD, total-column NO2/SO2/CO/HCHO/O3 etc.; before 2021-07-01 only AOD550 and PM2.5 exist; two 5-day forecasts per day, with `model_initialization_hour`/`model_forecast_hour` properties. Licence: "no restrictions on use, reproduction, or redistribution, for commercial or non-commercial purposes", attribution to CAMS required, modified products must be labelled as such. https://developers.google.com/earth-engine/datasets/catalog/ECMWF_CAMS_NRT

### 1.5 Satellite-derived PM2.5 (WUSTL ACAG, van Donkelaar group)

- **V6.GL.02.04** (recommended): 1998-2023, 0.01° and 0.1°, annual and monthly NetCDF, **CC BY 4.0**, cite Shen et al. 2024, ACS ES&T Air, doi 10.1021/acsestair.3c00054. V5.GL.05.02 (1998-2023, CC BY 4.0, van Donkelaar et al. 2021 ES&T doi 10.1021/acs.est.1c05309) also offered. The page states the estimates "explain most of the variance in ground-based PM2.5 measurements" but gives no R². https://sites.wustl.edu/acag/datasets/surface-pm2-5/ . The ACS abstract page returned 403, so the published R²/RMSE is **[U]**.
- A GEE community-catalog mirror exists ("global_pm25"): https://gee-community-catalog.org/projects/global_pm25/ (not fetched; version unverified **[U]**).
- The World Bank catalog redistributes a derived PM2.5 dataset: https://datacatalog.worldbank.org/search/dataset/0066908/air-pollution-sat-derived-pm-2-5-concentration (not fetched; licence **[U]**).

### 1.6 NASA GEOS-CF

`NASA/GEOS-CF/v1/rpl/htf` on GEE: 2018-01-01 to 2025-10-15 (metadata says 2026-01-02), 0.25° (27,750 m), hourly ("htf"), bands NO2/SO2/O3/CO mole fractions, `PM25_RH35_GCC` (µg/m³), `PM25_RH35_GOCART`, plus met. Terms: "NASA-produced data may generally be used for any purpose without prior permission". Caveats: global high bias in SO2 (2018-19 evaluation), v1 "overestimates aerosols by roughly 20-50%" (GEOS-Chem v12.0.1 bug), ML bias correction improves surface skill; **GEOS-CF v2 (January 2026) continues but does not back-process v1's period**. https://developers.google.com/earth-engine/datasets/catalog/NASA_GEOS-CF_v1_rpl_htf . Non-GEE access: NCCS portal, OPeNDAP, CFAPI for single points, S3 Zarr; `ana` (replay) vs `fcst` directories; v2 is latest. https://gmao.gsfc.nasa.gov/gmao-products/geos-cf/data-access_geos-cf

---

## 2. Ground stations

### 2.1 DENR-EMB network

- Count: "134 air quality monitoring stations nationwide as of October 2023", measuring PM10, PM2.5, CO, NOx, SOx; H1-2023 PM2.5 means Metro Manila 20 µg/Ncm (23 in H1-2022), national 18 (16). https://tribune.net.ph/2023/11/07/phls-air-quality-improved-in-2023-denr-emb . Annual PM2.5 guideline value is 25 µg/Ncm (same source). 2024: national PM2.5 16 µg/Ncm, Metro Manila 16.86 (EMB via PTV) https://ptvnews.ph/denr-notes-improvements-in-ph-air-quality/ **[U]** (snippet only).
- Metro Manila: a DENR-EMB advisory of 14 Sept 2026 listed 16 stations (Makati, Manila, Mandaluyong, Marikina-Parang, Muntinlupa-Bilibid, Muntinlupa-Filinvest, Parañaque-Don Bosco, Parañaque-PEATC, Pasay, Pateros, QC-Ateneo, QC-SMPH Commonwealth, San Juan, Taguig-TUP, Valenzuela, Las Piñas); the data was issued as a social-media advisory, no portal named. https://tribune.net.ph/2026/09/14/15-metro-manila-stations-record-good-pm25-aqi-amid-haze . A Sept 2025 Malaya piece reports 15 Metro Manila stations with only some online, and a Greenpeace figure that only 45% of Filipinos live within 25 km of a station https://malaya.com.ph/business/corporate/air-quality-monitoring-in-ph-needs-improvement **[U]** (page 403; snippet). A Dec 2024 SM Prime "Adopt-a-CAMS" station in QC feeds EMB-NCR's data acquisition system https://context.ph/2024/12/05/real-time-air-quality-monitoring-station-launched-in-quezon-city/ **[U]** (snippet).
- Public data: the live site is `air.emb.gov.ph` (credited by aqicn, https://aqicn.org/city/manila/ ). My probe returned **HTTP 403** from this network on 2026-10-21 (WebFetch and curl), so I could not inspect station lists, history or an API. A 2021 FOI request for "list of PM 2.5 monitoring locations, exact location, type of instrument used, monitoring method" was denied https://foi.gov.ph/requests/list-of-pm-25-monitoring-locations-exact-location-type-of-instrument-used-monitoring-method **[U]** (snippet). Open Knowledge's 2015 index already rated EMB data as not machine-readable or bulk-downloadable https://2015.index.okfn.org/place/philippines/emissions/ **[U]**.
- Report formats: the Clean Air Act requires a National Air Quality Status Report; the most recent NAQSR cited by Enviliance was published 2022 covering 2020 (national PM10 60 µg/Ncm in 2012 to 27 in 2020) https://enviliance.com/regions/southeast-asia/ph/ph-air/ph-air-quality-guideline **[U]**; I could not reach emb.gov.ph (403) to confirm 2021-2023 PDFs. Expect PDFs with annual/semestral station means, not time series.
- Practical reading: EMB numbers reach the public as PDF reports, Facebook advisories and third-party mirrors (aqicn, IQAir). Hourly history is not openly downloadable as far as I could verify. **This is the thinnest part of the project.**

### 2.2 OpenAQ

- API v3 requires a key: my unauthenticated probe of `https://api.openaq.org/v3/locations?iso=PH&limit=1` returned 401 "A valid API key must be provided in the X-API-Key header". Rate limits: 60 requests/min, 2,000/hour (free, per key). https://docs.openaq.org/using-the-api/rate-limits
- Bulk: public S3 archive `openaq-data-archive`, gzip CSV, Hive partitioning `records/csv.gz/locationid=…/year=…/month=…`. https://docs.openaq.org/aws/about
- Licensing is **per provider**, not a blanket CC BY 4.0: OpenAQ "asserts no intellectual property interest", ingests only openly-licensed data (CC0, CC BY 4.0 preferred), the Licenses resource lists "CC BY 4.0 DEED" with commercial use/modification/redistribution allowed and attribution required; OpenAQ asks for credit to both the original provider and OpenAQ. https://docs.openaq.org/resources/licenses , https://docs.openaq.org/docs/data-policy , https://docs.openaq.org/about/faq
- Philippines coverage: **not verified** **[U]**. No OpenAQ page listing PH providers surfaced; the only PH reference on openaq.org was a Quezon City map caption https://openaq.org/platform/ . A 2025 RSC paper by OpenAQ-affiliated authors describes a Clarity Node-S network in Manila collocated with the DENR-EMB reference station and says Manila "only had one continuous air quality monitoring station managed by DENR-EMB" https://pubs.rsc.org/en/content/articlehtml/2025/ea/d4ea00160e **[U]** (403 on fetch; snippet). Whether EMB feeds OpenAQ is unknown; aqicn clearly scrapes EMB.

### 2.3 Low-cost / community / commercial networks

- **Breathe Metro Manila** (Manila Observatory, Ateneo BUILD, ASMPH, Clarity Movement): Clarity Node-S sensors, started in 7 of 17 NCR LGUs; Quezon City uses "40 active monitoring sites" for class-suspension decisions; public map at breathemetromanila.org/map-and-monitoring/ (page last updated 2 Oct 2026). https://www.clarity.io/blog/breathe-metro-manila-pushes-for-metro-wide-air-quality-monitoring-using-real-time-data ; consortium description in https://liveablecities.ph/sites/default/files/Liveable%20Cities%20Philippines%20Co%2BLab%20Policy%20Paper%20-%20Let%27s%20Clear%20the%20Air%20Why%20Air%20Quality%20Matters.pdf **[U]** (snippet). Data licence/API: not stated **[U]**; Clarity is a commercial platform.
- **UP CARE** (Center for Air Research in Urban Environments, UP Diliman): low-cost PM2.5/PM10/CO2/VOC nodes, e-trike mobile system, Grafana app; July 2025 UP CIDS roundtable where DENR-EMB "expressed strong interest in integrating low-cost technologies" https://cids.up.edu.ph/?p=29392 , https://cids.up.edu.ph/wp-content/uploads/2026/07/PEP-2026_Proceedings_Making-the-Invisible-Visible-Democratizing-Air-Quality-Monitoring-Through-Low-Cost-Sensor-Technology.pdf **[U]** (snippets). Separate UPD-CS AirboxSense campus network https://science.upd.edu.ph/upd-cs-develops-automated-environmentally-sustainable-campus/ **[U]**. A 2026 ISPRS paper on siting 40 sensors near QC roads https://isprs-annals.copernicus.org/articles/X-5-W4-2025/315/2026/ **[U]**.
- **Manila Observatory** has measured New Year PM2.5 across Metro Manila sites since 2003 https://www.observatory.ph/tag/urban-air-quality/ **[U]**.
- **DOST-PCIEERD**: "461 locally developed air quality monitors to be deployed in Taal affected communities" https://pcieerd.dost.gov.ph/news/latest-news/461-locally-developed-air-quality-monitors-to-be-deployed-in-taal-affected-communities **[U]** (403; title only).
- **Health Care Without Harm** "Healthy Air Now" sensor assessment in PH https://asia.noharm.org/resources/new-report-healthy-air-now-summary-assessment-hcwh-sensors-philippines **[U]** (TLS failure).
- **PurpleAir**: data access is metered in points (third-party estimates ~100,000 points/$1, about $0.50/sensor/month at 15-min polling) https://psl.noaa.gov/repository/point/purpleair_index.html **[U]**; the licence page https://www.purpleair.com/license rendered only its title via WebFetch, so redistribution terms are **[U]**. PH sensor count unknown **[U]**.
- **Sensor.Community**: archive at https://archive.sensor.community/ (yearly folders 2015-2025, daily folders, `csv_per_month/`, `sensors_per_country_per_day.json`); no licence text on the index page; ODbL is my recollection, **[U]**. PH count: could be read from `sensors_per_country_per_day.json` (18 MB; not downloaded).
- **IQAir/AirVisual**: proprietary; Community API plan free at 5 calls/min, 500/day, 10,000/month, city-level AQI only https://www.iqair.com/commercial-air-quality-monitors/api **[U]** (snippet); IQAir lists Manila stations (e.g. DLSU) and says Metro Manila LGUs run 13 stations https://www.iqair.com/air-quality/philippines/ncr/manila **[U]**. Not redistributable; useful only as a comparison screenshot.
- **aqicn/WAQI**: mirrors EMB and Clarity stations (e.g. validation pages for Sta. Ana and Parañaque Clarity nodes https://aqicn.org/station/validation/@1411321/ ) **[U]**; WAQI terms restrict redistribution (general knowledge) **[U]**.

### 2.4 US Embassy Manila / AirNow DOS

AirNow's embassy map (EPA/DoS partnership) shows reference-grade PM2.5 monitors at embassies; daily history via the "Archive" tab (24-h PM2.5 averages, monitor ID only); "All current readings are preliminary, unvalidated, and subject to change"; no licence text on the page. https://gispub.epa.gov/airnowembassy/ . The AirNow embassy listing pages returned 404 on two URL variants, so **whether Manila is in the DOS programme is unverified [U]**; aqicn's "US Embassy" Manila station is attributed to EMB, not DoS https://aqicn.org/city/philippines/manila/us-embassy/ . US federal works are generally public domain **[U]** (general knowledge, not confirmed for this dataset).

---

## 3. Fires and sources

### 3.1 NASA FIRMS

- Area API: `/api/area/csv/[MAP_KEY]/[SOURCE]/[west,south,east,north]/[DAY_RANGE 1-5]/[YYYY-MM-DD]`; free MAP_KEY required; **5,000 transactions per 10 minutes** (multi-day requests count as several), increase on request; sources `MODIS_NRT/SP`, `VIIRS_SNPP_NRT/SP`, `VIIRS_NOAA20_NRT/SP`, `VIIRS_NOAA21_NRT/SP`, `LANDSAT_NRT` (US/Canada only). https://firms.modaps.eosdis.nasa.gov/api/area/
- Archives: MODIS Terra Nov 2000, Aqua Jul 2002, VIIRS SNPP 20 Jan 2012, NOAA-20 1 Jan 2020, NOAA-21 17 Jan 2024; NRT latency <3 h; "Delivery of new Suomi NPP data ceases on November 2, 2026". Citation: "NASA FIRMS" in captions, LANCE/ESDIS acknowledgement in papers; NASA "promotes full and open sharing". https://www.earthdata.nasa.gov/data/tools/firms/faq
- For a 7-year PH bbox pull: 2,670 days / 5 days per call = ~540 calls per source, trivial against the 5,000/10-min limit.

### 3.2 Crop and forest burning

- Biomass-burning chapter: fire frequency declined 1992-2018, strong seasonality, hotspots in agricultural areas; rice-straw high-emission provinces Isabela, Pangasinan, Tarlac, Nueva Ecija. https://www.apn-gcr.org/publication/swidden-agriculture-and-biomass-burning-in-the-philippines/ **[U]** (snippet).
- Crop-residue burning emissions 1990-2015 by province: Western Visayas (Negros sugarcane) top hotspot, Central Luzon next. https://js.cmu.edu.ph/CMUJS/article/download/46/49/188 **[U]**.
- PhilSA used FIRMS MODIS active fires with burned-area products for kaingin mapping in Palawan, noting fires are only detected at overpass. https://philsa.gov.ph/wp-content/uploads/2024/11/SPIE_129770I.pdf **[U]**.
- Tarlac sugarcane burn mapping with Landsat dNBR https://hazeportal.asean.org/?p=8555 **[U]**.
- Transboundary haze: early Sept 2026 Kalimantan smoke carried by the habagat reached Metro Manila; QC cancelled classes for children on 1 Sept; by 3 Sept seven NCR stations read "unhealthy" PM2.5; Davao reached USG. https://mb.com.ph/2026/09/01/haze-may-linger-through-sept-3-rain-could-improve-air-qualitydenr , https://mb.com.ph/2026/09/01/forest-fire-particles-from-indonesia-reaching-philippines-due-to-strong-habagat-says-pagasa , https://www.khaleejtimes.com/asia/indonesia-wildfire-haze-hits-philippines-triggers-class-suspensions-air-quality-warnings , https://www.sunstar.com.ph/davao/indonesia-fires-push-davao-air-quality-to-unhealthy-level **[U]** (snippets).

### 3.3 Taal SO2 and vog episodes (story timeline)

| Date | Event | Source |
|---|---|---|
| 12-13 Jan 2020 | Eruption; SO2/ash plume to ~15-20 km; TROPOMI and IASI retrievals in the literature | https://earthobservatory.sg/news/blog/update-on-the-eruption-of-taal-volcano , https://cimss.ssec.wisc.edu/satellite-blog/archives/35406 , https://mdpi-res.com/d_attachment/remotesensing/remotesensing-12-01026/article_deploy/remotesensing-12-01026.pdf **[U]** |
| 29-30 Jun 2021 | Record 14,326 t/d SO2; Phivolcs confirmed SO2 "spread to Metro Manila and adjoining areas, causing hazy skies" after first attributing the haze to man-made smog; plume over NCR, Calabarzon, Central Luzon | https://www.arabnews.com/node/1886376/world |
| 2022 | no specific episode verified **[U]** | |
| 5-7 Jun 2023 | 9,391 then 7,680 t/d; Agoncillo class suspensions | https://newsinfo.inquirer.net/1781794/classes-in-2-batangas-towns-suspended-due-to-taal-vog/amp **[U]** |
| 22 Sep 2023 | Metro Manila "smog": Manila Times blamed Taal, but Phivolcs/DENR said vog drifted WSW away from NCR and PM2.5 spikes (Parañaque "acutely unhealthy") were traffic plus inversion; LGUs suspended classes metro-wide | https://newsinfo.inquirer.net/?p=1835387 , https://alpha.pna.gov.ph/articles/1210372 , https://denr.gov.ph/wp-content/uploads/2023/09/DENR_News_Alerts_23_September_2023_Saturday_opt.pdf **[U]** |
| 19 Feb 2024 | 14,558 t/d (year high 18,638 t/d); ~10,000 t/d average since Jan 2024; no vog thanks to wind | https://tribune.net.ph/2024/02/19/taal-spews-over-14k-tonnes-of-sulfur-dioxide |
| 18-21 Aug 2024 | 5,128 t/d; class suspensions across Batangas, all of Cavite, parts of Laguna/Rizal | https://newsinfo.inquirer.net/?p=1974227 **[U]** |
| Sep-Oct 2024 | vog since first week of Sept; 4,213 t/d on one day; 8 Oct suspensions in Batangas, Rizal, Tagaytay | https://newsinfo.inquirer.net/1983464/vog-reappears-after-taal-volcano-emits-voluminous-sulfur-dioxide , https://newsinfo.inquirer.net/1991573/taal-vog-prompts-class-suspension-in-batangas **[U]** |
| 2025 | Phreatic/phreatomagmatic minor eruptions (Oct 20, Dec 4); SO2 318-466 t/d "weak"; bulletins report **no vog** | https://newsinfo.inquirer.net/2150484/phreatic-phreatomagmatic-eruptions-hit-taal-volcano **[U]** |
| Oct 2026 | fifth phreatic eruption of the month; 1,002 t/d; no vog; Alert Level 1 | https://newsinfo.inquirer.net/2327462/taal-volcano-logs-fifth-eruption-this-october-alert-level-1-stays/amp **[U]** |

The Phivolcs Taal bulletin page returned 404 at the URL I tried, so the depth of the public daily SO2-flux archive is **[U]**; daily figures are quoted in every bulletin and widely reprinted, so a scraped series is plausible. The 2020-2021 period (daily flux up to >14k t/d) versus 2025-2026 (hundreds of t/d) is a strong satellite-visible contrast for the SO2 collection, and the 22 Sep 2023 "smog vs vog" confusion is a ready-made honesty story: TROPOMI SO2 plus wind can show the plume went WSW.

### 3.4 Manila traffic NO2 and the 2020 lockdown

- CREA (3 Jun 2020): NO2 over Metro Manila "approximately 52% lower than 2019" for the ECQ (15 Mar-15 May 2020); PM2.5 fell to the lowest on record in the first 30 days; by 1 Jun NO2 in all seven cities examined was back at or above pre-lockdown levels; 2.5 M vehicles, mobile sources 65% of national emissions (EMB NAQSR). https://energyandcleanair.org/publication/special-reportmanaging-air-quality-beyond-covid-19/ . Mongabay reported the same work with TROPOMI as source and a 75% one-week NO2 jump in Pasig/Makati in May https://news.mongabay.com/2020/06/as-lockdown-ends-manilas-dirty-air-is-back-it-doesnt-have-to-stay/ **[U]**.
- UP Diliman (R. Ramos, Geodetic Engineering) mapped weekly TROPOMI L3 NO2 over Metro Manila through the first six ECQ weeks, confirmed with airtoday.ph ground stations at EDSA-Muñoz and the Lung Center; no percentages given. https://upd.edu.ph/?p=20864
- Cooper et al. 2022, Nature 601:380-387 (doi 10.1038/s41586-021-04229-0): TROPOMI columns converted to surface NO2 at ~1 km with GEOS-Chem profiles for 215 cities; mean -32 ± 2%; Manila listed among cities with decreased NO2 "despite similarly unfavourable meteorological conditions"; city value in Supplementary Table 1. https://pmc.ncbi.nlm.nih.gov/articles/PMC8770130/
- A FEU journal case study on NO2 and PM2.5 in NCR during ECQ https://journal.feu-nrmf.edu.ph/wp-content/uploads/2026/06/FEU-Journal-30-2_6-11.pdf **[U]**; ACRS 2022 paper https://acrs-aars.org/proceeding/ACRS2022/ACRS22_96.pdf **[U]**.

---

## 4. Scientific honesty

1. **Column is not concentration.** TROPOMI gives a tropospheric vertical column (mol/m²); surface NO2 depends on the boundary-layer depth and profile shape. Converting needs model profiles (Cooper et al. 2022, above) or regression with boundary-layer depth (Poland study) and omitting mixing "leads to underestimation" (Finland study). https://www2.mdpi.com/2073-4433/12/7/896 **[U]**, https://www.knmi.nl/kennis-en-datacentrum/publicatie/estimating-surface-level-nitrogen-dioxide-concentrations-from-sentinel-5p-tropomi-observations-in-finland **[U]**. Column uncertainty itself: tropospheric AMF error 20-50% in polluted scenes gives total tropospheric-column uncertainty of 30-60% (DLR product) https://amt.copernicus.org/articles/14/7297/2021/ **[U]**; the coarse 1° x 1° TM5 a-priori profile under-resolves hotspots, and a finer prior raises columns near sources by >30% https://amt.copernicus.org/articles/19/2437/2026/ **[U]**. Therefore a column map must never be labelled an AQI or compared to a µg/m³ guideline; it can show relative patterns, seasonal cycles and anomalies.
2. **Cloud gaps.** Over Manila, a Manila Observatory sky-camera study found ~80% cloud cover in the wet season (Jun-Oct) and ~62% in the dry season https://agu.confex.com/agu/fm14/webprogram/Paper15497.html **[U]**. For TROPOMI, the Iberian study shows availability of 30-45% in cloudy months and 70-80% in summer https://acp.copernicus.org/articles/23/3905/2023/ ; a 2026 paper reports `qa_value > 0.75` removes ~65% of daily pixels globally https://www.mdpi.com/2072-4292/18/14/2387 **[U]** (403; snippet); cloudy-scene sampling biases seasonal means by 11-22% https://acp.copernicus.org/articles/24/13047/2024/ **[U]**. **No published valid-day fraction for Manila was found.** My expectation: 15-35% of wet-season days and 40-60% of dry-season days have a qa>0.75 NO2 pixel over central Manila **[U, estimate]**; the project should compute and publish this coverage map as a first deliverable (counts per month per pixel are a cheap GEE reduction) and show "n valid days" next to every monthly mean.
3. **Satellite PM2.5 is a model product.** V6 fuses AOD (MODIS/MISR/SeaWiFS/VIIRS), GEOS-Chem and ground calibration; ground calibration in SE Asia is thin ("surface PM2.5 monitoring has been historically scant throughout Southeast Asia") https://acp.copernicus.org/articles/24/3699/2024/ **[U]**; GEOS-Chem under-predicts regional aerosol by 20-52% vs AOD; MODIS tends to overestimate AOD under high loading and humid, cloudy conditions in Malaysia https://jagst.utm.my/index.php/jagst/article/view/118 **[U]**; non-random cloud gaps bias means. GEOS-CF v1 over-estimates aerosol 20-50% (section 1.6). CAMS NRT is a forecast, not an observation.
4. **SO2.** The L3 filter (cloud<0.3, SZA<60) plus a column product that is sensitive to plume height (`_15km` band) means volcanic plumes are well seen but anthropogenic SO2 near Manila is near the noise floor; show Taal plumes, not city SO2 rankings.
5. **Safe claims** look like: "Tropospheric NO2 column over Metro Manila, monthly mean of N valid TROPOMI days (qa>0.75); columns are not surface concentrations"; "Satellite-derived PM2.5 estimate (V6.GL.02.04, CC BY 4.0), uncalibrated locally"; "Fire detections at overpass only; no detection under cloud"; never "AQI", never "unsafe to breathe", never health-outcome attribution. Where EMB station means exist (annual PDF values), plot them beside the satellite series as the only true ground reference and label the gap honestly.

---

## 5. Existing products and public-interest signals

- **CAMS charts** (https://atmosphere.copernicus.eu/charts/packages/cams/ rendered only a title via WebFetch; it is the official global forecast chart viewer **[U]**). CAMS is also the engine behind Windy's air-quality layers **[U]** (general knowledge; not fetched).
- **IQAir** city pages/map for Manila https://www.iqair.com/air-quality/philippines/ncr/manila and https://www.iqair.com/air-quality-map/philippines/ncr/manila **[U]**; **aqicn/WAQI** PH map https://aqicn.org/map/philippines/ **[U]**; both are AQI-first, present-tense, proprietary.
- **NASA Worldview** offers S5P NO2/SO2/AI layers **[U]** (not fetched).
- **Breathe Metro Manila** public map (section 2.3).
- **DENR-EMB** `air.emb.gov.ph` (403 from here) and Facebook advisories; a 2023 DENR alert describes a data centre and public screens in Ortigas https://denr.gov.ph/wp-content/uploads/2023/09/DENR_News_Alert_25_September_2023_Monday_opt.pdf **[U]**.
- **PhilSA**: no air-quality product found **[U]**; Phivolcs says it "routinely checks open satellite data information for volcanic SO2" https://www.arabnews.com/node/1886376/world .
- **Public interest**: Taal vog school closures 2023-2024 (section 3.3), the Sept 2023 Metro Manila smog scare, the Sept 2026 Kalimantan haze with QC class cancellations and DOH mask advice https://interaksyon.philstar.com/trends-spotlights/2026/09/02/318619/haze-alert-how-filipinos-stay-safe-poor-air-quality/ **[U]**, post-New-Year "unhealthy" readings https://newsinfo.inquirer.net/1882588/post-revelry-air-quality-unhealthy-in-metro-manila-areas-denr **[U]**, and Greenpeace/IQAir "dirty air" reports https://newsinfo.inquirer.net/1233395/filipinos-breathing-dirty-unsafe-air-report **[U]**. Interest is real and recurring, but it is event-driven and AQI-framed; nothing public shows a multi-year, nationwide, sensor-fused history with coverage honesty.

---

## 6. Licences and redistribution

| Source | Licence | Attribution | Redistribute processed outputs? | Archive raw privately? |
|---|---|---|---|---|
| Sentinel-5P (all) | Copernicus Legal Notice: free, full, open; reproduction, distribution, adaptation allowed | "Contains modified Copernicus Sentinel data [Year]" | Yes | Yes (GEE exports are "modified") |
| MODIS MCD19A2 | No restrictions (LP DAAC) | cite DOI 10.5067/MODIS/MCD19A2.061 | Yes | Yes |
| VIIRS AERDB | NASA open data policy | cite LAADS | Yes | Yes (needs EDL token) |
| CAMS EAC4 | CC-BY (ADS) | "Copernicus Atmosphere Monitoring Service" | Yes | ADS account needed to fetch |
| `ECMWF/CAMS/NRT` on GEE | no restrictions; attribution; label modifications | CAMS | Yes | Yes |
| WUSTL PM2.5 V6.GL.02.04 | CC BY 4.0 | Shen et al. 2024 | Yes | Yes |
| GEOS-CF | NASA, any purpose | GMAO | Yes | Yes |
| FIRMS | NASA open; cite "NASA FIRMS"/LANCE | yes | Yes | Yes (MAP_KEY, free) |
| DENR-EMB | unstated; government report PDFs; portal blocked from here | DENR-EMB | Values quoted from reports with citation: low risk **[U]**; scraping the portal: unclear **[U]** | PDFs yes |
| OpenAQ | per provider (CC0/CC BY 4.0 typical) | provider + OpenAQ | Yes if provider licence allows | S3 archive is public |
| Breathe Metro Manila / Clarity | unstated **[U]** | | Ask before use **[U]** | No |
| PurpleAir | points-metered; licence page unreadable **[U]** | | Unclear **[U]** | Costly |
| Sensor.Community | ODbL **[U]** | yes | ODbL share-alike **[U]** | Yes |
| IQAir, WAQI | proprietary | | No | No |
| Phivolcs bulletins | government text; SO2 t/d figures are facts | Phivolcs | Yes (facts, cited) **[U]** | Yes |

Fit with DATA-ARCHIVING.md: every satellite source is open and can be mirrored as raw exports into the private `<project>-archive` releases; EMB PDFs can be archived verbatim; the only sources that cannot be archived/republished are IQAir/WAQI (do not use) and possibly Clarity (ask). `sources.yaml` would carry GEE collection IDs, LAADS/ADS endpoints, FIRMS API, WUSTL NetCDF URLs, EMB PDF URLs, Phivolcs bulletin URLs.

---

## 7. Volumes and free-tier feasibility

- **GEE quota**: Community tier 150 EECU-hours/month (no extra requirements); Contributor 1,000 EECU-h (needs a billing account, not charged); Partner 100,000 (application, climate projects). Quotas cover batch + online; exhausted quota drops to restricted concurrency, not a hard stop; resets monthly; annual re-verification. https://developers.google.com/earth-engine/guides/noncommercial_tiers . Default 2 concurrent batch tasks, 3,000 queued. https://developers.google.com/earth-engine/guides/usage
- **TROPOMI reduction cost** (estimate **[U]**): PH land ~300,000 km² = ~240k 1.1-km pixels per band per day; 2,670 days (2018-07 to 2026-10) = ~640 M pixel-reads per pollutant for a `reduceRegions` (mean, count, p90) over 82 provinces or 1,634 cities/municipalities. From experience with country-scale daily zonal statistics at 1 km, this is on the order of 5-30 EECU-hours per pollutant, so all six collections fit inside one or two months of the 150 EECU-h Community allowance; monthly mosaic exports (100 months x 6 pollutants at 1 km) cost a further few EECU-hours. Incremental daily updates are negligible.
- **Table sizes**: per province per day: 82 x 2,670 = ~219k rows per pollutant (~1.3 M for six); per city/municipality: 1,634 x 2,670 = ~4.4 M rows per pollutant (~26 M for six). As Parquet with (date, area_id, mean, count, p90) that is roughly 10-60 MB per pollutant. Published on HF datasets (free public storage "best-effort", recommend <100k files, <10k files per folder, Parquet preferred) https://huggingface.co/docs/hub/en/storage-limits . For the site, serve one JSON per city (1,634 files x ~50-150 KB) or one Parquet per pollutant read with DuckDB-Wasm/hyparquet.
- **Raster mosaics**: PH bbox at 1 km is ~1,500 x 1,200 px (1.8 M px). A monthly 8-bit WebP/PNG is ~0.1-0.5 MB; a float32 COG ~2-3 MB compressed. 100 months x 6 pollutants = 600 files, ~0.3-2 GB total, every file far below the Cloudflare Pages 25 MiB limit and the 20,000-file cap (500 builds/month) https://developers.cloudflare.com/pages/platform/limits/ . Put COGs on HF and only web-ready PNG/WebP or PMTiles on Pages.
- **Fires**: VIIRS PH detections are tens of thousands per year **[U]**; a 7-year CSV is tens of MB.
- **EAC4**: 0.75° over PH is ~20 x 25 cells; 3-hourly 2003-2025 for a handful of variables is a few hundred MB raw, small once daily-averaged.
- Verdict: comfortably free-tier if the reductions are done in GEE and the raw archive goes to HF/GitHub Releases.

---

## 8. Technical showcase (beyond a night-lights poverty map and a typhoon replay)

1. **Raster time-series animation**: monthly NO2/AI/AOD mosaics scrubbed on a map (WebGL colour ramps, synchronous calendar scrubber), with the 2020 ECQ dip and the Kalimantan haze pulses visible.
2. **Coverage-aware calendar heatmaps**: per city, a day x year grid where cell colour is the column value and opacity is cloud validity (a visualised honesty metric, rarely seen in AQ dashboards).
3. **Multi-sensor fusion panel**: TROPOMI NO2 (column), MAIAC AOD, CAMS/EAC4 PM2.5, V6 PM2.5, GEOS-CF surface NO2, FIRMS counts on one time axis per city, with units kept distinct.
4. **Ground-vs-satellite validation**: EMB annual/semestral PM2.5 values (from NAQSR PDFs), Breathe Metro Manila/OpenAQ sensors where licences allow, scatter plots with R² and n, and a "what the satellite cannot see" explainer.
5. **Event stories**: Taal vog plume tracking (SO2 column + ERA5/CAMS winds) that reproduces the Phivolcs "drifted WSW, not toward Manila" argument of 22 Sep 2023; the 2021 June plume over all of Luzon.
6. **Engineering**: GEE batch pipeline with provenance, incremental daily append, Parquet on HF, DuckDB-Wasm in the browser, PMTiles rasters, Akari UI.

---

## 9. Risks

1. **Looks like IQAir/WAQI/Windy** unless the framing is explicitly historical, multi-sensor and coverage-honest; the pitch must be "seven years of what satellites can and cannot see", not "today's AQI".
2. **Ground truth is thin and gated**: EMB portal blocked/unknown terms, FOI denied, no bulk history; OpenAQ PH coverage unverified; Clarity data proprietary; the validation chapter may be limited to a few dozen annual numbers.
3. **Health-claim trap**: columns are not exposure; satellite PM2.5 is locally uncalibrated; any "unhealthy"/"deaths" language invites refutation. Mitigate with units, uncertainty bands, coverage counts, and a written claims policy.
4. **Data continuity**: SNPP deliveries end 2 Nov 2026; GEOS-CF v1 ended 2025-10 with v2 not back-filled; EAC4 lags 4-6 months; GEE L3 metadata inconsistencies (revisit, end dates).
5. **Interpretation**: SO2 near cities is noise; NO2 over small cities is a few pixels; monsoon cloud gaps bias wet-season means.

---

## Scored table

| Criterion (1-5) | Score | Justification |
|---|---|---|
| Data availability / licences | 4 | Satellites and models are open with clear attribution (Copernicus, NASA, CC BY, CC-BY); ground data is the weak link (EMB blocked, FOI denied, OpenAQ PH unverified). |
| Volume / free-tier feasibility | 5 | GEE reductions fit the 150 EECU-h Community tier; tables are tens of MB; 600 monthly mosaics stay far under Pages limits; HF hosts the raw archive. |
| Scientific honesty | 3 | Honest presentation is possible and even a differentiator (coverage maps, column-not-concentration), but every layer is a proxy or model and local validation data is scarce. |
| Public interest / portfolio appeal | 4 | Taal vog school closures, the 2023 smog scare, the 2026 Kalimantan haze, the 2020 lockdown: recurring, Philippine-specific, map-and-time-series friendly. |
| Technical showcase | 4 | Raster animation, calendar heatmaps, multi-sensor fusion, in-browser Parquet, provenance pipeline; validation panel is the one piece that may be thin. |
| Risk (5 = low) | 3 | Resemblance to AQI dashboards, thin ground truth and the health-claim trap are all manageable but real; SNPP end-of-life and GEOS-CF v1 cut-off need handling. |

**Top three risks**: (1) ground-station data cannot be obtained or redistributed, leaving validation anecdotal; (2) the product reads as yet another AQI map unless coverage and units are foregrounded; (3) over-claiming health or exposure from columns and modelled PM2.5.
