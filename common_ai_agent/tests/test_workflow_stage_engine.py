from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

from src.headless_workflow import _stable_json_sha256, _structured_ssot_yaml
from src.workflow_stage_engine import ToolRun, WorkflowStageEngine, _rtl_manifest_progress, canonical_stage


SOURCE_ROOT = Path(__file__).resolve().parents[1]
DERIVE_RTL_TODOS = SOURCE_ROOT / "workflow" / "rtl-gen" / "scripts" / "derive_rtl_todos.py"
SSOT_TO_RTL = SOURCE_ROOT / "workflow" / "rtl-gen" / "scripts" / "ssot_to_rtl.py"
PROFILE_RTL_REFERENCE = SOURCE_ROOT / "workflow" / "rtl-gen" / "scripts" / "profile_rtl_reference.py"
PREPARE_RTL_HUMAN_REVIEW = SOURCE_ROOT / "workflow" / "rtl-gen" / "scripts" / "prepare_rtl_human_review.py"
REFRESH_RTL_PROVENANCE = SOURCE_ROOT / "workflow" / "rtl-gen" / "scripts" / "refresh_rtl_provenance.py"
REPAIR_SSOT = SOURCE_ROOT / "workflow" / "ssot-gen" / "scripts" / "repair_ssot_schema.py"
WRITE_STA_SDC = SOURCE_ROOT / "workflow" / "sta" / "scripts" / "write_sdc.sh"
EMIT_FL_MODEL = SOURCE_ROOT / "workflow" / "fl-model-gen" / "scripts" / "emit_fl_model.py"
EMIT_AUTHORITY_MANIFEST = SOURCE_ROOT / "workflow" / "fl-model-gen" / "scripts" / "emit_authority_manifest.py"
EMIT_MODEL_SIGNATURE = SOURCE_ROOT / "workflow" / "fl-model-gen" / "scripts" / "emit_model_signature.py"


def _write_ssot(root: Path, ip: str) -> None:
    ssot = root / ip / "yaml" / f"{ip}.ssot.yaml"
    ssot.parent.mkdir(parents=True, exist_ok=True)
    ssot.write_text(_structured_ssot_yaml(ip, "double sampled input on valid transactions"), encoding="utf-8")


