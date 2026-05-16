from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import uuid
from pathlib import Path

import pytest
import yaml


REPO = Path(__file__).resolve().parents[1]
SCOREBOARD_PATH = REPO / "workflow" / "tb-gen" / "runtime" / "equivalence_scoreboard.py"
COMPARATOR_PATH = REPO / "workflow" / "sim_debug" / "scripts" / "compare_fl_rtl_results.py"
AUDIT_PATH = REPO / "workflow" / "sim_debug" / "scripts" / "audit_fl_rtl_equivalence_goal.py"
CHECK_SCOREBOARD_PATH = REPO / "workflow" / "tb-gen" / "scripts" / "check_scoreboard_events.py"
RTL_GEN_PATH = REPO / "workflow" / "rtl-gen" / "scripts" / "ssot_to_rtl.py"
DERIVE_RTL_TODOS_PATH = REPO / "workflow" / "rtl-gen" / "scripts" / "derive_rtl_todos.py"
RTL_COMPILE_PATH = REPO / "workflow" / "rtl-gen" / "scripts" / "rtl_compile_report.py"
DUT_LINT_PATH = REPO / "workflow" / "lint" / "scripts" / "dut_lint_report.py"
TB_GEN_PATH = REPO / "workflow" / "tb-gen" / "scripts" / "emit_goal_scoreboard_cocotb.py"
CHECK_PYUVM_PATH = REPO / "workflow" / "tb-gen" / "scripts" / "check_pyuvm_structure.sh"
SIM_SCRIPT_PATH = REPO / "workflow" / "tb-gen" / "scripts" / "sim.sh"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _receive_slash_output(ws, marker: str) -> str:
    for _ in range(20):
        msg = ws.receive_json()
        text = str(msg.get("text") or "")
        if msg.get("type") == "slash_output" and marker in text:
            return text
    raise AssertionError(f"did not receive slash_output containing {marker!r}")


def _receive_ws_event(ws, msg_type: str, marker: str = "") -> dict:
    for _ in range(40):
        msg = ws.receive_json()
        if msg.get("type") != msg_type:
            continue
        if marker and marker not in json.dumps(msg, sort_keys=True):
            continue
        return msg
    raise AssertionError(f"did not receive websocket event {msg_type!r} containing {marker!r}")


def _authenticated_client(app):
    from fastapi.testclient import TestClient

    client = TestClient(app)
    username = f"test_{uuid.uuid4().hex[:12]}"
    response = client.post("/api/auth/register", json={"username": username, "password": "pw"})
    assert response.status_code == 200, response.text
    client._atlas_username = username  # type: ignore[attr-defined]
    return client


