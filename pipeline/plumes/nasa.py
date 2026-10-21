"""NASA Earthdata sources: MSVOLSO2L4 (SO2 mass per eruption). Needs EARTHDATA_TOKEN (CI mints it from the login).

    EARTHDATA_TOKEN=… uv run python -m plumes.nasa msvolso2l4
"""

from __future__ import annotations

import json
import os
import sys

import httpx

from plumes.crawl.records import now, sha256
from plumes.paths import RAW

MSVOL_URL = "https://measures.gesdisc.eosdis.nasa.gov/data/SO2/MSVOLSO2L4.4/MSVOLSO2L4_v04-00-2026m0513.txt"
PH_BOX = (4.0, 22.0, 116.0, 128.0)


def parse_msvol(text: str) -> list[dict]:
    """Philippine rows (inside the box) of the tab-separated eruption table."""
    lines = text.splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.startswith("volcano\t"))
    cols = lines[start].split()
    out = []
    for ln in lines[start + 1:]:
        parts = ln.split()  # tabs and spaces are mixed; names use underscores
        if len(parts) != len(cols):
            continue
        r = dict(zip(cols, parts, strict=True))
        lat, lon = float(r["lat"]), float(r["lon"])
        if PH_BOX[0] <= lat <= PH_BOX[1] and PH_BOX[2] <= lon <= PH_BOX[3]:
            obs, est = float(r["p_alt_obs"]), float(r["p_alt_est"])
            out.append({"volcano": r["volcano"].replace("_", " "), "lat": lat, "lon": lon,
                        "date": f"{int(r['yyyy']):04d}-{int(r['mm']):02d}-{int(r['dd']):02d}", "type": r["type"],
                        "vei": None if r["vei"] in ("nd", "") else int(r["vei"]), "plume_km_obs": None if obs < 0 else obs,
                        "plume_km_est": None if est < 0 else est, "so2_kt": float(r["so2(kt)"])})
    return out


def msvolso2l4() -> dict:
    tok = os.environ.get("EARTHDATA_TOKEN")
    if not tok:
        sys.exit("EARTHDATA_TOKEN is not set")
    r = httpx.get(MSVOL_URL, headers={"Authorization": f"Bearer {tok}"}, follow_redirects=True, timeout=120)
    r.raise_for_status()
    if not r.text.lstrip().startswith("ESDT"):
        sys.exit("MSVOLSO2L4: unexpected response (login page?)")
    out = RAW / "nasa-msvolso2l4"
    out.mkdir(parents=True, exist_ok=True)
    (out / MSVOL_URL.rsplit("/", 1)[-1]).write_bytes(r.content)
    rows = parse_msvol(r.text)
    meta = {"url": MSVOL_URL, "fetched": now(), "sha256": sha256(r.content), "bytes": len(r.content), "rows_ph": len(rows)}
    (out / "philippines.json").write_text(json.dumps({"meta": meta, "rows": rows}, indent=1))
    return meta


if __name__ == "__main__":
    print(msvolso2l4())
