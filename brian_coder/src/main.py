import sys
import os
import json
import urllib.request
import urllib.error
import re
import copy
import time
import traceback
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, wait
from datetime import datetime
from typing import List, Tuple, Optional, Dict

# Add paths for imports
# Get the directory containing this script (src directory)
_script_dir = os.path.dirname(os.path.abspath(__file__))
# Get the project root (parent of src directory)
_project_root = os.path.dirname(_script_dir)


# Add paths: project root first, then src
# This allows imports like: from lib.display import Color, from core.tools import ...
sys.path.insert(0, _script_dir)  # src directory (highest priority for src modules)
sys.path.insert(0, _project_root)  # brian_coder directory (for lib, core, agents)

import config
from core import tools
from core.action_dependency import ActionDependencyAnalyzer, FileConflictDetector, ActionBatch
from core.slash_commands import get_registry as get_slash_command_registry
from core.context_tracker import get_tracker as get_context_tracker
import llm_client
from lib.display import Color
from llm_client import chat_completion_stream, call_llm_raw, estimate_message_tokens, get_actual_tokens
from lib.memory import MemorySystem
from lib.todo_tracker import TodoTracker, parse_todo_write_from_text
from core.graph_lite import GraphLite, Node, Edge
from lib.procedural_memory import ProceduralMemory, Action, Trajectory
from lib.message_classifier import MessageClassifier
from lib.curator import KnowledgeCurator

# Deep Think (optional - only import if enabled)
if config.ENABLE_DEEP_THINK and not config.ENABLE_SUB_AGENTS:
    from lib.deep_think import DeepThinkEngine, DeepThinkResult, format_deep_think_output

# Sub-Agent System (optional - replaces Deep Think when enabled)
if config.ENABLE_SUB_AGENTS:
    try:
        # Tests may add `agents/` to sys.path (so `sub_agents` is importable).
        from sub_agents import Orchestrator
    except ImportError:
        # Runtime default: import via namespace package under `agents/`.
        from agents.sub_agents import Orchestrator

from lib.iteration_control import IterationTracker, detect_completion_signal, show_iteration_warning

# --- Dynamic Plugin Loading ---
if config.ENABLE_VERILOG_TOOLS:
    try:
        from core import tools_verilog
        tools.AVAILABLE_TOOLS.update(tools_verilog.VERILOG_TOOLS)
        print(Color.system("[System] Verilog tools plugin loaded successfully 🔌"))
    except ImportError as e:
        print(Color.warning(f"[System] Failed to load Verilog tools: {e}"))

# --- 1. No Vendor Path Needed ---
# We are using standard libraries only.

# --- 2. API Client (urllib) ---
# Moved to llm_client.py

# --- Global Memory System ---
# Initialize memory system if enabled
memory_system = None
if config.ENABLE_MEMORY:
    try:
        memory_system = MemorySystem(memory_dir=config.MEMORY_DIR)
        # Success message will be shown during chat_loop startup
    except Exception as e:
        # Use basic print since Color class not yet defined
        print(f"\033[91m[System] ❌ Memory system initialization failed: {e}\033[0m")
        print(f"\033[93m[System] ⚠️  Continuing without memory system...\033[0m")
        memory_system = None

# --- Global Graph Lite System ---
# Initialize graph system if enabled
graph_lite = None
if config.ENABLE_GRAPH:
    try:
        graph_lite = GraphLite(memory_dir=config.MEMORY_DIR)
        # Success message will be shown during chat_loop startup
    except Exception as e:
        print(f"\033[91m[System] ❌ Graph system initialization failed: {e}\033[0m")
        print(f"\033[93m[System] ⚠️  Continuing without graph system...\033[0m")
        graph_lite = None

# --- Global Procedural Memory System ---
# Initialize procedural memory if enabled
procedural_memory = None
if config.ENABLE_PROCEDURAL_MEMORY:
    try:
        procedural_memory = ProceduralMemory(memory_dir=config.MEMORY_DIR)
        # Success message will be shown during chat_loop startup
    except Exception as e:
        print(f"\033[91m[System] ❌ Procedural memory initialization failed: {e}\033[0m")
        print(f"\033[93m[System] ⚠️  Continuing without procedural memory...\033[0m")
        procedural_memory = None

# --- Global Knowledge Curator ---
# Initialize curator if graph and curator are enabled
curator = None
if config.ENABLE_GRAPH and config.ENABLE_CURATOR and graph_lite is not None:
    try:
        curator = KnowledgeCurator(graph_lite, llm_call_func=call_llm_raw)
    except Exception as e:
        print(f"\033[91m[System] ❌ Curator initialization failed: {e}\033[0m")
        curator = None


# --- Global Sub-Agent Orchestrator ---
# Initialize orchestrator if sub-agents are enabled (replaces Deep Think)
orchestrator = None
if config.ENABLE_SUB_AGENTS:
    try:
        # Note: execute_tool is defined later in this file (line ~374)
        # Use lambda for lazy evaluation to avoid NameError
        orchestrator = Orchestrator(
            llm_call_func=call_llm_raw,
            execute_tool_func=lambda tool_name, args: execute_tool(tool_name, args),
            graph_lite=graph_lite,
            procedural_memory=procedural_memory,
            parallel_enabled=config.SUB_AGENT_PARALLEL_ENABLED,
            max_workers=config.SUB_AGENT_MAX_WORKERS,
            timeout=config.SUB_AGENT_TIMEOUT
        )
    except Exception as e:
        print(f"\033[91m[System] ❌ Orchestrator initialization failed: {e}\033[0m")
        orchestrator = None

# --- Global Hybrid RAG System ---
# Initialize HybridRAG if Smart RAG is enabled
hybrid_rag = None
if config.ENABLE_SMART_RAG or config.DEBUG_MODE:
    try:
        from core.hybrid_rag import HybridRAG
        from core.spec_graph import build_spec_graph_from_chunks
        from core.rag_db import get_rag_db
        
        # Get DB (singleton)
        _rag_db = get_rag_db()
        
        # Build Spec Graph from chunks (fast enough for 2-3k chunks)
        _spec_chunks = [c for c in _rag_db.chunks.values() if c.category == 'spec']
        if _spec_chunks:
            _spec_graph = build_spec_graph_from_chunks(_spec_chunks)
            if config.DEBUG_MODE:
                print(Color.system(f"[System] Built SpecGraph with {len(_spec_graph.nodes)} nodes"))
        else:
            _spec_graph = None
            
        hybrid_rag = HybridRAG(_rag_db, graph_lite, _spec_graph)
        
    except Exception as e:
        print(Color.warning(f"[System] ❌ HybridRAG initialization failed: {e}"))
        hybrid_rag = None


# --- Global Message Classifier ---
# Initialize classifier for smart compression
message_classifier = MessageClassifier() if config.ENABLE_SMART_COMPRESSION else None

# --- Color Utilities (ANSI Escape Codes) ---
# Moved to display.py

# LLM Client functions moved to llm_client.py

# --- Compression Prompts ---
STRUCTURED_SUMMARY_PROMPT = """Summarize the following conversation history in a structured format:

## Objectives
- List main goals or user requests (What was the user trying to achieve?)

## Completed Tasks
- Enumerate successfully finished tasks with outcomes

## Key Decisions & Changes
- Important choices made (e.g., architecture, API changes, renamed files)
- Configuration updates

## Issues Encountered
- Errors or problems that occurred
- How they were resolved (or if still open)

## Current State
- What's working now
- What's pending or blocked

## Important Context
- File paths, module names, or signals mentioned
- User preferences or conventions established

Keep each section concise. Use bullet points. Omit sections with no content."""

# --- 3. History Management ---

def save_conversation_history(messages):
    """Saves conversation history to a JSON file if enabled in config."""
    if not config.SAVE_HISTORY:
        return

    try:
        with open(config.HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)
        print(Color.success(f"[System] History saved to {config.HISTORY_FILE}"))
    except Exception as e:
        print(Color.error(f"[System] Failed to save history: {e}"))

def load_conversation_history():
    """Loads conversation history from JSON file if it exists."""
    if not config.SAVE_HISTORY:
        return None

    try:
        if os.path.exists(config.HISTORY_FILE):
            with open(config.HISTORY_FILE, 'r', encoding='utf-8') as f:
                messages = json.load(f)
                print(Color.success(f"[System] Loaded {len(messages)} messages from {config.HISTORY_FILE}"))
                return messages
    except Exception as e:
        print(Color.error(f"[System] Failed to load history: {e}"))

    return None

# --- 4. ReAct Logic ---


def sanitize_action_text(text):
    """
    Sanitize common LLM output errors in Action calls.
    Fixes patterns like: end_line=26") -> end_line=26)
    Also handles markdown formatting like **Action:** -> Action:
    """
    import re
    
    # Remove markdown bold around "Action:" (common LLM behavior)
    # e.g., **Action:** spawn_plan(...) -> Action: spawn_plan(...)
    text = re.sub(r'\*\*Action:\*\*', 'Action:', text)
    text = re.sub(r'\*\*Action\*\*:', 'Action:', text)  # Alternate format
    
    # Pattern: number followed by quote then closing paren/comma
    # e.g., =26") or =26", -> =26) or =26,
    text = re.sub(r'=(\d+)"([,\)])', r'=\1\2', text)
    
    # Pattern: number followed by single quote then closing paren/comma  
    text = re.sub(r"=(\d+)'([,\)])", r'=\1\2', text)
    
    return text


def parse_all_actions(text):
    """
    Parses ALL 'Action: Tool(args)' occurrences from the text.
    Returns a list of (tool_name, args_str) tuples.
    
    Improvements:
    - Sanitizes common LLM output errors (like end_line=26")
    - On parse failure, skips to next Action instead of stopping
    """
    # Sanitize common errors first
    text = sanitize_action_text(text)
    
    actions = []
    start_pos = 0
    # Support "Action:", "**Action:**", etc. 
    # Handle optional markdown formatting (bold **, italic _, code `) around tool name
    # e.g., Action: `read_file`(...) or **Action**: **read_file**(...)
    pattern = r"(?:\*\*|__)?Action(?:\*\*|__)?::*\s*[`*_]*\s*(\w+)\s*[`*_]*\s*\("
    
    if config.DEBUG_MODE:
        print(f"[DEBUG] parse_all_actions input length: {len(text)}")

    while True:
        match = re.search(pattern, text[start_pos:], re.DOTALL)
        if not match:
            break
            
        tool_name = match.group(1)
        # Absolute match position (after "tool_name(")
        match_start = start_pos + match.end()
        
        # Find matching closing parenthesis
        paren_count = 1
        in_single_quote = False
        in_double_quote = False
        in_triple_single = False
        in_triple_double = False
        i = match_start
        
        while i < len(text) and paren_count > 0:
            # Check for triple quotes first (only if not inside single/double quotes)
            if not in_single_quote and not in_double_quote:
                if i + 2 < len(text):
                    if text[i:i+3] == '"""':
                        if not in_triple_single:
                            in_triple_double = not in_triple_double
                            i += 3
                            continue
                    elif text[i:i+3] == "'''":
                        if not in_triple_double:
                            in_triple_single = not in_triple_single
                            i += 3
                            continue

            char = text[i]

            # Handle escape sequences
            if char == '\\':
                # Skip the backslash and the next character (it is escaped)
                i += 2
                continue

            # Track quotes (only if not in triple quotes)
            if not in_triple_single and not in_triple_double:
                if char == '"' and not in_single_quote:
                    in_double_quote = not in_double_quote
                elif char == "'" and not in_double_quote:
                    in_single_quote = not in_single_quote

            # Count parentheses (only if not in any quotes)
            if not (in_single_quote or in_double_quote or in_triple_single or in_triple_double):
                if char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1

            i += 1
            
        if paren_count == 0:
            args_str = text[match_start:i-1]
            actions.append((tool_name, args_str))
            start_pos = i  # Continue searching after this action
        else:
            # Unmatched parentheses - check if we hit end of string (Truncated Output)
            if i >= len(text):
                if config.DEBUG_MODE:
                    print(Color.warning(f"[System] ⚠️  Action '{tool_name}' appears truncated at end of text. Attempting auto-recovery..."))
                
                # Recover argument string up to current position
                args_str = text[match_start:]
                
                # Check if it looks like a valid partial argument (e.g. key="val...)
                # Heuristic: If it has at least one char, we try to use it.
                if args_str:
                     # Attempt to close quotes if open
                    if in_double_quote: args_str += '"'
                    elif in_single_quote: args_str += "'"
                    elif in_triple_double: args_str += '"""'
                    elif in_triple_single: args_str += "'''"
                    
                    actions.append((tool_name, args_str))
                    if config.DEBUG_MODE:
                        print(Color.warning(f"[System] 🔧 Auto-recovered truncated action: {tool_name}({args_str}...)"))
                    break # Stop parsing as we are at end of text
            
            # Unmatched parentheses in middle of text - skip this action and try next one
            if config.DEBUG_MODE:
                print(f"[DEBUG] parse_all_actions: Unmatched parentheses for {tool_name}, skipping to next Action")
            
            # Find next "Action:" and continue from there instead of breaking
            next_match = re.search(pattern, text[match_start:], re.DOTALL)
            if next_match:
                start_pos = match_start + next_match.start()
            else:
                 # No more actions possible
                start_pos = len(text)

            
    if config.DEBUG_MODE:
        print(f"[DEBUG] parse_all_actions found {len(actions)} actions")
        
    return actions


def parse_implicit_actions(text):
    """
    Parses implicit tool calls (e.g. from Command R+ format).
    Pattern: ... to=repo_browser.tool_name ... <|message|>{ json_args }
    """
    actions = []
    # Regex to capture tool name and JSON args
    # Look for 'to=...toolname' ... '<|message|> {json}'
    pattern = r"to=(?:[\w\.]+\.)?(\w+).*?<\|message\|>\s*(\{.*?\})"
    
    matches = re.finditer(pattern, text, re.DOTALL)
    for match in matches:
        tool_name = match.group(1)
        json_str = match.group(2)
        try:
            # Fix potential incomplete JSON if stopped mid-stream?
            # But we stopped at <|call|>, so JSON should be complete.
            args_dict = json.loads(json_str)
            
            # Reconstruct args string: key="value", key2=123
            pairs = []
            for k, v in args_dict.items():
                # Use json.dumps to handle escaping and quotes correctly
                pairs.append(f'{k}={json.dumps(v)}')
            
            args_str_reconstructed = ", ".join(pairs)
            actions.append((tool_name, args_str_reconstructed))
            
            if config.DEBUG_MODE:
                print(f"[DEBUG] Parsed implicit action: {tool_name}({args_str_reconstructed})")
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"[DEBUG] Failed to parse implicit JSON: {e}")
            pass
            
    return actions

