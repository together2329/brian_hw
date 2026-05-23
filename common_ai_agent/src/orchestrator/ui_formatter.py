"""Render orchestrator tool calls as raw terminal-style lines.

The DB-polled Atlas chat replays these rows after reconnects, so this module
must preserve the structured call shape instead of translating it into a
status summary.
"""

from __future__ import annotations

import json
from typing import Any, Dict


_MAX_VALUE_CHARS = 700
_MAX_LINE_CHARS = 2_400


def _truncate(text: str, limit: int = _MAX_VALUE_CHARS) -> str:
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)] + "..."


def _render_value(value: Any) -> str:
    try:
        rendered = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    except TypeError:
        rendered = json.dumps(str(value), ensure_ascii=False)
    return _truncate(rendered)


def _render_args(args: Dict[str, Any]) -> str:
    if not isinstance(args, dict) or not args:
        return ""
    return ", ".join(f"{key}={_render_value(value)}" for key, value in args.items())


def format_tool_call(tool_name: str, args: Dict[str, Any]) -> str:
    """Render ``(tool_name, args)`` without summarizing or translating it."""
    name = str(tool_name or "tool").strip() or "tool"
    rendered_args = _render_args(args if isinstance(args, dict) else {})
    line = f"⏺ {name}({rendered_args})"
    return _truncate(line, _MAX_LINE_CHARS)
