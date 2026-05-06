from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.headless_workflow import _structured_ssot_yaml
from src.workflow_stage_engine import WorkflowStageEngine, _rtl_manifest_progress, canonical_stage


SOURCE_ROOT = Path(__file__).resolve().parents[1]
DERIVE_RTL_TODOS = SOURCE_ROOT / "workflow" / "rtl-gen" / "scripts" / "derive_rtl_todos.py"


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
    assert canonical_stage("tb") == "ssot-tb-cocotb"
    assert canonical_stage("cov") == "coverage"
    assert canonical_stage("/sd") == "sim-debug"


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
    template_plan = json.loads((tmp_path / ip / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    assert template_plan["name"] == f"{ip}-rtl"
    assert "tasks" in template_plan
    assert len(template_plan["tasks"]) == summary["total_tasks"]
    first_task = template_plan["tasks"][0]
    assert "content" in first_task
    assert "activeForm" in first_task
    assert "detail" in first_task
    assert "priority" in first_task


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
    assert result.runs[1].returncode == 999
    assert result.runs[2].label == "audit_rtl_todos"
    assert result.runs[2].returncode == 999
    assert "rtl_dynamic_todos:" in result.message
    assert "gate: blocked" in result.message
    assert (tmp_path / ip / "rtl" / "rtl_todo_plan.json").is_file()
    assert (tmp_path / ip / "rtl" / "rtl_blocked.json").is_file()
