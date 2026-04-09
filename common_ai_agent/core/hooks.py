"""
Hook System for Common AI Agent v2

ReAct 루프의 lifecycle에 훅을 삽입하여 context 관리, tool output 제한,
자동 continuation 등을 처리하는 플러그인 시스템.

7개 Hook Point:
- BEFORE_LLM_CALL: context 압축, skill 주입
- AFTER_LLM_CALL: todo continuation 체크
- BEFORE_TOOL_EXEC: 권한 체크
- AFTER_TOOL_EXEC: tool output truncation
- ON_ERROR: emergency recovery
- ON_SESSION_START: 초기화 및 설정
- ON_SESSION_END: cleanup
"""

import builtins
import time
import re
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set


def _get_hook_message(key: str, default: str, **kwargs) -> str:
    """
    Look up a hook message template from the active workspace, falling back to default.
    Templates support str.format(**kwargs) substitution.
    The workspace loader stores messages in builtins._WORKSPACE_HOOK_MESSAGES
    to avoid circular imports.
    """
    try:
        msgs = getattr(builtins, "_WORKSPACE_HOOK_MESSAGES", {})
        tmpl = msgs.get(key, "")
        if tmpl:
            return tmpl.format(**kwargs) if kwargs else tmpl
    except Exception:
        pass
    return default.format(**kwargs) if kwargs else default


# ============================================================
# Hook Points
# ============================================================

class HookPoint(Enum):
    BEFORE_LLM_CALL = "before_llm_call"
    AFTER_LLM_CALL = "after_llm_call"
    BEFORE_TOOL_EXEC = "before_tool_exec"
    AFTER_TOOL_EXEC = "after_tool_exec"
    ON_ERROR = "on_error"
    ON_SESSION_START = "on_session_start"
    ON_SESSION_END = "on_session_end"


# ============================================================
# Hook Context (passed to each hook)
# ============================================================

@dataclass
class HookContext:
    """Hook에 전달되는 컨텍스트 데이터"""
    # BEFORE/AFTER_LLM_CALL
    messages: Optional[List[Dict]] = None

    # BEFORE/AFTER_TOOL_EXEC
    tool_name: Optional[str] = None
    tool_args: Optional[str] = None
    tool_output: Optional[str] = None

    # Context management
    max_context_chars: int = 512000
    compression_threshold: float = 0.80

    # ON_ERROR
    error: Optional[Exception] = None
    error_traceback: Optional[str] = None

    # Metadata
    iteration: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# Hook Registry
# ============================================================

class HookRegistry:
    """
    Hook 등록 및 실행 관리.

    각 HookPoint에 여러 hook을 등록할 수 있으며,
    등록 순서대로 실행됨. 각 hook은 context를 변환하여 반환.

    Usage:
        registry = HookRegistry()
        registry.register(HookPoint.AFTER_TOOL_EXEC, tool_output_truncator)
        ctx = registry.run(HookPoint.AFTER_TOOL_EXEC, HookContext(tool_output="..."))
    """

    def __init__(self):
        self._hooks: Dict[HookPoint, List[Callable]] = {
            point: [] for point in HookPoint
        }
        self._enabled = True

    def register(self, point: HookPoint, hook_fn: Callable, priority: int = 100):
        """
        Hook 등록.

        Args:
            point: Hook point
            hook_fn: (HookContext) -> HookContext
            priority: 낮을수록 먼저 실행 (default 100)
        """
        self._hooks[point].append((priority, hook_fn))
        # Sort by priority
        self._hooks[point].sort(key=lambda x: x[0])

    def run(self, point: HookPoint, context: HookContext) -> HookContext:
        """
        해당 point의 모든 hook을 순서대로 실행.

        Args:
            point: Hook point
            context: 현재 컨텍스트

        Returns:
            변환된 HookContext
        """
        if not self._enabled:
            return context

        for priority, hook_fn in self._hooks[point]:
            try:
                result = hook_fn(context)
                if result is not None:
                    context = result
            except Exception as e:
                # Hook 실패는 무시하되 로깅
                print(f"[Hook] Warning: {hook_fn.__name__} failed: {e}")

        return context

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False

    @property
    def is_enabled(self) -> bool:
        return self._enabled


