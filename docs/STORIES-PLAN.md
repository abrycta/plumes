# Stories plan: more story data first, then a standard story format

Status: 2026-10-22. **Kurt answered the 11 open questions the same day** (DECISIONS.md ST1–ST11, listed at the end of this plan); the plan below is updated to match. Nothing is built. Kurt's direction (2026-10-22): Plumes stories are **generated from data**, never hand-written and never AI-written. Fixed English and Japanese sentence templates are filled with sourced figures. A sentence appears only when its data exists. A story stays a draft until it is reviewed. The order is **first more story data (Part A), then the standard format (Part B)**. Plumes stays a retrospective record, never a hazard or warning service (Q1, Q14).

Inputs read: [DECISIONS.md](DECISIONS.md) (Q1–Q31, S1–S8, B1–B18, L1–L9, T1), [DATA-PLAN.md](DATA-PLAN.md), [LAYERS-PLAN.md](LAYERS-PLAN.md) (planned and rejected layers: not proposed again here without a new reason), [LICENCES.md](LICENCES.md), `pipeline/sources.yaml`, `story_taal()` in `pipeline/plumes/readmodels.py`, `contracts/schemas/story.schema.json`, and the live data version v2 (`https://krtmtthw.dev/plumes/data/v2/`: the manifest, the 24 volcano files and `story/taal-2020.json`). **[U]** marks a value that was not measured. Probes were limited to small read-only requests made on 2026-10-22; they are listed in §A6.

---

## Part A: story data sources

### A1. Where the 241 episodes stand today

The v2 volcano files hold **241 episodes**: 231 GVP eruptions and 10 PHIVOLCS alert windows (runs of Alert Level 2 or higher in the bulletins).

| Era | Episodes | Where |
|---|---|---|
| Before 1900 (13 BCE) | 117 | GVP only: a start date (often year or month only), sometimes a VEI |
| 1900–1999 | 73 | GVP only. Satellite and bulletin series do not reach these years |
| 2000–2009 | 17 | Mayon, Bulusan, Kanlaon. Only MODIS thermal (from 2000-11), USGS earthquakes and GVP VEI exist |
| 2010–2017 | 10 | adds Tokyo VAAC (from 2010) and VIIRS (from 2012); bulletins only from 2017-09 |
| 2018–2026 | 24 | every M1 series: bulletins and LAVA, VAAC, TROPOMI, thermal, USGS, GVP, MSVOLSO2L4; DROMIC for Taal 2020 only |

Every episode since 2000 belongs to one of five volcanoes: Mayon 23, Kanlaon 11, Bulusan 9, Taal 7 and Pinatubo 1. GVP lists no eruption since 2000 at the other 19. Their stories can only be deep-time cards (§B1).

Many GVP eruptions and alert windows describe the same event; Taal 2020, for example, is both `gvp-22344` and `alert-2020-01-12`. Merging the overlapping pairs gives **42 events since 2000**.

### A2. How "story-worthy" is measured

A story has four steps: **before** (the 90 days before the start), **onset** (the first 7 days), **course** (from day 8 to the end; empty for short episodes) and **after** (the 90 days after the end; an open-ended GVP episode is taken to end 30 days after its start). The step structure is justified in §B2.

A **fact family** is one kind of sourced fact that can fill a template:
- alert level (bulletins);
- bulletin numbers (volcanic earthquakes, SO₂ flux, plume height);
- VAAC advisories;
- satellite SO₂;
- thermal detections;
- USGS earthquakes;
- displacement (DROMIC);
- GVP VEI;
- MSVOLSO2L4 SO₂ mass.

The shortlist adds these families:
- GVP Weekly Report figures;
- HazEL impacts;
- DROMIC for more events;
- ~~OMI SO₂~~ (dropped 2026-10-23, DECISIONS L-OMI);
- Tokyo VAAC 2006–2009;
- COMET deformation.

Context that is always present does not count: population, imagery and winds. (Population is not a story sentence at all: ST13.)

- **Story-worthy:** at least 4 fact families, with at least one sentence in each of before, onset and after.
- **Rich:** at least 6 families, at least 2 of them event records (alert, bulletin numbers, VAAC, DROMIC, GVP Weekly, HazEL).

The score was computed from the v2 files with a throwaway script; it is not committed, because this PR is docs only. The method is above, so it can be rerun. The shortlist columns are **simulated** from the probes:
- a GVP Weekly Report counts when its week overlaps a step;
- ~~OMI SO₂ counts for every step from 2004-10~~ (dropped 2026-10-23);
- DROMIC counts when an event post's date falls in the onset or course;
- HazEL counts when the GVP number and year match;
- COMET counts for the before and after steps from 2016 at its 18 volcanoes.

These are upper bounds **[U]**. The real yield depends on how many figures can actually be extracted.

### A3. Coverage: story-worthy episodes, current sources vs. the shortlist

| Era | Episodes | Story-worthy now | With the shortlist | Rich now → shortlist |
|---|---|---|---|---|
| Before 1900 | 117 | 0 | 0 (deep-time cards, §B1) | 0 → 0 |
| 1900–1999 | 73 | 0 | 0 (deep-time cards) | 0 → 0 |
| 2000–2009 | 17 | 0 | **11** | 0 → 0 |
| 2010–2017 | 10 | 3 | **9** | 0 → 6 |
| 2018–2026 | 24 | 22 | **24** | 18 → 24 |
| **All** | **241** | **25** | **44** | **18 → 30** |
| Merged events since 2000 | 42 | 18 | **35** | — |

