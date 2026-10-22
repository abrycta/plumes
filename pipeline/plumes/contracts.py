"""Validate read models against contracts/schemas (used by the materialiser's checks and by the tests)."""

import json
import pathlib

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

SCHEMAS = pathlib.Path(__file__).resolve().parents[2] / "contracts" / "schemas"
KIND_TO_SCHEMA = {"volcano": "volcano", "volcanoes": "volcanoes", "layers": "layers", "story": "story", "latest": "latest", "manifest": "latest", "deeptime": "deeptime", "stories": "stories"}


def _registry() -> Registry:
    res = [(p.name, Resource.from_contents(json.loads(p.read_text()))) for p in SCHEMAS.glob("*.schema.json")]
    res += [(r.contents["$id"], r) for _, r in res]
    return Registry().with_resources(res)


_REG = _registry()


def validator(name: str) -> Draft202012Validator:
    schema = json.loads((SCHEMAS / f"{name}.schema.json").read_text())
    return Draft202012Validator(schema, registry=_REG, format_checker=FormatChecker())


def errors(doc: dict) -> list[str]:
    """Return schema errors for a read model, picking the schema from its `kind`."""
    kind = doc.get("kind")
    if kind not in KIND_TO_SCHEMA:
        return [f"unknown kind {kind!r}"]
    return [f"{'/'.join(map(str, e.absolute_path))}: {e.message}" for e in validator(KIND_TO_SCHEMA[kind]).iter_errors(doc)]
