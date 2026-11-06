# Candidates: which Philippine big-data map to build next

Status: phase 1, 2026-10-21. Six candidates researched that day with web search, page fetches and small API probes (a few KB each); full notes, with a URL and access date per claim, are in [`research/`](research/). **[U]** marks an estimate or a claim not verified on a primary page. Nothing is built; no account or resource was created.

The bar is Lights (`../../lgu-lights/`): many real public sources, a national map with a time series, stated uncertainty beside official figures, plain-language explanations, English and Japanese, a GitHub Actions pipeline, static-first delivery. Each candidate is also judged on what it adds beyond Lights (a per-LGU annual panel with a Rust core) and Typhoon Replay (a Java/PostGIS event replay), and on fit with the free tiers and the archiving standard (`../../DATA-ARCHIVING.md`).

Candidate 1, volcanoes, was the starting idea. Ideas rejected in `../../big-data-ideas.md` and earlier notes (PhilGEPS spending, Tokyo transit, CopybookBridge, a résumé builder) were not re-proposed. "Typhoon damage versus recovery from night lights" was not scored: it would reuse Typhoon Replay's tracks and Lights' night-lights pipeline almost unchanged, so it is noted as a possible Lights milestone instead.

## 0. Verdict at a glance

| # | Candidate | Data and licences | Free-tier fit | Honesty | Interest and portfolio | Technical scope | Risk (5 = low) | Total |
|---|---|---|---|---|---|---|---|---|
| 1 | **Philippine volcanoes: a retrospective multi-sensor record** | 3 | 4 | 3 | 5 | 5 | 3 | **23** |
| 2 | Land subsidence and flooding from Sentinel-1 InSAR | 3 | 3 | 4 | 5 | 5 | 2 | 22 |
| 3 | Air quality from satellites and ground stations | 4 | 5 | 3 | 3 | 4 | 3 | 22 |
| 4 | Coastal ecosystems: mangrove and coral change | 4 | 4 | 3 | 4 | 3 | 3 | 21 |
| 5 | Rice and drought | 4 | 3 | 3 | 5 | 4 | 3 | 22 |
| 6 | Earthquakes, faults and shaking exposure | 4 | 5 | 4 | 4 | 3 | 3 | 23 |

**Recommendation: build candidate 1, volcanoes, framed as a dated retrospective record (never a hazard or alert service), with the earthquake catalogue folded in as a layer around each volcano, and with InSAR deformation (the technique behind candidate 2) as a later milestone at Taal.** Reasons in §8. Runner-up for a safer build: candidate 6 (earthquakes), which shares PHIVOLCS as the authority and most of the ingestion work. Runner-up for a harder, more original build: candidate 2 (subsidence); its risks are compute and an official product (CopPhil) that may pre-empt it.

Scores are 1–5 judgements, not measurements; each reason is in the sections below. The totals are close: all six are viable, and the choice turns on what the project should show.

## 1. Philippine volcanoes

A national map of the 24 PHIVOLCS-listed active volcanoes with, for each, a multi-sensor time series: eruption history (Smithsonian GVP), the PHIVOLCS-reported daily figures (alert level, volcanic earthquake counts, SO2 flux, plume height, deformation statements), satellite SO2 columns (Sentinel-5P TROPOMI, 2018 →), thermal anomalies (MODIS and VIIRS since 2000 and 2012; MIROVA radiative power), earthquakes within 30 km (USGS since 1900, PHIVOLCS since 2016), ground deformation (COMET LiCSAR interferograms, a later milestone) and exposure (population within distance rings, land cover). Full notes: [`research/volcanoes.md`](research/volcanoes.md).

**Sources and licences.** Verified on 2026-10-21:

