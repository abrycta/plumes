"""Release tags of the private archive (abrycta/plumes-archive): every tag, newest per bundle by its (date, sequence).

Tags are `<id>-<YYYY-MM-DD>` with `.2`, `.3` … for later adoptions the same day. All releases share one createdAt (the
tagged commit's date), so neither `gh release list -L N` order nor a lexical sort finds the newest one: `.10` sorts
before `.2`, and a bundle that rarely changes falls out of a newest-N window (audit P11).
"""

from __future__ import annotations

import re
import subprocess

TAG = re.compile(r"^(?P<id>.+)-(?P<date>\d{4}-\d{2}-\d{2})(?:\.(?P<seq>\d+))?$")


def key(tag: str) -> tuple[str, int]:
    m = TAG.match(tag)
    return (m["date"], int(m["seq"] or 1)) if m else ("", 0)


def list_tags(repo: str, drafts: bool = False) -> list[str]:
    """Every release tag in `repo` (all pages of the API); drafts only when asked."""
    sel = ".[] | .tag_name" if drafts else ".[] | select(.draft | not) | .tag_name"
    out = subprocess.run(["gh", "api", "--paginate", f"repos/{repo}/releases?per_page=100", "--jq", sel],
                         capture_output=True, text=True, check=True).stdout
    return out.split()


def newest(tags: list[str], sid: str) -> str | None:
    """The newest tag of bundle `sid` (exact id: `firms-modis` never matches `firms-modis-x-…`)."""
    mine = [t for t in tags if (m := TAG.match(t)) and m["id"] == sid]
    return max(mine, key=key, default=None)
