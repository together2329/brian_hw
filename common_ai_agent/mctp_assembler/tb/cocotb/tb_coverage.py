from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from pyuvm import uvm_component


class FunctionalCoverageCollector(uvm_component):
    def __init__(self, name: str, parent=None):
        super().__init__(name, parent)
        self.coverage_bins: dict[str, dict[str, Any]] = {}

    def sample(self, scenario_id: str, refs: list[str], passed: bool) -> None:
        if not passed:
            return
        for ref in refs or [scenario_id]:
            key = str(ref)
            self.coverage_bins[key] = {"hit": True, "scenario_id": scenario_id}

    def write(self, ip_dir: Path) -> dict[str, Any]:
        total = len(self.coverage_bins)
        doc = {
            "schema_version": 1,
            "type": "functional_coverage",
            "status": "pass" if total else "partial",
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "functional": {
                "hit": total,
                "total": total,
                "pct": 100.0 if total else 0.0,
                "bins": self.coverage_bins,
            },
        }
        cov_dir = ip_dir / "cov"
        cov_dir.mkdir(parents=True, exist_ok=True)
        (cov_dir / "coverage_functional.json").write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
        return doc