What moves the numbers:
- The **GVP Weekly Reports** overlap 50 of the 51 episodes since 2000. The exception is Mayon 2000-07-16, because the reports start in November 2000.
- ~~**OMI SO₂** reaches 43 of them~~ (dropped 2026-10-23).
- **COMET** reaches 29.
- **DROMIC** beyond Taal 2020 reaches 15.

Seven episodes since 2000 stay below the bar even with the shortlist: Mayon 2000, 2002, 2003 (two), 2004, Bulusan 2010 and Kanlaon 2003. They are short events with a weekly-report mention but no before or after record; they get a one-paragraph reading instead (§B1).

Pre-2000 episodes cannot become four-step stories from any open source found:
- 150 of the 190 have a full start date;
- 160 have a VEI;
- 32 match a HazEL record with deaths, damage or houses destroyed.

That is enough for a deep-time card, not for a stepped story.

### A4. Candidates

Effort: S = under 2 days, M = 2–5 days, L = more than a week. "Story step" names the step the source feeds. Licences follow LICENCES.md; any new wording is quoted with its link.

| # | Candidate | Facts it adds (step) | Episode coverage | Access | Licence (derived figures) | Size / free tier | Archivable (DATA-ARCHIVING.md) | Effort | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **Smithsonian/USGS Weekly Volcanic Activity Reports** (GVP) | PHIVOLCS-cited figures before 2017-09: alert changes with dates, SO₂ t/d, plume heights, evacuee counts citing DROMIC or NDRRMC, lake and crater observations (before, onset, course, after) | 50 of 51 episodes since 2000. Report counts in the Wayback snapshots (Dec 2025 – Feb 2026): Mayon 187 (2001–2026), Kanlaon 120, Taal 114, Bulusan 100, Pinatubo 9 | Per-volcano page `https://volcano.si.edu/volcano.cfm?vn=<n>&vtab=Weekly`. **On 2026-10-22 volcano.si.edu answered 403 ("Smithsonian site temporarily unavailable") to every scripted request**; the GVP WFS still worked. Wayback snapshots, e.g. `http://web.archive.org/web/20260212045835/https://volcano.si.edu/volcano.cfm?vn=273070&vtab=Weekly`, load with no login | Smithsonian terms: non-commercial with citation, already accepted for `gvp-eruptions-ph` (LICENCES.md; the terms page itself stays **[U]**, Q27). Plumes takes typed numbers and dates only, never prose, each linked to its report | About 3.3 MB of HTML for the five volcanoes; no Earth Engine | `update-input`: crawled pages bundled and adopted (B8 path). Links: volcano.si.edu (primary), Wayback (fallback), archive | M | **Shortlist #1** |
| 2 | **DSWD DROMIC, generalised** (registered; the M2 promise in `sources.yaml`) | People affected, people inside and outside evacuation centres, with report number and date (course, after) | 16 event posts found by the site search: Mayon 2018, 2022, 2023, 2026; Taal 2020, 2021, 2022 (two), 2026; Kanlaon 2022, 2024 (two), 2026 (two); Bulusan 2022, 2025. Reaches 15 episodes since 2000 | No login. Event posts list their files: Kanlaon 2024-12 has 271 PDF and 1 docx; Mayon 2023 has 88 PDF; Bulusan 2022 has 45 PDF and 17 docx; Taal 2021 has 22 docx. **The Mayon 2018 post links no files in its HTML [U where they are]** | Open, government work (LICENCES.md) | About 2.4 MB a report; about 1 GB for all events **[U]**; Actions only | As now: `update-input`, files adopted as releases | M–L (PDF tables) | **Shortlist #2** |
| 3 | ~~**OMI SO₂ `OMSO2e`**~~ **dropped by Kurt 2026-10-23** (DECISIONS L-OMI) | An SO₂ baseline and peak before TROPOMI (before, onset) | 43 episodes, 2004-10 → 2018 | Harmony, Earthdata token minted in CI | NASA open | No Earth Engine; 10–20 Actions minutes | Already planned | S (with M2) | **Shortlist #3** (already in M2) |
| 4 | **NOAA NCEI HazEL** (LICENCES.md; LAYERS-PLAN M2 rank 8) | Deaths, houses destroyed, damage in US$ millions (after) | 50 Philippine records. 8 since 2000: Mayon 2006, 2013, 2018; Bulusan 2006, 2011; Taal 2020; Kanlaon 2024 (two). 32 pre-2000 episodes match | `https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/volcanoes?country=PHILIPPINES` (one page, 25 kB; needs a browser User-Agent) | Open: "Access to this dataset is unrestricted." | Under 100 kB | `file`; archivekit snapshot | S | **Shortlist #4** (already in M2) |
| 5 | **Before/after imagery, generalised** (registered: `s2-sr-harmonized`, `landsat-c2-l2`) | One before and one after scene per event (before, after) | Every event since 2000 where a clear scene exists. Landsat 5/7/8/9 from 2000; Sentinel-2 from 2017-03-28 | Earth Engine thumbnails, as `taal-s2.json` | Copernicus notice; US public domain | About 0.05 EECU-h for 42 events **[U]**; 3 × 640 px JPEG ≈ 150 kB an event | `remote-dataset` (Earth Engine, plus STAC as second link) | S–M | **Shortlist #5** |
| 6 | **COMET LiCSBAS deformation** (L2, planned M2) | Line-of-sight change across the event (before, after) | 29 episodes (2016 →, at the five volcanoes; 18 volcanoes in all) | As LAYERS-PLAN §3 | CC BY-NC 4.0 with attribution (L1a) | As planned | As planned | — (M2) | **Shortlist #6** (reuse, no new work) |
| 7 | **Tokyo VAAC 2006–2009** (registered source, earlier years) | Ash advisories before 2010 (onset) | Bulusan 2006, 2007; Mayon 2006, 2009 (names found in the yearly lists) | `https://ds.data.jma.go.jp/svd/vaac/data/Archives/<YYYY>_vaac_list.html` answers 200 from 2006 (2003: 404). Older text files are named differently (`20061230_SHEV_0068_Text.html`) **[U parser changes]** | JMA terms, as now | Under 1 MB | As now | S | **Shortlist #7** |
| 8 | **GPM IMERG rain** (L4, planned M2) | Rain totals per step, stated as context (before, onset, course, after) | Every episode since 2000-06 (IMERG's start); counted as context, not as a fact family, so the score in §A3 is unchanged | As planned | NASA open | As planned | As planned | S (after M2) | **Shortlist #8**: shown whenever data exists (ST9), worded as context (§B4) |
| 9 | GVP Bulletin (BGVN) monthly reports | Detailed figures from 1975 onwards: evacuees, deaths, plume heights | At least 15–34 reports per volcano in the snapshots (1991 → 2023) | Same pages and same 403 as #1 | As #1 | Small | As #1 | M | **Later**: deep-time cards for 1975–1999 (Pinatubo 1991, Mayon 1993) |
| 10 | PHIVOLCS bulletins before 2017-09 via the Wayback Machine | The bulletins themselves (alert, earthquakes, SO₂) for Mayon 2006–2014, Bulusan, Taal 2010–11 | **[U]**: the Wayback CDX API answered 503 and "Temporarily Offline" to three queries on 2026-10-22 | CDX API | Government work (Q5 ii: each value cited with its link) | **[U]** | Adopted bundle | L | **Re-probe later**; #1 carries the same PHIVOLCS facts second-hand now |
| 11 | ReliefWeb API (out by Q30) | Dated report titles: NDRRMC and OCHA sitreps, flash updates | Events since about 2006 **[U]** | **Needs an approved `appname` now**: a probe returned 403 "You are not using an approved appname" (https://apidoc.reliefweb.int/parameters#appname) | Metadata usable. Mirrored documents: "personal, non-commercial use, without any right … to compile or create derivative works" (LICENCES.md) | Small | `live-feed` | S once an appname exists | **Left out for now (ST8)**; low value after #1 and #2 |
| 12 | GDACS volcano events | GLIDE numbers and dates | 11 events 2018–2026, all marked "Orange" | `https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH?eventlist=VO&country=Philippines` (no key) | Not checked | Tiny | `file` | S | **Reject as a fact source**: its content is an alert colour from a warning system (Q1, Q14). Not shown at all, not even the GLIDE id as a link (ST10) |

### A5. Rejected or not found (with reasons)

| Candidate | Reason |
|---|---|
| NDRRMC situation reports (class suspensions, flights, damage) | `ndrrmc.gov.ph` answered 403 again on 2026-10-22. The ReliefWeb mirror forbids derivative works (LICENCES.md). Stays a hand-collected source, out of scope (Q27) |
| Airport and flight disruption (NOTAMs) | No free archive of past NOTAMs was found; the FAA NOTAM API serves current NOTAMs only **[U]**. OpenSky is out (Q30). Airport closures appear only as prose in weekly reports, so no template is possible |
| School and class suspensions | No structured archive: DepEd and LGU announcements are social-media posts; NDRRMC is blocked (above). No template |
| News wires, GDELT, Wikipedia page views | Unsourced or second-hand, noisy, and already out (Q30). A dated fact from a wire story cannot pass the "sourced figure" rule |
| Wikidata eruption items (CC0) | A handful of named Philippine eruptions; adds names and links, no figures. Not worth a source |
| EM-DAT | Needs a login, its licence restricts redistribution, and HazEL covers the same deaths and damage openly |
| Infrasound (CTBTO IMS) | Data only under a vDEC agreement, not open |
| Lightning (WWLLN, Vaisala GLD360; GOES GLM; ISS LIS) | WWLLN and GLD360 are paid. GLM does not cover the Philippines. ISS LIS ended in 2023 and its overpasses are sparse |
| Copernicus EMS, International Charter | Only EMSR418 (Taal 2020) is known, hand-collected (Q27). Link only |
| Himawari ash RGB | Q26 stands |
| HydroSHEDS lahar rivers | L6 stands. Rain (#8) is a box total around the volcano, never tied to a channel |
| Sentinel-1 SAR change, MIROVA, CAMS, CALIPSO | Already decided in LAYERS-PLAN §4 and Q30; no new story reason |

### A6. Probes made (2026-10-22, read-only)

These requests were made:
- the GVP WFS GetCapabilities (no eruption-events layer; `E3WebApp_Emissions` returns a server error);
- `volcano.si.edu` (403 on every page);
- seven Wayback snapshots of GVP volcano pages (0.36–1.3 MB each);
- the Wayback availability API (works) and the CDX API (503);
- the DROMIC site search, pages 1–3, and five event posts;
- HazEL (one JSON page);
- GDACS (one JSON page);
- ReliefWeb (403, no appname);
- Tokyo VAAC yearly lists 2003–2009;
- `ndrrmc.gov.ph` (403).

Nothing was archived and no data job was run.

---

## Part B: the standard story format

### B1. Episode selection

1. **Events, not episodes.** Overlapping GVP eruptions and alert windows at one volcano merge into one event (42 since 2000). The event keeps every episode id. Its dates are the union of their spans. Its title uses the earliest start.
2. **Score** each event with §A2. The score is published in the story index (§B7) so the page can say why a story exists.
3. **Tiers:**
   - **Story** (story-worthy): four steps, generated in full.
   - **Reading** (story-worthy fails, but at least 2 families): one paragraph on the volcano page. This is today's `readings` model, built from the same templates.
   - **Deep-time card** (before 2000): GVP dates with their uncertainty, VEI, and HazEL impacts where they match. No steps.
4. **Order of generation:** by score (families), then VEI, then most recent first. Kanlaon 2024 comes first (Q29, M1.1).
5. **Overrides** are data, never prose. A small `pipeline/stories/overrides.yaml` may pin an event's span or step boundaries (Taal keeps 1 December 2019 → 31 March 2020) or a scene id. (The population-ring pin went with POP-RING, ST13.) Each override carries a reason line.

### B2. Step structure: before → onset → course → after

The brief suggested before → escalation → peak → aftermath. This plan proposes **before → onset → course → after**, with the peak as a highlighted figure inside a step, not a step of its own. The reasons:
- **"Peak" differs by series.** The SO₂ peak, the alert peak and the ash-height peak fall on different days; Taal's SO₂ peaked on 13 January, a day after the alert. A peak step would have to pick one series and hide the others.
- **"Escalation" is a forecast-shaped word.** In the record, escalation is simply the alert changes inside "before" and "onset". Naming it a step invites a trend reading (Q1).
- **Fixed windows can be tested.** The windows (−90 d, first 7 d, the rest, +90 d) make the absent-data rule mechanical.

The steps:

| Step | Window | Typical families |
|---|---|---|
| before | start − 90 d → start − 1 d | alert held or raised, SO₂ baseline, earthquake quiet or count, thermal, deformation |
| onset | start → start + 6 d | alert change with bulletin time, VAAC height and count, SO₂ peak, thermal peak, VEI, SO₂ mass |
| course | start + 7 d → end (dropped if empty) | alert changes, DROMIC peak inside evacuation centres, weekly-report figures |
| after | end + 1 d → end + 90 d | alert lowered, DROMIC totals, HazEL impacts, deformation, before/after images |

Step titles are templated: EN "Before" / JA 「噴火前」 (for unrest without an eruption, 「活動活発化の前」), and EN "12–13 January 2020" / JA 「2020年1月12〜13日」 for date-titled steps, as Taal's are today.

### B3. Template catalogue (EN + JA pairs)

The catalogue is a file (`pipeline/stories/templates.yaml`), versioned. Each entry has:
- `id`;
- `step`;
- `needs`: the series and fields that must all resolve;
- `when`: a condition on the data;
- `en` and `ja` with typed placeholders;
- the `figures` it emits;
- `source` ids for the attribution.

Placeholders are typed (`date`, `range`, `week`, `int`, `num1`, `fl`, `level`, `km`, `name`). **No free text from any source ever enters a sentence:** weekly-report prose is parsed to typed values, and the prose itself is never quoted.

**Wording rules** (a generated step renders as a list, one line per sentence, ST12; Japanese stays in the plain form, ST14)
- Dates: EN "12 January 2020", JA 「2020年1月12日」. Ranges: EN "1 to 11 January 2020", JA 「2020年1月1日から11日まで」. Weeks: EN "15–21 January 2020", JA 「2020年1月15日〜21日」. No ISO dates in text. Bulletin times: EN "7:30 PM", JA 「午後7時30分」.
- Numbers: EN thousands separator "4,057"; JA keeps the comma 「4,057人」. One decimal only where the source has one. A typographic minus "−" (`neg()`). Shares go through `share_txt()`, so a non-zero share never rounds to 0 %.
- Units: µmol/m², km, m, MW, kt, mm. Flight levels always carry a gloss: EN "FL550 (about 16.8 km)", JA 「FL550（約16.8 km）」.
- Brackets: JA uses full-width （） only; EN uses half-width ().
- Attribution phrasing, fixed per source:
  - PHIVOLCS: EN ", as reported by PHIVOLCS." / JA 「（PHIVOLCS発表）」
  - PHIVOLCS via a weekly report (ST2): EN ", as reported by PHIVOLCS, via Smithsonian/USGS." / JA 「（PHIVOLCS発表、スミソニアン/USGS経由）」. The figure carries the weekly report's link and week, and `reportedBy: "PHIVOLCS"`
  - DROMIC: EN "according to DSWD DROMIC Report #{k}" / JA 「DSWD DROMIC報告第{k}号によると」
  - Other sources are named as the subject ("Tokyo VAAC observed…", "The USGS catalogue lists…", "GVP records…").
- Plural forms: EN "1 earthquake" / "{n} earthquakes"; JA needs no plural (「{n}回」).
- Voice: past tense, a record of what an instrument or agency reported. No adjectives of magnitude ("major", "massive", 大規模), no causal links between series, no comparison with today. Rain sentences never share a sentence with an eruption, ash or lahar fact and never use causal words (EN because, caused, triggered, led to, due to, after which; JA ため, により, 原因, 引き起こ, 誘発); the checks in §B6 reject them.

**Catalogue (first version; the Taal ones reproduce today's reviewed text)**

| Id | Step | Needs | EN | JA |
|---|---|---|---|---|
| ALERT-HELD | before | bulletins `alertLevel`, one level on every bulletin day in the window | PHIVOLCS bulletins reported Alert Level {level} on every day from {d1} to {d2}, as reported by PHIVOLCS. | PHIVOLCSの火山情報は{d1}から{d2}まで毎日、警戒レベル{level}を発表していた（PHIVOLCS発表）。 |
| ALERT-HELD-GAPS | before | as above, with days missing | PHIVOLCS bulletins reported Alert Level {level} on each of the {n} days with a bulletin from {d1} to {d2}, as reported by PHIVOLCS. | PHIVOLCSの火山情報は{d1}から{d2}まで、発表のあった{n}日すべてで警戒レベル{level}だった（PHIVOLCS発表）。 |
| ALERT-RAISED | any | a level change upward (B14 parser) | PHIVOLCS raised the alert from level {a} to level {b} on {date}{time_en}, as reported by PHIVOLCS. | PHIVOLCSは{date}{time_ja}、警戒レベルを{a}から{b}に引き上げた（PHIVOLCS発表）。 |
| ALERT-LOWERED | course, after | a level change downward | PHIVOLCS lowered the alert from level {a} to level {b} on {date}, as reported by PHIVOLCS. | PHIVOLCSは{date}、警戒レベルを{a}から{b}に引き下げた（PHIVOLCS発表）。 |
| BUL-VEQ-MAX | any | bulletins `volcanicEq` | PHIVOLCS bulletins counted up to {n} volcanic earthquakes in a day from {d1} to {d2}, as reported by PHIVOLCS. | PHIVOLCSの火山情報は{d1}から{d2}までに1日最大{n}回の火山性地震を記録した（PHIVOLCS発表）。 |
| BUL-SO2FLUX-MAX | any | bulletins `so2FluxTpd` | PHIVOLCS measured SO₂ emissions of up to {x} tonnes a day from {d1} to {d2}, as reported by PHIVOLCS. | PHIVOLCSは{d1}から{d2}までに最大1日{x}トンのSO₂放出量を測定した（PHIVOLCS発表）。 |
| BUL-PLUME-MAX | onset, course | bulletins `plumeM` | PHIVOLCS reported plumes up to {m} m above the crater from {d1} to {d2}, as reported by PHIVOLCS. | PHIVOLCSは{d1}から{d2}までに火口上最大{m} mの噴煙を報告した（PHIVOLCS発表）。 |
| SO2-BASELINE | before | `so2_s5p_15km` or `so2_omi_box`, at least 5 clear days | The {sensor} SO₂ column within {r} km had a median of {med} µmol/m² from {d1} to {d2} ({n} of {N} days with a clear view). | {r} km圏の{sensor} SO₂カラム量は{d1}から{d2}までの中央値が{med} µmol/m²だった（{N}日中{n}日が観測可能）。 |
| SO2-PEAK | onset, course | as above | The {sensor} SO₂ column within {r} km reached {x} µmol/m² on {date}, its highest in this step (coverage {cov}). | {r} km圏の{sensor} SO₂カラム量は{date}に{x} µmol/m²で、この期間の最大だった（被覆率{cov}）。 |
| EQ-QUIET | before | `eq_usgs_30km`, no rows for at least 30 days before the onset count | The USGS catalogue lists no earthquake within 30 km after {d1} until {d2}, when it lists {n}, the largest M{m}. | USGSのカタログには{d1}の後、{d2}まで30 km圏の地震がなく、同日には{n}回（最大M{m}）が記録されている。 |
| EQ-COUNT | any | `eq_usgs_30km` | The USGS catalogue lists {n} earthquakes within 30 km from {d1} to {d2}, the largest M{m}. | USGSのカタログには{d1}から{d2}までに30 km圏の地震が{n}回記録されており、最大はM{m}だった。 |
| VAAC-MAX | onset, course | advisories, `heightBasis = observed` | Tokyo VAAC observed ash up to {fl} on {date}. | 東京VAACは{date}に最高{fl}の火山灰を観測した。 |
| VAAC-COUNT | onset, course | advisories | Tokyo VAAC issued {n} ash advisories from {d1} to {d2}. | 東京VAACは{d1}から{d2}までに{n}件の火山灰情報を発表した。 |
| HEAT-DAYS | any | `frp_modis_15km` or `frp_viirs_15km` | {sensor} detected heat within 15 km on {n} days from {d1} to {d2}, the strongest {x} MW on {date}. | {sensor}は{d1}から{d2}までの{n}日、15 km圏で熱異常を検出し、最大は{date}の{x} MWだった。 |
| GVP-VEI | onset | episode `vei` | GVP records the eruption as VEI {vei}. | GVPはこの噴火をVEI {vei}としている。 |
| SO2-MASS | onset | episode `so2MassKt` | NASA's MSVOLSO2L4 record lists {x} kt of SO₂ for the eruption of {date}. | NASAのMSVOLSO2L4は{date}の噴火のSO₂量を{x} ktとしている。 |
| DROMIC-AFFECTED | after | `displacement.affectedPersons` | DSWD DROMIC reports counted {n} people affected by {date}. | DSWD DROMIC報告は{date}までに{n}人の被災者を数えた。 |
| DROMIC-INSIDE-MAX | course | `displacement.insidePersonsNow` | The most people in evacuation centres, {n}, were counted on {date}, according to DSWD DROMIC Report #{k}. | DSWD DROMIC報告第{k}号によると、避難所にいた人は{date}の{n}人が最多だった。 |
| WEEKLY-ALERT | any (before 2017-09) | weekly-report extraction `alert_change` | PHIVOLCS raised the alert to level {b} on {date}, as reported by PHIVOLCS, via Smithsonian/USGS. | PHIVOLCSは{date}に警戒レベルを{b}に引き上げた（PHIVOLCS発表、スミソニアン/USGS経由）。 |
| WEEKLY-EVAC | course | weekly extraction `evacuees` with the agency named in the same sentence | {n} people were in evacuation centres on {date}, as reported by {agency}, via Smithsonian/USGS. | {date}には{n}人が避難所にいた（{agency}発表、スミソニアン/USGS経由）。 |
| WEEKLY-SO2 | any | weekly extraction `so2_tpd` | SO₂ emissions were {x} tonnes a day on {date}, as reported by PHIVOLCS, via Smithsonian/USGS. | {date}のSO₂放出量は1日{x}トンだった（PHIVOLCS発表、スミソニアン/USGS経由）。 |
| WEEKLY-LAKE-GONE | onset, course | weekly extraction `lake_gone` (ST4) | Satellite images in the week of {week} showed that the Main Crater lake was gone, as reported by PHIVOLCS, via Smithsonian/USGS. | {week}の衛星画像では主火口湖が消失していた（PHIVOLCS発表、スミソニアン/USGS経由）。 |
| HAZEL-DEATHS | after | HazEL `deathsTotal` | NOAA's Significant Volcanic Eruptions Database records {n} deaths for this eruption. | NOAAの重要火山噴火データベースは、この噴火による死者を{n}人と記録している。 |
| HAZEL-HOUSES | after | HazEL `housesDestroyedTotal` | It records {n} houses destroyed. | 全壊家屋は{n}棟と記録されている。 |
| HAZEL-DAMAGE | after | HazEL `damageMillionsDollarsTotal` | It records damage of about US${x} million. | 被害額は約{x}百万米ドルと記録されている。 |
| DEFORM-LOS | before, after | `los_comet_<frame>` | COMET's Sentinel-1 record shows {x} mm of movement {toward/away from} the satellite along its line of sight from {d1} to {d2}. | COMETのSentinel-1記録では、{d1}から{d2}までに視線方向で{x} mm（衛星に{近づく/遠ざかる}向き）の変位があった。 |
| RAIN-TOTAL | any (ST9) | IMERG daily sums within 15 km, every day of the step present | GPM IMERG estimates {x} mm of rain within 15 km from {d1} to {d2}. | GPM IMERGの推定では、{d1}から{d2}までに15 km圏で{x} mmの雨が降った。 |
| RAIN-WETTEST | course, after | as above, and the step has at least one day of 1 mm or more | The wettest day in this period was {date}, with {x} mm. | この期間で最も雨が多かったのは{date}で、{x} mmだった。 |
| IMAGE-CAPTION | before, after | a chosen scene (§B5) | {sensor}, {date} | {sensor}、{date} |

Today's Taal "crater" step text ("the main crater lake on Volcano Island drained during the eruption") is a hand-written observation. **Kurt chose (ST4)** to source it from the weekly report for 15–21 January 2020 ("Satellite images showed that the Main Crater lake was gone"): the extractor gets a `lake_gone` rule, and the step renders WEEKLY-LAKE-GONE beside the Sentinel-2 captions. The reviewed text therefore changes once, and Kurt reviews it again.

### B4. The absent-data rule and its "why" sentences

- A template renders only when **every** placeholder resolves to a value with a source id, plus a URL for PHIVOLCS, VAAC, DROMIC and the weekly reports (Q5 ii).
- **A zero is not an absence.** "No earthquake within 30 km" is a fact sentence when the series covers those dates. A "why" sentence explains a missing record, never a zero.
- If a step has no fact sentence, it shows one fixed "why" line per missing family. These are the same reasons as the volcano page (B18), so both pages agree. If no step but "after" has anything, the event is not a story (§B1).

| Why id | EN | JA |
|---|---|---|
| WHY-NO-BULLETINS | PHIVOLCS bulletins for these dates are not on line; the online record for {volcano} starts on {date}. | この期間のPHIVOLCS火山情報はオンラインで公開されていない（{volcano}の記録は{date}から）。 |
| WHY-BEFORE-INSTRUMENT | {sensor} began observing on {date}, after these dates. | {sensor}の観測は{date}に始まり、この期間より後である。 |
| WHY-NO-VAAC | Tokyo VAAC's online list has no ash advisory for {volcano} in these dates (the list starts in {year}). | 東京VAACのオンライン一覧には、この期間の{volcano}に関する火山灰情報がない（一覧は{year}年から）。 |
| WHY-NO-DROMIC | No DSWD DROMIC report was found for this event. | このイベントに関するDSWD DROMIC報告は見つからなかった。 |
| WHY-NO-CLEAR-SCENE | No cloud-free Landsat or Sentinel-2 scene was found within 90 days. | 90日以内に雲のないLandsatまたはSentinel-2の画像が見つからなかった。 |
| WHY-NOT-COVERED | {source} does not cover {volcano}. | {source}は{volcano}を対象としていない。 |

**Rain (ST9):** RAIN-TOTAL and RAIN-WETTEST appear in every step where IMERG has every day, whether or not a lahar was reported. They are context, so they do not count towards the story-worthy score. They are always their own sentences, last in the step, never joined to an eruption, ash or lahar fact, and never phrased as a cause. Rain is never shown as a threshold or beside a channel (L6), so it cannot read as a lahar warning. If a lahar is reported, that is its own sentence from its own source.

### B5. Images per step (chosen by rule, not by hand)

- **Before:** the latest scene in [start − 90 d, start − 1 d]. **After:** the earliest scene in [end + 1 d, end + 90 d], or inside the course for events longer than 60 days.
- **Sensor:** Sentinel-2 L2A from 2017-03-28; otherwise Landsat 8/9, then Landsat 5. Landsat 7 is used only before 2003-05-31, because of the SLC-off stripes afterwards.
- **Clear:** under 10 % cloud inside a 5 km box around the summit (QA band / SCL). Ties go to the scene closest to the step boundary.
- **Pairs only:** both images exist or neither is shown, with WHY-NO-CLEAR-SCENE.
- **Format:** true colour, 640 px JPEG (as `assets/taal-s2-*.jpg`). The caption comes from IMAGE-CAPTION. The credit follows the source ("Contains modified Copernicus Sentinel data {year}"; Landsat: "Landsat imagery courtesy of the U.S. Geological Survey").
- A reviewer may pin a different scene id in `overrides.yaml`, with a reason (a cloud the mask missed, for example). The rule still says what was chosen.

### B6. Review flow (draft → reviewed)

> Superseded on 2026-10-23 by DECISIONS ST15: there is no manual review; a story publishes when the automated checks pass.

1. The generator writes every story with every step at `status: draft`.
2. `pipeline/stories/review.yaml` records reviews:
   - one entry per story and step, holding the SHA-256 of the step's rendered `en` + `ja` + figures, the reviewer and the date;
   - a step is `reviewed` only while its hash matches;
   - new data that changes a number turns the step back into a draft, which is the point.
3. A review page is built by the Data workflow as a CI artifact, not published: one HTML file listing every draft step with its figures, each figure's source link, and the template id behind each sentence. Kurt reviews a batch, and an agent's PR adds the hashes to `review.yaml`. Today's Taal 2020 story is migrated by recording the current hashes (T1, B15), so it stays reviewed.
4. Checks: the version check fails the build if any of these appear:
   - **safety or advice words** in rendered text, EN: should, must, avoid, stay away, safe, unsafe, danger, dangerous, warning, risk, hazard, expect, likely, forecast, predict, will erupt; JA: 危険, 安全, 注意して, 避難してください, 警告, 予測, 予想, 恐れ, 可能性, 見込み. The fixed summary disclaimer ("not a hazard assessment" / 「ハザード評価ではない」) is the only allowed exception, matched exactly;
   - **an unsourced number:** every digit run in a sentence must come from a placeholder whose value has a source id. The check re-renders the sentence with the placeholders masked and expects no digits left, except fixed template constants such as "30 km", "15 km", "7 days" and "FL", which are declared in the template;
   - **EN and JA disagree:** the same multiset of placeholder values in both languages, and every figure's value appears in its step's text;
   - **half-width brackets, English words or ISO dates in Japanese** (`ja_leftovers()`, extended to the step titles and the why lines);
   - **free text from a source:** no placeholder of type `text` exists, so the check is structural;
   - **causal words in a rain sentence** (the list in §B3's voice rule);
   - **a step with neither a sentence nor a why line.**
5. **Drafts on the site (ST1):** the site shows only stories whose steps are all reviewed. Drafts stay in the data files, marked `draft`, for the review page; the web app filters on the story's derived `status`.

### B7. Schema changes vs. `story.schema.json`

All changes are additive; v2 files stay valid. They land in one contract PR, approved by Kurt before it is built, like L3a.

| Where | Change |
|---|---|
| story | `generator: { name, version, catalogueVersion }`; `episodeIds: [string]`; `score: { families: int, steps: int, tier: "story" \| "reading" }`; `status` (derived: `reviewed` only when every step is) |
| step | `kind: "before" \| "onset" \| "course" \| "after"` (the `id` stays free, so Taal's `eruption` and `people` ids stay valid); `sentences: [{ template, text: localText, figures: [int], sources: [sourceId] }]` (`text` stays the joined sentences, so the web app needs no change at first); `absent: [{ why, text: localText }]` |
| asset | `role: "before" \| "after"`, so the page can pair images without parsing captions |
| figure (common.schema.json) | optional `reportedBy` (e.g. `"PHIVOLCS"` when the source is `gvp-weekly-reports`), so second-hand figures say whose number it is |
| new `stories.schema.json` | `<version>/stories.json`: an index of `{ id, volcanoId, title, span, episodeIds, score, status }` for every generated story and reading. The overview links reviewed stories from it |
| registry | new source ids: `gvp-weekly-reports`; `noaa-hazel` (planned M2); DROMIC links per event |

### B8. How `story_taal()` becomes the first instance

1. Move the helpers `date_en`, `date_ja`, `fl_gloss`, `neg`, `share_txt`, `ja_leftovers` and `wp_slug_meta` unchanged into `pipeline/plumes/stories/text.py`.
2. Express each Taal sentence as a catalogue template: ALERT-HELD, SO2-BASELINE (Taal's December median plus the 1–11 January range is a two-clause variant), EQ-QUIET, ALERT-RAISED with the bulletin time, VAAC-MAX, GVP-VEI, and DROMIC-AFFECTED. (Today's "WorldPop … within 14 km" sentence has no template: POP-RING was dropped, ST13.)
3. Add a golden test: the generic generator, run on v2 data with Taal's overrides, renders `taal-2020` **byte for byte** like today's reviewed story, apart from the crater-step change Kurt chose (ST4, §B3) and the new additive fields. When the test passes, `story_taal()` is deleted and `build()` calls `generate_stories()`.
4. The Taal reading on the volcano page is generated the same way. Its "within hours" phrase is not data-derived, so it becomes ALERT-RAISED's wording, after Kurt's review.

### B9. Where the shared format lives

- **Planned, not written now (Kurt, 2026-10-22):** a workspace-level `/Users/kurt/portfolio/STORY-FORMAT.md`, a short standard like DATA-ARCHIVING.md (step model, template-entry fields, wording rules, review-hash rule, checks). Until then this plan is the specification. The JSON schema stays in Plumes' `contracts/`.
- **Code:** the code stays in `plumes/pipeline/plumes/stories/` with no Plumes imports in the core (renderer, checks, review hashing); the series adapters are Plumes-specific.
- **When a second project wants stories** (Replay's storms are the obvious one), the core moves to a new private package **`abrycta/story-kit`** (ST7), not into `data-archive-kit`.

### B10. Implementation order and effort

| # | Step | Effort | Depends on |
|---|---|---|---|
| 1 | Contract PR (§B7), approved by Kurt | S | this plan |
| 2 | Generator core: catalogue loader, typed renderer, checks (§B6.4), review hashes; Taal golden port (§B8) | M (3–4 days) | 1 |
| 3 | Event merge, scoring, tiers, `stories.json`, why lines | S | 2 |
| 4 | Review page (CI artifact) and `review.yaml` flow | S | 2 |
| 5 | Imagery rule generalised (§B5) | S–M | 2 |
| 6 | Kanlaon 2024 as the first generated story; Kurt reviews (Q29) | S | 2–5 |
| 7 | Sources: HazEL (already in the M2 order; OMI SO₂ dropped 2026-10-23); Tokyo VAAC 2006–2009 | S each | — |
| 8 | GVP Weekly Reports crawler and extractor (typed patterns, each with a test from a real sentence) | M | ST2: Wayback snapshots as the primary link while volcano.si.edu refuses scripts |
| 9 | DROMIC generalised to the 16 events (docx and PDF tables; `pdfplumber` allowed, ST11) | M–L | — |
| 10 | Generate all story-worthy events (44 episodes, 35 events); Kurt reviews in batches of about 5 | S per batch | 3–9 |

Steps 7–9 can run beside 2–6. Step 10 is the only step that needs Kurt's time repeatedly.

---

## Kurt's answers (2026-10-22, recorded as ST1–ST11 in DECISIONS.md)

All 11 questions are resolved. Where the answer differs from the recommendation, the plan above has been changed.

1. ~~Drafts on the site~~ **Resolved (ST1):** hidden until every step is reviewed (as recommended).
2. ~~GVP Weekly Reports~~ **Resolved (ST2):** crawl them from Wayback snapshots; PHIVOLCS figures quoted in them are allowed, attributed "as reported by PHIVOLCS, via Smithsonian/USGS" (the attribution wording changed from the draft; §B3).
3. ~~Steps~~ **Resolved (ST3):** before → onset → course → after (as recommended).
4. ~~Taal crater step~~ **Resolved (ST4):** the "lake drained" line is sourced from the weekly report (`lake_gone`, WEEKLY-LAKE-GONE).
5. ~~Thresholds and tiers~~ **Resolved (ST5):** at least 4 fact kinds covering before, onset and after; deep-time cards for pre-2000 events (as recommended).
6. ~~Events~~ **Resolved (ST6):** each GVP eruption merges with its overlapping alert window into one story (as recommended).
7. ~~Shared format~~ **Resolved (ST7):** shared code goes to a new `abrycta/story-kit` when a second project needs it. `STORY-FORMAT.md` stays a planned item, not written now (§B9).
8. ~~ReliefWeb~~ **Resolved (ST8):** left out for now (as recommended).
9. ~~Rain~~ **Resolved (ST9), differs from the recommendation:** rain is shown **whenever data exists**, not only beside a reported lahar, worded as context without implying a cause (RAIN-TOTAL, RAIN-WETTEST; §B4 and the checks in §B6).
10. ~~GDACS~~ **Resolved (ST10):** not shown at all.
11. ~~DROMIC PDFs~~ **Resolved (ST11):** `pdfplumber` is allowed in the pipeline.

## Not verified

- **volcano.si.edu was unreachable to scripts on 2026-10-22** (403, "temporarily unavailable"). The weekly-report counts come from Wayback snapshots of December 2025 to February 2026.
- The Smithsonian terms page is still **[U]** (Q27).
- The Wayback CDX API was down, so the coverage of PHIVOLCS bulletins before 2017 is unknown.
- The shortlist coverage is simulated by overlap (§A2), not by extracted figures.
- The Mayon 2018 DROMIC files were not found.
- The DROMIC total size, the imagery EECU cost and the parsing of pre-2010 VAAC files are estimates.
- The FAA NOTAM archive statement is from documentation memory, not a probe.
