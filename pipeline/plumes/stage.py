"""Run one pipeline stage (a crawler, an Earth Engine step) in isolation, so one dead or changed source never stops
the others (audit P7). A failing stage keeps the records restored from the archive, prints a ::warning, opens or
updates its `stage <name>` health issue, and exits 0, so the run goes on to the build, whose blocking checks still
decide whether anything is published. A stage that succeeds again closes its issue.

    uv run python -m plumes.stage <name> <module> [args…]      # e.g. plumes.stage lava-index plumes.crawl.lava index --since auto
"""

from __future__ import annotations

import subprocess
import sys

from plumes import health


def run(name: str, argv: list[str]) -> int:
    r = subprocess.run([sys.executable, "-m", *argv])
    key = f"stage {name}"
    if r.returncode != 0:
        health.report(key, f"failed rc={r.returncode}",
                      f"Stage `{name}` (`python -m {' '.join(argv)}`) failed with exit code {r.returncode}; the records restored "
                      "from the archive were kept and the run went on. See the Data run log.")
    else:
        health.resolve(key, f"Stage `{name}` succeeded again.")
    return r.returncode


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    run(sys.argv[1], sys.argv[2:])
