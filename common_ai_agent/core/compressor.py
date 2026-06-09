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

import json
import os
import platform
import subprocess
import sys
import textwrap
import re as _re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class CompressionLLMError(RuntimeError):
    """Raised by ``compress_history`` (only when ``raise_on_llm_failure=True``)
    to signal that the summarizer LLM call failed and the produced "summary" is
    a non-LLM truncation fallback, not a real AI summary.

    The web ``/compact`` path opts in so a genuine LLM failure surfaces as the
    deterministic ``_compact_history_file`` fallback + an honest
    "(AI summary unavailable: …)" message, instead of silently reporting a
    successful "N% reduction" whose body is raw truncated text.
    """


# Substrings embedded by _compress_single / _compress_chunked when the LLM call
# fails and they fall back to a char-truncation summary. compress_history scans
# the produced summary for these to detect a swallowed failure. They are
# bracket-anchored so ordinary summary prose mentioning "compression failed"
# does not false-positive.
_LLM_FAILURE_MARKERS = (
    ", compression failed)]",
    "[Chunk compression failed",
    "[Compression failed]",
)

_DATA_IMAGE_RE = _re.compile(
    r"data:image/[A-Za-z0-9.+-]+(?:;[A-Za-z0-9=.+-]+)*;base64,[A-Za-z0-9+/=\r\n]+"
)
# Mirrors Codex's fixed context estimate for resized prompt images. The raw
# base64 payload is transport data, not model-visible text.
_RESIZED_IMAGE_BYTES_ESTIMATE = 7373
_IMAGE_TEXT_PLACEHOLDER = "[Image omitted from compression text]"


def _summary_is_llm_fallback(compressed: Optional[List[Dict]]) -> bool:
    """True if any compressed part is a non-LLM truncation fallback."""
    if not compressed:
        return False
    for _cm in compressed:
        if not isinstance(_cm, dict):
            continue
        _content = str(_cm.get("content", ""))
        if any(_mk in _content for _mk in _LLM_FAILURE_MARKERS):
            return True
    return False


def _image_placeholder(block: Dict[str, Any]) -> str:
    detail = str(block.get("detail") or "").strip()
    if detail:
        return f"{_IMAGE_TEXT_PLACEHOLDER} detail={detail}"
    return _IMAGE_TEXT_PLACEHOLDER


def _content_text(content: Any) -> str:
    """Flatten content without turning inline image payloads into text."""

    if isinstance(content, str):
        return _DATA_IMAGE_RE.sub(_IMAGE_TEXT_PLACEHOLDER, content)
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                block_type = str(block.get("type") or "")
                if block_type in ("text", "input_text", "output_text"):
                    text = block.get("text")
                    if text is not None:
                        parts.append(str(text))
                elif block_type == "input_image":
                    parts.append(_image_placeholder(block))
                elif "text" in block and block.get("text") is not None:
                    parts.append(str(block.get("text")))
            elif block is not None:
                parts.append(str(block))
        return "\n".join(part for part in parts if part)
    if content is None:
        return ""
    return str(content)


