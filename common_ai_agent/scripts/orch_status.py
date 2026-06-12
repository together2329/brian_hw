#!/usr/bin/env python3
"""Live pipeline status — where is this IP, what blocks it, what to do next.

One-shot dashboard joining:
  * per-stage FS-truth (the SAME _job_artifact_failure the dispatch gate and
    finalize gate read — so this prints exactly what the orchestrator sees),
  * the active orchestrator run (last steps from its supervisor log),
  * in-flight / recent worker jobs with failure classes,
  * every known blocker artifact WITH its embedded remediation text
    (ssot_validation blockers, rtl_blocked questions, tb gate, model checks),
  * judge cache population.

Usage:
  python3 scripts/orch_status.py <ip> --root <project-root> [--recent 5]

Companion to scripts/orch_profile.py (cost/time accounting); this one answers
"왜 지금 안 움직이는가" in real time. Campaign finding 29 follow-on.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

NEXT_ACTION = {
    "timeout": "raise ATLAS_STAGE_TOOL_TIMEOUT_S / retry the stage; check judge cache is enabled",
    "silent-fail": "worker wrote nothing — re-dispatch with a single concrete instruction",
    "semantic-gate": "read the violations below; repair belongs to ssot-gen (content) not retries",
    "evidence-missing": "run the evidence validator named below directly to see what it demands",
    "stage-gate": "open the stage record's gate/questions below and answer/repair them",
    "locked-truth": "truth pack issue — amend + re-lock via scripts/orch_campaign_truth.py (human)",
    "upstream-red": "fix the named upstream stage first (the dispatch gate is telling you the order)",
}


def _age(ts: float) -> str:
    d = max(0.0, time.time() - ts)
    if d >= 3600:
        return f"{d/3600:.1f}h ago"
    if d >= 60:
        return f"{d/60:.0f}m ago"
    return f"{d:.0f}s ago"


def _classify(text: str) -> str:
    rules = (
        ("timeout", r"timed out|timeout"),
        ("silent-fail", r"silent-fail"),
        ("semantic-gate", r"SEMANTIC GATE FAIL"),
        ("evidence-missing", r"missing required evidence"),
        ("upstream-red", r"upstream_stage_red"),
        ("locked-truth", r"locked truth|truth_not_locked"),
        ("stage-gate", r"stage evidence failed|gate status=f|BLOCKED"),
    )
    for name, rx in rules:
        if re.search(rx, text or "", re.I):
            return name
    return "other-error" if text else "ok"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("ip")
    ap.add_argument("--root", required=True)
    ap.add_argument("--recent", type=int, default=5)
    ns = ap.parse_args()
    root = Path(ns.root).resolve()
    ip_dir = root / ns.ip

    # ---- 1. per-stage truth (exactly what the orchestrator/gates read) ----
    print(f"== stage truth for {ns.ip} (the gates' own view) ==")
    try:
        from src import atlas_api_jobs as jobs  # noqa: deferred heavy import

        for stage in jobs._PIPELINE_STAGES:
            sid = stage["id"]
            bad, why = jobs._job_artifact_failure(
                {"ip": ns.ip, "stage_id": sid, "workflow": stage["workflow"]}, root
            )
            mark = "RED" if bad else "ok "
            line = f"  [{mark}] {sid:<14}"
            if bad:
                line += f" {why[:110]}"
            print(line)
    except Exception as exc:  # pragma: no cover — env without src deps
        print(f"  (stage truth unavailable: {exc})")

    # ---- 2. active orchestrator run ----
    orch_root = root / ".session" / "orchestrators-ipc"
    runs = sorted(orch_root.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True) if orch_root.is_dir() else []
    print("\n== latest orchestrator run ==")
    if runs:
        run_dir = runs[0]
        resp = run_dir / "response.json"
        state = "RUNNING (no response yet)"
        if resp.is_file():
            try:
                doc = json.loads(resp.read_text())
                state = f"{doc.get('status')} (steps={doc.get('steps_taken')})"
            except Exception:
                state = "response unreadable"
        print(f"  {run_dir.name[:12]}  {state}  · {_age(run_dir.stat().st_mtime)}")
        log = run_dir / "supervisor.log"
        if log.is_file():
            text = re.sub(r"\x1b\[[0-9;]*m", "", log.read_text(errors="replace"))
            steps = [l.strip()[:120] for l in text.splitlines()
                     if re.search(r"dispatch_workflow|woken|ask_user|finalised|upstream_stage_red", l)]
            for line in steps[-ns.recent:]:
                print(f"    {line}")
    else:
        print("  (none)")

    # ---- 3. worker jobs: in-flight + recent failures ----
    jobs_dir = root / ".session" / "workers-ipc"
    inflight, failed = [], []
    if jobs_dir.is_dir():
        for d in jobs_dir.iterdir():
            req = d / "request.json"
            if not req.is_file():
                continue
            try:
                rq = json.loads(req.read_text())
            except Exception:
                continue
            if str(rq.get("ip") or "") != ns.ip:
                continue
            m = re.search(r"workflow: (\S+)", str(rq.get("context") or ""))
            wf = m.group(1) if m else str(rq.get("template") or "?")
            resp = d / "response.json"
            if not resp.is_file():
                inflight.append((req.stat().st_mtime, wf, d.name))
                continue
            try:
                rs = json.loads(resp.read_text())
            except Exception:
                continue
            if rs.get("status") not in ("completed",):
                blob = str(rs.get("error") or "") + str((rs.get("result") or {}).get("result") or "")[:3000]
                failed.append((resp.stat().st_mtime, wf, _classify(blob), str(rs.get("error") or "")[:90], d.name))
    print("\n== in-flight worker jobs ==")
    for ts, wf, name in sorted(inflight, reverse=True):
        note = "" if time.time() - ts < 1800 else "  <- POSSIBLY HUNG/GHOST (no response.json)"
        print(f"  {wf:<16} started {_age(ts)}  {name}{note}")
    if not inflight:
        print("  (none)")
    print(f"\n== recent failed jobs (last {ns.recent}) ==")
    for ts, wf, klass, err, name in sorted(failed, reverse=True)[: ns.recent]:
        print(f"  {_age(ts):>9}  {wf:<14} {klass:<16} {err}")
        hint = NEXT_ACTION.get(klass)
        if hint:
            print(f"             -> {hint}")

    # ---- 4. blocker artifacts with embedded remediation ----
    print("\n== blockers on disk (with the validators' own remediation) ==")
    found = False
    v = ip_dir / "req" / "ssot_validation.json"
    if v.is_file():
        try:
            doc = json.loads(v.read_text())
            if doc.get("ok") is False:
                found = True
                for b in (doc.get("blockers") or [])[:6]:
                    print(f"  [ssot] {b.get('id')}: {str(b.get('message'))[:100]}")
                    print(f"         fix: {str(b.get('fix'))[:110]}")
        except Exception:
            pass
    rb = ip_dir / "rtl" / "rtl_blocked.json"
    if rb.is_file():
        try:
            doc = json.loads(rb.read_text())
            for q in (doc.get("questions") or [])[:6]:
                found = True
                print(f"  [rtl] {q.get('id')}: {str(q.get('decision_needed'))[:100]}")
                opts = q.get("options") or []
                if opts:
                    print(f"        fix: {str(opts[0])[:110]}")
        except Exception:
            pass
    for rel, label in (("model/fl_model_check.json", "fl"), ("model/cl_model_check.json", "cl")):
        p = ip_dir / rel
        if p.is_file():
            try:
                doc = json.loads(p.read_text())
                if doc.get("passed") is False:
                    found = True
                    sv = doc.get("semantic_validation") or {}
                    for src_name in ("deterministic_backstop", "llm_judge"):
                        section = sv.get(src_name) or {}
                        viols = section.get("violations") or []
                        for c in section.get("per_contract") or []:
                            viols = viols + (c.get("violations") or [])
                        for item in viols[:3]:
                            print(f"  [{label}] {str(item.get('detail'))[:120]}")
            except Exception:
                pass
    tb = ip_dir / "tb" / "tb_todo_plan.json"
    if tb.is_file():
        try:
            doc = json.loads(tb.read_text())
            gate = doc.get("gate") or {}
            if gate.get("status") not in (None, "pass"):
                found = True
                comp = doc.get("todo_completion") or {}
                print(f"  [tb] gate={gate.get('status')} authoring_open={comp.get('authoring_open_tasks')} "
                      f"validation_open={comp.get('validation_open_tasks')}")
                for item in (comp.get("open_authoring") or [])[:3]:
                    print(f"       open: {item.get('task_id')} — {str(item.get('reason'))[:100]}")
        except Exception:
            pass
    if not found:
        print("  (no blocker artifacts — if a stage is RED above, its record carries the reason)")

    # ---- 5. judge cache ----
    cache = ip_dir / "model" / ".judge_cache"
    n = len(list(cache.glob("*.json"))) if cache.is_dir() else 0
    print(f"\n== judge verdict cache ==\n  {n} cached verdict(s) in model/.judge_cache")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
