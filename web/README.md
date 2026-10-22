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
