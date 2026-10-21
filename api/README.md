# api

The read-only Java 17 Spring Boot 3 API (MyBatis, PostGIS), built as a GraalVM native image, pushed to the private GHCR package `ghcr.io/abrycta/plumes-api` and run on Render free (DECISIONS Q3, Q20, S7). Owned by the API agent. The site never depends on it: the static read models carry every page, and the API adds the relational, spatial-temporal queries.

## Endpoints (contract: [`../contracts/openapi.yaml`](../contracts/openapi.yaml))

Public at `https://plumes.krtmtthw.dev/api/…` through the Pages Function `web/functions/api/[[path]].ts` (edge cache); the origin serves the same paths without `/api`.

| Path | What |
|---|---|
| `GET /v1/meta` | build, contract, loaded data version, counts, event coverage |
| `GET /v1/volcanoes` | the 24 volcanoes: **equals** the published `volcanoes.geojson` |
| `GET /v1/volcanoes/{id}` | one volcano: **equals** the published `volcano/<id>.json` (`volcano.schema.json`) |
| `GET /v1/volcanoes/nearest?lat&lon&limit` | nearest volcanoes, geodesic km |
| `GET /v1/events?volcano=taal\|lat&lon&radiusKm&from&to&kind&limit` | USGS earthquakes and FIRMS thermal detections in a radius and a date window (≤ 100 km, ≤ 10 years, ≤ 1,000 listed, summary always complete) |
| `GET /v1/eruptions/precursors?minVei&days&radiusKm&since` | what the instruments recorded in the N days before each GVP eruption of VEI ≥ n |
| `GET /v1/openapi.yaml` | the contract |
| `GET /healthz`, `/readyz` | liveness (no database), readiness (database and a loaded version) |

Conventions shared with Replay: RFC 9457 problem documents with a `code` (`not-found`, `invalid-parameter`, `not-ready` + `Retry-After`, …); weak ETags `W/"c{contract}-java-{implVersion}-d{dataVersion}"` and 304s; `Cache-Control: public, max-age=300, s-maxage=86400, stale-while-revalidate=604800`. When `PLUMES_EDGE_SECRET` is set, `/v1/*` answers only requests carrying it (`X-Edge-Secret`, added by the edge), so reads cannot bypass the edge cache and spend Render's shared egress.

## Layout (hexagonal)

| Package | Role |
|---|---|
| `catalogue` | the core: records, the `CatalogueRepository` port, `CatalogueService` (query rules and limits) |
| `persistence` | driven adapter: MyBatis mapper over PostGIS, registered by hand plus native hints (`MyBatisNativeHints`) |
| `web` | driving adapter: controllers, problems, ETags, the edge-secret filter |
| `load` | `plumes-api load`: the batch loader (plain JDBC, no Spring context) |

Rows from the read models keep their published JSON verbatim (`json` columns), so the list and detail equal the static files by construction; relational columns beside them (`geography` points, partial-date-aware episode starts) serve the queries. Migrations: dbmate, `db/migrations/`.

## Run and test

```sh
# PostGIS 18 + 3.6 and the schema
docker run -d --name plumes-db -e POSTGRES_USER=plumes -e POSTGRES_PASSWORD=plumes -e POSTGRES_DB=plumes -p 5432:5432 postgis/postgis:18-3.6
DATABASE_URL='postgres://plumes:plumes@localhost:5432/plumes?sslmode=disable' dbmate --migrations-dir api/db/migrations --no-dump-schema up

# tests: unit always; the contract/integration test (ContractIT) when TEST_DATABASE_URL is set
cd api && TEST_DATABASE_URL='postgres://plumes:plumes@localhost:5432/plumes?sslmode=disable' mvn verify

# the native image (from the repository root)
docker build -f api/Dockerfile -t plumes-api .
docker run --rm -e DATABASE_URL=… plumes-api load /data [--usgs comcat.csv]... [--firms firms.csv]...
docker run -p 8080:8080 -e DATABASE_URL=… plumes-api
```

`ContractIT` loads `contracts/fixtures/data` with the real loader, then checks that the list and Taal's file equal the fixtures and validate against the schemas, and that the spatial queries rebuild the fixture's own daily series from the raw points (USGS within 30 km, VIIRS within 15 km). CI (`.github/workflows/api.yml`) runs it on Java 17 against a PostGIS service container; on main it builds the native image (cached Maven layer), pushes it to GHCR and calls Render's deploy hook; nightly it validates the live list and Taal through the edge.

## Loading a data version

`plumes-api load <data root>` reads `latest.json`, then `volcanoes.geojson`, every `volcano/<id>.json` and the GeoJSON months of the `thermal-detections` layer, and replaces the catalogue in one transaction (readers see the old or the new version, never a mix). Earthquakes are not in the read models at M1, so they come from USGS ComCat CSV files (`--usgs`, the FDSN `format=csv` columns); FIRMS area-API CSVs can be added with `--firms`. The data root is a folder or an HTTPS base URL (the published one is `https://krtmtthw.dev/plumes/data/`).

## Deployment and free-tier rules (DATA-PLAN §8)

- **Render** web service `plumes-java` (`plan: free`, Singapore), image from GHCR with a registry credential (`ghcr-read-token`, `read:packages`), health check `/healthz` (never touches Neon), no pinger, sleeps after 15 minutes. The workspace's 750 free hours are shared with Replay; Replay's budget guard pauses Replay Go first, never Plumes.
- **Neon** project `plumes` (pooled URL in Keychain `neon-database-url-plumes`): Hikari pool of 3, no idle connections, 20 s connection timeout for a resuming compute.
- **Edge**: the Pages Function caches every `/v1` read (s-maxage + stale-while-revalidate, revalidated by ETag) and answers a sleeping origin with a `backend-waking` problem while the request finishes in the background.
