"""python -m plumes.stories --version-dir DIR [--out DIR]"""

import argparse
import json
import pathlib

from plumes.stories.generate import generate

ap = argparse.ArgumentParser(description="Generate story drafts from a data version (STORIES-PLAN Part B)")
ap.add_argument("--version-dir", type=pathlib.Path, required=True, help="a data version folder (volcano/*.json, deeptime.json)")
ap.add_argument("--out", type=pathlib.Path, help="where to write story/ and stories.json (default: the version folder)")
a = ap.parse_args()
res = generate(a.version_dir, a.out)
failed = [c for c in res["checks"] if not c["passed"]]
print(json.dumps({"stories": [(s["id"], s.get("score", {}).get("tier"), s.get("sentences"), s.get("file")) for s in res["stories"]],
                  "excluded": len(res["excluded"]), "failed": failed}, indent=1, ensure_ascii=False))
raise SystemExit(1 if failed else 0)
