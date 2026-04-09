"""
core/compressor.py — Conversation history compression

Extracted from src/main.py (Phase 5 refactor).

Public API:
    compress_history(messages, *, cfg, llm_call_fn, ...)
    _compress_single(messages, *, llm_call_fn, instruction=None)
    _compress_chunked(messages, *, cfg, llm_call_fn, instruction=None)

All functions are pure with respect to global state: every external dependency
(config, LLM callable, token counters) is passed as a parameter.
"""
from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# ---------------------------------------------------------------------------
# Prompt constant
# ---------------------------------------------------------------------------

_STRUCTURED_SUMMARY_PROMPT_DEFAULT = """You are summarizing conversation history for an AI coding agent.
Goal: Preserve ALL context needed to continue the work seamlessly, while eliminating redundancy.

What to KEEP:
- Every file path, function name, class name, variable name that was touched
- All decisions made (architecture, API design, naming conventions, configs)
- Errors encountered and how they were resolved (or if still unresolved)
- User preferences, constraints, and explicit instructions
- Current state: what works, what's broken, what's next
- Any partial work in progress

What to SKIP:
- Greetings, filler phrases, repeated explanations
- Superseded approaches that were abandoned
- Tool call boilerplate (keep only the outcome)
- Identical information stated multiple times

Format: structured bullet points, no prose padding.
Be thorough on facts. Skip nothing important.

## Goals
[What the user is trying to achieve]

## Completed
[Tasks finished, with outcomes — include file names and what changed]

## Decisions & Conventions
[Architecture choices, naming rules, API design, config values]

## Errors & Fixes
[Errors hit and how resolved; unresolved issues clearly marked]

## In Progress / Next
[Partially done work; what to do next]

## Key Files & Symbols
[Important file paths, function/class names, config keys]

## User Preferences
[Coding style, language preference, workflow constraints]

Omit sections with nothing to report."""


def _load_default_compression_prompt() -> str:
    """
    Load compression prompt from the active workspace, falling back to default.
    Priority: builtins._WORKSPACE_HOOK_MESSAGES["compression_system"]
              → workflow/default/compression_prompt.md
              → built-in default
    """
    import builtins as _b
    # 1. Active workspace hook message
    msgs = getattr(_b, "_WORKSPACE_HOOK_MESSAGES", {})
    if msgs.get("compression_system"):
        return msgs["compression_system"]

    # 2. workflow/default/compression_prompt.md (adjacent to common_ai_agent/)
    candidates = [
        Path(__file__).parent.parent.parent / "new_feature" / "workflow" / "default" / "compression_prompt.md",
        Path(__file__).parent.parent / "workflow" / "default" / "compression_prompt.md",
    ]
    for p in candidates:
        if p.exists():
            try:
                return p.read_text(encoding="utf-8").strip()
            except Exception:
                pass

    return _STRUCTURED_SUMMARY_PROMPT_DEFAULT


STRUCTURED_SUMMARY_PROMPT = _load_default_compression_prompt()


# ---------------------------------------------------------------------------
# Hook helpers (standalone utilities, no external deps)
# ---------------------------------------------------------------------------

def _find_hook(hook_name: str) -> Optional[Path]:
    """Find a hook file, checking platform-appropriate extensions."""
    hooks_dir = Path.home() / ".common_ai_agent" / "hooks"
    if platform.system() == "Windows":
        candidates = [f"{hook_name}.bat", f"{hook_name}.ps1", f"{hook_name}.py"]
    else:
        candidates = [f"{hook_name}.sh"]
    for name in candidates:
        path = hooks_dir / name
        if path.exists():
            return path
    return None


def _hook_command(hook_path: Path) -> list:
    """Return the command list to execute a hook file."""
    suffix = hook_path.suffix.lower()
    if suffix == ".py":
        return [sys.executable, str(hook_path)]
    if suffix == ".ps1":
        return ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(hook_path)]
    return [str(hook_path)]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _default_estimate(message: Dict[str, Any]) -> int:
    content = message.get("content", "")
    if isinstance(content, list):
        text = " ".join(
            p.get("text", "") if isinstance(p, dict) else str(p) for p in content
        )
    else:
        text = str(content)
    return len(text) // 4


