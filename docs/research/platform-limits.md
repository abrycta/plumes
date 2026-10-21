<!-- Research notes gathered 2026-10-21 for docs/CANDIDATES.md. Kept as evidence: every claim has its URL and access date; [U] marks unverified items. The comparison and the plan are in the parent folder. -->

# Platform limits and tooling facts (verified 2026-10-21)

Scope: free-tier platform numbers and tool versions for a static-first big-data geospatial web app (Philippines). Research only, no accounts, no code. Every fact carries its primary URL and the access date (all accessed 2026-10-21 unless stated). **[U]** marks anything not confirmed on a primary page (secondary source, inference, or page unreadable).---

## 1. Google Earth Engine, noncommercial (Community tier)

### 1.1 Quota tiers (the big change since early 2026)
Source: https://developers.google.com/earth-engine/guides/noncommercial_tiers (page "Last updated 2026-09-25 UTC").

| Tier | Monthly EECU quota | Requirements |
|---|---|---|
| Community (default) | 150 EECU-hours (540,000 EECU-seconds) | verified noncommercial project only |
| Contributor | 1,000 EECU-hours (3,600,000 EECU-s) | an active Cloud billing account ("we require that projects have a billing account in order to access this tier"), but no EE charges while registered noncommercial |
| Partner | 100,000 EECU-hours | separate application; review "may take several weeks" |

- Quotas "took effect for noncommercial projects on April 27, 2026" (rollout gradual; some projects may still see legacy behaviour).
- Reset "on the first of each calendar month at midnight Pacific Time (PT)"; unused hours do not carry over.
- Not hard cut-offs: "These EECU-hour quota limits are not hard cut-off values." Over quota, the project enters **restricted mode**: requests, EE Apps and tasks still run, with "reduced performance and throughput"; restricted mode "limits your online and batch concurrency and reduces the number of compute workers allocated to you."
- Tier is changed on the "Manage Tier" page in Cloud Console; changes take effect immediately (Partner needs approval).
- Noncommercial registration: "If you register a noncommercial project, no billing configuration is required." Projects registered before 2025-04-15 must verify eligibility or access is paused; "All projects with noncommercial access will need to reverify for access on a periodic basis." Source: https://developers.google.com/earth-engine/guides/access.
- Eligibility categories (individuals doing noncommercial work are eligible; excludes fee-for-service): https://earthengine.google.com/noncommercial/.

### 1.2 Usage quotas and limits
Source: https://developers.google.com/earth-engine/guides/usage ("Last updated 2026-07-27 UTC").

Adjustable per-project quotas:
- Max concurrent requests, standard endpoint: **40**; high-volume endpoint: **40** (HTTP 429 beyond; client library retries up to 5 times).
- Max request rate: **100 requests/s (6,000/min)** per project and per account.
- "Average concurrent batch tasks": **2 tasks (on average)**; for noncommercial projects the effective limit "depends on your noncommercial tier" (no number given).
- Max asset storage: **250 GB**; max assets: **10,000** (more on request for noncommercial/research users).
- EECU-time per day: "Unlimited" by default (an optional cap a Quota Administrator can set).

Fixed, system-wide limits:
- **Request payload: "A single query to Earth Engine is limited to 10MB in size."**
- **Aggregation result size: "The size limit on computed results is 100 MiB, and this is a system-wide limit."** (this is the "Computed value too large" limit, i.e. the 100 MiB applies to computed/aggregated results, not to table exports)
- **Task queue: 3,000 tasks in READY state** per project.
- Concurrent aggregations: fixed per user ("Too many concurrent aggregations").
- Per-request memory and computation time: vary by request type ("User memory limit exceeded", "Computation timed out").

### 1.3 Table export limits
Source: https://developers.google.com/earth-engine/guides/exporting_tables.
- No byte-size limit is stated for Drive/Cloud Storage/BigQuery table exports. Limits stated are for **table assets**: max 100 million features, 1,000 properties, 100,000 vertices per geometry, 100,000 characters per string. Formats: CSV, SHP, GeoJSON, KML, KMZ, TFRecord. SHP must fit Shapefile limits (2 GB, per Esri, linked not stated) and truncates column names to 10 chars.
- Conclusion: the "100 MiB table export limit" in the planning doc is a conflation; the 100 MiB applies to **computed results returned interactively** (getInfo/evaluate/reduceRegions results), not to batch Export.table. [Interpretation, but each half is on a primary page.]

### 1.4 Direct reads (no export)
- `projects.image.computePixels`: "Requests are limited to 48MB in uncompressed data per request" (pixels × bands × bytes per pixel); "at most 32K pixels in either dimension and at most 1024 bands"; over limit gives HTTP 400. Source: https://developers.google.com/earth-engine/reference/rest/v1/projects.image/computePixels.
- `computeFeatures`: page body not readable through the fetch tool (navigation only) [U]; it is paginated via pageSize/pageToken like other REST list endpoints [U].
- High-volume endpoint: "designed to handle a higher volume of requests in parallel than the standard endpoint"; higher per-request latency, less caching, "typically use more EECU-time". Source: https://developers.google.com/earth-engine/cloud/highvolume. Parallel count is bounded by the concurrent-request quota (40). Source: https://developers.google.com/earth-engine/guides/data_extraction.

