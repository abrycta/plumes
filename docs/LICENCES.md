# Licence verification ledger

Status: 2026-10-21. One row group per source on the approved sources canvas (the core record plus nine passes, 77 rows), in canvas order. Every verdict was checked on the publisher's own terms page on 2026-10-21 unless the row says **not fetched**, in which case the page to check by hand is named. Quotes are verbatim from the fetched page; nothing in quotation marks is paraphrased. **[U]** marks an estimate or a claim read from a search snippet rather than the page itself.

**Scope (2026-10-21, DECISIONS.md Q30, Q31):** only 24 sources (25 at M1.1) are in use; see "Scope after Q30 and Q31" below. Entries for the other sources are kept, marked out of scope in the summary table.

The registry ([sources-draft.yaml](sources-draft.yaml)) carries the short form of each verdict in its `licence` field and the attribution text in `attribution`; this file holds the evidence. The product posture that applies to every source: Plumes is a non-commercial portfolio site that shows **derived per-volcano summaries and dated, linked figures**; it redistributes no dataset (DECISIONS.md Q1, Q15). Raw copies live only in the private archive (archiving standard §6).

## Verdict scale

| Verdict | Meaning here |
|---|---|
| **open** | public domain, CC0, CC BY or an equivalent "free, full and open" notice; derived data may be shown and the processed summaries served, with the attribution |
| **open-with-conditions** | reuse allowed but with a condition that shapes the design: share-alike (kept as a separate layer), a mandatory notice, a per-dataset licence acceptance, a government work with the "no profit without approval" rule, or a scraping limit |
| **noncommercial-only** | usable on this site only because it is non-commercial; the About page states that, and the figures are never offered as a download |
| **link-only** | terms forbid republishing, or no terms are stated and the publisher's wishes are clear: the site links and may quote a short dated figure with its link, nothing more |
| **paid** | a fee or a signed agreement is needed; not used (workspace rule 3) |
| **unusable** | terms or access make it impossible for this project |

## Changes from the canvas

The canvas marked 45 rows "to verify" and the rest open, public domain or CC. After verification (details per row below, summary table at the end):

- **Paid or unusable (2):** WWLLN lightning ("available at nominal cost", sold); OpenSky's historical database (by application, university affiliation; its REST API cannot serve a retrospective and a live integration needs a written licence). Both are dropped.
- **Noncommercial-only or permission needed (4):** LaMEVE/VOGRIPA (personal non-commercial use only, written permission otherwise: dropped unless permission is obtained); Global Fishing Watch (CC BY-NC 4.0, tokens for organisations); IOC Sea Level (no commercial use; registration); DAHITI (CC BY-NC 3.0 badge; registration). The COMET portal images were already CC BY-NC and are linked only.
- **Link-only that the canvas did not mark so (4):** Darwin VAAC on bom.gov.au (no scraping, personal use only); PhilGEPS (copyright reserved, open-data portal down); Department of Agriculture bulletins (no hosted bulletins, press releases only); NDRRMC sitreps in practice (the site answers 403 to every script; PDFs are collected by hand or from mirrors whose terms are personal non-commercial).
- **Conditions that shape the design (6):** OpenStreetMap, Overture and the building footprints (ODbL: counts per ring are a produced work, the clipped tables stay private); NOAA ISD (WMO Resolution 40: Philippine station files are never put in a public release); ReliefWeb (gated API since 2025-11-01; report files are link-only); Raspberry Shake (logo and attribution line, no re-serving of waveforms); IASI (notify the PI); eVolv2k (use v3/v4, not v2 which is "for scientific use only").
- **Substance corrections (3):** the Philippine volcanoes north of 10°N are in **Tokyo VAAC's** area, not Darwin's, and JMA publishes an open text archive from 2010; Himawari L1b on NODD is **HSD binary, not NetCDF** (780 MB per 10-minute full disk; ash RGB is built from bands 11/13/15); EarthScope holds only two open stations in the Philippines (IU DAV, PS BAG), and the FDSN code `PH` is Hawaii.
- **Sites that block scripts (403) and need a hand download once (5):** psa.gov.ph and openstat.psa.gov.ph (census, PSGC), nhfr.doh.gov.ph, ndrrmc.gov.ph, ScienceBase (Slab2), si.edu (GVP terms page). Their files are downloaded by hand and adopted as private archive releases, as Lights did for the PSA file.
- **Everything else** is confirmed open or CC BY with the attribution lines recorded below; nothing in the plan costs money.

---

## Scope after Q30 and Q31 (2026-10-21)

Kurt accepted the 20 query-in-place sources and four NASA/Earth Engine additions ([DECISIONS.md](DECISIONS.md), Q30, Q31): **24 sources, 25 with Open Buildings Temporal at M1.1**. In scope: GVP (volcanoes, eruptions), PHIVOLCS WordPress and LAVA bulletins, USGS ComCat, Sentinel-5P SO2 and aerosol index (M2), FIRMS, MOD14A1, VNP14A1, Tokyo VAAC, DSWD DROMIC, WorldPop, OCHA COD-AB, Copernicus DEM, Sentinel-2, ERA5, GPM IMERG (M2), Black Marble on Earth Engine (M1.1), the Lights poverty estimates (M1.1), **OMI SO2 `OMSO2e`**, **MSVOLSO2L4**, **Landsat C2 L2** (with the thermal band), **Sentinel-1 GRD**, and **Google Open Buildings 2.5D Temporal** (M1.1). Every other entry below is **out of scope (Q30)**: its verdict and evidence stay as history, and the summary table's "M" column says "out (Q30)". HazardHunterPH stays a link, not a source.

### NASA OMI/Aura SO2 daily L3 (`OMSO2e`) (added by Q31)

- **Verdict:** open. The CMR record points to the EOSDIS data use and citation guidance (NASA open data, no restriction, citation requested) (NASA-EE-CANDIDATES.md A1). 2004-10-01 → now, 0.25° daily; GES DISC, cloud-hosted.
- **Access:** a Harmony request (services "Harmony OPeNDAP SubSetter (HOSS) Geographic", "OPeNDAP") per volcano box and date range; nothing bulk-downloaded. **Auth: Earthdata login** (bearer token; CI mints short-lived tokens from the login, as Lights does).
- **Attribution [U]:** the GES DISC dataset citation for OMSO2e v003 (doi:10.5067/Aura/OMI/DATA3008), to be copied from the GES DISC landing page when the entry is built.

### Google Open Buildings 2.5D Temporal (added by Q31, M1.1)

- **Verdict:** open: **CC BY 4.0** (the Earth Engine STAC `license` field for `GOOGLE/Research/open-buildings-temporal/v1`; NASA-EE-CANDIDATES.md A5). Annual 2016-06-30 → 2023-06-30, effective 4 m (building presence, fractional counts, heights), covering South-East Asia per the STAC description.
- **Access:** Earth Engine reductions per ring per year with the existing service account; nothing downloaded.
- **Attribution [U]:** "Google Open Buildings 2.5D Temporal Dataset, CC BY 4.0" plus "Processed in Google Earth Engine"; the paper citation from the STAC record when the entry is built.

### Now in scope: Landsat, Sentinel-1, MSVOLSO2L4

Landsat C2 L2 (with the TM and ETM+ collections from 2000 and the thermal band), Sentinel-1 GRD and MSVOLSO2L4 move to M1 under Q31. Their verdicts (open, below under Pass 2 and Pass 8) are unchanged; MSVOLSO2L4 brings back the Earthdata login.

---

## Core record

### Sentinel-5P TROPOMI SO2 (Copernicus, on Earth Engine)

