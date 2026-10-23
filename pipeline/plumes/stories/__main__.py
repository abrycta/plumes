"""python -m plumes.stories --version-dir DIR [--out DIR] [--snapshot]

--snapshot: after Kurt's review (hashes added to review.yaml), save each reviewed story's text to reviewed/<id>.json, which
keeps it public until the next review whatever later data does (DECISIONS, "Reviewed stories stay stable").
"""

import argparse
import json
import pathlib

from plumes.stories.generate import REVIEWED, generate

ap = argparse.ArgumentParser(description="Generate story drafts from a data version (STORIES-PLAN Part B)")
ap.add_argument("--version-dir", type=pathlib.Path, required=True, help="a data version folder (volcano/*.json, deeptime.json)")
ap.add_argument("--out", type=pathlib.Path, help="where to write story/ and stories.json (default: the version folder)")
ap.add_argument("--snapshot", action="store_true", help="save every story whose new text matches review.yaml to reviewed/<id>.json")
a = ap.parse_args()
res = generate(a.version_dir, a.out)
failed = [c for c in res["checks"] if not c["passed"]]
if a.snapshot:
    out = a.out or a.version_dir
    pending = {p["id"] for p in res["pendingReview"]}
    for e in res["stories"]:
        if e["status"] == "reviewed" and e["id"] not in pending and e.get("file") == f"story/{e['id']}.json":
            f = out / e["file"] if (out / e["file"]).exists() else a.version_dir / e["file"]
            doc = json.loads(f.read_text())
            if doc.get("generator"):
                REVIEWED.mkdir(exist_ok=True)
                (REVIEWED / f"{e['id']}.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
print(json.dumps({"stories": [(s["id"], s.get("score", {}).get("tier"), s.get("sentences"), s.get("file")) for s in res["stories"]],
                  "excluded": len(res["excluded"]), "pendingReview": res["pendingReview"], "failed": failed}, indent=1, ensure_ascii=False))
raise SystemExit(1 if failed else 0)
