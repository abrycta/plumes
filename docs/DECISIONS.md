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