def parse_tool_arguments(args_str):
    """
    Safely parses tool arguments from string.
    Supports: key="value", key='value', key=123, key=triple-quote
    Returns: (args_list, kwargs_dict)
    """
    args = []
    kwargs = {}

    # Trim whitespace
    args_str = args_str.strip()
    if not args_str:
        return args, kwargs

    i = 0
    while i < len(args_str):
        # Skip whitespace and commas
        while i < len(args_str) and args_str[i] in ' ,\n':
            i += 1

        if i >= len(args_str):
            break

        # Check if it's a keyword argument (key=value)
        key_match = re.match(r'(\w+)\s*=\s*', args_str[i:])

        if key_match:
            # Keyword argument
            key = key_match.group(1)
            i += key_match.end()

            # Parse value
            value, chars_consumed = parse_value(args_str[i:])
            kwargs[key] = value
            i += chars_consumed
        else:
            # Positional argument
            value, chars_consumed = parse_value(args_str[i:])
            args.append(value)
            i += chars_consumed

    return args, kwargs

def parse_value(text):
    """
    Parses a single value from text.
    Returns: (value, chars_consumed)
    """
    text = text.lstrip()

    if not text:
        return None, 0

    # Triple-quoted string (""" or ''')
    if text.startswith('"""') or text.startswith("'''"):
        quote = text[:3]
        end_pos = text.find(quote, 3)
        if end_pos == -1:
            raise ValueError(f"Unclosed triple-quote string")
        value = text[3:end_pos]
        return value, end_pos + 3

    # Regular quoted string (" or ')
    if text[0] in '"\'':
        quote = text[0]
        i = 1
        value = ""
        while i < len(text):
            if text[i] == '\\' and i + 1 < len(text):
                # Handle escape sequences
                next_char = text[i + 1]
                if next_char == 'n':
                    value += '\n'
                elif next_char == 't':
                    value += '\t'
                elif next_char == '\\':
                    value += '\\'
                elif next_char == quote:
                    value += quote
                else:
                    value += next_char
                i += 2
            elif text[i] == quote:
                return value, i + 1
            else:
                value += text[i]
                i += 1
        raise ValueError(f"Unclosed string")

    # Number or identifier
    match = re.match(r'([^,)\s]+)', text)
    if match:
        value_str = match.group(1)
        # Try to parse as number
        try:
            if '.' in value_str:
                return float(value_str), len(value_str)
            else:
                return int(value_str), len(value_str)
        except ValueError:
            # Return as string
            return value_str, len(value_str)

    return None, 0


_PLAN_FILE = "current_plan.md"


def _read_text_file_best_effort(path: str, max_chars: Optional[int] = None) -> Optional[str]:
    """Read a UTF-8 text file, returning None on error."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = f.read()
            return data[:max_chars] if (max_chars is not None and isinstance(data, str)) else data
    except (FileNotFoundError, IsADirectoryError):
        return None
    except Exception:
        return None


def _parse_plan_task(plan_content: str) -> Optional[str]:
    if not plan_content:
        return None
    match = re.search(r"^##\s*Task:\s*(.+)$", plan_content, re.MULTILINE)
    return match.group(1).strip() if match else None


def _parse_plan_steps(plan_content: str) -> List[Tuple[int, str, bool]]:
    """
    Parse steps from current_plan.md.
    Returns a list of (step_number, text, done).
    """
    if not plan_content:
        return []

    steps: List[Tuple[int, str, bool]] = []
    seen_numbers = set()

    for raw_line in plan_content.splitlines():
        line = raw_line.rstrip()
        match = re.match(r"^\s*(\d+)\.\s*(.+?)\s*$", line)
        if not match:
            continue

        try:
            step_number = int(match.group(1))
        except ValueError:
            continue

        if step_number in seen_numbers:
            continue

        text = match.group(2).strip()
        done = "✅" in text
        text = text.replace("✅", "").strip()

        seen_numbers.add(step_number)
        steps.append((step_number, text, done))

    steps.sort(key=lambda x: x[0])
    return steps


def _plan_is_approved(plan_content: str) -> bool:
    return bool(plan_content) and ("STATUS: APPROVED" in plan_content)


def _get_plan_state() -> Dict[str, object]:
    """
    Best-effort snapshot of plan status for flow routing.
    """
    content = _read_text_file_best_effort(_PLAN_FILE, max_chars=20000)
    if not content:
        return {
            "exists": False,
            "approved": False,
            "task": None,
            "steps": [],
            "complete": False,
            "next_step": None,
        }

    steps = _parse_plan_steps(content)
    approved = _plan_is_approved(content)
    complete = bool(steps) and all(done for _, _, done in steps)
    next_step = next(((n, t, d) for (n, t, d) in steps if not d), None)

    return {
        "exists": True,
        "approved": approved,
        "task": _parse_plan_task(content),
        "steps": steps,
        "complete": complete,
        "next_step": next_step,
    }


def _looks_like_plan_status_request(text: str) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return False
    patterns = [
        r"\bcheck\s+plan\s+status\b",
        r"\bplan\s+status\b",
        r"계획\s*상태",
        r"승인\s*확인",
        r"status\s*:",
    ]
    return any(re.search(p, t) for p in patterns)


def _looks_like_execute_plan_request(text: str) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return False
    patterns = [
        r"\bexecute\s+plan\b",
        r"\brun\s+plan\b",
        r"\bcontinue\b",
        r"\bproceed\b",
        r"계획\s*실행",
        r"계획\s*진행",
        r"계속\s*진행",
        r"실행해",
        r"진행해",
    ]
    return any(re.search(p, t) for p in patterns)


def _looks_like_plan_approval_ack(text: str) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return False
    patterns = [
        r"\bapproved\b",
        r"\bokay\b",
        r"\bok\b",
        r"승인",
        r"오케이",
    ]
    return any(re.search(p, t) for p in patterns)


# ============================================================
# Phase 4: Autonomous Decision-Making - Complexity Analysis
# ============================================================

def _analyze_task_complexity_llm(task_description: str) -> dict:
    """
    Use LLM to analyze task complexity and determine if planning is needed.

    Args:
        task_description: The user's task/request

    Returns:
        dict with keys:
        - complexity: "simple" | "medium" | "complex"
        - needs_planning: bool
        - estimated_steps: int (1-10)
        - reasoning: str (why this complexity)
    """
    analysis_prompt = """You are a task complexity analyzer for a coding agent.

Analyze the task and output JSON only (no markdown, no explanations).

Complexity Guidelines:
- **simple**: 1-2 actions
  - Examples: fix typo, read single file, simple question
  - No planning needed - just execute

- **medium**: 3-5 steps
  - Examples: small feature, bug fix with testing, refactor a function
  - Can execute directly OR use simple plan

- **complex**: 6+ steps, exploration needed
  - Examples: design new system, multi-file refactoring, new feature with tests
  - MUST use Plan Mode - requires exploration and structured approach

Output JSON only:
{
  "complexity": "simple|medium|complex",
  "needs_planning": true/false,
  "estimated_steps": 1-10,
  "reasoning": "brief explanation"
}
"""

    try:
        response = call_llm_raw(
            [
                {"role": "system", "content": analysis_prompt},
                {"role": "user", "content": f"Task: {task_description}"},
            ],
            temperature=config.AUTONOMOUS_TEMPERATURE,
        )

        if not response or response.startswith("Error calling LLM:"):
            return {"complexity": "unknown", "needs_planning": False, "estimated_steps": 0, "reasoning": "LLM error"}

        # Extract JSON
        json_match = re.search(r"\{[\s\S]*\}", response)
        if not json_match:
            return {"complexity": "unknown", "needs_planning": False, "estimated_steps": 0, "reasoning": "No JSON found"}

        data = json.loads(json_match.group(0))

        # Validate and return
        return {
            "complexity": data.get("complexity", "unknown"),
            "needs_planning": data.get("needs_planning", False),
            "estimated_steps": data.get("estimated_steps", 0),
            "reasoning": data.get("reasoning", "No reasoning provided")
        }

    except Exception as e:
        print(Color.warning(f"[Autonomous] LLM complexity analysis failed: {e}"))
        return {"complexity": "unknown", "needs_planning": False, "estimated_steps": 0, "reasoning": str(e)}


def _should_auto_plan_heuristic(task_description: str) -> bool:
    """
    Original heuristic-based trigger for Plan→Approve flow.
    Used as fallback when AUTONOMOUS_COMPLEXITY_ANALYSIS is disabled.
    """
    text = (task_description or "").strip()
    if not text:
        return False

    # Avoid triggering on explicit plan execution/status commands.
    if _looks_like_execute_plan_request(text) or _looks_like_plan_status_request(text):
        return False

    if "\n" in text:
        return True

    if len(text) >= config.CLAUDE_FLOW_COMPLEX_TASK_CHAR_THRESHOLD:
        return True

    lowered = text.lower()
    keywords = [
        # English
        "implement", "design", "refactor", "feature", "pipeline", "agent",
        "memory", "rag", "test", "simulate", "integration",
        # Korean
        "구현", "설계", "리팩토링", "기능", "테스트", "시뮬레이션", "에이전트", "플로우", "개선",
    ]
    hits = sum(1 for k in keywords if k in lowered)
    return hits >= 2


def _should_auto_plan(task_description: str) -> bool:
    """
    Determine if Plan Mode should be triggered automatically.

    Phase 4: Uses LLM-based complexity analysis when AUTONOMOUS_COMPLEXITY_ANALYSIS=true,
    otherwise falls back to heuristic method.

    Args:
        task_description: The user's task/request

    Returns:
        True if Plan Mode should be entered, False otherwise
    """
    text = (task_description or "").strip()
    if not text:
        return False

    # Avoid triggering on explicit plan execution/status commands
    if _looks_like_execute_plan_request(text) or _looks_like_plan_status_request(text):
        return False

    # Phase 4: LLM-based analysis
    if config.AUTONOMOUS_COMPLEXITY_ANALYSIS:
        analysis = _analyze_task_complexity_llm(task_description)

        print(Color.system(f"\n[Autonomous] Task Complexity Analysis:"))
        print(Color.info(f"  Complexity: {analysis['complexity']}"))
        print(Color.info(f"  Estimated Steps: {analysis['estimated_steps']}"))
        print(Color.info(f"  Needs Planning: {analysis['needs_planning']}"))
        print(Color.info(f"  Reasoning: {analysis['reasoning']}\n"))

        # Use LLM decision if valid
        if analysis["complexity"] != "unknown":
            return analysis["needs_planning"]

        # Fallback to heuristic if LLM failed
        print(Color.warning("[Autonomous] LLM analysis failed, using heuristic fallback"))

    # Fallback: heuristic method
    return _should_auto_plan_heuristic(task_description)


# ============================================================
# Phase 3: Claude Flow Complete Implementation - Helper Functions
# ============================================================

def _run_explore_agent(target: str) -> str:
    """
    Run a single Explore agent using spawn_explore tool

    Args:
        target: Exploration target description

    Returns:
        Exploration result summary
    """
    try:
        # Use spawn_explore tool
        result = tools.spawn_explore(query=target, thoroughness="medium")
        return f"Explored: {target}\nResult:\n{result}"
    except Exception as e:
        return f"Explored: {target}\nError: {str(e)}"


def _spawn_parallel_explore_agents(task_description: str) -> List[str]:
    """
    Spawn multiple Explore agents in parallel

    Args:
        task_description: Task to explore

    Returns:
        List of exploration results
    """
    explore_count = min(config.PLAN_MODE_EXPLORE_COUNT, 5)  # Max 5

    print(Color.system(f"\n[Claude Flow] Phase 1: Spawning {explore_count}× Explore Agents (parallel)..."))

    # Define exploration targets
    explore_targets = [
        f"Explore existing implementations and patterns related to: {task_description}",
        f"Explore relevant modules, dependencies, and architecture for: {task_description}",
        f"Explore test patterns, examples, and edge cases for: {task_description}",
    ][:explore_count]

    from concurrent.futures import ThreadPoolExecutor, as_completed

    results = []

    with ThreadPoolExecutor(max_workers=explore_count) as executor:
        futures = {
            executor.submit(_run_explore_agent, target): i
            for i, target in enumerate(explore_targets)
        }

        for future in as_completed(futures):
            try:
                result = future.result(timeout=120)  # 2 min timeout
                results.append(result)
                agent_num = futures[future]
                print(Color.success(f"[Claude Flow] Explore Agent {agent_num + 1}/{explore_count} completed"))
            except Exception as e:
                agent_num = futures[future]
                error_msg = f"Explore target {agent_num + 1} failed: {str(e)}"
                results.append(error_msg)
                print(Color.error(f"[Claude Flow] {error_msg}"))

    return results


def _spawn_plan_agent(task_description: str, explore_results: List[str]) -> List[str]:
    """
    Spawn Plan agent to create implementation steps

    Args:
        task_description: Task to plan
        explore_results: Results from Explore agents

    Returns:
        List of plan steps
    """
    print(Color.system("\n[Claude Flow] Phase 2: Spawning Plan Agent..."))

    # Combine exploration results
    context = "\n\n".join([
        f"Exploration {i+1}:\n{result}"
        for i, result in enumerate(explore_results)
    ]) if explore_results else "No exploration data available."

    # Generate plan steps via LLM with context
    plan_steps = _generate_plan_steps_via_llm(
        task_description,
        additional_context=context
    )

    print(Color.success(f"[Claude Flow] Plan Agent generated {len(plan_steps)} steps"))

    return plan_steps


def _execute_plan_mode_workflow(messages, task_description: str) -> List[Dict]:
    """
    Complete Plan Mode Workflow (Claude Code style)

    6-Step Workflow:
    1. Complexity Analysis (already done by caller)
    2. Spawn 3× Explore Agents (parallel)
    3. Spawn 1× Plan Agent
    4. Review critical files (optional, covered by explore)
    5. Write plan file
    6. Wait for approval

    Args:
        messages: Message history
        task_description: Task to plan

    Returns:
        Updated messages with plan creation result
    """
    print(Color.system("\n[Claude Flow] ========================================"))
    print(Color.system("[Claude Flow] Entering Plan Mode Workflow..."))
    print(Color.system("[Claude Flow] ========================================"))

    # Phase 1: Spawn 3× Explore Agents (병렬)
    explore_results = []
    if config.PLAN_MODE_PARALLEL_EXPLORE:
        explore_results = _spawn_parallel_explore_agents(task_description)
    else:
        print(Color.system("[Claude Flow] Phase 1: Skipped (PLAN_MODE_PARALLEL_EXPLORE=false)"))

    # Phase 2: Spawn 1× Plan Agent
    plan_steps = _spawn_plan_agent(task_description, explore_results)

    # Phase 3: Review critical files (optional - already covered by explore agents)
    # Skipped for now

    # Phase 4: Write plan file
    if not plan_steps:
        # Fallback to default steps
        plan_steps = [
            "관련 파일/구조 탐색",
            "구현 계획 및 변경 범위 확정",
            "코드 수정/추가 적용",
            "테스트/검증 및 회귀 확인",
            "정리 및 문서 업데이트",
        ]
        print(Color.warning("[Claude Flow] Using fallback plan steps"))

    create_msg = tools.create_plan(
        task_description=task_description,
        steps="\n".join(plan_steps)
    )

    # Phase 5: Wait for approval
    approval_msg = tools.wait_for_plan_approval()
    plan_preview = tools.get_plan()

    print(Color.success(f"[Claude Flow] {create_msg}"))
    print(Color.info(approval_msg))
    print(Color.system("\n[Claude Flow] Plan preview:\n"))
    print(plan_preview[:2000] + ("\n...(truncated)" if len(plan_preview) > 2000 else ""))
    print()

    messages.append({
        "role": "assistant",
        "content": f"{create_msg}\n\n{approval_msg}",
    })

    return messages


def _generate_plan_steps_via_llm(task_description: str, max_steps: int = 8, additional_context: str = "") -> List[str]:
    """
    Ask the LLM for a concise plan as JSON {"steps":[...]} and extract steps.
    Returns [] on failure.
    """
    planning_prompt = """You are a planning assistant for a coding agent.

