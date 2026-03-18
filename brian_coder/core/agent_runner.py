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
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

# Ensure import paths
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_script_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
if os.path.join(_project_root, 'src') not in sys.path:
    sys.path.insert(0, os.path.join(_project_root, 'src'))


def _strip_native_tool_tokens(text):
    """
    Strip native tool call tokens and convert to ReAct Action: format.
    Standalone version for agent_runner (no main.py dependency).
    Handles GLM 4.7, Qwen, DeepSeek, Mistral native formats.
    """
    import re
    import json

    # Strip reasoning tokens leaked into content
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = re.sub(r'</?think>', '', text)

    def _json_to_action(json_str):
        try:
            data = json.loads(json_str.strip())
            name = data.get("name", "")
            args = data.get("arguments", {})
            if name and isinstance(args, dict):
                args_str = ", ".join(f'{k}={json.dumps(v)}' for k, v in args.items())
                return f"\nAction: {name}({args_str})\n"
        except (json.JSONDecodeError, AttributeError):
            pass
        return ""

    def _xml_params_to_action(tool_name, params_block):
        params = re.findall(r'<(\w+)>(.*?)</\1>', params_block, re.DOTALL)
        if tool_name and params:
            args_str = ", ".join(f'{k}={json.dumps(v)}' for k, v in params)
            return f"\nAction: {tool_name}({args_str})\n"
        elif tool_name:
            return f"\nAction: {tool_name}()\n"
        return ""

    # JSON-based: <tool_call>{...}</tool_call> or bare JSON
    text = re.sub(
        r'<tool_call>\s*(\{.*?\})\s*</tool_call>',
        lambda m: _json_to_action(m.group(1)), text, flags=re.DOTALL
    )
    text = re.sub(
        r'\{\s*"name"\s*:\s*"(\w+)"\s*,\s*"arguments"\s*:\s*\{[^}]*\}\s*\}',
        lambda m: _json_to_action(m.group(0)), text
    )

    # GLM-style universal: <tool/action/execute>NAME</tag> <param*>...<key>val</key>...</tag>
    tool_tag_re = re.compile(
        r'<(tool|action|execute|func\w*)\s*>'
        r'\s*(?:<(execute|tool)\s*>\s*)?'
        r'(\w+)'
        r'\s*(?:</\w+>\s*)?'
        r'</\w+>'
    )
    matches = list(tool_tag_re.finditer(text))
    for m in reversed(matches):
        tool_name = m.group(3)
        after_tool = text[m.end():]
        param_re = re.match(
            r'\s*<(p(?:ar|ra)\w*)\s*>(.*)</(p(?:ar|ra)\w*)\s*>',
            after_tool, re.DOTALL
        )
        if param_re:
            total_end = m.end() + param_re.end()
            action_str = _xml_params_to_action(tool_name, param_re.group(2))
            text = text[:m.start()] + action_str + text[total_end:]
        else:
            text = text[:m.start()] + f"\nAction: {tool_name}()\n" + text[m.end():]

    # Strip remaining tokens
    for token in [
        'tool_call_begin', 'tool_call_end',
        'tool_calls_section_begin', 'tool_calls_section_end',
        '<|tool_call|>', '<|tool_calls|>',
        '<|start_header_id|>tool_call<|end_header_id|>',
    ]:
        text = text.replace(token, '')

    text = re.sub(r'<\|(?:tool_call|tool_calls|functions)[^|]*\|>', '', text)
    text = re.sub(r'</?(?:tool_call|tool|action|execute|func\w*|p(?:ar|aram)\w*)>', '', text)

    # Bare function calls: "list_dir(path=".")" → "Action: list_dir(path=".")"
    _KNOWN_TOOLS = {
        'read_file', 'write_file', 'run_command', 'list_dir', 'grep_file',
        'read_lines', 'find_files', 'replace_in_file', 'replace_lines',
        'git_diff', 'git_status', 'todo_write', 'todo_update',
        'rag_search', 'rag_index', 'rag_explore', 'rag_status',
        'background_task', 'background_output',
        'analyze_verilog_module', 'find_signal_usage', 'find_module_definition',
        'extract_module_hierarchy', 'generate_module_testbench',
    }
    _tools_pattern = '|'.join(re.escape(t) for t in _KNOWN_TOOLS)
    text = re.sub(
        r'^(\s*)(' + _tools_pattern + r')\s*\(',
        r'\1Action: \2(',
        text,
        flags=re.MULTILINE
    )

    return text.strip()


