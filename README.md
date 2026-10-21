# dataviz-next (working name; proposed: Plumes)

The next big-data map of the Philippines in the spirit of [Lights](https://lights.krtmtthw.dev): many public sources, a national map with a time series, honest uncertainty beside official figures, plain-language explanations, English and Japanese.

**Status (2026-10-21):** planning. Six candidate topics were researched and compared ([docs/CANDIDATES.md](docs/CANDIDATES.md)); the recommendation is **a dated retrospective, multi-sensor record of the 24 active Philippine volcanoes** (Kurt's idea): Smithsonian eruption history, the daily figures DOST-PHIVOLCS reports in its public bulletins, Sentinel-5P SO2, MODIS/VIIRS thermal anomalies and MIROVA radiative power, earthquakes within 30 km, exposed population, and later Sentinel-1 InSAR. It is never a monitoring or alert service: DOST-PHIVOLCS is named as the authority on every view. The plan for it is written; Q1–Q18 await Kurt's answers ([docs/OPEN-QUESTIONS.md](docs/OPEN-QUESTIONS.md)). No code, no external resources. The folder is renamed once the topic and name are picked.

Start with [docs/WORKFLOW.md](docs/WORKFLOW.md), then [docs/README.md](docs/README.md).

Workspace rules apply ([../CLAUDE.md](../CLAUDE.md)): `archivekit` for every external source, the Akari design system, free tiers only, commits as Kurt, secrets in the Keychain, a project page and share card, architecture before code, lean testing.
