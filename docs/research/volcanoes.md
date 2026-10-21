<!-- Research notes gathered 2026-10-21 for docs/CANDIDATES.md. Kept as evidence: every claim has its URL and access date; [U] marks unverified items. The comparison and the plan are in the parent folder. -->

# Philippine volcanoes: data-visualisation project research dossier

Research date: 2026-10-21 (all URLs accessed that day unless stated). Method: WebSearch, WebFetch, and small `curl` probes (text-only, a few KB to a few hundred KB; one WFS CSV of 40 KB). No accounts, no code written, nothing installed.

Marking: **[U]** = not verified on a primary page (taken from a search snippet, a secondary page, my own derivation, or blocked pages). Where I quote, the text is verbatim from the page fetched.

Fetch failures to know about (they shape what is verified):

- `volcano.si.edu` (Smithsonian GVP) and `www.si.edu/termsofuse` returned HTTP 403 / a Cloudflare "Smithsonian site temporarily unavailable" or "Request verification" page on every attempt (WebFetch and curl with a browser user agent). Only its GeoServer WFS at `webservices.volcano.si.edu` answered. So GVP citation/terms wording is **[U]** below, from a search-engine snippet of `https://volcano.si.edu/gvp_cite.cfm`.
- `wovodat.phivolcs.dost.gov.ph` (PHIVOLCS-LAVA portal, bulletin list, data-request page) failed TLS verification ("unable to verify the first certificate") and, with verification disabled, returned HTTP 500 "An internal server error occurred." on all four pages probed.
- `www.georisk.gov.ph` failed TLS verification in WebFetch; curl with verification disabled worked. `faultfinder.phivolcs.dost.gov.ph` returned an empty body (JavaScript app).
- `volcanodiscovery.com`, `foi.gov.ph` request pages, Wiley, ESS Open Archive, `hub.worldpop.org` detail pages and `data.humdata.org` dataset pages returned 403 to WebFetch (HDX answered through its CKAN API instead).
---

## 1. PHIVOLCS: what is public and machine-readable

### 1.1 The website and navigation

The PHIVOLCS site (`https://www.phivolcs.dost.gov.ph/`) is a WordPress site. Its navigation (fetched 2026-10-21) links: "Latest Volcano Bulletin" to `https://wovodat.phivolcs.dost.gov.ph/bulletin/list-of-bulletin`; "Volcanoes of the Philippines" to `https://www.phivolcs.dost.gov.ph/volcanoes-of-the-philippines/`; "Volcano Alert Levels" to `https://www.phivolcs.dost.gov.ph/volcano-alert-levels/`; "Eruption History" to WOVODAT; "Local Active Volcanoes Archive (LAVA)" to `https://wovodat.phivolcs.dost.gov.ph/`; "Request for Volcano Data" to `https://wovodat.phivolcs.dost.gov.ph/docs/data-request`; volcano hazard maps to `https://www.phivolcs.dost.gov.ph/volcano-hazard/` and `https://www.phivolcs.dost.gov.ph/gis-web-hazard-maps/`; earthquake information to `https://earthquake.phivolcs.dost.gov.ph/`; a catalogue earthquake data request form (tinyurl); and an FOI seal linking to `https://www.foi.gov.ph/agencies/phivolcs/`. The footer carries the agency address and contacts only. **No copyright notice, terms of use, privacy policy or disclaimer appears on the home page, on bulletin pages, or on the hazard-map pages** (checked: home, `taal-volcano-bulletin-14-march-2022-8-00-am`, `kanlaon-volcano-eruption-bulletin-08-april-2025-02-00-pm`, `volcano-hazard`, `gis-web-hazard-maps`). The only policy text is the WCAG 2.0 accessibility statement.

The 2020–2022 search-engine snippets show older URL slugs such as `https://www.phivolcs.dost.gov.ph/taal-volcano-bulletin-25-january-2020-8-00-a-m/` still resolve (fetched; see 1.3).

### 1.2 Active volcano list (24)

`https://www.phivolcs.dost.gov.ph/volcanoes-of-the-philippines/` lists 24 active volcanoes: Babuyan Claro, Banahaw, Biliran (Anas), Bud Dajo, Bulusan, Cabalian, Cagua, Camiguin de Babuyanes, Didicas, Hibok-hibok, Iraya, Iriga, Isarog, Kanlaon, Leonard Kniaseff, Makaturing, Matutum, Mayon, Musuan (Calayo), Parker, Pinatubo, Ragang, Smith, Taal. Definitions quoted from the page: Active = "Erupted within historical times (within the last 600 years), accounts of these eruptions were documented by man" and "erupted within the last 10,000 years based on the analyses of material from young volcanic deposits"; Potentially active = "Morphologically young-looking but with no historical or analytical records of eruption"; Inactive = "No recorded eruptions physical form has been intensively weathered and eroded, bearing deep and long gullies." The page gives no names or counts for the potentially-active and inactive classes. Coordinates are not on this page; take them from the GVP WFS (section 2) or PHIVOLCS per-volcano pages [U].

### 1.3 Daily volcano bulletins: format, fields, archive depth

Format: HTML text (not PDF, not image). Two generations:

- **Up to 2024: "[VOLCANO] VOLCANO BULLETIN dd Month yyyy 8:00 A.M."**, one prose paragraph of monitoring data, one alert-level paragraph, one recommendations paragraph, signed "DOST-PHIVOLCS". Example (Taal, 14 March 2022, `https://www.phivolcs.dost.gov.ph/taal-volcano-bulletin-14-march-2022-8-00-am/`): nine volcanic earthquakes in 24 h including eight volcanic tremor events of 2–5 minutes and one low-frequency earthquake; plumes 2,200 m tall drifting southwest; "SO2 ... averaged 14,524 tonnes/day on 13 March 2022"; crater-lake temperature 63.7 °C (last measured 25 February 2022); ground deformation "Based on electronic tilt, continuous GPS, and InSAR monitoring, the island and region have been deflating since October 2021"; Alert Level 2 (Increased Unrest); recommendations (PDZ entry prohibited; aviation advisory). Example (Taal, 25 January 2020, `https://www.phivolcs.dost.gov.ph/taal-volcano-bulletin-25-january-2020-8-00-a-m/`): "Sulfur dioxide (SO2) emission was measured at an average of 409 tonnes/day. The Philippine Seismic Network (PSN) plotted a total of seven hundred forty-four (744) volcanic earthquakes since 1:00 PM, January 12, 2020 ... the Taal Volcano Network ... recorded four hundred twenty (420) volcanic earthquakes including eleven (11) low-frequency earthquakes ... Alert Level 4 still remains in effect over Taal Volcano."
  Fields recoverable by text parsing: volcanic earthquake count (and sub-types: volcanic tremor, low-frequency, hybrid; tremor durations), plume height (m) and drift direction, SO2 flux (tonnes/day) with its measurement date, crater-lake temperature where applicable, a deformation sentence (method named: tilt, cGPS, EDM, InSAR; "inflation/deflation since …"), alert level and its label, danger-zone radius, recommendations. Numbers are embedded in prose with spelled-out numerals in parentheses, so a parser is needed per volcano and era.
- **Since 2025: "[Volcano] Volcano Summary of 24Hr Observation dd Month yyyy 12:00 AM"**, posted in English and in Filipino ("BULKANG TAAL Buod ng 24 oras na pagmamanman …"). On the page I fetched (`https://www.phivolcs.dost.gov.ph/taal-volcano-summary-of-24hr-observation-09-july-2025-12-00-am/`) the WordPress `entry-content` block is **empty in the served HTML**; the body appears to be injected client-side or hosted on the WOVOdat portal (the page links to `https://wovodat.phivolcs.dost.gov.ph/bulletin/list-of-bulletin`, which was down). So the 2025+ daily summaries are **not** reliably scrapeable from static HTML [U until the WOVOdat portal is checked].
- **Eruption bulletins** (e.g. `https://www.phivolcs.dost.gov.ph/kanlaon-volcano-eruption-bulletin-08-april-2025-02-00-pm/`) are structured HTML sections: Eruption Data; Monitoring Data Prior to the Eruption; Current Outlook; Recommendations. Example values: "moderately explosive eruption" at 05:51 AM, 56 minutes; plume to 4,000 m; PDCs within ~1 km on the southern slopes; "Alert Level 3 (magmatic unrest) therefore remains over Kanlaon Volcano"; "communities within a 6-km radius of the summit crater remain evacuated".

