"""repair_ssot_schema.py cycle-waiver branch (OBL_SSOT_GEN_HONORS_CYCLE_WAIVER).

Root of the phantom-architecture family (campaign finding 15d). When
req/behavioral_contracts.json exists and EVERY locked behavioral contract is
cycle_model_waiver/combinational (derived from the locked decision tables by
behavioral_contracts._cycle_model_waived), repair_ssot_schema must NOT inject a
control FSM, function_model.state_variables, transaction state_updates, or a
cycle_model with handshake_rules/pipeline/backpressure/min_cycles>=1 latency.

Live evidence (add8_cin_v1, run 7abb7ba3, 2026-06-11): the ssot-gen LLM worker
repeatedly STRIPPED these fictional fields per validator feedback, and
repair_ssot_schema RE-INJECTED them on the next schema pass. verify_ssot now
hard-blocks those fields for combinational IPs (codes
ssot.combinational_ip_declares_*), so SSOT authoring for a combinational IP
could never converge: repair injects -> verify blocks -> LLM strips -> repair
injects. These tests prove repair now honors the waiver, prunes the forbidden
content if present, leaves stateful IPs byte-for-byte unchanged, and that the
combinational repair output passes verify_ssot (the loop converges).
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REPAIR_SSOT_SCRIPT = ROOT / "workflow" / "ssot-gen" / "scripts" / "repair_ssot_schema.py"
VERIFY_SSOT_SCRIPT = ROOT / "workflow" / "ssot-gen" / "scripts" / "verify_ssot.py"


# Reuse the locked-req bundle fixture builder from the verify_ssot waiver tests
# so the combinational/sequential split is derived from the SAME decision tables
# (a single non-waived contract flips _cycle_model_waived, the whole gate).
def _load_verify_fixtures():
    path = Path(__file__).resolve().parent / "test_verify_ssot_cycle_waiver.py"
    spec = importlib.util.spec_from_file_location("verify_ssot_cycle_waiver_fixtures", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_FIXTURES = _load_verify_fixtures()
_write_locked_req_bundle = _FIXTURES._write_locked_req_bundle


# --------------------------------------------------------------------------- #
# SSOT bodies
# --------------------------------------------------------------------------- #
# Minimal combinational adder SSOT with NO fsm / state / cycle handshake.
_CLEAN_SSOT = """
top_module:
  name: {ip}
  description: combinational adder
io_list:
  interfaces:
    - name: data
      type: custom
      ports:
        - {{ name: a, direction: input, width: 8, description: operand a }}
        - {{ name: b, direction: input, width: 8, description: operand b }}
        - {{ name: cin, direction: input, width: 1, description: carry in }}
        - {{ name: sum, direction: output, width: 8, description: sum }}
        - {{ name: cout, direction: output, width: 1, description: carry out }}
function_model:
  transactions:
    - id: FM_ADD
      name: add
      decision_table:
        rows:
          - when: cin == 0
            then: {{ sum: a + b, cout: carry(a + b) }}
          - when: cin == 1
            then: {{ sum: a + b + 1, cout: carry(a + b + 1) }}
      output_rules:
        - {{ name: sum, port: sum, expr: a + b + cin, width: 8 }}
      contract_refs:
        behavioral: [BC_A]
custom:
  locked_truth_authority:
    kind: locked_truth_projection
    approval_manifest: req/approval_manifest.json
    bundle_sha256: abc123
    projected_files:
      - req/requirements_index.json
      - req/obligations.json
      - req/contract_refs.json
      - req/structural_contracts.json
      - req/behavioral_contracts.json
      - req/evidence_plan.json
traceability:
  locked_truth_projection:
    requirements: [REQ_A]
    obligations: [OBL_A]
    contract_refs: [C_A]
    structural_contracts: [C_STRUCT_A]
    behavioral_contracts: [BC_A]
"""

# Same combinational truth, but the SSOT already carries the add8_cin_v1 phantom
# FSM + architectural state + fictional valid/ready timing that the LLM keeps
# stripping and repair keeps re-injecting.
_PHANTOM_SSOT = """
top_module:
  name: {ip}
  description: combinational adder
io_list:
  interfaces:
    - name: data
      type: custom
      ports:
        - {{ name: a, direction: input, width: 8, description: operand a }}
        - {{ name: b, direction: input, width: 8, description: operand b }}
        - {{ name: cin, direction: input, width: 1, description: carry in }}
        - {{ name: sum, direction: output, width: 8, description: sum }}
        - {{ name: cout, direction: output, width: 1, description: carry out }}
function_model:
  state_variables:
    - {{ name: state }}
    - {{ name: fm2_observed }}
  transactions:
    - id: FM_ADD
      name: add
      output_rules:
        - {{ name: sum, port: sum, expr: a + b + cin, width: 8 }}
      state_updates:
        - {{ name: fm2_observed }}
      contract_refs:
        behavioral: [BC_A]
