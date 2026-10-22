# Read-model contracts

The files the pipeline publishes and the front end and the Java API read. **The JSON Schemas in `schemas/` are the source of truth**; `ts/readmodels.ts` mirrors them for the web app, and the pipeline validates every published file against them (`pipeline/plumes/contracts.py`) before `latest.json` is flipped.

## Layout of a data version

```
latest.json                  pointer: {"current": "v3", "base": "v3/", "dataAsOf": …}   (latest.schema.json)
v3/manifest.json             every file with bytes and sha256, check results, provenance (latest.schema.json, kind "manifest")
v3/volcanoes.geojson         the 24 volcanoes, map index                                (volcanoes.schema.json)
v3/volcano/<id>.json         one per volcano: series, bulletins, episodes, readings…    (volcano.schema.json)
v3/layers.json               national layers by month                                   (layers.schema.json)
v3/layers/…                  PMTiles / raster tiles (GeoJSON in the fixture)
v3/layers/deformation/<f>.tif  deformation-velocity: one Int16 GeoTIFF per volcano and frame (mm/yr x 10, nodata -32768); ids in layers.json frames
v3/story/<id>.json           Taal January 2020 at M1                                    (story.schema.json)
v3/deeptime.json             GVP eruptions of the 24 volcanoes with NCEI HazEL impacts   (deeptime.schema.json; TS in ts/deeptime.ts)
v3/assets/…                  before/after thumbnails
```

Published base URL: `https://krtmtthw.dev/plumes/data/` (GitHub Pages, range requests and CORS verified); fallback `https://huggingface.co/datasets/permission-alluring/plumes/resolve/main/`. Clients read `latest.json`, then fetch everything relative to `base`. In published versions the thermal layer is one PMTiles file per year (`layers/thermal/{year}.pmtiles`, source layer `thermal`, filter on `month`); the fixture uses GeoJSON. Versions are immutable; rollback is a pointer flip. Hosting: GitHub Pages (primary) with the Hugging Face files-only mirror `permission-alluring/plumes` as fallback; `latest.json.mirrors` lists the base URLs.

## Conventions

- **Dates** are ISO days (`YYYY-MM-DD`); VAAC times are ISO UTC. GVP eruption dates can be partial (`YYYY` or `YYYY-MM`).
- **Daily series** (`daily.<id>`): `values[i]` is the value for `start + i` days; `null` means no valid observation (cloud, no overpass, before the instrument), never zero. `coverage[i]` (0–1) is the valid-pixel fraction; show it beside every satellite value.
- **Event series** (`events.<id>`): sparse rows, the first column a date, the rest as named in `cols` with units in `units`. `start` is when the instrument could first report: an empty stretch after `start` means "nothing detected", before it "not observed".
- **Tables** (`bulletins`, `advisories`, `displacement`): column arrays named by `cols`; **the last column is always the source URL** (DECISIONS Q5 ii: every PHIVOLCS, VAAC and DROMIC figure links to its page).
- **Text** is `{en, ja}`. Readings and story steps carry `status: "draft"` until Kurt has reviewed both languages.
- **Safety:** nothing is "current". Alert levels are labelled "as reported by PHIVOLCS on <date>", and the record ends at `dataAsOf` (Q14). No reading forecasts.
- **Provenance:** every file has `provenance.sources[]` with the registry id, attribution and licence; `fromArchive: true` means the app shows "data as of <snapshotDate>".

## Series ids (M1)

| id | where | unit | source |
|---|---|---|---|
| `so2_s5p_15km`, `so2_s5p_50km` | daily | µmol/m² column mean (published versions may add `so2_s5p_mass_15km` in t) | `s5p-offl-so2` |
| ~~`so2_omi_box`~~ (dropped 2026-10-23; never published) | daily | DU, mean column within a 50 km box (OMSO2e v004: GEOS-5 profile, not v003's PBL column; v003 ended 2026-03-22) | `omi-omso2e` |
| `frp_modis_15km`, `frp_viirs_15km` | events | MW (MaxFRP), pixels | `modis-mod14a1`, `viirs-vnp14a1` |
| `fire_viirs_15km`, `fire_modis_15km` | events | detections, MW | `firms-modis` (area API) |
| `fire_viirs_n20_15km` (M2) | events | detections, FIRMS-flagged volcanic detections, MW; NOAA-20, its own series (never joined to S-NPP) | `firms-viirs-noaa20` (area API) |
| `eq_usgs_30km`, `eq_usgs_10km` | events | count, max magnitude | `usgs-comcat-ph-*` |
| `lake_temp_landsat` | events | °C | `landsat-surface-temperature` |
| `los_comet_<frame>` | events | mm along the satellite's line of sight (cols `date`, `los_mm`, `los_std_mm`; positive = toward the satellite, relative to COMET's reference area and the first date) | `comet-licsbas` |
| `bulletins` / `advisories` / `displacement` | tables | see schema | `phivolcs-*`, `vaac-tokyo-advisories`, `dswd-dromic-reports` |

New series ids may appear; the UI should render any `daily`/`events` entry from its `label` and `unit`.

## Fixtures

`fixtures/data/` is a complete small data version (`v0`, `"fixture": true`) built from the spike's **real** Taal tables for 2019-12-01 → 2020-02-15: TROPOMI SO₂ for January 2020, MODIS MaxFRP, FIRMS VIIRS detections, USGS events within 30 km, two PHIVOLCS bulletins, 22 Tokyo VAAC advisories, three DROMIC reports, GVP eruptions with the MSVOLSO2L4 mass, WorldPop within 14 km, ERA5 winds and two Sentinel-2 thumbnails. Only Taal has a volcano file; the other 23 appear in `volcanoes.geojson`. Serve the folder as the data base URL (e.g. Vite `public/data` or a dev proxy).

Rebuild (local only; needs the gitignored spike outputs): `cd pipeline && uv run python scripts/build_fixtures.py`. Validate: `cd pipeline && uv run pytest -q tests/test_contracts.py`.
