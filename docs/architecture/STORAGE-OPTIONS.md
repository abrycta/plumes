# Storage options: keeping published data bounded

Status: **chosen: A1 now, then C's release step** (decided 2026-10-23; DECISIONS S1, S2). Done: C's release step and the
storage triggers (Data run). Not done: C's HF pruning and squash (waiting for the §3 step 4 triggers), D, A2, B.
Source: data audit P16 / CRITIC item 11 ("about 2 GB a year of HF history; changed bundles are
re-uploaded whole"). Measured 2026-10-23 on gh-pages `1c9e3b5` (v6), HF `permission-alluring/plumes`
`a6ccefc` and `abrycta/plumes-archive` releases.

## 1. What is stored today (measured)

| Store | What it holds | Size now | Growth per published version |
| --- | --- | --- | --- |
| gh-pages (Pages source, `abrycta/plumes`) | tree: last 2 versions (`publish.py` prunes older ones); history: every version | tree 76.6 MiB; branch pack 40.8 MiB (6 commits); whole repo 42.6 MiB (GitHub API `size`) | 0.7 to 15 MiB of git pack, depending on how well git deltas the near-identical files |
| HF mirror `permission-alluring/plumes` | **every version stays in the tree** (`upload_folder` never deletes): v1 to v6, 909 files | `usedStorage` 151.6 MB (= 144.6 MiB of unique LFS objects, 165 objects) plus 53.7 MiB of small JSON kept in plain git (not in `usedStorage`) | ~26.4 MiB of new LFS objects + ~11 MiB of JSON in git, i.e. **~37.5 MiB per version** |
| `abrycta/plumes-archive` releases | source **inputs** only (adopted bundles, `adopt --changed-only`), not published versions | 49 releases, 144 assets, 189 MiB (one-off `comet-licsbas` is 141 MB) | live feeds that change weekly (FIRMS MODIS ~6 MB, S5P SO2 9 to 13 MB, VIIRS 2.4 MB, S5P AI 2.2 MB): ~20 to 25 MB per week |

A version is 197 files, 38.3 MiB (128 pmtiles layers ≈ 26 MiB, 24 volcano JSON ≈ 11 MiB, stories, assets).
v1 to v6 were published 21 to 23 October by manual dispatch; the steady cadence is weekly (`data.yml` cron,
Saturday 18:00 UTC).

### Which files change each week, and why

From v4 to v5 and v5 to v6, **77 of 197 files (33.4 of 38.3 MiB, 87 %) changed**, almost none of it new data:

- **Every pmtiles file (28 files, ~26 MiB)**: tile data is byte-identical between versions; only the embedded
  metadata differs, because tippecanoe's default `name` and `description` are the output path (`.../site/v6/...`).
  That path is an absolute local build path (`/tmp/build/...`), so it is also published in every tile file.
  `readmodels.py:486,510` call tippecanoe without `-n`/`-N`.
- **Every JSON body (49 files, ~7 MiB)**: `dataVersion` and `generatedAt` are stamped into each file
  (`manifest.json`, `layers.json`, `stories.json`, `deeptime.json`, 24 volcano files, 20 stories,
  `volcanoes.geojson`). The API loader checks that per-file header (`Loader.java:141,157`), so it is part of the
  file contract.
- **Real content changes v5 to v6**: about 0.5 MiB (story copy edits and the manifest). A normal weekly run with new
  detections is expected to change the current-year thermal layer (~1.7 MiB), the earthquake layer (~3.3 MiB) and
  the volcano files that gained data: an estimated 2 to 15 MiB.

The growth comes from version stamps inside files. HF already de-duplicates identical LFS objects (`usedStorage`
equals the sum of unique LFS OIDs), so identical bytes would cost nothing.

### When a limit is reached at today's rate (one version per week, nothing changed)

| Store | Limit (source) | Reached |
| --- | --- | --- |
| HF public storage, free user | "Best-effort"; "beyond the first few gigabytes, please use this resource responsibly" ([HF storage limits](https://huggingface.co/docs/hub/storage-limits)). No hard cap, no bill for public repos. | ~1.4 GB/year counted + ~0.6 GB/year of git JSON ≈ **2 GB/year**: "a few gigabytes" (3 to 5 GB) in **mid-2028 to late 2029**; sooner with extra dispatches. Commit and file counts (2 commits and 197 files per version; recommended < 100k files, < 10k per folder) stay fine for ~10 years. |
| GitHub Pages published site | 1 GB hard ([Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)) | Never at 2 versions (77 MiB). |
| Pages source repo / any repo | 1 GB recommended for Pages sources; repos "ideally less than 1 GB, and less than 5 GB is strongly recommended" ([large files](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)); 100 MiB per file hard | Observed 40.8 MiB pack for 6 versions. 1 GB in **~1.3 years** if the stamped tiles stop delta-compressing (15 MiB/week), **~5 years** at the good-delta rate (4 MiB/week). Largest file 3.3 MiB. |
| Release assets | < 2 GiB per file, ≤ 1000 assets per release, "no limit on the total size of a release, nor bandwidth" ([about releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)) | Not reached (~1.2 GB/year of inputs, largest asset 141 MB). |
| HF history cleanup | `super_squash_history` squashes a branch into one commit; "a destructive operation that cannot be undone ... LFS file history will be removed"; quota updates within 36 hours; deleting LFS pointers alone frees nothing ([HF storage limits](https://huggingface.co/docs/hub/storage-limits)) | n/a |

### How a pruned version is recovered today

`DATA-ARCHIVING.md` requires published versions to stay recoverable. Today two places hold them: the gh-pages
**git history** (every `Data version vN` commit) and the HF tree (every `v<N>/` folder). The archive repo holds only
the inputs, and a rebuild from inputs is not byte-identical (stamps, Earth Engine results). Any option that squashes
HF or rewrites gh-pages therefore needs another copy of each published version first.

## 2. Options

### A. Stable bytes for unchanged files (stamp hygiene)

- **A1 (pipeline only):** pass stable `-n`/`-N` (layer name and description) to tippecanoe so a pmtiles file with
  unchanged tiles is byte-identical across versions. No contract change; removes the local-path leak. Low risk
  (test: two builds of the same input give the same pmtiles hash); about half a day.
- **A2 (contract change, optional):** keep `dataVersion`/`generatedAt` only in `manifest.json` and `latest.json`;
  the API loader checks the manifest instead of each file's header. Needs a contract version and an API change;
  one to two days.
- Effect: HF growth falls to the real changes. A1 alone: ~2 to 15 MiB of LFS per week (~0.1 to 0.8 GB/year) plus
  ~11 MiB of JSON in git; with A2, JSON growth is limited to files whose content changed. gh-pages history grows by
  the same real changes.
- Cost: free. Recovery: unchanged; nothing is deleted.

### B. Content-addressed objects

- Publish each file once as `data/objects/<sha256>.<ext>`; a version is a `v<N>/manifest.json` mapping logical paths
  to hashes. Unchanged files are never re-uploaded; pruning deletes only objects no kept manifest references.
- Free; medium risk (the web app, API loader, service worker/CSP and HF mirror layout all change; cache headers get
  simpler since objects are immutable); 3 to 5 days. Recovery: while a version's manifest and objects exist; pairs
  with C for old versions.
- Not chosen: with HF's OID de-duplication, A gives most of B's HF saving for a fraction of the work. B mainly adds
  smaller Pages trees and faster uploads.

### C. Retention window plus release-backed recovery

- Every publish also uploads the version to `abrycta/plumes-archive` as release `data-v<N>`: `v<N>.tar.zst` plus its
  sha256 and file list, ~28 MiB (tiles are already compressed; JSON shrinks ~5x). The asset is verified (download,
  hash) before anything is pruned.
- HF keeps the last 4 weekly versions plus the first version of each month for 12 months; older folders are deleted
  and `super_squash_history` runs monthly, after the release check passes. Pages keeps 2, as now.
- Effect: HF bounded at ~16 versions (~0.6 GB counted before A, ~0.15 GB after). Releases grow ~1.4 GB/year
  (~0.3 GB/year if tarballs are built from A's stable files and stored incrementally); GitHub has no total cap.
- Free (private releases are not billed). Squash is irreversible, so a release-step bug could lose a version; guard:
  never squash unless every pruned version has a verified release asset. 1 to 2 days (publish step, prune job, a
  `restore --version N` command, a runbook entry).
- Recovery: `gh release download data-v<N>` → verify sha256 → unpack into `data/v<N>/` (Pages) or upload to
  HF; then flip `latest.json` if it is a rollback.

### D. gh-pages as a single orphan commit

- Each publish force-pushes one orphan commit holding the current 2 versions; no history is kept. The Pages source
  stays at ~40 to 80 MiB (GitHub garbage-collects dropped commits later, so the reported size falls with a delay).
- Free; half a day. It drops the git history that is one of today's two recovery paths, so it **requires C's release
  step first**, and the workflow token must be allowed to force-push `gh-pages` only. Recovery: from the
  `data-v<N>` release assets (C).

## 3. Recommendation

1. **Do A1 now:** a few lines in `readmodels.py`; removes ~78 % of every version's new bytes and the published local
   path; no change for readers.
2. **Add C's release step (`data-v<N>` assets) next**, with no pruning yet. It makes published versions recoverable
   independently of gh-pages history and HF, as `DATA-ARCHIVING.md` requires, and is the precondition for any later
   cleanup.
3. **Decide A2 together with the next file-contract change.**
4. **Turn on C's HF pruning and squash, and D, only when a trigger is hit:** HF `usedStorage` above 2 GB, or the
   `abrycta/plumes` repo above 500 MB. Both numbers are in the weekly health check.
5. **Skip B** unless upload time or Pages tree size becomes a problem; with A in place it saves little more.

With A1 and the release step, expected growth is ~0.1 to 0.8 GB/year on HF and a similar or smaller amount in
gh-pages history, so both stay under their soft limits for well over five years; the step 4 triggers cover the rest.

## 4. How the numbers were measured

- gh-pages: bare clone of `gh-pages`; `git count-objects -vH`; per-commit `git ls-tree -r -l` sums; blob
  comparison per path between consecutive `Data version vN` commits; JSON compared after removing `dataVersion` and
  `generatedAt`; pmtiles compared by header, tile section and decompressed metadata.
- HF: `GET /api/datasets/permission-alluring/plumes` (`usedStorage`), `/commits/main`, and
  `/tree/main?recursive=true` (LFS OIDs and sizes).
- Archive: `gh api repos/abrycta/plumes-archive/releases` (asset counts and sizes); `gh api repos/abrycta/plumes`
  (`size`).