# ============================================================
# Built-in Hook: ToolOutputTruncator
# ============================================================

# Tool별 최대 출력 길이 (chars)
TOOL_OUTPUT_LIMITS = {
    "read_file": 50000,      # ~12.5K tokens
    "read_lines": 50000,
    "grep_file": 20000,      # ~5K tokens
    "find_files": 10000,     # ~2.5K tokens
    "run_command": 20000,    # ~5K tokens
    "git_diff": 30000,       # ~7.5K tokens
    "git_status": 10000,
    "rag_search": 10000,
    "rag_explore": 10000,
    "list_dir": 10000,
    # Web tools
    "web_fetch": 10000,
    "web_search": 10000,
    # Sub-agent results
    "spawn_explore": 8000,
    "spawn_plan": 8000,
    "background_output": 8000,
    # Default for unlisted tools
    "_default": 30000,
}


def tool_output_truncator(context: HookContext) -> HookContext:
    """
    Tool output을 제한하여 context window 절약.

    각 tool별 최대 출력 길이를 적용하고,
    초과 시 앞부분만 유지 + 요약 메시지 추가.
    """
    if not context.tool_output or not context.tool_name:
        return context

    output = context.tool_output
    tool_name = context.tool_name

    # Get limit for this tool
    max_chars = TOOL_OUTPUT_LIMITS.get(tool_name, TOOL_OUTPUT_LIMITS["_default"])

    if len(output) <= max_chars:
        return context

    # Truncate with informative message
    truncated = output[:max_chars]

    # Try to cut at a line boundary
    last_newline = truncated.rfind('\n', max_chars - 500, max_chars)
    if last_newline > max_chars * 0.8:
        truncated = truncated[:last_newline]

    total_lines = output.count('\n')
    shown_lines = truncated.count('\n')

    _default_truncated_msg = (
        f"[Truncated: showing {shown_lines}/{total_lines} lines, "
        f"{len(truncated)}/{len(output)} chars. "
        f"Use read_lines(path, offset, limit) for specific sections.]"
    )
    context.tool_output = (
        f"{truncated}\n\n"
        + _get_hook_message(
            "tool_truncated",
            _default_truncated_msg,
            shown_lines=shown_lines,
            total_lines=total_lines,
            shown_chars=len(truncated),
            total_chars=len(output),
        )
    )

    return context


# ============================================================
# Built-in Hook: PreemptiveCompactor
# ============================================================

def preemptive_compactor(context: HookContext) -> HookContext:
    """
    Context가 threshold를 초과하면 선제적으로 오래된 메시지를 압축.

    compress_history()를 직접 호출하지 않고,
    metadata에 compression_needed 플래그를 설정하여
    main.py가 처리하도록 위임.
    """
    if not context.messages:
        return context

    # Estimate current context size in TOKENS (chars // 4)
    # Must match compressor.py which uses: limit_tokens = MAX_CONTEXT_CHARS // 4
    total_chars = sum(
        len(str(m.get("content", ""))) for m in context.messages
    )
    total_tokens = total_chars // 4
    limit_tokens = context.max_context_chars // 4

    threshold_tokens = int(limit_tokens * context.compression_threshold)

    if total_tokens > threshold_tokens:
        context.metadata["compression_needed"] = True
        context.metadata["current_context_chars"] = total_chars
        context.metadata["threshold_chars"] = threshold_tokens * 4  # store as chars for display
        usage_pct = (total_tokens / limit_tokens) * 100
        context.metadata["context_usage_pct"] = usage_pct

    return context


# ============================================================
# Built-in Hook: DynamicContextPruner
# ============================================================