def _write_coverage_ready_fixture(root: Path, ip: str) -> None:
    ip_dir = root / ip
    for subdir in ("yaml", "cov", "sim", "tb/cocotb", "verify"):
        (ip_dir / subdir).mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "function_model:",
                "  transactions:",
                "    - id: FM_DOUBLE",
                "      name: double_transaction",
                "      outputs:",
                "        - result",
                "cycle_model:",
                "  latency: 1",
                "test_requirements:",
                "  scenarios:",
                "    - id: SC_DOUBLE",
                "      name: double accepted value",
                "      stimulus: accepted transaction with value 7",
                "      expected: result equals value * 2",
                "      checker: EquivalenceScoreboard compares FunctionalModel.apply against RTL observation",
                "  coverage_goals:",
                "    functional: SSOT state transition functional bins and scenarios reach 100%",
                "    planned_bins:",
                "      - id: FCOV_DOUBLE",
                "        class: functional",
                "        description: accepted double-value scenario observed",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "cov" / "fcov_plan.json").write_text(
        json.dumps(
            {
                "planned_before_rtl": True,
                "bins": [
                    {
                        "id": "FCOV_DOUBLE",
                        "class": "scenario",
                        "goal_id": "EQ_DOUBLE",
                        "source": "test_requirements.coverage_goals.planned_bins[0]",
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "verify" / "equivalence_goals.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "summary": {"total": 1, "required": 1, "blocked": 0},
                "goals": [
                    {
                        "goal_id": "EQ_DOUBLE",
                        "title": "Double accepted value",
                        "kind": "datapath",
                        "coverage_refs": ["FCOV_DOUBLE"],
                        "blocked": False,
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    test_body = (
        "import cocotb\n"
        "from equivalence_scoreboard import EquivalenceScoreboard\n\n"
        "SCOREBOARD_CONTRACT = {\n"
        "    'equivalence_goals.json': 'load goals',\n"
        "    'scoreboard_events.jsonl': 'emit rows',\n"
        "    'goal_id': 'goal_id',\n"
        "    'fl_expected': 'fl_expected',\n"
        "    'rtl_observed': 'rtl_observed',\n"
        "    'passed': 'passed',\n"
        "    'mismatch': 'mismatch',\n"
        "    'coverage_refs': 'coverage_refs',\n"
        "}\n\n"
        "class CoverageSmoke:\n"
        "    def __init__(self):\n"
        "        self.scoreboard_cls = EquivalenceScoreboard\n\n"
        "        # production path instantiates EquivalenceScoreboard(ip, root)\n"
        "    def sample(self):\n"
        "        assert True\n\n"
        "def test_assertion_path_exists():\n"
        "    assert CoverageSmoke().sample() is None\n\n"
        + ("# generic cocotb fixture filler for disk validator\n" * 20)
    )
    runner_body = (
        "from cocotb.runner import get_runner\n\n"
        "def test_runner():\n"
        "    runner = get_runner('icarus')\n"
        "    assert runner is not None\n\n"
        + ("# generic runner fixture filler for disk validator\n" * 20)
    )
    (ip_dir / "tb" / "cocotb" / f"test_{ip}.py").write_text(test_body, encoding="utf-8")
    (ip_dir / "tb" / "cocotb" / "test_runner.py").write_text(runner_body, encoding="utf-8")
    (ip_dir / "sim" / "results.xml").write_text(
        '<testsuite tests="1" failures="0" errors="0"><testcase name="SC_DOUBLE"/></testsuite>\n',
        encoding="utf-8",
    )
    (ip_dir / "sim" / "scoreboard_events.jsonl").write_text(
        json.dumps(
            {
                "goal_id": "EQ_DOUBLE",
                "scenario_id": "SC_DOUBLE",
                "cycle": 3,
                "stimulus": {"value": 7},
                "fl_expected": {"model_api": "FunctionalModel.apply", "model_result": {"result": 14}},
                "rtl_observed": {"result": 14},
                "passed": True,
                "mismatch": "",
                "coverage_refs": ["FCOV_DOUBLE"],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "sim" / "sim_report.txt").write_text("TESTS=1 PASS=1 FAIL=0\n0 errors, 0 warnings\n", encoding="utf-8")
    (ip_dir / "cov" / "coverage_functional.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "type": "functional_coverage",
                "status": "pass",
                "functional": {
                    "hit": 1,
                    "total": 1,
                    "pct": 100.0,
                    "bins": {"FCOV_DOUBLE": {"hit": True, "goal_id": "EQ_DOUBLE", "scenario_id": "SC_DOUBLE"}},
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_stage_aliases_canonicalize_ui_and_headless_names():
    assert canonical_stage("sfm") == "ssot-fl-model"
    assert canonical_stage("fl-model-gen") == "ssot-fl-model"
    assert canonical_stage("cl-model") == "ssot-cycle-model"
    assert canonical_stage("scm") == "ssot-cycle-model"
    assert canonical_stage("sdf") == "ssot-dual-fcov"
    assert canonical_stage("spa") == "ssot-protocol-assertions"
    assert canonical_stage("protocol-assertions") == "ssot-protocol-assertions"
    assert canonical_stage("tb") == "ssot-tb-cocotb"
    assert canonical_stage("cov") == "coverage"
    assert canonical_stage("/sd") == "sim-debug"


def test_protocol_assertions_stage_generates_sva_from_cycle_model(tmp_path: Path):
    ip = "protocol_assertion_stage"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "cycle_model:",
                "  clock: clk",
                "  reset: rst_n",
                "  handshake_rules:",
                "    - {name: cmd_accept, signal: valid && ready, rule: payload remains stable until accept}",
                "  ordering:",
                "    - response follows accepted command",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = WorkflowStageEngine(tmp_path).run_stage("ssot-protocol-assertions", ip)

    assert result.status == "pass", result.message
    assert result.runs[0].label == "emit_protocol_assertions"
    assert "assertions: 2" in result.message
    assert (ip_dir / "verify" / "protocol_assertions.sva").is_file()
    summary = json.loads((ip_dir / "verify" / "protocol_assertions.summary.json").read_text(encoding="utf-8"))
    assert summary["assertions_total"] == 2


def test_common_stage_engine_writes_disk_truth_log_for_fl_model(tmp_path: Path):
    ip = "common_engine_probe"
    _write_ssot(tmp_path, ip)

    result = WorkflowStageEngine(tmp_path).run_stage("ssot-fl-model", ip)

    assert result.status == "pass", result.message
    assert "[ssot-fl-model] generic SSOT-driven FL model stage" in result.message
    log_path = tmp_path / ip / "logs" / "stage_engine" / "ssot-fl-model.json"
    assert log_path.is_file()
    log = json.loads(log_path.read_text(encoding="utf-8"))
    assert log["stage"] == "ssot-fl-model"
    assert log["workflow"] == "fl-model-gen"
    assert log["ip"] == ip


def test_common_stage_engine_runs_cycle_model_and_dual_fcov_stages(tmp_path: Path):
    ip = "common_engine_cl_probe"
    _write_ssot(tmp_path, ip)

    cycle = WorkflowStageEngine(tmp_path).run_stage("ssot-cycle-model", ip)
    dual = WorkflowStageEngine(tmp_path).run_stage("ssot-dual-fcov", ip)

    assert cycle.status == "pass", cycle.message
    assert dual.status == "pass", dual.message
    assert (tmp_path / ip / "model" / "functional_model.py").is_file()
    assert (tmp_path / ip / "cov" / "fl_fcov_plan.json").is_file()
    assert (tmp_path / ip / "cov" / "fcov_plan.json").is_file()


def test_rtl_manifest_progress_rejects_flattened_top_when_ssot_submodules_missing(tmp_path: Path):
    ip = "manifest_probe"
    ip_dir = tmp_path / ip
    (ip_dir / "rtl").mkdir(parents=True)
    (ip_dir / "list").mkdir(parents=True)
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        "`default_nettype none\n\n"
        f"module {ip}(input wire clk, output reg done);\n"
        "  reg [7:0] count_q;\n"
        "  always @(posedge clk) begin\n"
        "    count_q <= count_q + 8'd1;\n"
        "    done <= count_q[7];\n"
        "  end\n"
        "endmodule\n\n"
        "`default_nettype wire\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\n", encoding="utf-8")
    doc = {
        "top_module": {"name": ip},
        "sub_modules": [
            {"name": f"{ip}_unit_a", "file": f"rtl/{ip}_unit_a.sv"},
            {"name": ip, "file": f"rtl/{ip}.sv"},
        ],
    }

    progress = _rtl_manifest_progress(ip_dir, doc)

    assert progress["status"] == "partial"
    assert progress["approved"] == 1
    assert progress["total"] == 2
    missing = [item for item in progress["modules"] if item["status"] != "approved"]
    assert missing[0]["file"] == f"rtl/{ip}_unit_a.sv"


def test_rtl_manifest_progress_rejects_disconnected_manifest_child(tmp_path: Path):
    ip = "manifest_hierarchy_probe"
    ip_dir = tmp_path / ip
    (ip_dir / "rtl").mkdir(parents=True)
    (ip_dir / "list").mkdir(parents=True)
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        "`default_nettype none\n\n"
        f"module {ip}(input wire clk, output wire done);\n"
        "  reg done_q;\n"
        "  always @(posedge clk) begin\n"
        "    done_q <= ~done_q;\n"
        "  end\n"
        "  assign done = done_q;\n"
        "endmodule\n\n"
        "`default_nettype wire\n"
        + ("// top filler\n" * 12),
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}_unit_a.sv").write_text(
        "`default_nettype none\n\n"
        f"module {ip}_unit_a(input wire clk, output wire child_done);\n"
        "  reg child_done_q;\n"
        "  always @(posedge clk) begin\n"
        "    child_done_q <= ~child_done_q;\n"
        "  end\n"
        "  assign child_done = child_done_q;\n"
        "endmodule\n\n"
        "`default_nettype wire\n"
        + ("// child filler\n" * 12),
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\nrtl/{ip}_unit_a.sv\n", encoding="utf-8")
    doc = {
        "top_module": {"name": ip},
        "sub_modules": [
            {"name": ip, "file": f"rtl/{ip}.sv", "ownership": "manifest"},
            {"name": f"{ip}_unit_a", "file": f"rtl/{ip}_unit_a.sv", "ownership": "manifest"},
        ],
    }

    progress = _rtl_manifest_progress(ip_dir, doc)

    assert progress["status"] == "partial"
    assert progress["hierarchy_issue_count"] == 1
    child = next(item for item in progress["modules"] if item["name"] == f"{ip}_unit_a")
    assert child["status"] == "partial"
    assert "not reachable from the top RTL hierarchy" in child["quality_issues"][0]


def test_rtl_manifest_progress_accepts_reachable_manifest_child(tmp_path: Path):
    ip = "manifest_hierarchy_pass"
    ip_dir = tmp_path / ip
    (ip_dir / "rtl").mkdir(parents=True)
    (ip_dir / "list").mkdir(parents=True)
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        "`default_nettype none\n\n"
        f"module {ip}(input wire clk, output wire done);\n"
        "  wire child_done;\n"
        f"  {ip}_unit_a u_unit_a(.clk(clk), .child_done(child_done));\n"
        "  assign done = child_done;\n"
        "endmodule\n\n"
        "`default_nettype wire\n"
        + ("// top filler\n" * 12),
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}_unit_a.sv").write_text(
        "`default_nettype none\n\n"
        f"module {ip}_unit_a(input wire clk, output wire child_done);\n"
        "  reg child_done_q;\n"
        "  always @(posedge clk) begin\n"
        "    child_done_q <= ~child_done_q;\n"
        "  end\n"
        "  assign child_done = child_done_q;\n"
        "endmodule\n\n"
        "`default_nettype wire\n"
        + ("// child filler\n" * 12),
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\nrtl/{ip}_unit_a.sv\n", encoding="utf-8")
    doc = {
        "top_module": {"name": ip},
        "sub_modules": [
            {"name": ip, "file": f"rtl/{ip}.sv", "ownership": "manifest"},
            {"name": f"{ip}_unit_a", "file": f"rtl/{ip}_unit_a.sv", "ownership": "manifest"},
        ],
    }

    progress = _rtl_manifest_progress(ip_dir, doc)

    assert progress["status"] == "pass"
    assert progress["hierarchy_issue_count"] == 0
    assert f"{ip}_unit_a" in progress["hierarchy"]["reachable_modules"]


def test_coverage_stage_requires_sim_evidence_and_preserves_raw_functional_bins(tmp_path: Path):
    ip = "coverage_probe"
    _write_coverage_ready_fixture(tmp_path, ip)

    result = WorkflowStageEngine(tmp_path).run_stage("coverage", ip)

    assert result.status == "pass", result.message
    ip_dir = tmp_path / ip
    assert (ip_dir / "cov" / "coverage_functional.json").is_file()
    coverage = json.loads((ip_dir / "cov" / "coverage.json").read_text(encoding="utf-8"))
    assert coverage["source"] == "ssot_coverage_summary"
    assert coverage["status"] == "pass"
    assert coverage["planned_bins"] == ["FCOV_DOUBLE"]
    assert coverage["functional"] == {"hit": 1, "total": 1, "pct": 100.0}
    assert coverage["functional_bins"]["FCOV_DOUBLE"]["hit"] is True
    assert coverage["limitations"] == {}
    plan = json.loads((ip_dir / "cov" / "coverage_todo_plan.json").read_text(encoding="utf-8"))
    assert plan["schema_version"] == "golden_todo_stage.v1"
    assert plan["approval_policy"] == "evidence_required"
    assert plan["gate"]["approval_state"] == "approved"
    assert plan["todo_completion"]["all_required_todos_pass"] is True
    assert plan["tasks"][0]["id"] == "COV-0001"
    assert plan["tasks"][0]["todo_completion"]["status"] == "pass"
    assert f"{ip}/cov/coverage.json" in plan["tasks"][0]["required_evidence"]
    tracker = json.loads((ip_dir / "todo" / "coverage_todo_tracker.json").read_text(encoding="utf-8"))
    assert tracker["source_plan"] == "cov/coverage_todo_plan.json"
    assert tracker["tasks"][0]["source_id"] == "COV-0001"


def test_lint_stage_writes_evidence_todo_plan(tmp_path: Path, monkeypatch):
    ip = "lint_todo_probe"
    _write_ssot(tmp_path, ip)
    engine = WorkflowStageEngine(tmp_path)

    def _fake_run_tool(label: str, command: list[str], timeout_s: int = 180) -> ToolRun:
        return ToolRun(label=label, command=command, returncode=0, stdout="lint clean")

    monkeypatch.setattr(engine, "_run_tool", _fake_run_tool)

    result = engine.run_stage("lint", ip)

    assert result.status == "pass", result.message
    ip_dir = tmp_path / ip
    plan = json.loads((ip_dir / "lint" / "lint_todo_plan.json").read_text(encoding="utf-8"))
    assert plan["stage"] == "lint"
    assert plan["workflow"] == "lint"
    assert plan["tasks"][0]["approval_state"] == "approved"
    assert plan["tasks"][0]["approval_policy"] == "evidence_required"
    assert plan["tasks"][0]["todo_completion"]["status"] == "pass"
    tracker = json.loads((ip_dir / "todo" / "lint_todo_tracker.json").read_text(encoding="utf-8"))
    assert tracker["source_plan"] == "lint/lint_todo_plan.json"
    assert tracker["tasks"][0]["source_id"] == "LINT-0001"
    assert f"{ip}/todo/lint_todo_tracker.json" in result.artifacts


def test_tb_stage_writes_human_review_todo_plan_for_blocked_contract(tmp_path: Path, monkeypatch):
    ip = "tb_human_gate_probe"
    _write_ssot(tmp_path, ip)
    ip_dir = tmp_path / ip
    blocked_path = ip_dir / "tb" / "cocotb" / "tb_blocked.json"
    blocked_path.parent.mkdir(parents=True, exist_ok=True)
    blocked_path.write_text(
        json.dumps(
            {
                "reason": "SSOT/RTL contract decision required",
                "next_action": "approve signal naming policy",
                "questions": [{"id": "TBQ-1", "decision_needed": "Which reset polarity should TB drive?"}],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    engine = WorkflowStageEngine(tmp_path)

    def _fake_run_tool(label: str, command: list[str], timeout_s: int = 180) -> ToolRun:
        return ToolRun(label=label, command=command, returncode=0, stdout=f"{label} ok")

    monkeypatch.setattr(engine, "_run_tool", _fake_run_tool)

    result = engine.run_stage("ssot-tb-cocotb", ip)

    assert result.status == "human_gate", result.message
    plan = json.loads((ip_dir / "tb" / "tb_todo_plan.json").read_text(encoding="utf-8"))
    assert plan["stage"] == "ssot-tb-cocotb"
    assert plan["workflow"] == "tb-gen"
    assert plan["gate"]["approval_state"] == "human_review_needed"
    assert plan["human_review_needed"][0]["id"] == "TBQ-1"
    assert plan["tasks"][0]["todo_completion"]["status"] == "open"
    tracker = json.loads((ip_dir / "todo" / "tb_todo_tracker.json").read_text(encoding="utf-8"))
    assert tracker["tasks"][0]["status"] == "human_review_needed"


def test_sim_stage_writes_blocked_todo_plan_without_runner(tmp_path: Path):
    ip = "sim_blocked_todo_probe"

    result = WorkflowStageEngine(tmp_path).run_stage("sim", ip)

    assert result.status == "blocked", result.message
    ip_dir = tmp_path / ip
    plan = json.loads((ip_dir / "sim" / "sim_todo_plan.json").read_text(encoding="utf-8"))
    assert plan["stage"] == "sim"
    assert plan["gate"]["approval_state"] == "blocked"
    assert plan["tasks"][0]["id"] == "SIM-0001"
    assert plan["tasks"][0]["todo_completion"]["status"] == "open"
    tracker = json.loads((ip_dir / "todo" / "sim_todo_tracker.json").read_text(encoding="utf-8"))
    assert tracker["source_plan"] == "sim/sim_todo_plan.json"


def test_coverage_stage_reports_function_and_cycle_model_coverage_separately(tmp_path: Path):
    ip = "coverage_model_split_probe"
    _write_coverage_ready_fixture(tmp_path, ip)
    ip_dir = tmp_path / ip
    ssot_path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    doc = yaml.safe_load(ssot_path.read_text(encoding="utf-8"))
    doc["test_requirements"]["coverage_goals"] = {
        "function": {
            "target_pct": 100,
            "model": "function_model",
            "bins": [
                {
                    "id": "FCOV_DOUBLE",
                    "source_ref": "function_model.transactions.FM_DOUBLE",
                    "class": "transaction",
                }
            ],
        },
        "cycle": {
            "target_pct": 100,
            "model": "cycle_model",
            "bins": [
                {
                    "id": "CCOV_LATENCY_ONE",
                    "source_ref": "cycle_model.latency",
                    "class": "latency",
                }
            ],
        },
    }
    ssot_path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    fcov_plan = json.loads((ip_dir / "cov" / "fcov_plan.json").read_text(encoding="utf-8"))
    fcov_plan["bins"][0]["coverage_domain"] = "function"
    fcov_plan["bins"].append(
        {
            "id": "CCOV_LATENCY_ONE",
            "class": "latency",
            "coverage_domain": "cycle",
            "goal_id": "EQ_DOUBLE",
            "source": "cycle_model.latency",
        }
    )
    (ip_dir / "cov" / "fcov_plan.json").write_text(json.dumps(fcov_plan, indent=2) + "\n", encoding="utf-8")
    functional = json.loads((ip_dir / "cov" / "coverage_functional.json").read_text(encoding="utf-8"))
    functional["functional"]["bins"]["CCOV_LATENCY_ONE"] = {
        "hit": True,
        "goal_id": "EQ_DOUBLE",
        "scenario_id": "SC_DOUBLE",
    }
    (ip_dir / "cov" / "coverage_functional.json").write_text(json.dumps(functional, indent=2) + "\n", encoding="utf-8")
    goals = json.loads((ip_dir / "verify" / "equivalence_goals.json").read_text(encoding="utf-8"))
    goals["goals"][0]["coverage_refs"] = ["FCOV_DOUBLE", "CCOV_LATENCY_ONE"]
    (ip_dir / "verify" / "equivalence_goals.json").write_text(json.dumps(goals, indent=2) + "\n", encoding="utf-8")
    row = json.loads((ip_dir / "sim" / "scoreboard_events.jsonl").read_text(encoding="utf-8"))
    row["coverage_refs"] = ["FCOV_DOUBLE", "CCOV_LATENCY_ONE"]
    (ip_dir / "sim" / "scoreboard_events.jsonl").write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")

    result = WorkflowStageEngine(tmp_path).run_stage("coverage", ip)

    assert result.status == "pass", result.message
    coverage = json.loads((ip_dir / "cov" / "coverage.json").read_text(encoding="utf-8"))
    assert coverage["function_coverage"]["hit"] == 1
    assert coverage["function_coverage"]["total"] == 1
    assert coverage["function_coverage"]["pct"] == 100.0
    assert coverage["cycle_coverage"]["hit"] == 1
    assert coverage["cycle_coverage"]["total"] == 1
    assert coverage["cycle_coverage"]["pct"] == 100.0
    assert coverage["functional_bins"]["FCOV_DOUBLE"]["coverage_domain"] == "function"
    assert coverage["functional_bins"]["CCOV_LATENCY_ONE"]["coverage_domain"] == "cycle"
    assert coverage["coverage_model"]["function"]["source"] == "function_model"
    assert coverage["coverage_model"]["cycle"]["source"] == "cycle_model"


def test_coverage_stage_merges_case_variant_ssot_and_fcov_bins(tmp_path: Path):
    ip = "coverage_case_alias_probe"
    _write_coverage_ready_fixture(tmp_path, ip)
    ip_dir = tmp_path / ip
    ssot_path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    doc = yaml.safe_load(ssot_path.read_text(encoding="utf-8"))
    doc["test_requirements"]["coverage_goals"] = {
        "function": {
            "target_pct": 100,
            "model": "function_model",
            "bins": [
                {
                    "id": "FCOV_DOUBLE",
                    "source_ref": "function_model.transactions.FM_DOUBLE",
                    "class": "transaction",
                }
            ],
        },
        "cycle": {
            "target_pct": 100,
            "model": "cycle_model",
            "bins": [
                {
                    "id": "CCOV_LATENCY_ONE",
                    "source_ref": "cycle_model.latency",
                    "class": "latency",
                }
            ],
        },
    }
    ssot_path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    (ip_dir / "cov" / "fcov_plan.json").write_text(
        json.dumps(
            {
                "planned_before_rtl": True,
                "bins": [
                    {
                        "id": "fcov_double",
                        "class": "transaction",
                        "coverage_domain": "function",
                        "source_ref": "function_model.transactions.FM_DOUBLE",
                    },
                    {
                        "id": "ccov_latency_one",
                        "class": "latency",
                        "coverage_domain": "cycle",
                        "source_ref": "cycle_model.latency",
                    },
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    functional = json.loads((ip_dir / "cov" / "coverage_functional.json").read_text(encoding="utf-8"))
    functional["functional"]["bins"] = {
        "fcov_double": {"hit": True, "goal_id": "EQ_DOUBLE", "scenario_id": "SC_DOUBLE"},
        "ccov_latency_one": {"hit": True, "goal_id": "EQ_DOUBLE", "scenario_id": "SC_DOUBLE"},
    }
    (ip_dir / "cov" / "coverage_functional.json").write_text(json.dumps(functional, indent=2) + "\n", encoding="utf-8")
    goals = json.loads((ip_dir / "verify" / "equivalence_goals.json").read_text(encoding="utf-8"))
    goals["goals"][0]["coverage_refs"] = ["fcov_double", "ccov_latency_one"]
    (ip_dir / "verify" / "equivalence_goals.json").write_text(json.dumps(goals, indent=2) + "\n", encoding="utf-8")
    row = json.loads((ip_dir / "sim" / "scoreboard_events.jsonl").read_text(encoding="utf-8"))
    row["coverage_refs"] = ["fcov_double", "ccov_latency_one"]
    (ip_dir / "sim" / "scoreboard_events.jsonl").write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")

    result = WorkflowStageEngine(tmp_path).run_stage("coverage", ip)

    assert result.status == "pass", result.message
    coverage = json.loads((ip_dir / "cov" / "coverage.json").read_text(encoding="utf-8"))
    assert coverage["planned_bins"] == ["fcov_double", "ccov_latency_one"]
    assert coverage["function_coverage"]["total"] == 1
    assert coverage["cycle_coverage"]["total"] == 1
    assert coverage["limitations"] == {}


def test_coverage_stage_rejects_raw_functional_bins_without_rtl_observed_scoreboard(tmp_path: Path):
    ip = "coverage_raw_only_probe"
    _write_coverage_ready_fixture(tmp_path, ip)
    ip_dir = tmp_path / ip
    (ip_dir / "sim" / "scoreboard_events.jsonl").unlink()

    result = WorkflowStageEngine(tmp_path).run_stage("coverage", ip)

    assert result.status == "blocked"
    coverage = json.loads((ip_dir / "cov" / "coverage.json").read_text(encoding="utf-8"))
    assert coverage["status"] == "blocked"
    assert coverage["functional"] == {"hit": 0, "total": 1, "pct": 0.0}
    assert coverage["raw_functional"]["pct"] == 100.0
    assert coverage["functional_bins"]["FCOV_DOUBLE"]["raw_hit"] is True
    assert "rtl_observed_coverage" in coverage["limitations"]


def test_coverage_stage_accepts_ssot_functional_fsm_bins_for_fsm_goal(tmp_path: Path):
    ip = "coverage_fsm_probe"
    _write_coverage_ready_fixture(tmp_path, ip)
    ip_dir = tmp_path / ip
    ssot_path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    ssot_path.write_text(
        ssot_path.read_text(encoding="utf-8").replace(
            "    planned_bins:\n",
            "    fsm: FSM coverage >= 100%\n"
            "    planned_bins:\n",
        ),
        encoding="utf-8",
    )
    fcov_plan = json.loads((ip_dir / "cov" / "fcov_plan.json").read_text(encoding="utf-8"))
    fcov_plan["bins"].append(
        {
            "id": "fsm_control_idle_to_accept",
            "class": "fsm",
            "goal_id": "EQ_FSM_IDLE_ACCEPT",
            "source": "test_requirements.coverage_goals.fsm",
        }
    )
    (ip_dir / "cov" / "fcov_plan.json").write_text(json.dumps(fcov_plan, indent=2) + "\n", encoding="utf-8")
    functional = json.loads((ip_dir / "cov" / "coverage_functional.json").read_text(encoding="utf-8"))
    functional["functional"]["bins"]["fsm_control_idle_to_accept"] = {
        "hit": True,
        "goal_id": "EQ_FSM_IDLE_ACCEPT",
        "scenario_id": "SC_DOUBLE",
    }
    (ip_dir / "cov" / "coverage_functional.json").write_text(json.dumps(functional, indent=2) + "\n", encoding="utf-8")
    goals = json.loads((ip_dir / "verify" / "equivalence_goals.json").read_text(encoding="utf-8"))
    goals["goals"][0]["coverage_refs"] = ["FCOV_DOUBLE", "fsm_control_idle_to_accept"]
    (ip_dir / "verify" / "equivalence_goals.json").write_text(json.dumps(goals, indent=2) + "\n", encoding="utf-8")
    row = json.loads((ip_dir / "sim" / "scoreboard_events.jsonl").read_text(encoding="utf-8"))
    row["coverage_refs"] = ["FCOV_DOUBLE", "fsm_control_idle_to_accept"]
    (ip_dir / "sim" / "scoreboard_events.jsonl").write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")

    result = WorkflowStageEngine(tmp_path).run_stage("coverage", ip)

    assert result.status == "pass", result.message
    coverage = json.loads((ip_dir / "cov" / "coverage.json").read_text(encoding="utf-8"))
    assert coverage["fsm_state"]["meets_target"] is True
    assert coverage["fsm_state"]["pct"] == 100.0
    assert coverage["limitations"] == {}


def _write_dynamic_todo_ssot(root: Path, ip: str, *, include_function: bool = True, include_cycle: bool = True) -> None:
    ip_dir = root / ip
    (ip_dir / "yaml").mkdir(parents=True, exist_ok=True)
    parts = [
        "top_module:",
        f"  name: {ip}",
        "sub_modules:",
        f"  - name: {ip}_core",
        f"    file: rtl/{ip}.sv",
        "    ownership: manifest",
        "    implements: [function_model, cycle_model, registers, dataflow, fsm]",
        "    source_sections: [function_model, cycle_model, registers, dataflow, fsm]",
        "    function_model_refs: [function_model]",
        "    cycle_model_refs: [cycle_model]",
        "    register_refs: [registers]",
        "    dataflow_refs: [dataflow]",
        "    fsm_refs: [fsm]",
        "parameters:",
        "  - name: DATA_WIDTH",
        "    default: 8",
        "io_list:",
        "  clock_domains:",
        "    - name: main",
        "      ports:",
        "        - {name: clk, direction: input, width: 1}",
        "  resets:",
        "    - name: rst_n",
        "      ports:",
        "        - {name: rst_n, direction: input, width: 1}",
        "  interfaces:",
        "    - name: cmd",
        "      ports:",
        "        - {name: valid, direction: input, width: 1}",
        "        - {name: ready, direction: output, width: 1}",
        "        - {name: data_in, direction: input, width: 8}",
        "        - {name: result, direction: output, width: 9}",
        "features:",
        "  - name: command_accept",
        "  - name: result_status",
        "dataflow:",
        "  sequence:",
        "    - sample command",
        "    - compute result",
        "    - publish response",
        "  ordering:",
        "    - response follows accepted command",
    ]
    if include_function:
        parts += [
            "function_model:",
            "  state_variables:",
            "    - {name: accepted_count, width: 8, reset: 0}",
            "    - {name: error_sticky, width: 1, reset: 0}",
            "  transactions:",
            "    - id: FM_ACCEPT",
            "      name: accept_command",
            "      preconditions: [valid and ready]",
            "      outputs: [result, result_valid]",
            "      output_rules:",
            "        - {name: result, port: result, expr: value * 2, width: 9}",
            "        - {name: result_valid, port: result_valid, expr: 1, width: 1}",
            "      state_updates:",
            "        - {name: accepted_count, expr: accepted_count + 1, width: 8}",
            "      side_effects: [clear pending response]",
            "    - id: FM_ERROR",
            "      name: detect_error",
            "      preconditions: [illegal_command]",
            "      outputs: [error]",
            "      output_rules:",
            "        - {name: error, port: error, expr: 1, width: 1}",
            "      state_updates:",
            "        - {name: error_sticky, expr: 1, width: 1}",
            "      error_cases: [bad_opcode]",
            "  invariants:",
            "    - reset clears visible status",
            "    - one response per accepted command",
        ]
    if include_cycle:
        parts += [
            "cycle_model:",
            "  clock: clk",
            "  reset: rst_n",
            "  latency: 1",
            "  handshake_rules:",
            "    - {name: valid_ready_accept, signal: valid}",
            "    - {name: hold_result_until_ready, signal: ready}",
            "  pipeline:",
            "    - {stage: S0_ACCEPT, cycle: 0}",
            "    - {stage: S1_EXECUTE, cycle: 1}",
            "    - {stage: S2_RESPONSE, cycle: 2}",
            "  ordering:",
            "    - command order preserved",
            "    - error response does not bypass normal response",
            "  backpressure:",
            "    - ready low stalls command acceptance",
        ]
    parts += [
        "registers:",
        "  register_list:",
        "    - name: CTRL",
        "      offset: 0x0",
        "      fields:",
        "        - {name: enable, access: rw, reset: 0}",
        "        - {name: irq_enable, access: rw, reset: 0}",
        "    - name: STATUS",
        "      offset: 0x4",
        "      fields:",
        "        - {name: busy, access: ro, reset: 0}",
        "        - {name: error, access: w1c, reset: 0}",
        "memory:",
        "  instances:",
        "    - {name: fifo, depth: 4, width: 8}",
        "interrupts:",
        "  sources:",
        "    - {name: done_irq, clear: w1c}",
        "fsm:",
        "  control:",
        "    states: [IDLE, EXECUTE, RESP]",
        "    transitions:",
        "      - {from: IDLE, to: EXECUTE, condition: valid}",
        "      - {from: EXECUTE, to: RESP, condition: done}",
        "test_requirements:",
        "  scenarios:",
        "    - {id: SC_ACCEPT, expected: result matches FL}",
        "    - {id: SC_ERROR, expected: error sticky is set}",
        "  coverage_goals:",
        "    planned_bins:",
        "      - {id: FCOV_ACCEPT}",
        "      - {id: FCOV_ERROR}",
        "      - {id: FCOV_BACKPRESSURE}",
        "workflow_todos:",
        "  rtl-gen:",
        "    - id: RTL_ACCEPT_PIPELINE",
        "      content: Implement accepted command response pipeline from SSOT todo",
        "      detail: Preserve valid/ready accepted command data through execute and response stages before asserting result_valid.",
        "      criteria:",
        "        - pipeline register captures data_in only on valid and ready",
        "        - result_valid asserts only when result corresponds to captured value",
        "      source_refs:",
        "        - function_model.transactions.FM_ACCEPT",
        "        - cycle_model.pipeline.S1_EXECUTE",
        f"      owner_module: {ip}_core",
        f"      owner_file: rtl/{ip}.sv",
        "      priority: high",
        "      required: true",
    ]
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text("\n".join(parts) + "\n", encoding="utf-8")


def _write_reference_profile_candidate(ip_dir: Path) -> None:
    reports_dir = ip_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "rtl_reference_profile.json").write_text(
        json.dumps(
            {
                "type": "rtl_reference_profile",
                "label": "candidate_reference",
                "summary": {
                    "file_count": 4,
                    "lines": 400,
                    "modules": 5,
                    "always_blocks": 8,
                    "assigns": 12,
                    "case_blocks": 2,
                    "instance_candidates": 7,
                    "state_updates": 20,
                },
                "suggested_ssot_target_scale": {
                    "source_files_min": 4,
                    "modules_min": 5,
                    "procedural_blocks_min": 8,
                    "state_updates_min": 20,
                    "depth_score_min": 64,
                },
                "guidance": {
                    "calibration_only": True,
                    "do_not_copy_reference_rtl": True,
                },
            }
        ),
        encoding="utf-8",
    )


def test_rtl_reference_profile_is_calibration_only_and_loaded_by_todo_plan(tmp_path: Path):
    ip = "reference_profile_probe"
    _write_dynamic_todo_ssot(tmp_path, ip)
    reference = tmp_path / "reference_rtl"
    reference.mkdir()
    (reference / "top.sv").write_text(
        "module top(input wire clk, input wire a, output wire y);\n"
        "  reg [1:0] state_q;\n"
        "  always @(posedge clk) begin\n"
        "    case (state_q)\n"
        "      2'd0: state_q <= 2'd1;\n"
        "      default: state_q <= 2'd0;\n"
        "    endcase\n"
        "  end\n"
        "  child u_child(.clk(clk), .a(a), .y(y));\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (reference / "child.v.xsl").write_text(
        "module child(input wire clk, input wire a, output wire y);\n"
        "  reg y_q;\n"
        "  always @(posedge clk) begin\n"
        "    y_q <= a;\n"
        "  end\n"
        "  assign y = y_q;\n"
        "  assign unused_constant = 1'b0;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    profile_path = tmp_path / ip / "reports" / "rtl_reference_profile.json"

    profile_result = subprocess.run(
        [
            sys.executable,
            str(PROFILE_RTL_REFERENCE),
            str(reference),
            "--label",
            "small_reference",
            "--output",
            str(profile_path),
        ],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert profile_result.returncode == 0, profile_result.stderr or profile_result.stdout
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    assert profile["type"] == "rtl_reference_profile"
    assert profile["guidance"]["calibration_only"] is True
    assert profile["guidance"]["do_not_copy_reference_rtl"] is True
    assert profile["summary"]["file_count"] == 2
    assert profile["summary"]["modules"] == 2
    assert profile["summary"]["always_blocks"] == 2
    assert profile["summary"]["assigns"] == 2
    assert profile["summary"]["nonconstant_assigns"] == 1
    assert profile["summary"]["case_blocks"] == 1
    assert profile["summary"]["state_updates"] == 3
    assert profile["target_candidate_basis"] == "design_candidate"
    assert profile["target_candidate_summary"]["file_count"] == 2
    assert profile["top_by_lines"][0]["path"] == "top.sv"
    assert profile["suggested_ssot_target_scale"]["source_files_min"] == 2
    assert profile["suggested_ssot_target_scale"]["modules_min"] == 2
    assert profile["suggested_ssot_target_scale"]["lines_min"] == 18
    assert profile["suggested_ssot_target_scale"]["procedural_blocks_min"] == 2
    assert profile["suggested_ssot_target_scale"]["nonconstant_assigns_min"] == 1

    derive_result = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert derive_result.returncode == 0, derive_result.stderr or derive_result.stdout
    plan = json.loads((tmp_path / ip / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    authoring = json.loads((tmp_path / ip / "rtl" / "rtl_authoring_plan.json").read_text(encoding="utf-8"))
    assert plan["summary"]["reference_profile_present"] is True
    assert plan["reference_profile"]["path"] == "reports/rtl_reference_profile.json"
    assert plan["reference_profile"]["summary"]["modules"] == 2
    assert plan["reference_profile"]["target_candidate_basis"] == "design_candidate"
    assert plan["reference_profile"]["target_candidate_summary"]["lines"] == 18
    assert plan["reference_profile"]["suggested_ssot_target_scale"]["modules_min"] == 2
    assert plan["policy"]["reference_profile_rule"].startswith("Optional rtl_reference_profile")
    assert authoring["summary"]["reference_profile_present"] is True
    assert authoring["reference_profile"]["guidance"]["do_not_copy_reference_rtl"] is True
    assert authoring["reference_profile"]["target_candidate_summary"]["modules"] == 2
    module_packet = next(packet for packet in authoring["packets"] if packet["kind"] == "module")
    module_packet_data = json.loads((tmp_path / ip / module_packet["json"]).read_text(encoding="utf-8"))
    assert module_packet_data["context"]["reference_profile"]["target_candidate_basis"] == "design_candidate"
    assert module_packet_data["context"]["reference_profile"]["target_candidate_summary"]["lines"] == 18
    assert module_packet_data["context"]["reference_profile"]["suggested_ssot_target_scale"]["lines_min"] == 18

    (tmp_path / ip / "list").mkdir(exist_ok=True)
    (tmp_path / ip / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input wire clk, input wire valid, output wire ready, output wire [8:0] result);\n"
        "  reg [8:0] result_q;\n"
        "  always @(posedge clk) begin\n"
        "    if (valid) begin\n"
        "      result_q <= result_q + 9'd1;\n"
        "    end\n"
        "  end\n"
        "  assign ready = valid;\n"
        "  assign result = result_q;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (tmp_path / ip / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\n", encoding="utf-8")
    audit_result = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert audit_result.returncode in {0, 1}, audit_result.stderr or audit_result.stdout
    audited_plan = json.loads((tmp_path / ip / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    audited_authoring = json.loads((tmp_path / ip / "rtl" / "rtl_authoring_plan.json").read_text(encoding="utf-8"))
    comparison = audited_plan["rtl_implementation_depth_evidence"]["reference_comparison"]
    assert comparison["status"] == "diagnostic_only"
    assert comparison["calibration_only"] is True
    assert comparison["ratios"]["source_files"]["current"] == 1
    assert comparison["ratios"]["source_files"]["reference"] == 2
    gap = audited_plan["reference_scale_gap"]
    assert gap["status"] == "diagnostic_only"
    assert gap["metrics"]["source_files"]["percent"] == 50.0
    assert gap["metrics"]["source_files"]["current"] == 1
    assert gap["metrics"]["source_files"]["reference"] == 2
    assert audited_authoring["summary"]["reference_scale_gap_present"] is True
    assert audited_authoring["reference_scale_gap"]["metrics"]["source_files"]["percent"] == 50.0
    assert (tmp_path / ip / "rtl" / "reference_scale_gap.json").is_file()
    status_md = (tmp_path / ip / "rtl" / "rtl_authoring_status.md").read_text(encoding="utf-8")
    assert "Reference scale gap" in status_md


def test_rtl_reference_profile_excludes_validation_from_target_candidate(tmp_path: Path):
    reference = tmp_path / "reference_rtl"
    (reference / "design").mkdir(parents=True)
    (reference / "validation" / "tb").mkdir(parents=True)
    (reference / "design" / "dma_core.sv").write_text(
        "module dma_core(input wire clk, output wire done);\n"
        "  reg state;\n"
        "  always @(posedge clk) begin\n"
        "    state <= ~state;\n"
        "  end\n"
        "  assign done = state;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (reference / "validation" / "tb" / "dma_core_tb.sv").write_text(
        "module dma_core_tb;\n"
        "  reg clk;\n"
        "  always begin\n"
        "    clk <= ~clk;\n"
        "  end\n"
        "endmodule\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(PROFILE_RTL_REFERENCE), str(reference), "--label", "mixed_reference"],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    profile = json.loads(result.stdout)
    assert profile["summary"]["file_count"] == 2
    assert profile["bucket_summaries"]["verification_collateral"]["file_count"] == 1
    assert profile["target_candidate_summary"]["file_count"] == 1
    assert profile["suggested_ssot_target_scale"]["source_files_min"] == 1
    assert profile["suggested_ssot_target_scale"]["modules_min"] == 1
    assert profile["guidance"]["target_candidate_rule"].startswith("suggested_ssot_target_scale is derived")
    buckets = {item["path"]: item["bucket"] for item in profile["top_by_lines"]}
    assert buckets["validation/tb/dma_core_tb.sv"] == "verification_collateral"

    spec = importlib.util.spec_from_file_location("derive_rtl_todos_for_test", DERIVE_RTL_TODOS)
    assert spec and spec.loader
    derive = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(derive)
    comparison = derive._rtl_reference_comparison(  # type: ignore[attr-defined]
        {
            "source_files": 1,
            "lines": profile["target_candidate_summary"]["lines"],
            "modules": 1,
            "procedural_blocks": 1,
            "nonconstant_assigns": 1,
            "control_flow": 0,
            "instances": 0,
            "state_updates": 1,
        },
        profile,
    )
    assert comparison["reference_basis"] == "design_candidate"
    assert comparison["ratios"]["source_files"]["reference"] == 1
    assert comparison["ratios"]["lines"]["reference"] == profile["target_candidate_summary"]["lines"]


def test_rtl_todo_hash_volatile_keys_match_across_workflow_tools():
    from src.headless_workflow import RTL_TODO_HASH_VOLATILE_KEYS as headless_keys

    derive_spec = importlib.util.spec_from_file_location("derive_rtl_todos_hash_keys_for_test", DERIVE_RTL_TODOS)
    assert derive_spec and derive_spec.loader
    derive = importlib.util.module_from_spec(derive_spec)
    derive_spec.loader.exec_module(derive)

    ssot_spec = importlib.util.spec_from_file_location("ssot_to_rtl_hash_keys_for_test", SSOT_TO_RTL)
    assert ssot_spec and ssot_spec.loader
    ssot = importlib.util.module_from_spec(ssot_spec)
    ssot_spec.loader.exec_module(ssot)

    expected_generated_diagnostics = {
        "connection_contract_suggestions",
        "reference_profile",
        "reference_scale_gap",
    }
    assert set(derive.RTL_TODO_HASH_VOLATILE_KEYS) == set(headless_keys) == set(ssot.RTL_TODO_HASH_VOLATILE_KEYS)
    assert expected_generated_diagnostics <= set(headless_keys)


def test_sv_instance_parser_ignores_system_function_fragments():
    derive_spec = importlib.util.spec_from_file_location("derive_rtl_todos_instance_parse_for_test", DERIVE_RTL_TODOS)
    assert derive_spec and derive_spec.loader
    derive = importlib.util.module_from_spec(derive_spec)
    derive_spec.loader.exec_module(derive)

    instances = derive._sv_instance_named_port_maps(  # type: ignore[attr-defined]
        """
        localparam int ADDR_W = $clog2(DEPTH);

        child_unit #(
          .WIDTH(WIDTH),
          .DEPTH(DEPTH)
        ) u_child (
          .clk(clk),
          .ready(child_ready)
        );
        """
    )

    assert instances == [
        {
            "module": "child_unit",
            "instance": "u_child",
            "has_named_ports": True,
            "ports": {
                "clk": "clk",
                "ready": "child_ready",
            },
        }
    ]


def test_reference_target_scale_candidate_requires_ssot_lock_or_waiver(tmp_path: Path):
    ip = "target_scale_policy_probe"
    ip_dir = tmp_path / ip
    _write_dynamic_todo_ssot(tmp_path, ip)
    _write_reference_profile_candidate(ip_dir)
    ssot_path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    base_ssot = ssot_path.read_text(encoding="utf-8")

    ssot_path.write_text(
        base_ssot
        + "\nquality_gates:\n"
        + "  rtl_gen:\n"
        + "    profile: production\n"
        + "    target_scale:\n"
        + "      basis: reference profile is still under review\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode in {0, 1}, result.stderr or result.stdout
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    authoring = json.loads((ip_dir / "rtl" / "rtl_authoring_plan.json").read_text(encoding="utf-8"))
    policy_task = next(
        task
        for task in plan["tasks"]
        if (task.get("gate_todo") or {}).get("kind") == "target_scale_policy"
    )
    assert plan["summary"]["target_scale_present"] is False
    assert policy_task["todo_completion"]["status"] == "open"
    assert authoring["execution_policy"]["pass_allowed"] is False
    assert any(
        item.get("gate_kind") == "target_scale_policy"
        for item in authoring["execution_policy"]["blocked_by_locked_truth"]
    )
    gate_packet = next(packet for packet in authoring["packets"] if packet["packet_id"] == "rtl_gate_human_closure")
    assert gate_packet["execution_policy"]["human_locked_open_count"] >= 1
    assert any(
        item.get("gate_kind") == "target_scale_policy"
        for item in gate_packet["execution_policy"]["blocked_by_locked_truth"]
    )
    preflight = subprocess.run(
        [sys.executable, str(SSOT_TO_RTL), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert preflight.returncode == 2
    blocked = json.loads((ip_dir / "rtl" / "rtl_blocked.json").read_text(encoding="utf-8"))
    blocked_ids = {question["id"] for question in blocked["questions"]}
    assert "RTL_TARGET_SCALE_POLICY" in blocked_ids
    target_question = next(question for question in blocked["questions"] if question["id"] == "RTL_TARGET_SCALE_POLICY")
    assert target_question["suggested_ssot_target_scale"]["modules_min"] == 5

    ssot_path.write_text(
        base_ssot
        + "\nquality_gates:\n"
        + "  rtl_gen:\n"
        + "    profile: production\n"
        + "    target_scale:\n"
        + "      basis: locked by architecture review\n"
        + "      source_files_min: 4\n"
        + "      modules_min: 5\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode in {0, 1}, result.stderr or result.stdout
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    policy_task = next(
        task
        for task in plan["tasks"]
        if (task.get("gate_todo") or {}).get("kind") == "target_scale_policy"
    )
    assert plan["summary"]["target_scale_present"] is True
    assert plan["policy"]["rtl_target_scale"]["min_source_files"] == 4
    assert policy_task["todo_completion"]["status"] == "pass"

    ssot_path.write_text(
        base_ssot
        + "\nquality_gates:\n"
        + "  rtl_gen:\n"
        + "    profile: production\n"
        + "    target_scale_waiver:\n"
        + "      approved: true\n"
        + "      reason: smaller IP variant intentionally does not enforce reference scale\n"
        + "      owner: human-review\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode in {0, 1}, result.stderr or result.stdout
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    policy_task = next(
        task
        for task in plan["tasks"]
        if (task.get("gate_todo") or {}).get("kind") == "target_scale_policy"
    )
    assert plan["summary"]["target_scale_waived"] is True
    assert policy_task["todo_completion"]["status"] == "pass"


def test_dynamic_rtl_todos_scale_from_ssot_complexity(tmp_path: Path):
    ip = "dynamic_todo_probe"
    _write_dynamic_todo_ssot(tmp_path, ip)

    result = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    internal_plan = json.loads((tmp_path / ip / "logs" / "rtl-gen" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    summary = internal_plan["summary"]
    assert summary["total_tasks"] >= 40
    assert summary["by_category"]["function_model.output_rule"] >= 3
    assert summary["by_category"]["cycle_model.handshake_rules"] == 2
    assert summary["by_category"]["registers.field"] == 4
    assert internal_plan["policy"]["fixed_template_role"] == "seed_only"
    assert internal_plan["gate"]["status"] == "planned"
    assert summary["ssot_workflow_todos"] == 1
    assert summary["rtl_gate_todos"] >= 6
    gate_tasks = [task for task in internal_plan["tasks"] if task["category"] == "rtl_gate.rtl_gen"]
    gate_kinds = {task["gate_todo"]["kind"] for task in gate_tasks}
    assert {"dut_compile", "dut_lint", "static_rtl_evidence", "dynamic_todo_closure"}.issubset(gate_kinds)
    assert any(task["source_ref"] == "quality_gates.rtl_gen.dut_compile" for task in gate_tasks)
    disk_plan = json.loads((tmp_path / ip / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    assert disk_plan["summary"]["total_tasks"] == summary["total_tasks"]
    assert disk_plan["gate"]["status"] == "planned"
    template_plan = json.loads((tmp_path / ip / "rtl" / "rtl_todo_tracker.json").read_text(encoding="utf-8"))
    assert template_plan["name"] == f"{ip}-rtl"
    assert template_plan["source_plan"] == "rtl/rtl_todo_plan.json"
    assert template_plan["source_task_count"] == summary["total_tasks"]
    assert template_plan["ui_grouping"]["strategy"] == "flat_ledger_one_todo_per_rtl_task"
    assert template_plan["ui_grouping"]["actual_count"] == len(template_plan["tasks"])
    assert "tasks" in template_plan
    assert len(template_plan["tasks"]) == summary["total_tasks"]
    assert template_plan["ui_grouping"]["target_min"] == len(template_plan["tasks"])
    assert len(template_plan["tasks"]) == template_plan["ui_grouping"]["target_max"]
    assert template_plan["status_counts"] == {"pending": summary["total_tasks"]}
    first_task = template_plan["tasks"][0]
    assert "content" in first_task
    assert "activeForm" in first_task
    assert first_task["status"] == "pending"
    assert "detail" in first_task
    assert "priority" in first_task
    assert "criteria" in first_task
    assert "todo_completion.status is pass after derive_rtl_todos.py --audit-rtl" in first_task["criteria"]
    assert any("function_model" in task["detail"] or "function_model" in task["criteria"] for task in template_plan["tasks"])
    authoring_plan = json.loads((tmp_path / ip / "rtl" / "rtl_authoring_plan.json").read_text(encoding="utf-8"))
    assert authoring_plan["type"] == "rtl_authoring_plan"
    assert authoring_plan["source_plan"] == "rtl/rtl_todo_plan.json"
    assert authoring_plan["packet_dir"] == "rtl/authoring_packets"
    assert authoring_plan["status_markdown"] == "rtl/rtl_authoring_status.md"
    assert authoring_plan["todo_plan_sha256"]
    assert authoring_plan["execution_policy"]["draft_allowed"] is True
    assert authoring_plan["execution_policy"]["pass_allowed"] is False
    assert authoring_plan["execution_policy"]["deferred_human_qa_allowed"] is True
    assert authoring_plan["summary"]["packets"] >= 2
    assert authoring_plan["summary"]["total_tasks"] == summary["total_tasks"]
    assert authoring_plan["summary"]["llm_actionable_packets"] >= 1
    assert authoring_plan["summary"]["llm_actionable_tasks"] >= 1
    assert authoring_plan["summary"]["deferred_human_qa_allowed"] is True
    assert authoring_plan["summary"]["pass_allowed"] is False
    assert authoring_plan["summary"]["recommended_packet_batch_limit"] == 4
    assert authoring_plan["summary"]["next_llm_packets"]
    assert any(packet["kind"] == "module" for packet in authoring_plan["packets"])
    assert any(packet["kind"] == "gate" for packet in authoring_plan["packets"])
    module_packet = next(packet for packet in authoring_plan["packets"] if packet["kind"] == "module")
    assert module_packet["owner_module"]
    module_packet_json = tmp_path / ip / module_packet["json"]
    module_packet_md = tmp_path / ip / module_packet["markdown"]
    assert module_packet_json.is_file()
    assert module_packet_md.is_file()
    module_packet_data = json.loads(module_packet_json.read_text(encoding="utf-8"))
    assert module_packet_data["kind"] == "module"
    assert module_packet_data["source_plan"] == "rtl/rtl_todo_plan.json"
    assert module_packet_data["summary"]["task_count"] > 0
    assert module_packet_data["summary"]["status_counts"]["planned"] > 0
    assert module_packet_data["summary"]["open_required_count"] == module_packet_data["summary"]["required_count"]
    assert module_packet_data["owner_module"] == module_packet["owner_module"]
    assert module_packet_data["context"]["owner"]["name"] == module_packet["owner_module"]
    assert module_packet_data["context"]["peer_modules"]
    assert module_packet_data["context"]["quality_profile"] in {"standard", "production"}
    assert module_packet_data["execution_policy"]["work_allowed"] is True
    assert module_packet_data["execution_policy"]["draft_allowed"] is True
    assert module_packet_data["execution_policy"]["pass_allowed"] is False
    assert module_packet_data["execution_policy"]["llm_actionable"] is True
    assert module_packet_data["execution_policy"]["llm_actionable_open_count"] == module_packet_data["summary"]["open_required_count"]
    assert module_packet_data["execution_policy"]["human_locked_open_count"] == 0
    assert module_packet["execution_policy"]["llm_actionable_open_count"] == module_packet_data["summary"]["open_required_count"]
    first_packet_task = module_packet_data["tasks"][0]
    assert first_packet_task["todo_completion"]["status"] == "planned"
    module_packet_markdown = module_packet_md.read_text(encoding="utf-8")
    assert "No fixed RTL template" in module_packet_markdown
    assert "## Context" in module_packet_markdown
    assert "- Draft allowed: True" in module_packet_markdown
    assert "- PASS allowed: False" in module_packet_markdown
    assert "- LLM-actionable open tasks:" in module_packet_markdown
    assert "- Human-locked open tasks: 0" in module_packet_markdown
    assert "- Status: planned" in module_packet_markdown
    status_markdown = (tmp_path / ip / "rtl" / "rtl_authoring_status.md").read_text(encoding="utf-8")
    assert f"# RTL Authoring Status: {ip}" in status_markdown
    assert "## Next LLM Packets" in status_markdown
    assert "- Deferred human QA allowed: True" in status_markdown
    assert "- PASS allowed: False" in status_markdown
    assert "- Recommended packet batch limit: 4" in status_markdown
    traceability = json.loads((tmp_path / ip / "rtl" / "rtl_traceability.json").read_text(encoding="utf-8"))
    assert traceability["authoring_plan"] == "rtl/rtl_authoring_plan.json"
    assert {packet["packet_id"] for packet in traceability["authoring_packets"]} == {
        packet["packet_id"] for packet in authoring_plan["packets"]
    }


def test_rtl_audit_keeps_owner_tasks_open_until_owner_rtl_exists(tmp_path: Path):
    ip = "audit_missing_owner_rtl"
    _write_dynamic_todo_ssot(tmp_path, ip)

    result = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 1, result.stderr or result.stdout
    plan = json.loads((tmp_path / ip / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    top_task = next(task for task in plan["tasks"] if task["category"] == "rtl_flow.top")
    assert top_task["todo_completion"]["status"] == "open"
    assert "Owner RTL file is missing" in top_task["todo_completion"]["reason"]

    authoring_plan = json.loads((tmp_path / ip / "rtl" / "rtl_authoring_plan.json").read_text(encoding="utf-8"))
    open_module_packets = [
        packet
        for packet in authoring_plan["packets"]
        if packet["kind"] == "module" and int((packet.get("summary") or {}).get("open_required_count") or 0) > 0
    ]
    assert open_module_packets
    packet_data = json.loads((tmp_path / ip / open_module_packets[0]["json"]).read_text(encoding="utf-8"))
    assert packet_data["summary"]["open_required_count"] > 0
    assert any(
        "Owner RTL file is missing" in ((task.get("todo_completion") or {}).get("reason") or "")
        for task in packet_data["tasks"]
    )


def test_rtl_authoring_plan_splits_large_module_packets_by_section(tmp_path: Path):
    ip = "large_packet_probe"
    _write_dynamic_todo_ssot(tmp_path, ip)
    ssot_path = tmp_path / ip / "yaml" / f"{ip}.ssot.yaml"
    with ssot_path.open("a", encoding="utf-8") as fh:
        for index in range(70):
            fh.write(
                "\n"
                f"    - id: RTL_EXTRA_{index:02d}\n"
                f"      content: Implement extra datapath behavior {index}\n"
                f"      detail: Add nonconstant state/control logic for extra behavior {index} without replacing earlier owner-file slices.\n"
                "      criteria:\n"
                f"        - extra behavior {index} has RTL evidence in the owner file\n"
                f"      source_refs: [function_model.transactions.extra_{index:02d}]\n"
                f"      owner_module: {ip}_core\n"
                f"      owner_file: rtl/{ip}.sv\n"
                "      priority: normal\n"
                "      required: true\n"
            )

    result = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    authoring_plan = json.loads((tmp_path / ip / "rtl" / "rtl_authoring_plan.json").read_text(encoding="utf-8"))
    module_packets = [
        packet
        for packet in authoring_plan["packets"]
        if packet["kind"] == "module" and packet["owner_module"] == f"{ip}_core"
    ]
    sliced_packets = [
        packet
        for packet in module_packets
        if packet["summary"]["module_slice"].get("enabled")
    ]
    assert len(sliced_packets) >= 2
    assert authoring_plan["summary"]["sliced_module_packets"] >= len(sliced_packets)
    assert authoring_plan["summary"]["max_packet_required_tasks"] <= authoring_plan["summary"]["packet_task_limit"]
    assert all(packet["summary"]["required_count"] <= authoring_plan["summary"]["packet_task_limit"] for packet in module_packets)
    assert any("__workflow_todo" in packet["packet_id"] for packet in sliced_packets)
    packet_path = tmp_path / ip / sliced_packets[0]["json"]
    packet_doc = json.loads(packet_path.read_text(encoding="utf-8"))
    assert packet_doc["context"]["module_slice"]["enabled"] is True
    assert packet_doc["context"]["module_slice"]["count"] == len(sliced_packets)
    packet_md = (tmp_path / ip / sliced_packets[0]["markdown"]).read_text(encoding="utf-8")
    assert "Module slice:" in packet_md
    assert "preserve logic from earlier slices" in packet_md


def test_dynamic_rtl_todos_adds_top_owner_when_ssot_lists_only_child_modules(tmp_path: Path):
    ip = "dynamic_child_only_top_owner"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "sub_modules:",
                f"  - name: {ip}_engine",
                f"    file: rtl/{ip}_engine.sv",
                "    ownership: manifest",
                "    implements: [function_model.transactions.run, cycle_model.pipeline]",
                "function_model:",
                "  transactions:",
                "    - id: run",
                "      outputs: [done]",
                "cycle_model:",
                "  pipeline:",
                "    - {name: sample, cycle: 0}",
                "parameters:",
                "  - {name: NUM_CHANNELS, default: 4}",
                "io_list:",
                "  interfaces:",
                "    - name: cmd",
                "      ports:",
                "        - {name: start, direction: input, width: 1}",
                "        - {name: done, direction: output, width: 1}",
                "interrupts:",
                "  outputs:",
                "    - {name: irq}",
                "features:",
                "  - {name: command_launch}",
                "security:",
                "  assets:",
                "    - {name: command_state}",
                "error_handling:",
                "  recovery:",
                "    - {id: retry_on_fault, action: clear_fault_and_resume}",
                "synthesis:",
                "  ppa_targets:",
                "    - {name: frequency_mhz_min, value: 500}",
                "test_requirements:",
                "  scenarios:",
                "    - {id: SC_RUN, expected: done after start}",
                "  coverage_goals:",
                "    planned_bins:",
                "      - {id: COV_RUN}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    owners = {item["name"]: item for item in plan["summary"]["owner_modules"]}
    assert ip in owners
    assert owners[ip]["file"] == f"rtl/{ip}.sv"
    assert "top_module" in owners[ip]["refs"]
    assert "io_list" in owners[ip]["refs"]
    for source_ref in (
        "top_module",
        "io_list",
        "parameters.NUM_CHANNELS",
        "io_list.interfaces.cmd.ports.start",
        "interrupts.outputs.irq",
        "features.command_launch",
        "error_handling.recovery.retry_on_fault",
        "security.assets.command_state",
        "synthesis.ppa_targets.frequency_mhz_min",
        "test_requirements.scenarios.SC_RUN",
        "test_requirements.coverage_goals.planned_bins.COV_RUN",
    ):
        task = next(task for task in plan["tasks"] if task["source_ref"] == source_ref)
        assert task["owner_module"] == ip
        assert task["owner_file"] == f"rtl/{ip}.sv"

    authoring_plan = json.loads((ip_dir / "rtl" / "rtl_authoring_plan.json").read_text(encoding="utf-8"))
    packet_ids = {packet["packet_id"] for packet in authoring_plan["packets"]}
    assert f"module__{ip}" in packet_ids
    assert "unowned_tasks" not in packet_ids


def test_dynamic_rtl_todos_gate_disconnected_manifest_child(tmp_path: Path):
    ip = "dynamic_hierarchy_gate"
    ip_dir = tmp_path / ip
    for subdir in ("yaml", "rtl", "list"):
        (ip_dir / subdir).mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "sub_modules:",
                f"  - name: {ip}",
                f"    file: rtl/{ip}.sv",
                "    ownership: manifest",
                "    implements: [cycle_model]",
                "    cycle_model_refs: [cycle_model]",
                f"  - name: {ip}_engine",
                f"    file: rtl/{ip}_engine.sv",
                "    ownership: manifest",
                "    implements: [function_model]",
                "    function_model_refs: [function_model]",
                "function_model:",
                "  transactions:",
                "    - id: FM_RUN",
                "      outputs: [done]",
                "cycle_model:",
                "  latency: 1",
                "filelist:",
                "  rtl:",
                f"    - rtl/{ip}.sv",
                f"    - rtl/{ip}_engine.sv",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input wire clk, output wire done);\n"
        "  reg done_q;\n"
        "  always @(posedge clk) done_q <= ~done_q;\n"
        "  assign done = done_q;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}_engine.sv").write_text(
        f"module {ip}_engine(input wire clk, output wire engine_done);\n"
        "  reg engine_done_q;\n"
        "  always @(posedge clk) engine_done_q <= ~engine_done_q;\n"
        "  assign engine_done = engine_done_q;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\nrtl/{ip}_engine.sv\n", encoding="utf-8")

    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    hierarchy_task = next(
        task
        for task in plan["tasks"]
        if (task.get("gate_todo") or {}).get("kind") == "manifest_hierarchy_integration"
    )
    assert hierarchy_task["todo_completion"]["status"] == "open"
    assert "not reachable from the top RTL hierarchy" in hierarchy_task["todo_completion"]["reason"]

    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input wire clk, output wire done);\n"
        "  wire engine_done;\n"
        f"  {ip}_engine u_engine(.clk(clk), .engine_done(engine_done));\n"
        "  assign done = engine_done;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    hierarchy_task = next(
        task
        for task in plan["tasks"]
        if (task.get("gate_todo") or {}).get("kind") == "manifest_hierarchy_integration"
    )
    assert hierarchy_task["todo_completion"]["status"] == "pass"
    assert f"{ip}_engine" in plan["manifest_hierarchy_evidence"]["reachable_modules"]


def test_dynamic_rtl_todos_gate_manifest_child_port_connections(tmp_path: Path):
    ip = "dynamic_port_gate"
    ip_dir = tmp_path / ip
    for subdir in ("yaml", "rtl", "list"):
        (ip_dir / subdir).mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "sub_modules:",
                f"  - name: {ip}",
                f"    file: rtl/{ip}.sv",
                "    ownership: manifest",
                "    cycle_model_refs: [cycle_model]",
                f"  - name: {ip}_engine",
                f"    file: rtl/{ip}_engine.sv",
                "    ownership: manifest",
                "    function_model_refs: [function_model]",
                "function_model:",
                "  transactions:",
                "    - id: FM_RUN",
                "      outputs: [done]",
                "cycle_model:",
                "  latency: 1",
                "filelist:",
                "  rtl:",
                f"    - rtl/{ip}.sv",
                f"    - rtl/{ip}_engine.sv",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input wire clk, output wire done);\n"
        "  wire engine_done;\n"
        f"  {ip}_engine u_engine(.clk(clk));\n"
        "  assign done = engine_done;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}_engine.sv").write_text(
        f"module {ip}_engine(input wire clk, output wire engine_done);\n"
        "  reg engine_done_q;\n"
        "  always @(posedge clk) engine_done_q <= ~engine_done_q;\n"
        "  assign engine_done = engine_done_q;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\nrtl/{ip}_engine.sv\n", encoding="utf-8")

    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    hierarchy_task = next(
        task
        for task in plan["tasks"]
        if (task.get("gate_todo") or {}).get("kind") == "manifest_hierarchy_integration"
    )
    port_task = next(
        task
        for task in plan["tasks"]
        if (task.get("gate_todo") or {}).get("kind") == "manifest_port_connection_evidence"
    )
    assert hierarchy_task["todo_completion"]["status"] == "pass"
    assert port_task["todo_completion"]["status"] == "open"
    assert "manifest port connection issue" in port_task["todo_completion"]["reason"]
    assert plan["manifest_hierarchy_evidence"]["port_connection_issues"][0]["missing_ports"] == ["engine_done"]

    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input wire clk, output wire done);\n"
        "  wire engine_done;\n"
        f"  {ip}_engine u_engine(.clk(clk), .engine_done(engine_done));\n"
        "  assign done = engine_done;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    port_task = next(
        task
        for task in plan["tasks"]
        if (task.get("gate_todo") or {}).get("kind") == "manifest_port_connection_evidence"
    )
    assert port_task["todo_completion"]["status"] == "pass"
    assert plan["manifest_hierarchy_evidence"]["port_connection_status"] == "pass"


def test_dynamic_rtl_todos_ignores_function_inputs_for_child_port_gate(tmp_path: Path):
    ip = "dynamic_port_function_arg"
    ip_dir = tmp_path / ip
    for subdir in ("yaml", "rtl", "list"):
        (ip_dir / subdir).mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "sub_modules:",
                f"  - name: {ip}",
                f"    file: rtl/{ip}.sv",
                "    ownership: manifest",
                f"  - name: {ip}_engine",
                f"    file: rtl/{ip}_engine.sv",
                "    ownership: manifest",
                "function_model:",
                "  transactions:",
                "    - id: FM_RUN",
                "      outputs: [done]",
                "cycle_model:",
                "  latency: 1",
                "filelist:",
                "  rtl:",
                f"    - rtl/{ip}.sv",
                f"    - rtl/{ip}_engine.sv",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input wire clk, output wire done);\n"
        "  wire engine_done;\n"
        f"  {ip}_engine u_engine(.clk(clk), .engine_done(engine_done));\n"
        "  assign done = engine_done;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}_engine.sv").write_text(
        f"module {ip}_engine(input wire clk, output wire engine_done);\n"
        "  function automatic [3:0] inc_ptr;\n"
        "    input [3:0] ptr;\n"
        "    begin\n"
        "      inc_ptr = ptr + 4'd1;\n"
        "    end\n"
        "  endfunction\n"
        "  reg engine_done_q;\n"
        "  always @(posedge clk) engine_done_q <= inc_ptr({3'b000, engine_done_q})[0];\n"
        "  assign engine_done = engine_done_q;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\nrtl/{ip}_engine.sv\n", encoding="utf-8")

    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )

    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    port_task = next(
        task
        for task in plan["tasks"]
        if (task.get("gate_todo") or {}).get("kind") == "manifest_port_connection_evidence"
    )
    assert port_task["todo_completion"]["status"] == "pass"
    assert plan["manifest_hierarchy_evidence"]["port_connection_status"] == "pass"
    assert plan["manifest_hierarchy_evidence"]["port_connection_issues"] == []


def test_dynamic_rtl_todos_gate_manifest_child_signal_flow(tmp_path: Path):
    ip = "dynamic_signal_flow_gate"
    ip_dir = tmp_path / ip
    for subdir in ("yaml", "rtl", "list"):
        (ip_dir / subdir).mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "clocks:",
                "  - {name: clk}",
                "io_list:",
                "  interfaces:",
                "    - name: cmd",
                "      ports:",
                "        - {name: start_i, direction: input, width: 1}",
                "        - {name: done, direction: output, width: 1}",
                "sub_modules:",
                f"  - name: {ip}",
                f"    file: rtl/{ip}.sv",
                "    ownership: manifest",
                "    cycle_model_refs: [cycle_model]",
                f"  - name: {ip}_engine",
                f"    file: rtl/{ip}_engine.sv",
                "    ownership: manifest",
                "    function_model_refs: [function_model]",
                "function_model:",
                "  transactions:",
                "    - id: FM_RUN",
                "      inputs: [start_i]",
                "      outputs: [done]",
                "cycle_model:",
                "  latency: 1",
                "filelist:",
                "  rtl:",
                f"    - rtl/{ip}.sv",
                f"    - rtl/{ip}_engine.sv",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input wire clk, input wire start_i, output wire done);\n"
        "  wire engine_done;\n"
        f"  {ip}_engine u_engine(.clk(clk), .enable_i(1'b0), .done_o(engine_done));\n"
        "  assign done = start_i;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}_engine.sv").write_text(
        f"module {ip}_engine(input wire clk, input wire enable_i, output wire done_o);\n"
        "  assign done_o = clk & enable_i;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\nrtl/{ip}_engine.sv\n", encoding="utf-8")

    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    flow_task = next(
        task
        for task in plan["tasks"]
        if (task.get("gate_todo") or {}).get("kind") == "manifest_signal_flow_evidence"
    )
    assert flow_task["todo_completion"]["status"] == "open"
    flow_issues = plan["manifest_signal_flow_evidence"]["issues"]
    assert any("constant" in item["issue"] for item in flow_issues)
    assert any("does not feed" in item["issue"] for item in flow_issues)

    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input wire clk, input wire start_i, output wire done);\n"
        "  wire engine_done;\n"
        f"  {ip}_engine u_engine(.clk(clk), .enable_i(start_i), .done_o(engine_done));\n"
        "  assign done = engine_done;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    flow_task = next(
        task
        for task in plan["tasks"]
        if (task.get("gate_todo") or {}).get("kind") == "manifest_signal_flow_evidence"
    )
    assert flow_task["todo_completion"]["status"] == "pass"
    assert plan["manifest_signal_flow_evidence"]["checked_inputs"] >= 2
    assert plan["manifest_signal_flow_evidence"]["checked_outputs"] == 1


def test_dynamic_rtl_todos_gate_rejects_rtl_placeholder_markers(tmp_path: Path):
    ip = "dynamic_placeholder_gate"
    ip_dir = tmp_path / ip
    for subdir in ("yaml", "rtl", "list"):
        (ip_dir / subdir).mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "io_list:",
                "  interfaces:",
                "    - name: cmd",
                "      ports:",
                "        - {name: start_i, direction: input, width: 1}",
                "        - {name: done, direction: output, width: 1}",
                "function_model:",
                "  transactions:",
                "    - id: FM_RUN",
                "      inputs: [start_i]",
                "      outputs: [done]",
                "cycle_model:",
                "  latency: 1",
                "filelist:",
                "  rtl:",
                f"    - rtl/{ip}.sv",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input wire start_i, output wire done);\n"
        "  // TODO implement later\n"
        "  assign done = start_i;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\n", encoding="utf-8")

    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    placeholder_task = next(
        task
        for task in plan["tasks"]
        if (task.get("gate_todo") or {}).get("kind") == "rtl_placeholder_free_evidence"
    )
    assert placeholder_task["todo_completion"]["status"] == "open"
    assert plan["rtl_placeholder_free_evidence"]["issues"][0]["token"] == "TODO"

    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input wire start_i, output wire done);\n"
        "  assign done = start_i;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    placeholder_task = next(
        task
        for task in plan["tasks"]
        if (task.get("gate_todo") or {}).get("kind") == "rtl_placeholder_free_evidence"
    )
    assert placeholder_task["todo_completion"]["status"] == "pass"
    assert plan["rtl_placeholder_free_evidence"]["issues"] == []


def test_dynamic_rtl_todos_gate_requires_production_connection_contracts(tmp_path: Path):
    ip = "dynamic_contract_required"
    ip_dir = tmp_path / ip
    for subdir in ("yaml", "rtl", "list"):
        (ip_dir / subdir).mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "sub_modules:",
                f"  - name: {ip}",
                f"    file: rtl/{ip}.sv",
                "    ownership: manifest",
                "    cycle_model_refs: [cycle_model]",
                f"  - name: {ip}_engine",
                f"    file: rtl/{ip}_engine.sv",
                "    ownership: manifest",
                "    function_model_refs: [function_model]",
                "function_model:",
                "  transactions:",
                "    - id: FM_RUN",
                "      outputs: [done]",
                "cycle_model:",
                "  latency: 1",
                "quality_gates:",
                "  rtl_gen:",
                "    profile: production",
                "filelist:",
                "  rtl:",
                f"    - rtl/{ip}.sv",
                f"    - rtl/{ip}_engine.sv",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input wire clk, output wire done);\n"
        "  wire engine_done;\n"
        f"  {ip}_engine u_engine(.clk(clk), .engine_done(engine_done));\n"
        "  assign done = engine_done;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}_engine.sv").write_text(
        f"module {ip}_engine(input wire clk, output wire engine_done);\n"
        "  assign engine_done = clk;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\nrtl/{ip}_engine.sv\n", encoding="utf-8")

    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    contract_task = next(
        task
        for task in plan["tasks"]
        if (task.get("gate_todo") or {}).get("kind") == "manifest_connection_contract_evidence"
    )
    assert contract_task["todo_completion"]["status"] == "open"
    assert "no machine-readable SSOT connection contracts" in contract_task["todo_completion"]["reason"]
    suggestions = plan["connection_contract_suggestions"]
    assert suggestions["summary"]["status"] == "pending_review"
    assert suggestions["summary"]["applied_to_ssot"] is False
    assert suggestions["summary"]["suggested_rows"] == 2
    suggestion_rows = {
        (row["module"], row["port"]): row
        for row in suggestions["rows"]
    }
    clk_row = suggestion_rows[(f"{ip}_engine", "clk")]
    done_row = suggestion_rows[(f"{ip}_engine", "engine_done")]
    assert clk_row["signal"] == "clk"
    assert clk_row["review_status"] == "pending"
    assert clk_row["confidence"] == "observed_named_port_map"
    assert done_row["signal"] == "engine_done"
    assert done_row["review_status"] == "pending"
    assert (ip_dir / "rtl" / "connection_contract_suggestions.json").is_file()
    fragment = (ip_dir / "rtl" / "connection_contract_draft_top.svfrag").read_text(encoding="utf-8")
    assert f"{ip}_engine u_engine (" in fragment
    assert ".clk(clk)," in fragment
    assert ".engine_done(engine_done)" in fragment
    assert "DRAFT ONLY" in fragment

    preflight = subprocess.run(
        [sys.executable, str(SSOT_TO_RTL), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert preflight.returncode == 2
    blocked = json.loads((ip_dir / "rtl" / "rtl_blocked.json").read_text(encoding="utf-8"))
    assert "prepare_rtl_human_review.py" in blocked["next_action"]
    question_ids = {question["id"] for question in blocked["questions"]}
    assert "RTL_RESOLVE_CONNECTION_CONTRACTS" in question_ids
    contract_question = next(question for question in blocked["questions"] if question["id"] == "RTL_RESOLVE_CONNECTION_CONTRACTS")
    assert contract_question["answer_schema"]["root_key"] == "connection_contracts"
    assert contract_question["answer_schema"]["item_required_fields"] == ["module", "port", "signal"]
    assert contract_question["connection_contract_gap"]["status"] == "missing"
    pending = contract_question["pending_connection_contract_suggestions"]
    assert pending["path"] == "rtl/connection_contract_suggestions.json"
    assert pending["summary"]["suggested_rows"] == 2
    assert pending["sample_rows"][0]["review_status"] == "pending"


def test_prepare_rtl_human_review_packet_keeps_drafts_unapproved(tmp_path: Path):
    ip = "human_review_packet"
    rtl_dir = tmp_path / ip / "rtl"
    rtl_dir.mkdir(parents=True)
    (rtl_dir / "rtl_blocked.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "type": "rtl_blocked",
                "ip": ip,
                "top": ip,
                "questions": [
                    {
                        "id": "RTL_TARGET_SCALE_POLICY",
                        "decision_needed": "Lock target scale.",
                        "recommended_default": "Review candidate only.",
                        "suggested_ssot_target_scale": {
                            "source_files_min": 4,
                            "modules_min": 3,
                            "lines_min": 120,
                        },
                    },
                    {
                        "id": "RTL_RESOLVE_CONNECTION_CONTRACTS",
                        "decision_needed": "Approve machine-readable connection contracts.",
                        "connection_contract_gap": {"status": "missing"},
                    },
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (rtl_dir / "connection_contract_suggestions.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "type": "rtl_connection_contract_suggestions",
                "summary": {"status": "pending_review", "suggested_rows": 2},
                "rows": [
                    {
                        "module": f"{ip}_engine",
                        "instance": "u_engine",
                        "port": "clk",
                        "signal": "clk",
                        "direction": "input",
                        "confidence": "observed_named_port_map",
                        "review_status": "pending",
                    },
                    {
                        "module": f"{ip}_engine",
                        "instance": "u_engine",
                        "port": "done",
                        "signal": "engine_done",
                        "direction": "output",
                        "confidence": "observed_named_port_map",
                        "review_status": "pending",
                    },
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(PREPARE_RTL_HUMAN_REVIEW), ip, "--root", str(tmp_path), "--max-markdown-rows", "1"],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    packet = json.loads((rtl_dir / "rtl_human_review_packet.json").read_text(encoding="utf-8"))
    assert packet["status"] == "pending_human_review"
    assert "rtl_blocker_answers" not in packet
    assert packet["target_scale_review"]["suggested_target_scale"]["lines_min"] == 120
    assert packet["connection_contract_review"]["candidate_count"] == 2
    assert packet["connection_contract_review"]["candidate_rows"][0]["approval_required"] is True
    draft_by_id = {answer["id"]: answer for answer in packet["draft_rtl_blocker_answers"]}
    assert draft_by_id["RTL_TARGET_SCALE_POLICY"]["review_status"] == "pending_human_approval"
    assert draft_by_id["RTL_RESOLVE_CONNECTION_CONTRACTS"]["connection_contracts"][0]["signal"] == "clk"
    markdown = (rtl_dir / "rtl_human_review_packet.md").read_text(encoding="utf-8")
    assert "This packet is not approval" in markdown
    assert "1 more row(s) in JSON" in markdown


def test_prepare_rtl_human_review_packet_can_use_todo_plan_without_blocked_preflight(tmp_path: Path):
    ip = "human_review_from_todo_plan"
    rtl_dir = tmp_path / ip / "rtl"
    rtl_dir.mkdir(parents=True)
    (rtl_dir / "rtl_todo_plan.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "type": "rtl_todo_plan",
                "top": ip,
                "target_scale": {},
                "target_scale_waiver": {},
                "reference_profile": {
                    "suggested_ssot_target_scale": {
                        "source_files_min": 57,
                        "modules_min": 52,
                        "lines_min": 52338,
                    }
                },
                "manifest_hierarchy_evidence": {
                    "connection_contract_status": "fail",
                    "connection_contract_issues": [
                        {
                            "issue": "Production-profile multi-module RTL has no machine-readable SSOT connection contracts",
                            "required_sources": ["integration.connections", "sub_modules[].connections"],
                        }
                    ],
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (rtl_dir / "connection_contract_suggestions.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "type": "rtl_connection_contract_suggestions",
                "summary": {"status": "pending_review", "suggested_rows": 1},
                "rows": [
                    {
                        "module": f"{ip}_engine",
                        "instance": "u_engine",
                        "port": "done",
                        "signal": "engine_done",
                        "direction": "output",
                        "review_status": "pending",
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(PREPARE_RTL_HUMAN_REVIEW), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    packet = json.loads((rtl_dir / "rtl_human_review_packet.json").read_text(encoding="utf-8"))
    assert packet["evidence_source"] == "rtl_todo_plan"
    assert packet["inputs"]["rtl_blocked"] == ""
    assert packet["inputs"]["rtl_todo_plan"] == f"{ip}/rtl/rtl_todo_plan.json"
    assert "rtl_blocker_answers" not in packet
    assert packet["target_scale_review"]["suggested_target_scale"]["modules_min"] == 52
    assert packet["connection_contract_review"]["connection_contract_gap"]["status"] == "missing"
    draft_by_id = {answer["id"]: answer for answer in packet["draft_rtl_blocker_answers"]}
    assert draft_by_id["RTL_TARGET_SCALE_POLICY"]["review_status"] == "pending_human_approval"
    assert draft_by_id["RTL_RESOLVE_CONNECTION_CONTRACTS"]["connection_contracts"][0]["signal"] == "engine_done"


def test_prepare_rtl_human_review_packet_prefers_fresh_todo_plan_evidence(tmp_path: Path):
    ip = "human_review_fresh_evidence"
    rtl_dir = tmp_path / ip / "rtl"
    rtl_dir.mkdir(parents=True)
    (rtl_dir / "rtl_blocked.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "type": "rtl_blocked",
                "ip": ip,
                "top": ip,
                "questions": [
                    {
                        "id": "RTL_TARGET_SCALE_POLICY",
                        "decision_needed": "Keep this human-facing wording.",
                        "suggested_ssot_target_scale": {"modules_min": 3},
                    },
                    {
                        "id": "RTL_RESOLVE_CONNECTION_CONTRACTS",
                        "connection_contract_gap": {"status": "old"},
                    },
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (rtl_dir / "rtl_todo_plan.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "type": "rtl_todo_plan",
                "top": ip,
                "reference_profile": {
                    "suggested_ssot_target_scale": {"modules_min": 52, "lines_min": 52338}
                },
                "manifest_hierarchy_evidence": {
                    "connection_contract_status": "fail",
                    "connection_contract_issues": [{"issue": "fresh missing contracts"}],
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (rtl_dir / "connection_contract_suggestions.json").write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "module": f"{ip}_engine",
                        "instance": "u_engine",
                        "port": "done",
                        "signal": "engine_done",
                    }
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(PREPARE_RTL_HUMAN_REVIEW), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    packet = json.loads((rtl_dir / "rtl_human_review_packet.json").read_text(encoding="utf-8"))
    assert packet["evidence_source"] == "rtl_blocked+rtl_todo_plan"
    assert packet["target_scale_review"]["decision_needed"] == "Keep this human-facing wording."
    assert packet["target_scale_review"]["suggested_target_scale"]["modules_min"] == 52
    assert packet["connection_contract_review"]["connection_contract_gap"]["status"] == "missing"
    assert packet["connection_contract_review"]["connection_contract_gap"]["issues"][0]["issue"] == "fresh missing contracts"


def test_refresh_rtl_provenance_updates_existing_common_agent_record(tmp_path: Path):
    ip = "refresh_cli_probe"
    ip_dir = tmp_path / ip
    for subdir in ("yaml", "rtl", "list"):
        (ip_dir / subdir).mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "sub_modules:",
                f"  - name: {ip}",
                f"    file: rtl/{ip}.sv",
                "    ownership: manifest",
                f"  - name: {ip}_engine",
                f"    file: rtl/{ip}_engine.sv",
                "    ownership: manifest",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(f"module {ip}; endmodule\n", encoding="utf-8")
    (ip_dir / "rtl" / f"{ip}_engine.sv").write_text(f"module {ip}_engine; endmodule\n", encoding="utf-8")
    todo_path = ip_dir / "rtl" / "rtl_todo_plan.json"
    todo_path.write_text(
        json.dumps({"schema_version": 1, "type": "rtl_todo_plan", "tasks": [{"id": "RTL-1"}]}, indent=2) + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / "rtl_authoring_provenance.json").write_text(
        json.dumps(
            {
                "type": "rtl_authoring_provenance",
                "agent": "common_ai_agent",
                "workflow": "rtl-gen",
                "surface": "headless_common_engine",
                "todo_plan_sha256": "stale",
                "rtl_files": [f"rtl/{ip}.sv", f"rtl/{ip}_engine.sv"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(REFRESH_RTL_PROVENANCE), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    provenance = json.loads((ip_dir / "rtl" / "rtl_authoring_provenance.json").read_text(encoding="utf-8"))
    assert provenance["todo_plan_sha256"] == _stable_json_sha256(todo_path)
    assert provenance["refresh_reason"].startswith("SSOT metadata gate update")
    assert (ip_dir / "list" / f"{ip}.f").read_text(encoding="utf-8").splitlines() == [
        f"rtl/{ip}.sv",
        f"rtl/{ip}_engine.sv",
    ]


def test_refresh_rtl_provenance_refuses_operator_authored_record(tmp_path: Path):
    ip = "refresh_refuse_probe"
    ip_dir = tmp_path / ip
    for subdir in ("yaml", "rtl"):
        (ip_dir / subdir).mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        f"top_module:\n  name: {ip}\nfilelist:\n  rtl:\n    - rtl/{ip}.sv\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(f"module {ip}; endmodule\n", encoding="utf-8")
    (ip_dir / "rtl" / "rtl_todo_plan.json").write_text('{"type":"rtl_todo_plan"}\n', encoding="utf-8")
    (ip_dir / "rtl" / "rtl_authoring_provenance.json").write_text(
        json.dumps(
            {
                "type": "rtl_authoring_provenance",
                "agent": "operator",
                "workflow": "rtl-gen",
                "surface": "headless_common_engine",
                "rtl_files": [f"rtl/{ip}.sv"],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(REFRESH_RTL_PROVENANCE), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode != 0
    assert "refusing to refresh non-authoritative provenance" in (result.stderr + result.stdout)


def test_dynamic_rtl_todos_gate_checks_top_io_contracts(tmp_path: Path):
    ip = "dynamic_top_io_gate"
    ip_dir = tmp_path / ip
    for subdir in ("yaml", "rtl", "list"):
        (ip_dir / subdir).mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "clocks:",
                "  - {name: clk}",
                "resets:",
                "  - {name: rst_n}",
                "io_list:",
                "  interfaces:",
                "    - name: ctrl",
                "      type: input_bundle",
                "      signals:",
                "        - {name: start_i, width: 1}",
                "    - {name: result_o, type: output, width: DATA_WIDTH}",
                "function_model:",
                "  transactions:",
                "    - id: FM_RUN",
                "      inputs: [start_i]",
                "      outputs: [result_o]",
                "cycle_model:",
                "  latency: 1",
                "filelist:",
                "  rtl:",
                f"    - rtl/{ip}.sv",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input wire clk, input wire rst_n, output wire [DATA_WIDTH-1:0] result_o);\n"
        "  assign result_o = '0;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\n", encoding="utf-8")

    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    top_task = next(
        task
        for task in plan["tasks"]
        if (task.get("gate_todo") or {}).get("kind") == "top_io_contract_evidence"
    )
    assert top_task["todo_completion"]["status"] == "open"
    assert "start_i" in top_task["todo_completion"]["reason"]
    assert plan["top_io_contract_evidence"]["issues"][0]["issue"] == "SSOT top IO port is missing from RTL top declaration"

    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input wire clk, input wire rst_n, input wire start_i, output wire [DATA_WIDTH-1:0] result_o);\n"
        "  assign result_o = {DATA_WIDTH{start_i}};\n"
        "endmodule\n",
        encoding="utf-8",
    )
    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    top_task = next(
        task
        for task in plan["tasks"]
        if (task.get("gate_todo") or {}).get("kind") == "top_io_contract_evidence"
    )
    assert top_task["todo_completion"]["status"] == "pass"
    assert plan["top_io_contract_evidence"]["status"] == "pass"


def test_dynamic_rtl_todos_gate_accepts_parameterized_width_for_numeric_ssot(tmp_path: Path):
    ip = "dynamic_top_io_param_width_gate"
    ip_dir = tmp_path / ip
    for subdir in ("yaml", "rtl", "list"):
        (ip_dir / subdir).mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "clocks:",
                "  - {name: clk}",
                "resets:",
                "  - {name: rst_n}",
                "io_list:",
                "  interfaces:",
                "    - name: data_in",
                "      type: input",
                "      width: 8",
                "    - name: result",
                "      type: output",
                "      width: 9",
                "function_model:",
                "  transactions:",
                "    - id: FM_RUN",
                "      inputs: [data_in]",
                "      outputs: [result]",
                "cycle_model:",
                "  latency: 1",
                "filelist:",
                "  rtl:",
                f"    - rtl/{ip}.sv",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        "\n".join(
            [
                f"module {ip} #(",
                "  parameter integer DATA_W = 8,",
                "  parameter integer RESULT_W = DATA_W + 1",
                ") (",
                "  input wire clk,",
                "  input wire rst_n,",
                "  input wire [DATA_W-1:0] data_in,",
                "  output wire [RESULT_W-1:0] result",
                ");",
                "  assign result = {1'b0, data_in};",
                "endmodule",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\n", encoding="utf-8")

    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    top_task = next(
        task
        for task in plan["tasks"]
        if (task.get("gate_todo") or {}).get("kind") == "top_io_contract_evidence"
    )
    assert top_task["todo_completion"]["status"] == "pass"
    assert plan["top_io_contract_evidence"]["status"] == "pass"
    assert plan["top_io_contract_evidence"]["top_parameters"] == {"DATA_W": 8, "RESULT_W": 9}


def test_dynamic_rtl_todos_gate_rejects_constant_top_output_without_ssot_tieoff(tmp_path: Path):
    ip = "dynamic_top_output_drive_gate"
    ip_dir = tmp_path / ip
    for subdir in ("yaml", "rtl", "list"):
        (ip_dir / subdir).mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "clocks:",
                "  - {name: clk}",
                "io_list:",
                "  interfaces:",
                "    - name: cmd",
                "      ports:",
                "        - {name: start_i, direction: input, width: 1}",
                "        - {name: result_o, direction: output, width: 1}",
                "function_model:",
                "  transactions:",
                "    - id: FM_RUN",
                "      inputs: [start_i]",
                "      outputs: [result_o]",
                "cycle_model:",
                "  latency: 1",
                "filelist:",
                "  rtl:",
                f"    - rtl/{ip}.sv",
                f"    - rtl/{ip}_engine.sv",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input wire clk, input wire start_i, output wire result_o);\n"
        "  assign result_o = 1'b0;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}_engine.sv").write_text(
        f"module {ip}_engine(input wire clk, input wire start_i, output wire result_o);\n"
        "  assign result_o = clk & start_i;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\nrtl/{ip}_engine.sv\n", encoding="utf-8")

    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    drive_task = next(
        task
        for task in plan["tasks"]
        if (task.get("gate_todo") or {}).get("kind") == "top_output_drive_evidence"
    )
    assert drive_task["todo_completion"]["status"] == "open"
    assert "constant" in drive_task["todo_completion"]["reason"]

    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input wire clk, input wire start_i, output wire result_o);\n"
        f"  {ip}_engine u_engine(.clk(clk), .start_i(start_i), .result_o(result_o));\n"
        "endmodule\n",
        encoding="utf-8",
    )
    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    drive_task = next(
        task
        for task in plan["tasks"]
        if (task.get("gate_todo") or {}).get("kind") == "top_output_drive_evidence"
    )
    assert drive_task["todo_completion"]["status"] == "pass"
    assert plan["top_output_drive_evidence"]["driven"] == 1


def test_dynamic_rtl_todos_gate_allows_explicit_ssot_output_tieoff(tmp_path: Path):
    ip = "dynamic_top_output_tieoff_gate"
    ip_dir = tmp_path / ip
    for subdir in ("yaml", "rtl", "list"):
        (ip_dir / subdir).mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "clocks:",
                "  - {name: clk}",
                "io_list:",
                "  interfaces:",
                "    - name: status",
                "      ports:",
                "        - {name: idle_o, direction: output, width: 1, tieoff: 1'b1}",
                "function_model:",
                "  outputs:",
                "    - idle_o",
                "cycle_model:",
                "  latency: 0",
                "filelist:",
                "  rtl:",
                f"    - rtl/{ip}.sv",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input wire clk, output wire idle_o);\n"
        "  assign idle_o = 1'b1;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\n", encoding="utf-8")

    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    drive_task = next(
        task
        for task in plan["tasks"]
        if (task.get("gate_todo") or {}).get("kind") == "top_output_drive_evidence"
    )
    assert drive_task["todo_completion"]["status"] == "pass"
    assert plan["top_output_drive_evidence"]["driven"] == 1


def test_dynamic_rtl_todos_gate_allows_controlled_constant_procedural_output(tmp_path: Path):
    ip = "dynamic_top_output_controlled_constant_gate"
    ip_dir = tmp_path / ip
    for subdir in ("yaml", "rtl", "list"):
        (ip_dir / subdir).mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "io_list:",
                "  interfaces:",
                "    - name: stream",
                "      ports:",
                "        - {name: clk, direction: input, width: 1}",
                "        - {name: rst_n, direction: input, width: 1}",
                "        - {name: start_i, direction: input, width: 1}",
                "        - {name: valid_o, direction: output, width: 1}",
                "function_model:",
                "  outputs:",
                "    - valid_o",
                "cycle_model:",
                "  latency: 1",
                "filelist:",
                "  rtl:",
                f"    - rtl/{ip}.sv",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input wire clk, input wire rst_n, input wire start_i, output reg valid_o);\n"
        "  always @(posedge clk or negedge rst_n) begin\n"
        "    if (!rst_n) valid_o <= 1'b0;\n"
        "    else if (start_i) valid_o <= 1'b1;\n"
        "    else valid_o <= 1'b0;\n"
        "  end\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\n", encoding="utf-8")

    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    drive_task = next(
        task
        for task in plan["tasks"]
        if (task.get("gate_todo") or {}).get("kind") == "top_output_drive_evidence"
    )
    assert drive_task["todo_completion"]["status"] == "pass"
    assert plan["top_output_drive_evidence"]["driven"] == 1


def test_dynamic_rtl_todos_gate_rejects_unused_top_input_without_ssot_waiver(tmp_path: Path):
    ip = "dynamic_top_input_use_gate"
    ip_dir = tmp_path / ip
    for subdir in ("yaml", "rtl", "list"):
        (ip_dir / subdir).mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "clocks:",
                "  - {name: clk}",
                "io_list:",
                "  interfaces:",
                "    - name: cmd",
                "      ports:",
                "        - {name: start_i, direction: input, width: 1}",
                "        - {name: idle_o, direction: output, width: 1, tieoff: 1'b1}",
                "function_model:",
                "  transactions:",
                "    - id: FM_RUN",
                "      inputs: [start_i]",
                "      outputs: [idle_o]",
                "cycle_model:",
                "  latency: 1",
                "filelist:",
                "  rtl:",
                f"    - rtl/{ip}.sv",
                f"    - rtl/{ip}_engine.sv",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input wire clk, input wire start_i, output wire idle_o);\n"
        "  assign idle_o = 1'b1;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}_engine.sv").write_text(
        f"module {ip}_engine(input wire start_i);\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\nrtl/{ip}_engine.sv\n", encoding="utf-8")

    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    input_task = next(
        task
        for task in plan["tasks"]
        if (task.get("gate_todo") or {}).get("kind") == "top_input_consumption_evidence"
    )
    assert input_task["todo_completion"]["status"] == "open"
    assert "input consumption" in input_task["todo_completion"]["reason"]

    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input wire clk, input wire start_i, output wire idle_o);\n"
        f"  {ip}_engine u_engine(.start_i(start_i));\n"
        "  assign idle_o = 1'b1;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    input_task = next(
        task
        for task in plan["tasks"]
        if (task.get("gate_todo") or {}).get("kind") == "top_input_consumption_evidence"
    )
    assert input_task["todo_completion"]["status"] == "pass"
    assert plan["top_input_consumption_evidence"]["consumed"] == 1


def test_dynamic_rtl_todos_gate_rejects_token_only_behavior_owner(tmp_path: Path):
    ip = "dynamic_owner_logic_gate"
    ip_dir = tmp_path / ip
    for subdir in ("yaml", "rtl", "list"):
        (ip_dir / subdir).mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "sub_modules:",
                f"  - name: {ip}",
                f"    file: rtl/{ip}.sv",
                "    ownership: manifest",
                "    cycle_model_refs: [cycle_model]",
                f"  - name: {ip}_counter",
                f"    file: rtl/{ip}_counter.sv",
                "    ownership: manifest",
                "    function_model_refs: [function_model.state_variables.counter]",
                "function_model:",
                "  state_variables:",
                "    - {name: counter, width: 8, reset: 0}",
                "  transactions:",
                "    - id: FM_INC",
                "      state_updates: [counter += 1]",
                "cycle_model:",
                "  latency: 1",
                "filelist:",
                "  rtl:",
                f"    - rtl/{ip}.sv",
                f"    - rtl/{ip}_counter.sv",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input wire clk, output wire [7:0] count_o);\n"
        "  wire [7:0] counter_value;\n"
        f"  {ip}_counter u_counter(.clk(clk), .count_o(counter_value));\n"
        "  assign count_o = counter_value;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}_counter.sv").write_text(
        f"module {ip}_counter(input wire clk, output wire [7:0] count_o);\n"
        "  wire [7:0] counter;\n"
        "  assign count_o = counter;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\nrtl/{ip}_counter.sv\n", encoding="utf-8")

    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    logic_task = next(
        task
        for task in plan["tasks"]
        if (task.get("gate_todo") or {}).get("kind") == "owner_logic_structure_evidence"
    )
    assert logic_task["todo_completion"]["status"] == "open"
    assert "lacks sequential/procedural update evidence" in logic_task["todo_completion"]["reason"]

    (ip_dir / "rtl" / f"{ip}_counter.sv").write_text(
        f"module {ip}_counter(input wire clk, output wire [7:0] count_o);\n"
        "  reg [7:0] counter;\n"
        "  always @(posedge clk) counter <= counter + 8'd1;\n"
        "  assign count_o = counter;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    logic_task = next(
        task
        for task in plan["tasks"]
        if (task.get("gate_todo") or {}).get("kind") == "owner_logic_structure_evidence"
    )
    assert logic_task["todo_completion"]["status"] == "pass"
    assert plan["owner_logic_evidence"]["status"] == "pass"


def test_dynamic_rtl_todos_owner_logic_accepts_filelist_entries_with_ip_prefix(tmp_path: Path):
    ip = "dynamic_owner_prefixed_filelist"
    ip_dir = tmp_path / ip
    for subdir in ("yaml", "rtl", "list"):
        (ip_dir / subdir).mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "sub_modules:",
                f"  - name: {ip}",
                f"    file: rtl/{ip}.sv",
                "    ownership: manifest",
                "    wiring_only: true",
                f"  - name: {ip}_counter",
                f"    file: rtl/{ip}_counter.sv",
                "    ownership: manifest",
                "    function_model_refs: [function_model.state_variables.counter]",
                "function_model:",
                "  state_variables:",
                "    - {name: counter, width: 8, reset: 0}",
                "  transactions:",
                "    - id: FM_INC",
                "      state_updates: [counter += 1]",
                "cycle_model:",
                "  latency: 1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input wire clk, output wire [7:0] count_o);\n"
        "  wire [7:0] counter_value;\n"
        f"  {ip}_counter u_counter(.clk(clk), .count_o(counter_value));\n"
        "  assign count_o = counter_value;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}_counter.sv").write_text(
        f"module {ip}_counter(input wire clk, output wire [7:0] count_o);\n"
        "  reg [7:0] counter;\n"
        "  always @(posedge clk) counter <= counter + 8'd1;\n"
        "  assign count_o = counter;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(
        f"{ip}/rtl/{ip}.sv\n{ip}/rtl/{ip}_counter.sv\n",
        encoding="utf-8",
    )

    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )

    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    assert plan["owner_logic_evidence"]["status"] == "pass"
    assert not any(
        issue.get("issue") == "Behavior-owner module is not declared in its owner file"
        for issue in plan["owner_logic_evidence"]["issues"]
    )


def test_dynamic_rtl_todos_gate_checks_ssot_connection_contract_signal(tmp_path: Path):
    ip = "dynamic_contract_signal"
    ip_dir = tmp_path / ip
    for subdir in ("yaml", "rtl", "list"):
        (ip_dir / subdir).mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "sub_modules:",
                f"  - name: {ip}",
                f"    file: rtl/{ip}.sv",
                "    ownership: manifest",
                "    cycle_model_refs: [cycle_model]",
                f"  - name: {ip}_engine",
                f"    file: rtl/{ip}_engine.sv",
                "    ownership: manifest",
                "    function_model_refs: [function_model]",
                "function_model:",
                "  transactions:",
                "    - id: FM_RUN",
                "      outputs: [done]",
                "cycle_model:",
                "  latency: 1",
                "integration:",
                "  connections:",
                f"    - {{module: {ip}_engine, port: engine_done, signal: engine_done_wire}}",
                "filelist:",
                "  rtl:",
                f"    - rtl/{ip}.sv",
                f"    - rtl/{ip}_engine.sv",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}_engine.sv").write_text(
        f"module {ip}_engine(input wire clk, output wire engine_done);\n"
        "  assign engine_done = clk;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\nrtl/{ip}_engine.sv\n", encoding="utf-8")
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input wire clk, output wire done);\n"
        "  wire engine_done_wire;\n"
        "  wire wrong_done_wire;\n"
        f"  {ip}_engine u_engine(.clk(clk), .engine_done(wrong_done_wire));\n"
        "  assign done = engine_done_wire;\n"
        "endmodule\n",
        encoding="utf-8",
    )

    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    contract_task = next(
        task
        for task in plan["tasks"]
        if (task.get("gate_todo") or {}).get("kind") == "manifest_connection_contract_evidence"
    )
    assert contract_task["todo_completion"]["status"] == "open"
    assert "does not match SSOT connection signal terms" in contract_task["todo_completion"]["reason"]
    assert plan["manifest_hierarchy_evidence"]["connection_contract_status"] == "fail"

    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input wire clk, output wire done);\n"
        "  wire engine_done_wire;\n"
        f"  {ip}_engine u_engine(.clk(clk), .engine_done(engine_done_wire));\n"
        "  assign done = engine_done_wire;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    contract_task = next(
        task
        for task in plan["tasks"]
        if (task.get("gate_todo") or {}).get("kind") == "manifest_connection_contract_evidence"
    )
    assert contract_task["todo_completion"]["status"] == "pass"
    assert plan["manifest_hierarchy_evidence"]["connection_contract_status"] == "pass"
    authoring_plan = json.loads((ip_dir / "rtl" / "rtl_authoring_plan.json").read_text(encoding="utf-8"))
    packet_ids = {packet["packet_id"]: packet for packet in authoring_plan["packets"]}
    top_packet = json.loads((ip_dir / packet_ids[f"module__{ip}"]["json"]).read_text(encoding="utf-8"))
    engine_packet = json.loads((ip_dir / packet_ids[f"module__{ip}_engine"]["json"]).read_text(encoding="utf-8"))
    assert top_packet["context"]["ssot_connection_contracts"][0]["module"] == f"{ip}_engine"
    assert engine_packet["context"]["ssot_connection_contracts"][0]["port"] == "engine_done"
    top_packet_md = (ip_dir / packet_ids[f"module__{ip}"]["markdown"]).read_text(encoding="utf-8")
    assert "SSOT connection contracts" in top_packet_md


def test_dynamic_rtl_todos_accepts_submodule_connection_map(tmp_path: Path):
    ip = "dynamic_submodule_contract"
    ip_dir = tmp_path / ip
    for subdir in ("yaml", "rtl", "list"):
        (ip_dir / subdir).mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "sub_modules:",
                f"  - name: {ip}",
                f"    file: rtl/{ip}.sv",
                "    ownership: manifest",
                "    cycle_model_refs: [cycle_model]",
                f"  - name: {ip}_engine",
                f"    file: rtl/{ip}_engine.sv",
                "    ownership: manifest",
                "    function_model_refs: [function_model]",
                "    connections:",
                "      engine_done: engine_done_wire",
                "function_model:",
                "  transactions:",
                "    - id: FM_RUN",
                "      outputs: [done]",
                "cycle_model:",
                "  latency: 1",
                "filelist:",
                "  rtl:",
                f"    - rtl/{ip}.sv",
                f"    - rtl/{ip}_engine.sv",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}_engine.sv").write_text(
        f"module {ip}_engine(input wire clk, output wire engine_done);\n"
        "  assign engine_done = clk;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\nrtl/{ip}_engine.sv\n", encoding="utf-8")
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input wire clk, output wire done);\n"
        "  wire engine_done_wire;\n"
        f"  {ip}_engine u_engine(.clk(clk), .engine_done(engine_done_wire));\n"
        "  assign done = engine_done_wire;\n"
        "endmodule\n",
        encoding="utf-8",
    )

    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))

    contracts = plan["ssot_connection_contracts"]
    assert contracts[0]["source_ref"] == "sub_modules[1].connections"
    assert contracts[0]["machine_readable"] is True
    assert contracts[0]["module"] == f"{ip}_engine"
    assert contracts[0]["port"] == "engine_done"
    assert contracts[0]["signal"] == "engine_done_wire"
    contract_task = next(
        task
        for task in plan["tasks"]
        if (task.get("gate_todo") or {}).get("kind") == "manifest_connection_contract_evidence"
    )
    assert contract_task["todo_completion"]["status"] == "pass"
    assert plan["manifest_hierarchy_evidence"]["connection_contract_status"] == "pass"


