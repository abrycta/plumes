# Spike results

Status: 2026-10-21. **The spike has not run.** Kurt said "go ahead with everything" the same day, but the first spike step (creating the throwaway Python environment in `spike/`: `earthengine-api`, `httpx`, `python-docx`, `xarray`, `zarr`) was refused by the session's permission check, and the rule for this work is to stop a refused step, not to work around it. No measurement was taken, no Earth Engine compute was used, no page was crawled, no NASA file was read. The table below records what each item needs, so the spike can start as soon as the permission is granted. Item numbers follow [SPIKE-PLAN.md](SPIKE-PLAN.md).

Checked before stopping (no secret printed):
- No Lights data run was in progress (`gh run list -R abrycta/lgu-lights`: the last runs were Web, Rust and Pipeline jobs, all finished).
- The Keychain has `earth-engine-sa-key`; it has **no** `firms-map-key`.

| # | Item | Result | Needs |
|---|---|---|---|
| 1–3, 11, 16, 18 (EE part), 20, 22, 25–27 | Earth Engine reductions, mosaic, Taal 2020 signal, WorldPop, quota accounting, thumbnails, Open Buildings | not run | permission to install the spike environment (or run Python with `earthengine-api`) in `spike/` |
| 4, 5, 17 | PHIVOLCS WordPress and LAVA bulletins, Tokyo VAAC and DROMIC (at most about 100 pages at 1 request/s) | not run | the same permission |
| 6 | PHIVOLCS earthquake tables | removed (Q30) | — |
| 7 | MapLibre frame time while scrubbing | not run | a browser session on the laptop and a mid-range phone |
| 8 | Taal per-volcano JSON size | not run | the item 1–3 tables |
| 9, 10 | GVP WFS and USGS CSVs through `archivekit fetch` | not run | the same permission |
| 12 | Taal and Kanlaon readings in EN and JA | not run | the item 1–5 tables, then Kurt's review |
| 13, 15 | Java API cold start on Render free; edge cache in front | **needs Kurt's go-ahead**: one Render web service, `plan: free`, in the existing workspace (Singapore), deploying a prebuilt GHCR image of a Spring Boot skeleton, deleted the same day; one throwaway Cloudflare Pages project with a `/api/*` function (free plan), deleted the same day | Kurt's go-ahead |
| 14 | PostGIS catalogue size on Neon free | **needs Kurt's go-ahead**: one Neon project `plumes-spike` (free, Singapore, PostGIS), or a branch, deleted the same day | Kurt's go-ahead |
| 18 (ERA5 part) | ARCO-ERA5 winds over Taal, 12–13 January 2020 | not run | the same permission |
| 19 | FIRMS area API `type` column | **blocked** | a FIRMS MAP_KEY in the Keychain as `firms-map-key` (Kurt's action, free) |
| 21 | COD-AB `.dbf` range read | not run | the same permission |
| 23, 24 | MSVOLSO2L4 / MSAQSO2L4 Philippine rows; OMI `OMSO2e` Harmony subset for Taal | not run (Kurt approved the Earthdata reads later the same day, but the spike had already stopped) | the same permission |

No DECISIONS.md addendum (S1…) is written until there are measurements.
