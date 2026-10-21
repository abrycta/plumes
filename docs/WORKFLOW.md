# Workflow: from idea to milestone 1

Written 2026-10-21, before any topic research. This project is the next big-data map of the Philippines in the spirit of Lights (`../../lgu-lights/`), but its topic is not fixed yet: Kurt suggested volcanoes and asked for alternatives. The workflow below adapts how Lights and Typhoon Replay were run (`../../lgu-lights/docs/`, `../../typhoon-replay/docs/architecture/`) to that situation, and applies the workspace rules in `../../CLAUDE.md`: the archiving standard with `archivekit` (`../../DATA-ARCHIVING.md`), the Akari design system, free tiers only, the commit identity, Keychain secrets, the project page and share card (`../../PROJECT-PAGES.md`, `../../share-cards/README.md`), "architecture before code" and lean testing.

## What is different about this project

1. **The topic is chosen by comparison, not assumed.** Lights started from a paper Kurt co-authored; here the first phase produces a scored comparison of 4–6 candidates and Kurt picks one. Everything after that phase is specific to the chosen topic, so the deep documents are written only for the recommended candidate (with enough on the runners-up that a different pick costs a day, not a week).
2. **It must be Lights-like without repeating Lights.** The bar set by Lights: many real public sources, a national map with a time series, honest uncertainty shown beside official figures, plain-language explanations, English and Japanese, a pipeline in GitHub Actions, static-first delivery. The comparison scores each candidate on what it adds technically beyond Lights (a per-LGU annual panel with a Rust core) and Typhoon Replay (a Java/PostGIS event replay).
3. **Natural-hazard topics carry a safety duty.** If the topic touches volcanoes, earthquakes, floods or air quality, the site is a retrospective record, never a source of live hazard status or alerts. It names the authority (PHIVOLCS, PAGASA, DENR) on every view and links to it. This is a gate in the research phase, not a footnote.
4. **Licences decide what can be published.** Satellite agencies (ESA Copernicus, NASA) are open; Philippine government sources are a mix of CC BY (PSA OpenSTAT), government works under RA 8293 §176 (free use, prior approval for profit-making exploitation) and portals with no stated terms. Every source's terms are quoted in `RESEARCH.md` and encoded in `sources-draft.yaml` before anything is downloaded in bulk.

Rules carried over from the other projects:
- **Questions are not requests.** Each phase ends in numbered questions with a recommendation each; nothing is built until Kurt answers.
- **Lean testing.** Targeted tests locally for what changed; full suites on GitHub CI; no tests that don't guard something likely to break.
- **No external resources during planning.** No repos, accounts, DNS, Cloudflare, Neon, Render or Hugging Face resources are created; the plan lists what will be needed.

## Phases

| # | Phase | Produces | Decision gate | Done when |
|---|---|---|---|---|
| 0 | Workflow | `docs/WORKFLOW.md` (this file) | — | Committed before research starts |
| 1 | Candidate research and comparison | `docs/CANDIDATES.md` (4–6 candidates, scored; a recommendation), the candidate-specific sections of `docs/RESEARCH.md` | **Q1: which candidate to build** | Every candidate has its sources listed with licences and access dates, a volume estimate against the free tiers, a safety and honesty assessment, and scores with one-line reasons; the recommendation names its runner-up |
| 2 | Kurt picks a topic | an answer to Q1 in `docs/DECISIONS.md` | — | Q1 answered; the working folder is renamed to the project's name |
| 3 | Deep research and architecture options | `docs/RESEARCH.md` (full), `docs/DATA-PLAN.md`, `docs/ARCHITECTURE-OPTIONS.md` (2–3 named standard patterns, trade-offs, recommendation with a "standard → our variant" table), `docs/sources-draft.yaml` validated with `archivekit validate-registry`, `docs/SPIKE-PLAN.md`, `docs/OPEN-QUESTIONS.md` (Q2…Qn) | **Q2…Qn**: architecture, languages, hosting, scope of milestone 1, publishing, naming | Every claim has a link and an access date; estimates are marked **[U]**; each option is costed against the free tiers with size estimates; the safety framing is written into the product scope |
| 4 | Kurt's decisions | `docs/DECISIONS.md` filled (Q1…Qn, with the reason where Kurt gave one) | — | Every question has an answer or an accepted default; any credential the spike needs is in the Keychain |
| 5 | Measurement spike | `docs/SPIKE-RESULTS.md`; throwaway code in `spike/` (outputs gitignored); an addendum in `DECISIONS.md` (S1…Sn: what changed, what stands) | the addendum may reopen a question | Every **[U]** the spike covers is replaced by a measurement; nothing measured threatens the chosen architecture, or the architecture is amended and the amendment is recorded |
| 6 | Build slices | code, `pipeline/sources.yaml`, the private archive repo, CI, the data version, the site; build notes appended to `DECISIONS.md` (B1, B2, …) | — | Each slice is deployable on its own and leaves the app working (see the slice list) |
| 7 | Milestone review | the project page updated, the share card and LinkedIn copy, "Where it stands" honest, `docs/README.md` refreshed | — | The page's facts match the deployed app; known limitations are listed; the data-as-of date and attributions are shown in the app |

Phase 1 runs now, in one planning session; phases 1 and 3 overlap for the recommended candidate so that Kurt's pick in phase 2 can be followed by decisions in phase 4 without another research round. Phases 5–7 repeat for each milestone.

### Phase 1: candidate research and comparison

