"""Append-only trace log for orchestrator + worker interactions.

Every actor (orchestrator, individual workers) writes one JSON line per event
to ``<ip>/orchestrator/trace.jsonl``. The schema is intentionally tiny so the
log can be consumed by ``tail -f``, ``jq``, the Pipeline UI strip, and
postmortem replay tooling without parsing custom formats.

Event schema (one JSON object per line):

    {
      "ts":     "2026-05-17T14:23:01.234Z",      # ISO-8601 with millis
      "step":   3,                                # monotonic per ip (best-effort)
      "lens":   "interaction"|"intermediate"|"result",
      "actor":  "orchestrator"|"ssot-gen-worker"|...,
      "peer":   "<peer actor>" (optional, for interactions),
      "kind":   "http_send"|"http_response"|"http_rejected"|
                "llm_decision"|"llm_stream"|"tool_call"|
                "gate_verdict"|"gate_read"|"routing"|"retry"|"escalate",
      "corr":   "corr_<8hex>",                   # correlation id linking related events
      # kind-specific keys follow (status, run_id, payload, reasoning, ...)
    }

Hard constraints:
- never raise from writer paths; tracing must not break the call site
- caller chooses the lens/kind; this module only handles serialization
- file lock not required since each line is atomic on POSIX append
"""
from __future__ import annotations

import json
import os
import secrets
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

_DEFAULT_DIR_NAME = "orchestrator"
_DEFAULT_FILE_NAME = "trace.jsonl"
_STEP_LOCK = threading.Lock()
_STEP_COUNTERS: dict[str, int] = {}


def new_corr() -> str:
    """Return a fresh correlation id for grouping related trace events."""
    return f"corr_{secrets.token_hex(4)}"


def _resolve_root(project_root: Path | str | None = None) -> Path:
    """Resolve the project root from env (set by main.py / agent_server.py)."""
    if project_root is not None:
        return Path(project_root)
    explicit = os.environ.get("ATLAS_PROJECT_ROOT", "").strip()
    if explicit:
        return Path(explicit)
    return Path.cwd()


def _ip_dir(ip: str, project_root: Path | str | None = None) -> Path:
    """Return ``<project_root>/<ip>/<_DEFAULT_DIR_NAME>``."""
    ip = (ip or "_unknown").strip() or "_unknown"
    return _resolve_root(project_root) / ip / _DEFAULT_DIR_NAME


def _trace_path(ip: str, project_root: Path | str | None = None) -> Path:
    return _ip_dir(ip, project_root) / _DEFAULT_FILE_NAME


def _next_step(ip: str) -> int:
    with _STEP_LOCK:
        cur = _STEP_COUNTERS.get(ip, 0) + 1
        _STEP_COUNTERS[ip] = cur
        return cur


def record_trace(
    ip: str,
    *,
    lens: str,
    actor: str,
    kind: str,
    project_root: Path | str | None = None,
    peer: Optional[str] = None,
    corr: Optional[str] = None,
    step: Optional[int] = None,
    **extra: Any,
) -> Optional[str]:
    """Append one event to ``<ip>/orchestrator/trace.jsonl``.

    Returns the correlation id used (newly minted if caller did not supply
    one), or ``None`` when writing failed.
    """
    if lens not in ("interaction", "intermediate", "result"):
        return None
    if not actor or not kind:
        return None
    corr = corr or new_corr()
    try:
        step_n = step if isinstance(step, int) and step > 0 else _next_step(ip or "_unknown")
        now_ms = int(time.time() * 1000) / 1000.0
        ts = datetime.fromtimestamp(now_ms, tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%S.") + f"{int((now_ms % 1) * 1000):03d}Z"
        record: dict[str, Any] = {
            "ts": ts,
            "step": step_n,
            "lens": lens,
            "actor": actor,
            "kind": kind,
            "corr": corr,
        }
        if peer:
            record["peer"] = peer
        for k, v in extra.items():
            if v is not None:
                record[k] = v
        target = _trace_path(ip, project_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record, ensure_ascii=False, default=str)
        with open(target, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        return corr
    except Exception:
        return None


def read_trace(
    ip: str,
    *,
    limit: int = 100,
    project_root: Path | str | None = None,
    corr: Optional[str] = None,
    lens: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Read trace events for ``ip``. Returns the most recent ``limit`` events,
    optionally filtered by correlation id or lens."""
    path = _trace_path(ip, project_root)
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if corr and rec.get("corr") != corr:
                    continue
                if lens and rec.get("lens") != lens:
                    continue
                out.append(rec)
    except Exception:
        return []
    if limit and len(out) > limit:
        out = out[-limit:]
    return out


def clear_trace(ip: str, project_root: Path | str | None = None) -> bool:
    """Remove the trace file for ``ip``. Returns True if removed or absent."""
    try:
        p = _trace_path(ip, project_root)
        if p.exists():
            p.unlink()
        with _STEP_LOCK:
            _STEP_COUNTERS.pop(ip, None)
        return True
    except Exception:
        return False