### 1.5 reduceRegions guidance
- Best practices: "Calling reduceRegions() with a very large or complex FeatureCollection as input may result in" "Computed value is too large"; "One potential solution is to map reduceRegion() over the FeatureCollection instead." "Specifying a very small scale can substantially increase computation cost." For memory/timeouts, "the same computations may be able to succeed by using Export" because "the timeouts are longer and the allowable memory footprint is larger when running in the batch system." Source: https://developers.google.com/earth-engine/guides/best_practices.
- Debugging: "Too many concurrent aggregations" (reduction inside map) → use Export; "User memory limit exceeded" → raise `tileScale`, avoid arrays; "Too many pixels" → increase `scale`. Source: https://developers.google.com/earth-engine/guides/debugging.
- Practical rule for 1,600+ LGU polygons: run `reduceRegions` as `Export.table` (batch), not interactively; keep `scale` at native resolution; split by region/time if memory errors appear. [Opinion from the above.]

### 1.6 Exports from a service account; Drive vs Cloud Storage
- Service accounts: "All service accounts in the project with the correct permissions will have access to Earth Engine"; needs the Earth Engine Resource Viewer role (and possibly Service Usage Consumer). The page does not discuss Drive at all. Source: https://developers.google.com/earth-engine/guides/service_account.
- `Export.table.toDrive`: "Creates a batch task to export a FeatureCollection as a table to Drive"; folder resolves inside "The Google Drive Folder that the export will reside in", created at root if missing; defaults to Drive root. No statement about whose Drive. Source: https://developers.google.com/earth-engine/apidocs/export-table-todrive.
- Exporting guide: "The exports can be sent to your Google Drive account, to Google Cloud Storage or to a new Earth Engine asset." For Cloud Storage "you'll need to set up a project, enable billing for the project, and create a storage bucket" and "You must have write permission for the specified bucket." Source: https://developers.google.com/earth-engine/guides/exporting.
- **[U] Service account + Drive:** No primary page states it. Standard Google behaviour is that a service account is its own Google identity with its own Drive; a Drive export run under a service account lands in that account's Drive (not the human's), so the human must either share a folder with the service-account email and pass that folder name, or read the files back through the Drive API with the same service-account credentials. Community sources repeat this but none fetched was authoritative. Treat as [U] and test once in CI before relying on it.
- **Cloud Storage on the free tier:** GCS exports need a billing-enabled project (primary, above). Google Cloud Free Tier: "A Google Cloud billing account is required to access the Google Cloud Free Tier"; Always Free includes "5 GB-months of regional storage (US regions only) per month", "5,000 Class A Operations per month", "50,000 Class B Operations per month", "100 GB of outbound data transfer from North America" (us-east1/us-west1/us-central1 only). Source: https://docs.cloud.google.com/free/docs/free-cloud-features. So: GCS exports are possible with a card-backed billing account within Always-Free limits; with **no billing account at all**, only Drive exports, EE assets, or direct reads (computePixels 48 MB; getInfo/evaluate under the 100 MiB computed-result cap) are available. The Contributor tier also needs a billing account.

### 1.7 Catalog availability (catalog pages at https://developers.google.com/earth-engine/datasets/catalog/<ID>)
| Collection | Exists | Availability (page header) | Pixel | Notes |
|---|---|---|---|---|
| COPERNICUS/S5P/OFFL/L3_SO2 | yes | 2018-12-05 → 2026-10-18 | 1113.2 m | revisit "2 Days" field |
| COPERNICUS/S5P/OFFL/L3_NO2 | yes | 2018-06-28 → 2026-10-11 | 1113.2 m | |
| FIRMS | yes | 2000-11-01 → 2026-10-19 | 1000 m | daily; NRT "not considered to be of science quality"; bands T21, confidence, line_number |
| MODIS/061/MOD14A1 | yes | 2000-02-24 → 2026-10-14 | 1000 m | daily; summary text says "to October 2025" (stale blurb) |
| NASA/VIIRS/002/VNP14A1 | yes | 2012-01-19 → 2026-10-16 | 1000 m | daily |
| COPERNICUS/S1_GRD | yes | 2014-10-03 → 2026-10-21 | 10 m (HH/HV/VV/VH), angle 20 km | revisit 6 days; S1_GRD_FLOAT is "updated faster" |
| ESA/WorldCover/v200 | yes | 2021-01-01 → 2022-01-01 | 10 m | single 2021 map |
| WorldPop/GP/100m/pop | yes | 2000-01-01 → 2021-01-01 | 92.77 m | annual to 2020 |
| JRC/GHSL/P2023A/GHS_BUILT_S | yes | 1975-01-01 → 2030-12-31 | 100 m | 5-year epochs |
| COPERNICUS/DEM/GLO30 | yes but **"This dataset has been superseded by COPERNICUS/DEM/GLO30_2024_1"** | 2010-12-01 → 2015-01-31 | 30 m | use GLO30_2024_1: ImageCollection (because of multiple source resolutions), 2010-12-01 → 2020-11-13, 30 m |
| UCSB-CHG/CHIRPS/DAILY | yes | 1981-01-01 → 2026-09-30 | 5566 m | daily |