Each candidate gets the same treatment in `CANDIDATES.md`:
- the sources, each with: what it contains, years, resolution, format, access path (direct file, API, Earth Engine, STAC), licence quoted, redistribution answer (raw: archive privately only; processed: publish with attribution), fit with `archivekit` (`file`, `live-feed`, `remote-dataset`, `update-input`);
- data volume and free-tier fit: GitHub Actions minutes (public repo: free; private archive repo: 2,000 min/month shared), Earth Engine noncommercial EECU-hours, Cloudflare Pages 25 MiB per file and 20,000 files, Hugging Face datasets, Neon free storage, browser payload budgets;
- scientific honesty: what the data can and cannot say, the uncertainty, what safe claims look like, and (for hazards) the authority framing;
- public interest in the Philippines and how the project reads in a portfolio (to a recruiter, in two sentences);
- technical showcase: what it demonstrates that Lights and Typhoon Replay do not;
- risks, with mitigations;
- scores 1–5 on each axis with a one-line reason, plus an overall recommendation.

Rejected ideas from `../../big-data-ideas.md` and the memory notes are not re-proposed without saying so. Research is web search and fetch with citations and access dates; probes are tiny (one API call to see a response shape); nothing is downloaded in bulk and Earth Engine is touched only if a small probe truly needs it.

### Phase 3: deep research and options

For the recommended candidate (and in outline for the runner-up):
- `RESEARCH.md`: per source, the facts above in full, plus the science (what the measurements mean, known biases, the literature that validates them), existing products, free-tier limits re-verified on the day;
- `DATA-PLAN.md`: the data model, per-source volumes, the processing path (Earth Engine, Actions, or browser), the published artefacts with sizes, archiving with `archivekit`, data versions and rollback, cadence and CI budget, the resources to create;
- `ARCHITECTURE-OPTIONS.md`: 2–3 named, widely recognised patterns customised for this project (Kurt's preference: a well-known standard, customised). It reuses what worked (Akari, MapLibre, static-first, `archivekit`, Rust/WASM or Java where it earns its place) and justifies any new technology with a measured or cited reason. It defines the 60-second demo, the user stories and the milestone-1 scope;
- `SPIKE-PLAN.md`: the one-day measurement spike, with the estimate, the method and the pass/fail bar per item;
- `OPEN-QUESTIONS.md`: Q2…Qn with options and a recommendation each; a list of what to verify by hand;
- `sources-draft.yaml`: the registry draft, validated against the kit's schema.

### Phase 5: the spike

One day, after the decisions. Throwaway code in `spike/` with gitignored outputs. It measures what the documents estimated: Earth Engine cost per year of data, output sizes, tile sizes and request counts, browser load times, and anything the architecture depends on. It never backfills and never creates permanent resources. Results go to `SPIKE-RESULTS.md` with a table (measurement, estimate, result, verdict) and an addendum in `DECISIONS.md`.

### Phase 6: build slices

The order is fixed once the architecture is decided; the default is: (1) repository layout, registry, CI skeleton and the private archive repo; (2) the pipeline for one source end to end, with data-quality checks and a published data version; (3) the remaining sources; (4) the read models and tiles; (5) the React/Akari map and the per-place view with uncertainty and plain-language text; (6) English and Japanese; (7) the project page, share card and LinkedIn copy. Choices made while building where the docs were silent are appended to `DECISIONS.md` as build notes.

### Phase 7: milestone review

Update the site page (`../../site/src/content/projects/<slug>.mdx`, owned by the site agent during planning: send a list of changes), the status (`Planned` → `In development` → `Live`), `facts`, the architecture diagram, "Where it stands" with limitations, `updated`. Make the share card and LinkedIn copy per `../../share-cards/README.md` when the app first goes live.

## How knowledge is kept

All project knowledge lives in `docs/`:

| File | Role |
|---|---|
| `README.md` | Index: what each document is, in reading order, plus the status line |
| `WORKFLOW.md` | This file |
| `CANDIDATES.md` | The phase-1 comparison and recommendation |
| `RESEARCH.md` | Facts with sources and access dates; **[U]** marks estimates |
| `DATA-PLAN.md` | Sources, licences, volumes, processing, archiving, versions |
| `ARCHITECTURE-OPTIONS.md` | Patterns, trade-offs, recommendation, product scope |
| `OPEN-QUESTIONS.md` | Numbered questions for Kurt; the "verify by hand" list |
| `DECISIONS.md` | The log: decisions, spike addenda, build notes; never rewritten, only appended |
| `SPIKE-PLAN.md`, `SPIKE-RESULTS.md` | Measurement before building |
| `sources-draft.yaml` | Registry draft until `pipeline/sources.yaml` exists |

Other projects' documents are referenced by relative path, never copied. Dates are written in full (2026-10-21). Writing: plain English, short sentences, facts over adjectives, no invented numbers; every external fact carries a link and an access date.

## Testing stance

- **Locally:** only the tests for what changed (one pytest module, one Vitest file, one Rust test); none for trivial edits. Never a full suite on the laptop.
- **CI (GitHub Actions, public repo):** the pipeline's data-quality tests, the core's unit and parity tests, the web unit tests, a build. Merge on green.
- **What gets tests:** parsers against committed small fixtures (licence-checked), the zonal-statistics cross-check, the read-model builder (idempotent, deterministic), the uncertainty and plain-language rules, the registry hooks. Not: UI snapshots for every component, or tests that restate the code.
- **Data-quality tests block publishing** (archiving standard §4): a failed check never replaces good data.

## Keeping the page and the share card current

- Project start: after Q1 is answered, the page exists with status `Planned`, from the recommended architecture; after phase 4 it shows the decided architecture (diagram, stack chips with only decided technologies).
- Every milestone: `status`, `facts`, links, "Where it stands", `updated`; a screenshot when live.
- The share card and the LinkedIn title and description are made when the app first goes live and refreshed at milestones.
- During planning the site repo is not touched; the planning report lists the page changes to make.
