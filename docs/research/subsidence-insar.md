<!-- Research notes gathered 2026-10-21 for docs/CANDIDATES.md. Kept as evidence: every claim has its URL and access date; [U] marks unverified items. The comparison and the plan are in the parent folder. -->

# Research dossier: land subsidence and flooding in Philippine cities from Sentinel-1 InSAR

Research date: 2026-10-21. All URLs accessed 2026-10-21 unless stated. Claims that could not be verified from a fetched page are marked **[U]**.Scope asked for: Metro Manila first (CAMANAVA, Pampanga delta, Bulacan), then Cebu, Davao, Iloilo; joined with flood extent/hazard maps, groundwater extraction, sea-level rise, built-up growth and exposed population; free tiers only; honest uncertainty.

---

## 1. Ready-made InSAR products over the Philippines

### 1.1 COMET LiCSAR (the single most important finding)

**Coverage over Luzon is real and deep.** The LiCSAR public product tree is organised by Sentinel-1 relative orbit (track) number, 1–175, at `https://gws-access.jasmin.ac.uk/public/nceo_geohazards/LiCSAR_products/` (listing fetched 2026-10-21). I probed frame polygon files (`<frame>/metadata/<frame>-poly.txt`) and found these Philippine frames:

| Frame | Orbit | Lon/lat extent (from poly.txt) | What it covers | Epochs (SLC dates) | Interferograms |
|---|---|---|---|---|---|
| **032D_07536_111313** | descending 32 | 119.66–122.31 E, 13.32–15.97 N | **All of Metro Manila, CAMANAVA, Bulacan, Pampanga delta, Cavite, Laguna, Taal** | **374** (2014-10-19 to 2026-08-12) | ~2,400 (earliest 20141019_20141112; listing truncated, count is an extrapolation) |
| 032D_07333_131313 | descending 32 | 120.05–122.79 E, 15.32–17.97 N | Central/North Luzon (Tarlac, Pangasinan, Nueva Ecija) | not counted | not counted |
| 032D_07741_141414 | descending 32 | 119.24–121.97 E, 11.15–13.97 N | Mindoro, Marinduque, Batangas south | not counted | not counted |
| **142A_07606_131313** | ascending 142 | 119.78–122.51 E, 12.63–15.19 N | **Metro Manila, Cavite, Laguna, Batangas, south Bulacan** | **214** (2014-10-27 to 2026-08-02) | listing truncated; earliest visible 20190209 |
| 142A_07411_111313 | ascending 142 | 119.44–122.12 E, 14.64–17.18 N | Bulacan, Pampanga, north edge of Manila (southern boundary ~14.6 N) | 202 (2014-10-27 to 2026-05-27) | listing truncated |
| 142A_07215_001012 | ascending 142 | 119.82–121.74 E, 16.84–19.01 N | Ilocos/Cagayan | — | — |
| 032D_07142_071411 | descending 32 | 120.44–123.00 E, 17.32–20.06 N | North Luzon/Batanes | — | — |