| Source | Content | Access | Licence | Redistribution |
|---|---|---|---|---|
| PHIVOLCS daily bulletins (WordPress) | prose bulletins since 2017-09-02 (about 1,498 listing pages, about 15,000 posts [U]): earthquake counts, SO2 t/day, plume, deformation sentence, alert level | HTML; crawl | no terms on the site; government work under RA 8293 §176 (no copyright; prior approval only for exploitation for profit) | show with citation and link; see the policy caveat below |
| PHIVOLCS-LAVA portal (`wovodat.phivolcs.dost.gov.ph`) | structured 24-hour bulletins since about early 2022 (`/bulletin/activity-{tvo,mvo,kvo,bvo}?bid=N&lang=en`: alert level, eruption events, seismicity, crater-lake acidity and temperature, SO2 flux t/day, plume, deformation); eruption history (216 rows, "ongoing audit"); monitoring time series | HTML, probed; downloads and the eruption-history CSV need a registered login | **Data policy (updated 2020-07-01):** registration required; cite DOST-PHIVOLCS; "should not be used by anyone other than DOST-PHIVOLCS officials for publicly forecasting ongoing unrest"; "Redistribution or charging for access to DOST-PHIVOLCS data is prohibited" | public bulletin pages are press releases; the policy text governs the registered downloads. Posture: display bulletin values with per-value citation and link; no bulk PHIVOLCS dataset is published until PHIVOLCS confirms in writing; no registered downloads are used |
| PHIVOLCS earthquake information | HTML monthly tables since 2016 with gaps, about 1,450 events/month in 2025 | crawl | as above | as above |
| Smithsonian GVP | 23 Holocene volcanoes in the Philippines, 233 eruption rows with VEI and explicit date uncertainty | GeoServer WFS (CSV/GeoJSON, `AccessConstraints NONE`), probed | Smithsonian terms: personal, educational and other non-commercial use with citation [U: site blocked, wording from a snippet] | derived figures with citation; private archive only |
| Sentinel-5P TROPOMI SO2 (`COPERNICUS/S5P/OFFL/L3_SO2`) | daily column density, ground-level and 15 km bands, 1.1 km, 2018-12-05 → 2026-10-18 | Earth Engine | Copernicus: free, full and open; "Contains modified Copernicus Sentinel data [Year]" | yes |
| NASA FIRMS, MOD14A1, VNP14A1 | active fire and thermal anomalies, 1 km daily, 2000-11 → (MODIS), 2012 → (VIIRS); FIRMS API 5,000 transactions per 10 min; `type = 1` "active volcano" only in standard-quality archive data | Earth Engine and the FIRMS API/archive (Earthdata login exists) | NASA open data; replicate the LANCE disclaimer | yes |
| MIROVA Dataset v2.5 | volcanic radiative power from MODIS and VIIRS, 2000–2025, global CSV 98.6 MB, includes Taal, Mayon, Kanlaon, Pinatubo | OSF `zm62w`, probed | CC BY 4.0 | yes |
| USGS ComCat (FDSN) | 27,333 events in 4–22°N 116–128°E since 1900 (24,990 at M ≥ 4, probed); 20,000 per query | CSV/GeoJSON | US public domain | yes |
| COMET LiCSAR | Sentinel-1 interferograms, frames identified for Taal (`032D_07536_111313`, 374 epochs 2014–2026), Mayon, Kanlaon, Bulusan, Hibok-Hibok; about 30 MB per pair, tens of GB per frame [U] | CEDA/JASMIN HTTP; paths broken by an October 2025 migration during probing | Copernicus derived works; "LiCSAR contains modified Copernicus Sentinel data [year]" | derived products yes; never mirror a frame |
| WorldPop, GHSL, ESA WorldCover, Copernicus DEM, OCHA COD-AB | exposure, land cover, terrain, boundaries | Earth Engine and HDX (already used by Lights) | CC BY 4.0, EU open, CC BY 4.0, free licence, CC BY-IGO | yes |
| HazardHunterPH, GeoRiskPH, GISWEB hazard KMZ | lahar, PDC, PDZ layers | account or form gated | HazardHunterPH terms forbid republishing | **link only, never re-served** |

