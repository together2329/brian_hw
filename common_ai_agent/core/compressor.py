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
import re as _re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# ---------------------------------------------------------------------------
# Working-path collector — snapshot current project context at compress time
# ---------------------------------------------------------------------------

def _collect_working_paths_from_log(max_entries: int = 50) -> str:
    """Pull the last N entries from builtins._FILE_ACCESS_LOG for compression context.

    Returns empty string if the log is empty or unavailable.
    """
    import builtins as _b
    log = getattr(_b, '_FILE_ACCESS_LOG', None)
    if not log:
        return ""

    cwd = os.getcwd()
    lines: list[str] = [f"CWD: {cwd}"]

    # Take last max_entries entries
    entries = list(log.items())[-max_entries:]

    # Group by parent directory
    dirs: dict[str, list[tuple[str, str, int]]] = {}
    for abs_path, info in entries:
        display = info.get("display", abs_path)
        op = info.get("op", "?")
        count = info.get("count", 1)
        parent = os.path.dirname(abs_path)
        if parent.startswith(cwd + "/"):
            parent_d = parent[len(cwd) + 1:]
        elif parent == cwd:
            parent_d = "."
        else:
            parent_d = parent
        fname = os.path.basename(abs_path)
        dirs.setdefault(parent_d, []).append((fname, op, count))

    for dir_path in sorted(dirs.keys()):
        files = dirs[dir_path]
        lines.append(f"  [{dir_path}/]")
        for fname, op, cnt in sorted(files, key=lambda x: x[0]):
            icon = {"read": "📖", "write": "✏️ ", "edit": "🔧"}.get(op, "•")
            lines.append(f"    {icon} {fname}  ({op}, {cnt}x)")

    return "\n".join(lines)


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


def _message_text(m: Dict[str, Any]) -> str:
    """Flatten a message's content to a plain string for scanning."""
    c = m.get("content", "")
    if isinstance(c, list):
        return " ".join(
            p.get("text", "") if isinstance(p, dict) else str(p) for p in c
        )
    return str(c)


# ---------------------------------------------------------------------------
# Smart truncation — preserve more context for code/errors, less for filler
# ---------------------------------------------------------------------------

# Patterns that indicate high-value content worth preserving longer
_CODE_PATTERNS = ("```", "def ", "class ", "function ", "import ", "module ", "always @", "assign ", "wire ", "reg ")
_ERROR_PATTERNS = ("Traceback", "Error:", "error:", "Exception", "FAILED", "AssertionError", "TimeoutError", "FATAL")
_DIFF_PATTERNS = ("--- a/", "+++ b/", "@@ -", "@@ +", "diff --git")


def _smart_truncate(content: str, role: str, default_max: int = 2000) -> str:
    """Truncate message content adaptively based on content type.

    Code blocks, error traces, and diffs get up to 2x more characters
    than plain text, because losing half a function definition or stack
    trace is far worse than losing conversational filler.

    Args:
        content: The message content string.
        role: Message role ('user', 'assistant', 'tool', etc.).
        default_max: Default character limit for plain text.

    Returns:
        Truncated content string.
    """
    # Tool results are often code/output — give them a generous default
    if role == "tool":
        base_max = 2000
    else:
        base_max = default_max

    # Detect high-value content patterns
    is_code = any(p in content for p in _CODE_PATTERNS)
    is_error = any(p in content for p in _ERROR_PATTERNS)
    is_diff = any(p in content for p in _DIFF_PATTERNS)

    if is_code or is_error or is_diff:
        base_max *= 2  # Double the allocation for structured/valuable content

    return content[:base_max]


