"""Plumes series adapters: turn a volcano read model (and the deep-time HazEL impacts) into typed template values for
one step window. Every value carries the source id of the series it came from; PHIVOLCS, VAAC and DROMIC figures
carry their page's URL (Q5 ii). Nothing here reads prose: only numbers, dates and levels already in the read models.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import statistics

from plumes.parse import wp_slug_meta
from plumes.stories.events import Event, add
from plumes.stories.render import V
from plumes.stories.text import lt

BUL = "phivolcs-bulletins"
LAVA = "phivolcs-lava-bulletins"
HAZEL = "noaa-hazel-volcanoes-ph"
TROPOMI_ID, OMI_ID, RAIN_ID = "so2_s5p_15km", "so2_omi_box", "rain_imerg_15km"
THERMAL = [("frp_viirs_15km", "VIIRS", "viirs-vnp14a1"), ("frp_modis_15km", "MODIS", "modis-mod14a1")]
MIN_CLEAR_DAYS = 5


@dataclasses.dataclass
class Candidate:
    template: str
    values: dict[str, V]
    figures: list[dict] = dataclasses.field(default_factory=list)
    series: list[str] = dataclasses.field(default_factory=list)


def _days(a: str, b: str) -> int:
    return (dt.date.fromisoformat(b) - dt.date.fromisoformat(a)).days


def _in(x: str, w: tuple[str, str]) -> bool:
    return w[0] <= x[:10] <= w[1]


def _bul_src(url: str) -> str:
    return LAVA if "wovodat" in url else BUL


def _first_max(rows: list, key) -> list:
    """The earliest row holding the largest value (rows are in date order)."""
    top = max(key(r) for r in rows)
    return next(r for r in rows if key(r) == top)


def _fig(label: dict, value, source: str, as_of: str | None = None, url: str | None = None, unit: str | None = None, note: dict | None = None) -> dict:
    f = {"label": label, "value": value, "source": source}
    for k, v in (("unit", unit), ("asOf", as_of), ("url", url), ("note", note)):
        if v is not None:
            f[k] = v
    return f


# ---------------------------------------------------------------- PHIVOLCS bulletins

def _alert_rows(m: dict) -> list[list]:
    """Bulletin rows with a level, with single-row blips removed (a level that differs from two equal neighbours is a
    parse or page error more often than a one-day change; it would otherwise read as two changes)."""
    rows = [r for r in (m.get("bulletins") or {"rows": []})["rows"] if r[1] is not None]
    return [r for i, r in enumerate(rows) if not (0 < i < len(rows) - 1 and rows[i - 1][1] == rows[i + 1][1] != r[1])]


def alert(m: dict, kind: str, w: tuple[str, str]) -> list[Candidate]:
    rows = _alert_rows(m)
    out = []
    inside = [r for r in rows if _in(r[0], w)]
    changes = [(rows[i - 1], rows[i]) for i in range(1, len(rows)) if rows[i][1] != rows[i - 1][1] and _in(rows[i][0], w)]
    if kind == "before" and inside and not changes and len({r[1] for r in inside}) == 1:
        lvl, d1, d2 = inside[0][1], inside[0][0], inside[-1][0]
        src = _bul_src(inside[-1][8])
        vals = {"level": V(lvl, src), "span": V((d1, d2), src)}
        if len(inside) == _days(d1, d2) + 1:
            out.append(Candidate("ALERT-HELD", vals, series=["bulletins"]))
        else:
            out.append(Candidate("ALERT-HELD-GAPS", vals | {"n": V(len(inside), src)}, series=["bulletins"]))
    for prev, cur in changes:
        src = _bul_src(cur[8])
        fig = _fig(lt("Alert level (as reported)", "警戒レベル（発表値）"), cur[1], src, cur[0], cur[8])
        vals = {"a": V(prev[1], _bul_src(prev[8]), prev[8]), "b": V(cur[1], src, cur[8]), "date": V(cur[0], src, cur[8])}
        if _days(prev[0], cur[0]) > 1:
            out.append(Candidate("ALERT-CHANGED-GAP", vals | {"d0": V(prev[0], _bul_src(prev[8]), prev[8])}, [fig], ["bulletins"]))
        elif cur[1] < prev[1]:
            out.append(Candidate("ALERT-LOWERED", vals, [fig], ["bulletins"]))
        else:
            t = wp_slug_meta(cur[8]) if src == BUL else {}
            if t.get("hour") is not None and t.get("date") == cur[0]:
                out.append(Candidate("ALERT-RAISED", vals | {"time": V((t["hour"], t["minute"]), src, cur[8])}, [fig], ["bulletins"]))
            else:
                out.append(Candidate("ALERT-RAISED-DAY", vals, [fig], ["bulletins"]))
    return out


def bulletin_numbers(m: dict, kind: str, w: tuple[str, str]) -> list[Candidate]:
    rows = [r for r in (m.get("bulletins") or {"rows": []})["rows"] if _in(r[0], w)]
    out = []
    eq = [r for r in rows if r[2] is not None]
    if eq:
        top = _first_max(eq, lambda r: r[2])
        src = _bul_src(top[8])
        out.append(Candidate("BUL-VEQ-MAX", {"n": V(int(top[2]), src, top[8]), "span": V((eq[0][0], eq[-1][0]), src)},
                             [_fig(lt("Volcanic earthquakes in a day (most)", "1日の火山性地震（最多）"), int(top[2]), src, top[0], top[8])], ["bulletins"]))
    so2 = {}
    for r in rows:  # one value per measurement date (a flux is repeated on later bulletins until the next measurement)
        if r[4] is not None and (r[5] or r[0]) and _in(r[5] or r[0], w):
            so2.setdefault(r[5] or r[0], r)
    if so2:
        dates = sorted(so2)
        top = _first_max([so2[k] for k in dates], lambda r: r[4])
        src = _bul_src(top[8])
        out.append(Candidate("BUL-SO2FLUX-MAX", {"x": V(int(top[4]), src, top[8]), "span": V((dates[0], dates[-1]), src)},
                             [_fig(lt("SO₂ emission (most, tonnes a day)", "SO₂放出量（最大、1日あたりトン）"), int(top[4]), src, top[5] or top[0], top[8], "t/d")], ["bulletins"]))
    plume = [r for r in rows if r[6] is not None]
    if plume and kind in ("onset", "course"):
        top = _first_max(plume, lambda r: r[6])
        src = _bul_src(top[8])
        out.append(Candidate("BUL-PLUME-MAX", {"m": V(int(top[6]), src, top[8]), "span": V((plume[0][0], plume[-1][0]), src)},
                             [_fig(lt("Plume above the crater (highest)", "火口上の噴煙（最高）"), int(top[6]), src, top[0], top[8], "m")], ["bulletins"]))
    return out


# ---------------------------------------------------------------- satellite SO₂

def _daily(m: dict, sid: str, w: tuple[str, str]) -> list[tuple[str, float | None, float | None]]:
    s = m.get("daily", {}).get(sid)
    if not s:
        return []
    out = []
    n = _days(w[0], w[1]) + 1
    for k in range(n):
        day = add(w[0], k)
        i = _days(s["start"], day)
        if 0 <= i < len(s["values"]):
            cov = s.get("coverage")
            out.append((day, s["values"][i], cov[i] if cov else None))
    return out


def _median(xs: list[float]) -> float:
    md = statistics.median(xs)
    return round(md) if all(isinstance(x, int) for x in xs) else round(md, 2)


def so2(m: dict, kind: str, w: tuple[str, str]) -> list[Candidate]:
    for sid, src, sensor in ((TROPOMI_ID, "s5p-offl-so2", "TROPOMI"), (OMI_ID, "omi-omso2e", "OMI")):
        days = _daily(m, sid, w)
        clear = [(d, x, c) for d, x, c in days if x is not None]
        if not days:
            continue
        omi = sensor == "OMI"
        if kind == "before":
            if len(clear) < MIN_CLEAR_DAYS:
                continue
            vals = {"med": V(_median([x for _, x, _ in clear]), src), "span": V((days[0][0], days[-1][0]), src), "n": V(len(clear), src), "N": V(len(days), src)}
            if not omi:
                vals |= {"sensor": V(sensor, src), "r": V(int(m["daily"][sid]["ringKm"]), src)}
            return [Candidate("SO2-BASELINE-OMI" if omi else "SO2-BASELINE", vals, series=[sid])]
        if kind in ("onset", "course") and clear:
            d, x, c = _first_max(clear, lambda r: r[1])
            unit = "DU" if omi else "µmol/m²"
            vals = {"x": V(x, src), "date": V(d, src), "cov": V(c, src)}
            if not omi:
                vals |= {"sensor": V(sensor, src), "r": V(int(m["daily"][sid]["ringKm"]), src)}
            label = lt("OMI SO₂ column, 50 km box (highest)", "OMI SO₂カラム量、50 km範囲（最大）") if omi else lt("TROPOMI SO₂ column within 15 km (highest)", "TROPOMI SO₂カラム量、15 km圏（最大）")
            return [Candidate("SO2-PEAK-OMI" if omi else "SO2-PEAK", vals, [_fig(label, x, src, d, unit=unit)], [sid])]
    return []


# ---------------------------------------------------------------- USGS earthquakes

def usgs(m: dict, kind: str, w: tuple[str, str], ev: Event) -> list[Candidate]:
    s = m.get("events", {}).get("eq_usgs_30km")
    if not s or w[0] < s["start"] or w[1] > m["dataAsOf"]:
        return []
    src = "usgs-comcat-ph-2010" if w[0] >= "2010-01-01" else "usgs-comcat-ph-1900-2009"
    rows = s["rows"]
    if kind == "before":
        on = next((r for r in rows if r[0] == ev.start), None)
        prior = [r for r in rows if r[0] < ev.start]
        if on and prior and _days(prior[-1][0], ev.start) >= 30 and on[2] is not None:
            return [Candidate("EQ-QUIET", {"d1": V(prior[-1][0], src), "d2": V(ev.start, src), "n": V(int(on[1]), src), "m": V(on[2], src)}, series=["eq_usgs_30km"])]
    inside = [r for r in rows if _in(r[0], w)]
    if not inside:
        return [Candidate("EQ-NONE", {"span": V(w, src)}, series=["eq_usgs_30km"])]
    n = sum(int(r[1]) for r in inside)
    mags = [r[2] for r in inside if r[2] is not None]
    if not mags:
        return []
    return [Candidate("EQ-COUNT", {"n": V(n, src), "span": V(w, src), "m": V(max(mags), src)},
                      [_fig(lt("USGS earthquakes within 30 km", "USGS 地震（30 km圏）"), n, src, w[1])], ["eq_usgs_30km"])]


# ---------------------------------------------------------------- Tokyo VAAC

def vaac(m: dict, kind: str, w: tuple[str, str]) -> list[Candidate]:
    if kind not in ("onset", "course") or not m.get("advisories"):
        return []
    src = "vaac-tokyo-advisories"
    rows = [r for r in m["advisories"]["rows"] if _in(r[0], w)]
    out = []
    obs = [r for r in rows if r[3] == "observed" and r[2]]
    if obs:
        top = _first_max(obs, lambda r: r[2])
        out.append(Candidate("VAAC-MAX", {"fl": V(int(top[2]), src, top[4]), "date": V(top[0][:10], src, top[4])},
                             [_fig(lt("Ash top (Tokyo VAAC, observed)", "火山灰の高度（東京VAAC観測）"), int(top[2]), src, top[0][:10], top[4], "FL")], ["advisories"]))
    nrs = {r[1] or r[0] for r in rows}
    if nrs:
        out.append(Candidate("VAAC-COUNT", {"n": V(len(nrs), src), "span": V((rows[0][0][:10], rows[-1][0][:10]), src)}, series=["advisories"]))
    return out


# ---------------------------------------------------------------- thermal

def thermal(m: dict, kind: str, w: tuple[str, str]) -> list[Candidate]:
    for sid, sensor, src in THERMAL:
        s = m.get("events", {}).get(sid)
        if not s or w[0] < s["start"]:
            continue
        rows = [r for r in s["rows"] if _in(r[0], w) and r[1] is not None]
        if not rows:
            return []
        top = _first_max(rows, lambda r: r[1])
        return [Candidate("HEAT-DAYS", {"sensor": V(sensor, src), "n": V(len(rows), src), "span": V(w, src), "x": V(top[1], src), "date": V(top[0], src)},
                          [_fig(lt(f"{sensor} fire radiative power within 15 km (highest)", f"{sensor} 放射電力、15 km圏（最大）"), top[1], src, top[0], unit="MW")], [sid])]
    return []


# ---------------------------------------------------------------- GVP, MSVOLSO2L4, DROMIC, HazEL, COMET

def gvp(ev: Event, kind: str, w: tuple[str, str]) -> list[Candidate]:
    if kind != "onset":
        return []
    er = next((e for e in ev.eruptions if _in(e["start"], w)), None)
    if not er:
        return []
    out = []
    if er.get("vei") is not None:
        out.append(Candidate("GVP-VEI", {"vei": V(int(er["vei"]), "gvp-eruptions-ph", er.get("url"))},
                             [_fig(lt("Volcanic Explosivity Index (GVP)", "火山爆発指数（GVP）"), int(er["vei"]), "gvp-eruptions-ph", url=er.get("url"))]))
    if er.get("so2MassKt") is not None:
        out.append(Candidate("SO2-MASS", {"x": V(er["so2MassKt"], "nasa-msvolso2l4"), "date": V(er["start"], "nasa-msvolso2l4")},
                             [_fig(lt("SO₂ mass (MSVOLSO2L4)", "SO₂量（MSVOLSO2L4）"), er["so2MassKt"], "nasa-msvolso2l4", er["start"], unit="kt")]))
    return out


def dromic(m: dict, kind: str, w: tuple[str, str], ev: Event) -> list[Candidate]:
    rows = [r for r in (m.get("displacement") or {"rows": []})["rows"] if r[0] >= ev.start]
    src = "dswd-dromic-reports"
    if kind == "course":
        inside = [r for r in rows if _in(r[0], w) and r[3] is not None]
        if inside:
            top = _first_max(inside, lambda r: r[3])
            return [Candidate("DROMIC-INSIDE-MAX", {"n": V(int(top[3]), src, top[7]), "date": V(top[0], src, top[7]), "k": V(int(top[1]), src, top[7])},
                              [_fig(lt("People inside evacuation centres (most)", "避難所にいた人（最多）"), int(top[3]), src, top[0], top[7])], ["displacement"])]
    if kind == "after":
        done = [r for r in rows if r[0] <= w[1] and r[2] is not None]
        if done:
            last = done[-1]
            return [Candidate("DROMIC-AFFECTED", {"n": V(int(last[2]), src, last[7]), "date": V(last[0], src, last[7])},
                              [_fig(lt("Persons affected", "被災者数"), int(last[2]), src, last[0], last[7])], ["displacement"])]
    return []


def _first(imp: dict, *keys: str):
    return next((imp[k] for k in keys if imp.get(k) is not None), None)


def hazel(deep: dict | None, ev: Event, kind: str) -> list[Candidate]:
    if kind != "after" or not deep:
        return []
    ids = {e["id"] for e in ev.eruptions}
    imps = [i for e in deep.get("eruptions", []) if e["id"] in ids for i in e.get("impacts", [])]
    if not imps:
        return []
    imp = imps[0]
    url = imp.get("url")
    out = []
    for tid, keys, label, unit in (("HAZEL-DEATHS", ("deathsTotal", "deaths"), lt("Deaths (NOAA NCEI estimate)", "死者（NOAA NCEI推計）"), None),
                                   ("HAZEL-HOUSES", ("housesDestroyedTotal", "housesDestroyed"), lt("Houses destroyed (NOAA NCEI estimate)", "全壊家屋（NOAA NCEI推計）"), None),
                                   ("HAZEL-DAMAGE", ("damageMusdTotal", "damageMusd"), lt("Damage (NOAA NCEI estimate)", "被害額（NOAA NCEI推計）"), "US$ million")):
        v = _first(imp, *keys)
        if v is None:
            continue
        name = "x" if tid == "HAZEL-DAMAGE" else "n"
        v = v if tid == "HAZEL-DAMAGE" else int(v)
        out.append(Candidate(tid, {name: V(v, HAZEL, url)}, [_fig(label, v, HAZEL, url=url, unit=unit)]))
    return out


def deformation(m: dict, kind: str, w: tuple[str, str]) -> list[Candidate]:
    if kind not in ("before", "after"):
        return []
    best = None
    for sid, s in m.get("events", {}).items():
        if not sid.startswith("los_comet_"):
            continue
        rows = [r for r in s["rows"] if _in(r[0], w) and r[1] is not None]
        if len(rows) >= 2 and _days(rows[0][0], rows[-1][0]) >= 30 and (best is None or len(rows) > len(best[1])):
            best = (sid, rows)
    if not best:
        return []
    sid, rows = best
    x = round(rows[-1][1] - rows[0][1], 1)
    if x == 0:
        return []
    src = "comet-licsbas"
    return [Candidate("DEFORM-LOS", {"x": V(abs(x), src), "dir": V("toward" if x > 0 else "away", src), "span": V((rows[0][0], rows[-1][0]), src)},
                      [_fig(lt("Line-of-sight change (COMET)", "視線方向の変位（COMET）"), x, src, rows[-1][0], unit="mm")], [sid])]


# ---------------------------------------------------------------- context

def rain(m: dict, kind: str, w: tuple[str, str]) -> list[Candidate]:
    days = _daily(m, RAIN_ID, w)
    if not days or len(days) != _days(w[0], w[1]) + 1 or any(x is None for _, x, _ in days):
        return []
    src = "gpm-imerg-v07"
    total = round(sum(x for _, x, _ in days), 1)
    out = [Candidate("RAIN-TOTAL", {"x": V(total, src), "span": V(w, src)}, [_fig(lt("Rain within 15 km (GPM IMERG)", "15 km圏の雨量（GPM IMERG）"), total, src, w[1], unit="mm")], [RAIN_ID])]
    if kind in ("course", "after"):
        d, x, _ = _first_max(days, lambda r: r[1])
        if x >= 1:
            out.append(Candidate("RAIN-WETTEST", {"date": V(d, src), "x": V(x, src)}, series=[RAIN_ID]))
    return out


def population(m: dict, kind: str, ring_km: int) -> list[Candidate]:
    if kind != "after":
        return []
    r = next((x for x in m["exposure"]["rings"] if x["radiusKm"] == ring_km), None)
    if not r:
        return []
    src = r["source"]
    return [Candidate("POP-RING", {"n": V(int(r["population"]), src), "r": V(int(r["radiusKm"]), src), "year": V(int(r["year"]), src)},
                      [_fig(lt(f"People within {ring_km} km (WorldPop {r['year']})", f"{ring_km} km圏内の人口（WorldPop {r['year']}年）"), int(r["population"]), src)])]


def step_candidates(m: dict, deep: dict | None, ev: Event, kind: str, w: tuple[str, str], ring_km: int) -> list[Candidate]:
    """Every candidate sentence for one step, in reading order (rain last, ST9)."""
    return (alert(m, kind, w) + bulletin_numbers(m, kind, w) + so2(m, kind, w) + usgs(m, kind, w, ev) + vaac(m, kind, w) + thermal(m, kind, w)
            + gvp(ev, kind, w) + dromic(m, kind, w, ev) + hazel(deep, ev, kind) + deformation(m, kind, w) + population(m, kind, ring_km) + rain(m, kind, w))
