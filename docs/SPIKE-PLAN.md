# Measurement spike plan

One day, after Kurt answers [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md) and the Earth Engine project question (Q11) is settled. Throwaway code in `spike/` (outputs gitignored); results go to `SPIKE-RESULTS.md` as a table (measurement, estimate, result, verdict) and an addendum S1…Sn in [DECISIONS.md](DECISIONS.md). The spike never backfills, never creates permanent resources, never registers on the PHIVOLCS portal, and keeps Earth Engine use to a few EECU-minutes.

## What to measure

| # | Measurement | Estimate today | Method | Pass / fail bar |
|---|---|---|---|---|
| 1 | Earth Engine: `reduceRegions` of `COPERNICUS/S5P/OFFL/L3_SO2` over the 24 boxes and rings for **one month** (January 2020, Taal's eruption): EECU-seconds, rows, wall time; the same for `FIRMS` and `VNP14A1` for one month | a few EECU-minutes per month per collection; a few EECU-hours for the backfill **[U]** | Python client with the service account; `ee.data.getTaskStatus` and the profiler; export to Drive and, as the fallback, `computeFeatures` | the extrapolated backfill is under 30 EECU-hours; one path to get tables out without billing works |
| 2 | Earth Engine: a national monthly mean SO2 mosaic at 1 km for one month, as GeoTIFF: size, EECU, export path | under 1 MB per month **[U]** | export to Drive; tile with `rio-pmtiles` or `gdal2tiles` | the yearly tileset is under 25 MiB per file and the monthly cost under 1 EECU-hour |
| 3 | Taal 2020-01-12 reproduces: the 15 km SO2 column mass spikes on 12–13 January; fire pixels on the island; USGS events in the box climb from 10 January | known from the literature | the spike's tables | the known signal is visible with the planned rings; if not, the ring sizes or bands change |
| 4 | PHIVOLCS WordPress bulletins: fetch 40 pages across eras (2017, 2020, 2022, 2024, 2025) at 1 request/s; size, format drift, parse rate of the prose parser (counts, SO2 flux with date, plume, alert level, deformation sentence) | 15–30 kB per page; parse rate above 95 % on prose bulletins; 2025 pages empty **[U]** | `httpx` + a regex/grammar parser with fixtures | the fields the product needs parse on at least 95 % of 2017–2024 pages; the 2025+ gap is confirmed and covered by LAVA |
| 5 | PHIVOLCS-LAVA: fetch 40 bulletins by id across 2022–2026 for the four volcanoes; id density (how many ids per day), TLS behaviour from the GitHub runner, section parse rate | about 4 ids per day; TLS chain fails in Node but not curl **[U]** | `httpx` with the system trust store, then with `certifi`; fixtures | a crawl strategy by id works from a runner; parse rate above 98 % |
| 6 | PHIVOLCS earthquake monthly pages: fetch three months (2016-01, 2020-01, 2025-10), row counts, the magnitude type on event pages | 0.5–2.8 MB, 500–5,600 rows **[U]** | parser with fixtures | rows parse; the per-volcano 30 km counts for January 2020 match the bulletin counts within reason |
| 7 | Front end: MapLibre GL 6 with a PMTiles layer of 300k synthetic points filtered by month (circle layer with a feature-state or filter): frame time while scrubbing on the laptop and on a mid-range phone | smooth at z5–z8 with a filter expression **[U]** | a Vite page with Akari; `performance.now()` | 30 fps or better while scrubbing; otherwise deck.gl's ScatterplotLayer is tested and the choice recorded |
| 8 | Per-volcano JSON: build Taal's JSON from the spike tables (one month of real data extrapolated to the full span): raw and gzip size; chart render time with Akari's chart layer | under 80 kB gz **[U]** | the spike's materialiser; `gzip -9` | under 120 kB gz; charts render in one frame |
| 9 | GVP WFS and MIROVA CSV through `archivekit fetch` with the draft registry: bytes, rows, checks, profile | GVP 23 + 233 rows; MIROVA 98.6 MB | `archivekit fetch --registry docs/sources-draft.yaml` (kit from the local checkout) | both fetch and validate; MIROVA's Philippine subset has daily rows for Taal, Mayon, Kanlaon, Pinatubo |
| 10 | USGS CSV links: both period files download under the 20,000 cap with the expected columns and row counts | 1900–2009 and 2010 → under 20,000 each | `archivekit fetch` | checks pass; the yearly delta link works |
| 11 | Exposure: WorldPop 2020 within 14 km of Taal versus OCHA's about 459,300 (2020) | within 20 % **[U]** | Earth Engine `reduceRegions` | the difference is explained (vintage, rings vs barangays) and stated on the site |
| 12 | Plain-language reading: write the Taal January 2020 and Kanlaon September 2024 readings in EN and JA by hand from the spike tables, with the limits sentences; check them against the safety rules | — | a review pass | the rules hold; the wording becomes the template |

## What the spike does not do

- No full backfill, no crawl beyond about 100 pages, no Earth Engine run beyond about 30 minutes of batch time.
- No registration on PHIVOLCS-LAVA, HazardHunterPH or GeoRiskPH; no FIRMS archive request beyond one small email download if item 3 needs `type`.
- No permanent deployment, no DNS, no repos, no datasets.
- No full test suites: targeted checks only.

## Outputs

- `SPIKE-RESULTS.md` with the table filled in, the method per item, and the findings that change the plan.
- `DECISIONS.md` addendum S1…Sn.
- Updated **[U]** figures in RESEARCH.md §10, ARCHITECTURE-OPTIONS.md §2.3 and DATA-PLAN.md §1–§7 citing the spike.
- The fixtures (a few bulletin pages, one monthly earthquake page, one GVP CSV, a MIROVA subset) kept for the parser tests; nothing else is committed.
