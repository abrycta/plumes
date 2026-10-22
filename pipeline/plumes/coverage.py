"""Which days the Earth Engine fire tables (MOD14A1, VNP14A1, FIRMS) actually cover.

The tables are sparse (one row per volcano ring and day with a detection), so a missing day reads as "nothing
detected". That is only true where the collection had an image: a month run before the collection reached its last
day, or after a sensor stopped, would otherwise turn a gap into zeros. Each month table therefore carries a sidecar
`<month>.coverage.json` ({source: [days with an image]}); a month is re-run until every source covers it, and each
series ends on the last day its source covers.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from plumes.thermal_n20 import SNPP_END

FIRE_SOURCES = ("modis-mod14a1", "viirs-vnp14a1", "firms-modis")
# Last day a source can cover (S-NPP deliveries end; VNP14A1 has no images after).
SOURCE_END = {"viirs-vnp14a1": SNPP_END}
# Tables written before the sidecars (Earth Engine run A, 2026-10) are trusted as whole months up to here; later
# legacy months count only up to their last detection and are re-run.
LEGACY_SETTLED_TO = "2026-04"


def month_last_day(month: str) -> str:
    y, m = map(int, month.split("-"))
    return ((dt.date(y, m, 28) + dt.timedelta(days=4)).replace(day=1) - dt.timedelta(days=1)).isoformat()


def _covers(month: str, source: str, days: list[str]) -> bool:
    need = min(month_last_day(month), SOURCE_END.get(source, "9999-12-31"))
    return need < f"{month}-01" or (bool(days) and max(days) >= need)


def fire_month_complete(month: str, cov: dict | None) -> bool:
    """True when every fire source has images up to the month's last day (or its own end)."""
    if cov is None:
        return month <= LEGACY_SETTLED_TO
    return all(_covers(month, s, cov.get(s, [])) for s in FIRE_SOURCES)


def read_coverage(table: Path) -> dict | None:
    side = table.with_suffix(".coverage.json")
    return json.loads(side.read_text()) if side.exists() else None


def fire_ends(tables: Path, rows: list[dict]) -> dict[str, str]:
    """Last covered day per fire source over the month tables in `tables` (ee-fire)."""
    last_row: dict[tuple[str, str], str] = {}
    for r in rows:
        k = (r["source"], r["date"][:7])
        last_row[k] = max(last_row.get(k, ""), r["date"])
    ends: dict[str, str] = {}
    for table in sorted(tables.glob("*.csv")):
        month = table.stem
        cov = read_coverage(table)
        for s in FIRE_SOURCES:
            if cov is not None:
                day = max(cov.get(s, []), default=None)
            elif month <= LEGACY_SETTLED_TO:
                day = month_last_day(month)
            else:
                day = last_row.get((s, month))
            if day:
                day = min(day, SOURCE_END.get(s, day))
                ends[s] = max(ends.get(s, day), day)
    return ends
