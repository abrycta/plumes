"""python -m plumes.stories --version-dir DIR [--out DIR] [--previous URL|DIR]"""

import argparse
import json
import pathlib

from plumes.stories import previous as prev
from plumes.stories.generate import generate

ap = argparse.ArgumentParser(description="Generate stories from a data version (STORIES-PLAN Part B)")
ap.add_argument("--version-dir", type=pathlib.Path, required=True, help="a data version folder (volcano/*.json, deeptime.json)")
ap.add_argument("--out", type=pathlib.Path, help="where to write story/ and stories.json (default: the version folder)")
ap.add_argument("--previous", default=prev.PAGES, help="the previous version (a folder, or the Pages base URL), whose public stories keep their ids")
a = ap.parse_args()
p = pathlib.Path(a.previous) if not a.previous.startswith("http") else a.previous
res = generate(a.version_dir, a.out, previous=prev.load(p))
failed = [c for c in res["checks"] if not c["passed"]]
print(json.dumps({"stories": [(s["id"], s.get("score", {}).get("tier"), s.get("sentences"), s.get("file")) for s in res["stories"]],
                  "excluded": len(res["excluded"]), "left": res["left"], "failed": failed}, indent=1, ensure_ascii=False))
raise SystemExit(1 if failed else 0)