# ---------------------------------------------------------------------------
# Core compression functions
# ---------------------------------------------------------------------------

def _compress_single(
    messages: List[Dict],
    *,
    llm_call_fn: Callable,
    instruction: Optional[str] = None,
) -> Dict[str, Any]:
    """Single-pass compression: summarize all messages at once.

    Args:
        messages: Messages to compress.
        llm_call_fn: Callable(messages, **kwargs) -> Iterable[str | tuple].
            Yields text chunks or ('reasoning', ...) tuples (which are ignored).
        instruction: Optional custom summarization prompt.

    Returns:
        A single system message dict containing the summary.
    """
    MAX_COMPRESS_CHARS = 80_000  # ~20K tokens, leaves room for prompt + output
    summary_prompt = instruction if instruction else STRUCTURED_SUMMARY_PROMPT

    conversation_text = ""
    for m in messages:
        role = m.get("role", "unknown")
        content = str(m.get("content", ""))[:1000]  # Truncate per-message
        conversation_text += f"{role}: {content}\n"

    # Truncate total if still too long (head + tail strategy)
    if len(conversation_text) > MAX_COMPRESS_CHARS:
        half = MAX_COMPRESS_CHARS // 2
        conversation_text = (
            conversation_text[:half]
            + "\n\n... [truncated] ...\n\n"
            + conversation_text[-half:]
        )

    summary_request = [
        {
            "role": "system",
            "content": "You are a helpful assistant that summarizes conversation history for an AI agent.",
        },
        {"role": "user", "content": f"{summary_prompt}\n\n{conversation_text}"},
    ]

    summary_content = ""
    try:
        print(f"  [Compress] Summarizing {len(messages)} messages...", end="", flush=True)
        for chunk in llm_call_fn(summary_request, suppress_spinner=True):
            if isinstance(chunk, tuple) and chunk[0] == "reasoning":
                continue
            summary_content += chunk
        print(f" done ({len(summary_content):,} chars)")

        return {
            "role": "system",
            "content": f"[Previous Conversation Summary ({len(messages)} messages)]: {summary_content}",
        }
    except Exception as e:
        print(f"\n  [Compress] Failed: {e}")
        # Return all messages as a single system message on failure
        # (was returning messages[0] which dropped ALL other messages)
        if not messages:
            return {"role": "system", "content": "[Compression failed]"}
        combined = "\n".join(
            f"{m.get('role', 'unknown')}: {str(m.get('content', ''))[:500]}"
            for m in messages
        )
        return {
            "role": "system",
            "content": f"[Previous Conversation Summary ({len(messages)} messages, compression failed)]: {combined}",
        }