def _safe_prune(messages: List[Dict], max_keep: int) -> List[Dict]:
    """Emergency-prune messages while preserving role-pair integrity.

    Guarantees:
    - The last user message is ALWAYS included (API requirement).
    - Assistant messages with tool_calls are never split from their
      corresponding tool responses.
    - Falls back to simple tail-cut if pair integrity fails.

    Args:
        messages: List of message dicts to prune.
        max_keep: Maximum number of messages to keep.

    Returns:
        Pruned list of messages.
    """
    if len(messages) <= max_keep:
        return messages

    # Walk backward from the tail, collecting complete role-pairs.
    kept: List[Dict] = []
    i = len(messages) - 1
    while i >= 0 and len(kept) < max_keep:
        m = messages[i]
        kept.insert(0, m)

        # If this is a tool message, collect sibling tool messages and
        # the parent assistant message together.
        if m.get("role") == "tool" and i > 0:
            # Collect all contiguous tool messages
            tool_ids = set()
            while i >= 0 and messages[i].get("role") == "tool":
                tid = messages[i].get("tool_call_id")
                if tid:
                    tool_ids.add(tid)
                i -= 1
            # Now i points to the assistant message that spawned these tools
            if i >= 0 and messages[i].get("role") == "assistant" and messages[i].get("tool_calls"):
                # Check if this assistant was already added (from a previous iteration)
                if messages[i] not in kept:
                    kept.insert(0, messages[i])
                # Re-add all the tool messages we skipped
                for j in range(i + 1, len(messages)):
                    if messages[j].get("role") == "tool" and messages[j] not in kept:
                        kept.insert(len(kept) - 1, messages[j])
                        # Don't count these against max_keep since they're part of the pair
                break  # Done collecting this pair
            else:
                i += 1  # Put back
        i -= 1

    # Safety: ensure at least one user message exists in kept
    has_user = any(m.get("role") == "user" for m in kept)
    if not has_user:
        # Find and prepend the last user message
        for j in range(len(messages) - 1, -1, -1):
            if messages[j].get("role") == "user":
                kept.insert(0, messages[j])
                break

    return kept


# Signals that an assistant turn is asking the user for information.
_AWAIT_PATTERNS = (
    "please provide",
    "please specify",
    "please confirm",
    "please share",
    "please let me know",
    "could you provide",
    "could you specify",
    "could you confirm",
    "can you provide",
    "can you specify",
    "can you confirm",
    "i need you to",
    "waiting for your",
    "awaiting your",
    "awaiting required",
    "required user-provided",
)


def _detect_awaiting_user(messages: List[Dict[str, Any]]) -> bool:
    """Detect whether the conversation ended with the assistant asking
    the user a question that was never answered.

    Heuristic: walk backward from the tail, skipping system/tool frames.
    - If we see a user message with real content first → not awaiting.
    - If we see an assistant message first AND its text contains a
      question mark or an await-prompt phrase → awaiting user input.
    Otherwise → not awaiting.
    """
    for m in reversed(messages):
        role = m.get("role", "")
        if role in ("system", "tool"):
            continue
        text = _message_text(m).strip()
        if role == "user":
            # Continuation reminders are not real user answers — skip them
            # so a stale reminder doesn't mask an unanswered question.
            if text.startswith("[Task ") or "⚠️ MANDATORY" in text:
                continue
            return False
        if role == "assistant":
            if not text:
                return False
            low = text.lower()
            if "?" in text:
                return True
            return any(p in low for p in _AWAIT_PATTERNS)
    return False


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
        if role == "tool":
            # Tool result — include tool name if available for context
            content = _smart_truncate(str(m.get("content", "")), role)
            tool_name = m.get("name", "")
            if tool_name:
                conversation_text += f"tool({tool_name}): {content}\n"
            else:
                conversation_text += f"observation: {content}\n"
            continue
        content = _smart_truncate(str(m.get("content") or ""), role)
        # Assistant message with tool_calls — preserve function names and truncated args
        if role == "assistant" and m.get("tool_calls"):
            call_parts = []
            for tc in m["tool_calls"]:
                fn = tc.get("function", {})
                name = fn.get("name", "?")
                args_str = str(fn.get("arguments", ""))[:80]
                call_parts.append(f"{name}({args_str})" if args_str else name)
            if content:
                conversation_text += f"assistant: {content}\n  → called: {', '.join(call_parts)}\n"
            else:
                conversation_text += f"assistant → called: {', '.join(call_parts)}\n"
        else:
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
            content = _smart_truncate(str(m.get("content", "")), role)
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
                # Preserve ALL messages in the chunk, not just chunk[0].
                # Combine into a single system message with head+tail truncation.
                _combined = "\n".join(
                    f"{m.get('role', '?')}: {str(m.get('content', ''))[:500]}"
                    for m in chunk
                )
                if len(_combined) > 4000:
                    _half = 2000
                    _combined = _combined[:_half] + "\n... [truncated] ...\n" + _combined[-_half:]
                compressed.append({
                    "role": "system",
                    "content": f"[Chunk compression failed ({len(chunk)} messages)]: {_combined}",
                })

    return compressed


