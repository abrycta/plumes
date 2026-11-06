# Documentation

Status (2026-11-06): milestone 1 is live (map, 24 volcano timelines, generated stories). [DECISIONS.md](DECISIONS.md) records planning Q1–Q31, the spike (S1–S8), the build notes (B*), the layers plan (L1–L9) and the stories decisions (ST*). The scope is 24 sources queried in place (Q30, Q31); Google Open Buildings Temporal and the Lights link (night lights and poverty) follow at M1.1. The folder was renamed from `dataviz-next/` to `plumes/` on 2026-10-21.

Reading order:

1. [CANDIDATES.md](CANDIDATES.md): the six candidates (volcanoes, InSAR subsidence, air quality, coastal ecosystems, rice and drought, earthquakes) scored on data and licences, free-tier fit, honesty, interest, technical scope and risk, with the recommendation and reasons.
2. [RESEARCH.md](RESEARCH.md): the recommended candidate in depth: PHIVOLCS (what is public, the LAVA data policy, RA 8293), GVP, TROPOMI SO2, thermal anomalies (FIRMS, MODIS/VIIRS, MIROVA), InSAR (LiCSAR, COMET, HyP3), earthquakes (USGS, ISC, PHIVOLCS, GEM), exposure, existing products and interest, the safety and honesty rules, free tiers, runner-up outlines.
3. [ARCHITECTURE-OPTIONS.md](ARCHITECTURE-OPTIONS.md): three named patterns (static read models; plus a Java read API; a Rust core), the recommendation, the front end, the milestone-1 scope and the 60-second demo, the repository layout.
4. [DATA-PLAN.md](DATA-PLAN.md): the 24+1 sources and what reaches the browser, the processing path, the PHIVOLCS posture, the data model, hosting without a published dataset, the shared Earth Engine quota rule, the Java API on free tiers, the milestone-1 cut and the M1.1/M2 roadmap, size and quota totals, resources to create.
5. [LICENCES.md](LICENCES.md): the licence verification ledger for the 77 canvas sources plus the two Q31 additions (verdict, quoted clause with URL, attribution text), the in-scope set, the pages to re-read by hand.
6. [sources-draft.yaml](sources-draft.yaml): the registry draft (92 entries, one per source, with publisher, access, format, size, cadence, auth and licence; the chosen 24+1 marked `# chosen: true`), validated with `archivekit validate-registry` (kit v1.1.0) on 2026-10-21; moves to `pipeline/sources.yaml`.
7. [DECISIONS.md](DECISIONS.md): the log: Q1–Q31 answered on 2026-10-21, then spike addenda, build notes and the layers-plan answers (L1–L9).
8. [`research/`](research/): raw research notes per candidate and the platform-limits check, with a URL and access date on every claim (`volcanoes.md`, `subsidence-insar.md`, `air-quality.md`, `coastal-ecosystems.md`, `rice-drought.md`, `earthquakes-faults.md`, `platform-limits.md`).
9. [LAYERS-PLAN.md](LAYERS-PLAN.md): the layers after data v1: every candidate, the M2 and M3 shortlists, the deformation velocity layer spec, the Akari event-marker prerequisite, the M2 build order and its "ready to start" checklist.
10. [STORIES-PLAN.md](STORIES-PLAN.md): stories generated from data: the story data sources (ranked, with the coverage gain over the 241 episodes) and the standard story format (steps, EN/JA template catalogue, absent-data rule, images, review flow, schema changes, the Taal port), with open questions.

Conventions: plain English, facts with sources, dates in full, **[U]** for unverified items; other projects' documents are referenced by relative path (`../../lgu-lights/docs/`, `../../typhoon-replay/docs/architecture/`, `../../DATA-ARCHIVING.md`), never copied.
