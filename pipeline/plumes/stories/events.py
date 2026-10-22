"""Events and their step windows (STORIES-PLAN §B1, §B2).

Overlapping GVP eruptions and PHIVOLCS alert windows at one volcano merge into one event (ST6). Its dates are the
union of the episodes' spans; its title uses the earliest start. Steps are fixed windows: before (start − 90 d →
start − 1 d), onset (start → start + 6 d), course (start + 7 d → end, dropped if empty) and after (90 days from the
day after the end, or after the onset for a short event). Windows never reach into a neighbouring event at the same volcano.
"""

from __future__ import annotations

import dataclasses
import datetime as dt

SINCE = "2000-01-01"
MERGE_GAP_DAYS = 7  # the same gap the alert windows are merged across (readmodels.episodes_for)
OPEN_GVP_DAYS = 30  # an open-ended GVP episode is taken to end 30 days after its start (§A2)
BEFORE_DAYS, ONSET_DAYS, AFTER_DAYS = 90, 7, 90
KINDS = ("before", "onset", "course", "after")


def d(iso: str) -> dt.date:
    return dt.date.fromisoformat(iso)


def add(iso: str, days: int) -> str:
    return (d(iso) + dt.timedelta(days=days)).isoformat()


def full(x: str | None) -> bool:
    return bool(x) and len(x) == 10 and not x.startswith("-")


@dataclasses.dataclass
class Event:
    volcano: str
    start: str
    end: str
    episodes: list[dict]
    id: str = ""
    open: bool = False  # the after window reaches past the data: not a past record yet

    @property
    def eruptions(self) -> list[dict]:
        return [e for e in self.episodes if e["kind"] == "gvp_eruption"]

    @property
    def unrest(self) -> bool:
        """Raised alert levels with no GVP eruption in the event."""
        return not self.eruptions


def episode_span(e: dict) -> tuple[str, str] | None:
    if not full(e.get("start")) or e["start"] < SINCE:
        return None
    end = e.get("end")
    if not full(end):
        end = add(e["start"], OPEN_GVP_DAYS)
    return e["start"], max(end, e["start"])


def merge(vid: str, episodes: list[dict], as_of: str) -> list[Event]:
    spans = sorted(((s, en, e) for e in episodes if (sp := episode_span(e)) for s, en in [sp]), key=lambda x: (x[0], x[1]))
    events: list[Event] = []
    for s, en, e in spans:
        cur = events[-1] if events else None
        if cur and (d(s) - d(cur.end)).days <= MERGE_GAP_DAYS:
            cur.end = max(cur.end, en)
            cur.episodes.append(e)
        else:
            events.append(Event(vid, s, en, [e]))
    years: dict[str, int] = {}
    for ev in events:
        years[ev.start[:4]] = years.get(ev.start[:4], 0) + 1
    for ev in events:
        ev.id = f"{vid}-{ev.start[:4]}" if years[ev.start[:4]] == 1 else f"{vid}-{ev.start[:7]}"
        ev.open = add(ev.end, AFTER_DAYS) > as_of
    return events


def windows(ev: Event, prev_end: str | None, next_start: str | None, override: dict | None = None) -> dict[str, tuple[str, str]]:
    """{kind: (start, end)} for the event's steps; course is left out when the event is shorter than the onset."""
    o = override or {}
    before_start = o.get("before_start") or add(ev.start, -BEFORE_DAYS)
    if prev_end and before_start <= prev_end:
        before_start = add(prev_end, 1)
    after_end = o.get("after_end") or add(max(ev.end, add(ev.start, ONSET_DAYS - 1)), AFTER_DAYS)
    if next_start and after_end >= next_start and not o.get("after_end"):
        after_end = add(next_start, -1)
    onset_end = add(ev.start, ONSET_DAYS - 1)
    out = {"before": (before_start, add(ev.start, -1)), "onset": (ev.start, onset_end)}
    if add(ev.start, ONSET_DAYS) <= ev.end:
        out["course"] = (add(ev.start, ONSET_DAYS), ev.end)
    out["after"] = (add(max(ev.end, onset_end), 1), after_end)
    return {k: v for k, v in out.items() if v[0] <= v[1]}
