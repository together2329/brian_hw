"""History compaction helpers — extracted from src/atlas_ui.py.

Self-contained: web `/compact` LLM-based history compaction and the JSON
fallback. Used by the textual + web sessions to reduce conversation size
without losing critical context. Phase 3 of refactor/atlas-modular.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Callable, Optional


def _hydrate_atlas_ui_helpers() -> None:
    """One-time backport of atlas_ui helpers Phase 3 didn't bring along.

    `_compact_history_file` / `_compact_history_llm` bodies call into 3
    atlas_ui helpers (`_parse_compact_history_signal`,
    `_history_message_preview`, `_write_history_json`) via bare-name
    resolution. atlas_ui imports us at its line 401, so a top-level
    back-import would be circular. Lazy import + idempotent module-global
    backfill fixes the `/compact` slash command which was raising
    NameError at call time.
    """
    g = globals()
    if g.get("_AUI_HYDRATED"):
        return
    from src import atlas_ui as _aui
    for name in ("_parse_compact_history_signal", "_history_message_preview", "_write_history_json"):
        if hasattr(_aui, name):
            g[name] = getattr(_aui, name)
    g["_AUI_HYDRATED"] = True


def _load_history_json(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        return []
    return [m for m in raw if isinstance(m, dict)]

def _compact_history_file(path: Path, signal: str) -> tuple[str, list[dict[str, Any]]]:
    """Apply Web UI /compact to a local .session conversation file.

    The CLI compactor uses the live agent loop. The Web command plane is
    outside that loop, so this deterministic local compactor avoids returning
    the raw COMPACT_HISTORY token or blocking the UI on a second LLM call.
    """
    _hydrate_atlas_ui_helpers()
    messages = _load_history_json(path)
    system_msgs = [m for m in messages if m.get("role") == "system"]
    active_msgs = [m for m in messages if m.get("role") != "system"]
    keep_recent, dry_run, instruction = _parse_compact_history_signal(signal)
    keep_recent = min(keep_recent, len(active_msgs))
    old_msgs = active_msgs[: len(active_msgs) - keep_recent] if keep_recent else active_msgs
    recent_msgs = active_msgs[len(active_msgs) - keep_recent:] if keep_recent else []

    if not old_msgs:
        return (
            f"History is already compact: {len(active_msgs)} non-system message(s), "
            f"keeping {keep_recent}.",
            messages,
        )

    preview_lines = [
        f"- {_history_message_preview(m)}"
        for m in old_msgs[:20]
    ]
    omitted = len(old_msgs) - len(preview_lines)
    if omitted > 0:
        preview_lines.append(f"- ... {omitted} older message(s) omitted from this local summary")
    summary = [
        f"[Previous Conversation Summary ({len(old_msgs)} messages, local web compact)]:",
        f"Compacted from {path.as_posix()} at {time.strftime('%Y-%m-%d %H:%M:%S')}.",
    ]
    if instruction:
        summary.append(f"Instruction: {instruction}")
    summary.extend(["", "Older message preview:", *preview_lines])
    compacted = system_msgs + [{"role": "system", "content": "\n".join(summary)}] + recent_msgs

    msg = (
        f"Compacted local session history: {len(messages)} -> {len(compacted)} message(s); "
        f"summarized {len(old_msgs)}, kept {len(recent_msgs)} recent."
    )
    if dry_run:
        return "Dry run: " + msg, messages
    _write_history_json(path, compacted)
    return msg, compacted

def _default_web_compress_fn(messages: list[dict[str, Any]], **kwargs):
    """Real LLM compaction — the SAME path the CLI / Textual UI use.

    Delegates to core.compressor.compress_history with the web server's config
    and streaming LLM client injected (mirrors src/main.py's wrapper). Raises on
    import/LLM failure so the caller can fall back to the deterministic local
    compactor.
    """
    from core.compressor import compress_history as _impl
    try:
        import src.config as _cfg  # noqa: WPS433
    except Exception:  # pragma: no cover - import path differs by entrypoint
        import config as _cfg  # type: ignore  # noqa: WPS433
    try:
        from src.llm_client import (
            chat_completion_stream as _stream,
            estimate_message_tokens as _est,
            get_actual_tokens as _act,
        )
    except Exception:  # pragma: no cover
        from llm_client import (  # type: ignore
            chat_completion_stream as _stream,
            estimate_message_tokens as _est,
            get_actual_tokens as _act,
        )
    return _impl(
        messages,
        cfg=_cfg,
        llm_call_fn=_stream,
        estimate_tokens_fn=_est,
        get_actual_tokens_fn=_act,
        **kwargs,
    )

def _compact_history_llm(
    path: Path, signal: str, *, compress_fn=None
) -> tuple[str, list[dict[str, Any]]]:
    """Apply Web UI /compact using the real LLM compactor (Textual-equivalent).

    Loads the session conversation file, runs `compress_history` (AI summary that
    preserves working paths / code / todos), and persists the result. `compress_fn`
    is injectable for tests; it defaults to the live LLM path.
    """
    _hydrate_atlas_ui_helpers()
    messages = _load_history_json(path)
    keep_recent, dry_run, instruction = _parse_compact_history_signal(signal)
    if compress_fn is None:
        compress_fn = _default_web_compress_fn
    emitted: list[str] = []
    compacted = compress_fn(
        messages,
        force=True,
        instruction=(instruction or None),
        keep_recent=keep_recent,
        dry_run=dry_run,
        quiet=True,
        emit_fn=lambda text: emitted.append(str(text or "")),
    )
    if not isinstance(compacted, list) or not compacted:
        raise RuntimeError("compressor returned no messages")
    if emitted and "".join(emitted).strip():
        msg = "".join(emitted).rstrip()
    elif len(compacted) >= len(messages):
        msg = (
            f"History already compact (AI summary): {len(messages)} message(s); "
            "no reduction needed."
        )
    elif dry_run:
        msg = f"Dry run: AI summary would compact {len(messages)} -> {len(compacted)} message(s)."
    else:
        msg = f"Compacted history with AI summary: {len(messages)} -> {len(compacted)} message(s)."
    if not dry_run:
        _write_history_json(path, compacted)
    return msg, compacted
