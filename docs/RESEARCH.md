# Research: a retrospective multi-sensor record of Philippine volcanoes

Status: 2026-10-21, phase 3 of [WORKFLOW.md](WORKFLOW.md), written for the recommended candidate in [CANDIDATES.md](CANDIDATES.md). Every claim has a link and an access date (2026-10-21 unless stated); **[U]** marks an estimate or a claim not verified on a primary page. The raw notes with more detail are in [`research/volcanoes.md`](research/volcanoes.md) (and [`research/platform-limits.md`](research/platform-limits.md) for the free tiers). Probes were tiny: a few KB per request, no bulk downloads, no accounts, no Earth Engine calls.

## 0. What the product is, in one paragraph

For each of the 24 volcanoes PHIVOLCS lists as active, the site shows what instruments and institutions recorded over about two decades: eruptions and their size (Smithsonian GVP), the daily figures PHIVOLCS reported in its public bulletins (alert level, volcanic earthquake counts, SO2 flux, plume height, deformation statements; 2017 → ), satellite SO2 columns (TROPOMI, 2018-12 → ), thermal anomalies (MODIS 2000 → , VIIRS 2012 → , MIROVA radiative power), earthquakes within 30 km (USGS 1900 → , PHIVOLCS 2016 → ), the population and land cover within distance rings, and later ground deformation (Sentinel-1 InSAR). Official figures sit beside independent satellite measurements, each labelled with its instrument, quantity, coverage and limits. It is a **dated retrospective record**, not a monitoring service: no current status, no alerts, DOST-PHIVOLCS named as the authority on every view.

## 1. PHIVOLCS: what is public, what it says, what the terms are

### 1.1 The active list and the alert schemes