Write a concise implementation plan as JSON only (no markdown, no code).

Constraints:
- Steps must be actionable and short (one sentence each)
- No code snippets
- Mention concrete file paths when applicable

Output JSON only:
{
  "steps": ["...", "..."]
}
"""

    user_content = f"Task: {task_description}"
    if additional_context:
        user_content += f"\n\nContext from exploration:\n{additional_context}"

    response = call_llm_raw(
        [
            {"role": "system", "content": planning_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,
    )

    if not response or response.startswith("Error calling LLM:"):
        return []

    json_match = re.search(r"\{[\s\S]*\}", response)
    if not json_match:
        return []

    try:
        data = json.loads(json_match.group(0))
    except Exception:
        return []

    steps = data.get("steps")
    if not isinstance(steps, list):
        return []

    cleaned: List[str] = []
    for step in steps:
        if not isinstance(step, str):
            continue
        s = step.strip()
        s = re.sub(r"^\s*[-*]\s*", "", s)
        s = re.sub(r"^\s*\d+\.\s*", "", s)
        if not s:
            continue
        if s not in cleaned:
            cleaned.append(s)

    return cleaned[:max_steps]


def _create_plan_and_wait(messages, task_description: str) -> List[Dict]:
    """
    Create current_plan.md and instruct user to approve.
    Uses the complete Plan Mode Workflow (Phase 3).
    """
    # Use the new complete workflow
    return _execute_plan_mode_workflow(messages, task_description)


def _execute_approved_plan(messages, mode: str) -> List[Dict]:
    """
    Execute the next (or all) incomplete steps in an APPROVED plan.
    Enhanced with TodoTracker integration (Phase 3).
    """
    state = _get_plan_state()
    if not state.get("exists"):
        msg = "No plan file found. Use create_plan() first."
        print(Color.warning(f"[Claude Flow] {msg}"))
        messages.append({"role": "assistant", "content": msg})
        return messages

    if not state.get("approved"):
        status = tools.check_plan_status()
        print(Color.warning("[Claude Flow] Plan is not approved yet."))
        print(status)
        messages.append({"role": "assistant", "content": status})
        return messages

    if state.get("complete"):
        msg = "✅ Plan is already complete (all steps marked ✅)."
        print(Color.success(f"[Claude Flow] {msg}"))
        messages.append({"role": "assistant", "content": msg})
        return messages

    steps: List[Tuple[int, str, bool]] = state.get("steps", [])  # type: ignore[assignment]
    plan_task = state.get("task") or "Current plan"

    # Phase 3: Initialize TodoTracker
    todo_tracker = None
    if config.ENABLE_TODO_TRACKING:
        todo_tracker = TodoTracker()
        todos = [
            {
                "content": f"Step {num}: {text}",
                "status": "completed" if done else "pending",
                "activeForm": f"Executing Step {num}: {text}"
            }
            for num, text, done in steps
        ]
        todo_tracker.add_todos(todos)
        print(Color.system("\n[Claude Flow] ========================================"))
        print(Color.info(todo_tracker.format_progress()))
        print(Color.system("[Claude Flow] ========================================\n"))

    for step_number, step_text, done in steps:
        if done:
            continue

        # Phase 3: Mark current step as in_progress
        if todo_tracker:
            step_index = step_number - 1  # 0-indexed
            todo_tracker.mark_in_progress(step_index)
            print(Color.system("\n[Claude Flow] ========================================"))
            print(Color.info(todo_tracker.format_progress()))
            print(Color.system("[Claude Flow] ========================================\n"))

        print(Color.system(f"\n[Claude Flow] Executing plan step {step_number}: {step_text}"))

        step_guidance = f"""=== EXECUTE APPROVED PLAN ===
Task: {plan_task}
Current step: {step_number}. {step_text}

