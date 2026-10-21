# Plumes (噴煙), planning folder `dataviz-next`

The next big-data map of the Philippines in the spirit of [Lights](https://lights.krtmtthw.dev): many public sources, a national map with a time series, honest uncertainty beside official figures, plain-language explanations, English and Japanese.

**Status (2026-10-21):** planning, decisions made, spike next. Kurt chose **Plumes: a retrospective record of the 24 active Philippine volcanoes** (a past record and visualisation only, never a hazard service; no dataset redistributed; DOST-PHIVOLCS named as the authority on every view): Smithsonian eruption history, the daily figures in DOST-PHIVOLCS's public bulletins as dated linked markers, Sentinel-5P SO2, MODIS/VIIRS thermal anomalies and MIROVA radiative power, earthquakes, Tokyo VAAC plume heights, DSWD evacuee counts, exposure rings, before/after imagery, and 60 more sources in later passes ([docs/LICENCES.md](docs/LICENCES.md), [docs/sources-draft.yaml](docs/sources-draft.yaml)). Architecture: static read models plus a read-only Java 17 API on PostGIS from milestone 1, React front end ([docs/DECISIONS.md](docs/DECISIONS.md)). Q19–Q29 await Kurt ([docs/OPEN-QUESTIONS.md](docs/OPEN-QUESTIONS.md)). No code, no external resources. The folder becomes `plumes/` when the repo is created.

Start with [docs/WORKFLOW.md](docs/WORKFLOW.md), then [docs/README.md](docs/README.md).

Workspace rules apply ([../CLAUDE.md](../CLAUDE.md)): `archivekit` for every external source, the Akari design system, free tiers only, commits as Kurt, secrets in the Keychain, a project page and share card, architecture before code, lean testing.
