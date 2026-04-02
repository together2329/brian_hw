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

STRUCTURED_SUMMARY_PROMPT = """You are summarizing conversation history for an AI coding agent.
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
    summary_prompt = instruction if instruction else STRUCTURED_SUMMARY_PROMPT

    conversation_text = ""
    for m in messages:
        role = m.get("role", "unknown")
        content = str(m.get("content", ""))
        conversation_text += f"{role}: {content}\n"

    summary_request = [
        {
            "role": "system",
            "content": "You are a helpful assistant that summarizes conversation history for an AI agent.",
        },
        {"role": "user", "content": f"{summary_prompt}\n\n{conversation_text}"},
    ]

    summary_content = ""
    try:
        import sys
        char_count = 0
        print("[System] Compressing", end="", flush=True)
        for chunk in llm_call_fn(summary_request, suppress_spinner=True):
            if isinstance(chunk, tuple) and chunk[0] == "reasoning":
                continue
            summary_content += chunk
            char_count += len(chunk)
            if char_count % 200 == 0:
                print(".", end="", flush=True)
        print(f" done ({len(summary_content)} chars)")

        return {
            "role": "system",
            "content": f"[Previous Conversation Summary ({len(messages)} messages)]: {summary_content}",
        }
    except Exception as e:
        print(f"\n[System] Failed to generate summary: {e}")
        return messages[0] if messages else {"role": "system", "content": "[Compression failed]"}


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
    print(f"[System] Compressing {len(messages)} messages in {total_chunks} chunks...")

    for i in range(0, len(messages), chunk_size):
        chunk = messages[i : i + chunk_size]
        chunk_num = i // chunk_size + 1

        print(f"[System] Chunk {chunk_num}/{total_chunks}...", end="", flush=True)

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
        print(f"\n[System] Compression triggered. Context: {current_tokens:,} {token_source} tokens.")

    if not messages:
        return messages

    print("[System] Using traditional compression...")

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
            recent_msgs = []
            old_msgs = other_msgs
        else:
            recent_msgs = other_msgs[-keep_recent:]
            old_msgs = other_msgs[:-keep_recent]

        if not old_msgs:
            return messages

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
    if mode == "chunked":
        print(f"[System] Using chunked compression (chunk_size={cfg.COMPRESSION_CHUNK_SIZE})...")
        compressed = _compress_chunked(old_msgs, cfg=cfg, llm_call_fn=llm_call_fn, instruction=instruction)
    else:
        compressed = [_compress_single(old_msgs, llm_call_fn=llm_call_fn, instruction=instruction)]

    new_history = system_msgs + important_msgs + compressed + todo_preservation + recent_msgs

    new_tokens = sum(_est(m) for m in new_history)
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

    print("\n" + "=" * 60)
    print("Compression Complete")
    print("=" * 60)
    print(f"Messages: {old_msg_count} → {new_msg_count} ({msg_reduction_pct}% reduction)")
    print(
        f"Tokens:   {current_tokens:,} ({token_source}) → {new_tokens:,} (estimated) = "
        f"{reduction_pct}% reduction"
    )
    print(f"Kept recent: {keep_recent} messages")
    print(f"Summarized: {len(old_msgs)} → 1 summary")
    print("=" * 60 + "\n")

    return new_history
