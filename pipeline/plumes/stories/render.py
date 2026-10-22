"""The template engine: catalogue loader, typed placeholders and the text checks (STORIES-PLAN §B3, §B4, §B6.4).

No Plumes imports. A sentence is rendered only when every placeholder has a value with a source id; there is no
placeholder type that takes text from a source, so source prose cannot reach a sentence.
"""

from __future__ import annotations

import dataclasses
import pathlib
import re
from collections.abc import Mapping
from typing import Any

import yaml

from plumes.stories import text as tx

CATALOGUE = pathlib.Path(__file__).with_name("templates.yaml")
LANGS = ("en", "ja")
_PH = re.compile(r"\{(\w+)\}")

# Closed lists: values of these types are chosen by the generator, never read from a source's text.
SENSORS = {"TROPOMI", "MODIS", "VIIRS", "Sentinel-2", "Landsat 5", "Landsat 7", "Landsat 8", "Landsat 9"}
DIRS = {"toward": tx.lt("toward", "近づく"), "away": tx.lt("away from", "遠ざかる")}
AGENCIES = {"PHIVOLCS": tx.lt("PHIVOLCS", "PHIVOLCS"), "DSWD": tx.lt("DSWD", "DSWD"), "NDRRMC": tx.lt("NDRRMC", "NDRRMC")}

SAFETY_EN = re.compile(r"\b(?:should|must|avoid|stay away|safe|unsafe|danger|dangerous|warning|risk|hazard|expect|likely|forecast|predict|will erupt)\b", re.I)
SAFETY_JA = re.compile(r"危険|安全|注意して|避難してください|警告|予測|予想|恐れ|可能性|見込み")
DISCLAIMER = ("not a hazard assessment", "ハザード評価ではない")
CAUSAL_EN = re.compile(r"\b(?:because|caused|triggered|led to|due to|after which)\b", re.I)
CAUSAL_JA = re.compile(r"ため|により|原因|引き起こ|誘発")


class TemplateError(ValueError):
    pass


@dataclasses.dataclass(frozen=True)
class V:
    """A typed placeholder value with its source. `value` is a date string, a number, a (start, end) pair, an
    (hour, minute) pair, a closed-list key, or a {en, ja} name from Plumes' own crosswalk."""

    value: Any
    source: str
    url: str | None = None


@dataclasses.dataclass
class Template:
    id: str
    family: str
    steps: list[str]
    source: list[str]
    types: dict[str, str]
    text: dict[str, str]
    variants: list[dict]
    constants: list[str]
    rain: bool = False


def _fmt(kind: str, v: Any, lang: str) -> str:
    if kind == "date":
        return tx.date_en(v) if lang == "en" else tx.date_ja(v)
    if kind == "span":
        return tx.span_en(*v) if lang == "en" else tx.span_ja(*v)
    if kind == "dash":
        return tx.dash_en(*v) if lang == "en" else tx.dash_ja(*v)
    if kind == "month":
        return tx.month_en(v) if lang == "en" else tx.month_ja(v)
    if kind in ("int", "level", "km"):
        if not isinstance(v, int) or isinstance(v, bool):
            raise TemplateError(f"{kind} needs an int, got {v!r}")
        return tx.num(v)
    if kind == "year":
        return str(int(v))
    if kind == "num":
        if not isinstance(v, int | float) or isinstance(v, bool):
            raise TemplateError(f"num needs a number, got {v!r}")
        return tx.num(v)
    if kind == "fl":
        return tx.fl_gloss(int(v))[lang]
    if kind == "share":
        return tx.share_txt(float(v))
    if kind == "time":
        return tx.time_en(*v) if lang == "en" else tx.time_ja(*v)
    if kind == "sensor":
        if v not in SENSORS:
            raise TemplateError(f"unknown sensor {v!r}")
        return v
    if kind == "dir":
        return DIRS[v][lang]
    if kind == "agency":
        return AGENCIES[v][lang]
    if kind == "name":
        return v[lang]
    raise TemplateError(f"unknown placeholder type {kind!r}")


