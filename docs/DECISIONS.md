# Decisions

The log for this project: Kurt's answers to [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md), then spike addenda (S1, S2, …) and build notes (B1, B2, …). Never rewritten, only appended. Each entry has a date, the decision and the reason where one was given.

## 2026-10-21: Q1 and Q2

| # | Decision | Reason given |
|---|---|---|
| Q1 | **Volcanoes.** A retrospective record of Philippine volcanoes: a past record and visualisation only, never a hazard service. No dataset is redistributed; the site shows derived per-volcano summaries with their sources. | Kurt's own idea; recommended in [CANDIDATES.md](CANDIDATES.md) §8 |
| Q2 | **Plumes** (噴煙). Folder `plumes/`, domain `plumes.krtmtthw.dev`, repos `abrycta/plumes` and `abrycta/plumes-archive`. | Short, plural like Lights, says what the satellites see |

The design canvas Kurt approved the same day (overview map, volcano page, Taal January 2020 story, phone view, and the sources page with a core record plus nine passes, 77 sources) is the product reference; its source list is folded into [sources-draft.yaml](sources-draft.yaml), [LICENCES.md](LICENCES.md) and [DATA-PLAN.md](DATA-PLAN.md).

## 2026-10-21: Q3 to Q18

Answers that differ from the defaults in [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md) are marked **(not the default)**.

| # | Decision | Reason given |
|---|---|---|
| Q3 | **Architecture B from the start (not the default).** The read-only Java 17 Spring Boot API on PostGIS is part of milestone 1, not milestone 2 or 3. The static read models still carry the map and the per-volcano views; the site works with the API deleted. | Kurt's choice; the API shows the relational, spatial-temporal side of the data (ARCHITECTURE-OPTIONS.md §3) |
| Q4 | **Python (uv) pipeline + React 19/TypeScript front end (Vite, Akari, MapLibre) + Java 17/Spring Boot/MyBatis API at M1. No Rust.** | Kurt: "use React for the front end"; Java at M1 follows from Q3 |
| Q5 | **(ii) (not the default):** cite every PHIVOLCS value with its bulletin link, publish no PHIVOLCS bulk file, and send **no email** to PHIVOLCS. | Kurt's choice |
| Q6 | All 24 volcanoes on the map; deep series where bulletins exist, with an explicit note where they do not. | default |
| Q7 | 2000 to the snapshot date, each series starting when its instrument does, stated per chart. | default |
| Q8 | InSAR as links (COMET portal, PHIVOLCS deformation sentences) at M1; the Taal LiCSBAS crop at M2. | default |
| Q9 | National monthly SO2 and thermal layers at M1 if spike items 2 and 7 pass; otherwise series first, layers at M1.1. | default |
| Q10 | deck.gl only if the spike shows MapLibre stutters (spike item 7). | default |
| Q11 | **Reuse the existing `lgu-lights` Earth Engine service account (not the default)**, Keychain `earth-engine-sa-key`, sharing that project's 150 EECU-hour monthly Community quota. Plumes is budgeted so it cannot starve Lights' runs: see [DATA-PLAN.md](DATA-PLAN.md) §7. | Kurt's choice; one registration to re-verify, one key to rotate |
| Q12 | Tiles and large files on GitHub Pages (primary) with Hugging Face as hosting fallback only; no Cloudflare R2. | default |
| Q13 | archivekit's adopt path for crawled bundles now; file the `collection` kind as a kit issue. | default |
| Q14 | Never show a "current" alert level; the history ends at the snapshot, labelled "as reported by PHIVOLCS on <date>", under the banner. | default |
| Q15 | **No published dataset (not the default):** no public Hugging Face dataset, no Zenodo DOI. Files on Hugging Face exist purely as hosting and fallback for the app. See [DATA-PLAN.md](DATA-PLAN.md) §5 for the private-versus-public repo question this raises. | Kurt's choice |
| Q16 | English and Japanese; no Filipino. | default |
| Q17 | The milestone-1 scope of ARCHITECTURE-OPTIONS.md §6, plus the Java API (Q3). | default plus Q3 |
| Q18 | A one-day measurement spike before building ([SPIKE-PLAN.md](SPIKE-PLAN.md)). | default |

