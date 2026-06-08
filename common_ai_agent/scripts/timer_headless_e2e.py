#!/usr/bin/env python3
"""Real-LLM headless E2E for a simple timer: req -> ssot -> rtl -> tb -> sim.

Proves the generated stage todos drive a headless run end to end and that the
new RTL phase-grouped todos + VCM per-obligation tb/sim/lint todos appear.

Flow (segmented so the locked req bundle = the "req" step lands before tb/sim):
  1. real LLM: ssot-gen, fl-model-gen, equiv-goals, rtl-gen   (-> SSOT + RTL phase todos)
  2. req step: author + lock a timer VCM bundle (req->obligation->contract->evidence)
  3. real LLM: lint, tb-gen, sim                               (-> VCM obligation todos + gates)

Each stage appends a line to <root>/e2e_progress.jsonl and the final report is
written to <root>/e2e_report.json.

Usage:
  python3 scripts/timer_headless_e2e.py [--root DIR] [--model glm-5.1]
          [--run-mode starter] [--connectivity-only] [--segment1-only]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

IP = "timer"
REQ_TEXT = (
    "# Timer IP requirement\n\n"
    "The timer is a small APB-style peripheral. After reset deassertion the counter "
    "holds at zero and is disabled. Software writes a 32-bit LOAD register and sets the "
    "ENABLE bit in a CTRL register. While enabled, the counter decrements by one every "
    "clock cycle. When the counter reaches zero it asserts a single-cycle irq pulse and "
    "reloads the LOAD value, continuing to count. Writing ENABLE=0 stops and holds the "
    "counter. A STATUS register exposes the current count (read-only). The generated "
    "FunctionalModel is the expected-behavior source for the cocotb/pyuvm scoreboard. "
    "DUT-only compile, DUT-only lint, structured scoreboard events, and FL-vs-RTL "
    "comparison are required.\n"
)

# Timer VCM bundle (the "req" step injected between rtl and tb).
_BUNDLE = {
    "requirements": [
        {"requirement_id": "REQ_TIMER_001", "title": "Down-counter with reload + irq",
         "statement": "Enabled timer counts down, pulses irq at zero, reloads LOAD.",
         "obligation_refs": ["OBL_TIMER_COUNT_001", "OBL_TIMER_IRQ_001", "OBL_TIMER_LINT_001"]},
    ],
    "obligations": [
        {"obligation_id": "OBL_TIMER_COUNT_001", "requirement_refs": ["REQ_TIMER_001"],
         "statement": "Counter decrements each enabled cycle and reloads at zero.",
         "contract_refs": ["C_TIMER_COUNT"], "required_stages": ["rtl", "tb", "sim"],
         "owned_by_stage": "sim", "closure_stage": "sim", "granularity": "temporal", "failure_owner": "rtl-gen"},
        {"obligation_id": "OBL_TIMER_IRQ_001", "requirement_refs": ["REQ_TIMER_001"],
         "statement": "irq pulses one cycle when the counter reaches zero.",
         "contract_refs": ["C_TIMER_IRQ"], "required_stages": ["rtl", "tb"],
         "owned_by_stage": "tb", "closure_stage": "tb", "granularity": "structural", "failure_owner": "rtl-gen"},
        {"obligation_id": "OBL_TIMER_LINT_001", "requirement_refs": ["REQ_TIMER_001"],
         "statement": "No inferred latches; single driver per register.",
         "contract_refs": ["C_TIMER_LINT"], "required_stages": ["lint"],
         "owned_by_stage": "lint", "closure_stage": "lint", "granularity": "structural", "failure_owner": "rtl-gen"},
    ],
    "contract_refs": [
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
    ],
    "evidence_plan": [
        {"evidence_id": "E_TIMER_COUNT", "contract_ref": "C_TIMER_COUNT", "artifact": "sim/scoreboard_events.jsonl",
         "validator": "check_evidence_contract.py", "pass_condition": "observed counter seq == FL expected"},
        {"evidence_id": "E_TIMER_IRQ", "contract_ref": "C_TIMER_IRQ", "artifact": "tb/cocotb/test_timer.py",
         "validator": "check_scoreboard_events.py", "pass_condition": "irq pulse at zero"},
        {"evidence_id": "E_TIMER_LINT", "contract_ref": "C_TIMER_LINT", "artifact": "lint/dut_lint.json",
         "validator": "dut_lint_report.py", "pass_condition": "no latch/single-driver findings"},
    ],
    "structural_contracts": [
        {"id": "SC_TIMER_REGS",
         "obligations": ["OBL_TIMER_COUNT_001", "OBL_TIMER_IRQ_001", "OBL_TIMER_LINT_001"],
         "ssot_anchor": "io_list",
         "signals": [
             {"name": "clk", "dir": "input", "width": 1},
             {"name": "rst_n", "dir": "input", "width": 1},
             {"name": "load", "dir": "input", "width": 32},
             {"name": "enable", "dir": "input", "width": 1},
             {"name": "count", "dir": "output", "width": 32},
             {"name": "irq", "dir": "output", "width": 1},
         ]},
    ],
}


def _log(progress: Path, **row) -> None:
    row["t"] = time.strftime("%H:%M:%S")
    with progress.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")
    print(json.dumps(row), flush=True)


def _tracker_summary(ip_dir: Path, slug: str) -> dict:
    for rel in (f"todo/{slug}_todo_tracker.json", f"{slug}/{slug}_todo_tracker.json",
                "rtl/rtl_todo_tracker.json", "todo/rtl_todo_tracker.json"):
        p = ip_dir / rel
        if p.is_file():
            try:
                trk = json.loads(p.read_text("utf-8"))
            except Exception:
                continue
            tasks = trk.get("tasks", [])
            grp = trk.get("ui_grouping")
            return {
                "tracker": rel,
                "strategy": grp.get("strategy") if isinstance(grp, dict) else grp,
                "task_count": len(tasks),
                "contents": [t.get("content") for t in tasks],
                "has_gate": any(t.get("command") for t in tasks),
            }
    return {}


def _lock_bundle(root: Path) -> dict:
    ip_dir = root / IP
    req = ip_dir / "req"
    req.mkdir(parents=True, exist_ok=True)
    for name, key, listkey in (("requirements_index", "requirements", "requirements"),
                               ("obligations", "obligations", "obligations"),
                               ("contract_refs", "contract_refs", "contract_refs"),
                               ("structural_contracts", "structural_contracts", "contracts"),
                               ("evidence_plan", "evidence_plan", "evidence_plan")):
        (req / f"{name}.json").write_text(
            json.dumps({"schema_version": 1, "type": name, "ip": IP, listkey: _BUNDLE[key]}), "utf-8")
    lock = REPO / "workflow" / "req-gen" / "scripts" / "lock_requirement_set.py"
    r = subprocess.run([sys.executable, str(lock), IP, "--root", str(root),
                        "--from-candidate", "--approved-by", "brian"], capture_output=True, text=True)
    return {"exit": r.returncode, "tail": (r.stdout + r.stderr).strip().splitlines()[-1:] }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(REPO / ".e2e" / "timer_run"))
    ap.add_argument("--model", default="glm-5.1")
    ap.add_argument("--run-mode", default="starter")
    ap.add_argument("--connectivity-only", action="store_true")
    ap.add_argument("--segment1-only", action="store_true")
    ns = ap.parse_args()

    root = Path(ns.root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    progress = root / "e2e_progress.jsonl"
    report = root / "e2e_report.json"
    ip_dir = root / IP
    (ip_dir).mkdir(parents=True, exist_ok=True)
    req_file = root / f"{IP}_requirements.md"
    req_file.write_text(REQ_TEXT, "utf-8")

    from src.headless_workflow import HeadlessWorkflowRunner, RealLLMProvider

    runner = HeadlessWorkflowRunner(root=root, model=ns.model,
                                    llm_provider=RealLLMProvider(), run_mode=ns.run_mode)
    out: dict = {"ip": IP, "model": ns.model, "run_mode": ns.run_mode, "root": str(root), "stages": {}, "trackers": {}}

    def run_stage(stage: str, with_req=False):
        _log(progress, event="stage_start", stage=stage)
        t0 = time.time()
        try:
            res = runner.run(ip=IP, requirement_path=str(req_file) if with_req else None, stages=[stage])
            st = getattr(res, "status", "?")
        except Exception as exc:
            st = f"error:{exc}"
            res = None
        dt = round(time.time() - t0, 1)
        out["stages"][stage] = {"status": st, "seconds": dt}
        _log(progress, event="stage_done", stage=stage, status=st, seconds=dt)
        report.write_text(json.dumps(out, indent=2), "utf-8")
        return st

    _log(progress, event="begin", model=ns.model, run_mode=ns.run_mode)

    # connectivity check: just ssot-gen
    s = run_stage("ssot-gen", with_req=True)
    out["trackers"]["ssot"] = _tracker_summary(ip_dir, "ssot")
    if ns.connectivity_only:
        report.write_text(json.dumps(out, indent=2), "utf-8")
        _log(progress, event="end", note="connectivity-only")
        return 0 if not str(s).startswith("error") else 1

    # segment 1: through rtl
    for stage in ["fl-model-gen", "equiv-goals", "rtl-gen"]:
        run_stage(stage)
    out["trackers"]["rtl"] = _tracker_summary(ip_dir, "rtl")
    _log(progress, event="rtl_tracker", **out["trackers"]["rtl"])

    if ns.segment1_only:
        report.write_text(json.dumps(out, indent=2), "utf-8")
        _log(progress, event="end", note="segment1-only")
        return 0

    # req step: author + lock the VCM bundle so tb/sim/lint project obligation todos
    out["req_lock"] = _lock_bundle(root)
    _log(progress, event="req_locked", **out["req_lock"])

    # segment 2: lint, tb, sim  (now bundle exists -> VCM obligation todos)
    for stage in ["lint", "tb-gen", "sim"]:
        run_stage(stage)
    for slug, key in (("lint", "lint"), ("tb", "tb"), ("sim", "sim")):
        out["trackers"][slug] = _tracker_summary(ip_dir, slug)
        _log(progress, event="vcm_tracker", stage=slug, **out["trackers"][slug])

    report.write_text(json.dumps(out, indent=2), "utf-8")
    _log(progress, event="end", report=str(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