def _check_static(t: Template) -> None:
    for form in [t.text, *t.variants]:
        en, ja = form["en"], form["ja"]
        pe, pj = set(_PH.findall(en)), set(_PH.findall(ja))
        if pe != pj:
            raise TemplateError(f"{t.id}: EN and JA use different placeholders: {sorted(pe ^ pj)}")
        if not pe <= set(t.types):
            raise TemplateError(f"{t.id}: untyped placeholders {sorted(pe - set(t.types))}")
        for lang, s in (("en", en), ("ja", ja)):
            bare = _PH.sub("", s)
            for c in t.constants:
                bare = bare.replace(c, "")
            if re.search(r"\d", bare):
                raise TemplateError(f"{t.id} ({lang}): a digit outside placeholders and declared constants: {bare!r}")
        if lang_left := tx.ja_leftovers(_PH.sub("", ja)):
            raise TemplateError(f"{t.id}: English or half-width brackets in the JA template: {lang_left}")
    if "text" in t.types.values():
        raise TemplateError(f"{t.id}: free-text placeholders are not allowed")


def load(path: pathlib.Path = CATALOGUE) -> tuple[int, dict[str, Template]]:
    doc = yaml.safe_load(path.read_text())
    out: dict[str, Template] = {}
    for e in doc["templates"]:
        t = Template(id=e["id"], family=e["family"], steps=e.get("steps", []), source=e.get("source", []), types=e.get("types") or {},
                     text={"en": e["en"], "ja": e["ja"]}, variants=e.get("variants", []), constants=e.get("constants", []), rain=bool(e.get("rain")))
        if t.id in out:
            raise TemplateError(f"duplicate template {t.id}")
        _check_static(t)
        out[t.id] = t
    return int(doc["version"]), out


def _matches(when: Mapping, values: Mapping[str, V], ctx: Mapping) -> bool:
    for k, arg in when.items():
        if k == "one" and values[arg].value != 1:
            return False
        if k == "zero" and values[arg].value != 0:
            return False
        if k == "single" and values[arg].value[0] != values[arg].value[1]:
            return False
        if k == "cont" and ctx.get("prev_family") != arg:
            return False
        if k == "unrest" and bool(ctx.get("unrest")) != bool(arg):
            return False
    return True


def render(t: Template, values: Mapping[str, V | None], ctx: Mapping | None = None) -> dict | None:
    """{en, ja} for the template, or None when any placeholder is missing (the absent-data rule)."""
    ctx = ctx or {}
    for name in t.types:
        v = values.get(name)
        if v is None or v.value is None or (isinstance(v.value, tuple) and None in v.value):
            return None
        if not v.source:
            raise TemplateError(f"{t.id}: {name} has no source id")
    form = dict(next((f for f in t.variants if _matches(f["when"], values, ctx)), t.text))
    for name, kind in t.types.items():  # a one-day span reads "on 3 June 2024", not "from 3 June 2024"
        if kind == "span" and values[name].value[0] == values[name].value[1]:
            form["en"] = form["en"].replace(f"from {{{name}}}", f"on {{{name}}}")
    return {lang: _PH.sub(lambda m, lang=lang: _fmt(t.types[m.group(1)], values[m.group(1)].value, lang), form[lang]) for lang in LANGS}


# ---------------------------------------------------------------- checks on rendered text (§B6.4)

def safety_words(text: dict) -> list[str]:
    en = text["en"].replace(DISCLAIMER[0], "")
    ja = text["ja"].replace(DISCLAIMER[1], "")
    return SAFETY_EN.findall(en) + SAFETY_JA.findall(ja)


def causal_words(text: dict) -> list[str]:
    return CAUSAL_EN.findall(text["en"]) + CAUSAL_JA.findall(text["ja"])


def check_sentence(t: Template, text: dict) -> list[str]:
    errs = []
    if w := safety_words(text):
        errs.append(f"{t.id}: safety or advice words {w}")
    if t.rain and (w := causal_words(text)):
        errs.append(f"{t.id}: causal words in a rain sentence {w}")
    if left := tx.ja_leftovers(text["ja"]):
        errs.append(f"{t.id}: English, ISO dates or half-width brackets in Japanese {left}")
    return errs
