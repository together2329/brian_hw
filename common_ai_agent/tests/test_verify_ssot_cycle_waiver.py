"""verify_ssot.py combinational-state gate (OBL_SSOT_GEN_HONORS_CYCLE_WAIVER).

When req/behavioral_contracts.json exists and EVERY locked behavioral contract
is cycle_model_waiver/combinational (derived from the locked decision tables by
behavioral_contracts._cycle_model_waived), the SSOT must declare no state-control
FSM and no architectural state. This mirrors the live add8_cin_v1 phantom-FSM
defect: ssot-gen authored fsm states IDLE/ACCEPT/EXEC_FEATURE_1/.../ERROR,
function_model.state_variables [state, error, fm2_observed], and a transaction
carrying state_updates [fm2_observed] into a purely combinational adder. The
downstream FL semantic gate blocked it, but verify_ssot passed it, so the LLM
repair loop regenerated the same FSM forever. These tests prove verify_ssot now
fails FIRST, at the authoring stage, with no false positives.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFY_SSOT_SCRIPT = ROOT / "workflow" / "ssot-gen" / "scripts" / "verify_ssot.py"


# --------------------------------------------------------------------------- #
# Fixture builders
# --------------------------------------------------------------------------- #
def _write_locked_req_bundle(req_dir: Path, ip: str, *, sequential: bool) -> None:
    """Write a minimal locked req/ bundle.

    sequential=False -> a single combinational behavioral contract (no clock /
    cycle / reset / handshake / state vocabulary in its decision table), which
    _cycle_model_waived derives as waived.

    sequential=True -> a behavioral contract whose decision table uses clocked
    vocabulary, so _cycle_model_waived is False and the combinational gate must
    NOT fire.
    """
    req_dir.mkdir(parents=True, exist_ok=True)
    (req_dir / "approval_manifest.json").write_text(
        json.dumps(
            {
                "type": "locked_truth_approval_manifest",
                "ip": ip,
                "status": "requirements_locked",
                "bundle_sha256": "abc123",
                "requirements": [
                    {"requirement_id": "REQ_A", "required": True, "status": "locked"},
                ],
            }
        ),
        encoding="utf-8",
    )
    (req_dir / "requirements_index.json").write_text(
        json.dumps(
            {
                "ip": ip,
                "requirements": [
                    {"requirement_id": "REQ_A", "required": True, "status": "locked"},
                ],
            }
        ),
        encoding="utf-8",
    )
    (req_dir / "obligations.json").write_text(
        json.dumps(
            {
                "ip": ip,
                "obligations": [
                    {"obligation_id": "OBL_A", "requirement_refs": ["REQ_A"]},
                ],
            }
        ),
        encoding="utf-8",
    )
    (req_dir / "contract_refs.json").write_text(
        json.dumps(
            {
                "ip": ip,
                "contract_refs": [
                    {"contract_ref_id": "C_A", "obligation_refs": ["OBL_A"]},
                ],
            }
        ),
        encoding="utf-8",
    )
    (req_dir / "structural_contracts.json").write_text(
        json.dumps(
            {
                "ip": ip,
                "contracts": [
                    {
                        "id": "C_STRUCT_A",
                        "obligations": ["OBL_A"],
                        "signals": [{"name": "a", "dir": "input", "width": 8}],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    if sequential:
        decision_table = [
            {"when": "en == 1", "then": {"count": "count + 1 on next clock cycle"}},
            {"when": "en == 0", "then": {"count": "hold previous count"}},
        ]
    else:
        decision_table = [
            {"when": "cin == 0", "then": {"sum": "a + b", "cout": "carry(a + b)"}},
            {"when": "cin == 1", "then": {"sum": "a + b + 1", "cout": "carry(a + b + 1)"}},
        ]
    (req_dir / "behavioral_contracts.json").write_text(
        json.dumps(
            {
                "ip": ip,
                "contracts": [
                    {
                        "id": "BC_A",
                        "obligations": ["OBL_A"],
                        "decision_table": decision_table,
                        "stage_contracts": [
                            {"stage": "ssot", "check": "function_model mirrors BC_A"},
                        ],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )


# The SSOT body without any FSM / state — purely combinational. Combinational
# adder transaction projects BC_A via decision_table when/then + output_rules.
_CLEAN_FUNCTION_BLOCK = """function_model:
  transactions:
    - id: FM_ADD
      name: add
      description: combinational add
      decision_table:
        rows:
          - when: cin == 0
            then: { sum: a + b, cout: carry(a + b) }
          - when: cin == 1
            then: { sum: a + b + 1, cout: carry(a + b + 1) }
      output_rules:
        - { name: sum, port: sum, expr: a + b + cin, width: 8 }
      contract_refs:
        behavioral: [BC_A]"""

# The SSOT body WITH the add8_cin_v1 phantom FSM + architectural state.
_PHANTOM_FSM_FUNCTION_BLOCK = """function_model:
  state_variables:
    - { name: state }
    - { name: error }
    - { name: fm2_observed }
  transactions:
    - id: FM_ADD
      name: add
      description: combinational add
      decision_table:
        rows:
          - when: cin == 0
            then: { sum: a + b, cout: carry(a + b) }
          - when: cin == 1
            then: { sum: a + b + 1, cout: carry(a + b + 1) }
      output_rules:
        - { name: sum, port: sum, expr: a + b + cin, width: 8 }
      state_updates:
        - { name: fm2_observed }
      contract_refs:
        behavioral: [BC_A]
