# Plumes (噴煙)

Plumes puts satellite SO₂ and heat, earthquakes and PHIVOLCS bulletins for 24 Philippine volcanoes on one timeline, since 2000. It is in English and Japanese.

A past record; DOST-PHIVOLCS is the authority on alert levels and advisories.

Project page: [krtmtthw.dev/projects/plumes](https://krtmtthw.dev/projects/plumes/)

**Where it stands (2026-11-06):** the map, 24 volcano timelines and 21 generated stories are live on data version 9. Each data version is published at https://krtmtthw.dev/plumes/data/latest.json, with a files-only hosting mirror on Hugging Face (`permission-alluring/plumes`, not a dataset release). The planning trail is in [docs/README.md](docs/README.md).

## What it shows

- Smithsonian GVP eruption history
- DOST-PHIVOLCS bulletin figures as dated, linked markers
- Sentinel-5P and OMI SO₂ (OMI from 2004), with NASA's per-eruption SO₂ masses
- MODIS and VIIRS thermal anomalies and radiative power
- USGS earthquakes
- Tokyo VAAC plume heights
- DSWD evacuee counts
- Exposure rings (people living nearby)
- Sentinel-2, Landsat and Sentinel-1 before/after imagery
- ERA5 winds

24 sources, queried in place where possible; licences in [docs/LICENCES.md](docs/LICENCES.md).

## Architecture

Static read models built by a Python pipeline, plus a read-only Java 17 Spring Boot API on PostGIS (GraalVM native image) and a React front end; see [docs/DECISIONS.md](docs/DECISIONS.md).

## Layout

| Folder | What |
|---|---|
| [`contracts/`](contracts/README.md) | the read-model contracts: JSON Schemas (source of truth), TypeScript types, and a real Taal fixture data version |
| `pipeline/` | Python (uv): `sources.yaml` (archivekit registry), crawlers, Earth Engine reductions, read-model materialiser, tests |
| [`web/`](web/README.md) | React 19 + Akari + MapLibre front end |
| [`api/`](api/README.md) | read-only Java 17 Spring Boot API on PostGIS (GraalVM native image) |
| `docs/` | planning, decisions, licences |
| `spike/fixtures/` | crawled pages kept from the pre-build measurement spike; the pipeline's parser tests read them |

Source snapshots are kept in a private archive, the last fallback when an upstream is unavailable.

Start with [docs/README.md](docs/README.md).

Conventions shared with my other projects: every external source goes through a registry with fallbacks and a private snapshot archive (`archivekit`); the UI uses the Akari design system; everything runs on free tiers; architecture is decided and recorded before code; targeted tests run locally and the full suites run in CI.
