# web

The Plumes front end: Vite + React 19 + TypeScript, `@abrycta/akari` (Header, Page, Prose, Scrollytelling, MapLegendKey, theme cookie), MapLibre GL with PMTiles support (ARCHITECTURE-OPTIONS.md §5). Deployed to the Cloudflare Pages project `plumes` by `.github/workflows/web.yml` on every push to `main`.

## Screens

| Path | What |
|---|---|
| `/` | Overview map of the 24 volcanoes, thermal detections by month, the volcano list |
| `/volcanoes` | All 24, most recent eruption first |
| `/volcano/<id>` | Every record on one time axis with a day scrubber (`?from&to&date&ring`): PHIVOLCS alert levels as dated linked markers, earthquakes, SO₂ with coverage, heat, GVP eruptions, VAAC ash, DSWD displacement, exposure, readings, sources |
| `/stories`, `/story/taal-2020` | Taal, January 2020 (Akari Scrollytelling) |
| `/about` | What Plumes is and is not, how to read it, every source's licence and attribution, required notices |

## Embed (`/embed`)

`embed.html` (served at `/embed`; `src/embed/`) is the live picture krtmtthw.dev frames on its Plumes project page (workspace rules 6b, 6c; `LIVE-EMBEDS-PLAN.md`). The national map with thermal detections and earthquakes steps month by month through the year up to the most recent eruption GVP records, over a two-line caption. Two layouts by the frame's width: the desktop frame (1280×800, scaled down by the parent; larger type and markers) and compact (≤ 1100 px, the slot's real size; 14/12 px caption, phones get small unlabelled markers). No Header, controls, attribution box or links; the frame is inert and the map non-interactive, so touches scroll the parent. `?pr=` caps the canvas pixel ratio (≤ 2), `?paused=1` starts it still; `parent-bridge.ts` posts `akari:embed-ready` and accepts `akari:embed-pause` / `-resume` / `akari:theme` only from `https://krtmtthw.dev`. Reduced motion stays on the eruption month. `_headers` detaches `X-Frame-Options` and the CSP for `/embed` only and sets `frame-ancestors https://krtmtthw.dev`.

## Data

Data contract: [`../contracts/`](../contracts/README.md). Types come straight from `../contracts/ts/readmodels.ts` (alias `@contracts/*`); never copy them.

`public/config.json` names the data base URL and fallbacks (no rebuild to switch): the published versions at `https://krtmtthw.dev/plumes/data/` (GitHub Pages), then the Hugging Face mirror. The app reads `latest.json` there, then every file relative to the version's `base`, falling back to `latest.mirrors`. Tests and offline development use the contract fixtures instead: with `PLUMES_FIXTURES=1` (set by `playwright.config.ts`), `scripts/vite-fixture-data.ts` serves `../contracts/fixtures/data` at `/data/` and a `config.json` pointing there; the build never contains them.

`src/content/sources.json` (the About page's licence table) is generated from `../docs/sources-draft.yaml`: `npm run sources`.

## Safety rules in code (RESEARCH.md §9)

- `SafetyBanner` is a layout element in `Shell`, on every route, not dismissable.
- `DataThrough` on every chart and map; alert levels only as "as reported by PHIVOLCS on <date>" markers (`data/tracks.ts`); every track carries its instrument wording (`INSTRUMENTS`) and coverage.
- `src/lib/safety.test.ts` scans the source for present-status and forecasting words (EN and JA); `e2e/safety.spec.ts` checks every rendered route in both languages.
- Rule 6b: `lib/richMedia.ts` loads MapLibre only with ≥768px, a hovering fine pointer and no Save-Data; otherwise the static SVG map (`map/StaticMap.tsx`).

## Develop

```sh
export NODE_AUTH_TOKEN=$(gh auth token)   # read:packages, for @abrycta/akari (copy .npmrc.example to .npmrc)
npm ci
npm run dev
npm run typecheck && npm run lint && npm test          # lean, local
npm run build && npm run e2e                           # full: screens, safety, axe in four themes, 390 px, device matrix (CI runs it)
```
