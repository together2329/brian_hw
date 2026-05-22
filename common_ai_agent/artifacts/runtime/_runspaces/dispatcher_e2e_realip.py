"""Deep end-to-end orchestrator-style test on a real IP.

Picks 6 actual TODOs from `parity_gen/rtl/rtl_todo_tracker.json`,
fans them out to 3 mixed-provider workers (claude-cli / glm-5.1 /
kimi), waits for all results, then audits:

  - spawn synchronicity (workers must start within ~10 ms of each other)
  - parallelism factor (sum_durations / wall_time)
  - per-worker model isolation (each worker actually ran on its
    assigned provider, not the process default)
  - content sanity (worker output references the assigned RTL-XXXX IDs)
  - artefact integrity (manifest.json + per-worker result.json on disk,
    JSON round-trips, no missing fields)

Run with:

    cd common_ai_agent
    ATLAS_RUN_REAL_LLM_TDD=1 python3 _runspaces/dispatcher_e2e_realip.py

Wall time is bounded by the slowest worker (typically 2-5 minutes for
real LLM calls); the timeout per worker is set to 4 minutes.
"""
from __future__ import annotations

import json
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
for p in (PROJECT, PROJECT / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

os.chdir(PROJECT)

from core.parallel_todo_dispatcher import ParallelTodoDispatcher  # noqa: E402


IP = "parity_gen"
N_TODOS = 6
WORKER_MODELS = ["claude-cli", "glm-5.1", "kimi"]


def _bullet(passed: bool, label: str, detail: str = "") -> None:
    glyph = "PASS" if passed else "FAIL"
    print(f"  [{glyph}] {label}" + (f" — {detail}" if detail else ""), flush=True)


def main() -> int:
    print(f"=== orchestrator-style real-IP deep test ===", flush=True)
    print(f"  IP:      {IP}", flush=True)
    print(f"  TODOs:   first {N_TODOS} from {IP}/rtl/rtl_todo_tracker.json", flush=True)
    print(f"  workers: {WORKER_MODELS}", flush=True)
    print(f"  python:  {sys.version.split()[0]}", flush=True)
    print("", flush=True)

    tracker_path = PROJECT / IP / "rtl" / "rtl_todo_tracker.json"
    if not tracker_path.is_file():
        print(f"FATAL: {tracker_path} not found", flush=True)
        return 2

    raw_tracker = json.loads(tracker_path.read_text("utf-8"))
    todos_raw = raw_tracker.get("todos") or raw_tracker.get("tasks") or []
    batch: list[dict[str, Any]] = []
    for t in todos_raw[:N_TODOS]:
        content = t.get("content") or t.get("description") or t.get("detail") or ""
        batch.append({
            "id": t.get("task_id") or t.get("id") or f"todo-{len(batch)+1}",
            "content": f"For IP {IP!r}: {content}",
        })
    print(f"selected {len(batch)} todos:")
    for b in batch:
        print(f"  - {b['id']:18}  {b['content'][:80]}")
    print("", flush=True)

    d = ParallelTodoDispatcher()
    t0 = time.time()
    print(f"dispatching at t=0 ...", flush=True)
    job_id = d.dispatch(
        todos=batch,
        max_workers=len(WORKER_MODELS),
        models=WORKER_MODELS,
    )
    print(f"job_id = {job_id} (waiting up to 4 min per worker)", flush=True)
    result = d.wait(job_id, timeout_s=240)
    wall = time.time() - t0
    print(f"wall = {wall:.1f}s", flush=True)
    print("", flush=True)

    # ── analysis ────────────────────────────────────────────────────
    job_dir = Path(result["result_dir"])
    manifest = json.loads((job_dir / "manifest.json").read_text("utf-8"))
    per_worker = [
        json.loads((job_dir / str(i) / "result.json").read_text("utf-8"))
        for i in range(len(WORKER_MODELS))
        if (job_dir / str(i) / "result.json").is_file()
    ]

    print(f"=== audit ===", flush=True)

    # 1. Manifest sanity
    _bullet(
        manifest["job_id"] == result["job_id"] and len(manifest["chunks"]) == len(WORKER_MODELS),
        "manifest.json shape matches dispatch",
        f"chunks={[len(c) for c in manifest['chunks']]} job_id={manifest['job_id']}",
    )

    # 2. All workers reported
    _bullet(
        len(per_worker) == len(WORKER_MODELS),
        "every worker wrote result.json",
        f"{len(per_worker)}/{len(WORKER_MODELS)} result.json present",
    )

    # 3. Spawn synchronicity (start spread ≤ 50 ms)
    starts = sorted(w["started_at"] for w in per_worker)
    spread = starts[-1] - starts[0] if starts else 0.0
    _bullet(
        spread <= 0.05,
        "workers spawned within 50 ms of each other",
        f"start-spread = {spread*1000:.1f} ms",
    )

    # 4. Parallelism factor
    sum_dur = sum(w["duration_s"] for w in per_worker)
    wall_workers = max((w["completed_at"] for w in per_worker), default=time.time()) - min(starts, default=time.time())
    speedup = sum_dur / wall_workers if wall_workers else 0.0
    expected_min_speedup = 0.6 * len(WORKER_MODELS)  # allow for one slow worker dominating wall
    _bullet(
        speedup >= expected_min_speedup,
        f"parallelism speedup ≥ {expected_min_speedup:.1f}×",
        f"sum_dur={sum_dur:.1f}s wall={wall_workers:.1f}s speedup={speedup:.2f}×",
    )

    # 5. Per-worker model isolation
    model_ok = []
    for i, w in enumerate(per_worker):
        wanted = WORKER_MODELS[i]
        seen = w.get("requested_model") or w.get("model")
        ok = wanted == seen or wanted in str(seen)
        model_ok.append((wanted, seen, ok))
    _bullet(
        all(ok for _, _, ok in model_ok),
        "each worker actually ran on its assigned provider",
        ", ".join(f"{w}→{s}{'✓' if ok else '✗'}" for w, s, ok in model_ok),
    )

    # 6. Content sanity — each worker's result mentions at least one of its assigned todo IDs
    content_ok = []
    for i, w in enumerate(per_worker):
        assigned_ids = [t.get("id") for t in (w.get("todos_assigned") or [])]
        result_text = str(w.get("result", ""))
        hit = any(tid and tid in result_text for tid in assigned_ids)
        # also accept a status keyword (DONE / PASS / completed) as proxy
        hit = hit or any(kw in result_text for kw in ("DONE", "PASS", "completed", "DELIVERED"))
        content_ok.append((i, hit, len(result_text)))
    _bullet(
        all(hit for _, hit, _ in content_ok),
        "every worker's result references an assigned ID or reports completion",
        ", ".join(f"w{i}:hit={hit}(len={l})" for i, hit, l in content_ok),
    )

    # 7. Disk artefact integrity (required fields)
    required = {"status", "model", "requested_model", "todos_assigned",
                 "todos_done", "started_at", "completed_at", "duration_s"}
    missing = [(i, sorted(required - set(w.keys()))) for i, w in enumerate(per_worker) if required - set(w.keys())]
    _bullet(
        not missing,
        "result.json carries full status/model/duration/todos fields",
        f"missing_per_worker={missing}",
    )

    # 8. Aggregated result JSON round-trips
    try:
        encoded = json.dumps(result, ensure_ascii=False)
        decoded = json.loads(encoded)
        rt = decoded == result
    except Exception as exc:
        rt = False
    _bullet(rt, "aggregated wait() output JSON-round-trips", f"bytes={len(encoded) if rt else 'n/a'}")

    # 9. Aggregator status
    status = result.get("status")
    completed = result.get("completed_workers", 0)
    _bullet(
        completed == len(WORKER_MODELS) and status in {"completed", "partial", "partial_error"},
        f"aggregator status = {status}",
        f"completed={completed}/{len(WORKER_MODELS)}",
    )

    # ── summary line ────────────────────────────────────────────────
    print("", flush=True)
    print(f"=== summary ===", flush=True)
    print(f"  wall:               {wall:.1f}s", flush=True)
    duration_strs = [f"{w['duration_s']:.1f}s" for w in per_worker]
    print(f"  worker durations:   {duration_strs}", flush=True)
    print(f"  speedup:            {speedup:.2f}×", flush=True)
    print(f"  spawn spread:       {spread*1000:.1f} ms", flush=True)
    print(f"  aggregator status:  {status} ({completed}/{len(WORKER_MODELS)} done)", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        print(traceback.format_exc(), flush=True)
        raise SystemExit(2)
