"""Extract the chosen sources (licence verdict and attribution) for the About & sources page.

Reads ../docs/sources-draft.yaml (the evidence is in ../docs/LICENCES.md) and writes src/content/sources.json.
Run: npm run sources   (re-run whenever the registry's licence or attribution text changes).
"""

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
REG = ROOT / "docs" / "sources-draft.yaml"
OUT = Path(__file__).resolve().parents[1] / "src" / "content" / "sources.json"

text = REG.read_text(encoding="utf-8")
chosen: dict[str, str] = {}
for m in re.finditer(r"- id: ([\w.-]+)\n\s+# chosen: true\s+# source (\d+) of \d+, (M[\d.]+)", text):
    chosen[m.group(1)] = m.group(3)

reg = yaml.safe_load(text)
rows = []
for s in reg["sources"]:
    if s["id"] not in chosen:
        continue
    desc = " ".join(s["description"].split())
    publisher = re.sub(r"^\[M[\d.]+\]\s*", "", desc).split(":")[0].split(". ")[0]
    licence = " ".join(s["licence"].split())
    vm = re.match(r"(open-with-conditions|noncommercial-only|link-only|open|paid)", licence)
    verdict = vm.group(1) if vm else "see-ledger"
    # A human-readable page only: API queries, buckets and catalogue endpoints are not linked.
    api = re.compile(r"[?]|/api/|cmr\.|s3\.|harmony\.|/ows|wmts|/fdsnws/|stac\.")
    first_link = next((l["url"] for l in s.get("links", []) if l.get("url", "").startswith("http") and not api.search(l["url"])), None)
    rows.append(
        {
            "id": s["id"],
            "milestone": chosen[s["id"]],
            "title": publisher[:160],
            "verdict": verdict,
            "licence": licence,
            "attribution": " ".join(str(s["attribution"]).split()),
            "link": first_link,
        }
    )

if len(rows) < 24:
    sys.exit(f"expected at least 24 chosen sources, found {len(rows)}")
OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"{len(rows)} sources -> {OUT.relative_to(ROOT)}")