Archive depth on the WordPress site: the category listing `https://www.phivolcs.dost.gov.ph/category/volcano-bulletin/` paginates to **page 1,498** (page 1,499 returns 404; probed 2026-10-21). The last page's titles are "BULUSAN VOLCANO BULLETIN 04 September 2017", "KANLAON VOLCANO BULLETIN 04 September 2017", "MAYON VOLCANO BULLETIN 03 September 2017", down to "MAYON VOLCANO BULLETIN 02 September 2017". So the online bulletin archive starts **2 September 2017** and holds roughly 1,498 × 10 ≈ 15,000 posts (bilingual since 2025) [U for the exact count]. Bulletins before September 2017 are not on the website; they would have to come from the WOVOdat/LAVA portal, from GVP weekly/monthly reports, or by request.

### 1.4 Alert levels and alert-level history

`https://www.phivolcs.dost.gov.ph/volcano-alert-levels/` documents the 0–5 schemes per volcano (they differ: Taal 0 Normal / 1 Low-Level Unrest / 2 Increasing Unrest / 3 Intensified or Magmatic Unrest / 4 Hazardous Eruption Imminent / 5 Highly Hazardous Eruption in Progress; Mayon 0 No Alert / 1 Abnormal / 2 Increasing Unrest / 3 Increased Tendency Toward Hazardous Eruption / 4 Hazardous Eruption Imminent / 5 Hazardous Eruption; Kanlaon and Bulusan use a general scheme with PDZ radii growing from 4 km at Level 0 to 14 km at Level 5 for Kanlaon; Pinatubo and Hibok-hibok have their own). **No alert-level history table is published**; the history must be reconstructed from bulletins (daily since Sept 2017 on the site) and from GVP weekly reports for earlier years [U].

### 1.5 Earthquake information

`https://earthquake.phivolcs.dost.gov.ph/` is an HTML table with columns "Date - Time (Philippine Time)", "Latitude (ºN)", "Longitude (ºE)", "Depth (km)", "Mag", "Location" (e.g. "004 km N 35° E of City Of Alaminos (Pangasinan)"). Each row links to an HTML event page, e.g. `https://earthquake.phivolcs.dost.gov.ph/2026_Earthquake_Information/October/2026_1021_0855_B1.html`, with fields: Date/Time "21 Oct 2026 - 04:55:22 PM"; Location "16.18°N, 120.00°E - 004 km N 35° E of City Of Alaminos (Pangasinan)"; "Depth of Focus" 001 km; Origin "TECTONIC"; Magnitude "Ms 2.4" (so the magnitude type is on the event page, surface-wave Ms here; the list page shows only "Mag"); Reported Intensities; Expecting Damage "NO"; Expecting Aftershocks "NO"; an epicentral-map JPG. Note on the event page: "Always refer to the latest earthquake information posted at the PHIVOLCS official website".

Monthly archive pages exist at `https://earthquake.phivolcs.dost.gov.ph/EQLatest-Monthly/YYYY/YYYY_Month.html`: January 2016 (HTTP 200, 523 KB), February 2016 (200), June 2016 (404), December 2015 (404), January 2018 (200, 551 KB), January 2025 (200, 2.78 MB, about 1,459 table rows, i.e. ~1,450 located events in the month). So the machine-readable PHIVOLCS catalogue online runs from **2016, with gaps** (a GitHub scraper notes "Around year 2016, there are missing data since the website returns an error 404", `https://github.com/DaijobuDes/phivolcs-dataset`, CC0-1.0, columns not stated). No API, no CSV, no bulk file. FOI precedent (search snippets, pages 403) [U]: a 2000–2023 annual-data request was answered by pointing to the website; a time-history data request was denied.

### 1.6 APIs and open-data portals

- **data.gov.ph**: the home page served only its title to WebFetch; no PHIVOLCS dataset was found by search [U: unverified absence].
- **HazardHunterPH** (`https://hazardhunter.georisk.gov.ph/`): "the country's one-stop shop for hazard assessment"; "All hazard information used for assessment has been generated by government agencies"; partners DOST (PCIEERD, PHIVOLCS, PAGASA, ASTI), DENR-MGB, DENR-NAMRIA, DND-OCD, DepEd, DOH. Footer "© 2018 - 2020 DOST-PHIVOLCS, All rights reserved". It links to a downloads page on `gisweb.phivolcs.dost.gov.ph`. **No ArcGIS REST, WMS or WFS endpoint is documented.** Terms of use (`https://hazardhunter.georisk.gov.ph/terms-of-use`), verbatim: "Unless otherwise stated, HazardHunterPH and/or it's licensors own the intellectual property rights for all material on HazardHunterPH. All intellectual property rights are reserved. You may view and/or print pages from https://hazardhunter.georisk.gov.ph/ for your own personal use subject to restrictions set in these terms and conditions. You must not: Republish material from https://hazardhunter.georisk.gov.ph/ Sell, rent or sub-license material from https://hazardhunter.georisk.gov.ph/ Reproduce, duplicate or copy material from https://hazardhunter.georisk.gov.ph/ Redistribute content from HazardHunterPH (unless content is specifically made for redistribution)." (It is a boilerplate template: it even reads "subject to, prevailing law of ." with the jurisdiction blank.)
- **GeoRiskPH** (`https://www.georisk.gov.ph/`, curl with TLS verification off): platforms HazardHunterPH, GeoAnalyticsPH, GeoMapperPH, "GeoRiskPH API Hub" (brand "Map And Features"), 3D Earth Risk, PlanSmart (Ready to Rebuild; Safe Schools). The site says "Request an account"; `https://data.georisk.gov.ph/` is a login page ("3DPH Information Systems"). The API hub is therefore account-gated; its terms were not reachable [U].
- **PHIVOLCS GISWEB** (`https://gisweb.phivolcs.dost.gov.ph/`): "PHIVOLCS GeoHazards Portal is still undergoing construction"; links FaultFinder, a Google Form to "download available earthquake & volcanic hazard maps", and a Geoportal at `geoportal.phivolcs.dost.gov.ph:8080/maps/` (1:50,000 quadrangle maps). The download page `https://gisweb.phivolcs.dost.gov.ph/gisweb/earthquake-volcano-related-hazard-gis-information` has a Login button and region/province/city/barangay selectors and these volcano layers: "Active & Potentially Active Volcanoes, Ballistic projectile, Fissure, Lahar, Lava flow, Permanent Danger Zone, Pyroclastic Flow, Volcanic Tsunami" (earthquake layers: Earthquake-induced Landslide, Ground Rupture (Active Fault), Ground Shaking, Liquefaction, Tsunami; others: Deep-Seated Landslide, PGA, Risk Maps, Spectral Acceleration). `https://www.phivolcs.dost.gov.ph/gis-web-hazard-maps/` says the downloads are KMZ: "Click the kmz files, which will be downloaded automatically", also available "in the HazardHunterPH app under 'Download Maps'"; "These maps may be revised as new information becomes available."
- **PHIVOLCS-LAVA / WOVOdat portal** (`https://wovodat.phivolcs.dost.gov.ph/`, alt host `https://volcano.phivolcs.dost.gov.ph/` which answered HTTP 200 on the root only): search snippets say it "lets users search, view, or download monitoring data on volcanic seismicity, ground deformation, gas, visual and other parameters", with a time-series visualiser and a volcano catalogue, and that PHIVOLCS "added online forms for ... volcanic SO2 flux measurements using campaign spectrometery" [U; portal returned HTTP 500 on all pages on 2026-10-21]. This is the single most important thing to re-check: if LAVA exposes SO2 flux and earthquake-count downloads, the ground-truth series exist in machine-readable form.