Rules:
- Focus ONLY on the current step.
- Use tools as needed.
- When the step is complete, you MUST call: mark_step_done(step_number={step_number})
- After marking the step done, provide a brief summary and STOP (no more Actions).
============================
"""
        messages.append({"role": "system", "content": step_guidance})

        step_tracker = IterationTracker(max_iterations=config.CLAUDE_FLOW_STEP_MAX_ITERATIONS)
        messages = run_react_agent(
            messages,
            step_tracker,
            f"[Plan Step {step_number}] {step_text}",
            mode=mode,
            allow_claude_flow=False,
            preface_enabled=False,
        )

        # Re-check if the step was marked done.
        refreshed = _get_plan_state()
        refreshed_steps: List[Tuple[int, str, bool]] = refreshed.get("steps", [])  # type: ignore[assignment]
        step_done_now = next((d for (n, _t, d) in refreshed_steps if n == step_number), False)

        # Phase 3: Mark step as completed in TodoTracker
        if todo_tracker and step_done_now:
            todo_tracker.mark_completed(step_index)
            print(Color.system("\n[Claude Flow] ========================================"))
            print(Color.success(todo_tracker.format_progress()))
            print(Color.system("[Claude Flow] ========================================\n"))

        if not step_done_now:
            msg = (
                f"[Claude Flow] Step {step_number} is not marked ✅ yet. "
                f"Review `current_plan.md`, adjust if needed, then run 'execute plan' again."
            )
            print(Color.warning(msg))
            messages.append({"role": "assistant", "content": msg})
            break

        if not config.CLAUDE_FLOW_AUTO_EXECUTE:
            break

    # Phase 3: Final progress summary
    if todo_tracker:
        print(Color.system("\n[Claude Flow] ========================================"))
        print(Color.system("[Claude Flow] Final Progress:"))
        print(Color.info(todo_tracker.format_progress()))
        print(Color.system("[Claude Flow] ========================================\n"))

    return messages


def _extract_steps_from_plan_text(plan_text: str) -> List[str]:
    if not plan_text:
        return []

    def _steps_from_section(marker: str) -> List[str]:
        if marker not in plan_text:
            return []
        section = plan_text.split(marker, 1)[1]
        section = section.split("##", 1)[0]
        matches = re.findall(r'\d+\.\s*(.+?)(?=\n\d+\.|\n##|$)', section, re.DOTALL)
        return [m.strip() for m in matches if m.strip()]

    steps = _steps_from_section("## Implementation Steps")
    if not steps:
        steps = _steps_from_section("## Steps")
    if steps:
        return steps

    matches = re.findall(r'^\s*\d+\.\s*(.+)$', plan_text, re.MULTILINE)
    return [m.strip() for m in matches if m.strip()]


def _extract_task_from_plan_text(plan_text: str) -> str:
    if "## Task" not in plan_text:
        return ""
    section = plan_text.split("## Task", 1)[1]
    lines = [line.strip() for line in section.splitlines()]
    for line in lines:
        if line:
            return line
    return ""


def _execute_plan_from_file(messages: List[Dict], plan_path: str) -> List[Dict]:
    """
    Execute a plan from a saved plan file.

    Args:
        messages: Current message history
        plan_path: Path to the plan file

    Returns:
        Updated messages after plan execution
    """
    # Read plan file
    if not plan_path:
        msg = "Error: Empty plan path provided"
        print(Color.error(f"[Plan Mode] {msg}"))
        messages.append({"role": "assistant", "content": msg})
        return messages

    try:
        with open(plan_path, "r", encoding="utf-8") as handle:
            plan_text = handle.read()
    except FileNotFoundError:
        msg = f"Error: Plan file not found: {plan_path}"
        print(Color.error(f"[Plan Mode] {msg}"))
        messages.append({"role": "assistant", "content": msg})
        return messages
    except PermissionError:
        msg = f"Error: Permission denied reading plan file: {plan_path}"
        print(Color.error(f"[Plan Mode] {msg}"))
        messages.append({"role": "assistant", "content": msg})
        return messages
    except Exception as e:
        msg = f"Error: Failed to read plan file: {e}"
        print(Color.error(f"[Plan Mode] {msg}"))
        messages.append({"role": "assistant", "content": msg})
        return messages

    if not plan_text or not plan_text.strip():
        msg = f"Error: Plan file is empty: {plan_path}"
        print(Color.error(f"[Plan Mode] {msg}"))
        messages.append({"role": "assistant", "content": msg})
        return messages

    # Extract task and steps
    task = _extract_task_from_plan_text(plan_text)
    task_label = task or f"Execute approved plan ({os.path.basename(plan_path)})"
    steps = _extract_steps_from_plan_text(plan_text)

    if not steps:
        print(Color.warning("[Plan Mode] No steps found in plan, proceeding with full plan text"))

    # Create TodoWrite if steps exist
    if config.ENABLE_TODO_TRACKING and len(steps) >= 3:
        try:
            todos = []
            for idx, step in enumerate(steps):
                status = "in_progress" if idx == 0 else "pending"
                todos.append({
                    "content": step,
                    "activeForm": f"Executing: {step}",
                    "status": status
                })
            todo_display = tools.todo_write(todos)
            if todo_display:
                print(Color.info(todo_display))
        except Exception as e:
            print(Color.warning(f"[Plan Mode] Failed to create todo list: {e}"))

    # Add plan message
    plan_message = (
        "You have an approved implementation plan. Execute the steps in order.\n"
        "Do not change the plan without asking. Use tools as needed.\n\n"
        f"{plan_text}"
    )
    messages.append({"role": "user", "content": plan_message})

    # Execute plan
    try:
        tracker = IterationTracker(max_iterations=config.MAX_ITERATIONS)
        return run_react_agent(
            messages,
            tracker,
            task_label,
            mode="interactive",
            allow_claude_flow=False
        )
    except Exception as e:
        msg = f"Error during plan execution: {e}"
        print(Color.error(f"[Plan Mode] {msg}"))
        if config.FULL_PROMPT_DEBUG:
            import traceback
            print(Color.DIM + traceback.format_exc() + Color.RESET)
        messages.append({"role": "assistant", "content": msg})
        return messages


def _maybe_handle_claude_flow(messages, task_description: str, mode: str) -> Optional[List[Dict]]:
    """
    Route control for Claude Code-like flow.
    Returns updated messages if handled, otherwise None.
    """
    if config.CLAUDE_FLOW_MODE == "off":
        return None

    state = _get_plan_state()
    user_text = (task_description or "").strip()

    if state.get("exists"):
        if _looks_like_plan_status_request(user_text):
            status = tools.check_plan_status()
            print(status)
            messages.append({"role": "assistant", "content": status})
            return messages

        if not state.get("approved") and config.CLAUDE_FLOW_REQUIRE_APPROVAL:
            status = tools.check_plan_status()
            print(Color.warning("[Claude Flow] Waiting for plan approval."))
            print(status)
            messages.append({"role": "assistant", "content": status})
            return messages

        if state.get("approved") and not state.get("complete"):
            if _looks_like_execute_plan_request(user_text) or _looks_like_plan_approval_ack(user_text):
                return _execute_approved_plan(messages, mode=mode)

        return None

    # No existing plan file: handle explicit plan commands gracefully.
    if (
        _looks_like_plan_status_request(user_text)
        or _looks_like_execute_plan_request(user_text)
        or _looks_like_plan_approval_ack(user_text)
    ):
        msg = "No plan file found. Ask me to create a plan first (or call create_plan())."
        print(Color.warning(f"[Claude Flow] {msg}"))
        messages.append({"role": "assistant", "content": msg})
        return messages

    # No existing plan file → maybe auto-create plan.
    if config.CLAUDE_FLOW_MODE == "always":
        return _create_plan_and_wait(messages, task_description)

    if config.CLAUDE_FLOW_MODE == "auto" and _should_auto_plan(task_description):
        return _create_plan_and_wait(messages, task_description)

    return None


def execute_tool(tool_name, args_str):
    if tool_name not in tools.AVAILABLE_TOOLS:
        return f"Error: Tool '{tool_name}' not found."

    func = tools.AVAILABLE_TOOLS[tool_name]
    try:
        # Parse arguments safely
        parsed_args, parsed_kwargs = parse_tool_arguments(args_str)

        if config.DEBUG_MODE:
            print(f"[DEBUG] Parsed args: {parsed_args}, kwargs: {parsed_kwargs}")

        result = func(*parsed_args, **parsed_kwargs)
        
        # Ensure result is string for downstream processing
        if not isinstance(result, str):
            import json
            try:
                # Pretty print dict/list for readability
                result = json.dumps(result, indent=2, ensure_ascii=False)
            except Exception:
                result = str(result)
                
        return result

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        return f"Error parsing/executing arguments: {e}\n{error_detail}\nargs_str was: {args_str[:200]}"

# --- 5. Context Management ---

# Helper functions moved to llm_client.py

def load_active_skills(messages, allowed_tools=None):
    """
    Load active skills based on recent conversation context

    Args:
        messages: Message history for context analysis
        allowed_tools: Optional set of allowed tools (for sub-agents)

    Returns:
        List of skill prompt strings to inject
    """
    if not config.ENABLE_SKILL_SYSTEM or not messages:
        return []

    try:
        from core.skill_system import get_skill_registry, get_skill_activator

        registry = get_skill_registry()
        activator = get_skill_activator()

        # Get recent user messages for context
        user_messages = [m for m in messages if m.get("role") == "user"]
        if not user_messages:
            return []

        # Analyze last 5 user messages
        recent_context = " ".join([
            msg["content"] for msg in user_messages[-5:]
            if isinstance(msg.get("content"), str)
        ])

        # Detect relevant skills
        active_skill_names = activator.detect_skills(
            context=recent_context,
            allowed_tools=allowed_tools,
            threshold=config.SKILL_ACTIVATION_THRESHOLD
        )

        if not active_skill_names:
            return []

        # Generate skill prompts
        skill_prompts = []
        for skill_name in active_skill_names:
            skill = registry.get_skill(skill_name)
            if skill:
                skill_prompts.append(skill.format_for_prompt())

        # Debug output
        if config.DEBUG_MODE and skill_prompts:
            print(Color.system(f"[PROMPT] ✅ Skills: {len(skill_prompts)} activated"))
            for skill_name in active_skill_names:
                print(Color.system(f"[PROMPT]     - {skill_name}"))

        return skill_prompts

    except ImportError as e:
        if config.DEBUG_MODE:
            print(Color.warning(f"[PROMPT] ⚠️ Skill system not available: {e}"))
        return []
    except Exception as e:
        if config.DEBUG_MODE:
            print(Color.warning(f"[PROMPT] ⚠️ Error loading skills: {e}"))
        return []


def build_system_prompt(messages=None, allowed_tools=None):
    """
    Build system prompt with memory, graph context, and procedural guidance if available.

    Args:
        messages: Optional message history for graph semantic search and procedural retrieval
        allowed_tools: Optional set of allowed tools (for sub-agents)

    Returns:
        Complete system prompt string
    """
    # Use new tool description system from config
    base_prompt = config.build_base_system_prompt(allowed_tools=allowed_tools)
    
    # Debug: Show prompt building start
    if config.DEBUG_MODE and messages:
        print(Color.system("[PROMPT] Building system prompt with context..."))
        print(Color.system(f"[PROMPT]   Messages in history: {len(messages)}"))

    # Build context section
    if memory_system is not None or graph_lite is not None or procedural_memory is not None:
        context_parts = []

        # Add memory preferences
        if memory_system is not None:
            memory_context = memory_system.format_all_for_prompt()
            if memory_context:
                context_parts.append(memory_context)
                if config.DEBUG_MODE:
                    # Get detailed breakdown
                    prefs = memory_system.list_preferences()
                    project_ctx = memory_system.list_project_context()
                    print(Color.system(f"[PROMPT] ✅ Memory loaded:"))
                    if prefs:
                        print(Color.system(f"[PROMPT]     📋 Preferences ({len(prefs)} items):"))
                        for key, val in prefs.items():
                            val_str = str(val)[:50] + "..." if len(str(val)) > 50 else str(val)
                            print(Color.system(f"[PROMPT]        {key}: {val_str}"))
                    if project_ctx:
                        print(Color.system(f"[PROMPT]     🗂️ Project Context ({len(project_ctx)} items):"))
                        for key, val in project_ctx.items():
                            val_str = str(val)[:50] + "..." if len(str(val)) > 50 else str(val)
                            print(Color.system(f"[PROMPT]        {key}: {val_str}"))

        # Add procedural guidance (from past similar tasks)
        if procedural_memory is not None and config.PROCEDURAL_INJECT_GUIDANCE and messages:
            # Get recent user messages to understand current task
            user_messages = [m for m in messages if m.get("role") == "user"]
            if user_messages:
                # Use last user message as current task
                current_task = user_messages[-1].get("content", "")[:200]

                try:
                    # Retrieve similar past trajectories
                    similar_trajs = procedural_memory.retrieve(
                        current_task,
                        limit=config.PROCEDURAL_RETRIEVE_LIMIT
                    )

                    # Filter by threshold
                    similar_trajs = [(score, traj) for score, traj in similar_trajs
                                    if score >= config.PROCEDURAL_SIMILARITY_THRESHOLD]

                    if similar_trajs:
                        guidance = "=== PAST EXPERIENCE ===\n\n"
                        guidance += "You have similar past experiences that may help:\n\n"

                        for i, (score, traj) in enumerate(similar_trajs, 1):
                            guidance += f"{i}. Task: {traj.task_description}\n"
                            guidance += f"   Outcome: {traj.outcome.upper()} ({traj.iterations} iterations)\n"

                            # Show key actions for successful trajectories
                            if traj.outcome == "success":
                                guidance += "   Successful approach:\n"
                                for action in traj.actions[:3]:  # Show first 3 actions
                                    guidance += f"     - {action.tool}({action.args[:50]}...)\n"

                            # Show errors for failed trajectories
                            elif traj.errors_encountered:
                                guidance += f"   Errors encountered: {', '.join(traj.errors_encountered[:2])}\n"

                            guidance += "\n"

                        guidance += "Use this experience to avoid past mistakes and follow proven approaches.\n"
                        guidance += "=====================\n"

                        context_parts.append(guidance)
                        
                        # Debug output
                        if config.DEBUG_MODE:
                            print(Color.system(f"[PROMPT] ✅ Procedural: {len(similar_trajs)} similar trajectories"))
                            for score, traj in similar_trajs:
                                print(Color.system(f"[PROMPT]     - {traj.task_description[:40]}... (score: {score:.2f})"))

                        # Increment usage count for retrieved trajectories
                        for score, traj in similar_trajs:
                            procedural_memory.increment_usage(traj.id)

                except Exception as e:
                    # Fail silently if procedural retrieval fails
                    pass

        # Add graph knowledge (semantic search based on recent conversation)
        if graph_lite is not None and messages:
            # Get recent user messages for context
            user_messages = [m for m in messages if m.get("role") == "user"]
            if user_messages:
                # Use last user message as search query
                recent_topic = user_messages[-1].get("content", "")[:200]

                try:
                    # Graph RAG: Search with graph traversal for richer context
                    relevant_results = graph_lite.graph_rag_search(
                        recent_topic,
                        limit=config.GRAPH_SEARCH_LIMIT,
                        hop=1  # Follow 1 hop of edges
                    )

                    if relevant_results:
                        graph_context = "=== RELEVANT KNOWLEDGE ===\n\n"
                        included_nodes = []
                        for score, node in relevant_results:
                            # Only include nodes with reasonable similarity
                            if score > config.GRAPH_SIMILARITY_THRESHOLD:
                                # Try multiple fields: content, description, name
                                node_desc = node.data.get("content") or node.data.get("description") or node.data.get("name", "")
                                if node_desc:
                                    # Truncate long content
                                    if len(node_desc) > 200:
                                        node_desc = node_desc[:200] + "..."
                                    graph_context += f"- {node.type}: {node_desc}\n"
                                    included_nodes.append((score, node))

                        graph_context += "\n=====================\n"
                        context_parts.append(graph_context)
                        
                        # Debug output with type breakdown and content preview
                        if config.DEBUG_MODE and included_nodes:
                            type_counts = {}
                            for score, node in included_nodes:
                                type_counts[node.type] = type_counts.get(node.type, 0) + 1
                            type_summary = ", ".join([f"{t}:{c}" for t, c in type_counts.items()])
                            
                            # Get total graph stats
                            total_nodes = len(graph_lite.nodes) if hasattr(graph_lite, 'nodes') else 0
                            total_edges = len(graph_lite.edges) if hasattr(graph_lite, 'edges') else 0
                            print(Color.system(f"[PROMPT] ✅ Graph: {len(included_nodes)}/{total_nodes} nodes matched ({type_summary}), {total_edges} edges"))
                            
                            # Show all matched nodes with details
                            for i, (score, node) in enumerate(included_nodes, 1):
                                content = node.data.get('content') or node.data.get('description') or node.data.get('name', '')
                                content_preview = content[:80].replace('\n', ' ') + "..." if len(content) > 80 else content.replace('\n', ' ')
                                
                                # Get usage stats
                                helpful = getattr(node, 'helpful_count', 0)
                                harmful = getattr(node, 'harmful_count', 0)
                                usage = getattr(node, 'usage_count', 0)
                                stats = f"👍{helpful} 👎{harmful} 📊{usage}" if any([helpful, harmful, usage]) else ""
                                
                                print(Color.system(f"[PROMPT]     {i}. [{node.type}] \"{content_preview}\""))
                                if stats:
                                    print(Color.system(f"[PROMPT]        score:{score:.2f} {stats}"))

                except Exception as e:
                    # Fail silently if graph search fails
                    pass

        # Smart RAG: Auto-inject relevant code/spec context
        if config.ENABLE_SMART_RAG and messages:
            user_messages = [m for m in messages if m.get("role") == "user"]
            if user_messages:
                recent_query = user_messages[-1].get("content", "")[:200]
                
                try:
                    from core.smart_rag import SmartRAGDecision
                    from core.rag_db import get_rag_db
                    
                    # Create Smart RAG decision maker
                    smart_rag = SmartRAGDecision(
                        high_threshold=config.SMART_RAG_HIGH_THRESHOLD,
                        low_threshold=config.SMART_RAG_LOW_THRESHOLD,
                        top_k=config.SMART_RAG_TOP_K,
                        debug=config.DEBUG_MODE
                    )
                    
                    # Define RAG search function (Hybrid if available)
                    def rag_search_func(query, limit=3):
                        if hybrid_rag:
                            # Use HybridRAG (Embedding + BM25 + Graph)
                            # This will also trigger the detailed debug visualization
                            return hybrid_rag.search(query, limit=limit)
                        else:
                            # Fallback to simple Embedding search
                            db = get_rag_db()
                            return db.search(query, limit=limit)
                    
                    # LLM judge function (only if enabled)
                    llm_judge_func = call_llm_raw if config.SMART_RAG_LLM_JUDGE else None
                    
                    # Decide and get results
                    should_use, rag_results = smart_rag.decide(
                        recent_query,
                        rag_search_func,
                        llm_judge_func
                    )
                    
                    # Always show Smart RAG decision (for visibility)
                    # Always show Smart RAG decision (for visibility)
                    if rag_results:
                        top_score = rag_results[0].score if hybrid_rag else (rag_results[0][0] if rag_results else 0)
                        decision = "✅ Injected" if should_use else "❌ Ignored"
                        
                        # Note: Detailed debug visualization is handled inside hybrid_rag.search() if enabled
                        
                        # Simple output (always visible)
                        print(Color.system(f"[SmartRAG] Query: \"{recent_query}\""))
                        print(Color.system(f"[SmartRAG] Top Score: {top_score:.3f} | Threshold: {config.SMART_RAG_LOW_THRESHOLD}-{config.SMART_RAG_HIGH_THRESHOLD} | {decision}"))
                        
                        if should_use:
                            for i, item in enumerate(rag_results[:3], 1):
                                if hybrid_rag:
                                    # HybridRAG returns SearchResult objects
                                    score = item.score
                                    source = os.path.basename(item.source_file)
                                    category = getattr(item, 'chunk_type', 'unknown').upper()
                                else:
                                    # Basic RAG returns (score, chunk) tuples
                                    score, chunk = item
                                    source = os.path.basename(getattr(chunk, 'source_file', 'unknown'))
                                    category = getattr(chunk, 'category', 'unknown').upper()
                                    
                                print(Color.system(f"[SmartRAG]   {i}. [{category}] {source} (score: {score:.2f})"))
                        print("")
                    
                    if should_use and rag_results:
                        rag_context = smart_rag.format_context(rag_results, max_chars=2000)
                        context_parts.append(rag_context)
                        
                        # DEBUG: Print the injected context to verify prompt inclusion (Always visible now)
                        print(Color.system(f"\n[SmartRAG] Injected Context Preview ({len(rag_context)} chars):"))
                        print(Color.system("-" * 40))
                        # User requested full context visibility
                        print(Color.system(rag_context.strip()))
                        print(Color.system("-" * 40 + "\n"))
                
                except ImportError:
                    # RAG module not available, skip silently
                    pass
                except Exception as e:
                    if config.DEBUG_MODE:
                        print(Color.warning(f"[SmartRAG] Error: {e}"))

        # Add active skills (domain-specific expertise)
        if config.ENABLE_SKILL_SYSTEM and messages:
            try:
                skill_prompts = load_active_skills(messages, allowed_tools)
                if skill_prompts:
                    skills_section = "=== ACTIVE SKILLS ===\n\n"
                    skills_section += "The following domain expertise is active:\n\n"
                    skills_section += "\n\n".join(skill_prompts)
                    skills_section += "\n\n====================="
                    context_parts.append(skills_section)
            except Exception as e:
                if config.DEBUG_MODE:
                    print(Color.warning(f"[PROMPT] ⚠️ Error injecting skills: {e}"))

        # Add RAG tool guidance for Verilog and Spec analysis
        rag_guidance = """=== RAG CODE & SPEC SEARCH ===

Use RAG tools for semantic search (much faster than grep):
- rag_search(query, categories, limit): Semantic search
  Categories: "verilog", "testbench", "spec", "all" (default: "all")
  Example: rag_search("axi_awready signal", categories="verilog", limit=5)
  Example: rag_search("TDISP state machine", categories="spec", limit=5)
  Example: rag_search("CONFIG_LOCKED transition", categories="all", limit=5)
- rag_index(path, fine_grained): Index files (run once)
- rag_status(): Check indexed files count
- read_lines(file, start, end): Read specific lines after finding location

