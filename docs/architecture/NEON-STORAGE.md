# Neon storage: how much room the API load has

Measured 2026-10-26 on the production project `plumes` (Neon Free, Singapore). `tools/ops-watch.sh quota` in
portfolio-docs watches these numbers every day.

## What counts against the 1 GB

- Neon Free caps each project's **logical size** at 1 GB, enforced by the compute as `neon.max_cluster_size = 1GB`. A
  write past it fails with `DiskFull: ... project size limit (1024 MB) has been exceeded`.
- Logical size is the sum of every database in the branch: `neondb` plus about 23 MB for `postgres`, `template0` and
  `template1`. Tables, TOAST, indexes and dead rows count; free space inside a table counts until it is truncated.
- History (the 6-hour restore window on Free, WAL) is billed separately and is not part of this check.
- Plumes has its own Neon project. Replay's is a different one, so neither can push the other over.

## How a load uses space

`plumes-api load` replaces everything in one transaction, so readers see the old version until the commit.
`event` (almost all of the data) is built fresh in `event_next`: rows first, then the primary key and indexes
(definitions read from the live table, so they follow the migrations), then `DROP TABLE event` and renames. The
small tables keep `DELETE` and `INSERT`. Until the commit the database holds **the current size + one compact copy
of `event`**; at the commit the old table's files are freed.

Before 2026-10-27 `event` was replaced with `DELETE` and `INSERT` too. That churn left its indexes about three times
their fresh size, which a one-off `REINDEX` would not have fixed for long. Measured in a rolled-back transaction on
production data (data v8, 676,580 rows):

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

A failed load leaves nothing behind: `event_next` and every change roll back with the transaction, and dropping
`event_next` frees its files at once. What remains is dead rows in the small tables (and, once, in the old
`event`), reclaimed by `VACUUM (ANALYZE) event, episode, volcano, dataset` on those four tables only (no
`VACUUM FULL`, no exclusive lock; seconds):

- *startup sweep*, before the guard measures: drops a committed leftover `event_next` (a running load's is
  uncommitted and invisible), then VACUUMs;
- *after the commit*, for the version just replaced;
- *after a failure*, on a fresh connection once the failed transaction has rolled back (best effort; the next
  run's sweep repeats it). Tested in `LoaderCleanupIT`: a load that dies while building `event_next`'s primary key
  leaves the same tables, no `event_next` and the previous version serving; the next load swaps in a compact
  `event` under the migration's index names.

**Versions kept: only the current one.** The API never reads an older version; a rollback reloads the previous
data version from the data root, which keeps every version. A second copy in the database would cost about
224 MB and raise the load peak to about 70 %.

**History retention** stays at 6 hours (`history_retention_seconds = 21600`, the Free maximum). Lowering it is free
but frees nothing of the 1 GB (history is not part of the logical size), and it is the only way to undo a bad write
within those hours.

## Size guard

Before it writes anything, the loader projects `database + replaced tables scaled to the new event count + 10 %`.
Above **85 % of the cap** (870 MB) it refuses: it prints an `::error`, exits 3, the workflow's report job opens or
comments on the "API load failed" issue, and the API keeps serving the previous version. `PLUMES_DB_CAP_MB` and
`PLUMES_DB_GUARD_PCT` override the cap and the share (tests only).

## Growth

- Events grow by about 30,000 to 50,000 a year (thermal detections and earthquakes; 2024 had 52,000), about
  330 bytes each with compact indexes: about 13 MB a year in the database and **about 26 MB a year at the load
  peak**.
- At that rate the load peak reaches ops-watch's 70 % warning (717 MB) in about 9 years and the 85 % guard
  (870 MB) in about 15. Before the swap it was already past 70 % and would have reached 85 % around late 2028.
- If that ever needs more room: load only the months that changed. The guard stops a load safely before then.

## Migrations

`api-load.yml` applies pending migrations (`dbmate up`, `api/db/migrations`, direct endpoint, main only) before
each load, so a schema change reaches production with the next load instead of by hand.