**Data volume and free-tier fit.** Everything published is MB-scale: per-volcano daily series (about 2,900 TROPOMI days × 24 volcanoes), 100k–400k thermal detections within 20 km of the volcanoes since 2000 [U], 27k USGS events, about 150k PHIVOLCS events [U], about 15,000 bulletins. The one-off Earth Engine work is a few EECU-hours against the Community tier's 150 per month [U, derived]; InSAR, the only heavy data, is cropped or linked, never mirrored. Fits Cloudflare Pages (25 MiB per file), GitHub Pages or Hugging Face for tiles, and the private archive repo for raw snapshots. Score 4.

**Scientific honesty.** A satellite SO2 *column* is not a *flux*; thermal "fire" pixels include vegetation fires (FIRMS: the products "have not been validated ... for their ability to detect volcanoes"); InSAR line-of-sight change is not magma; TROPOMI starts in late 2018, so a 20-year view mixes sources by era. All of this can be shown (coverage fractions, detection limits, per-series provenance); this is the Lights pattern of proxies beside ground truth. Score 3: every proxy needs labelling.

**Public interest and portfolio.** Taal's January 2020 eruption drew 1,374,478 English Wikipedia page views in a month; Kanlaon's 2024–2025 eruptions 160k–180k in peak months; Kanlaon erupted again on 2026-10-10 and is in an eruptive phase today. No public product combines the PHIVOLCS ground series with satellite SO2, thermal and deformation in one retrospective per-volcano view. Pitch: "a multi-sensor, 20-year record of every active Philippine volcano, with official figures beside independent satellite measurements and the uncertainty of each". Score 5.

**Technical scope.** Earth Engine pipelines over daily rasters (S5P, MODIS, VIIRS, WorldPop rings), WFS and FDSN ingestion, bulletin text parsing with tests, event-driven time series (episodes, baselines, anomalies), map plus synchronised multi-series charts, optional InSAR. Different from Lights (annual panel, regression) and Typhoon Replay (hourly replay of one storm). Score 5.

**Risks and mitigations.**
1. *Being read as a live hazard source.* Kanlaon is erupting now. Mitigation: a dated snapshot ("data through <date>") on every view, no current alert badge (history only, "as reported by PHIVOLCS on <date>"), a persistent banner naming DOST-PHIVOLCS as the sole authority with a link to its bulletins, no live feeds, no push notifications, no "is it safe" language. This is a scope rule.
2. *PHIVOLCS data posture.* The LAVA policy forbids redistribution of registered data and public forecasting; the website has no terms. Mitigation: use only public bulletin pages, cite each value with its bulletin link, publish no PHIVOLCS bulk dataset until PHIVOLCS confirms by email (as Lights did with PSA), design the site so the satellite and GVP series stand alone if PHIVOLCS values are withdrawn, and never forecast.
3. *Proxy misreading.* Mitigation: label every series by instrument and quantity, show coverage, never convert a column to a flux, keep thermal detections as "detections within N km (includes fires)".
4. *Source fragility.* LiCSAR paths changed in October 2025; GVP's site is behind Cloudflare (its WFS works); PHIVOLCS pages change format by era. Mitigation: `archivekit` snapshots from day one, parsers per era with fixtures.

Risk score 3 (medium): each risk has a design answer.

## 2. Land subsidence and flooding from Sentinel-1 InSAR

A ground-motion map of Philippine cities from Sentinel-1 interferometry (Metro Manila, CAMANAVA, Bulacan and the Pampanga delta first), joined with flood extents, hazard maps, built-up growth, the Manila tide gauge and exposed population. Full notes: [`research/subsidence-insar.md`](research/subsidence-insar.md).