Workflow: rag_search() → find location → read_lines() → analyze
==============================
"""
        context_parts.append(rag_guidance)

        # Combine all context parts
        if context_parts:
            base_prompt = base_prompt + "\n\n" + "\n\n".join(context_parts)
            
            # Debug: Show prompt build summary
            if config.DEBUG_MODE and messages:
                total_chars = len(base_prompt)
                estimated_tokens = total_chars // 4
                print(Color.system(f"[PROMPT] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"))
                print(Color.system(f"[PROMPT] Build complete: {len(context_parts)} sections, ~{estimated_tokens:,} tokens"))

    # Claude Flow: Inject current plan status into the prompt (if present).
    plan_state = _get_plan_state()
    if plan_state.get("exists"):
        approved = bool(plan_state.get("approved"))
        plan_task = plan_state.get("task") or ""
        steps = plan_state.get("steps") or []
        next_step = plan_state.get("next_step")

        status_str = "APPROVED" if approved else "PENDING APPROVAL"
        plan_lines = [f"=== CURRENT PLAN ({status_str}) ==="]
        if plan_task:
            plan_lines.append(f"Task: {plan_task}")
        plan_lines.append(f"Plan file: {_PLAN_FILE}")

        if steps:
            if next_step:
                try:
                    plan_lines.append(f"Next step: {next_step[0]}. {next_step[1]}")
                except Exception:
                    pass
            plan_lines.append("Steps:")
            for step_number, step_text, done in steps[:20]:
                suffix = " ✅" if done else ""
                plan_lines.append(f"{step_number}. {step_text}{suffix}")

        if (not approved) and config.CLAUDE_FLOW_REQUIRE_APPROVAL:
            plan_lines.append("Rule: Do NOT run write/replace/run_command until the user approves the plan.")
            plan_lines.append("Ask the user to edit current_plan.md and set: STATUS: APPROVED")
        else:
            plan_lines.append("Rule: Follow the plan and execute steps in order.")
            plan_lines.append("When a step is complete: mark_step_done(step_number=N)")

        plan_lines.append("===========================")
        base_prompt = base_prompt + "\n\n" + "\n".join(plan_lines)

    return base_prompt

def save_procedural_trajectory(task_description, actions_taken, outcome, iterations):
    """
    Save completed task as a trajectory in procedural memory.

    Args:
        task_description: Description of the task
        actions_taken: List of Action objects
        outcome: "success" or "failure"
        iterations: Number of iterations taken
    """
    if not procedural_memory:
        return

    try:
        trajectory_id = procedural_memory.build(
            task_description=task_description,
            actions=actions_taken,
            outcome=outcome,
            iterations=iterations
        )

        # Save to disk
        procedural_memory.save()

        print(Color.success(f"[Procedural Memory] Saved trajectory: {trajectory_id}"))
        print(Color.info(f"  Task type: {procedural_memory.trajectories[trajectory_id].task_type}"))
        print(Color.info(f"  Outcome: {outcome}, Iterations: {iterations}"))

    except Exception as e:
        print(Color.error(f"[Procedural Memory] Failed to save trajectory: {e}"))

def on_conversation_end(messages):
    """
    Extract and save knowledge from conversation to graph.
    Now uses A-MEM auto-linking for intelligent connections.
    
    Args:
        messages: Full message history
    """
    if not (config.ENABLE_GRAPH and config.GRAPH_AUTO_EXTRACT and graph_lite):
        return

    print(Color.system("\n[Graph] Extracting knowledge from conversation..."))

    try:
        # Get recent messages for context (skip system message)
        recent_messages = [m for m in messages if m.get("role") != "system"][-config.GRAPH_EXTRACTION_MESSAGES:]

        if not recent_messages:
            return

        # Build conversation summary
        conversation_text = "\n".join([
            f"{m.get('role')}: {m.get('content', '')[:500]}"
            for m in recent_messages
        ])

        # A-MEM: Create free-form notes with auto-linking
        # Instead of extracting entities/relations separately, we create rich notes
        # that automatically link to relevant existing knowledge
        
        print(Color.system("[Graph] Creating memory notes with auto-linking..."))
        
        # Extract key insights/learnings from conversation
        prompt = f"""Extract 2-3 key learnings or insights from this conversation.
        
Conversation:
{conversation_text}

For each learning, provide a concise statement (1-2 sentences).
Return as JSON array: [{{"learning": "..."}}]

Learnings (JSON only):"""

        try:
            response = call_llm_raw(prompt)
            
            # Parse JSON
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                learnings = json.loads(json_str)
                
                # Add each learning as a note with auto-linking (PARALLELIZED)
                notes_added = 0
                
                # Check config or define locally
                max_workers = 3 
                
                def _add_learning_task(item):
                    learning = item.get('learning', '')
                    if learning:
                        try:
                            # A-MEM auto-linking!
                            return graph_lite.add_note_with_auto_linking(
                                content=learning,
                                context={
                                    'source': 'conversation',
                                    'timestamp': datetime.now().isoformat()
                                }
                            )
                        except Exception as e:
                            print(Color.warning(f"[Graph] Failed to add note: {e}"))
                    return None

                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = [executor.submit(_add_learning_task, item) for item in learnings]
                    for future in futures:
                        try:
                            if future.result():
                                notes_added += 1
                        except Exception:
                            pass
                
                print(Color.success(f"[Graph] Added {notes_added} notes with auto-linking"))
                
                # Save graph
                graph_lite.save()
                
                # Display stats
                stats = graph_lite.get_stats()
                print(Color.info(f"[Graph] Total: {stats['total_nodes']} nodes, {stats['total_edges']} edges"))
                
        except Exception as e:
            print(Color.error(f"[Graph] Failed to extract learnings: {e}"))
            return

    except Exception as e:
        print(Color.error(f"[Graph] Knowledge extraction failed: {e}"))


def show_context_usage(messages, use_actual=True):
    """
    Displays current context usage information.

    Args:
        messages: list of message dicts
        use_actual: if True, use actual tokens from API (hybrid mode)
    """
    if use_actual:
        current_tokens = get_actual_tokens(messages)
        source = "actual" if llm_client.last_input_tokens > 0 else "estimated"
    else:
        current_tokens = sum(estimate_message_tokens(m) for m in messages)
        source = "estimated"

    limit_tokens = config.MAX_CONTEXT_CHARS // 4
    threshold_tokens = int(limit_tokens * config.COMPRESSION_THRESHOLD)

    usage_pct = int((current_tokens / limit_tokens) * 100) if limit_tokens > 0 else 0

    # Color coding based on usage
    if usage_pct >= 100:
        color = Color.error
        status = "OVER LIMIT"
    elif usage_pct >= 80:
        color = Color.warning
        status = "HIGH"
    elif usage_pct >= 50:
        color = Color.info
        status = "MEDIUM"
    else:
        color = Color.success
        status = "OK"

    bar_length = 20
    filled = int(bar_length * usage_pct / 100)
    bar = '█' * filled + '░' * (bar_length - filled)

    # Show source in debug mode
    if config.DEBUG_MODE:
        print(color(f"[Context: {current_tokens:,}/{limit_tokens:,} tokens ({usage_pct}%) {bar} {status}] ({source})"))
    else:
        print(color(f"[Context: {current_tokens:,}/{limit_tokens:,} tokens ({usage_pct}%) {bar} {status}]"))

    # Auto-warning when context exceeds 85%
    if usage_pct >= 85:
        print(Color.warning("\n⚠️  Context is 85%+ full. Consider running '/compact' soon."))
        print(Color.info("   Tip: Use '/compact --dry-run' to preview compression.\n"))


def compress_history(messages, force=False, instruction=None, keep_recent=None, dry_run=False):
    """
    Compresses history if it exceeds the token limit.
    Strategy: Keep System messages + Last N messages. Summarize the middle.
    Uses last_input_tokens from API (no additional API call).
    Supports both single and chunked compression modes.
    Args:
        messages: Conversation history
        force: If True, bypass token threshold check
        instruction: Optional custom instruction for summarization
        keep_recent: Number of recent messages to keep (None = use config default)
        dry_run: If True, return preview without modifying state
    """
    if not config.ENABLE_COMPRESSION and not force:
        return messages

    limit_tokens = config.MAX_CONTEXT_CHARS // 4
    threshold_tokens = int(limit_tokens * config.COMPRESSION_THRESHOLD)

    # Use last_input_tokens from previous API call (no additional API call)
    current_tokens = get_actual_tokens(messages)
    token_source = "actual" if llm_client.last_input_tokens > 0 else "estimated"

    if not force and current_tokens < threshold_tokens:
        return messages

    print(Color.warning(f"\n[System] {'Manual' if force else 'Auto'} Compression triggered. Context: {current_tokens:,} {token_source} tokens."))

    if not messages:
        return messages

    # Traditional compression: Simple time-based approach
    # Structure: [system] + [summary of old] + [recent N]
    print(Color.info("[System] Using traditional compression..."))

    # Pre-compact hook
    pre_hook_path = Path.home() / ".brian_coder" / "hooks" / "pre_compact.sh"
    if pre_hook_path.exists():
        print(Color.info("[Hook] Running pre_compact.sh..."))
        try:
            subprocess.run([str(pre_hook_path)], timeout=10, check=False, shell=False)
        except subprocess.TimeoutExpired:
            print(Color.warning("[Hook] pre_compact.sh timed out (10s)"))
        except Exception as e:
            print(Color.warning(f"[Hook] pre_compact.sh failed: {e}"))

    # Separate system messages from regular messages (like Strix)
    system_msgs = [m for m in messages if m.get("role") == "system"]
    regular_msgs = [m for m in messages if m.get("role") != "system"]

    # Extract !important messages (preserve them)
    important_msgs = []
    other_msgs = []
    for msg in regular_msgs:
        content = str(msg.get("content", ""))
        if "!important" in content.lower():
            # Remove tag for cleaner history
            msg_copy = msg.copy()
            msg_copy["content"] = content.replace("!important", "").replace("!IMPORTANT", "").replace("!Important", "").strip()
            important_msgs.append(msg_copy)
        else:
            other_msgs.append(msg)

    if important_msgs:
        print(Color.info(f"[System] Preserving {len(important_msgs)} !important messages"))

    # Check if history is too short
    if keep_recent is None:
        keep_recent = config.COMPRESSION_KEEP_RECENT
    if len(other_msgs) <= keep_recent:
        print(Color.info(f"[System] History too short to compress ({len(other_msgs)} <= {keep_recent} recent)."))
        return messages

    # Keep last N messages (from non-important messages)
    recent_msgs = other_msgs[-keep_recent:]
    old_msgs = other_msgs[:-keep_recent]

    if not old_msgs:
        return messages

    # Choose compression mode
    mode = config.COMPRESSION_MODE.lower()

    if mode == "chunked":
        # Chunked compression (like Strix)
        print(Color.info(f"[System] Using chunked compression (chunk_size={config.COMPRESSION_CHUNK_SIZE})..."))
        compressed = _compress_chunked(old_msgs, instruction=instruction)
    else:
        # Single compression (default, faster and cheaper)
        print(Color.info("[System] Using single compression..."))
        compressed = [_compress_single(old_msgs, instruction=instruction)]

    # Construct new history: system + important + compressed + recent
    new_history = system_msgs + important_msgs + compressed + recent_msgs

    # Calculate detailed statistics
    new_tokens = sum(estimate_message_tokens(m) for m in new_history)
    reduction_pct = int((1 - new_tokens / current_tokens) * 100) if current_tokens > 0 else 0

    old_msg_count = len(messages)
    new_msg_count = len(new_history)
    msg_reduction_pct = int((1 - new_msg_count / old_msg_count) * 100) if old_msg_count > 0 else 0

    # Dry-run mode: Preview only, don't modify state
    if dry_run:
        print(Color.info("\n" + "=" * 60))
        print(Color.info("🔍 Compression Preview (Dry Run)"))
        print(Color.info("=" * 60))
        print(Color.info(f"Current:  {old_msg_count} messages, {current_tokens:,} tokens"))
        print(Color.info(f"After:    {new_msg_count} messages, {new_tokens:,} tokens"))
        print(Color.info(f"Reduction: {msg_reduction_pct}% messages, {reduction_pct}% tokens"))
        print(Color.info(f"Kept recent: {keep_recent} messages"))
        print(Color.info(f"Summarizing: {len(old_msgs)} messages → 1 summary"))
        print(Color.info("=" * 60))
        print(Color.warning("\nℹ️  Run '/compact' without --dry-run to apply.\n"))
        return messages  # Return original (no changes)

    # Normal mode: Apply compression
    # Invalidate last_input_tokens because history structure has changed significantly
    llm_client.last_input_tokens = 0

    # Clean up _tokens metadata from all messages in new_history
    # This forces context_tracker to recalculate using estimation
    for msg in new_history:
        if "_tokens" in msg:
            del msg["_tokens"]

    # Post-compact hook (with stats as environment variables)
    post_hook_path = Path.home() / ".brian_coder" / "hooks" / "post_compact.sh"
    if post_hook_path.exists():
        print(Color.info("[Hook] Running post_compact.sh..."))
        try:
            env = os.environ.copy()
            env["BRIAN_OLD_MSGS"] = str(old_msg_count)
            env["BRIAN_NEW_MSGS"] = str(new_msg_count)
            env["BRIAN_OLD_TOKENS"] = str(current_tokens)
            env["BRIAN_NEW_TOKENS"] = str(new_tokens)
            env["BRIAN_REDUCTION_PCT"] = str(reduction_pct)

            subprocess.run([str(post_hook_path)], env=env, timeout=10, check=False, shell=False)
        except subprocess.TimeoutExpired:
            print(Color.warning("[Hook] post_compact.sh timed out (10s)"))
        except Exception as e:
            print(Color.warning(f"[Hook] post_compact.sh failed: {e}"))

    # Print detailed statistics
    print(Color.success("\n" + "=" * 60))
    print(Color.success("✅ Compression Complete"))
    print(Color.success("=" * 60))
    print(Color.success(f"Messages: {old_msg_count} → {new_msg_count} ({msg_reduction_pct}% reduction)"))
    print(Color.success(f"Tokens:   {current_tokens:,} ({token_source}) → {new_tokens:,} (estimated) = {reduction_pct}% reduction"))
    print(Color.success(f"Kept recent: {keep_recent} messages"))
    print(Color.success(f"Summarized: {len(old_msgs)} → 1 summary"))
    print(Color.success("=" * 60 + "\n"))

    return new_history


def _compress_single(messages, instruction=None):
    """Single-pass compression: summarize all messages at once"""
    # Use structured summary prompt for better quality
    summary_prompt = instruction if instruction else STRUCTURED_SUMMARY_PROMPT

    conversation_text = ""
    for m in messages:
        role = m.get("role", "unknown")
        content = str(m.get("content", ""))  # Read full message (no truncation)
        conversation_text += f"{role}: {content}\n"

    summary_request = [
        {"role": "system", "content": "You are a helpful assistant that summarizes conversation history for an AI agent."},
        {"role": "user", "content": f"{summary_prompt}\n\n{conversation_text}"}
    ]

    print(Color.info("[System] Generating summary..."), end="", flush=True)
    summary_content = ""
    try:
        for chunk in chat_completion_stream(summary_request):
            summary_content += chunk
        print(Color.success(" Done."))

        return {
            "role": "system",
            "content": f"[Previous Conversation Summary ({len(messages)} messages)]: {summary_content}"
        }
    except Exception as e:
        print(Color.error(f"\n[System] Failed to generate summary: {e}"))
        return messages[0] if messages else {"role": "system", "content": "[Compression failed]"}


def _compress_chunked(messages, instruction=None):
    """Chunked compression: summarize in chunks (like Strix)"""
    chunk_size = config.COMPRESSION_CHUNK_SIZE
    compressed = []

    total_chunks = (len(messages) + chunk_size - 1) // chunk_size
    print(Color.info(f"[System] Compressing {len(messages)} messages in {total_chunks} chunks..."))

    for i in range(0, len(messages), chunk_size):
        chunk = messages[i:i + chunk_size]
        chunk_num = i // chunk_size + 1

        print(Color.info(f"[System] Chunk {chunk_num}/{total_chunks}..."), end="", flush=True)

        default_prompt = "Summarize the following conversation segment concisely. Focus on completed tasks, key decisions, and current state."
        summary_prompt = instruction if instruction else default_prompt

        conversation_text = ""
        for m in chunk:
            role = m.get("role", "unknown")
            content = str(m.get("content", ""))[:1000]
            conversation_text += f"{role}: {content}\n"

        summary_request = [
            {"role": "system", "content": "You are a helpful assistant that summarizes conversation history for an AI agent."},
            {"role": "user", "content": f"{summary_prompt}\n\n{conversation_text}"}
        ]

        try:
            summary_content = ""
            for chunk_data in chat_completion_stream(summary_request):
                summary_content += chunk_data

            compressed.append({
                "role": "system",
                "content": f"[Summary chunk {chunk_num}/{total_chunks} ({len(chunk)} messages)]: {summary_content}"
            })
            print(Color.success(" Done."))
        except Exception as e:
            print(Color.error(f" Failed: {e}"))
            # Keep original first message as fallback
            if chunk:
                compressed.append(chunk[0])

    return compressed

def process_observation(observation, messages):
    """
    Processes observation before adding to message history.
    Handles large file truncation and context management.
    Returns updated messages list.
    """
    # Check if adding observation would exceed context limit
    limit_tokens = config.MAX_CONTEXT_CHARS // 4
    threshold_tokens = int(limit_tokens * config.COMPRESSION_THRESHOLD)
    
    # Step 1: First check if observation itself is too large
    observation_msg = {"role": "user", "content": f"Observation: {observation}"}
    observation_tokens = estimate_message_tokens(observation_msg)

    if observation_tokens > limit_tokens * 0.3:  # Observation > 30% of limit (stricter)
        original_size = len(observation)
        lines = observation.split('\n')
        total_lines = len(lines)

        # Show first N lines as preview + guidance
        PREVIEW_LINES = config.LARGE_FILE_PREVIEW_LINES
        preview_lines = lines[:PREVIEW_LINES]
        preview = '\n'.join(preview_lines)
        
        # Safety Truncation: Ensure preview itself isn't too huge (e.g. if lines are very long)
        # Limit preview to 50% of MAX_OBSERVATION_CHARS
        MAX_PREVIEW_CHARS = config.MAX_OBSERVATION_CHARS // 2
        if len(preview) > MAX_PREVIEW_CHARS:
            preview = preview[:MAX_PREVIEW_CHARS] + f"\n... [Preview truncated at {MAX_PREVIEW_CHARS} chars] ..."

        # Calculate max readable lines (based on context limit)
        MAX_READABLE_LINES = (config.MAX_OBSERVATION_CHARS // 80)  # Assume ~80 chars per line

        observation = f"""[File Preview - Too large to display completely]

