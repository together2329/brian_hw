from __future__ import annotations

import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any

_SAFE_BRIDGE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,160}$")


def safe_bridge_id(value: Any, fallback: str = "invalid") -> str:
    candidate = str(value or "").strip()
    if _SAFE_BRIDGE_ID_RE.fullmatch(candidate):
        return candidate
    fallback_text = str(fallback or "").strip()
    if _SAFE_BRIDGE_ID_RE.fullmatch(fallback_text):
        return fallback_text
    return "invalid"


def write_json_atomic(path: Path, payload: dict[str, Any], *, create_parent: bool = True) -> None:
    parent = path.parent
    if parent.is_symlink():
        raise ValueError(f"JSON parent directory must not be a symlink: {parent}")
    if create_parent:
        parent.mkdir(parents=True, exist_ok=True)
    elif not parent.is_dir():
        raise ValueError(f"JSON parent directory must exist: {parent}")
    if parent.is_symlink():
        raise ValueError(f"JSON parent directory must not be a symlink: {parent}")
    if path.is_symlink():
        raise ValueError(f"JSON path must not be a symlink: {path}")

    tmp = parent / f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(tmp, flags, 0o600)
    replaced = False
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
        tmp.replace(path)
        replaced = True
    finally:
        if not replaced:
            try:
                tmp.unlink()
            except OSError:
                pass


def call_bridge(
    bridge_dir: str | Path,
    *,
    tool: str,
    kwargs: dict[str, Any],
    timeout_s: float = 60.0,
    token: str | None = None,
) -> dict[str, Any]:
    root = Path(bridge_dir)
    request_id = safe_bridge_id(f"{os.getpid()}-{time.time_ns()}-{uuid.uuid4().hex[:8]}")
    request_path = root / "requests" / f"{request_id}.json"
    response_path = root / "responses" / f"{request_id}.json"
    bridge_token = str(
        token if token is not None else os.environ.get("ATLAS_ORCHESTRATOR_TOOL_BRIDGE_TOKEN", "")
    )
    write_json_atomic(
        request_path,
        {
            "id": request_id,
            "tool": str(tool or ""),
            "kwargs": kwargs,
            "token": bridge_token,
            "created_at": time.time(),
        },
    )
    deadline = time.monotonic() + max(0.01, float(timeout_s or 60.0))
    while time.monotonic() < deadline:
        if response_path.is_file():
            try:
                data = json.loads(response_path.read_text(encoding="utf-8", errors="replace"))
                if isinstance(data, dict):
                    return data
                return {"ok": False, "error": "bridge response must be an object"}
            finally:
                try:
                    response_path.unlink()
                except OSError:
                    pass
        time.sleep(0.05)
    try:
        request_path.unlink()
    except OSError:
        pass
    return {
        "ok": False,
        "error": f"{tool} bridge timed out",
        "tool": str(tool or ""),
    }
