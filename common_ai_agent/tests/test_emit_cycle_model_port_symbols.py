"""CL self-check must bind declared io ports as rule expression symbols.

Regression evidence for OBL_CL_COMBINATIONAL_RULE_SYMBOLS (campaign finding 19).

``emit_cycle_model`` generates a ``cycle_model.py`` whose ``run_self_check``
drives every declared transaction once through the *real* FunctionalModel
oracle. A purely combinational IP (e.g. add8_cin_v1) declares its operands as
``function_model.transactions[].inputs[].port`` (``a``, ``b``, ``cin``) and its
output rules reference those io ports directly (``(a + b + cin) & 255``). The
FL oracle binds rule symbols from the transaction payload, so the cycle
self-check has to seed every declared input PORT NAME or the oracle raises
"unknown rule name a" and the self-check reports ``fl_errors``.

Unlike the existing ``test_emit_cycle_model.py`` cases (which stub
FunctionalModel and only exercise the static symbol contract), these tests
generate the *real* FunctionalModel via ``emit_fl_model`` so the runtime rule
evaluation actually executes — the only way to reproduce the live defect.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "workflow" / "fl-model-gen" / "scripts"
EMIT_FL_MODEL = SCRIPTS / "emit_fl_model.py"
EMIT_CYCLE_MODEL = SCRIPTS / "emit_cycle_model.py"

LIVE_ADD8 = Path(
    "/Users/brian/Desktop/Project/NEW_WORKSPACE/admin/default/add8_cin_v1"
)


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _write_ssot(ip_dir: Path, ssot: dict) -> None:
    import yaml  # local import: only the tests need a yaml dumper

    (ip_dir / "yaml").mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip_dir.name}.ssot.yaml").write_text(
        yaml.safe_dump(ssot, sort_keys=False), encoding="utf-8"
    )


def _emit_fl(ip: str, root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(EMIT_FL_MODEL), ip, "--root", str(root), "--no-semantic"],
        text=True,
        capture_output=True,
        check=False,
    )


def _emit_cl(ip: str, root: Path) -> subprocess.CompletedProcess:
    # Skip the LLM judge; the deterministic semantic backstop still runs.
    return subprocess.run(
        [sys.executable, str(EMIT_CYCLE_MODEL), ip, "--root", str(root), "--no-semantic-llm"],
        text=True,
        capture_output=True,
        check=False,
    )


def _cl_report(ip: str, root: Path) -> dict:
    return json.loads(
        (root / ip / "model" / "cl_model_check.json").read_text(encoding="utf-8")
    )


# A combinational IP shaped like add8_cin_v1: operand ports declared via
# transactions[].inputs[].port, output rules referencing them directly, and a
# cycle_model trigger (frequency target) that forces an executable CL stepper.
def _comb_ssot(ip: str) -> dict:
    return {
        "top_module": {"name": ip, "type": "combinational_arithmetic"},
        "io_list": {
            "ports": [
                {"name": "a", "direction": "input", "width": 8},
                {"name": "b", "direction": "input", "width": 8},
                {"name": "cin", "direction": "input", "width": 1},
                {"name": "sum", "direction": "output", "width": 8},
                {"name": "cout", "direction": "output", "width": 1},
            ]
        },
        "function_model": {
            "transactions": [
                {
                    "id": "add",
                    "name": "combinational_add",
                    "inputs": [
                        {"port": "a", "width": 8},
                        {"port": "b", "width": 8},
                        {"port": "cin", "width": 1},
                    ],
                    "outputs": [
                        {"port": "sum", "width": 8},
                        {"port": "cout", "width": 1},
                    ],
                    "output_rules": [
                        {"name": "sum_result", "port": "sum",
                         "expr": "(a + b + cin) & 255", "width": 8},
                        {"name": "carry_result", "port": "cout",
                         "expr": "((a + b + cin) >> 8) & 1", "width": 1},
                    ],
                }
            ]
        },
        "cycle_model": {
            "cycle_model_waiver": True,
            "latency": {"input_to_output": {"min_cycles": 0, "max_cycles": 0}},
        },
        "synthesis": {"ppa_targets": {"frequency_mhz_min": 100}},
    }


# --------------------------------------------------------------------------- #
# 1. combinational IP referencing io ports directly → CL self-check passes
# --------------------------------------------------------------------------- #
def test_cl_self_check_binds_combinational_io_port_symbols(tmp_path: Path) -> None:
    ip = "comb_add_port_ip"
    ip_dir = tmp_path / ip
    _write_ssot(ip_dir, _comb_ssot(ip))

    fl = _emit_fl(ip, tmp_path)
    assert fl.returncode == 0, fl.stdout + fl.stderr

    cl = _emit_cl(ip, tmp_path)
    assert cl.returncode == 0, cl.stdout + cl.stderr

    report = _cl_report(ip, tmp_path)
    assert report["passed"] is True, json.dumps(report["self_check"], indent=2)

    self_check = report["self_check"]
    assert self_check["passed"] is True
    assert self_check["fl_errors"] == []
    # Every declared transaction was driven through the oracle and observed.
    assert self_check["results_observed"] == self_check["transactions"]
    # The static symbol contract was already clean (io ports are declared);
    # the fix is purely the runtime seeding of those ports into the self-check.
    assert report["symbol_contract"]["status"] == "pass"

    # The bug surfaced as an "unknown rule name <port>" fl_error — assert it is
    # gone from the entire report, not merely that passed flipped to True.
    assert "unknown rule name" not in json.dumps(report)


# --------------------------------------------------------------------------- #
# 2. sequential IP (state_variables + clocked rules) → unchanged, still passes
# --------------------------------------------------------------------------- #
def test_cl_self_check_sequential_ip_still_passes(tmp_path: Path) -> None:
    ip = "seq_counter_ip"
    ip_dir = tmp_path / ip
    _write_ssot(
        ip_dir,
        {
            "top_module": {"name": ip},
            "function_model": {
                "state_variables": [{"name": "count_q", "reset": 0, "width": 8}],
                "transactions": [
                    {
                        "id": "increment",
                        "name": "increment",
                        "required_fields": ["en"],
                        "output_rules": [
                            {"name": "count_o", "expr": "count_q", "width": 8},
                        ],
                        "state_updates": [
                            {"name": "count_q",
                             "expr": "(count_q + en) & 255", "width": 8},
                        ],
                    }
                ],
            },
            "cycle_model": {
                "executable": "python",
                "latency": {"increment": {"min_cycles": 1, "max_cycles": 1}},
                "handshake_rules": [
                    {"name": "valid_ready", "description": "valid-ready beat"},
                ],
                "ordering": [
                    {"name": "in_order", "description": "responses in request order"},
                ],
            },
        },
    )

    fl = _emit_fl(ip, tmp_path)
    assert fl.returncode == 0, fl.stdout + fl.stderr

    cl = _emit_cl(ip, tmp_path)
    assert cl.returncode == 0, cl.stdout + cl.stderr

    report = _cl_report(ip, tmp_path)
    assert report["passed"] is True, json.dumps(report["self_check"], indent=2)
    assert report["self_check"]["fl_errors"] == []
    assert report["symbol_contract"]["status"] == "pass"


# --------------------------------------------------------------------------- #
# 3. genuinely unknown symbol → gate must still FAIL (no silent pass)
# --------------------------------------------------------------------------- #
def test_cl_gate_still_blocks_genuinely_unknown_symbol(tmp_path: Path) -> None:
    ip = "comb_unknown_symbol_ip"
    ssot = _comb_ssot(ip)
    # Reference a symbol that is NOT a declared io port / param / state / derived.
    ssot["function_model"]["transactions"][0]["output_rules"].append(
        {"name": "bogus", "expr": "(a + b + nonexistent_signal) & 255", "width": 8}
    )
    ip_dir = tmp_path / ip
    _write_ssot(ip_dir, ssot)

    fl = _emit_fl(ip, tmp_path)
    assert fl.returncode == 0, fl.stdout + fl.stderr

    cl = _emit_cl(ip, tmp_path)
    # The static symbol contract catches the undeclared symbol up front.
    assert cl.returncode != 0, cl.stdout + cl.stderr

    report = _cl_report(ip, tmp_path)
    assert report["passed"] is False
    sc = report["symbol_contract"]
    assert sc["status"] == "blocked"
    assert "nonexistent_signal" in sc["unknown_symbols"]
    # The fix ADDS port bindings; it must not bind invented names. Seeding the
    # known ports (a, b) must not mask the genuinely missing one.
    assert sc["unknown_symbols"] == ["nonexistent_signal"]


# --------------------------------------------------------------------------- #
# 4. real-workspace acceptance (READ-ONLY copy of the live add8 SSOT + req)
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(
    not (LIVE_ADD8 / "yaml" / "add8_cin_v1.ssot.yaml").is_file(),
    reason="live add8_cin_v1 workspace not present",
)
def test_cl_self_check_passes_on_live_add8_ssot_copy(tmp_path: Path) -> None:
    """Copy the live add8 SSOT + req into a tmp dir (never touch the workspace)
    and prove the generated CL self-check passes end-to-end."""
    ip = "add8_cin_v1"
    ip_dir = tmp_path / ip
    ip_dir.mkdir(parents=True)
    shutil.copytree(LIVE_ADD8 / "yaml", ip_dir / "yaml")
    shutil.copytree(LIVE_ADD8 / "req", ip_dir / "req")

    fl = _emit_fl(ip, tmp_path)
    assert fl.returncode == 0, fl.stdout + fl.stderr

    cl = _emit_cl(ip, tmp_path)
    assert cl.returncode == 0, cl.stdout + cl.stderr

    report = _cl_report(ip, tmp_path)
    assert report["passed"] is True, json.dumps(report, indent=2)
    assert report["self_check"]["fl_errors"] == []
    assert "unknown rule name" not in json.dumps(report)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