def test_rtl_authoring_policy_allows_module_draft_but_blocks_top_signoff_without_contracts(tmp_path: Path):
    ip = "production_contract_gap"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "quality_gates:",
                "  rtl_gen:",
                "    profile: production",
                "sub_modules:",
                f"  - name: {ip}",
                f"    file: rtl/{ip}.sv",
                "    ownership: manifest",
                "    cycle_model_refs: [cycle_model]",
                f"  - name: {ip}_engine",
                f"    file: rtl/{ip}_engine.sv",
                "    ownership: manifest",
                "    function_model_refs: [function_model]",
                "function_model:",
                "  transactions:",
                "    - id: FM_RUN",
                "      outputs: [done]",
                "cycle_model:",
                "  latency: 1",
                "filelist:",
                "  rtl:",
                f"    - rtl/{ip}.sv",
                f"    - rtl/{ip}_engine.sv",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    authoring_plan = json.loads((ip_dir / "rtl" / "rtl_authoring_plan.json").read_text(encoding="utf-8"))
    plan_policy = authoring_plan["execution_policy"]
    assert plan_policy["draft_allowed"] is True
    assert plan_policy["pass_allowed"] is False
    assert plan_policy["connection_contract_gap"]["status"] == "missing"
    assert plan_policy["deferred_human_qa_allowed"] is True
    assert any(
        item["source"] == "ssot_connection_contracts"
        for item in plan_policy["blocked_by_locked_truth"]
    )

    packet_ids = {packet["packet_id"]: packet for packet in authoring_plan["packets"]}
    top_packet = json.loads((ip_dir / packet_ids[f"module__{ip}"]["json"]).read_text(encoding="utf-8"))
    engine_packet = json.loads((ip_dir / packet_ids[f"module__{ip}_engine"]["json"]).read_text(encoding="utf-8"))
    evidence_packet = json.loads((ip_dir / packet_ids["rtl_gate_evidence_closure"]["json"]).read_text(encoding="utf-8"))
    tool_packet = json.loads((ip_dir / packet_ids["rtl_gate_tool_evidence"]["json"]).read_text(encoding="utf-8"))
    contract_packet = json.loads((ip_dir / packet_ids["rtl_gate_contract_blocked"]["json"]).read_text(encoding="utf-8"))
    gate_packet = json.loads((ip_dir / packet_ids["rtl_gate_human_closure"]["json"]).read_text(encoding="utf-8"))

    assert top_packet["execution_policy"]["draft_allowed"] is True
    assert top_packet["execution_policy"]["integration_signoff_allowed"] is False
    assert top_packet["execution_policy"]["pass_allowed"] is False
    assert top_packet["execution_policy"]["human_locked_open_count"] == 0
    assert top_packet["context"]["connection_contract_gap"]["status"] == "missing"
    assert top_packet["execution_policy"]["blocked_by_locked_truth"] == []

    assert engine_packet["execution_policy"]["draft_allowed"] is True
    assert engine_packet["execution_policy"]["integration_signoff_allowed"] is True
    assert engine_packet["execution_policy"]["pass_allowed"] is False

    assert evidence_packet["execution_policy"]["evidence_closure_allowed"] is True
    assert evidence_packet["execution_policy"]["integration_signoff_allowed"] is False
    assert evidence_packet["execution_policy"]["human_locked_open_count"] == 0
    assert evidence_packet["execution_policy"]["llm_actionable_open_count"] > 0

    assert tool_packet["execution_policy"]["llm_actionable_open_count"] == 0
    assert tool_packet["execution_policy"]["tool_evidence_open_count"] > 0
    assert tool_packet["execution_policy"]["human_locked_open_count"] == 0
    tool_runbook = tool_packet["execution_policy"]["tool_evidence_plan"]
    tool_kinds = {item["gate_kind"] for item in tool_runbook}
    assert {"dut_compile", "dut_lint"}.issubset(tool_kinds)
    compile_step = next(item for item in tool_runbook if item["gate_kind"] == "dut_compile")
    lint_step = next(item for item in tool_runbook if item["gate_kind"] == "dut_lint")
    assert "rtl_compile_report.py" in compile_step["commands"][0]
    assert f"{ip}/rtl/rtl_compile.json" in compile_step["artifacts"]
    assert "dut_lint_report.py" in lint_step["commands"][0]
    status_md = (ip_dir / "rtl" / "rtl_authoring_status.md").read_text(encoding="utf-8")
    assert "next_tool=" in status_md

    assert contract_packet["execution_policy"]["llm_actionable_open_count"] == 0
    assert contract_packet["execution_policy"]["human_locked_open_count"] > 0
    assert contract_packet["execution_policy"]["contract_blocked_open_count"] > 0
    assert contract_packet["execution_policy"]["blocked_by_locked_truth"][0]["source"] == "ssot_connection_contracts"

    assert gate_packet["execution_policy"]["evidence_closure_allowed"] is True
    assert gate_packet["execution_policy"]["integration_signoff_allowed"] is False
    assert gate_packet["execution_policy"]["pass_allowed"] is False
    assert gate_packet["execution_policy"]["blocked_by_locked_truth"][0]["source"] == "ssot_connection_contracts"

    top_packet_md = (ip_dir / packet_ids[f"module__{ip}"]["markdown"]).read_text(encoding="utf-8")
    assert "Connection contract gap" in top_packet_md
    assert "Locked-truth blockers" not in top_packet_md

    (ip_dir / "rtl").mkdir(exist_ok=True)
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input wire clk, output wire done);\n"
        "  assign done = clk;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    rerun = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert rerun.returncode == 1, rerun.stderr or rerun.stdout
    authoring_plan = json.loads((ip_dir / "rtl" / "rtl_authoring_plan.json").read_text(encoding="utf-8"))
    assert authoring_plan["summary"]["next_llm_packets"][0] == f"module__{ip}_engine"


