"""Wording helpers shared by every story sentence (STORIES-PLAN §B3 "Wording rules", §B8 step 1).

No Plumes imports: these format typed values only.
"""

from __future__ import annotations

import datetime as dt
import re

MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def lt(en: str, ja: str) -> dict:
    return {"en": en, "ja": ja}


def _d(iso: str) -> dt.date:
    return dt.date.fromisoformat(iso[:10])


def date_en(iso: str) -> str:
    """'2020-09-07' -> '7 September 2020' (the story's date style)."""
    d = _d(iso)
    return f"{d.day} {MONTHS_EN[d.month - 1]} {d.year}"


def date_ja(iso: str) -> str:
    """'2020-09-07' -> '2020年9月7日'."""
    d = _d(iso)
    return f"{d.year}年{d.month}月{d.day}日"


def month_en(iso: str) -> str:
    d = _d(iso[:7] + "-01")
    return f"{MONTHS_EN[d.month - 1]} {d.year}"


def month_ja(iso: str) -> str:
    d = _d(iso[:7] + "-01")
    return f"{d.year}年{d.month}月"


def span_en(a: str, b: str) -> str:
    """'1 to 11 January 2020', '3 June to 9 September 2024', '1 December 2019 to 11 January 2020'."""
    x, y = _d(a), _d(b)
    if x == y:
        return date_en(a)
    if (x.year, x.month) == (y.year, y.month):
        return f"{x.day} to {date_en(b)}"
    if x.year == y.year:
        return f"{x.day} {MONTHS_EN[x.month - 1]} to {date_en(b)}"
    return f"{date_en(a)} to {date_en(b)}"


def span_ja(a: str, b: str) -> str:
    """'2020年1月1日から11日まで', '2024年6月3日から9月9日まで', '2019年12月1日から2020年1月11日まで'."""
    x, y = _d(a), _d(b)
    if x == y:
        return date_ja(a)
    if (x.year, x.month) == (y.year, y.month):
        return f"{date_ja(a)}から{y.day}日まで"
    if x.year == y.year:
        return f"{date_ja(a)}から{y.month}月{y.day}日まで"
    return f"{date_ja(a)}から{date_ja(b)}まで"


def dash_en(a: str, b: str) -> str:
    """A step title or week: '12–13 January 2020', '28 May – 3 June 2024', '30 December 2019 – 5 January 2020'."""
    x, y = _d(a), _d(b)
    if x == y:
        return date_en(a)
    if (x.year, x.month) == (y.year, y.month):
        return f"{x.day}–{date_en(b)}"
    if x.year == y.year:
        return f"{x.day} {MONTHS_EN[x.month - 1]} – {date_en(b)}"
    return f"{date_en(a)} – {date_en(b)}"


def dash_ja(a: str, b: str) -> str:
    """'2020年1月12〜13日', '2024年5月28日〜6月3日', '2019年12月30日〜2020年1月5日'."""
    x, y = _d(a), _d(b)
    if x == y:
        return date_ja(a)
    if (x.year, x.month) == (y.year, y.month):
        return f"{x.year}年{x.month}月{x.day}〜{y.day}日"
    if x.year == y.year:
        return f"{date_ja(a)}〜{y.month}月{y.day}日"
    return f"{date_ja(a)}〜{date_ja(b)}"


def time_en(h: int, m: int) -> str:
    return f"{h % 12 or 12}:{m:02d} {'AM' if h < 12 else 'PM'}"


def time_ja(h: int, m: int) -> str:
    return f"{'午前' if h < 12 else '午後'}{h % 12 or 12}時{m:02d}分"


def fl_gloss(fl: int) -> dict:
    """A flight level with its height in km: EN "FL550 (about 16.8 km)", JA "FL550（約16.8 km）" (full-width brackets)."""
    km = fl * 30.48 / 1000
    return lt(f"FL{fl} (about {km:.1f} km)", f"FL{fl}（約{km:.1f} km）")


def neg(x) -> str:
    """A number with a typographic minus."""
    return str(x).replace("-", "−")


def num(x: float | int) -> str:
    """A number as the source gives it: thousands separators, no trailing '.0', a typographic minus."""
    if isinstance(x, float) and x.is_integer():
        x = int(x)
    return neg(f"{x:,}")


def share_txt(c: float) -> str:
    """A coverage share that never rounds a non-zero share to 0%."""
    return f"{c:.0%}" if c >= 0.01 or c == 0 else f"{c:.1%}"


# English words, ISO dates and half-width brackets that should not be left in Japanese text.
_JA_LEFTOVERS = re.compile(r"\b(?:about|the|and|by|on|from|to|in|of|n/a)\b|\d{4}-\d{2}-\d{2}|[()]")


def ja_leftovers(text: str) -> list[str]:
    return _JA_LEFTOVERS.findall(text)
