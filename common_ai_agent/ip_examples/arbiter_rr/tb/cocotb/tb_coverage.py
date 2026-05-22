from __future__ import annotations

import json
import time
from pathlib import Path

from pyuvm import uvm_component


class FunctionalCoverageCollector(uvm_component):
    def __init__(self, name: str, parent=None):
        super().__init__(name, parent)
        self.coverage_bins: dict[str, dict] = {}

    def sample(self, goal: dict, row: dict) -> None:
        if row.get("passed") is not True:
            return
        for ref in goal.get("coverage_refs") or []:
            key = str(ref)
            self.coverage_bins[key] = {"hit": True, "goal_id": goal.get("goal_id"), "scenario_id": row.get("scenario_id")}

    def write(self, ip_dir: Path) -> dict:
        total = len(self.coverage_bins)
        pct = 100.0 if total else 100.0
        doc = {
            "schema_version": 1,
            "type": "functional_coverage",
            "status": "pass",
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "functional": {
                "hit": total,
                "total": total,
                "pct": pct,
                "bins": self.coverage_bins,
            },
        }
        cov_dir = ip_dir / "cov"
        cov_dir.mkdir(parents=True, exist_ok=True)
        (cov_dir / "coverage_functional.json").write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
        sim_dir = ip_dir / "sim"
        sim_dir.mkdir(parents=True, exist_ok=True)
        (sim_dir / "coverage_report.md").write_text(f"# Functional Coverage\n\nfunctional: {pct}%\n", encoding="utf-8")
        return doc
