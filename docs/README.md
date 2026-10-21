# Documentation

Status (2026-10-21): **planning, phase 1–3 done**. Six candidates researched and scored; volcanoes recommended; the deep plan is written for that candidate; Q1–Q18 are open for Kurt. No code, no external resources, no accounts. The folder is renamed once Q1 and Q2 are answered.

Reading order:

1. [WORKFLOW.md](WORKFLOW.md): how this project goes from idea to milestone 1 (phases, gates, documents, testing stance, page and share-card upkeep).
2. [CANDIDATES.md](CANDIDATES.md): the six candidates (volcanoes, InSAR subsidence, air quality, coastal ecosystems, rice and drought, earthquakes) scored on data and licences, free-tier fit, honesty, interest, showcase and risk, with the recommendation and its reasons.
3. [RESEARCH.md](RESEARCH.md): the recommended candidate in depth: PHIVOLCS (what is public, the LAVA data policy, RA 8293), GVP, TROPOMI SO2, thermal anomalies (FIRMS, MODIS/VIIRS, MIROVA), InSAR (LiCSAR, COMET, HyP3), earthquakes (USGS, ISC, PHIVOLCS, GEM), exposure, existing products and interest, the safety and honesty rules, free tiers, runner-up outlines.
4. [ARCHITECTURE-OPTIONS.md](ARCHITECTURE-OPTIONS.md): three named patterns (static read models; plus a Java read API; a Rust core), the recommendation, the front end, the milestone-1 scope and the 60-second demo, the repository layout.
5. [DATA-PLAN.md](DATA-PLAN.md): sources with kinds and licences, the processing path, the PHIVOLCS posture, the data model, sizes, versions and provenance, the InSAR outline, cadence and CI budget, resources to create.
6. [sources-draft.yaml](sources-draft.yaml): the registry draft, validated with `archivekit validate-registry` (kit v1.1.0) on 2026-10-21; moves to `pipeline/sources.yaml`.
7. [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md): Q1 (which candidate) to Q18, a recommendation each, the actions for Kurt, what to verify by hand.
8. [SPIKE-PLAN.md](SPIKE-PLAN.md): the one-day measurement spike before building.
9. [DECISIONS.md](DECISIONS.md): the log (empty until Kurt answers); spike addenda and build notes are appended there.
10. [`research/`](research/): the raw research notes per candidate and the platform-limits check, with a URL and access date on every claim (`volcanoes.md`, `subsidence-insar.md`, `air-quality.md`, `coastal-ecosystems.md`, `rice-drought.md`, `earthquakes-faults.md`, `platform-limits.md`).

Conventions: plain English, facts with sources, dates in full, **[U]** for unverified items; other projects' documents are referenced by relative path (`../../lgu-lights/docs/`, `../../typhoon-replay/docs/architecture/`, `../../DATA-ARCHIVING.md`), never copied.