fsm:
  control:
    states: [IDLE, ACCEPT, EXEC_FEATURE_1, EXEC_FEATURE_2, COMPLETE, ERROR]
    transitions:
      - from: IDLE
        to: ACCEPT
        when: start == 1"""


def _write_ssot(ssot_path: Path, ip: str, function_block: str) -> None:
    ssot_path.parent.mkdir(parents=True, exist_ok=True)
    ssot_path.write_text(
        f"""
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
{function_block}
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
""".strip()
        + "\n",
        encoding="utf-8",
    )


def _run_verify(ip: str, root: Path, run_mode: str = "signoff") -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    # signoff keeps every blocker hard (the relaxed/guardrail demotion only
    # applies when ATLAS_RUN_MODE != signoff), so the gate's exit code and the
    # blockers list are deterministic regardless of run-mode defaults.
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
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=30,
        env=env,
    )


def _blockers(root: Path, ip: str) -> list[dict[str, str]]:
    report = json.loads((root / ip / "req" / "ssot_validation.json").read_text(encoding="utf-8"))
    return report.get("blockers") or []


# --------------------------------------------------------------------------- #
# 1. Combinational locked truth + phantom FSM SSOT -> FAIL on all three paths
# --------------------------------------------------------------------------- #
def test_combinational_contracts_reject_phantom_fsm_and_state(tmp_path):
    ip = "add8_cin_phantom"
    _write_locked_req_bundle(tmp_path / ip / "req", ip, sequential=False)
    _write_ssot(tmp_path / ip / "yaml" / f"{ip}.ssot.yaml", ip, _PHANTOM_FSM_FUNCTION_BLOCK)

    result = _run_verify(ip, tmp_path)

    assert result.returncode != 0, result.stdout
    blockers = _blockers(tmp_path, ip)
    ids = {item.get("id") for item in blockers}
    assert "ssot.combinational_ip_declares_fsm" in ids
    assert "ssot.combinational_ip_declares_state_variables" in ids
    assert "ssot.combinational_ip_declares_state_updates" in ids

    by_id = {item["id"]: item for item in blockers if item.get("id") in ids}
    # (a) names the offending paths/values
    fsm_msg = by_id["ssot.combinational_ip_declares_fsm"]["message"]
    assert "fsm.control.states" in by_id["ssot.combinational_ip_declares_fsm"]["path"]
    assert "EXEC_FEATURE_1" in fsm_msg
    sv = by_id["ssot.combinational_ip_declares_state_variables"]
    assert "function_model.state_variables" in sv["path"]
    assert "fm2_observed" in sv["message"]
    su = by_id["ssot.combinational_ip_declares_state_updates"]
    assert "state_updates" in su["path"]
    assert "fm2_observed" in su["message"]
    # (b) states the reason
    assert "combinational" in fsm_msg
    assert "cycle_model_waiver" in fsm_msg
    # (c) gives the remediation
    assert "Remove" in sv["fix"] and "state_updates" in sv["fix"]


# --------------------------------------------------------------------------- #
# 2. Combinational locked truth + clean combinational SSOT -> no new-check issue
# --------------------------------------------------------------------------- #
def test_combinational_contracts_pass_clean_combinational_ssot(tmp_path):
    ip = "add8_cin_clean"
    _write_locked_req_bundle(tmp_path / ip / "req", ip, sequential=False)
    _write_ssot(tmp_path / ip / "yaml" / f"{ip}.ssot.yaml", ip, _CLEAN_FUNCTION_BLOCK)

    _run_verify(ip, tmp_path)

    ids = {item.get("id") for item in _blockers(tmp_path, ip)}
    assert "ssot.combinational_ip_declares_fsm" not in ids
    assert "ssot.combinational_ip_declares_state_variables" not in ids
    assert "ssot.combinational_ip_declares_state_updates" not in ids


# --------------------------------------------------------------------------- #
# 3. Sequential (non-waived) locked truth + FSM SSOT -> no false positive
# --------------------------------------------------------------------------- #
def test_sequential_contracts_allow_fsm_no_false_positive(tmp_path):
    ip = "counter_seq"
    _write_locked_req_bundle(tmp_path / ip / "req", ip, sequential=True)
    _write_ssot(tmp_path / ip / "yaml" / f"{ip}.ssot.yaml", ip, _PHANTOM_FSM_FUNCTION_BLOCK)

    _run_verify(ip, tmp_path)

    ids = {item.get("id") for item in _blockers(tmp_path, ip)}
    assert "ssot.combinational_ip_declares_fsm" not in ids
    assert "ssot.combinational_ip_declares_state_variables" not in ids
    assert "ssot.combinational_ip_declares_state_updates" not in ids


# --------------------------------------------------------------------------- #
# 4. No locked behavioral_contracts.json present -> no new-check issue
# --------------------------------------------------------------------------- #
def test_no_locked_contracts_no_combinational_check(tmp_path):
    ip = "no_lock_ip"
    ssot_path = tmp_path / ip / "yaml" / f"{ip}.ssot.yaml"
    _write_ssot(ssot_path, ip, _PHANTOM_FSM_FUNCTION_BLOCK)
    # No req/ bundle at all -> locked-truth gate is inactive.

    _run_verify(ip, tmp_path)

    ids = {item.get("id") for item in _blockers(tmp_path, ip)}
    assert "ssot.combinational_ip_declares_fsm" not in ids
    assert "ssot.combinational_ip_declares_state_variables" not in ids
    assert "ssot.combinational_ip_declares_state_updates" not in ids


# --------------------------------------------------------------------------- #
# 5. Relaxed (engineering) run mode must NOT demote the combinational gate:
#    the build-first guardrail demotion bounced the live add8_cin_v1 repair
#    loop forever (verify_ssot ok=true kept the phantom FSM while the hard
#    downstream FL semantic gate kept failing). These codes stay blockers in
#    every run mode.
# --------------------------------------------------------------------------- #
def test_relaxed_mode_keeps_combinational_gate_hard(tmp_path):
    ip = "add8_cin_relaxed"
    _write_locked_req_bundle(tmp_path / ip / "req", ip, sequential=False)
    _write_ssot(tmp_path / ip / "yaml" / f"{ip}.ssot.yaml", ip, _PHANTOM_FSM_FUNCTION_BLOCK)

    result = _run_verify(ip, tmp_path, run_mode="engineering")

    assert result.returncode != 0, result.stdout
    report = json.loads((tmp_path / ip / "req" / "ssot_validation.json").read_text(encoding="utf-8"))
    assert report.get("run_mode_relaxed") is True
    assert report.get("ok") is False
    ids = {item.get("id") for item in (report.get("blockers") or [])}
    assert "ssot.combinational_ip_declares_fsm" in ids
    assert "ssot.combinational_ip_declares_state_variables" in ids
    assert "ssot.combinational_ip_declares_state_updates" in ids
    demoted = {item.get("id") for item in (report.get("guardrails") or [])}
    assert "ssot.combinational_ip_declares_fsm" not in demoted


# --------------------------------------------------------------------------- #
# 6. Fictional TIMING on a combinational IP (the live add8 cycle_model defect):
#    handshake_rules + min_cycles>=1 latency must hard-fail like the FSM did,
#    in relaxed mode too.
# --------------------------------------------------------------------------- #
_FICTIONAL_TIMING_BLOCK = _CLEAN_FUNCTION_BLOCK + """
cycle_model:
  clock: clk
  handshake_rules:
    - { signal: valid/ready, rule: payload stable until ready }
  latency:
    primary_operation: { min_cycles: 1, max_cycles: null }
    response: { min_cycles: 0 }"""


def test_combinational_contracts_reject_fictional_cycle_model_timing(tmp_path):
    ip = "add8_cin_timing"
    _write_locked_req_bundle(tmp_path / ip / "req", ip, sequential=False)
    _write_ssot(tmp_path / ip / "yaml" / f"{ip}.ssot.yaml", ip, _FICTIONAL_TIMING_BLOCK)

    result = _run_verify(ip, tmp_path, run_mode="engineering")

    assert result.returncode != 0, result.stdout
    report = json.loads((tmp_path / ip / "req" / "ssot_validation.json").read_text(encoding="utf-8"))
    assert report.get("ok") is False
    ids = {item.get("id") for item in (report.get("blockers") or [])}
    assert "ssot.combinational_ip_declares_handshake" in ids
    assert "ssot.combinational_ip_declares_clocked_latency" in ids
    by_id = {item["id"]: item for item in (report.get("blockers") or [])}
    lat = by_id["ssot.combinational_ip_declares_clocked_latency"]
    assert "primary_operation" in lat["path"]
    # min_cycles: 0 lanes must not be flagged
    assert not any("latency.response" in str(item.get("path")) for item in report.get("blockers") or [])