def _compress_chunked(
    messages: List[Dict],
    *,
    cfg: Any,
    llm_call_fn: Callable,
    instruction: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Chunked compression: summarize in chunks.

    Args:
        messages: Messages to compress.
        cfg: Config namespace with COMPRESSION_CHUNK_SIZE.
        llm_call_fn: Callable(messages, **kwargs) -> Iterable[str | tuple].
        instruction: Optional custom summarization prompt.

    Returns:
        List of system message dicts, one per chunk.
    """
    chunk_size = cfg.COMPRESSION_CHUNK_SIZE
    compressed = []
    total_chunks = (len(messages) + chunk_size - 1) // chunk_size
    print(f"  [Compress] {len(messages)} messages in {total_chunks} chunks")

    for i in range(0, len(messages), chunk_size):
        chunk = messages[i : i + chunk_size]
        chunk_num = i // chunk_size + 1

        print(f"  [Compress] chunk {chunk_num}/{total_chunks}...", end="", flush=True)

        default_prompt = (
            "Summarize the following conversation segment concisely. "
            "Focus on completed tasks, key decisions, and current state."
        )
        summary_prompt = instruction if instruction else default_prompt

        conversation_text = ""
        for m in chunk:
            role = m.get("role", "unknown")
            content = str(m.get("content", ""))[:1000]
            conversation_text += f"{role}: {content}\n"

        summary_request = [
            {
                "role": "system",
                "content": "You are a helpful assistant that summarizes conversation history for an AI agent.",
            },
            {"role": "user", "content": f"{summary_prompt}\n\n{conversation_text}"},
        ]

        try:
            summary_content = ""
            for chunk_data in llm_call_fn(summary_request, suppress_spinner=True):
                if isinstance(chunk_data, tuple) and chunk_data[0] == "reasoning":
                    continue
                summary_content += chunk_data

            compressed.append(
                {
                    "role": "system",
                    "content": (
                        f"[Summary chunk {chunk_num}/{total_chunks} ({len(chunk)} messages)]: "
                        f"{summary_content}"
                    ),
                }
            )
            print(" Done.")
        except Exception as e:
            print(f" Failed: {e}")
            if chunk:
                compressed.append(chunk[0])

    return compressed


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def compress_history(
    messages: List[Dict],
    todo_tracker=None,
    force: bool = False,
    instruction: Optional[str] = None,
    keep_recent: Optional[int] = None,
    dry_run: bool = False,
    quiet: bool = False,
    *,
    cfg: Any,
    llm_call_fn: Callable,
    estimate_tokens_fn: Optional[Callable] = None,
    get_actual_tokens_fn: Optional[Callable] = None,
    last_input_tokens: int = 0,
    on_compressed_fn: Optional[Callable] = None,
    find_hook_fn: Optional[Callable] = None,
    hook_command_fn: Optional[Callable] = None,
    emit_fn: Optional[Callable] = None,
) -> List[Dict]:
    """Compress conversation history when it exceeds the token limit.

    Args:
        messages: Conversation history.
        todo_tracker: Optional tracker to preserve task state.
        force: If True, bypass token threshold check.
        instruction: Optional custom summarization instruction.
        keep_recent: Number of recent messages to keep (None = cfg default).
        dry_run: If True, return preview without modifying state.
        quiet: Suppress informational prints.
        cfg: Config namespace (ENABLE_COMPRESSION, MAX_CONTEXT_CHARS, etc.).
        llm_call_fn: Callable for LLM streaming (replaces chat_completion_stream).
        estimate_tokens_fn: Per-message token estimator (falls back to char//4).
        get_actual_tokens_fn: Returns total token count for all messages.
        last_input_tokens: Last actual token count from API (0 = unknown).
        on_compressed_fn: Called (no args) after compression completes.
        find_hook_fn: Locates hook files (defaults to built-in _find_hook).
        hook_command_fn: Builds hook command list (defaults to built-in _hook_command).

    Returns:
        Compressed (or original) message list.
    """
    if not cfg.ENABLE_COMPRESSION and not force:
        return messages

    _est = estimate_tokens_fn if estimate_tokens_fn is not None else _default_estimate
    _find_hook_fn = find_hook_fn if find_hook_fn is not None else _find_hook
    _hook_cmd_fn = hook_command_fn if hook_command_fn is not None else _hook_command

    limit_tokens = cfg.MAX_CONTEXT_CHARS // 4
    preemptive_threshold = int(limit_tokens * cfg.PREEMPTIVE_COMPRESSION_THRESHOLD)
    emergency_threshold = int(limit_tokens * cfg.COMPRESSION_THRESHOLD)

    if get_actual_tokens_fn is not None:
        current_tokens = get_actual_tokens_fn(messages)
    else:
        current_tokens = sum(_est(m) for m in messages)

    token_source = "actual" if last_input_tokens > 0 else "estimated"

    if current_tokens >= preemptive_threshold and not force:
        usage_pct = int(current_tokens / limit_tokens * 100)
        if not quiet:
            print(
                f"\n[System] Preemptive compression triggered at {current_tokens:,} tokens "
                f"({usage_pct}%)"
            )
        force = True

    if not force and current_tokens < emergency_threshold:
        return messages

    if not quiet:
        print(f"\n  [Compress] triggered — {current_tokens:,} {token_source} tokens")

    if not messages:
        return messages

    # Pre-compact hook
    pre_hook_path = _find_hook_fn("pre_compact")
    if pre_hook_path and pre_hook_path.exists():
        print(f"[Hook] Running {pre_hook_path.name}...")
        try:
            subprocess.run(_hook_cmd_fn(pre_hook_path), timeout=10, check=False, shell=False)
        except subprocess.TimeoutExpired:
            print(f"[Hook] {pre_hook_path.name} timed out (10s)")
        except Exception as e:
            print(f"[Hook] {pre_hook_path.name} failed: {e}")

    # Separate system vs regular messages
    _GENERATED_PREFIXES = (
        "[Previous Conversation Summary",
        "[Ongoing Task]",
        "[Todo Status]",
        "[Todo ",
    )
    system_msgs = [
        m
        for m in messages
        if m.get("role") == "system"
        and not str(m.get("content", "")).startswith(_GENERATED_PREFIXES)
    ]
    regular_msgs = [m for m in messages if m.get("role") != "system"]

    # Extract !important messages (preserve them)
    important_msgs = []
    other_msgs = []
    for msg in regular_msgs:
        content = str(msg.get("content", ""))
        if "!important" in content.lower():
            msg_copy = msg.copy()
            msg_copy["content"] = (
                content.replace("!important", "")
                .replace("!IMPORTANT", "")
                .replace("!Important", "")
                .strip()
            )
            important_msgs.append(msg_copy)
        else:
            other_msgs.append(msg)

    if important_msgs:
        print(f"[System] Preserving {len(important_msgs)} !important messages")

    if keep_recent is None:
        keep_recent = cfg.COMPRESSION_KEEP_RECENT

    # Turn-based protection
    if (
        keep_recent != 0
        and cfg.ENABLE_TURN_PROTECTION
        and any(m.get("turn_id") for m in other_msgs)
    ):
        protected_turns = cfg.TURN_PROTECTION_COUNT
        max_turn = max((m.get("turn_id", 0) for m in other_msgs), default=0)
        protected_turn_threshold = max(0, max_turn - protected_turns + 1)

        recent_msgs = [m for m in other_msgs if m.get("turn_id", 0) >= protected_turn_threshold]
        old_msgs = [m for m in other_msgs if m.get("turn_id", 0) < protected_turn_threshold]

        if not old_msgs and protected_turns > 1:
            protected_turns = 1
            protected_turn_threshold = max_turn
            recent_msgs = [m for m in other_msgs if m.get("turn_id", 0) >= protected_turn_threshold]
            old_msgs = [m for m in other_msgs if m.get("turn_id", 0) < protected_turn_threshold]

        print(
            f"[System] Protecting last {protected_turns} turns "
            f"({len(recent_msgs)} messages, turns {protected_turn_threshold}-{max_turn})"
        )

        if not old_msgs:
            fallback_keep = min(4, len(other_msgs))
            if len(other_msgs) <= fallback_keep:
                print(f"[System] History too short to compress ({len(other_msgs)} messages).")
                return messages
            recent_msgs = other_msgs[-fallback_keep:]
            old_msgs = other_msgs[:-fallback_keep]
            print(
                f"[System] Single-turn fallback: compressing {len(old_msgs)} messages, "
                f"keeping {len(recent_msgs)}"
            )
    else:
        if len(other_msgs) <= keep_recent:
            print(
                f"[System] History too short to compress ({len(other_msgs)} <= {keep_recent} recent)."
            )
            return messages

        if keep_recent == 0:
            # Even with keep_recent=0, preserve the last user message and any trailing
            # messages after it. Strict APIs (GLM-5.1 etc.) require at least one user
            # message; without it the conversation is [system, assistant] which causes
            # HTTP 400 "messages parameter is illegal".
            _last_user_idx = next(
                (i for i in range(len(other_msgs) - 1, -1, -1)
                 if other_msgs[i].get("role") == "user"),
                None
            )
            if _last_user_idx is not None and _last_user_idx > 0:
                recent_msgs = other_msgs[_last_user_idx:]   # last user + any trailing
                old_msgs = other_msgs[:_last_user_idx]
            elif _last_user_idx == 0:
                # Only user message is the first one; keep it, compress the rest
                recent_msgs = other_msgs[:1]
                old_msgs = other_msgs[1:]
            else:
                recent_msgs = []
                old_msgs = other_msgs
        else:
            recent_msgs = other_msgs[-keep_recent:]
            old_msgs = other_msgs[:-keep_recent]

        if not old_msgs:
            return messages

    # Native tool call pair integrity: ensure no assistant message with tool_calls
    # is split from its corresponding role:tool response messages across the
    # old_msgs/recent_msgs boundary. If the last message in old_msgs is an assistant
    # with tool_calls, move those orphaned tool messages from recent_msgs into old_msgs
    # so they are compressed together (and the sequence remains valid).
    if old_msgs and recent_msgs:
        if (old_msgs[-1].get("role") == "assistant"
                and old_msgs[-1].get("tool_calls")):
            # Collect the tool_call_ids that need responses
            _needed_ids = {tc["id"] for tc in old_msgs[-1]["tool_calls"]}
            _move: list = []
            for _m in list(recent_msgs):
                if _m.get("role") == "tool" and _m.get("tool_call_id") in _needed_ids:
                    _move.append(_m)
                    _needed_ids.discard(_m.get("tool_call_id"))
                else:
                    break  # tool messages are always contiguous after their assistant msg
            if _move:
                old_msgs = old_msgs + _move
                recent_msgs = recent_msgs[len(_move):]

    # Choose compression mode
    mode = cfg.COMPRESSION_MODE.lower() if hasattr(cfg, "COMPRESSION_MODE") else "traditional"

    # Todo preservation
    todo_preservation: List[Dict] = []
    if todo_tracker and todo_tracker.todos:
        status_icon = {
            "pending": "⏸",
            "in_progress": "▶",
            "completed": "👀",
            "approved": "✅",
            "rejected": "❌",
        }
        todo_lines = ["[Todo Status]:"]
        for i, t in enumerate(todo_tracker.todos):
            icon = status_icon.get(t.status, "?")
            line = f"  {icon} {i+1}. [{t.status}] {t.content}"
            if t.rejection_reason and t.status in ("rejected", "in_progress", "pending"):
                line += f"\n     ⚠ REJECTED: {t.rejection_reason}"
            todo_lines.append(line)
        todo_snapshot = "\n".join(todo_lines)

        if not todo_tracker.is_all_processed():
            prompt = todo_tracker.get_continuation_prompt()
            next_idx = todo_tracker._get_next_pending()
            if prompt:
                next_instruction = f"\n[Ongoing Task]: {prompt}"
            elif next_idx is not None:
                todo = todo_tracker.todos[next_idx]
                approved = sum(1 for t in todo_tracker.todos if t.status == "approved")
                total = len(todo_tracker.todos)
                next_instruction = (
                    f"\n[Ongoing Task]: [Todo {approved}/{total}] Next task ready: {todo.content}\n"
                    f"→ Start with: todo_update(index={next_idx + 1}, status='in_progress')"
                )
            else:
                next_instruction = ""
            todo_preservation = [
                {"role": "system", "content": todo_snapshot + next_instruction}
            ]
        else:
            todo_preservation = [
                {"role": "system", "content": todo_snapshot + "\n[All tasks completed]"}
            ]

    # Compress
    compressed = None
    try:
        if mode == "chunked":
            print(f"  [Compress] chunked (chunk_size={cfg.COMPRESSION_CHUNK_SIZE})")
            compressed = _compress_chunked(old_msgs, cfg=cfg, llm_call_fn=llm_call_fn, instruction=instruction)
        else:
            compressed = [_compress_single(old_msgs, llm_call_fn=llm_call_fn, instruction=instruction)]
    except Exception as exc:
        print(f"  [Compress] LLM compression failed entirely: {exc}")

    if compressed is not None:
        raw_history = system_msgs + important_msgs + compressed + todo_preservation + recent_msgs
    else:
        raw_history = system_msgs + important_msgs + todo_preservation + recent_msgs

    # Consolidate all system messages into a single leading system message.
    # Strict APIs (GLM-5.1/Z.AI, etc.) reject system messages mid-conversation,
    # causing HTTP 400 "The messages parameter is illegal".
    _sys_parts = []
    _non_sys = []
    for m in raw_history:
        if m.get("role") == "system":
            _content = m.get("content", "")
            if isinstance(_content, list):
                # Extract plain text from cache_control block format
                _text = "\n".join(
                    block.get("text", "") for block in _content
                    if isinstance(block, dict) and block.get("type") == "text"
                )
            else:
                _text = str(_content)
            _sys_parts.append(_text)
        else:
            _non_sys.append(m)

    if _sys_parts:
        _merged = "\n\n".join(p for p in _sys_parts if p.strip())
        new_history = [{"role": "system", "content": _merged}] + _non_sys
    else:
        new_history = _non_sys

    new_tokens = sum(_est(m) for m in new_history)

    # Emergency pruning: if still over limit after compression, tail-truncate
    if new_tokens > limit_tokens:
        print(f"  [Compress] EMERGENCY: still {new_tokens:,} tokens (limit {limit_tokens:,}), pruning to tail")
        emergency_keep = max(4, len(todo_preservation) + len(system_msgs) + 2)
        prunable = [m for m in new_history if m not in system_msgs and m not in todo_preservation]
        kept_system = [m for m in new_history if m in system_msgs or m in todo_preservation]
        # Keep only the last few messages
        pruned = prunable[-emergency_keep:]
        new_history = kept_system + pruned
        new_tokens = sum(_est(m) for m in new_history)
        print(f"  [Compress] Emergency prune: {len(prunable)} → {len(pruned)} messages ({new_tokens:,} tokens)")
    reduction_pct = int((1 - new_tokens / current_tokens) * 100) if current_tokens > 0 else 0
    old_msg_count = len(messages)
    new_msg_count = len(new_history)
    msg_reduction_pct = int((1 - new_msg_count / old_msg_count) * 100) if old_msg_count > 0 else 0

    if dry_run:
        print("\n" + "=" * 60)
        print("Compression Preview (Dry Run)")
        print("=" * 60)
        print(f"Current:  {old_msg_count} messages, {current_tokens:,} tokens")
        print(f"After:    {new_msg_count} messages, {new_tokens:,} tokens")
        print(f"Reduction: {msg_reduction_pct}% messages, {reduction_pct}% tokens")
        print(f"Kept recent: {keep_recent} messages")
        print(f"Summarizing: {len(old_msgs)} messages → 1 summary")
        print("=" * 60)
        print("\nRun '/compact' without --dry-run to apply.\n")
        return messages

    # Notify caller to reset last_input_tokens
    if on_compressed_fn is not None:
        on_compressed_fn()

    # Clean up _tokens metadata
    for msg in new_history:
        if "_tokens" in msg:
            del msg["_tokens"]

    # Post-compact hook
    post_hook_path = _find_hook_fn("post_compact")
    if post_hook_path and post_hook_path.exists():
        print(f"[Hook] Running {post_hook_path.name}...")
        try:
            env = os.environ.copy()
            env["BRIAN_OLD_MSGS"] = str(old_msg_count)
            env["BRIAN_NEW_MSGS"] = str(new_msg_count)
            env["BRIAN_OLD_TOKENS"] = str(current_tokens)
            env["BRIAN_NEW_TOKENS"] = str(new_tokens)
            env["BRIAN_REDUCTION_PCT"] = str(reduction_pct)
            subprocess.run(_hook_cmd_fn(post_hook_path), env=env, timeout=10, check=False, shell=False)
        except subprocess.TimeoutExpired:
            print(f"[Hook] {post_hook_path.name} timed out (10s)")
        except Exception as e:
            print(f"[Hook] {post_hook_path.name} failed: {e}")

    print(
        f"\n  [Compress] done\n"
        f"  | msgs    {old_msg_count:>6} → {new_msg_count:<6} ({msg_reduction_pct}% reduction)\n"
        f"  | tokens  {current_tokens:>6,} → {new_tokens:<6,} ({reduction_pct}% reduction)\n"
        f"  | kept    {keep_recent} recent  |  summarized {len(old_msgs)} → 1\n"
    )

    # Emit summary as markdown (TUI) or print to stdout (terminal)
    if compressed:
        raw = compressed[0].get("content", "") if isinstance(compressed[0], dict) else ""
        # Strip "[Previous Conversation Summary (N messages)]: " prefix
        import re as _re
        summary_text = _re.sub(r"^\[Previous Conversation Summary \(\d+ messages\)\]:\s*", "", raw)
        if summary_text.strip():
            md = f"## Compression Summary\n\n{summary_text.strip()}\n"
            if emit_fn:
                emit_fn(md)
            else:
                print(md)

    return new_history