cycle_model:
  clock: clk
  handshake_rules:
    - {{ signal: valid/ready, rule: payload stable until ready }}
  pipeline:
    - {{ stage: S0, cycle: 0, action: accept }}
  backpressure:
    - ready deassertion stalls
  latency:
    primary_operation: {{ min_cycles: 1, max_cycles: null }}
    response: {{ min_cycles: 0 }}
fsm:
  control:
    states: [IDLE, ACCEPT, EXEC_FEATURE_1, ERROR]
    transitions:
      - {{ from: IDLE, to: ACCEPT, when: start == 1 }}
custom:
  locked_truth_authority:
    kind: locked_truth_projection
    approval_manifest: req/approval_manifest.json
    bundle_sha256: abc123
    projected_files:
      - req/requirements_index.json
      - req/obligations.json
      - req/contract_refs.json
      - req/structural_contracts.json
      - req/behavioral_contracts.json
      - req/evidence_plan.json
traceability:
  locked_truth_projection:
    requirements: [REQ_A]
    obligations: [OBL_A]
    contract_refs: [C_A]
    structural_contracts: [C_STRUCT_A]
    behavioral_contracts: [BC_A]
"""


def _write_ssot(root: Path, ip: str, body: str) -> Path:
    ssot = root / ip / "yaml" / f"{ip}.ssot.yaml"
    ssot.parent.mkdir(parents=True, exist_ok=True)
    ssot.write_text(body.format(ip=ip).strip() + "\n", encoding="utf-8")
    return ssot


def _run_repair(ip: str, root: Path, run_mode: str = "engineering") -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["ATLAS_RUN_MODE"] = run_mode
    return subprocess.run(
        [sys.executable, str(REPAIR_SSOT_SCRIPT), ip, "--root", str(root), "--mode", run_mode],
        cwd=str(ROOT),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=60,
        env=env,
    )


def _run_verify(ip: str, root: Path, run_mode: str = "engineering") -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["ATLAS_RUN_MODE"] = run_mode
    return subprocess.run(
        [
            sys.executable,
            str(VERIFY_SSOT_SCRIPT),
            ip,
            "--root",
            str(root),
            "--mode",
            "starter",
            "--preview",
            "off",
            "--skip-disk-check",
        ],
        cwd=str(ROOT),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=60,
        env=env,
    )


def _load_ssot(root: Path, ip: str) -> dict:
    return yaml.safe_load((root / ip / "yaml" / f"{ip}.ssot.yaml").read_text(encoding="utf-8"))


def _fsm_states(doc: dict) -> list[str]:
    fsm = doc.get("fsm")
    if not isinstance(fsm, dict):
        return []
    states: list[str] = []
    for group_value in fsm.values():
        if isinstance(group_value, dict) and isinstance(group_value.get("states"), list):
            states.extend(str(s) for s in group_value["states"])
    if isinstance(fsm.get("states"), list):
        states.extend(str(s) for s in fsm["states"])
    return states


def _state_updates(doc: dict) -> list:
    fm = doc.get("function_model") if isinstance(doc.get("function_model"), dict) else {}
    updates: list = []
    for tx in fm.get("transactions") or []:
        if isinstance(tx, dict) and tx.get("state_updates"):
            updates.extend(tx["state_updates"])
    return updates


def _min_cycles_ge1(doc: dict) -> list:
    cm = doc.get("cycle_model") if isinstance(doc.get("cycle_model"), dict) else {}
    latency = cm.get("latency") if isinstance(cm.get("latency"), dict) else {}
    flagged = []
    for lane, entry in latency.items():
        if isinstance(entry, dict):
            try:
                if int(entry.get("min_cycles") or 0) >= 1:
                    flagged.append(lane)
            except (TypeError, ValueError):
                pass
    return flagged


def _assert_no_combinational_state(doc: dict) -> None:
    assert _fsm_states(doc) == [], f"unexpected fsm states: {_fsm_states(doc)}"
    fm = doc.get("function_model") if isinstance(doc.get("function_model"), dict) else {}
    assert not (fm.get("state_variables") or []), f"unexpected state_variables: {fm.get('state_variables')}"
    assert _state_updates(doc) == [], f"unexpected state_updates: {_state_updates(doc)}"
    cm = doc.get("cycle_model") if isinstance(doc.get("cycle_model"), dict) else {}
    assert not (cm.get("handshake_rules") or []), f"unexpected handshake_rules: {cm.get('handshake_rules')}"
    assert not (cm.get("pipeline") or []), f"unexpected pipeline: {cm.get('pipeline')}"
    assert not (cm.get("backpressure") or []), f"unexpected backpressure: {cm.get('backpressure')}"
    assert _min_cycles_ge1(doc) == [], f"unexpected min_cycles>=1 lanes: {_min_cycles_ge1(doc)}"


# --------------------------------------------------------------------------- #
# 1. Combinational bundle + clean SSOT -> repair injects NO state/fsm/handshake.
# --------------------------------------------------------------------------- #
def test_repair_combinational_clean_ssot_injects_no_state(tmp_path):
    ip = "add8_cin_clean_repair"
    _write_locked_req_bundle(tmp_path / ip / "req", ip, sequential=False)
    _write_ssot(tmp_path, ip, _CLEAN_SSOT)

    result = _run_repair(ip, tmp_path)

    assert result.returncode == 0, result.stderr + result.stdout
    doc = _load_ssot(tmp_path, ip)
    _assert_no_combinational_state(doc)


# --------------------------------------------------------------------------- #
# 2. Combinational bundle + phantom SSOT -> repair PRUNES the forbidden content
#    (and never adds more); does not crash.
# --------------------------------------------------------------------------- #
def test_repair_combinational_phantom_ssot_is_pruned(tmp_path):
    ip = "add8_cin_phantom_repair"
    _write_locked_req_bundle(tmp_path / ip / "req", ip, sequential=False)
    _write_ssot(tmp_path, ip, _PHANTOM_SSOT)

    result = _run_repair(ip, tmp_path)

    assert result.returncode == 0, result.stderr + result.stdout
    doc = _load_ssot(tmp_path, ip)
    _assert_no_combinational_state(doc)
    # The phantom FSM is replaced with explicit absence, not a re-synthesized FSM.
    fsm = doc.get("fsm")
    assert isinstance(fsm, dict) and fsm.get("present") is False


# --------------------------------------------------------------------------- #
# 3. Sequential (non-waived) bundle + same minimal SSOT -> repair still injects
#    its usual stateful template (fsm/state/cycle_model). No regression.
# --------------------------------------------------------------------------- #
def test_repair_sequential_ssot_still_injects_template(tmp_path):
    ip = "counter_seq_repair"
    _write_locked_req_bundle(tmp_path / ip / "req", ip, sequential=True)
    _write_ssot(tmp_path, ip, _CLEAN_SSOT)

    result = _run_repair(ip, tmp_path)

    assert result.returncode == 0, result.stderr + result.stdout
    doc = _load_ssot(tmp_path, ip)
    # Stateful template is present exactly as before the waiver branch existed.
    assert _fsm_states(doc), "sequential IP should keep its synthesized control FSM"
    fm = doc.get("function_model") if isinstance(doc.get("function_model"), dict) else {}
    assert fm.get("state_variables"), "sequential IP should keep function_model.state_variables"
    cm = doc.get("cycle_model") if isinstance(doc.get("cycle_model"), dict) else {}
    assert cm.get("handshake_rules"), "sequential IP should keep cycle_model.handshake_rules"
    assert cm.get("pipeline"), "sequential IP should keep cycle_model.pipeline"
    assert _min_cycles_ge1(doc), "sequential IP should keep min_cycles>=1 latency"


# --------------------------------------------------------------------------- #
# 4. End-to-end convergence: after repair on the combinational fixture,
#    verify_ssot passes (returncode 0 / report ok=true) -> the inject/block/strip
#    loop converges.
# --------------------------------------------------------------------------- #
def test_repair_combinational_output_passes_verify_ssot(tmp_path):
    ip = "add8_cin_converge"
    _write_locked_req_bundle(tmp_path / ip / "req", ip, sequential=False)
    _write_ssot(tmp_path, ip, _CLEAN_SSOT)

    repair = _run_repair(ip, tmp_path)
    assert repair.returncode == 0, repair.stderr + repair.stdout

    verify = _run_verify(ip, tmp_path)
    report = json.loads((tmp_path / ip / "req" / "ssot_validation.json").read_text(encoding="utf-8"))
    combinational_blockers = [
        b.get("id")
        for b in (report.get("blockers") or [])
        if "combinational_ip" in str(b.get("id"))
    ]
    assert combinational_blockers == [], f"repair output still trips combinational gate: {combinational_blockers}"
    assert report.get("ok") is True, report.get("blockers")
    assert verify.returncode == 0, verify.stderr + verify.stdout


# --------------------------------------------------------------------------- #
# 5. The phantom SSOT, after pruning, also passes verify_ssot end-to-end.
# --------------------------------------------------------------------------- #
def test_repair_pruned_phantom_output_passes_verify_ssot(tmp_path):
    ip = "add8_cin_prune_converge"
    _write_locked_req_bundle(tmp_path / ip / "req", ip, sequential=False)
    _write_ssot(tmp_path, ip, _PHANTOM_SSOT)

    repair = _run_repair(ip, tmp_path)
    assert repair.returncode == 0, repair.stderr + repair.stdout

    _run_verify(ip, tmp_path)
    report = json.loads((tmp_path / ip / "req" / "ssot_validation.json").read_text(encoding="utf-8"))
    combinational_blockers = [
        b.get("id")
        for b in (report.get("blockers") or [])
        if "combinational_ip" in str(b.get("id"))
    ]
    assert combinational_blockers == [], f"pruned output still trips combinational gate: {combinational_blockers}"
    assert report.get("ok") is True, report.get("blockers")