### 1.7 Terms, copyright and Philippine law

- PHIVOLCS website: no copyright or terms text (see 1.1). HazardHunterPH: all rights reserved, no republishing (1.6). PHIVOLCS Philippine Fault Zone maps page (`https://www.phivolcs.dost.gov.ph/philippine-fault-zone-maps/`): "now available on this website and upon request to PHIVOLCS-DOST"; "The authors have made reasonable efforts to ensure the accuracy of the maps based on available data"; "Use of the active faults map in this website can be cited as:" Tsutsumi and Perez (2013), Active Fault Research 39, 29–37.
- **RA 8293 (Intellectual Property Code)**, from `https://lawphil.net/statutes/repacts/ra1997/ra_8293_1997.html`: Sec. 171.11: a "work of the Government of the Philippines" is "a work created by an officer or employee of the Philippine Government or any of its subdivisions and instrumentalities, including government-owned or controlled corporations as a part of his regularly prescribed official duties." Sec. 176.1: "No copyright shall subsist in any work of the Government of the Philippines. However, prior approval of the government agency or office wherein the work is created shall be necessary for exploitation of such work for profit. Such agency or office may, among other things, impose as a condition the payment of royalties." Sec. 176.3: the Government may hold copyrights "transferred to it by assignment, bequest or otherwise".
  Reading for this project: bulletin text, counts and SO2 numbers are government works without copyright; a non-profit portfolio site needs no approval; anything "for profit" would. HazardHunterPH's contractual terms are a separate restriction on that site's material (and the maps may include third-party-contributed layers), so do not re-serve its layers.

### 1.8 Is there a PHIVOLCS SO2 flux dataset anywhere?

- **NOVAC database**: "SO2 flux of MAYON volcano, from the NOVAC data-base", DOI 10.17196/NOVAC.MAYON.001 (`https://researchdata.se/en/catalogue/dataset/doi-10-17196-novac-mayon-001`), contributor "Philippine Institute of Volcanology and Seismology & Earth Observatory of Singapore", creators include Bornas, Arellano, Costa, Newhall, Galle; "daily statistics of total SO2 emission from the volcano" from scanning mini-DOAS; licence URL `https://creativecommons.org/licenses/by/4.0/`; "publicly available on the condition that credit is given according to the NOVAC Data Use Agreement"; years, format and size not stated on the record [U].
- **WOVOdat (global)** (`https://wovodat.org/`): PHIVOLCS is a listed contributor; "The Pinatubo 1991 Plinian eruption data is available at WOVOdat"; site has Login/Register and a Data Policy page (not read) [U for Taal/Mayon/Kanlaon coverage].
- **PHIVOLCS bulletins** carry daily SO2 flux (t/day, e.g. 409 on 25 Jan 2020; 14,524 on 13 Mar 2022) since at least 2017 online; news reports relay them (Taal record "18,638 metric tons per day" [U, Inquirer snippet]).
- **GVP weekly reports** relay PHIVOLCS numbers (section 2) [U because the GVP site was blocked].
- **PHIVOLCS-LAVA** may offer direct downloads (1.6) [U].

---

## 2. Smithsonian Global Volcanism Program (GVP)

### 2.1 Database, version, terms

Citation format (search snippet of `https://volcano.si.edu/gvp_cite.cfm`) [U verbatim]: "Global Volcanism Program, 2025. [Database] Volcanoes of the World (v. 5.3.0; 17 Jul 2025). Distributed by Smithsonian Institution, compiled by Venzke, E. https://doi.org/10.5479/si.GVP.VOTW5-2025.5.3"; a snippet of `https://volcano.si.edu/gvp_votw.cfm?vn=283003` shows "v. 5.3.4 (30 Dec 2025)" [U]. Terms (same snippet) [U]: all GVP material "is governed by the Smithsonian Terms of Use", which "invites visitors to use its online content for personal, educational, and other non-commercial purposes"; for general references cite "Global Volcanism Program, Smithsonian Institution" with a link. UN-SPIDER's catalogue entry (`https://www.un-spider.org/links-and-resources/data-sources/global-volcanism-program-database-gvp-smithsonian-institution`) lists cost "free", export "xml", and an older required citation "Global Volcanism Program, 2013. Volcanoes of the World, v. 4.7.6."

Practical reading: free for a non-commercial portfolio with citation; **not an open licence** (no CC); redistribution of a bulk copy should be avoided; show derived figures and link back.

### 2.2 Web services (verified by probe)

GeoServer WFS at `https://webservices.volcano.si.edu/geoserver/GVP-VOTW/ows?service=WFS&version=2.0.0&request=GetCapabilities` (259 KB capabilities). Capabilities state `<ows:Fees>NONE` and `<ows:AccessConstraints>NONE`. Feature types include `GVP-VOTW:Smithsonian_VOTW_Holocene_Volcanoes` (1,214 features), `GVP-VOTW:Smithsonian_VOTW_Holocene_Eruptions` (11,089), `GVP-VOTW:Smithsonian_VOTW_Pleistocene_Volcanoes`, `GVP-VOTW:E3WebApp_Eruptions1960`, `GVP-VOTW:E3WebApp_HoloceneVolcanoes`, `GVP-VOTW:E3WebApp_Emissions` (this one threw a server IOException on GetFeature). CSV, GeoJSON and CQL filters work (`outputFormat=csv&CQL_FILTER=Country='Philippines'`). The HTML page `https://volcano.si.edu/database/webservices.cfm` (and the "Database Download" xlsx) could not be fetched [U].

Holocene volcano fields: `Volcano_Number, Volcano_Name, Volcanic_Landform, Primary_Volcano_Type, Last_Eruption_Year, Country, Region, Subregion, Geological_Summary, Latitude, Longitude, Elevation, Tectonic_Setting, Geologic_Epoch, Evidence_Category, Primary_Photo_Link/Caption/Credit, Major_Rock_Type, GeoLocation`.

Eruption fields: `Volcano_Number, Volcano_Name, Eruption_Number, Activity_Type (Confirmed/Uncertain Eruption), ExplosivityIndexMax (VEI), ExplosivityIndexModifier, ActivityArea, ActivityUnit, StartEvidenceMethod, StartDateYearModifier, StartDateYear, StartDateYearUncertainty, StartDateDayModifier, StartDateMonth, StartDateDay, StartDateDayUncertainty, EndDateYearModifier, EndDateYear, EndDateYearUncertainty, EndDateDayModifier, EndDateMonth, EndDateDay, EndDateDayUncertainty, GeoLocation`. Dating uncertainty is therefore explicit (year ± and day ± fields, "?" and "P" modifiers), e.g. Melebingoy 1640-12-26 ±5 days, VEI 5?.

`E3WebApp_Eruptions1960` fields: `VolcanoNumber, VolcanoName, ExplosivityIndexMax, StartDate, StartDateYear/Month/Day, EndDate, EndDateYear/Month/Day, ContinuingEruption, LatitudeDecimal, LongitudeDecimal, Activity_ID`.

### 2.3 Philippines in GVP (verified by WFS CSV)

23 Holocene volcanoes with `Country='Philippines'`: Melebingoy (271011, Parker; last 1641), Matutum (271020; 1290), Leonard Range (271031; 80 CE), Makaturing (271040; 1882), Ragang (271060; 1916), Musuan (271070; evidence uncertain), Camiguin (271080, Hibok-Hibok; 1953), Kanlaon (272020; 2026), Cabalían (272050; 1820), Biliran (272080; 1939), Bulusan (273010; 2025), Mayon (273030; 2026), Iriga (273041), Isarog (273042; −3500), Banahaw (273050), San Pablo Volcanic Field (273060; 1350), Taal (273070; 2026), Pinatubo (273083; 2021), Cagua (273090; 1860), Camiguin de Babuyanes (274010; 1857), Didicas (274020; 1978), Babuyan Claro (274030; 1924), Iraya (274060; 1454). The PHIVOLCS 24 and GVP 23 differ in membership (GVP lacks Bud Dajo, Smith; has San Pablo VF; names differ: Parker→Melebingoy, Leonard Kniaseff→Leonard Range, Hibok-hibok→Camiguin).

