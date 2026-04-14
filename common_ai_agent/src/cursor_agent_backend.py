"""
cursor_agent_backend.py — route LLM calls through the cursor-agent CLI.

Stream-json chunk schema (confirmed by testing):
  {"type":"system","subtype":"init",...}          — capture model name
  {"type":"user",...}                             — skip
  {"type":"assistant","message":{"content":[{"type":"text","text":"..."}]},
   "timestamp_ms": <int>}                         — delta chunk, yield text
  {"type":"assistant","message":{"content":[{"type":"text","text":"..."}]}}
                                                  — final aggregated text, skip (no timestamp_ms)
  {"type":"tool_call","subtype":"started","tool_call":{...}}
                                                  — tool call; translate updateTodosToolCall
  {"type":"result","subtype":"success","result":"...",
   "usage":{"inputTokens":N,"outputTokens":N,"cacheReadTokens":N,"cacheWriteTokens":N}}
                                                  — done; read usage

Usage:
  from src.cursor_agent_backend import cursor_agent_stream, cursor_agent_call
"""

import json
import subprocess
import sys
from typing import Generator, Iterator, List, Dict, Optional, Tuple

# ---------------------------------------------------------------------------
# Todo translation state
# ---------------------------------------------------------------------------

_CURSOR_STATUS_MAP = {
    "TODO_STATUS_IN_PROGRESS": "in_progress",
    "TODO_STATUS_PENDING":     "pending",
    "TODO_STATUS_DONE":        "completed",
    "TODO_STATUS_CANCELLED":   "completed",
}

_CURSOR_PRIORITY_MAP = {
    "TODO_PRIORITY_HIGH":   "high",
    "TODO_PRIORITY_MEDIUM": "medium",
    "TODO_PRIORITY_LOW":    "low",
}

_STATUS_RANK = {
    "pending":     0,
    "in_progress": 1,
    "completed":   2,
    "approved":    3,
}

_STATUS_ICON = {
    "pending":     "○",
    "in_progress": "◉",
    "completed":   "✓",
    "approved":    "✅",
}

# Track previous raw cursor status per task to detect IN_PROGRESS → PENDING
# (cursor-agent resets completed tasks to PENDING instead of DONE)
_prev_todo_statuses: dict = {}   # {content: raw_cursor_status}

# Track highest effective status ever emitted per task to prevent downgrades
# (cursor-agent sends the full list on every update, resetting done tasks to PENDING)
_emitted_statuses: dict = {}     # {content: effective_status}


def _translate_update_todos(tool_call_val: dict) -> str:
    """Translate cursor-agent's updateTodosToolCall → Action: text.

    cursor-agent fires updateTodosToolCall as a stream event instead of
    outputting Action: lines. We translate it here so the ReAct loop can
    parse and execute it against common_ai_agent's own todo tracker.

    cursor-agent makes its own approval judgment via text output
    ("Action: todo_update(index=N, status='approved')") after reviewing work.
    We only emit completed here; approved comes from cursor-agent's review text.
    """
    args      = tool_call_val.get("args", {})
    todos_raw = args.get("todos", [])
    merge     = args.get("merge", False)

    todos = []
    for t in todos_raw:
        raw_status   = t.get("status", "TODO_STATUS_PENDING")
        raw_priority = t.get("priority", "")
        content      = t.get("content", "")

        # Detect IN_PROGRESS → PENDING: cursor-agent's signal for "task done"
        prev = _prev_todo_statuses.get(content, "")
        if raw_status == "TODO_STATUS_PENDING" and prev == "TODO_STATUS_IN_PROGRESS":
            status = "completed"
        else:
            status = _CURSOR_STATUS_MAP.get(raw_status, "pending")
        _prev_todo_statuses[content] = raw_status

        # Downgrade guard: keep highest rank already emitted (cursor-agent batch-resets
        # completed tasks to PENDING when updating other tasks in the same call)
        best = _emitted_statuses.get(content, "")
        if best and _STATUS_RANK.get(status, 0) < _STATUS_RANK.get(best, 0):
            status = best

        todos.append({
            "content":  content,
            "status":   status,
            "priority": _CURSOR_PRIORITY_MAP.get(raw_priority, "medium"),
        })

    if not todos:
        return ""

    if merge:
        lines = []
        for i, t in enumerate(todos, start=1):
            content = t["content"]
            status  = t["status"]
            if status == _emitted_statuses.get(content):
                continue  # no-op, skip
            icon  = _STATUS_ICON.get(status, "•")
            short = content[:40] + "…" if len(content) > 40 else content
            lines.append(f'\n[{icon} Task {i}: {short} → {status}]')
            lines.append(f'\nAction: todo_update(index={i}, status="{status}")')
            _emitted_statuses[content] = status
        return "".join(lines)
    else:
        _prev_todo_statuses.clear()
        _emitted_statuses.clear()
        n = len(todos)
        todos_json = json.dumps(todos, ensure_ascii=False)
        return f"\n[todo_write: {n} task{'s' if n != 1 else ''}]\nAction: todo_write(todos={todos_json})"


