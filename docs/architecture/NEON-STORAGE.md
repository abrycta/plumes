# Neon storage: how much room the API load has

Measured 2026-10-26 on production project `plumes` (Neon Free, Singapore); `tools/ops-watch.sh quota` in
portfolio-docs checks them daily.

## What counts against the 1 GB

- Neon Free caps each project's **logical size** at 1 GB, enforced by the compute as `neon.max_cluster_size = 1GB`; a
  write past it fails with `DiskFull: ... project size limit (1024 MB) has been exceeded`.
- Logical size sums every database in the branch: `neondb` plus about 23 MB for `postgres`, `template0` and
  `template1`. Tables, TOAST, indexes and dead rows count; free space inside a table counts until truncated.
- History (6-hour restore window on Free, WAL) is billed separately and does not count toward the 1 GB.
- Plumes and Replay use separate Neon projects, so neither can push the other over.

## How a load uses space

`plumes-api load` replaces everything in one transaction; readers see the old version until the commit. `event`
(almost all the data) is built in `event_next`: rows, then primary key and indexes (definitions read from the live
table, so they follow migrations), then `DROP TABLE event` and renames. Small tables use `DELETE` and `INSERT`.
Peak before the commit: **current size + one compact copy of `event`**; the commit frees the old table's files.

Before 2026-10-27 `event` also used `DELETE` and `INSERT`; the churn left its indexes about three times their fresh
size, which a one-off `REINDEX` would not fix for long. Measured in a rolled-back transaction on production data
(data v8, 676,580 rows):

| `event` | live (after DELETE/INSERT churn) | built fresh |
|---|---|---|
| table | 125 MB | 122 MB |
| GiST on `geog` | 153 MB | 49 MB |
| primary key `(kind, ext_id)` | 81 MB | 48 MB |
| `(kind, day)` | 13 MB | 5 MB |
| **total** | **372 MB** | **224 MB** |

| | before | after the first swap |
|---|---|---|
| database (logical) | 413 MB (40 %) | about 265 MB (26 %) |
| load peak | about 788 MB (77 %) | about 489 MB (48 %) |

The first load with the swap peaks at about 413 + 224 = 637 MB (62 %).

## Cleanup, automatic and cheap

A failed load leaves nothing behind: `event_next` and every change roll back, and dropping `event_next` frees its
files at once. Dead rows in the small tables (and, once, the old `event`) are reclaimed by
`VACUUM (ANALYZE) event, episode, volcano, dataset` (no `VACUUM FULL`, no exclusive lock; seconds), run:

- *startup sweep*, before the guard measures: drops a committed leftover `event_next` (a running load's is
  uncommitted and invisible), then VACUUMs;
- *after the commit*, for the version just replaced;
- *after a failure*, on a fresh connection after rollback (best effort; the next run's sweep repeats it). Tested in
  `LoaderCleanupIT`: a load that fails while building `event_next`'s primary key leaves the same tables, no
  `event_next` and the previous version serving; the next load swaps in a compact `event` under the migration's
  index names.

Only the current version is kept. The API never reads older versions; a rollback reloads the previous version
from the data root, which keeps all of them. A second copy in the database would cost about 224 MB and raise the
load peak to about 70 %.

History retention stays at 6 hours (`history_retention_seconds = 21600`, the Free maximum): lowering it frees none
of the 1 GB, and it is the only way to undo a bad write within those hours.

## Size guard

Before writing, the loader projects `database + replaced tables scaled to the new event count + 10 %`. Above
**85 % of the cap** (870 MB) it refuses: it prints an `::error` and exits 3, the workflow's report job opens or
comments on the "API load failed" issue, and the API keeps serving the previous version. `PLUMES_DB_CAP_MB` and
`PLUMES_DB_GUARD_PCT` override the cap and share (tests only).

## Growth

- Events grow by about 30,000–50,000 a year (thermal detections and earthquakes; 2024 had 52,000) at about
  330 bytes each with compact indexes: about 13 MB a year in the database, **about 26 MB a year at the load peak**.
- At that rate the load peak reaches ops-watch's 70 % warning (717 MB) in about 9 years and the 85 % guard
  (870 MB) in about 15. Before the swap it was already past 70 % and would have reached 85 % around late 2028.
- If more room is needed, load only the months that changed; the guard stops a load safely before then.

## Migrations

`api-load.yml` applies pending migrations (`dbmate up`, `api/db/migrations`, direct endpoint, main only) before
each load, so a schema change reaches production with the next load instead of by hand.