Eruption rows: 215 for volcano numbers 271000–273999; **233 including the Babuyan group (274xxx)**. Of the 215: VEI distribution blank 30, VEI 0: 4, 1: 36, 2: 101, 3: 28, 4: 9, 5: 2, 6: 5; 198 confirmed, 17 uncertain; 104 start in 1900 or later, 41 in 2000 or later, 192 in 1600 or later; 122 have an end date; 51 have a day uncertainty and 19 a year uncertainty. Most-listed: Mayon 69, Taal 40, Kanlaon 33, Bulusan 26, Ragang 9, Pinatubo 9. Recent rows (as of 2026-10-21): Mayon 2018-01-13 VEI 3 (to 2019-07-31); Taal 2020-01-12 VEI 4 (to 2020-01-22); Taal 2021-07-01 VEI 1; Taal 2021-11-15 VEI 2 (to 2022-04-01); Pinatubo 2021-11-30 VEI 1; Bulusan 2022-06-05 VEI 2; Mayon 2022-06-06 VEI 0; Taal 2022-10-05 VEI 1; Mayon 2023-04-27 VEI 2 (to 2024-02-04); Taal 2024-04-12 VEI 2 (to 2026-03-16); Mayon 2024-05-30 VEI 2; Kanlaon 2024-06-03 VEI 3; Kanlaon 2024-10-19 VEI 3 (to 2026-03-25); Bulusan 2025-04-28 VEI 2; Mayon 2026-01-06 (to 2026-03-25).

### 2.4 Weekly reports

`https://volcano.si.edu/reports_weekly.cfm` could not be fetched (Cloudflare). From general knowledge, the Smithsonian/USGS Weekly Volcanic Activity Report summarises PHIVOLCS bulletins each week, including SO2 t/day, earthquake counts, plume heights and alert levels, in HTML with per-volcano archives back to 2000 [U]. Wikipedia's Kanlaon article cites GVP for eruptive history (section 8). No bulk download of weekly reports is known [U]; the E3 "Emissions" layer exists in WFS but errored.

---

## 3. Sentinel-5P TROPOMI SO2

### 3.1 Earth Engine datasets (verified)

- `COPERNICUS/S5P/OFFL/L3_SO2` (`https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_SO2`): availability 2018-12-05 to 2026-10-18; pixel size 1,113.2 m; bands `SO2_column_number_density` (mol/m², "at ground level, from DOAS"), `SO2_column_number_density_15km` (mol/m², "ingested only when solar zenith angle < 70"), `SO2_column_number_density_amf`, `SO2_slant_column_number_density`, `cloud_fraction`, `absorbing_aerosol_index`, four geometry bands. QA is applied at ingestion ("qa_value above 0.5", plus solar zenith < 60 and cloud fraction criteria). Note: "negative column values are often seen over clean regions"; filter only values below −0.001 mol/m². Terms verbatim: "The use of Sentinel data is governed by the Copernicus Sentinel Data Terms and Conditions." No formatted citation given.
- `COPERNICUS/S5P/NRTI/L3_SO2`: 2018-07-10 to 2026-10-20; same bands; "The 15km SO2 band is ingested only when solar_zenith_angle < 70".
- **Only two heights are on GEE: ground-level/boundary-layer and 15 km.** The L2 product also carries 7 km and 1 km a priori box-profile columns [U: the ESA product pages `sentinel.esa.int`/`sentinels.copernicus.eu` were unreachable; `https://sentiwiki.copernicus.eu/web/s5p-products` only lists L2__SO2___ with PUM/ATBD links].

### 3.2 Licence (verified)

Copernicus Sentinel data licence, mirrored at `https://ads.atmosphere.copernicus.eu/licences/ec-sentinel`: "users shall have a free, full and open access to Copernicus Sentinel Data"; permitted uses "reproduction", "distribution", "communication to the public", "adaptation, modification and combination with other data and information"; attribution "Contains modified Copernicus Sentinel data [Year]"; "without any express or implied warranty, including as regards quality and suitability for any purpose". The Copernicus Data Space terms page (`https://dataspace.copernicus.eu/terms-and-conditions`) confirms "The access and use of Copernicus Sentinel data is available on a free, full and open basis".

### 3.3 What a column is, versus PHIVOLCS flux

- TROPOMI gives a **vertical column density** (mol/m², often shown in Dobson Units) per ~3.5 × 5.5 km pixel at one overpass per day (~13:30 local); PHIVOLCS gives a **flux** (tonnes/day) from ground scanning DOAS (campaign or NOVAC-style), integrating gas crossing a traverse with wind speed. The two are related only through plume transport (flux ≈ column × plume width × wind speed), so a daily "SO2 mass in a 50 km box" from GEE is a proxy, not the same quantity. Retrieval basics: Theys et al. 2017, AMT 10, 119 (`https://amt.copernicus.org/articles/10/119/2017/`): "The spectral fitting is performed using the differential optical absorption spectroscopy (DOAS) method", "pixel size of 7 km × 3.5 km at nadir" (5.5 × 3.5 km since August 2019 [U]); air-mass factors use "a set of representative a priori profiles". Detection limit: weak passive degassing (hundreds of t/day) sits near the noise floor; only eruptive or strong degassing (thousands of t/day, as at Taal 2021–22 and Kanlaon 2024–25) gives clear daily signals [U; the AMT page did not state a DU noise figure]. Cloud: tropical convective cloud over Luzon/Negros removes many afternoon pixels (`cloud_fraction` band; GEE already drops cloud fraction > 0.3 at ingestion). Plume height matters: the 15 km band suits explosive plumes (Taal Jan 2020), the ground-level band suits passive degassing.
- Known uses: Taal 2020 — ESA planned 6-day Sentinel-1 repeats and TROPOMI tracked the plume [U, search snippets]; MOUNTS runs daily TROPOMI SO2 for Taal, Mayon, Kanlaon and Bulusan (3.4).### 3.4 MOUNTS (verified by probe)

`http://www.mounts-project.com/` (port 443 refused connections; port 80 works). Home map has 100 `/timeseries/<GVP number>` links; Philippine entries: Kanlaon (272020), Bulusan (273010), Mayon (273030), Taal (273070). Bulusan page (`/timeseries/273010`): "Monitoring priority: medium"; Sentinel-1 "product type: IW L1 SLC - downloaded products: orbit [69]"; Sentinel-2 "Level-1C - downloaded products: all available"; Sentinel-5P "NRTI L2 SO2 - downloaded products: all available"; time series with linked images (wrapped/unwrapped interferograms, coherence, intensity; S2 infrared + detections; SO2 PBL images, e.g. `bulusan_20261020T0552_SO2_PBL.png`). **No CSV/JSON download links on the time-series page.** About page cites Valade et al. 2019, Remote Sensing 11, 1528 (DOI 10.3390/rs11131528) and Massimetti et al. 2020 (DOI 10.3390/rs12050820). No licence statement found on the site [U].

---

## 4. Thermal anomalies

### 4.1 MIROVA (verified by probe)

`https://www.mirovaweb.it/NRT/` (University of Turin, contact diego.coppola@unito.it). Volcano list (`/NRT/volcanoes.php`) has 176 volcanoes; Philippine entries: Kanlaon (272020), Mayon (273030), Taal (273070), Pinatubo (273083); **Bulusan and Hibok-Hibok are not listed.** Kanlaon page (`/NRT/volcanoDetails_MOD.php?volcano_id=272020`): sensors MODIS, VIIRS750, VIIRS375, Combined MIR; "Log VRP", "Linear VRP", "Max Distance", "Google Earth (.kmz)"; "The Volcanic Radiative Power (VRP) is calculated using the MIR-method with a lower detection limit of about 1 MW. Data are processed in Near Real Time, that is within 1-4 hours from image acquisition." No CSV link on the page.