def _content_estimate_tokens(content: Any) -> int:
    """Estimate model-visible tokens for text plus image blocks."""

    if isinstance(content, str):
        adjusted = len(content)
        for match in _DATA_IMAGE_RE.finditer(content):
            adjusted -= len(match.group(0))
            adjusted += _RESIZED_IMAGE_BYTES_ESTIMATE
        return max(0, adjusted // 4)
    if isinstance(content, dict):
        if str(content.get("type") or "") == "input_image":
            return max(1, _RESIZED_IMAGE_BYTES_ESTIMATE // 4)
        return sum(
            _content_estimate_tokens(value)
            for value in content.values()
            if isinstance(value, (str, list, dict))
        )
    if isinstance(content, list):
        return sum(_content_estimate_tokens(block) for block in content)
    return len(str(content)) // 4 if content is not None else 0


def _content_blocks(content: Any) -> list[Any]:
    if isinstance(content, list):
        return list(content)
    text = _content_text(content)
    return [{"type": "text", "text": text}] if text else []


def _merge_message_content(left: Any, right: Any) -> Any:
    if not isinstance(left, list) and not isinstance(right, list):
        left_text = str(left or "")
        right_text = str(right or "")
        if left_text and right_text:
            return left_text + "\n\n---\n\n" + right_text
        return left_text or right_text

    merged = _content_blocks(left)
    if merged and _content_blocks(right):
        merged.append({"type": "text", "text": "\n\n---\n\n"})
    merged.extend(_content_blocks(right))
    return merged

# ---------------------------------------------------------------------------
# Working-path collector — snapshot current project context at compress time
# ---------------------------------------------------------------------------

def _collect_working_paths_from_log(max_entries: int = 20) -> str:
    """Pull the most-recently-accessed N entries from builtins._FILE_ACCESS_LOG.

    Sorted by seq (descending) so the most recent accesses appear first.
    Returns empty string if the log is empty or unavailable.
    """
    import builtins as _b
    log = getattr(_b, '_FILE_ACCESS_LOG', None)
    if not log:
        return ""

    cwd = os.getcwd()
    lines: list[str] = [f"CWD: {cwd}"]

    # Sort by seq descending → most recently accessed first
    entries = sorted(log.items(), key=lambda kv: kv[1].get("seq", 0), reverse=True)[:max_entries]

    for abs_path, info in entries:
        display = info.get("display", abs_path)
        op = info.get("op", "?")
        cnt = info.get("count", 1)
        lines.append(f"  {op}: {display}  (x{cnt})")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Prompt constant
# ---------------------------------------------------------------------------

_STRUCTURED_SUMMARY_PROMPT_DEFAULT = """You are summarizing conversation history for an AI coding agent.

The history contains:
  - user/assistant dialog
  - [tool_name(arg=val, ...)] — agent tool calls (with arguments)
  - tool(name): result       — tool return values
  - [Prior summary context]  — earlier compression (must be incorporated)

Goal: Produce a dense, actionable summary that lets the agent resume work
seamlessly. Every fact that affects future decisions must be preserved.

━━━ WHAT TO KEEP ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Working directory / project path / git branch (extract from tool args or output)
• Every file path that was read, written, created, deleted, or searched
• Shell commands run AND their key outcome (exit code, error message, important stdout)
• All decisions: architecture, naming conventions, API design, config values
• Errors encountered → resolution taken (or mark UNRESOLVED if still open)
• User instructions, constraints, preferences stated explicitly
• Partial work: what was completed, what still needs to be done
• Discovered facts: test results, benchmark numbers, API responses, schema info
• Prior summary context: all important facts from [Prior summary context] blocks

━━━ WHAT TO SKIP ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Greetings, filler phrases, repeated information
• Full file contents (only note path + what changed)
• Abandoned approaches (one-liner: "tried X → failed because Y")
• Redundant tool call boilerplate (record outcome, not raw output)

━━━ FORMAT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Structured bullet points. No prose padding. Omit sections with nothing to report.

## Working Context
- CWD / project root (from bash cwd, tool paths, or explicit mention)
- Git branch / commit if known
- Active workspace / environment name

## Goals
- What the user is trying to achieve overall

## Completed Work
- Tasks finished with concrete outcomes (file created, test passed, bug fixed)
- Include exact file paths and what specifically changed

## Tool Activity
### Files Read
- List each path read (from read_file / read_lines args)
### Files Written / Modified
- path — brief description of what was changed
### Commands Run
- `command` → outcome (success / error snippet / key output)
### Searches
- pattern or query → what was found (or "not found")

## Decisions & Conventions
- Architecture choices, naming rules, API design, config values chosen

## Errors & Fixes
- Error → how resolved. Mark **UNRESOLVED** if still open.

## In Progress / Next
- What is partially done and what the next concrete step is

## Key Files & Symbols
- Critical file paths, function/class/variable names, config keys, env vars

## User Preferences
- Coding style, language, workflow constraints explicitly stated

Omit any section with nothing to report."""


def _load_default_compression_prompt() -> str:
    """
    Load compression prompt from the active workspace, falling back to default.
    Priority: builtins._WORKSPACE_HOOK_MESSAGES["compression_user_instruction"]
              → builtins._WORKSPACE_HOOK_MESSAGES["compression_system"]  (legacy)
              → workflow/default/compression_prompt.md
              → built-in default

    Naming history: the legacy key is "compression_system" but the value is
    used as the *user-instruction* prompt, not the system-role prompt — a
    long-standing foot-gun. New code should use "compression_user_instruction".
    The legacy key is still read for backward compatibility but emits a
    deprecation note via stderr-quiet print so existing customizations keep
    working without surprise.
    """
    import builtins as _b
    msgs = getattr(_b, "_WORKSPACE_HOOK_MESSAGES", {})
    # 1. New canonical key
    if msgs.get("compression_user_instruction"):
        return msgs["compression_user_instruction"]
    # 2. Legacy key (still supported)
    if msgs.get("compression_system"):
        return msgs["compression_system"]

    # 3. workflow/default/compression_prompt.md (adjacent to common_ai_agent/)
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
    total_tokens = _content_estimate_tokens(message.get("content", ""))

    # Native tool-call assistant turns often have empty content; the actual
    # tokens live in tool_calls (function name + serialized arguments). Without
    # this, threshold checks fire late on tool-heavy sessions.
    tcs = message.get("tool_calls")
    if tcs and isinstance(tcs, list):
        for tc in tcs:
            if not isinstance(tc, dict):
                continue
            fn = tc.get("function", {}) if isinstance(tc.get("function"), dict) else {}
            total_tokens += len(str(fn.get("name", ""))) // 4
            args = fn.get("arguments", "")
            total_tokens += (len(args) if isinstance(args, str) else len(str(args))) // 4

    return total_tokens


def _message_text(m: Dict[str, Any]) -> str:
    """Flatten a message's content to a plain string for scanning."""
    return _content_text(m.get("content", ""))


# ---------------------------------------------------------------------------
# Smart truncation — preserve more context for code/errors, less for filler
# ---------------------------------------------------------------------------

# Patterns that indicate high-value content worth preserving longer
_CODE_PATTERNS = ("```", "def ", "class ", "function ", "import ", "module ", "always @", "assign ", "wire ", "reg ")
_ERROR_PATTERNS = ("Traceback", "Error:", "error:", "Exception", "FAILED", "AssertionError", "TimeoutError", "FATAL")
_DIFF_PATTERNS = ("--- a/", "+++ b/", "@@ -", "@@ +", "diff --git")


def _smart_truncate(content: str, role: str, default_max: int = 2000, cfg: Any = None) -> str:
    """Truncate message content adaptively based on content type.

    Code blocks, error traces, and diffs get an upgraded budget compared
    to plain text — losing half a function definition or stack trace is
    far worse than losing conversational filler.

    Caps are configurable via cfg:
      - SMART_TRUNCATE_TEXT_MAX: per-message char cap for plain user/assistant text
        (default 2000)
      - SMART_TRUNCATE_TOOL_MAX: per-message char cap for tool results
        (default 2000 — bump to 8000+ if your tools return long outputs)
      - SMART_TRUNCATE_HIGHVALUE_MULT: multiplier applied when code/error/diff
        patterns are detected (default 2.0)

    Args:
        content: The message content string.
        role: Message role ('user', 'assistant', 'tool', etc.).
        default_max: Default character limit for plain text (overridden by
            SMART_TRUNCATE_TEXT_MAX when cfg is provided).
        cfg: Optional config namespace for the knobs above.

    Returns:
        Truncated content string.
    """
    # Resolve caps from cfg with sensible fallbacks
    _text_max = default_max
    _tool_max = 2000
    _hv_mult = 2.0
    if cfg is not None:
        try:
            _text_max = int(getattr(cfg, "SMART_TRUNCATE_TEXT_MAX", default_max) or default_max)
            _tool_max = int(getattr(cfg, "SMART_TRUNCATE_TOOL_MAX", 2000) or 2000)
            _hv_mult = float(getattr(cfg, "SMART_TRUNCATE_HIGHVALUE_MULT", 2.0) or 2.0)
        except Exception:
            pass

    base_max = _tool_max if role == "tool" else _text_max

    # Detect high-value content patterns
    is_code = any(p in content for p in _CODE_PATTERNS)
    is_error = any(p in content for p in _ERROR_PATTERNS)
    is_diff = any(p in content for p in _DIFF_PATTERNS)

    if is_code or is_error or is_diff:
        base_max = int(base_max * _hv_mult)

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


# ---------------------------------------------------------------------------
# Post-compression message sequence repair
# ---------------------------------------------------------------------------

def _validate_and_repair_sequence(
    messages: List[Dict],
    *,
    model_name: str = "",
) -> List[Dict]:
    """Validate and repair the message sequence after compression.

    Fixes two critical post-compression issues that cause HTTP 400 errors:

    1. **Orphaned tool messages**: A ``role: tool`` message must always be
       preceded by an ``role: assistant`` message whose ``tool_calls``
       list declares the matching ``tool_call_id``.  Compression can split
       the assistant→tool pair across the old/new boundary, leaving a
       dangling tool response.  This function converts orphaned tool
       messages into user-role messages so the API accepts the sequence.

    2. **DeepSeek reasoning_content**: DeepSeek's thinking mode REQUIRES
       every assistant message to carry ``reasoning_content``.  After
       compression the field may be missing, causing HTTP 400
       "The reasoning_content in the thinking mode must be passed back
       to the API."

    Inspired by Claude Code's ``ensureToolResultPairing()`` (see
    leaked-claude-code/utils/messages.ts).

    Args:
        messages: The message list to validate/repair.
        model_name: Current model name (used for DeepSeek detection).

    Returns:
        Repaired message list (may be longer or shorter than input).
    """
    if not messages:
        return messages

    repaired: List[Dict] = []
    # Track tool_call_ids declared by preceding assistant messages.
    # We keep a running set that is populated as we encounter
    # assistant messages with tool_calls.
    declared_tool_call_ids: set = set()

    # --- Pass 1: fix orphaned tool messages ---
    for msg in messages:
        role = msg.get("role", "")

        if role == "assistant":
            # Register any tool_calls this assistant declares
            tool_calls = msg.get("tool_calls")
            if tool_calls:
                for tc in tool_calls:
                    tc_id = tc.get("id") if isinstance(tc, dict) else None
                    if tc_id:
                        declared_tool_call_ids.add(tc_id)
            repaired.append(msg)

        elif role == "tool":
            tool_call_id = msg.get("tool_call_id")
            if tool_call_id and tool_call_id in declared_tool_call_ids:
                # Valid: has a parent assistant → keep as-is
                repaired.append(msg)
            elif tool_call_id:
                # Orphaned: no assistant declared this tool_call_id.
                # Convert to user message to preserve content without
                # violating the API contract.
                _content = str(msg.get("content", ""))[:800]
                repaired.append({
                    "role": "user",
                    "content": (
                        f"[Tool result (reconstructed — original "
                        f"tool_call_id={tool_call_id})]\n{_content}"
                    ),
                })
            else:
                # tool message without tool_call_id — also orphaned.
                _content = str(msg.get("content", ""))[:800]
                repaired.append({
                    "role": "user",
                    "content": f"[Tool result (reconstructed)]\n{_content}",
                })
        else:
            # system / user / other — keep as-is
            repaired.append(msg)

    # --- Pass 2: ensure non-empty assistant content ---
    # Some APIs (GLM-5.1, etc.) reject assistant messages with empty content.
    for msg in repaired:
        if msg.get("role") == "assistant":
            _c = msg.get("content")
            if _c is None or (isinstance(_c, str) and not _c.strip()):
                # Keep None if tool_calls present (valid for many APIs),
                # otherwise set to a minimal placeholder.
                if not msg.get("tool_calls"):
                    msg["content"] = " "

    # --- Pass 3: DeepSeek reasoning_content ---
    _model_lower = model_name.lower()
    if not _model_lower:
        try:
            import builtins as _bi
            _model_lower = str(
                getattr(
                    getattr(_bi, "_AGENT_CONFIG", object()),
                    "MODEL_NAME", ""
                )
            ).lower()
        except Exception:
            pass

    if "deepseek" in _model_lower:
        # DeepSeek reasoning mode requires reasoning_content on every assistant
        # message round-tripped back. Compression / repair can drop the field
        # on synthesized assistant messages (e.g. emergency-prune fillers,
        # placeholder content). Some DeepSeek revisions reject whitespace-only
        # values, so use a short non-empty placeholder.
        _RC_PLACEHOLDER = "[reasoning omitted by compression]"
        for msg in repaired:
            if msg.get("role") == "assistant":
                _rc = msg.get("reasoning_content")
                if _rc is None or (isinstance(_rc, str) and not _rc.strip()):
                    msg["reasoning_content"] = _RC_PLACEHOLDER

    # --- Pass 4: ensure first non-system message is 'user' ---
    # Strict APIs (GLM-5.1, Z.AI, etc.) reject sequences where the first
    # non-system message is 'assistant' or 'tool'.  After compression the
    # kept recent messages are typically the ReAct tail:
    #   [assistant, tool, assistant, tool]
    # which yields  system → assistant → …  → HTTP 400 code 1214.
    # Fix: prepend a synthetic user message so the sequence starts with
    #   system → user → assistant → …
    _first_non_sys = None
    for _i, _m in enumerate(repaired):
        if _m.get("role") != "system":
            _first_non_sys = _i
            break
    if _first_non_sys is not None:
        _first_role = repaired[_first_non_sys].get("role", "")
        if _first_role != "user":
            # Build a synthetic user message from the system summary context
            # so the model has enough context to continue the task.
            _synth_content = (
                "[Context restored after compression. Continue the current task.]\n"
            )
            # Try to extract a task hint from the system message
            for _sm in repaired[:_first_non_sys]:
                _sc = str(_sm.get("content", ""))
                # Pull the first line that looks like a goal/task instruction
                for _line in _sc.split("\n"):
                    _line = _line.strip().lstrip("#-= ").strip()
                    if _line and len(_line) > 10:
                        _synth_content += _line[:300]
                        break
                if len(_synth_content) > 100:
                    break

            repaired.insert(_first_non_sys, {
                "role": "user",
                "content": _synth_content,
            })

    # --- Pass 5: orphaned assistant tool_calls (reverse of Pass 1) ---
    # An assistant message with tool_calls must be IMMEDIATELY followed by tool
    # messages covering every declared tool_call_id. Compression can strip some
    # or all of those tool responses, leaving the assistant "dangling" — which
    # causes HTTP 400 on DeepSeek and other strict APIs.
    # Fix: strip tool_calls from the assistant; convert any partially-present
    # tool messages (now orphaned) to user messages.
    _final: List[Dict] = []
    _pi = 0
    while _pi < len(repaired):
        _m = repaired[_pi]
        if _m.get("role") == "assistant" and _m.get("tool_calls"):
            _expected_ids = {
                tc.get("id")
                for tc in _m["tool_calls"]
                if isinstance(tc, dict) and tc.get("id")
            }
            # Peek at immediately-following tool messages
            _pj = _pi + 1
            _found_ids: set = set()
            while _pj < len(repaired) and repaired[_pj].get("role") == "tool":
                _tid = repaired[_pj].get("tool_call_id")
                if _tid:
                    _found_ids.add(_tid)
                _pj += 1

            if _expected_ids and not _expected_ids.issubset(_found_ids):
                # Insufficient tool responses — strip tool_calls to prevent 400
                _stripped = {k: v for k, v in _m.items() if k != "tool_calls"}
                if not str(_stripped.get("content") or "").strip():
                    _stripped["content"] = "[Tool calls made; responses unavailable after compression]"
                _final.append(_stripped)
                # Convert immediately-following tool messages to user messages
                # (they're now orphaned since we removed their parent's tool_calls)
                _pi += 1
                while _pi < len(repaired) and repaired[_pi].get("role") == "tool":
                    _tc_msg = repaired[_pi]
                    _final.append({
                        "role": "user",
                        "content": (
                            f"[Tool result (reconstructed after compression)]: "
                            f"{str(_tc_msg.get('content', ''))[:400]}"
                        ),
                    })
                    _pi += 1
                continue
            else:
                _final.append(_m)
        else:
            _final.append(_m)
        _pi += 1
    repaired = _final

    # --- Pass 6: collapse consecutive same-role messages ---
    # Strict APIs (GLM-5.1, Anthropic) reject A→A→A or U→U→U sequences
    # without the alternating role between them.  This can happen when
    # react_loop appends multiple assistant responses without tool calls
    # (loop detected in Pass B fix above) or when context injection
    # creates consecutive user messages.  Merge them by concatenating
    # content with a separator.
    _collapsed: List[Dict] = []
    for _m in repaired:
        _role = _m.get("role")
        if (
            _collapsed
            and _collapsed[-1].get("role") == _role
            and _role in ("user", "assistant")
        ):
            _prev = _collapsed[-1]
            _prev["content"] = _merge_message_content(
                _prev.get("content"),
                _m.get("content"),
            )
            # Preserve tool_calls if either has them
            if _m.get("tool_calls"):
                _prev["tool_calls"] = _m["tool_calls"]
            # Preserve last reasoning_content
            if _m.get("reasoning_content"):
                _prev["reasoning_content"] = _m["reasoning_content"]
        else:
            _collapsed.append(_m)
    repaired = _collapsed

    # --- Pass 7: dedupe consecutive identical assistant+tool pairs ---
    # react_loop can replay the same Action multiple times when the LLM
    # repeats itself.  Compression preserves all of them, leaving the API
    # with a redundant (and sometimes malformed) tail.  Detect identical
    # adjacent (assistant→tool) pairs by content fingerprint and keep only
    # the first occurrence.
    def _fp(_msg: Dict) -> str:
        _c = _message_text(_msg)[:400]
        _r = _msg.get("role", "")
        _t = ""
        _tcs = _msg.get("tool_calls") or []
        if _tcs:
            try:
                _t = "|".join(
                    (tc.get("function", {}).get("name", "") + ":" +
                     str(tc.get("function", {}).get("arguments", ""))[:200])
                    for tc in _tcs if isinstance(tc, dict)
                )
            except Exception:
                _t = ""
        return f"{_r}::{_c}::{_t}"

    _deduped: List[Dict] = []
    _i2 = 0
    while _i2 < len(repaired):
        _m = repaired[_i2]
        # Look for assistant→(tool×N) block; dedupe against previous identical block
        if _m.get("role") == "assistant" and _i2 + 1 < len(repaired):
            _block_end = _i2 + 1
            while _block_end < len(repaired) and repaired[_block_end].get("role") == "tool":
                _block_end += 1
            _cur_block_fp = _fp(_m) + "##" + "||".join(_fp(repaired[k]) for k in range(_i2 + 1, _block_end))
            # Compare with last block in _deduped
            if _deduped and len(_deduped) >= (_block_end - _i2):
                _dedup_start = len(_deduped) - (_block_end - _i2)
                if _deduped[_dedup_start].get("role") == "assistant":
                    _prev_fp = _fp(_deduped[_dedup_start]) + "##" + "||".join(
                        _fp(_deduped[k]) for k in range(_dedup_start + 1, len(_deduped))
                    )
                    if _prev_fp == _cur_block_fp:
                        # identical block — skip
                        _i2 = _block_end
                        continue
            _deduped.extend(repaired[_i2:_block_end])
            _i2 = _block_end
        else:
            _deduped.append(_m)
            _i2 += 1
    repaired = _deduped

    # --- Pass 8: final assistant content/tool_calls sanity scrub ---
    # After all transforms above, an assistant message can still slip
    # through with content=None AND tool_calls=[] (or tool_calls full of
    # entries with no `id`).  Strict APIs (GLM 1214) reject this.
    # This pass is the last line of defense: every assistant message
    # MUST have a non-empty string content.  GLM-5.1 rejects content=null
    # even when tool_calls is present (observed in mini_cpu run logs).
    # Always force content to a non-empty string regardless of tool_calls.
    for _m in repaired:
        if _m.get("role") != "assistant":
            continue
        _c = _m.get("content")
        _tcs = _m.get("tool_calls")
        # Normalize tool_calls: drop entries without id, drop empty list
        if isinstance(_tcs, list):
            _valid_tcs = [
                tc for tc in _tcs
                if isinstance(tc, dict) and tc.get("id")
            ]
            if not _valid_tcs:
                _m.pop("tool_calls", None)
                _tcs = None
            else:
                _m["tool_calls"] = _valid_tcs
                _tcs = _valid_tcs
        # Force non-empty string content ALWAYS (GLM-5.1 rejects null
        # content even with valid tool_calls; OpenAI accepts but space
        # placeholder is harmless there).
        if _c is None or not isinstance(_c, str) or _c == "None":
            _m["content"] = " " if _tcs else " "
        elif not _c.strip():
            _m["content"] = " "

    # --- Pass 9: scrub user/tool messages with null content too ---
    # Strict APIs reject any message with content=null.
    for _m in repaired:
        _r = _m.get("role")
        if _r in ("user", "tool"):
            _c = _m.get("content")
            if _c is None or _c == "None":
                _m["content"] = " "
            elif isinstance(_c, list) and _r == "user":
                pass
            elif not isinstance(_c, str):
                _m["content"] = str(_c)

    return repaired


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


def _strip_code_fences(text: str) -> str:
    """Remove fenced code blocks (```...```) and inline code (`...`) so that
    a "?" inside a code sample doesn't trigger the awaiting-user heuristic.
    """
    if not text:
        return text
    # Triple-backtick fences (multi-line). Use a non-greedy DOTALL match.
    text = _re.sub(r"```.*?```", " ", text, flags=_re.DOTALL)
    # Inline single-backtick code spans.
    text = _re.sub(r"`[^`\n]+`", " ", text)
    return text


def _detect_awaiting_user(messages: List[Dict[str, Any]]) -> bool:
    """Detect whether the conversation ended with the assistant asking
    the user a question that was never answered.

    Heuristic: walk backward from the tail, skipping system/tool frames.
    - If we see a user message with real content first → not awaiting.
    - If we see an assistant message first AND its text (with code blocks
      stripped) contains a question mark or an await-prompt phrase →
      awaiting user input.
    Otherwise → not awaiting.

    Code fences are stripped before scanning because "?" inside ``` python
    code samples (e.g. "if x?:" or "user.get('?')") is a false positive
    for the question-mark check.
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
            scan_text = _strip_code_fences(text)
            low = scan_text.lower()
            if "?" in scan_text:
                return True
            return any(p in low for p in _AWAIT_PATTERNS)
    return False


# ---------------------------------------------------------------------------
# Core compression functions
# ---------------------------------------------------------------------------

# Reasoning content preservation during compression.
# DeepSeek/GLM chain-of-thought is stored in reasoning_content on assistant
# messages.  Without including it in the text sent to the compressor LLM,
# the compressed summary loses the model's internal decision-making context,
# which degrades tool-calling accuracy on large tasks (observed in CPU req-gen).
_REASONING_PREFIX = "[assistant reasoning] "
_REASONING_MAX_CHARS = 800  # keep first ~400 + last ~400 chars (head+tail strategy)


def _serialize_tool_calls(tool_calls: Any) -> str:
    """Render an assistant message's native tool_calls as `[name(arg=val, ...)]` text.

    Empty-content assistant turns that only carry tool_calls would otherwise
    disappear from the compression input — the summarizer would never see
    that the agent took an action.  Both _compress_single and _compress_chunked
    use this so chunked mode preserves the same fidelity as single-pass.
    """
    if not tool_calls or not isinstance(tool_calls, list):
        return ""
    calls: list = []
    for tc in tool_calls:
        if not isinstance(tc, dict):
            continue
        fn = tc.get("function", {})
        name = fn.get("name", "?")
        args_raw = fn.get("arguments", "{}")
        try:
            args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
            arg_str = ", ".join(
                f"{k}={repr(v)[:60]}"
                for k, v in (args.items() if isinstance(args, dict) else [])
            )
        except Exception:
            arg_str = str(args_raw)[:80]
        calls.append(f"{name}({arg_str})")
    if not calls:
        return ""
    return "[" + ", ".join(calls) + "]"

def _resolve_compress_char_budget(cfg: Any = None) -> int:
    """Decide how many characters of conversation_text to feed the summarizer.

    Old behavior was a hardcoded 80_000 (~20K tokens). On a 128K-token model
    that capped input at ~16% of the window, dropping the middle of long
    sessions via head+tail truncation. Scaling with MAX_CONTEXT_TOKENS keeps
    long sessions intact while leaving room for the prompt + output budget.

    Order of resolution:
      1. cfg.COMPRESSION_INPUT_MAX_CHARS  (explicit override, 0 = use default)
      2. cfg.MAX_CONTEXT_TOKENS * 4 * COMPRESSION_INPUT_BUDGET_RATIO (default 0.5)
      3. fallback to 80_000
    """
    try:
        explicit = int(getattr(cfg, "COMPRESSION_INPUT_MAX_CHARS", 0) or 0)
        if explicit > 0:
            return explicit
        ctx_tokens = int(getattr(cfg, "MAX_CONTEXT_TOKENS", 0) or 0)
        ratio = float(getattr(cfg, "COMPRESSION_INPUT_BUDGET_RATIO", 0.5) or 0.5)
        if ctx_tokens > 0:
            # 4 chars/token heuristic; cap ratio to a safe band
            ratio = max(0.2, min(0.8, ratio))
            return max(20_000, int(ctx_tokens * 4 * ratio))
    except Exception:
        pass
    return 80_000


def _compress_single(
    messages: List[Dict],
    *,
    llm_call_fn: Callable,
    instruction: Optional[str] = None,
    cfg: Any = None,
) -> Dict[str, Any]:
    """Single-pass compression: summarize all messages at once.

    Args:
        messages: Messages to compress.
        llm_call_fn: Callable(messages, **kwargs) -> Iterable[str | tuple].
            Yields text chunks or ('reasoning', ...) tuples (which are ignored).
        instruction: Optional custom summarization prompt.
        cfg: Config namespace (for COMPRESSION_INPUT_MAX_CHARS / MAX_CONTEXT_TOKENS).

    Returns:
        A single system message dict containing the summary.
    """
    MAX_COMPRESS_CHARS = _resolve_compress_char_budget(cfg)
    summary_prompt = instruction if instruction else STRUCTURED_SUMMARY_PROMPT

    conversation_text = ""
    for m in messages:
        role = m.get("role", "unknown")
        if role == "tool":
            # Tool result — include tool name if available for context
            content = _smart_truncate(_message_text(m), role, cfg=cfg)
            tool_name = m.get("name", "")
            if tool_name:
                conversation_text += f"tool({tool_name}): {content}\n"
            else:
                conversation_text += f"observation: {content}\n"
            continue
        content = _smart_truncate(_message_text(m), role, cfg=cfg)

        # Tool-calling assistant turns have no text — annotate with func(args) so the
        # summarizing LLM knows exactly what was called and with what arguments.
        if role == "assistant" and not content.strip():
            content = _serialize_tool_calls(m.get("tool_calls"))
            if not content.strip():
                continue  # nothing to add (no tool_calls at all)

        # Preserve reasoning_content for assistant messages (DeepSeek/GLM chain-of-thought)
        reasoning_text = ""
        reasoning = m.get("reasoning_content")
        if reasoning and role == "assistant":
            reasoning_str = str(reasoning).strip()
            if len(reasoning_str) > _REASONING_MAX_CHARS:
                half = _REASONING_MAX_CHARS // 2
                reasoning_str = reasoning_str[:half] + "\n…[reasoning truncated]…\n" + reasoning_str[-half:]
            reasoning_text = _REASONING_PREFIX + reasoning_str + "\n"

        conversation_text += f"{role}: {reasoning_text}{content}\n"

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

    # Real-message count excludes the synthetic [Prior summary context] system
    # message that compress_history may prepend to old_msgs as a context hint.
    # Including it inflated the "(N messages)" header by 1 every time prior
    # summaries were merged.
    _real_count = sum(
        1 for _m in messages
        if not (
            _m.get("role") == "system"
            and str(_m.get("content", "")).startswith("[Prior summary context")
        )
    )

    summary_content = ""
    try:
        print(f"  [Compress] Summarizing {_real_count} messages...", end="", flush=True)
        for chunk in llm_call_fn(summary_request, suppress_spinner=True):
            if isinstance(chunk, tuple) and chunk[0] == "reasoning":
                continue
            summary_content += chunk
        print(f" done ({len(summary_content):,} chars)")

        return {
            "role": "system",
            "content": f"[Previous Conversation Summary ({_real_count} messages)]: {summary_content}",
        }
    except Exception as e:
        print(f"\n  [Compress] Failed: {e}")
        # Return all messages as a single system message on failure
        # (was returning messages[0] which dropped ALL other messages)
        if not messages:
            return {"role": "system", "content": "[Compression failed]"}
        combined = "\n".join(
            f"{m.get('role', 'unknown')}: {_message_text(m)[:500]}"
            for m in messages
        )
        return {
            "role": "system",
            "content": f"[Previous Conversation Summary ({_real_count} messages, compression failed)]: {combined}",
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
            if role == "tool":
                content = _smart_truncate(_message_text(m), role, cfg=cfg)
                tool_name = m.get("name", "")
                if tool_name:
                    conversation_text += f"tool({tool_name}): {content}\n"
                else:
                    conversation_text += f"observation: {content}\n"
                continue
            content = _smart_truncate(_message_text(m), role, cfg=cfg)

            # Tool-calling assistant turns have no text — annotate with func(args)
            # so the summarizing LLM still sees what action the agent took.
            if role == "assistant" and not content.strip():
                content = _serialize_tool_calls(m.get("tool_calls"))
                if not content.strip():
                    continue

            # Preserve reasoning_content for assistant messages
            reasoning_text = ""
            reasoning = m.get("reasoning_content")
            if reasoning and role == "assistant":
                reasoning_str = str(reasoning).strip()
                if len(reasoning_str) > _REASONING_MAX_CHARS:
                    half = _REASONING_MAX_CHARS // 2
                    reasoning_str = reasoning_str[:half] + "\n…[reasoning truncated]…\n" + reasoning_str[-half:]
                reasoning_text = _REASONING_PREFIX + reasoning_str + "\n"
            conversation_text += f"{role}: {reasoning_text}{content}\n"

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
                    f"{m.get('role', '?')}: {_message_text(m)[:500]}"
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
        content = _message_text(m)[:600]
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
    emit_summary: bool = True,
    raise_on_llm_failure: bool = False,
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
        emit_summary: If True, surface the generated compression markdown via
            emit_fn/stdout. Auto-compaction callers should set this False so an
            internal context-maintenance step does not appear as an assistant
            answer in chat.
        raise_on_llm_failure: If True, raise CompressionLLMError when the
            summarizer LLM call fails (instead of returning a degraded
            truncation summary). The web /compact path opts in so it can fall
            back to the deterministic compactor with an honest message; the
            CLI/worker loop leaves this False to survive transient LLM errors.

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

    # Separate system vs regular messages.
    # Prior summaries are extracted from system messages in two cases:
    #   (a) separate system message with a generated prefix  → extract text, drop message
    #   (b) embedded section inside a consolidated message   → strip section, keep base
    # Extracted text is injected as context into the new compression so the LLM produces
    # ONE unified summary — no accumulation across multiple compressions.
    _GENERATED_PREFIXES = (
        "[Previous Conversation Summary",
        "[Ongoing Task]",
        "[Todo Status]",
        "[Todo ",
        "[Summary chunk",
        "[Chunk compression failed",
        "[FROZEN SUMMARY",
    )
    _SUMMARY_SECTION = "===== CONVERSATION SUMMARY ====="
    _PRESERVED_SECTION = "===== PRESERVED CONTEXT ====="
    import re as _re_local
    _SECTION_RE = _re_local.compile(r'\n===== [A-Z]')

    system_msgs: List[Dict] = []
    prior_summary_parts: List[str] = []

    for _sm in messages:
        if _sm.get("role") != "system":
            continue
        _sc = str(_sm.get("content", ""))

        # Case (a): standalone generated summary/todo message — extract for context only
        if any(_sc.startswith(p) for p in _GENERATED_PREFIXES):
            _clean = _sc
            if _clean.startswith("[FROZEN SUMMARY - preserved verbatim] "):
                _clean = _clean[len("[FROZEN SUMMARY - preserved verbatim] "):]
            prior_summary_parts.append(_clean)
            continue

        # Case (b): consolidated message may embed a CONVERSATION SUMMARY section — strip it
        _cleaned_sc = _sc
        for _sec_marker in (_SUMMARY_SECTION, _PRESERVED_SECTION):
            if _sec_marker not in _cleaned_sc:
                continue
            _idx = _cleaned_sc.index(_sec_marker)
            _after_marker = _cleaned_sc[_idx + len(_sec_marker):]
            _nxt = _SECTION_RE.search(_after_marker)
            if _nxt:
                prior_summary_parts.append(_after_marker[:_nxt.start()].strip())
                _cleaned_sc = (_cleaned_sc[:_idx].rstrip() + "\n\n" + _after_marker[_nxt.start():].lstrip()).strip()
            else:
                prior_summary_parts.append(_after_marker.strip())
                _cleaned_sc = _cleaned_sc[:_idx].rstrip()

        system_msgs.append(dict(_sm, content=_cleaned_sc.strip()))

    regular_msgs = [m for m in messages if m.get("role") != "system"]

    # Extract !important messages (preserve them)
    important_msgs = []
    other_msgs = []
    for msg in regular_msgs:
        content = _message_text(msg)
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
            fallback_keep = min(keep_recent or 4, len(other_msgs))
            if len(other_msgs) <= fallback_keep:
                print(f"[System] History too short to compress ({len(other_msgs)} messages).")
                return messages
            recent_msgs = other_msgs[-fallback_keep:]
            old_msgs = other_msgs[:-fallback_keep]
            print(
                f"[System] Single-turn fallback: compressing {len(old_msgs)} messages, "
                f"keeping {len(recent_msgs)}"
            )

        # Safety cap: if turn protection yields too few old_msgs (poor compression ratio),
        # override with the standard keep_recent split to guarantee meaningful compression.
        _effective_keep = keep_recent or 4
        if len(old_msgs) < _effective_keep and len(other_msgs) > _effective_keep:
            recent_msgs = other_msgs[-_effective_keep:]
            old_msgs = other_msgs[:-_effective_keep]
            print(
                f"[System] Turn protection override: compressing {len(old_msgs)}, "
                f"keeping {len(recent_msgs)} (keep_recent={_effective_keep})"
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

        # Option 1: Always preserve the most recent user message in recent_msgs.
        # Without this, post-compression tail can be all assistant/tool which
        # gives the LLM no driving "intent" — it produces a recap instead of
        # action.  If recent_msgs has no user message, expand backward to the
        # latest user message in old_msgs.
        if recent_msgs and not any(m.get("role") == "user" for m in recent_msgs):
            _last_user_idx = next(
                (i for i in range(len(old_msgs) - 1, -1, -1)
                 if old_msgs[i].get("role") == "user"),
                None
            )
            if _last_user_idx is not None:
                recent_msgs = old_msgs[_last_user_idx:] + recent_msgs
                old_msgs = old_msgs[:_last_user_idx]

        if not old_msgs:
            return messages

    # Native tool call pair integrity: ensure no assistant message with tool_calls
    # is split from its corresponding role:tool response messages across the
    # old_msgs/recent_msgs boundary. Find the last assistant-with-tool_calls in
    # old_msgs (could be old_msgs[-1] OR earlier if some sibling tool responses
    # already landed in old_msgs), then absorb any remaining sibling responses
    # that are stuck at the head of recent_msgs.
    if old_msgs and recent_msgs:
        _parent_idx: Optional[int] = None
        for _i in range(len(old_msgs) - 1, -1, -1):
            _r = old_msgs[_i].get("role")
            if _r == "assistant" and old_msgs[_i].get("tool_calls"):
                _parent_idx = _i
                break
            if _r != "tool":
                break  # walked past the contiguous tool-block — no parent here
        if _parent_idx is not None:
            _parent = old_msgs[_parent_idx]
            _all_ids = {
                tc["id"] for tc in _parent["tool_calls"]
                if isinstance(tc, dict) and tc.get("id")
            }
            _already = {
                old_msgs[_j].get("tool_call_id")
                for _j in range(_parent_idx + 1, len(old_msgs))
                if old_msgs[_j].get("role") == "tool"
            }
            _needed_ids = _all_ids - _already
            if _needed_ids:
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

    # Inject prior summaries (extracted from system messages above) as context so
    # the LLM produces ONE unified summary covering all prior + new context.
    if prior_summary_parts:
        _prior_text = "\n\n".join(p for p in prior_summary_parts if p.strip())
        if _prior_text.strip():
            old_msgs = [{"role": "system", "content": f"[Prior summary context — incorporate into new summary]:\n{_prior_text}"}] + old_msgs
            print(f"  [Compress] Merging {len(prior_summary_parts)} prior summary(s) into new compression")

    if not old_msgs:
        print(f"  [Compress] No new messages to compress")

    # Choose compression mode
    mode = cfg.COMPRESSION_MODE.lower() if hasattr(cfg, "COMPRESSION_MODE") else "traditional"

    # Todo preservation
    todo_preservation: List[Dict] = []
    todo_tail_directive: List[Dict] = []
    if todo_tracker and todo_tracker.todos:
        status_icon = {
            "pending": "⏸",
            "in_progress": "▶",
            "completed": "👀",
            "approved": "✅",
            "rejected": "❌",
        }
        status_label = {
            "pending": "pending",
            "in_progress": "in progress",
            "completed": "review",
            "approved": "approved",
            "rejected": "rejected",
        }
        total = len(todo_tracker.todos)
        approved = sum(1 for t in todo_tracker.todos if getattr(t, "status", "") == "approved")
        active = sum(1 for t in todo_tracker.todos if getattr(t, "status", "") != "approved")

        def _todo_wrap(prefix: str, value: str, width: int = 100) -> List[str]:
            text = str(value or "").strip()
            if not text:
                return []
            return textwrap.wrap(
                text,
                width=width,
                initial_indent=prefix,
                subsequent_indent=" " * len(prefix),
                break_long_words=False,
                break_on_hyphens=False,
            )

        todo_lines = [
            "[Todo Status]:",
            f"  progress: {approved}/{total} approved · {active} open",
        ]
        for i, t in enumerate(todo_tracker.todos):
            icon = status_icon.get(t.status, "?")
            label = status_label.get(t.status, t.status)
            title = str(getattr(t, "content", "") or "").strip()
            line_parts = _todo_wrap(f"  {icon} {i+1}. [{label}] ", title, width=106)
            line = "\n".join(line_parts) if line_parts else f"  {icon} {i+1}. [{label}]"
            if t.detail:
                line += "\n" + "\n".join(_todo_wrap("     detail: ", t.detail))
            if t.criteria:
                for _c in t.criteria.splitlines():
                    if _c.strip():
                        line += "\n" + "\n".join(_todo_wrap("     - ", _c.strip()))
            if t.rejection_reason and t.status in ("rejected", "in_progress", "pending"):
                line += "\n" + "\n".join(_todo_wrap("     rejected: ", t.rejection_reason))
            if getattr(t, "notes", None):
                for ni, note in enumerate(t.notes, 1):
                    line += "\n" + "\n".join(_todo_wrap(f"     note {ni}: ", note))
            todo_lines.append(line)
        todo_snapshot = "\n".join(todo_lines)

        # Snapshot stays as system (background context).  The directive
        # ("do TODO #N now") moves to a SEPARATE user-role message at the
        # tail (Option 2) so the LLM treats it as a directive, not buried
        # system context.
        try:
            _has_open_todos = bool(todo_tracker.has_open_items())
        except Exception:
            try:
                from lib.todo_tracker import todo_items_have_open_work
                _has_open_todos = todo_items_have_open_work(getattr(todo_tracker, "todos", []))
            except Exception:
                _has_open_todos = not todo_tracker.is_all_processed()
        if _has_open_todos:
            prompt = todo_tracker.get_continuation_prompt()
            next_idx = todo_tracker._get_next_pending()
            if prompt:
                next_instruction = f"\n[Ongoing Task]: {prompt}"
            elif next_idx is not None:
                todo = todo_tracker.todos[next_idx]
                next_instruction = (
                    f"\n[Ongoing Task]: [Todo {approved}/{total}] Next task ready: {todo.content}\n"
                    f"→ Start with: todo_update(index={next_idx + 1}, status='in_progress')"
                )
            else:
                next_instruction = ""
            # System snapshot only — no directive in system anymore.
            todo_preservation = [
                {"role": "system", "content": todo_snapshot}
            ]
            # Tail directive (USER role) — drives action post-compression.
            if next_instruction.strip():
                todo_tail_directive = [
                    {"role": "user",
                     "content": f"[Resume after compression]{next_instruction}"}
                ]
            else:
                todo_tail_directive = []
        else:
            todo_preservation = [
                {"role": "system", "content": todo_snapshot + "\n[All tasks completed]"}
            ]
            todo_tail_directive = []

    # Compress (skip if all old messages were frozen summaries)
    compressed = None
    llm_failed = False
    if old_msgs:
        try:
            if mode == "chunked":
                print(f"  [Compress] chunked (chunk_size={cfg.COMPRESSION_CHUNK_SIZE})")
                compressed = _compress_chunked(old_msgs, cfg=cfg, llm_call_fn=llm_call_fn, instruction=instruction)
            else:
                compressed = [_compress_single(old_msgs, llm_call_fn=llm_call_fn, instruction=instruction, cfg=cfg)]
        except Exception as exc:
            llm_failed = True
            print(f"  [Compress] LLM compression failed entirely: {exc}")

    # _compress_single / _compress_chunked swallow LLM errors internally and
    # return a char-truncation fallback (preserving content, never raising) so
    # the agent loop survives. That silent substitution is exactly what makes a
    # web /compact look like a successful "N% reduction" whose body is raw text.
    # Detect the fallback marker so we can (a) warn in the emitted output and
    # (b) re-raise for callers that opt in (the web path) so they can fall back
    # to the deterministic compactor with an honest "AI summary unavailable".
    if _summary_is_llm_fallback(compressed):
        llm_failed = True
    if llm_failed and raise_on_llm_failure:
        raise CompressionLLMError(
            "summarizer LLM call failed; produced a non-LLM truncation fallback"
        )

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

    # Tail directive: when a TODO is active, the directive lives at the
    # very end as a user-role message so the LLM treats it as the next
    # action to take, not background context.  When all tasks are done
    # or there's no tracker, this is empty.
    if compressed is not None:
        raw_history = (
            system_msgs + important_msgs + compressed
            + awaiting_note + todo_preservation + recent_msgs + todo_tail_directive
        )
    else:
        raw_history = (
            system_msgs + important_msgs
            + awaiting_note + todo_preservation + recent_msgs + todo_tail_directive
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

        # Append file access log (config: COMPRESSION_TOOL_CALL_PATHS, 0=disable)
        try:
            _n = int(getattr(cfg, 'COMPRESSION_TOOL_CALL_PATHS', 0))
            if _n > 0:
                _file_log = _collect_working_paths_from_log(max_entries=_n)
                if _file_log:
                    _ordered_parts.append("===== WORKING PATHS (recent tool calls) =====\n" + _file_log)
        except Exception as _fle:
            print(f"  [Compress] file log collection failed: {_fle}")

        _merged = "\n\n".join(_ordered_parts)
        new_history = [{"role": "system", "content": _merged}] + _non_sys
    else:
        new_history = _non_sys

    # --- Post-compression validation and repair ---
    # Fix orphaned tool messages (HTTP 400 "tool must be response to tool_calls")
    # and DeepSeek reasoning_content (HTTP 400 "reasoning_content must be passed back").
    _model_name = str(getattr(cfg, 'MODEL_NAME', ''))
    new_history = _validate_and_repair_sequence(
        new_history, model_name=_model_name
    )

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
        # Re-validate after emergency pruning (pruning can create new orphans)
        new_history = _validate_and_repair_sequence(
            new_history, model_name=_model_name
        )
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
            _im_content = _message_text(_im)[:500]
            _imp_lines.append("**[" + _im_role + "]** " + _im_content)
        md_parts.append("## Important Messages (" + str(len(important_msgs)) + ")\n\n" + "\n\n".join(_imp_lines))

    # 5. Recent Messages (brief preview)
    if recent_msgs:
        _rm_lines = []
        for _rm in recent_msgs:
            _rm_role = _rm.get("role", "unknown")
            _rm_content = _message_text(_rm)[:200]
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

    # Surface a swallowed LLM failure at the top of the emitted output so the
    # user is not misled by the "N% reduction" stats below it. The history was
    # still reduced (via raw truncation), but it is NOT an AI summary.
    if llm_failed:
        md_parts.insert(
            0,
            "## ⚠️ AI Summary Unavailable\n\n"
            "The summarizer LLM call failed, so the conversation was reduced with a "
            "raw text truncation instead of an AI summary. Check the model / API "
            "configuration (model name, base URL, API key) and re-run /compact.",
        )

    if emit_summary and md_parts:
        md = "\n\n---\n\n".join(md_parts) + "\n"
        if emit_fn:
            emit_fn(md)
        else:
            print(md)

    return new_history