# ---------------------------------------------------------------------------
# Pre-compression analysis (LLM identifies critical context)
# ---------------------------------------------------------------------------

# Single-pass analysis+summarization prompt (replaces two separate LLM calls)
_SINGLE_PASS_PROMPT = """You are summarizing conversation history for an AI coding agent.

## Step 1: Identify Critical Context
First, identify what MUST be preserved. Focus on:
1. Active goal and current task status
2. Critical decisions, findings, or constraints discovered
3. Files/symbols/errors that are currently relevant
4. Last action taken and its outcome
5. Anything the agent must NOT forget

## Step 2: Summarize
Then summarize the conversation preserving ALL critical items.

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

Format your response as:

## Critical Context
[5-10 bullet points of what must not be lost]

## Summary
[Structured summary with these sections]
### Goals
### Completed
### Decisions & Conventions
### Errors & Fixes
### In Progress / Next
### Key Files & Symbols
### User Preferences

Be thorough on facts. Skip nothing important."""


def _pre_analysis(messages: List[Dict], llm_call_fn: Callable) -> str:
    """Ask LLM what is critical in current context before compression.
    Only called when compression is actually triggered (past threshold checks).

    DEPRECATED: This function is kept for backward compatibility but the
    single-pass approach (_SINGLE_PASS_PROMPT) is preferred as it avoids
    a separate LLM call.
    """
    recent = messages[-20:] if len(messages) > 20 else messages
    conv_text = ""
    for m in recent:
        role = m.get("role", "?")
        content = str(m.get("content") or "")[:600]
        conv_text += role + ": " + content + "\n"

    analysis_msgs = [
        {
            "role": "system",
            "content": "You are helping preserve critical context before conversation compression.",
        },
        {
            "role": "user",
            "content": (
                "Analyze the recent conversation below and identify what MUST be preserved "
                "during compression. Focus on:\n"
                "1. Active goal and current task status\n"
                "2. Critical decisions, findings, or constraints discovered\n"
                "3. Files/symbols/errors that are currently relevant\n"
                "4. Last action taken and its outcome\n"
                "5. Anything the agent must NOT forget\n\n"
                "Be concise - 5-10 bullet points max.\n\n"
                + conv_text
            ),
        },
    ]
    analysis = ""
    try:
        print("  [Compress] Pre-analysis: identifying critical context...", end="", flush=True)
        for chunk in llm_call_fn(analysis_msgs, suppress_spinner=True):
            if isinstance(chunk, tuple) and chunk[0] == "reasoning":
                continue
            analysis += chunk
        print(f" done ({len(analysis):,} chars)")
    except Exception as e:
        print(f" failed ({e})")
        return ""
    return analysis.strip()


