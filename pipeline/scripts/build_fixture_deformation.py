"""Add the COMET deformation fixture (LAYERS-PLAN §3.1) to contracts/fixtures/data/v0 from the canary download (local).

Needs the Taal frame 032D_07536_111313 in data/raw/comet-licsbas/ (`uv run --group comet python -m plumes.comet fetch
--only taal --limit 1`). Writes layers/deformation/taal-032D_07536_111313.tif, the `deformation-velocity` entry in
layers.json and the `los_comet_032D_07536_111313` series in volcano/taal.json, trimmed to the fixture window like the
other fixture series. The spike-based build_fixtures.py leaves these alone, so run this after it.

    cd pipeline && PYTHONPATH=. uv run --group comet python scripts/build_fixture_deformation.py
"""

import json
import pathlib

from plumes import comet

ROOT = pathlib.Path(__file__).resolve().parents[2]
V = ROOT / "contracts" / "fixtures" / "data" / "v0"
TAAL = {"id": "taal", "lon": 120.9975, "lat": 14.0106}
FRAME = "032D_07536_111313"


def main() -> None:
    raw = comet.OUT / f"taal_{FRAME}.json"
    if not raw.exists():
        raise SystemExit(f"missing {raw}: run `python -m plumes.comet fetch --only taal --limit 1` first")
    listing = json.loads((comet.OUT / "frames.json").read_text())
    tmp = comet.OUT / "fixture-frames"
    tmp.mkdir(exist_ok=True)
    (tmp / "frames.json").write_text(json.dumps({"frames": [r for r in listing["frames"] if r["volcano"] == "taal" and r["frame"] == FRAME]}))
    (tmp / raw.name).unlink(missing_ok=True)
    (tmp / raw.name).symlink_to(raw)
    series, layer = comet.build(V, [TAAL], raw_dir=tmp)
    assert layer and "taal" in series, "the Taal canary produced no layer or series"

    layers_path = V / "layers.json"
    doc = json.loads(layers_path.read_text())
    layer["note"] = {"en": layer["note"]["en"] + " Fixture: the Taal frame 032D only.", "ja": layer["note"]["ja"] + "フィクスチャはタールの032Dフレームのみ。"}
    doc["layers"] = [x for x in doc["layers"] if x["id"] != "deformation-velocity"] + [layer]
    layers_path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")

    taal_path = V / "volcano" / "taal.json"
    taal = json.loads(taal_path.read_text())
    s = series["taal"][f"los_comet_{FRAME}"]
    s["rows"] = [r for r in s["rows"] if taal["span"]["start"] <= r[0] <= taal["span"]["end"]]
    taal["events"][f"los_comet_{FRAME}"] = s
    srcs = [x for x in taal["provenance"]["sources"] if x["id"] != comet.SOURCE_ID]
    reg = next(x for x in srcs)  # same shape as the other fixture provenance records
    srcs.append({"id": comet.SOURCE_ID, "attribution": comet.attribution(s["start"], layer["time"]["end"]),
                 "licence": "noncommercial-only: COMET Volcano Portal CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/)",
                 **{k: reg[k] for k in ("snapshotDate", "fromArchive") if k in reg}})
    taal["provenance"]["sources"] = srcs
    taal_path.write_text(json.dumps(taal, ensure_ascii=False, indent=1) + "\n")
    print("deformation fixture written:", layer["frames"][0]["id"], len(s["rows"]), "rows")


if __name__ == "__main__":
    main()