Consequences recorded the same day: the action items for a new Earth Engine project and for the PHIVOLCS email are removed from OPEN-QUESTIONS.md; ARCHITECTURE-OPTIONS.md keeps the three options as written history with the choice marked; the Java slice gets its own spike items; the milestone plan and the source cut are in [DATA-PLAN.md](DATA-PLAN.md) §9.

## 2026-10-21: Q19 to Q31

Kurt, the same day: **"go ahead with everything."** That accepts the recommendation on file for every open question. Q30 and Q31 change the source set, so several of Q19–Q29 are answered against the new set rather than the 86-entry plan they were written for; where that makes a question moot or changes its premise, the row says so.

| # | Decision | Note |
|---|---|---|
| Q30 | **(a) The 20 sources, queried in place** ([NO-DOWNLOAD-ALTERNATIVES.md](NO-DOWNLOAD-ALTERNATIVES.md); 21 registry entries, USGS split in two). Black Marble (now on Earth Engine) and the Lights poverty join move to **M1.1**; the S5P aerosol index and GPM IMERG stay at M2. Every other registry entry is out of scope and kept as history. MIROVA's role (radiative power) goes to the MOD14A1 and VNP14A1 **MaxFRP** on Earth Engine | recommendation |
| Q31 | **(b) Add A1–A4 now: 24 sources.** OMI SO₂ `OMSO2e` through Harmony/OPeNDAP (SO₂ track from 2004-10), MEaSUREs `MSVOLSO2L4` (SO₂ mass per eruption), Landsat C2 L2 on Earth Engine (before/after and crater-lake temperature from 2000), Sentinel-1 GRD on Earth Engine (before/after through the 2020 ash). **A5, Google Open Buildings 2.5D Temporal, at M1.1** beside Black Marble and the Lights poverty join: **25**. The (b) nice-to-haves are held | recommendation |
| Q19 | **(a)** a public, files-only Hugging Face repo `permission-alluring/plumes` as the hosting mirror, its README saying it is not a dataset release; no licence tag, no DOI. Unchanged by the cut; it holds only what GitHub Pages already serves | recommendation |
| Q20 | **(a)** a second free Render web service `plumes-java` in the shared workspace, prebuilt GHCR image, no pinger, sleep after 15 minutes, one nightly contract check, edge cache in front. Created only after spike items 13 and 15, and only on the free plan | recommendation |
| Q21 | **Own free Neon project** `plumes` (Singapore, PostGIS). The cut lowers the catalogue estimate to about 100–200 MB **[U]** | recommendation |
| Q22 | **Accept the DATA-PLAN.md §7 rule** (Plumes ceiling 50 EECU-hours a month, 10 per run, chunked backfill, Sunday window) and **create a second service account** with its own key `earth-engine-sa-key-plumes` when the repo exists (Kurt's action). The cut lowers the backfill to about 6–7 EECU-hours at M1 and about 10–12 for the roadmap **[U]** | recommendation |
| Q23 | **Premise changed.** The 11-row, 25-entry M1 cut is replaced by the 24 sources (DATA-PLAN.md §9). VAAC, DROMIC and ERA5 stay at M1, as the recommendation wanted; MIROVA, GHSL, WorldCover, PSGC, GEM faults and the HazardHunterPH entry leave (HazardHunterPH stays a link) | the recommendation's intent holds |
| Q24 | **Moot.** The PHIVOLCS monthly earthquake tables are cut by Q30, not deferred to M1.1. USGS plus the bulletins' volcanic-earthquake counts carry the track | Q30 |
| Q25 | **Mostly moot.** IOC, DAHITI, Raspberry Shake, Global Fishing Watch and LaMEVE are all out of scope. What remains is the About-page statement that Plumes is a non-commercial site, which GVP's Smithsonian terms (non-commercial with citation) still need | Q30 |
| Q26 | **Moot.** Himawari event replays are cut (no query route for past dates; 780 MB scans) | Q30 |
| Q27 | **Mostly moot.** Every hand-collected source (PSA, PSGC xlsx, DOH, NDRRMC, Slab2, GEBCO, EMSR418) is out of scope. What remains is Kurt re-reading the GVP terms page by hand, plus the checklist-and-adopt path kept in reserve | Q30 |
| Q28 | **Only M1's registrations: the FIRMS MAP_KEY** (Keychain `firms-map-key`), Kurt's action. **The Earthdata login returns** for A1 and A2 (the login exists; CI already mints short-lived tokens from it for Lights). OpenAQ, ReliefWeb, OpenAlex, ECMWF, Copernicus Marine, IOC, DAHITI and EROS fall away. The second Earth Engine service account is Q22 | Q30, Q31 |
| Q29 | **Taal January 2020 at M1, Kanlaon 2024 at M1.1** on the same machinery | recommendation |

Consequences recorded the same day: DATA-PLAN.md (§0–§2, §4, §7, §9–§11), LICENCES.md (out-of-scope marks; entries for OMSO2e and Open Buildings Temporal), SPIKE-PLAN.md (items 6 and MIROVA's half of 9 removed, item 17 corrected to Tokyo VAAC and DROMIC docx, items 19–27 added), [sources-draft.yaml](sources-draft.yaml) (the chosen set marked `# chosen: true`, two entries added: `omi-omso2e`, `open-buildings-temporal`) and both READMEs are aligned with the 24+1 set. Out-of-scope sources stay in the registry and the licence ledger as history. For the InSAR crop at M2 (Q8, unchanged), the ARIA S1 GUNW range read (NASA-EE-CANDIDATES.md B6) is noted as the preferred route; it is not a source until M2 starts. Still Kurt's: the FIRMS MAP_KEY, the GVP terms re-read, permission for the spike to read NASA files with the Earthdata token, and the go-ahead for the throwaway Render service and Neon project of spike items 13–15.

## 2026-10-22: spike addenda S1 to S8

From [SPIKE-RESULTS.md](SPIKE-RESULTS.md) Runs 1 and 2. These change the plan where a measurement now exists; they are recommendations recorded from the spike, and the ones marked **(Kurt)** need his choice.

| # | Change | Measurement behind it |
|---|---|---|
| S1 | **The PHIVOLCS WordPress crawl shrinks to the English prose bulletins, 2017-09 → 2023 (about 5,300 pages, 1.5 h at 1 request/s).** The English and Filipino "Summary of 24hr Observation" pages from 2021-10 are empty shells and are not crawled; the archive keeps the extracted `entry-content` block and the page hash, not the 82 kB page | Run 2, item 4 |
| S2 | **PHIVOLCS-LAVA carries everything from mid-2022.** The crawler pins the GlobalSign intermediate (the server omits it) and takes the id → volcano map from the daily list page, never from the URL path or heading, which the server does not check. History before the crawler starts needs another id → volcano map: **open**, to be settled before M1's LAVA backfill (candidate: the fixed daily order of the four ids; to be verified against list pages archived by the Wayback Machine). The gap 2021-10 → 2022-06 (WordPress summaries empty, LAVA not yet live) is shown as a gap unless the Filipino pages fill it (unchecked) | Run 2, item 5 |
| S3 | **VAAC and DROMIC parsers go ahead at M1** (VAAC heights 21/21 applicable advisories; DROMIC grand totals 3/3). DROMIC Report #1 (`.doc`) is hand-entered | Run 2, item 17 |
| S4 | **ERA5 winds stay at M1, read 6-hourly** through a Blosc block-range reader of ARCO-ERA5 (33 MB and 18 s for the two days with 8 parallel requests; a plain Zarr read would move about 11 GB). M1 adds a check that decodes one whole chunk and compares | Run 2, item 18 |
| S5 | **Per-volcano JSON: keep daily columns and one bulletin row a day.** Taal over the full span is 49 kB gzip, so the 80 kB (120 kB deep-volcano) budget stands without trimming | Run 2, item 8 |
| S6 | **Neon: Plumes' catalogue is about 220 MB with indexes**, the three M1 queries run in under 0.3 ms on the server. Q21 (own free Neon project) stands; detections can stay in PostGIS | Run 2, item 14 |
| S7 | **The Java API's cold start on Render free is the open risk (Kurt).** At Render free's 0.1 CPU the Spring Boot JVM needs about 78 s to `/readyz` with CDS (96 s without), before Render's own wake, so the 90 s bar likely fails. Options, in the order recommended: (a) keep Java 17 + Spring Boot and build a **GraalVM native image** (Spring Boot 3 supports it; MyBatis needs its native hints), then re-measure; (b) accept the slow first request: the site never waits on the API (Q3), and the UI says "waking the API"; (c) a Go or Node API instead of Java, which drops Q3/Q4's stated reason for the API. The Render measurement itself is still owed: it needs a pullable image, and pushing to the anonymous ttl.sh registry was denied in this session, so Kurt chooses the route (allow ttl.sh, or a private GHCR image with a Render registry credential) before item 13 and the edge-cache item 15 run | Run 2, item 13 (local, 0.1 CPU, 512 MB, amd64 under emulation) |
| S8 | **Earth Engine: the series backfill is about 3 EECU-hours** (3.0 EECU-s per volcano-month measured), half the estimate. Per-run accounting uses the EE profiler and task `batch_eecu_usage_seconds`; the project's monthly total cannot be read by API without billing, so Kurt reads it in the console before each backfill chunk | Run 2, items 1 and 16 |

## 2026-10-22: build notes B1 to B9 (M1 pipeline)

Kurt approved M1 on 2026-10-22: the repos `abrycta/plumes` (public) and `abrycta/plumes-archive` (private), and the Java API as a GraalVM native image on a private GHCR image (S7 option a; built by the API work, not here). Facts found while building the pipeline:

| # | Note | Evidence |
|---|---|---|
| B1 | **S2's open question is settled: the LAVA id → volcano map comes from the portal's own archive search** (`/bulletin/list-of-bulletin?vdId=<id>&type=bulletin&sdate=…&edate=…`; vdId Bulusan 571, Hibok-hibok 562, Kanlaon 565, Mayon 574, Pinatubo 583, Taal 580). It returns (volcano, type, date, bid) rows, at most 30 per query, newest first, so the crawler queries 15-day windows and halves any full one. It covers the history from 2022 as well, so no id sweep and no "fixed daily order" guess; the weekly delta re-queries the last three weeks (no daily list-page poll) | `plumes/crawl/lava.py`; Taal 2022-07-02 = bid 1259, as in the spike |
| B2 | The LAVA leaf certificate expires **2026-11-19**; the pinned GlobalSign "RSA OV SSL CA 2018" intermediate (valid to 2028-11-21) must be replaced if the renewed leaf has another issuer | `plumes/http.py`, `plumes/certs/` |
| B3 | **COD-AB:** the registry entry now describes the range read (the zip is 928,515,157 bytes; 7 requests, 121,632 bytes for `phl_admin3.dbf`); the zip is never downloaded or archived, the extracted table is adopted | `plumes/codab.py` |
| B4 | **Earth Engine:** many concurrent `reduceRegions` are refused ("Too many concurrent aggregations"), so a month is one aggregation: the daily S5P means are stacked as bands and reduced once over all 24 × 5 rings. Measured: **87 EECU-s per month for SO₂** (24 volcanoes, rings 5/10/15/30 km plus the 50 km box) and **64 EECU-s per month for fire** (MOD14A1, VNP14A1, FIRMS; 5/10/15 km). Full backfill about 2.3 + 5.5 EECU-h, run as three runs under the 10 EECU-h per-run cap. Per-run accounting reads the EE profiler; the ledger `ee-usage.json` is published with each version | `plumes/ee_series.py`, `plumes/ee_budget.py` |
| B5 | **FIRMS `type` coding:** 0 presumed vegetation fire, **1 active volcano**, 2 other static land source, 3 offshore (SPIKE-RESULTS Run 1 wrote "2 = active volcano"; the Taal rows carry 1). The FIRMS area API answers each 5-day call with a CSV without a trailing newline, so responses are split on the header | `plumes/firms.py` |
| B6 | **ERA5:** the story needs one grid point, so the reader fetches one Blosc block per level instead of a ±2° window (Taal 11–15 Jan 2020, 6-hourly, four levels: 243 requests, 84 MB). The S4 check passes: the block reader equals a full numcodecs decode of the same chunk | `plumes/era5.py --verify` |
| B7 | **GitHub Pages** for the data files serves at `https://krtmtthw.dev/plumes/data/`, because the user site carries the apex custom domain; no DNS record changes, and the project page stays at `/projects/plumes/`. The Hugging Face mirror is `permission-alluring/plumes` (a dataset repo used only as a files mirror, README says so, no licence tag) | `plumes/publish.py` |
| B8 | **Crawled bundles and query results** are adopted into `abrycta/plumes-archive` by `plumes/adopt.py` (the kit's tag and asset layout: `<id>-<date>`, `<id>.tar.zst`, `SHA256SUMS`, `manifest.json`; draft first); the four `file` sources were snapshotted by `archivekit snapshot` itself. A kit-level `collection` kind stays the Q13 follow-up | — |
| B9 | **CI tokens still needed (Kurt):** `ARCHIVE_READ_TOKEN` (fine-grained; Contents read on `data-archive-kit` and `plumes-archive`, Issues read/write on `plumes-archive`; in both repos) lets the weekly `data.yml` install the kit and restore state; `ARCHIVE_WRITE_TOKEN` (Contents read/write on `plumes-archive` only) lets CI adopt new bundles. Until they exist, `data.yml` skips with a notice and versions are built by hand | `.github/workflows/data.yml` |
| B10 | **Data version v1 published 2026-10-22** (`dataAsOf` 2026-10-22; 58 files, 26 MB; 82 of 82 checks passed): `https://krtmtthw.dev/plumes/data/latest.json` and the Hugging Face mirror. Earth Engine used for the whole M1 backfill: **6.21 EECU-hours** (S5P 2.3, fire 3.9, exposure and trials 0.05) in five runs, none above 10; the ledger is `data/ee-usage.json` on Pages | `v1/manifest.json` |
| B11 | **Coverage facts from the full crawl:** the WordPress sitemaps have no Taal posts before 2019, so Taal's bulletin record starts 2019-03-28 (Mayon, Kanlaon, Bulusan from 2017-09); 5,290 WordPress pages and 6,084 LAVA bulletins fetched with no failed request; per day, the row is the latest page that reports an alert level, every field from that one page; some slugs use Filipino month names (`enero`, `pebrero`, `marso`). VAAC: 2,105 Philippine advisories since 2010, 1,217 with a height (164 observed, 1,053 reported), the rest "VA CLD UNKNOWN". DROMIC Taal 2020: 69 of 70 reports parsed (#1 is `.doc`) | `plumes/parse.py` |
| B12 | **FIRMS area API:** VIIRS calls take about 35 s each and the key's transaction limit weighs by size ("Exceeding allowed transaction limit"); the client now waits out the 10-minute window. Year ranges can run in parallel; detections are de-duplicated on (product, lat, lon, date, time, satellite). 649,248 detections (MODIS 2000-11 → 2026-07, VIIRS 2012-01 → 2026-06) | `plumes/firms.py` |

## 2026-10-22: build notes B13 to B18 (live on the published data)

Kurt approved the same day: the site and the API switch from the fixtures to the published data, the reviewed story text, and an end to the archive's repeat snapshots.

| # | Note | Evidence |
|---|---|---|
| B13 | **The site reads the published versions**: `web/public/config.json` points at `https://krtmtthw.dev/plumes/data/` with the Hugging Face mirror as fallback. The fixtures are served only to tests and offline development (`PLUMES_FIXTURES=1`), never deployed. The CSP adds `https://krtmtthw.dev` (connect and img). GitHub Pages answers a single-range `Range` request with 206 and `Access-Control-Allow-Origin: *` but refuses CORS preflights (405), so PMTiles reads rely on browsers treating a single byte range as a safelisted header; the HF mirror (`*.hf.co`) answers both | `web/public/_headers`, `scripts/vite-fixture-data.ts` |
| B14 | **Bulletin parser fixes found in the real data, no contract change:** a notice of change ("raising … from Alert Level 3 (magmatic unrest) to Alert Level 4") now reports the new level (v1 had Taal at level 3 on 12 January 2020 although the 7:30 PM bulletin raised it to 4); a running total ("since 28 March 2019 … recorded 4857 volcanic earthquakes") is no longer a bulletin's count; when the English and Filipino editions share an hour, the English one is the day's row | `plumes/parse.py`, `tests/test_parse.py` |
| B15 | **Story text reviewed by Kurt (data version v2):** every number in the Taal 2020 story is read from the volcano read model (Alert Level 1 through 11 January; TROPOMI December median 25 µmol/m²; no USGS earthquake within 30 km after 11 October 2019, then 35 on 12 January; level 4 in the 7:30 PM bulletin of 12 January, as reported by PHIVOLCS); dates are written as words (EN "7 September 2020", JA 2020年9月7日); steps are `reviewed`. The Taal reading on the volcano page keeps its v1 draft text until Kurt reviews it. New checks: no English words or ISO dates in the story's Japanese text; every step reviewed | `plumes/readmodels.py` |
| B16 | **The API reloads after every Data run** (`.github/workflows/api-load.yml`, also by hand): the published data root plus the latest archived `usgs-comcat-ph-*` and `firms-modis` snapshots, in one transaction; secret `NEON_DATABASE_URL`. The published earthquake layer is PMTiles, which the loader does not read, so the archived ComCat CSVs (the files the version was built from) stay the earthquake source | `api-load.yml`, `api/…/load/Loader.java` |
| B17 | **The archive no longer re-snapshots unchanged GVP data.** GeoServer's WFS CSV starts with an `FID` column of feature ids generated on every request (`…fid-5949073e_1a16163f341_-673`), so each run hashed different bytes and published `.2`, `.3` releases. archivekit 1.2.0 adds the built-in `csv-drop-columns` transform; both GVP links drop `FID` | `sources.yaml`, data-archive-kit v1.2.0 |
| B18 | **Volcano pages say why a series is empty** ("Nothing to show, and why"): no bulletins issued, no VAAC advisory since 2010 (or no GVP number to match), not in GVP's Holocene list, DROMIC for Taal 2020 only, nothing detected within the ring since the instrument record starts. Long spans draw dense markers as a tick strip and the axis in years. The map reads the published layers as they are (`{year}` PMTiles filtered on `month`; the earthquake layer added beside thermal detections) and opens on the month of the most recent GVP eruption | `web/src/data/tracks.ts` `absentRecords`, `web/src/volcano/Timeline.tsx` |

## 2026-10-22: layers plan L1 to L9

Kurt's answers to the nine questions of [LAYERS-PLAN.md](LAYERS-PLAN.md) §5 (written as L1–L9 there; they were not in OPEN-QUESTIONS.md). The plan's build order (§7) and its "ready to start" checklist (§8) follow from them.

| # | Decision | Note |
|---|---|---|
| L1 | **Email COMET before publishing any COMET-derived data.** The draft is [research/comet-licence-email.md](research/comet-licence-email.md); Kurt sends it. No COMET file is published until the reply is recorded here | The portal's CC BY-NC 4.0 covers its images; the JSON files carry no licence of their own |
| L2 | **COMET LiCSBAS series for all 18 covered volcanoes at M2. This supersedes Q8's Taal-only crop** and the ARIA S1 GUNW route noted in "Q19 to Q31" | ARIA GUNW covers only Taal, Pinatubo and Banahaw and ends 2025-09-15 |
| L3 | **Deformation: a LOS chart per volcano and a velocity map layer**, new layer id `deformation-velocity` (contract change in `contracts/schemas/layers.schema.json` and `contracts/ts/readmodels.ts`, approved by Kurt before it is built; spec in LAYERS-PLAN.md §3.1) | the per-volcano series needs no contract change |
| L4 | **IMERG rain on Earth Engine**, one month measured before the backfill | simplest route; 1–3 EECU-h estimated |
| L5 | **NOAA-20 VIIRS thermal as its own series** with a sensor-change marker at the S-NPP → NOAA-20 switch. Akari has no dated marker on its charts, so an Akari addition is a prerequisite (LAYERS-PLAN.md §6) | S-NPP deliveries end 2026-11-01 |
| L6 | **Lahar rivers excluded** (moved to the rejections) | too close to a hazard map for a site that is not a warning service |
| L7 | **OSM school and hospital counts at M3 only with a clear "as of <date>" label** | a snapshot of today, not history |
| L8 | **ISC licence: checked by hand later; not needed for M2.** Stays open | its site returned 404 on 2026-10-22 |
| L9 | **One read of `MSAQSO2L4` allowed; done.** It lists 7 Philippine sources: Mayon, Bulusan, Kanlaon and "Taai" (presumably Taal) **[U]**, plus three power plants (Sual, Masinloc, Mariveles). Per-year values not yet read | the one 1.7 MB file, read with the Earthdata token; nothing else downloaded |

## 2026-10-22: layers plan revisions L1a, L3a, L9a; Taal reading reviewed

| # | Decision | Note |
|---|---|---|
| L1a | **Supersedes L1: no email to COMET.** The COMET Volcano Portal's CC BY-NC 4.0 notice is treated as covering the LiCSBAS data; Plumes publishes the derived series and velocity layer with attribution to COMET, the LiCSAR Copernicus acknowledgement and the CC BY-NC 4.0 notice (wording in LICENCES.md). The draft [research/comet-licence-email.md](research/comet-licence-email.md) is kept, marked "not sent — decided 2026-10-22" | Kurt's choice |
| L3a | **The `deformation-velocity` contract change is approved** as specified in LAYERS-PLAN.md §3.1 (`layers.schema.json` enum, `LayerId`, `{frame}`, `frames`). It is built with M2 step 9, not now | Kurt's approval |
| L9a | **Agents may install `h5py` in the plumes environment**, for reading the `MSAQSO2L4` per-year values at M3. Nothing is run now | the earlier install was refused by the permission check |
| L10 | **The `deformation-velocity` coherence floor is 0.2** (LAYERS-PLAN §3.1), not the planned 0.3, which left a speckled map | canary 2026-10-22, Taal 032D: 1,983 of 8,811 COMET-valid pixels kept at 0.2, 1,230 at 0.3 |
| L11 | **The Taal deformation fixture may be committed** to the public repo (CC BY-NC 4.0, with its attribution beside it: `contracts/fixtures/data/v0/layers/deformation/ATTRIBUTION.md`) | COMET is listed in LICENCES.md (`comet-licsbas`) |
| T1 | **The Taal reading on the volcano page is reviewed** (`status: reviewed`, published with the next data version). Its Japanese height gloss reads （約16.8 km） in full-width brackets instead of the English "(about 16.8 km)"; the story's other Japanese glosses use full-width brackets too. The version check now also rejects half-width brackets and English left in the reading's Japanese text | `pipeline/plumes/readmodels.py` (`fl_gloss`, `ja_leftovers`), `pipeline/tests/test_text.py` |


## 2026-10-22: stories plan ST1 to ST11; phone embed P1

Kurt's answers to the 11 open questions of [STORIES-PLAN.md](STORIES-PLAN.md) (written there as questions 1–11; they were not in OPEN-QUESTIONS.md). Stories are generated from data with fixed EN/JA templates; nothing is built yet. Answers that differ from the plan's recommendation are marked **(not the default)**.

| # | Decision | Note |
|---|---|---|
| ST1 | **Stories stay hidden on the site until every step is reviewed.** Drafts stay in the data files, marked `draft`, for the review page | STORIES-PLAN §B6 |
| ST2 | **The Smithsonian/USGS Weekly Volcanic Activity Reports are crawled from Wayback snapshots** while volcano.si.edu refuses scripts (403 on 2026-10-22). PHIVOLCS figures quoted in them may be used, attributed **"as reported by PHIVOLCS, via Smithsonian/USGS"** (JA 「（PHIVOLCS発表、スミソニアン/USGS経由）」), each with the report's link | Q5 (ii) satisfied by citing the weekly report's link |
| ST3 | **Steps: before → onset → course → after**; the peak is a highlighted figure, not a step | STORIES-PLAN §B2 |
| ST4 | **Taal's "lake drained" line is sourced from the weekly report** (15–21 January 2020, "Satellite images showed that the Main Crater lake was gone"): a `lake_gone` extraction rule and template WEEKLY-LAKE-GONE. The reviewed Taal crater step changes once and is reviewed again | replaces the hand-written sentence |
| ST5 | **Story-worthy = at least 4 fact kinds with sentences in before, onset and after; pre-2000 events get deep-time cards**, not stories | 25 → 44 episodes with the shortlist (STORIES-PLAN §A3) |
| ST6 | **A GVP eruption and its overlapping alert window merge into one story** (42 events since 2000) | STORIES-PLAN §B1 |
| ST7 | **Shared story code moves to a new private `abrycta/story-kit` when a second project needs it.** The workspace-level `STORY-FORMAT.md` is a planned item only, not written now | until then STORIES-PLAN.md is the specification |
| ST8 | **ReliefWeb stays out for now** (its API needs an approved appname) | — |
| ST9 | **(not the default) Rain is shown whenever IMERG data exists**, not only beside a reported lahar. It is worded as context without implying a cause: its own sentences (RAIN-TOTAL, RAIN-WETTEST), never joined to an eruption, ash or lahar fact; the checks reject causal words in them. It does not count towards the story-worthy score | STORIES-PLAN §B3, §B4, §B6 |
| ST10 | **GDACS is not used at all**, not even its GLIDE ids as links | its content is an alert colour from a warning system |
| ST11 | **`pdfplumber` may be added to the pipeline** for the DROMIC PDF reports | DROMIC generalised to 16 events |
| P1 | **The Plumes phone embed stays Luzon–Visayas with the data layers** | Kurt, 2026-10-22 |

## 2026-10-23: story drafts ST12 to ST14

Kurt's decisions on the first generated drafts (Kanlaon 2024 and Taal 2020, PR #27).

| # | Decision | Note |
|---|---|---|
| ST12 | **A generated step renders as a list, one short line per fact** (and one per missing-record line), not as a paragraph | compact, workspace rule 28; hand-built steps keep their paragraph |
| ST13 | **No "people nearby" sentence in stories** (template POP-RING removed, with the population-ring override) | the volcano page already shows the WorldPop rings |
| ST14 | **The Japanese templates keep the plain form** (〜した／だった), as in the reviewed Taal text | not です・ます |

## 2026-10-23: OMI SO₂ dropped

| # | Decision | Note |
|---|---|---|
| L-OMI | **OMI SO₂ (`omi-omso2e`, series `so2_omi_box`) is dropped** (Kurt, 2026-10-23): no OMI data is published; `plumes.omi`, its `data.yml` step and the web wording are removed, and the registry entry is marked rejected | SO₂ stays TROPOMI (`s5p-offl-so2`, from 2018-12) and MSVOLSO2L4 (`nasa-msvolso2l4`, eruption masses); the backfill was slow (about 20 min a year in Harmony) and never reached a version |

## 2026-10-23: stories publish automatically and stay stable across data updates (ST15)

Why: data v7 (CI trial run 39893964947) filled a gap in Kanlaon's 2024 bulletins; its event merged into the alert window still open in 2026, was renamed `kanlaon-2024` and dropped as open, and the #1 story vanished. The same could follow from any gap filled later, an id derived from how many events a year has, windows clipped by a new neighbour, or a changed number under the review hash. Kurt: "drop the manual review for me for plumes."

| # | Decision | Note |
|---|---|---|
| ST15 | **No manual review** (supersedes ST1): a story is public when the generator's automated checks pass (the story bar: 4 fact families, facts in before, onset and after; no template or schema error). Its text updates with the data | `review.yaml` and the hash gate are removed; `status: reviewed` in the data now means "passed the checks"; the hand-built Taal 2020 stays as it is |
| ST15a | **Stable ids**: a story public in the previous published version keeps its id; it claims the event at its volcano that holds its onset date, and no other event takes that id | read from the published `latest.json` version, the same for CI and local builds |
| ST15b | **An alert window still open at the end of the data counts for 90 days from its start** (as an open GVP episode counts for 30) | a raised level that lasts years never stretches an event or pulls a later eruption into it; the per-story Kanlaon `after_end` pin is removed |
| ST15c | **A public story may leave only with a data-driven reason** (below the story bar, no event holds its onset, its volcano is gone, still open), logged as a check and a CI warning; any other loss fails the build | nothing is published from a failed build |

## 2026-10-23: storage of published versions (S1, S2)

Options and measurements: [`architecture/STORAGE-OPTIONS.md`](architecture/STORAGE-OPTIONS.md). Kurt chose "A1 now, then C".

| # | Decision | Note |
|---|---|---|
| S1 | **Stable tile bytes (option A1):** tippecanoe gets a fixed name and description and runs on paths relative to its work folder, so a PMTiles file whose tiles did not change is byte-identical across versions and no local build path reaches its metadata | `readmodels.tippecanoe`; the build check "no local path in any published file" (`plumes.leaks`) blocks publishing; `tests/test_stable_files.py` |
| S2 | **Published versions saved as release assets (option C's release step, no pruning):** after each publish, release `data-v<N>` in `abrycta/plumes-archive` (`v<N>.tar.zst`, `.sha256`, `manifest.json`), downloaded again and hash-checked; a trial run saves under `trial-data-v<N>-run<id>` and deletes it. The Data run also measures HF `usedStorage` (trigger 2 GB) and the `abrycta/plumes` repo size (trigger 500 MB), internal warning and health issue only. Pruning, squash and D wait for a trigger | `plumes.release` (`save`, `restore`), `plumes.storage`, `data.yml`; recovery in `pipeline/README.md` |
