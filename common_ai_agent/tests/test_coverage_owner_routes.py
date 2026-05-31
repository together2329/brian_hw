from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def _load_module():
    path = Path(__file__).resolve().parents[1] / "workflow" / "coverage" / "scripts" / "ssot_coverage_summary.py"
    spec = importlib.util.spec_from_file_location(f"ssot_coverage_owner_routes_test_{id(path)}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_main_returns_owner_routed_status_for_non_signoff_coverage_gaps(tmp_path: Path, monkeypatch):
    cov = _load_module()
    ip_dir = tmp_path / "owner_routed_ip"
    for subdir in ("yaml", "cov", "verify", "sim"):
        (ip_dir / subdir).mkdir(parents=True)
    (ip_dir / "yaml" / "owner_routed_ip.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                "  name: owner_routed_ip",
                "test_requirements:",
                "  coverage_goals:",
                "    function:",
                "      target_pct: 100",
                "      bins:",
                "        - id: FCOV_NEEDS_RTL_REPAIR",
                "          coverage_domain: function",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "cov" / "fcov_plan.json").write_text(
        json.dumps({"bins": [{"id": "FCOV_NEEDS_RTL_REPAIR", "coverage_domain": "function"}]}) + "\n",
        encoding="utf-8",
    )
    (ip_dir / "cov" / "coverage_functional.json").write_text(
        json.dumps({"status": "pass", "functional": {"bins": {"FCOV_NEEDS_RTL_REPAIR": {"hit": True}}}})
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "verify" / "equivalence_goals.json").write_text(
        json.dumps({"goals": [{"goal_id": "EQ_REPAIR", "coverage_refs": ["FCOV_NEEDS_RTL_REPAIR"]}]}) + "\n",
        encoding="utf-8",
    )
    (ip_dir / "sim" / "scoreboard_events.jsonl").write_text(
        json.dumps(
            {
                "goal_id": "EQ_REPAIR",
                "scenario_id": "SC_REPAIR",
                "coverage_refs": ["FCOV_NEEDS_RTL_REPAIR"],
                "passed": False,
                "fl_expected": {"model_result": {"needs_repair": 1}},
                "rtl_observed": {"needs_repair": 0},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "cov" / "coverage_owner_routes.json").write_text(
        json.dumps(
            {
                "type": "coverage_owner_routes",
                "status": "non_signoff",
                "routes": [
                    {
                        "bin_id": "FCOV_NEEDS_RTL_REPAIR",
                        "owner": "rtl-gen",
                        "status": "non_signoff_blocker",
                        "reason": "scoreboard row failed; repair RTL before production signoff",
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(sys, "argv", ["ssot_coverage_summary.py", str(ip_dir)])

    assert cov.main() == 0
    payload = json.loads((ip_dir / "cov" / "coverage.json").read_text(encoding="utf-8"))
    assert payload["status"] == "owner_routed"
    assert payload["rtl_observed"]["status"] == "owner_routed"
    assert payload["owner_routes"]["unrouted_missing_bins"] == []
    assert payload["owner_routes"]["routes_by_bin"]["FCOV_NEEDS_RTL_REPAIR"]["owner"] == "rtl-gen"