def dynamic_context_pruner(context: HookContext) -> HookContext:
    """
    불필요한 메시지를 제거하여 context 최적화:
    1. 중복 read_file 결과 제거 (같은 파일 → 최신만 유지)
    2. 에러 후 성공한 재시도 → 에러 메시지 제거
    3. Superseded write_file → 이전 버전 제거
    """
    if not context.messages or len(context.messages) < 10:
        return context

    messages = context.messages

    # Track which files have been read (keep latest)
    file_reads: Dict[str, int] = {}  # path -> latest message index
    # Track error+success pairs
    error_indices: Set[int] = set()

    # Scan for patterns (skip system message and recent messages)
    keep_recent = 6  # Always keep last 6 messages
    scan_end = max(1, len(messages) - keep_recent)

    for i in range(1, scan_end):
        msg = messages[i]
        content = str(msg.get("content", ""))

        # Pattern 1: Duplicate file reads
        if msg.get("role") == "user" and "Observation:" in content:
            # Check if this is a read_file result
            read_match = re.search(r'\[Action \d+\] read_file.*?---\n', content)
            if read_match:
                # Extract file path from the preceding assistant message
                if i > 0:
                    prev_content = str(messages[i-1].get("content", ""))
                    path_match = re.search(r'read_file\((?:path=)?["\']([^"\']+)["\']', prev_content)
                    if path_match:
                        path = path_match.group(1)
                        if path in file_reads:
                            # Mark older read for removal
                            old_idx = file_reads[path]
                            error_indices.add(old_idx)
                            # Also mark the assistant message before it
                            if old_idx > 0:
                                error_indices.add(old_idx - 1)
                        file_reads[path] = i

        # Pattern 2: Error followed by success (same tool)
        if msg.get("role") == "user" and content.strip().startswith("Observation:"):
            if "error:" in content.lower()[:200] or "Error:" in content[:200]:
                # Check if next observation (2 messages ahead) is success for same tool
                if i + 2 < scan_end:
                    next_obs = str(messages[i + 2].get("content", ""))
                    if (messages[i + 2].get("role") == "user"
                        and "Observation:" in next_obs
                        and "error:" not in next_obs.lower()[:200]):
                        error_indices.add(i)
                        error_indices.add(i - 1)  # The assistant action too

    # Remove marked messages
    if error_indices:
        context.messages = [
            msg for idx, msg in enumerate(messages)
            if idx not in error_indices
        ]
        pruned = len(error_indices)
        if pruned > 0:
            context.metadata["pruned_messages"] = pruned

    return context


# ============================================================
# Built-in Hook: EmergencyRecovery
# ============================================================

def emergency_recovery(context: HookContext) -> HookContext:
    """
    Context limit 초과 또는 심각한 에러 시 긴급 복구.

    메시지를 최소한으로 줄이고 요약을 생성하여 재구성.
    """
    if not context.error:
        return context

    error_str = str(context.error)

    # Context limit exceeded
    if "context" in error_str.lower() and ("limit" in error_str.lower() or "length" in error_str.lower()):
        if context.messages and len(context.messages) > 4:
            # Keep system prompt + last 2 exchanges
            system_msg = context.messages[0]
            recent = context.messages[-4:]

            # Create summary of removed messages
            removed_count = len(context.messages) - 5
            _topic = _extract_topic(context.messages)
            _default_recovery_msg = (
                f"[Emergency Recovery] {removed_count} messages were removed "
                f"due to context limit. The conversation was about: {_topic}"
            )
            summary = {
                "role": "system",
                "content": _get_hook_message(
                    "emergency_recovery",
                    _default_recovery_msg,
                    removed_count=removed_count,
                    topic=_topic,
                ),
            }

            context.messages = [system_msg, summary] + recent
            context.metadata["emergency_recovery"] = True
            context.metadata["removed_messages"] = removed_count

    return context


def _extract_topic(messages: List[Dict]) -> str:
    """메시지에서 주제 추출 (간단한 휴리스틱)"""
    for msg in messages:
        if msg.get("role") == "user":
            content = str(msg.get("content", ""))
            if content and not content.startswith("Observation:"):
                return content[:200]
    return "unknown topic"


# ============================================================
# Built-in Hook: TodoContinuationEnforcer
# ============================================================