Sources: frame listings `.../LiCSAR_products/32/` and `.../LiCSAR_products/142/`; poly files e.g. `https://gws-access.jasmin.ac.uk/public/nceo_geohazards/LiCSAR_products/32/032D_07536_111313/metadata/032D_07536_111313-poly.txt`; epochs listing `https://gws-access.jasmin.ac.uk/public/nceo_geohazards/LiCSAR_products/32/032D_07536_111313/epochs/` (374 entries); `.../142/142A_07606_131313/epochs/` (214); `.../142/142A_07411_111313/epochs/` (202). Independent confirmation that descending track 32 is the Manila track: the Tay et al. replication dataset names its Manila file `Manila_TD032.zip` (https://researchdata.ntu.edu.sg/dataset.xhtml?persistentId=doi:10.21979/N9/GPVX0F&q=Manila).

Note that track 69 (which I had guessed) is over Ecuador/Peru, and the 142A frames numbered 05897–06296 are over Fujian/Zhejiang, so the frame number is **not** a latitude code; only the poly files tell you where a frame is. Visayas/Mindanao coverage (Cebu 10.3 N, Iloilo 10.7 N, Davao 7.1 N) was **not** probed; 032D_07741 stops at 11.15 N, so other tracks would have to be found on the portal map **[U]**.

**Frame 032D_07536 metadata folder** (fetched `.../032D_07536_111313/metadata/`): `metadata.txt` (master 2017-03-01, heading −168.93°, incidence 33.95°, SRTM 30 m DEM), `geo.E/N/U.tif` (LOS unit vectors, 20 MB each), `geo.hgt.tif` (20 MB), `geo.landmask.tif`, `geo.meancoh.<N>.tif` mean-coherence maps for several temporal baselines (7 MB each), `network.png`, a `baselines` file, and a **`032D_07536_111313.geo.vlos_eur.tif` (16 MB)**, which looks like a frame-wide LOS velocity map (the suffix suggests a Eurasia-referenced velocity, but no README explains it) **[U]**.

**What is published per frame** (https://comet.nerc.ac.uk/comet-lics-portal-product-details/ and the CEDA record https://catalogue.ceda.ac.uk/uuid/52cda2e0e6c04272ae15ac836c1e8493/): per interferogram `geo.unw.tif` (unwrapped phase, SNAPHU, zeros = masked), `geo.diff_pha.tif` (wrapped), `geo.cc.tif` (coherence 0–255), PNG previews; per epoch multilooked intensity; multilooked 5×20 to ~100 m pixels at 0.001°, WGS-84; frames ~220×250 km. GACOS tropospheric maps and LiCSBAS time-series "modules" were announced for 2020 but the product page still says "will become available"; LiCSAlert is not mentioned on the portal pages I fetched **[U as a product]**. The portal's "Velocities" page only hosts a Turkey time-series app and links to Alpine-Himalayan/Tibet velocity datasets (https://comet.nerc.ac.uk/comet-lics-portal-velocities/; `.../LiCSAR_products/velocities/` contains only `ahb/`, `tibet/`, GNSS and fault GeoJSONs). So **no ready-made LiCSBAS velocity/time series for Manila is published; you would run LiCSBAS yourself on the Manila frames**.

**Sizes.** The CEDA record lists the whole archive at 13.57 million files / 124 TB. Per-interferogram file sizes could not be read because the interferogram subfolders returned 404 during my probe (the portal's October 2025 storage-migration notice says moved data are only visible under `LiCSAR_products.future`, and that path 404ed too; https://comet.nerc.ac.uk/comet-lics-portal/). Estimate from the metadata tifs: a float32 full-frame GeoTIFF is ~20 MB compressed, a byte coherence tif ~7 MB, so **~25–30 MB per interferogram for unw+cc, i.e. ~60–70 GB for ~2,400 interferograms on 032D_07536** **[U, estimate]**. LiCSBAS needs only the unw and cc files and can clip to a bounding box after download, but the download itself is full-frame.

**Licence.** Two statements coexist: the CEDA catalogue record says **Open Government Licence v3**, "Permitted Use: Any", open access (https://catalogue.ceda.ac.uk/uuid/52cda2e0e6c04272ae15ac836c1e8493/), while the portal says the products are "Derived Works of Copernicus data" under the Sentinel terms, with a required acknowledgement ("LiCSAR contains modified Copernicus Sentinel data [Year]... COMET... JASMIN") and four required citations (Lazecký et al. 2020 Remote Sensing; Morishita et al. 2020 for LiCSBAS; Yu et al. 2018 for GACOS) (https://comet.nerc.ac.uk/comet-lics-portal/). **Not CC BY 4.0**, but both OGL v3 and the Sentinel legal notice permit reproduction, redistribution and adaptation with attribution. The portal also says processing capacity is prioritised for COMET research; external frame requests go by email and are not guaranteed.

### 1.2 European Ground Motion Service: confirmed no PH coverage
EGMS covers 30 countries: EU-27 (minus none listed), Iceland, Norway, UK; "no non-European territory is listed" (https://land.copernicus.eu/en/faq/products/european-ground-motion-service/which-areas-and-regions-are-covered-by-the-data).

### 1.3 CopPhil Ground Motion Monitoring Service (EU Global Gateway + PhilSA), a potential national product
A page at https://copphil.philsa.gov.ph/ground-motion-monitoring-service/ (fetched 2026-10-21) describes an EGMS-style service for the Philippines: Sentinel-1 SBAS and PSI, "consistent coverage across most of the Philippines", three products (Basic LOS velocities asc/desc with per-point reliability relative to a local reference; Calibrated against GNSS; Ortho E-W/Up-Down). Implemented by ESA under EU Global Gateway, © CopPhil 2026; flyer dated May 2026. **Status, launch date, download access and licence are not stated** (the flyer PDF text is not extractable) **[U]**. This is the biggest strategic uncertainty: if CopPhil publishes open velocity points nationally, the project's "process it yourself" angle collapses into "visualise CopPhil's product", which is still a good showcase but a different one.

### 1.4 Global coastal-subsidence datasets
- **Tay et al. 2022, Nature Sustainability** ("Sea-level rise from land subsidence in major coastal cities", 48 cities, Sentinel-1 ~2014–2020, ARIA/ISCE/MintPy; https://doi.org/10.1038/s41893-022-00947-z; abstract via Semantic Scholar). Replication data on DR-NTU Dataverse, DOI 10.21979/N9/GPVX0F, **CC BY-NC 4.0**, 50 files / 821 MB, shapefiles per city, including **`Manila_TD032.zip` (2.3 MB)** (https://researchdata.ntu.edu.sg/dataset.xhtml?persistentId=doi:10.21979/N9/GPVX0F). Manila's rate is in the paper's city table; not read here **[U]**. NC licence means it can be shown and cited but a commercial reuse would be out; fine for a portfolio.
- **Wu, Wei & D'Hondt 2022, GRL** ("Subsidence in coastal cities throughout the world observed by InSAR", 99 cities, PS-InSAR 2015–2020, paper **CC BY 4.0**, https://doi.org/10.1029/2022GL098477); supplement on Zenodo https://zenodo.org/records/6300903 (Supplement.zip 91.9 MB, **CC BY 4.0**); whether Manila is included and in what format is not visible from the record **[U]**.
- **Sulapas et al. 2024, Int. J. Applied Earth Obs. & Geoinf. 133:104107** (UP RI NOAH Center; InSAR Dec 2014–Oct 2020; open access **CC BY-NC**; https://doi.org/10.1016/j.jag.2024.104107; SSRN preprint 10.2139/ssrn.4779261). Rates: Bulacan (Guiguinto, Balagtas, Bulakan) up to 109 mm/yr; Metro Davao 38 mm/yr (Panabo); Legazpi 29 mm/yr; Metro Cebu 11 mm/yr (Naga); Metro Iloilo 9 mm/yr (https://resilience.up.edu.ph/understanding-ground-subsidence-a-growing-threat-to-philippine-communities/; https://science.upd.edu.ph/up-geologists-report-subsidence-rates-in-select-ph-metropolitan-cities/). The sensor/software and any data release are not stated on the pages I could read (ScienceDirect blocked) **[U]**.

### 1.5 JAXA ALOS-2
PALSAR-2 ScanSAR L2.2 became free in Nov 2022 and L1.1/L2.2 (Aug 2014–Feb 2023) via G-Portal in Apr 2023; L1.1 goes to ASF, L2.2 to GEE/AWS; GEE entries are "non-commercial use, subject to G-Portal Terms of Service"; L1.1 ScanSAR files are ~30–60 GB each (search results: https://www.eorc.jaxa.jp/ALOS/en/dataset/alos_open_and_free_e.htm; https://forum.step.esa.int/t/alos-2-scansar-data-to-be-made-freely-available/19217; https://developers.google.cn/earth-engine/datasets/catalog/JAXA_ALOS_PALSAR-2_Level2_1_StripMap_202401). L-band ScanSAR InSAR of Manila is possible in principle (GMTSAR/ISCE support it) but file sizes and the NC terms make it a stretch goal at best **[U for a Manila-specific product]**.

### 1.6 ARIA/JPL GUNW on ASF
ARIA S1 GUNW: CF-compliant NetCDF, 90 m, unwrapped phase + geometry + correction layers, VV only, >1 million products "covering areas worldwide identified for natural hazard monitoring"; no explicit licence, but required credit "ARIA S1 GUNW, NASA [year]. Contains modified Copernicus Sentinel data" and citation of Buzzanga et al. 2020; Earthdata Login required to download (https://www.earthdata.nasa.gov/data/projects/aria). **Philippine coverage confirmed by probe:** the ASF search API returns **5,305** GUNW products intersecting Manila (120.98 E, 14.65 N) (`https://api.daac.asf.alaska.edu/services/search/param?dataset=ARIA%20S1%20GUNW&intersectsWith=POINT(120.98%2014.65)&output=count`). The same API counts **607 Sentinel-1 IW SLC scenes** intersecting Manila (all tracks). ASF data policy for GUNW is NASA open data; the Data.gov listings disagree on licence wording (search results: https://catalog.data.gov/dataset/aria-sentinel-1-geocoded-unwrapped-interferograms) **[U on exact licence]**.

---

## 2. On-demand processing on free tiers

### 2.1 ASF HyP3
- Free "HyP3 Basic" allotment: **8,000 credits/month per user**; InSAR full-scene (GAMMA) 10 credits at 80 m or 15 at 40 m; burst InSAR 1 credit for 1–4 pairs at 80 m; ARIA GUNW on demand 60 credits; RTC 5–60 (https://hyp3-docs.asf.alaska.edu/using/credits/). That is up to ~800 full-scene or ~533 40-m InSAR pairs a month on the free tier.
- Products: unwrapped phase, coherence, amplitude, water mask, optional LOS/vertical displacement, look vectors, DEM; no atmospheric correction; reference point defaults to the highest-coherence pixel; LOS only; "not recommended to draw conclusions from a single interferogram"; MintPy time-series tutorial linked (https://hyp3-docs.asf.alaska.edu/guides/insar_product_guide/). Products are kept **14 days** (GUNW on-demand is archived indefinitely) (https://hyp3-docs.asf.alaska.edu/products/).
- Risk: the 20 Oct 2025 HyP3+ announcement says the free tier depends on NASA funding and cites "growing uncertainty around federal funding" (https://hyp3-docs.asf.alaska.edu/news/hyp3_plus_introduction/). Licence of outputs is not stated on the product pages; attribution follows the Sentinel notice **[U]**.

### 2.2 Earth Engine: GRD only, no InSAR
`COPERNICUS/S1_GRD` contains "all of the GRD scenes" (HH/VV/VH/HV in dB plus incidence angle); no SLC or phase product exists in the catalog; terms are the Copernicus Sentinel terms (https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S1_GRD). Confirmed: **no InSAR on GEE**. GEE is still useful for flood mapping (GRD change detection), GHSL, WorldPop, GSW and the Global Flood Database.

### 2.3 Copernicus Data Space Ecosystem quotas
General users: 12 TB/30-day rolling transfer for immediately-available data, 4 concurrent connections, 20 MB/s per connection, then throttled to 1 MB/s; 0.1 TB/month for offline data; S3/OData/STAC 2,000 requests/min (https://documentation.dataspace.copernicus.eu/Quotas.html). IW SLC products are ~4 GB (single-pol) / ~8 GB (dual-pol) (https://www.esa.int/Our_Activities/Observing_the_Earth/Copernicus/Sentinel-1/Data_products). Quota is not the problem; compute and disk are.

### 2.4 Running LiCSBAS / MintPy / ISCE in GitHub Actions: numbers
- GitHub-hosted standard Linux runner for public repos: **4 vCPU, 16 GB RAM, 14 GB SSD**; job limit **6 h**; 2,000 min/month on Free for private repos (public repos are free); artifact storage 500 MB; cache 10 GB (https://docs.github.com/en/actions/reference/runners/github-hosted-runners; https://docs.github.com/en/actions/reference/limits).
- A full SLC stack for Manila: 374 epochs on 032D × ~4 GB ≈ **1.5 TB** of SLC (dual-pol would be ~3 TB); even the 607 scenes ASF counts over the point are >2.4 TB. That does not fit 14 GB of disk or a 6 h job, and ISCE/GAMMA coregistration of a 374-date stack needs tens of GB RAM. **Infeasible in Actions.**
- LiCSBAS on LiCSAR GeoTIFFs: the interferograms are already made; the download is ~60–70 GB per frame (estimate, §1.1) but can be chunked by date and clipped (LiCSBAS05op_clip) to a Manila box (~0.6°×0.6° ≈ 5% of the frame, so a few GB). Time-series inversion of ~2,400 clipped interferograms × ~360k pixels is feasible in 16 GB RAM in chunks; MintPy users report 63 GB RAM blowups only for very large areas (https://groups.google.com/g/mintpy/c/MYhYxp6YcBM). **Feasible with care**, probably as several 6-h jobs with intermediate state pushed to a HF dataset, or run once on a laptop and only the refresh in CI.
- HyP3 route: ~100–300 burst/full-scene pairs a month on the free credits → a MintPy SBAS network over Manila is feasible, but products expire after 14 days so the pipeline must fetch them promptly, and the free tier's future is uncertain.

**Realistic free-tier pipeline:** (1) download LiCSAR unw/cc for 032D_07536 and 142A_07606, clip to Greater Manila, run LiCSBAS (GPL-3, https://github.com/comet-licsar/licsbas) with GACOS correction and a chosen stable reference, produce LOS velocity + vstd + cumulative displacement; (2) optionally decompose asc/desc into vertical and E-W; (3) validate against published rates (Sulapas 2024, Espiritu 2022, Tay 2022, Wu 2022, Manila tide gauge); (4) archive raw inputs privately, publish derived rasters/points.

---

## 3. Flood data

- **Global Flood Database v1** (`GLOBAL_FLOOD_DB/MODIS_EVENTS/V1`): 913 events 2000-02-17 to 2018-12-10, MODIS 250 m, bands flooded/duration/clear_views/jrc_perm_water, filterable by `cc`/`countries`/`dfo_country`; **CC BY-NC 4.0**; Tellman et al. 2021 Nature doi:10.1038/s41586-021-03695-w (https://developers.google.com/earth-engine/datasets/catalog/GLOBAL_FLOOD_DB_MODIS_EVENTS_V1).
- **Sentinel-1 flood mapping on GEE**: GRD change detection is standard (UN-SPIDER recipe) and PhilSA now publishes AI-detected Sentinel-1 flood extents with shapefiles (e.g. Typhoon Inday, 10–11 July 2026, 64 maps, regions 9–13/BARMM), with the caveat that SAR underestimates urban/vegetated flooding and the site footer "All content is in the public domain unless otherwise stated" (https://philsa.gov.ph/news/satellite-data-show-flood-extents-in-mindanao-due-to-typhoon-inday/).
- **UNOSAT**: products for PH on HDX under **CC BY-SA** (e.g. TC20241028PHL Camarines Sur, 26–29 Oct 2024; Capiz Nov 2022 Sentinel-1) (search results: https://geo.btaa.org/catalog/297c8293-2de7-4413-ad76-ee9bdca5ca96; https://reliefweb.int/map/philippines/satellite-detected-waters-albay-and-camarines-sur-provinces-bicol-region-region-v-0).
- **Sentinel Asia** activations list flood proxy maps (EOS-RS, AIT, MBRSC) from Sentinel-1 as PNG/KMZ/SHP for 2025 PH storms, requester PhilSA; no terms stated (https://sentinel-asia.org/EO/2025/article20250925PH.html).
- **UP NOAH** (https://noah.up.edu.ph, UP Resilience Institute since 2017): flood (5/25/100-yr return periods), storm surge, landslide; downloadable **ESRI shapefiles under ODbL** according to the Space Climate Observatory description (https://www.spaceclimateobservatory.org/noah); the NOAH site itself is a JS app whose terms page I could not fetch **[U: confirm ODbL on noah.up.edu.ph]**.
- **HazardHunterPH / GeoRiskPH** (DOST-PHIVOLCS-led, with PAGASA, ASTI, MGB, NAMRIA, OCD, DepEd): generates "indicative" hazard reports; flood and rain-induced-landslide layers from DENR-MGB, storm surge from PAGASA. Terms of use **prohibit reproducing, republishing or redistributing site material**; no public API; vector files "may soon be available" via a Map and Feature Services Portal, otherwise request from agencies (https://hazardhunter.georisk.gov.ph/about-hazardhunterph; https://hazardhunter.georisk.gov.ph/terms-of-use; https://hazardhunter.georisk.gov.ph/faqs). **Not usable as a data source**; link to it instead.
- **JRC Global Surface Water** v1.4: 1984–2021, 30 m, occurrence/change/seasonality/recurrence/transition/max_extent; "free of charge, without restriction of use", cite Pekel et al. 2016 and "Source: EC JRC/Google" (https://developers.google.com/earth-engine/datasets/catalog/JRC_GSW1_4_GlobalSurfaceWater).
- **Copernicus EMS**: Philippine activations found: EMSR017 (Aug 2012 Manila/Pampanga floods, 16 maps), EMSR143 (Koppu 2015), EMSR310/312 (Mangkhut 2018), EMSR556 (Rai 2021), EMSR636 (Noru 2022) (https://emergency.copernicus.eu/EMSR017; https://emergency.copernicus.eu/mapping/list-of-components/EMSR143; https://data.jrc.ec.europa.eu/dataset/a54291d3-0ff9-4faf-900f-9d090969c0ca). EMSR848 (Oct–Nov 2025) was for Viet Nam. No 2024–2025 PH activation was confirmed; the activations site is now behind a JS app (https://mapping.emergency.copernicus.eu/activations/) **[U]**. CEMS vector products are free to reuse with attribution under the Copernicus terms **[U: licence page not fetched]**.

---

## 4. Context data

- **WorldPop** Philippines 100 m: **CC BY 4.0**, 92.77 m pixels, 2000–2020 on GEE (https://developers.google.com/earth-engine/datasets/catalog/WorldPop_GP_100m_pop; https://hub.worldpop.org/doi/10.5258/SOTON/WP00216). Layers derived from OSM/Microsoft footprints are ODbL (search result).
- **GHSL GHS-BUILT-S R2023A**: 1975–2030 at 5-yr epochs (post-2018 extrapolated), 100 m and 1 km, built_surface and built_surface_nres; "reuse is authorised, provided the source is acknowledged" (EC reuse notice; AWS registry says CC BY 4.0) (https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_BUILT_S; https://registry.opendata.aws/ghs-built-s/).
- **Groundwater extraction: mostly not public.** NWRB Resolution 001-0904 (2004) imposed a deep-well moratorium in Metro Manila; NWRB "no longer allow[s] construction of deep wells in Metro Manila" (PNA, 14 Mar 2019, https://ptvnews.ph/?p=110990). A UP CIDS policy brief puts Metro Manila groundwater use at ~800 MLD, down from 1,500–2,000 MLD in the 1980s (search snippet of https://cids.up.edu.ph/wp-content/uploads/2022/02/UP-CIDS-Policy-Brief-2019-17.pdf; PDF text not extractable) **[U]**. Well-permit records surface only through FOI requests (https://foi.gov.ph/agencies/denrnwrb/). MWSS does not publish extraction statistics **[U]**. Sulapas et al. say their next step is to "add groundwater extraction data", which confirms it is not currently a public layer (https://science.upd.edu.ph/up-geologists-report-subsidence-rates-in-select-ph-metropolitan-cities/).
- **Sea level, PSMSL station 145 "MANILA, S. HARBOR"**: record 1901–2024, 85% complete, datum TSO 1901 throughout, gauge moved ~1 km NNW in 2002, benchmarks changed (4a → 4B → BM 66), QC flag ("read the documentation"), authority NAMRIA; a 1987 letter attributed the trend increase to reclamation and river deposition "although subsidence not totally discarded" (https://psmsl.org/data/obtaining/stations/145.php). Manila is **absent from PSMSL's own trends table** (https://psmsl.org/products/trends/trends.txt: Ids jump 144 → 148), consistent with the flag. A NAMRIA GNSS2024 presentation lists Manila at 8.4/13.2/14.4 mm/yr over 1901–2023 (search snippet; PDF 404) **[U]**; a 2023 Philippine Engineering Journal paper reports Manila Bay rise "accelerating at 13.13 mm/yr" and PSInSAR subsidence of 8–12 mm/yr north of Manila (search snippet; https://journals.upd.edu.ph/index.php/pej/article/view/9137) **[U]**. PSMSL asks for citation of Holgate et al. 2013 and the dataset; no formal licence text was found on the obtaining/notes pages (https://psmsl.org/data/obtaining/; https://psmsl.org/data/obtaining/notes.php) **[U: licence]**. Rodolfo & Siringan's Port of Manila summary: ~2 mm/yr 1902–early 1960s, then much faster, attributed to groundwater withdrawal (search snippet, https://www.chikyu.ac.jp/USE/pdf3/pdf_manila_e.pdf) **[U]**.
- **DEM**: Copernicus GLO-30 (2024_1 on GEE) is free worldwide with a mandatory notice ("© DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS...", modified data: "produced using Copernicus WorldDEM-30...", plus a liability disclaimer) (https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_DEM_GLO30_2024_1). NAMRIA IfSAR 5 m DEM/DTM and Phil-LiDAR 1 m DTMs exist but are obtained by request (FOI logs show requests; DREAM reports are "for research and educational purposes with acknowledgment") and are **not openly downloadable** (https://foi.gov.ph/agencies/denrnamria/; https://dream.upd.edu.ph/about/phil-lidar-1/) **[U]**.
- **Boundaries**: OCHA COD-AB Philippines (levels 0–4; PSA/NAMRIA source; "indicative, not official"; last modified 2023-11-09, reviewed Apr 2024) on HDX (https://data.humdata.org/dataset/philippines-administrative-levels-0-to-3); the licence field could not be fetched (403) **[U; HDX CODs are usually CC BY-IGO]**.

---

## 5. Scientific literature on Manila subsidence

| Study | Data / method | Period | Headline rates | Uncertainty reported | Cause |
|---|---|---|---|---|---|
| Rodolfo & Siringan 2006, *Disasters* 30(1):118–139, "Global sea-level rise is recognised, but flooding from anthropogenic land subsidence is ignored around northern Manila Bay" | levelling, tide gauges, wells | to ~2003 | SLR 1–3 mm/yr vs groundwater-driven subsidence "several cm to >1 dm per year"; companion Siringan & Rodolfo 2003 (Science Diliman) attributes up to 97% of Pampanga-delta subsidence to human causes, natural compaction 0.09–0.37 cm/yr | qualitative | fishpond and municipal groundwater pumping |
| Eco, Lagmay & Bato, EGU 2012-1064 | PSInSAR (MAINSAR), 21 descending Envisat scenes | 2003–2006 | max 4.38 cm/yr LOS in CAMANAVA; consistent with levelling 1979–2009 (~1 m, 3.33 cm/yr) | none stated | NAMRIA: highest groundwater extraction areas |
| Raucoules et al. 2013, *RSE* 139:386–397 | DInSAR stacking, ERS + Envisat | 1993–2010 | local vertical motions "on the order of 15 cm/yr", uplift and subsidence, highly non-linear in space and time | implies GPS/DORIS cannot correct the tide gauge | groundwater, Marikina Valley Fault |
| Deguchi, ACRS 2014 | ALOS PALSAR and others | ~6 yr | max ~600 mm over 6 yr (~100 mm/yr) | none stated | groundwater |
| Espiritu et al. 2022, *Natural Hazards* ("Sentinel-1 InSAR reveals continued ground deformation in and around Metro Manila... associated with groundwater exploitation") | Sentinel-1 PS-InSAR | 2015–2019 | 1–2 cm/yr LOS in Manila, Caloocan, Malabon, Navotas, Valenzuela (except some coastal communities); >4 cm/yr in Bulacan, Cavite, Laguna; uplift 0.1–1 cm/yr in parts | not visible (paywalled) **[U]** | groundwater extraction and recharge |
| Sulapas et al. 2024, *JAG* 133:104107 (UP RI) | InSAR (sensor not stated on open pages) | Dec 2014–Oct 2020 | Bulacan 109 mm/yr; CAMANAVA fell from 35–40 to ~15 mm/yr; Las Piñas 17 → 6 mm/yr; Davao 38; Legazpi 29; Cebu 11; Iloilo 9 mm/yr | not visible **[U]** | groundwater, urbanisation, tectonics, compaction |
| Tay et al. 2022, *Nat. Sustain.* | ARIA/ISCE/MintPy SBAS, Sentinel-1 | ~2014–2020 | RLLS range −16.2 to +1.1 mm/yr across 48 cities; Manila value in city table **[U]** | per-city uncertainty in supplement **[U]** | groundwater (general) |
| UP Geodetic Eng. 2026 (Manila Bay Freeport Zone reclamation) | PS-InSAR, 119 Sentinel-1 scenes asc+desc, validated vs levelling (r 0.81–0.96) | 2018–2021 | mean −2.06 ± 2.84 mm/yr; local −17.5 mm/yr | ± given per zone | construction loading |
| Ibarra-Marinas et al. 2026, *Geographies* 6(2) | PSMSL + AR6 + VLM | to 2150 | cumulative VLM ~0.785 m by 2100, ~1.289 m by 2150; subsidence 55–75% of projected RSLR (secondary source) | scenario ranges | — |

Sources: https://research.fit.edu/... (Rodolfo & Siringan PDF 404; abstract via https://agris.fao.org/search/en/records/647248962c1d629bc979a5a3 search snippet) **[U on exact numbers]**; https://meetingorganizer.copernicus.org/EGU2012/EGU2012-1064.pdf (text extracted locally); https://bibbase.org/network/publication/raucoules-... (abstract); https://link.springer.com/10.1007/s11069-022-05509-2 (abstract snippet; title/authors via Semantic Scholar); https://www.blocktec.ph/blog/news-4/... (2 Sep 2026 compilation of rates, including Hagonoy/Calumpit up to 124.5 mm/yr 2015–2021 near pumping stations, source unnamed) **[U]**; https://www.gmanetwork.com/news/scitech/science/976193/up-study-ground-subsidence-manila-bay-areas/story (11 Feb 2026); https://www.mdpi.com/... (Geographies 2026 via search snippet) **[U]**.

Consistent story: CAMANAVA sank at 3–4.5 cm/yr in the 1980s–2000s and has slowed to ~1–2 cm/yr after the NWRB moratorium; the hotspot has moved north-west into Bulacan/Pampanga (Guiguinto–Bulakan–Hagonoy–Calumpit) at ~10 cm/yr or more, where fishponds and industry pump unregulated wells. Uncertainty is rarely reported in the Philippine literature; the 2026 reclamation study is the exception.

---

## 6. Public interest and existing products

- News: AFP/Inside Climate News 2022 "Sinking land and rising seas threaten Manila Bay's coastal communities" (Bulacan/Pampanga; 5,000 displaced; groundwater) (https://insideclimatenews.org/news/18112022/sinking-land-and-rising-seas-threaten-manila-bays-coastal-communities/); Inquirer 2019 "Sinking PH areas: slow onset disaster"; Esquire PH 2024 "Philippine Cities Are Sinking Faster Than We Realize"; AFP Sep 2025 "parts of Bulacan sinking almost 11 cm a year, the fastest in the Philippines" (Lagmay) (search snippets; https://climate.gov.ph/public/ckfinder/userfiles/files/News%20Roundup/08_29_2024.pdf) **[U for the paywalled/blocked ones]**; GMA Feb 2026 on Bay City reclamation; Manila Bulletin Dec 2024 "Sinking cities" on the UP study; the New Manila International Airport flooding controversy (Ramon Ang blaming subsidence, Sep 2026 via blocktec.ph) **[U]**.
- Existing dashboards: **none national and public.** UP RI publishes figures and a podcast, not a map service; PhilSA presented PSInSAR for Baguio, Greater Manila and dams at a Feb 2025 roundtable and a Metro Manila Subway PSInSAR study (Dec 2022–May 2025) (https://philsa.gov.ph/research/application-of-persistent-scatterer-interferometric-synthetic-aperture-radar-psinsar-in-detecting-ground-motion-due-to-the-phase-1-of-the-metro-manila-subway-project/); CopPhil GMS is the planned official product (§1.3). HazardHunterPH has no subsidence layer.
- Users: LGU planners in CAMANAVA/Bulacan/Pampanga, DPWH flood-control critics, journalists, UP RI/PhilSA researchers wanting an independent cross-check, insurers and property buyers, and the "is the airport causing the floods" debate.

---

## 7. Honesty: what InSAR can and cannot show

- **Relative, not absolute.** Every velocity is relative to a reference point/area the analyst chooses; HyP3 defaults to the highest-coherence pixel "which may sit in a deforming area" (https://hyp3-docs.asf.alaska.edu/guides/insar_product_guide/). The project must publish the reference location and say "relative to X".
- **Line of sight.** Sentinel-1 sees ~34° off nadir (032D incidence 33.95°, metadata.txt); vertical is only recoverable by assuming no horizontal motion or by combining ascending (142A) and descending (032D) frames, which both exist for Manila (§1.1).
- **Atmosphere.** Tropospheric delays reach 2–3 cm typically and up to ~10 cm in the tropics (search results; GACOS correction, Yu et al. 2018); single interferograms are not evidence; only multi-year time series are.
- **Decorrelation.** Fishponds, rice paddies and mangroves in the Pampanga delta decorrelate at C-band; the subsidence hotspots in Hagonoy/Calumpit are exactly where coverage is poorest, so point density and vstd must be shown, not hidden.
- **Unwrapping errors and nonlinearity.** Raucoules 2013 found "highly nonlinear" motion; a single linear rate over 2014–2026 can mislead; show time series and per-pixel vstd.
- **Tide gauge.** The Manila gauge moved in 2002 and is flagged; its "sea-level rise" is mostly subsidence; say so explicitly rather than quoting 13 mm/yr as climate signal.
- Safe claims: "LOS velocity relative to [ref] of X ± Y mm/yr over 2014–2026, from LiCSAR frame Z, N interferograms, coherence-masked"; "consistent/inconsistent with published rates (table)"; "flood-hazard zones (NOAH 100-yr) overlap areas subsiding faster than Z mm/yr". Unsafe: "Manila is sinking N cm/yr" without reference, LOS caveat and uncertainty; any causal attribution to a specific well, project or the airport.

---

## 8. Licences and redistribution

| Source | Licence | Redistribute processed outputs? | Archive raw privately? |
|---|---|---|---|
| LiCSAR products | OGL v3 (CEDA) + Copernicus Sentinel terms; acknowledgement + 4 citations | Yes, with "LiCSAR contains modified Copernicus Sentinel data [Year]" and COMET/JASMIN credit | Yes (GitHub Release snapshots fine; large) |
| Sentinel-1 SLC/GRD | Copernicus legal notice: free, full, open; reproduction, distribution, adaptation allowed; notice "Contains modified Copernicus Sentinel data [Year]" (https://sentinels.copernicus.eu/documents/247904/690755/Sentinel_Data_Legal_Notice, text extracted locally) | Yes | Yes |
| HyP3 outputs | not stated; Sentinel notice applies; 14-day retention | Yes (attribution) **[U]** | Must copy within 14 days |
| ARIA GUNW | NASA open data; credit line required | Yes **[U exact licence]** | Yes |
| Tay 2022 data | CC BY-NC 4.0 | Yes, non-commercial, attribution | Yes |
| Wu 2022 supplement | CC BY 4.0 | Yes | Yes |
| Sulapas 2024 | paper CC BY-NC; no data release found | Figures only, cite | n/a |
| Global Flood Database | CC BY-NC 4.0 | Yes, NC | via GEE export |
| JRC GSW | free, no restriction; cite | Yes | via GEE |
| GHSL | EC reuse notice / CC BY 4.0 | Yes | Yes |
| WorldPop | CC BY 4.0 | Yes | Yes |
| GLO-30 DEM | free worldwide; mandatory DLR/Airbus notice and disclaimer | Yes with notice | Yes |
| UP NOAH hazard maps | ODbL (secondary source) **[U]** | Yes, share-alike for derived databases | Yes |
| HazardHunterPH | all rights reserved; no redistribution | **No**; link only | No |
| UNOSAT maps | CC BY-SA | Yes, share-alike | Yes |
| PhilSA flood shapefiles | "public domain unless otherwise stated" (site footer) | Yes **[U per-product]** | Yes |
| PSMSL | citation requested; no licence text found | Yes **[U]** | Yes (tiny) |
| OCHA COD-AB | not fetched **[U]** | likely yes | Yes |
| NWRB/MWSS groundwater | not public | n/a | FOI copies, private only |

Fit with the archiving standard: raw LiCSAR/HyP3 copies (tens of GB) belong in the private `<project>-archive` releases or a private HF dataset, not GitHub; sources.yaml can register LiCSAR (JASMIN primary, CEDA mirror), ASF, GEE exports, NOAH, PSMSL, HDX, each with health checks; the ODbL/CC BY-SA/NC layers must be kept separable so the published derived dataset's licence is clear (publish the subsidence product under CC BY 4.0 with the Sentinel/LiCSAR notices; keep NC flood-database derivatives separate).

---

## 9. Volumes and free-tier feasibility (numbers)

- LiCSAR 032D_07536: 374 epochs, ~2,400 interferograms (extrapolated), ~25–30 MB each for unw+cc (estimate) → **~60–70 GB** full-frame download; Manila clip ~5% → **~3–4 GB** working set. 142A_07606: 214 epochs, similar per-ifg size, fewer pairs.
- SLC alternative: 374 × 4 GB ≈ 1.5 TB (single-pol) per track; impossible in Actions (14 GB disk, 6 h, 16 GB RAM).
- HyP3: 8,000 credits/month → up to 800 full-scene InSAR pairs or ~8,000 burst pairs; outputs expire in 14 days.
- Velocity map: Greater Manila box 0.6°×0.6° at 0.001° = **~360k pixels**; after coherence masking perhaps 100–200k valid points; as a PMTiles/MVT point layer with vel+vstd that is **a few MB**; as COG rasters per product (vel, vstd, mask, cum displacement for 374 dates = 374 × 360k × 4 B ≈ **540 MB** uncompressed) the cumulative stack must be chunked or down-sampled (e.g. Zarr on HF, or 50-date subsets).
- Cloudflare Pages: **25 MiB per file, 20,000 files** on Free (https://developers.cloudflare.com/pages/platform/limits) → tiles and per-city COGs must stay under 25 MiB; large stacks go to HF datasets (free public storage "best-effort", files <200 GB, <10k entries per folder; https://huggingface.co/docs/hub/storage-limits).
- GitHub Actions: 6 h job, 4 vCPU/16 GB/14 GB; a LiCSBAS run over the clipped stack fits if the download is pre-staged; a full refresh per month is realistic (LiCSAR adds ~2–3 epochs per month per frame).

---

## 10. Technical showcase (beyond night-lights and typhoon replay)

- Running a real geodetic time-series inversion (LiCSBAS SBAS, GACOS correction, loop-closure checks, reference selection, asc/desc decomposition) and reproducing it in CI with provenance.
- Serving **per-pixel uncertainty** (vel ± vstd) and time series on the map: click a point → 2014–2026 displacement curve with error band, compared against the published rates table.
- Raster time series on the web: cumulative displacement as a scrubber (COG/Zarr → WebGL), plus flood-event overlays (GFD, PhilSA/UNOSAT shapefiles) and NOAH hazard polygons.
- Exposure analytics: zonal stats of subsidence × WorldPop × GHSL built-up change 1975–2030 × NOAH 100-yr flood, per barangay (COD-AB level 4), with the "where the hotspot moved" story (CAMANAVA → Bulacan).
- Honest-science UI: reference-point selector, coherence mask toggle, "LOS vs vertical" explainer, and a validation panel (tide gauge, levelling where published).
- Multi-source archiving: LiCSAR + ASF + GEE + HDX + NOAH in one sources.yaml with fallbacks and health checks.

---

## Scored table (1–5; 5 = best / lowest risk)

| Criterion | Score | Justification |
|---|---|---|
| Data availability / licences | **4** | LiCSAR has 12 years of interferograms on both Manila tracks under OGL/Copernicus terms; ARIA GUNW has 5,305 products over Manila; context layers are CC BY; but no ready-made Manila velocity product, groundwater data is not public, HazardHunterPH is closed, NOAH licence needs confirming. |
| Volume / free-tier feasibility | **3** | SLC processing is out (1.5 TB); the LiCSAR+LiCSBAS route is ~60–70 GB download then a few GB working set, workable but needs staging outside a 6-h Actions job; HyP3 works but expires in 14 days and its free tier is funding-dependent. |
| Scientific honesty | **4** | The caveats are well understood and can be surfaced (reference, LOS, vstd, coherence); risk is in the Pampanga fishpond zone where C-band decorrelates exactly where subsidence is worst. |
| Public interest / portfolio appeal | **5** | "Bulacan sinking 11 cm/yr", NMIA flooding debate, reclamation, CAMANAVA; no public national subsidence map exists; CopPhil may change that. |
| Technical showcase | **5** | Geodetic time-series inversion + uncertainty maps + raster time series + exposure analytics, well beyond raster-overlay apps. |
| Risk (5 = low) | **3** | CopPhil GMS could release an official national product and reframe the project; LiCSAR storage migration broke interferogram paths during probing; HyP3 free tier uncertain; reputational risk if rates are over-claimed. |

**Top three risks**
1. **CopPhil Ground Motion Monitoring Service** launches an official, open, national Sentinel-1 velocity product (page live, flyer May 2026, status unknown): the "I processed it" story weakens; mitigation: design the app to ingest CopPhil points as a source and position the project as cross-validation and flood/exposure joining.
2. **Data-path fragility**: LiCSAR's October 2025 migration left interferogram folders 404 under both `LiCSAR_products` and `.future` during my probe; HyP3 products expire in 14 days and the free tier depends on NASA funding; both need the archiving standard's fallback snapshots from day one.
3. **Scientific over-reach**: the strongest subsidence is in decorrelating fishpond/paddy terrain and Philippine papers rarely publish uncertainties; without vstd, reference disclosure and asc/desc decomposition, headline numbers will not survive scrutiny by UP RI or PhilSA.
