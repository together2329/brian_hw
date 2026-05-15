"""
claude_cli_backend.py — route LLM calls through the Claude Code CLI.

The stable default mirrors the cursor-agent backend shape but uses Claude's
simple non-interactive print path:

  claude --model sonnet --print --output-format json <prompt>

JSON mode avoids the hook/noise behavior seen with verbose stream-json while
still preserving token and cost usage from Claude Code's result object.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
from typing import Dict, Generator, Iterator, List, Optional

try:
    from src.cursor_agent_backend import serialize_messages
except Exception:  # pragma: no cover - import fallback for direct src path usage
    from cursor_agent_backend import serialize_messages  # type: ignore


last_claude_model: str = ""


def _build_cmd(
    model: str = "sonnet",
    permission_mode: str = "default",
    tools: str = "",
    workspace: str = "",
    no_session_persistence: bool = True,
    output_format: str = "json",
) -> List[str]:
    cmd = ["claude"]
    if model:
        cmd += ["--model", model]
    if permission_mode:
        cmd += ["--permission-mode", permission_mode]
    # Empty string is intentional: it disables Claude Code's built-in tools.
    # common_ai_agent remains the single executor for Action: lines.
    cmd += ["--tools", tools or ""]
    if workspace:
        cmd += ["--add-dir", workspace]
    if no_session_persistence:
        cmd.append("--no-session-persistence")
    cmd.append("--print")
    fmt = (output_format or "json").lower()
    if fmt == "json":
        cmd += ["--output-format", "json"]
    elif fmt == "stream-json":
        cmd += ["--verbose", "--output-format", "stream-json", "--include-partial-messages"]
    return cmd


def _terminate_process_group(proc: subprocess.Popen) -> None:
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except Exception:
        proc.terminate()


def _run_cmd(cmd: List[str], prompt: str, timeout_sec: int) -> tuple[int, str]:
    proc = subprocess.Popen(
        cmd + [prompt],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )
    try:
        out, _ = proc.communicate(timeout=timeout_sec)
    except subprocess.TimeoutExpired:
        _terminate_process_group(proc)
        try:
            out, _ = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except Exception:
                proc.kill()
            out, _ = proc.communicate()
        return 124, out
    return proc.returncode or 0, out


def _first_json_object(text: str) -> Optional[dict]:
    """Return the first JSON object in stdout, ignoring hook diagnostics."""
    decoder = json.JSONDecoder()
    for idx, ch in enumerate(text or ""):
        if ch != "{":
            continue
        try:
            value, _end = decoder.raw_decode(text[idx:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None


def _iter_chunks(proc, raw_lines: Optional[List[str]] = None) -> Iterator[dict]:
    for raw_line in proc.stdout:
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        try:
            yield json.loads(raw_line)
        except json.JSONDecodeError:
            if raw_lines is not None:
                raw_lines.append(raw_line)
            continue


def _usage_total(usage: dict) -> int:
    return int(usage.get("input_tokens", 0) or 0) + int(usage.get("cache_read_input_tokens", 0) or 0) + int(usage.get("cache_creation_input_tokens", 0) or 0)


def _handle_result_object(result: dict, lc) -> str:
    global last_claude_model

    usage = result.get("usage") or {}
    if usage:
        lc.last_input_tokens = _usage_total(usage)
        lc.last_output_tokens = int(usage.get("output_tokens", 0) or 0)
    model_usage = result.get("modelUsage") or {}
    if isinstance(model_usage, dict) and model_usage:
        last_claude_model = next(iter(model_usage.keys())) or last_claude_model
    text = result.get("result")
    return text if isinstance(text, str) else ""


def _handle_chunk(chunk: dict, lc, *, emit_final_assistant: bool = False) -> Optional[str]:
    """Process one Claude stream-json event.

    In streaming mode, text deltas are emitted from stream_event content block
    deltas. In raw-call mode, the result event is the safest final aggregate.
    """
    global last_claude_model

    chunk_type = chunk.get("type")
    if chunk_type == "system" and chunk.get("subtype") == "init":
        last_claude_model = chunk.get("model", "") or last_claude_model
        return None

    if chunk_type == "stream_event":
        event = chunk.get("event") or {}
        if event.get("type") == "message_start":
            message = event.get("message") or {}
            last_claude_model = message.get("model", "") or last_claude_model
            usage = message.get("usage") or {}
            if usage:
                lc.last_input_tokens = _usage_total(usage)
                lc.last_output_tokens = int(usage.get("output_tokens", 0) or 0)
        elif event.get("type") == "message_delta":
            usage = event.get("usage") or {}
            if usage:
                lc.last_input_tokens = _usage_total(usage)
                lc.last_output_tokens = int(usage.get("output_tokens", 0) or 0)
        elif event.get("type") == "content_block_delta":
            delta = event.get("delta") or {}
            if delta.get("type") == "text_delta":
                return delta.get("text", "") or None
        return None

    if chunk_type == "assistant":
        message = chunk.get("message") or {}
        last_claude_model = message.get("model", "") or last_claude_model
        usage = message.get("usage") or {}
        if usage:
            lc.last_input_tokens = _usage_total(usage)
            lc.last_output_tokens = int(usage.get("output_tokens", 0) or 0)
        if not emit_final_assistant:
            return None
        parts = []
        for block in message.get("content", []):
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "".join(parts) or None

    if chunk_type == "result":
        usage = chunk.get("usage") or {}
        if usage:
            lc.last_input_tokens = _usage_total(usage)
            lc.last_output_tokens = int(usage.get("output_tokens", 0) or 0)
        result = chunk.get("result")
        return result if emit_final_assistant and isinstance(result, str) else None

    return None


def claude_cli_stream(
    messages: List[Dict],
    model: str = "sonnet",
    permission_mode: str = "default",
    tools: str = "",
    workspace: str = "",
    no_session_persistence: bool = True,
    output_format: str = "json",
    timeout_sec: int = 300,
) -> Generator[str, None, None]:
    """Yield Claude Code text deltas, matching chat_completion_stream()."""
    import src.llm_client as _lc

    fmt = (output_format or "json").lower()
    if fmt != "stream-json":
        text = claude_cli_call(
            messages=messages,
            model=model,
            permission_mode=permission_mode,
            tools=tools,
            workspace=workspace,
            no_session_persistence=no_session_persistence,
            output_format=fmt,
            timeout_sec=timeout_sec,
        )
        if text:
            yield text
        return

    cmd = _build_cmd(model, permission_mode, tools, workspace, no_session_persistence, "stream-json")
    prompt = serialize_messages(messages)
    try:
        # Merge stderr into stdout and ignore non-JSON diagnostic lines. Claude
        # Code can emit verbose hook/debug output; leaving stderr unread can
        # deadlock once that pipe fills.
        proc = subprocess.Popen(
            cmd + [prompt],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            start_new_session=True,
        )
    except FileNotFoundError:
        yield "\n[claude-cli error: claude not found. Install Claude Code or check PATH.]"
        return

    try:
        saw_text = False
        final_result = ""
        diagnostics: List[str] = []
        for chunk in _iter_chunks(proc, diagnostics):
            if chunk.get("type") == "result" and isinstance(chunk.get("result"), str):
                final_result = chunk.get("result") or final_result
            text = _handle_chunk(chunk, _lc, emit_final_assistant=False)
            if text:
                saw_text = True
                yield text
        if not saw_text and final_result:
            yield final_result
    finally:
        if proc.stdout:
            proc.stdout.close()
        proc.wait()
        if proc.returncode != 0:
            detail = "\n".join(diagnostics[-8:]).strip()
            yield f"\n[claude-cli error: {detail or f'exit code {proc.returncode}'}]"


def claude_cli_call(
    messages: List[Dict],
    model: str = "sonnet",
    permission_mode: str = "default",
    tools: str = "",
    workspace: str = "",
    no_session_persistence: bool = True,
    output_format: str = "json",
    timeout_sec: int = 300,
    stream_prefix: Optional[str] = None,
) -> str:
    """Collect the full Claude Code response, matching call_llm_raw()."""
    import src.llm_client as _lc

    fmt = (output_format or "json").lower()
    cmd = _build_cmd(model, permission_mode, tools, workspace, no_session_persistence, fmt)
    prompt = serialize_messages(messages)

    if fmt != "stream-json":
        try:
            returncode, out = _run_cmd(cmd, prompt, timeout_sec)
        except FileNotFoundError:
            return "[claude-cli error] claude not found. Install Claude Code or check PATH."
        if returncode == 124:
            return f"[claude-cli error] timed out after {timeout_sec}s"
        if returncode != 0:
            return f"[claude-cli error] {out.strip() or f'exit code {returncode}'}"
        if fmt == "json":
            result = _first_json_object(out)
            if result is None:
                return out.strip()
            text = _handle_result_object(result, _lc)
        else:
            text = out.strip()
        if stream_prefix is not None and text:
            sys.stdout.write(stream_prefix + text)
            sys.stdout.flush()
        return text

    try:
        # Merge stderr into stdout for the same reason as streaming mode: this
        # process is line-read synchronously and must drain all CLI output.
        proc = subprocess.Popen(
            cmd + [prompt],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            start_new_session=True,
        )
    except FileNotFoundError:
        return "[claude-cli error] claude not found. Install Claude Code or check PATH."

    collected = []
    final_result = ""
    diagnostics: List[str] = []
    try:
        for chunk in _iter_chunks(proc, diagnostics):
            if chunk.get("type") == "result" and isinstance(chunk.get("result"), str):
                final_result = chunk.get("result") or final_result
            text = _handle_chunk(chunk, _lc, emit_final_assistant=False)
            if text:
                collected.append(text)
                if stream_prefix is not None:
                    sys.stdout.write(stream_prefix + text)
                    sys.stdout.flush()
    finally:
        if proc.stdout:
            proc.stdout.close()
        proc.wait()
    if proc.returncode != 0:
        detail = "\n".join(diagnostics[-8:]).strip()
        return f"[claude-cli error] {detail or f'exit code {proc.returncode}'}"
    return "".join(collected) or final_result
