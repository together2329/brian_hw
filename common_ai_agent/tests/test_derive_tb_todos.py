from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.workflow_stage_engine import ToolRun, WorkflowStageEngine


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "workflow" / "tb-gen" / "scripts" / "derive_tb_todos.py"


def _write_ip(root: Path, ip: str) -> Path:
    ip_dir = root / ip
    for rel in ("yaml", "req", "verify", "rtl", "list"):
        (ip_dir / rel).mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        f"""
top_module:
  name: {ip}_top
io_list:
  clock_domains:
    - name: sysclk
      clock_signal: clk
      ports:
        - name: clk
          direction: input
          width: 1
          timing:
            kind: clock
  resets:
    - name: rst
      clock_domain: sysclk
      ports:
        - name: rst_n
          direction: input
          width: 1
          timing:
            kind: reset
            clock_domain: sysclk
  interfaces:
    - name: ctrl
      clock_domain: sysclk
      ports:
        - name: cmd_valid
          direction: input
          width: 1
        - name: cmd_ready
          direction: output
          width: 1
        - name: rsp_data
          direction: output
          width: 32
function_model:
  transactions:
    - id: READ
      behavioral_contract_refs: [BC_READ]
      preconditions: ["cmd_valid == 1"]
      outputs:
        - name: rsp_data
      output_rules:
        - name: rsp_data
          port: rsp_data
          expr: state_count
      state_updates:
        - name: state_count
          expr: state_count + 1
  state_variables:
    - name: state_count
      width: 32
      reset: 0
cycle_model:
  handshake_rules:
    - name: ctrl_accept
      behavioral_contract_refs: [BC_READ]
      valid: cmd_valid
      ready: cmd_ready
      condition: cmd_valid && cmd_ready
test_requirements:
  scenarios:
    - id: SC_READ
      source_refs: [BC_READ]
      stimulus: "drive cmd_valid"
      expected: "rsp_data follows state_count"
  coverage_goals:
    function:
      bins:
        - id: FCOV_READ
          source_ref: BC_READ
quality_gates:
  tb_gen:
    require_scoreboard: true
""",
        encoding="utf-8",
    )
    (ip_dir / "req" / "obligations.json").write_text(
        json.dumps(
            {
                "ip": ip,
                "obligations": [
                    {
                        "obligation_id": "OBL_READ",
                        "requirement_refs": ["REQ_READ"],
                        "statement": "Expose read transaction behavior.",
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "req" / "behavioral_contracts.json").write_text(
        json.dumps(
            {
                "ip": ip,
                "contracts": [
                    {
                        "id": "BC_READ",
                        "obligations": ["OBL_READ"],
                        "inputs": ["cmd_valid", "cmd_ready"],
                        "outputs": ["rsp_data"],
                        "decision_table": [
                            {
                                "when": "cmd_valid == 1 and cmd_ready == 1",
                                "then": {"rsp_data": "state_count"},
                            }
                        ],
                        "stage_contracts": [
                            {
                                "stage": "tb-gen",
                                "observable": "scoreboard_events.jsonl goal EQ_READ",
                                "pass_condition": "passing row observes rsp_data",
                            }
                        ],
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "req" / "structural_contracts.json").write_text(
        json.dumps(
            {
                "ip": ip,
                "contracts": [
                    {
                        "id": "SC_CTRL",
                        "obligations": ["OBL_READ"],
                        "signals": [
                            {"name": "clk", "dir": "input", "width": 1, "timing": {"kind": "clock"}},
                            {
                                "name": "rst_n",
                                "dir": "input",
                                "width": 1,
                                "timing": {"kind": "reset", "clock_domain": "sysclk"},
                            },
                            {
                                "name": "cmd_valid",
                                "dir": "input",
                                "width": 1,
                                "timing": {"kind": "sync", "clock_domain": "sysclk"},
                            },
                            {
                                "name": "cmd_ready",
                                "dir": "output",
                                "width": 1,
                                "timing": {"kind": "sync", "clock_domain": "sysclk"},
                            },
                            {
                                "name": "rsp_data",
                                "dir": "output",
                                "width": 32,
                                "timing": {"kind": "sync", "clock_domain": "sysclk"},
                            },
                        ],
                        "clock_domains": [{"id": "sysclk", "clock_signal": "clk"}],
                        "reset_domains": [{"id": "rst", "reset_signal": "rst_n", "clock_domain": "sysclk"}],
                        "interfaces": [{"id": "ctrl", "signals": ["cmd_valid", "cmd_ready", "rsp_data"], "clock_domain": "sysclk"}],
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "verify" / "equivalence_goals.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "goals": [
                    {
                        "goal_id": "EQ_READ",
                        "required": True,
                        "coverage_refs": ["FCOV_READ"],
                        "stimulus_contract": {"source_refs": ["BC_READ"]},
                        "expected_contract": {"source_refs": ["BC_READ"]},
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / "rtl_contract.json").write_text(
        json.dumps(
            {
                "type": "generic_ssot_rule_rtl_contract",
                "top": f"{ip}_top",
                "contract": {
                    "clock": "clk",
                    "reset": "rst_n",
                    "reset_active": "low",
                    "input_map": {"cmd_valid": "cmd_valid"},
                    "outputs": [{"name": "rsp_data", "port": "rsp_data"}],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return ip_dir


def _run(root: Path, ip: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), ip, "--root", str(root), *args],
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )


def _write_tb_artifacts(ip_dir: Path, ip: str) -> None:
    tb_dir = ip_dir / "tb" / "cocotb"
    tb_dir.mkdir(parents=True, exist_ok=True)
    for name in (
        f"test_{ip}.py",
        "test_runner.py",
        "transactions.py",
        "sequences.py",
        "agents.py",
        "tb_coverage.py",
        "uvm_env.py",
    ):
        (tb_dir / name).write_text("print('ok')\n", encoding="utf-8")
    (tb_dir / "scoreboard.py").write_text("from equivalence_scoreboard import EquivalenceScoreboard\n", encoding="utf-8")
    (tb_dir / "tb_manifest.json").write_text(json.dumps({"top": f"{ip}_top"}) + "\n", encoding="utf-8")
    (tb_dir / "tb_generation.json").write_text(json.dumps({"status": "pass"}) + "\n", encoding="utf-8")


def test_derive_tb_todos_builds_contract_ledger_with_signal_timing(tmp_path: Path) -> None:
    ip = "tb_contract_demo"
    _write_ip(tmp_path, ip)

    result = _run(tmp_path, ip)

    assert result.returncode == 0, result.stderr + result.stdout
    plan = json.loads((tmp_path / ip / "tb" / "tb_todo_plan.json").read_text(encoding="utf-8"))
    assert plan["gate"]["status"] == "planned"
    assert plan["summary"]["locked_truth_behavioral_contracts"] == 1
    assert plan["summary"]["locked_truth_structural_contracts"] == 1
    categories = plan["summary"]["by_category"]
    assert categories["contract.behavioral.scoreboard"] == 1
    assert categories["contract.structural.signal"] == 5
    signal_rows = [row for row in plan["tasks"] if row["category"] == "contract.structural.signal"]
    cmd_valid = next(row for row in signal_rows if row["ssot_context"]["signal"]["name"] == "cmd_valid")
    assert cmd_valid["ssot_context"]["effective_timing"] == {"kind": "sync", "clock_domain": "sysclk"}
    assert (tmp_path / ip / "todo" / "tb_todo_tracker.json").is_file()


def test_audit_tb_passes_authoring_and_leaves_validation_pending(tmp_path: Path) -> None:
    ip = "tb_authoring_demo"
    ip_dir = _write_ip(tmp_path, ip)
    _write_tb_artifacts(ip_dir, ip)

    result = _run(tmp_path, ip, "--audit-tb")

    assert result.returncode == 0, result.stderr + result.stdout
    plan = json.loads((ip_dir / "tb" / "tb_todo_plan.json").read_text(encoding="utf-8"))
    assert plan["gate"]["status"] == "pass"
    assert plan["todo_completion"]["authoring_todos_pass"] is True
    assert plan["todo_completion"]["validation_open_tasks"] > 0
    assert plan["todo_completion"]["all_required_todos_pass"] is False


def test_audit_evidence_closes_scoreboard_and_coverage_contracts(tmp_path: Path) -> None:
    ip = "tb_evidence_demo"
    ip_dir = _write_ip(tmp_path, ip)
    _write_tb_artifacts(ip_dir, ip)
    (ip_dir / "sim").mkdir(parents=True, exist_ok=True)
    (ip_dir / "cov").mkdir(parents=True, exist_ok=True)
    (ip_dir / "sim" / "scoreboard_events.jsonl").write_text(
        json.dumps(
            {
                "goal_id": "EQ_READ",
                "scenario_id": "SC_READ",
                "cycle": 3,
                "stimulus": {"cmd_valid": 1},
                "fl_expected": {"rsp_data": 0},
                "rtl_observed": {"rsp_data": 0},
                "passed": True,
                "coverage_refs": ["FCOV_READ"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "cov" / "coverage.json").write_text(
        json.dumps({"status": "pass", "rtl_observed": {"status": "pass", "missing_bins": [], "invalid_rows": []}}) + "\n",
        encoding="utf-8",
    )

    result = _run(tmp_path, ip, "--audit-evidence")

    assert result.returncode == 0, result.stderr + result.stdout
    plan = json.loads((ip_dir / "tb" / "tb_todo_plan.json").read_text(encoding="utf-8"))
    assert plan["gate"]["status"] == "pass"
    assert plan["todo_completion"]["all_required_todos_pass"] is True
    assert plan["todo_completion"]["validation_open_tasks"] == 0


def test_stage_engine_tb_runs_contract_ledger_before_and_after_generation(tmp_path: Path, monkeypatch) -> None:
    ip = "tb_stage_demo"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text("top_module:\n  name: tb_stage_demo_top\n", encoding="utf-8")
    calls: list[str] = []

    def write_plan(status: str) -> None:
        plan = {
            "schema_version": 1,
            "type": "ssot_derived_tb_todo_plan",
            "ip": ip,
            "top": "tb_stage_demo_top",
            "summary": {"total_tasks": 3},
            "gate": {"status": status, "authoring_open_todos": 0, "validation_open_todos": 2},
            "todo_completion": {"authoring_todos_pass": status == "pass", "all_required_todos_pass": False},
            "tasks": [],
        }
        (ip_dir / "tb").mkdir(parents=True, exist_ok=True)
        (ip_dir / "tb" / "tb_todo_plan.json").write_text(json.dumps(plan) + "\n", encoding="utf-8")
        (ip_dir / "tb" / "tb_todo_tracker.json").write_text(json.dumps({"tasks": []}) + "\n", encoding="utf-8")
        (ip_dir / "tb" / "tb_traceability.json").write_text(json.dumps({"rows": []}) + "\n", encoding="utf-8")

    def write_tb_files() -> None:
        tb_dir = ip_dir / "tb" / "cocotb"
        tb_dir.mkdir(parents=True, exist_ok=True)
        for name in (f"test_{ip}.py", "test_runner.py"):
            (tb_dir / name).write_text("print('ok')\n", encoding="utf-8")
        (tb_dir / "tb_manifest.json").write_text(json.dumps({"top": "tb_stage_demo_top"}) + "\n", encoding="utf-8")
        (tb_dir / "tb_generation.json").write_text(json.dumps({"status": "pass"}) + "\n", encoding="utf-8")

    def fake_run_tool(self, label: str, command: list[str], timeout_s: int = 180) -> ToolRun:
        calls.append(label)
        if label == "derive_tb_todos":
            write_plan("planned")
        elif label == "emit_goal_scoreboard_cocotb":
            write_tb_files()
        elif label == "audit_tb_todos":
            write_plan("pass")
        return ToolRun(label=label, command=command, returncode=0, stdout=f"{label} ok")

    monkeypatch.setattr(WorkflowStageEngine, "_run_tool", fake_run_tool)

    result = WorkflowStageEngine(tmp_path, source_root=REPO).run_stage("ssot-tb-cocotb", ip)

    assert result.status == "pass"
    assert calls == [
        "derive_tb_todos",
        "emit_goal_scoreboard_cocotb",
        "check_pyuvm_structure",
        "equivalence_scoreboard_self_check",
        "audit_tb_todos",
    ]
    assert "dynamic_todos" in result.message
    assert result.metadata["tb_todo_plan"]["gate"]["status"] == "pass"


# ---------------------------------------------------------------------------
# Mutation-gate negative tests (A0)
#
# A gate's defining test is the FAIL case: start from a known-good fixture that
# legitimately passes, degrade exactly one thing the gate claims to enforce, and
# assert the gate STOPS reporting "pass". These reproduce the content-blind
# silent-PASS holes (HIGH-1/2/3) and are the red harness that A1-A3 must turn
# green.
# ---------------------------------------------------------------------------

_GOOD_EVENT = {
    "goal_id": "EQ_READ",
    "scenario_id": "SC_READ",
    "cycle": 3,
    "stimulus": {"cmd_valid": 1},
    "fl_expected": {"rsp_data": 0},
    "rtl_observed": {"rsp_data": 0},
    "passed": True,
    "coverage_refs": ["FCOV_READ"],
}
_GOOD_COVERAGE = {
    "status": "pass",
    "rtl_observed": {"status": "pass", "missing_bins": [], "invalid_rows": []},
}


def _write_evidence(ip_dir: Path, *, event: dict, coverage: dict) -> None:
    (ip_dir / "sim").mkdir(parents=True, exist_ok=True)
    (ip_dir / "cov").mkdir(parents=True, exist_ok=True)
    (ip_dir / "sim" / "scoreboard_events.jsonl").write_text(
        json.dumps(event) + "\n", encoding="utf-8"
    )
    (ip_dir / "cov" / "coverage.json").write_text(
        json.dumps(coverage) + "\n", encoding="utf-8"
    )


def _mut_comment_only_scoreboard(ip_dir: Path, ip: str) -> None:
    # HIGH-1: substring "EquivalenceScoreboard" present, but only inside a comment
    # — no real import/usage. A hollow scoreboard must not pass authoring.
    (ip_dir / "tb" / "cocotb" / "scoreboard.py").write_text(
        "# TODO: someday wire EquivalenceScoreboard\n", encoding="utf-8"
    )


def _mut_empty_tb_bodies(ip_dir: Path, ip: str) -> None:
    # HIGH-1: scoreboard import kept intact, but the files that should carry the
    # contract stimulus/sequences are gutted. File-existence-only checks miss this.
    for name in ("transactions.py", "sequences.py", "agents.py", f"test_{ip}.py"):
        (ip_dir / "tb" / "cocotb" / name).write_text("", encoding="utf-8")


@pytest.mark.parametrize(
    "name,mutate",
    [
        ("comment_only_scoreboard", _mut_comment_only_scoreboard),
        ("empty_tb_bodies", _mut_empty_tb_bodies),
    ],
)
def test_audit_tb_gate_rejects_hollow_authoring(tmp_path: Path, name, mutate) -> None:
    ip = "tb_mut_authoring"
    ip_dir = _write_ip(tmp_path, ip)
    _write_tb_artifacts(ip_dir, ip)
    mutate(ip_dir, ip)

    _run(tmp_path, ip, "--audit-tb")

    plan = json.loads((ip_dir / "tb" / "tb_todo_plan.json").read_text(encoding="utf-8"))
    assert plan["gate"]["status"] != "pass", f"silent-PASS on hollow authoring `{name}`: {plan['gate']}"


def test_audit_evidence_gate_rejects_vacuous_scoreboard_row(tmp_path: Path) -> None:
    # HIGH-2: a row whose stimulus/fl_expected/rtl_observed are all empty dicts but
    # passed=True (empty == empty) must not close contract validation.
    ip = "tb_mut_vacuous"
    ip_dir = _write_ip(tmp_path, ip)
    _write_tb_artifacts(ip_dir, ip)
    vacuous = {
        "goal_id": "EQ_READ",
        "scenario_id": "",
        "stimulus": {},
        "fl_expected": {},
        "rtl_observed": {},
        "passed": True,
        "coverage_refs": [],
    }
    _write_evidence(ip_dir, event=vacuous, coverage=_GOOD_COVERAGE)

    _run(tmp_path, ip, "--audit-evidence")

    plan = json.loads((ip_dir / "tb" / "tb_todo_plan.json").read_text(encoding="utf-8"))
    assert plan["gate"]["status"] != "pass", f"silent-PASS on vacuous scoreboard row: {plan['gate']}"


def test_audit_evidence_gate_rejects_coverage_without_status(tmp_path: Path) -> None:
    # HIGH-3: coverage.json with the status field omitted must fail, not pass.
    ip = "tb_mut_coverage"
    ip_dir = _write_ip(tmp_path, ip)
    _write_tb_artifacts(ip_dir, ip)
    _write_evidence(ip_dir, event=_GOOD_EVENT, coverage={"note": "no status field"})

    _run(tmp_path, ip, "--audit-evidence")

    plan = json.loads((ip_dir / "tb" / "tb_todo_plan.json").read_text(encoding="utf-8"))
    assert plan["gate"]["status"] != "pass", f"silent-PASS on coverage without status: {plan['gate']}"
