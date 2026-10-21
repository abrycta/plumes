import json
import pathlib

import pytest

from plumes.contracts import errors

FIX = pathlib.Path(__file__).resolve().parents[2] / "contracts" / "fixtures" / "data"
FILES = sorted(p for p in FIX.rglob("*.json*") if "layers/" not in p.as_posix().split("v0/", 1)[-1])


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.relative_to(FIX).as_posix())
def test_fixture_matches_schema(path):
    assert errors(json.loads(path.read_text())) == []


def test_every_phivolcs_vaac_dromic_row_has_a_url():
    taal = json.loads((FIX / "v0" / "volcano" / "taal.json").read_text())
    for table in ("bulletins", "advisories", "displacement"):
        assert all(r[-1].startswith("https://") for r in taal[table]["rows"]), table
