#!/usr/bin/env python3
"""Pipeline wall-clock / LLM-call profiler — answer "where did the time go?"

Joins three evidence sources for one IP:
  1. llm_calls rows in the control DB (latency, tokens, cost, call_role,
     stage path inside session_id),
  2. workers-ipc/<job>/{request,response}.json (job wall time, status,
     error class),
  3. orchestrator_runs (run lifecycle).

Usage:
  python3 scripts/orch_profile.py <ip> --root <project-root>
      [--db ~/.common_ai_agent/atlas.db] [--since-hours 24] [--top 12]

Born from campaign finding 29 (2026-06-12): an afternoon was lost to a slow
nondeterministic CL judge + redundant full-chain dispatches, and nothing in
the platform could SAY that — debugging was manual archaeology.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import time
from collections import defaultdict
from pathlib import Path


def _fmt_s(ms: float) -> str:
    s = ms / 1000.0
    if s >= 3600:
        return f"{s/3600:.1f}h"
    if s >= 60:
        return f"{s/60:.1f}m"
    return f"{s:.1f}s"


def _stage_of(session_id: str, workflow: str) -> str:
    # session ids look like admin/default/<ip>/pipeline/<pid>/01-ssot-gen
    m = re.search(r"/\d{2}-([A-Za-z0-9_-]+)$", session_id or "")
    if m:
        return m.group(1)
    if (session_id or "").endswith("/orchestrator"):
        return "orchestrator"
    return workflow or "?"


_ERROR_CLASSES = (
    ("timeout", re.compile(r"timed out|timeout", re.I)),
    ("silent-fail", re.compile(r"silent-fail", re.I)),
    ("semantic-gate", re.compile(r"SEMANTIC GATE FAIL", re.I)),
    ("evidence-missing", re.compile(r"missing required evidence", re.I)),
    ("stage-gate", re.compile(r"stage evidence failed|gate status=f|BLOCKED", re.I)),
    ("locked-truth", re.compile(r"locked truth|truth_not_locked", re.I)),
    ("upstream-red", re.compile(r"upstream_stage_red", re.I)),
)


def _classify(text: str) -> str:
    for name, rx in _ERROR_CLASSES:
        if rx.search(text or ""):
            return name
    return "other-error" if text else "ok"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("ip")
    ap.add_argument("--root", required=True, help="project root (the dir holding <ip>/ and .session/)")
    ap.add_argument("--db", default=str(Path.home() / ".common_ai_agent" / "atlas.db"))
    ap.add_argument("--since-hours", type=float, default=24.0)
    ap.add_argument("--top", type=int, default=12)
    ns = ap.parse_args()
    since = time.time() - ns.since_hours * 3600
    root = Path(ns.root)

    # ---------------- LLM calls ----------------
    db = sqlite3.connect(ns.db)
    db.row_factory = sqlite3.Row
    rows = db.execute(
        "SELECT * FROM llm_calls WHERE ip_id = ? AND created_at >= ?", (ns.ip, since)
    ).fetchall()
    by_stage: dict[tuple[str, str], dict] = defaultdict(lambda: {"n": 0, "ms": 0.0, "cost": 0.0, "err": 0})
    total = {"n": 0, "ms": 0.0, "cost": 0.0}
    for r in rows:
        key = (str(r["call_role"] or "?"), _stage_of(str(r["session_id"] or ""), str(r["workflow"] or "")))
        b = by_stage[key]
        b["n"] += 1
        b["ms"] += float(r["latency_ms"] or 0)
        b["cost"] += float(r["cost_usd"] or 0)
        if str(r["status"] or "ok") != "ok":
            b["err"] += 1
        total["n"] += 1
        total["ms"] += float(r["latency_ms"] or 0)
        total["cost"] += float(r["cost_usd"] or 0)

    print(f"== LLM calls for {ns.ip} (last {ns.since_hours:g}h) ==")
    print(f"  total: {total['n']} calls · {_fmt_s(total['ms'])} model time · ${total['cost']:.2f}")
    ranked = sorted(by_stage.items(), key=lambda kv: -kv[1]["ms"])
    for (role, stage), b in ranked[: ns.top]:
        print(f"  {role:>12} · {stage:<22} {b['n']:>4} calls  {_fmt_s(b['ms']):>8}  ${b['cost']:.2f}"
              + (f"  errors={b['err']}" if b["err"] else ""))

    # ---------------- worker jobs ----------------
    jobs_dir = root / ".session" / "workers-ipc"
    by_class: dict[tuple[str, str], dict] = defaultdict(lambda: {"n": 0, "ms": 0.0})
    job_rows = []
    if jobs_dir.is_dir():
        for d in jobs_dir.iterdir():
            req, resp = d / "request.json", d / "response.json"
            if not req.is_file():
                continue
            try:
                rq = json.loads(req.read_text())
            except Exception:
                continue
            if str(rq.get("ip") or "") != ns.ip:
                continue
            started = float(rq.get("created_at") or 0) or req.stat().st_mtime
            if started < since:
                continue
            wf = str(rq.get("template") or "")
            m = re.search(r"workflow: (\S+)", str(rq.get("context") or ""))
            if m:
                wf = m.group(1)
            if resp.is_file():
                try:
                    rs = json.loads(resp.read_text())
                except Exception:
                    continue
                dur = float(rs.get("duration_ms") or 0)
                status = str(rs.get("status") or "?")
                blob = str(rs.get("error") or "") + str((rs.get("result") or {}).get("result") or "")[:4000]
                klass = "ok" if status == "completed" else _classify(blob)
            else:
                dur, status, klass = (time.time() - started) * 1000, "running", "running"
            by_class[(wf, klass)]["n"] += 1
            by_class[(wf, klass)]["ms"] += dur
            job_rows.append((dur, wf, status, klass, d.name))

    print(f"\n== worker jobs for {ns.ip} (wall time by workflow × outcome) ==")
    tot_ms = sum(b["ms"] for b in by_class.values())
    print(f"  total: {len(job_rows)} jobs · {_fmt_s(tot_ms)} wall")
    for (wf, klass), b in sorted(by_class.items(), key=lambda kv: -kv[1]["ms"])[: ns.top]:
        print(f"  {wf:<16} {klass:<18} {b['n']:>3} jobs  {_fmt_s(b['ms']):>8}")

    print(f"\n== slowest {min(ns.top, len(job_rows))} jobs ==")
    for dur, wf, status, klass, job in sorted(job_rows, reverse=True)[: ns.top]:
        print(f"  {_fmt_s(dur):>8}  {wf:<16} {status:<10} {klass:<18} {job}")

    # ---------------- orchestrator runs ----------------
    runs = db.execute(
        "SELECT r.* FROM orchestrator_runs r JOIN ip_blocks i ON i.id = r.ip_id "
        "WHERE i.ip_name = ? AND r.started_at >= ? ORDER BY r.started_at",
        (ns.ip, since),
    ).fetchall()
    if not runs:
        runs = db.execute(
            "SELECT * FROM orchestrator_runs WHERE ip_id = ? AND started_at >= ? ORDER BY started_at",
            (ns.ip, since),
        ).fetchall()
    print(f"\n== orchestrator runs ({len(runs)}) ==")
    for r in runs:
        dur = ((r["ended_at"] or time.time()) - r["started_at"]) * 1000 if r["started_at"] else 0
        print(f"  {str(r['id'])[:8]}  {r['model']:<9} {str(r['status']):<10} {_fmt_s(dur):>8}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
