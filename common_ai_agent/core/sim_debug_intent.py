"""core/sim_debug_intent.py — tool→browser channel for the Sim Debug panel.

The agent `sim_debug` tool runs server-side (possibly in a worker process); the
Sim Debug waveform UI lives in the browser. They communicate through a single
small JSON file under `.session/` (gitignored, runtime-writable, process-
agnostic). The tool `push_intent(...)`s the latest navigation/show/trace action;
the `/api/sim_debug/intent` route reads it back via `get_intent()`; the panel
polls that route and applies the intent when the `seq` increases.

Only the LATEST intent is kept. Each intent carries the target `ip`; the UI
applies it only when the ip matches the panel's active IP (or is blank).
"""
from __future__ import annotations

import json
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Dict

_LOCK = threading.Lock()

# Actions the Sim Debug panel knows how to apply
# (see frontend/atlas/sim-debug-intent-hook.tsx).
VALID_ACTIONS = frozenset({
    "show", "goto", "cursor", "trace", "fit", "reorder", "group", "ungroup",
    "color", "radix", "remove", "keep", "clear", "fold", "unfold",
})


def _project_root() -> Path:
    """Same basis the FastAPI app uses (src/atlas_ui.py: Path(os.getcwd())),
    honouring ATLAS_PROJECT_ROOT so tool and API resolve the identical file."""
    return Path(os.environ.get("ATLAS_PROJECT_ROOT") or os.getcwd())


def _intent_path(base_root: "str | Path | None" = None) -> Path:
    root = Path(base_root) if base_root else _project_root()
    return root / ".session" / "sim_debug_intent.json"


def push_intent(ip: str, action: str, base_root: "str | Path | None" = None, **fields: Any) -> int:
    """Write the latest Sim Debug intent and return its monotonic `seq`.

    `fields` may include: signals(list[str]), signal(str), t_start, t_end,
    cursor_a, cursor_b, note. Unknown/None fields are dropped. ``base_root``
    overrides the project root (defaults to ATLAS_PROJECT_ROOT/cwd, which under
    process_per_session is already the worker's session workspace root).
    """
    seq = time.time_ns()
    intent: Dict[str, Any] = {
        "seq": seq,
        "ip": str(ip or "").strip(),
        "action": str(action or "").strip(),
        "ts": time.time(),
    }
    for k, v in fields.items():
        if v is not None:
            intent[k] = v
    path = _intent_path(base_root)
    with _LOCK:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            # Atomic replace so a concurrent reader never sees a half-written file.
            fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".sdintent", suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    json.dump(intent, fh)
                os.replace(tmp, path)
            except Exception:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
                raise
        except OSError:
            # Best-effort channel; never break the tool call on a write failure.
            pass
    return seq


def get_intent(ip: str = "", base_root: "str | Path | None" = None) -> Dict[str, Any]:
    """Return the latest intent (any ip — the UI filters by ip itself), or
    {"seq": 0} when none has been pushed.

    ``base_root`` overrides the project root so the web API can read the intent
    from the requesting session's workspace root (the agent worker, running
    process_per_session, writes it there — not under the web process root)."""
    path = _intent_path(base_root)
    with _LOCK:
        if not path.is_file():
            return {"seq": 0}
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except (OSError, json.JSONDecodeError):
            return {"seq": 0}
    if not isinstance(data, dict) or "seq" not in data:
        return {"seq": 0}
    return data