@dataclass
class AgentResult:
    """Sub-agent 실행 결과"""
    output: str                        # 압축된 최종 결과 (≤2000 tokens)
    raw_output: str = ""               # 압축 전 전체 출력
    status: str = "completed"          # "completed" | "error" | "timeout"
    tool_calls: List[Dict] = field(default_factory=list)
    files_examined: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    iterations: int = 0
    execution_time_ms: int = 0
    token_usage: Dict[str, int] = field(default_factory=dict)
    error: Optional[str] = None


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
) -> AgentResult:
    """
    독립 세션에서 미니 ReAct 루프를 실행.

    Args:
        agent_name: Agent 이름 (explore, plan, execute, review)
        prompt: Agent에게 전달할 작업 설명
        model_override: 사용할 모델 (None이면 agent config에서 결정)
        allowed_tools: 허용할 tool 이름 집합 (None이면 agent config 사용)
        max_iterations: 최대 반복 횟수
        system_prompt: 커스텀 시스템 프롬프트 (None이면 agents/prompts/ 에서 로드)
        parent_context: Primary agent가 전달하는 추가 context
        compress_result: 결과를 LLM으로 압축할지 여부
        max_result_chars: 최대 결과 문자 수
        verbose: 실시간 디버그 출력 (foreground 실행 시 유용)

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

    # Load system prompt
    if system_prompt is None:
        system_prompt = _load_agent_prompt(agent_name)

    # Resolve allowed tools from agent config
    if allowed_tools is None:
        allowed_tools = _get_agent_tools(agent_name)

    # Resolve model
    model = model_override or _get_agent_model(agent_name)

    from lib.display import (
        format_agent_banner, format_agent_done, format_tool_header,
        format_tool_result, format_context_bar, _extract_tool_args_summary, Color
    )

    def _log(msg):
        if verbose:
            print(f"  {Color.DIM}[{agent_name}]{Color.RESET} {msg}")

    # Always show banner (brief when not verbose)
    if verbose:
        print(format_agent_banner(agent_name, model, f"tools={len(allowed_tools)}, max_iter={max_iterations}"))
    else:
        print(f"  {Color.DIM}┌─ {agent_name} · {model or 'default'}{Color.RESET}")

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

    # Import parsing utilities from main.py
    try:
        from main import parse_all_actions, sanitize_action_text, parse_tool_arguments
    except ImportError:
        # Fallback for different import contexts
        sys.path.insert(0, os.path.join(_project_root, 'src'))
        from main import parse_all_actions, sanitize_action_text, parse_tool_arguments

    # Import LLM client
    from llm_client import chat_completion_stream, call_llm_raw

    # Sub-agent context limit (기본 32K tokens, primary보다 훨씬 작음)
    sub_agent_max_tokens = int(os.getenv("SUBAGENT_MAX_CONTEXT_TOKENS", "32000"))
    compression_threshold = 0.75  # 75%에서 압축

    # Mini ReAct loop
    all_observations = []
    iteration = 0

    try:
        while iteration < max_iterations:
            iteration += 1
            _log(f"--- Iteration {iteration}/{max_iterations} ---")

            # Context status + auto-compression
            current_tokens = _context_status(messages, sub_agent_max_tokens, agent_name, verbose)
            if current_tokens > int(sub_agent_max_tokens * compression_threshold):
                _log(f"Context {current_tokens}/{sub_agent_max_tokens} ({int(current_tokens/sub_agent_max_tokens*100)}%) — compressing...")
                messages = _compress_agent_context(messages, agent_name, keep_recent=4, model=model)
                _context_status(messages, sub_agent_max_tokens, agent_name, verbose)

            # LLM call (non-streaming for reliable native tool token parsing)
            collected_content = ""
            _log(f"LLM call (model={model})...")
            try:
                collected_content = call_llm_raw(
                    prompt="",
                    messages=messages,
                    stop=["Observation:"],
                    model=model,
                ) or ""
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

            # Add assistant message
            messages.append({"role": "assistant", "content": collected_content})

            # Show LLM response in verbose
            if verbose:
                lines = collected_content.strip().split('\n')
                for line in lines[:15]:
                    # Color Thought/Action keywords
                    if line.strip().startswith('Thought:'):
                        print(f"  {Color.DIM}{Color.CYAN}┃{Color.RESET}  {line}")
                    elif line.strip().startswith('Action:'):
                        print(f"  {Color.YELLOW}▸{Color.RESET}  {line}")
                    else:
                        print(f"  {Color.DIM}┃{Color.RESET}  {line}")
                if len(lines) > 15:
                    print(f"  {Color.DIM}┃  ... ({len(lines) - 15} more lines){Color.RESET}")

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
                _log("No actions found. Natural completion.")
                break

            _log(f"Parsed {len(actions)} action(s)")

            # Execute actions (sequential for sub-agents)
            combined_results = []
            for idx, (tool_name, args_str, *hint) in enumerate(actions):
                # Filter by allowed tools
                if allowed_tools and "*" not in allowed_tools:
                    if tool_name not in allowed_tools:
                        observation = f"Error: Tool '{tool_name}' is not allowed for {agent_name} agent."
                        combined_results.append(observation)
                        continue

                # Execute tool — always show tool header
                summary = _extract_tool_args_summary(tool_name, args_str)
                print(format_tool_header(tool_name, summary, idx + 1, len(actions)))
                try:
                    func = tools_module.AVAILABLE_TOOLS.get(tool_name)
                    if not func:
                        observation = f"Error: Tool '{tool_name}' not found."
                    else:
                        parsed_args, parsed_kwargs = parse_tool_arguments(args_str)
                        observation = func(*parsed_args, **parsed_kwargs)
                        if not isinstance(observation, str):
                            import json
                            try:
                                observation = json.dumps(observation, indent=2, ensure_ascii=False)
                            except Exception:
                                observation = str(observation)
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
                    print(format_tool_result(observation, max_lines=3, max_chars=200))
                else:
                    # Brief: just line count
                    line_count = observation.count('\n') + 1
                    print(f"  {Color.DIM}│ ({line_count} lines){Color.RESET}")
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

    # Final truncation safety net
    if len(output) > max_result_chars:
        output = output[:max_result_chars] + "\n[Result truncated]"

    elapsed_ms = int((time.time() - start_time) * 1000)
    if verbose:
        print(format_agent_done(
            agent_name, model,
            elapsed_sec=elapsed_ms / 1000,
            iterations=iteration,
            tool_count=len(tool_calls),
        ))
    else:
        print(f"  {Color.DIM}└─ {agent_name} · {elapsed_ms/1000:.1f}s · {len(tool_calls)} tools · {iteration} iters{Color.RESET}")

    return AgentResult(
        output=output,
        raw_output=raw_output,
        status="completed",
        tool_calls=tool_calls,
        files_examined=list(set(files_examined)),
        files_modified=list(set(files_modified)),
        iterations=iteration,
        execution_time_ms=elapsed_ms,
    )


# ============================================================
# Helper Functions
# ============================================================

def _load_agent_prompt(agent_name: str) -> str:
    """agents/prompts/{agent_name}.md 에서 시스템 프롬프트 로드"""
    prompts_dir = os.path.join(_project_root, "agents", "prompts")
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
        "plan": (
            "You are a planning agent. Analyze the task and create a detailed step-by-step plan. "
            "You have READ-ONLY access to understand the codebase.\n\n"
            "Output format:\n"
            "<plan>\n1. Step description\n   - Files needed: ...\n   - Tools needed: ...\n</plan>\n\n"
            "Use the ReAct format to gather information, then output your plan."
        ),
        "execute": (
            "You are an execution agent. Implement code changes according to the given plan. "
            "You have FULL access to read, write, and run commands.\n\n"
            "Follow existing code patterns and conventions. "
            "Use the ReAct format:\n"
            "Thought: what to implement\n"
            "Action: tool_name(args)"
        ),
        "review": (
            "You are a code review agent. Review the code changes for bugs, style issues, "
            "and potential improvements. You have READ-ONLY access.\n\n"
            "Output format:\n"
            "<issues>\n- Issue description (severity: high/medium/low)\n</issues>\n"
            "<suggestions>\n- Improvement suggestion\n</suggestions>"
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
        "find_files", "rag_search", "rag_explore",
        "git_diff", "git_status",
    }
    ALL_TOOLS = {"*"}

    TASK_TOOLS = READ_ONLY | {
        "background_task", "background_output",
        "todo_write", "todo_read",
    }

    defaults = {
        "explore": READ_ONLY,
        "plan": READ_ONLY | {"create_plan", "get_plan"},
        "execute": ALL_TOOLS,
        "review": READ_ONLY,
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