# ---------------------------------------------------------------------------
# Public entry point
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
        cfg: Config namespace (ENABLE_COMPRESSION, MAX_CONTEXT_TOKENS, etc.).
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

    limit_tokens = cfg.MAX_CONTEXT_TOKENS
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

    # Pre-compression analysis: use single-pass prompt to combine analysis
    # and summarization into one LLM call (instead of two separate calls).
    if getattr(cfg, "COMPRESSION_PRE_ANALYSIS", False) and not dry_run and instruction is None:
        instruction = _SINGLE_PASS_PROMPT

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

    # Frozen summary detection: prevent re-compression of already-compressed summaries.
    # When compression runs multiple times, previously generated summaries should be
    # preserved verbatim instead of being re-summarized (generation loss prevention).
    frozen_summaries: List[Dict] = []
    _FROZEN_PREFIXES = (
        "[Previous Conversation Summary",
        "[Summary chunk",
        "[Chunk compression failed",
        "[FROZEN SUMMARY",
    )
    truly_new_msgs = []
    for _m in old_msgs:
        _mc = str(_m.get("content", ""))
        if _m.get("role") == "system" and any(_mc.startswith(p) for p in _FROZEN_PREFIXES):
            # Tag and preserve — do not re-compress
            if not _mc.startswith("[FROZEN SUMMARY"):
                _m = dict(_m, content="[FROZEN SUMMARY - preserved verbatim] " + _mc)
            frozen_summaries.append(_m)
        else:
            truly_new_msgs.append(_m)
    old_msgs = truly_new_msgs

    if frozen_summaries:
        print(f"  [Compress] Preserving {len(frozen_summaries)} frozen summaries verbatim")

    if not old_msgs and frozen_summaries:
        # All old messages are frozen summaries — nothing new to compress
        print(f"  [Compress] No new messages to compress, only frozen summaries")

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
            if t.detail:
                line += f"\n     Detail: {t.detail}"
            if t.criteria:
                for _c in t.criteria.splitlines():
                    if _c.strip():
                        line += f"\n     • {_c.strip()}"
            if t.rejection_reason and t.status in ("rejected", "in_progress", "pending"):
                line += f"\n     ⚠ REJECTED: {t.rejection_reason}"
            if getattr(t, "notes", None):
                for ni, note in enumerate(t.notes, 1):
                    line += f"\n     [{ni}] {note}"
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

    # Compress (skip if all old messages were frozen summaries)
    compressed = None
    if old_msgs:
        try:
            if mode == "chunked":
                print(f"  [Compress] chunked (chunk_size={cfg.COMPRESSION_CHUNK_SIZE})")
                compressed = _compress_chunked(old_msgs, cfg=cfg, llm_call_fn=llm_call_fn, instruction=instruction)
            else:
                compressed = [_compress_single(old_msgs, llm_call_fn=llm_call_fn, instruction=instruction)]
        except Exception as exc:
            print(f"  [Compress] LLM compression failed entirely: {exc}")

    # Preserve "awaiting user input" state across compression. If the pre-
    # compression tail shows the assistant asked the user a question that
    # was never answered, the post-compression summary alone won't convey
    # that — the model will happily re-ask the same question every turn,
    # producing the 60→81 livelock observed in the CPU req-gen incident.
    _awaiting_user = _detect_awaiting_user(messages)
    awaiting_note: List[Dict[str, Any]] = []
    if _awaiting_user:
        awaiting_note = [{
            "role": "system",
            "content": (
                "[AWAITING USER INPUT] Your previous turn asked the user for "
                "information and no answer has arrived yet. Do NOT repeat the "
                "question, do NOT retry the task, do NOT mark any task rejected "
                "because of missing input. Produce a minimal acknowledgement "
                "(or nothing) and wait — the user will respond when ready."
            ),
        }]

    if compressed is not None:
        raw_history = (
            system_msgs + important_msgs + frozen_summaries + compressed
            + awaiting_note + todo_preservation + recent_msgs
        )
    else:
        raw_history = (
            system_msgs + important_msgs + frozen_summaries
            + awaiting_note + todo_preservation + recent_msgs
        )

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
        # Categorize and order system parts with section headers
        # Order: instructions → frozen summaries → new summary → todo → awaiting
        _cat_instructions = []
        _cat_frozen = []
        _cat_summary = []
        _cat_todo = []
        _cat_awaiting = []
        _cat_other = []
        for _p in _sys_parts:
            if not _p.strip():
                continue
            if _p.startswith("[AWAITING USER INPUT"):
                _cat_awaiting.append(_p)
            elif _p.startswith("[FROZEN SUMMARY"):
                _cat_frozen.append(_p)
            elif _p.startswith("[Previous Conversation Summary") or _p.startswith("[Summary chunk"):
                _cat_summary.append(_p)
            elif _p.startswith("[Todo Status"):
                _cat_todo.append(_p)
            elif _p.startswith("[Chunk compression failed"):
                _cat_summary.append(_p)  # failed chunks go with summary
            else:
                _cat_instructions.append(_p)

        _ordered_parts = []
        if _cat_instructions:
            _ordered_parts.append("===== SYSTEM INSTRUCTIONS =====\n" + "\n\n".join(_cat_instructions))
        if _cat_frozen:
            _ordered_parts.append("===== PRESERVED CONTEXT =====\n" + "\n\n".join(_cat_frozen))
        if _cat_summary:
            _ordered_parts.append("===== CONVERSATION SUMMARY =====\n" + "\n\n".join(_cat_summary))
        if _cat_todo:
            _ordered_parts.append("===== TASK STATUS =====\n" + "\n\n".join(_cat_todo))
        if _cat_awaiting:
            _ordered_parts.append("===== AGENT DIRECTIVE =====\n" + "\n\n".join(_cat_awaiting))
        if _cat_other:
            _ordered_parts.append("\n\n".join(_cat_other))

        # Append file access log (last ~50 tool-touched paths)
        _file_log = _collect_working_paths_from_log(max_entries=50)
        if _file_log:
            _ordered_parts.append("===== WORKING PATHS (recent tool calls) =====\n" + _file_log)

        _merged = "\n\n".join(_ordered_parts)
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
        # Use safe pruning to preserve role-pair integrity
        pruned = _safe_prune(prunable, emergency_keep)
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

    # Emit full context as markdown (TUI) or print to stdout (terminal)
    # Display everything that goes into new_history so the user sees exactly
    # what the model will see in context — not just the LLM summary.
    import re as _re
    md_parts = []

    # 1. Compression Summary (the LLM-generated summary)
    if compressed:
        for _ci, _comp_msg in enumerate(compressed):
            raw = _comp_msg.get("content", "") if isinstance(_comp_msg, dict) else ""
            summary_text = _re.sub(r"^\[Previous Conversation Summary \(\d+ messages\)\]:\s*", "", raw)
            summary_text = _re.sub(r"^\[Summary chunk \d+/\d+ \(\d+ messages\)\]:\s*", "", summary_text)
            if summary_text.strip():
                md_parts.append("## Compression Summary\n\n" + summary_text.strip())

    # 2. Todo Status
    if todo_preservation:
        for _tp in todo_preservation:
            _tpc = str(_tp.get("content", ""))
            if _tpc.strip():
                md_parts.append("## Todo Status\n\n" + _tpc.strip())

    # 3. Awaiting Input Note
    if awaiting_note:
        for _an in awaiting_note:
            _anc = str(_an.get("content", ""))
            if _anc.strip():
                md_parts.append("## Awaiting Input\n\n" + _anc.strip())

    # 4. Important Messages (preserved with !important)
    if important_msgs:
        _imp_lines = []
        for _im in important_msgs:
            _im_role = _im.get("role", "unknown")
            _im_content = str(_im.get("content", ""))[:500]
            _imp_lines.append("**[" + _im_role + "]** " + _im_content)
        md_parts.append("## Important Messages (" + str(len(important_msgs)) + ")\n\n" + "\n\n".join(_imp_lines))

    # 5. Recent Messages (brief preview)
    if recent_msgs:
        _rm_lines = []
        for _rm in recent_msgs:
            _rm_role = _rm.get("role", "unknown")
            _rm_content = str(_rm.get("content", ""))[:200]
            _rm_lines.append("**[" + _rm_role + "]** " + _rm_content)
        md_parts.append(
            "## Recent Messages (" + str(len(recent_msgs)) + " kept)\n\n"
            + "\n\n".join(_rm_lines)
        )

    # 6. Stats
    md_parts.append(
        "## Stats\n\n"
        "- Messages: " + str(old_msg_count) + " -> " + str(new_msg_count) + " (" + str(msg_reduction_pct) + "% reduction)\n"
        "- Tokens: " + f"{current_tokens:,}" + " -> " + f"{new_tokens:,}" + " (" + str(reduction_pct) + "% reduction)\n"
        "- Kept: " + str(len(recent_msgs)) + " recent | Summarized: " + str(len(old_msgs)) + " -> " + str(len(compressed) if compressed else 0)
    )

    if md_parts:
        md = "\n\n---\n\n".join(md_parts) + "\n"
        if emit_fn:
            emit_fn(md)
        else:
            print(md)

    return new_history