Showing first {PREVIEW_LINES} lines (Total: {total_lines:,} lines, {original_size:,} characters)

--- BEGIN PREVIEW ---
{preview}
--- END PREVIEW ---

💡 File is too large for full display. You can read up to ~{MAX_READABLE_LINES} lines at a time.

To read specific sections:
1. Use read_lines(path, start_line, end_line)
   Examples:
   - read_lines(path, start_line=100, end_line=200)           # Lines 100-200
   - read_lines(path, start_line={max(1, total_lines-100)}, end_line={total_lines})  # Last 100 lines

2. Use grep_file(pattern, path) to search for patterns
   Example:
   - grep_file(pattern="module\\s+\\w+", path)   # Find modules
   - grep_file(pattern="always.*@", path)        # Find always blocks

3. Ask the user which part they want to see
"""
        observation_msg = {"role": "user", "content": f"Observation: {observation}"}
        observation_tokens = estimate_message_tokens(observation_msg)
        print(Color.warning(f"[System] ⚠️  Large observation truncated: {original_size:,} chars → {config.MAX_OBSERVATION_CHARS:,} chars ({total_lines:,} lines total)"))

    # Step 2: Check total context size
    current_tokens = sum(estimate_message_tokens(m) for m in messages)
    total_tokens = current_tokens + observation_tokens

    if total_tokens > threshold_tokens and config.ENABLE_COMPRESSION:
        print(Color.warning(f"\n[System] ⚠️  Adding observation would exceed threshold ({total_tokens:,} > {threshold_tokens:,} tokens)"))
        print(Color.info("[System] Compressing history before adding observation..."))
        messages = compress_history(messages)

        # Re-calculate after compression
        current_tokens = sum(estimate_message_tokens(m) for m in messages)
        total_tokens = current_tokens + observation_tokens

        # If still exceeding after compression, force truncate observation
        if total_tokens > threshold_tokens:
            print(Color.warning(f"[System] ⚠️  Still exceeding threshold after compression. Force truncating observation..."))
            original_size = len(observation)
            # Limit observation to 20% of limit to be safe
            max_safe_tokens = int(limit_tokens * 0.2)
            max_safe_chars = max_safe_tokens * 4

            if len(observation) > max_safe_chars:
                observation = observation[:max_safe_chars] + f"\n\n[Observation truncated: {original_size:,} → {max_safe_chars:,} chars to prevent context overflow]"
                observation_msg = {"role": "user", "content": f"Observation: {observation}"}
                observation_tokens = estimate_message_tokens(observation_msg)
                print(Color.info(f"[System] Observation truncated to {observation_tokens:,} tokens"))

    messages.append(observation_msg)
    return messages


# --- 6. ReAct Agent Logic ---

_PARALLEL_ELIGIBLE_TOOLS = {
    # Safe, read-only tools (no filesystem writes, no external side effects).
    # 기본 읽기 도구
    "read_file",
    "read_lines",
    "grep_file",
    "list_dir",
    "find_files",
    # Git 도구
    "git_status",
    "git_diff",
    # RAG 도구 (read-only)
    "rag_search",
    "rag_status",
    # Verilog 분석 도구 (read-only)
    "analyze_verilog_module",
    "find_signal_usage",
    "find_module_definition",
    "extract_module_hierarchy",
    "find_potential_issues",
    "analyze_timing_paths",
    # Meta 도구
    "spawn_explore",  # 여러 explore agent 병렬 실행 가능
}


def execute_actions_parallel(actions, tracker):
    """
    Execute Actions with intelligent parallelism using ActionDependencyAnalyzer.

    Claude Code Style Strategy:
    - Analyze action dependencies using ActionDependencyAnalyzer
    - Read-only tools → parallel execution
    - Write tools → sequential barrier
    - File conflict detection → automatic warning

    Returns:
        List of tuples: (index, tool_name, args_str, observation)
    """
    if not actions:
        return []

    results = []

    # Record tool usage for progress tracking
    for tool_name, _ in actions:
        tracker.record_tool(tool_name)

    # Use enhanced dependency analysis if enabled
    # For now, always use the new analyzer (config option will be added later)
    use_enhanced = getattr(config, 'ENABLE_ENHANCED_PARALLEL', True)

    if use_enhanced:
        # === Enhanced Mode: ActionDependencyAnalyzer ===
        analyzer = ActionDependencyAnalyzer()
        batches = analyzer.analyze(actions)

        # File conflict detection
        detector = FileConflictDetector()
        all_indexed_actions = []
        for batch in batches:
            all_indexed_actions.extend(batch.actions)

        warnings = detector.check_conflicts(all_indexed_actions, analyzer)
        for warning in warnings:
            print(Color.warning(warning))

        # Execute each batch
        for batch in batches:
            if config.DEBUG_MODE:
                print(Color.system(f"  [Batch] {batch.reason}: {len(batch.actions)} action(s), parallel={batch.parallel}"))

            if batch.parallel and len(batch.actions) > 1 and config.ENABLE_REACT_PARALLEL:
                # Parallel execution
                print(Color.info(f"  ⚡ Parallel batch: {len(batch.actions)} action(s)"))
                batch_results = _execute_batch_parallel(batch.actions)
                results.extend(batch_results)
            else:
                # Sequential execution
                for idx, tool_name, args_str in batch.actions:
                    observation = execute_tool(tool_name, args_str)
                    results.append((idx, tool_name, args_str, observation))

    else:
        # === Legacy Mode: Simple allowlist-based ===
        parallel_batch = []

        def flush_parallel_batch():
            nonlocal parallel_batch

            if not parallel_batch:
                return

            if len(parallel_batch) == 1 or not config.ENABLE_REACT_PARALLEL:
                idx, tool_name, args_str = parallel_batch[0]
                observation = execute_tool(tool_name, args_str)
                results.append((idx, tool_name, args_str, observation))
                parallel_batch = []
                return

            print(Color.info(f"  ⚡ Parallel batch: {len(parallel_batch)} action(s)"))
            batch_results = _execute_batch_parallel(parallel_batch)
            results.extend(batch_results)
            parallel_batch = []

        for idx, (tool_name, args_str) in enumerate(actions):
            if tool_name in _PARALLEL_ELIGIBLE_TOOLS:
                parallel_batch.append((idx, tool_name, args_str))
                continue

            flush_parallel_batch()
            observation = execute_tool(tool_name, args_str)
            results.append((idx, tool_name, args_str, observation))

        flush_parallel_batch()

    # Sort by original index
    results.sort(key=lambda x: x[0])
    return results


def _execute_batch_parallel(batch_actions):
    """
    Helper function: Execute a batch of actions in parallel using ThreadPoolExecutor.

    Args:
        batch_actions: List of (idx, tool_name, args_str) tuples

    Returns:
        List of (idx, tool_name, args_str, observation) tuples
    """
    results = []
    max_workers = min(len(batch_actions), max(1, config.REACT_MAX_WORKERS))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(execute_tool, tool_name, args_str): (idx, tool_name, args_str)
            for idx, tool_name, args_str in batch_actions
        }

        done, not_done = wait(future_map.keys(), timeout=max(1, config.REACT_ACTION_TIMEOUT))

        for future in done:
            idx, tool_name, args_str = future_map[future]
            try:
                observation = future.result()
            except Exception as e:
                observation = f"Error: Exception in parallel execution: {e}\n{traceback.format_exc()}"
            results.append((idx, tool_name, args_str, observation))

        for future in not_done:
            idx, tool_name, args_str = future_map[future]
            try:
                future.cancel()
            except Exception:
                pass
            results.append((idx, tool_name, args_str, f"Error: Timeout after {config.REACT_ACTION_TIMEOUT}s"))

    return results


def run_react_agent(messages, tracker, task_description, mode='interactive', allow_claude_flow=True, preface_enabled=True):
    """
    Executes the ReAct agent loop for a given task.
    
    Args:
        messages: List of message dicts (context)
        tracker: IterationTracker instance
        task_description: Description of the task (for procedural memory)
        mode: 'interactive' or 'oneshot'
        
    Returns:
        Updated messages list
    """
    consecutive_errors = 0
    last_error_observation = None
    MAX_CONSECUTIVE_ERRORS = 3

    # Initialize action tracking for procedural memory
    actions_taken = []

    # ACE Credit Assignment: Track referenced node IDs from Deep Think
    referenced_node_ids = []

    # Todo Tracking System (Phase 2 - Claude Code Style)
    todo_tracker = TodoTracker() if config.ENABLE_TODO_TRACKING else None

    # ============================================================
    # Sub-Agent System (Claude Code Style) - Replaces Deep Think
    # ============================================================
    if allow_claude_flow:
        handled_messages = _maybe_handle_claude_flow(messages, task_description, mode=mode)
        if handled_messages is not None:
            return handled_messages

    if preface_enabled and config.ENABLE_SUB_AGENTS and orchestrator:
        print(Color.system("\n[Sub-Agent] Orchestrator analyzing task..."))

        try:
            # Build context from recent messages
            context = {}
            context_parts = []
            for msg in messages[-5:]:
                if msg.get("role") != "system":
                    content = str(msg.get("content", ""))[:200]
                    context_parts.append(f"{msg['role']}: {content}")

            # Add current directory info
            try:
                files = os.listdir(".")[:20]
                context_parts.append(f"Current directory: {', '.join(files)}")
            except:
                pass

            context["recent_messages"] = "\n".join(context_parts)

            # Run Orchestrator
            result = orchestrator.run(task=task_description, context=context)

            # Display result summary
            print(Color.success(f"[Sub-Agent] Completed in {result.execution_time_ms}ms"))
            print(Color.info(f"  Agents: {result.execution_plan.agents_needed}"))
            print(Color.info(f"  Mode: {result.execution_plan.execution_mode}"))

            # Inject orchestrator result into messages
            if result.final_output:
                guidance = f"""=== SUB-AGENT ANALYSIS ===
{result.final_output[:2000]}
===========================