**Sources.** COMET LiCSAR has deep Manila coverage (descending `032D_07536_111313`, 374 epochs 2014-10 → 2026-08, about 2,400 interferograms; two ascending frames), under the Open Government Licence plus Copernicus terms; no velocity product for Manila is published, so LiCSBAS (GPL-3) would be run by the project. ARIA GUNW has 5,305 products over Manila. EGMS is Europe-only (confirmed). ASF HyP3 gives 8,000 free credits a month (10–15 per interferogram), products expire after 14 days and the free tier is funding-dependent. Earth Engine has GRD only, so no InSAR there. Context: JRC Global Surface Water (free), Global Flood Database (CC BY-NC), UNOSAT (CC BY-SA), PhilSA Sentinel-1 flood shapefiles, NOAH hazard maps (licence to confirm), HazardHunterPH (link only), groundwater extraction not public, Manila tide gauge (PSMSL 145, 1901–2024, flagged), Tay et al. 2022 Manila data (CC BY-NC), Wu et al. 2022 (CC BY 4.0). Literature: CAMANAVA 4.4 cm/yr (2003–06), Bulacan up to 109 mm/yr (2014–20), Cebu 11, Davao 38, Iloilo 9, Legazpi 29 mm/yr (Sulapas 2024).

**Free-tier fit.** A full SLC stack is impossible (about 1.5 TB); the LiCSAR + LiCSBAS route is about 60–70 GB per frame to download and a few GB working set after clipping, which needs staged jobs to fit the 6-hour, 14 GB-disk GitHub runner. Score 3.

**Honesty.** InSAR caveats are well understood and showable (reference point, line of sight, standard deviation per pixel, coherence); the worst subsidence is in fishpond terrain where C-band decorrelates. Score 4.

**Interest and technical scope.** "Bulacan is sinking", the new Manila airport, reclamation and flooding are live national stories; no public national subsidence map exists. Technically the strongest: time-series inversion, uncertainty maps, ascending/descending decomposition, exposure analytics. Scores 5 and 5.

**Risks.** CopPhil's Ground Motion Monitoring Service (EU/ESA with PhilSA; page live, flyer May 2026, status unknown) may release an official national velocity product; data-path fragility (LiCSAR migration, HyP3 expiry); over-claiming rates that Philippine researchers would challenge. Score 2: the compute path and pre-emption by CopPhil are outside the project's control.

## 3. Air quality from satellites and ground stations

NO2, SO2, CO, aerosol and modelled PM2.5 over the Philippines, 2018 →, per province and city, with the stories (the 2020 lockdown NO2 drop, Taal vog school closures, the 2023 "smog" that was traffic, the 2026 Kalimantan haze). Full notes: [`research/air-quality.md`](research/air-quality.md).

**Sources.** All six Sentinel-5P L3 collections on Earth Engine (NO2 and CO from 2018-06-28, SO2 and HCHO from 2018-12-05), 1.1 km, open with attribution; MAIAC AOD (1 km, 2000 →, no restrictions); CAMS (CC BY); WUSTL satellite PM2.5 (CC BY 4.0, 0.01°, 1998–2023); FIRMS. Ground stations are the weak link: DENR-EMB has 134 stations but its site returned 403, a 2021 FOI request for station locations was denied, and history reaches the public as PDFs and Facebook posts; OpenAQ needs a key and its Philippine coverage is unverified; IQAir and WAQI are proprietary.

**Fit, honesty, interest, technical scope.** Fit 5. Honesty 3: columns are not surface concentrations, tropical cloud removes a large share of days, satellite PM2.5 is uncalibrated locally. Interest 3: the result resembles existing AQI dashboards. Technical scope 4: raster animation, calendar heatmaps, multi-sensor fusion. Risk 3: thin ground truth and the health-claim trap.

## 4. Coastal ecosystems: mangrove and coral change

Mangrove extent 1985–2025 and coral reef habitat per municipality, with heat stress, typhoons, aquaculture and fisherfolk poverty. Full notes: [`research/coastal-ecosystems.md`](research/coastal-ecosystems.md).