- 24 active volcanoes: Babuyan Claro, Banahaw, Biliran (Anas), Bud Dajo, Bulusan, Cabalian, Cagua, Camiguin de Babuyanes, Didicas, Hibok-hibok, Iraya, Iriga, Isarog, Kanlaon, Leonard Kniaseff, Makaturing, Matutum, Mayon, Musuan (Calayo), Parker, Pinatubo, Ragang, Smith, Taal; "active" = "erupted within historical times (within the last 600 years)" or within the last 10,000 years by dating ([Volcanoes of the Philippines](https://www.phivolcs.dost.gov.ph/volcanoes-of-the-philippines/)). Coordinates are not on that page; the GVP WFS supplies them (§2), and the two lists differ in membership and naming (GVP has 23, lacks Bud Dajo and Smith, adds the San Pablo Volcanic Field; Parker = Melebingoy, Leonard Kniaseff = Leonard Range, Hibok-hibok = Camiguin). The crosswalk is a small hand-made table in the repo.
- Alert levels 0–5 differ by volcano (Taal: Normal / Low-Level Unrest / Increasing Unrest / Intensified or Magmatic Unrest / Hazardous Eruption Imminent / Highly Hazardous Eruption in Progress; Mayon, Kanlaon, Bulusan, Pinatubo and Hibok-hibok have their own wording and danger-zone radii) ([Volcano Alert Levels](https://www.phivolcs.dost.gov.ph/volcano-alert-levels/)). **No alert-level history table is published**; the history is reconstructed from bulletins.

### 1.2 Daily bulletins: two channels, two eras

| Channel | Period | Format | Fields | Probe |
|---|---|---|---|---|
| WordPress site, category `volcano-bulletin` | 2017-09-02 → 2024 (prose "VOLCANO BULLETIN dd Month yyyy 8:00 A.M."); 2025 → titles only ("Summary of 24Hr Observation", body empty in the served HTML) | HTML prose, numerals spelled out in parentheses | volcanic earthquake count and sub-types, tremor durations, plume height and drift, SO2 t/day with its measurement date, crater-lake temperature, a deformation sentence naming the method (tilt, cGPS, EDM, InSAR), alert level, danger-zone radius, recommendations | listing paginates to page 1,498 (about 15,000 posts [U]); examples [Taal 2022-03-14](https://www.phivolcs.dost.gov.ph/taal-volcano-bulletin-14-march-2022-8-00-am/) ("SO2 ... averaged 14,524 tonnes/day on 13 March 2022"), [Taal 2020-01-25](https://www.phivolcs.dost.gov.ph/taal-volcano-bulletin-25-january-2020-8-00-a-m/) |
| PHIVOLCS-LAVA portal (`https://wovodat.phivolcs.dost.gov.ph/`) | about early 2022 → today (bulletin id 1000 = 2022-04-02; id 2000 = 2023-01-13; id 14000 = 2026-05-30; id 16917 = 2026-10-21; ids are not contiguous) | HTML with labelled sections (English with `&lang=en`, Filipino by default) | alert level and label; eruption events; seismicity ("2 volcanic earthquakes including 1 volcanic tremor"); crater-lake acidity and temperature with dates; SO2 flux ("1002 tonnes / day (20 October 2026)"); plume ("600 meters tall; weak emission; southeast drift"); ground deformation ("Short-term inflation of Taal Volcano Island"); earthquake totals; recommendations | `/bulletin/activity-{tvo,mvo,kvo,bvo}?bid=N&lang=en` for Taal, Mayon, Kanlaon, Bulusan; `/bulletin/list-of-bulletin` lists the latest four. The TLS chain fails verification in some clients (curl on macOS succeeded; a Node fetch did not) |

Eruption bulletins (e.g. [Kanlaon 2025-04-08](https://www.phivolcs.dost.gov.ph/kanlaon-volcano-eruption-bulletin-08-april-2025-02-00-pm/)) are structured sections: eruption data, monitoring data before the eruption, outlook, recommendations.

Bulletins exist only for the volcanoes with observatories (Taal, Mayon, Kanlaon, Bulusan, occasionally Pinatubo and Hibok-hibok). The other 18 active volcanoes get GVP history, satellite series, earthquakes and exposure only; the site says so.

### 1.3 The LAVA portal beyond bulletins

Navigation (probed): Volcano Status, Volcanic Earthquake, Volcano Catalog (active 24, potentially active, inactive), Eruption History, Alert Level Bulletin/Advisory, Monitoring Data (visual, time series, 3D/2D), Data Policy. Eruption history shows 216 rows for 24 volcanoes with "Ongoing Audit ... subject to change" and a download link; the download endpoint (`/volcan/download-eruption-history`) redirects to the login page (HTTP 302), as do `/data/download`, `/graph/plot` and `/seismic/seismic-plot`.

**Data policy** (`/user/policy`, "Updated: July 01, 2020", quoted verbatim from the probe):
> DOST-PHIVOLCS data that are labeled "public" are shared by DOST-PHIVOLCS to the national and international scientific communities for free. Such usage includes, but may not limited to scientific research, responses to volcanic crises and education. [...] DOST-PHIVOLCS data users need to register. [...] Data source should be cited as DOST-PHIVOLCS. [...] DOST-PHIVOLCS data should not be used by anyone other than DOST-PHIVOLCS officials for publicly forecasting ongoing unrest in a monitored active volcano in the Philippines. [...] Redistribution or charging for access to DOST-PHIVOLCS data is prohibited.

Reading: the policy binds registered users of the portal's datasets. The public bulletin pages are press releases that PHIVOLCS also posts on Facebook and that the Smithsonian weekly reports relay; they carry no terms, and under RA 8293 §176.1 "No copyright shall subsist in any work of the Government of the Philippines. However, prior approval of the government agency or office wherein the work is created shall be necessary for exploitation of such work for profit" ([lawphil](https://lawphil.net/statutes/repacts/ra1997/ra_8293_1997.html)). The portfolio is non-profit. Still, the no-forecasting and no-redistribution sentences set the tone PHIVOLCS wants, so the posture in [DATA-PLAN.md](DATA-PLAN.md) §3 is: public pages only, no registered downloads, every value cited with its bulletin link, no bulk PHIVOLCS-derived file published until PHIVOLCS confirms in writing, and nothing that forecasts.

### 1.4 Earthquake information

[`earthquake.phivolcs.dost.gov.ph`](https://earthquake.phivolcs.dost.gov.ph/) is a 2.5 MB HTML page (probed: 1,295 table rows, October 2026 to date) with columns date-time (PHT), latitude, longitude, depth (km), magnitude, location text; each row links to an event page (`/2026_Earthquake_Information/October/2026_1021_0855_B1.html`) with the magnitude type ("Ms 2.4"), origin, intensities, and "Always refer to the latest earthquake information posted at the PHIVOLCS official website". Monthly archive pages (`/EQLatest-Monthly/YYYY/YYYY_Month.html`) exist from 2016 with gaps (June 2016 404), 0.5–2.8 MB each, about 1,450 events a month in 2025. No API, no CSV; FOI precedents point requesters to the website [U].

### 1.5 Hazard maps

Volcano hazard maps are raster images (PDF, PNG, JPG) on [volcano-hazard](https://www.phivolcs.dost.gov.ph/volcano-hazard/) without georeferencing or licence; GIS versions are KMZ through GISWEB and HazardHunterPH after login or a form. HazardHunterPH's [terms](https://hazardhunter.georisk.gov.ph/terms-of-use) forbid republishing and redistribution. Decision: **link, never re-serve**; the site's own rings (5, 10, 20, 30 km) and the published PDZ radii (Taal 7 km [U], Mayon 6 km, Kanlaon 4–14 km by alert level, Bulusan 4 km) are drawn from the alert-level page and bulletins, labelled as such.

## 2. Smithsonian Global Volcanism Program

- GeoServer WFS at `https://webservices.volcano.si.edu/geoserver/GVP-VOTW/ows` (probed; `Fees NONE`, `AccessConstraints NONE`): layers `Smithsonian_VOTW_Holocene_Volcanoes` (1,214), `Smithsonian_VOTW_Holocene_Eruptions` (11,089), `Smithsonian_VOTW_Pleistocene_Volcanoes`, `E3WebApp_Eruptions1960`, `E3WebApp_HoloceneVolcanoes`; CSV and GeoJSON output with CQL filters (`Country='Philippines'`, `Volcano_Number=273070` returns Taal's 40 eruptions).
- Volcano fields: number, name, landform, type, last eruption year, region, geological summary, latitude, longitude, elevation, tectonic setting, evidence category, rock type. Eruption fields: eruption number, activity type (confirmed/uncertain), **VEI** with modifier, start and end year/month/day with **explicit uncertainty fields and modifiers**, evidence method.
- Philippines: 23 Holocene volcanoes; 233 eruption rows including the Babuyan group; of the 215 on the main islands, 104 start in 1900 or later and 41 in 2000 or later; VEI 4: 9 rows, VEI 5: 2, VEI 6: 5 (Pinatubo 1991 among them); Mayon 69 rows, Taal 40, Kanlaon 33, Bulusan 26. Recent rows: Taal 2020-01-12 VEI 4; Kanlaon 2024-06-03 and 2024-10-19 VEI 3; Mayon 2026-01-06 ongoing.
- Terms: the database page could not be fetched (Cloudflare); search snippets give "Global Volcanism Program, 2025. Volcanoes of the World (v. 5.3.0; 17 Jul 2025) ... https://doi.org/10.5479/si.GVP.VOTW5-2025.5.3" and the Smithsonian terms of use ("personal, educational, and other non-commercial purposes" with citation) [U]. Posture: fetch through WFS, archive privately, show derived figures with the citation, and keep GVP-derived rows in a separately licensed file of the published dataset (§3 of the data plan).
- Weekly Volcanic Activity Reports relay PHIVOLCS numbers week by week back to 2000 [U: site blocked]; they are the fallback source for 2000–2017 PHIVOLCS figures if a later milestone wants them.

## 3. Satellite SO2: Sentinel-5P TROPOMI

- Earth Engine `COPERNICUS/S5P/OFFL/L3_SO2` ([catalog](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_SO2), STAC probed: 2018-12-05 → 2026-10-18): 1,113 m pixels; bands `SO2_column_number_density` (mol/m², ground-level a priori), `SO2_column_number_density_15km`, `_amf`, `SO2_slant_column_number_density`, `cloud_fraction`, `absorbing_aerosol_index`, geometry; one image per orbit; QA applied at ingestion (`qa_value > 0.5`, solar zenith < 60°, cloud fraction limits). Only the ground-level and 15 km a priori columns are on GEE; the 1 km and 7 km box profiles exist in the L2 product only [U]. `NRTI/L3_SO2` runs from 2018-07-10.
- Licence: "free, full and open access to Copernicus Sentinel Data"; reproduction, distribution, adaptation permitted; attribution "Contains modified Copernicus Sentinel data [Year]" ([Copernicus Sentinel licence](https://ads.atmosphere.copernicus.eu/licences/ec-sentinel), [Data Space terms](https://dataspace.copernicus.eu/terms-and-conditions)).
- Science: a vertical column (mol/m², or Dobson Units) per pixel at one afternoon overpass is not a flux (t/day); a flux needs plume transport (wind) and is what PHIVOLCS measures by ground DOAS. The project computes **SO2 column mass inside a 50 km box** (sum of column × pixel area × 64 g/mol) and the valid-pixel fraction per day, and labels it as a proxy. Retrieval reference: Theys et al. 2017, AMT 10, 119 ([link](https://amt.copernicus.org/articles/10/119/2017/)). Weak passive degassing (hundreds of t/day) sits near the noise floor; eruptive and strong degassing (Taal 2021–22, Kanlaon 2024–25, thousands of t/day) is clear [U for a DU noise figure]. Tropical cloud removes many afternoon pixels; the coverage fraction is shown with every value. The 15 km band suits explosive plumes (Taal 2020-01-12), the ground-level band passive degassing.
- Existing automated users: MOUNTS ([mounts-project.com](http://www.mounts-project.com/), port 80 only) runs daily TROPOMI SO2, Sentinel-1 and Sentinel-2 for Taal, Mayon, Kanlaon and Bulusan as images with no CSV download and no licence statement [U].

## 4. Thermal anomalies

- **Earth Engine:** `FIRMS` (MODIS, 1 km daily, 2000-11-01 → 2026-10-19, STAC probed; bands `T21`, `confidence`, `line_number`), `MODIS/061/MOD14A1` (2000-02-24 → ; `FireMask` classes 7/8/9, `MaxFRP`; "no restrictions on subsequent use, sale, or redistribution"), `NASA/VIIRS/002/VNP14A1` (2012-01-19 → ; LP DAAC, freely accessible, cite).
- **FIRMS API** ([docs](https://firms.modaps.eosdis.nasa.gov/api/)): `/api/area/csv/[MAP_KEY]/[SOURCE]/[west,south,east,north]/[1–5 days]/[date]`; sources `MODIS_SP`, `VIIRS_SNPP_SP`, `VIIRS_NOAA20_SP`, `VIIRS_NOAA21_SP` and their NRT variants; "MAP_KEY limit is 5000 transactions / 10-minute interval"; the archive download tool returns CSV/shapefile/JSON by email with an Earthdata login; attributes include `frp` (MW), `confidence`, `daynight`, and `type` ("1 = active volcano", **only in standard-quality archive data**). Caveat to replicate: "the active fire products have not been validated against independent data for their ability to detect volcanoes" ([FAQ](https://www.earthdata.nasa.gov/data/tools/firms/faq)). Kanlaon's April 2025 wildfires near the crater show why the series is called "thermal detections within N km (includes fires)".
- **MIROVA** ([mirovaweb.it](https://www.mirovaweb.it/NRT/)): volcanic radiative power (VRP, MIR method, detection limit about 1 MW) for 176 volcanoes including Taal, Mayon, Kanlaon, Pinatubo (not Bulusan); site terms are non-commercial. The **MIROVA Dataset v2.5** on OSF ([osf.io/zm62w](https://osf.io/zm62w/), OSF API probed: licence "CC-By Attribution 4.0 International", modified 2026-08-19) holds `VRP_GLOBAL_ARCHIVE_2025.csv` (98,625,213 bytes), `VRP_GLOBAL_ARCHIVE_2025.sql` (138 MB) and a schema document; MODIS + VIIRS, 2000–2025. This is the cleanest thermal series and a `file` source for the registry.

## 5. Ground deformation (InSAR)

- **COMET LiCSAR** ([portal](https://comet.nerc.ac.uk/comet-lics-portal/)): automatic Sentinel-1 interferograms and coherence; products are "Derived Works of Copernicus data" with the acknowledgement "LiCSAR contains modified Copernicus Sentinel data [year]" and citations (Lazecký et al. 2020; Morishita et al. 2020 for LiCSBAS). Frames found by reading frame polygons: Taal and Pinatubo `032D_07536_111313` (374 epochs, 2,888 pairs, 2014-10-19 → 2026-08-12; pairs bracket 2020-01-12) and `142A_07606_131313`; Mayon `134D_07688_131313`, `061D_07748_050613`, `069A_07674_131310`; Kanlaon `134D_07892_131210`, `061D_07906_131313`, `069A_07955_090909`; Bulusan and Hibok-Hibok also covered. Per-pair files could not be sized (the October 2025 storage migration left pair folders returning 404 on both paths); estimate about 30 MB per pair and tens of GB per frame [U]. Frame metadata holds look vectors, DEM, mean coherence and a Eurasia-referenced velocity (`geo.vlos_eur.tif`).
- **COMET Volcano Deformation Portal** ([index](https://comet.nerc.ac.uk/comet-volcano-portal/)): Taal and Pinatubo have time series and tools, Kanlaon partially, Mayon and Bulusan are absent; images CC BY-NC 4.0; "for general information purposes only". Link at milestone 1.
- **ASF HyP3**: 8,000 free credits a month, InSAR 10–15 credits per pair ([credits](https://hyp3-docs.asf.alaska.edu/using/credits/)); products expire; the free tier is funding-dependent. Earth Engine has `COPERNICUS/S1_GRD` only (no SLC, no InSAR).
- Literature: Bato et al. 2021, GRL, DOI 10.1029/2021GL092803 (Taal 2020: pre-eruptive pressurisation of a ~5 km reservoir, co-eruptive volume loss 0.531 ± 0.004 km³, lateral dike 0.643 ± 0.001 km³); UN-SPIDER DInSAR/SBAS note for Taal (−91 mm on the SW flank, +197 mm on the NE crater-lake shore, 2020-01-11/17 pair). PHIVOLCS bulletins themselves cite "electronic tilt, continuous GPS, and InSAR monitoring".
- Plan: milestone 1 links to the COMET portal and shows PHIVOLCS deformation statements as text; milestone 2 runs a cropped LiCSBAS time series for the Taal frame (see [DATA-PLAN.md](DATA-PLAN.md) §6).

## 6. Earthquakes

- **USGS ComCat / FDSN** ([service](https://earthquake.usgs.gov/fdsnws/event/1/)): CSV/GeoJSON; 20,000 events per query; probe counts for 4–22°N 116–128°E since 1900: 27,333 events, 24,990 at M ≥ 4, 16,011 at M ≥ 4.5, 631 at M ≥ 6; CSV columns `time, latitude, longitude, depth, mag, magType, ..., place, type, horizontalError, depthError, magError, ..., status`; US public domain, credit USGS. Pre-1970 rows are mostly ISC-GEM imports, so a century series is honest only above about M5.5 [U]. The Taal 2020 week (13.5–14.5°N, 120.5–121.5°E, 2020-01-10/16) returns 59 events, mostly mb 4.0–4.5 at 10 km.
- **ISC Bulletin** ([link](https://www.isc.ac.uk/iscbulletin/)): 1900 → , reviewed 24 months behind; citation required; includes PHIVOLCS-authored hypocentres for earlier years (a 2015 sample: 1,920 of 3,112 Philippine events authored by PHIVOLCS). Candidate for a later milestone.
- **PHIVOLCS** (§1.4): 2016 → with gaps, about 17,000 events a year in 2025.
- **GEM Global Active Faults** ([repo](https://github.com/GEMScienceTools/gem-global-active-faults)): CC BY-SA 4.0, 10.6 MB GeoJSON, Philippine traces from Peñarubia et al. 2019; share-alike, kept as a separate, credited layer. PHIVOLCS fault shapefiles are not public (KMZ, FOI denied [U]).

## 7. Exposure and context

| Dataset | Use | Access | Licence |
|---|---|---|---|
| WorldPop 100 m population (2015–2030 R2025A; GEE `WorldPop/GP/100m/pop` 2000–2020) | population within 5/10/20/30 km rings and the PDZ, per volcano | Earth Engine (`reduceRegions`) | CC BY 4.0 |
| GHSL GHS-POP and GHS-BUILT-S R2023A (1975–2030, 5-year steps) | population and built-up growth near volcanoes since 1975 | Earth Engine | EU open, acknowledge source |
| ESA WorldCover v200 (2021, 10 m) | land cover within rings | Earth Engine | CC BY 4.0 |
| Copernicus DEM GLO-30 (`COPERNICUS/DEM/GLO30_2024_1`, the GLO30 asset is superseded) | terrain, hillshade, profile | Earth Engine | free licence with notice |
| OCHA COD-AB PHL v03 (admin 0–4; 1,642 ADM3; gdb 361 MB) | boundaries, "which LGUs lie within N km" | HDX (as in Lights) | CC BY-IGO |

Exposure is a descriptive count ("people living within 10 km, WorldPop 2020"), never "people at risk".

## 8. Existing products, interest, literature

- Products: PHIVOLCS site and Facebook; GVP; MOUNTS (daily images for four volcanoes); MIROVA (VRP); COMET portal (Taal, Pinatubo, Kanlaon); Volcano Discovery; HazardHunterPH; unofficial scrapers (`DaijobuDes/phivolcs-dataset`, CC0; R package `lindol` [U]). **None combines PHIVOLCS ground series with satellite SO2, thermal and deformation in one retrospective per-volcano view for the Philippines.**
- Interest (Wikimedia pageviews API, en.wikipedia, monthly, 2019-01 → 2026-10, probed): Taal_Volcano 3.46 M views (peak January 2020: 1,374,478); Kanlaon 1.25 M (June 2024: 182,642; December 2024: 162,887; April 2025: 87,156; October 2025: 63,240); Mayon_Volcano 172k; Bulusan_Volcano 13k. Interest is crisis-driven; Kanlaon erupted on 2026-10-10 with a 5–6 km plume at Alert Level 2 (GMA News).
- Events for stories: Taal 2020-01-12 (VEI 4, Alert 2 → 4 in hours, about 459,300 people within 14 km per OCHA, 70,413 in evacuation centres by 18 January); Taal 2021-07 (record SO2) and 2022-03; Mayon 2018-01 and 2023-06 (20,000 evacuated); Kanlaon 2024-06-03, record SO2 11,556 t on 2024-09-11, 2024-12-09 eruption (about 87,000 to evacuate), 2025-04-08, 2026-02-19 and 2026-10-10; Bulusan 2022-06 and 2025-04-28.
- Literature: Valade et al. 2019 (MOUNTS, Remote Sensing 11, 1528); Massimetti et al. 2020; Coppola et al. 2020 (MIROVA, Frontiers in Earth Science 7); Campus et al. 2022 (MODIS → VIIRS continuity); Bato et al. 2021 (Taal InSAR); Theys et al. 2017 (TROPOMI SO2). No Philippine multi-sensor review was found [U].

## 9. Safety and honesty rules (product scope, not footnotes)

1. Header on every page: "A retrospective record, 2000–2026. Not a monitoring or warning service. DOST-PHIVOLCS is the sole authority for alert levels and advisories", with a link to `https://www.phivolcs.dost.gov.ph/` and the bulletin list.
2. No live feeds; a dated snapshot ("Data through 2026-09-30") on every chart; no "current" alert level; alert-level *history* ends at the snapshot and is labelled "as reported by PHIVOLCS on <date>".
3. Series labelled by instrument and quantity: "TROPOMI SO2 column mass in a 50 km box (satellite, afternoon overpass, cloud-limited; coverage 62 %)" beside "PHIVOLCS SO2 flux (ground DOAS, t/day)"; "thermal detections within 10 km (MODIS/VIIRS; includes vegetation fires)"; "LOS displacement (InSAR; atmospheric artefacts likely in the tropics)".
4. Exposure as "population within N km (WorldPop 2020)".
5. Required notices reproduced: Copernicus, LiCSAR, NASA FIRMS/LANCE disclaimer, GVP citation, ISC citation, MIROVA Dataset CC BY, DOST-PHIVOLCS for every ground number with the bulletin link.
6. Hazard layers from HazardHunterPH or GISWEB are linked, never embedded.
7. No forecasting language anywhere, in either language; the Japanese text follows the same rules.

## 10. Free tiers (re-verified 2026-10-21; details in [`research/platform-limits.md`](research/platform-limits.md))

| Platform | Limit that matters here |
|---|---|
| Earth Engine noncommercial (Community tier, since 2026-04-27) | **150 EECU-hours a month per project**, soft (restricted mode beyond); 2 concurrent batch tasks; 100 MiB computed result; exports to Drive or EE assets only without billing. The one-off backfill is estimated at a few EECU-hours [U]; the GEE service account from Lights (project `lgu-lights`) shares that project's quota, so a separate project is proposed (OPEN-QUESTIONS Q11) |
| GitHub Actions | public repo minutes free; 4 vCPU / 16 GB / 14 GB SSD; 6 h per job; private archive repo shares 2,000 min a month |
| Cloudflare Pages | 25 MiB per file, 20,000 files, 500 builds a month; static requests unlimited |
| GitHub Pages / Hugging Face | 1 GB site, 100 GB a month soft / best-effort public storage, Range requests work |
| Neon free | 1 GB per project, PostGIS 3.6 (only if the Java API milestone is built) |
| Render free | sleeps after 15 min; overages bill since a card is on file (only if the Java API milestone is built; edge-cache everything) |

## 11. Runner-up outlines

- **Earthquakes (candidate 6):** USGS + ISC + PHIVOLCS catalogues, GEM faults, ShakeMaps for damaging events, NCEI tsunamis, WorldPop and buildings for exposure; no Earth Engine; everything under 100 MB; see [`research/earthquakes-faults.md`](research/earthquakes-faults.md). About 70 % of its ingestion (USGS, PHIVOLCS crawl, exposure rings, boundaries) is built by the volcano project anyway.
- **Subsidence (candidate 2):** LiCSAR Manila frames + LiCSBAS in staged Actions jobs, JRC surface water, PhilSA flood shapefiles, tide gauge, GHSL growth; see [`research/subsidence-insar.md`](research/subsidence-insar.md). The LiCSBAS tooling built for the Taal InSAR milestone would carry over.
