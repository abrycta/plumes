"""Internal alerts for the pipeline's own stages and sources, through the kit's issue mechanism (archivekit
IssueReporter: one open `source-health` issue per key in the registry's issue repo, a comment only when the state
changes). Always also a GitHub ::warning. Never public: nothing here reaches the app or the published files.

Reporting never fails the run: without the kit, a token or CI (ARCHIVEKIT_REPORT_ISSUES), only the ::warning is printed.
"""

from __future__ import annotations

import functools
import os

from plumes.paths import PIPELINE, REGISTRY


@functools.cache
def _reporter():
    if os.environ.get("PLUMES_TRIAL") == "true":  # a trial Data run (publish=false) warns but opens or closes no issue
        return None
    try:
        import archivekit
        import httpx
        from archivekit.github import IssueReporter

        reg = archivekit.load_registry(REGISTRY, root=PIPELINE)
        h = reg.health
        return IssueReporter.from_env(reg.issue_repo, httpx.Client(timeout=30), token_env=h.get("issue_token_env", "ARCHIVE_READ_TOKEN"),
                                      label=h.get("issue_label", "source-health"), title_prefix=h.get("issue_title_prefix", "source-health"))
    except Exception as e:  # the alert is best effort; the ::warning below always shows
        print(f"::notice title=health issue not filed::{type(e).__name__}: {e}", flush=True)
        return None


def report(key: str, state: str, summary: str) -> str:
    """A problem with `key` (a stage or a source): ::warning, and the issue opened or updated when `state` changed."""
    print(f"::warning title={key}::{summary.splitlines()[0]}", flush=True)
    r = _reporter()
    if r is None:
        return "not filed"
    try:
        return r.report_problem(key, state, summary)
    except Exception as e:
        print(f"::notice title=health issue not filed::{type(e).__name__}: {e}", flush=True)
        return "not filed"


def resolve(key: str, note: str) -> str:
    """`key` is healthy again: closes its open issue, if any."""
    r = _reporter()
    if r is None:
        return "none"
    try:
        return r.resolve(key, note)
    except Exception as e:
        print(f"::notice title=health issue not resolved::{type(e).__name__}: {e}", flush=True)
        return "none"