Site terms (`/NRT/credits.php`), verbatim: "All original content on this website ... is property of MIROVA and is released under the following conditions: Free to copy, share, and quote for non-commercial purposes with appropriate attribution to MIROVA. Not permitted to alter, transform, or use for commercial purposes without explicit permission." Disclaimer: "All data and content on the MIROVA website are provided 'as is.'"

**Better route: the "MIROVA Dataset V2.5"** dashboard (`https://www.mirovaweb.it/ARCHIVE/Explore_Archive.php`) links an OSF repository `https://osf.io/zm62w/` (DOI 10.17605/OSF.IO/ZM62W), a user guide PDF and a Scientific Data paper (DOI 10.1038/s41597-026-08100-7; page redirected to a login so contents unverified [U]). The OSF API (`https://api.osf.io/v2/nodes/zm62w/?embed=license`) returns title "MIROVA Dataset", description "A Global Dataset of volcanic thermal anomalies detected through the MIROVA system", modified 2026-08-19, **licence "CC-By Attribution 4.0 International"**. The dashboard's volcano selector includes Kanlaon, Mayon, Pinatubo and (by the same list) Taal. So VRP time series for the main Philippine volcanoes are available as CC BY 4.0 data via OSF (file formats and sizes unverified [U]).

### 4.2 NASA FIRMS (verified)

- API (`https://firms.modaps.eosdis.nasa.gov/api/`, version 4.2.1): endpoints `area`, `data_availability`, `kml_fire_footprints`, `map_key`, `missing_data` (country endpoint "currently not available"). Area pattern (`/api/area/`): `/api/area/csv/[MAP_KEY]/[SOURCE]/[AREA_COORDINATES]/[DAY_RANGE]` and `.../[DAY_RANGE]/[DATE]`; sources `MODIS_NRT, MODIS_SP, VIIRS_SNPP_NRT, VIIRS_SNPP_SP, VIIRS_NOAA20_NRT, VIIRS_NOAA20_SP, VIIRS_NOAA21_NRT, VIIRS_NOAA21_SP, LANDSAT_NRT` (US/Canada only); area as `west,south,east,north`; day range 1 to 5; "MAP_KEY limit is 5000 transactions / 10-minute interval" (a 7-day request counts as more than one transaction).
- Archive download (`https://firms.modaps.eosdis.nasa.gov/download/`): "shapefiles (.shp), comma-separated text files (.csv) or JSON files (.json)"; Earthdata Login or emailed code; coverage MODIS Collection 6.1 from 1 November 2000, VIIRS S-NPP 375 m from 20 January 2012, VIIRS NOAA-20 from 1 April 2018, VIIRS NOAA-21 from 1 March 2023, Landsat 30 m from 20 June 2022 (the FAQ gives NOAA-20 from 1 Jan 2020 and NOAA-21 from 17 Jan 2024: inconsistent, treat as [U]); "Near Real-Time (NRT) data are replaced with standard science quality data as they become available (with approximately a 5 month lag)"; delivery by email; a "yearly summary by country [.csv]" exists.
- Attributes (`https://www.earthdata.nasa.gov/data/tools/firms/active-fire-data-attributes-modis-viirs`): MODIS `latitude, longitude, brightness (K, ch 21/22), scan, track, acq_date, acq_time (UTC), satellite (A/T), confidence 0–100, version, bright_t31, frp (MW), daynight (D/N), type`; `type`: "0 = presumed vegetation fire", "1 = active volcano", "2 = other static land source", "3 = offshore", footnote "This attribute is only available for MCD14ML (standard quality) data". VIIRS: `bright_ti4`, `bright_ti5`, confidence low/nominal/high.
- Caveats (FAQ `https://www.earthdata.nasa.gov/data/tools/firms/faq`): "While both the MODIS and VIIRS algorithms routinely detect active volcanoes, the active fire products have not been validated against independent data for their ability to detect volcanoes. There is a separate near-real time MODIS product, MODVOLC, specifically for volcanoes."; "Different types of thermal anomalies are not currently attributed in the NRT MODIS or VIIRS data." So **fire products pick up lava, hot PDC deposits, crater glow, but also agricultural burning and forest fires (Kanlaon April 2025 "wildfires near the crater", section 8).** Filter by `type=1` only in SP data, and by distance/elevation to the crater.
- Policy: FAQ "NASA promotes [full and open sharing of data]"; caption credit "NASA FIRMS"; GEE FIRMS page: "NASA promotes the full and open sharing of all data with the research and applications communities" and asks to "replicate or provide a link to the disclaimer" (LANCE).
- GEE: `FIRMS` (2000-11-01 to 2026-10-19; 1 km daily; bands `T21`, `confidence`, `line_number`; citation DOI 10.5067/FIRMS/MODIS/MCD14DL.NRT.006); `MODIS/061/MOD14A1` (2000-02-24 onward, 1 km daily, `FireMask` 7/8/9 = low/nominal/high-confidence fire, `MaxFRP` MW, `sample`, `QA`; terms "MODIS data and products acquired through the LP DAAC have no restrictions on subsequent use, sale, or redistribution."); `NASA/VIIRS/002/VNP14A1` (2012-01-19 onward, 1 km daily, same FireMask classes; LP DAAC: "freely accessible", cite when publishing).

---

## 5. InSAR deformation

### 5.1 COMET LiCSAR (verified by probe)

Portal `https://comet.nerc.ac.uk/comet-lics-portal/`: "Interferograms and coherence maps have been produced automatically"; "Derived Works of Copernicus data", subject to the Copernicus terms (no CC licence stated); acknowledgement requested: "LiCSAR contains modified Copernicus Sentinel data [year]"; cite Lazecký et al. 2020 (Remote Sensing), Morishita et al. 2020 (LiCSBAS), González et al. 2016, Lawrence et al. 2013 (JASMIN). Bulk access: `https://data.ceda.ac.uk/neodc/comet/data/licsar_products/` and `https://gws-access.jasmin.ac.uk/public/nceo_geohazards/LiCSAR_products/`; an October 2025 storage migration means some data only appears under `LiCSAR_products.future` ("temporary"). LiCSBAS: `https://github.com/comet-licsar/LiCSBAS` (`LiCSBAS01_get_geotiff.py` downloads frame products).