def todo_continuation_enforcer(context: HookContext) -> HookContext:
    """
    LLM 응답 후 미완료 todo가 있으면 리마인더를 주입.

    metadata에 todo_tracker가 전달되어야 함.
    """
    todo_tracker = context.metadata.get("todo_tracker")
    if not todo_tracker:
        return context

    if not context.messages:
        return context

    # Check if there are incomplete todos
    if hasattr(todo_tracker, 'is_all_completed') and not todo_tracker.is_all_completed():
        current = todo_tracker.get_current_todo() if hasattr(todo_tracker, 'get_current_todo') else None
        if current:
            # Check if the last assistant message seems to be stopping
            last_msg = context.messages[-1] if context.messages else None
            if last_msg and last_msg.get("role") == "assistant":
                content = str(last_msg.get("content", ""))
                # Detect premature completion signals
                completion_signals = [
                    "task is complete", "all done", "finished",
                    "작업 완료", "모두 완료", "끝났습니다"
                ]
                is_stopping = any(sig in content.lower() for sig in completion_signals)

                if is_stopping:
                    # Inject reminder with explicit todo_update instruction
                    completed = sum(
                        1 for t in todo_tracker.todos
                        if t.status in ("completed", "approved")
                    )
                    remaining = len(todo_tracker.todos) - completed
                    cur_idx = todo_tracker.todos.index(current) + 1
                    _default_continuation = (
                        f"[System] {completed}/{len(todo_tracker.todos)} tasks done, {remaining} remaining.\n"
                        f"Current task {cur_idx}: {current.content}\n"
                        f"If the work is done, mark it complete:\n"
                        f"Action: todo_update\n"
                        f"Action Input: {{\"index\": {cur_idx}, \"status\": \"completed\"}}\n"
                        f"Then continue to the next task."
                    )
                    reminder = {
                        "role": "user",
                        "content": _get_hook_message(
                            "todo_continuation",
                            _default_continuation,
                            completed=completed,
                            total=len(todo_tracker.todos),
                            remaining=remaining,
                            cur_idx=cur_idx,
                            content=current.content,
                        ),
                    }
                    context.messages.append(reminder)
                    context.metadata["continuation_injected"] = True

    return context


# ============================================================
# Built-in Hook: SkillAutoActivator
# ============================================================

def skill_auto_activator(context: HookContext) -> HookContext:
    """
    현재 대화 context에서 관련 도메인 skill prompt를 자동 주입.

    main.py의 load_active_skills()를 활용하되,
    hook으로 래핑하여 BEFORE_LLM_CALL에서 자동 실행.

    metadata에 skill_prompts가 설정되면 main.py가 system prompt에 주입.
    """
    if not context.messages:
        return context

    # Extract recent user queries for skill matching
    recent_queries = []
    for msg in context.messages[-6:]:
        if msg.get("role") == "user":
            content = str(msg.get("content", ""))
            if not content.startswith("Observation:") and not content.startswith("[System]"):
                recent_queries.append(content[:200])

    if recent_queries:
        context.metadata["skill_queries"] = recent_queries

    return context


# ============================================================
# Default Hook Setup
# ============================================================

def create_default_hooks(
    enable_session_start: bool = True,
) -> HookRegistry:
    registry = HookRegistry()

    if enable_session_start:
        registry.register(HookPoint.ON_SESSION_START, lambda ctx: ctx, priority=10)

    # Phase 1: Tool output truncation (prevents context bloat from large outputs)
    registry.register(HookPoint.AFTER_TOOL_EXEC, tool_output_truncator, priority=10)

    # Phase 2: Context compression hooks
    registry.register(HookPoint.BEFORE_LLM_CALL, dynamic_context_pruner, priority=10)
    registry.register(HookPoint.BEFORE_LLM_CALL, preemptive_compactor, priority=20)
    registry.register(HookPoint.BEFORE_LLM_CALL, skill_auto_activator, priority=30)

    # Phase 2: Post-LLM hooks
    registry.register(HookPoint.AFTER_LLM_CALL, todo_continuation_enforcer, priority=10)

    # Error recovery
    registry.register(HookPoint.ON_ERROR, emergency_recovery, priority=10)

    return registry
