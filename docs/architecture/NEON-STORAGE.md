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

`plumes-api load` replaces everything in one transaction with `DELETE` and `INSERT`, so readers see the old version
until the commit. The deleted rows stay on disk until the commit and a `VACUUM`, so during a load the database holds
**the current size + a second copy of the replaced tables**. After the commit, the loader runs
`VACUUM (ANALYZE)`, which makes the old rows' space reusable by the next load instead of growing the files.

| 2026-10-26 (data v8) | |
|---|---|
| database (logical) | 413 MB |
| `event` | 371 MB for 676,580 rows (125 MB table, 152 MB GiST on `geog`, 81 MB primary key, 12 MB `day`) |
| load peak | about 413 + 371 = **about 784 MB (77 %)** |

## Cleanup, automatic and cheap

A Plumes load creates no tables, so nothing can be orphaned as a table. What a load can leave behind is dead
rows: the previous version's after a commit, or a failed load's own inserted rows after a rollback. Each is
reclaimed by `VACUUM (ANALYZE) event, episode, volcano, dataset`, on those four tables only (no `VACUUM FULL`, no
exclusive lock; seconds on all-visible pages):

- *startup sweep*, before the guard measures, so rows left dead by any earlier run are reusable first;
- *after the commit*, for the version just replaced;
- *after a failure*, on a fresh connection once the failed transaction has rolled back (best effort; the next
  run's sweep repeats it). Tested in `LoaderCleanupIT`: a load that dies in its last insert batch leaves the same
  tables and the previous version serving, and the next load reuses the reclaimed space instead of growing.

**Versions kept: only the current one.** The API never reads an older version; a rollback reloads the previous
data version from the data root, which keeps every version. A second copy in the database would cost about
370 MB and put the load peak over the cap.

**History retention** stays at 6 hours (`history_retention_seconds = 21600`, the Free maximum). Lowering it is free
but frees nothing of the 1 GB (history is not part of the logical size), and it is the only way to undo a bad write
within those hours.

## Size guard

Before it deletes anything, the loader projects `database + replaced tables scaled to the new event count + 10 %`.
Above **85 % of the cap** (870 MB) it refuses: it prints an `::error`, exits 3, the workflow's report job opens or
comments on the "API load failed" issue, and the API keeps serving the previous version. `PLUMES_DB_CAP_MB` and
`PLUMES_DB_GUARD_PCT` override the cap and the share (tests only).

## Growth

- Events grow by about 30,000 to 50,000 a year (thermal detections and earthquakes; 2024 had 52,000), about
  575 bytes each with indexes: about 23 MB a year in the database and **about 46 MB a year at the load peak**.
- At that rate the load peak passes ops-watch's 70 % warning now, reaches the 85 % guard (870 MB) in about 2 years
  (around late 2028) and the cap in about 5 (around 2031).
- Before then, the load needs to shrink. Options, cheapest first: rebuild the `event` indexes compactly (the GiST
  index is larger than the table), load only the months that changed instead of every event, or stage per table.
  This is listed as a follow-up; the guard stops a load safely if it is reached first.
