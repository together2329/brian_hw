#!/usr/bin/env python3
"""Watch the three triple-LLM runs and emit COMPARISON.md when all three end.

Polls the three sandbox run.json files (the headless workflow's stdout
JSON dump) and the per-IP `logs/headless_run.json` written by `_finish()`.
When all three sandboxes have a final-status JSON, runs `compare_runs.py`
and exits.

This is the synchronous waiter — meant to be launched once in the
background so the foreground assistant turn can hand off to a single
auto-notification instead of polling three independent backgrounds.
"""
from __future__ import annotations
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROVIDERS = ("codex", "claude", "cursor")
TIMEOUT_S = 4 * 60 * 60   # 4-hour ceiling so the watcher never hangs forever
POLL_S = 30


def _run_status(prov: str) -> str:
    """Return final overall status if the sandbox has a complete run.json."""
    rj = ROOT / prov / "run.json"
    if not rj.is_file() or rj.stat().st_size == 0:
        return ""
    try:
        doc = json.loads(rj.read_text(encoding="utf-8"))
    except Exception:
        return ""
    status = str(doc.get("status") or "")
    stages = doc.get("stages") or []
    if status in {"pass", "fail", "blocked"} and isinstance(stages, list) and len(stages) >= 1:
        return status
    return ""


def main() -> int:
    print(f"[wait_and_compare] watching {PROVIDERS}, poll={POLL_S}s, ceiling={TIMEOUT_S//60}min", flush=True)
    deadline = time.time() + TIMEOUT_S
    last_state: dict[str, str] = {p: "" for p in PROVIDERS}
    while True:
        statuses = {p: _run_status(p) for p in PROVIDERS}
        if statuses != last_state:
            ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            print(f"[{ts}] " + " ".join(f"{p}={s or '...'}" for p, s in statuses.items()), flush=True)
            last_state = dict(statuses)
        if all(s for s in statuses.values()):
            break
        if time.time() >= deadline:
            print("[wait_and_compare] ceiling reached; producing partial COMPARISON.md", flush=True)
            break
        time.sleep(POLL_S)
    cmp_path = ROOT / "compare_runs.py"
    print(f"[wait_and_compare] running {cmp_path.name}", flush=True)
    rc = subprocess.run(["python3", str(cmp_path)], cwd=str(ROOT)).returncode
    print(f"[wait_and_compare] compare_runs.py exit={rc}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
