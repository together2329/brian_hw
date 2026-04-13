"""
cursor_agent_backend.py — route LLM calls through the cursor-agent CLI.

Stream-json chunk schema (confirmed by testing):
  {"type":"system","subtype":"init",...}          — skip
  {"type":"user",...}                             — skip
  {"type":"assistant","message":{"content":[{"type":"text","text":"..."}]},
   "timestamp_ms": <int>}                         — delta chunk, yield text
  {"type":"assistant","message":{"content":[{"type":"text","text":"..."}]}}
                                                  — final aggregated text, skip (no timestamp_ms)
  {"type":"result","subtype":"success","result":"...",
   "usage":{"inputTokens":N,"outputTokens":N,"cacheReadTokens":N,"cacheWriteTokens":N}}
                                                  — done; read usage

Usage:
  from src.cursor_agent_backend import cursor_agent_stream, cursor_agent_call
"""

import json
import subprocess
import sys
import os
from typing import Generator, List, Dict, Optional


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
                    inner = block.get("content", "")
                    parts.append(_extract_text(inner))
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts)
    return str(content) if content is not None else ""


def serialize_messages(messages: List[Dict]) -> str:
    """
    Convert an OpenAI-format messages list into a single prompt string
    suitable for cursor-agent's -p flag.

    Structure:
      [SYSTEM]
      <system content>

      [CONVERSATION HISTORY]
      <role>: <content>
      ...

      [CURRENT REQUEST]
      <last user message>
    """
    system_parts = []
    history_parts = []
    last_user_msg = ""

    # Split into system, history, and last user message
    user_messages_seen = []
    non_system = []

    for msg in messages:
        role = msg.get("role", "")
        if role == "system":
            system_parts.append(_extract_text(msg.get("content", "")))
        else:
            non_system.append(msg)

    # Find the last user message
    last_user_idx = -1
    for i, msg in enumerate(non_system):
        if msg.get("role") == "user":
            last_user_idx = i

    for i, msg in enumerate(non_system):
        role = msg.get("role", "")
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
            tool_id = msg.get("tool_call_id", "")
            text = _extract_text(content)
            history_parts.append(f"Tool result ({tool_id}): {text}")
        elif role == "user":
            text = _extract_text(content)
            if text.strip():
                history_parts.append(f"User: {text}")

    # Build prompt
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
    cmd = ["cursor-agent"]
    # Always pass --model: without it, cursor-agent uses the editor's default
    # which may not match the free-plan restriction. Default is "auto".
    cmd += ["--model", model or "auto"]
    if yolo:
        cmd.append("--yolo")
    if mode:
        cmd += ["--mode", mode]
    if workspace:
        cmd += ["--workspace", workspace]
    return cmd


# ---------------------------------------------------------------------------
# Streaming variant
# ---------------------------------------------------------------------------

def cursor_agent_stream(
    messages: List[Dict],
    model: str = "auto",
    yolo: bool = False,
    mode: str = "",
    workspace: str = "",
) -> Generator[str, None, None]:
    """
    Generator that calls cursor-agent with stream-json output and yields text
    deltas, mirroring the interface of chat_completion_stream().

    Also updates llm_client globals last_input_tokens / last_output_tokens
    from the usage field in the final result event.
    """
    import src.llm_client as _lc  # late import to avoid circular

    prompt = serialize_messages(messages)
    cmd = _build_cmd(model, yolo, mode, workspace) + [
        "--print",
        "--output-format", "stream-json",
        "--stream-partial-output",
        "-p", prompt,
    ]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    try:
        for raw_line in proc.stdout:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                chunk = json.loads(raw_line)
            except json.JSONDecodeError:
                continue

            chunk_type = chunk.get("type")

            if chunk_type == "assistant" and "timestamp_ms" in chunk:
                # Streaming delta — yield text
                content = chunk.get("message", {}).get("content", [])
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text = block.get("text", "")
                        if text:
                            yield text

            elif chunk_type == "result":
                # Final event — capture usage
                usage = chunk.get("usage", {})
                input_tokens = usage.get("inputTokens", 0) + usage.get("cacheReadTokens", 0)
                output_tokens = usage.get("outputTokens", 0)
                _lc.last_input_tokens = input_tokens
                _lc.last_output_tokens = output_tokens

    finally:
        proc.stdout.close()
        proc.wait()
        if proc.returncode != 0:
            stderr = proc.stderr.read() if proc.stderr else ""
            if stderr.strip():
                # Surface errors without crashing the caller
                yield f"\n[cursor-agent error: {stderr.strip()}]"


# ---------------------------------------------------------------------------
# Non-streaming variant
# ---------------------------------------------------------------------------

def cursor_agent_call(
    messages: List[Dict],
    model: str = "auto",
    yolo: bool = False,
    mode: str = "",
    workspace: str = "",
    stream_prefix: Optional[str] = None,
) -> str:
    """
    Calls cursor-agent and returns the full response as a string,
    mirroring the interface of call_llm_raw().

    If stream_prefix is set, prints lines with that prefix while collecting
    (mimics call_llm_raw's stream_prefix behavior).
    """
    import src.llm_client as _lc  # late import to avoid circular

    prompt = serialize_messages(messages)
    cmd = _build_cmd(model, yolo, mode, workspace) + [
        "--print",
        "--output-format", "stream-json",
        "--stream-partial-output",
        "-p", prompt,
    ]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    collected = []
    try:
        for raw_line in proc.stdout:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                chunk = json.loads(raw_line)
            except json.JSONDecodeError:
                continue

            chunk_type = chunk.get("type")

            if chunk_type == "assistant" and "timestamp_ms" in chunk:
                content = chunk.get("message", {}).get("content", [])
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text = block.get("text", "")
                        if text:
                            collected.append(text)
                            if stream_prefix is not None:
                                sys.stdout.write(stream_prefix + text)
                                sys.stdout.flush()

            elif chunk_type == "result":
                usage = chunk.get("usage", {})
                input_tokens = usage.get("inputTokens", 0) + usage.get("cacheReadTokens", 0)
                output_tokens = usage.get("outputTokens", 0)
                _lc.last_input_tokens = input_tokens
                _lc.last_output_tokens = output_tokens

    finally:
        proc.stdout.close()
        proc.wait()

    return "".join(collected)
