"""Earth Engine budget guard for the shared lgu-lights project (DATA-PLAN §7, DECISIONS Q11, Q22, S8).

Plumes' own ceiling: 50 EECU-hours a calendar month and 10 per run. Every interactive call runs under the EE profiler;
its EECU-seconds are summed into a state file (`ee-usage.json`, published with each data version so the next run and
Kurt can read the month-to-date). A call that would start above either ceiling raises BudgetExceeded: the run fails
clearly and nothing else is affected. The project's monthly total can only be read in the Cloud console (S8), so this
counts Plumes' own use only.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import re
import tempfile
import time

import ee

MONTH_CAP_S = 50 * 3600
RUN_CAP_S = 10 * 3600


class BudgetExceeded(RuntimeError):
    pass


def init() -> None:
    """Authenticate from EE_SA_KEY (the JSON text, CI) or EE_KEY_FILE (a path, local). The key never touches the repo."""
    raw = os.environ.get("EE_SA_KEY")
    path = os.environ.get("EE_KEY_FILE")
    if raw:
        info = json.loads(raw)
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write(raw)
        try:
            creds = ee.ServiceAccountCredentials(info["client_email"], f.name)
        finally:
            os.unlink(f.name)
    elif path:
        info = json.load(open(path))
        creds = ee.ServiceAccountCredentials(info["client_email"], path)
    else:
        raise SystemExit("EE_SA_KEY or EE_KEY_FILE must be set")
    ee.Initialize(creds, project=info["project_id"])


def _eecu_seconds(profile_text: str) -> float:
    total = 0.0
    for line in profile_text.splitlines():
        m = re.match(r"\s*([\d.]+)\s+\S+\s+\d+\s+", line)
        if m:
            total += float(m.group(1))
    return total


class Budget:
    def __init__(self, state: pathlib.Path):
        self.state = state
        self.month = dt.date.today().strftime("%Y-%m")
        self.data = json.loads(state.read_text()) if state.exists() else {"months": {}, "runs": []}
        self.run_s = 0.0
        self.calls = 0
        self.saved = False

    @property
    def month_s(self) -> float:
        """Month-to-date: the ledger as read at start (or after save) plus this run so far."""
        return self.data["months"].get(self.month, 0.0) + (0.0 if self.saved else self.run_s)

    def check(self) -> None:
        if self.month_s >= MONTH_CAP_S:
            raise BudgetExceeded(f"Plumes' Earth Engine month {self.month} is at {self.month_s / 3600:.2f} EECU-h (cap 50)")
        if self.run_s >= RUN_CAP_S:
            raise BudgetExceeded(f"this run used {self.run_s / 3600:.2f} EECU-h (cap 10 per run)")

    def get(self, obj):
        """obj.getInfo() under the profiler; adds the call's EECU-seconds to the run and the month."""
        self.check()
        ids: list[str] = []
        for attempt in range(5):
            try:
                with ee.data.profiling(ids.append):
                    out = obj.getInfo()
                break
            except ee.EEException as e:
                if "Too many concurrent" not in str(e) or attempt == 4:
                    raise
                time.sleep(20 * (attempt + 1))
        secs = 0.0
        if ids:
            for _ in range(6):
                try:
                    secs = _eecu_seconds(ee.ApiFunction.call_("Profile.getProfiles", ids=ids, format="text").getInfo())
                    break
                except ee.EEException:
                    time.sleep(3)
        self.run_s += secs
        self.calls += 1
        return out

    def save(self, label: str) -> dict:
        rec = {"date": dt.date.today().isoformat(), "label": label, "eecu_s": round(self.run_s, 1), "calls": self.calls}
        # re-read and merge, so concurrent runs (e.g. so2 and fire chunks) don't overwrite each other
        cur = json.loads(self.state.read_text()) if self.state.exists() else {"months": {}, "runs": []}
        cur["months"][self.month] = cur["months"].get(self.month, 0.0) + self.run_s
        cur["runs"].append(rec)
        self.data = cur
        self.state.parent.mkdir(parents=True, exist_ok=True)
        self.state.write_text(json.dumps(self.data, indent=1))
        self.saved = True
        return {**rec, "month_to_date_eecu_h": round(self.month_s / 3600, 3)}
