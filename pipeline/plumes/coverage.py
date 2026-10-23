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
# A month whose last day is this far back is no longer re-run, whatever its coverage (a source has ended or stalled).
SETTLE_DAYS = 120
SO2_SOURCE = "s5p-offl-so2"


def month_last_day(month: str) -> str:
    y, m = map(int, month.split("-"))
    return ((dt.date(y, m, 28) + dt.timedelta(days=4)).replace(day=1) - dt.timedelta(days=1)).isoformat()


def _covers(month: str, source: str, days: list[str]) -> bool:
    need = min(month_last_day(month), SOURCE_END.get(source, "9999-12-31"))
    return need < f"{month}-01" or (bool(days) and max(days) >= need)


def settled(month: str, today: dt.date | None = None) -> bool:
    """The month ended more than SETTLE_DAYS ago: a source that still has no images for it has ended or stalled."""
    return month_last_day(month) < ((today or dt.date.today()) - dt.timedelta(days=SETTLE_DAYS)).isoformat()


def fire_month_complete(month: str, cov: dict | None, today: dt.date | None = None) -> bool:
    """True when every fire source has images up to the month's last day (or its own end), or the month has settled:
    a collection that stops (Terra MOD14A1 at end of mission, the FIRMS collection) then counts as ended, its series
    stops at its last covered day (fire_ends), and the month is no longer re-run every week (audit P10)."""
    if cov is None:
        return month <= LEGACY_SETTLED_TO
    return all(_covers(month, s, cov.get(s, [])) for s in FIRE_SOURCES) or settled(month, today)


def so2_month_complete(month: str, cov: dict | None, today: dt.date | None = None) -> bool:
    """An SO2 month is re-run until TROPOMI covers its last day (late OFFL days), or it settles (audit P12). Tables
    written before the sidecar existed are kept as they are."""
    if cov is None:
        return True
    return _covers(month, SO2_SOURCE, cov.get(SO2_SOURCE, [])) or settled(month, today)


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