Frames covering Philippine volcanoes (found by reading each frame's `metadata/<frame>-poly.txt` polygon on tracks 32, 142 and the orbit-arithmetic neighbours 134, 61, 163, 69, 171, 98; 190 frame polygons read):

| Volcano | Frames (pairs listed, first..last pair) |
|---|---|
| Taal | `032D_07536_111313` (2,888 pairs, 20141019_20141112 .. 20260731_20260812; 374 epochs), `142A_07606_131313` (2,018 pairs, 20141027 .. 20260802) |
| Pinatubo | `032D_07536_111313`, `142A_07411_111313` |
| Mayon | `134D_07688_131313` (1,724 pairs, 20150915 .. 20260831), `061D_07748_050613` (1,589 pairs, 20141021 .. 20260620), `069A_07674_131310` (2,904 pairs, 20180104 .. 20260522) |
| Kanlaon | `134D_07892_131210` (1,845 pairs, 20141014 .. 20260508), `061D_07906_131313`, `069A_07955_090909` (3,877 pairs, 20141010 .. 20260429) |
| Bulusan | `061D_07748_050613`, `069A_07674_131310` |
| Hibok-Hibok | `061D_08107_131313`, `069A_08127_131414` |

The Taal frame has pairs bracketing the 12 January 2020 eruption (e.g. `20200109_20200115`, `20200109_20200121`, `20200115_20200121`). Frame metadata directory holds `geo.E/N/U.tif` (look vectors), `geo.hgt.tif`, `geo.landmask.tif`, `geo.meancoh.*.tif`, `geo.vlos_eur.tif`, `baselines`, `network.png`, `metadata.txt`. **Per-pair file sizes could not be measured**: the pair directories returned 404 on both the current and `.future` paths (migration in progress), so a volume estimate is derived: LiCSAR products are ~0.001° (≈100 m) GeoTIFFs over a ~250 × 250 km frame, i.e. ~2,300 × 2,300 pixels; unwrapped (float32) ≈ 20 MB, wrapped phase and coherence (8-bit) ≈ 5 MB each → ~30 MB per pair → **~85 GB for the Taal descending frame alone** [U]. Not something to mirror; crop, or use the time series.

### 5.2 COMET Volcano Deformation Portal (verified)

`https://comet.nerc.ac.uk/comet-volcano-portal/`: "Worldwide Database of Volcanic Ground Deformation"; tools (displacement time series, profiles, ML probability maps) "are only active for volcanoes where the majority of Sentinel-1 imagery has been processed". Volcano index (`/volcano-index/Search-All`, 208 rows): Taal "Philippines and SE Asia Yes Yes", Pinatubo "Yes Yes", Kanlaon "Yes No", Ambalatungan Group and Amorong "No"; **Mayon and Bulusan absent.** Copyright page (`/comet-volcano-portal/copyright`): "Images used throughout the website are licensed under the Creative Commons Attribution-NonCommercial 4.0 International"; disclaimer: "The information contained in this website is for general information purposes only ... we make no representations or warranties of any kind ... Any reliance you place on such information is therefore strictly at your own risk." Footer "Website designed by CEMAC © 2019 University of Leeds".

### 5.3 ASF HyP3 on-demand InSAR (verified)

`https://hyp3-docs.asf.alaska.edu/using/credits/`: "On Demand users are given a free allotment of 8,000 credits per month to use for processing jobs"; InSAR 80 m (20×4 looks) 10 credits ($0.50 for HyP3+), 40 m 15 credits ($0.75); Burst InSAR 1–110 credits by pairs and resolution; RTC 30 m 5 credits; AutoRIFT 25; implied $0.05 per credit. So ~800 full-scene 80 m interferograms per month free. Products are derived Sentinel-1 data (Copernicus terms, attribution). No reset rule stated on the page.

### 5.4 Sentinel-1 on GEE and CDSE limits (verified)

GEE `COPERNICUS/S1_GRD` (2014-10-03 onward; 10/25/40 m; bands HH/HV/VV/VH in dB, `angle`): "This collection contains all of the GRD scenes" — **GRD only, no SLC, so no InSAR on GEE**. Copernicus Data Space quotas (`https://documentation.dataspace.copernicus.eu/Quotas.html`, general tier): 4 concurrent connections (S3/OData/STAC), monthly transfer 12 TB ("After reaching this monthly transfer limit, the maximum bandwidth drops to 1MB/s"), Sentinel Hub 10,000 requests and 10,000 processing units per month, openEO 12 requests/min. SLC bursts are offered through OData ("Sentinel-1 SLC Bursts" link).

### 5.5 Published InSAR for Taal and Mayon

- Bato, M.G., Lundgren, P.R., Pinel, V., Solidum, R., Daag, A., Cahulogan, M. (2021), "The 2020 Eruption and Large Lateral Dike Emplacement at Taal Volcano, Philippines: Insights From Satellite Radar Data", Geophysical Research Letters 48, e2021GL092803, DOI 10.1029/2021GL092803 (`https://espo.nasa.gov/node/82364`): Taal "erupted on January 12, 2020, after 43 years of repose"; pre-eruption pressurisation of a ~5 km deep reservoir; co-eruptive loss of 0.531 ± 0.004 km³ with a 0.643 ± 0.001 km³ lateral dike; recovery from ~3 weeks after. Datasets named only as "various satellite systems" on that page [U for Sentinel-1/ALOS-2].
- UN-SPIDER, "Use of DinSAR and SBAS to monitor activity of the Taal volcano" (`https://www.un-spider.org/use-dinsar-and-sbas-monitor-activity-taal-volcano`): Sentinel-1 11 and 17 January 2020 pair; SBAS on 18 ascending images over the six months before; −91 mm deflation on the SW outer flank, +37 mm near the rim, ~+197 mm on the NE shore of the crater lake; no dataset provided.
- PHIVOLCS bulletins themselves cite "electronic tilt, continuous GPS, and InSAR monitoring" (Taal, 14 Mar 2022).
- An ESA proceedings paper ran ALOS-1 InSAR time series over Mayon, Bulusan, Kanlaon and Taal (`https://proceedings.esa.int/files/302.pdf`; server refused connection) [U].

---

## 6. Earthquake catalogues

### 6.1 USGS ComCat / FDSN (verified)

`https://earthquake.usgs.gov/fdsnws/event/1/`: `limit` 1–20,000 ("The service limits queries to 20000"; more gives HTTP 400); parameters `starttime, endtime, minlatitude, maxlatitude, minlongitude, maxlongitude, latitude/longitude/maxradiuskm, minmagnitude, mindepth, maxdepth, catalog, contributor, orderby`; formats csv, geojson, kml, quakeml (default), text; `/count` endpoint. Probe counts for the box 4–22°N, 116–128°E, 1900-01-01 to 2026-10-21: **27,333 events (all magnitudes)**; **16,011 with M ≥ 4.5**. So two or three paged queries fetch the whole box. Licence: "USGS-authored or produced data and information are considered to be in the U.S. Public Domain." (`https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits`); credit "U.S. Geological Survey". ISC-GEM feeds ComCat for early years: "ISC-GEM Global Instrumental Earthquake Catalogue (1904-2022)", events M ≥ 5.5 plus continental M ≥ 5.0 (`http://www.isc.ac.uk/iscgem/`).

### 6.2 ISC Bulletin (verified)

`https://www.isc.ac.uk/iscbulletin/`: "contains data from 1900 to present day"; Reviewed Bulletin "is typically 24 months behind real-time" (currently to 2024-10-01); search outputs CSV, QuakeML, ISF; no request limit stated; citation required: "International Seismological Centre (2026), On-line Bulletin, https://doi.org/10.31905/D808B830" and "Data retrieved from the ISC Bulletin should always be cited." No licence text (Data Management Policy PDF not read) [U].

### 6.3 PHIVOLCS catalogue

See 1.5: HTML monthly tables from 2016 (with gaps), fields date-time PHT, lat, lon, depth km, magnitude (type on event page, e.g. Ms), location string; ~1,450 events/month in 2025; no bulk download; request via the catalogue request form or FOI. Unofficial CC0 scrape on GitHub (`DaijobuDes/phivolcs-dataset`) and the R package `lindol` (bulletins from 2018) [U].

### 6.4 Faults

- GEM Global Active Faults (`https://github.com/GEMScienceTools/gem-global-active-faults`): "available under a Creative Commons attribution sharealike license" (sidebar CC-BY-SA-4.0); GeoJSON (version of record), GeoPackage, KML, Shapefile; harmonised GeoJSON is 10.6 MB (HEAD); Philippines contributed from Peñarubia et al. (2019); citation Styron & Pagani 2020, Earthquake Spectra 36(1S), DOI 10.1177/8755293020944182. CC BY-SA is viral for derived layers; keep the fault layer separate and credited.
- PHIVOLCS active faults: PFZ maps as JPG and a Google Drive folder on `https://www.phivolcs.dost.gov.ph/philippine-fault-zone-maps/` (cite Tsutsumi & Perez 2013); Valley Fault System via FaultFinder (JS app) and HazardHunterPH. FOI requests for VFS/active-fault shapefiles were denied in 2021 and 2023 per search snippets (pages 403) [U].

---

## 7. Hazard maps and exposure

- **PHIVOLCS volcano hazard maps** (`https://www.phivolcs.dost.gov.ph/volcano-hazard/`): Taal base surge, volcanic tsunami/fissuring, ballistic projectiles (A0 PDFs, January 2020 layouts, plus barangay lists); Bulusan PDC, lahar, lava flow (PNG); Kanlaon lava flow, lahar, pyroclastic flow (JPG); Mayon pyroclastic flow, lahar, lava flow (JPG), ash fall (PNG); Pinatubo lahar/flood (PDF) and provincial maps (PNG). Raster images only, no georeferencing, no licence text. GIS versions (KMZ) through GISWEB/HazardHunterPH after login/Google Form (1.6); HazardHunterPH terms forbid republishing. PDZ radii are in bulletins and the alert-level page (Taal 7 km [U], Mayon 6 km, Kanlaon 4 km at Level 0 growing to 14 km, Bulusan 4 km).
- **OCHA COD-AB Philippines** (HDX CKAN API, dataset `cod-ab-phl`): "Philippines - Subnational Administrative Boundaries", admin 0–4 (Admin 1: 17, Admin 2: 88, Admin 3: 1,642, Admin 4: 11,920), source NAMRIA and PSA, licence "Creative Commons Attribution for Intergovernmental Organisations (CC BY-IGO)", last modified 2026-05-28; files: geodatabase 361 MB, shapefile 929 MB, GeoJSON 1.06 GB, XLSX 9 MB. Barangay level is heavy; simplify server-side.
- **WorldPop**: "WorldPop datasets are licensed under the Creative Commons Attribution 4.0 International License" (`https://hub.worldpop.org/project/categories?id=3`); country 100 m population counts 2015–2030 (R2025A v1) in GeoTIFF.
- **GHSL** GHS-POP R2023A on GEE (`JRC/GHSL/P2023A/GHS_POP`): 100 m, epochs 1975–2030 in 5-year steps; "The GHSL has been produced by the European Commission Joint Research Centre as open and free data. Reuse is authorised, provided the source is acknowledged."
- **ESA WorldCover** v200 (2021, 10 m, 11 classes) on GEE: terms "CC-BY-4.0"; citation Zanaga et al. 2022, DOI 10.5281/zenodo.7254221.
- **Copernicus DEM GLO-30** on GEE: 30 m; "available worldwide with a free license with the exception of two countries (Armenia and Azerbaijan)"; "© DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved"; the GLO30 asset is deprecated in favour of `COPERNICUS/DEM/GLO30_2024_1`.
- Exposure method: population within 6/10/14 km rings (and within the PDZ) per volcano from WorldPop or GHSL via GEE `reduceRegions`; this is a *descriptive* count, not a hazard model, and must not be labelled "at risk".

---

## 8. Existing products and public interest

What exists: PHIVOLCS website and Facebook (daily summaries, eruption bulletins, hazard maps); GVP (eruption history, weekly reports); MOUNTS (daily S1/S2/S5P imagery and time series for Taal, Mayon, Kanlaon, Bulusan); MIROVA (VRP for Taal, Mayon, Kanlaon, Pinatubo; OSF dataset CC BY 4.0); COMET portal (Taal, Pinatubo, Kanlaon); Volcano Discovery (status pages, e.g. `https://www.volcanodiscovery.com/kanlaon.html`, "erupting", last update 2026-10-19 per snippet; page 403) [U]; HazardHunterPH (location hazard check); unofficial scrapers/MCP wrappers for PHIVOLCS feeds. **No public product combines PHIVOLCS ground series with satellite SO2, thermal and InSAR in one retrospective, per-volcano view for the Philippines** — that is the gap.

Recent activity (for story-telling and for checking the project's "retrospective" framing):

- Taal 2020–2022 (`https://en.wikipedia.org/wiki/2020_Taal_Volcano_eruption`): 12 January 2020 phreatomagmatic eruption, column ~10–15 km, VEI 4; Alert Level 2 → 3 → 4 within hours; ~459,300 people within the 14 km zone (OCHA); 70,413 in 300 evacuation centres by 18 January (NDRRMC SitRep 74); crop damage ₱3.06 billion; later eruptions July 2021 (record SO2 on 4 July), November 2021, March 2022 (VEI 3 episodes).
- Mayon 2018 and 2023 (`https://en.wikipedia.org/wiki/Mayon`): 13 January 2018 phreatic eruption, Alert 2→3 (14 Jan)→4 (22 Jan), ~40,000 displaced; 2023: Alert 3 on 8 June, lava flow 1.5 km by 18 June, 20,000 evacuated, lowered to Alert 2 on 8 December 2023; GVP lists 2023-04-27 to 2024-02-04 VEI 2.
- Kanlaon 2024–2026 (`https://en.wikipedia.org/wiki/2024%E2%80%932026_Kanlaon_eruptions`): 3 June 2024 explosive eruption (5 km plume, Alert 1→2; 57,563 affected); record SO2 11,556 t on 11 September 2024 and 10,074 t on 28 October 2024; 9 December 2024 eruption (Alert 2→3; ~87,000 to evacuate, state of calamity in 31 LGUs); 8 April 2025 (4 km plume; 28,272 displaced); 13 May 2025; Alert lowered 3→2 on 29 July 2025; 24 October 2025 minor eruption; 19 February 2026 (2 km plume, ashfall in 41 barangays); further events 26 Feb, 15 Mar, 9 Jul and 10 October 2026 (news: GMA, `https://www.gmanetwork.com/news/topstories/regions/1005552/...`, plume 5–6 km on 10 October 2026, Alert Level 2 in effect). Kanlaon is erupting as of the research date.
- Bulusan (`https://en.wikipedia.org/wiki/Bulusan`): phreatic eruptions 5 and 12 June 2022 (Alert 1; ~180 evacuated); 28 April 2025 phreatic eruption, plume 4,500 m, PDC within 3 km, Alert 1; 29 April second eruption.

Public-interest signal (Wikimedia pageviews API, en.wikipedia, all-access user, monthly, 2019-01 to 2026-10, probed 2026-10-21):

| Article | Months | Total views | Median/month | Peak months |
|---|---|---|---|---|
| Taal_Volcano | 94 | 3,462,636 | 18,867 | Jan 2020: 1,374,478; Feb 2020: 91,369; Sep 2023: 72,184; Oct 2020: 63,989; Jul 2021: 63,751 |
| Kanlaon | 94 | 1,254,034 | 6,358 | Jun 2024: 182,642; Dec 2024: 162,887; Apr 2025: 87,156; Oct 2025: 63,240 |
| Mayon_Volcano | 94 | 172,317 | 1,445 | Jan 2020: 16,131 |
| Bulusan_Volcano | 94 | 12,694 | 54 | Jan 2020: 3,461 |

Google Trends could not be queried (no API without an account) [U]. Interest is event-driven and very spiky, dominated by Taal 2020 and Kanlaon 2024–25; between crises it is low.

Academic multi-sensor work: Valade et al. 2019 (MOUNTS; S1 SAR, S2 SWIR, S5P TROPOMI, GEOFON/USGS seismicity, AI); Massimetti et al. 2020 (S2 hotspots vs MODIS-MIROVA); Coppola et al. 2020 (Frontiers in Earth Science 7, DOI 10.3389/feart.2019.00362, MIROVA global monitoring); Campus et al. 2022 (Sensors 22, 1713, MODIS→VIIRS); Bato et al. 2021 (Taal InSAR); Theys et al. 2017 (TROPOMI SO2 algorithm). A Philippine-specific multi-sensor review was not found [U].

---

## 9. Safety and honesty

What a non-authority site can say: *what the instruments recorded in the past* (satellite columns, hotspots, interferograms, catalogue earthquakes, PHIVOLCS-reported numbers with their dates), with provenance and uncertainty. What it cannot say: the current alert level as if it were authoritative, whether an eruption is likely, whether a place is safe, or anything that reads as an evacuation instruction. The risk is real: Kanlaon is in an eruptive phase today, and Wikipedia pageviews show that during a crisis hundreds of thousands of people search for exactly this topic; a stale "Alert Level 2" badge or a hotspot plotted next to a town would be read as live information.

How the authorities word it: PHIVOLCS event bulletins say "This will be the only bulletin issued unless additional information becomes available" and "Always refer to the latest earthquake information posted at the PHIVOLCS official website"; hazard-map pages say "These maps may be revised as new information becomes available"; FIRMS says the fire products "have not been validated against independent data for their ability to detect volcanoes" and asks redistributors to replicate the LANCE disclaimer; MIROVA: "provided 'as is'"; COMET: "for general information purposes only ... Any reliance you place on such information is therefore strictly at your own risk"; GVP material is non-commercial with citation [U].

Recommended framing:

1. Title and header: "A retrospective record, 2005–2026. Not a monitoring or warning service. DOST-PHIVOLCS is the sole authority for alert levels and advisories" with a persistent link to `https://www.phivolcs.dost.gov.ph/` and the volcano bulletin list.
2. No live feeds: freeze data at a dated snapshot ("Data through 2026-09-30"), show the snapshot date on every chart, and never show a "current" alert level; show alert-level *history* ending at the snapshot with an explicit "as reported by PHIVOLCS on <date>".
3. Label proxies honestly: "TROPOMI SO2 column (satellite, afternoon overpass, cloud-limited)" separate from "PHIVOLCS SO2 flux (ground DOAS, t/day)"; "FIRMS thermal anomalies within 10 km (includes vegetation fires)" rather than "lava"; InSAR as "LOS displacement; atmospheric artefacts likely in the tropics".
4. Exposure as "population within N km (WorldPop 2020)", not "people at risk".
5. Replicate the required notices: "Contains modified Copernicus Sentinel data [year]"; "LiCSAR contains modified Copernicus Sentinel data"; NASA FIRMS/LANCE disclaimer link; GVP citation; ISC citation; MIROVA Dataset CC BY citation; PHIVOLCS as source of every ground number with the bulletin link.
6. Do not reproduce HazardHunterPH or GISWEB hazard layers; link to them. Hazard-map rasters from the PHIVOLCS site are government works (no copyright) but still link rather than embed, with the "may be revised" caveat.

---

## 10. Volumes and free-tier feasibility

- **TROPOMI SO2 zonal stats on GEE**: OFFL L3 SO2 has one image per day from 2018-12-05, i.e. ~2,880 days to 2026-10. A 30 km-radius disc at 1.1 km pixels is ~2,300 pixels; 24 volcanoes × 2 bands × 2,880 days ≈ 320 M pixel-reads for a `reduceRegions` export to a table: minutes of batch time, on the order of **0.1–1 EECU-hour** [U, derived]. Earth Engine is free for "an individual developer using Earth Engine for noncommercial purposes" (`https://earthengine.google.com/noncommercial/`); default quotas 40 concurrent requests, 2 concurrent batch tasks, no daily EECU cap by default (`https://developers.google.com/earth-engine/guides/usage`). **Important: a "20-year" SO2 series is not possible from TROPOMI (launched 2017, data from mid-2018)**; 2004–2018 would need OMI/OMPS SO2 (NASA GES DISC, not on GEE) [U], or PHIVOLCS flux from bulletins/GVP reports.
- **FIRMS points within 20 km of 24 volcanoes since 2000**: Philippine national totals are not published on the pages fetched. Derived: 24 discs of 1,257 km² ≈ 30,000 km² (~10% of Philippine land); MODIS detections in the Philippines are of order tens of thousands per year, VIIRS several times more, so the within-20 km subset is roughly **100k–400k rows for 2000–2026** [U]; the vast majority will be agricultural/forest fires, so the useful volcanic subset is far smaller. The archive download tool returns the whole country by email in CSV; the API needs 5-day chunks (≈73 requests per source per year; under the 5,000/10-minute limit).
- **USGS events in the Philippine box (4–22°N, 116–128°E) since 1900**: 27,333 (16,011 at M ≥ 4.5), verified counts; two paged queries; GeoJSON of ~10–15 MB [U].
- **PHIVOLCS earthquakes**: ~1,450 located events/month in 2025 (≈17,000/year), monthly HTML of 0.5–2.8 MB; since 2016 roughly 100k–150k rows [U].
- **PHIVOLCS bulletins**: ~15,000 posts since September 2017 (1,498 listing pages) [U]; text parsing yields daily SO2, counts, plume, alert level for 4–5 volcanoes.
- **LiCSAR**: Taal frame 2,888 pairs; ~30 MB per pair → ~85 GB per frame [U]; three frames for Mayon and three for Kanlaon with 1,589–3,877 pairs each. Do not mirror; either run LiCSBAS on a crop for one or two frames offline and publish a small time-series table, or link to COMET portal time series (Taal, Pinatubo, Kanlaon) and MOUNTS.
- **GVP**: 23 volcanoes, 233 eruption rows (Philippines incl. Babuyan group); whole WFS layers are 1,214 volcanoes and 11,089 eruptions.
- **Boundaries/exposure**: COD-AB geodatabase 361 MB (admin 4), WorldPop 100 m Philippines GeoTIFF of order 100 MB per year [U]; compute ring statistics once in GEE and store a few KB.
- Hosting: all outputs are small tables (MBs) suited to Cloudflare Pages + a static Parquet/JSON bundle; the only heavy step is a one-off GEE export and an optional offline LiCSBAS run.

---

## Scores (1–5)

| Criterion | Score | Justification |
|---|---|---|
| Data availability and licences | 3 | Satellite, catalogue and global sources are open and verified (Copernicus free/full/open; NASA open; USGS public domain; GVP WFS with "AccessConstraints NONE" but non-commercial site terms; MIROVA Dataset CC BY 4.0; WorldPop/WorldCover CC BY; COD-AB CC BY-IGO), but the ground truth (PHIVOLCS SO2 flux, counts, alert history) is only in prose bulletins since Sept 2017, the LAVA portal was down, and HazardHunterPH forbids republishing. |
| Volume / free-tier feasibility | 4 | Everything except InSAR is MB-scale; GEE zonal stats are cheap; USGS 27k events; InSAR must be linked or cropped (tens of GB per frame). |
| Scientific honesty | 3 | TROPOMI gives columns not flux and only since 2018; FIRMS cannot separate fires from lava without SP `type`; tropical atmosphere degrades InSAR; a "20-year multi-sensor" claim needs careful caveats and era-dependent sources. |
| Public interest and portfolio appeal | 5 | Taal Jan 2020: 1.37 M Wikipedia views in a month; Kanlaon 2024–26 sustained 60k–180k monthly peaks and an ongoing eruption; strong national relevance. |
| Technical showcase | 5 | GEE pipelines (S5P, MODIS/VIIRS, WorldPop rings), WFS/FDSN ingestion, bulletin NLP parsing, InSAR products, map plus multi-series time-series UI. |
| Risk (5 = low) | 3 | A volcano site can be mistaken for a live hazard service during a crisis; PHIVOLCS reuse terms are unwritten (RA 8293 covers non-profit use, but "for profit" needs approval); scraping ~15k bulletins and re-serving numbers invites attribution and accuracy disputes. |

**Top three risks**

1. **Being read as a live alert source.** Kanlaon is erupting now; any "alert level" or hotspot shown without a hard snapshot date and a PHIVOLCS-is-the-authority banner can mislead. Mitigate with a frozen, dated, retrospective design and no live feeds.
2. **Ground-truth access and terms.** The only machine-readable PHIVOLCS series are prose bulletins (Sept 2017 onward) and the WOVOdat/LAVA portal, which was down with an invalid certificate; GeoRiskPH/HazardHunterPH are account-gated with no-republish terms; the 2025+ daily summaries have empty static HTML. Check LAVA again, request data through the "Request for Volcano Data" page, and keep hazard layers as links.
3. **Scientific misreading of proxies.** SO2 column ≠ flux (and only 8 years of TROPOMI), fire pixels ≠ lava, InSAR LOS change ≠ magma; the "20-year" framing must be honest that the series mix sources by era (GVP/PHIVOLCS before 2018, satellites after).
