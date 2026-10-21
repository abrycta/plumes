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
