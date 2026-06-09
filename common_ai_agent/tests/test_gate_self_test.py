"""
Meta-gate: a gate is not trusted until it proves it can REJECT bad input.

This is the workflow-level fix for the recurring silent-PASS failure mode. A
"gate" (a check/closure command in STAGE_MANIFEST, or an engine-internal content
gate) is only meaningful if a deliberately-degraded input makes it fail. Per-gate
predicate fixes (the A-series) close individual holes; this file closes the
*process* hole that let hollow gates ship in the first place:

  1. enumerate every gate-like command in STAGE_MANIFEST,
  2. RATCHET — require each to be acknowledged in the registry (covered,
     uncovered-backlog, or advisory); a NEW gate that ships unregistered fails,
  3. run the self-test (good fixture + mutation battery -> assert kill-all) for
     every COVERED gate,
  4. keep the UNCOVERED backlog explicit and FROZEN, so it can only shrink by a
     reviewed change, never grow silently.

To retire backlog: write a GateSelfTest for the gate, move it from UNCOVERED_GATES
into COVERED_GATES, and update the frozen set. Goal state: UNCOVERED_GATES == {}.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

from tests.test_atlas_to_ssot_locked_truth import _write_locked_contract_bundle
from tests.test_derive_tb_todos import (
    _GOOD_COVERAGE,
    _GOOD_EVENT,
    _mut_comment_only_scoreboard,
    _mut_empty_tb_bodies,
    _run,
    _write_evidence,
    _write_ip,
    _write_tb_artifacts,
)
from tests.contract_reflection_helpers import (
    CONTRACT_CHECK_SCRIPT as _CR_GATE,
    make_contract_ip as _cr_make_ip,
    read_json as _cr_read_json,
    write_json as _cr_write_json,
    write_rows as _cr_write_rows,
)
from tests.test_derive_rtl_todos import _load_derive as _rtlf_load_derive, _write_behavioral_contract as _rtlf_write_bc
from tests.test_ip_signoff_gate import _make_ip as _signoff_make_ip
from tests.test_truth_coverage_gate import _write_direct_ssot_ip as _tc_write_good
from tests.test_workflow_stage_engine import _clear_obligation_authority_refs

REPO = Path(__file__).resolve().parents[1]
MANIFEST = REPO / "workflow" / "STAGE_MANIFEST.json"


# ---------------------------------------------------------------------------
# Reusable harness: the known-good fixture must pass; each mutation must NOT.
# ---------------------------------------------------------------------------

class GateSelfTest:
    """A gate's defining proof: it passes a known-good fixture and rejects every
    deliberate degradation of the property it claims to enforce."""

    def __init__(self, *, build_good, run_gate, read_status, mutations):
        self.build_good = build_good    # (work_dir) -> ctx
        self.run_gate = run_gate        # (work_dir, ctx) -> None (invokes the gate)
        self.read_status = read_status  # (work_dir, ctx) -> str  (the gate verdict)
        self.mutations = mutations      # list[(name, mutate(work_dir, ctx))]

    def assert_kills_all(self, tmp_path_factory, gate_id: str) -> None:
        good = tmp_path_factory.mktemp(f"{gate_id}__good")
        ctx = self.build_good(good)
        self.run_gate(good, ctx)
        assert self.read_status(good, ctx) == "pass", (
            f"{gate_id}: known-good fixture must pass, gate is broken the other way"
        )
        for name, mutate in self.mutations:
            work = tmp_path_factory.mktemp(f"{gate_id}__{name}")
            ctx = self.build_good(work)
            mutate(work, ctx)
            self.run_gate(work, ctx)
            assert self.read_status(work, ctx) != "pass", (
                f"{gate_id}: SILENT-PASS on mutation `{name}` — gate does not enforce its contract"
            )


# ---------------------------------------------------------------------------
# tb contract-ledger gate self-test (reuses the A0 fixtures/mutations)
# ---------------------------------------------------------------------------

_TB_IP = "gate_tb"


def _tb_build_good(work: Path) -> str:
    ip_dir = _write_ip(work, _TB_IP)
    _write_tb_artifacts(ip_dir, _TB_IP)
    _write_evidence(ip_dir, event=_GOOD_EVENT, coverage=_GOOD_COVERAGE)
    return _TB_IP


def _tb_run_gate(work: Path, ip: str) -> None:
    _run(work, ip, "--audit-tb")
    _run(work, ip, "--audit-evidence")


def _tb_read_status(work: Path, ip: str) -> str:
    plan = json.loads((work / ip / "tb" / "tb_todo_plan.json").read_text(encoding="utf-8"))
    return plan["gate"]["status"]


def _tb_mut_vacuous_row(work: Path, ip: str) -> None:
    _write_evidence(
        work / ip,
        event={
            "goal_id": "EQ_READ", "scenario_id": "", "stimulus": {},
            "fl_expected": {}, "rtl_observed": {}, "passed": True, "coverage_refs": [],
        },
        coverage=_GOOD_COVERAGE,
    )


def _tb_mut_coverage_without_status(work: Path, ip: str) -> None:
    _write_evidence(work / ip, event=_GOOD_EVENT, coverage={"note": "no status field"})


TB_CONTRACT_LEDGER_SELF_TEST = GateSelfTest(
    build_good=_tb_build_good,
    run_gate=_tb_run_gate,
    read_status=_tb_read_status,
    mutations=[
        ("comment_only_scoreboard", lambda w, ip: _mut_comment_only_scoreboard(w / ip, ip)),
        ("empty_tb_bodies", lambda w, ip: _mut_empty_tb_bodies(w / ip, ip)),
        ("vacuous_scoreboard_row", _tb_mut_vacuous_row),
        ("coverage_without_status", _tb_mut_coverage_without_status),
    ],
)


# ---------------------------------------------------------------------------
# req contract-authority gate self-test (check_contract_bundle.py)
# ---------------------------------------------------------------------------

_REQ_IP = "gate_req"
_REQ_GATE = REPO / "workflow" / "req-gen" / "scripts" / "check_contract_bundle.py"


def _req_build_good(work: Path) -> dict:
    # Writes + locks a full valid contract bundle under work/<ip>/req/.
    _write_locked_contract_bundle(work, _REQ_IP)
    return {"ip": _REQ_IP}


def _req_run_gate(work: Path, ctx: dict) -> None:
    proc = subprocess.run(
        [sys.executable, str(_REQ_GATE), ctx["ip"], "--root", str(work)],
        capture_output=True, text=True, check=False,
    )
    ctx["rc"] = proc.returncode
    ctx["out"] = proc.stdout + proc.stderr


def _req_read_status(work: Path, ctx: dict) -> str:
    return "pass" if ctx.get("rc") == 0 else "fail"


def _req_mut_anchor_only(work: Path, ctx: dict) -> None:
    # Content authority: obligation with no structural/behavioral contract refs
    # (manifest hash refreshed so it fails on the anchor-ref check, not the hash).
    _clear_obligation_authority_refs(work / ctx["ip"] / "req")


def _req_mut_tamper_without_rehash(work: Path, ctx: dict) -> None:
    # Lock integrity: edit a hashed req-graph file but do NOT refresh the manifest
    # hash — the gate must reject the tampered locked bundle.
    obl_path = work / ctx["ip"] / "req" / "obligations.json"
    obl = json.loads(obl_path.read_text(encoding="utf-8"))
    obl["_tamper"] = "edited after lock; manifest hash intentionally not refreshed"
    obl_path.write_text(json.dumps(obl, indent=2, sort_keys=True) + "\n", encoding="utf-8")


REQ_CONTRACT_AUTHORITY_SELF_TEST = GateSelfTest(
    build_good=_req_build_good,
    run_gate=_req_run_gate,
    read_status=_req_read_status,
    mutations=[
        ("anchor_only_obligation", _req_mut_anchor_only),
        ("tamper_without_rehash", _req_mut_tamper_without_rehash),
    ],
)


# ---------------------------------------------------------------------------
# scoreboard schema/observable gate self-test (check_scoreboard_events.py)
# ---------------------------------------------------------------------------

_SB_IP = "gate_sb"
_SB_GATE = REPO / "workflow" / "tb-gen" / "scripts" / "check_scoreboard_events.py"

_SB_GOOD_ROW = {
    "goal_id": "EQ_DATA",
    "scenario_id": "SC_DATA",
    "cycle": 1,
    "stimulus": {"kind": "READ"},
    "fl_expected": {"model_api": "FunctionalModel.apply", "model_result": {"data_o": 3}},
    "rtl_observed": {"data_o": 3},
    "passed": True,
    "mismatch": "",
    "coverage_refs": ["SC_DATA_executed"],
}


def _sb_write_events(ip_dir: Path, rows: list) -> None:
    path = ip_dir / "sim" / "scoreboard_events.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


def _sb_build_good(work: Path) -> dict:
    ip_dir = work / _SB_IP
    (ip_dir / "verify").mkdir(parents=True, exist_ok=True)
    (ip_dir / "verify" / "equivalence_goals.json").write_text(
        json.dumps({"goals": [{"goal_id": "EQ_DATA"}]}), encoding="utf-8"
    )
    _sb_write_events(ip_dir, [dict(_SB_GOOD_ROW)])
    sb = ip_dir / "tb" / "cocotb" / "scoreboard.py"
    sb.parent.mkdir(parents=True, exist_ok=True)
    sb.write_text(
        "from equivalence_scoreboard import EquivalenceScoreboard\nsb = EquivalenceScoreboard()\n",
        encoding="utf-8",
    )
    return {"ip": _SB_IP}


def _sb_run_gate(work: Path, ctx: dict) -> None:
    proc = subprocess.run(
        [sys.executable, str(_SB_GATE), ctx["ip"], "--root", str(work), "--source-check", "--require-events"],
        capture_output=True, text=True, check=False,
    )
    ctx["rc"] = proc.returncode
    ctx["out"] = proc.stdout + proc.stderr


def _sb_read_status(work: Path, ctx: dict) -> str:
    return "pass" if ctx.get("rc") == 0 else "fail"


def _sb_mut_empty_events(work: Path, ctx: dict) -> None:
    _sb_write_events(work / ctx["ip"], [])  # --require-events must reject 0 rows


def _sb_mut_vacuous_observed(work: Path, ctx: dict) -> None:
    row = dict(_SB_GOOD_ROW)
    row["rtl_observed"] = {}  # empty observed = no real DUT evidence
    _sb_write_events(work / ctx["ip"], [row])


def _sb_mut_observed_copies_fl(work: Path, ctx: dict) -> None:
    row = dict(_SB_GOOD_ROW)
    row["rtl_observed"] = dict(row["fl_expected"])  # FL-copy cheat (observed == expected)
    _sb_write_events(work / ctx["ip"], [row])


def _sb_mut_fl_not_from_model(work: Path, ctx: dict) -> None:
    row = dict(_SB_GOOD_ROW)
    row["fl_expected"] = {"model_result": {"data_o": 3}}  # missing model_api authenticity
    _sb_write_events(work / ctx["ip"], [row])


SCOREBOARD_EVENTS_SELF_TEST = GateSelfTest(
    build_good=_sb_build_good,
    run_gate=_sb_run_gate,
    read_status=_sb_read_status,
    mutations=[
        ("empty_events", _sb_mut_empty_events),
        ("vacuous_rtl_observed", _sb_mut_vacuous_observed),
        ("rtl_observed_copies_fl", _sb_mut_observed_copies_fl),
        ("fl_expected_not_from_model", _sb_mut_fl_not_from_model),
    ],
)


# ---------------------------------------------------------------------------
# final signoff gate self-test (check_ip_signoff.py)
# ---------------------------------------------------------------------------

_SIGNOFF_IP = "gate_signoff"
_SIGNOFF_GATE = REPO / "workflow" / "signoff" / "scripts" / "check_ip_signoff.py"


def _signoff_build_good(work: Path) -> dict:
    # Complete local-evidence fixture that passes every signoff gate.
    _signoff_make_ip(work, _SIGNOFF_IP)
    return {"ip": _SIGNOFF_IP}


def _signoff_run_gate(work: Path, ctx: dict) -> None:
    proc = subprocess.run(
        [sys.executable, str(_SIGNOFF_GATE), ctx["ip"], "--root", str(work)],
        capture_output=True, text=True, check=False,
    )
    ctx["rc"] = proc.returncode
    ctx["out"] = proc.stdout + proc.stderr


def _signoff_read_status(work: Path, ctx: dict) -> str:
    return "pass" if ctx.get("rc") == 0 else "fail"


def _signoff_mut_missing_ip_contract(work: Path, ctx: dict) -> None:
    (work / ctx["ip"] / "verify" / "ip_contract.json").unlink()


def _signoff_mut_missing_truth_coverage(work: Path, ctx: dict) -> None:
    (work / ctx["ip"] / "signoff" / "truth_coverage.json").unlink()


def _signoff_mut_stale_rtl_provenance(work: Path, ctx: dict) -> None:
    # _make_ip is not idempotent (mkdir w/o exist_ok), so clear then rebuild bad.
    shutil.rmtree(work / ctx["ip"])
    _signoff_make_ip(work, ctx["ip"], bad_provenance=True)  # stale todo_plan_sha256


def _signoff_mut_missing_observable(work: Path, ctx: dict) -> None:
    shutil.rmtree(work / ctx["ip"])
    _signoff_make_ip(work, ctx["ip"], missing_observable=True)  # scoreboard omits an expected observable


IP_SIGNOFF_SELF_TEST = GateSelfTest(
    build_good=_signoff_build_good,
    run_gate=_signoff_run_gate,
    read_status=_signoff_read_status,
    mutations=[
        ("missing_ip_contract", _signoff_mut_missing_ip_contract),
        ("missing_truth_coverage", _signoff_mut_missing_truth_coverage),
        ("stale_rtl_provenance", _signoff_mut_stale_rtl_provenance),
        ("missing_observable", _signoff_mut_missing_observable),
    ],
)


# ---------------------------------------------------------------------------
# truth-coverage gate self-test (check_truth_coverage.py)  [FIXED 2026-06-09]
# fabricated coverage.json with no sim must NOT cover obligations.
# ---------------------------------------------------------------------------

_TC_IP = "direct_truth_ip"
_TC_GATE = REPO / "workflow" / "reqcov" / "scripts" / "check_truth_coverage.py"


def _tc_build_good(work: Path) -> dict:
    _tc_write_good(work, _TC_IP)  # mkdir w/o exist_ok -> call on a fresh work root
    return {"ip": _TC_IP, "ip_dir": work / _TC_IP}


def _tc_run_gate(work: Path, ctx: dict) -> None:
    proc = subprocess.run(
        [sys.executable, str(_TC_GATE), ctx["ip"], "--root", str(work)],
        capture_output=True, text=True, check=False,
    )
    ctx["rc"] = proc.returncode


def _tc_read_status(work: Path, ctx: dict) -> str:
    return "pass" if ctx.get("rc") == 0 else "fail"


def _tc_mut_fabricated_coverage(work: Path, ctx: dict) -> None:
    # Delete real sim evidence, hand-write coverage.json with obligation-named hit:true
    # bins. A genuine gate must reject this (no sim ran).
    shutil.rmtree(ctx["ip_dir"] / "sim")
    fab = {"function_coverage": {"bins": {
        tok: {"hit": True} for tok in (
            "FM_ACCEPT", "ERR_BAD_PACKET", "CTRL", "IRQ_DONE", "SC_ACCEPT",
            "FCOV_ACCEPT", "FCOV_BAD_PACKET")}}}
    (ctx["ip_dir"] / "cov" / "coverage.json").write_text(json.dumps(fab), encoding="utf-8")


def _tc_mut_blank_scoreboard(work: Path, ctx: dict) -> None:
    (ctx["ip_dir"] / "sim" / "scoreboard_events.jsonl").unlink()


def _tc_mut_scoreboard_status_fail(work: Path, ctx: dict) -> None:
    p = ctx["ip_dir"] / "sim" / "scoreboard_events.jsonl"
    rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    for r in rows:
        r["passed"] = False
    p.write_text("\n".join(json.dumps(r, sort_keys=True) for r in rows) + "\n", encoding="utf-8")


TRUTH_COVERAGE_SELF_TEST = GateSelfTest(
    build_good=_tc_build_good,
    run_gate=_tc_run_gate,
    read_status=_tc_read_status,
    mutations=[
        ("fabricated_coverage_no_sim", _tc_mut_fabricated_coverage),
        ("blank_scoreboard", _tc_mut_blank_scoreboard),
        ("scoreboard_status_fail", _tc_mut_scoreboard_status_fail),
    ],
)


# ---------------------------------------------------------------------------
# contract-reflection closure gate self-test (run_contract_check.py, default mode)
# [FIXED 2026-06-09] vacuous closure (0 obligations) must NOT pass.
# ---------------------------------------------------------------------------

_CR_IP = "contract_ip"  # make_contract_ip hardcodes this dir name


def _cr_write_stage_artifacts(ip_dir: Path) -> None:
    for rel in (
        "yaml/contract_ip.ssot.yaml", "model/functional_model.py",
        "model/cycle_model.py", "rtl/contract_ip.sv", "tb/cocotb/test_contract_ip.py",
    ):
        p = ip_dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("// marker\n" if rel.endswith(".sv") else "# marker\n", encoding="utf-8")
    (ip_dir / "sim" / "contract_ip.vcd").write_text(
        "$var wire 13 ! payload_byte_count [12:0] $end\n"
        "$var wire 17 @ sram_wr_strb [16:0] $end\n"
        "#0\nb10001 !\nb11111111111111111 @\n",
        encoding="utf-8",
    )
    _cr_write_json(ip_dir / "verify" / "contract_reflection.json", {
        "contract_refs": [{
            "contract_ref": "STATE_PAYLOAD_COUNT",
            "fl": {"path": "model/functional_model.py"},
            "cl": {"path": "model/cycle_model.py"},
            "rtl": {"owner_files": ["rtl/contract_ip.sv"], "observable_via": ["payload_byte_count"]},
            "sim": {"scoreboard": "sim/scoreboard_events.jsonl", "wave": "sim/contract_ip.vcd"},
            "ssot": {"path": "yaml/contract_ip.ssot.yaml"},
            "tb": {"path": "tb/cocotb/test_contract_ip.py", "monitor": "payload_monitor"},
        }],
        "schema_version": 1, "type": "contract_reflection",
    })


def _cr_build_good(work: Path) -> dict:
    ip_dir = _cr_make_ip(work)
    _cr_write_stage_artifacts(ip_dir)
    return {"ip": _CR_IP, "ip_dir": ip_dir}


def _cr_run_gate(work: Path, ctx: dict) -> None:
    proc = subprocess.run(
        [sys.executable, str(_CR_GATE), ctx["ip"], "--root", str(work)],  # DEFAULT mode
        capture_output=True, text=True, check=False,
    )
    ctx["rc"] = proc.returncode


def _cr_read_status(work: Path, ctx: dict) -> str:
    return "pass" if ctx.get("rc") == 0 else "fail"


def _cr_mut_blank_scoreboard(work: Path, ctx: dict) -> None:
    (ctx["ip_dir"] / "sim" / "scoreboard_events.jsonl").write_text("", encoding="utf-8")


def _cr_mut_wrong_observed_value(work: Path, ctx: dict) -> None:
    _cr_write_rows(ctx["ip_dir"] / "sim" / "scoreboard_events.jsonl", [
        {"goal_id": "EQ_PAYLOAD", "scenario_id": "SC_PAYLOAD", "passed": True,
         "rtl_observed": {"payload_byte_count": 999, "sram_wr_strb": 0x1FFFF}}])


def _cr_mut_row_not_passed(work: Path, ctx: dict) -> None:
    _cr_write_rows(ctx["ip_dir"] / "sim" / "scoreboard_events.jsonl", [
        {"goal_id": "EQ_PAYLOAD", "scenario_id": "SC_PAYLOAD", "passed": False,
         "rtl_observed": {"payload_byte_count": 17, "sram_wr_strb": 0x1FFFF}}])


def _cr_mut_break_ref_evidence_link(work: Path, ctx: dict) -> None:
    refl = _cr_read_json(ctx["ip_dir"] / "verify" / "contract_reflection.json")
    refl["contract_refs"][0]["fl"]["path"] = "model/does_not_exist.py"
    _cr_write_json(ctx["ip_dir"] / "verify" / "contract_reflection.json", refl)


def _cr_mut_vacuous_zero_obligations(work: Path, ctx: dict) -> None:
    # [FIX target] strip all required obligations/refs — must NOT close as pass.
    ip_dir = ctx["ip_dir"]
    _cr_write_json(ip_dir / "verify" / "requirements_index.json",
                   {"requirements": [], "schema_version": 1, "type": "requirements_index"})
    _cr_write_json(ip_dir / "verify" / "evidence_contract.json",
                   {"obligations": [], "schema_version": 1, "type": "evidence_contract"})
    _cr_write_json(ip_dir / "verify" / "contract_reflection.json",
                   {"contract_refs": [], "schema_version": 1, "type": "contract_reflection"})


CONTRACT_REFLECTION_SELF_TEST = GateSelfTest(
    build_good=_cr_build_good,
    run_gate=_cr_run_gate,
    read_status=_cr_read_status,
    mutations=[
        ("blank_scoreboard_evidence", _cr_mut_blank_scoreboard),
        ("wrong_observed_value", _cr_mut_wrong_observed_value),
        ("scoreboard_row_not_passed", _cr_mut_row_not_passed),
        ("break_contract_ref_to_evidence_link", _cr_mut_break_ref_evidence_link),
        ("vacuous_zero_obligations", _cr_mut_vacuous_zero_obligations),
    ],
)


# ---------------------------------------------------------------------------
# SSOT functional coverage summary gate self-test (ssot_coverage_summary.py)
# Signals pass/fail via the produced cov/coverage.json status (rc agrees).
# ---------------------------------------------------------------------------

_COV_GATE = REPO / "workflow" / "coverage" / "scripts" / "ssot_coverage_summary.py"


def _cov_build_good(work: Path) -> dict:
    ip = work / "counter_ip"
    for sub in ("yaml", "cov", "verify", "sim"):
        (ip / sub).mkdir(parents=True, exist_ok=True)
    (ip / "yaml" / "counter_ip.ssot.yaml").write_text(
        "top_module:\n  name: counter_ip\n"
        "test_requirements:\n"
        "  scenarios:\n    - id: SC_COUNT\n      name: count\n      checker: FL-vs-RTL scoreboard\n"
        "  coverage_goals:\n"
        "    function:\n      target_pct: 100\n      bins:\n        - id: FCOV_COUNT\n          coverage_domain: function\n"
        "    cycle:\n      target_pct: 100\n      bins:\n        - id: CCOV_COUNT\n          coverage_domain: cycle\n"
        "    code: line >= 95%, branch >= 95%\n",
        encoding="utf-8",
    )
    (ip / "cov" / "fcov_plan.json").write_text(json.dumps(
        {"bins": [{"id": "FCOV_COUNT", "coverage_domain": "function"},
                  {"id": "CCOV_COUNT", "coverage_domain": "cycle"}]}), encoding="utf-8")
    (ip / "cov" / "coverage_functional.json").write_text(json.dumps(
        {"status": "pass", "functional": {"bins": {"FCOV_COUNT": {"hit": True}, "CCOV_COUNT": {"hit": True}}}}),
        encoding="utf-8")
    (ip / "verify" / "equivalence_goals.json").write_text(json.dumps(
        {"goals": [{"goal_id": "EQ_COUNT", "coverage_refs": ["FCOV_COUNT", "CCOV_COUNT"]}]}), encoding="utf-8")
    (ip / "sim" / "scoreboard_events.jsonl").write_text(json.dumps(
        {"goal_id": "EQ_COUNT", "scenario_id": "SC_COUNT", "coverage_refs": ["FCOV_COUNT", "CCOV_COUNT"],
         "passed": True, "fl_expected": {"model_result": {"count": 1}}, "rtl_observed": {"count": 1}}) + "\n",
        encoding="utf-8")
    return {"ip": ip}


def _cov_run_gate(work: Path, ctx: dict) -> None:
    proc = subprocess.run(
        [sys.executable, str(_COV_GATE), str(ctx["ip"]), "--root", str(ctx["ip"].parent)],
        capture_output=True, text=True, check=False,
    )
    ctx["rc"] = proc.returncode


def _cov_read_status(work: Path, ctx: dict) -> str:
    cov = ctx["ip"] / "cov" / "coverage.json"
    if not cov.is_file():
        return "fail"
    return "pass" if json.loads(cov.read_text(encoding="utf-8")).get("status") == "pass" else "fail"


def _cov_write_events(ctx: dict, rows: list) -> None:
    (ctx["ip"] / "sim" / "scoreboard_events.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def _cov_mut_empty_scoreboard(work: Path, ctx: dict) -> None:
    (ctx["ip"] / "sim" / "scoreboard_events.jsonl").write_text("", encoding="utf-8")


def _cov_mut_zero_required_bins(work: Path, ctx: dict) -> None:
    _cov_write_events(ctx, [{"goal_id": "EQ_COUNT", "coverage_refs": ["FCOV_UNRELATED"], "passed": True,
                             "fl_expected": {"model_result": {"count": 1}}, "rtl_observed": {"count": 1}}])


def _cov_mut_all_fail(work: Path, ctx: dict) -> None:
    _cov_write_events(ctx, [{"goal_id": "EQ_COUNT", "coverage_refs": ["FCOV_COUNT", "CCOV_COUNT"], "passed": False,
                             "fl_expected": {"model_result": {"count": 1}}, "rtl_observed": {"count": 1}}])


def _cov_mut_fl_copy_observed(work: Path, ctx: dict) -> None:
    _cov_write_events(ctx, [{"goal_id": "EQ_COUNT", "coverage_refs": ["FCOV_COUNT", "CCOV_COUNT"], "passed": True,
                             "fl_expected": {"model_result": {"count": 1}}, "rtl_observed": {"model_result": {"count": 1}}}])


def _cov_mut_uncover_one_bin(work: Path, ctx: dict) -> None:
    _cov_write_events(ctx, [{"goal_id": "EQ_COUNT", "coverage_refs": ["FCOV_COUNT"], "passed": True,
                             "fl_expected": {"model_result": {"count": 1}}, "rtl_observed": {"count": 1}}])


SSOT_COVERAGE_SUMMARY_SELF_TEST = GateSelfTest(
    build_good=_cov_build_good,
    run_gate=_cov_run_gate,
    read_status=_cov_read_status,
    mutations=[
        ("empty_scoreboard", _cov_mut_empty_scoreboard),
        ("zero_required_bins_covered", _cov_mut_zero_required_bins),
        ("all_fail_events", _cov_mut_all_fail),
        ("fl_copy_rtl_observed", _cov_mut_fl_copy_observed),
        ("uncover_one_required_bin", _cov_mut_uncover_one_bin),
    ],
)


# ---------------------------------------------------------------------------
# pre-sim TB python compile gate self-test (check_tb_python_compile.py)
# ---------------------------------------------------------------------------

_TBC_IP = "gate_tb_compile"
_TBC_GATE = REPO / "workflow" / "tb-gen" / "scripts" / "check_tb_python_compile.py"


def _tbc_build_good(work: Path) -> dict:
    tb_dir = work / _TBC_IP / "tb" / "cocotb"
    tb_dir.mkdir(parents=True)
    (tb_dir / f"test_{_TBC_IP}.py").write_text(
        "import cocotb\n\n@cocotb.test()\nasync def test_basic(dut):\n    pass\n", encoding="utf-8")
    return {"ip": _TBC_IP}


def _tbc_run_gate(work: Path, ctx: dict) -> None:
    proc = subprocess.run(
        [sys.executable, str(_TBC_GATE), ctx["ip"], "--root", str(work)],
        capture_output=True, text=True, check=False,
    )
    ctx["rc"] = proc.returncode


def _tbc_read_status(work: Path, ctx: dict) -> str:
    return "pass" if ctx.get("rc") == 0 else "fail"


def _tbc_mut_syntax_error(work: Path, ctx: dict) -> None:
    (work / ctx["ip"] / "tb" / "cocotb" / f"test_{ctx['ip']}.py").write_text("def broken(:\n    pass\n", encoding="utf-8")


def _tbc_mut_empty_dir(work: Path, ctx: dict) -> None:
    for f in (work / ctx["ip"] / "tb" / "cocotb").glob("*.py"):
        f.unlink()


def _tbc_mut_no_cocotb_dir(work: Path, ctx: dict) -> None:
    shutil.rmtree(work / ctx["ip"] / "tb" / "cocotb")


def _tbc_mut_no_ip_dir(work: Path, ctx: dict) -> None:
    shutil.rmtree(work / ctx["ip"])


TB_PYTHON_COMPILE_SELF_TEST = GateSelfTest(
    build_good=_tbc_build_good,
    run_gate=_tbc_run_gate,
    read_status=_tbc_read_status,
    mutations=[
        ("syntax_error", _tbc_mut_syntax_error),
        ("empty_cocotb_dir", _tbc_mut_empty_dir),
        ("no_cocotb_dir", _tbc_mut_no_cocotb_dir),
        ("no_ip_dir", _tbc_mut_no_ip_dir),
    ],
)


# ---------------------------------------------------------------------------
# DUT lint gate self-test (dut_lint_report.py) — requires verilator
# ---------------------------------------------------------------------------

_DUT_IP = "gate_dut_lint"
_DUT_GATE = REPO / "workflow" / "lint" / "scripts" / "dut_lint_report.py"
_DUT_GOOD_SV = (
    "module gate_dut_lint(\n"
    "    input  logic clk,\n    input  logic rst_n,\n"
    "    input  logic [7:0] data_in,\n    output logic [7:0] data_out\n);\n"
    "  logic [7:0] state_q;\n"
    "  always @(posedge clk or negedge rst_n) begin\n"
    "    if (!rst_n) state_q <= 8'h00;\n    else        state_q <= data_in;\n  end\n"
    "  assign data_out = state_q;\nendmodule\n"
)


def _dut_build_good(work: Path) -> dict:
    ip_dir = work / _DUT_IP
    (ip_dir / "rtl").mkdir(parents=True)
    (ip_dir / "list").mkdir()
    (ip_dir / "rtl" / f"{_DUT_IP}.sv").write_text(_DUT_GOOD_SV, encoding="utf-8")
    (ip_dir / "list" / f"{_DUT_IP}.f").write_text(f"rtl/{_DUT_IP}.sv\n", encoding="utf-8")
    return {"ip": _DUT_IP}


def _dut_run_gate(work: Path, ctx: dict) -> None:
    proc = subprocess.run([sys.executable, str(_DUT_GATE), ctx["ip"], "--root", str(work)],
                          capture_output=True, text=True, check=False)
    ctx["rc"] = proc.returncode


def _dut_read_status(work: Path, ctx: dict) -> str:
    rp = work / ctx["ip"] / "lint" / "dut_lint.json"
    if not rp.exists():
        return "fail"
    return "pass" if json.loads(rp.read_text(encoding="utf-8")).get("passed") else "fail"


def _dut_mut_undefined_signal(work: Path, ctx: dict) -> None:
    (work / ctx["ip"] / "rtl" / f"{ctx['ip']}.sv").write_text(
        "module gate_dut_lint(\n  input  logic clk,\n  output logic data_out\n);\n"
        "  assign data_out = undefined_signal;\nendmodule\n", encoding="utf-8")


def _dut_mut_suppression(work: Path, ctx: dict) -> None:
    sv = work / ctx["ip"] / "rtl" / f"{ctx['ip']}.sv"
    sv.write_text("/* verilator lint_off UNUSEDSIGNAL */\n" + sv.read_text(encoding="utf-8")
                  + "/* verilator lint_on UNUSEDSIGNAL */\n", encoding="utf-8")


def _dut_mut_banned_style(work: Path, ctx: dict) -> None:
    (work / ctx["ip"] / "rtl" / f"{ctx['ip']}.sv").write_text(
        "module gate_dut_lint(\n  input  logic clk,\n  input  logic [7:0] data_in,\n"
        "  output logic [7:0] data_out\n);\n  typedef enum logic [1:0] {IDLE, RUN} state_e;\n"
        "  state_e state_q;\n  always_ff @(posedge clk) begin\n    state_q <= RUN;\n  end\n"
        "  assign data_out = (state_q == RUN) ? data_in : 8'h00;\nendmodule\n", encoding="utf-8")


def _dut_mut_empty_filelist(work: Path, ctx: dict) -> None:
    (work / ctx["ip"] / "list" / f"{ctx['ip']}.f").write_text("# no sv files\n", encoding="utf-8")


DUT_LINT_SELF_TEST = GateSelfTest(
    build_good=_dut_build_good, run_gate=_dut_run_gate, read_status=_dut_read_status,
    mutations=[
        ("undefined_signal", _dut_mut_undefined_signal),
        ("suppression_comment", _dut_mut_suppression),
        ("banned_style", _dut_mut_banned_style),
        ("empty_filelist", _dut_mut_empty_filelist),
    ],
)


# ---------------------------------------------------------------------------
# DUT RTL compile gate self-test (rtl_compile_report.py) — requires iverilog
# ---------------------------------------------------------------------------

_RTLC_IP = "gate_rtl_compile"
_RTLC_GATE = REPO / "workflow" / "rtl-gen" / "scripts" / "rtl_compile_report.py"
_RTLC_GOOD_SV = (
    "module gate_rtl_compile (\n"
    "    input  logic        clk,\n    input  logic        rst_n,\n"
    "    input  logic [7:0]  data_i,\n    output logic [7:0]  data_o\n);\n"
    "    always @(posedge clk or negedge rst_n) begin\n"
    "        if (!rst_n) data_o <= 8'h00;\n        else        data_o <= data_i;\n    end\n"
    "endmodule\n"
)


def _rtlc_build_good(work: Path) -> dict:
    ip_dir = work / _RTLC_IP
    (ip_dir / "rtl").mkdir(parents=True, exist_ok=True)
    (ip_dir / "list").mkdir(parents=True, exist_ok=True)
    (ip_dir / "rtl" / f"{_RTLC_IP}.sv").write_text(_RTLC_GOOD_SV, encoding="utf-8")
    (ip_dir / "list" / f"{_RTLC_IP}.f").write_text(f"rtl/{_RTLC_IP}.sv\n", encoding="utf-8")
    return {"ip": _RTLC_IP}


def _rtlc_run_gate(work: Path, ctx: dict) -> None:
    proc = subprocess.run([sys.executable, str(_RTLC_GATE), ctx["ip"], "--root", str(work)],
                          capture_output=True, text=True, check=False)
    ctx["rc"] = proc.returncode


def _rtlc_read_status(work: Path, ctx: dict) -> str:
    return "pass" if ctx.get("rc") == 0 else "fail"


def _rtlc_mut_syntax(work: Path, ctx: dict) -> None:
    (work / ctx["ip"] / "rtl" / f"{ctx['ip']}.sv").write_text(
        f"module {ctx['ip']} (input logic clk, output logic [7:0] data_o);\n"
        "    always @(posedge clk) begin\n        data_o <= ;\n    end\nendmodule\n", encoding="utf-8")


def _rtlc_mut_empty_filelist(work: Path, ctx: dict) -> None:
    (work / ctx["ip"] / "list" / f"{ctx['ip']}.f").write_text("# empty\n", encoding="utf-8")


def _rtlc_mut_banned_style(work: Path, ctx: dict) -> None:
    (work / ctx["ip"] / "rtl" / f"{ctx['ip']}.sv").write_text(
        f"module {ctx['ip']} (\n  input  logic clk,\n  input  logic rst_n,\n"
        "  input  logic [7:0] data_i,\n  output logic [7:0] data_o\n);\n"
        "  always_ff @(posedge clk or negedge rst_n) begin\n"
        "    if (!rst_n) data_o <= 8'h00;\n    else        data_o <= data_i;\n  end\nendmodule\n",
        encoding="utf-8")


def _rtlc_mut_missing_filelist(work: Path, ctx: dict) -> None:
    (work / ctx["ip"] / "list" / f"{ctx['ip']}.f").unlink()


RTL_COMPILE_SELF_TEST = GateSelfTest(
    build_good=_rtlc_build_good, run_gate=_rtlc_run_gate, read_status=_rtlc_read_status,
    mutations=[
        ("syntax_error", _rtlc_mut_syntax),
        ("empty_filelist", _rtlc_mut_empty_filelist),
        ("banned_style_always_ff", _rtlc_mut_banned_style),
        ("missing_filelist", _rtlc_mut_missing_filelist),
    ],
)


# ---------------------------------------------------------------------------
# RTL final closure gate self-test (derive_rtl_todos.py --audit-rtl)
# NOTE: --audit-rtl is the real enforcement flag; the manifest's --enforce is an
# invalid argparse arg (rc=2, gate never runs) — a separate manifest bug to fix.
# ---------------------------------------------------------------------------

_RTLF_IP = "gate_rtl"
_RTLF_GATE = REPO / "workflow" / "rtl-gen" / "scripts" / "derive_rtl_todos.py"
_rtlf_derive = _rtlf_load_derive()


def _rtlf_top_sv(top: str) -> str:
    return (
        f"module {top}(\n  input  logic clk,\n  input  logic rst_n,\n"
        "  input  logic cmd_valid,\n  output logic cmd_ready,\n  output logic [31:0] rsp_rdata\n);\n"
        "  logic [31:0] count_q;\n  logic ready_q;\n"
        "  always @(posedge clk or negedge rst_n) begin\n"
        "    if (!rst_n) begin\n      count_q <= 32'd0;\n      ready_q <= 1'b0;\n    end else begin\n"
        "      ready_q <= ~ready_q | cmd_valid;\n"
        "      if (cmd_valid && cmd_ready) count_q <= count_q + 32'd1;\n    end\n  end\n"
        "  assign cmd_ready = ready_q | cmd_valid;\n"
        "  assign rsp_rdata = cmd_valid ? count_q : 32'd0;\nendmodule\n"
    )


def _rtlf_build_good(work: Path) -> dict:
    ip = _RTLF_IP
    ip_dir = work / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "req").mkdir(parents=True)
    top = f"{ip}_top"
    rel = f"rtl/{top}.sv"
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        f"top_module:\n  name: {top}\n"
        "io_list:\n  clock_domains:\n    - {name: clk, direction: input, width: 1}\n"
        "  resets:\n    - {name: rst_n, direction: input, width: 1}\n"
        "  interfaces:\n    - name: ctrl\n      ports:\n"
        "        - {name: cmd_valid, direction: input, width: 1}\n"
        "        - {name: cmd_ready, direction: output, width: 1}\n"
        "        - {name: rsp_rdata, direction: output, width: 32}\n"
        f"sub_modules:\n  - name: {top}\n    file: {rel}\n    refs:\n"
        "      - function_model.transactions.READ\n      - cycle_model.handshake_rules.ctrl\n"
        "function_model:\n  transactions:\n    - id: READ\n      name: read_cmd\n"
        "      behavioral_contract_refs: [BC_READ]\n      inputs: [cmd_valid]\n"
        "      outputs:\n        - {name: rsp_rdata}\n"
        "      output_rules:\n        - {name: rsp_rdata, port: rsp_rdata, expr: count_q}\n"
        "      state_updates:\n        - {name: count_q, expr: count_q + 1}\n"
        "cycle_model:\n  handshake_rules:\n    - {name: ctrl, signal: cmd_valid, condition: cmd_valid && cmd_ready}\n"
        "traceability:\n  locked_truth_projection:\n    behavioral_contracts: [BC_READ]\n"
        "quality_gates:\n  rtl_gen:\n    direct_rtl_allowed:\n      approved: true\n"
        "      reason: locked contracts gate RTL directly\n",
        encoding="utf-8",
    )
    (ip_dir / "req" / "obligations.json").write_text(json.dumps(
        {"ip": ip, "obligations": [{"obligation_id": "OBL_READ", "requirement_refs": ["REQ_READ"],
                                    "statement": "Implement read."}]}), encoding="utf-8")
    _rtlf_write_bc(ip_dir, rtl_stage=True)
    (ip_dir / "req" / "design_spec_trace.json").write_text(json.dumps(
        {"schema_version": 1, "type": "design_spec_trace_check", "ip": ip, "status": "pass"}) + "\n", encoding="utf-8")
    (ip_dir / "rtl").mkdir()
    (ip_dir / "list").mkdir()
    (ip_dir / "lint").mkdir()
    (ip_dir / "list" / f"{ip}.f").write_text(rel + "\n", encoding="utf-8")
    (ip_dir / "rtl" / f"{top}.sv").write_text(_rtlf_top_sv(top), encoding="utf-8")
    (ip_dir / "rtl" / "rtl_compile.json").write_text(json.dumps(
        {"type": "rtl_compile", "ip": ip, "dut_only": True, "passed": True,
         "errors": 0, "diagnostics": 0, "style_violations": 0, "rtl_files": [rel]}) + "\n", encoding="utf-8")
    (ip_dir / "lint" / "dut_lint.json").write_text(json.dumps(
        {"type": "dut_lint", "ip": ip, "dut_only": True, "passed": True,
         "errors": 0, "warnings": 0, "suppression_violation_count": 0, "rtl_files": [rel]}) + "\n", encoding="utf-8")
    # Provenance hash is chicken-and-egg: derive once, read the STABLE plan hash, then write provenance.
    _rtlf_derive.derive_plan(work, ip, audit_rtl=True)
    stable = _rtlf_derive._stable_json_sha256(ip_dir / "rtl" / "rtl_todo_plan.json")
    (ip_dir / "rtl" / "rtl_authoring_provenance.json").write_text(json.dumps(
        {"type": "rtl_authoring_provenance", "agent": "common_ai_agent", "workflow": "rtl-gen",
         "surface": "headless_common_engine", "todo_plan_sha256": stable, "rtl_files": [rel]}) + "\n", encoding="utf-8")
    future = time.time() + 30
    for art in ("rtl/rtl_compile.json", "lint/dut_lint.json", "rtl/rtl_authoring_provenance.json"):
        os.utime(ip_dir / art, (future, future))
    return {"ip": ip, "top": top, "rel": rel}


def _rtlf_run_gate(work: Path, ctx: dict) -> None:
    proc = subprocess.run([sys.executable, str(_RTLF_GATE), ctx["ip"], "--root", str(work), "--audit-rtl"],
                          capture_output=True, text=True, check=False)
    ctx["rc"] = proc.returncode


def _rtlf_read_status(work: Path, ctx: dict) -> str:
    return "pass" if ctx.get("rc") == 0 else "fail"


def _rtlf_bump(work: Path, ctx: dict) -> None:
    f = time.time() + 60
    d = work / ctx["ip"]
    for art in ("rtl/rtl_compile.json", "lint/dut_lint.json", "rtl/rtl_authoring_provenance.json"):
        os.utime(d / art, (f, f))


def _rtlf_mut_empty_body(work: Path, ctx: dict) -> None:
    p = work / ctx["ip"] / "rtl" / f"{ctx['top']}.sv"
    p.write_text(f"module {ctx['top']}(input logic clk, input logic rst_n, input logic cmd_valid, "
                 f"output logic cmd_ready, output logic [31:0] rsp_rdata);\nendmodule\n", encoding="utf-8")
    os.utime(p, (time.time() - 5, time.time() - 5))
    _rtlf_bump(work, ctx)


def _rtlf_mut_drop_io_port(work: Path, ctx: dict) -> None:
    p = work / ctx["ip"] / "rtl" / f"{ctx['top']}.sv"
    s = p.read_text(encoding="utf-8").replace("  output logic [31:0] rsp_rdata\n", "").replace(
        "  assign rsp_rdata = cmd_valid ? count_q : 32'd0;\n", "")
    p.write_text(s, encoding="utf-8")
    os.utime(p, (time.time() - 5, time.time() - 5))
    _rtlf_bump(work, ctx)


def _rtlf_mut_constant_tieoff(work: Path, ctx: dict) -> None:
    p = work / ctx["ip"] / "rtl" / f"{ctx['top']}.sv"
    p.write_text(p.read_text(encoding="utf-8").replace(
        "assign cmd_ready = ready_q | cmd_valid;", "assign cmd_ready = 1'b1;"), encoding="utf-8")
    os.utime(p, (time.time() - 5, time.time() - 5))
    _rtlf_bump(work, ctx)


def _rtlf_mut_compile_failed(work: Path, ctx: dict) -> None:
    p = work / ctx["ip"] / "rtl" / "rtl_compile.json"
    d = json.loads(p.read_text())
    d["passed"] = False
    p.write_text(json.dumps(d))
    _rtlf_bump(work, ctx)


def _rtlf_mut_provenance_hash_wrong(work: Path, ctx: dict) -> None:
    p = work / ctx["ip"] / "rtl" / "rtl_authoring_provenance.json"
    d = json.loads(p.read_text())
    d["todo_plan_sha256"] = "0" * 64
    p.write_text(json.dumps(d))
    _rtlf_bump(work, ctx)


def _rtlf_mut_stale_compile(work: Path, ctx: dict) -> None:
    # RTL source newer than the compile artifact -> freshness violation.
    os.utime(work / ctx["ip"] / "rtl" / f"{ctx['top']}.sv", (time.time() + 120, time.time() + 120))


DERIVE_RTL_TODOS_SELF_TEST = GateSelfTest(
    build_good=_rtlf_build_good,
    run_gate=_rtlf_run_gate,
    read_status=_rtlf_read_status,
    mutations=[
        ("empty_rtl_module_body", _rtlf_mut_empty_body),
        ("ssot_io_port_dropped_from_rtl", _rtlf_mut_drop_io_port),
        ("top_output_constant_tieoff", _rtlf_mut_constant_tieoff),
        ("compile_passed_false", _rtlf_mut_compile_failed),
        ("provenance_hash_wrong", _rtlf_mut_provenance_hash_wrong),
        ("stale_compile_artifact", _rtlf_mut_stale_compile),
    ],
)


# ---------------------------------------------------------------------------
# Gate registry — single source of truth.
# ---------------------------------------------------------------------------

# Covered: gate has a mutation self-test proving it kills hollow input.
COVERED_GATES = {
    # Engine-internal content gate (NOT listed as a STAGE_MANIFEST stage command).
    "tb_contract_ledger": {
        "scripts": ("derive_tb_todos.py",),
        "self_test": TB_CONTRACT_LEDGER_SELF_TEST,
    },
    # req contract-authority gate (manifest "contract_authority" entrypoint).
    "req_contract_authority": {
        "scripts": ("check_contract_bundle.py", "check_locked_truth_bundle.py"),
        "self_test": REQ_CONTRACT_AUTHORITY_SELF_TEST,
    },
    # scoreboard schema/observable gate (manifest "scoreboard_schema" stage).
    "scoreboard_events": {
        "scripts": ("check_scoreboard_events.py",),
        "self_test": SCOREBOARD_EVENTS_SELF_TEST,
    },
    # final local-evidence signoff gate (manifest "signoff" stage/entrypoint).
    "ip_signoff": {
        "scripts": ("check_ip_signoff.py",),
        "self_test": IP_SIGNOFF_SELF_TEST,
    },
    # locked-truth obligation coverage gate (fixed 2026-06-09).
    "truth_coverage": {
        "scripts": ("check_truth_coverage.py",),
        "self_test": TRUTH_COVERAGE_SELF_TEST,
    },
    # contract-reflection closure gate, default mode (fixed 2026-06-09).
    "contract_reflection": {
        "scripts": ("run_contract_check.py",),
        "self_test": CONTRACT_REFLECTION_SELF_TEST,
    },
    # SSOT functional coverage summary gate (manifest "coverage" stage).
    "ssot_coverage_summary": {
        "scripts": ("ssot_coverage_summary.py",),
        "self_test": SSOT_COVERAGE_SUMMARY_SELF_TEST,
    },
    # pre-sim TB python compile gate (manifest "tb_python_compile" stage).
    "tb_python_compile": {
        "scripts": ("check_tb_python_compile.py",),
        "self_test": TB_PYTHON_COMPILE_SELF_TEST,
    },
    # DUT lint gate (manifest "dut_lint" stage) — needs verilator.
    "dut_lint": {
        "scripts": ("dut_lint_report.py",),
        "self_test": DUT_LINT_SELF_TEST,
        "requires_tool": "verilator",
    },
    # DUT RTL compile gate (manifest "rtl_compile" stage) — needs iverilog.
    "rtl_compile": {
        "scripts": ("rtl_compile_report.py",),
        "self_test": RTL_COMPILE_SELF_TEST,
        "requires_tool": "iverilog",
    },
    # RTL final static/todo closure gate (manifest "rtl_final_gate" stage).
    "rtl_final": {
        "scripts": ("derive_rtl_todos.py",),
        "self_test": DERIVE_RTL_TODOS_SELF_TEST,
    },
}

# Explicit, FROZEN backlog: acknowledged gates that still lack a direct
# mutation self-test. Shrinks only by a reviewed change (see module docstring).
# Goal state reached: every manifest gate has a kill-proof self-test.
UNCOVERED_GATES: dict[str, str] = {}

# Gate-shaped but advisory: no hard pass/fail contract, so no kill-proof required.
ADVISORY_NOT_GATE = {
    "mutation_guard.py": "advisory mutant kill-rate signal, not a pass/fail gate",
}


# ---------------------------------------------------------------------------
# Manifest enumeration + gate detection
# ---------------------------------------------------------------------------

def _iter_manifest_commands() -> list[str]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cmds: list[str] = []
    for ep in (data.get("entrypoints") or {}).values():
        if ep.get("command"):
            cmds.append(ep["command"])
    for stage in data.get("stages") or []:
        for key in ("command", "strict_command"):
            if stage.get(key):
                cmds.append(stage[key])
    return cmds


def _script_basename(command: str) -> str | None:
    for tok in command.split():
        if tok.endswith(".py") or tok.endswith(".sh"):
            return Path(tok).name
    return None


# A command is a gate if its job is to REJECT bad input: a check_* script, an
# explicit enforcement flag, or a known closure/report gate.
_EXPLICIT_GATE_SCRIPTS = {
    "run_contract_check.py",
    "ssot_coverage_summary.py",
    "dut_lint_report.py",
    "rtl_compile_report.py",
}


def _is_gate_command(command: str) -> bool:
    base = _script_basename(command) or ""
    if base.startswith("check_"):
        return True
    if "--enforce" in command or "--require" in command:
        return True
    return base in _EXPLICIT_GATE_SCRIPTS


def _registered_scripts() -> set[str]:
    reg = set(UNCOVERED_GATES) | set(ADVISORY_NOT_GATE)
    for spec in COVERED_GATES.values():
        reg |= set(spec["scripts"])
    return reg


# ---------------------------------------------------------------------------
# Meta-gate tests
# ---------------------------------------------------------------------------

def test_every_manifest_gate_is_registered():
    """Ratchet: a gate-like command in STAGE_MANIFEST must be acknowledged in the
    registry. A new hollow gate cannot ship without either a self-test or an
    explicit UNCOVERED_GATES entry."""
    registered = _registered_scripts()
    unregistered = sorted({
        _script_basename(cmd)
        for cmd in _iter_manifest_commands()
        if _is_gate_command(cmd) and _script_basename(cmd) not in registered
    })
    assert not unregistered, (
        "Unregistered gate(s) in STAGE_MANIFEST — add a GateSelfTest or acknowledge "
        f"in UNCOVERED_GATES: {unregistered}"
    )


def test_ratchet_can_fail_on_an_unregistered_gate():
    """The meta-gate must itself be killable: a gate-shaped command that is not in
    the registry is detected as unregistered. (A meta-gate that cannot fail would
    be the same silent-PASS sin one level up.)"""
    fake = "python3 workflow/new/scripts/check_brand_new_thing.py <ip> --root <ip-parent>"
    assert _is_gate_command(fake), "detector failed to recognize a check_* gate"
    assert _script_basename(fake) == "check_brand_new_thing.py"
    assert _script_basename(fake) not in _registered_scripts(), (
        "fixture script should be unregistered for this proof"
    )


@pytest.mark.parametrize("gate_id", sorted(COVERED_GATES))
def test_covered_gate_self_test_kills_all_mutations(gate_id, tmp_path_factory):
    """Every covered gate must pass a known-good fixture and reject every mutation."""
    spec = COVERED_GATES[gate_id]
    tool = spec.get("requires_tool")
    if tool and shutil.which(tool) is None:
        pytest.skip(f"{gate_id} self-test requires external tool {tool!r} (not installed)")
    spec["self_test"].assert_kills_all(tmp_path_factory, gate_id)


def test_uncovered_backlog_is_explicit_and_frozen(capsys):
    """The backlog of not-yet-self-tested gates is explicit and frozen, so it can
    only shrink by a reviewed change. Goal state: UNCOVERED_GATES == {}."""
    with capsys.disabled():
        print(
            f"\n[gate-self-test] covered={sorted(COVERED_GATES)} | "
            f"uncovered={len(UNCOVERED_GATES)} -> {sorted(UNCOVERED_GATES)}"
        )
    frozen: set[str] = set()  # backlog retired — every gate is covered
    assert set(UNCOVERED_GATES) == frozen, (
        "Gate self-test backlog changed — if you added coverage, move the gate to "
        "COVERED_GATES and update this frozen set deliberately."
    )