### 1.8 Commercial pricing (for contrast) [U]
The pricing page https://cloud.google.com/earth-engine/pricing is JS-rendered and unreadable by the fetch tool; a search-engine summary of it listed Enterprise/Individual & SMB plans: Basic $500/month with 100 batch + 33 online EECU-h and up to 8 concurrent batch tasks; Professional $2,000/month with 500 batch + 166 online EECU-h and 20 concurrent tasks; a "Limited" usage-fee-only plan with no credits. Treat all as [U].

---

## 2. GitHub

- **Actions minutes:** "The use of standard GitHub-hosted runners is free: In public repositories." "Larger runners are always charged for, even when used by public repositories." Private repos on GitHub Free: 2,000 min/month and 500 MB artifact/packages storage (shared with Packages); Pro 3,000 min / 1 GB; Team 3,000 / 2 GB; Enterprise Cloud 50,000 / 50 GB. Overage storage $0.25/GB-month. Source: https://docs.github.com/en/billing/managing-billing-for-your-products/about-billing-for-github-actions.
- **Runner specs:** public repos `ubuntu-latest`: 4 CPU, 16 GB RAM, 14 GB SSD (same for windows-latest; macOS arm64 3 CPU/7 GB). Private repos `ubuntu-latest`: 2 CPU, 8 GB, 14 GB. Source: https://docs.github.com/en/actions/reference/runners/github-hosted-runners.
- **Time limits:** job "up to 6 hours" on GitHub-hosted (5 days self-hosted); workflow run max 35 days; concurrent jobs Free 20 / Pro 40 / Team 60 / Enterprise 500; matrix max 256 jobs; GITHUB_TOKEN API 1,000 req/h per repo. Source: https://docs.github.com/en/actions/reference/limits.
- **Artifacts:** default retention 90 days; configurable 1–90 days for public repos, 1–400 days for private. Source: https://docs.github.com/en/organizations/managing-organization-settings/configuring-the-retention-period-for-github-actions-artifacts-and-logs-in-your-organization. Storage counted against the plan's shared artifact/Packages quota (above).
- **Pages:** "Published GitHub Pages sites may be no larger than 1 GB"; source repo "recommended limit of 1 GB"; "soft bandwidth limit of 100 GB per month"; "soft limit of 10 builds per hour" (not applicable with a custom Actions workflow). Source: https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits.
- **Releases:** "Each file included in a release must be under 2 GiB"; "Up to 1000 release assets may be associated with a single release"; "There is no limit on the total size of a release, nor bandwidth usage." Source: https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases.
- **Git LFS:** Free/Pro/Free-for-orgs: 10 GiB storage and 10 GiB bandwidth included; Team/Enterprise 250 GiB each; data packs "have been removed and replaced with metered billing" (bandwidth billed per GiB downloaded, storage hourly). Source: https://docs.github.com/en/billing/concepts/product-billing/git-lfs.
- **Repo files:** warning above 50 MiB, "GitHub blocks files larger than 100 MiB"; browser upload max 25 MiB; repos ideally < 1 GB, "less than 5 GB is strongly recommended". Source: https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github.

---

## 3. Cloudflare