Use the above analysis to guide your response. Continue with the ReAct loop if more actions are needed."""
                messages.append({"role": "system", "content": guidance})
                print(Color.info(f"  Result injected into context"))

            print()

        except Exception as e:
            print(Color.warning(f"[Sub-Agent] Orchestrator failed: {e}"))
            print(Color.info("[Sub-Agent] Continuing with standard ReAct..."))
            print()

    # ============================================================
    # Deep Think Integration (Hypothesis Branching) - Legacy
    # ============================================================
    elif preface_enabled and config.ENABLE_DEEP_THINK and not config.ENABLE_SUB_AGENTS:
        print(Color.system("\n[Deep Think] Analyzing task and generating strategies..."))

        try:
            # Build context from recent messages
            context_parts = []
            for msg in messages[-5:]:
                if msg.get("role") != "system":
                    content = str(msg.get("content", ""))[:200]
                    context_parts.append(f"{msg['role']}: {content}")

            # Add current directory info
            try:
                files = os.listdir(".")[:20]
                context_parts.append(f"Current directory: {', '.join(files)}")
            except:
                pass

            context = "\n".join(context_parts)

            # Initialize Deep Think engine
            engine = DeepThinkEngine(
                procedural_memory=procedural_memory,
                graph_lite=graph_lite,
                llm_call_func=call_llm_raw,
                execute_tool_func=execute_tool
            )

            # Run Deep Think pipeline
            deep_think_result = engine.think(
                task=task_description,
                context=context
            )

            # Display result
            print(format_deep_think_output(deep_think_result, verbose=True))

            # Inject selected strategy into messages
            strategy_guidance = engine.format_strategy_guidance(deep_think_result)
            messages.append({"role": "system", "content": strategy_guidance})

            print(Color.success(f"[Deep Think] Selected: {deep_think_result.selected_hypothesis.strategy_name}"))
            print(Color.info(f"  First action: {deep_think_result.selected_hypothesis.first_action}"))

            # ACE Credit Assignment: Extract referenced node IDs
            referenced_node_ids = deep_think_result.referenced_node_ids
            if referenced_node_ids:
                print(Color.info(f"  [ACE] Tracking {len(referenced_node_ids)} knowledge nodes for credit"))
            print()

        except Exception as e:
            print(Color.warning(f"[Deep Think] Analysis failed: {e}"))
            print(Color.info("[Deep Think] Continuing with standard approach..."))
            print()

    while True:
        # Check iteration limit with progressive warning
        warning_action = show_iteration_warning(tracker, mode=mode)
        if warning_action == 'stop':
            break
        elif warning_action == 'extend':
            tracker.extend(20)

        # Context Management: Compress if needed
        messages = compress_history(messages)

        # Smart RAG: Refresh system prompt with current context
        # This enables dynamic RAG context injection based on latest user message
        # Refresh on every iteration to find new relevant context as conversation progresses
        if config.ENABLE_SMART_RAG or config.DEBUG_MODE:
            # Only refresh if there's a new user message since last refresh
            user_messages = [m for m in messages if m.get("role") == "user"]
            current_query = user_messages[-1].get("content", "")[:100] if user_messages else ""
            
            # Check if query changed or first iteration
            last_rag_query = getattr(tracker, '_last_rag_query', None)
            if tracker.current == 0 or current_query != last_rag_query:
                tracker._last_rag_query = current_query
                
                # Legacy PCIe indexing removed - strictly use .ragconfig now
                pass

                new_system_prompt = build_system_prompt(messages)
                # Update system message if it exists
                if messages and messages[0].get("role") == "system":
                    messages[0]["content"] = new_system_prompt

        # Show context usage before each iteration
        if config.DEBUG_MODE or tracker.current == 0:
            show_context_usage(messages)

        # Show flow stage: LLM Call
        if config.DEBUG_MODE:
            import time
            llm_start_time = time.time()
            user_msgs = len([m for m in messages if m.get('role') == 'user'])
            asst_msgs = len([m for m in messages if m.get('role') == 'assistant'])
            sys_msgs = len([m for m in messages if m.get('role') == 'system'])
            print(Color.system(f"[FLOW] Stage 1: LLM Call"))
            print(Color.system(f"[FLOW]   Messages: user:{user_msgs} assistant:{asst_msgs} system:{sys_msgs} total:{len(messages)}"))
            
        print(Color.agent(f"Agent (Iteration {tracker.current+1}/{tracker.max_iterations}): "), end="", flush=True)

        collected_content = ""
        # Call LLM via urllib (collect without printing)
        for content_chunk in chat_completion_stream(messages, stop=["Observation:", "<|call|>"]):
            collected_content += content_chunk

        # Apply colors to complete text and print
        colored_output = collected_content
        colored_output = colored_output.replace("Thought:", Color.CYAN + "Thought:" + Color.RESET)
        colored_output = colored_output.replace("Action:", Color.YELLOW + "Action:" + Color.RESET)

        # In DEBUG_MODE, content is already streamed with labels, so skip duplicate print
        if not config.DEBUG_MODE:
            # Apply highlighting to Action and Thought if not already applied
            colored_output = colored_output.replace("Action:", Color.YELLOW + "Action:" + Color.RESET)
            colored_output = colored_output.replace("Thought:", Color.CYAN + "Thought:" + Color.RESET)
            print(colored_output)
        print()
        
        # Show flow stage: Response received
        if config.DEBUG_MODE:
            llm_elapsed = time.time() - llm_start_time if 'llm_start_time' in dir() else 0
            has_thought = "Thought:" in collected_content
            has_action = "Action:" in collected_content
            response_len = len(collected_content)
            response_tokens_est = response_len // 4
            print(Color.system(f"[FLOW] Stage 2: Response received"))
            print(Color.system(f"[FLOW]   Time: {llm_elapsed:.2f}s | Length: {response_len} chars (~{response_tokens_est} tokens)"))
            print(Color.system(f"[FLOW]   Parsed: Thought:{has_thought} Action:{has_action}"))

        # Add assistant response to history with token metadata
        assistant_msg = {"role": "assistant", "content": collected_content}

        # Attach actual token usage from API if available
        usage = llm_client.get_last_usage()
        if usage:
            assistant_msg["_tokens"] = usage  # Store as metadata

        messages.append(assistant_msg)

        # Check for Action first (needed for TodoWrite explicit call detection)
        actions = parse_all_actions(collected_content)

        # Parse TodoWrite (Phase 2 - Claude Code Style with explicit call detection)
        if todo_tracker is not None and config.ENABLE_TODO_TRACKING:
            # Check if todo_write was explicitly called as a tool
            explicit_todo_call = any(
                action.get("tool") == "todo_write"
                for action in actions
                if isinstance(action, dict) and action.get("tool")
            )

            # Only parse from text if NOT explicitly called
            # This prevents duplicate todos when LLM uses the tool directly
            if not explicit_todo_call:
                parsed_todos = parse_todo_write_from_text(collected_content)
                if parsed_todos:
                    todo_tracker.add_todos(parsed_todos)
                    print(Color.info(todo_tracker.format_progress()))
                    print()

        # Check for explicit completion signal
        if detect_completion_signal(collected_content):
            print(Color.success("\n[System] ✅ Task completion detected. Ending ReAct loop.\n"))
            break

        # Check for hallucinated Observation
        if "Observation:" in collected_content and not actions:
            print(Color.warning("  [System] ⚠️  Agent hallucinated an Observation. Correcting..."))
            # We already appended the assistant message above.
            # Now append the correction user message.
            messages.append({
                "role": "user", 
                "content": "[System] You generated 'Observation:' yourself. PLEASE DO NOT DO THIS. You must output an Action, wait for me to execute it, and then I will give you the Observation. Now, please output the correct Action."
            })
            continue

        if actions:
            combined_results = []

            # Todo Tracking: Mark current step as in_progress (Phase 2)
            if todo_tracker is not None and todo_tracker.get_current_todo():
                current_todo = todo_tracker.get_current_todo()
                print(Color.system(f"▶️ {current_todo.active_form}..."))

            # Show flow stage
            if config.DEBUG_MODE:
                print(Color.system(f"  ┌─ FLOW: Parse → Found {len(actions)} action(s)"))

            if len(actions) > 1 and config.ENABLE_REACT_PARALLEL:
                print(Color.info(f"  ⚡ Executing {len(actions)} actions (parallel mode)"))
                action_results = execute_actions_parallel(actions, tracker)

                for idx, tool_name, args_str, observation in action_results:
                    # Visual separator for multi-action (except first)
                    if idx > 0:
                        print(Color.system(f"  {'-'*40}"))

                    print(Color.tool(f"  🔧 Tool {idx+1}/{len(actions)}: {tool_name}"))

                    # Error detection: check if observation contains error indicators
                    obs_lower = observation.lower()
                    is_error = any(indicator in obs_lower for indicator in
                                  ['error:', 'exception:', 'traceback', 'syntax error', 'compilation failed'])

                    # Special case: ignore "error" in file content reads
                    if tool_name in ['read_file', 'read_lines', 'grep_file', 'get_plan'] and "error" in obs_lower:
                        if not observation.strip().lower().startswith("error:"):
                            is_error = False

                    # Record action for procedural memory
                    if procedural_memory is not None:
                        action_result = "error" if is_error else "success"
                        action_obj = Action(
                            tool=tool_name,
                            args=args_str[:100],  # Truncate args
                            result=action_result,
                            observation=observation[:200]  # Truncate observation
                        )
                        actions_taken.append(action_obj)

                    # Smart preview based on tool type
                    if tool_name in ['read_file', 'read_lines']:
                        lines = observation.split('\n')[:config.TOOL_RESULT_PREVIEW_LINES]
                        obs_preview = '\n'.join(lines) + f"\n... ({len(observation)} chars total)"
                    elif len(observation) > config.TOOL_RESULT_PREVIEW_CHARS:
                        obs_preview = observation[:config.TOOL_RESULT_PREVIEW_CHARS] + f"... ({len(observation)} chars total)"
                    else:
                        obs_preview = observation

                    print(Color.info(f"  ✓ Result: {obs_preview}\n"))

                    # Format for combined output
                    combined_results.append(f"--- [Action {idx+1}] {tool_name} ---\n{observation}")
            else:
                for i, (tool_name, args_str) in enumerate(actions):
                    # Visual separator for multi-action (except first)
                    if i > 0:
                        print(Color.system(f"  {'-'*40}"))

                    # Show tool execution stage
                    if config.DEBUG_MODE:
                        import time
                        tool_start_time = time.time()
                        print(Color.system(f"  ├─ FLOW: Execute → {tool_name}({args_str[:50]}...)"))

                    print(Color.tool(f"  🔧 Tool {i+1}/{len(actions)}: {tool_name}"))

                    # Record tool usage for progress tracking
                    tracker.record_tool(tool_name)

                    # Execute
                    observation = execute_tool(tool_name, args_str)

                    # Show tool execution timing
                    if config.DEBUG_MODE:
                        tool_elapsed = time.time() - tool_start_time
                        print(Color.system(f"  ├─ FLOW: Complete → {tool_elapsed:.2f}s | {len(observation)} chars"))

                    # Error detection: check if observation contains error indicators
                    obs_lower = observation.lower()
                    is_error = any(indicator in obs_lower for indicator in
                                  ['error:', 'exception:', 'traceback', 'syntax error', 'compilation failed'])

                    # Special case: ignore "error" in file content reads
                    if tool_name in ['read_file', 'read_lines', 'grep_file', 'get_plan'] and "error" in obs_lower:
                        if not observation.strip().lower().startswith("error:"):
                            is_error = False

                    # Record action for procedural memory
                    if procedural_memory is not None:
                        action_result = "error" if is_error else "success"
                        action_obj = Action(
                            tool=tool_name,
                            args=args_str[:100],  # Truncate args
                            result=action_result,
                            observation=observation[:200]  # Truncate observation
                        )
                        actions_taken.append(action_obj)

                    # Smart preview based on tool type
                    if tool_name in ['read_file', 'read_lines']:
                        lines = observation.split('\n')[:config.TOOL_RESULT_PREVIEW_LINES]
                        obs_preview = '\n'.join(lines) + f"\n... ({len(observation)} chars total)"
                    elif len(observation) > config.TOOL_RESULT_PREVIEW_CHARS:
                        obs_preview = observation[:config.TOOL_RESULT_PREVIEW_CHARS] + f"... ({len(observation)} chars total)"
                    else:
                        obs_preview = observation

                    print(Color.info(f"  ✓ Result: {obs_preview}\n"))

                    # Format for combined output
                    combined_results.append(f"--- [Action {i+1}] {tool_name} ---\n{observation}")

            # Combine all observations
            observation = "\n\n".join(combined_results)

            # Check consecutive errors using the combined observation
            if observation == last_error_observation:
                consecutive_errors += 1
                print(Color.warning(f"  [System] ⚠️  Consecutive error #{consecutive_errors}/{MAX_CONSECUTIVE_ERRORS}"))

                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    print(Color.error(f"  [System] ❌ Same error occurred {MAX_CONSECUTIVE_ERRORS} times. Stopping to prevent infinite loop."))
                    messages.append({
                        "role": "user",
                        "content": f"Observation: {observation}\n\n[System] The same error occurred {MAX_CONSECUTIVE_ERRORS} times consecutively. Please ask the user for help or try a different approach."
                    })
                    break
            else:
                consecutive_errors = 0
                last_error_observation = observation if "error" in observation.lower() else None

            # Process observation (handles large files and context management)
            messages = process_observation(observation, messages)

            # Todo Tracking: Auto-advance to next step if all actions succeeded (Phase 2)
            if todo_tracker is not None and config.TODO_AUTO_ADVANCE:
                # Check if all actions succeeded (no errors)
                all_success = True
                if hasattr(observation, 'lower') and 'error:' in observation.lower()[:100]:
                    all_success = False

                if all_success and todo_tracker.get_current_todo():
                    todo_tracker.auto_advance()
                    print(Color.success(f"✅ Step completed"))
                    if not todo_tracker.is_all_completed():
                        print(Color.info(todo_tracker.format_progress()))
                    else:
                        print(Color.success("🎉 All todos completed!"))
                    print()

            # Check for stall condition
            if tracker.is_stalled():
                print(Color.warning(f"  [System] ⚠️  Detected {tracker.consecutive_reads} consecutive read operations. Agent may be stalled."))
        else:
            # No action = natural completion
            break

        # Increment iteration counter
        tracker.increment()

    # Save trajectory after task completion
    if procedural_memory is not None and actions_taken:
        # Determine outcome
        has_errors = any(a.result == "error" for a in actions_taken)
        outcome = "failure" if has_errors else "success"

        save_procedural_trajectory(
            task_description=task_description,
            actions_taken=actions_taken,
            outcome=outcome,
            iterations=tracker.current
        )

    # ============================================================
    # ACE Credit Assignment: Update node credits based on outcome
    # ============================================================
    if graph_lite and referenced_node_ids and config.ENABLE_CREDIT_TRACKING:
        # Determine outcome tag
        has_errors = any(a.result == "error" for a in actions_taken) if actions_taken else False
        tag = 'harmful' if has_errors else 'helpful'

        # Update node credits
        updated = graph_lite.update_node_credits(referenced_node_ids, tag)

        if updated > 0:
            print(Color.info(f"[ACE] Updated {updated} knowledge nodes with tag '{tag}'"))
            graph_lite.save()

    return messages


# --- 7. Main Loop ---

def chat_loop():
    # Try to load existing conversation history
    loaded_messages = load_conversation_history()
    if loaded_messages:
        messages = loaded_messages
        print(Color.system("[System] Resuming from previous conversation.\n"))
    else:
        messages = [
            {"role": "system", "content": build_system_prompt()}
        ]

    # Initialize context tracker
    max_tokens = config.MAX_CONTEXT_CHARS // 4  # Convert chars to tokens
    context_tracker = get_context_tracker(max_tokens=max_tokens)

    # Update tracker with initial context
    # Note: System message includes base prompt + tools + memory + graph context
    if messages and messages[0].get("role") == "system":
        context_tracker.update_system_prompt(messages[0]["content"])

    # Tools and memory are included in system message, so set to 0 to avoid double counting
    context_tracker.update_tools("")
    context_tracker.update_memory({})

    # Update messages tokens (exclude system message to avoid double counting)
    context_tracker.update_messages(messages, exclude_system=True)

    print(Color.BOLD + Color.CYAN + f"Brian Coder Agent (Zero-Dependency) initialized." + Color.RESET)
    print(Color.system(f"Connecting to: {config.BASE_URL}"))
    print(Color.system(f"Rate Limit: {config.RATE_LIMIT_DELAY}s | Max Iterations: {config.MAX_ITERATIONS}"))
    print(Color.system(f"History: {'Enabled' if config.SAVE_HISTORY else 'Disabled'}"))

    compression_mode = "Smart" if config.ENABLE_SMART_COMPRESSION else "Traditional"
    print(Color.system(f"Compression: {'Enabled' if config.ENABLE_COMPRESSION else 'Disabled'} ({compression_mode}, Threshold: {int(config.COMPRESSION_THRESHOLD*100)}%)"))

    print(Color.system(f"Prompt Caching: {'Enabled' if config.ENABLE_PROMPT_CACHING else 'Disabled'}"))
    print(Color.system(f"Memory: {'Enabled' if config.ENABLE_MEMORY and memory_system else 'Disabled'}"))
    print(Color.system(f"Graph: {'Enabled' if config.ENABLE_GRAPH and graph_lite else 'Disabled'}"))
    
    # Perform Memory Healing (One-time check on startup)
    if config.ENABLE_GRAPH and graph_lite:
        graph_lite.heal_embeddings()
    print(Color.system(f"Procedural Memory: {'Enabled' if config.ENABLE_PROCEDURAL_MEMORY and procedural_memory else 'Disabled'}"))
    print(Color.system(f"Curator: {'Enabled' if config.ENABLE_CURATOR and curator else 'Disabled'}"))

    # Show initial context usage
    show_context_usage(messages)

    # ACE Credit Assignment: Track conversation count for periodic curation
    conversation_count = 0

    # Auto RAG Indexing on startup
    if config.ENABLE_RAG_AUTO_INDEX:
        try:
            from tools import rag_index
            mode_str = "(fine-grained)" if config.RAG_FINE_GRAINED else ""
            print(Color.system(f"[RAG] Checking for Verilog files to index... {mode_str}"))
            result = rag_index(".", fine_grained=config.RAG_FINE_GRAINED)
            # Result contains indexing info (files indexed or skipped via hash)
            if "Indexed" in result or "chunks" in result.lower():
                print(Color.success(f"[RAG] {result}"))
            else:
                print(Color.system(f"[RAG] {result}"))
        except Exception as e:
            print(Color.warning(f"[RAG] Auto-index skipped: {e}"))


    print(Color.system(f"Deep Think: {'Enabled' if config.ENABLE_DEEP_THINK else 'Disabled'}"))

    # Initialize slash command registry
    slash_registry = get_slash_command_registry()

    print(Color.info("\nType 'exit' or 'quit' to stop."))
    print(Color.info("Type /help for available slash commands.\n"))


    while True:
        try:
            user_input = input(Color.user("You: ") + Color.RESET)
            if user_input.lower() in ["exit", "quit"]:
                break

            # Handle slash commands
            if user_input.startswith('/'):
                # Update context tracker with current state before executing /context
                if user_input.strip() == '/context':
                    # Update with latest messages
                    if messages and messages[0].get("role") == "system":
                        context_tracker.update_system_prompt(messages[0]["content"])
                    context_tracker.update_messages(messages, exclude_system=True)

                result = slash_registry.execute(user_input)

                if result:
                    # Check for special commands
                    if result == "CLEAR_HISTORY":
                        # Clear conversation history
                        messages = [{"role": "system", "content": build_system_prompt()}]

                        # Update context tracker
                        if messages and messages[0].get("role") == "system":
                            context_tracker.update_system_prompt(messages[0]["content"])
                        context_tracker.update_tools("")
                        context_tracker.update_memory({})
                        context_tracker.update_messages(messages, exclude_system=True)

                        # Save to history
                        save_conversation_history(messages)

                        print(Color.success("\n✅ Conversation history cleared.\n"))
                        continue
                    elif result.startswith("COMPACT_HISTORY"):
                        # Compact conversation with optional options
                        import re
                        parts = result.split(":", 1)
                        options_str = parts[1].strip() if len(parts) > 1 else ""

                        instruction = None
                        keep_recent = None  # Use config default
                        dry_run = False

                        if options_str:
                            # Parse key=value options
                            if "keep=" in options_str:
                                keep_match = re.search(r'keep=(\d+)', options_str)
                                if keep_match:
                                    keep_recent = int(keep_match.group(1))
                            elif "dry_run=true" in options_str:
                                dry_run = True
                            else:
                                # Custom instruction
                                instruction = options_str

                        # Compress with options
                        messages = compress_history(
                            messages,
                            force=True,
                            instruction=instruction,
                            keep_recent=keep_recent,
                            dry_run=dry_run
                        )

                        # Update tracker and save (only if not dry-run)
                        if not dry_run:
                            context_tracker.update_messages(messages, exclude_system=True)
                            save_conversation_history(messages)

                        continue

                    elif result.startswith("SNAPSHOT_SAVE"):
                        # Save snapshot
                        from core.session_snapshot import save_snapshot
                        parts = result.split(":", 1)
                        name = parts[1].strip() if len(parts) > 1 and parts[1].strip() else None

                        try:
                            path = save_snapshot(messages, name)
                            snapshot_name = Path(path).stem
                            print(Color.success(f"\n✅ Snapshot saved: {snapshot_name}\n"))
                        except Exception as e:
                            print(Color.error(f"\n❌ Failed to save snapshot: {e}\n"))
                        continue

                    elif result.startswith("SNAPSHOT_LOAD"):
                        # Load snapshot
                        from core.session_snapshot import load_snapshot
                        parts = result.split(":", 1)
                        name = parts[1].strip()

                        try:
                            messages = load_snapshot(name)
                            context_tracker.update_messages(messages, exclude_system=True)
                            print(Color.success(f"\n✅ Snapshot loaded: {name}\n"))
                        except FileNotFoundError as e:
                            print(Color.error(f"\n❌ {e}\n"))
                        except Exception as e:
                            print(Color.error(f"\n❌ Failed to load snapshot: {e}\n"))
                        continue

                    elif result.startswith("SNAPSHOT_DELETE"):
                        # Delete snapshot
                        from core.session_snapshot import delete_snapshot
                        parts = result.split(":", 1)
                        name = parts[1].strip()

                        try:
                            if delete_snapshot(name):
                                print(Color.success(f"\n✅ Snapshot deleted: {name}\n"))
                            else:
                                print(Color.error(f"\n❌ Snapshot not found: {name}\n"))
                        except Exception as e:
                            print(Color.error(f"\n❌ Failed to delete snapshot: {e}\n"))
                        continue

                    elif result.startswith("PLAN_MODE_RESULT:"):
                        plan_path = result.split(":", 1)[1].strip()
                        if not plan_path:
                            print(Color.error("\n❌ Plan mode did not return a plan path.\n"))
                            continue

                        messages = _execute_plan_from_file(messages, plan_path)
                        continue

                    elif result.startswith("PLAN_MODE_REQUEST:"):
                        task = result.split(":", 1)[1].strip()
                        if not task:
                            print(Color.error("\n❌ Plan mode requires a task description.\n"))
                            continue

                        try:
                            from core.plan_mode import plan_mode_loop
                            plan_result = plan_mode_loop(task, context_messages=messages)
                        except Exception as e:
                            print(Color.error(f"\n❌ Plan mode failed with exception: {e}\n"))
                            if config.FULL_PROMPT_DEBUG:
                                import traceback
                                print(Color.DIM + traceback.format_exc() + Color.RESET)
                            continue

                        if plan_result is None:
                            print(Color.warning("\n⚠️  Plan mode cancelled.\n"))
                            continue

                        # Execute plan (use plan_content if plan_path is empty)
                        if plan_result.plan_path:
                            messages = _execute_plan_from_file(messages, plan_result.plan_path)
                        elif plan_result.plan_content:
                            # Plan not saved to file, but we have content
                            print(Color.info("[Plan Mode] Using in-memory plan (not saved to file)"))
                            plan_message = (
                                "You have an approved implementation plan. Execute the steps in order.\n"
                                "Do not change the plan without asking. Use tools as needed.\n\n"
                                f"{plan_result.plan_content}"
                            )
                            messages.append({"role": "user", "content": plan_message})
                            try:
                                tracker = IterationTracker(max_iterations=config.MAX_ITERATIONS)
                                messages = run_react_agent(
                                    messages,
                                    tracker,
                                    "Execute approved plan",
                                    mode="interactive",
                                    allow_claude_flow=False
                                )
                            except Exception as e:
                                print(Color.error(f"[Plan Mode] Error during plan execution: {e}"))
                        else:
                            print(Color.error("\n❌ Plan result has no path or content.\n"))

                        continue

                    elif result == "PLAN_MODE_CANCELLED":
                        print(Color.warning("\n⚠️  Plan mode cancelled.\n"))
                        continue

                    else:
                        # Regular command output
                        print(result)
                        continue

            # Auto-extract preferences from user input (Mem0-style)
            if memory_system is not None and config.ENABLE_MEMORY and config.ENABLE_AUTO_EXTRACT:
                try:
                    result = memory_system.auto_extract_and_update(user_input)
                    if result.get("actions"):
                        for action in result["actions"]:
                            if action["action"] == "ADD":
                                print(Color.success(f"  [Memory] ✅ Learned new preference: {action['key']} = {action['value']}"))
                            elif action["action"] == "UPDATE":
                                print(Color.info(f"  [Memory] 🔄 Updated preference: {action['key']} = {action['new_value']} (was: {action['old_value']})"))
                            elif action["action"] == "DELETE":
                                print(Color.warning(f"  [Memory] ❌ Removed preference: {action['key']}"))
                except Exception as e:
                    # Fail silently if extraction fails
                    pass

            messages.append({"role": "user", "content": user_input})

            # ReAct Loop: Smart Iteration Control with progress tracking
            # Initialize iteration tracker
            tracker = IterationTracker(max_iterations=config.MAX_ITERATIONS)
            
            # Run ReAct Agent
            messages = run_react_agent(messages, tracker, user_input, mode='interactive')

            # Extract knowledge from conversation at end
            try:
                on_conversation_end(messages)
            except Exception as e:
                print(Color.warning(f"[Warning] Failed to save knowledge: {e}"))
                print(Color.warning("[Warning] Conversation will continue normally"))

            # ACE Credit Assignment: Run periodic curation
            conversation_count += 1
            if curator and conversation_count % config.CURATOR_INTERVAL == 0:
                print(Color.system("\n[Curator] Running periodic knowledge curation..."))
                try:
                    stats = curator.curate()
                    if stats['deleted_harmful'] > 0 or stats['pruned_unused'] > 0:
                        print(Color.info(f"[Curator] Cleaned up: {stats['deleted_harmful']} harmful, "
                                       f"{stats['pruned_unused']} unused nodes"))
                        print(Color.info(f"[Curator] Graph size: {stats['total_before']} → {stats['total_after']} nodes"))
                    else:
                        print(Color.info("[Curator] No cleanup needed. Graph is healthy."))
                except Exception as e:
                    print(Color.warning(f"[Curator] Curation failed: {e}"))

        except KeyboardInterrupt:
            print(Color.warning("\nExiting..."))
            save_conversation_history(messages)
            try:
                on_conversation_end(messages)
            except Exception as e:
                print(Color.warning(f"[Warning] Failed to save knowledge: {e}"))
            break
        except Exception as e:
            print(Color.error(f"\nAn error occurred: {e}"))
            pass

    # Save history on normal exit
    save_conversation_history(messages)
    try:
        on_conversation_end(messages)
    except Exception as e:
        print(Color.warning(f"[Warning] Failed to save knowledge: {e}"))

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--prompt":
        # One-shot mode with ReAct loop
        prompt = sys.argv[2]
        messages = [
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": prompt}
        ]
        
        print(Color.user(f"User: {prompt}\n"))

        # ReAct loop: Smart Iteration Control with progress tracking
        # Initialize iteration tracker (oneshot mode)
        tracker = IterationTracker(max_iterations=config.MAX_ITERATIONS)

        # Run ReAct Agent
        messages = run_react_agent(messages, tracker, prompt, mode='oneshot')

        # Extract knowledge from conversation at end
        try:
            on_conversation_end(messages)
        except Exception as e:
            print(Color.warning(f"[Warning] Failed to save knowledge: {e}"))
    else:
        chat_loop()
