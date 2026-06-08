#!/usr/bin/env python3
"""Deterministic demo of VCM-driven per-stage todos (no LLM).

Authors a small `timer` Verification Contract Model bundle, locks it via the
real lock_requirement_set.py, then runs the lint / tb / sim stage engine and
prints each stage's generated tracker — proving that the locked
requirement->obligation->contract spine projects into one visible obligation
todo per stage plus a deterministic detect-and-skip gate.

Usage:  python3 scripts/timer_vcm_demo.py [--root <dir>] [--keep]
Exit 0 on success (each stage shows its owned obligation todos + a gate todo).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

IP = "timer"

# --- a minimal but complete VCM bundle: req -> obligation -> contract -> evidence
REQUIREMENTS = [
    {"requirement_id": "REQ_TIMER_COUNT_001", "title": "Down-counter with reload",
     "statement": "The timer counts down from the loaded value and reloads on expiry.",
     "obligation_refs": ["OBL_TIMER_COUNT_001", "OBL_TIMER_IRQ_001", "OBL_TIMER_LINT_001"]},
]
OBLIGATIONS = [
    {"obligation_id": "OBL_TIMER_COUNT_001", "requirement_refs": ["REQ_TIMER_COUNT_001"],
     "statement": "Counter decrements every enabled cycle and reloads at zero.",
     "contract_refs": ["C_TIMER_COUNT"], "required_stages": ["rtl", "tb", "sim"],
     "owned_by_stage": "sim", "closure_stage": "sim", "granularity": "temporal", "failure_owner": "rtl-gen"},
    {"obligation_id": "OBL_TIMER_IRQ_001", "requirement_refs": ["REQ_TIMER_COUNT_001"],
     "statement": "irq pulses for one cycle when the counter reaches zero.",
     "contract_refs": ["C_TIMER_IRQ"], "required_stages": ["rtl", "tb"],
     "owned_by_stage": "tb", "closure_stage": "tb", "granularity": "structural", "failure_owner": "rtl-gen"},
    {"obligation_id": "OBL_TIMER_LINT_001", "requirement_refs": ["REQ_TIMER_COUNT_001"],
     "statement": "No inferred latches and a single driver per register.",
     "contract_refs": ["C_TIMER_LINT"], "required_stages": ["lint"],
     "owned_by_stage": "lint", "closure_stage": "lint", "granularity": "structural", "failure_owner": "rtl-gen"},
]
CONTRACTS = [
    {"contract_ref_id": "C_TIMER_COUNT", "obligation_refs": ["OBL_TIMER_COUNT_001"],
     "ssot_anchor": "function_model.transactions.tick",
     "stage_contracts": [{"stage": "rtl", "artifact": "rtl/timer.sv"},
                          {"stage": "tb", "artifact": "tb/cocotb/test_timer.py"},
                          {"stage": "sim", "artifact": "sim/scoreboard_events.jsonl"}]},
    {"contract_ref_id": "C_TIMER_IRQ", "obligation_refs": ["OBL_TIMER_IRQ_001"],
     "ssot_anchor": "interrupts.irq",
     "stage_contracts": [{"stage": "rtl", "artifact": "rtl/timer.sv"},
                         {"stage": "tb", "artifact": "tb/cocotb/test_timer.py"}]},
    {"contract_ref_id": "C_TIMER_LINT", "obligation_refs": ["OBL_TIMER_LINT_001"],
     "ssot_anchor": "coding_rules",
     "stage_contracts": [{"stage": "lint", "artifact": "lint/dut_lint.json"}]},
]
EVIDENCE = [
    {"evidence_id": "E_TIMER_COUNT", "contract_ref": "C_TIMER_COUNT",
     "artifact": "sim/scoreboard_events.jsonl", "validator": "check_evidence_contract.py",
     "pass_condition": "observed counter sequence == FL expected"},
    {"evidence_id": "E_TIMER_IRQ", "contract_ref": "C_TIMER_IRQ",
     "artifact": "tb/cocotb/test_timer.py", "validator": "check_scoreboard_events.py",
     "pass_condition": "irq pulse observed at zero"},
    {"evidence_id": "E_TIMER_LINT", "contract_ref": "C_TIMER_LINT",
     "artifact": "lint/dut_lint.json", "validator": "dut_lint_report.py",
     "pass_condition": "no latch / single-driver findings"},
]
# Structural contracts (mandatory bundle file): physical signal/interface truth
# each obligation is anchored to. Minimal but schema-valid.
STRUCTURAL = [
    {"id": "SC_TIMER_REGS", "obligations": ["OBL_TIMER_COUNT_001", "OBL_TIMER_IRQ_001", "OBL_TIMER_LINT_001"],
     "ssot_anchor": "io_list",
     "signals": [
         {"name": "clk", "dir": "input", "width": 1},
         {"name": "rst_n", "dir": "input", "width": 1},
         {"name": "load", "dir": "input", "width": 32},
         {"name": "enable", "dir": "input", "width": 1},
         {"name": "count", "dir": "output", "width": 32},
         {"name": "irq", "dir": "output", "width": 1},
     ]},
]


def _write_candidate(req_dir: Path) -> None:
    req_dir.mkdir(parents=True, exist_ok=True)
    (req_dir / "requirements_index.json").write_text(
        json.dumps({"schema_version": 1, "type": "requirements_index", "ip": IP, "requirements": REQUIREMENTS}), "utf-8")
    (req_dir / "obligations.json").write_text(
        json.dumps({"schema_version": 1, "type": "obligations", "ip": IP, "obligations": OBLIGATIONS}), "utf-8")
    (req_dir / "contract_refs.json").write_text(
        json.dumps({"schema_version": 1, "type": "contract_refs", "ip": IP, "contract_refs": CONTRACTS}), "utf-8")
    (req_dir / "structural_contracts.json").write_text(
        json.dumps({"schema_version": 1, "type": "structural_contracts", "ip": IP, "contracts": STRUCTURAL}), "utf-8")
    (req_dir / "evidence_plan.json").write_text(
        json.dumps({"schema_version": 1, "type": "evidence_plan", "ip": IP, "evidence_plan": EVIDENCE}), "utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="")
    ap.add_argument("--keep", action="store_true")
    ns = ap.parse_args()

    root = Path(ns.root) if ns.root else Path(tempfile.mkdtemp(prefix="timer_vcm_"))
    ip_dir = root / IP
    (ip_dir / "yaml").mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{IP}.ssot.yaml").write_text("ip: timer\n", "utf-8")
    _write_candidate(ip_dir / "req")

    lock = REPO / "workflow" / "req-gen" / "scripts" / "lock_requirement_set.py"
    r = subprocess.run([sys.executable, str(lock), IP, "--root", str(root),
                        "--from-candidate", "--approved-by", "brian"],
                       capture_output=True, text=True)
    print(f"[lock] exit={r.returncode}  {(r.stdout + r.stderr).strip().splitlines()[-1] if (r.stdout+r.stderr).strip() else ''}")
    if r.returncode != 0:
        print(r.stdout + r.stderr)
        return 1
    assert (ip_dir / "req" / "approval_manifest.json").is_file(), "lock did not produce manifest"

    from src.workflow_stage_engine import WorkflowStageEngine
    eng = WorkflowStageEngine(root)
    expected = {"lint": {"OBL_TIMER_LINT_001"},
                "ssot-tb-cocotb": {"OBL_TIMER_IRQ_001", "OBL_TIMER_COUNT_001"},
                "sim": {"OBL_TIMER_COUNT_001"}}
    slug = {"lint": "lint", "ssot-tb-cocotb": "tb", "sim": "sim"}
    ok = True
    for stage, want in expected.items():
        try:
            eng.run_stage(stage, IP)
        except Exception as exc:  # stage tools may fail without RTL/TB; tracker is still written
            print(f"[{stage}] stage tool raised (expected without RTL/TB): {exc}")
        trk_path = ip_dir / "todo" / f"{slug[stage]}_todo_tracker.json"
        if not trk_path.is_file():
            print(f"[{stage}] FAIL: no tracker at {trk_path}")
            ok = False
            continue
        trk = json.loads(trk_path.read_text("utf-8"))
        tasks = trk.get("tasks", [])
        obl_ids = {t.get("source_id") for t in tasks if str(t.get("source_id", "")).startswith("OBL_")}
        gate = [t for t in tasks if t.get("command")]
        print(f"\n=== stage {stage}  (ui_grouping={trk.get('ui_grouping', {}).get('strategy') if isinstance(trk.get('ui_grouping'), dict) else trk.get('ui_grouping')}) ===")
        for t in tasks:
            print(f"   - {t['content']!r:60} cmd={'Y' if t.get('command') else '-'} on_reject={t.get('on_reject','-')}")
        if obl_ids != want:
            print(f"[{stage}] FAIL: obligations {obl_ids} != expected {want}")
            ok = False
        if not gate:
            print(f"[{stage}] FAIL: no deterministic gate todo")
            ok = False

    print("\n" + ("✅ PASS: every stage projects its owned VCM obligations + a deterministic gate"
                  if ok else "❌ FAIL"))
    if not ns.keep and not ns.root:
        import shutil
        shutil.rmtree(root, ignore_errors=True)
    else:
        print(f"artifacts kept under: {root}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