def _register_live_user(base_url: str) -> str:
    username = f"live_{uuid.uuid4().hex[:12]}"
    request = urllib.request.Request(
        f"{base_url}/api/auth/register",
        data=json.dumps({"username": username, "password": "pw"}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=3) as response:
        cookie = response.headers.get("Set-Cookie") or ""
    assert "atlas_session=" in cookie
    return cookie.split(";", 1)[0]


def _port_open(host: str, port: int) -> bool:
    sock = socket.socket()
    sock.settimeout(0.2)
    try:
        return sock.connect_ex((host, port)) == 0
    finally:
        sock.close()


def _write_fixture(root: Path) -> str:
    ip = "generic_counter_ip"
    ip_dir = root / ip
    for sub in ("yaml", "model", "verify", "sim", "cov", "tb/cocotb"):
        (ip_dir / sub).mkdir(parents=True, exist_ok=True)

    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "io_list:",
                "  interfaces:",
                "    - name: data_in",
                "      type: input",
                "      width: 8",
                "features:",
                "  - name: double_value",
                "    description: Output value is twice the input value.",
                "function_model:",
                "  transactions:",
                "    - id: FM_PRIMARY",
                "      name: primary_behavior",
                "      outputs:",
                "        - value",
                "cycle_model:",
                "  latency: 1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "model" / "functional_model.py").write_text(
        """
class FunctionalModel:
    def _transactions(self):
        return [{"id": "FM_PRIMARY", "name": "primary_behavior"}]

    def apply(self, txn):
        value = int(txn.get("value", 0))
        return {"resp": 0, "value": value * 2}
""".lstrip(),
        encoding="utf-8",
    )
    (ip_dir / "model" / "fl_model_check.json").write_text('{"passed": true}\n', encoding="utf-8")
    (ip_dir / "verify" / "equivalence_goals.json").write_text(
        json.dumps(
            {
                "ip": ip,
                "schema_version": 1,
                "source_of_truth": {
                    "ssot": f"{ip}/yaml/{ip}.ssot.yaml",
                    "functional_model": f"{ip}/model/functional_model.py",
                    "cycle_model_section": "cycle_model",
                    "coverage_plan": f"{ip}/cov/fcov_plan.json",
                },
                "summary": {"total": 1, "required": 1, "optional": 0, "blocked": 0},
                "goals": [
                    {
                        "goal_id": "EQ_DOUBLE",
                        "title": "Primary value doubles",
                        "kind": "datapath",
                        "ssot_refs": ["function_model.transactions[0]"],
                        "decomposition_refs": ["datapath"],
                        "coverage_refs": ["FCOV_DOUBLE"],
                        "stimulus_contract": {
                            "transaction_type": "primary_behavior",
                            "required_fields": ["value"],
                            "constraints": [],
                        },
                        "expected_contract": {
                            "model_api": "FunctionalModel.apply",
                            "observables": ["value"],
                            "latency": "1",
                            "state_updates": [],
                            "error_policy": "",
                        },
                        "pass_criteria": ["RTL value equals FunctionalModel value"],
                        "owner_on_fail": {
                            "default": "rtl",
                            "possible": ["ssot", "fl_model", "rtl", "tb", "coverage", "human"],
                        },
                        "blocked": False,
                        "blocker": "",
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "sim" / "results.xml").write_text(
        '<testsuite tests="1" failures="0" errors="0"><testcase name="EQ_DOUBLE"/></testsuite>\n',
        encoding="utf-8",
    )
    (ip_dir / "cov" / "coverage.json").write_text(
        '{"functional": {"bins": {"FCOV_DOUBLE": {"hit": true}}}}\n',
        encoding="utf-8",
    )
    (ip_dir / "tb" / "cocotb" / f"test_{ip}.py").write_text(
        "from equivalence_scoreboard import EquivalenceScoreboard\n"
        "scoreboard = EquivalenceScoreboard('generic_counter_ip')\n",
        encoding="utf-8",
    )
    return ip


def _write_ssot_only_fixture(root: Path) -> str:
    ip = "fresh_equiv_ip"
    ip_dir = root / ip
    (ip_dir / "yaml").mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "io_list:",
                "  interfaces:",
                "    - name: stream_in",
                "      type: input",
                "      width: 8",
                "features:",
                "  - name: double_value",
                "    description: Double accepted input transactions and count accepted items.",
                "function_model:",
                "  state_variables:",
                "    - name: accepted_count",
                "      reset: 0",
                "  transactions:",
                "    - id: FM_PRIMARY",
                "      name: primary_behavior",
                "      outputs:",
                "        - value",
                "      side_effects:",
                "        - accepted_count increments for non-malformed transactions",
                "cycle_model:",
                "  latency: 1",
                "  handshake_rules:",
                "    - name: stream_ready_valid",
                "      description: Payload is sampled only when ready and valid are both high.",
                "test_requirements:",
                "  scenarios:",
                "    - id: SC_DOUBLE",
                "      name: double accepted value",
                "      stimulus: accepted stream transaction with value 12",
                "      expected: output value follows FunctionalModel result",
                "      checker: EquivalenceScoreboard compares RTL observed value against FunctionalModel.apply",
                "  coverage_goals:",
                "    planned_bins:",
                "      - id: FCOV_DOUBLE",
                "        class: datapath",
                "        description: accepted double-value scenario executed",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return ip


def _write_structured_rule_ssot(root: Path) -> str:
    ip = "fresh_rule_ip"
    ip_dir = root / ip
    (ip_dir / "yaml").mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "io_list:",
                "  clock_domains:",
                "    - name: main",
                "      ports:",
                "        - name: clk",
                "          direction: input",
                "          width: 1",
                "  resets:",
                "    - name: rst_n",
                "      active: low",
                "      ports:",
                "        - name: rst_n",
                "          direction: input",
                "          width: 1",
                "  interfaces:",
                "    - name: rule_io",
                "      type: custom",
                "      ports:",
                "        - name: valid",
                "          direction: input",
                "          width: 1",
                "        - name: data_in",
                "          direction: input",
                "          width: 8",
                "        - name: result",
                "          direction: output",
                "          width: 9",
                "        - name: ready",
                "          direction: output",
                "          width: 1",
                "        - name: result_valid",
                "          direction: output",
                "          width: 1",
                "        - name: accepted_count",
                "          direction: output",
                "          width: 8",
                "features:",
                "  - name: double_value",
                "    description: Sample data_in when valid is high and produce result=data_in*2 one cycle later.",
                "function_model:",
                "  state_variables:",
                "    - name: accepted_count",
                "      width: 8",
                "      reset: 0",
                "  transactions:",
                "    - id: FM_PRIMARY",
                "      name: primary_behavior",
                "      required_fields:",
                "        - value",
                "      outputs:",
                "        - result",
                "      output_rules:",
                "        - name: result",
                "          port: result",
                "          expr: value * 2",
                "          width: 9",
                "      side_effects:",
                "        - accepted_count increments on each sampled transaction",
                "      state_updates:",
                "        - name: accepted_count",
                "          expr: accepted_count + 1",
                "          width: 8",
                "cycle_model:",
                "  latency: 1",
                "  handshake_rules:",
                "    - name: valid_sample",
                "      description: data_in is sampled only when valid is high; ready remains high after reset.",
                "rtl_contract:",
                "  clock: clk",
                "  reset: rst_n",
                "  reset_active: low",
                "  transaction: FM_PRIMARY",
                "  sample_condition: valid and ready",
                "  input_map:",
                "    value: data_in",
                "  ready_output: ready",
                "  output_valid: result_valid",
                "test_requirements:",
                "  scenarios:",
                "    - id: SC_RULE_DOUBLE",
                "      name: double sampled input",
                "      stimulus: assert valid with data_in=13 after reset",
                "      expected: result equals FunctionalModel result and result_valid pulses",
                "      checker: EquivalenceScoreboard compares result observable against FunctionalModel.apply",
                "  coverage_goals:",
                "    planned_bins:",
                "      - id: FCOV_RULE_DOUBLE",
                "        class: datapath",
                "        description: sampled data_in doubling rule observed",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return ip


def _write_fl_output_alias_sample_ssot(root: Path) -> str:
    ip = "fl_output_alias_ip"
    ip_dir = root / ip
    (ip_dir / "yaml").mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "io_list:",
                "  interfaces:",
                "    - name: cmd_if",
                "      type: custom",
                "      ports:",
                "        - name: cmd_valid",
                "          direction: input",
                "          width: 1",
                "        - name: cmd_ready",
                "          direction: output",
                "          width: 1",
                "features:",
                "  - name: valid_ready_accept",
                "    description: Accept commands only on cmd_valid and generated cmd_ready.",
                "function_model:",
                "  state_variables:",
                "    - name: halted",
                "      width: 1",
                "      reset: 0",
                "    - name: accepted_count",
                "      width: 8",
                "      reset: 0",
                "  transactions:",
                "    - id: FM_PRIMARY",
                "      name: primary_behavior",
                "      sample_condition: cmd_valid and cmd_ready",
                "      output_rules:",
                "        - name: ready",
                "          port: cmd_ready",
                "          expr: not halted",
                "          width: 1",
                "        - name: busy",
                "          port: busy",
                "          expr: cmd_valid and cmd_ready",
                "          width: 1",
                "      state_updates:",
                "        - name: accepted_count",
                "          expr: accepted_count + 1",
                "          width: 8",
                "test_requirements:",
                "  scenarios:",
                "    - id: SC_VALID_READY",
                "      name: generated ready acceptance",
                "      stimulus: cmd_valid=1 while halted=0",
                "      expected: cmd_ready is generated and accepted_count increments",
                "      checker: FunctionalModel resolves output-rule aliases before sample_condition",
                "  coverage_goals:",
                "    planned_bins:",
                "      - id: FCOV_VALID_READY_ALIAS",
                "        class: protocol",
                "        description: sample_condition references generated output alias",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return ip


def _write_structured_rule_req(root: Path, ip: str) -> None:
    req_dir = root / ip / "req"
    req_dir.mkdir(parents=True, exist_ok=True)
    paragraph = (
        "The IP accepts one transaction when reset is released and valid is asserted. "
        "The data_in value is sampled on the clock edge accepted by the cycle model, "
        "and the externally visible result must equal twice that sampled value on the "
        "next observed cycle. The ready output remains available after reset, and "
        "result_valid marks the result cycle. The generated FunctionalModel is the "
        "expected-behavior authority for every scoreboard row. The cocotb pyuvm "
        "environment must drive only the SSOT-declared ports, observe only the "
        "SSOT/RTL-contract outputs, record one structured scoreboard row for every "
        "unblocked equivalence goal, and mark the linked functional coverage bins. "
        "DUT-only compile and lint evidence must be produced before simulation "
        "evidence is accepted, and FL-vs-RTL comparison must classify any mismatch "
        "to SSOT, FunctionalModel, RTL, TB, coverage, or a human decision gate. "
    )
    (req_dir / "requirements.md").write_text("# Requirements\n\n" + paragraph * 5 + "\n", encoding="utf-8")


def _write_executable_sim_runner(root: Path, ip: str) -> None:
    tb_dir = root / ip / "tb" / "cocotb"
    tb_dir.mkdir(parents=True, exist_ok=True)
    (tb_dir / f"test_{ip}.py").write_text(
        """
try:
    import cocotb
except Exception:
    cocotb = None


class GenericTransaction:
    def __init__(self, goal_id, value):
        self.goal_id = goal_id
        self.value = value


class GenericSequence:
    def __iter__(self):
        yield GenericTransaction("dynamic", 12)


class GenericDriver:
    def drive(self, txn):
        return {"value": txn.value}


class GenericMonitor:
    def observe(self, expected):
        model_result = expected.get("model_result") if isinstance(expected, dict) else {}
        return {"value": model_result.get("value", 0)} if isinstance(model_result, dict) else {"value": 0}


class GenericCoverage:
    def __init__(self):
        self.hit = set()

    def sample(self, refs):
        self.hit.update(refs)


def expected_got_assert(expected, got):
    assert got.items() <= expected.get("model_result", {}).items()


def test_placeholder_for_static_cocotb_layout():
    # The executable runner owns this unit-test fixture. Production cocotb
    # environments import cocotb directly; this placeholder keeps the generic
    # disk validator focused on layout and assertion paths without requiring a
    # simulator in the unit-test process.
    assert GenericDriver().drive(GenericTransaction("dynamic", 1)) == {"value": 1}
""".lstrip(),
        encoding="utf-8",
    )
    (tb_dir / "test_runner.py").write_text(
        f"""
from __future__ import annotations

import json
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

RUNTIME = {str((REPO / "workflow" / "tb-gen" / "runtime").resolve())!r}
if RUNTIME not in sys.path:
    sys.path.insert(0, RUNTIME)

from equivalence_scoreboard import EquivalenceScoreboard


def main() -> int:
    ip = {ip!r}
    root = Path(__file__).resolve().parents[2]
    sim_dir = root / "sim"
    cov_dir = root / "cov"
    sim_dir.mkdir(parents=True, exist_ok=True)
    cov_dir.mkdir(parents=True, exist_ok=True)

    goals_doc = json.loads((root / "verify" / "equivalence_goals.json").read_text(encoding="utf-8"))
    goals = [g for g in goals_doc.get("goals", []) if not g.get("blocked")]
    scoreboard = EquivalenceScoreboard(ip, root.parent, reset_events=True)
    coverage_bins = {{}}

    for idx, goal in enumerate(goals):
        goal_id = goal["goal_id"]
        stimulus = {{"value": 12 + idx}}
        expected = scoreboard.expected_for_goal(goal_id, stimulus, f"SC_{{idx + 1:03d}}")
        model_result = expected.get("model_result") if isinstance(expected, dict) else {{}}
        if isinstance(model_result, dict):
            rtl_observed = {{
                str(key): value
                for key, value in model_result.items()
                if isinstance(value, (str, int, float, bool)) and key not in {{"transaction_id", "transaction_name"}}
            }}
        else:
            rtl_observed = {{}}
        if not rtl_observed:
            rtl_observed = {{"value": stimulus["value"]}}
        row = scoreboard.record(
            goal_id,
            scenario_id=f"SC_{{idx + 1:03d}}",
            cycle=10 + idx,
            stimulus=stimulus,
            rtl_observed=rtl_observed,
        )
        if not row["passed"]:
            raise AssertionError(row["mismatch"])
        for ref in goal.get("coverage_refs") or []:
            coverage_bins[str(ref)] = {{"hit": True, "goal_id": goal_id}}

    scoreboard.assert_all_required_goals_observed()
    tests = max(len(goals), 1)
    suite = ET.Element("testsuite", tests=str(tests), failures="0", errors="0")
    for goal in goals or [{{"goal_id": "NO_GOALS"}}]:
        ET.SubElement(suite, "testcase", name=str(goal.get("goal_id")))
    ET.ElementTree(suite).write(sim_dir / "results.xml", encoding="utf-8", xml_declaration=True)
    ET.ElementTree(suite).write(root / "tb" / "cocotb" / "results.xml", encoding="utf-8", xml_declaration=True)

    pct = 100.0 if coverage_bins else 0.0
    coverage = {{
        "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "pass",
        "functional": {{
            "hit": len(coverage_bins),
            "total": len(coverage_bins),
            "pct": pct,
            "bins": coverage_bins,
        }},
    }}
    (cov_dir / "coverage_functional.json").write_text(json.dumps(coverage, indent=2) + "\\n", encoding="utf-8")
    (cov_dir / "coverage.json").write_text(json.dumps(coverage, indent=2) + "\\n", encoding="utf-8")
    (sim_dir / "coverage_report.md").write_text(f"# Coverage\\n\\nfunctional: {{pct}}%\\n", encoding="utf-8")
    (sim_dir / f"{{ip}}.vcd").write_text("$date\\n  generated\\n$end\\n", encoding="utf-8")
    (sim_dir / "sim_report.txt").write_text(
        f"TESTS={{tests}} PASS={{tests}} FAIL=0\\n0 errors, 0 warnings\\n",
        encoding="utf-8",
    )
    print(f"TESTS={{tests}} PASS={{tests}} FAIL=0")
    print("0 errors, 0 warnings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
""".lstrip(),
        encoding="utf-8",
    )


def _write_goal_audit_complete_fixture(root: Path) -> str:
    ip = _write_fixture(root)
    ip_dir = root / ip
    for sub in ("req", "rtl", "list", "lint"):
        (ip_dir / sub).mkdir(parents=True, exist_ok=True)

    (ip_dir / "req" / "requirements.md").write_text(
        "# Requirements\n\n"
        + (
            "The IP accepts an 8-bit value and returns double that value after one cycle. "
            "The input transaction is sampled after reset is deasserted, the functional "
            "model is the expected-behavior authority, and the RTL observable named "
            "value must equal the FunctionalModel result for every scoreboard event. "
        ) * 8
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "model" / "decomposition.json").write_text(
        json.dumps(
            {
                "complete": True,
                "units": [
                    {
                        "name": "datapath",
                        "kind": "datapath",
                        "responsibility": "compute doubled value from accepted transaction",
                        "ssot_refs": ["features[0]", "function_model.transactions[0]"],
                    },
                    {
                        "name": "cycle_contract",
                        "kind": "timing",
                        "responsibility": "enforce one-cycle observable latency after transaction sampling",
                        "ssot_refs": ["cycle_model"],
                    },
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "model" / "functional_model.py").write_text(
        '''
class FunctionalModel:
    """Executable SSOT-derived model for the generic counter audit fixture.

    The model is intentionally small but fully executable: every expected
    value used by the scoreboard comes from apply(), not from RTL observation.
    It tracks an accepted transaction count so the self-check can prove state
    update behavior as well as datapath behavior.  The one-cycle latency is
    represented in equivalence_goals.json and checked by the scoreboard event
    cycle field during simulation evidence capture.
    """

    def __init__(self):
        self.accepted_count = 0

    def _transactions(self):
        return [{"id": "FM_PRIMARY", "name": "primary_behavior"}]

    def reset(self):
        self.accepted_count = 0

    def apply(self, txn):
        value = int(txn.get("value", 0))
        self.accepted_count += 1
        return {
            "resp": 0,
            "value": value * 2,
            "accepted_count": self.accepted_count,
        }
'''.lstrip(),
        encoding="utf-8",
    )
    (ip_dir / "cov" / "fcov_plan.json").write_text(
        json.dumps(
            {
                "planned_before_rtl": True,
                "bins": [
                    {
                        "id": "FCOV_DOUBLE",
                        "goal_id": "EQ_DOUBLE",
                        "description": "double-value equivalence goal observed",
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"""
module {ip} (
    input  logic       clk,
    input  logic       rst_n,
    input  logic [7:0] data_in,
    output logic [8:0] value
);
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            value <= '0;
        end else begin
            value <= {{1'b0, data_in}} << 1;
        end
    end
endmodule
""".lstrip(),
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"../{ip}/rtl/{ip}.sv\n", encoding="utf-8")
    compile_report = {
        "type": "rtl_compile",
        "scope": "dut",
        "dut_only": True,
        "tool": "verilator",
        "command": f"verilator --lint-only -f {ip}/list/{ip}.f --top-module {ip}",
        "passed": True,
        "errors": 0,
        "warnings": 0,
        "diagnostics": [],
        "style_violations": [],
    }
    (ip_dir / "rtl" / "rtl_compile.json").write_text(json.dumps(compile_report, indent=2) + "\n", encoding="utf-8")
    lint_report = dict(compile_report)
    lint_report["type"] = "dut_lint"
    (ip_dir / "lint" / "dut_lint.json").write_text(json.dumps(lint_report, indent=2) + "\n", encoding="utf-8")

    time.sleep(0.02)
    scoreboard_mod = _load_module(SCOREBOARD_PATH, f"equivalence_scoreboard_audit_{time.time_ns()}")
    scoreboard = scoreboard_mod.EquivalenceScoreboard(ip, root, reset_events=True)
    scoreboard.record(
        "EQ_DOUBLE",
        scenario_id="SC_DOUBLE",
        cycle=21,
        stimulus={"value": 11},
        rtl_observed={"value": 22},
    )
    (ip_dir / "sim" / "results.xml").write_text(
        '<testsuite tests="1" failures="0" errors="0"><testcase name="EQ_DOUBLE"/></testsuite>\n',
        encoding="utf-8",
    )
    (ip_dir / "sim" / f"{ip}.vcd").write_text("$date\n  generated\n$end\n", encoding="utf-8")
    (ip_dir / "cov" / "coverage.json").write_text(
        json.dumps(
            {
                "source": "ssot_coverage_summary",
                "status": "pass",
                "functional": {
                    "hit": 1,
                    "total": 1,
                    "pct": 100.0,
                    "bins": {"FCOV_DOUBLE": {"hit": True, "goal_id": "EQ_DOUBLE"}},
                },
                "functional_bins": {
                    "FCOV_DOUBLE": {
                        "hit": True,
                        "source": "scoreboard_events",
                        "goal_id": "EQ_DOUBLE",
                        "scenario_id": "SC_DOUBLE",
                        "rtl_observed_keys": ["value"],
                    }
                },
                "rtl_observed": {
                    "status": "pass",
                    "scoreboard_events": 1,
                    "scoreboard_passed_events_with_refs": 1,
                    "goal_refs": ["FCOV_DOUBLE"],
                    "missing_bins": [],
                    "invalid_rows": [],
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    comparator_mod = _load_module(COMPARATOR_PATH, f"compare_fl_rtl_results_audit_{time.time_ns()}")
    compare_doc, classify_doc = comparator_mod.compare(ip, root)
    assert compare_doc["status"] == "pass"
    assert classify_doc["status"] == "pass"
    return ip


def test_scoreboard_runtime_and_comparator_pass(tmp_path: Path):
    ip = _write_fixture(tmp_path)
    scoreboard_mod = _load_module(SCOREBOARD_PATH, "equivalence_scoreboard_under_test")
    comparator_mod = _load_module(COMPARATOR_PATH, "compare_fl_rtl_results_under_test")

    scoreboard = scoreboard_mod.EquivalenceScoreboard(ip, tmp_path, reset_events=True)
    row = scoreboard.record(
        "EQ_DOUBLE",
        scenario_id="SC_DOUBLE",
        cycle=7,
        stimulus={"value": 21},
        rtl_observed={"value": 42},
    )
    assert row["passed"] is True
    scoreboard.assert_all_required_goals_observed()

    check = subprocess.run(
        [
            sys.executable,
            str(CHECK_SCOREBOARD_PATH),
            ip,
            "--root",
            str(tmp_path),
            "--source-check",
            "--require-events",
            "--require-all-goals",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert check.returncode == 0, check.stdout

    compare_doc, classify_doc = comparator_mod.compare(ip, tmp_path)
    assert compare_doc["status"] == "pass"
    assert compare_doc["summary"]["total"] == 1
    assert compare_doc["summary"]["goals_checked"] == 1
    assert compare_doc["summary"]["goals_passed"] == 1
    assert compare_doc["summary"]["goals_failed"] == 0
    assert classify_doc["status"] == "pass"
    assert classify_doc["classifications"] == []


def test_scoreboard_treats_highz_as_zero_for_integer_drive_mask(tmp_path: Path):
    ip = _write_fixture(tmp_path)
    scoreboard_mod = _load_module(SCOREBOARD_PATH, f"equivalence_scoreboard_highz_{time.time_ns()}")
    scoreboard = scoreboard_mod.EquivalenceScoreboard(ip, tmp_path, reset_events=True)

    row = scoreboard.record(
        "EQ_DOUBLE",
        scenario_id="SC_HIGHZ",
        cycle=1,
        stimulus={"value": 0},
        rtl_observed={"value": "zzzz"},
    )

    assert row["passed"] is True


def test_scoreboard_self_check_blocks_prose_only_ssot_questions(tmp_path: Path):
    ip = _write_fixture(tmp_path)
    model_path = tmp_path / ip / "model" / "functional_model.py"
    model_path.write_text(
        """
class FunctionalModel:
    def _transactions(self):
        return [{"id": "FM_PRIMARY", "name": "primary_behavior"}]

    def apply(self, txn):
        return {
            "resp": 0,
            "value": 1,
            "ssot_question": "[SSOT QUESTION] structured output_rules/state_updates undefined for transaction FM_PRIMARY",
        }
""".lstrip(),
        encoding="utf-8",
    )
    scoreboard_mod = _load_module(SCOREBOARD_PATH, f"equivalence_scoreboard_ssot_question_{time.time_ns()}")
    scoreboard = scoreboard_mod.EquivalenceScoreboard(ip, tmp_path, reset_events=True)

    report = scoreboard.self_check()

    assert report["passed"] is False
    assert report["ssot_questions"] == 1
    assert report["contract_gaps"][0]["goal_id"] == "EQ_DOUBLE"
    check = subprocess.run(
        [sys.executable, str(SCOREBOARD_PATH), ip, "--root", str(tmp_path), "--self-check"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert check.returncode == 2, check.stdout
    blocked = json.loads((tmp_path / ip / "tb" / "cocotb" / "tb_blocked.json").read_text(encoding="utf-8"))
    assert blocked["reason"].startswith("SSOT/FunctionalModel contract")
    assert blocked["questions"][0]["id"] == "TB_SELF_CHECK_001"
    assert "structured output_rules" in blocked["questions"][0]["evidence"]


def test_tb_manifest_allows_inout_observable_output(tmp_path: Path):
    ip = "inout_tb_ip"
    ip_dir = tmp_path / ip
    for subdir in ("yaml", "verify", "rtl", "list"):
        (ip_dir / subdir).mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        yaml.safe_dump(
            {
                "top_module": {"name": ip},
                "io_list": {
                    "clock_domains": [{"ports": [{"name": "clk", "direction": "input", "width": 1}]}],
                    "resets": [{"ports": [{"name": "rst_n", "direction": "input", "width": 1}]}],
                    "interfaces": [
                        {
                            "name": "gpio",
                            "type": "custom",
                            "ports": [{"name": "gpio_pins", "direction": "inout", "width": 32}],
                        }
                    ],
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (ip_dir / "verify" / "equivalence_goals.json").write_text(
        json.dumps({"goals": [{"goal_id": "EQ_GPIO", "blocked": False}]}, indent=2) + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / "rtl_contract.json").write_text(
        json.dumps(
            {
                "type": "generic_ssot_rule_rtl_contract",
                "contract": {
                    "clock": "clk",
                    "reset": "rst_n",
                    "reset_active": "low",
                    "sample_condition": "1",
                    "outputs": [{"name": "gpio_pins", "port": "gpio_pins", "width": 32}],
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text("module inout_tb_ip; endmodule\n", encoding="utf-8")
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\n", encoding="utf-8")
    tb_mod = _load_module(TB_GEN_PATH, f"tb_gen_inout_{time.time_ns()}")

    manifest, questions = tb_mod._build_manifest(ip, tmp_path)

    assert not [q for q in questions if q["id"].startswith("TB_OUTPUT_GPIO_PINS")]
    assert any(item["port"] == "gpio_pins" for item in manifest["outputs"])
    assert manifest["inout_ports"] == ["gpio_pins"]


def test_generated_driver_releases_inout_except_input_capture(monkeypatch):
    import types

    cocotb_mod = types.ModuleType("cocotb")
    cocotb_mod.test = lambda: (lambda fn: fn)
    cocotb_mod.start_soon = lambda _awaitable: None
    binary_mod = types.ModuleType("cocotb.binary")
    binary_mod.BinaryValue = lambda value: value
    clock_mod = types.ModuleType("cocotb.clock")
    clock_mod.Clock = lambda *_args, **_kwargs: types.SimpleNamespace(start=lambda: None)
    triggers_mod = types.ModuleType("cocotb.triggers")
    triggers_mod.ClockCycles = lambda *_args, **_kwargs: None
    triggers_mod.FallingEdge = lambda *_args, **_kwargs: None
    triggers_mod.ReadOnly = lambda *_args, **_kwargs: None
    triggers_mod.RisingEdge = lambda *_args, **_kwargs: None
    monkeypatch.setitem(sys.modules, "cocotb", cocotb_mod)
    monkeypatch.setitem(sys.modules, "cocotb.binary", binary_mod)
    monkeypatch.setitem(sys.modules, "cocotb.clock", clock_mod)
    monkeypatch.setitem(sys.modules, "cocotb.triggers", triggers_mod)
    tb_mod = _load_module(TB_GEN_PATH, f"tb_gen_inout_drive_{time.time_ns()}")
    ns: dict[str, object] = {}
    exec(tb_mod.TEST_PY, ns)

    class Signal:
        def __init__(self):
            self.value = None

    class Dut:
        clk = Signal()
        rst_n = Signal()
        gpio_pins = Signal()
        psel = Signal()
        penable = Signal()

    manifest = {
        "clock": "clk",
        "reset": "rst_n",
        "input_ports": ["clk", "rst_n", "gpio_pins", "psel", "penable"],
        "output_ports": ["gpio_pins"],
        "inout_ports": ["gpio_pins"],
        "input_map": {"gpio_pins": "gpio_pins", "psel": "psel", "penable": "penable"},
        "sample_inputs": [],
        "port_widths": {"gpio_pins": 4, "psel": 1, "penable": 1, "clk": 1, "rst_n": 1},
    }

    ns["_drive_inputs"](Dut, manifest, {"kind": "gpio_pin_drive", "gpio_pins": 0xF, "psel": 1, "penable": 1})
    assert Dut.gpio_pins.value == "zzzz"
    assert Dut.psel.value == 1
    assert Dut.penable.value == 1

    ns["_drive_inputs"](Dut, manifest, {"kind": "gpio_input_capture", "gpio_pins": 0xA})
    assert Dut.gpio_pins.value == 0xA


def test_generated_apb_goal_stimulus_uses_ssot_register_offsets_without_register_fallback(tmp_path: Path, monkeypatch):
    import types

    ip = "apb_goal_stimulus_ip"
    ip_dir = tmp_path / ip
    for subdir in ("yaml", "verify", "rtl", "list"):
        (ip_dir / subdir).mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        yaml.safe_dump(
            {
                "top_module": {"name": ip},
                "io_list": {
                    "clock_domains": [{"ports": [{"name": "clk", "direction": "input", "width": 1}]}],
                    "resets": [{"ports": [{"name": "rst_n", "direction": "input", "width": 1}]}],
                    "interfaces": [
                        {
                            "name": "apb",
                            "type": "apb",
                            "ports": [
                                {"name": "psel", "direction": "input", "width": 1},
                                {"name": "penable", "direction": "input", "width": 1},
                                {"name": "pwrite", "direction": "input", "width": 1},
                                {"name": "paddr", "direction": "input", "width": 8},
                                {"name": "pwdata", "direction": "input", "width": 32},
                                {"name": "pstrb", "direction": "input", "width": 4},
                                {"name": "prdata", "direction": "output", "width": 32},
                                {"name": "pready", "direction": "output", "width": 1},
                                {"name": "pslverr", "direction": "output", "width": 1},
                            ],
                        }
                    ],
                },
                "parameters": [{"name": "APB_ADDR_WIDTH", "default": 8}],
                "registers": {
                    "config": {"byte_addressable": True},
                    "register_list": [
                        {"name": "CTRL", "offset": 0, "width": 32, "access": "rw", "reset": 0},
                        {"name": "STATUS", "offset": 4, "width": 32, "access": "ro", "reset": 0},
                    ],
                },
                "function_model": {
                    "transactions": [
                        {
                            "id": "FM1",
                            "name": "apb_write_register",
                            "required_fields": ["psel", "penable", "pwrite", "paddr", "pwdata", "pstrb"],
                            "output_rules": [{"name": "pslverr", "port": "pslverr", "expr": "0", "width": 1}],
                        }
                    ]
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    goal = {
        "goal_id": "EQ_TRANSACTION_FM1",
        "title": "Transaction apb_write_register matches FunctionalModel",
        "kind": "transaction",
        "stimulus_contract": {
            "transaction_type": "apb_write_register",
            "required_fields": ["psel", "penable", "pwrite", "paddr", "pwdata", "pstrb"],
        },
        "expected_contract": {
            "observables": ["pready", "pslverr", "prdata"],
            "error_policy": "addr_valid == 0 returns pslverr == 1 without updating registers",
        },
        "blocked": False,
    }
    (ip_dir / "verify" / "equivalence_goals.json").write_text(
        json.dumps({"goals": [goal]}, indent=2) + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / "rtl_contract.json").write_text(
        json.dumps(
            {
                "ip": ip,
                "owner_module": f"{ip}_regs",
                "implemented_behavior": ["legacy packet-style RTL contract"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(f"module {ip}; endmodule\n", encoding="utf-8")
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\n", encoding="utf-8")
    tb_mod = _load_module(TB_GEN_PATH, f"tb_gen_apb_offsets_{time.time_ns()}")
    manifest, questions = tb_mod._build_manifest(ip, tmp_path)

    assert questions == []
    assert manifest["rtl_contract_source"] == "ssot_fallback"
    assert [row["offset"] for row in manifest["registers"]["register_list"]] == [0, 4]

    cocotb_mod = types.ModuleType("cocotb")
    cocotb_mod.test = lambda: (lambda fn: fn)
    cocotb_mod.start_soon = lambda _awaitable: None
    binary_mod = types.ModuleType("cocotb.binary")
    binary_mod.BinaryValue = lambda value: value
    clock_mod = types.ModuleType("cocotb.clock")
    clock_mod.Clock = lambda *_args, **_kwargs: types.SimpleNamespace(start=lambda: None)
    triggers_mod = types.ModuleType("cocotb.triggers")
    triggers_mod.ClockCycles = lambda *_args, **_kwargs: None
    triggers_mod.FallingEdge = lambda *_args, **_kwargs: None
    triggers_mod.ReadOnly = lambda *_args, **_kwargs: None
    triggers_mod.RisingEdge = lambda *_args, **_kwargs: None
    monkeypatch.setitem(sys.modules, "cocotb", cocotb_mod)
    monkeypatch.setitem(sys.modules, "cocotb.binary", binary_mod)
    monkeypatch.setitem(sys.modules, "cocotb.clock", clock_mod)
    monkeypatch.setitem(sys.modules, "cocotb.triggers", triggers_mod)
    ns: dict[str, object] = {}
    exec(tb_mod.TEST_PY, ns)

    stimulus = ns["_stimulus_for_goal"](goal, manifest, 0)

    assert stimulus["paddr"] == 0
    assert stimulus["pwrite"] == 1
    assert stimulus["psel"] == 1
    assert stimulus["penable"] == 1
    assert stimulus["pstrb"] == 15
    assert "reg" not in stimulus
    assert "addr_or_name" not in stimulus

    read_goal = {
        **goal,
        "goal_id": "EQ_TRANSACTION_FM2",
        "title": "Transaction apb_read_register decodes address, drives prdata read mux, or latches write data in other paths",
        "stimulus_contract": {
            "transaction_type": "apb_read_register",
            "required_fields": ["psel", "penable", "pwrite", "paddr"],
        },
    }
    read_stimulus = ns["_stimulus_for_goal"](read_goal, manifest, 1)
    assert read_stimulus["op"] == "read"
    assert read_stimulus["pwrite"] == 0
    assert read_stimulus["paddr"] == 4


def test_generated_runner_escalates_soft_scoreboard_mismatches(tmp_path: Path, monkeypatch):
    import types

    cocotb_test_mod = types.ModuleType("cocotb_test")
    simulator_mod = types.ModuleType("cocotb_test.simulator")
    simulator_mod.run = lambda **_kwargs: ""
    monkeypatch.setitem(sys.modules, "cocotb_test", cocotb_test_mod)
    monkeypatch.setitem(sys.modules, "cocotb_test.simulator", simulator_mod)
    tb_mod = _load_module(TB_GEN_PATH, f"tb_gen_runner_escalate_{time.time_ns()}")
    ns: dict[str, object] = {}
    exec(tb_mod.RUNNER_PY, ns)
    events = tmp_path / "scoreboard_events.jsonl"
    events.write_text(
        json.dumps(
            {
                "goal_id": "EQ_GPIO",
                "passed": False,
                "mismatch": "irq: expected=1 observed=0",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    lines = ns["_scoreboard_escalations"](events)

    assert lines
    assert lines[0].startswith("[SIM ESCALATE] scoreboard_failed=1")
    assert "EQ_GPIO" in lines[1]
    assert "irq: expected=1 observed=0" in lines[1]


def test_blocked_goal_creates_human_gate_question(tmp_path: Path):
    ip = _write_fixture(tmp_path)
    goals_path = tmp_path / ip / "verify" / "equivalence_goals.json"
    goals_doc = json.loads(goals_path.read_text(encoding="utf-8"))
    goals_doc["summary"] = {"total": 1, "required": 0, "optional": 0, "blocked": 1}
    goals_doc["goals"][0]["blocked"] = True
    goals_doc["goals"][0]["blocker"] = "undefined SSOT behavior for response ordering"
    goals_path.write_text(json.dumps(goals_doc, indent=2) + "\n", encoding="utf-8")

    comparator_mod = _load_module(COMPARATOR_PATH, "compare_fl_rtl_results_blocked_under_test")
    compare_doc, classify_doc = comparator_mod.compare(ip, tmp_path)

    assert compare_doc["status"] == "blocked"
    assert compare_doc["summary"]["goals_blocked"] == 1
    assert classify_doc["status"] == "action_required"
    assert len(classify_doc["classifications"]) == 1
    classification = classify_doc["classifications"][0]
    assert classification["classification"] == "ssot_ambiguity"
    assert classification["owner"] == "ssot-gen"
    assert classification["llm_loop_allowed"] is False
    assert "Decision needed:" in classification["human_question"]
    assert "Downstream effect:" in classification["human_question"]


def test_atlas_progress_reports_equivalence_pass_from_compare_artifacts(tmp_path: Path, monkeypatch):
    ip = _write_fixture(tmp_path)
    scoreboard_mod = _load_module(SCOREBOARD_PATH, "equivalence_scoreboard_progress_under_test")
    comparator_mod = _load_module(COMPARATOR_PATH, "compare_fl_rtl_results_progress_under_test")

    scoreboard = scoreboard_mod.EquivalenceScoreboard(ip, tmp_path, reset_events=True)
    scoreboard.record(
        "EQ_DOUBLE",
        scenario_id="SC_DOUBLE",
        cycle=11,
        stimulus={"value": 5},
        rtl_observed={"value": 10},
    )
    comparator_mod.compare(ip, tmp_path)

    from fastapi.testclient import TestClient
    import src.atlas_ui as atlas_ui

    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    client = _authenticated_client(atlas_ui.create_app())
    response = client.get("/api/progress", params={"scope": ip})

    assert response.status_code == 200
    selected = response.json()["selected"]
    equiv = selected["progress"]["equivalence_goals"]
    assert equiv["status"] == "pass"
    assert equiv["total"] == 1
    assert equiv["checked"] == 1
    assert equiv["passed"] == 1
    assert equiv["compare_evidence"] == f"{ip}/sim/fl_rtl_compare.json"
    assert equiv["classification_evidence"] == f"{ip}/sim/mismatch_classification.json"
    assert selected["signoff"]["status"]["equivalence_goals"] == "pass"
    assert selected["signoff"]["status"]["signoff"] != "pass"
    ownership = selected["signoff"]["ownership"]
    required_stages = {
        "req",
        "ssot",
        "fl_model",
        "fl_decomp",
        "fcov_plan",
        "equivalence_goals",
        "goal_audit",
        "rtl",
        "lint",
        "tb",
        "sim_debug",
        "coverage",
        "signoff",
    }
    assert required_stages <= set(ownership)
    for stage in required_stages:
        entry = ownership[stage]
        assert entry["stage"] == stage
        for field in ("status", "owner", "validator", "evidence", "blocker", "next_action"):
            assert field in entry
    assert ownership["signoff"]["owner"] in {"LLM loop", "human gate"}


def test_atlas_progress_simple_summary_turns_req_blocker_into_user_action(tmp_path: Path, monkeypatch):
    ip = _write_goal_audit_complete_fixture(tmp_path)
    req_path = tmp_path / ip / "req" / "requirements.md"
    req_path.write_text("# Requirements\n\nTBD\n", encoding="utf-8")

    run = subprocess.run(
        [sys.executable, str(AUDIT_PATH), ip, "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert run.returncode != 0, run.stdout

    from fastapi.testclient import TestClient
    import src.atlas_ui as atlas_ui

    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    client = _authenticated_client(atlas_ui.create_app())
    response = client.get("/api/progress", params={"scope": ip})

    assert response.status_code == 200
    selected = response.json()["selected"]
    summary = selected["simple_summary"]
    assert summary == selected["signoff"]["simple_summary"]
    assert summary["state"] == "needs_review"
    assert summary["primary_action"]["label"] == "Open Review"
    assert summary["next_steps"][0]["stage"] == "req"
    assert summary["next_steps"][0]["owner"] == "user"
    assert "goal audit" not in summary["headline"].lower()
    assert "blockers=req" not in summary["message"].lower()
    assert any("goal audit" in item.lower() for item in summary["expert_blockers"])


def test_atlas_progress_rtl_artifact_status_uses_strict_manifest_gate(tmp_path: Path, monkeypatch):
    ip = "manifest_partial_ip"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "rtl").mkdir()
    (ip_dir / "list").mkdir()
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "sub_modules:",
                f"  - name: {ip}",
                f"    file: rtl/{ip}.sv",
                f"  - name: {ip}_decode",
                f"    file: rtl/{ip}_decode.sv",
                "io_list:",
                "  interfaces: []",
                "features: []",
                "function_model:",
                "  transactions: []",
                "cycle_model:",
                "  latency: 1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        "\n".join(
            [
                f"module {ip}(",
                "    input logic clk,",
                "    input logic rst_n,",
                "    output logic ready",
                ");",
                "    logic [15:0] count_q;",
                "    always_ff @(posedge clk or negedge rst_n) begin",
                "        if (!rst_n) begin",
                "            count_q <= 16'd0;",
                "            ready <= 1'b0;",
                "        end else begin",
                "            count_q <= count_q + 16'd1;",
                "            ready <= count_q[0];",
                "        end",
                "    end",
                "endmodule",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\n", encoding="utf-8")

    from fastapi.testclient import TestClient
    import src.atlas_ui as atlas_ui

    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    client = _authenticated_client(atlas_ui.create_app())
    response = client.get("/api/progress", params={"scope": ip})

    assert response.status_code == 200
    selected = response.json()["selected"]
    assert selected["status"]["rtl"] == "partial"
    assert selected["artifact_status"]["rtl"] == "partial"
    assert "1/2 RTL files approved" in selected["artifact_detail"]["rtl"]


def test_atlas_progress_prefers_ssot_kind_over_name_heuristic(tmp_path: Path, monkeypatch):
    ip = "arm_m0_i3c_bus"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "  type: bus",
                "io_list:",
                "  interfaces: []",
                "features: []",
                "function_model:",
                "  transactions: []",
                "cycle_model:",
                "  latency: 1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    from fastapi.testclient import TestClient
    import src.atlas_ui as atlas_ui

    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    client = _authenticated_client(atlas_ui.create_app())
    response = client.get("/api/progress", params={"scope": ip})

    assert response.status_code == 200
    assert response.json()["selected"]["kind"] == "bus"


def test_stale_equivalence_evidence_blocks_progress(tmp_path: Path, monkeypatch):
    ip = _write_fixture(tmp_path)
    scoreboard_mod = _load_module(SCOREBOARD_PATH, "equivalence_scoreboard_stale_under_test")
    comparator_mod = _load_module(COMPARATOR_PATH, "compare_fl_rtl_results_stale_under_test")

    scoreboard = scoreboard_mod.EquivalenceScoreboard(ip, tmp_path, reset_events=True)
    scoreboard.record(
        "EQ_DOUBLE",
        scenario_id="SC_DOUBLE",
        cycle=17,
        stimulus={"value": 6},
        rtl_observed={"value": 12},
    )
    goals_path = tmp_path / ip / "verify" / "equivalence_goals.json"
    future = time.time() + 10
    os.utime(goals_path, (future, future))

    compare_doc, classify_doc = comparator_mod.compare(ip, tmp_path)
    assert compare_doc["status"] == "stale"
    assert compare_doc["summary"]["stale_evidence"]
    assert classify_doc["status"] == "action_required"

    from fastapi.testclient import TestClient
    import src.atlas_ui as atlas_ui

    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    client = _authenticated_client(atlas_ui.create_app())
    response = client.get("/api/progress", params={"scope": ip})

    assert response.status_code == 200
    selected = response.json()["selected"]
    equiv = selected["progress"]["equivalence_goals"]
    assert equiv["status"] == "stale"
    assert equiv["stale_evidence"]
    assert selected["signoff"]["status"]["equivalence_goals"] == "stale"
    assert selected["signoff"]["status"]["signoff"] != "pass"
    assert selected["signoff"]["ownership"]["equivalence_goals"]["owner"] == "LLM loop"


def test_stale_derived_oracle_routes_to_fl_model_gen_instead_of_rtl(tmp_path: Path):
    ip = _write_fixture(tmp_path)
    scoreboard_mod = _load_module(SCOREBOARD_PATH, "equivalence_scoreboard_stale_oracle_under_test")
    comparator_mod = _load_module(COMPARATOR_PATH, "compare_fl_rtl_results_stale_oracle_under_test")

    scoreboard = scoreboard_mod.EquivalenceScoreboard(ip, tmp_path, reset_events=True)
    scoreboard.record(
        "EQ_DOUBLE",
        scenario_id="SC_DOUBLE",
        cycle=23,
        stimulus={"value": 10},
        rtl_observed={"value": 19},
    )

    ip_dir = tmp_path / ip
    old = time.time() - 20
    ssot_time = time.time()
    fresh = time.time() + 20
    for rel in [
        "model/functional_model.py",
        "model/fl_model_check.json",
        "verify/equivalence_goals.json",
    ]:
        path = ip_dir / rel
        os.utime(path, (old, old))
    os.utime(ip_dir / "yaml" / f"{ip}.ssot.yaml", (ssot_time, ssot_time))
    for rel in [
        "sim/scoreboard_events.jsonl",
        "sim/results.xml",
        "cov/coverage.json",
    ]:
        path = ip_dir / rel
        os.utime(path, (fresh, fresh))

    compare_doc, classify_doc = comparator_mod.compare(ip, tmp_path)

    assert compare_doc["status"] == "stale"
    assert compare_doc["summary"]["stale_oracle_evidence"]
    assert compare_doc["summary"]["goals_failed"] == 0
    assert classify_doc["status"] == "action_required"
    assert len(classify_doc["classifications"]) == 1
    classification = classify_doc["classifications"][0]
    assert classification["classification"] == "stale_oracle"
    assert classification["owner"] == "fl-model-gen"
    assert classification["llm_loop_allowed"] is True
    assert "Do not repair RTL" in classification["repair_prompt"]
    assert not [item for item in classify_doc["classifications"] if item.get("owner") == "rtl-gen"]


def test_sim_result_failure_without_scoreboard_mismatch_is_classified(tmp_path: Path):
    ip = _write_fixture(tmp_path)
    scoreboard_mod = _load_module(SCOREBOARD_PATH, "equivalence_scoreboard_result_fail_under_test")
    comparator_mod = _load_module(COMPARATOR_PATH, "compare_fl_rtl_results_result_fail_under_test")

    scoreboard = scoreboard_mod.EquivalenceScoreboard(ip, tmp_path, reset_events=True)
    scoreboard.record(
        "EQ_DOUBLE",
        scenario_id="SC_DOUBLE",
        cycle=19,
        stimulus={"value": 8},
        rtl_observed={"value": 16},
    )
    (tmp_path / ip / "sim" / "results.xml").write_text(
        '<testsuite tests="1" failures="1" errors="0">'
        '<testcase name="infra_failure"><failure message="runner failed"/></testcase>'
        '</testsuite>\n',
        encoding="utf-8",
    )

    compare_doc, classify_doc = comparator_mod.compare(ip, tmp_path)

    assert compare_doc["status"] == "fail"
    assert compare_doc["summary"]["goals_failed"] == 1
    assert classify_doc["status"] == "action_required"
    infra = [item for item in classify_doc["classifications"] if item["goal_id"] == ""]
    assert len(infra) == 1
    assert infra[0]["classification"] == "tb_bug"
    assert infra[0]["owner"] == "tb-gen"
    assert infra[0]["llm_loop_allowed"] is True
    assert "scoreboard goal_id" in infra[0]["repair_prompt"]


def test_goal_audit_passes_complete_equivalence_evidence(tmp_path: Path):
    ip = _write_goal_audit_complete_fixture(tmp_path)

    run = subprocess.run(
        [sys.executable, str(AUDIT_PATH), ip, "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert run.returncode == 0, run.stdout
    audit_doc = json.loads((tmp_path / ip / "sim" / "fl_rtl_goal_audit.json").read_text(encoding="utf-8"))
    assert audit_doc["status"] == "pass"
    assert audit_doc["summary"]["blockers"] == []
    assert audit_doc["stop_condition"]["signoff_evidence_backed"] is True
    required_checks = {
        "req",
        "ssot",
        "fl_model",
        "fl_decomposition",
        "fcov_plan",
        "equivalence_goals",
        "rtl_artifacts",
        "dut_compile",
        "dut_lint",
        "scoreboard_contract",
        "simulation",
        "fl_rtl_compare",
        "mismatch_classification",
        "functional_coverage",
        "fresh_evidence",
    }
    assert required_checks <= {check["id"] for check in audit_doc["checks"]}


def test_goal_audit_accepts_functional_coverage_when_code_metrics_are_uninstrumented(tmp_path: Path):
    ip = _write_goal_audit_complete_fixture(tmp_path)
    coverage_path = tmp_path / ip / "cov" / "coverage.json"
    coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    coverage["status"] = "blocked"
    coverage["limitations"] = {
        "line": "coverage.info has no line records",
        "branch": "coverage.info has no branch records",
    }
    coverage_path.write_text(json.dumps(coverage, indent=2) + "\n", encoding="utf-8")

    run = subprocess.run(
        [sys.executable, str(AUDIT_PATH), ip, "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert run.returncode == 0, run.stdout
    audit_doc = json.loads((tmp_path / ip / "sim" / "fl_rtl_goal_audit.json").read_text(encoding="utf-8"))
    check = next(item for item in audit_doc["checks"] if item["id"] == "functional_coverage")
    assert check["status"] == "pass"
    assert "status=blocked" in check["detail"]


def test_goal_audit_fails_with_exact_blockers_for_incomplete_ip(tmp_path: Path):
    ip = _write_fixture(tmp_path)

    run = subprocess.run(
        [sys.executable, str(AUDIT_PATH), ip, "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert run.returncode == 1, run.stdout
    audit_doc = json.loads((tmp_path / ip / "sim" / "fl_rtl_goal_audit.json").read_text(encoding="utf-8"))
    blockers = set(audit_doc["summary"]["blockers"])
    assert {"req", "fl_decomposition", "fcov_plan", "rtl_artifacts", "dut_compile", "dut_lint"} <= blockers
    assert audit_doc["stop_condition"]["signoff_evidence_backed"] is False


def test_derive_rtl_static_evidence_uses_ports_context_and_cross_module_invariants(tmp_path: Path):
    ip = "semantic_gpio_ip"
    ip_dir = tmp_path / ip
    for sub in ("yaml", "rtl", "list"):
        (ip_dir / sub).mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        yaml.safe_dump(
            {
                "top_module": {"name": ip},
                "sub_modules": [
                    {
                        "name": f"{ip}_regs",
                        "file": f"rtl/{ip}_regs.sv",
                        "function_model_refs": [
                            "function_model.transactions.FM2",
                            "function_model.state_variables.dir_reg",
                        ],
                        "register_refs": ["registers"],
                    },
                    {
                        "name": f"{ip}_datapath",
                        "file": f"rtl/{ip}_datapath.sv",
                        "function_model_refs": [
                            "function_model.transactions.FM4",
                            "function_model.state_variables.gpio_sync2",
                            "function_model.state_variables.gpio_prev",
                        ],
                        "dataflow_refs": ["dataflow"],
                    },
                ],
                "io_list": {
                    "interfaces": [
                        {"name": "paddr", "type": "input", "width": 8},
                        {"name": "prdata", "type": "output", "width": 32},
                        {"name": "gpio_pins", "type": "inout", "width": 32},
                    ]
                },
                "function_model": {
                    "state_variables": [
                        {"name": "dir_reg", "width": 32, "reset": 0},
                        {
                            "name": "gpio_sync2",
                            "width": 32,
                            "reset": 0,
                            "description": "Synchronized GPIO input value",
                        },
                        {
                            "name": "gpio_prev",
                            "width": 32,
                            "reset": 0,
                            "description": "Previous synchronized input used for edge detection",
                        },
                    ],
                    "transactions": [
                        {
                            "id": "FM2",
                            "name": "apb_read_register",
                            "required_fields": ["paddr"],
                            "output_rules": [
                                {"name": "prdata", "port": "prdata", "expr": "read_mux(paddr)", "width": 32}
                            ],
                        },
                        {
                            "id": "FM4",
                            "name": "gpio_input_capture",
                            "required_fields": ["gpio_pins"],
                            "output_rules": [
                                {"name": "gpio_pins", "port": "gpio_pins", "expr": "gpio_pins", "width": 32}
                            ],
                            "side_effects": ["Synchronized value readable via IN_DATA register"],
                            "state_updates": [
                                {"name": "gpio_sync2", "expr": "gpio_pins", "width": 32},
                                {"name": "gpio_prev", "expr": "gpio_sync2", "width": 32},
                            ],
                        },
                    ],
                    "invariants": [
                        "Edge detection operates only on 2-stage synchronized inputs, never on raw gpio_pins."
                    ],
                },
                "cycle_model": {"latency": 1},
                "registers": {
                    "register_list": [
                        {"name": "IN_DATA", "offset": 8, "width": 32, "access": "ro", "reset": 0}
                    ]
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}_regs.sv").write_text(
        f"""
module {ip}_regs (
  input  logic [7:0]  paddr,
  output logic [31:0] prdata
);
  logic [31:0] read_data;
  always_comb begin
    read_data = 32'h0;
    prdata = read_data;
  end
endmodule
""".lstrip(),
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}_datapath.sv").write_text(
        f"""
module {ip}_datapath (
  inout  wire  [31:0] gpio_pins,
  output logic [31:0] gpio_sync2_o,
  output logic [31:0] gpio_prev_o
);
  logic [31:0] gpio_sync2_r;
  logic [31:0] gpio_prev_r;
  assign gpio_sync2_o = gpio_sync2_r;
  assign gpio_prev_o = gpio_prev_r;
  assign gpio_sync2_r = gpio_pins;
  assign gpio_prev_r = gpio_sync2_r;
endmodule
""".lstrip(),
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(f"module {ip}; endmodule\n", encoding="utf-8")
    (ip_dir / "list" / f"{ip}.f").write_text(
        f"../{ip}/rtl/{ip}.sv\n../{ip}/rtl/{ip}_regs.sv\n../{ip}/rtl/{ip}_datapath.sv\n",
        encoding="utf-8",
    )

    subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS_PATH), ip, "--root", str(tmp_path), "--audit-rtl"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    plan = json.loads((ip_dir / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    by_ref = {task["source_ref"]: task for task in plan["tasks"]}
    assert by_ref["function_model.transactions.FM2.output_rules.prdata"]["todo_completion"]["status"] == "pass"
    assert by_ref["function_model.transactions.FM4.side_effects.side_effect_0"]["todo_completion"]["status"] == "pass"
    invariant = by_ref["function_model.invariants.invariant_0"]
    assert invariant["todo_completion"]["status"] == "pass"
    assert invariant["owner_file"] == f"rtl/{ip}_datapath.sv"
    assert invariant["static_evidence"]["source_scope"].endswith(f"rtl/{ip}_datapath.sv")


def test_atlas_websocket_runs_ssot_equivalence_goal_command(tmp_path: Path, monkeypatch):
    ip = _write_fixture(tmp_path)

    from fastapi.testclient import TestClient
    import src.atlas_ui as atlas_ui

    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    client = _authenticated_client(atlas_ui.create_app())
    with client.websocket_connect("/ws/agent") as ws:
        assert ws.receive_json()["type"] == "hello"
        ws.send_json({"type": "prompt", "text": f"/ssot-equiv-goals {ip}"})
        output = _receive_slash_output(ws, "[ssot-equiv-goals]")

    assert "[ssot-equiv-goals] PASS" in output
    goals_path = tmp_path / ip / "verify" / "equivalence_goals.json"
    goals_doc = json.loads(goals_path.read_text(encoding="utf-8"))
    assert goals_doc["summary"]["total"] > 0
    assert goals_doc["summary"]["blocked"] == 0


def test_atlas_websocket_import_seeds_active_ssot_before_grill_me(tmp_path: Path, monkeypatch):
    ip = "sqa"
    doc_dir = tmp_path / "docs"
    doc_dir.mkdir()
    (doc_dir / "sqa_spec.md").write_text(
        "\n".join([
            "# SQA overview",
            "Purpose: sqa is an APB4-controlled status and quality-assurance block for firmware-visible checks.",
            "Bus interface: APB4 slave, firmware-mapped CSR access.",
            "Register map: CTRL 0x00 RW enable bit0, STATUS 0x04 RO done/error bits, IRQ_STATUS 0x08 W1C.",
            "Clock reset: clk at 100 MHz, rst_n active-low reset.",
            "Interrupt: irq level-high when IRQ_STATUS has enabled bits set.",
            "Memory map: CSR window only, 0x1000 byte range, base address assigned by SoC integration.",
            "Parameters: DATA_WIDTH=32, ADDR_WIDTH=12, FIFO_DEPTH=4 defaults.",
            "Submodule structure: sqa_regs, sqa_core, sqa_irq are manifest-owned submodules.",
            "Test expectation: cocotb tests cover reset, APB reads/writes, irq set/clear, error path, and coverage bins.",
        ]) + "\n",
        encoding="utf-8",
    )

    from fastapi.testclient import TestClient
    import src.atlas_ui as atlas_ui

    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    client = _authenticated_client(atlas_ui.create_app())
    with client.websocket_connect("/ws/agent") as ws:
        assert ws.receive_json()["type"] == "hello"
        ws.send_json({"type": "prompt", "text": f"/new-ip {ip} APB4 SQA controller"})
        plan = _receive_slash_output(ws, "[SSOT PLAN]")
        assert "no document import is run by /new-ip" in plan

        ws.send_json({"type": "prompt", "text": "/import docs/sqa_spec.md"})
        imported = _receive_slash_output(ws, "[SSOT IMPORT]")
        assert "filled decisions:" in imported
        assert "missing decisions: (none)" in imported

        ws.send_json({"type": "prompt", "text": "approve"})
        approved = _receive_slash_output(ws, "[SSOT APPROVED]")
        assert ip in approved

    username = client._atlas_username  # type: ignore[attr-defined]
    state = json.loads((tmp_path / ".session" / username / ip / "ssot-gen" / "state.json").read_text(encoding="utf-8"))
    assert state["approved"] is True
    assert "decisions" not in state
    assert "decision_sources" not in state
    assert "imports" not in state
    assert state["imported_artifacts"][0]["path"] == "docs/sqa_spec.md"

    import yaml

    ssot_doc = yaml.safe_load((tmp_path / ip / "yaml" / f"{ip}.ssot.yaml").read_text(encoding="utf-8"))
    atlas_decisions = ssot_doc["custom"]["atlas_decisions"]
    assert atlas_decisions["bus_interface"]
    assert atlas_decisions["test_expectation"]


def test_atlas_websocket_fresh_new_ip_to_ssot_fl_equivalence_flow(tmp_path: Path, monkeypatch):
    ip = "fresh_web_timer_ip"

    from fastapi.testclient import TestClient
    import src.atlas_ui as atlas_ui

    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    client = _authenticated_client(atlas_ui.create_app())
    with client.websocket_connect("/ws/agent") as ws:
        assert ws.receive_json()["type"] == "hello"
        ws.send_json({"type": "prompt", "text": f"/new-ip {ip} APB4 programmable timer"})
        plan = _receive_slash_output(ws, "[SSOT PLAN]")
        assert ip in plan
        ws.send_json({"type": "prompt", "text": "/grill-me"})
        grill = _receive_slash_output(ws, "[SSOT GRILL]")
        assert "queued ssot-gen LLM" in grill

    ssot_path = tmp_path / ip / "yaml" / f"{ip}.ssot.yaml"
    username = client._atlas_username  # type: ignore[attr-defined]
    state = json.loads((tmp_path / ".session" / username / ip / "ssot-gen" / "state.json").read_text(encoding="utf-8"))
    assert ssot_path.is_file()
    assert state["last_step"] == "grill-me"
    assert state["active_session"] == f"{username}/{ip}/ssot-gen"


def test_atlas_websocket_generates_fl_equivalence_from_ssot_only_ip(tmp_path: Path, monkeypatch):
    ip = _write_ssot_only_fixture(tmp_path)

    from fastapi.testclient import TestClient
    import src.atlas_ui as atlas_ui

    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    client = _authenticated_client(atlas_ui.create_app())
    with client.websocket_connect("/ws/agent") as ws:
        assert ws.receive_json()["type"] == "hello"
        ws.send_json({"type": "prompt", "text": f"/ssot-equiv-goals {ip}"})
        output = _receive_slash_output(ws, "[ssot-equiv-goals]")

    assert "[ssot-equiv-goals] PASS" in output
    model_check = json.loads((tmp_path / ip / "model" / "fl_model_check.json").read_text(encoding="utf-8"))
    decomp = json.loads((tmp_path / ip / "model" / "decomposition.json").read_text(encoding="utf-8"))
    fcov = json.loads((tmp_path / ip / "cov" / "fcov_plan.json").read_text(encoding="utf-8"))
    goals_doc = json.loads((tmp_path / ip / "verify" / "equivalence_goals.json").read_text(encoding="utf-8"))

    assert model_check["passed"] is True
    assert decomp["complete"] is True
    assert len(decomp["units"]) > 0
    assert fcov["planned_before_rtl"] is True
    assert len(fcov["bins"]) > 0
    assert goals_doc["source_of_truth"]["functional_model_exists"] is True
    authority = goals_doc["source_of_truth"]["authority_contract"]
    locked_names = {item["name"] for item in authority["locked_artifacts"]}
    assert {"requirement", "ssot_spec", "functional_model", "coverage_plan", "interface_contract", "performance_target"} <= locked_names
    assert any("rtl" in item for item in authority["llm_editable_artifacts"])
    criteria_ids = {item["id"] for item in authority["general_evaluation_criteria"]}
    assert {"traceability", "functional_equivalence", "module_equivalence", "coverage_closure", "lint_compile", "maintainability"} <= criteria_ids
    assert any(item["loop"] == "module_function" for item in authority["loopable_evidence_points"])
    assert goals_doc["summary"]["total"] > 0
    assert goals_doc["summary"]["blocked"] == 0
    assert goals_doc["summary"]["module_total"] > 0
    assert goals_doc["summary"]["module_blocked"] == 0
    goal_ids = {goal["goal_id"] for goal in goals_doc["goals"]}
    assert any(goal_id.startswith("EQ_TRANSACTION_") for goal_id in goal_ids)
    assert any(goal_id.startswith("EQ_SCENARIO_") for goal_id in goal_ids)
    assert any(goal_id.startswith("EQ_PROTOCOL_") for goal_id in goal_ids)
    assert any(goal_id.startswith("EQ_MODULE_") for goal_id in goal_ids)

    response = client.get("/api/progress", params={"scope": ip})
    assert response.status_code == 200
    equiv_progress = response.json()["selected"]["progress"]["equivalence_goals"]
    assert equiv_progress["module_total"] > 0
    assert equiv_progress["general_evaluation_criteria"]
    assert equiv_progress["locked_artifacts"]
    assert equiv_progress["loopable_evidence_points"]


def test_direct_ssot_equivalence_goals_publish_authority_and_module_progress(tmp_path: Path, monkeypatch):
    ip = _write_ssot_only_fixture(tmp_path)
    fl_path = REPO / "workflow" / "fl-model-gen" / "scripts" / "emit_fl_model.py"
    equiv_path = REPO / "workflow" / "fl-model-gen" / "scripts" / "emit_equivalence_goals.py"

    fl_run = subprocess.run(
        [sys.executable, str(fl_path), ip, "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=30,
    )
    assert fl_run.returncode == 0, fl_run.stdout
    eq_run = subprocess.run(
        [sys.executable, str(equiv_path), ip, "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=30,
    )
    assert eq_run.returncode == 0, eq_run.stdout

    goals_doc = json.loads((tmp_path / ip / "verify" / "equivalence_goals.json").read_text(encoding="utf-8"))
    decomp_doc = json.loads((tmp_path / ip / "model" / "decomposition.json").read_text(encoding="utf-8"))
    fcov_doc = json.loads((tmp_path / ip / "cov" / "fcov_plan.json").read_text(encoding="utf-8"))
    authority = goals_doc["source_of_truth"]["authority_contract"]

    locked_names = {item["name"] for item in authority["locked_artifacts"]}
    assert {"requirement", "ssot_spec", "functional_model", "coverage_plan", "interface_contract", "performance_target"} <= locked_names
    criteria_ids = {item["id"] for item in authority["general_evaluation_criteria"]}
    assert {"traceability", "simulation_evidence", "debug_observability", "human_decision"} <= criteria_ids
    assert any(item["loop"] == "traceability_closure" for item in authority["loopable_evidence_points"])
    assert decomp_doc["authority_contract"]["human_gate_required_for"]
    assert any("traceability" in item for item in decomp_doc["authority_contract"]["general_evaluation_criteria"])
    assert fcov_doc["authority_contract"]["loopable_oracles"]
    assert goals_doc["summary"]["module_total"] > 0
    assert goals_doc["summary"]["module_blocked"] == 0
    assert any(
        isinstance(goal.get("scope"), dict) and goal["scope"].get("level") == "module"
        for goal in goals_doc["goals"]
    )

    from fastapi.testclient import TestClient
    import src.atlas_ui as atlas_ui

    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    client = _authenticated_client(atlas_ui.create_app())
    response = client.get("/api/progress", params={"scope": ip})
    assert response.status_code == 200
    equiv_progress = response.json()["selected"]["progress"]["equivalence_goals"]
    assert equiv_progress["module_total"] == goals_doc["summary"]["module_total"]
    assert equiv_progress["general_evaluation_criteria"]
    assert equiv_progress["locked_artifacts"]
    assert equiv_progress["loopable_evidence_points"]


def test_module_equivalence_requires_module_scope_scoreboard_row(tmp_path: Path):
    ip = "module_scope_contract_ip"
    ip_dir = tmp_path / ip
    for sub in ("verify", "sim", "tb/cocotb"):
        (ip_dir / sub).mkdir(parents=True, exist_ok=True)
    (ip_dir / "verify" / "equivalence_goals.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "summary": {"total": 1, "required": 1, "blocked": 0, "module_total": 1, "module_required": 1, "module_blocked": 0},
                "goals": [
                    {
                        "goal_id": "EQ_MODULE_U_CORE",
                        "title": "Module u_core functionality equals FunctionalModel",
                        "kind": "module",
                        "scope": {"level": "module", "rtl_module": "u_core", "rtl_file": "rtl/u_core.sv"},
                        "ssot_refs": ["function_model.transactions.primary"],
                        "coverage_refs": [],
                        "expected_contract": {"model_api": "FunctionalModel.apply", "observables": ["value"]},
                        "blocked": False,
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "sim" / "scoreboard_events.jsonl").write_text(
        json.dumps(
            {
                "goal_id": "EQ_MODULE_U_CORE",
                "scenario_id": "SC_MODULE",
                "cycle": 3,
                "stimulus": {"value": 4},
                "fl_expected": {"model_api": "FunctionalModel.apply", "model_result": {"value": 8}},
                "rtl_observed": {"value": 8},
                "passed": True,
                "mismatch": "",
                "coverage_refs": [],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "sim" / "results.xml").write_text(
        '<testsuite tests="1" failures="0" errors="0"><testcase name="EQ_MODULE_U_CORE"/></testsuite>\n',
        encoding="utf-8",
    )
    (ip_dir / "tb" / "cocotb" / f"test_{ip}.py").write_text(
        "from equivalence_scoreboard import EquivalenceScoreboard\nscoreboard = EquivalenceScoreboard('module_scope_contract_ip')\n",
        encoding="utf-8",
    )

    check = subprocess.run(
        [
            sys.executable,
            str(CHECK_SCOREBOARD_PATH),
            ip,
            "--root",
            str(tmp_path),
            "--require-events",
            "--require-all-goals",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert check.returncode == 1
    assert "scope.level=module" in check.stdout

    comparator_mod = _load_module(COMPARATOR_PATH, "compare_fl_rtl_results_module_scope_under_test")
    compare_doc, classify_doc = comparator_mod.compare(ip, tmp_path)

    assert compare_doc["status"] == "fail"
    classification = classify_doc["classifications"][0]
    assert classification["classification"] == "tb_bug"
    assert classification["owner"] == "tb-gen"
    assert classification["llm_loop_allowed"] is True
    assert "module equivalence row missing scope.level=module" in classification["reason"]


def test_fl_golden_change_is_human_gate_not_loopable_repair(tmp_path: Path):
    ip = "fl_golden_gate_ip"
    ip_dir = tmp_path / ip
    for sub in ("verify", "sim"):
        (ip_dir / sub).mkdir(parents=True, exist_ok=True)
    (ip_dir / "verify" / "equivalence_goals.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "summary": {"total": 1, "required": 1, "blocked": 0},
                "goals": [
                    {
                        "goal_id": "EQ_GOLDEN",
                        "title": "Golden model behavior",
                        "kind": "transaction",
                        "scope": {"level": "top"},
                        "ssot_refs": ["function_model.transactions[0]"],
                        "coverage_refs": [],
                        "expected_contract": {"model_api": "FunctionalModel.apply", "observables": ["value"]},
                        "blocked": False,
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "sim" / "scoreboard_events.jsonl").write_text(
        json.dumps(
            {
                "goal_id": "EQ_GOLDEN",
                "scenario_id": "SC_GOLDEN",
                "cycle": 5,
                "stimulus": {"value": 2},
                "fl_expected": {"model_api": "FunctionalModel.apply", "model_result": {"value": 4}},
                "rtl_observed": {"value": 5},
                "passed": False,
                "mismatch": "Functional Model golden model change would be required to match observed RTL",
                "coverage_refs": [],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "sim" / "results.xml").write_text(
        '<testsuite tests="1" failures="0" errors="0"><testcase name="EQ_GOLDEN"/></testsuite>\n',
        encoding="utf-8",
    )

    comparator_mod = _load_module(COMPARATOR_PATH, "compare_fl_rtl_results_fl_gate_under_test")
    compare_doc, classify_doc = comparator_mod.compare(ip, tmp_path)

    assert compare_doc["status"] == "fail"
    classification = classify_doc["classifications"][0]
    assert classification["classification"] == "locked_artifact_change_requires_human"
    assert classification["owner"] == "human"
    assert classification["llm_loop_allowed"] is False
    assert "Locked artifact rule:" in classification["human_question"]
    assert classification["repair_prompt"] == ""


def test_fl_model_resolves_output_rule_alias_before_sample_condition(tmp_path: Path):
    ip = _write_fl_output_alias_sample_ssot(tmp_path)
    fl_path = REPO / "workflow" / "fl-model-gen" / "scripts" / "emit_fl_model.py"

    fl_run = subprocess.run(
        [sys.executable, str(fl_path), ip, "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert fl_run.returncode == 0, fl_run.stdout

    model_mod = _load_module(tmp_path / ip / "model" / "functional_model.py", "fl_output_alias_model")
    model = model_mod.FunctionalModel()
    result = model.apply({"kind": "FM_PRIMARY", "cmd_valid": 1})

    assert result["resp"] == 0
    assert result["ready"] == 1
    assert result["cmd_ready"] == 1
    assert result["busy"] == 1
    assert result["sample_accepted"] == 1
    assert result["state_updates"]["accepted_count"] == 1


def test_scoreboard_routes_cmd_ready_scenario_to_primary_not_csr(tmp_path: Path):
    ip = "scoreboard_route_ip"
    ip_dir = tmp_path / ip
    (ip_dir / "model").mkdir(parents=True)
    (ip_dir / "verify").mkdir(parents=True)
    (ip_dir / "model" / "functional_model.py").write_text(
        """
class FunctionalModel:
    def _transactions(self):
        return [
            {"id": "FM_PRIMARY", "name": "primary_behavior"},
            {"id": "FM_CSR", "name": "control_status_access"},
        ]

    def apply(self, txn):
        return {"resp": 0, "transaction_id": txn.get("kind")}
""".lstrip(),
        encoding="utf-8",
    )
    (ip_dir / "verify" / "equivalence_goals.json").write_text(
        json.dumps(
            {
                "goals": [
                    {
                        "goal_id": "EQ_SCENARIO_CMD_READY",
                        "title": "Scenario SC3: command_accepted_only_on_cmd_valid_cmd_ready",
                        "kind": "transaction",
                        "ssot_refs": ["test_requirements.scenarios[3]"],
                        "stimulus_contract": {"transaction_type": "SC3"},
                        "expected_contract": {"observables": ["command accepted on cmd_valid && cmd_ready"]},
                        "pass_criteria": [
                            "Generated sequence executes the SSOT stimulus",
                            "Scoreboard expected result comes from FunctionalModel.apply and SSOT scenario expected field",
                        ],
                        "blocked": False,
                    }
                ]
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    scoreboard_mod = _load_module(SCOREBOARD_PATH, "scoreboard_route_runtime")
    scoreboard = scoreboard_mod.EquivalenceScoreboard(ip, tmp_path, reset_events=True)
    expected = scoreboard.expected_for_goal(
        "EQ_SCENARIO_CMD_READY",
        {"kind": "SC3", "cmd_valid": 1, "cmd_ready": 1},
        "SC_001_EQ_SCENARIO_CMD_READY",
    )

    assert expected["transaction"]["kind"] == "FM_PRIMARY"
    assert expected["model_result"]["transaction_id"] == "FM_PRIMARY"


def test_structured_ssot_rules_drive_fl_model_equivalence_and_rtl_todo_handoff(tmp_path: Path):
    ip = _write_structured_rule_ssot(tmp_path)
    fl_path = REPO / "workflow" / "fl-model-gen" / "scripts" / "emit_fl_model.py"
    equiv_path = REPO / "workflow" / "fl-model-gen" / "scripts" / "emit_equivalence_goals.py"

    fl_run = subprocess.run(
        [sys.executable, str(fl_path), ip, "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert fl_run.returncode == 0, fl_run.stdout

    model_mod = _load_module(tmp_path / ip / "model" / "functional_model.py", "structured_rule_functional_model")
    model = model_mod.FunctionalModel()
    result = model.apply({"kind": "FM_PRIMARY", "value": 13})
    assert result["resp"] == 0
    assert result["result"] == 26
    assert result["state_updates"]["accepted_count"] == 1

    eq_run = subprocess.run(
        [sys.executable, str(equiv_path), ip, "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert eq_run.returncode == 0, eq_run.stdout

    derive_run = subprocess.run(
        [sys.executable, str(DERIVE_RTL_TODOS_PATH), ip, "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert derive_run.returncode == 0, derive_run.stdout

    rtl_run = subprocess.run(
        [sys.executable, str(RTL_GEN_PATH), ip, "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert rtl_run.returncode == 2, rtl_run.stdout
    assert "[RTL BLOCKED]" in rtl_run.stdout
    assert "LLM-authored RTL" in rtl_run.stdout
    assert not (tmp_path / ip / "rtl" / f"{ip}.sv").exists()
    blocked = json.loads((tmp_path / ip / "rtl" / "rtl_blocked.json").read_text(encoding="utf-8"))
    question_ids = {q["id"] for q in blocked["questions"]}
    assert "LLM_RTL_IMPLEMENTATION_REQUIRED" in question_ids
    assert (tmp_path / ip / "rtl" / "rtl_todo_plan.json").is_file()
    todo_plan = json.loads((tmp_path / ip / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    assert todo_plan["summary"]["total_tasks"] > 0
    assert todo_plan["policy"]["fixed_template_role"] == "seed_only"

    goals_doc = json.loads((tmp_path / ip / "verify" / "equivalence_goals.json").read_text(encoding="utf-8"))

    transaction_goal = next(goal for goal in goals_doc["goals"] if goal["goal_id"] == "EQ_TRANSACTION_FM_PRIMARY")
    assert "result" in transaction_goal["expected_contract"]["observables"]


def test_fl_model_supports_register_read_mux_and_reduction_or_helpers(tmp_path: Path):
    ip = _write_structured_rule_ssot(tmp_path)
    ssot_path = tmp_path / ip / "yaml" / f"{ip}.ssot.yaml"
    doc = yaml.safe_load(ssot_path.read_text(encoding="utf-8"))
    doc["registers"] = {
        "register_list": [
            {
                "name": "DATA",
                "offset": 0,
                "width": 32,
                "access": "ro",
                "reset": 5,
                "fields": [
                    {"name": "data", "bits": [7, 0], "access": "ro", "reset": 5, "description": "read data"}
                ],
            }
        ]
    }
    doc["function_model"]["state_variables"].extend(
        [
            {"name": "status_q", "width": 8, "reset": 0},
            {"name": "enable_q", "width": 8, "reset": 0},
        ]
    )
    tx = doc["function_model"]["transactions"][0]
    tx["required_fields"] = ["paddr", "valid", "ready"]
    tx["output_rules"] = [
        {"name": "result", "port": "result", "expr": "read_mux(paddr)", "width": 9},
        {"name": "result_valid", "port": "result_valid", "expr": "|((status_q) & (enable_q))", "width": 1},
    ]
    ssot_path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    fl_path = REPO / "workflow" / "fl-model-gen" / "scripts" / "emit_fl_model.py"

    fl_run = subprocess.run(
        [sys.executable, str(fl_path), ip, "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert fl_run.returncode == 0, fl_run.stdout
    model_mod = _load_module(tmp_path / ip / "model" / "functional_model.py", "fl_helper_function_model")
    model = model_mod.FunctionalModel()
    result = model.apply({"kind": "FM_PRIMARY", "paddr": 0, "valid": 1, "ready": 1, "status_q": 2, "enable_q": 2})
    assert result["resp"] == 0
    assert result["result"] == 5
    assert result["result_valid"] == 1


def test_fl_model_prefers_structured_transaction_over_register_hint_fields(tmp_path: Path):
    ip = _write_structured_rule_ssot(tmp_path)
    ssot_path = tmp_path / ip / "yaml" / f"{ip}.ssot.yaml"
    doc = yaml.safe_load(ssot_path.read_text(encoding="utf-8"))
    doc["io_list"]["interfaces"][0]["ports"].extend(
        [
            {"name": "paddr", "direction": "input", "width": 8},
            {"name": "psel", "direction": "input", "width": 1},
            {"name": "penable", "direction": "input", "width": 1},
            {"name": "pwrite", "direction": "input", "width": 1},
            {"name": "pwdata", "direction": "input", "width": 32},
            {"name": "pslverr", "direction": "output", "width": 1},
        ]
    )
    doc["registers"] = {
        "register_list": [
            {"name": "CTRL", "offset": 0, "width": 32, "access": "rw", "reset": 0}
        ]
    }
    doc["function_model"]["state_variables"][0]["source"] = "registers.CTRL"
    tx = doc["function_model"]["transactions"][0]
    tx["id"] = "FM_APB_WRITE"
    tx["name"] = "apb_write_register"
    tx["required_fields"] = ["paddr", "psel", "penable", "pwrite", "pwdata"]
    tx["sample_condition"] = "psel == 1 and penable == 1 and pwrite == 1"
    tx["output_rules"] = [{"name": "pslverr", "port": "pslverr", "expr": "0 if paddr == 0 else 1", "width": 1}]
    tx["state_updates"] = [{"name": "accepted_count", "expr": "pwdata if paddr == 0 else accepted_count", "width": 8}]
    doc["function_model"]["transactions"].append(
        {
            "id": "FM2",
            "name": "apb_read_register",
            "required_fields": ["paddr", "psel", "penable", "pwrite"],
            "sample_condition": "psel == 1 and penable == 1 and pwrite == 0",
            "output_rules": [{"name": "prdata", "port": "prdata", "expr": "read_mux(paddr)", "width": 32}],
        }
    )
    ssot_path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    fl_path = REPO / "workflow" / "fl-model-gen" / "scripts" / "emit_fl_model.py"

    fl_run = subprocess.run(
        [sys.executable, str(fl_path), ip, "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert fl_run.returncode == 0, fl_run.stdout
    model_mod = _load_module(tmp_path / ip / "model" / "functional_model.py", "fl_structured_apb_model")
    model = model_mod.FunctionalModel()
    result = model.apply(
        {
            "kind": "FM_APB_WRITE",
            "reg": 99,
            "addr_or_name": 99,
            "paddr": 0,
            "psel": 1,
            "penable": 1,
            "pwrite": 1,
            "pwdata": 7,
        }
    )

    assert result["resp"] == 0
    assert result["transaction_id"] == "FM_APB_WRITE"
    assert result["pslverr"] == 0
    assert result["state_updates"]["accepted_count"] == 7
    assert "write" not in result
    read_result = model.apply({"kind": "FM2", "psel": 1, "penable": 1, "pwrite": 0, "paddr": 0})
    assert read_result["prdata"] == 7


def test_module_contract_uses_specific_transaction_ref_over_broad_function_model_ref(tmp_path: Path):
    ip = "specific_ref_gpio"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    ssot_path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    ssot_path.write_text(
        "\n".join(
            [
                "spec_version: '1.0'",
                f"module_name: {ip}",
                f"top_module: {ip}",
                "io_list:",
                "  ports:",
                "    - {name: clk, direction: input, width: 1}",
                "    - {name: rst_n, direction: input, width: 1}",
                "    - {name: result, direction: output, width: 8}",
                "    - {name: result_valid, direction: output, width: 1}",
                "sub_modules:",
                "  - name: gpio_regs",
                "    file: rtl/gpio_regs.sv",
                "    source_sections: [function_model]",
                "    function_model_refs: [function_model.transactions.TR_WRITE]",
                "  - name: gpio_sync",
                "    file: rtl/gpio_sync.sv",
                "    source_sections: [function_model, cycle_model]",
                "    implements: [function_model.transactions.TR_SAMPLE_INPUT]",
                "    function_model_refs: [function_model.transactions.TR_SAMPLE_INPUT]",
                "    cycle_model_refs: [cycle_model.pipeline]",
                "function_model:",
                "  state_variables:",
                "    - {name: data_q, width: 8, reset: 0}",
                "    - {name: sync_q, width: 8, reset: 0}",
                "  transactions:",
                "    - id: TR_WRITE",
                "      name: write_data",
                "      required_fields: [kind]",
                "      output_rules:",
                "        - {name: result, port: result, expr: data_q, width: 8}",
                "    - id: TR_SAMPLE_INPUT",
                "      name: sample_input",
                "      required_fields: [kind]",
                "      output_rules:",
                "        - {name: result, port: result, expr: sync_q, width: 8}",
                "cycle_model:",
                "  latency: 1",
                "  pipeline:",
                "    - {stage: sample, action: sample synchronized input}",
                "test_requirements:",
                "  scenarios:",
                "    - {id: SC_SAMPLE, stimulus: sample input, expected: sampled input visible, checker: result scoreboard}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    fl_path = REPO / "workflow" / "fl-model-gen" / "scripts" / "emit_fl_model.py"
    equiv_path = REPO / "workflow" / "fl-model-gen" / "scripts" / "emit_equivalence_goals.py"

    fl_run = subprocess.run(
        [sys.executable, str(fl_path), ip, "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert fl_run.returncode == 0, fl_run.stdout
    decomp = json.loads((ip_dir / "model" / "decomposition.json").read_text(encoding="utf-8"))
    by_name = {item["name"]: item for item in decomp["module_contracts"]}
    assert "function_model.transactions.tr_sample_input" in by_name["gpio_sync"]["function_model_refs"]
    assert "function_model.transactions.tr_sample_input.output_rules.result" in by_name["gpio_sync"]["function_model_refs"]
    assert "function_model.transactions.tr_sample_input.output_rules.result" not in by_name["gpio_regs"]["function_model_refs"]

    eq_run = subprocess.run(
        [sys.executable, str(equiv_path), ip, "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert eq_run.returncode == 0, eq_run.stdout
    goals = json.loads((ip_dir / "verify" / "equivalence_goals.json").read_text(encoding="utf-8"))
    assert goals["summary"]["blocked"] == 0


def test_atlas_websocket_ssot_rtl_queues_llm_authored_rtl_handoff(tmp_path: Path, monkeypatch):
    ip = _write_structured_rule_ssot(tmp_path)
    fl_path = REPO / "workflow" / "fl-model-gen" / "scripts" / "emit_fl_model.py"
    equiv_path = REPO / "workflow" / "fl-model-gen" / "scripts" / "emit_equivalence_goals.py"
    assert subprocess.run([sys.executable, str(fl_path), ip, "--root", str(tmp_path)], check=False).returncode == 0
    assert subprocess.run([sys.executable, str(equiv_path), ip, "--root", str(tmp_path)], check=False).returncode == 0

    from fastapi.testclient import TestClient
    import src.atlas_ui as atlas_ui

    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    client = _authenticated_client(atlas_ui.create_app())
    with client.websocket_connect("/ws/agent") as ws:
        assert ws.receive_json()["type"] == "hello"
        ws.send_json({"type": "prompt", "text": f"/ssot-rtl {ip}"})
        output = _receive_slash_output(ws, "[RTL BLOCKED]")

    assert "LLM-authored RTL" in output
    assert "rtl_dynamic_todos" in output
    assert f"{ip}/rtl/rtl_blocked.json" in output
    blocked = json.loads((tmp_path / ip / "rtl" / "rtl_blocked.json").read_text(encoding="utf-8"))
    question_ids = {q["id"] for q in blocked["questions"]}
    assert "LLM_RTL_IMPLEMENTATION_REQUIRED" in question_ids
    assert (tmp_path / ip / "rtl" / "rtl_todo_plan.json").is_file()


def test_atlas_websocket_runs_sim_debug_command(tmp_path: Path, monkeypatch):
    ip = _write_fixture(tmp_path)
    scoreboard_mod = _load_module(SCOREBOARD_PATH, "equivalence_scoreboard_ws_under_test")

    scoreboard = scoreboard_mod.EquivalenceScoreboard(ip, tmp_path, reset_events=True)
    scoreboard.record(
        "EQ_DOUBLE",
        scenario_id="SC_DOUBLE",
        cycle=13,
        stimulus={"value": 9},
        rtl_observed={"value": 18},
    )

    from fastapi.testclient import TestClient
    import src.atlas_ui as atlas_ui

    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    client = _authenticated_client(atlas_ui.create_app())
    with client.websocket_connect("/ws/agent") as ws:
        assert ws.receive_json()["type"] == "hello"
        ws.send_json({"type": "prompt", "text": f"/sim-debug {ip}"})
        output = _receive_slash_output(ws, "[sim-debug]")

    assert "[sim-debug] FL-vs-RTL compare" in output
    compare_doc = json.loads((tmp_path / ip / "sim" / "fl_rtl_compare.json").read_text(encoding="utf-8"))
    classify_doc = json.loads((tmp_path / ip / "sim" / "mismatch_classification.json").read_text(encoding="utf-8"))
    assert compare_doc["status"] == "pass"
    assert compare_doc["summary"]["goals_checked"] == 1
    assert classify_doc["status"] == "pass"


def test_atlas_websocket_queues_loopable_equivalence_repair(tmp_path: Path, monkeypatch):
    ip = _write_fixture(tmp_path)
    scoreboard_mod = _load_module(SCOREBOARD_PATH, "equivalence_scoreboard_repair_under_test")
    comparator_mod = _load_module(COMPARATOR_PATH, "compare_fl_rtl_results_repair_under_test")

    scoreboard = scoreboard_mod.EquivalenceScoreboard(ip, tmp_path, reset_events=True)
    scoreboard.record(
        "EQ_DOUBLE",
        scenario_id="SC_DOUBLE",
        cycle=23,
        stimulus={"value": 10},
        rtl_observed={"value": 19},
    )
    compare_doc, classify_doc = comparator_mod.compare(ip, tmp_path)
    assert compare_doc["status"] == "fail"
    assert classify_doc["classifications"][0]["llm_loop_allowed"] is True
    assert classify_doc["classifications"][0]["owner"] == "rtl-gen"

    from fastapi.testclient import TestClient
    import src.atlas_ui as atlas_ui

    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    client = _authenticated_client(atlas_ui.create_app())
    with client.websocket_connect("/ws/agent") as ws:
        assert ws.receive_json()["type"] == "hello"
        ws.send_json({"type": "prompt", "text": f"/repair-equiv {ip}"})
        output = _receive_slash_output(ws, "[repair-equiv]")

    assert "queued loopable equivalence repairs" in output
    assert "rtl-gen: 1 classification" in output
    assert "human-gated: 0" in output


def test_atlas_websocket_runs_goal_audit_command(tmp_path: Path, monkeypatch):
    ip = _write_goal_audit_complete_fixture(tmp_path)

    from fastapi.testclient import TestClient
    import src.atlas_ui as atlas_ui

    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    client = _authenticated_client(atlas_ui.create_app())
    with client.websocket_connect("/ws/agent") as ws:
        assert ws.receive_json()["type"] == "hello"
        ws.send_json({"type": "prompt", "text": f"/goal-audit {ip}"})
        output = _receive_slash_output(ws, "[goal-audit]")

    assert "[goal-audit] PASS" in output
    assert f"module: {ip}" in output
    audit_doc = json.loads((tmp_path / ip / "sim" / "fl_rtl_goal_audit.json").read_text(encoding="utf-8"))
    assert audit_doc["status"] == "pass"
    response = client.get("/api/progress", params={"scope": ip})
    assert response.status_code == 200
    selected = response.json()["selected"]
    assert selected["progress"]["goal_audit"]["status"] == "pass"
    assert selected["signoff"]["status"]["goal_audit"] == "pass"


def test_atlas_websocket_sim_debug_human_gate_persists_answer(tmp_path: Path, monkeypatch):
    ip = _write_fixture(tmp_path)
    goals_path = tmp_path / ip / "verify" / "equivalence_goals.json"
    goals_doc = json.loads(goals_path.read_text(encoding="utf-8"))
    goals_doc["summary"] = {"total": 1, "required": 0, "optional": 0, "blocked": 1}
    goals_doc["goals"][0]["blocked"] = True
    goals_doc["goals"][0]["blocker"] = "undefined SSOT behavior for response ordering"
    goals_path.write_text(json.dumps(goals_doc, indent=2) + "\n", encoding="utf-8")

    from fastapi.testclient import TestClient
    import src.atlas_ui as atlas_ui

    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    client = _authenticated_client(atlas_ui.create_app())
    with client.websocket_connect("/ws/agent") as ws:
        assert ws.receive_json()["type"] == "hello"
        ws.send_json({"type": "prompt", "text": f"/sim-debug {ip}"})
        qcard = _receive_ws_event(ws, "ask_user", "EQ_DOUBLE")
        flow_id = qcard["flow_id"]
        ws.send_json({
            "type": "answer",
            "flow_id": flow_id,
            "answers": [
                {
                    "selected": ["EQ_DOUBLE_update_ssot"],
                    "custom": "Expected response ordering is FIFO by accepted transaction.",
                }
            ],
        })
        captured = _receive_slash_output(ws, "[SIM HUMAN GATE] captured")

    assert "human_gate_answers.json" in captured
    answer_path = tmp_path / ip / "sim" / "human_gate_answers.json"
    username = client._atlas_username  # type: ignore[attr-defined]
    state_path = tmp_path / ".session" / username / ip / "ssot-gen" / "state.json"
    answers = json.loads(answer_path.read_text(encoding="utf-8"))
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert answers["answers"][0]["goal_id"] == "EQ_DOUBLE"
    assert answers["answers"][0]["classification"] == "ssot_ambiguity"
    assert "FIFO" in answers["answers"][0]["answer"]
    assert state["status"] == "equivalence_human_gate_answered"
    assert state["equivalence_human_gate_answers"][0]["goal_id"] == "EQ_DOUBLE"


def test_atlas_websocket_runs_fresh_structured_ip_full_equivalence_flow(tmp_path: Path, monkeypatch):
    if not shutil.which("iverilog"):
        pytest.skip("iverilog is required for cocotb/RTL simulation")
    if not (shutil.which("verilator") or shutil.which("iverilog")):
        pytest.skip("verilator or iverilog is required for DUT lint evidence")
    pytest.importorskip("cocotb_test")

    ip = _write_structured_rule_ssot(tmp_path)
    _write_structured_rule_req(tmp_path, ip)

    from fastapi.testclient import TestClient
    import src.atlas_ui as atlas_ui

    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    client = _authenticated_client(atlas_ui.create_app())
    with client.websocket_connect("/ws/agent") as ws:
        assert ws.receive_json()["type"] == "hello"
        ws.send_json({"type": "prompt", "text": f"/ssot-equiv-goals {ip}"})
        eq_out = _receive_slash_output(ws, "[ssot-equiv-goals]")
        assert "[ssot-equiv-goals] PASS" in eq_out

        ws.send_json({"type": "prompt", "text": f"/ssot-rtl {ip}"})
        rtl_out = _receive_slash_output(ws, "[RTL RESULT]")
        assert "PASS - generated RTL and DUT-only compile/lint evidence" in rtl_out

        ws.send_json({"type": "prompt", "text": f"/tb {ip}"})
        tb_out = _receive_slash_output(ws, "[ssot-tb-cocotb]")
        assert "PASS - generated goal-driven pyuvm/cocotb scoreboard" in tb_out

        ws.send_json({"type": "prompt", "text": f"/sim {ip}"})
        sim_out = _receive_slash_output(ws, "[sim]")
        assert "[sim] PASS" in sim_out

        ws.send_json({"type": "prompt", "text": f"/sim-debug {ip}"})
        debug_out = _receive_slash_output(ws, "[sim-debug]")
        assert "status=pass" in debug_out

        ws.send_json({"type": "prompt", "text": f"/goal-audit {ip}"})
        audit_out = _receive_slash_output(ws, "[goal-audit]")
        assert "[goal-audit] PASS" in audit_out

        ws.send_json({"type": "prompt", "text": f"/signoff {ip}"})
        signoff_out = _receive_slash_output(ws, "[signoff] strict SSOT progress gate")
        assert f"module: {ip}" in signoff_out

    audit_doc = json.loads((tmp_path / ip / "sim" / "fl_rtl_goal_audit.json").read_text(encoding="utf-8"))
    compare_doc = json.loads((tmp_path / ip / "sim" / "fl_rtl_compare.json").read_text(encoding="utf-8"))
    coverage_doc = json.loads((tmp_path / ip / "cov" / "coverage.json").read_text(encoding="utf-8"))
    assert audit_doc["status"] == "pass"
    assert audit_doc["stop_condition"]["signoff_evidence_backed"] is True
    assert compare_doc["status"] == "pass"
    assert compare_doc["summary"]["goals_checked"] == compare_doc["summary"]["total"]
    assert coverage_doc["status"] == "pass"

    response = client.get("/api/progress", params={"scope": ip})
    assert response.status_code == 200
    selected = response.json()["selected"]
    assert selected["progress"]["equivalence_goals"]["status"] == "pass"
    assert selected["progress"]["goal_audit"]["status"] == "pass"
    assert selected["signoff"]["status"]["goal_audit"] == "pass"
    assert selected["signoff"]["status"]["equivalence_goals"] == "pass"


def test_live_atlas_server_5400_equivalence_smoke(tmp_path: Path, monkeypatch):
    host = "127.0.0.1"
    port = 5400
    if _port_open(host, port):
        pytest.skip("port 5400 is already occupied by an external ATLAS backend")

    uvicorn = pytest.importorskip("uvicorn")
    websockets = pytest.importorskip("websockets")

    ip = _write_fixture(tmp_path)
    _write_executable_sim_runner(tmp_path, ip)

    import src.atlas_ui as atlas_ui

    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    server = uvicorn.Server(
        uvicorn.Config(
            atlas_ui.create_app(),
            host=host,
            port=port,
            log_level="warning",
            access_log=False,
        )
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    try:
        deadline = time.time() + 8
        health = {}
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(f"http://{host}:{port}/healthz", timeout=1) as response:
                    health = json.loads(response.read().decode("utf-8"))
                break
            except Exception:
                time.sleep(0.1)
        assert health.get("ok") is True
        cookie = _register_live_user(f"http://{host}:{port}")

        async def drive_live_backend():
            async with websockets.connect(
                f"ws://{host}:{port}/ws/agent",
                extra_headers={"Cookie": cookie},
                open_timeout=3,
            ) as ws:
                hello = json.loads(await ws.recv())
                assert hello["type"] == "hello"

                await ws.send(json.dumps({"type": "prompt", "text": f"/ssot-equiv-goals {ip}"}))
                for _ in range(30):
                    msg = json.loads(await ws.recv())
                    if msg.get("type") == "slash_output" and "[ssot-equiv-goals]" in str(msg.get("text")):
                        assert "[ssot-equiv-goals] PASS" in msg["text"]
                        break
                else:
                    raise AssertionError("missing live /ssot-equiv-goals output")

                await ws.send(json.dumps({"type": "prompt", "text": f"/sim {ip}"}))
                for _ in range(30):
                    msg = json.loads(await ws.recv())
                    if msg.get("type") == "slash_output" and "[sim]" in str(msg.get("text")):
                        assert "[sim] PASS" in msg["text"]
                        break
                else:
                    raise AssertionError("missing live /sim output")

                await ws.send(json.dumps({"type": "prompt", "text": f"/sim-debug {ip}"}))
                for _ in range(30):
                    msg = json.loads(await ws.recv())
                    if msg.get("type") == "slash_output" and "[sim-debug] FL-vs-RTL compare" in str(msg.get("text")):
                        assert "status=pass" in msg["text"]
                        return
                raise AssertionError("missing live /sim-debug output")

        asyncio.run(drive_live_backend())

        request = urllib.request.Request(
            f"http://{host}:{port}/api/progress?scope={ip}",
            headers={"Cookie": cookie},
        )
        with urllib.request.urlopen(request, timeout=2) as response:
            progress = json.loads(response.read().decode("utf-8"))
        equiv = progress["selected"]["progress"]["equivalence_goals"]
        assert equiv["status"] == "pass"
        assert equiv["total"] >= 1
        assert equiv["checked"] == equiv["total"]
        assert equiv["passed"] == equiv["total"]
    finally:
        server.should_exit = True
        thread.join(timeout=5)
        assert not thread.is_alive()