- **Verdict:** open.
- **Quote:** "EU law grants free access to Copernicus Sentinel Data and Service Information for the purpose of the following use in so far as it is lawful: (a) reproduction; (b) distribution; (c) communication to the public; (d) adaptation, modification and combination with other data and information; (e) any combination of points (a) to (d)." — Sentinel Data Legal Notice, https://sentinels.copernicus.eu/documents/247904/690755/Sentinel_Data_Legal_Notice
- **Attribution:** "Contains modified Copernicus Sentinel data [Year]" (the notice's wording for derived products); "processed in Google Earth Engine" added as a courtesy. Earth Engine is free only for noncommercial use: "You are an individual developer using Earth Engine for noncommercial purposes." (https://earthengine.google.com/noncommercial/).
- **Access:** `COPERNICUS/S5P/OFFL/L3_SO2` (STAC https://earthengine-stac.storage.googleapis.com/catalog/COPERNICUS/COPERNICUS_S5P_OFFL_L3_SO2.json), 2018-12-05 → , 1,113 m, one image per orbit. Auth: the Earth Engine service account.

### NASA FIRMS (VIIRS, MODIS), and MOD14A1 / VNP14A1 on Earth Engine

- **Verdict:** open ("as is").
- **Quote:** "sign up for free MAP_KEY using your email." and "MAP_KEY limit is 5000 transactions / 10-minute interval." — https://firms.modaps.eosdis.nasa.gov/api/map_key/. LANCE disclaimer, to be reproduced: "The information presented through LANCE, GIBS, Worldview, and FIRMS are provided "as is" and users bear all responsibility and liability for their use of data" and "Due to the spatial resolution and other characteristics of these data, their use for tactical decision-making or informing about conditions at a local scale are not advised." — https://www.earthdata.nasa.gov/data/projects/lance/disclaimer. MOD14A1 (LP DAAC): "no restrictions on subsequent use, sale, or redistribution" (RESEARCH.md §4).
- **Attribution:** "We acknowledge the use of data and/or imagery from NASA's Fire Information for Resource Management System (FIRMS) (https://earthdata.nasa.gov/firms), part of NASA's Earth Science Data and Information System (ESDIS)", plus the product citations (MCD14DL/MCD14ML; VNP14IMGTDL; MOD14A1 doi:10.5067/MODIS/MOD14A1.061; VNP14A1).
- **Access:** Earth Engine `FIRMS`, `MODIS/061/MOD14A1`, `NASA/VIIRS/002/VNP14A1`; the area API `https://firms.modaps.eosdis.nasa.gov/api/area/csv/[MAP_KEY]/[SOURCE]/116,4,128,22/[1-5]/[DATE]` (free MAP_KEY, Kurt's action); the archive tool (Earthdata login or emailed code) for the standard-quality CSV with the `type` column (1 = active volcano). S-NPP deliveries end 2026-11-02; NOAA-20 continues.

### MIROVA Dataset v2.5

- **Verdict:** open (CC BY 4.0, read from the OSF API on 2026-10-21; RESEARCH.md §4). The MIROVA *website* terms are non-commercial and are not used.
- **Attribution:** "MIROVA Dataset v2.5, University of Turin (Coppola, D. et al.), https://osf.io/zm62w/, DOI 10.17605/OSF.IO/ZM62W; Coppola et al. 2020, Frontiers in Earth Science 7, doi:10.3389/feart.2019.00362".
- **Access:** https://osf.io/download/53zwm/ (98.6 MB CSV). No auth.

### USGS ComCat

- **Verdict:** open (US public domain).
- **Quote:** "USGS-authored or produced data and information are considered to be in the U.S. Public Domain." — https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits
- **Attribution:** "U.S. Geological Survey, ANSS Comprehensive Earthquake Catalog (ComCat)".
- **Access:** FDSN CSV, 20,000 events per query (two period files; RESEARCH.md §6). No auth.

### Smithsonian Global Volcanism Program

- **Verdict:** open-with-conditions (non-commercial use with citation). **Terms page not fetched**: https://www.si.edu/termsofuse and https://volcano.si.edu/gvp_termsofuse.cfm answered a Cloudflare challenge on 2026-10-21; check by hand. A search snippet of the SI terms reads "You may not use any Content with usage conditions for commercial purposes, unless you have first obtained permission from the Smithsonian museum or program responsible for the Content" and "You must cite the author and source of the Content as you would material from any printed work. You must also cite and link to, when possible, the SI Website as the source of the Content." **[U]**. The WFS GetCapabilities (fetched) declares `AccessConstraints: NONE`, `Fees: NONE`.
- **Attribution:** the GVP database citation with the current version string, e.g. "Global Volcanism Program, 2026. [Database] Volcanoes of the World (v. 5.4.0; 7 Aug 2026). Distributed by Smithsonian Institution, compiled by Venzke, E. https://doi.org/10.5479/si.GVP.VOTW5-2026.5.4" **[U version]**, linked to volcano.si.edu.
- **Design consequence:** the derived episode table is shown on the site with the citation and is not offered as a download (Q15 makes this moot). Photo fields carry individual photographer credits and are not reused.

### WorldPop, GHSL, ESA WorldCover, Copernicus DEM

- **Verdict:** open. WorldPop CC BY 4.0 ("WorldPop datasets are licensed under the Creative Commons Attribution 4.0 International License", https://hub.worldpop.org/project/categories?id=3); GHSL: European Commission JRC open data, reuse with acknowledgement; WorldCover CC BY 4.0 (doi:10.5281/zenodo.7254221); Copernicus DEM: free licence with the mandatory notice "© DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved".
- **Attribution:** as in [sources-draft.yaml](sources-draft.yaml). Auth: Earth Engine service account.

### PHIVOLCS public bulletins (and the LAVA bulletin pages, and the earthquake tables)

- **Verdict:** link-only in the canvas sense: every figure is shown with its date and bulletin link; no PHIVOLCS-derived bulk file is published; no registered LAVA download is used (DECISIONS.md Q5 = (ii), no email).
- **Quote:** RA 8293 §176.1: "No copyright shall subsist in any work of the Government of the Philippines. However, prior approval of the government agency or office wherein the work is created shall be necessary for exploitation of such work for profit" — https://lawphil.net/statutes/repacts/ra1997/ra_8293_1997.html. LAVA data policy (registered data, not used): "Redistribution or charging for access to DOST-PHIVOLCS data is prohibited." — https://wovodat.phivolcs.dost.gov.ph/user/policy (RESEARCH.md §1.3).
- **Attribution:** "DOST-PHIVOLCS, [Volcano] Volcano Bulletin, <date>" with the URL on every figure.

### HazardHunterPH / GeoRiskPH

- **Verdict:** link-only. Quote: "You must not: Republish material from https://hazardhunter.georisk.gov.ph/" — https://hazardhunter.georisk.gov.ph/terms-of-use (research/volcanoes.md).

---

## Pass 1: the plume and the sky

### Himawari-8/9 (NOAA Open Data Dissemination, AWS)

- **Verdict:** open; attribution requested; no endorsement. Nothing costs money (anonymous S3).
- **Quote:** "Himawari data is produced and managed by JMA. NOAA has rights to distribute this data freely and openly to the public. [...] NOAA and JMA request attribution for the use or dissemination of unaltered data. However, it is not permissible to state or imply endorsement by or affiliation with NOAA or JMA. If you modify these data, you may not state or imply that it is original, unaltered data." — https://registry.opendata.aws/noaa-himawari/. JMA: "The user must cite the source when using the Content." — https://www.jma.go.jp/jma/en/copyright.html (terms "compatible with the Creative Commons Attribution License 4.0").
- **Attribution:** "Himawari-8/9 AHI data: Japan Meteorological Agency (JMA), via NOAA Open Data Dissemination (NODD); processed imagery, not original JMA data".
- **Access and format (corrected):** `s3://noaa-himawari9/AHI-L1b-FLDK/YYYY/MM/DD/HHMM/HS_H09_YYYYMMDD_HHMM_Bnn_FLDK_Rxx_Sss10.DAT.bz2` (HTTPS `https://noaa-himawari9.s3.amazonaws.com/<key>`); Himawari-8 in `noaa-himawari8` (2015-07 → 2022-12, with gaps in the listing). **L1b is HSD binary (bzip2), not NetCDF**; NetCDF exists only in the L2 ISatSS tiles. No "Ash RGB" product is in the bucket: the ash RGB is built from bands B11, B13, B15. A 2.5-minute Target Area (`AHI-L1b-Target/`, 1,000 × 1,000 km, "normally centered on active volcanoes within the Tokyo VAAC domain") exists from 2022.
- **Size (read from the listing):** one full-disk scan, 16 bands = 780 MB; the three ash bands ≈ 72 MB per scan, ≈ 10 GB per day; a segment of a 2 km band ≈ 3 MB. Only event windows are fetched; only derived animations are kept (DATA-PLAN.md §9).

### Sentinel-5P aerosol index and layer height

- **Verdict:** open (same Sentinel notice as SO2).
- **Access:** `COPERNICUS/S5P/OFFL/L3_AER_AI` (2018-07-04 → ; band `absorbing_aerosol_index`) and `COPERNICUS/S5P/OFFL/L3_AER_LH` (2018-07-04 → ; `aerosol_height` m, `aerosol_pressure` Pa, `aerosol_optical_depth`), both 1,113 m; STAC https://earthengine-stac.storage.googleapis.com/catalog/COPERNICUS/COPERNICUS_S5P_OFFL_L3_AER_AI.json and …_AER_LH.json (both read). AER_LH retrievals are sparse (cloud-free elevated layers only).

### VAAC advisories: Tokyo VAAC (JMA), not Darwin

- **Finding:** the Philippines north of 10°N is in **Tokyo VAAC's** area (ICAO FASID Table MET 3B); Taal, Mayon, Kanlaon and Bulusan advisories are issued by JMA. Darwin covers Mindanao south of 10°N and backs Tokyo up.
- **Verdict (Tokyo/JMA archive):** open-with-conditions (JMA terms, CC BY 4.0-compatible; cite the source).
- **Quote:** "The user must cite the source when using the Content." with the example "Source: Japan Meteorological Agency website (URL of relevant page)" — https://www.jma.go.jp/jma/en/copyright.html.
- **Access:** yearly lists `https://ds.data.jma.go.jp/svd/vaac/data/Archives/<YYYY>_vaac_list.html` (2010 → ); text advisories `https://ds.data.jma.go.jp/svd/vaac/data/TextData/<YYYY>/<YYYYMMDD>_<volcano8>_<seq4>_Text.html` (Taal = 27307000; e.g. …/2020/20200112_27307000_0001_Text.html). 2020: 3,108 advisories, 45 for Taal (2020-01-12 → 2020-02-02). 1–3 kB each. No auth.
- **Verdict (Darwin on bom.gov.au):** link-only. Quote: "Unless we state otherwise, you can download, copy and use our content for personal use, or use within your organisation. You must not supply it to any other person or use it for any commercial purpose." and "we do not allow you to use automated or manual techniques to hack, scrape or otherwise extract material from our site." — http://www.bom.gov.au/other/copyright.shtml. The data.gov.au record "Volcanic Ash Advisory - past archived advisories" was **not fetched** (403); check by hand for a CC BY declaration.

### CALIPSO lidar (NASA ASDC, to 2023)

- **Verdict:** open (US Government work / CC0).
- **Quote:** "While there are no restrictions on the use of these data" and "data provided from a NASA-led mission are licensed as Creative Commons Zero (CC0)" — https://www.earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance. "By mutual agreement between NASA and CNES, CALIPSO concluded all science operations on August 1, 2023." — https://www.earthdata.nasa.gov/data/alerts-outages/calipso-final-data-products.
- **Attribution:** the product DOI, e.g. "NASA/LARC/SD/ASDC, CALIPSO Lidar Level 2 Aerosol Profile V4-51, doi:10.5067/CALIOP/CALIPSO/CAL_LID_L2_05kmAPro-Standard-V4-51".
- **Access:** CMR collection C3880521383-LARC_CLOUD; OPeNDAP subsetting at https://opendap.earthdata.nasa.gov/collections/C3880521383-LARC_CLOUD/granules/<granule>; HDF4 granules 135–153 MB per half-orbit (read from CMR). **Auth: NASA Earthdata login** (Keychain `earthdata-login`; the CI mints tokens).

### Copernicus CAMS reanalysis (EAC4)

- **Verdict:** open (CC BY 4.0 since 2025-07-02).
- **Quote:** the ADS catalogue JSON for `cams-global-reanalysis-eac4` lists licence `CC-BY-4.0` — https://ads.atmosphere.copernicus.eu/api/catalogue/v1/collections/cams-global-reanalysis-eac4; ECMWF: "on Wednesday 2nd July 2025" the licence in "the Climate Data Store (CDS), Atmosphere Data Store (ADS) and the CEMS Early Warning Data Store (EWDS)" "will be replaced with the Creative Commons Attribution License (CC-BY)" — https://forum.ecmwf.int/t/cc-by-licence-to-replace-licence-to-use-copernicus-products-on-02-july-2025/13464. "One must agree to the Terms of Use of a dataset before downloading any data out of it." — https://ads.atmosphere.copernicus.eu/how-to-api.
- **Attribution:** "Contains modified Copernicus Atmosphere Monitoring Service information [Year]; CAMS global reanalysis EAC4, ECMWF, doi:10.24381/d58bbf47".
- **Access:** `cdsapi` with a personal access token (**new free ECMWF account: Kurt's action if this source is built**); 0.75°, 3-hourly, 2003 → 2025-12; total column SO2 and AOD at 550 nm. Philippine box ≈ 2.5 MB per month for ten variables **[U]**.

### ERA5 winds (as in Replay)

- **Verdict:** open (CC BY 4.0 since 2025-07-02 on the CDS; UCAR terms CC BY 4.0 on the NCAR mirror; the Google ARCO-ERA5 copy under the Copernicus terms).
- **Quote:** CDS catalogue JSON for `reanalysis-era5-single-levels` lists licence `CC-BY-4.0` — https://cds.climate.copernicus.eu/api/catalogue/v1/collections/reanalysis-era5-single-levels; ARCO-ERA5 README: "Yes, you can use our ERA5 data according to the terms of the Copernicus license" — https://github.com/google-research/arco-era5.
- **Attribution:** "Contains modified Copernicus Climate Change Service information [Year]; Hersbach et al. 2020, doi:10.1002/qj.3803", plus NSF NCAR RDA ds633.0 when served by NCAR.
- **Access:** Replay's registry entries (`../../typhoon-replay/pipeline/sources.yaml`: `era5-an-sfc`) are single-level; the plume-height winds need the **pressure-level** Zarr `gs://gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3` (u/v at 250–500 hPa), read by HTTP range. No auth.

### NASA Worldview / GIBS imagery

- **Verdict:** open; acknowledgement requested.
- **Quote:** "We ask that users who make use of GIBS in their clients or when referencing it in written or oral presentations to add the following acknowledgment: We acknowledge the use of imagery provided by services from NASA's Global Imagery Browse Services (GIBS), part of NASA's Earth Science Data and Information System (ESDIS)." — https://nasa-gibs.github.io/gibs-api-docs/
- **Access:** snapshot API `https://wvs.earthdata.nasa.gov/api/v1/snapshot?REQUEST=GetSnapshot&TIME=YYYY-MM-DD&BBOX=S,W,N,E&CRS=EPSG:4326&LAYERS=MODIS_Terra_CorrectedReflectance_TrueColor,Coastlines_15m&FORMAT=image/jpeg&WIDTH=1024&HEIGHT=1024` (HEAD 200, no auth, `Access-Control-Allow-Origin: *`); a 1° box around Taal on 2020-01-12 = 77.5 kB JPEG (read from HEAD). WMTS/WMS also available.

---

## Pass 2: the ground

### Sentinel-1 InSAR (COMET LiCSAR)

- **Verdict:** open-with-conditions (derived works of Copernicus Sentinel data; acknowledgement required). Quote: products are "Derived Works of Copernicus data"; acknowledgement "LiCSAR contains modified Copernicus Sentinel data [year]" — https://comet.nerc.ac.uk/comet-lics-portal/ (research/volcanoes.md). The COMET Volcano Portal's *images* are CC BY-NC 4.0 and are linked, not embedded. The portal's LiCSBAS JSON files carry no licence of their own; **Kurt decided on 2026-10-22 (DECISIONS L1a) to treat the portal's CC BY-NC 4.0 notice as covering them, without emailing COMET.** Attribution for derived series and the velocity layer: "Deformation: COMET LiCSBAS (COMET Volcano Portal, https://comet.nerc.ac.uk/comet-volcano-portal/), processed by COMET; LiCSAR contains modified Copernicus Sentinel data [years]. Licence: CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/); changes made: reduced to a summit series and a mean velocity per frame." Plumes is non-commercial (as GVP already requires). Access as in [sources-draft.yaml](sources-draft.yaml) (`licsar-taal-032d`; milestone 2).

### COMET Volcano Portal LiCSBAS series (`comet-licsbas`, M2)

- **Verdict:** noncommercial-only: the portal's CC BY-NC 4.0 notice, treated as covering the LiCSBAS JSON (DECISIONS L1a); LiCSAR is a derived work of Copernicus Sentinel data. Plumes is non-commercial.
- **Used for:** the per-volcano LOS series `los_comet_<frame>` and the `deformation-velocity` layer, published versions and the contract fixture (Taal frame 032D_07536_111313, DECISIONS L11).
- **Attribution (in every layer entry, series note, provenance record and beside the fixture):** "COMET LiCSBAS (COMET Volcano Portal, https://comet.nerc.ac.uk/comet-volcano-portal/), processed by COMET, not by Plumes; LiCSAR contains modified Copernicus Sentinel data [years]. Changes made: reduced to a summit series and a mean velocity per frame. CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/)." Citations in the registry: Lazecký et al. 2020; Morishita et al. 2020; Yu et al. 2018 (GACOS).

### Sentinel-2 and Landsat (before/after strip, crater lake, NDVI)

- **Verdict:** open. Sentinel-2: the Sentinel legal notice (above); `COPERNICUS/S2_SR_HARMONIZED` (2017-03-28 → ; B4/B8 at 10 m). Landsat: "Landsat datasets are federally created data" "and therefore reside in the public domain and may be used, transferred, or reproduced without copyright restriction." — https://earthengine-stac.storage.googleapis.com/catalog/LANDSAT/LANDSAT_LC08_C02_T1_L2.json; "There are no restrictions on Landsat data downloaded from the USGS; it can be used or redistributed as desired." — https://www.usgs.gov/faqs/are-there-any-restrictions-use-or-redistribution-landsat-data.
- **Attribution:** "Contains modified Copernicus Sentinel data [Year]"; "Landsat image courtesy of the U.S. Geological Survey" (https://www.usgs.gov/centers/eros/data-citation).
- **Access:** `LANDSAT/LC08/C02/T1_L2` (2013-03-18 → ) and `LANDSAT/LC09/C02/T1_L2` (2021-10-31 → ); 30 m. Auth: the Earth Engine service account.

### Landsat thermal band (crater-lake temperature)

- **Verdict:** open (as above). Band `ST_B10` (surface temperature, K, scale 0.00341802, offset 149; masked on L2SR scenes), 16-day per satellite. The Taal main-crater lake is about 1.2 km across, so a few dozen 30 m pixels per scene; the lake disappeared in January 2020 and the series says so.

### Sentinel-1 SAR change detection

- **Verdict:** open (Sentinel notice). `COPERNICUS/S1_GRD` (2014-10-03 → ; VV/VH in dB at 10 m; STAC https://earthengine-stac.storage.googleapis.com/catalog/COPERNICUS/COPERNICUS_S1_GRD.json). Reduced in Earth Engine; nothing downloaded.

### Copernicus EMS rapid mapping

- **Verdict:** open. Quote: "users are granted free access to the data of CEMS On-Demand Mapping for the following purposes and within the limits allowed under applicable law: (a) reproduction; (b) distribution; (c) communication to the public; (d) adaptation, modification and combination with other data and information; (e) any combination of points (a) to (d)." — https://mapping.emergency.copernicus.eu/terms-and-conditions/.
- **Attribution (mandatory form):** "Copernicus Emergency Management Service (© activation_year European Union), [Activation ID] Name of the Area of Interest (AOI): Product Type", e.g. "Copernicus Emergency Management Service (© 2020 European Union), [EMSR418] Taal (AOI01): Delineation Map" — https://mapping.emergency.copernicus.eu/about/citation-guidelines/.
- **Access:** **EMSR418 "Taal Volcano eruption in Philippines"** (activated 2020-01-13; AOI01 Taal, AOI02 Laurel; reference, first-estimate, delineation and grading products as PDF maps and vector-package zips), https://mapping.emergency.copernicus.eu/activations/EMSR418. No other Philippine volcano activation was found (Mayon 2018, Kanlaon 2024–25 absent; confirm by hand in the activations list). 1–20 MB per vector package **[U]**. No auth.

### Raspberry Shake citizen seismographs

- **Verdict:** open-with-conditions (free for hobbyists and researchers; a logo and attribution line on the site; no re-serving of waveforms; not a Creative Commons licence).
- **Quote:** "Free for hobbyists, school teachers, researchers and geophysical institutes."; "It is strictly prohibited to redistribute Raspberry Shake waveform data obtained from" the FDSN service "via your own FDSN Web Service, data center or server."; you must "include the following logo and attribution message on your website." — https://raspberryshake.org/license/; "each request allows to download up to 24h of data." — https://manual.raspberryshake.org/fdsn.html.
- **Attribution:** "Data powered by Raspberry Shake, S.A., a citizen-science project." with the logo; DOI 10.7914/SN/AM for publications.
- **Access:** `https://data.raspberryshake.org/fdsnws/dataselect/1/query?net=AM&sta=<STA>&loc=00&cha=EHZ&starttime=…&endtime=…` (miniSEED, 2–4 MB per channel-day **[U]**; 5 requests/s, 200 MB then throttled). Stations currently open (station query read 2026-10-21): about 20 around Taal/Tagaytay (e.g. R0693, RF944, S7E86), one near Mayon (RF78E, since 2023-05-18), one near Kanlaon (R6A17, since 2026-08-21); lifetimes are short and uneven. No auth.

### EarthScope FDSN stations

- **Verdict:** open (CC BY 4.0 by default since 2025-06-12; network licences take precedence). Quote: "When no license has been declared by the owner, the facility distributes the data with a license of CC-BY-4.0." — https://registry.opendata.aws/earthscope-geophysical-data/; "all data originating from EarthScope operated facilities" are "licensed under the Creative Commons Attribution 4.0 International License" — https://www.unavco.org/data/policies_forms/data-policy/data-license.html.
- **Attribution:** "Data were accessed from the NSF NGF data archive operated by EarthScope Consortium (NSF award 2435260)." plus the network DOI (IU: 10.7914/SN/IU) — https://www.earthscope.org/how-to-cite/.
- **Access:** `https://service.earthscope.org/fdsnws/station/1/query?network=<NET>&level=channel&format=text` (service.iris.edu redirects). **Finding:** only two open stations in the Philippine box: `IU DAV` (Davao) and `PS BAG` (Baguio); `PS TGY` (Tagaytay) closed in 1998; network code `PH` is Hawaii, not the Philippines; PHIVOLCS stations are not in the archive. Regional context only.

### NASA GPM IMERG

- **Verdict:** open (CC0). Quote: "All NASA-produced data from the GPM mission is made freely available for the public to use." — https://earthengine-stac.storage.googleapis.com/catalog/NASA/NASA_GPM_L3_IMERG_V07.json.
- **Attribution:** "Huffman, G.J. et al. (2019), GPM IMERG Final Precipitation L3 Half Hourly 0.1 degree x 0.1 degree V07, GES DISC, doi:10.5067/GPM/IMERG/3B-HH/07" (daily: doi:10.5067/GPM/IMERGDF/DAY/07).
- **Access:** `NASA/GPM_L3/IMERG_V07` (half-hourly, 0.1°, 1998 → ) on Earth Engine; GES DISC daily files (12 MB global, Earthdata login) as the second link. Per-volcano daily series tens of kB.

---

## Pass 3: people and impact

### DSWD DROMIC reports

- **Verdict:** open (work of the Government of the Philippines, RA 8293 §176.1). No site terms: neither https://dromic.dswd.gov.ph/ nor https://www.dswd.gov.ph/ carries a terms or copyright statement (both fetched).
- **Attribution:** "DSWD DROMIC Report #N on the Taal Volcano Eruption as of <date>" with the post link.
- **Access:** event posts, e.g. https://dromic.dswd.gov.ph/taal-volcano-phreatic-eruption-13-jan-2020/ (70 reports, 2020-01-13 → 2020-09-07); year index https://dromic.dswd.gov.ph/category/situation-reports/<year>/ (2016 → ). Files are **.docx, not PDF** (Report #1 of Taal 2020 is .doc), about 2.4 MB each (Report #70 = 2,438,599 bytes, HEAD); two a day during an event. No auth; scripted GET works. Events in range: Mayon 2018, Taal 2020–2022, Kanlaon 2024–25.

### NDRRMC situation reports

- **Verdict:** open (government work) but **ndrrmc.gov.ph answers 403 to every scripted request**; the ReliefWeb mirror's terms allow personal non-commercial use only. Treat as a hand-collected source: PDFs fetched once by hand, archived privately, figures shown with the citation.
- **Quote (mirror):** "ReliefWeb grants permission to Users to visit the Space and to download and copy the information, documents and materials (collectively, "Materials") from the Space for the User's personal, non-commercial use, without any right to resell or redistribute them or to compile or create derivative works therefrom" — https://reliefweb.int/terms-conditions.
- **Attribution:** "NDRRMC Update: Situational Report No. N re Taal Volcano Eruption, <date>".
- **Access:** official PDFs under `https://ndrrmc.gov.ph/attachments/article/<id>/<file>.pdf` (pattern seen in a GDACS link, not verified); mirrors on ReliefWeb and the AHA Centre ADINet (Kanlaon 2024). 1–5 MB per PDF **[U]**.

### NOAA NCEI Significant Volcanic Eruptions (HazEL)

- **Verdict:** open (US federal work).
- **Quote:** "Access to this dataset is unrestricted." — https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ngdc.mgg.hazards:G10147; "Please cite this data/database as doi:10.7289/V5JW8BSH" — https://www.ncei.noaa.gov/products/natural-hazards/tsunamis-earthquakes-volcanoes/volcanoes.
- **Attribution:** "National Geophysical Data Center / World Data Service (NGDC/WDS): NCEI/WDS Global Significant Volcanic Eruptions Database. NOAA National Centers for Environmental Information. doi:10.7289/V5JW8BSH".
- **Access:** `https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/volcanoes?country=PHILIPPINES` (50 records; JSON; works without a key, but answers 403 to a non-browser User-Agent). Under 100 kB.

### Department of Agriculture damage bulletins (+ cropland NDVI)

- **Verdict:** open ("All content is in the public domain unless otherwise stated." — https://www.da.gov.ph/agri-damage-from-taal-eruption-reaches-php3b/), but in practice **link-only**: no bulletin PDFs are hosted; the Taal 2020 figures (₱3.06 billion, 15,790 ha) exist as press releases, and later figures sit inside NDRRMC sitreps. The NDVI half comes from Sentinel-2 (pass 2).

### OpenStreetMap

- **Verdict:** open-with-conditions (ODbL 1.0: attribution; share-alike for derivative databases only).
- **Quote:** "OpenStreetMap is open data, licensed under the Open Data Commons Open Database License (ODbL)"; "If you alter or build upon our data, you may distribute the result only under the same license."; "Provide credit to OpenStreetMap by displaying our attribution notice." — https://www.openstreetmap.org/copyright. ODbL 4.3: "Creating and Using a Produced Work does not require the notice in Section 4.2." — https://opendatacommons.org/licenses/odbl/1-0/. The OSMF Produced Work guideline was **not fetched** (503 all day); check https://osmfoundation.org/wiki/Licence/Community_Guidelines/Produced_Work_-_Guideline by hand.
- **Attribution:** "© OpenStreetMap contributors" linked to the copyright page.
- **Design consequence:** counts of schools, hospitals and roads shown per ring are a Produced Work (attribution only); the intermediate POI table per volcano is a derivative database and stays private (not in a public release). Access: Geofabrik `https://download.geofabrik.de/asia/philippines-latest.osm.pbf` (610,963,420 bytes on 2026-10-20, HEAD; daily rebuilds, no history) or Overpass for dated queries. No auth.

### Meta high-resolution population (HDX)

- **Verdict:** open-with-conditions (CC BY).
- **Quote:** HDX record `license_id: cc-by`, `license_title: Creative Commons Attribution International (CC BY)`; required citation: "Facebook Connectivity Lab and Center for International Earth Science Information Network - CIESIN - Columbia University. 2016. High Resolution Settlement Layer (HRSL). Source imagery for HRSL © 2016 DigitalGlobe. Accessed DAY MONTH YEAR." — https://data.humdata.org/api/3/action/package_show?id=philippines-high-resolution-population-density-maps-demographic-estimates.
- **Access:** 14 resources (`phl_general_2020_geotiff.zip` 56 MB, CSV 47 MB, plus six demographic groups); one 2020 snapshot, last modified 2022-12-16, ~30 m. No auth (HDX shows a JS challenge to bots; use the CKAN links).

### OpenAQ and MODIS AOD

- **OpenAQ verdict:** open-with-conditions; free API key; per-provider licences; **Philippine coverage for Taal 2020 unverified** (likely the US Embassy Manila PM2.5 feed and low-cost sensors; no EMB reference monitors found).
- **Quote:** "Attribution to OpenAQ as the source data is also required when using OpenAQ services for accessing the data."; "OpenAQ users must therefore review and comply with any terms published by data providers." — https://docs.openaq.org/about/terms. Rate limits "60 / minute", "2,000 / hour" — https://docs.openaq.org/using-the-api/rate-limits.
- **Access:** `https://api.openaq.org/v3/locations?iso=PH` (401 without a key; **free registration is Kurt's action if built**), `/v3/sensors/{id}/days`.
- **MODIS MAIAC AOD verdict:** open. Quote: "MODIS data and products acquired through the LP DAAC have no restrictions on subsequent use, sale, or redistribution." — https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD19A2_GRANULES. Access: `MODIS/061/MCD19A2_GRANULES` (1 km, daily, 2000-02-24 → ; bands `Optical_Depth_047`, `Optical_Depth_055`, `AOD_QA`). Attribution doi:10.5067/MODIS/MCD19A2.061.

### OpenSky Network

- **Verdict:** noncommercial-only, and **unusable for the historical database** (Trino access is "available to university-affiliated researchers, governmental organisations, and aviation authorities"; "Access is granted based on application review." — https://openskynetwork.github.io/opensky-api/trino.html). The REST API serves only the last hour of states and ≤ 2-day flight windows, so a Taal 2020 retrospective is impossible through it. A live integration needs a written licence: "(vi) The REST API is provided for non-profit research and educational use only. Use of the REST API in any operational capacity — including but not limited to integration into a live product, service, or automated system — requires a written license from OpenSky Network, regardless of the entity's non-profit status." — https://opensky-network.org/about/terms-of-use.
- **Design consequence:** dropped from the plan; the "flights rerouted" story point uses published figures (CAAP/MIAA statements, NDRRMC sitreps) with links, and OurAirports for the airport layer.

### Wikipedia page views and GDELT

- **Wikimedia verdict:** open (CC0). Quote: "All Analytics datasets are available under the Creative Commons CC0 dedication" — https://dumps.wikimedia.org/other/pageviews/readme.html. A descriptive User-Agent is mandatory ("Wikimedia sites require a HTTP User-Agent header for all requests." — https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy). Access: `https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{project}/{access}/{agent}/{article}/{granularity}/{start}/{end}` (per-article data from 2015-07-01; live test returned Taal_Volcano 361,962 views on 2020-01-12). Under 500 kB per article series.
- **GDELT verdict:** open. Quote: "all datasets released by the GDELT Project are available for unlimited and unrestricted use" "for any academic, commercial, or governmental use of any kind without fee."; "any use or redistribution of the data must include a citation to the GDELT Project and a link to this website" — https://www.gdeltproject.org/about.html. Access: 15-minute files `http://data.gdeltproject.org/gdeltv2/YYYYMMDDHHMMSS.export.CSV.zip` (about 80 kB each; GKG about 4.9 MB each, ≈ 470 MB per day zipped); the DOC API's timelines cover only the last three months, so retrospective curves come from the raw files. **Cost flag:** the BigQuery route is paid beyond the free 1 TB per month; not used.

### HazardHunterPH / GeoRiskPH

- Link-only (see the core record).

---

## Pass 4: deep earth and deep time

### Nevada Geodetic Laboratory GNSS

- **Verdict:** open (no licence stated; citation requested). Quote: "Henceforth please use the following for citation of our data products:" (Blewitt, Hammond and Kreemer 2018) and "Please also note that many stations have an original data citation that should also be referenced." — https://geodesy.unr.edu/.
- **Attribution:** "Blewitt, G., W. C. Hammond, and C. Kreemer (2018), Harnessing the GPS data explosion for interdisciplinary science, Eos, 99, doi:10.1029/2018EO104623", plus the station network (PAGeNet/NAMRIA for Philippine `P***` stations **[U]**).
- **Access:** `https://geodesy.unr.edu/gps_timeseries/IGS20/tenv3/IGS20/<STA>.tenv3` (also `/SU/<STA>.SU.tenv3` Sunda-fixed); station list https://geodesy.unr.edu/NGLStationPages/DataHoldings.txt. Stations: Taal **PTGY** (Tagaytay, 2008-10 → 2025-09, 625 solutions, 127,704 bytes), PIMO/PTAG (Manila, continuous); Mayon **PLEG** (2014–2020, 485), PLG2, PNAG; Kanlaon **PBGO** (13 solutions), PSIP, PILC, PDUM. Most PAGeNet stations are campaign-style (few solutions a year). About 200 bytes per daily solution. No auth.

### GEM Global Active Faults

- **Verdict:** open-with-conditions (CC BY-SA 4.0, share-alike: kept as its own credited layer; RESEARCH.md §6).

### USGS Slab2

- **Verdict:** open (US public domain). Quote: use constraints "none", access constraints "none" — https://data.usgs.gov/datacatalog/metadata/USGS.5aa40a33e4b0b1c392eaaef4.xml (Philippines Region item); licence http://www.usa.gov/publicdomain/label/1.0/ on the Manila Trench item.
- **Attribution:** "Hayes, G., 2018, Slab2 - A Comprehensive Subduction Zone Geometry Model, U.S. Geological Survey data release, https://doi.org/10.5066/F7PV6JNV".
- **Access:** ScienceBase https://www.sciencebase.gov/catalog/item/5aa1b00ee4b0b1c392e86467 (**blocked scripted fetches with a Cloudflare challenge; the file list was not read**, check by hand); NetCDF grids per region (depth, dip, strike, thickness, uncertainty; region codes likely `phi`, `man`, `cot`, `sul` **[U]**), a few MB each **[U]**. No auth.

### LaMEVE (VOGRIPA)

- **Verdict:** **noncommercial-only / permission needed** (changed from "to verify"). Quote: "All text, images and other content on this website is copyright of VOGRIPA unless explicitly stated otherwise."; "You may only download or copy it for personal, non-commercial use."; "You are required to seek written permission from VOGRIPA for any other use or purpose." — https://vogripa.org/view/controller.cfc?method=terms. No bulk export: "The database is searchable via a spatial tool and or a series of attributes, the results of which can be downloaded into a spreadsheet format." — https://vogripa.org/view/controller.cfc?method=lameve.
- **Design consequence:** not used without written permission; the same facts (magnitude of large Philippine eruptions) come from GVP (VEI) and NCEI. If a later milestone wants LaMEVE, Kurt writes to the webmaster named on the terms page (OPEN-QUESTIONS Q25).
- **Attribution if permitted:** "LaMEVE database (version #), VOGRIPA"; Crosweller et al. 2012, J. Appl. Volcanol. 1:4, doi:10.1186/2191-5040-1-4.

### GloSSAC stratospheric aerosol

- **Verdict:** open (NASA; `FreeAndOpenData: true`, access constraints "WORLD" — https://cmr.earthdata.nasa.gov/search/collections.umm_json?concept_id=C3880704181-LARC_CLOUD). Attribution: "NASA/LARC/SD/ASDC, GloSSAC V2.22, doi:10.5067/GLOSSAC-L3-V2.22; Kovilakam et al. 2020, ESSD 12, doi:10.5194/essd-12-2607-2020". Access: one NetCDF, `https://data.asdc.earthdata.nasa.gov/asdc-prod-protected/GloSSAC/GloSSAC_2.22/GloSSAC_V2.22.nc` (518.05 MB, from CMR; 1979–2023, monthly zonal means). **Auth: Earthdata login.** A V2.24 readme exists; check whether it supersedes V2.22.

### eVolv2k ice-core sulphate

- **Verdict:** open (CC BY 4.0 for v3 and v4). **Caveat:** the v2 WDCC entry says "For scientific use only."; v3/v4 are used. Quote: v4 license "Creative Commons Attribution 4.0 International"; "Version 4 of this database replaces the previous version eVolv2k_v3." — https://doi.pangaea.de/10.1594/PANGAEA.971968.
- **Attribution:** "Sigl, Michael; Toohey, Matthew (2024): Volcanic stratospheric sulfur injections from 500 BCE to 1900 CE, eVolv2k_version4, PANGAEA, doi:10.1594/PANGAEA.971968"; Toohey and Sigl 2017, ESSD 9, doi:10.5194/essd-9-809-2017.
- **Access:** `https://doi.pangaea.de/10.1594/PANGAEA.971968?format=textfile` (tab-delimited, 3,072 values, under 1 MB). No auth. Pre-1900 only (Parker 1641 and possibly Mayon 1814 **[U]**).

### NASA GISTEMP

- **Verdict:** open. Quote: "When referencing the GISTEMP v4 data provided here, please cite both this webpage" "and also our most recent scholarly publication about the data." — https://data.giss.nasa.gov/gistemp/.
- **Attribution:** "GISTEMP Team, 2026: GISS Surface Temperature Analysis (GISTEMP), version 4. NASA Goddard Institute for Space Studies. Dataset accessed <date>"; Lenssen et al. 2024, doi:10.1029/2023JD040179.
- **Access:** https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv (12,886 bytes, HEAD; monthly, 1880 → ). No auth.

---

## Pass 5: water and land

### DAHITI / Hydroweb altimetry

- **DAHITI verdict:** open-with-conditions, licence ambiguous (the badge is CC BY-NC 3.0, the text says "Attribution 3.0 Unported"); registration. Quote: "All products are available free of charge for the user community after a short registration process." — https://dahiti.dgfi.tum.de/en/; the terms page /en/terms-of-use/ returns 404 (**not fetched**; the registration form shows the terms). Taal Lake **is** a target (DAHITI-ID 41711, water level 2019-02-03 → 2025-10-21, **15 data points**), too sparse for more than a marker. Citation: Schwatke et al. 2015, HESS 19, doi:10.5194/hess-19-4345-2015. **Registration is Kurt's action if built.**
- **Hydroweb.next verdict:** open (ETALAB 2.0). Quote: "Hydroweb Datat are distributed with an ETALAB V2.0 license" — https://www.theia-land.fr/blog/product/water-levels-of-rivers-and-lakes-hydroweb/. Taal **not confirmed** in the 399 operational lakes; a Theia account is needed to download. Low priority.

### JRC Global Surface Water

- **Verdict:** open. Quote: "All data here is produced under the Copernicus Programme and is provided free of charge, without restriction of use." — https://earthengine-stac.storage.googleapis.com/catalog/JRC/JRC_GSW1_4_GlobalSurfaceWater.json. Attribution: "Pekel, J.-F., Cottam, A., Gorelick, N., Belward, A.S. (2016), Nature 540, 418-422, doi:10.1038/nature20584; Source: EC JRC/Google". Access: `JRC/GSW1_4/GlobalSurfaceWater` and `JRC/GSW1_4/MonthlyHistory` (30 m, 1984-03 → 2021-12; covers Taal 2020 but nothing after).

### Sentinel-3 OLCI

- **Verdict:** open (Sentinel notice). `COPERNICUS/S3/OLCI` is **Level-1B radiance only** (21 bands, 300 m, 2016-10-18 → ); chlorophyll and turbidity proxies would have to be derived in Earth Engine. Low priority.

### HydroSHEDS

- **Verdict:** open. v1: "The core products of HydroSHEDS v1 are freely available for scientific, educational and commercial use." — https://www.hydrosheds.org/products/hydrosheds; EE STAC: "HydroSHEDS data are free for non-commercial and commercial use." v2 is CC BY 4.0 but "The data is currently limited to the Americas." — https://www.hydrosheds.org/products/hydrosheds-v2, so **v1 is used**. Attribution: Lehner, Verdin, Jarvis 2008, Eos 89(10), doi:10.1029/2008eo100001. Access: `WWF/HydroSHEDS/03DIR`, `15ACC`, `WWF/HydroSHEDS/v1/Basins/hybas_12` on Earth Engine.

### Copernicus GloFAS

- **Verdict:** open-with-conditions (CEMS-FLOODS licence; account and licence acceptance). Quote: "users are granted free access to the data of CEMS EFAS & GloFAS" for "(a) reproduction; (b) distribution; (c) communication to the public; (d) adaptation, modification and combination with other data and information" — https://ewds.climate.copernicus.eu/licences/cems-floods. Attribution: "Contains modified Copernicus Emergency Management Service information [Year]"; doi:10.24381/cds.a4fdd6b9. Access: `cems-glofas-historical` on the Early Warning Data Store (0.05°, daily, 1979 → ; `cdsapi` ≥ 0.7.7 with a token; **account is Kurt's action if built**). A 60 km box-year ≈ 0.2–0.5 MB **[U]**.

### NASA SMAP

- **Verdict:** open. Quote: "This dataset is in the public domain and is available without restriction on use and distribution." — https://earthengine-stac.storage.googleapis.com/catalog/NASA/NASA_SMAP_SPL4SMGP_008.json. Attribution: "Reichle, R., De Lannoy, G., et al. (2025). SMAP L4 Global 3-hourly 9 km EASE-Grid Surface and Root Zone Soil Moisture Geophysical Data, Version 8, NSIDC DAAC, doi:10.5067/T5RUATAQREF8". Access: `NASA/SMAP/SPL4SMGP/008` (3-hourly, 9 km, 2015-03-31 → ; 007 deprecated).

### MODIS land surface temperature

- **Verdict:** open. Quote: "MODIS data and products acquired through the LP DAAC have no restrictions on subsequent use, sale, or redistribution." — https://earthengine-stac.storage.googleapis.com/catalog/MODIS/MODIS_061_MOD11A1.json. Attribution: "Wan, Z., Hook, S., Hulley, G. (2021). MOD11A1 / MYD11A1 V061, NASA EOSDIS LP DAAC, doi:10.5067/MODIS/MOD11A1.061, doi:10.5067/MODIS/MYD11A1.061". Access: `MODIS/061/MOD11A1` (2000-02-24 → ), `MODIS/061/MYD11A1` (2002-07-04 → ); bands `LST_Day_1km`, `LST_Night_1km`, `QC_*`; 1 km daily.

### Hansen Global Forest Change

- **Verdict:** open (CC BY 4.0; license field `CC-BY-4.0` in https://earthengine-stac.storage.googleapis.com/catalog/UMD/UMD_hansen_global_forest_change_2025_v1_13.json). Attribution: "Hansen, M. C. et al. 2013. High-Resolution Global Maps of 21st-Century Forest Cover Change. Science 342, 850-53, doi:10.1126/science.1244693". Access: `UMD/hansen/global_forest_change_2025_v1_13` (2000–2025; bands `treecover2000`, `loss`, `lossyear`, `gain` (2000–2012 only), `datamask`; 30 m).

---

## Pass 6: society, response and links to the other projects

### NASA Black Marble night lights (as in Lights)

- **Verdict:** open ("NASA open data; no restrictions"); the same LAADS path and Earthdata token Lights uses (`../../lgu-lights/pipeline/sources.yaml`, `black-marble-vnp46a4`; the daily VNP46A2 is the product for power cuts).

### Lights poverty estimates

- **Verdict:** own data (Lights' published table, CC BY 4.0 with its attribution block, `../../lgu-lights/docs/DATA-PLAN.md` §5). Read from the Lights data version by LGU PSGC; no new upstream.

### PSA census by barangay (2020 CPH)

- **Verdict:** open-with-conditions (CC BY per the OpenSTAT terms) but **psa.gov.ph and openstat.psa.gov.ph answer 403 to scripts**; the terms page was **not fetched** (search snippet: "The statistical tables (or datasets) including documents (collectively as material) on this site are classified under Open Data with Creative Commons Attribution License (cc-by)." **[U]**; check https://openstat.psa.gov.ph/Terms by hand; Lights records the same posture). Access: per-region barangay workbooks (`https://psa.gov.ph/system/files/phcd/Region%20IV-A.xlsx` pattern **[U]**), downloaded once by hand and adopted as an archive release (Lights' PSA pattern). 1–3 MB per region **[U]**.

### Overture Maps, Google and Microsoft Open Buildings

- **Overture verdict:** open-with-conditions. Quote: buildings "© OpenStreetMap contributors. Available under the Open Database License."; places "Data from [Provider]. Available under CDLA Permissive 2.0." — https://docs.overturemaps.org/attribution/. Access: `s3://overturemaps-us-west-2/release/<RELEASE>/theme=buildings/type=building/*.parquet` (GeoParquet, monthly releases, no history before 2023); Philippine bbox 2–4 GB **[U]**; a 30 km ring 50–200 MB **[U]**. No auth.
- **Google Open Buildings verdict:** open-with-conditions. Quote: "The data is shared under the Creative Commons Attribution (CC BY-4.0) license and the Open Data Commons Open Database License (ODbL) v1.0 license." — https://sites.research.google/open-buildings/. Access: `GOOGLE/Research/open-buildings/v3/polygons` on Earth Engine (one May 2023 snapshot; Philippines covered). Attribution: Sirko et al. 2021, arXiv:2107.12283.
- **Microsoft verdict:** open-with-conditions; the global set is **CDLA Permissive 2.0** ("This data is licensed by Microsoft under the CDLA Permissive 2.0." — https://github.com/microsoft/GlobalMLBuildingFootprints), the Philippines legacy file ODbL (https://github.com/microsoft/IdMyPhBuildingFootprints). Philippines legacy file 1,189,283,353 bytes (HEAD).
- **Design consequence:** building counts per ring are a produced work; the clipped tables stay private.

### DOH health facility registry

- **Verdict:** open (government work) but **nhfr.doh.gov.ph answers 403 to scripts** and its terms were **not fetched**; check https://nhfr.doh.gov.ph/ by hand. Access: the facility list page with Excel/CSV export (per FOI responses **[U]**); current master list only; a few MB **[U]**. Hand download, archived privately.

### OCHA Financial Tracking Service

- **Verdict:** open (public API, no credentials; no licence text in the docs). Quote: "we decided to make the public API openly accessible as of December 2017. This means that users will be able to request and view data in general without any special credentials." — https://api.hpc.tools/docs/v1/. Access: `https://api.hpc.tools/v1/public/fts/flow?countryISO3=PHL&year=2020` (JSON). Attribution "Source: OCHA Financial Tracking Service (fts.unocha.org), accessed <date>".

### ReliefWeb API and GLIDE numbers

- **ReliefWeb verdict:** open-with-conditions and **gated since 2025-11-01** ("From 1 November 2025, you need to use a pre-approved appname."; "The maximum number of calls allowed per day is 1000." — https://apidoc.reliefweb.int/); report files are link-only under the terms quoted above. Metadata (title, date, source, link) is shown; files are not re-served. Requesting an appname is Kurt's action if built.
- **GLIDE verdict:** open (no terms on the site). Access: `https://www.glidenumber.net/glide/jsonglideset.jsp?level1=PHL&events=VO` (23 records, 17,896 bytes, no auth), e.g. VO-2020-000002-PHL (Taal), VO-2024-000222-PHL (Kanlaon). Attribution "GLIDE number <id> (ADRC, glidenumber.net)".

### OurAirports

- **Verdict:** open (public domain). Quote: "This is free and unencumbered software released into the public domain." — https://raw.githubusercontent.com/davidmegginson/ourairports-data/main/LICENSE. Access: https://davidmegginson.github.io/ourairports-data/airports.csv (12,748,669 bytes, HEAD), daily. No auth.

---

## Pass 7: the sea and the coast

### NOAA NCEI Global Historical Tsunami Database

- **Verdict:** open. Quote: "Access to this dataset is unrestricted." — https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ngdc.mgg.hazards:G02151. Attribution: "NCEI/WDS Global Historical Tsunami Database. NOAA National Centers for Environmental Information. doi:10.7289/V5PN93H7". Access: `https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/tsunamis/events?country=PHILIPPINES` (76 events 1700–1970; Taal 1716, 1749, 1754, 1911, 1965 present, cause code 6). No auth; about 50 kB.

### GEBCO bathymetry

- **Verdict:** open (public domain). Quote: "The GEBCO Grid is placed in the public domain and may be used free of charge." and "The GEBCO Grid should NOT be used for navigation or for any other purpose involving safety at sea." — https://www.gebco.net/data-products/gridded-bathymetry/terms-of-use. Attribution: "GEBCO Bathymetric Compilation Group 2026 (2026)", doi:10.5285/4f68d5c7-45eb-f999-e063-7086abc036fa. Access: https://download.gebco.net (user-defined area, GeoTIFF/NetCDF, 15 arc-second); Earth Engine only through the community catalog (`projects/sat-io/open-datasets/gebco/gebco_grid`, GEBCO_2023). A 60 km box ≈ 50 kB **[U]**.

### IOC Sea Level Station Monitoring Facility

- **Verdict:** noncommercial-only; registration. Quote: "Data and products available on this web-site may not be used for any commercial purposes." and "The data presented under this service has not undergone any quality control and data is provided as received." — https://www.ioc-sealevelmonitoring.org/disclaimer.php; "Users are required to register for this service." — https://www.ioc-sealevelmonitoring.org/service.php. Attribution: "Sea level station monitoring facility. Accessed at https://www.ioc-sealevelmonitoring.org on <date> at VLIZ", doi:10.14284/482. Access: `service.php?query=data&code=<station>&timestart=…&timestop=…&format=json` (v1) or the v2 API with a key; Philippine stations `luba`, `curri`, `lega`, `mani`, `subi`, `davo`. **Registration is Kurt's action if built.** 2–3 MB per station-month at 1 minute **[U]**.

### Copernicus Marine (CMEMS) ocean colour

- **Verdict:** open (Copernicus Marine licence; free account). Quote: "This Licence is granted free of charge." (§2.1); derivative works carry "Generated using E.U. Copernicus Marine Service Information" (§2.4a) — https://marine.copernicus.eu/user-corner/service-commitments-and-licence. Access: `copernicusmarine subset --dataset-id …` on OCEANCOLOUR_GLO_BGC_L4_MY_009_104 (4 km, 1997-09 → , daily/monthly CHL; doi:10.48670/moi-00281). **Account is Kurt's action if built.** 50–100 kB per box-month **[U]**.

### NOAA OISST v2.1

- **Verdict:** open (NOAA data; cite Huang et al. 2021, doi:10.1175/JCLI-D-20-0166.1). Access: `https://www.ncei.noaa.gov/data/sea-surface-temperature-optimum-interpolation/v2.1/access/avhrr/YYYYMM/oisst-avhrr-v02r01.YYYYMMDD.nc` (1,532,099 bytes per global day, HEAD; 0.25°, 1981-09 → ). No auth.

### Allen Coral Atlas

- **Verdict:** open (CC BY 4.0 for maps and statistics; the Planet mosaics are CC BY-NC-SA and are not reused). Quote: "Allen Coral Atlas maps, bathymetry and map statistics are © 2018-2023 Allen Coral Atlas Partnership" "and Arizona State University and licensed CC BY 4.0." — https://allencoralatlas.org/resources. Access: Earth Engine `ACA/reef_habitat/v2_0` (5 m; bands `geomorphic`, `benthic`, `reef_mask`; STAC license CC-BY-4.0). Attribution: "Allen Coral Atlas (2022), doi:10.5281/zenodo.3833242".

### Global Fishing Watch

- **Verdict:** noncommercial-only (CC BY-NC 4.0); API token issued to organisations. Quote: "The Services are available for noncommercial use only in accordance with the CC BY-NC 4.0 license."; "50,000 requests per day" — https://globalfishingwatch.org/our-apis/documentation/docs/license-rate-limits; "You may not scrape the Site to extract data." — https://globalfishingwatch.org/terms-of-use/. Applicants "represent that you are applying on behalf of an organization or entity". Attribution: "Powered by Global Fishing Watch." with a link. **Design consequence:** low priority; an individual portfolio may not qualify for a token; decide at M3 (OPEN-QUESTIONS Q25).

---

## Pass 8: the long air record, sound and pressure

### NASA MEaSUREs multi-satellite volcanic SO2 (MSVOLSO2L4)

- **Verdict:** open (NASA full and open; access constraints "None" in the CMR record https://cmr.earthdata.nasa.gov/search/collections.umm_json?short_name=MSVOLSO2L4). Attribution: "Carn, S. (2025), Multi-Satellite Volcanic Sulfur Dioxide L4 Long-Term Global Database V4, GES DISC, doi:10.5067/MEASURES/SO2/DATA405". Access: `https://measures.gesdisc.eosdis.nasa.gov/data/SO2/MSVOLSO2L4.4/MSVOLSO2L4_v04-00-2026m0513.txt` (193,575 bytes, HEAD; one ASCII table, 1978-10-31 → 2026-05-13, yearly updates). **Auth: Earthdata login** plus the "NASA GESDISC DATA ARCHIVE" app authorisation on the account.

### NASA MERRA-2 reanalysis

- **Verdict:** open. Access: Earth Engine `NASA/GSFC/MERRA/aer_nv/2` (3-hourly aerosol, 1980-01-01 → 2026-09-01; STAC https://earthengine-stac.storage.googleapis.com/catalog/NASA/NASA_GSFC_MERRA_aer_nv_2.json), or GES DISC `M2TMNXAER` monthly files (481 MB each, global; Earthdata login). Attribution: "GMAO (2015), MERRA-2 tavgM_2d_aer_Nx V5.12.4, GES DISC, doi:10.5067/FH9A0MLJPC7N".

### IASI SO2 (AERIS / EUMETSAT)

- **Verdict:** open-with-conditions. Quote: for minor use "Please notify the Principal Investigator, send a copy of the manuscript before publication" and for substantial use "Please contact the principal investigator to offer co-authorship to the team." — https://iasi.aeris-data.fr/data-use-policy/. Attribution: "IASI is a joint mission of EUMETSAT and the Centre National d'Etudes Spatiales (CNES, France)"; Clarisse et al. 2026, ESSD 18, doi:10.5194/essd-18-6667-2026; data DOIs 10.25326/868–870. Access: THREDDS https://thredds-su.ipsl.fr/thredds/catalog/catalog-iasi-l2.html (daily global L2 NetCDF, tens to hundreds of MB each **[U]**; 2007 → ). **Design consequence:** a cross-check series only; the PI is notified before it goes live (a courtesy, not a licence condition for a website).

### NOAA IGRA radiosondes

- **Verdict:** open. Attribution: Durre et al. 2016, doi:10.7289/V5X63K0Q. Access: `https://www.ncei.noaa.gov/data/integrated-global-radiosonde-archive/access/data-por/<ID>-data.txt.zip`; Philippine stations use the RPM prefix: RPM00098223 Laoag (22.3 MB), RPM00098433 Tanay (12.3 MB), RPM00098444 Legaspi (17.2 MB), RPM00098646 Mactan (15.5 MB), RPM00098753 Davao (11.2 MB) (HEAD sizes). No auth.

### NOAA Integrated Surface Database (hourly)

- **Verdict:** open-with-conditions. Quote: "IMPORTANT NOTE:  The non-U.S. data in ISD are subject to WMO Resolution 40 restrictions, and cannot be redistributed to other users or customers." — https://noaa-isd-pds.s3.amazonaws.com/readme.txt. Attribution: "NOAA National Centers for Environmental Information (2001): Global Surface Hourly"; Smith, Lott, Vose 2011, doi:10.1175/2011BAMS3015.1. Access: `https://www.ncei.noaa.gov/data/global-hourly/access/<YYYY>/<USAF><WBAN>.csv` (Legazpi 98444099999 1.33 MB, Tanay 98433099999 1.28 MB, Laoag 98223099999 4.56 MB for 2024, HEAD). No auth.
- **Design consequence:** only derived pressure-jump indicators are shown; the raw Philippine station files are never put in a public release (the private archive is fine under archiving standard §6).

### Infrasound channels on FDSN

- See EarthScope in pass 2 (same services and terms).

### WWLLN lightning network

- **Verdict:** **paid / unusable.** Quote: "WWLLN archival data are copyrighted by the University of Washington and are available at nominal cost." and "Archival data are available for sale from August 15, 2004 to the present." and "Our site hosts receive a free monthly subscription." — https://wwlln.net/. No free path short of hosting a sensor. Alternatives checked: GOES GLM does not see the Philippines; ISS LIS (NASA GHRC, free, 2017-03-01 → 2023-11-16, doi:10.5067/LIS/ISSLIS/DATA109) only on overpasses; GLD360 and ENTLN are commercial. **Dropped**; the volcanic-lightning story point cites the literature instead.

---

## Pass 9: archives, research and the economy

### Library of Congress Chronicling America

- **Verdict:** open (pre-1931 newspapers treated as public domain; the user assesses rights). The collection rights page was **not fetched** (403; check https://www.loc.gov/collections/chronicling-america/about-this-collection/rights-and-access/ by hand). Quote: "Beginning in 2025, the Chronicling America collection is accessible exclusively via the loc.gov API." — https://www.loc.gov/apis/additional-apis/chronicling-america-api/; "This API is accessible to the public with no API key or authentication required, however, rate limiting is enforced." — https://guides.loc.gov/chronicling-america/additional-features; 20 requests per minute for JSON — https://www.loc.gov/apis/json-and-yaml/working-within-limits/. Access: `https://www.loc.gov/collections/chronicling-america/?q=<terms>&dates=1911/1911&fo=json`. No auth; a descriptive User-Agent.

### USGS declassified satellite imagery (1960s–80s)

- **Verdict:** open (public domain) for frames already scanned; **a scanning fee of "$30.00 per frame"** for unscanned ones (https://www.usgs.gov/centers/eros/science/usgs-eros-archive-declassified-data-declassified-satellite-imagery-1). Attribution: "USGS EROS, Declassified Satellite Imagery-1, doi:10.5066/F78P5XZM". Access: EarthExplorer (free EROS login, **Kurt's action if built**); Corona frames about 80 MB at 14 µm. **Only already-scanned frames are used.**

### Wikimedia Commons historical photos

- **Verdict:** open-with-conditions (per-file licence). Quote: "Each media file has its licensing specified on its file description page." — https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia. Access: `https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&titles=File:<name>&iiprop=extmetadata|url` to store author, licence and link per image. No auth; descriptive User-Agent.

### OpenAlex

- **Verdict:** open (CC0). Quote: "Our data is CC0, our code is open source, and our governance is transparent." — https://openalex.org/about; "OpenAlex data is free, and so is casual use of the API — you can make basic queries with no key at all." — https://help.openalex.org/how-to-use-the-api/rate-limits-and-authentication (10 requests per second without a key; a free key for cursor paging). Access: `https://api.openalex.org/works?search=<terms>&filter=publication_year:2020`. 1–2 MB per volcano query **[U]**.

### PSGC geographic codes (PSA)

- **Verdict:** open (PSA statistical classification); **psa.gov.ph answers 403 to scripts**, terms not fetched (same posture as Replay and Lights: `../../typhoon-replay/pipeline/sources.yaml`, `psgc-cities-municipalities`). Access: the quarterly xlsx by hand (adopted as an archive release); the community mirror https://psgc.gitlab.io/api/ as the automatic link (last modified 2022-08-27, stale for post-2023 code changes).

### WRI Global Power Plant Database

- **Verdict:** open (CC BY 4.0; https://github.com/wri/global-power-plant-database, v1.3.0, "not currently maintained by WRI"). Access: https://wri-dataportal-prod.s3.amazonaws.com/manual/global_power_plant_database_v_1_3.zip (4,178,889 bytes, HEAD). Attribution: "Global Energy Observatory, Google, KTH Royal Institute of Technology in Stockholm, Enipedia, World Resources Institute. 2018. Global Power Plant Database v1.3.0" **[U wording]**.

### PhilGEPS procurement notices

- **Verdict:** **link-only.** Quote: "Unless otherwise specified, no one has permission to copy, redistribute, reproduce or republish in any form, any information found in this website." — PhilGEPS Terms and Conditions PDF, https://philgeps.gov.ph/CMS_DOCUMENTS/TC_Policy/1640056854_TERMS%20AND%20CONDITION_Final%20v2.pdf. The open-data portal https://data.philgeps.gov.ph/ answered HTTP 522 (origin down) twice. **Dropped from the roadmap** unless the portal returns with a licence.

### Department of Tourism arrivals

- **Verdict:** open ("All content is in the public domain unless otherwise stated." — https://www.tourism.gov.ph/dot/). Access: national monthly arrivals by country as CSV/JSON (e.g. https://dot-governance.s3.ap-southeast-1.amazonaws.com/2026/09/2025-MONTHLY-VISITOR-ARRIVALS-BY-COUNTRY-OF-CITIZENSHIP.csv, 2010 → ); **provincial series (Albay, Batangas) exist only as FOI releases and PSA regional PDFs**, so they are hand-transcribed. No auth.

---

## Summary table

Verdicts in canvas order; "registry id" points into [sources-draft.yaml](sources-draft.yaml); "M" is the milestone decided on 2026-10-21 (DECISIONS.md Q30, Q31; [DATA-PLAN.md](DATA-PLAN.md) §9); "out (Q30)" marks a source outside the 24+1 set, kept here as evidence and history. "Changed" marks a verdict or fact that differs from the canvas.

| # | Canvas row | Verdict | Auth | Registry id(s) | M | Changed |
|---|---|---|---|---|---|---|
| 1 | Sentinel-5P TROPOMI SO2 | open | EE service account | `s5p-offl-so2` | M1 | |
| 2 | NASA FIRMS (VIIRS, MODIS) | open | EE; free MAP_KEY; Earthdata for the archive tool | `firms-modis`, `modis-mod14a1`, `viirs-vnp14a1` | M1 | |
| 3 | MIROVA v2.5 | open (CC BY 4.0) | none | `mirova-vrp` | out (Q30) | |
| 4 | USGS ComCat | open (public domain) | none | `usgs-comcat-ph-1900-2009`, `usgs-comcat-ph-2010` | M1 | |
| 5 | Smithsonian GVP | open-with-conditions (non-commercial, cite); terms page not fetched | none | `gvp-volcanoes-ph`, `gvp-eruptions-ph` | M1 | |
| 6 | WorldPop, GHSL, WorldCover, DEM | open (CC BY 4.0; JRC; CC BY 4.0; notice) | EE | `worldpop-100m`, `ghsl-r2023a`, `esa-worldcover-v200`, `copernicus-dem-glo30` | M1 (WorldPop, DEM); GHSL, WorldCover out (Q30) | |
| 7 | PHIVOLCS public bulletins | link-only (cite each figure) | none | `phivolcs-bulletins`, `phivolcs-lava-bulletins` (+ `phivolcs-earthquakes` M1.1) | M1 (earthquake tables out, Q30) | |
| 8 | Himawari-8/9 (NODD) | open | none | `himawari-ahi-nodd` | out (Q30) | **fact: HSD, not NetCDF; 780 MB per scan** |
| 9 | Sentinel-5P aerosol index and layer height | open | EE | `s5p-offl-aer-ai`, `s5p-offl-aer-lh` | M2 (AER_AI); AER_LH out (Q30) | |
| 10 | Darwin VAAC advisories | **Tokyo VAAC (JMA): open-with-conditions; Darwin (BoM): link-only** | none | `vaac-tokyo-advisories` | M1 | **changed: issuer and verdict** |
| 11 | CALIPSO lidar | open (CC0) | Earthdata login | `calipso-lid-l2` | out (Q30) | |
| 12 | Copernicus CAMS reanalysis | open (CC BY 4.0) | free ADS account | `cams-eac4` | out (Q30) | |
| 13 | ERA5 winds | open (CC BY 4.0) | none (buckets) | `era5-pressure-levels` | M1 | |
| 14 | NASA Worldview / GIBS | open | none | `nasa-gibs-worldview` | out (Q30) | |
| 15 | Sentinel-1 InSAR (LiCSAR) | open-with-conditions (acknowledgement) | none | `licsar-taal-032d` | out (Q30) | |
| 16 | Sentinel-2 and Landsat | open | EE | `s2-sr-harmonized`, `landsat-c2-l2` | M1 | |
| 17 | Landsat thermal band | open | EE | `landsat-surface-temperature` | M1 (Q31) | |
| 18 | Sentinel-1 SAR change detection | open | EE | `s1-grd` | M1 (Q31) | |
| 19 | Copernicus EMS rapid mapping | open (mandatory citation form) | none | `copernicus-ems-emsr418` | out (Q30) | EMSR418 found (Taal 2020) |
| 20 | Raspberry Shake | open-with-conditions (logo + line; no re-serving) | none | `raspberry-shake-am` | out (Q30) | not CC BY-SA |
| 21 | EarthScope FDSN | open (CC BY 4.0 default) | none | `earthscope-fdsn` | out (Q30) | **fact: only IU DAV and PS BAG in the Philippines** |
| 22 | NASA GPM IMERG | open (CC0) | EE | `gpm-imerg-v07` | M2 | |
| 23 | DSWD DROMIC | open (government work) | none | `dswd-dromic-reports` | M1 | fact: .docx files |
| 24 | NDRRMC situation reports | open (government work); site blocks scripts; mirrors personal-use | none (hand) | `ndrrmc-sitreps` | out (Q30) | **in practice hand-collected** |
| 25 | NOAA NCEI significant eruptions | open | none | `ncei-significant-eruptions` | out (Q30) | |
| 26 | DA damage bulletins + cropland NDVI | open but **link-only in practice** (no hosted bulletins) | none | `da-damage-bulletins`, `s2-sr-harmonized` | out (Q30) | **changed** |
| 27 | OpenStreetMap | open-with-conditions (ODbL) | none | `osm-philippines` | out (Q30) | |
| 28 | Meta high-resolution population | open-with-conditions (CC BY) | none | `meta-hrsl-phl` | out (Q30) | |
| 29 | OpenAQ and MODIS AOD | open-with-conditions (OpenAQ, per station; free key) / open (MCD19A2) | free API key / EE | `openaq-ph`, `modis-mcd19a2-aod` | out (Q30) | PH coverage unverified |
| 30 | OpenSky Network | **noncommercial-only and unusable (historical access by application)** | application | `opensky-network` (retired) | dropped | **changed** |
| 31 | Wikipedia page views and GDELT | open (CC0) / open (cite) | none | `wikimedia-pageviews`, `gdelt-v2` | out (Q30) | BigQuery route paid, not used |
| 32 | HazardHunterPH / GeoRiskPH | link-only | n/a | `hazardhunterph` | link only | |
| 33 | Nevada Geodetic Lab GNSS | open (cite) | none | `ngl-gnss-tenv3` | out (Q30) | |
| 34 | GEM Global Active Faults | open-with-conditions (CC BY-SA) | none | `gem-active-faults` | out (Q30) | |
| 35 | USGS Slab2 | open (public domain); ScienceBase blocks scripts | none (hand) | `usgs-slab2` | out (Q30) | |
| 36 | LaMEVE (VOGRIPA) | **noncommercial-only / written permission needed** | none | `lameve-vogripa` (retired) | dropped unless permitted | **changed** |
| 37 | GloSSAC | open | Earthdata login | `glossac` | out (Q30) | |
| 38 | eVolv2k | open (CC BY 4.0, v3/v4) | none | `evolv2k-v4` | out (Q30) | v2 "scientific use only" avoided |
| 39 | NASA GISTEMP | open | none | `nasa-gistemp-v4` | out (Q30) | |
| 40 | DAHITI / Hydroweb | open-with-conditions, NC-ambiguous (DAHITI); open ETALAB (Hydroweb, Taal unconfirmed) | registration | `dahiti-taal` | out (Q30) | Taal has 15 points |
| 41 | JRC Global Surface Water | open | EE | `jrc-global-surface-water` | out (Q30) | ends 2021 |
| 42 | Sentinel-3 OLCI | open | EE | `s3-olci` | out (Q30) | L1B only on EE |
| 43 | HydroSHEDS | open (v1; v2 Americas only) | EE | `hydrosheds-v1` | out (Q30) | |
| 44 | Copernicus GloFAS | open-with-conditions (CEMS-FLOODS; account) | free EWDS account | `glofas-historical` | out (Q30) | |
| 45 | NASA SMAP | open (public domain) | EE | `nasa-smap-l4` | out (Q30) | |
| 46 | MODIS land surface temperature | open | EE | `modis-lst-daily` | out (Q30) | |
| 47 | Hansen Global Forest Change | open (CC BY 4.0) | EE | `hansen-gfc` | out (Q30) | |
| 48 | NASA Black Marble | open | EE service account | `black-marble-vnp46a2` | M1.1 (now on EE) | |
| 49 | Lights poverty estimates | own data (CC BY 4.0) | none | `lights-poverty-estimates` | M1.1 | |
| 50 | PSA census by barangay | open-with-conditions (CC BY per OpenSTAT); site blocks scripts | none (hand) | `psa-census-barangay-2020` | out (Q30) | hand download |
| 51 | Overture, Google and Microsoft buildings | open-with-conditions (ODbL / CC BY 4.0 / CDLA-P 2.0) | none | `overture-buildings` | out (Q30) | Microsoft global is CDLA, not ODbL |
| 52 | DOH health facility registry | open (government work); site blocks scripts; terms not fetched | none (hand) | `doh-nhfr` | out (Q30) | hand download |
| 53 | OCHA Financial Tracking Service | open (public API) | none | `ocha-fts-flows` | out (Q30) | |
| 54 | ReliefWeb API and GLIDE | open-with-conditions (gated appname; files link-only) / open | appname / none | `reliefweb-glide` | out (Q30) | API gated since 2025-11-01 |
| 55 | OurAirports | open (public domain) | none | `ourairports` | out (Q30) | |
| 56 | NOAA NCEI tsunami database | open | none | `ncei-tsunami-events` | out (Q30) | |
| 57 | GEBCO bathymetry | open (public domain) | none (hand) | `gebco-grid` | out (Q30) | |
| 58 | IOC Sea Level Station Monitoring Facility | **noncommercial-only**; registration | registration | `ioc-sea-level` | out (Q30) | **changed** |
| 59 | Copernicus Marine ocean colour | open (Copernicus Marine licence; account) | free account | `cmems-ocean-colour` | out (Q30) | |
| 60 | NOAA OISST | open | none | `noaa-oisst-v21` | out (Q30) | |
| 61 | Allen Coral Atlas | open (CC BY 4.0) | EE | `allen-coral-atlas` | out (Q30) | |
| 62 | Global Fishing Watch | **noncommercial-only (CC BY-NC 4.0); token for organisations** | application | `global-fishing-watch` | out (Q30) | |
| 63 | NASA MEaSUREs MSVOLSO2L4 | open | Earthdata login | `nasa-msvolso2l4` | M1 (Q31) | |
| 64 | NASA MERRA-2 | open | EE / Earthdata | `merra2-aerosol` | out (Q30) | |
| 65 | IASI SO2 (AERIS) | open-with-conditions (notify the PI) | none | `iasi-so2-aeris` | out (Q30) | |
| 66 | NOAA IGRA radiosondes | open | none | `noaa-igra2-ph` | out (Q30) | |
| 67 | NOAA Integrated Surface Database | open-with-conditions (WMO Res. 40: no redistribution of PH station files) | none | `noaa-isd-ph` | out (Q30) | **condition added** |
| 68 | Infrasound channels on FDSN | open (as EarthScope) | none | `earthscope-fdsn` | out (Q30) | |
| 69 | WWLLN lightning | **paid / unusable** | contract | `wwlln-lightning` (retired) | dropped | **changed (canvas: "may cost")** |
| 70 | Chronicling America | open (public domain newspapers; API, rate-limited) | none | `loc-chronicling-america` | out (Q30) | rights page not fetched |
| 71 | USGS declassified imagery | open (public domain) for scanned frames; **$30 per unscanned frame** | EROS login | `usgs-declassified-imagery` | out (Q30) | scanning fee excluded |
| 72 | Wikimedia Commons photos | open-with-conditions (per file) | none | `wikimedia-commons-photos` | out (Q30) | |
| 73 | OpenAlex | open (CC0) | none (free key optional) | `openalex-works` | out (Q30) | |
| 74 | PSGC geographic codes | open; site blocks scripts (mirror automatic) | none | `psgc-cities-municipalities` | out (Q30) | |
| 75 | WRI Global Power Plant Database | open (CC BY 4.0) | none | `wri-global-power-plants` | out (Q30) | |
| 76 | PhilGEPS procurement notices | **link-only (copyright reserved; portal down)** | registration | `philgeps-notices` (retired) | dropped | **changed** |
| 77 | Department of Tourism arrivals | open (public domain); provincial series hand-transcribed | none | `dot-visitor-arrivals` | out (Q30) | |

Also in the registry but not canvas rows: `cod-ab-phl-gdb` (OCHA boundaries, CC BY-IGO, M1, read by range), `phivolcs-earthquakes` (the monthly tables, out under Q30), and the two Q31 additions `omi-omso2e` (OMI SO2, open, Earthdata login, M1) and `open-buildings-temporal` (CC BY 4.0, EE, M1.1).

## Pages to re-read by hand (blocked on 2026-10-21)

https://www.si.edu/termsofuse and https://volcano.si.edu/gvp_termsofuse.cfm (GVP); https://openstat.psa.gov.ph/Terms and https://psa.gov.ph/classification/psgc (PSA); https://nhfr.doh.gov.ph/ (DOH); https://ndrrmc.gov.ph/ (NDRRMC); https://www.sciencebase.gov/catalog/item/5aa1b00ee4b0b1c392e86467 (Slab2 file list); https://www.loc.gov/collections/chronicling-america/about-this-collection/rights-and-access/; https://osmfoundation.org/wiki/Licence/Community_Guidelines/Produced_Work_-_Guideline; https://data.gov.au/data/dataset/volcanic-ash-advisory-past-archived-advisories (Darwin VAAC archive licence); the DAHITI registration terms; the HydroSHEDS v1 TechDoc licence PDF; https://disc.gsfc.nasa.gov/data-guidelines (GES DISC citation template); https://asdc.larc.nasa.gov/citing-data and whether GloSSAC V2.24 supersedes V2.22.