# ---------------------------------------------------------------------------
# Tool call display
# ---------------------------------------------------------------------------

def _parse_tool_call(tool_call_dict: dict) -> Tuple[str, str]:
    """Extract (tool_name, detail) from a cursor-agent tool_call dict."""
    for key, val in tool_call_dict.items():
        name = key.replace("ToolCall", "")
        args = val.get("args", {}) if isinstance(val, dict) else {}
        detail = args.get("path") or args.get("file_path") or args.get("command", "")[:60]
        return name, str(detail) if detail else ""
    return "tool", ""


# ---------------------------------------------------------------------------
# Model tracking
# ---------------------------------------------------------------------------

# Human-readable model label from cursor-agent's system/init event.
# e.g. "Auto", "Sonnet 4.6 1M", "Composer 2 Fast"
last_cursor_model: str = ""


# ---------------------------------------------------------------------------
# Message serialization
# ---------------------------------------------------------------------------

def _extract_text(content) -> str:
    """Flatten OpenAI content (str or list of blocks) to plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
                elif block.get("type") == "tool_result":
                    parts.append(_extract_text(block.get("content", "")))
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts)
    return str(content) if content is not None else ""


def serialize_messages(messages: List[Dict]) -> str:
    """Convert OpenAI-format messages → single prompt string for cursor-agent -p.

    Structure:
      [SYSTEM]
      <system content>

      [CONVERSATION HISTORY]
      <role>: <content>
      ...

      [CURRENT REQUEST]
      <last user message>
    """
    system_parts  = []
    history_parts = []
    non_system    = []

    for msg in messages:
        if msg.get("role") == "system":
            system_parts.append(_extract_text(msg.get("content", "")))
        else:
            non_system.append(msg)

    last_user_idx = max(
        (i for i, m in enumerate(non_system) if m.get("role") == "user"),
        default=-1,
    )

    last_user_msg = ""
    for i, msg in enumerate(non_system):
        role    = msg.get("role", "")
        content = msg.get("content", "")

        if i == last_user_idx:
            last_user_msg = _extract_text(content)
            continue

        if role == "assistant":
            tool_calls = msg.get("tool_calls", [])
            if tool_calls:
                tc_summary = ", ".join(
                    f"{tc.get('function', {}).get('name', '?')}(...)"
                    for tc in tool_calls
                )
                history_parts.append(f"Assistant [tool calls]: {tc_summary}")
            else:
                text = _extract_text(content)
                if text.strip():
                    history_parts.append(f"Assistant: {text}")
        elif role == "tool":
            text = _extract_text(content)
            history_parts.append(f"Tool result ({msg.get('tool_call_id', '')}): {text}")
        elif role == "user":
            text = _extract_text(content)
            if text.strip():
                history_parts.append(f"User: {text}")

    sections = []
    if system_parts:
        sections.append("[SYSTEM]\n" + "\n\n".join(system_parts))
    if history_parts:
        sections.append("[CONVERSATION HISTORY]\n" + "\n".join(history_parts))
    sections.append("[CURRENT REQUEST]\n" + last_user_msg)
    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# Subprocess helpers
# ---------------------------------------------------------------------------

def _build_cmd(model: str, yolo: bool, mode: str, workspace: str) -> List[str]:
    cmd = ["cursor-agent", "--model", model or "auto"]
    if yolo:
        cmd.append("--yolo")
    if mode:
        cmd += ["--mode", mode]
    if workspace:
        cmd += ["--workspace", workspace]
    return cmd


def _iter_chunks(proc) -> Iterator[dict]:
    """Yield parsed JSON chunks from cursor-agent subprocess stdout."""
    for raw_line in proc.stdout:
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        try:
            yield json.loads(raw_line)
        except json.JSONDecodeError:
            continue


def _handle_chunk(chunk: dict, lc) -> Optional[str]:
    """Process one stream-json chunk.

    Returns a text string to emit, or None if nothing to emit.
    Side effects: updates last_cursor_model and lc token counters.
    """
    global last_cursor_model
    chunk_type = chunk.get("type")

    if chunk_type == "system" and chunk.get("subtype") == "init":
        last_cursor_model = chunk.get("model", "")
        return None

    if chunk_type == "assistant" and "timestamp_ms" in chunk:
        parts = []
        for block in chunk.get("message", {}).get("content", []):
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "".join(parts) or None

    if chunk_type == "tool_call" and chunk.get("subtype") == "started":
        tc = chunk.get("tool_call", {})
        if "updateTodosToolCall" in tc:
            text = _translate_update_todos(tc["updateTodosToolCall"])
            return text or None
        tool_name, detail = _parse_tool_call(tc)
        return f"\n[{tool_name}" + (f": {detail}" if detail else "") + "]"

    if chunk_type == "result":
        usage = chunk.get("usage", {})
        lc.last_input_tokens  = usage.get("inputTokens", 0) + usage.get("cacheReadTokens", 0)
        lc.last_output_tokens = usage.get("outputTokens", 0)
        return None

    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def cursor_agent_stream(
    messages:  List[Dict],
    model:     str  = "auto",
    yolo:      bool = False,
    mode:      str  = "",
    workspace: str  = "",
) -> Generator[str, None, None]:
    """Stream text chunks from cursor-agent, mirroring chat_completion_stream()."""
    import src.llm_client as _lc

    cmd = _build_cmd(model, yolo, mode, workspace) + [
        "--print", "--output-format", "stream-json",
        "--stream-partial-output", "-p", serialize_messages(messages),
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, bufsize=1)
    try:
        for chunk in _iter_chunks(proc):
            text = _handle_chunk(chunk, _lc)
            if text:
                yield text
    finally:
        proc.stdout.close()
        proc.wait()
        if proc.returncode != 0:
            stderr = proc.stderr.read() if proc.stderr else ""
            if stderr.strip():
                yield f"\n[cursor-agent error: {stderr.strip()}]"


def cursor_agent_call(
    messages:      List[Dict],
    model:         str  = "auto",
    yolo:          bool = False,
    mode:          str  = "",
    workspace:     str  = "",
    stream_prefix: Optional[str] = None,
) -> str:
    """Collect full cursor-agent response as a string, mirroring call_llm_raw()."""
    import src.llm_client as _lc

    cmd = _build_cmd(model, yolo, mode, workspace) + [
        "--print", "--output-format", "stream-json",
        "--stream-partial-output", "-p", serialize_messages(messages),
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, bufsize=1)
    collected = []
    try:
        for chunk in _iter_chunks(proc):
            text = _handle_chunk(chunk, _lc)
            if text:
                collected.append(text)
                if stream_prefix is not None:
                    sys.stdout.write(stream_prefix + text)
                    sys.stdout.flush()
    finally:
        proc.stdout.close()
        proc.wait()
    return "".join(collected)
