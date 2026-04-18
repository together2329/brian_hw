"""
Lightweight Sub-Agent ReAct Loop Runner

독립 messages[] 리스트로 미니 ReAct 루프를 실행하는 경량 agent runner.
main.py의 parse_all_actions(), execute_tool()을 재사용하며,
완료 시 LLM으로 결과를 압축하여 반환.

Primary Agent의 context와 완전히 분리된 독립 세션에서 실행.
"""

import os
import sys
import time
import json
import traceback
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

# Ensure import paths
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_script_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)
if os.path.join(_project_root, 'src') not in sys.path:
    sys.path.insert(0, os.path.join(_project_root, 'src'))

from text_utils import strip_thinking_tags as _strip_thinking_tags
from action_parser import (
    _strip_native_tool_tokens,
    parse_all_actions,
    sanitize_action_text,
    parse_tool_arguments,
)


def _dedup_intra_line(text):
    """Remove repeated content within each line of text.
    Scans for any 50-char segment that appears twice — truncates before the second occurrence."""
    cleaned = []
    for line in text.split('\n'):
        if len(line) > 100:
            check_len = 50
            limit = min(len(line) // 2, 600)
            for i in range(0, limit):
                segment = line[i:i + check_len]
                if len(segment) < check_len:
                    break
                second = line.find(segment, i + check_len)
                if second > i:
                    line = line[:second].rstrip()
                    break
        cleaned.append(line)
    return '\n'.join(cleaned)


@dataclass
class AgentResult:
    """Sub-agent 실행 결과"""
    output: str                        # 압축된 최종 결과 (≤2000 tokens)
    raw_output: str = ""               # 압축 전 전체 출력
    status: str = "completed"          # "completed" | "error" | "timeout"
    tool_calls: List[Dict] = field(default_factory=list)
    tool_observations: str = ""        # concatenated tool outputs (for converge metric parsing)
    files_examined: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    iterations: int = 0
    execution_time_ms: int = 0
    token_usage: Dict[str, int] = field(default_factory=dict)
    error: Optional[str] = None


def _build_converge_context(converge_state: Any, iteration: int = 0) -> str:
    """
    Build a converge context string from a Project instance.
    Returns empty string if converge_state is None or has no useful info.

    This is injected as a system message so the sub-agent knows about
    the current loop state: stage, score, criteria, iteration progress.
    """
    if converge_state is None:
        return ""

    parts = ["[CONVERGE CONTEXT]"]

    # Current stage and iteration
    stage = getattr(converge_state, 'current_stage', '')
    if stage:
        parts.append(f"Stage: {stage}")

    total_iter = getattr(converge_state, 'iteration', 0)
    if total_iter > 0:
        parts.append(f"Total iteration: {total_iter}")

    # Score info
    score = getattr(converge_state, 'score', -999.0)
    best = getattr(converge_state, 'best_score', -999.0)
    if score > -999.0:
        parts.append(f"Score: {score:.1f} (best: {best:.1f})")

    # Target score from config
    config = getattr(converge_state, 'converge_config', None)
    if config:
        threshold = getattr(config, 'criteria_score_threshold', 10.0)
        max_iters = getattr(config, 'criteria_max_total_iterations', 15)
        parts.append(f"Target score: {threshold} | Max iterations: {max_iters}")

    # Current metrics (compact)
    metrics = getattr(converge_state, 'metrics', {})
    if metrics:
        flat = []
        _flatten_metrics(metrics, flat)
        if flat:
            parts.append("Metrics: " + ", ".join(flat[:8]))

    # Criteria status
    check_fn = getattr(converge_state, 'check_hard_stop_criteria', None)
    if check_fn:
        try:
            criteria = check_fn()
            if criteria:
                met = sum(1 for v in criteria.values() if v)
                total = len(criteria)
                parts.append(f"Criteria: {met}/{total} met")
        except Exception:
            pass

    if len(parts) <= 1:
        return ""

    return " | ".join(parts)


def _flatten_metrics(metrics: Dict, out: list, prefix: str = "") -> None:
    """Flatten nested metrics dict into 'key=value' strings."""
    for k, v in metrics.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            _flatten_metrics(v, out, full_key)
        else:
            out.append(f"{full_key}={v}")


def run_agent_session(
    agent_name: str,
    prompt: str,
    model_override: Optional[str] = None,
    allowed_tools: Optional[Set[str]] = None,
    max_iterations: int = 15,
    system_prompt: Optional[str] = None,
    parent_context: str = "",
    compress_result: bool = True,
    max_result_chars: int = 8000,
    verbose: bool = False,
    workflow_name: str = "",
    converge_state: Any = None,        # Project instance for converge context injection
    tier: str = "sub",                 # "sub" (32K, limited tools) | "main" (200K, all tools)
) -> AgentResult:
    """
    독립 세션에서 미니 ReAct 루프를 실행.

    Args:
        agent_name: Agent 이름 (explore, execute, review)
        prompt: Agent에게 전달할 작업 설명
        model_override: 사용할 모델 (None이면 agent config에서 결정)
        allowed_tools: 허용할 tool 이름 집합 (None이면 agent config 사용)
        max_iterations: 최대 반복 횟수
        system_prompt: 커스텀 시스템 프롬프트 (None이면 workflow/prompts/ 에서 로드)
        parent_context: Primary agent가 전달하는 추가 context
        compress_result: 결과를 LLM으로 압축할지 여부
        max_result_chars: 최대 결과 문자 수
        verbose: 실시간 디버그 출력 (foreground 실행 시 유용)
        workflow_name: 워크스페이스 이름
        converge_state: Project instance for converge context injection (optional)
        tier: "sub" (32K context, limited tools) | "main" (200K context, all tools)

    Returns:
        AgentResult with compressed output
    """
    import config
    from core import tools as tools_module
    from lib.display import Color

    start_time = time.time()
    tool_calls = []
    files_examined = []
    files_modified = []

    # ── Redirect TODO_FILE to a job-scoped directory ────────────────────
    # Allocate a job dir upfront so the sub-agent's TodoTracker writes
    # to jobs/job<N>/todo.json instead of the project-level todo.json.
    _saved_todo_file = config.TODO_FILE
    _job_dir = None
    try:
        session_dir = getattr(config, 'SESSION_DIR', '')
        if session_dir:
            counter = _next_job_counter(session_dir)
            _job_dir = Path(session_dir) / "jobs" / f"job{counter}"
            _job_dir.mkdir(parents=True, exist_ok=True)
            config.TODO_FILE = str(_job_dir / "todo.json")
            # Also patch todo_tracker module-level path
            try:
                import lib.todo_tracker as _tt
                _tt.TODO_FILE = _job_dir / "todo.json"
            except Exception:
                pass
    except Exception:
        _job_dir = None

    # Load system prompt
    if system_prompt is None:
        system_prompt = _load_agent_prompt(agent_name)

    # Resolve allowed tools from agent config
    if allowed_tools is None:
        if tier == "main":
            allowed_tools = {"*"}  # main tier: all tools allowed
        else:
            allowed_tools = _get_agent_tools(agent_name)

    # Resolve model
    model = model_override or _get_agent_model(agent_name)

    from lib.display import (
        format_agent_banner, format_agent_done, format_tool_header,
        format_tool_result, format_context_bar, _extract_tool_args_summary, Color,
        live_print,
    )

    def _log(msg):
        if verbose:
            live_print(f"  {Color.DIM}[{agent_name}]{Color.RESET} {msg}")

    # Always show banner (brief when not verbose)
    if verbose:
        live_print(format_agent_banner(agent_name, model, f"tools={len(allowed_tools)}, max_iter={max_iterations}"))
    else:
        live_print(f"  {Color.DIM}┌─ {agent_name} · {model or 'default'}{Color.RESET}")

    # Build messages
    messages = [
        {"role": "system", "content": system_prompt},
    ]

    if parent_context:
        messages.append({
            "role": "user",
            "content": f"[Context from primary agent]\n{parent_context}"
        })

    messages.append({
        "role": "user",
        "content": prompt
    })

    # ── Converge context injection ────────────────────────────
    # If converge_state is provided, inject a system message with current
    # loop context so the sub-agent knows about score, stage, and criteria.
    if converge_state is not None:
        _converge_ctx = _build_converge_context(converge_state, iteration=0)
        if _converge_ctx:
            messages.append({
                "role": "system",
                "content": _converge_ctx,
            })

    # Parsing utilities already imported at module level from action_parser

    # Import LLM client
    from llm_client import chat_completion_stream, call_llm_raw

    # Context limit: main tier는 200K, sub tier는 32K (env override 가능)
    if tier == "main":
        sub_agent_max_tokens = int(os.getenv("MAINAGENT_MAX_CONTEXT_TOKENS", "200000"))
        max_result_chars = max(max_result_chars, 32000)
        max_iterations = max(max_iterations, 30)
    else:
        sub_agent_max_tokens = int(os.getenv("SUBAGENT_MAX_CONTEXT_TOKENS", "32000"))
    compression_threshold = 0.75  # 75%에서 압축

    # Mini ReAct loop
    all_observations = []
    iteration = 0

    try:
        while iteration < max_iterations:
            # Check ESC abort
            from lib.display import EscapeWatcher
            if EscapeWatcher.check():
                _log("ESC abort detected")
                break

            # ── Converge inbox check ────────────────────────────
            # Check if the orchestrator sent override/abort messages
            if converge_state is not None and hasattr(converge_state, 'has_inbox_messages'):
                if converge_state.has_inbox_messages():
                    inbox_msgs = converge_state.drain_inbox()
                    for imsg in inbox_msgs:
                        msg_type = imsg.get("type", "")
                        msg_text = imsg.get("message", "")
                        if msg_type == "abort":
                            _log(f"Converge abort: {msg_text}")
                            # Break out of ReAct loop
                            iteration = max_iterations + 1  # force exit
                            break
                        elif msg_type == "override":
                            _log(f"Converge override: {msg_text}")
                            messages.append({
                                "role": "system",
                                "content": f"[CONVERGE OVERRIDE] {msg_text}",
                            })
                        else:
                            messages.append({
                                "role": "system",
                                "content": f"[CONVERGE MESSAGE] {msg_text}",
                            })
                    # Re-check in case abort was issued
                    if iteration > max_iterations:
                        break

            iteration += 1
            _log(f"--- Iteration {iteration}/{max_iterations} ---")

            # Context status + auto-compression
            current_tokens = _context_status(messages, sub_agent_max_tokens, agent_name, verbose)
            if current_tokens > int(sub_agent_max_tokens * compression_threshold):
                _log(f"Context {current_tokens}/{sub_agent_max_tokens} ({int(current_tokens/sub_agent_max_tokens*100)}%) — compressing...")
                messages = _compress_agent_context(messages, agent_name, keep_recent=4, model=model)
                _context_status(messages, sub_agent_max_tokens, agent_name, verbose)

            # LLM call (non-blocking, ESC can abort mid-call)
            collected_content = ""
            _log(f"LLM call (model={model})...")
            try:
                import concurrent.futures
                _llm_future = concurrent.futures.ThreadPoolExecutor(max_workers=1).submit(
                    call_llm_raw,
                    prompt="",
                    messages=messages,
                    stop=["Observation:"],
                    model=model,
                )
                while not _llm_future.done():
                    if EscapeWatcher.check():
                        break
                    time.sleep(0.1)
                if EscapeWatcher.check():
                    _llm_future.cancel()
                    break
                collected_content = (_llm_future.result() or "")
            except Exception as e:
                return AgentResult(
                    output=f"LLM call failed: {e}",
                    status="error",
                    error=str(e),
                    iterations=iteration,
                    execution_time_ms=int((time.time() - start_time) * 1000),
                )

            # Clean up native tool tokens + convert to ReAct format
            collected_content = _strip_native_tool_tokens(collected_content)

            # Remove intra-line repetition from LLM response
            collected_content = _dedup_intra_line(collected_content)

            # Add assistant message
            messages.append({"role": "assistant", "content": collected_content})

            # Show LLM response in verbose
            if verbose:
                lines = collected_content.strip().split('\n')
                for line in lines[:15]:
                    # Color Thought/Action keywords
                    if line.strip().startswith('Thought:'):
                        live_print(f"  {Color.DIM}{Color.CYAN}┃{Color.RESET}  {line}")
                    elif line.strip().startswith('Action:'):
                        live_print(f"  {Color.YELLOW}▸{Color.RESET}  {line}")
                    else:
                        live_print(f"  {Color.DIM}┃{Color.RESET}  {line}")
                if len(lines) > 15:
                    live_print(f"  {Color.DIM}┃  ... ({len(lines) - 15} more lines){Color.RESET}")

            # Check for completion
            from lib.iteration_control import detect_completion_signal

            # Parse actions first (REASONING blocks are stripped inside parse_all_actions)
            actions = parse_all_actions(collected_content)

            # Only check completion if there are no pending actions
            if not actions:
                if detect_completion_signal(collected_content):
                    _log("Completion signal detected.")
                    break

            if not actions:
                # Check if the response looks like it *should* have been a tool call
                # (contains code blocks or file-like content but no Action: was issued)
                _has_code_block = '```' in collected_content or 'endmodule' in collected_content
                _has_file_intent = any(kw in collected_content.lower() for kw in
                    ['write', 'create', 'implement', 'save', 'generate file', 'output:'])

                if _has_code_block and _has_file_intent and iteration < max_iterations - 1:
                    # Inject corrective message and retry
                    _correction = (
                        "[SYSTEM ERROR] You described code but did NOT call any tools. "
                        "You MUST use `Action: write_file(path=\"...\", content=\"...\")` to save code to files. "
                        "Do NOT just describe what you would do. Actually call the tool now.\n"
                        "Example: Action: write_file(path=\"counter/rtl/counter.sv\", content=\"\"\"module counter; ... endmodule\"\"\")"
                    )
                    messages.append({
                        "role": "user",
                        "content": _correction
                    })
                    _log("No actions found but code detected. Injecting correction and retrying.")
                    continue  # Retry this iteration
                else:
                    _log("No actions found. Natural completion.")
                    break

            _log(f"Parsed {len(actions)} action(s)")

            # Execute actions (sequential for sub-agents)
            combined_results = []
            for idx, (tool_name, args_str, *hint) in enumerate(actions):
                # Check ESC abort between tools
                if EscapeWatcher.check():
                    break

                # Filter by allowed tools
                if allowed_tools and "*" not in allowed_tools:
                    if tool_name not in allowed_tools:
                        observation = f"Error: Tool '{tool_name}' is not allowed for {agent_name} agent."
                        combined_results.append(observation)
                        continue

                # Execute tool
                summary = _extract_tool_args_summary(tool_name, args_str)
                try:
                    func = tools_module.AVAILABLE_TOOLS.get(tool_name)
                    if not func:
                        observation = f"Error: Tool '{tool_name}' not found."
                    else:
                        # Use dispatch_tool for all safety nets (positional truncation,
                        # unknown kwarg stripping, grep auto-fix, timeout, alias resolution)
                        from tool_dispatcher import dispatch_tool as _dispatch
                        observation = _dispatch(
                            tool_name, args_str,
                            available_tools=tools_module.AVAILABLE_TOOLS,
                            global_timeout=300,
                        )
                except Exception as e:
                    observation = f"Error executing {tool_name}: {e}"

                # Track tool usage
                tool_calls.append({"tool": tool_name, "args": args_str[:100]})

                # Track file operations
                if tool_name in ("read_file", "read_lines", "grep_file"):
                    # Extract path from args
                    path = _extract_path_from_args(args_str)
                    if path:
                        files_examined.append(path)
                elif tool_name in ("write_file", "replace_in_file", "replace_lines"):
                    path = _extract_path_from_args(args_str)
                    if path:
                        files_modified.append(path)

                # Truncate long outputs for sub-agent context
                if len(observation) > 20000:
                    observation = observation[:20000] + f"\n[Truncated: {len(observation)} chars total]"

                if verbose:
                    live_print(format_tool_header(tool_name, summary))
                    live_print(format_tool_result(observation, max_lines=3, max_chars=200))
                else:
                    from lib.display import format_tool_brief
                    brief = format_tool_brief(tool_name, args_str, observation)
                    header = format_tool_header(tool_name, summary)
                    live_print(f"{header}  {Color.DIM}({brief}){Color.RESET}")
                combined_results.append(f"[{tool_name}] {observation}")

            # Add observation
            observation_text = "\n\n".join(combined_results)
            all_observations.append(observation_text)
            messages.append({
                "role": "user",
                "content": f"Observation: {observation_text}"
            })

    except Exception as e:
        return AgentResult(
            output=f"Agent session error: {e}\n{traceback.format_exc()}",
            status="error",
            error=str(e),
            tool_calls=tool_calls,
            files_examined=files_examined,
            files_modified=files_modified,
            iterations=iteration,
            execution_time_ms=int((time.time() - start_time) * 1000),
        )

    # Extract final output (last assistant message)
    raw_output = ""
    for msg in reversed(messages):
        if msg.get("role") == "assistant":
            raw_output = msg.get("content", "")
            break

    # Compress result if needed
    if compress_result and len(raw_output) > max_result_chars:
        output = _compress_output(
            raw_output, all_observations, agent_name, prompt, model
        )
    else:
        output = raw_output

    # Remove intra-line repetition in output (LLM repetition trap)
    output = _dedup_intra_line(output)

    # Final truncation safety net
    if len(output) > max_result_chars:
        output = output[:max_result_chars] + "\n[Result truncated]"

    elapsed_ms = int((time.time() - start_time) * 1000)
    if verbose:
        live_print(format_agent_done(
            agent_name, model,
            elapsed_sec=elapsed_ms / 1000,
            iterations=iteration,
            tool_count=len(tool_calls),
        ))
    else:
        live_print(f"  {Color.DIM}└─ {agent_name} · {elapsed_ms/1000:.1f}s · {len(tool_calls)} tools · {iteration} iters{Color.RESET}")

    result = AgentResult(
        output=output,
        raw_output=raw_output,
        status="completed",
        tool_calls=tool_calls,
        tool_observations="\n".join(all_observations),
        files_examined=list(set(files_examined)),
        files_modified=list(set(files_modified)),
        iterations=iteration,
        execution_time_ms=elapsed_ms,
    )

    # Persist sub-agent result to .session/<project>/jobs/job<N>/
    try:
        import config as _cfg
        session_dir = getattr(_cfg, 'SESSION_DIR', '')
        if session_dir:
            _persist_job_result(
                session_dir=session_dir,
                agent_name=agent_name,
                messages=messages,
                result=result,
                job_dir=_job_dir,
            )
    except Exception:
        pass

    # Restore project-level TODO_FILE
    config.TODO_FILE = _saved_todo_file
    try:
        import lib.todo_tracker as _tt
        _tt.TODO_FILE = Path(_saved_todo_file) if _saved_todo_file else _saved_todo_file
    except Exception:
        pass

    return result


# ============================================================
# Job Persistence (v2 — flat project layout)
# ============================================================

def _next_job_counter(session_dir: str) -> int:
    """Atomically increment and return the job counter.

    Counter file: .session/<project>/jobs/.counter
    """
    counter_path = Path(session_dir) / "jobs" / ".counter"
    counter_path.parent.mkdir(parents=True, exist_ok=True)

    # If counter_path is somehow a directory, remove it
    if counter_path.is_dir():
        import shutil
        shutil.rmtree(counter_path, ignore_errors=True)

    count = 1
    if counter_path.exists():
        try:
            count = int(counter_path.read_text().strip()) + 1
        except (ValueError, OSError):
            count = 1
    try:
        counter_path.write_text(str(count))
    except OSError:
        pass  # Cannot write counter — continue with in-memory count
    return count


def _persist_job_result(
    session_dir: str,
    agent_name: str,
    messages: List[Dict],
    result: "AgentResult",
    job_dir: Optional[Path] = None,
) -> None:
    """Save job conversation, full history, todos, and result to .session/<project>/jobs/job<N>/.

    Layout (4 files):
      .session/<project>/jobs/job1/conversation.json       ← active conversation
      .session/<project>/jobs/job1/full_conversation.json   ← append-only full history
      .session/<project>/jobs/job1/todo.json                ← job's todo state
      .session/<project>/jobs/job1/result.json              ← result summary
    """
    if not session_dir:
        return

    try:
        # Reuse pre-allocated job_dir (from TODO_FILE redirect) or allocate new one
        if job_dir is not None:
            job_dir = Path(job_dir)
        else:
            counter = _next_job_counter(session_dir)
            job_dir = Path(session_dir) / "jobs" / f"job{counter}"
        job_dir.mkdir(parents=True, exist_ok=True)

        # Save conversation (active messages)
        conv_path = job_dir / "conversation.json"
        safe_messages = []
        for m in messages:
            safe_messages.append({
                "role": m.get("role", ""),
                "content": str(m.get("content", ""))[:50000],
            })
        conv_path.write_text(
            json.dumps(safe_messages, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # Save full conversation (append-only — same as active for first run)
        full_conv_path = job_dir / "full_conversation.json"
        if not full_conv_path.exists():
            full_conv_path.write_text(
                json.dumps(safe_messages, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        else:
            # Append new messages beyond what's already stored
            try:
                existing = json.loads(full_conv_path.read_text(encoding="utf-8"))
                new_count = len(safe_messages) - len(existing)
                if new_count > 0:
                    existing.extend(safe_messages[len(existing):])
                    full_conv_path.write_text(
                        json.dumps(existing, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
            except Exception:
                pass

        # Save todo state (job-scoped — already written by TodoTracker to config.TODO_FILE)
        # The TODO_FILE was redirected to this job_dir before execution, so the file
        # should already exist. No copy needed — just verify it's there.
        todo_path = job_dir / "todo.json"
        if not todo_path.exists():
            # Fallback: create empty todo file
            todo_path.write_text("[]", encoding="utf-8")

        # Save result summary
        result_path = job_dir / "result.json"
        result_data = {
            "agent_name": agent_name,
            "status": result.status,
            "iterations": result.iterations,
            "execution_time_ms": result.execution_time_ms,
            "tool_calls": len(result.tool_calls),
            "files_examined": result.files_examined[:20],
            "files_modified": result.files_modified[:20],
            "output_preview": result.output[:2000] if result.output else "",
        }
        # Save tool_observations for converge metric parsing
        if result.tool_observations:
            result_data["tool_observations_preview"] = result.tool_observations[:5000]
        result_path.write_text(
            json.dumps(result_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass  # Persistence failure should never crash the agent


# ============================================================
# Helper Functions
# ============================================================

def _load_agent_prompt(agent_name: str) -> str:
    """workflow/prompts/{agent_name}.md 에서 시스템 프롬프트 로드"""
    prompts_dir = os.path.join(_project_root, "workflow", "prompts")
    prompt_path = os.path.join(prompts_dir, f"{agent_name}.md")

    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    # Fallback: minimal prompt
    return _get_default_prompt(agent_name)


def _get_default_prompt(agent_name: str) -> str:
    """Agent별 기본 시스템 프롬프트"""
    defaults = {
        "explore": (
            "You are an exploration agent. Your job is to quickly find relevant files, "
            "code patterns, and architecture details. You have READ-ONLY access.\n\n"
            "Output format:\n"
            "<files>\nList of relevant files found\n</files>\n"
            "<answer>\nConcise findings with key details\n</answer>\n\n"
            "Use the ReAct format:\n"
            "Thought: what to look for\n"
            "Action: tool_name(args)\n"
            "When done, provide your final answer."
        ),
        "workflow": (
            "You are a unified workflow agent with full access. "
            "You handle exploration, execution, and review in a single session.\n\n"
            "Phases: Understand (read-only) → Plan → Execute → Verify.\n"
            "Use the ReAct format:\n"
            "Thought: what to do\n"
            "Action: tool_name(args)"
        ),
    }
    return defaults.get(agent_name, f"You are a {agent_name} agent. Use the ReAct format.")


def _get_agent_tools(agent_name: str) -> Set[str]:
    """Agent config에서 허용 tool 목록 반환"""
    try:
        from core.agent_config import get_agent_config
        config = get_agent_config(agent_name)
        if config:
            return config.get_allowed_tools()
    except ImportError:
        pass

    # Fallback defaults
    READ_ONLY = {
        "read_file", "read_lines", "grep_file", "list_dir",
        "find_files",
        "git_diff", "git_status",
    }
    ALL_TOOLS = {"*"}

    TASK_TOOLS = READ_ONLY | {
        "background_task", "background_output",
        "todo_write", "todo_read",
    }

    defaults = {
        "explore": READ_ONLY,
        "execute": ALL_TOOLS,  # execute agent needs full tool access
        "workflow": ALL_TOOLS,
        "task": TASK_TOOLS,
    }
    return defaults.get(agent_name, READ_ONLY)


def _get_agent_model(agent_name: str) -> Optional[str]:
    """Agent config에서 모델 설정 반환"""
    try:
        from core.agent_config import get_agent_config
        agent_cfg = get_agent_config(agent_name)
        if agent_cfg and agent_cfg.model:
            model_str = agent_cfg.model.model_id
            if agent_cfg.model.provider_id:
                model_str = f"{agent_cfg.model.provider_id}/{model_str}"
            return model_str
    except ImportError:
        pass
    return None  # Use default model


def _extract_path_from_args(args_str: str) -> Optional[str]:
    """Tool arguments에서 파일 경로 추출"""
    import re
    # Match path="..." or first positional "..."
    match = re.search(r'(?:path\s*=\s*)?["\']([^"\']+)["\']', args_str)
    return match.group(1) if match else None


# ============================================================
# Sub-Agent Context Management
# ============================================================

def _estimate_tokens(messages: List[Dict]) -> int:
    """messages의 대략적 토큰 수 추정 (1 token ≈ 4 chars)"""
    total_chars = sum(len(str(m.get("content", ""))) for m in messages)
    return total_chars // 4


def _context_status(messages: List[Dict], max_tokens: int, agent_name: str, verbose: bool = False) -> int:
    """Context 사용량 표시. 현재 토큰 수 반환."""
    current = _estimate_tokens(messages)

    if verbose:
        from lib.display import format_context_bar
        bar = format_context_bar(current, max_tokens, label=agent_name)
        print(f"  {bar}")

    return current


def _compress_agent_context(
    messages: List[Dict],
    agent_name: str,
    keep_recent: int = 4,
    model: Optional[str] = None,
) -> List[Dict]:
    """
    Sub-agent용 경량 context compression.
    system + 요약 + 최근 N개 메시지만 유지.
    """
    try:
        from llm_client import call_llm_raw
    except ImportError:
        # compression 불가 — 그냥 반환
        return messages

    # system 메시지 분리
    system_msgs = [m for m in messages if m.get("role") == "system"]
    regular_msgs = [m for m in messages if m.get("role") != "system"]

    if len(regular_msgs) <= keep_recent:
        return messages  # 너무 짧아서 압축 불필요

    old_msgs = regular_msgs[:-keep_recent]
    recent_msgs = regular_msgs[-keep_recent:]

    # 오래된 메시지를 요약
    old_text = "\n".join(
        f"[{m.get('role')}] {str(m.get('content', ''))[:500]}"
        for m in old_msgs
    )
    if len(old_text) > 10000:
        old_text = old_text[:10000] + "\n[...truncated...]"

    summary_prompt = (
        f"Summarize this {agent_name} agent conversation history into key facts only. "
        f"Preserve: file paths, function names, findings, errors. Max 500 words.\n\n"
        f"{old_text}"
    )

    try:
        summary = call_llm_raw(
            prompt="",
            messages=[{"role": "user", "content": summary_prompt}],
            model=model,
        )
        if not summary or not isinstance(summary, str):
            summary = old_text[:3000]
    except Exception:
        summary = old_text[:3000]

    summary_msg = {
        "role": "user",
        "content": f"[Compressed context from earlier iterations]\n{summary}"
    }

    print(f"  [{agent_name}] Context compressed: {len(old_msgs)} messages → 1 summary")
    return system_msgs + [summary_msg] + recent_msgs


def _compress_output(
    raw_output: str,
    observations: List[str],
    agent_name: str,
    original_prompt: str,
    model: Optional[str] = None,
) -> str:
    """LLM을 사용하여 agent 출력을 압축"""
    try:
        from llm_client import call_llm_raw

        # Build compression prompt
        content = raw_output
        if len(content) > 15000:
            content = content[:15000] + "\n[... truncated ...]"

        compress_prompt = (
            f"Summarize the following {agent_name} agent's output into a concise result "
            f"(max 2000 tokens). Preserve:\n"
            f"- Key findings and file paths\n"
            f"- Specific code references (line numbers, function names)\n"
            f"- Action items or decisions made\n"
            f"- Any errors or warnings\n\n"
            f"Original task: {original_prompt[:200]}\n\n"
            f"Agent output:\n{content}"
        )

        result = call_llm_raw(
            prompt="",
            messages=[{"role": "user", "content": compress_prompt}],
            model=model,
        )

        if result and isinstance(result, str):
            return result

    except Exception as e:
        # Compression failed, use truncation fallback
        pass

    # Fallback: simple truncation
    if len(raw_output) > 8000:
        return raw_output[:8000] + "\n[Output truncated to 8000 chars]"
    return raw_output
