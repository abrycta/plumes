# Open questions and decisions for Kurt

Status: 2026-10-21, after [CANDIDATES.md](CANDIDATES.md), [RESEARCH.md](RESEARCH.md), [ARCHITECTURE-OPTIONS.md](ARCHITECTURE-OPTIONS.md), [DATA-PLAN.md](DATA-PLAN.md) and [SPIKE-PLAN.md](SPIKE-PLAN.md). Nothing is implemented. Each question names the default the documents assume, so "Q1 = volcanoes, yes to the defaults" is enough to start. Answers go to [DECISIONS.md](DECISIONS.md).

## Decisions

| # | Question | Options | Recommendation (the default in the docs) |
|---|---|---|---|
| Q1 | **Which candidate to build** | 1 volcanoes; 2 subsidence (InSAR); 3 air quality; 4 coastal ecosystems; 5 rice and drought; 6 earthquakes | **1, volcanoes**, as a dated retrospective record with earthquakes as a layer and InSAR as a later milestone (CANDIDATES.md §8). Safer alternative: 6. Bolder: 2 |
| Q2 | **Name, folder, domain** | "Plumes" (噴煙, glyph 噴 or 火) at `plumes.krtmtthw.dev`, folder `plumes/`, repos `abrycta/plumes` and `abrycta/plumes-archive`; alternatives "Vents", "Magma Record", or a Filipino-free Japanese-style name like Lights/Akari | **Plumes**: short, plural like Lights, says what the satellites see. The folder is renamed when Q1 and Q2 are answered |
| Q3 | **Architecture** | A static read models (no server); B = A plus a Java read API on PostGIS as milestone 2 or 3; C Rust core with three adapters | **A for milestone 1, B planned as the "Under the hood" slice** (ARCHITECTURE-OPTIONS.md §0). C only if a later milestone needs heavy client-side maths |
| Q4 | **Languages and stack** | Python (uv) pipeline because of the Earth Engine client; TypeScript front end (Vite, React 19, Akari, MapLibre 6, PMTiles); Java 17 + Spring Boot + MyBatis for the milestone-2 API; no Rust at M1 | **Yes.** Rust is reopened only for the InSAR client-side case |
| Q5 | **PHIVOLCS data posture** | (i) use public bulletin and earthquake pages, cite every value with its link, publish no PHIVOLCS bulk file, email PHIVOLCS to ask whether a derived daily table may be published with attribution; (ii) same, without the email; (iii) register on PHIVOLCS-LAVA for the datasets (policy: no redistribution, no public forecasting) | **(i)**, as Lights did with PSA. No registration: the policy's redistribution clause would bind everything downstream. A draft email can be written on request |
| Q6 | **Volcano scope** | all 24 PHIVOLCS active volcanoes on the map, deep series for the 4 with daily bulletins (Taal, Mayon, Kanlaon, Bulusan), plus Pinatubo and Hibok-hibok when bulletins exist; or only the monitored 4–6 | **All 24 on the map, deep series where bulletins exist**, with an explicit "no ground bulletins for this volcano" note |
| Q7 | **Time span and the "20 years" claim** | 2000 → snapshot, each series from its own start (MODIS 2000-11, VIIRS 2012, TROPOMI 2018-12, bulletins 2017-09, LAVA 2022, USGS 1900), stated per chart; or 2018 → only (every satellite series present) | **2000 → snapshot with per-series starts shown.** A 2018 → only product would hide Pinatubo-era context and the MODIS record |
| Q8 | **InSAR** | M1: links to the COMET portal and PHIVOLCS deformation sentences; M2: a cropped LiCSBAS time series at Taal; or InSAR at M1 | **M1 links, M2 Taal crop** (DATA-PLAN.md §6) |
| Q9 | **National raster layers at M1** | monthly SO2 mosaics (2018-12 → ) and monthly thermal detections as PMTiles; or per-volcano series only | **Both national layers at M1 if spike items 2 and 7 pass**; otherwise series first, layers at M1.1 |
| Q10 | **deck.gl** | add `@deck.gl/maplibre` 9.4 for the animated point layer; or MapLibre-only | **Spike item 7 decides**; MapLibre-only unless it stutters |
| Q11 | **Earth Engine project** | a new Google Cloud project registered for noncommercial use with its own service account (its own 150 EECU-h/month); or reuse the `lgu-lights` service account (shared quota) | **New project**: isolation of quota and credentials. This is Kurt's action (Google Cloud console + Earth Engine registration), key saved in the Keychain as `earth-engine-sa-key-plumes` |
| Q12 | **Tiles and large files hosting** | GitHub Pages primary, Hugging Face fallback (Lights' Q5); or Cloudflare R2 (payment method expected) | **GitHub Pages + Hugging Face; no R2** |
| Q13 | **archivekit fit** | crawled page bundles adopted as archive releases through the existing manual-adopt path; propose a `collection` kind (per-item crawl with batch snapshots) as a kit issue, as Kessan Lens proposed; an `html` format exists already | **Use the adopt path now; file the kit issue** |
| Q14 | **Alert-level display rule** | never show a "current" level; show the history as a step line ending at the snapshot, labelled "as reported by PHIVOLCS on <date>", with the banner; or show the latest reported level with a date | **Never show "current".** The snapshot date and the banner are on every view |
| Q15 | **Published dataset** | Hugging Face `permission-alluring/plumes` with per-file licences (satellite-derived CC BY 4.0 with notices; GVP-derived file under the Smithsonian non-commercial terms; GEM CC BY-SA; no PHIVOLCS bulk file at v1) plus a Zenodo DOI; or static files only | **Yes, publish with per-file licences** |
| Q16 | **Japanese** | EN + JA (workspace standard; captions first as in Lights); no Filipino (Lights' Q8) | **Yes** |
| Q17 | **Milestone-1 scope** | as ARCHITECTURE-OPTIONS.md §6; or a narrower M1 of Taal and Kanlaon only | **The §6 scope**: the per-volcano machinery costs the same for 4 or 24 once the pipeline exists |
| Q18 | **Spike** | one day before building (SPIKE-PLAN.md); or start building | **Yes, one day**; the EE export path and the PHIVOLCS crawl are the two things that must be measured |

## Actions for Kurt

1. Answer Q1 (and Q2 if 1).
2. If Q11 = new project: create a Google Cloud project, register it for noncommercial Earth Engine (individual, Community tier), create a service account with an Earth Engine role, download its JSON key and save it: `security add-generic-password -a "$USER" -s earth-engine-sa-key-plumes -U -w "$(xxd -p < key.json | tr -d '\n')"` (multi-line values are stored hex-encoded, as with the Lights key). Later it becomes the GitHub secret on the project repo.
3. Request a free FIRMS MAP_KEY at `https://firms.modaps.eosdis.nasa.gov/api/map_key/` (email) and save it in the Keychain as `firms-map-key`.
4. If Q5 = (i): send the PHIVOLCS email (a draft can be written on request) to the Volcano Monitoring and Eruption Prediction Division contact on the LAVA portal (`mail.vmepd@phivolcs.dost.gov.ph`).
5. Answer Q3–Q18 (defaults are fine).

## Verification still to do by hand or in the spike

- GVP's exact terms-of-use and citation wording (the site was behind Cloudflare; only the WFS answered).
- Whether the 2025+ WordPress "Summary of 24Hr Observation" pages are empty for every volcano, and the first LAVA bulletin id and date (ids 500 and below returned nothing; 1000 = 2022-04-02).
- The LAVA portal's TLS chain from a GitHub runner.
- Earth Engine batch export to Drive from a service account without billing (documentation is thin), and the EECU cost of one month of S5P reductions.
- LiCSAR pair file sizes once the October 2025 storage migration settles (milestone 2 only).
- The NOVAC Mayon SO2 flux dataset (CC BY 4.0 per the catalogue record): URL, years, format.
- The Smithsonian weekly reports as a 2000–2017 source for PHIVOLCS figures (milestone 2 only).
- Akari: whether synchronised multi-series charts with a shared time scrubber need a new Akari composite (an Akari change, not an app fork).