def test_repair_ssot_schema_preserves_general_ip_and_defers_connection_contracts(tmp_path: Path):
    ip = "dma330_repair_contract"
    ip_dir = tmp_path / ip
    ssot_path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    ssot_path.parent.mkdir(parents=True, exist_ok=True)
    doc = {
        "top_module": {
            "name": ip,
            "type": "dma",
            "description": "General DMA controller draft from imported documents",
        },
        "sub_modules": [
            {
                "name": f"{ip}_engine",
                "file": f"rtl/{ip}_engine.sv",
                "ownership": "manifest",
                "function_model_refs": ["function_model"],
            },
            {
                "name": ip,
                "file": f"rtl/{ip}.sv",
                "ownership": "manifest",
                "wiring_only": True,
                "source_sections": ["top_module", "io_list", "integration"],
            },
        ],
        "io_list": {
            "clock_domains": [{"ports": [{"name": "clk"}], "frequency_mhz": 100}],
            "resets": [{"ports": [{"name": "rst_n"}], "name": "rst_n", "polarity": "active_low"}],
            "interfaces": [
                {
                    "name": "cmd",
                    "ports": [
                        {"name": "cmd_valid", "direction": "input"},
                        {"name": "cmd_ready", "direction": "output"},
                    ],
                }
            ],
        },
        "quality_gates": {"rtl_gen": {"profile": "production"}},
    }
    ssot_path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(REPAIR_SSOT), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    repaired = yaml.safe_load(ssot_path.read_text(encoding="utf-8"))
    assert repaired["quality_gates"]["rtl_gen"]["profile"] == "production"
    assert repaired["quality_gates"]["rtl_gen"]["pass"]
    assert repaired["pnr"]["utilization_pct"] == 60
    assert repaired["pnr"]["io_layers"] == {"horizontal": "met3", "vertical": "met2"}
    assert repaired["integration"]["connections"] == []
    assert repaired["integration"]["connection_contract_status"].startswith("missing machine-readable")
    todo_ids = [item["id"] for item in repaired["workflow_todos"]["rtl-gen"]]
    assert "RTL_TARGET_SCALE_POLICY" in todo_ids
    assert "RTL_RESOLVE_CONNECTION_CONTRACTS" in todo_ids
    scale_todo = next(item for item in repaired["workflow_todos"]["rtl-gen"] if item["id"] == "RTL_TARGET_SCALE_POLICY")
    assert scale_todo["answer_schema"]["root_key"] == "target_scale or target_scale_waiver"
    assert "source_files_min" in scale_todo["answer_schema"]["target_scale_fields"]
    assert "lines_min" in scale_todo["answer_schema"]["target_scale_fields"]
    assert scale_todo["example_answer"]["target_scale"]["modules_min"] == 8
    contract_todo = next(item for item in repaired["workflow_todos"]["rtl-gen"] if item["id"] == "RTL_RESOLVE_CONNECTION_CONTRACTS")
    assert contract_todo["answer_schema"]["root_key"] == "connection_contracts"
    assert contract_todo["answer_schema"]["item_required_fields"] == ["module", "port", "signal"]
    assert contract_todo["example_answer"]["connection_contracts"][0]["source_ref"] == "integration.connections.done_o"
    serialized = yaml.safe_dump(repaired, sort_keys=False).lower()
    assert "crypto" not in serialized
    assert "sram" not in serialized
    assert "axi4-lite" not in serialized

    check = subprocess.run(
        ["bash", str(SOURCE_ROOT / "workflow" / "ssot-gen" / "scripts" / "check_ssot_disk.sh"), ip],
        cwd=str(tmp_path),
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert check.returncode == 0, check.stdout + check.stderr

    derive = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert derive.returncode == 0, derive.stderr or derive.stdout
    authoring_plan = json.loads((ip_dir / "rtl" / "rtl_authoring_plan.json").read_text(encoding="utf-8"))
    policy = authoring_plan["execution_policy"]
    assert policy["draft_allowed"] is True
    assert policy["pass_allowed"] is False
    assert policy["connection_contract_gap"]["status"] == "missing"

    fl = subprocess.run(
        [sys.executable, str(EMIT_FL_MODEL), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert fl.returncode == 0, fl.stderr or fl.stdout
    decomposition = json.loads((ip_dir / "model" / "decomposition.json").read_text(encoding="utf-8"))
    top_contract = next(item for item in decomposition["module_contracts"] if item["name"] == ip)
    assert top_contract["blocked"] is False
    assert {"top_module", "io_list", "integration"} <= set(top_contract["structural_refs"])
    assert decomposition["complete"] is True


def test_sta_sdc_uses_canonical_timing_target_clocks(tmp_path: Path):
    ip = "sta_clock_from_timing"
    ip_dir = tmp_path / ip
    ssot_path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    ssot_path.parent.mkdir(parents=True, exist_ok=True)
    ssot_path.write_text(
        yaml.safe_dump(
            {
                "top_module": {"name": ip},
                "io_list": {
                    "clock_domains": [{"name": "main", "ports": [{"name": "clk", "direction": "input", "width": 1}]}],
                    "resets": [{"name": "rst_n", "ports": [{"name": "rst_n"}], "sync_async": "async"}],
                },
                "timing": {"target_clocks": [{"name": "clk", "frequency_mhz": 125}]},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        ["bash", str(WRITE_STA_SDC), ip],
        cwd=str(tmp_path),
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    sdc = (ip_dir / "sta" / "out" / f"{ip}.sdc").read_text(encoding="utf-8")
    assert "create_clock -name clk -period 8.0 [get_ports clk]" in sdc
    assert "set_false_path -from [get_ports rst_n]" in sdc


def test_static_rtl_evidence_is_scoped_to_owner_file(tmp_path: Path):
    ip = "owner_static_scope"
    ip_dir = tmp_path / ip
    for subdir in ("yaml", "rtl", "list"):
        (ip_dir / subdir).mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "sub_modules:",
                f"  - name: {ip}",
                f"    file: rtl/{ip}.sv",
                "    ownership: manifest",
                "    cycle_model_refs: [cycle_model]",
                f"  - name: {ip}_engine",
                f"    file: rtl/{ip}_engine.sv",
                "    ownership: manifest",
                "    function_model_refs: [function_model]",
                "function_model:",
                "  transactions:",
                "    - id: FM_RUN",
                "      output_rules:",
                "        - {name: UniquePayloadX, expr: UniquePayloadX}",
                "cycle_model:",
                "  latency: 1",
                "filelist:",
                "  rtl:",
                f"    - rtl/{ip}.sv",
                f"    - rtl/{ip}_engine.sv",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input wire clk, output wire done);\n"
        "  wire engine_done;\n"
        "  reg UniquePayloadX;\n"
        f"  {ip}_engine u_engine(.clk(clk), .engine_done(engine_done));\n"
        "  assign done = UniquePayloadX | engine_done;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}_engine.sv").write_text(
        f"module {ip}_engine(input wire clk, output wire engine_done);\n"
        "  assign engine_done = clk;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\nrtl/{ip}_engine.sv\n", encoding="utf-8")

    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    output_rule = next(task for task in plan["tasks"] if task["category"] == "function_model.output_rule")
    assert output_rule["owner_file"] == f"rtl/{ip}_engine.sv"
    assert output_rule["static_evidence"]["status"] == "missing"
    assert output_rule["static_evidence"]["source_scope"] == f"rtl/{ip}_engine.sv"

    (ip_dir / "rtl" / f"{ip}_engine.sv").write_text(
        f"module {ip}_engine(input wire clk, output wire engine_done);\n"
        "  reg UniquePayloadX;\n"
        "  always @(posedge clk) UniquePayloadX <= ~UniquePayloadX;\n"
        "  assign engine_done = UniquePayloadX;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    output_rule = next(task for task in plan["tasks"] if task["category"] == "function_model.output_rule")
    assert output_rule["static_evidence"]["status"] == "pass"
    assert "UniquePayloadX" in output_rule["static_evidence"]["matched_terms"]


def test_static_rtl_evidence_requires_multiple_terms_for_rich_tasks(tmp_path: Path):
    ip = "owner_static_strength"
    ip_dir = tmp_path / ip
    for subdir in ("yaml", "rtl", "list"):
        (ip_dir / subdir).mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "sub_modules:",
                f"  - name: {ip}",
                f"    file: rtl/{ip}.sv",
                "    ownership: manifest",
                "    cycle_model_refs: [cycle_model]",
                f"  - name: {ip}_engine",
                f"    file: rtl/{ip}_engine.sv",
                "    ownership: manifest",
                "    function_model_refs: [function_model]",
                "function_model:",
                "  transactions:",
                "    - id: FM_RUN",
                "      output_rules:",
                "        - {name: ComplexOut, expr: payload_flag && ComplexOut}",
                "cycle_model:",
                "  latency: 1",
                "filelist:",
                "  rtl:",
                f"    - rtl/{ip}.sv",
                f"    - rtl/{ip}_engine.sv",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input wire clk, output wire done);\n"
        f"  {ip}_engine u_engine(.clk(clk), .engine_done(done));\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}_engine.sv").write_text(
        f"module {ip}_engine(input wire clk, output wire engine_done);\n"
        "  reg ComplexOut;\n"
        "  always @(posedge clk) ComplexOut <= ~ComplexOut;\n"
        "  assign engine_done = ComplexOut;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\nrtl/{ip}_engine.sv\n", encoding="utf-8")

    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    output_rule = next(task for task in plan["tasks"] if task["category"] == "function_model.output_rule")
    assert output_rule["static_evidence"]["status"] == "missing"
    assert output_rule["static_evidence"]["matched_count"] == 1
    assert output_rule["static_evidence"]["required_match_count"] == 2

    (ip_dir / "rtl" / f"{ip}_engine.sv").write_text(
        f"module {ip}_engine(input wire clk, output wire engine_done);\n"
        "  reg ComplexOut;\n"
        "  wire payload_flag = clk;\n"
        "  always @(posedge clk) ComplexOut <= payload_flag & ~ComplexOut;\n"
        "  assign engine_done = ComplexOut;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    output_rule = next(task for task in plan["tasks"] if task["category"] == "function_model.output_rule")
    assert output_rule["static_evidence"]["status"] == "pass"
    assert {"ComplexOut", "payload_flag"}.issubset(set(output_rule["static_evidence"]["matched_terms"]))


def test_static_rtl_evidence_matches_protocol_response_error_aliases(tmp_path: Path):
    ip = "protocol_alias_static"
    ip_dir = tmp_path / ip
    for subdir in ("yaml", "rtl", "list"):
        (ip_dir / subdir).mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "sub_modules:",
                f"  - name: {ip}",
                f"    file: rtl/{ip}.sv",
                "    ownership: manifest",
                "    function_model_refs: [function_model]",
                "function_model:",
                "  transactions:",
                "    - id: FM_DMALD",
                "      error_cases:",
                "        - condition: AXI rresp != OKAY",
                "          result: fault_status |= DATA_READ_ERR",
                "cycle_model:",
                "  latency: 1",
                "filelist:",
                "  rtl:",
                f"    - rtl/{ip}.sv",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input wire ld_rsp_error_i, output wire fault_valid);\n"
        "  wire dmald_error_case_fired = ld_rsp_error_i;\n"
        "  assign fault_valid = dmald_error_case_fired;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode in {0, 1}, result.stderr or result.stdout
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    error_case = next(task for task in plan["tasks"] if task["category"] == "function_model.error_case")
    assert error_case["static_evidence"]["status"] == "pass"
    assert {"DMALD", "ld_rsp_error_i"}.issubset(set(error_case["static_evidence"]["matched_terms"]))


def test_dynamic_rtl_todos_import_ssot_workflow_todo_content_detail_criteria(tmp_path: Path):
    ip = "dynamic_todo_workflow"
    _write_dynamic_todo_ssot(tmp_path, ip)

    result = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    plan = json.loads((tmp_path / ip / "logs" / "rtl-gen" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    task = next(task for task in plan["tasks"] if task["category"] == "workflow_todo.rtl_gen")
    assert task["workflow_todo"]["id"] == "RTL_ACCEPT_PIPELINE"
    assert task["content"] == "Implement accepted command response pipeline from SSOT todo"
    assert "Preserve valid/ready accepted command data through execute and response stages" in task["detail"]
    assert "SSOT ref: workflow_todos.rtl-gen[0]." in task["detail"]
    assert task["owner_module"] == f"{ip}_core"
    assert task["owner_file"] == f"rtl/{ip}.sv"
    assert "function_model.transactions.FM_ACCEPT" in task["ssot_refs"]
    assert "cycle_model.pipeline.S1_EXECUTE" in task["ssot_refs"]
    assert "pipeline register captures data_in only on valid and ready" in task["criteria"]
    assert "result_valid asserts only when result corresponds to captured value" in task["criteria"]
    assert any("content/detail/criteria are preserved" in item for item in task["criteria"])
    assert plan["summary"]["by_category"]["workflow_todo.rtl_gen"] == 1


def test_dynamic_rtl_todos_embed_ip_specific_detail_and_criteria(tmp_path: Path):
    ip = "dynamic_todo_specific"
    _write_dynamic_todo_ssot(tmp_path, ip)

    result = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    plan = json.loads((tmp_path / ip / "logs" / "rtl-gen" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    enable_task = next(
        task for task in plan["tasks"]
        if task["source_ref"] == "registers.register_list.CTRL.fields.enable"
    )
    assert "SSOT ref: registers.register_list.CTRL.fields.enable." in enable_task["detail"]
    assert "Owner: dynamic_todo_specific_core in rtl/dynamic_todo_specific.sv" in enable_task["detail"]
    assert enable_task["ssot_context"]["access"] == "rw"
    assert enable_task["ssot_context"]["reset"] == "0"
    assert any("access policy rw" in item for item in enable_task["criteria"])
    assert any("reset behavior matches SSOT value 0" in item for item in enable_task["criteria"])

    output_rule_task = next(
        task for task in plan["tasks"]
        if task["source_ref"] == "function_model.transactions.FM_ACCEPT.output_rules.result"
    )
    assert output_rule_task["ssot_context"]["expr"] == "value * 2"
    assert any("RTL expression implements SSOT expression value * 2" in item for item in output_rule_task["criteria"])
    assert any("DUT port result is the implementation/observation point" in item for item in output_rule_task["criteria"])


def test_dynamic_rtl_todos_expand_relative_module_refs(tmp_path: Path):
    ip = "dynamic_todo_relative_refs"
    _write_dynamic_todo_ssot(tmp_path, ip)
    ssot_path = tmp_path / ip / "yaml" / f"{ip}.ssot.yaml"
    text = ssot_path.read_text(encoding="utf-8")
    text = text.replace(
        "    implements: [function_model, cycle_model, registers, dataflow, fsm]",
        (
            "    implements: [function_model.transactions.FM_ACCEPT, .FM_ERROR, "
            "function_model.state_variables, function_model.invariants, "
            "cycle_model.handshake_rules.valid_ready_accept, .hold_result_until_ready, "
            "cycle_model.pipeline, cycle_model.ordering, cycle_model.backpressure, "
            "registers, dataflow, fsm]"
        ),
    )
    text = re.sub(r"\n    source_sections: \[.*?\]", "", text)
    text = re.sub(r"\n    function_model_refs: \[.*?\]", "", text)
    text = re.sub(r"\n    cycle_model_refs: \[.*?\]", "", text)
    text = re.sub(r"\n    register_refs: \[.*?\]", "", text)
    text = re.sub(r"\n    dataflow_refs: \[.*?\]", "", text)
    text = re.sub(r"\n    fsm_refs: \[.*?\]", "", text)
    ssot_path.write_text(text, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    plan = json.loads((tmp_path / ip / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    refs = plan["summary"]["owner_modules"][0]["refs"]
    assert "function_model.transactions.FM_ERROR" in refs
    assert "cycle_model.handshake_rules.hold_result_until_ready" in refs
    error_task = next(task for task in plan["tasks"] if task["source_ref"] == "function_model.transactions.FM_ERROR")
    assert error_task["owner_match"] == "function_model.transactions.FM_ERROR"
    assert plan["summary"]["orphan_tasks"] == 0


def test_dynamic_rtl_todos_infer_strong_leaf_and_unique_section_owner(tmp_path: Path):
    ip = "dynamic_todo_owner_infer"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "sub_modules:",
                f"  - name: {ip}_periph",
                f"    file: rtl/{ip}_periph.sv",
                "    ownership: manifest",
                "    implements: [cycle_model.handshake_rules.periph_dr_da]",
                f"  - name: {ip}_engine",
                f"    file: rtl/{ip}_engine.sv",
                "    ownership: manifest",
                "    implements: [fsm.engine]",
                "function_model:",
                "  transactions:",
                "    - id: FM_NOOP",
                "      outputs: [done]",
                "cycle_model:",
                "  handshake_rules:",
                "    - {name: periph_dr, signal: drvalid && drready}",
                "    - {name: periph_da, signal: davalid && daready}",
                "fsm:",
                "  channel_state:",
                "    states: [IDLE, RUN]",
                "    transitions:",
                "      - {from: IDLE, to: RUN, condition: start}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    plan = json.loads((tmp_path / ip / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    periph_dr = next(task for task in plan["tasks"] if task["source_ref"] == "cycle_model.handshake_rules.periph_dr")
    periph_da = next(task for task in plan["tasks"] if task["source_ref"] == "cycle_model.handshake_rules.periph_da")
    fsm_state = next(task for task in plan["tasks"] if task["source_ref"] == "fsm.channel_state.states.state_0")
    noop_tx = next(task for task in plan["tasks"] if task["source_ref"] == "function_model.transactions.FM_NOOP")
    assert periph_dr["owner_module"] == f"{ip}_periph"
    assert periph_da["owner_module"] == f"{ip}_periph"
    assert periph_dr["owner_match"] == "cycle_model.handshake_rules.periph_dr_da"
    assert fsm_state["owner_module"] == f"{ip}_engine"
    assert fsm_state["owner_match"] == "unique_fsm_owner"
    assert noop_tx["owner_module"] == f"{ip}_engine"
    assert plan["summary"]["orphan_tasks"] == 0


def test_dynamic_rtl_todos_infer_owner_from_transaction_semantics(tmp_path: Path):
    ip = "dynamic_semantic_owner"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "sub_modules:",
                f"  - name: {ip}_engine",
                f"    file: rtl/{ip}_engine.sv",
                "    ownership: manifest",
                "    implements: [fsm.engine, cycle_model.pipeline]",
                f"  - name: {ip}_lsq",
                f"    file: rtl/{ip}_lsq.sv",
                "    ownership: manifest",
                "    implements: [function_model.transactions.load, .store, cycle_model.ordering.lsq_order]",
                f"  - name: {ip}_periph",
                f"    file: rtl/{ip}_periph.sv",
                "    ownership: manifest",
                "    implements: [function_model.transactions.peripheral_request, cycle_model.handshake_rules.periph_dr_da]",
                f"  - name: {ip}_axi",
                f"    file: rtl/{ip}_axi.sv",
                "    ownership: manifest",
                "    implements: [cycle_model.handshake_rules.axi_ar, .axi_aw, cycle_model.ordering.axi_outstanding]",
                "function_model:",
                "  state_variables:",
                "    - {name: channel_state, width: 4, reset: 0}",
                "    - {name: outstanding_reads, width: 4, reset: 0}",
                "  transactions:",
                "    - id: FM_DMALD",
                "      name: dmald_load",
                "      preconditions: [channel_state==1, mfifo has space]",
                "      outputs: [outstanding_reads += 1]",
                "      side_effects: [issue AXI AR]",
                "    - id: FM_DMASTP",
                "      name: dmastp_periph_store",
                "      preconditions: [periph davalid acknowledged]",
                "      outputs: [outstanding_writes += 1]",
                "      side_effects: [daready asserted]",
                "cycle_model:",
                "  latency: 1",
                "  handshake_rules:",
                "    - {name: engine_issue, signal: valid && ready}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    load_tx = next(task for task in plan["tasks"] if task["source_ref"] == "function_model.transactions.FM_DMALD")
    load_side_effect = next(
        task
        for task in plan["tasks"]
        if task["source_ref"] == "function_model.transactions.FM_DMALD.side_effects.side_effect_0"
    )
    periph_tx = next(task for task in plan["tasks"] if task["source_ref"] == "function_model.transactions.FM_DMASTP")
    channel_state = next(task for task in plan["tasks"] if task["source_ref"] == "function_model.state_variables.channel_state")
    engine_issue = next(task for task in plan["tasks"] if task["source_ref"] == "cycle_model.handshake_rules.engine_issue")
    assert load_tx["owner_module"] == f"{ip}_lsq"
    assert load_tx["owner_match"].startswith("semantic_terms:")
    assert load_side_effect["owner_module"] == f"{ip}_axi"
    assert periph_tx["owner_module"] == f"{ip}_periph"
    assert channel_state["owner_module"] == f"{ip}_engine"
    assert channel_state["owner_match"] == "control_owner_fallback"
    assert engine_issue["owner_module"] == f"{ip}_engine"


def test_fl_model_decomposition_uses_generic_relative_and_semantic_ownership(tmp_path: Path):
    ip = "fl_semantic_decomp"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "sub_modules:",
                f"  - name: {ip}_engine",
                f"    file: rtl/{ip}_engine.sv",
                "    ownership: manifest",
                "    implements: [fsm.engine, cycle_model.pipeline]",
                f"  - name: {ip}_lsq",
                f"    file: rtl/{ip}_lsq.sv",
                "    ownership: manifest",
                "    implements: [function_model.transactions.load, .store, cycle_model.ordering.lsq_order]",
                f"  - name: {ip}_axi",
                f"    file: rtl/{ip}_axi.sv",
                "    ownership: manifest",
                "    implements: [cycle_model.handshake_rules.axi_ar, .axi_aw, .axi_w]",
                f"  - name: {ip}_merge_buffer",
                f"    file: rtl/{ip}_merge_buffer.sv",
                "    ownership: manifest",
                "    implements: [memory.instances.merge_buffer, dataflow.paths.write_merge]",
                "parameters:",
                "  - {name: MERGE_BUFFER_DEPTH, default: 4}",
                "dataflow:",
                "  paths:",
                f"    - {{name: write_merge, source: {ip}_lsq, sink: {ip}_axi, via: [{ip}_merge_buffer]}}",
                "memory:",
                "  instances:",
                "    - {name: merge_buffer, type: register_array, depth: MERGE_BUFFER_DEPTH, width: 32}",
                "function_model:",
                "  state_variables:",
                "    - {name: channel_state, width: 4, reset: 0}",
                "  transactions:",
                "    - id: FM_DMALD",
                "      name: dmald_load",
                "      outputs: [load data enters mfifo]",
                "      side_effects: [issue AXI AR]",
                "    - id: FM_DMAST",
                "      name: dmast_store",
                "      outputs: [store data leaves mfifo]",
                "      side_effects: [issue AXI AW and W]",
                "cycle_model:",
                "  latency: 1",
                "  handshake_rules:",
                "    - {name: axi_ar, signal: arvalid && arready}",
                "    - {name: axi_aw, signal: awvalid && awready}",
                "    - {name: axi_w, signal: wvalid && wready}",
                "test_requirements:",
                "  scenarios:",
                "    - id: SC_LOAD",
                "      name: load flow",
                "      expected: load transaction completes",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(EMIT_FL_MODEL), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    decomp = json.loads((ip_dir / "model" / "decomposition.json").read_text(encoding="utf-8"))
    assert decomp["complete"] is True
    assert decomp["orphan_function_cycle_refs"] == []
    by_name = {item["name"]: item for item in decomp["module_contracts"]}
    assert "function_model.transactions.fm_dmald" in by_name[f"{ip}_lsq"]["function_model_refs"]
    assert "function_model.transactions.fm_dmast" in by_name[f"{ip}_lsq"]["function_model_refs"]
    assert "function_model.state_variables.channel_state" in by_name[f"{ip}_engine"]["function_model_refs"]
    assert "cycle_model.handshake_rules.axi_w" in by_name[f"{ip}_axi"]["cycle_model_refs"]
    assert by_name[f"{ip}_merge_buffer"]["requires_module_equivalence"] is False
    assert by_name[f"{ip}_merge_buffer"]["blocked"] is False
    assert "memory.instances.merge_buffer" in by_name[f"{ip}_merge_buffer"]["structural_refs"]
    assert "dataflow.paths.write_merge" in by_name[f"{ip}_merge_buffer"]["structural_refs"]
    axi_matches = {item["ref"]: item["matched_ref"] for item in by_name[f"{ip}_axi"]["owner_matches"]}
    assert axi_matches["cycle_model.handshake_rules.axi_w"] == "cycle_model.handshake_rules.axi_w"


def test_dynamic_rtl_todos_add_production_gates_from_ssot_profile(tmp_path: Path):
    ip = "production_todo_probe"
    _write_dynamic_todo_ssot(tmp_path, ip)
    ssot_path = tmp_path / ip / "yaml" / f"{ip}.ssot.yaml"
    ssot_path.write_text(
        ssot_path.read_text(encoding="utf-8")
        + "\nquality_gates:\n"
        + "  rtl_gen:\n"
        + "    profile: production\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    plan = json.loads((tmp_path / ip / "logs" / "rtl-gen" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    assert plan["summary"]["rtl_quality_profile"] == "production"
    assert plan["policy"]["rtl_quality_profile"] == "production"
    gate_tasks = [task for task in plan["tasks"] if task["category"] == "rtl_gate.rtl_gen"]
    gate_kinds = {task["gate_todo"]["kind"] for task in gate_tasks}
    assert {
        "golden_authority_artifacts",
        "cycle_model_artifacts",
        "protocol_assertion_evidence",
        "fl_rtl_goal_audit",
        "coverage_closure",
    }.issubset(gate_kinds)
    assert any(task["source_ref"] == "quality_gates.rtl_gen.fl_rtl_goal_audit" for task in gate_tasks)
    assert any(task["source_ref"] == "quality_gates.rtl_gen.protocol_assertion_evidence" for task in gate_tasks)
    assert plan["summary"]["rtl_gate_todos"] >= 13


def test_dynamic_rtl_todos_gate_rejects_shallow_production_rtl_depth(tmp_path: Path):
    ip = "production_depth_gate"
    ip_dir = tmp_path / ip
    for subdir in ("yaml", "rtl", "list"):
        (ip_dir / subdir).mkdir(parents=True, exist_ok=True)
    output_rules = "\n".join(
        f"        - {{name: rule_{idx}, expr: start_i && rule_{idx}_enable}}"
        for idx in range(16)
    )
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "sub_modules:",
                f"  - name: {ip}",
                f"    file: rtl/{ip}.sv",
                "    ownership: manifest",
                "    cycle_model_refs: [cycle_model]",
                f"  - name: {ip}_engine",
                f"    file: rtl/{ip}_engine.sv",
                "    ownership: manifest",
                "    function_model_refs: [function_model]",
                "function_model:",
                "  transactions:",
                "    - id: FM_RUN",
                "      output_rules:",
                output_rules,
                "cycle_model:",
                "  latency: 2",
                "  handshake_rules:",
                "    - {id: accept, valid: start_i, ready: ready_o}",
                "quality_gates:",
                "  rtl_gen:",
                "    profile: production",
                "filelist:",
                "  rtl:",
                f"    - rtl/{ip}.sv",
                f"    - rtl/{ip}_engine.sv",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input wire clk, input wire start_i, output wire done_o);\n"
        "  wire engine_done;\n"
        f"  {ip}_engine u_engine(.clk(clk), .start_i(start_i), .done_o(engine_done));\n"
        "  assign done_o = engine_done;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}_engine.sv").write_text(
        f"module {ip}_engine(input wire clk, input wire start_i, output wire done_o);\n"
        "  assign done_o = start_i;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\nrtl/{ip}_engine.sv\n", encoding="utf-8")

    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    depth_task = next(
        task
        for task in plan["tasks"]
        if (task.get("gate_todo") or {}).get("kind") == "rtl_implementation_depth_evidence"
    )
    assert depth_task["todo_completion"]["status"] == "open"
    assert "implementation-depth" in depth_task["todo_completion"]["reason"]
    assert (
        plan["rtl_implementation_depth_evidence"]["aggregate"]["depth_score"]
        < plan["rtl_implementation_depth_evidence"]["thresholds"]["min_depth_score"]
    )

    (ip_dir / "rtl" / f"{ip}_engine.sv").write_text(
        f"module {ip}_engine(input wire clk, input wire start_i, output wire done_o);\n"
        "  reg [3:0] state;\n"
        "  reg [3:0] count;\n"
        "  reg done_r;\n"
        "  always @(posedge clk) begin\n"
        "    if (!start_i) begin\n"
        "      state <= 4'd0;\n"
        "      count <= 4'd0;\n"
        "      done_r <= 1'b0;\n"
        "    end else begin\n"
        "      case (state)\n"
        "        4'd0: begin state <= 4'd1; count <= count + 4'd1; done_r <= 1'b0; end\n"
        "        4'd1: begin state <= 4'd2; count <= count + 4'd1; done_r <= 1'b0; end\n"
        "        default: begin state <= 4'd0; done_r <= 1'b1; end\n"
        "      endcase\n"
        "    end\n"
        "  end\n"
        "  always @* begin\n"
        "    if (count == 4'd0) begin\n"
        "      done_r = done_r;\n"
        "    end\n"
        "  end\n"
        "  assign done_o = done_r | (count[0] & start_i);\n"
        "endmodule\n",
        encoding="utf-8",
    )
    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    depth_task = next(
        task
        for task in plan["tasks"]
        if (task.get("gate_todo") or {}).get("kind") == "rtl_implementation_depth_evidence"
    )
    assert depth_task["todo_completion"]["status"] == "pass"
    assert (
        plan["rtl_implementation_depth_evidence"]["aggregate"]["depth_score"]
        >= plan["rtl_implementation_depth_evidence"]["thresholds"]["min_depth_score"]
    )


def test_dynamic_rtl_todos_enforce_ssot_locked_target_scale(tmp_path: Path):
    ip = "production_target_scale"
    ip_dir = tmp_path / ip
    for subdir in ("yaml", "rtl", "list"):
        (ip_dir / subdir).mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "sub_modules:",
                f"  - name: {ip}",
                f"    file: rtl/{ip}.sv",
                "    ownership: manifest",
                "    cycle_model_refs: [cycle_model]",
                f"  - name: {ip}_engine",
                f"    file: rtl/{ip}_engine.sv",
                "    ownership: manifest",
                "    function_model_refs: [function_model]",
                f"  - name: {ip}_fifo",
                f"    file: rtl/{ip}_fifo.sv",
                "    ownership: manifest",
                "    function_model_refs: [function_model]",
                "function_model:",
                "  state_variables:",
                "    - {name: count, width: 8, reset: 0}",
                "  transactions:",
                "    - id: FM_RUN",
                "      outputs: [done]",
                "cycle_model:",
                "  latency: 2",
                "quality_gates:",
                "  rtl_gen:",
                "    profile: production",
                "    target_scale:",
                "      basis: calibrated review target",
                "      source_files_min: 3",
                "      modules_min: 3",
                "      lines_min: 40",
                "      procedural_blocks_min: 2",
                "      state_updates_min: 4",
                "      depth_score_min: 35",
                "      logic_modules_min: 2",
                "      behavior_owner_logic_modules_min: 2",
                "filelist:",
                "  rtl:",
                f"    - rtl/{ip}.sv",
                f"    - rtl/{ip}_engine.sv",
                f"    - rtl/{ip}_fifo.sv",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input wire clk, input wire start_i, output wire done_o);\n"
        "  assign done_o = start_i;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(
        f"rtl/{ip}.sv\nrtl/{ip}_engine.sv\nrtl/{ip}_fifo.sv\n",
        encoding="utf-8",
    )

    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    depth = plan["rtl_implementation_depth_evidence"]
    depth_task = next(
        task
        for task in plan["tasks"]
        if (task.get("gate_todo") or {}).get("kind") == "rtl_implementation_depth_evidence"
    )
    assert plan["summary"]["target_scale_present"] is True
    assert plan["policy"]["rtl_target_scale"]["min_source_files"] == 3
    assert plan["policy"]["rtl_target_scale"]["min_lines"] == 40
    assert depth["thresholds"]["min_source_files"] == 3
    assert depth["thresholds"]["min_modules"] == 3
    assert depth["thresholds"]["min_lines"] == 40
    assert depth_task["todo_completion"]["status"] == "open"
    assert any(issue["source"] == "quality_gates.rtl_gen.target_scale" for issue in depth["issues"])

    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input wire clk, input wire start_i, output wire done_o);\n"
        "  wire engine_done;\n"
        "  wire fifo_done;\n"
        f"  {ip}_engine u_engine(.clk(clk), .start_i(start_i), .done_o(engine_done));\n"
        f"  {ip}_fifo u_fifo(.clk(clk), .start_i(engine_done), .done_o(fifo_done));\n"
        "  assign done_o = engine_done & fifo_done;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}_engine.sv").write_text(
        f"module {ip}_engine(input wire clk, input wire start_i, output wire done_o);\n"
        "  reg [3:0] state;\n"
        "  reg [3:0] count;\n"
        "  always @(posedge clk) begin\n"
        "    if (start_i) begin\n"
        "      state <= state + 4'd1;\n"
        "      count <= count + 4'd1;\n"
        "    end else begin\n"
        "      state <= 4'd0;\n"
        "      count <= 4'd0;\n"
        "    end\n"
        "  end\n"
        "  assign done_o = state[0] & count[0];\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}_fifo.sv").write_text(
        f"module {ip}_fifo(input wire clk, input wire start_i, output wire done_o);\n"
            "  reg [3:0] level;\n"
            "  reg [3:0] watermark;\n"
            "  reg [3:0] occupancy_limit;\n"
            "  wire watermark_hit;\n"
            "  assign watermark_hit = |watermark;\n"
            "  always @(posedge clk) begin\n"
        "    if (start_i) begin\n"
        "      level <= level + 4'd1;\n"
        "      watermark <= level;\n"
        "      occupancy_limit <= watermark + 4'd1;\n"
        "    end else begin\n"
        "      level <= 4'd0;\n"
        "      watermark <= 4'd0;\n"
        "      occupancy_limit <= 4'd0;\n"
        "    end\n"
        "  end\n"
            "  assign done_o = watermark_hit & |occupancy_limit;\n"
        "endmodule\n",
        encoding="utf-8",
    )

    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    depth = plan["rtl_implementation_depth_evidence"]
    depth_task = next(
        task
        for task in plan["tasks"]
        if (task.get("gate_todo") or {}).get("kind") == "rtl_implementation_depth_evidence"
    )
    assert depth["aggregate"]["source_files"] == 3
    assert depth["aggregate"]["modules"] == 3
    assert depth["aggregate"]["lines"] >= 40
    assert depth["aggregate"]["procedural_blocks"] >= 2
    assert depth["aggregate"]["state_updates"] >= 4
    assert depth_task["todo_completion"]["status"] == "pass"


def test_dynamic_rtl_todos_require_locked_authority_manifest_for_production(tmp_path: Path):
    ip = "production_authority_gate"
    ip_dir = tmp_path / ip
    _write_dynamic_todo_ssot(tmp_path, ip)
    ssot_path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    ssot_path.write_text(
        ssot_path.read_text(encoding="utf-8")
        + "\nquality_gates:\n"
        + "  rtl_gen:\n"
        + "    profile: production\n",
        encoding="utf-8",
    )
    for subdir in ("req", "governance", "model", "cov", "verify", "rtl", "list"):
        (ip_dir / subdir).mkdir(parents=True, exist_ok=True)
    (ip_dir / "req" / "requirement.md").write_text("human-approved requirement baseline\n", encoding="utf-8")
    (ip_dir / "model" / "functional_model.py").write_text("class FunctionalModel:\n    pass\n", encoding="utf-8")
    (ip_dir / "model" / "cycle_model.py").write_text("class CycleModel:\n    pass\n", encoding="utf-8")
    (ip_dir / "model" / "fl_model_check.json").write_text(json.dumps({"passed": True}) + "\n", encoding="utf-8")
    (ip_dir / "model" / "decomposition.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "type": "fl_model_decomposition",
                "ip": ip,
                "complete": True,
                "units": [
                    {
                        "name": f"{ip}_core",
                        "rtl_file": f"rtl/{ip}.sv",
                        "function_model_refs": ["function_model.transactions.FM_ACCEPT"],
                        "cycle_model_refs": ["cycle_model.pipeline"],
                        "blocked": False,
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    fcov_payload = {
        "planned_before_rtl": True,
        "bins": [{"id": "FCOV_ACCEPT", "goal_id": "EQ_ACCEPT", "source": "test_requirements.coverage_goals"}],
    }
    (ip_dir / "cov" / "fcov_plan.json").write_text(json.dumps(fcov_payload, indent=2) + "\n", encoding="utf-8")
    (ip_dir / "cov" / "fl_fcov_plan.json").write_text(json.dumps(fcov_payload, indent=2) + "\n", encoding="utf-8")
    (ip_dir / "cov" / "cl_fcov_plan.json").write_text(
        json.dumps({"planned_before_rtl": True, "bins": []}, indent=2) + "\n",
        encoding="utf-8",
    )
    (ip_dir / "verify" / "equivalence_goals.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "summary": {"total": 1, "required": 1, "blocked": 0},
                "goals": [{"goal_id": "EQ_ACCEPT", "kind": "datapath", "blocked": False, "required": True}],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    subprocess.run(
        [sys.executable, str(EMIT_MODEL_SIGNATURE), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        check=True,
    )
    (ip_dir / "governance" / "authority.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "type": "human_llm_authority_manifest",
                "ip": ip,
                "operating_rules": [{"id": "R1"}],
                "human_gates": [{"id": "G1", "status": "pending"}],
                "llm_loops": [{"id": "L1"}],
                "repo_layout": {"locked": [], "llm_editable": [], "agent_runnable_validators": []},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 1, result.stderr or result.stdout
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    authority_gate = next(task for task in plan["tasks"] if (task.get("gate_todo") or {}).get("kind") == "golden_authority_artifacts")
    assert authority_gate["todo_completion"]["status"] == "open"
    assert "authority.json" in authority_gate["todo_completion"]["reason"]

    subprocess.run(
        [sys.executable, str(EMIT_AUTHORITY_MANIFEST), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        check=True,
    )
    result = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 1, result.stderr or result.stdout
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    authority_gate = next(task for task in plan["tasks"] if (task.get("gate_todo") or {}).get("kind") == "golden_authority_artifacts")
    assert authority_gate["todo_completion"]["status"] == "pass"


def test_dynamic_rtl_todos_require_protocol_assertion_sim_evidence_for_production(tmp_path: Path):
    ip = "production_protocol_gate"
    _write_dynamic_todo_ssot(tmp_path, ip)
    ssot_path = tmp_path / ip / "yaml" / f"{ip}.ssot.yaml"
    ssot_path.write_text(
        ssot_path.read_text(encoding="utf-8")
        + "\nquality_gates:\n"
        + "  rtl_gen:\n"
        + "    profile: production\n",
        encoding="utf-8",
    )
    protocol_result = WorkflowStageEngine(tmp_path).run_stage("spa", ip)
    assert protocol_result.status == "pass", protocol_result.message
    for subdir in ("rtl", "list"):
        (tmp_path / ip / subdir).mkdir(exist_ok=True)
    rtl_path = tmp_path / ip / "rtl" / f"{ip}.sv"
    rtl_path.write_text(f"module {ip}(input logic clk, input logic rst_n); endmodule\n", encoding="utf-8")
    (tmp_path / ip / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\n", encoding="utf-8")
    os.utime(rtl_path, (1_700_000_000, 1_700_000_000))

    result = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 1, result.stderr or result.stdout
    plan = json.loads((tmp_path / ip / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    protocol_gate = next(task for task in plan["tasks"] if (task.get("gate_todo") or {}).get("kind") == "protocol_assertion_evidence")
    assert protocol_gate["todo_completion"]["status"] == "open"
    assert "sim/assertion_failures.jsonl" in protocol_gate["todo_completion"]["reason"]

    (tmp_path / ip / "sim").mkdir(exist_ok=True)
    (tmp_path / ip / "sim" / "assertion_failures.jsonl").write_text("", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 1, result.stderr or result.stdout
    plan = json.loads((tmp_path / ip / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    protocol_gate = next(task for task in plan["tasks"] if (task.get("gate_todo") or {}).get("kind") == "protocol_assertion_evidence")
    assert protocol_gate["todo_completion"]["status"] == "pass"


def test_dynamic_rtl_todos_require_fl_rtl_compare_to_cover_all_equivalence_goals(tmp_path: Path):
    ip = "production_compare_gate"
    ip_dir = tmp_path / ip
    _write_dynamic_todo_ssot(tmp_path, ip)
    ssot_path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    ssot_path.write_text(
        ssot_path.read_text(encoding="utf-8")
        + "\nquality_gates:\n"
        + "  rtl_gen:\n"
        + "    profile: production\n",
        encoding="utf-8",
    )
    for subdir in ("rtl", "list", "verify", "sim"):
        (ip_dir / subdir).mkdir(parents=True, exist_ok=True)
    rtl_path = ip_dir / "rtl" / f"{ip}.sv"
    rtl_path.write_text(
        "\n".join(
            [
                f"module {ip}(",
                "    input logic clk,",
                "    input logic rst_n,",
                "    input logic valid,",
                "    output logic ready,",
                "    input logic [7:0] data_in,",
                "    output logic [8:0] result",
                ");",
                "  assign ready = 1'b1;",
                "  assign result = valid ? {1'b0, data_in} + {1'b0, data_in} : 9'd0;",
                "endmodule",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\n", encoding="utf-8")
    (ip_dir / "verify" / "equivalence_goals.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "summary": {"total": 2, "required": 2, "blocked": 0},
                "goals": [
                    {"goal_id": "EQ_ACCEPT", "kind": "datapath", "blocked": False},
                    {"goal_id": "EQ_ERROR", "kind": "error", "blocked": False},
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "sim" / "fl_rtl_goal_audit.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "type": "fl_rtl_goal_audit",
                "status": "pass",
                "summary": {"total_checks": 15, "passed_checks": 15, "failed_checks": 0, "blockers": []},
                "stop_condition": {"fl_rtl_compare_complete": True, "signoff_evidence_backed": True},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    compare_path = ip_dir / "sim" / "fl_rtl_compare.json"
    compare_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "type": "fl_rtl_compare",
                "status": "pass",
                "summary": {"total": 2, "goals_checked": 1, "goals_passed": 1, "goals_failed": 0},
                "goals": [{"goal_id": "EQ_ACCEPT", "status": "pass", "events": 1}],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 1, result.stderr or result.stdout
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    audit_gate = next(task for task in plan["tasks"] if (task.get("gate_todo") or {}).get("kind") == "fl_rtl_goal_audit")
    assert audit_gate["todo_completion"]["status"] == "open"
    assert "EQ_ERROR" in audit_gate["todo_completion"]["reason"]

    compare_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "type": "fl_rtl_compare",
                "status": "pass",
                "summary": {"total": 2, "goals_checked": 2, "goals_passed": 2, "goals_failed": 0},
                "goals": [
                    {"goal_id": "EQ_ACCEPT", "status": "pass", "events": 1},
                    {"goal_id": "EQ_ERROR", "status": "pass", "events": 1},
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 1, result.stderr or result.stdout
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    audit_gate = next(task for task in plan["tasks"] if (task.get("gate_todo") or {}).get("kind") == "fl_rtl_goal_audit")
    assert audit_gate["todo_completion"]["status"] == "pass"


def test_dynamic_rtl_todos_require_rtl_observed_coverage_closure(tmp_path: Path):
    ip = "production_coverage_gate"
    ip_dir = tmp_path / ip
    _write_dynamic_todo_ssot(tmp_path, ip)
    ssot_path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    ssot_path.write_text(
        ssot_path.read_text(encoding="utf-8")
        + "\nquality_gates:\n"
        + "  rtl_gen:\n"
        + "    profile: production\n",
        encoding="utf-8",
    )
    for subdir in ("rtl", "list", "cov"):
        (ip_dir / subdir).mkdir(parents=True, exist_ok=True)
    rtl_path = ip_dir / "rtl" / f"{ip}.sv"
    rtl_path.write_text(
        "\n".join(
            [
                f"module {ip}(",
                "    input logic clk,",
                "    input logic rst_n,",
                "    input logic valid,",
                "    output logic ready,",
                "    input logic [7:0] data_in,",
                "    output logic [8:0] result",
                ");",
                "  assign ready = 1'b1;",
                "  assign result = valid ? {1'b0, data_in} + {1'b0, data_in} : 9'd0;",
                "endmodule",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\n", encoding="utf-8")
    coverage_path = ip_dir / "cov" / "coverage.json"
    coverage_path.write_text(
        json.dumps(
            {
                "status": "pass",
                "limitations": {},
                "functional": {"hit": 1, "total": 1, "pct": 100.0},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 1, result.stderr or result.stdout
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    coverage_gate = next(task for task in plan["tasks"] if (task.get("gate_todo") or {}).get("kind") == "coverage_closure")
    assert coverage_gate["todo_completion"]["status"] == "open"
    assert "ssot_coverage_summary" in coverage_gate["todo_completion"]["reason"]

    coverage_path.write_text(
        json.dumps(
            {
                "source": "ssot_coverage_summary",
                "status": "pass",
                "limitations": {},
                "functional": {"hit": 1, "total": 1, "pct": 100.0},
                "planned_bins": [{"id": "FCOV_ACCEPT"}],
                "rtl_observed": {
                    "status": "pass",
                    "scoreboard_events": 1,
                    "scoreboard_passed_events_with_refs": 1,
                    "goal_refs": ["FCOV_ACCEPT"],
                    "missing_bins": [],
                    "invalid_rows": [],
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 1, result.stderr or result.stdout
    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    coverage_gate = next(task for task in plan["tasks"] if (task.get("gate_todo") or {}).get("kind") == "coverage_closure")
    assert coverage_gate["todo_completion"]["status"] == "pass"


def test_dynamic_rtl_todos_block_missing_mandatory_ssot_sections(tmp_path: Path):
    ip = "dynamic_todo_blocked"
    _write_dynamic_todo_ssot(tmp_path, ip, include_function=False, include_cycle=False)

    result = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 2
    plan = json.loads((tmp_path / ip / "logs" / "rtl-gen" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    assert plan["gate"]["status"] == "blocked"
    assert plan["summary"]["blocking_questions"] == 2
    blocker = json.loads((tmp_path / ip / "rtl" / "rtl_blocked.json").read_text(encoding="utf-8"))
    question_ids = [q["id"] for q in blocker["questions"]]
    assert "RTL_DYNAMIC_TODO_SSOT_REQUIRED_SECTIONS" in question_ids


def test_dynamic_rtl_todo_audit_rejects_missing_rtl_evidence(tmp_path: Path):
    ip = "dynamic_todo_audit_probe"
    _write_dynamic_todo_ssot(tmp_path, ip)

    result = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 1
    plan = json.loads((tmp_path / ip / "logs" / "rtl-gen" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    assert plan["gate"]["status"] == "fail"
    assert plan["gate"]["static_missing"] > 0
    assert plan["summary"]["rtl_gate_todos"] >= 6
    compile_gate = next(task for task in plan["tasks"] if (task.get("gate_todo") or {}).get("kind") == "dut_compile")
    lint_gate = next(task for task in plan["tasks"] if (task.get("gate_todo") or {}).get("kind") == "dut_lint")
    closure_gate = next(task for task in plan["tasks"] if (task.get("gate_todo") or {}).get("kind") == "dynamic_todo_closure")
    assert compile_gate["todo_completion"]["status"] == "open"
    assert "rtl_compile.json" in compile_gate["todo_completion"]["reason"]
    assert lint_gate["todo_completion"]["status"] == "open"
    assert "dut_lint.json" in lint_gate["todo_completion"]["reason"]
    assert closure_gate["todo_completion"]["status"] == "open"
    assert plan["static_rtl_evidence"]["checked"] > 0


def test_dynamic_rtl_todo_audit_rejects_stale_compile_and_lint_evidence(tmp_path: Path):
    ip = "dynamic_todo_stale_evidence"
    ip_dir = tmp_path / ip
    _write_dynamic_todo_ssot(tmp_path, ip)
    for subdir in ("rtl", "list", "lint"):
        (ip_dir / subdir).mkdir(parents=True, exist_ok=True)
    rtl_path = ip_dir / "rtl" / f"{ip}.sv"
    rtl_path.write_text(
        "\n".join(
            [
                f"module {ip}(",
                "    input logic clk,",
                "    input logic rst_n,",
                "    input logic valid,",
                "    output logic ready,",
                "    input logic [7:0] data_in,",
                "    output logic [8:0] result",
                ");",
                f"  {ip}_core u_core (",
                "    .clk(clk), .rst_n(rst_n), .valid(valid), .ready(ready), .data_in(data_in), .result(result)",
                "  );",
                "endmodule",
                f"module {ip}_core(",
                "    input logic clk,",
                "    input logic rst_n,",
                "    input logic valid,",
                "    output logic ready,",
                "    input logic [7:0] data_in,",
                "    output logic [8:0] result",
                ");",
                "  always_ff @(posedge clk or negedge rst_n) begin",
                "    if (!rst_n) result <= '0;",
                "    else if (valid && ready) result <= {1'b0, data_in} + {1'b0, data_in};",
                "  end",
                "  assign ready = 1'b1;",
                "endmodule",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\n", encoding="utf-8")
    compile_path = ip_dir / "rtl" / "rtl_compile.json"
    lint_path = ip_dir / "lint" / "dut_lint.json"
    compile_path.write_text(
        json.dumps({"passed": True, "dut_only": True, "errors": 0, "diagnostics": 0, "style_violations": 0}) + "\n",
        encoding="utf-8",
    )
    lint_path.write_text(
        json.dumps({"passed": True, "dut_only": True, "errors": 0, "warnings": 0, "suppression_violation_count": 0}) + "\n",
        encoding="utf-8",
    )
    old_time = 1_700_000_000
    new_time = old_time + 100
    os.utime(compile_path, (old_time, old_time))
    os.utime(lint_path, (old_time, old_time))
    os.utime(rtl_path, (new_time, new_time))

    result = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 1
    plan = json.loads((tmp_path / ip / "logs" / "rtl-gen" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    compile_gate = next(task for task in plan["tasks"] if (task.get("gate_todo") or {}).get("kind") == "dut_compile")
    lint_gate = next(task for task in plan["tasks"] if (task.get("gate_todo") or {}).get("kind") == "dut_lint")
    assert compile_gate["todo_completion"]["status"] == "open"
    assert "older than current RTL source" in compile_gate["todo_completion"]["reason"]
    assert lint_gate["todo_completion"]["status"] == "open"
    assert "older than current RTL source" in lint_gate["todo_completion"]["reason"]


def test_dynamic_rtl_todo_audit_rejects_compile_and_lint_source_set_mismatch(tmp_path: Path):
    ip = "dynamic_todo_source_set_evidence"
    ip_dir = tmp_path / ip
    _write_dynamic_todo_ssot(tmp_path, ip)
    for subdir in ("rtl", "list", "lint"):
        (ip_dir / subdir).mkdir(parents=True, exist_ok=True)
    (ip_dir / "rtl" / f"{ip}.sv").write_text(f"module {ip}; endmodule\n", encoding="utf-8")
    (ip_dir / "rtl" / f"{ip}_engine.sv").write_text(f"module {ip}_engine; endmodule\n", encoding="utf-8")
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\nrtl/{ip}_engine.sv\n", encoding="utf-8")
    compile_path = ip_dir / "rtl" / "rtl_compile.json"
    lint_path = ip_dir / "lint" / "dut_lint.json"
    compile_path.write_text(
        json.dumps(
            {
                "passed": True,
                "dut_only": True,
                "errors": 0,
                "diagnostics": 0,
                "style_violations": 0,
                "rtl_files": [f"rtl/{ip}.sv"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    lint_path.write_text(
        json.dumps(
            {
                "passed": True,
                "dut_only": True,
                "errors": 0,
                "warnings": 0,
                "suppression_violation_count": 0,
                "rtl_files": [f"rtl/{ip}.sv"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    now = 1_700_000_100
    os.utime(ip_dir / "rtl" / f"{ip}.sv", (now, now))
    os.utime(ip_dir / "rtl" / f"{ip}_engine.sv", (now, now))
    os.utime(compile_path, (now + 10, now + 10))
    os.utime(lint_path, (now + 10, now + 10))

    result = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 1
    plan = json.loads((tmp_path / ip / "logs" / "rtl-gen" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    compile_gate = next(task for task in plan["tasks"] if (task.get("gate_todo") or {}).get("kind") == "dut_compile")
    lint_gate = next(task for task in plan["tasks"] if (task.get("gate_todo") or {}).get("kind") == "dut_lint")
    assert compile_gate["todo_completion"]["status"] == "open"
    assert "does not cover current DUT filelist" in compile_gate["todo_completion"]["reason"]
    assert f"rtl/{ip}_engine.sv" in compile_gate["todo_completion"]["reason"]
    assert lint_gate["todo_completion"]["status"] == "open"
    assert "does not cover current DUT filelist" in lint_gate["todo_completion"]["reason"]
    assert f"rtl/{ip}_engine.sv" in lint_gate["todo_completion"]["reason"]


def test_dynamic_rtl_todo_audit_rejects_partial_authoring_provenance_rtl_files(tmp_path: Path):
    ip = "dynamic_todo_authoring_scope"
    ip_dir = tmp_path / ip
    for subdir in ("yaml", "rtl", "list"):
        (ip_dir / subdir).mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "sub_modules:",
                f"  - name: {ip}",
                f"    file: rtl/{ip}.sv",
                "    ownership: manifest",
                "    cycle_model_refs: [cycle_model]",
                f"  - name: {ip}_engine",
                f"    file: rtl/{ip}_engine.sv",
                "    ownership: manifest",
                "    function_model_refs: [function_model]",
                "function_model:",
                "  transactions:",
                "    - id: FM_RUN",
                "      output_rules:",
                "        - {name: engine_done, expr: payload_flag && engine_done}",
                "cycle_model:",
                "  latency: 1",
                "filelist:",
                "  rtl:",
                f"    - rtl/{ip}.sv",
                f"    - rtl/{ip}_engine.sv",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(f"module {ip}; endmodule\n", encoding="utf-8")
    (ip_dir / "rtl" / f"{ip}_engine.sv").write_text(f"module {ip}_engine; endmodule\n", encoding="utf-8")
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\nrtl/{ip}_engine.sv\n", encoding="utf-8")

    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        check=False,
        capture_output=True,
        text=True,
    )
    todo_path = ip_dir / "rtl" / "rtl_todo_plan.json"

    def stable_json_sha256(path: Path) -> str:
        volatile = {
            "connection_contract_suggestions",
            "generated_at",
            "gate",
            "manifest_hierarchy_evidence",
            "manifest_signal_flow_evidence",
            "owner_logic_evidence",
            "reference_profile",
            "reference_scale_gap",
            "rtl_implementation_depth_evidence",
            "rtl_placeholder_free_evidence",
            "static_evidence",
            "static_rtl_evidence",
            "todo_completion",
            "top_input_consumption_evidence",
            "top_io_contract_evidence",
            "top_output_drive_evidence",
        }
        data = json.loads(path.read_text(encoding="utf-8"))

        def normalize(value):
            if isinstance(value, dict):
                return {str(key): normalize(item) for key, item in value.items() if str(key) not in volatile}
            if isinstance(value, list):
                return [normalize(item) for item in value]
            return value

        payload = json.dumps(normalize(data), sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    (ip_dir / "rtl" / "rtl_authoring_provenance.json").write_text(
        json.dumps(
            {
                "type": "rtl_authoring_provenance",
                "agent": "common_ai_agent",
                "workflow": "rtl-gen",
                "surface": "headless_common_engine",
                "todo_plan_sha256": stable_json_sha256(todo_path),
                "rtl_files": [f"rtl/{ip}.sv"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path), "--audit-rtl"],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 1
    plan = json.loads((tmp_path / ip / "logs" / "rtl-gen" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    author_gate = next(task for task in plan["tasks"] if (task.get("gate_todo") or {}).get("kind") == "common_ai_agent_authoring")
    assert author_gate["todo_completion"]["status"] == "open"
    assert "rtl_files_missing_manifest" in author_gate["todo_completion"]["reason"]
    assert f"rtl/{ip}_engine.sv" in author_gate["todo_completion"]["reason"]


def test_ssot_rtl_template_is_seed_not_locked_to_fixed_task_count():
    template = json.loads((SOURCE_ROOT / "workflow" / "rtl-gen" / "todo_templates" / "ssot-rtl.json").read_text(encoding="utf-8"))
    assert template["lock_additions"] is False
    assert "seed" in template["description"].lower()
    assert len(template["tasks"]) < 10


def test_rtl_stage_uses_dynamic_todo_gate_before_generation(tmp_path: Path):
    ip = "rtl_stage_dynamic_gate"
    _write_dynamic_todo_ssot(tmp_path, ip, include_function=False, include_cycle=False)

    result = WorkflowStageEngine(tmp_path).run_stage("ssot-rtl", ip)

    assert result.status == "human_gate", result.message
    assert result.runs[0].label == "derive_rtl_todos"
    assert result.runs[0].returncode == 2
    assert result.runs[1].label == "rtl_preflight"
    assert result.runs[1].returncode == 2
    assert result.runs[2].label == "audit_rtl_todos"
    assert result.runs[2].returncode == 2
    assert "rtl_dynamic_todos:" in result.message
    assert "gate: blocked" in result.message
    assert (tmp_path / ip / "rtl" / "rtl_todo_plan.json").is_file()
    assert (tmp_path / ip / "rtl" / "rtl_blocked.json").is_file()


def test_rtl_stage_reports_orphan_groups_from_blocker(tmp_path: Path):
    ip = "rtl_stage_orphan_groups"
    _write_dynamic_todo_ssot(tmp_path, ip)
    ssot_path = tmp_path / ip / "yaml" / f"{ip}.ssot.yaml"
    text = ssot_path.read_text(encoding="utf-8")
    text = re.sub(
        r"sub_modules:\n(?:  - .*\n(?:    .*\n)*)parameters:",
        (
            "sub_modules:\n"
            f"  - name: {ip}_cycle\n"
            f"    file: rtl/{ip}_cycle.sv\n"
            "    ownership: manifest\n"
            "    implements: [cycle_model.handshake_rules.valid_ready_accept]\n"
            f"  - name: {ip}_regs\n"
            f"    file: rtl/{ip}_regs.sv\n"
            "    ownership: manifest\n"
            "    implements: [registers]\n"
            "parameters:"
        ),
        text,
        count=1,
    )
    ssot_path.write_text(text, encoding="utf-8")

    result = WorkflowStageEngine(tmp_path).run_stage("ssot-rtl", ip)

    assert result.status == "human_gate", result.message
    assert "orphan_groups:" in result.message
    assert "function_model.output:" in result.message
    assert "field=sub_modules[].function_model_refs" in result.message


def test_ssot_to_rtl_preflight_does_not_emit_fixed_template_rtl(tmp_path: Path):
    ip = "rtl_preflight_no_template"
    _write_dynamic_todo_ssot(tmp_path, ip)
    ssot_path = tmp_path / ip / "yaml" / f"{ip}.ssot.yaml"
    ssot_path.write_text(
        ssot_path.read_text(encoding="utf-8").replace(
            "        - {name: result, direction: output, width: 9}\n",
            "        - {name: result, direction: output, width: 9}\n"
            "        - {name: result_valid, direction: output, width: 1}\n",
        )
        + "\nrtl_contract:\n"
        + "  clock: clk\n"
        + "  reset: rst_n\n"
        + "  reset_active: low\n"
        + "  input_map:\n"
        + "    value: data_in\n"
        + "  output_map:\n"
        + "    result: result\n"
        + "    result_valid: result_valid\n",
        encoding="utf-8",
    )

    derive = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert derive.returncode == 0, derive.stderr or derive.stdout

    result = subprocess.run(
        [sys.executable, str(SSOT_TO_RTL), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 2
    assert "[RTL BLOCKED]" in result.stdout
    assert "LLM-authored RTL" in result.stdout
    assert not (tmp_path / ip / "rtl" / f"{ip}.sv").exists()
    assert not (tmp_path / ip / "list" / f"{ip}.f").exists()
    blocked = json.loads((tmp_path / ip / "rtl" / "rtl_blocked.json").read_text(encoding="utf-8"))
    assert blocked["questions"][0]["id"] == "LLM_RTL_IMPLEMENTATION_REQUIRED"


def test_ssot_to_rtl_accepts_implements_as_module_contract_refs(tmp_path: Path):
    ip = "rtl_implements_refs"
    _write_dynamic_todo_ssot(tmp_path, ip)
    ssot_path = tmp_path / ip / "yaml" / f"{ip}.ssot.yaml"
    text = ssot_path.read_text(encoding="utf-8")
    text = text.replace(
        "        - {name: result, direction: output, width: 9}\n",
        "        - {name: result, direction: output, width: 9}\n"
        "        - {name: result_valid, direction: output, width: 1}\n",
    )
    text = re.sub(r"\n    source_sections: \[.*?\]", "", text)
    text = re.sub(r"\n    function_model_refs: \[.*?\]", "", text)
    text = re.sub(r"\n    cycle_model_refs: \[.*?\]", "", text)
    text = re.sub(r"\n    register_refs: \[.*?\]", "", text)
    text = re.sub(r"\n    dataflow_refs: \[.*?\]", "", text)
    text = re.sub(r"\n    fsm_refs: \[.*?\]", "", text)
    text += (
        "\nrtl_contract:\n"
        "  clock: clk\n"
        "  reset: rst_n\n"
        "  reset_active: low\n"
        "  input_map:\n"
        "    value: data_in\n"
        "  output_map:\n"
        "    result: result\n"
        "    result_valid: result_valid\n"
    )
    ssot_path.write_text(text, encoding="utf-8")

    derive = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert derive.returncode == 0, derive.stderr or derive.stdout

    result = subprocess.run(
        [sys.executable, str(SSOT_TO_RTL), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 2
    assert "[RTL BLOCKED]" in result.stdout
    assert "RTL_MODULE_CONTRACTS" not in result.stdout
    blocked = json.loads((tmp_path / ip / "rtl" / "rtl_blocked.json").read_text(encoding="utf-8"))
    question_ids = {q["id"] for q in blocked["questions"]}
    assert "LLM_RTL_IMPLEMENTATION_REQUIRED" in question_ids
    assert "RTL_MODULE_CONTRACTS" not in question_ids


def test_ssot_to_rtl_preserves_dynamic_todo_blocker_questions(tmp_path: Path):
    ip = "rtl_preserve_dynamic_blocker"
    _write_dynamic_todo_ssot(tmp_path, ip)
    ssot_path = tmp_path / ip / "yaml" / f"{ip}.ssot.yaml"
    text = ssot_path.read_text(encoding="utf-8")
    text = text.replace(
        "    implements: [function_model, cycle_model, registers, dataflow, fsm]",
        "    implements: [cycle_model.handshake_rules.valid_ready_accept]",
    )
    text = re.sub(r"\n    source_sections: \[.*?\]", "", text)
    text = re.sub(r"\n    function_model_refs: \[.*?\]", "", text)
    text = re.sub(r"\n    register_refs: \[.*?\]", "", text)
    text = re.sub(r"\n    dataflow_refs: \[.*?\]", "", text)
    text = re.sub(r"\n    fsm_refs: \[.*?\]", "", text)
    ssot_path.write_text(text, encoding="utf-8")

    rtl_dir = tmp_path / ip / "rtl"
    rtl_dir.mkdir(parents=True, exist_ok=True)
    (rtl_dir / "rtl_todo_plan.json").write_text(
        json.dumps(
            {
                "summary": {"orphan_tasks": 1},
                "blockers": [],
                "orphans": [
                    {
                        "source_ref": "function_model.transactions.FM_ACCEPT",
                        "category": "function_model.transaction",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (rtl_dir / "rtl_blocked.json").write_text(
        json.dumps({
            "questions": [
                {
                    "id": "RTL_DYNAMIC_TODO_OWNERSHIP",
                    "decision_needed": "Assign every SSOT-derived task to an RTL module owner.",
                    "orphan_refs": ["function_model.transactions.FM_ACCEPT"],
                }
            ]
        }),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(SSOT_TO_RTL), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 2
    blocked = json.loads((tmp_path / ip / "rtl" / "rtl_blocked.json").read_text(encoding="utf-8"))
    question_ids = {q["id"] for q in blocked["questions"]}
    assert "RTL_CLOCK_PORT" in question_ids
    assert "RTL_DYNAMIC_TODO_OWNERSHIP" in question_ids
    assert f"{len(blocked['questions'])} fix/gate(s)" in result.stdout
    for qid in question_ids:
        assert qid in result.stdout
    dynamic = next(q for q in blocked["questions"] if q["id"] == "RTL_DYNAMIC_TODO_OWNERSHIP")
    assert dynamic["orphan_groups"][0]["section_id"] == "function_model"
    assert dynamic["orphan_groups"][0]["required_field"] == "sub_modules[].function_model_refs"
