"""
Observation processing for ReAct agent loop.

Extracted from src/main.py. Handles large observation truncation and
context-overflow protection before appending observations to message history.

The compress_fn parameter breaks the circular dependency on main.compress_history.
"""
from typing import Any, Callable, Dict, List, Optional


def process_observation(
    observation: str,
    messages: List[Dict[str, Any]],
    cfg=None,
    estimate_tokens_fn: Optional[Callable] = None,
    compress_fn: Optional[Callable] = None,
    todo_tracker=None,
) -> List[Dict[str, Any]]:
    """Process an observation before adding it to message history.

    Handles large file truncation and context management.

    Args:
        observation:        Raw observation string from a tool.
        messages:           Current message history (modified in place via append).
        cfg:                Config namespace (defaults to importing config module).
        estimate_tokens_fn: Callable(msg) -> int. Defaults to llm_client.estimate_message_tokens.
        compress_fn:        Callable(messages, **kw) -> messages. Called when context
                            overflows threshold. If None, compression is skipped even
                            when ENABLE_COMPRESSION is True.
        todo_tracker:       Optional TodoTracker (passed through to compress_fn).

    Returns:
        Updated messages list with observation appended.
    """
    if cfg is None:
        import config as cfg  # type: ignore

    if estimate_tokens_fn is None:
        from llm_client import estimate_message_tokens as estimate_tokens_fn  # type: ignore

    limit_tokens = cfg.MAX_CONTEXT_TOKENS
    threshold_tokens = int(limit_tokens * cfg.COMPRESSION_THRESHOLD)

    observation_msg: Dict[str, Any] = {"role": "user", "content": f"Observation: {observation}"}
    observation_tokens = estimate_tokens_fn(observation_msg)

    # ── Step 1: Truncate if observation itself is too large (> 30% of limit) ──
    if observation_tokens > limit_tokens * 0.3:
        original_size = len(observation)
        lines = observation.split('\n')
        total_lines = len(lines)

        PREVIEW_LINES = cfg.LARGE_FILE_PREVIEW_LINES
        preview_lines = lines[:PREVIEW_LINES]
        preview = '\n'.join(preview_lines)

        MAX_PREVIEW_CHARS = cfg.MAX_OBSERVATION_CHARS // 2
        if len(preview) > MAX_PREVIEW_CHARS:
            preview = preview[:MAX_PREVIEW_CHARS] + f"\n... [Preview truncated at {MAX_PREVIEW_CHARS} chars] ..."

        MAX_READABLE_LINES = cfg.MAX_OBSERVATION_CHARS // 80

        observation = (
            f"[File Preview - Too large to display completely]\n\n"
            f"Showing first {PREVIEW_LINES} lines "
            f"(Total: {total_lines:,} lines, {original_size:,} characters)\n\n"
            f"--- BEGIN PREVIEW ---\n"
            f"{preview}\n"
            f"--- END PREVIEW ---\n\n"
            f"\U0001f4a1 File is too large for full display. "
            f"You can read up to ~{MAX_READABLE_LINES} lines at a time.\n\n"
            f"To read specific sections:\n"
            f"1. Use read_lines(path, start_line, end_line)\n"
            f"   Examples:\n"
            f"   - read_lines(path, start_line=100, end_line=200)\n"
            f"   - read_lines(path, start_line={max(1, total_lines-100)}, "
            f"end_line={total_lines})  # Last 100 lines\n\n"
            f"2. Use grep_file(pattern, path) to search for patterns\n"
            f"   Example:\n"
            f"   - grep_file(pattern=\"module\\\\s+\\\\w+\", path)   # Find modules\n"
            f"   - grep_file(pattern=\"always.*@\", path)        # Find always blocks\n\n"
            f"3. Ask the user which part they want to see\n"
        )
        observation_msg = {"role": "user", "content": f"Observation: {observation}"}
        observation_tokens = estimate_tokens_fn(observation_msg)

        try:
            from lib.display import Color  # type: ignore
            print(Color.warning(
                f"[System] \u26a0\ufe0f  Large observation truncated: "
                f"{original_size:,} chars \u2192 {cfg.MAX_OBSERVATION_CHARS:,} chars "
                f"({total_lines:,} lines total)"
            ))
        except ImportError:
            print(
                f"[System] Large observation truncated: "
                f"{original_size:,} chars -> {cfg.MAX_OBSERVATION_CHARS:,} chars "
                f"({total_lines:,} lines total)"
            )

    # ── Step 2: Compress if total context exceeds threshold ──
    current_tokens = sum(estimate_tokens_fn(m) for m in messages)
    total_tokens = current_tokens + observation_tokens

    if total_tokens > threshold_tokens and cfg.ENABLE_COMPRESSION and compress_fn is not None:
        try:
            from lib.display import Color  # type: ignore
            print(Color.warning(
                f"\n[System] \u26a0\ufe0f  Adding observation would exceed threshold "
                f"({total_tokens:,} > {threshold_tokens:,} tokens)"
            ))
            print(Color.info("[System] Compressing history before adding observation..."))
        except ImportError:
            print(f"[System] Compressing history (tokens: {total_tokens:,} > {threshold_tokens:,})")

        messages = compress_fn(messages, todo_tracker=todo_tracker, force=True, quiet=True)

        current_tokens = sum(estimate_tokens_fn(m) for m in messages)
        total_tokens = current_tokens + observation_tokens

        # Force-truncate if still exceeding after compression
        if total_tokens > threshold_tokens:
            max_safe_tokens = int(limit_tokens * 0.2)
            max_safe_chars = max_safe_tokens * 4
            original_size = len(observation)

            if len(observation) > max_safe_chars:
                observation = (
                    observation[:max_safe_chars]
                    + f"\n\n[Observation truncated: {original_size:,} \u2192 {max_safe_chars:,} chars "
                    f"to prevent context overflow]"
                )
                observation_msg = {"role": "user", "content": f"Observation: {observation}"}
                observation_tokens = estimate_tokens_fn(observation_msg)
                try:
                    from lib.display import Color  # type: ignore
                    print(Color.warning(f"[System] \u26a0\ufe0f  Still exceeding threshold. Force truncating..."))
                    print(Color.info(f"[System] Observation truncated to {observation_tokens:,} tokens"))
                except ImportError:
                    print(f"[System] Observation force-truncated to {observation_tokens:,} tokens")

    # Append action reminder so the model sees it as the last tokens before generating.
    # More effective than system prompt alone — system prompt gets buried in long context.
    # Note: codex/Responses API models respond better to direct instructions without
    # the "Action: tool_name(param=value)" template (they tend to echo it literally).
    if getattr(cfg, "ACTION_REMINDER", True):
        reminder = getattr(
            cfg,
            "ACTION_REMINDER_TEXT",
            "If further action is needed, output it now: Action: tool_name(param=value)",
        )
        # For codex/Responses API models, use a simpler reminder that won't be echoed
        try:
            from src.llm_client import is_responses_api_model
            if is_responses_api_model():
                reminder = "Continue with the next tool call if needed."
                if getattr(cfg, "DEBUG_MODE", False):
                    print("[DEBUG] Codex mode: simplified action reminder")
        except ImportError:
            pass
        observation_msg["content"] += f"\n\n[System] {reminder}"

    messages.append(observation_msg)
    return messages