**Sources.** Global Mangrove Watch v4.1 (Zenodo, CC BY 4.0, annual 1985–2025 at 10 m, F1 0.93 for extent but change classes about 60 % accurate and early years infilled; the Philippines at 3,038 km² in 2025); PSA Mangrove Accounts (CC BY); Allen Coral Atlas habitat maps (CC BY 4.0 on Earth Engine, 24,219 km² of Philippine reef ecosystem; habitat, not health); NOAA Coral Reef Watch 5 km (public domain, 1985 →, via ERDDAP); UNEP-WCMC reefs and WDPA are no-redistribution and are excluded; Clark Labs pond maps carry a contradictory non-commercial clause; NAMRIA national maps are not downloadable (FOI denied). Fisherfolk poverty 27.4 % in 2023 (PSA, CC BY).

**Fit, honesty, interest, technical scope.** Fit 4 (GB-scale subsets; CRW box subsets about 2.6 GB per variable). Honesty 3 (change classes, infill, DHW is not observed bleaching). Interest 4 (planting drives, Boracay, Verde Island Passage, Haiyan, the 2024 bleaching). Technical scope 3: mostly a re-display of two global products with a municipal synthesis and little new computation. Risk 3.

## 5. Rice and drought

Palay area, production and prices per province beside satellite rice phenology and drought indicators, with the El Niño years. Full notes: [`research/rice-drought.md`](research/rice-drought.md).

**Sources.** PSA OpenSTAT (CC BY; the PX-Web JSON API answered plain curl with no Cloudflare challenge, unlike psa.gov.ph) has palay production and area by province and quarter 1987–2026, monthly retail rice prices by province 2018 →, farmgate prices, stocks; the province is the floor (no municipal series). PRiSM (IRRI/PhilRice Sentinel-1 rice monitoring) publishes nothing; PAGASA station data forbids redistribution; NESEA-Rice10 (CC BY 4.0) gives 10 m rice maps 2017–2019; CHIRPS, ERA5-Land, SMAP, MODIS NDVI, NOAA VHI, ONI are open; SPEIbase is ODbL. Sentinel-1's record is discontinuous (S1B lost in 2021, S1A retired mid-2026).

**Fit, honesty, interest, technical scope.** Fit 3: national 10 m Sentinel-1 phenology would far exceed 150 EECU-hours a month, so the SAR layer must be 100 m zonal statistics plus sample provinces [U]. Honesty 3: area and phenology anomalies are defensible, yields are not, and 2024 mixes El Niño with typhoons. Interest 5: rice inflation peaked at 24.4 % in March 2024, with price caps, a tariff cut, an import ban and a strong El Niño forecast for late 2026. Technical scope 4, with the caveat that if scope is cut to "annual index versus statistic per LGU" it duplicates Lights. Risk 3.

## 6. Earthquakes, faults and shaking exposure

Century-long seismicity explorer: faults, the "Big One" scenario, ShakeMaps for damaging events, exposure, tsunami history. Full notes: [`research/earthquakes-faults.md`](research/earthquakes-faults.md).

**Sources.** USGS ComCat (public domain; 27,334 events in the box since 1900, 631 at M ≥ 6; about 5 MB of CSV; pre-1970 rows are mostly ISC-GEM imports, so the century series is complete only above about M5.5); ISC Bulletin (citation required, 24 months behind); PHIVOLCS HTML tables (2018 → via monthly pages per these notes, 2016 → per the volcano notes; no API, no licence); GEM Global Active Faults (CC BY-SA 4.0, share-alike); GEM hazard map (CC BY-NC-SA); USGS ShakeMap (public domain, about 0.3 MB light products per event); PHIVOLCS fault shapefiles are not public (KMZ only, FOI denied); HazardHunterPH all rights reserved; NCEI tsunami database (113 Philippine events since 1627); WorldPop, GHSL, building footprints, COD-AB. The 2025 Cebu (M6.9, 2025-09-30) and Davao Oriental (M7.4, 2025-10-10) earthquakes appear in both catalogues; PHIVOLCS and USGS differ on depth.

