from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable


TERMINAL_SUPERVISOR_STATUSES = {"completed", "blocked", "error", "cancelled"}


def watch_supervisor_job(
    *,
    db: Any,
    job_id: str,
    process_key: str,
    run_id: str,
    response_path: Path,
    proc: Any,
    update_job: Callable[[str, dict[str, Any]], None],
    unregister_process: Callable[[str], None],
) -> None:
    try:
        rc = proc.wait()
    except Exception:
        rc = -1
    unregister_process(process_key)
    data = read_supervisor_response(response_path)
    status = str(data.get("status") or ("completed" if rc == 0 else "error"))
    updates = {"status": status, "finished_at": time.time(), "returncode": rc}
    if data.get("error"):
        updates["error"] = str(data.get("error"))
    update_job(job_id, updates)
    if status in TERMINAL_SUPERVISOR_STATUSES:
        db.update_orchestrator_run(run_id, status=status, ended=True)


def read_supervisor_response(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}
