# Plumes (噴煙)

The next big-data map of the Philippines in the spirit of [Lights](https://lights.krtmtthw.dev): many public sources, a national map with a time series, honest uncertainty beside official figures, plain-language explanations, English and Japanese.

**Status (2026-10-22):** milestone 1 started. Planning (Q1–Q31) and the spike (S1–S8, [docs/SPIKE-RESULTS.md](docs/SPIKE-RESULTS.md)) are done. Kurt chose **Plumes: a retrospective record of the 24 active Philippine volcanoes** (a past record and visualisation only, never a hazard service; no dataset redistributed; DOST-PHIVOLCS named as the authority on every view): **24 sources, queried in place where possible** (25 with Google Open Buildings Temporal at M1.1): Smithsonian eruption history, the daily figures in DOST-PHIVOLCS's public bulletins as dated linked markers, Sentinel-5P and OMI SO2 (from 2004) with NASA's per-eruption SO2 masses, MODIS/VIIRS thermal anomalies and radiative power, USGS earthquakes, Tokyo VAAC plume heights, DSWD evacuee counts, exposure rings, Sentinel-2, Landsat and Sentinel-1 before/after imagery, ERA5 winds, and the Lights link (night lights and poverty) at M1.1 ([docs/DECISIONS.md](docs/DECISIONS.md) Q30–Q31, [docs/LICENCES.md](docs/LICENCES.md), [docs/sources-draft.yaml](docs/sources-draft.yaml)). Architecture: static read models plus a read-only Java 17 API on PostGIS from milestone 1, React front end ([docs/DECISIONS.md](docs/DECISIONS.md)). Remaining actions for Kurt are in [docs/OPEN-QUESTIONS.md](docs/OPEN-QUESTIONS.md).

## Layout

| Folder | What |
|---|---|
| [`contracts/`](contracts/README.md) | the read-model contracts: JSON Schemas (source of truth), TypeScript types, and a real Taal fixture data version |
| `pipeline/` | Python (uv): `sources.yaml` (archivekit registry), crawlers, Earth Engine reductions, read-model materialiser, tests |
| [`web/`](web/README.md) | React 19 + Akari + MapLibre front end |
| [`api/`](api/README.md) | read-only Java 17 Spring Boot API on PostGIS (GraalVM native image) |
| `docs/` | planning, decisions, licences |
| `spike/` | the measurement spike (throwaway; outputs gitignored) |

The private archive of source snapshots is `abrycta/plumes-archive`.

Start with [docs/WORKFLOW.md](docs/WORKFLOW.md), then [docs/README.md](docs/README.md).

Workspace rules apply ([../CLAUDE.md](../CLAUDE.md)): `archivekit` for every external source, the Akari design system, free tiers only, commits as Kurt, secrets in the Keychain, a project page and share card, architecture before code, lean testing.