**Fit, honesty, interest, technical scope.** Fit 5 (no Earth Engine; all under 100 MB). Honesty 4 (magnitude types, completeness; three death tolls for the same MMEIRS scenario are a good exhibit). Interest 4 ("Big One" drills through 2026, the 2025 disasters; many authoritative maps already exist). Technical scope 3: point and raster batch work, no satellite component; stacked shaking and catalogue reconciliation must lead or it repeats USGS. Risk 3: real-time misuse (PHIVOLCS fact-checked a fake prediction map in September 2026), PHIVOLCS terms, share-alike mixing.

## 7. What the comparison says

- PHIVOLCS: candidates 1, 2 (in part) and 6 depend on it. It publishes HTML pages with no stated licence and gates datasets behind registration with a no-redistribution policy. Rule: display with citation, archive privately, publish no PHIVOLCS bulk file without written confirmation, never forecast. Candidates 1 and 6 share the authority and the crawl; build one, use the other as a layer.
- Satellite data: Copernicus, NASA, USGS, WorldPop and Earth Engine collections are open with attribution. The noncommercial Earth Engine tier (150 EECU-hours a month since 2026-04-27) covers zonal statistics for every candidate except national Sentinel-1 phenology (5) and InSAR (2).
- Provenance: every candidate sets proxies beside official figures, so, as in Lights, each chart must show coverage, detection limits and provenance.
- Public interest: highest for 1, 2 and 5 (crisis-driven for volcanoes, structural for rice prices, chronic for sinking cities).
- Technical novelty: highest for 1 and 2; 4 and 6 are mostly re-display; 3 resembles existing dashboards; 5 may duplicate Lights.

## 8. Recommendation

**Candidate 1, Philippine volcanoes.** Chosen because it alone combines:

- the strongest personal and public interest;
- the widest sources (ground, three satellite modalities, catalogues, exposure);
- a clear gap (no retrospective multi-sensor view exists for the Philippines);
- a technical story distinct from Lights and Typhoon Replay;
- a free-tier pipeline with small published outputs.

Two risks, both handled in the design:

1. Reading as a hazard or alert service. Scope: a dated snapshot, no current status, history "as reported by PHIVOLCS on <date>", no live feeds, and a permanent banner naming DOST-PHIVOLCS as the authority with links to its bulletins. The site records what instruments measured, with provenance.
2. PHIVOLCS terms: unwritten for the website, restrictive for the portal. Use only public bulletin pages, cite every value with its link, publish no PHIVOLCS bulk dataset until PHIVOLCS confirms (email, as with PSA), and publish the satellite and GVP series as the dataset so the product works without PHIVOLCS numbers.

Absorbed from the others:

- 6: the earthquake catalogue becomes a per-volcano "earthquakes within 30 km" series and a national seismicity layer.
- 2: InSAR becomes a later milestone at Taal (LiCSAR has 374 epochs; pairs bracket the 2020 eruption).
- 3: SO2 uses the same Earth Engine collection, so the national SO2 map is a by-product.

Runners-up: **6, earthquakes** for a safer build (fastest to ship, no Earth Engine, best honesty exhibit, narrowest technical scope); **2, subsidence** for a bolder one (widest technical scope and story, heaviest compute, exposed to CopPhil).

Q1 in [DECISIONS.md](DECISIONS.md) records the choice. The rest of the planning documents ([RESEARCH.md](RESEARCH.md), [DATA-PLAN.md](DATA-PLAN.md), [ARCHITECTURE-OPTIONS.md](ARCHITECTURE-OPTIONS.md), [sources-draft.yaml](sources-draft.yaml)) are written for candidate 1; `research/` holds enough on 2 and 6 to switch in about a day.
