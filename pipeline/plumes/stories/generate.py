"""Generate stories from a data version (STORIES-PLAN Part B). A story publishes when the automated checks pass (ST15).

    uv run python -m plumes.stories --version-dir data/build/site/v3            # writes into the version
    uv run python -m plumes.stories --version-dir /tmp/v2 --out /tmp/v2-stories  # or next to it

Reads volcano/*.json and deeptime.json (when present) of the version; writes story/<id>.json for every story that passes
the automated checks (the story bar, no template or schema error), story/drafts/<id>.json for a generated story that a
hand-built one stands in for, and stories.json (the index). There is no manual review gate (DECISIONS ST15).

Stability across data updates (ST15): a story public in the previous version keeps its id (it claims the event that holds
its onset at the same volcano, never by the derived id), and it may leave only with a data-driven reason, logged as a
check; otherwise the build fails.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

import yaml

from plumes.contracts import errors as schema_errors
from plumes.paths import REGISTRY
from plumes.stories import facts
from plumes.stories import render as rd
from plumes.stories import text as tx
from plumes.stories.events import KINDS, ONSET_DAYS, Event, add, d, merge, windows
from plumes.stories.render import V

HERE = pathlib.Path(__file__).parent
OVERRIDES = HERE / "overrides.yaml"
GENERATOR = {"name": "plumes.stories", "version": "1"}
COUNTED = {"alert", "bulletin", "vaac", "so2", "thermal", "usgs", "dromic", "vei", "so2mass", "hazel", "deformation", "weekly"}
STORY_FAMILIES, READING_FAMILIES = 4, 2
CREDITS = {"s2-sr-harmonized": "Contains modified Copernicus Sentinel data {year}", "landsat-c2-l2": "Landsat imagery courtesy of the U.S. Geological Survey"}


def _yaml(p: pathlib.Path) -> Any:
    return yaml.safe_load(p.read_text()) if p.exists() else None


def _provenance(ids: list[str]) -> dict:
    reg = {e["id"]: e for e in yaml.safe_load(REGISTRY.read_text())["sources"]}
    return {"sources": [{"id": i, "attribution": " ".join(reg[i]["attribution"].split()), "licence": " ".join(reg[i]["licence"].split()), "fromArchive": False}
                        for i in dict.fromkeys(ids) if i in reg]}


def _why(m: dict, kind: str, w: tuple[str, str], cat: dict) -> list[dict]:
    """Fixed reasons for a step with no fact sentence (§B4), one per missing record that has a known start."""
    out = []
    name = V(m["volcano"]["name"], "plumes-crosswalk")
    b = (m.get("bulletins") or {}).get("rows") or []
    if b and b[0][0] > w[1]:
        out.append(("WHY-NO-BULLETINS", {"volcano": name, "date": V(b[0][0], facts.BUL)}))
    if kind in ("onset", "course") and w[1] < "2010-01-01":
        out.append(("WHY-NO-VAAC", {"volcano": name, "year": V(2010, "vaac-tokyo-advisories")}))
    for sid, sensor, src in facts.THERMAL[::-1]:
        s = m.get("events", {}).get(sid)
        if s and s["start"] > w[1]:
            out.append(("WHY-BEFORE-INSTRUMENT", {"sensor": V(sensor, src), "date": V(s["start"], src)}))
            break
    if kind == "after" and not m.get("displacement"):
        out.append(("WHY-NO-DROMIC", {}))
    return [{"why": t, "text": rd.render(cat[t], v)} for t, v in out]


def _assets(spec: dict | None) -> list[dict]:
    if not spec:
        return []
    return [{"kind": "image", "url": spec["url"], "date": spec["date"], "sensor": spec["sensor"], "source": spec["source"], "role": spec["role"],
             "caption": spec["caption"], "credit": CREDITS[spec["source"]].format(year=spec["date"][:4])}]


def build_story(m: dict, deep_v: dict | None, ev: Event, wins: dict, cat: dict, ov: dict) -> tuple[dict, dict, list[str]]:
    """(story, score, errors) for one event."""
    errs: list[str] = []
    ctx_unrest = {"unrest": ev.unrest}
    vol = m["volcano"]
    images = {}
    for role, spec in (ov.get("images") or {}).items():
        cap = rd.render(cat["IMAGE-CAPTION"], {"sensor": V(spec["sensor"], spec["source"]), "date": V(spec["date"], spec["source"])})
        images[role] = {**spec, "role": role, "caption": cap}
    if len(images) == 1:  # pairs only (§B5)
        images = {}
    steps, families, used = [], set(), []
    for kind in KINDS:
        if kind not in wins:
            continue
        w = wins[kind]
        sentences, figures, series, prev = [], [], [], None
        for c in facts.step_candidates(m, deep_v, ev, kind, w):
            t = cat[c.template]
            if kind not in t.steps:
                continue
            txt = rd.render(t, c.values, {"prev_family": prev, **ctx_unrest})
            if txt is None:
                continue
            errs += rd.check_sentence(t, txt)
            idx = list(range(len(figures), len(figures) + len(c.figures)))
            figures += c.figures
            series += [s for s in c.series if s not in series]
            srcs = sorted({v.source for v in c.values.values()})
            used += srcs
            sentences.append({"template": t.id, "text": txt, "figures": idx, "sources": srcs})
            prev = t.family
        fact = [s for s in sentences if cat[s["template"]].family in COUNTED]
        families |= {cat[s["template"]].family for s in fact}
        absent = [] if fact else _why(m, kind, w, cat)
        if kind == "course" and not sentences and not absent:
            continue
        parts = [s["text"] for s in sentences] + [a["text"] for a in absent]
        title = (rd.render(cat["STEP-BEFORE"], {}, ctx_unrest) if kind == "before" else rd.render(cat["STEP-AFTER"], {}, ctx_unrest) if kind == "after"
                 else rd.render(cat["STEP-DATES"], {"dates": V(w, "plumes-stories")}))
        step = {"id": kind, "kind": kind, "start": w[0], "end": w[1], "title": title,
                "text": {"en": " ".join(p["en"] for p in parts), "ja": "".join(p["ja"] for p in parts)},
                "status": "draft", "series": series, "figures": figures, "sentences": sentences, "absent": absent,
                "map": {"center": [vol["lon"], vol["lat"]], "zoom": 10}}
        assets = _assets(images.get(kind))
        if assets:
            step["assets"] = assets
            used += [a["source"] for a in assets]
        if not parts:
            errs.append(f"{kind}: a step with neither a sentence nor a why line")
        for f in figures:
            if isinstance(f["value"], int | float) and tx.num(abs(f["value"])) not in step["text"]["en"]:
                errs.append(f"{kind}: figure {f['label']['en']} = {f['value']} not in the step text")
        steps.append(step)
    with_facts = {s["kind"] for s in steps if any(cat[x["template"]].family in COUNTED for x in s["sentences"])}
    tier = ("story" if len(families) >= STORY_FAMILIES and {"before", "onset", "after"} <= with_facts
            else "reading" if len(families) >= READING_FAMILIES else "none")
    score = {"families": len(families), "steps": len(with_facts), "tier": tier}
    first = ev.eruptions[0]["start"] if ev.eruptions else ev.start
    name = V(vol["name"], "plumes-crosswalk")
    summary = rd.render(cat["SUMMARY-UNREST" if ev.unrest else "SUMMARY-ERUPTION"], {"date": V(first, "plumes-stories")})
    errs += [f"summary: {e}" for e in rd.check_sentence(cat["SUMMARY-ERUPTION"], summary)]
    story = {"kind": "story", "id": ev.id, "volcanoId": vol["id"], "volcanoFile": f"volcano/{vol['id']}.json",
             "title": rd.render(cat["TITLE"], {"name": name, "month": V(ev.start, "plumes-stories")}), "summary": summary,
             "span": {"start": steps[0]["start"], "end": steps[-1]["end"]} if steps else {"start": ev.start, "end": ev.end},
             "status": "draft",
             "generator": GENERATOR, "episodeIds": [e["id"] for e in ev.episodes], "score": score, "steps": steps,
             "provenance": _provenance(used)}
    return story, score, errs


def _vei(ev: Event) -> int:
    return max((e["vei"] for e in ev.eruptions if e.get("vei") is not None), default=-1)


def claim(vid: str, evs: list[Event], previous: dict[str, dict]) -> None:
    """Each story public in the previous version takes the event at its volcano that holds its onset, and keeps its id.
    No other event takes a previously public id (a derived id moves when events merge, split or share a year)."""
    taken: set[int] = set()
    for sid, p in sorted(previous.items(), key=lambda x: x[1]["onset"]):
        if p["volcanoId"] != vid:
            continue
        a = p["onset"]
        cands = [i for i, ev in enumerate(evs) if i not in taken and ev.start <= add(a, ONSET_DAYS - 1) and ev.end >= a]
        if cands:
            i = min(cands, key=lambda i: abs((d(evs[i].start) - d(a)).days))
            taken.add(i)
            evs[i].id = sid
    for i, ev in enumerate(evs):
        if i not in taken and ev.id in previous:
            ev.id = f"{vid}-{ev.start}"


def generate(v_dir: pathlib.Path, out_dir: pathlib.Path | None = None, cat_path: pathlib.Path = rd.CATALOGUE,
             overrides_path: pathlib.Path = OVERRIDES, previous: dict[str, dict] | None = None) -> dict:
    """previous: {id: {"volcanoId", "onset"}} of the stories public in the previous version (plumes.stories.previous)."""
    out_dir = out_dir or v_dir
    previous = previous or {}
    cat_version, cat = rd.load(cat_path)
    ov = _yaml(overrides_path) or {}
    deep_p = v_dir / "deeptime.json"
    deep = {x["id"]: x for x in json.loads(deep_p.read_text())["volcanoes"]} if deep_p.exists() else {}
    models = {p.stem: json.loads(p.read_text()) for p in sorted((v_dir / "volcano").glob("*.json"))}
    hdr = None
    built, excluded, checks, gone = [], [], [], {}
    for vid, m in models.items():
        hdr = hdr or {k: m[k] for k in ("schemaVersion", "dataVersion", "dataAsOf", "generatedAt")}
        evs = merge(vid, m["episodes"], m["dataAsOf"])
        claim(vid, evs, previous)
        for i, ev in enumerate(evs):
            if ev.open:
                excluded.append({"id": ev.id, "reason": "open: the after step reaches past the data"})
                continue
            eo = (ov.get("events") or {}).get(ev.id, {})
            wins = windows(ev, evs[i - 1].end if i else None, evs[i + 1].start if i + 1 < len(evs) else None, eo)
            story, score, errs = build_story(m, deep.get(vid), ev, wins, cat, eo)
            story = {**hdr, **story, "generator": {**GENERATOR, "catalogueVersion": cat_version}}
            errs += schema_errors(story)
            if score["tier"] == "story" and not errs:  # published when the automated checks pass (no manual review, ST15)
                story["status"] = "reviewed"
                story["steps"] = [{**s, "status": "reviewed"} for s in story["steps"]]
                errs += schema_errors(story)
            elif score["tier"] != "story":
                gone[ev.id] = (f"below the story bar: {score['families']} fact families (4 needed), facts in {score['steps']} steps"
                               " (before, onset and after needed)")
            checks.append({"check": f"story {ev.id}", "passed": not errs, "detail": "; ".join(errs[:3])})
            if score["tier"] == "none":
                excluded.append({"id": ev.id, "reason": f"below the reading bar ({score['families']} fact families)"})
                continue
            built.append((ev, story, errs))
    pinned = ov.get("first") or []
    built.sort(key=lambda x: (x[1]["id"] not in pinned, pinned.index(x[1]["id"]) if x[1]["id"] in pinned else 0,
                              -x[1]["score"]["families"], -_vei(x[0]), [-ord(c) for c in x[0].start]))
    # Hand-built stories already in the version (Taal 2020, reviewed by Kurt) stay listed, and stay the public file.
    hand = {}
    for p in sorted((v_dir / "story").glob("*.json")):
        doc = json.loads(p.read_text())
        if doc.get("generator"):
            continue
        status = "reviewed" if all(s.get("status") == "reviewed" for s in doc["steps"]) else "draft"
        hand[doc["id"]] = {"id": doc["id"], "volcanoId": doc["volcanoId"], "title": doc["title"], "span": doc["span"], "status": status,
                           "file": f"story/{p.name}"}
    index = []
    for rank, (_ev, story, errs) in enumerate(built, 1):
        h = hand.get(story["id"])
        if h and h["status"] == "reviewed":
            # A reviewed hand-built story stands in for the generated story of the same event, at its rank (listed once).
            p = out_dir / f"story/drafts/{story['id']}.json"
            if story["score"]["tier"] == "story" and not errs:
                draft = {**story, "status": "draft", "steps": [{**s, "status": "draft"} for s in story["steps"]]}
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(json.dumps(draft, separators=(",", ":"), ensure_ascii=False))
            index.append(hand.pop(story["id"]) | {"rank": rank})
            continue
        entry = {k: story[k] for k in ("id", "volcanoId", "title", "span", "episodeIds", "score", "status")} | {"rank": rank}
        if story["score"]["tier"] == "story" and not errs:
            rel = f"story/{story['id']}.json" if story["status"] == "reviewed" else f"story/drafts/{story['id']}.json"
            p = out_dir / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(story, separators=(",", ":"), ensure_ascii=False))
            entry["file"] = rel
            entry["sentences"] = sum(len(s["sentences"]) for s in story["steps"])
        index.append(entry)
    index = [h for h in hand.values() if h["id"] not in {e["id"] for e in index}][::-1] + index
    # A previously public story may leave only with a data-driven reason, logged here; otherwise the build fails.
    public = {e["id"] for e in index if e["status"] == "reviewed" and e.get("file") == f"story/{e['id']}.json"}
    reasons = {e["id"]: e["reason"] for e in excluded} | gone
    left, failed = [], []
    for sid, p in sorted(previous.items()):
        if sid in public:
            continue
        why = (reasons.get(sid) if sid in reasons else f"volcano/{p['volcanoId']}.json is not in this version" if p["volcanoId"] not in models
               else None if any(e["id"] == sid for e in index) else f"no event at {p['volcanoId']} holds its onset ({p['onset']}) in this data")
        (left if why else failed).append(f"{sid}: {why or 'failed the checks: ' + next((c['detail'] for c in checks if c['check'] == f'story {sid}'), '')}")
    checks.append({"check": "previously public stories stay public, or leave with a data-driven reason", "passed": not failed,
                   "detail": "; ".join(failed + left) or f"{len(previous)} kept"})
    doc = {**(hdr or {}), "kind": "stories", "stories": index, "excluded": excluded}
    e = schema_errors(doc)
    checks.append({"check": "stories.json schema", "passed": not e, "detail": "; ".join(e[:3])})
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "stories.json").write_text(json.dumps(doc, separators=(",", ":"), ensure_ascii=False))
    return {"stories": index, "excluded": excluded, "checks": checks, "left": left}
