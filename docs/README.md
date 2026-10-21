# Documentation

Status (2026-10-21): **planning, phases 1–4 done; the spike is next.** Six candidates researched and scored; Kurt chose **volcanoes** and the name **Plumes**, then answered Q3–Q18 (architecture B from the start with a Java 17 API at M1, React front end, Q5 = cite only with no email, the shared `lgu-lights` Earth Engine account, no published dataset). The 77 sources of the approved design canvas are folded into the registry, their licences verified, and a milestone-1 cut proposed; Q19–Q29 are open. No code, no external resources, no accounts. The folder is renamed to `plumes/` when the repo is created.

Reading order:

1. [WORKFLOW.md](WORKFLOW.md): how this project goes from idea to milestone 1 (phases, gates, documents, testing stance, page and share-card upkeep).
2. [CANDIDATES.md](CANDIDATES.md): the six candidates (volcanoes, InSAR subsidence, air quality, coastal ecosystems, rice and drought, earthquakes) scored on data and licences, free-tier fit, honesty, interest, showcase and risk, with the recommendation and its reasons.
3. [RESEARCH.md](RESEARCH.md): the recommended candidate in depth: PHIVOLCS (what is public, the LAVA data policy, RA 8293), GVP, TROPOMI SO2, thermal anomalies (FIRMS, MODIS/VIIRS, MIROVA), InSAR (LiCSAR, COMET, HyP3), earthquakes (USGS, ISC, PHIVOLCS, GEM), exposure, existing products and interest, the safety and honesty rules, free tiers, runner-up outlines.
4. [ARCHITECTURE-OPTIONS.md](ARCHITECTURE-OPTIONS.md): three named patterns (static read models; plus a Java read API; a Rust core), the recommendation, the front end, the milestone-1 scope and the 60-second demo, the repository layout.
5. [DATA-PLAN.md](DATA-PLAN.md): the source families and what reaches the browser, the processing path, the PHIVOLCS posture, the data model, hosting without a published dataset, the shared Earth Engine quota rule, the Java API on free tiers, the milestone-1 cut and the M2–M4 roadmap, size and quota totals, resources to create.
6. [LICENCES.md](LICENCES.md): the licence verification ledger for the 77 canvas sources (verdict, quoted clause with URL, attribution text), what changed from the canvas, the pages to re-read by hand.
7. [sources-draft.yaml](sources-draft.yaml): the registry draft (90 entries, one per source, with publisher, access, format, size, cadence, auth and licence), validated with `archivekit validate-registry` (kit v1.1.0) on 2026-10-21; moves to `pipeline/sources.yaml`.
8. [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md): Q1–Q18 as history; Q19–Q29 open, a recommendation each, the actions for Kurt, what to verify by hand.
9. [SPIKE-PLAN.md](SPIKE-PLAN.md): the one-day measurement spike before building (items 13–18 added for the Java slice, the shared quota and the M1 sources).
10. [DECISIONS.md](DECISIONS.md): the log: Q1–Q18 answered on 2026-10-21; spike addenda and build notes are appended there.
11. [`research/`](research/): the raw research notes per candidate and the platform-limits check, with a URL and access date on every claim (`volcanoes.md`, `subsidence-insar.md`, `air-quality.md`, `coastal-ecosystems.md`, `rice-drought.md`, `earthquakes-faults.md`, `platform-limits.md`).

Conventions: plain English, facts with sources, dates in full, **[U]** for unverified items; other projects' documents are referenced by relative path (`../../lgu-lights/docs/`, `../../typhoon-replay/docs/architecture/`, `../../DATA-ARCHIVING.md`), never copied.