- **Pages Free:** 500 builds/month, 1 concurrent build, 20-minute build timeout, "up to 20,000 files on the Free plan", "maximum file size for a single Cloudflare Pages site asset is 25 MiB", 100 custom domains/project, 100 projects/account, `_headers` max 100 rules, `_redirects` max 2,000 static + 100 dynamic. Source: https://developers.cloudflare.com/pages/platform/limits/.
- **Pages bandwidth:** "On both free and paid plans, requests to static assets are free and unlimited." Functions draw on the Workers Free 100,000 req/day quota; default "fail open" serves static files when the quota is exhausted. Source: https://developers.cloudflare.com/pages/functions/pricing/. (The phrase "unlimited bandwidth" itself is third-party wording; the primary text is "free and unlimited" requests.)
- **Workers Free:** "daily request limit of 100,000 requests, resetting at midnight UTC"; 10 ms CPU per HTTP request; 128 MB memory per isolate; 64 MiB uncompressed Worker size; 50 subrequests/invocation; no hard wall-clock limit for HTTP; Workers Static Assets: 20,000 files per version (Free), 25 MiB per file. Source: https://developers.cloudflare.com/workers/platform/limits/.
- **R2 free tier (Standard storage only):** 10 GB-month storage, 1 million Class A ops, 10 million Class B ops per month; "There are no charges for egress bandwidth for any storage class." Paid: $0.015/GB-month, $4.50/M Class A, $0.36/M Class B. Source: https://developers.cloudflare.com/r2/pricing/. Limits: 5 TiB objects (4.995 TiB multipart), 5 GiB single-part upload, 10,000 parts. Source: https://developers.cloudflare.com/r2/platform/limits/.
- **R2 card requirement [U-inferred]:** "You need a Cloudflare account with an R2 subscription", obtained by "Complete the checkout flow to add an R2 subscription" (https://developers.cloudflare.com/r2/get-started/); and "A primary payment method is required to purchase Cloudflare products and services" (https://developers.cloudflare.com/fundamentals/subscriptions-and-billing/create-billing-profile/). No page says "R2 needs a card" in those words, but the checkout flow is a purchase, so expect to add a payment method even for free-tier use.
- **D1 Free:** 5 million rows read/day, 100,000 rows written/day, 5 GB total storage; resets 00:00 UTC. Source: https://developers.cloudflare.com/d1/platform/pricing/.
- **KV Free:** 100,000 reads/day, 1,000 writes/day, 1,000 deletes/day, 1,000 lists/day, 1 GB stored. Source: https://developers.cloudflare.com/kv/platform/pricing/.

---

## 4. Hugging Face Hub (datasets)

- **Storage policy:** Free user/org public storage is "Best-effort"; private 100 GB free. Footnote: "Beyond the first few gigabytes, please use this resource responsibly by uploading content that offers genuine value to other users." PRO: up to 10 TB public + add-ons ($12/TB/month). Hard cap "no single file will exceed 500GB"; recommendations: <100k files per repo, <10k entries per folder (hard: "cannot exceed 10k files per folder"), files <200 GB, ~50–100 files per commit. Large datasets must have a dataset card and be meant for community reuse; Parquet/WebDataset preferred. Source: https://huggingface.co/docs/hub/storage-limits.
- **Rate limits (table dated "September '25", 5-minute fixed windows):** Anonymous per IP: API 500, **Resolvers 3,000**, Pages 100; Free user: 1,000 / 5,000 / 200; PRO: 2,500 / 12,000 / 400. Anonymous/Free marked "subject to change over time depending on platform health". 429 with `RateLimit` headers. Source: https://huggingface.co/docs/hub/rate-limits.
- **Xet storage:** the Hub "has adopted Xet", chunk-level dedup; Git LFS still supported. Legacy clients and plain HTTP: "a legacy client will get a single URL from the bridge which does the work of reconstructing the request file and returning the URL to the resource. This allows downloading files through a URL so that you can continue to use the Hub's web interface or `curl`." Repos keep LFS pointer files. Sources: https://huggingface.co/docs/hub/storage-backends, https://huggingface.co/docs/hub/xet/legacy-git-lfs, https://huggingface.co/docs/hub/xet/using-xet-storage (hf_xet, 64-bit only).
- **Range requests on resolve URLs [partly U]:** DuckDB's `hf://datasets/...` paths (DuckDB ≥ 0.10.3) read Parquet on the Hub through httpfs, which depends on HTTP Range; this is documented as working (https://huggingface.co/docs/hub/datasets-duckdb). The Hub docs do not state "Range supported" explicitly for `/resolve/` URLs; the LFS bridge hands back a CDN/S3 URL after redirect, and those honour Range. Treat "Range on resolve URLs works for Parquet/PMTiles" as well-established in practice but [U] on a primary page; test with `curl -r`.
- **Parquet converter (datasets-server):** every public dataset (or PRO/Enterprise private) is auto-converted to Parquet on `refs/convert/parquet`; shards ~500 MB; conversion is partial beyond 5 GB ("Parquet files are generated up to 5GB and placed in a split directory prefixed with 'partial'"); Parquet-native datasets are linked, not re-written, unless row groups are too big (recommended 100–300 MB uncompressed). Endpoints: `https://datasets-server.huggingface.co/parquet?dataset=...` and `https://huggingface.co/api/datasets/<id>/parquet`. Source: https://huggingface.co/docs/dataset-viewer/parquet.

---

## 5. Neon Free plan
Source: https://neon.com/docs/introduction/plans and https://neon.com/pricing.
- $0; **100 projects**; **10 branches/project**; compute **100 CU-hours per project per month**; max autoscaling 2 CU (8 GB RAM); **scale to zero after 5 minutes of inactivity, cannot be disabled**; storage **"1 GB/project, 20 GB account total"**; public network transfer 5 GB/project/month; instant restore 6 hours; 1 manual snapshot. Next plan (Launch): $0.106/CU-hour, $0.35/GB-month, 500 GB transfer included then $0.10/GB.
- So the answer to "0.5 GB or 1 GB?" is **1 GB per project** (and 20 GB across projects) on the current page.
- **PostGIS:** "can be installed on any Neon Project" (https://neon.com/docs/extensions/postgis); versions per Postgres: PG14–16 → PostGIS 3.3.10; PG17 → 3.5.7; **PG18 → 3.6.4** (h3 4.2.3, pgrouting 3.8.0). Source: https://neon.com/docs/extensions/pg-extensions. Matches the workspace's existing Neon setup (PG 18.6 + PostGIS 3.6).

---

## 6. Render free web services
Source: https://render.com/docs/free.
- "Render spins down a Free web service that goes 15 minutes without receiving any inbound traffic"; spin-up ~1 minute; local disk changes lost on spin-down.
- "Render grants 750 Free instance hours to each workspace per calendar month"; exhausted → "Render suspends all of your Free web services until the start of the next month."
- Bandwidth: "If you consume all of your outbound bandwidth during a given month, Render bills you for a supplementary amount." "If you haven't added a payment method, Render instead suspends all of your Free services for the remainder of the month." Build minutes overage is billed likewise (or new builds disabled without a card). "Free web services count against your monthly included amounts of outbound bandwidth and build pipeline minutes."
- **Numbers [U]:** the docs page states no numeric bandwidth/build allowance and the pricing page is JS-rendered. The commonly cited Hobby allowance is 100 GB/month outbound and 500 build minutes, with bandwidth overage around $0.30/GB [U]. Check the "Monthly Included Usage" section of the Render Billing page.
- Free Postgres: expires 30 days after creation (14-day grace, then deleted), 1 GB, no backups.
- Implication (card on file since 2026-10-21): overages bill instead of suspending; keep Render traffic behind Cloudflare caching or avoid Render for anything bandwidth-heavy.

---

## 7. Browser-side data tooling (versions as of 2026-10-21)

| Package | Version | Date | Source |
|---|---|---|---|
| `@duckdb/duckdb-wasm` | npm `latest` tag = **1.33.1-dev57.0** (dev build; `next` 1.33.1-dev65.0); last tagged GitHub release **v1.33.0**, 2025-12-16 ("no real differences from 1.32.0", which was 2025-12-16 too) | | https://registry.npmjs.org/@duckdb/duckdb-wasm ; https://api.github.com/repos/duckdb/duckdb-wasm/releases/latest |
| `pmtiles` | **4.5.0** | | https://registry.npmjs.org/pmtiles/latest |
| `maplibre-gl` | **6.15.0** (GitHub v6.15.0 published 2026-10-18) | | https://registry.npmjs.org/maplibre-gl/latest ; https://api.github.com/repos/maplibre/maplibre-gl-js/releases/latest |
| `tippecanoe` (felt) | **2.79.0**, 2025-07-24 | | https://api.github.com/repos/felt/tippecanoe/releases/latest |
| `deck.gl` | **9.4.0**, 2026-09-05 | | https://registry.npmjs.org/deck.gl/latest ; https://api.github.com/repos/visgl/deck.gl/releases/latest |
| `@deck.gl/maplibre` | **9.4.0** ("Use deck.gl layers with MapLibre GL JS"; peer `maplibre-gl ^4.5.1 || ^5.0.0 || ^6.0.0`) | | https://registry.npmjs.org/@deck.gl/maplibre/latest |
| `apache-arrow` | **21.2.0** | | https://registry.npmjs.org/apache-arrow/latest |
| `@geoarrow/geoarrow-js` | **0.3.3** (peer `apache-arrow >=15`) | | https://registry.npmjs.org/@geoarrow/geoarrow-js/latest |
| `@geoarrow/deck.gl-layers` | **0.3.2** (peer `@deck.gl/* ^9.0.12`) | | https://registry.npmjs.org/@geoarrow/deck.gl-layers/latest |
| `flatgeobuf` | **4.6.0** | | https://registry.npmjs.org/flatgeobuf/latest |
| `geotiff` | **3.0.5** | | https://registry.npmjs.org/geotiff/latest |
| `@geomatico/maplibre-cog-protocol` | **0.10.0** ("Custom protocol to load Cloud Optimized GeoTIFFs (COG) in Maplibre GL JS") | | https://registry.npmjs.org/@geomatico/maplibre-cog-protocol/latest |
| `maplibre-contour` | **0.1.1**, 2026-09-17 (previous 0.1.0 was 2024-12-21) | | https://registry.npmjs.org/maplibre-contour |

Notes:
- **DuckDB-WASM:** WebAssembly caps memory at 4 GB ("browsers may impose even stricter limits"); single-threaded by default, multithreading "experimental" (the `coi` bundle needs cross-origin isolation and is not in `getJsDelivrBundles()`); bundles mvp / eh / coi; Parquet over HTTP: "The JavaScript httpfs implementation fetches only the required byte ranges" (but the built-in httpfs extension "may currently download the whole file instead", so use the default JS httpfs). CORS on the data host is required. Sources: https://duckdb.org/docs/current/clients/wasm/overview.html, https://duckdb.org/docs/current/clients/wasm/instantiation.html. Package unpackedSize on npm is 149,377,663 bytes for the whole package (all bundles); per-bundle .wasm sizes could not be read from a primary page [U]; expect tens of MB per wasm, so lazy-load it.
- **deck.gl 9.4** is "expected to be the final release in the v9 series"; `@deck.gl/maplibre` is a new module forked from `@deck.gl/mapbox` supporting overlaid and interleaved rendering with MapLibre v4/v5/v6; WebGPU "remains experimental and is not yet recommended for production". Source: https://deck.gl/docs/whats-new.
- **FlatGeobuf:** "Fetching a subset of a file over HTTP utilizes Range requests"; optional packed R-tree index; reference implementations in JS/TS, C++, C#, Go, Java, Rust. Source: https://flatgeobuf.org/.
- **COG in the browser without TiTiler:** `geotiff.js` 3.x reads COG tiles via Range requests; `@geomatico/maplibre-cog-protocol` wraps it as a MapLibre `cog://` source. Both verified to exist at the versions above; performance claims not verified [U].
- **Protomaps basemaps:** daily builds at https://maps.protomaps.com/builds (metadata JSON at https://build-metadata.protomaps.dev/builds.json): latest `20261021.pmtiles` = 139,052,567,898 bytes (~139 GB), version 4.15.2, uploaded 2026-10-21; docs say "A full planet file is roughly 120 gigabytes" (slightly stale). Licence: "Open Database License Produced Work (OpenStreetMap attribution required)"; code BSD-3; styles CC0. Hotlinking the build bucket is "discouraged"; extract a Philippines cut-out with `pmtiles extract` (each extra zoom level "roughly doubles the size") and host it yourself (R2/HF/Pages). Sources: https://docs.protomaps.com/basemaps/downloads, https://github.com/protomaps/basemaps/blob/main/LICENSE.md.

---

## 8. Rust and Java geospatial tooling

| Crate / project | Version | Date | Source |
|---|---|---|---|
| `geo` | 0.33.1 | 2026-04-20 | https://crates.io/api/v1/crates/geo |
| `geozero` | 0.15.1 | 2025-12-11 | https://crates.io/api/v1/crates/geozero |
| `gdal` (georust) | 0.19.0 | 2025-12-23 | https://crates.io/api/v1/crates/gdal |
| `wasm-bindgen` | 0.2.129 | 2026-09-25 | https://crates.io/api/v1/crates/wasm-bindgen |
| Apache SedonaDB | 0.5.0 (`apache-sedona-db-0.5.0`) | 2026-10-02 | https://api.github.com/repos/apache/sedona-db/releases/latest (adds raster functions RS_SummaryStats, RS_Stack, RS_SetValue, DataFusion 54.1, Rust 2024 edition; breaking: raster pixel coords now 1-based like PostGIS) |
| GeoTools | 35.2 | 2026-10-16 (33.7 and 34.6 maintenance releases same day) | https://api.github.com/repos/geotools/geotools/releases/latest |
| JTS | 1.20.0 | 2024-09-04 (still latest) | https://github.com/locationtech/jts/releases/latest |

**Opinion: which core for raster time-series work?**
- The heavy lifting (zonal statistics of daily/weekly rasters over ~1,600 LGU polygons, 2018–2026) should happen **in batch on the server side**, and Earth Engine or Python (`exactextract` + `rioxarray`) is the natural batch engine; neither Rust nor Java needs to do the raster reduction itself.
- For the **batch** stage, a Python job on GitHub Actions is the least-friction fit today: `exactextract` 0.3.0 gives exact area-weighted zonal stats, `odc-stac`/`rioxarray` stream COGs, and `earthengine-api` 1.7.49 drives EE. Java (as in Typhoon Replay) is fine for vector/tabular batch and GeoTools 35 has coverage support, but the raster ecosystem (COG streaming, STAC, xarray-style lazy time axes) is thinner and slower to write.
- A **Rust→WASM core** (as in the Lights app, `wasm-bindgen` 0.2.129, `geo` 0.33) is the right choice only for the **client-side** part: fast per-polygon aggregation, interpolation and chart prep over pre-reduced Parquet/Arrow served from HF/R2, in a Worker, deterministic and shared with a CLI. It is not a good fit for first-pass raster reduction (no GDAL in WASM without a large custom build, 4 GB memory cap, single thread).
- SedonaDB 0.5 (Rust/DataFusion, raster functions now present) is promising for a local/CI batch step on GeoParquet, but 0.x with breaking changes (pixel indexing just changed); keep it optional.
- Recommended split: EE/Python batch → versioned Parquet/GeoArrow + PMTiles → DuckDB-WASM and a small Rust-WASM module in the browser.

---

## 9. Python geospatial tooling and free STAC endpoints

| Package | Version | Upload date | Source |
|---|---|---|---|
| `xarray` | 2026.9.0 | 2026-09-29 | https://pypi.org/pypi/xarray/json |
| `rioxarray` | 0.23.0 | 2026-07-27 | https://pypi.org/pypi/rioxarray/json |
| `exactextract` | 0.3.0 | 2025-12-01 | https://pypi.org/pypi/exactextract/json |
| `geopandas` | 1.2.0 | 2026-09-28 | https://pypi.org/pypi/geopandas/json |
| `pystac-client` | 0.9.1 | 2026-10-20 | https://pypi.org/pypi/pystac-client/json |
| `earthengine-api` | 1.7.49 | 2026-10-19 | https://pypi.org/pypi/earthengine-api/json |
| `geemap` | 0.38.9 | 2026-10-01 | https://pypi.org/pypi/geemap/json |
| `odc-stac` | 0.5.3 | 2026-07-30 | https://pypi.org/pypi/odc-stac/json |
| `stackstac` | 0.5.1 | 2024-08-10 (no release in 2+ years; prefer odc-stac) | https://pypi.org/pypi/stackstac/json |
| `pyarrow` | 26.0.0 | 2026-10-09 | https://pypi.org/pypi/pyarrow/json |

STAC / data endpoints:
- **Copernicus Data Space Ecosystem (CDSE):** STAC at `https://stac.dataspace.copernicus.eu/v1/` (legacy `catalogue.dataspace.copernicus.eu/stac` deprecated from 2025-11-17); collections include Sentinel-1 GRD/SLC, Sentinel-2 L1C/L2A, Sentinel-3, Sentinel-5P L1/L2 (NRTI/OFFL/RPRO). Source: https://documentation.dataspace.copernicus.eu/APIs/STAC.html. S3: endpoint `https://eodata.dataspace.copernicus.eu/`, needs S3 keys from a registered CDSE account; each file counts as a request. Source: https://documentation.dataspace.copernicus.eu/APIs/S3.html. Quotas (general/free users): 20 MB/s per connection, 4 concurrent connections, 2,000 requests/min (S3), **12 TB per rolling 30 days**, after which bandwidth drops to 1 MB/s and 1 connection. Source: https://documentation.dataspace.copernicus.eu/Quotas.html. Searching the STAC API anonymously: not stated on the page [U]; downloads need an account.
- **Microsoft Planetary Computer:** STAC API alive at `https://planetarycomputer.microsoft.com/api/stac/v1` (STAC 1.0.0, CQL2, item search). The SAS token endpoint `https://planetarycomputer.microsoft.com/api/sas/v1/token/sentinel-2-l2a` returned a token JSON anonymously (expiry 2026-10-21T10:46:15Z) when fetched. Changes: the JupyterHub was retired 2024-06-06 (discussion #347); Oct 2024 "Disabling Anonymous Access for Azure Storage Accounts" (#378) for a list of storage accounts (astersa, nasademeuwest, naipeuwest, elevationeuwest, …) with NOAA NODD to follow; "Collection ID requirement in STAC search API" (#385, 2024-10-25). 2026 announcements are maintenance only (#504 2026-09-19, #508 2026-10-12 redirecting traffic per collection for 22 small collections). The docs site is JS-rendered so the "anonymous but throttled" wording could not be read directly [U]. Net: still free and open as of today, with SAS signing required for blob access and a search-side collection filter required; no 2025 pricing change found. Planetary Computer Pro is a separate paid Azure product.
- **AWS Open Data (registry.opendata.aws):** `sentinel-cogs` (Sentinel-2 L2A COGs, us-west-2, Earth Search STAC `https://earth-search.aws.element84.com/v1`, "No AWS account required"); `sentinel-s2-l2a` listed as plain "S3 Bucket" (eu-central-1) while `sentinel-s2-l1c` and the `-zips` buckets are "S3 Bucket [Requester Pays]"; `sentinel-s1-l1c` listed as "S3 Bucket" (eu-central-1) with `--no-sign-request` example; `meeo-s5p` (Sentinel-5P NRTI/OFFL/RPRO/COGT, eu-central-1, no account required); `usgs-landsat` (us-west-2) is **"S3 Bucket [Requester Pays]"**, STAC at `https://landsatlook.usgs.gov/stac-server`. Sources: https://registry.opendata.aws/sentinel-2-l2a-cogs/, https://registry.opendata.aws/sentinel-2/, https://registry.opendata.aws/sentinel-1/, https://registry.opendata.aws/sentinel5p/, https://registry.opendata.aws/usgs-landsat/. Note: cross-region egress from eu-central-1 is slow from GitHub runners (US) [U]; prefer `sentinel-cogs`/Earth Search.
- **NASA CMR-STAC:** `https://cmr.earthdata.nasa.gov/stac` root lists 61 provider catalogs (LPCLOUD, ASF, PODAAC, …) plus `ALL`; STAC 1.0.0. Source: fetched landing JSON. Data downloads need an Earthdata login/token (already in the Keychain).

---

## Limits cheat-sheet (free tiers, 2026-10-21)

| Platform | Limit | Value |
|---|---|---|
| Earth Engine Community | compute | 150 EECU-h/month, soft (restricted mode after) |
| Earth Engine | concurrent interactive requests | 40 (standard and high-volume) |
| Earth Engine | request rate | 100 req/s |
| Earth Engine | batch tasks | ~2 concurrent on average; 3,000 queued (READY) |
| Earth Engine | payload / computed result / computePixels | 10 MB / 100 MiB / 48 MB (32K px per side, 1024 bands) |
| Earth Engine | assets | 250 GB, 10,000 assets |
| Earth Engine | export destinations w/o billing | Drive, EE asset (GCS needs billing; Contributor tier needs billing account) |
| GitHub Actions | public repo minutes | free on standard runners; private 2,000 min/month |
| GitHub Actions | runner (public) | 4 vCPU / 16 GB / 14 GB SSD (private: 2 / 8 / 14) |
| GitHub Actions | job / workflow | 6 h / 35 days; 20 concurrent jobs (Free); 256 matrix jobs |
| GitHub Actions | artifacts | 500 MB (Free, shared w/ Packages); 90-day default, max 90 public / 400 private |
| GitHub Pages | site / bandwidth / builds | 1 GB / 100 GB per month (soft) / 10 builds per hour (soft) |
| GitHub Releases | asset / per release / total | < 2 GiB / 1,000 assets / unlimited size and bandwidth |
| Git LFS | free | 10 GiB storage + 10 GiB bandwidth, then metered |
| Git repo | file | 100 MiB hard block (50 MiB warning), repo ideally < 1 GB |
| Cloudflare Pages | builds / files / file size | 500 per month / 20,000 / 25 MiB; static requests "free and unlimited" |
| Cloudflare Workers | requests / CPU / memory | 100,000 per day / 10 ms / 128 MB; Static Assets 20,000 files, 25 MiB |
| Cloudflare R2 | storage / ops / egress | 10 GB-month / 1 M Class A + 10 M Class B / free; subscription via checkout (payment method expected [U]) |
| Cloudflare D1 | reads / writes / storage | 5 M per day / 100 k per day / 5 GB |
| Cloudflare KV | reads / writes / storage | 100 k per day / 1 k per day / 1 GB |
| Hugging Face | public storage | best-effort ("first few gigabytes"); 10k entries per folder; 500 GB per file hard cap |
| Hugging Face | anonymous rate | 3,000 resolver requests per 5 min per IP (500 API, 100 pages) |
| Hugging Face | Parquet converter | auto on `refs/convert/parquet`, partial beyond 5 GB, ~500 MB shards |
| Neon Free | storage / compute / projects | 1 GB per project, 20 GB total / 100 CU-h per project per month / 100 projects, 10 branches; suspend after 5 min; 5 GB transfer per project |
| Render Free | hours / sleep | 750 instance-h per month / 15 min idle spin-down; bandwidth and build overages billed once a card is on file (numbers [U]) |
| GCP Always Free | storage | 5 GB-month US-only, needs billing account |
| CDSE | transfer | 12 TB per 30 days, 4 connections, 20 MB/s each, 2,000 S3 req/min |

## What changed since early 2026 (would surprise a plan written then)

1. **Earth Engine noncommercial quotas are now metered: Community tier = 150 EECU-hours/month, effective 2026-04-27**, with restricted mode (not cut-off) beyond that; the Contributor tier (1,000 EECU-h) needs a billing account even though it is not charged. A plan that assumed "noncommercial = unmetered" must budget EECU-hours and prefer batch exports (cheaper than repeated interactive calls) and caching of results.
2. **COPERNICUS/DEM/GLO30 is superseded by COPERNICUS/DEM/GLO30_2024_1** (now an ImageCollection); update any asset ID.
3. **Neon Free plan is now 1 GB per project / 20 GB total with 100 projects** (older plans were 0.5 GB and 10 projects); PG18 with PostGIS 3.6.4 is available.
4. **deck.gl 9.4 (2026-09-05) ships `@deck.gl/maplibre`** (use it instead of `@deck.gl/mapbox`), and is the planned final v9 release; MapLibre GL JS is at **6.15.0**.
5. **DuckDB-WASM's npm `latest` tag points at a dev build (1.33.1-dev57.0)**; the last tagged release is 1.33.0 (2025-12-16). Pin an explicit version.
6. **GitHub Git LFS data packs are gone**, replaced by metered billing above the 10 GiB free storage and bandwidth.
7. **Hugging Face rate limits are now published** (anonymous 3,000 resolver requests per 5 min per IP) and public storage is explicitly "best-effort" beyond "the first few gigabytes"; Xet is the storage backend, with an LFS bridge so plain URLs still work.
8. **CDSE legacy STAC endpoint was retired (from 2025-11-17)**; use `stac.dataspace.copernicus.eu/v1`.
9. **Planetary Computer remains free**, but blob access on several storage accounts requires SAS signing (since late 2024) and STAC search requires a collection ID; October 2026 maintenance moved some collections behind redirects.
10. **Protomaps planet build has grown to ~139 GB (v4.15.2)** versus the ~120 GB quoted in the docs; a Philippines extract is the only practical option.
11. **SedonaDB 0.5.0 (2026-10-02)** now has raster functions in Rust/DataFusion, a new option for CI-side zonal work; still 0.x with breaking changes.
12. `stackstac` has had no release since 2024-08; `odc-stac` 0.5.3 (2026-07) is the maintained choice.
