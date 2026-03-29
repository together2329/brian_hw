import sys
import os
import json
import platform
import urllib.request
import urllib.error
import re
import copy
import time
import traceback
import subprocess

# Windows: force UTF-8 for stdout/stderr to avoid cp1252 emoji crashes
if platform.system() == "Windows":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
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
sys.path.insert(0, _project_root)  # common_ai_agent directory (for lib, core, agents)

import config
from core import tools
from core.action_dependency import ActionDependencyAnalyzer, FileConflictDetector, ActionBatch
from core.slash_commands import get_registry as get_slash_command_registry
from core.context_tracker import get_tracker as get_context_tracker
from core.session_manager import SessionManager, RecoveryPoint
import llm_client
from lib.display import Color
from llm_client import chat_completion_stream, call_llm_raw, estimate_message_tokens, get_actual_tokens
from lib.memory import MemorySystem
from lib.todo_tracker import TodoTracker
from core.graph_lite import GraphLite, Node, Edge
from lib.procedural_memory import ProceduralMemory, Action, Trajectory
from lib.message_classifier import MessageClassifier
from lib.curator import KnowledgeCurator
from core.hooks import (
    HookRegistry, HookPoint, HookContext, create_default_hooks,
    TOOL_OUTPUT_LIMITS
)
from core.background import get_background_manager

# Deep Think (deprecated - replaced by plan agent in v2)
if getattr(config, 'ENABLE_DEEP_THINK', False) and not getattr(config, 'ENABLE_SUB_AGENTS', False):
    try:
        from lib.deep_think import DeepThinkEngine, DeepThinkResult, format_deep_think_output
    except ImportError:
        pass

# Legacy Sub-Agent System (deprecated - replaced by background agent system in v2)
orchestrator = None
if getattr(config, 'ENABLE_SUB_AGENTS', False):
    try:
        from sub_agents import Orchestrator
    except ImportError:
        try:
            from agents.sub_agents import Orchestrator
        except ImportError:
            Orchestrator = None

from lib.iteration_control import IterationTracker, detect_completion_signal, show_iteration_warning

# Global Todo Tracker state (synced with tools)
todo_tracker = None

def _parse_todo_markdown(text: str) -> List[Dict]:
    """
    TodoWrite: [ ] ... 형태의 마크다운 리스트를 파싱하여 todo_write 인자로 변환.
    """
    # Look for TodoWrite: followed by a checkbox list
    pattern = r"TodoWrite:.*?\n((?:\s*[-*]\s*\[\s*[ xX]*\]\s*.*?\n?)+)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if not match:
        return []
    
    tasks = []
    list_content = match.group(1)
    for line in list_content.strip().split("\n"):
        line = line.strip()
        # Extract content after [ ] or [x]
        content_match = re.search(r"\[\s*([ xX]*)\s*\]\s*(.*)", line)
        if content_match:
            status_char = content_match.group(1).lower()
            content = content_match.group(2).strip()
            
            status = "pending"
            if "x" in status_char:
                status = "completed"
            
            tasks.append({
                "content": content,
                "activeForm": content,
                "status": status
            })
    return tasks

# --- Dynamic Plugin Loading ---
if config.ENABLE_VERILOG_TOOLS:
    try:
        from core import tools_verilog
        tools.AVAILABLE_TOOLS.update(tools_verilog.VERILOG_TOOLS)
        if config.DEBUG_MODE:
            print(Color.system("[System] Verilog tools plugin loaded successfully 🔌"))
    except ImportError as e:
        print(Color.warning(f"[System] Failed to load Verilog tools: {e}"))

try:
    from core.tools_spec import spec_navigate
    tools.AVAILABLE_TOOLS["spec_navigate"] = spec_navigate
    if config.DEBUG_MODE:
        print(Color.system("[System] spec tools loaded: spec_navigate"))
except ImportError as e:
    print(Color.warning(f"[System] Failed to load spec tools: {e}"))

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

# --- Global Hook System ---
hook_registry = None
if getattr(config, 'ENABLE_HOOKS', True):
    try:
        hook_registry = create_default_hooks()
    except Exception as e:
        print(f"\033[91m[System] ❌ Hook system initialization failed: {e}\033[0m")
        hook_registry = None


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

# --- Turn Tracking ---
# Track conversation turns for better context management
current_turn_id = 0  # Current turn number (incremented on each user message)

# --- Session Recovery ---
# Session management for recovery system
session_manager = None  # SessionManager instance (initialized in chat_loop)
current_session_id = None  # Current session ID
current_recovery_point = None  # Latest recovery point

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
    text = re.sub(r'\*\*(?:Action|tool_call):\*\*', 'Action:', text)
    text = re.sub(r'\*\*(?:Action|tool_call)\*\*:', 'Action:', text)  # Alternate format
    text = re.sub(r'tool_call:', 'Action:', text) # Direct fallback
    # Normalize lowercase "action:" to "Action:" (glm-4.7 sometimes generates lowercase)
    text = re.sub(r'(?m)^action:', 'Action:', text)
    
    # Pattern: number followed by quote then closing paren/comma
    # e.g., =26") or =26", -> =26) or =26,
    text = re.sub(r'=(\d+)"([,\)])', r'=\1\2', text)
    
    # Pattern: number followed by single quote then closing paren/comma  
    text = re.sub(r"=(\d+)'([,\)])", r'=\1\2', text)
    
    return text


def _convert_all_glm_tool_calls(text, xml_params_to_action_fn):
    """
    Convert GLM 4.7 style XML tool calls to Action: format.
    Handles all tag name variations and typos.

    Examples:
      <tool>list_dir</tool><parameter><path>.</path></parameter>
      <action><execute>read_file</execute><paramater><path>f.py</path></paramater>
      <tool>grep_file</tool><paratemeter><pattern>x</pattern><path>f.py</path></paratemeter>
    """
    import re

    result = text
    # Tag patterns for tool name wrapper
    tool_tag_re = re.compile(
        r'<(tool|action|execute|func\w*)\s*>'       # open tag
        r'\s*(?:<(execute|tool)\s*>\s*)?'            # optional nested: <action><execute>
        r'(\w+)'                                     # tool name
        r'\s*(?:</\w+>\s*)?'                         # optional nested close
        r'</\w+>'                                    # close tag
    )

    # Find all tool name occurrences
    matches = list(tool_tag_re.finditer(result))
    if not matches:
        return text

    # Process in reverse order to preserve positions
    for m in reversed(matches):
        tool_name = m.group(3)
        after_tool = result[m.end():]

        # Look for parameter block right after.
        # Opening: <parameter>, <paramater>, <prameter>, <paratemeter>, etc.
        # Must start with "par" or "pra" to avoid matching </path>, </pattern>
        param_re = re.match(
            r'\s*<(p(?:ar|ra)\w*)\s*>'    # opening: par* or pra* (parameter, paramater, prameter...)
            r'(.*)'                        # content (greedy — take everything until last matching close)
            r'</(p(?:ar|ra)\w*)\s*>',     # closing: par* or pra*
            after_tool,
            re.DOTALL
        )

        if param_re:
            params_block = param_re.group(2)
            total_end = m.end() + param_re.end()
            action_str = xml_params_to_action_fn(tool_name, params_block)
            result = result[:m.start()] + action_str + result[total_end:]
        else:
            # No parameter block — just tool name
            action_str = f"\nAction: {tool_name}()\n"
            result = result[:m.start()] + action_str + result[m.end():]

    return result


def _strip_native_tool_tokens(text):
    """
    Strip native tool call tokens emitted by models (GLM, Qwen, Mistral, DeepSeek, etc.)
    and convert them to the ReAct Action: format.

    GLM 4.7 variants (tag names are often misspelled):
      <tool>list_dir</tool><parameter><path>.</path></parameter>
      <action><execute>list_dir</execute><parameter><path>.</path></paratemeter>
      <tool>grep_file</tool><paramater><pattern>main</pattern><path>file.py</path></paramater>

    Other models:
      <tool_call>{"name":"func","arguments":{...}}</tool_call>
      {"name":"func","arguments":{...}}  (bare JSON)
    """
    import re

    # ── Strip reasoning tokens leaked into content ──
    # DeepSeek/GLM sometimes emit <think>...</think> as content instead of reasoning
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    # Partial tags (stream cut mid-tag)
    text = re.sub(r'</?think>', '', text)

    # ── Helper ──
    def _json_tool_call_to_action(json_str):
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
        """Parse <key>value</key> pairs from any XML parameter block."""
        params = re.findall(r'<(\w+)>(.*?)</\1>', params_block, re.DOTALL)
        if tool_name and params:
            args_str = ", ".join(f'{k}={json.dumps(v)}' for k, v in params)
            return f"\nAction: {tool_name}({args_str})\n"
        elif tool_name:
            return f"\nAction: {tool_name}()\n"
        return ""

    # ── Pattern 0: <tool_call>func(args)</tool_call> — direct function call format ──
    def _func_call_to_action(content):
        content = content.strip()
        # Already looks like a function call: name(args)
        if re.match(r'^\w+\s*\(', content):
            return f"\nAction: {content}\n"
        return content

    text = re.sub(
        r'<tool_call>\s*(\w+\s*\([^<]*\))\s*(?:</tool_call>)?',
        lambda m: _func_call_to_action(m.group(1)),
        text, flags=re.DOTALL
    )

    # ── Pattern 1: JSON-based tool calls ──
    # <tool_call>{"name":"func","arguments":{...}}</tool_call>
    # Use greedy match to capture nested JSON (non-greedy stops at first })
    text = re.sub(
        r'<tool_call>\s*(\{.*\})\s*</tool_call>',
        lambda m: _json_tool_call_to_action(m.group(1)),
        text, flags=re.DOTALL
    )
    # Bare JSON: {"name":"func","arguments":{...}}
    text = re.sub(
        r'\{\s*"name"\s*:\s*"(\w+)"\s*,\s*"arguments"\s*:\s*\{[^{}]*\}\s*\}',
        lambda m: _json_tool_call_to_action(m.group(0)),
        text
    )

    # ── Pattern 2: GLM-style XML tool calls (UNIVERSAL) ──
    # Catches ALL variants:
    #   <tool>name</tool><parameter>...</parameter>
    #   <action><execute>name</execute><parameter>...</paratemeter>
    #   <tool>name</tool><paramater>...</paramater>   (typo)
    # Strategy:
    #   tag1 = any tag containing tool/action/execute → extract tool name
    #   tag2 = any tag starting with "par" or "param" → extract <key>val</key> params

    # Step 2a: Find tool name from various wrapper tags
    # Match: <ANYTAG>tool_name</ANYTAG> followed by <param-like-tag>...</close-tag>
    def _convert_glm_tool_call(match):
        tool_name = match.group(1).strip()
        params_block = match.group(2)
        return _xml_params_to_action(tool_name, params_block)

    # Universal GLM pattern: use a function to avoid regex greediness issues
    text = _convert_all_glm_tool_calls(text, _xml_params_to_action)

    # ── Pattern 3: Strip remaining special tokens ──
    native_tokens = [
        'tool_call_begin', 'tool_call_end',
        'tool_calls_section_begin', 'tool_calls_section_end',
        '<|tool_call|>', '<|tool_calls|>',
        '<|start_header_id|>tool_call<|end_header_id|>',
    ]
    for token in native_tokens:
        text = text.replace(token, '')

    # Strip <|...|> special tokens
    text = re.sub(r'<\|(?:tool_call|tool_calls|functions)[^|]*\|>', '', text)

    # Strip any remaining XML-like tags from tool calling (tool, action, execute, param*)
    text = re.sub(r'</?(?:tool_call|tool|action|execute|func\w*|p(?:ar|aram)\w*)>', '', text)

    # ── Pattern 4: Bare function calls without Action: prefix ──
    # Models like Qwen sometimes output just "list_dir(path=".")" without any prefix.
    # Detect known tool names at line start and prepend "Action: "
    _KNOWN_TOOLS = {
        'read_file', 'write_file', 'run_command', 'list_dir', 'grep_file',
        'read_lines', 'find_files', 'replace_in_file', 'replace_lines',
        'git_diff', 'git_status', 'todo_write', 'todo_update',
        # RAG tools disabled by default (ENABLE_SMART_RAG=true to re-enable)
        # 'rag_search', 'rag_index', 'rag_explore', 'rag_status', 'rag_clear',
        'background_task', 'background_output', 'background_cancel', 'background_list',
        'analyze_verilog_module', 'find_signal_usage', 'find_module_definition',
        'extract_module_hierarchy', 'generate_module_testbench', 'find_potential_issues',
        'analyze_timing_paths', 'generate_module_docs', 'suggest_optimizations',
    }
    _tools_pattern = '|'.join(re.escape(t) for t in _KNOWN_TOOLS)
    text = re.sub(
        r'^(\s*)(' + _tools_pattern + r')\s*\(',
        r'\1Action: \2(',
        text,
        flags=re.MULTILINE
    )

    return text.strip()


def _extract_annotation_ranges(text):
    """
    Extract @parallel/@sequential annotation ranges from text.

    Returns:
        List[Tuple[int, int, str]]: [(start_pos, end_pos, hint_type)]
    """
    hint_ranges = []

    # Pattern: @parallel ... @end_parallel
    parallel_blocks = re.finditer(
        r'@parallel\s*\n(.*?)\n\s*@end_parallel',
        text,
        re.DOTALL | re.MULTILINE
    )
    for match in parallel_blocks:
        hint_ranges.append((match.start(1), match.end(1), "parallel"))

    # Pattern: @sequential ... @end_sequential
    sequential_blocks = re.finditer(
        r'@sequential\s*\n(.*?)\n\s*@end_sequential',
        text,
        re.DOTALL | re.MULTILINE
    )
    for match in sequential_blocks:
        hint_ranges.append((match.start(1), match.end(1), "sequential"))

    return hint_ranges


def parse_all_actions(text):
    """
    Parses ALL 'Action: Tool(args)' occurrences from the text.
    Returns a list of (tool_name, args_str, hint) tuples.

    Improvements:
    - Sanitizes common LLM output errors (like end_line=26")
    - On parse failure, skips to next Action instead of stopping
    - ENHANCED: Parses @parallel/@sequential annotations for LLM hints
    """
    # Sanitize common errors first
    text = sanitize_action_text(text)

    # Extract annotation ranges (for LLM hints)
    hint_ranges = _extract_annotation_ranges(text)

    if config.DEBUG_MODE and hint_ranges:
        print(f"[DEBUG] Found {len(hint_ranges)} annotation blocks")
        for start, end, hint in hint_ranges:
            print(f"  - {hint}: chars {start}-{end}")

    actions = []
    action_positions = []  # Track text position of each action
    start_pos = 0
    # Support "Action:", "**Action:**", "tool_call:", etc. 
    # Handle optional markdown formatting (bold **, italic _, code `) around tool name
    # e.g., Action: `read_file`(...) or **Action**: **read_file**(...)
    pattern = r"(?:\*\*|__)?(?:Action|tool_call)(?:\*\*|__)?::*\s*[`*_]*\s*(\w+)\s*[`*_]*\s*\("
    
    if config.DEBUG_MODE:
        print(f"[DEBUG] parse_all_actions input length: {len(text)}")

    while True:
        match = re.search(pattern, text[start_pos:], re.DOTALL | re.IGNORECASE)
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
            action_positions.append(start_pos + match.start())  # Store action position
            start_pos = i  # Continue searching after this action
        else:
            # Unmatched parentheses - check if there's another Action after this one
            next_action_match = re.search(pattern, text[match_start:], re.DOTALL)

            if i >= len(text) and not next_action_match:
                # Truly truncated at end of text with no further actions
                if config.DEBUG_MODE:
                    print(Color.warning(f"[System] ⚠️  Action '{tool_name}' appears truncated at end of text. Attempting auto-recovery..."))

                args_str = text[match_start:]
                if args_str:
                    if in_double_quote: args_str += '"'
                    elif in_single_quote: args_str += "'"
                    elif in_triple_double: args_str += '"""'
                    elif in_triple_single: args_str += "'''"

                    actions.append((tool_name, args_str))
                    action_positions.append(start_pos + match.start())
                    if config.DEBUG_MODE:
                        print(Color.warning(f"[System] 🔧 Auto-recovered truncated action: {tool_name}({args_str}...)"))
                    break

            # Unmatched parentheses in middle of text - skip this action and try next one
            if config.DEBUG_MODE:
                print(f"[DEBUG] parse_all_actions: Unmatched parentheses for {tool_name}, skipping to next Action")
            
            # Find next "Action:" and continue from there instead of breaking
            if next_action_match:
                start_pos = match_start + next_action_match.start()
            else:
                start_pos = len(text)

            
    
    # Deduplicate actions (preserve order)
    # Why? Often models repeat the exact same action in Thought and Action blocks.
    # Logic: Keep if (tool_name, args_str) has not been seen.
    unique_actions = []
    unique_positions = []
    seen = set()
    for idx, (tool_name, args_str) in enumerate(actions):
        # Normalize args string (strip whitespace) for comparison
        clean_args = args_str.strip()
        signature = (tool_name, clean_args)

        if signature not in seen:
            seen.add(signature)
            unique_actions.append((tool_name, args_str))
            if idx < len(action_positions):
                unique_positions.append(action_positions[idx])
            else:
                unique_positions.append(0)  # Fallback

    if config.DEBUG_MODE and len(unique_actions) != len(actions):
        print(f"[DEBUG] Deduplicated actions: {len(actions)} -> {len(unique_actions)}")

    # Assign hints based on position
    actions_with_hints = []
    for idx, (tool_name, args_str) in enumerate(unique_actions):
        action_pos = unique_positions[idx]
        hint = None

        # Find matching hint range
        for range_start, range_end, hint_type in hint_ranges:
            if range_start <= action_pos < range_end:
                hint = hint_type
                break

        actions_with_hints.append((tool_name, args_str, hint))

        if config.DEBUG_MODE and hint:
            print(f"[DEBUG] Action '{tool_name}' has hint: {hint}")

    return actions_with_hints


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
            if chars_consumed == 0:
                break
            i += chars_consumed
        else:
            # Positional argument
            value, chars_consumed = parse_value(args_str[i:])
            if chars_consumed == 0:
                break
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

    # JSON-like List or Dict
    if text.startswith('[') or text.startswith('{'):
        try:
            # We need to find the matching closing bracket/brace
            # This is tricky without a full parser, but let's try a simple bracket counter or json decoder
            import json
            decoder = json.JSONDecoder()
            value, end_pos = decoder.raw_decode(text)
            return value, end_pos
        except json.JSONDecodeError:
            # Fallback if strict JSON parsing fails (might be Python list repr?)
            # But for now, let's assume valid JSON for complex types
            pass

    # Number or identifier
    match = re.search(r'^([^,)\s]+)', text) # fixed regex anchor
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



# Thread-local storage for Agent communication metadata
import threading
_agent_metadata = threading.local()

# Phase 3: Thread-local storage for SharedContext
_shared_context_storage = threading.local()


def get_shared_context():
    """Get current thread's SharedContext"""
    if not hasattr(_shared_context_storage, 'context'):
        # Lazy import to avoid circular dependency
        try:
            from agents.shared_context import SharedContext
            _shared_context_storage.context = SharedContext()
        except ImportError:
            _shared_context_storage.context = None
    return _shared_context_storage.context


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

        # Phase 2: Check if result is AgentResult and store metadata
        if hasattr(result, '__class__') and result.__class__.__name__ == 'AgentResult':
            # Store metadata in thread-local for accumulated_context
            _agent_metadata.last_result = {
                'tool_name': tool_name,
                'files_examined': result.get('files_examined', []),
                'planned_steps': result.get('planned_steps', []),
                'summary': result.get('summary', ''),
                'tool_calls_count': result.get('tool_calls_count', 0),
                'execution_time_ms': result.get('execution_time_ms', 0),
                'agent_type': result.get('metadata', {}).get('agent_type', '')
            }
        else:
            # Clear metadata for non-agent tools
            _agent_metadata.last_result = None

        # Ensure result is string for downstream processing
        if not isinstance(result, str):
            import json
            try:
                # Pretty print dict/list for readability
                result = json.dumps(result, indent=2, ensure_ascii=False)
            except Exception:
                result = str(result)

        # Hook: AFTER_TOOL_EXEC (tool output truncation)
        if hook_registry:
            hook_ctx = HookContext(
                tool_name=tool_name,
                tool_args=args_str,
                tool_output=result,
            )
            hook_ctx = hook_registry.run(HookPoint.AFTER_TOOL_EXEC, hook_ctx)
            result = hook_ctx.tool_output

        return result

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        _agent_metadata.last_result = None  # Clear metadata on error

        # Hook: ON_ERROR
        if hook_registry:
            hook_ctx = HookContext(
                tool_name=tool_name,
                tool_args=args_str,
                error=e,
                error_traceback=error_detail,
            )
            hook_registry.run(HookPoint.ON_ERROR, hook_ctx)

        return f"Error parsing/executing arguments: {e}\n{error_detail}\nargs_str was: {args_str[:200]}"

# --- 5. Context Management ---

# Helper functions moved to llm_client.py

def _route_skill_via_llm(user_message: str, skills: list):
    """
    LLM 1 call로 가장 적합한 skill을 선택.
    Returns skill name string or None.
    """
    if not skills:
        return None
    skill_names = {s.name.lower(): s.name for s in skills}
    menu = "\n".join(f"- {s.name}: {s.description.strip()}" for s in skills)
    routing_prompt = (
        f"Available skills:\n{menu}\n\n"
        f"User message: \"{user_message[:200]}\"\n\n"
        "Rules:\n"
        "- large-file-analyst: user wants to read/understand an ENTIRE file or its overall structure. Keywords: 분석, analyze, 전체, 구조, 함수 목록, 클래스 목록, 내용, 파악\n"
        "- code-analysis-expert: user wants to FIND or TRACE a specific symbol/function/signal. Keywords: find, trace, 어디, 어느, 정의, definition, usage\n"
        "- Reply with ONLY the skill name, or \"none\" if no skill fits."
    )
    routing_model = os.getenv("SUBAGENT_LOW_MODEL", config.MODEL_NAME)
    try:
        response = call_llm_raw(routing_prompt, temperature=0.0, model=routing_model)
    except Exception as e:
        import sys as _sys
        _sys.stderr.write(f"[skill routing error] {e}\n")
        return None
    if not response:
        return None
    cleaned = response.strip().lower()
    if cleaned in ("none", "none.", "no skill", ""):
        return None
    if cleaned in skill_names:
        return skill_names[cleaned]
    for lower_name, original_name in skill_names.items():
        if lower_name in cleaned:
            return original_name
    return None


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
        from core.skill_system import get_skill_registry

        registry = get_skill_registry()

        # Get last user message
        user_messages = [m for m in messages if m.get("role") == "user"]
        if not user_messages:
            return []

        last_msg = user_messages[-1].get("content", "")
        if isinstance(last_msg, list):
            last_msg = " ".join(p.get("text", "") for p in last_msg if isinstance(p, dict))
        cache_key = last_msg[:300].strip()

        # Recent history context for routing (last 6 user turns)
        def _extract_text(m):
            c = m.get("content", "")
            if isinstance(c, list):
                return " ".join(p.get("text", "") for p in c if isinstance(p, dict))
            return c or ""
        recent_user_msgs = [_extract_text(m) for m in messages if m.get("role") == "user"]
        history_context = " | ".join(recent_user_msgs[-6:-1])  # 직전 5턴 (현재 제외)

        # Session-level skill state (persists across compressions)
        # _active_skill: currently loaded skill name (None = none)
        if "skill" not in cache_key.lower():
            # No "skill" keyword → reuse existing active skill (skip routing)
            routed = getattr(load_active_skills, '_active_skill', None)
            # If no active skill (e.g. session restart), try routing with history context
            if routed is None and history_context:
                all_skills = registry.get_all_skills()
                routable = [s for s in all_skills if s.activation.auto_detect]
                routing_ctx = f"{history_context} | {cache_key}"
                routed = _route_skill_via_llm(routing_ctx, routable) if routable else None
                load_active_skills._active_skill = routed
                if routed:
                    print(Color.system(f"  [skill] {routed} (llm-routed, history)"))
        else:
            # "skill" keyword present → LLM routing (with cache)
            if cache_key == getattr(load_active_skills, '_cached_key', ""):
                # Same message → use cache silently
                routed = getattr(load_active_skills, '_cached_skill', None)
            elif getattr(load_active_skills, '_active_skill', None) is not None:
                # Mid-loop re-call (tool results added as user messages) → keep existing skill
                routed = load_active_skills._active_skill
            else:
                # First routing for this user turn
                all_skills = registry.get_all_skills()
                routable = [s for s in all_skills if s.activation.auto_detect]
                routed = _route_skill_via_llm(cache_key, routable) if routable else None
                load_active_skills._cached_key = cache_key
                load_active_skills._cached_skill = routed
                load_active_skills._active_skill = routed  # None clears, name sets
                if routed:
                    print(Color.system(f"  [skill] {routed} (llm-routed)"))

        auto_detected = [routed] if routed else []

        # Manual overrides (set by /skill enable/disable commands)
        forced_skills = getattr(load_active_skills, 'forced_skills', set())
        disabled_skills = getattr(load_active_skills, 'disabled_skills', set())

        # Merge: forced + auto - disabled
        active_skill_names = list(forced_skills | set(auto_detected))
        active_skill_names = [s for s in active_skill_names if s not in disabled_skills]

        # Store for /skill active command and debugging
        load_active_skills.active_skills = active_skill_names

        if not active_skill_names:
            return []

        # Generate skill prompts
        skill_prompts = []
        for skill_name in active_skill_names:
            skill = registry.get_skill(skill_name)
            if skill:
                skill_prompts.append(skill.format_for_prompt())

        # forced skills output (llm-routed already printed above)
        if skill_prompts:
            for skill_name in active_skill_names:
                if skill_name in forced_skills:
                    print(Color.system(f"  [skill] {skill_name} (forced)"))

        return skill_prompts

    except ImportError as e:
        if config.DEBUG_MODE:
            print(Color.warning(f"[PROMPT] ⚠️ Skill system not available: {e}"))
        return []
    except Exception as e:
        if config.DEBUG_MODE:
            print(Color.warning(f"[PROMPT] ⚠️ Error loading skills: {e}"))
        return []


def _build_system_prompt_str(**kwargs) -> str:
    """build_system_prompt() wrapper — always returns a string (handles optimized dict return)."""
    sp = build_system_prompt(**kwargs)
    if isinstance(sp, dict):
        return (sp.get("static", "") + "\n\n" + sp.get("dynamic", "")).strip()
    return sp


def build_system_prompt(messages=None, allowed_tools=None, agent_mode=None):
    """
    Build system prompt with memory, graph context, and procedural guidance if available.

    Args:
        messages: Optional message history for graph semantic search and procedural retrieval
        allowed_tools: Optional set of allowed tools (for sub-agents)
        agent_mode: Optional agent operation mode (plan/normal)

    Returns:
        Complete system prompt string
    """
    # Determine effective tool list
    if allowed_tools is None:
        from core import tools
        _at = set(tools.AVAILABLE_TOOLS.keys())
    else:
        _at = set(allowed_tools)

    # Plan mode filtering: proactive tool hiding from system prompt
    if agent_mode in ('plan', 'plan_q'):
        _at = set(t for t in _at if t not in config.PLAN_MODE_BLOCKED_TOOLS)

    # Use new tool description system from config with filtered tool list
    is_plan = agent_mode in ('plan', 'plan_q')
    
    # Hide todo tools from prompt if no active tasks, as requested by user
    todo_active = False
    if todo_tracker is not None and todo_tracker.todos:
        todo_active = True
    
    base_prompt = config.build_base_system_prompt(allowed_tools=_at, plan_mode=is_plan, todo_active=todo_active)
    
    # Debug: Show prompt building start
    if config.DEBUG_MODE and messages:
        print(Color.system("[PROMPT] Building system prompt with context..."))
        print(Color.system(f"[PROMPT]   Messages in history: {len(messages)}"))

    # Build context section
    dynamic_context = ""
    if memory_system is not None or graph_lite is not None or procedural_memory is not None or config.ENABLE_SKILL_SYSTEM:
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
                print(Color.warning(f"[PROMPT] ⚠️ Error injecting skills: {e}"))


        # Combine all context parts
        dynamic_context = ""
        if context_parts:
            dynamic_context = "\n\n".join(context_parts)

            # Debug: Show prompt build summary
            if config.DEBUG_MODE and messages:
                total_chars = len(base_prompt) + len(dynamic_context)
                estimated_tokens = total_chars // 4
                print(Color.system(f"[PROMPT] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"))
                print(Color.system(f"[PROMPT] Build complete: {len(context_parts)} sections, ~{estimated_tokens:,} tokens"))

    # Return format based on CACHE_OPTIMIZATION_MODE
    if config.CACHE_OPTIMIZATION_MODE == "optimized":
        # Optimized mode: Return dict with static/dynamic parts
        return {
            "static": base_prompt,
            "dynamic": dynamic_context if dynamic_context else ""
        }
    else:
        # Legacy mode: Return single string
        full_prompt = base_prompt
        if dynamic_context:
            full_prompt = full_prompt + "\n\n" + dynamic_context
        return full_prompt

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
    Also displays session statistics including cache usage.

    Args:
        messages: Full message history
    """
    # Display cache statistics if caching was enabled
    if config.ENABLE_PROMPT_CACHING and llm_client.total_cache_read > 0:
        print(f"\n{Color.info('='*60)}")
        print(f"{Color.info('[Session Cache Statistics]')}")
        print(f"{Color.info('='*60)}")
        print(f"{Color.info(f'  Total Cache Created: {llm_client.total_cache_created:,} tokens')}")
        print(f"{Color.success(f'  Total Cache Hits: {llm_client.total_cache_read:,} tokens')}")

        # Calculate total savings (cache reads are 90% cheaper)
        total_savings = int(llm_client.total_cache_read * 0.9)
        print(f"{Color.success(f'  Estimated Cost Savings: ~{total_savings:,} tokens worth!')}")

        # Calculate efficiency percentage
        if llm_client.total_cache_created > 0:
            efficiency = (llm_client.total_cache_read / llm_client.total_cache_created) * 100
            print(f"{Color.success(f'  Cache Efficiency: {efficiency:.1f}% (hits/created)')}")

        print(f"{Color.info('='*60)}\n")

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


def _find_hook(hook_name: str):
    """Find a hook file, checking platform-appropriate extensions."""
    import platform
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
    # .sh, .bat, and others: run directly
    return [str(hook_path)]


def compress_history(messages, todo_tracker=None, force=False, instruction=None, keep_recent=None, dry_run=False, quiet=False):
    """
    Compresses history if it exceeds the token limit.
    Strategy: Keep System messages + Last N messages. Summarize the middle.
    Uses last_input_tokens from API (no additional API call).
    Supports both single and chunked compression modes.
    Args:
        messages: Conversation history
        todo_tracker: Optional tracker to preserve state
        force: If True, bypass token threshold check
        instruction: Optional custom instruction for summarization
        keep_recent: Number of recent messages to keep (None = use config default)
        dry_run: If True, return preview without modifying state
    """
    if not config.ENABLE_COMPRESSION and not force:
        return messages

    limit_tokens = config.MAX_CONTEXT_CHARS // 4
    # ... (skipping some logic for context calculation) ...

    # Preemptive compression threshold (85%)
    preemptive_threshold = int(limit_tokens * config.PREEMPTIVE_COMPRESSION_THRESHOLD)
    emergency_threshold = int(limit_tokens * config.COMPRESSION_THRESHOLD)

    # Use last_input_tokens from previous API call (no additional API call)
    current_tokens = get_actual_tokens(messages)
    token_source = "actual" if llm_client.last_input_tokens > 0 else "estimated"

    # Trigger preemptive compression at 85%
    if current_tokens >= preemptive_threshold and not force:
        usage_pct = int(current_tokens / limit_tokens * 100)
        if not quiet:
            print(Color.warning(
                f"\n[System] Preemptive compression triggered at {current_tokens:,} tokens "
                f"({usage_pct}%)"
            ))
        force = True

    if not force and current_tokens < emergency_threshold:
        return messages

    if not quiet:
        print(Color.warning(f"\n[System] Compression triggered. Context: {current_tokens:,} {token_source} tokens."))

    if not messages:
        return messages

    # Traditional compression: Simple time-based approach
    # Structure: [system] + [summary of old] + [recent N]
    print(Color.info("[System] Using traditional compression..."))

    # Pre-compact hook (platform-aware)
    pre_hook_path = _find_hook("pre_compact")
    if pre_hook_path and pre_hook_path.exists():
        print(Color.info(f"[Hook] Running {pre_hook_path.name}..."))
        try:
            subprocess.run(_hook_command(pre_hook_path), timeout=10, check=False, shell=False)
        except subprocess.TimeoutExpired:
            print(Color.warning(f"[Hook] {pre_hook_path.name} timed out (10s)"))
        except Exception as e:
            print(Color.warning(f"[Hook] {pre_hook_path.name} failed: {e}"))

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

    # Turn-based protection or legacy message-based protection
    if config.ENABLE_TURN_PROTECTION and any(m.get("turn_id") for m in other_msgs):
        # Turn-based protection (protects recent N turns)
        protected_turns = config.TURN_PROTECTION_COUNT

        # Find maximum turn ID
        max_turn = max((m.get("turn_id", 0) for m in other_msgs), default=0)
        protected_turn_threshold = max(0, max_turn - protected_turns + 1)

        # Protect recent N turns
        recent_msgs = [m for m in other_msgs if m.get("turn_id", 0) >= protected_turn_threshold]
        old_msgs = [m for m in other_msgs if m.get("turn_id", 0) < protected_turn_threshold]

        # Fallback: if all messages are in protected turns, reduce protection
        # to last 1 turn so we can still compress something
        if not old_msgs and protected_turns > 1:
            protected_turns = 1
            protected_turn_threshold = max_turn  # only protect current turn
            recent_msgs = [m for m in other_msgs if m.get("turn_id", 0) >= protected_turn_threshold]
            old_msgs = [m for m in other_msgs if m.get("turn_id", 0) < protected_turn_threshold]

        print(Color.info(
            f"[System] Protecting last {protected_turns} turns "
            f"({len(recent_msgs)} messages, turns {protected_turn_threshold}-{max_turn})"
        ))

        if not old_msgs:
            # True single-turn: fall back to message-based split (keep last 4 messages)
            fallback_keep = min(4, len(other_msgs))
            if len(other_msgs) <= fallback_keep:
                print(Color.info(f"[System] History too short to compress ({len(other_msgs)} messages)."))
                return messages
            recent_msgs = other_msgs[-fallback_keep:]
            old_msgs = other_msgs[:-fallback_keep]
            print(Color.info(f"[System] Single-turn fallback: compressing {len(old_msgs)} messages, keeping {len(recent_msgs)}"))
    else:
        # Legacy message-based protection (for backward compatibility)
        if keep_recent is None:
            keep_recent = config.COMPRESSION_KEEP_RECENT
        if len(other_msgs) <= keep_recent:
            print(Color.info(f"[System] History too short to compress ({len(other_msgs)} <= {keep_recent} recent)."))
            return messages

        recent_msgs = other_msgs[-keep_recent:]
        old_msgs = other_msgs[:-keep_recent]

        if not old_msgs:
            return messages

    # Choose compression mode
    mode = config.COMPRESSION_MODE.lower() if hasattr(config, "COMPRESSION_MODE") else "traditional"
    
    # Preservation of critical task state
    todo_preservation = []
    if todo_tracker:
        prompt = todo_tracker.get_continuation_prompt()
        if prompt:
            todo_preservation = [{"role": "system", "content": f"[Ongoing Task]: {prompt}"}]

    compressed = []
    if mode == "chunked":
        # Chunked compression (like Strix)
        print(Color.info(f"[System] Using chunked compression (chunk_size={config.COMPRESSION_CHUNK_SIZE})..."))
        compressed = _compress_chunked(old_msgs, instruction=instruction)
    else:
        # Default strategy: summarize all old messages into one
        compressed = [_compress_single(old_msgs, instruction=instruction)]

    # Construct new history: system + important + compressed + todo + recent
    new_history = system_msgs + important_msgs + compressed + todo_preservation + recent_msgs

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

    # Post-compact hook (with stats as environment variables, platform-aware)
    post_hook_path = _find_hook("post_compact")
    if post_hook_path and post_hook_path.exists():
        print(Color.info(f"[Hook] Running {post_hook_path.name}..."))
        try:
            env = os.environ.copy()
            env["BRIAN_OLD_MSGS"] = str(old_msg_count)
            env["BRIAN_NEW_MSGS"] = str(new_msg_count)
            env["BRIAN_OLD_TOKENS"] = str(current_tokens)
            env["BRIAN_NEW_TOKENS"] = str(new_tokens)
            env["BRIAN_REDUCTION_PCT"] = str(reduction_pct)

            subprocess.run(_hook_command(post_hook_path), env=env, timeout=10, check=False, shell=False)
        except subprocess.TimeoutExpired:
            print(Color.warning(f"[Hook] {post_hook_path.name} timed out (10s)"))
        except Exception as e:
            print(Color.warning(f"[Hook] {post_hook_path.name} failed: {e}"))

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

def process_observation(observation, messages, todo_tracker=None):
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
        messages = compress_history(messages, todo_tracker=todo_tracker, force=True, quiet=True)  # skip duplicate logs

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
    # RAG 도구 (disabled by default, set ENABLE_SMART_RAG=true to re-enable)
    # "rag_search",
    # "rag_status",
    # Verilog 분석 도구 (read-only)
    "analyze_verilog_module",
    "find_signal_usage",
    "find_module_definition",
    "extract_module_hierarchy",
    "find_potential_issues",
    "analyze_timing_paths",
}


def execute_actions_parallel(actions, tracker, agent_mode='normal'):
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
    for action in actions: 
        tool_name = action[0]
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
        for batch_idx, batch in enumerate(batches):
            if batch.parallel and len(batch.actions) > 1 and config.ENABLE_REACT_PARALLEL:
                # Parallel execution: Filter out blocked tools first
                allowed_actions = []
                for idx, tool_name, args_str in batch.actions:
                    # Plan mode gating in parallel batch
                    if agent_mode == 'plan_q':
                        observation = "[Plan Mode] Tool calls blocked. Ask clarifying questions first."
                        results.append((idx, tool_name, args_str, observation))
                    elif agent_mode == 'plan' and tool_name in config.PLAN_MODE_BLOCKED_TOOLS:
                        observation = f"[Plan Mode] '{tool_name}' is blocked. Only read/search tools are available."
                        results.append((idx, tool_name, args_str, observation))
                    else:
                        allowed_actions.append((idx, tool_name, args_str))

                if allowed_actions:
                    if config.DEBUG_MODE:
                        print(Color.info(f"  ⚡ Parallel batch: {len(allowed_actions)} action(s)"))
                    batch_results = _execute_batch_parallel(allowed_actions)
                    results.extend(batch_results)
            else:
                # Sequential execution
                for idx, tool_name, args_str in batch.actions:
                    # Plan mode gating in sequential batch
                    if agent_mode == 'plan_q':
                        observation = "[Plan Mode] Tool calls blocked. Ask clarifying questions first."
                    elif agent_mode == 'plan' and tool_name in config.PLAN_MODE_BLOCKED_TOOLS:
                        observation = f"[Plan Mode] '{tool_name}' is blocked. Only read/search tools are available."
                    else:
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

        for idx, action_tuple in enumerate(actions):
             # Unpack action tuple (tool, args, hint)
            if len(action_tuple) == 3:
                tool_name, args_str, hint = action_tuple
            else:
                tool_name, args_str = action_tuple

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


def _maybe_inject_exploration_strategy(messages, task_description):
    """
    Agent delegation 또는 탐색 요청에 대해 전략 주입

    1. Agent delegation: "task agent 써서", "explore agent로" 등 → 해당 agent에 위임
    2. Exploration: "analyze", "structure" 등 → 병렬 탐색 전략

    Returns:
        True if strategy was injected
        False otherwise
    """
    if not messages:
        return False

    user_query = messages[-1].get("content", "").lower()

    # 이미 주입되었는지 확인 (중복 방지)
    for msg in messages:
        if msg.get("role") == "system" and ("DELEGATION STRATEGY" in msg.get("content", "") or "EXPLORATION STRATEGY" in msg.get("content", "")):
            return False

    # === Priority 1: 명시적 agent delegation ===
    # "task agent 써서", "explore agent로", "plan agent를 사용" 등
    agent_types = ["task", "explore", "plan", "execute", "review"]
    detected_agent = None
    for agent_type in agent_types:
        patterns = [
            f"{agent_type} agent",
            f"{agent_type} 에이전트",
            f"{agent_type}agent",
        ]
        if any(p in user_query for p in patterns):
            detected_agent = agent_type
            break

    if detected_agent:
        strategy = f"""=== DELEGATION STRATEGY ===

The user wants to use the **{detected_agent}** agent. Delegate the entire task:

**Execute {detected_agent} agent (foreground, synchronous):**
Thought: Delegating to {detected_agent} agent.
Action: background_task(agent="{detected_agent}", prompt="{task_description}", foreground="true")

**Rules:**
- foreground="true" runs the agent synchronously — result is returned directly
- Do NOT call background_output() — result is already in the response
- Do NOT do the work yourself — the {detected_agent} agent handles everything
- After receiving the result, summarize it for the user
==="""
        messages.append({"role": "system", "content": strategy})
        print(Color.info("[META] Agent delegation strategy injected"))
        print(Color.info(f"[System] 🤖 Delegating to {detected_agent} agent...\n"))
        return True

    # Priority 2 제거됨 — 명시적 agent delegation만 지원
    return False


def _sys_content_append(msg, text):
    """Append text to system message content (handles str and list formats)."""
    if isinstance(msg["content"], str):
        msg["content"] += text
    elif isinstance(msg["content"], list):
        for block in msg["content"]:
            if isinstance(block, dict) and block.get("type") == "text":
                block["text"] += text
                return


def _sys_content_strip_plan(msg):
    """Remove PLAN MODE section from system message content (handles str and list formats)."""
    if isinstance(msg["content"], str):
        msg["content"] = msg["content"].split("\n\n=== PLAN MODE ===")[0]
    elif isinstance(msg["content"], list):
        for block in msg["content"]:
            if isinstance(block, dict) and block.get("type") == "text":
                block["text"] = block["text"].split("\n\n=== PLAN MODE ===")[0]
                return


def run_react_agent(messages, tracker, task_description, mode='interactive', preface_enabled=True, agent_mode='normal', todo_tracker=None):
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
    recovery_attempts = 0  # Track recovery attempts
    final_answer_attempts = 0  # Track think-only → final answer injection attempts

    # Initialize action tracking for procedural memory
    actions_taken = []

    # ACE Credit Assignment: Track referenced node IDs from Deep Think
    referenced_node_ids = []

    # Todo Tracking System (Phase 2 - Claude Code Style)
    if config.ENABLE_TODO_TRACKING:
        todo_tracker = TodoTracker.load(Path(config.TODO_FILE))
    else:
        todo_tracker = None

    # ============================================================
    # Phase 2: Agent Communication - Accumulated Context
    # ============================================================
    accumulated_context = {
        'explored_files': [],      # Files examined by spawn_explore
        'planned_steps': [],       # Steps from spawn_plan
        'agent_artifacts': {},     # Other agent results
        'exploration_summaries': [],  # Brief summaries from explore
        'plan_summaries': []       # Brief summaries from plan
    }

    # ============================================================
    # Priority 1: Explicit agent delegation
    # ============================================================
    if preface_enabled:
        if _maybe_inject_exploration_strategy(messages, task_description):
            print(Color.info("[System] Agent delegation strategy injected.\n"))

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

    # (delegation/exploration strategy injection moved above Claude Flow check)

    # Start ESC key watcher for loop abort
    from lib.display import EscapeWatcher
    EscapeWatcher.start()

    while True:
        # Check ESC key abort
        if EscapeWatcher.check():
            print(Color.warning("\n  ⎋ Aborted by ESC. Returning to input prompt."))
            break

        # Check iteration limit with progressive warning
        warning_action = show_iteration_warning(tracker, mode=mode)
        if warning_action == 'stop':
            break
        elif warning_action == 'extend':
            tracker.extend(20)

        # Context Management: Compress if needed
        messages = compress_history(messages, todo_tracker=todo_tracker)

        # Smart RAG: Refresh system prompt with current context
        # This enables dynamic RAG context injection based on latest user message
        # Refresh on every iteration to find new relevant context as conversation progresses
        if config.ENABLE_SMART_RAG or config.DEBUG_MODE or config.ENABLE_SKILL_SYSTEM:
            # Only refresh if there's a new user message since last refresh
            user_messages = [m for m in messages if m.get("role") == "user"]
            current_query = user_messages[-1].get("content", "")[:100] if user_messages else ""
            
            # Check if query changed or first iteration
            last_rag_query = getattr(tracker, '_last_rag_query', None)
            if tracker.current == 0 or current_query != last_rag_query:
                tracker._last_rag_query = current_query
                
                # Legacy PCIe indexing removed - strictly use .ragconfig now
                pass

                system_prompt_data = build_system_prompt(messages, allowed_tools=set(tools.AVAILABLE_TOOLS.keys()), agent_mode=agent_mode)
                # Update system message if it exists
                if messages and messages[0].get("role") == "system":
                    if config.CACHE_OPTIMIZATION_MODE == "optimized" and isinstance(system_prompt_data, dict):
                        # Optimized mode: Multi-block format for cache efficiency
                        blocks = []

                        # Static block (always cached - base prompt + tools)
                        if system_prompt_data.get("static"):
                            blocks.append({
                                "type": "text",
                                "text": system_prompt_data["static"],
                                "cache_control": {"type": "ephemeral"}
                            })

                        # Dynamic block (no caching - RAG/Graph/Memory context changes per iteration)
                        if system_prompt_data.get("dynamic"):
                            blocks.append({
                                "type": "text",
                                "text": system_prompt_data["dynamic"]
                            })

                        messages[0]["content"] = blocks if blocks else system_prompt_data.get("static", "")

                        if config.DEBUG_MODE:
                            print(Color.info(f"[CACHE] Optimized mode: {len(blocks)} block(s) configured"))
                    else:
                        # Legacy mode: Single string
                        messages[0]["content"] = system_prompt_data

        # Phase 2: Inject Accumulated Context into system message
        if accumulated_context and any(accumulated_context.values()):
            context_summary = []

            if accumulated_context.get('explored_files'):
                files = accumulated_context['explored_files']
                context_summary.append(f"📁 Files examined by agents: {len(files)} files")
                if len(files) <= 10:
                    context_summary.append(f"   {', '.join(files)}")

            if accumulated_context.get('planned_steps'):
                steps = accumulated_context['planned_steps']
                context_summary.append(f"📋 Planned steps: {len(steps)} steps")
                if len(steps) <= 5:
                    for idx, step in enumerate(steps, 1):
                        context_summary.append(f"   {idx}. {step}")

            if accumulated_context.get('exploration_summaries'):
                summaries = accumulated_context['exploration_summaries']
                context_summary.append(f"🔍 Exploration insights: {len(summaries)} summary(ies)")

            if context_summary:
                context_msg = "\n\n[Agent Communication Context]\n" + "\n".join(context_summary)

                if config.CACHE_OPTIMIZATION_MODE == "optimized" and isinstance(messages[0].get("content"), list):
                    # Add to dynamic block
                    messages[0]["content"].append({
                        "type": "text",
                        "text": context_msg
                    })
                elif isinstance(messages[0].get("content"), str):
                    # Append to string
                    messages[0]["content"] += context_msg

                if config.DEBUG_MODE:
                    print(Color.info(f"[CONTEXT] Injected accumulated context: {len(context_summary)} items"))

        # Hook: BEFORE_LLM_CALL (context pruning, compression check, skill activation)
        if hook_registry:
            hook_ctx = HookContext(
                messages=messages,
                max_context_chars=config.MAX_CONTEXT_CHARS,
                compression_threshold=getattr(config, 'CONTEXT_COMPRESSION_THRESHOLD', 0.80),
                iteration=tracker.current,
                metadata={"todo_tracker": todo_tracker} if todo_tracker else {},
            )
            hook_ctx = hook_registry.run(HookPoint.BEFORE_LLM_CALL, hook_ctx)
            messages = hook_ctx.messages

            # Handle compression flag from PreemptiveCompactor
            if hook_ctx.metadata.get("compression_needed"):
                if config.DEBUG_MODE:
                    usage_pct = hook_ctx.metadata.get("context_usage_pct", 0)
                    print(Color.warning(f"  [Hook] Context at {usage_pct:.1f}% - triggering compression"))
                messages = compress_history(messages, todo_tracker=todo_tracker, force=True)

            if hook_ctx.metadata.get("pruned_messages"):
                pruned = hook_ctx.metadata["pruned_messages"]
                if config.DEBUG_MODE:
                    print(Color.info(f"  [Hook] Pruned {pruned} redundant messages"))

        # Show context usage before each iteration
        if config.DEBUG_MODE or tracker.current == 0:
            show_context_usage(messages)

        # Show flow stage: LLM Call
        if config.DEBUG_MODE:
            llm_start_time = time.time()
            user_msgs = len([m for m in messages if m.get('role') == 'user'])
            asst_msgs = len([m for m in messages if m.get('role') == 'assistant'])
            sys_msgs = len([m for m in messages if m.get('role') == 'system'])
            print(Color.system(f"[FLOW] Stage 1: LLM Call"))
            print(Color.system(f"[FLOW]   Messages: user:{user_msgs} assistant:{asst_msgs} system:{sys_msgs} total:{len(messages)}"))
            
        from lib.display import format_iteration_header, Spinner
        print(format_iteration_header(tracker.current + 1, tracker.max_iterations, agent_name="primary", model=config.MODEL_NAME), flush=True)

        # ── Streaming display ──
        # Design: 3 states (NOISE → CONTENT → ACTION), 3 filters (think, dedup, width)
        #
        # States:
        #   NOISE   — before first meaningful line (Thought/Action/#header). Suppress all.
        #   CONTENT — displaying Thought/text. Show with dedup.
        #   ACTION  — after Action: detected. Suppress all (tool UI handles display).
        #
        # Filters:
        #   1. <think>...</think> — stripped before state machine
        #   2. Dedup — intra-line (50-char sliding window) + inter-line (set + substring)
        #   3. Terminal width cap — partial display only
        #
        import shutil
        _TERM_W = shutil.get_terminal_size().columns - 4
        _NOISE, _CONTENT, _ACTION = 0, 1, 2

        _stop_seqs = ["Observation:", "<|call|>", "tool_call_begin", "tool_calls_section_begin", "<|tool_call|>", "<tool_call>"]
        _stream_start = time.time()
        collected_content = ""
        _buf = ""           # incomplete line buffer
        _state = _NOISE
        _aborted = False
        _in_think = False
        _seen = set()       # printed lines for dedup
        _last_partial = ""  # last partial line displayed (avoid duplicate \r writes)

        def _dedup_line(text):
            """Remove intra-line repetition (50-char sliding window)."""
            if len(text) < 100:
                return text
            for i in range(min(len(text) // 2, 600)):
                seg = text[i:i + 50]
                if len(seg) < 50:
                    break
                j = text.find(seg, i + 50)
                if j > i:
                    return text[:j].rstrip()
            return text

        def _is_dup(text):
            """Check if text was already printed (exact or substring with 70% overlap)."""
            if text in _seen:
                return True
            if len(text) > 60:
                for prev in _seen:
                    shorter, longer = (text, prev) if len(text) <= len(prev) else (prev, text)
                    if len(shorter) > len(longer) * 0.7 and shorter in longer:
                        return True
            return False

        _content_emitted = False  # tracks whether any response text was actually printed

        def _emit(text):
            """Print a completed line with dedup."""
            nonlocal _content_emitted
            text = _dedup_line(text)
            if not _is_dup(text):
                sys.stdout.write(f"\r\033[2K  {text}\n")
                sys.stdout.flush()
                _seen.add(text)
                _content_emitted = True

        def _strip_think(text):
            """Remove <think> tags, return (cleaned_text, entered_think, exited_think, reasoning_text)."""
            nonlocal _in_think
            parts = re.split(r'(</?think>)', text)
            clean_parts = []
            reasoning_parts = []
            entered_here = False
            exited_here = False
            for p in parts:
                if p == "<think>":
                    _in_think = True
                    entered_here = True
                elif p == "</think>":
                    _in_think = False
                    exited_here = True
                elif p:
                    if _in_think:
                        reasoning_parts.append(p)
                    else:
                        clean_parts.append(p)
            return "".join(clean_parts), entered_here, exited_here, "".join(reasoning_parts)

        # ── Thinking spinner (disabled in Debug Mode to prevent output artifacts) ──
        _thinking_spinner = None
        if not config.DEBUG_MODE:
            _thinking_spinner = Spinner("Thinking")
            _thinking_spinner.start()
        _thinking_stopped = False

        try:
            for chunk in chat_completion_stream(messages, stop=_stop_seqs):
                if not _thinking_stopped and _thinking_spinner:
                    _elapsed_think = time.time() - _stream_start
                    _thinking_spinner.stop()
                    sys.stderr.write(f"  \033[36m✽\033[0m \033[2mThinking... (Done {_elapsed_think:.1f}s)\033[0m\n")
                    sys.stderr.flush()
                    _thinking_stopped = True

                if EscapeWatcher.check():
                    _aborted = True
                    break

                collected_content += chunk

                if config.DEBUG_MODE:
                    continue

                _buf += chunk

                # ── Process complete lines ──
                while '\n' in _buf:
                    raw_line, _buf = _buf.split('\n', 1)
                    # Ensure trailing newline if we streamed anything.
                    # Track whether this line was already partially shown (streaming effect).
                    _line_was_partial = _content_emitted
                    _content_emitted = False
                    # Merge tokenization-split fragments: if raw_line is a short lowercase
                    # fragment (e.g. "c" split from "code inspection."), re-attach to next line
                    _stripped = raw_line.strip()
                    if _stripped and len(_stripped) <= 3 and _stripped.islower() and '\n' in _buf:
                        _buf = _stripped + _buf
                        continue
                    text, entered, exited, reasoning = _strip_think(raw_line)

                    if _in_think and not exited:
                        continue
                    if not text:
                        if _state == _CONTENT:
                            sys.stdout.write(f"\r\033[2K\n")
                            sys.stdout.flush()
                        continue

                    # Detect Thought: / Action: anywhere in line (case-insensitive for glm-4.7)
                    _text_lower = text.lower()
                    ai = _text_lower.find('action:')
                    # Also catch bare "Action" line (some models omit the colon)
                    if ai < 0 and _text_lower.strip() == 'action':
                        ai = 0
                    ti = _text_lower.find('thought:')

                    if ai >= 0 and (ti < 0 or ai < ti):
                        # → ACTION state
                        if _state != _ACTION:
                            sys.stdout.write(f"\r\033[2K")
                            sys.stdout.flush()
                        _state = _ACTION

                    elif ti >= 0:
                        # Thought line
                        thought = text[ti + 8:]
                        if thought and not _is_dup(thought):
                            sys.stdout.write(f"\r\033[2K  {Color.CYAN}Thought:{Color.RESET}{thought}\n")
                            sys.stdout.flush()
                            _seen.add(thought)
                        _state = _CONTENT

                    elif _state == _NOISE or _state == _ACTION:
                        # NOISE: only markdown headers break out
                        # ACTION: suppress non-Thought/Action lines
                        if _state == _NOISE and text.startswith('#'):
                            _state = _CONTENT
                            _emit(text)

                    else:
                        # CONTENT state — normal text
                        if _line_was_partial:
                            # Overwrite the truncated partial with the full completed line
                            text = _dedup_line(text)
                            if not _is_dup(text):
                                sys.stdout.write(f"\r\033[2K  {text}\n")
                                sys.stdout.flush()
                                _seen.add(text)
                            else:
                                sys.stdout.write(f"\r\033[2K\n")
                                sys.stdout.flush()
                        else:
                            _emit(text)

                # ── Partial line display (typing effect) ──
                if _state == _CONTENT and not _in_think and _buf:
                    # Correctly strip reasoning from partial buffer for display
                    p = ""
                    _tmp_in_think = _in_think
                    for _p in re.split(r'(</?think>)', _buf):
                        if _p == "<think>": _tmp_in_think = True
                        elif _p == "</think>": _tmp_in_think = False
                        elif not _tmp_in_think: p += _p
                    p = p.rstrip()
                    # If Action: appears mid-line (no newline before it), show only preceding text
                    _ai_mid = p.lower().find('action:')
                    if _ai_mid > 0:
                        p = p[:_ai_mid].rstrip()
                        if p != _last_partial:  # skip if content unchanged
                            sys.stdout.write(f"\r\033[2K  {p}")
                            sys.stdout.flush()
                            _last_partial = p
                            _content_emitted = True

        except Exception as e:
            if not _thinking_stopped:
                _thinking_spinner.stop()
            if not collected_content:
                print(Color.error(f"\n  LLM call failed: {e}"))
                break

        # Clean up partial line display
        if not config.DEBUG_MODE and _state != _ACTION:
            remaining = _buf.strip() if _buf else ""
            if remaining:
                text, entered, exited, reasoning = _strip_think(remaining)
                # Ensure we handle any leftover reasoning if we just exited think
                if exited and reasoning:
                    # just drop it or handle it... streaming already handled it if in real-time
                    pass
                
                # Truncate at Action: if present (stream ended without \n before Action:)
                _ai_end = text.lower().find('action:')
                if _ai_end == 0:
                    text = ""  # starts with Action: — suppress entirely
                elif _ai_end > 0:
                    text = text[:_ai_end].rstrip()
                
                if text:
                    _emit(text)
                else:
                    sys.stdout.write(f"\r\033[2K")
            else:
                sys.stdout.write(f"\r\033[2K")
            sys.stdout.flush()

        llm_elapsed = time.time() - _stream_start

        if _aborted:
            print(Color.warning("\n  ⎋ Aborted by ESC. Returning to input prompt."))
            break

        # Strip any leaked native tool call tokens from content
        collected_content = _strip_native_tool_tokens(collected_content)

        # Strip <think>...</think> reasoning tokens before storing in history
        # Reasoning is for display only — storing it inflates context unnecessarily
        collected_content = re.sub(r'<think>.*?</think>', '', collected_content, flags=re.DOTALL).strip()

        # Strip echoed system prompt fragments before first Thought:/Action:
        # Some models (GLM 4.7) echo tail of system prompt at response start
        import re as _re
        _first_marker = _re.search(r'^(Thought:|Action:)', collected_content, _re.MULTILINE)
        if _first_marker and _first_marker.start() > 0:
            prefix = collected_content[:_first_marker.start()]
            # Only strip if prefix looks like noise (no newlines = single fragment)
            if '\n' not in prefix.strip():
                collected_content = collected_content[_first_marker.start():]

        # Show summary line (streaming already displayed the Thought in real-time)
        if not config.DEBUG_MODE:
            elapsed_str = f"{llm_elapsed:.1f}s" if llm_elapsed < 60 else f"{int(llm_elapsed//60)}m{int(llm_elapsed%60):02d}s"
            _fk = lambda n: f"{n/1000:.1f}k" if n >= 1000 else str(n)
            _in = llm_client.last_input_tokens
            _out = llm_client.last_output_tokens
            if _in > 0 and _out > 0:
                token_str = f"in {_fk(_in)} · out {_fk(_out)} · sum {_fk(_in + _out)}"
            else:
                token_est = len(collected_content) // 4
                token_str = f"~{_fk(token_est)}"
            print(f"  {Color.DIM}✽ {elapsed_str} · {token_str} tokens{Color.RESET}")
        
        # Ensure newline after response before debug info
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

        # Add assistant response to history with token metadata and turn tracking
        global current_turn_id
        assistant_msg = {
            "role": "assistant",
            "content": collected_content,
            "turn_id": current_turn_id,  # Same turn as user message
            "timestamp": time.time()
        }

        # Attach actual token usage from API if available
        usage = llm_client.get_last_usage()
        if usage:
            assistant_msg["_tokens"] = usage  # Store as metadata

        messages.append(assistant_msg)

        # Hook: AFTER_LLM_CALL (todo continuation check)
        if hook_registry:
            hook_ctx = HookContext(
                messages=messages,
                iteration=tracker.current,
                metadata={"todo_tracker": todo_tracker} if todo_tracker else {},
            )
            hook_ctx = hook_registry.run(HookPoint.AFTER_LLM_CALL, hook_ctx)
            messages = hook_ctx.messages

        # Check for Action first (needed for TodoWrite explicit call detection)
        actions = parse_all_actions(collected_content)

        # Todo tracking: supports explicit tool calls AND markdown auto-parsing
        markdown_tasks = _parse_todo_markdown(collected_content)
        if markdown_tasks and not any(a[0] == 'todo_write' for a in actions):
            # Auto-generate todo_write action if markdown plan detected but no explicit tool call
            # This ensures the visual progress tracker appears even without the tool
            _todo_write_func = tools.AVAILABLE_TOOLS.get('todo_write')
            if _todo_write_func:
                observation = _todo_write_func(markdown_tasks)
                # Display it as if the assistant called it
                print(format_tool_header("todo_write", "Auto-parsed from markdown plan"))
                print(format_tool_result(observation, max_lines=1000, max_chars=100000))
        # (no auto-parsing from numbered lists)

        # Check for explicit completion signal
        # Skip if there are pending actions to execute (agent isn't done yet)
        if not actions and detect_completion_signal(collected_content):
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
            # Plan Mode Safety: If todo_write is called in plan mode, it must be the ONLY tool in the batch.
            # This prevents bypassing the confirmation prompt by bundling modifications with plan creation.
            _todo_ops = {'todo_write', 'todo_update', 'todo_add', 'todo_remove'}
            _has_todo_op = any(a[0] in _todo_ops for a in actions)
            _is_todo_write = any(a[0] == 'todo_write' for a in actions)
            if _has_todo_op and agent_mode in ('plan', 'plan_q'):
                # Filter to only FIRST todo op to force clean transition
                _todo_action = next(a for a in actions if a[0] in _todo_ops)
                if len(actions) > 1:
                    print(Color.warning(f"  [System] ⚠️  Todo operation detected in Plan Mode. Bundled actions deferred until plan confirmation."))
                actions = [_todo_action]

            combined_results = []

            # Todo Tracking: Mark current step as in_progress (Phase 2)
            if todo_tracker is not None and todo_tracker.get_current_todo():
                current_todo = todo_tracker.get_current_todo()
                print(Color.system(f"▶️ {current_todo.active_form}..."))

            # Show flow stage
            if config.DEBUG_MODE:
                print(Color.system(f"  ┌─ FLOW: Parse → Found {len(actions)} action(s)"))

            # Single action warning removed — too noisy for normal usage

            from lib.display import format_tool_header, format_tool_result, format_tool_brief, _extract_tool_args_summary, _friendly_tool_name, Spinner

            if len(actions) > 1 and config.ENABLE_REACT_PARALLEL:
                print(Color.DIM + f"  ⚡ {len(actions)} actions (parallel)" + Color.RESET)
                action_results = execute_actions_parallel(actions, tracker, agent_mode=agent_mode)

                for idx, tool_name, args_str, observation in action_results:
                    summary = _extract_tool_args_summary(tool_name, args_str)

                    # Error detection
                    obs_lower = observation.lower()
                    is_error = any(indicator in obs_lower for indicator in
                                  ['error:', 'exception:', 'traceback', 'syntax error', 'compilation failed'])
                    if tool_name in ['read_file', 'read_lines', 'grep_file'] and "error" in obs_lower:
                        if not observation.strip().lower().startswith("error:"):
                            is_error = False

                    # Record action for procedural memory
                    if procedural_memory is not None:
                        action_result = "error" if is_error else "success"
                        action_obj = Action(
                            tool=tool_name,
                            args=args_str[:100],
                            result=action_result,
                            observation=observation[:200]
                        )
                        actions_taken.append(action_obj)

                    # Tool display: header + inline brief on same line
                    _INLINE_TOOLS = {'read_file', 'read_lines', 'grep_file', 'find_files', 'list_dir', 'git_diff', 'git_status', 'write_file'}
                    if tool_name == 'background_task' and not config.DEBUG_MODE:
                        pass  # handoff line already printed by background_task()
                    elif tool_name in _INLINE_TOOLS and not config.DEBUG_MODE:
                        _is_sys_msg = observation and any(
                            observation.startswith(p) for p in ('[Plan Mode]', '[System]', '[Error')
                        )
                        if _is_sys_msg:
                            print(format_tool_header(tool_name, summary))
                            print(format_tool_result(observation))
                        else:
                            brief = format_tool_brief(tool_name, args_str, observation)
                            header = format_tool_header(tool_name, summary)
                            print(f"{header}  {Color.DIM}({brief}){Color.RESET}")
                    elif tool_name in ['replace_in_file', 'replace_lines']:
                        print(format_tool_header(tool_name, summary))
                        print(format_tool_result(observation, max_lines=1000, max_chars=100000))
                    elif tool_name in ['todo_write', 'todo_update', 'todo_add', 'todo_remove', 'todo_status']:
                        print(format_tool_header(tool_name, summary))
                        print(format_tool_result(observation, max_lines=1000, max_chars=100000))
                    elif tool_name == 'spec_navigate':
                        print(format_tool_header(tool_name, summary))
                        print(format_tool_result(observation, max_lines=50, max_chars=5000))
                    else:
                        print(format_tool_header(tool_name, summary))
                        print(format_tool_result(observation))

                    combined_results.append(f"--- [Action {idx+1}] {tool_name} ---\n{observation}")
            else:
                for i, action_tuple in enumerate(actions):
                    # Check ESC between tool executions
                    if EscapeWatcher.check():
                        break

                    if len(action_tuple) == 3:
                        tool_name, args_str, hint = action_tuple
                    else:
                        tool_name, args_str = action_tuple
                        hint = None

                    if config.DEBUG_MODE:
                        tool_start_time = time.time()

                    summary = _extract_tool_args_summary(tool_name, args_str)

                    # Run tool with spinner for slow tools (run_command, rag_*, background_*)
                    _SLOW_TOOLS = {'run_command', 'background_task', 'background_output'}
                    _PRE_HEADER_TOOLS = {'spec_search'}
                    tracker.record_tool(tool_name)
                    tool_start = time.time()
                    # Print header before execution for tools that emit progress lines
                    if tool_name in _PRE_HEADER_TOOLS and not config.DEBUG_MODE:
                        print(format_tool_header(tool_name, summary))
                    # Plan mode tool gating
                    _PLAN_READONLY_TOOLS = frozenset({
                        'list_dir', 'read_file', 'read_lines', 'grep_file', 'find_files',
                        'git_status', 'git_diff',
                        'todo_write', 'todo_update', 'todo_add', 'todo_remove', 'todo_status',
                    })
                    if agent_mode == 'plan_q' and tool_name not in _PLAN_READONLY_TOOLS:
                        # First clarification turn: only read-only tools allowed
                        observation = (
                            f"[Plan Mode] '{tool_name}' is blocked during clarification. "
                            "Only read-only tools are allowed (list_dir, read_file, grep_file, find_files, etc.). "
                            "Ask the user clarifying questions first."
                        )
                    elif agent_mode == 'plan' and tool_name in config.PLAN_MODE_BLOCKED_TOOLS:
                        observation = (
                            f"[Plan Mode] '{tool_name}' is blocked. "
                            "Only read/search tools are available (read_file, read_lines, grep_file, find_files). "
                            "Clarify requirements with the user, then call todo_write() when confirmed."
                        )
                    elif tool_name in _SLOW_TOOLS and not config.DEBUG_MODE:
                        friendly = _friendly_tool_name(tool_name)
                        with Spinner(f"Running {friendly}"):
                            observation = execute_tool(tool_name, args_str)
                    else:
                        observation = execute_tool(tool_name, args_str)
                    tool_elapsed = time.time() - tool_start

                    if config.DEBUG_MODE:
                        print(format_tool_header(tool_name, summary))
                        print(Color.DIM + f"  │ {tool_elapsed:.2f}s" + Color.RESET)

                    # Warn about lint errors detected in this turn (append to completed observation)
                    if tool_name == 'todo_update' and 'completed' in args_str:
                        _has_lint_errors = any(
                            "❌" in r and ("error" in r.lower() or "linting" in r.lower())
                            for r in combined_results
                        )
                        if _has_lint_errors:
                            observation += "\n⚠️ LINT ERRORS detected — fix before approving."

                    # Error detection
                    obs_lower = observation.lower()
                    is_error = any(indicator in obs_lower for indicator in
                                  ['error:', 'exception:', 'traceback', 'syntax error', 'compilation failed'])
                    if tool_name in ['read_file', 'read_lines', 'grep_file'] and "error" in obs_lower:
                        if not observation.strip().lower().startswith("error:"):
                            is_error = False

                    # Record action for procedural memory
                    if procedural_memory is not None:
                        action_result = "error" if is_error else "success"
                        action_obj = Action(
                            tool=tool_name,
                            args=args_str[:100],
                            result=action_result,
                            observation=observation[:200]
                        )
                        actions_taken.append(action_obj)
                    
                    # Tool display: header + inline brief + elapsed on same line
                    _INLINE_TOOLS = {'read_file', 'read_lines', 'grep_file', 'find_files', 'list_dir', 'git_diff', 'git_status', 'write_file', 'todo_write', 'todo_update', 'todo_add', 'todo_remove'}
                    elapsed_suffix = f" · {tool_elapsed:.1f}s" if tool_elapsed >= 1.0 else ""
                    if tool_name == 'background_task' and not config.DEBUG_MODE:
                        pass  # handoff line already printed by background_task()
                    elif tool_name in ['replace_in_file', 'replace_lines']:
                        if not config.DEBUG_MODE:
                            print(format_tool_header(tool_name, summary))
                        print(format_tool_result(observation, max_lines=1000, max_chars=100000))
                    elif not config.DEBUG_MODE:
                        if tool_name == 'todo_write' and agent_mode in ('plan', 'plan_q'):
                            # In plan mode: show full todo list so user can review before confirming
                            print(format_tool_header(tool_name, summary))
                            print(format_tool_result(observation, max_lines=1000, max_chars=100000))
                        elif tool_name == 'todo_update':
                            # Always show full progress table after every todo_update
                            print(format_tool_header(tool_name, summary))
                            print(format_tool_result(observation, max_lines=1000, max_chars=100000))
                        elif tool_name in _INLINE_TOOLS:
                            brief = format_tool_brief(tool_name, args_str, observation)
                            header = format_tool_header(tool_name, summary)
                            # Ensure tool header is on a new line
                            print(f"{header}  {Color.DIM}({brief}{elapsed_suffix}){Color.RESET}")
                        elif tool_name in _PRE_HEADER_TOOLS:
                            # Header already printed before execution; only show result
                            print(format_tool_result(observation))
                        elif tool_name == 'spec_navigate':
                            print(format_tool_header(tool_name, summary))
                            print(format_tool_result(observation, max_lines=50, max_chars=5000))
                        else:
                            print(format_tool_header(tool_name, summary))
                            print(format_tool_result(observation))

                    # [Context Optimization] Truncate successful write results for LLM context
                    agent_observation = observation
                    _WRITE_TOOLS = {'write_to_file', 'replace_file_content', 'multi_replace_file_content', 'replace_in_file', 'replace_lines', 'todo_write'}
                    if tool_name in _WRITE_TOOLS and not is_error:
                        _obs_lines = observation.splitlines()
                        if len(_obs_lines) > 5:
                            agent_observation = "\n".join(_obs_lines[:5]) + "\n\n(Remaining output truncated for brevity. Use read_file to verify if needed.)"

                    combined_results.append(f"--- [Action {i+1}] {tool_name} ---\n{agent_observation}")


                    # [Step Review] todo_update(completed) logic already handled above

            # Combine all observations
            observation = "\n\n".join(combined_results)

            # Step-by-Step Safety: Break loop after todo_write to allow user to see/confirm the plan.
            # Other todo operations during execution (like todo_update) no longer break.
            if _is_todo_write:
                break

            # Check consecutive errors using the combined observation
            if observation == last_error_observation:
                consecutive_errors += 1
                print(Color.warning(f"  [System] ⚠️  Consecutive error #{consecutive_errors}/{MAX_CONSECUTIVE_ERRORS}"))

                # Try recovery if enabled (2+ consecutive errors and haven't exceeded max attempts)
                global current_recovery_point, session_manager, current_session_id
                if (consecutive_errors >= 2 and
                    recovery_attempts < config.MAX_RECOVERY_ATTEMPTS and
                    config.ENABLE_SESSION_RECOVERY and
                    current_recovery_point and
                    session_manager):

                    recovery_attempts += 1
                    print(Color.warning(
                        f"\n[Recovery] Attempt {recovery_attempts}/{config.MAX_RECOVERY_ATTEMPTS}: "
                        f"Rolling back to recovery point..."
                    ))

                    # Rollback
                    try:
                        success = session_manager.recovery.rollback_to_point(
                            current_session_id,
                            current_recovery_point
                        )

                        if success:
                            print(Color.success("[Recovery] Rollback successful. Retrying..."))
                            # Rollback messages to recovery point
                            messages = messages[:current_recovery_point.message_count]
                            consecutive_errors = 0  # Reset after successful rollback
                            # Continue to next iteration
                        else:
                            print(Color.error("[Recovery] Rollback failed."))
                    except Exception as e:
                        print(Color.error(f"[Recovery] Rollback error: {e}"))

                # If max consecutive errors reached and no recovery or recovery failed
                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    print(Color.error(f"  [System] ❌ Same error occurred {MAX_CONSECUTIVE_ERRORS} times. Session recovery failed."))

                    # Offer user choices (simple text prompt)
                    if config.ENABLE_SESSION_RECOVERY and current_recovery_point:
                        print(Color.warning("\n복구 옵션을 선택하세요:"))
                        print("  1. 마지막 복구 지점부터 계속")
                        print("  2. 새 세션 시작")
                        print("  3. 종료")

                        try:
                            choice = input(Color.info("\n선택 (1-3): ")).strip()

                            if choice == "1":
                                print(Color.info("[System] 복구 지점부터 계속합니다..."))
                                messages = messages[:current_recovery_point.message_count]
                                consecutive_errors = 0
                                recovery_attempts = 0
                                # Continue loop
                            elif choice == "2":
                                print(Color.info("[System] 새 세션을 시작합니다..."))
                                # Create new session
                                session = session_manager.create_session(
                                    directory=str(Path.cwd()),
                                    title=f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                                )
                                current_session_id = session.id
                                # Reset everything
                                messages = [{"role": "system", "content": _build_system_prompt_str()}]
                                consecutive_errors = 0
                                recovery_attempts = 0
                                # Continue loop
                            else:
                                print(Color.info("[System] 종료합니다."))
                                break
                        except (KeyboardInterrupt, EOFError):
                            print(Color.info("\n[System] 종료합니다."))
                            break
                    else:
                        # No recovery available, just stop
                        messages.append({
                            "role": "user",
                            "content": f"Observation: {observation}\n\n[System] The same error occurred {MAX_CONSECUTIVE_ERRORS} times consecutively. Please ask the user for help or try a different approach."
                        })
                        break
            else:
                consecutive_errors = 0
                recovery_attempts = 0  # Reset recovery attempts on success
                last_error_observation = observation if "error" in observation.lower() else None

            # Process observation (handles large files and context management)
            # End of tool execution block. Reload todo_tracker from disk to pick up tool changes
            if config.ENABLE_TODO_TRACKING:
                todo_tracker = TodoTracker.load(Path(config.TODO_FILE))
                if config.DEBUG_MODE and tool_name in ('todo_update', 'todo_write', 'todo_add', 'todo_remove') and todo_tracker:
                    todo_tracker.print_debug_status()

            # Append only current step to observation (not full list)
            if todo_tracker and todo_tracker.todos:
                current_todo = todo_tracker.get_current_todo()
                total = len(todo_tracker.todos)
                # Only count 'approved' tasks because 'completed' tasks are still awaiting review
                # and should be considered the active / current operation in focus.
                completed = sum(1 for t in todo_tracker.todos if t.status == 'approved')
                if current_todo:
                    header_parts = [f"[Step {completed + 1}/{total}: {current_todo.content}]"]
                    if current_todo.rejection_reason:
                        header_parts.append(f"⚠️  Previously rejected: {current_todo.rejection_reason}")
                    if current_todo.detail:
                        header_parts.append(f"Detail: {current_todo.detail}")
                    if current_todo.criteria:
                        header_parts.append(f"Criteria: {current_todo.criteria}")
                    header_parts.append("→ 현재 목표를 염두에 두고 아래 결과를 해석할 것")
                    step_header = "\n".join(header_parts) + "\n\n"
                    observation = step_header + observation


            messages = process_observation(observation, messages, todo_tracker=todo_tracker)

            # Inject todo reminder after tool results so agent stays aware of progress
            # Skip injection when the last tool was a todo op — its return value already has guidance
            _last_tool_was_todo = tool_name in ('todo_update', 'todo_write', 'todo_add')
            if (todo_tracker and todo_tracker.todos
                    and not todo_tracker.is_all_processed()
                    and not _last_tool_was_todo):
                reminder = todo_tracker.get_continuation_prompt()
                if reminder:
                    # Deduplicate: Don't inject if the last user message already has it
                    last_content = messages[-1].get("content", "") if messages else ""
                    if reminder not in last_content:
                        messages.append({"role": "user", "content": reminder})
                        if config.DEBUG_MODE:
                            _rem_clean = reminder.replace('\n', ' ')
                            print(Color.info(f"  [Debug] Injected continuation: {_rem_clean}"))

            # Stall tracking (silent — logged but not shown to agent)
        else:
            # No action — check if todos remain
            if config.ENABLE_TODO_TRACKING:
                todo_tracker = TodoTracker.load(Path(config.TODO_FILE))

            if (todo_tracker and not todo_tracker.is_all_processed()
                    and todo_tracker.todos):
                if todo_tracker.check_stagnation(max_stagnation=3):
                    hint = todo_tracker.get_stagnation_hint()
                    print(Color.warning(f"[System] Todo stagnation detected (3x no progress)."))
                    print(Color.info(f"  {hint}"))
                    print(Color.warning("Stopping."))
                    break
                # Inject continuation reminder (ONLY if we didn't just complete a task in this turn)
                reminder = todo_tracker.get_continuation_prompt()
                if reminder:
                    # Deduplicate: Don't inject if the last user message already has it
                    last_content = messages[-1].get("content", "") if messages else ""
                    if reminder not in last_content:
                        # Logic check: If the last turn ended in a break due to _has_todo_op,
                        # this block might be reached in the next ReAct loop if user-input was empty.
                        messages.append({"role": "user", "content": reminder})
                        if config.DEBUG_MODE:
                            _rem_clean = reminder.replace('\n', ' ')
                            print(Color.info(f"  [Debug] Injected continuation (stale): {_rem_clean}"))
                    
                    approved_count = sum(1 for t in todo_tracker.todos if t.status == 'approved')
                    print(Color.info(f"[System] {approved_count}/{len(todo_tracker.todos)} todos approved — resuming..."))
                    # Don't break — continue loop
                else:
                    break
            else:
                # Check if response was think-only (no visible content)
                import re as _re2
                visible = _re2.sub(r'<think>.*?</think>', '', collected_content, flags=_re2.DOTALL).strip()
                if len(visible) < 10 and final_answer_attempts < 2:
                    final_answer_attempts += 1
                    messages.append({
                        "role": "user",
                        "content": "Please provide your final answer to the user based on your research so far."
                    })
                    print(Color.info(f"  [System] Think-only response detected — requesting final answer (attempt {final_answer_attempts}/2)"))
                    # continue loop to get final answer
                else:
                    # Fallback: print only if streaming did NOT already show content.
                    # Catches NOISE-state responses (no Thought: prefix) that were suppressed.
                    _has_react = any(m in visible for m in ('Thought:', 'Action:', 'Response:'))
                    if visible and not _has_react and not _content_emitted and not config.DEBUG_MODE:
                        print(f"  {visible}")
                    break

        # Increment iteration counter
        tracker.increment()

    # Stop ESC key watcher
    EscapeWatcher.stop()

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

    return messages, agent_mode


# --- 7. Main Loop ---

def chat_loop():
    # Initialize session manager (for recovery system)
    global session_manager, current_session_id, current_recovery_point

    if config.ENABLE_SESSION_RECOVERY and session_manager is None:
        try:
            session_manager = SessionManager()
            session = session_manager.create_session(
                directory=str(Path.cwd()),
                title=f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            current_session_id = session.id
            if config.DEBUG_MODE:
                print(Color.system(f"[System] Session ID: {current_session_id[:8]}"))
        except Exception as e:
            print(Color.warning(f"[System] Session manager initialization failed: {e}"))
            print(Color.warning("[System] Continuing without session recovery..."))
            session_manager = None

    # Default mode
    agent_mode = 'normal'

    # Try to load existing conversation history
    loaded_messages = load_conversation_history()
    if loaded_messages:
        messages = loaded_messages
        print(Color.system("[System] Resuming from previous conversation.\n"))
    else:
        messages = [
            {"role": "system", "content": _build_system_prompt_str(agent_mode=agent_mode)}
        ]

    # Initialize context tracker
    max_tokens = config.MAX_CONTEXT_CHARS // 4  # Convert chars to tokens
    context_tracker = get_context_tracker(max_tokens=max_tokens)

    # Update tracker with initial context
    # Note: System message includes base prompt + tools + memory + graph context
    if messages and messages[0].get("role") == "system":
        context_tracker.update_system_prompt(messages[0]["content"])

    # Rolling window (default disabled, set by /window N)
    rolling_window_size = 0
    full_messages = None  # Full history when rolling window is active

    # Auto-compression (default disabled, set by /compression N)
    auto_compression_threshold = 0

    # Agent mode: "normal" (default ReAct loop) or "plan" (explore→todo_write→compress)
    agent_mode = "normal"

    # Tools and memory are included in system message, so set to 0 to avoid double counting
    context_tracker.update_tools("")
    context_tracker.update_memory({})

    # Update messages tokens (exclude system message to avoid double counting)
    context_tracker.update_messages(messages, exclude_system=True)

    # .UPD_RULE.md — create default if missing
    _upd_rule_paths = [
        Path.home() / ".common_ai_agent" / ".UPD_RULE.md",  # global
        Path(__file__).parent.parent / ".UPD_RULE.md",       # project
    ]
    _upd_rule_default = (
        "# Update Rules\n\n"
        "Project-specific instructions for this AI agent.\n"
        "Add rules here to customize behavior for this project.\n\n"
        "## Examples\n"
        "- Always use Korean for responses\n"
        "- Follow PEP 8 for Python code\n"
        "- Use snake_case for variable names\n"
    )
    _any_upd_rule_exists = any(p.exists() for p in _upd_rule_paths)
    if not _any_upd_rule_exists:
        _default_path = _upd_rule_paths[1]  # project-level
        try:
            _default_path.parent.mkdir(parents=True, exist_ok=True)
            _default_path.write_text(_upd_rule_default, encoding="utf-8")
            print(Color.info(f"[System] Created default .UPD_RULE.md at {_default_path}"))
        except Exception as e:
            print(Color.warning(f"[System] Could not create .UPD_RULE.md: {e}"))
    else:
        _loaded = [str(p) for p in _upd_rule_paths if p.exists()]
        if config.DEBUG_MODE:
            print(Color.system(f"[System] .UPD_RULE.md loaded: {', '.join(_loaded)}"))

    # Perform Memory Healing (One-time check on startup)
    if config.ENABLE_GRAPH and graph_lite:
        graph_lite.heal_embeddings()

    # Compact startup banner
    from lib.display import format_startup_banner
    print(format_startup_banner(
        base_url=config.BASE_URL,
        model=config.MODEL_NAME,
        features={
            'rate_limit': config.RATE_LIMIT_DELAY,
            'max_iter': config.MAX_ITERATIONS,
            'cache': config.ENABLE_PROMPT_CACHING,
            'compress': config.ENABLE_COMPRESSION,
            'memory': config.ENABLE_MEMORY and memory_system,
            'rag': config.ENABLE_RAG_AUTO_INDEX,
        }
    ))

    # Show initial context usage
    show_context_usage(messages)

    # ACE Credit Assignment: Track conversation count for periodic curation
    conversation_count = 0
    # Todo tracker for UI confirmation checks
    todo_tracker_main = TodoTracker.load(Path(config.TODO_FILE)) if config.ENABLE_TODO_TRACKING else None

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


    # Deep Think removed (replaced by plan agent)

    # Initialize slash command registry
    slash_registry = get_slash_command_registry()

    is_first_turn = True

    # ── Multiline input setup ──
    _multiline_prompt = None
    if config.ENABLE_MULTILINE_INPUT:
        try:
            # Add vendored packages to path (use resolve() for absolute path on all platforms)
            _vendor_dir = str(Path(__file__).resolve().parent.parent / 'vendor')
            if _vendor_dir not in sys.path:
                sys.path.insert(0, _vendor_dir)
            from prompt_toolkit import PromptSession, ANSI

            _multiline_prompt = PromptSession(multiline=False)
            _prompt_text = ANSI(Color.user("> ") + Color.RESET)
        except Exception as e:
            print(Color.warning(f"  [Multiline] prompt_toolkit unavailable ({type(e).__name__}: {e}) — falling back to single-line input"))

    print(Color.info("\nType 'exit' or 'quit' to stop."))
    print(Color.info("Type /help for available slash commands.\n"))


    while True:
        try:
            if config.ENABLE_TODO_TRACKING:
                todo_tracker_main = TodoTracker.load(Path(config.TODO_FILE))

            if _multiline_prompt:
                is_plan_turn = (agent_mode in ('plan', 'plan_q'))
                
                if agent_mode == 'plan_q':
                    _plan_prompt = ANSI(Color.warning("Plan Mode ") + Color.CYAN + "> " + Color.RESET)
                    user_input = _multiline_prompt.prompt(_plan_prompt, multiline=False)
                elif agent_mode == 'plan':
                    _plan_prompt = ANSI(Color.warning("Plan Confirmation [y/yc/feedback] ") + Color.CYAN + "> " + Color.RESET)
                    user_input = _multiline_prompt.prompt(_plan_prompt, multiline=False)
                else:
                    user_input = _multiline_prompt.prompt(_prompt_text)
            else:
                is_plan_turn = (agent_mode in ('plan', 'plan_q'))
                
                if agent_mode == 'plan_q':
                    user_input = input(Color.warning("Plan Mode ") + Color.CYAN + "> " + Color.RESET)
                elif agent_mode == 'plan':
                    print(f"{Color.YELLOW}[Plan Mode]{Color.RESET} A plan is active. Confirm to execute or provide feedback.")
                    user_input = input(Color.warning("Plan Confirmation [y/yc/feedback] ") + Color.CYAN + "> " + Color.RESET)
                else:
                    user_input = input(Color.user("> ") + Color.RESET)
            if user_input.lower() in ["exit", "quit"]:
                break

            # Handle slash commands
            if user_input.startswith('/'):
                # Update context tracker with current state before executing /context
                if user_input.startswith('/context'):
                    # Update with latest messages
                    if messages and messages[0].get("role") == "system":
                        context_tracker.update_system_prompt(messages[0]["content"])
                    context_tracker.update_messages(messages, exclude_system=True)
                    # Store messages for verbose mode
                    context_tracker.messages = messages

                # Handle /skill commands for manual skill control
                if user_input.startswith('/skill ') or user_input.strip() == '/skill':
                    skill_arg = user_input[7:].strip() if len(user_input) > 7 else ""

                    try:
                        from core.skill_system import get_skill_registry
                        registry = get_skill_registry()

                        if skill_arg == "list" or skill_arg == "":
                            # List all available skills
                            all_skills = registry.list_skills()
                            print(Color.info("\n=== Available Skills ==="))
                            for skill_name in sorted(all_skills):
                                skill = registry.get_skill(skill_name)
                                if skill:
                                    priority_color = Color.CYAN if skill.priority >= 85 else Color.RESET
                                    print(f"  • {Color.BOLD}{skill_name}{Color.RESET} {priority_color}(priority: {skill.priority}){Color.RESET}")
                                    print(f"    {skill.description}")
                            print()
                            continue

                        elif skill_arg == "active":
                            # Show currently active skills
                            forced = getattr(load_active_skills, 'forced_skills', set())
                            disabled = getattr(load_active_skills, 'disabled_skills', set())

                            print(Color.info("\n=== Active Skill Configuration ==="))
                            if forced:
                                print(Color.success("Force-Enabled:"))
                                for skill_name in sorted(forced):
                                    print(f"  ✅ {skill_name}")
                            if disabled:
                                print(Color.warning("Disabled:"))
                                for skill_name in sorted(disabled):
                                    print(f"  ❌ {skill_name}")
                            if not forced and not disabled:
                                print(Color.system("  (No manual overrides - using auto-detection)"))
                            print()
                            continue

                        elif skill_arg.startswith("enable "):
                            # Force-enable specific skill
                            skill_name = skill_arg[7:].strip()
                            if not hasattr(load_active_skills, 'forced_skills'):
                                load_active_skills.forced_skills = set()
                            if not hasattr(load_active_skills, 'disabled_skills'):
                                load_active_skills.disabled_skills = set()

                            # Check if skill exists
                            if skill_name not in registry.list_skills():
                                print(Color.error(f"❌ Skill '{skill_name}' not found. Use '/skill list' to see available skills."))
                                continue

                            load_active_skills.forced_skills.add(skill_name)
                            # Remove from disabled if present
                            load_active_skills.disabled_skills.discard(skill_name)

                            print(Color.success(f"✅ Skill '{skill_name}' force-enabled (will be active in next turn)"))
                            continue

                        elif skill_arg.startswith("disable "):
                            # Disable specific skill
                            skill_name = skill_arg[8:].strip()
                            if not hasattr(load_active_skills, 'disabled_skills'):
                                load_active_skills.disabled_skills = set()
                            if not hasattr(load_active_skills, 'forced_skills'):
                                load_active_skills.forced_skills = set()

                            load_active_skills.disabled_skills.add(skill_name)
                            # Remove from forced if present
                            load_active_skills.forced_skills.discard(skill_name)

                            print(Color.warning(f"❌ Skill '{skill_name}' disabled (will not activate in next turn)"))
                            continue

                        elif skill_arg == "clear":
                            # Clear all manual overrides
                            load_active_skills.forced_skills = set()
                            load_active_skills.disabled_skills = set()
                            print(Color.success("✅ Manual skill overrides cleared (back to auto-detection)"))
                            continue

                        else:
                            print(Color.info("\n=== Skill Control Commands ==="))
                            print("  /skill list          - List all available skills")
                            print("  /skill active        - Show manual overrides (forced/disabled)")
                            print("  /skill enable <name> - Force-enable a specific skill")
                            print("  /skill disable <name> - Disable a specific skill")
                            print("  /skill clear         - Clear all manual overrides")
                            print()
                            continue

                    except ImportError:
                        print(Color.error("❌ Skill system not available"))
                        continue
                    except Exception as e:
                        print(Color.error(f"❌ Error processing /skill command: {e}"))
                        continue

                result = slash_registry.execute(user_input)

                if result:
                    # Check for special commands
                    if result == "CLEAR_HISTORY" or result.startswith("CLEAR_HISTORY:"):
                        # Parse optional keep count: CLEAR_HISTORY or CLEAR_HISTORY:N
                        keep_n = 0
                        if ":" in result:
                            try:
                                keep_n = int(result.split(":", 1)[1])
                            except ValueError:
                                keep_n = 0

                        # Rebuild: system prompt + last keep_n user/assistant pairs
                        system_msg = {"role": "system", "content": _build_system_prompt_str(agent_mode=agent_mode)}
                        if keep_n > 0:
                            non_system = [m for m in messages if m.get("role") != "system"]
                            kept = non_system[-(keep_n * 2):]  # N pairs = 2N messages
                            messages = [system_msg] + kept
                        else:
                            messages = [system_msg]

                        # Update context tracker
                        if messages and messages[0].get("role") == "system":
                            context_tracker.update_system_prompt(messages[0]["content"])
                        context_tracker.update_tools("")
                        context_tracker.update_memory({})
                        context_tracker.update_messages(messages, exclude_system=True)

                        # Save to history
                        save_conversation_history(messages)

                        # Reset active skill (history cleared = new context)
                        load_active_skills._active_skill = None
                        load_active_skills._cached_key = ""
                        load_active_skills._cached_skill = None

                        # Clear todo tracker
                        if todo_tracker_main:
                            todo_tracker_main.clear()

                        # Reset last_input_tokens so context bar reflects trimmed messages
                        llm_client.last_input_tokens = 0

                        if keep_n > 0:
                            print(Color.success(f"\n✅ Conversation history cleared (kept last {keep_n} message pair(s)).\n"))
                        else:
                            print(Color.success("\n✅ Conversation history cleared.\n"))
                        show_context_usage(messages, use_actual=False)
                        continue

                    if result == "GIT_CLEAR":
                        # Delete .git directory
                        try:
                            abs_path = os.path.abspath(".")
                            # Find git root starting from current dir
                            curr = Path(abs_path)
                            git_dir = None
                            for parent in [curr] + list(curr.parents):
                                if (parent / ".git").exists():
                                    git_dir = parent / ".git"
                                    break
                            
                            if git_dir:
                                import shutil
                                shutil.rmtree(git_dir)
                                print(Color.success(f"\n✅ Git history cleared (.git directory removed from {git_dir.parent}).\n"))
                            else:
                                print(Color.warning("\n⚠️  No .git directory found to clear.\n"))
                        except Exception as e:
                            print(Color.error(f"\n❌ Failed to clear git history: {e}\n"))
                        continue

                    if result == "GIT_DIFF":
                        # Show git diff
                        try:
                            import subprocess
                            proc = subprocess.run(["git", "diff"], capture_output=True, text=True)
                            if proc.stdout:
                                print(f"\n{Color.CYAN}--- Git Diff ---{Color.RESET}")
                                print(proc.stdout)
                                print(f"{Color.CYAN}----------------{Color.RESET}\n")
                            else:
                                print(Color.info("\nℹ️  No changes detected in git.\n"))
                        except Exception as e:
                            print(Color.error(f"\n❌ Failed to show git diff: {e}\n"))
                        continue

                    if result.startswith("WINDOW_MODE:"):
                        n = int(result.split(":", 1)[1])
                        rolling_window_size = n
                        if n > 0:
                            full_messages = list(messages)  # Start tracking full history
                            print(Color.success(f"\n✅ Rolling window: last {n} message pair(s) per LLM call.\n"))
                        else:
                            full_messages = None  # Disable full history tracking
                            print(Color.success("\n✅ Rolling window disabled.\n"))
                        continue

                    if result.startswith("COMPRESSION_MODE:"):
                        n = int(result.split(":", 1)[1])
                        auto_compression_threshold = n
                        if n > 0:
                            print(Color.success(f"\n✅ Auto-compression: triggers when messages exceed {n}.\n"))
                        else:
                            print(Color.success("\n✅ Auto-compression disabled.\n"))
                        continue

                    if result.startswith("AGENT_MODE:"):
                        agent_mode = result.split(":", 1)[1]
                        if agent_mode == "plan":
                            agent_mode = "plan_q"  # first turn: questions only, tools blocked
                            os.environ["PLAN_MODE"] = "true"
                            print(Color.success("\n✅ Plan mode: clarify → explore → refine → user confirms → execute.\n"))
                            # Clear stale todos from previous session
                            todo_file = Path(config.TODO_FILE)
                            if todo_file.exists():
                                todo_file.unlink()
                            
                            # Refresh system prompt with Plan Mode instructions
                            if messages and messages[0].get("role") == "system":
                                system_prompt_data = build_system_prompt(messages, agent_mode=agent_mode)
                                if config.CACHE_OPTIMIZATION_MODE == "optimized" and isinstance(system_prompt_data, dict):
                                    blocks = []
                                    if system_prompt_data.get("static"):
                                        blocks.append({"type": "text", "text": system_prompt_data["static"], "cache_control": {"type": "ephemeral"}})
                                    if system_prompt_data.get("dynamic"):
                                        blocks.append({"type": "text", "text": system_prompt_data["dynamic"]})
                                    messages[0]["content"] = blocks if blocks else system_prompt_data.get("static", "")
                                else:
                                    messages[0]["content"] = _build_system_prompt_str(messages=messages, agent_mode=agent_mode)
                                save_conversation_history(messages)
                        else:
                            agent_mode = "normal"
                            os.environ["PLAN_MODE"] = "false"
                            print(Color.success("\n✅ Normal mode.\n"))
                            # Restore normal system prompt
                            if messages and messages[0].get("role") == "system":
                                system_prompt_data = build_system_prompt(messages, agent_mode=agent_mode)
                                if config.CACHE_OPTIMIZATION_MODE == "optimized" and isinstance(system_prompt_data, dict):
                                    blocks = []
                                    if system_prompt_data.get("static"):
                                        blocks.append({"type": "text", "text": system_prompt_data["static"], "cache_control": {"type": "ephemeral"}})
                                    if system_prompt_data.get("dynamic"):
                                        blocks.append({"type": "text", "text": system_prompt_data["dynamic"]})
                                    messages[0]["content"] = blocks if blocks else system_prompt_data.get("static", "")
                                else:
                                    messages[0]["content"] = _build_system_prompt_str(messages=messages, agent_mode=agent_mode)
                                save_conversation_history(messages)
                        continue

                    if result.startswith("STEP_MODE:"):
                        status = result.split(":", 1)[1]
                        if status == "ON":
                            print(Color.success(f"\n✅ Step-by-Step execution mode enabled (will pause after each task).\n"))
                        else:
                            print(Color.warning(f"\n⏸️  Step-by-Step execution mode disabled.\n"))
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
                            todo_tracker=todo_tracker_main,
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

            # Create recovery point (before adding user message)
            global current_turn_id, current_recovery_point
            if config.ENABLE_SESSION_RECOVERY and config.AUTO_RECOVERY_POINT and session_manager:
                try:
                    current_recovery_point = session_manager.create_auto_recovery_point(
                        current_session_id,
                        description=f"User turn: {user_input[:50]}"
                    )
                except Exception as e:
                    print(Color.warning(f"[Recovery] Failed to create recovery point: {e}"))

            # Add user message with turn tracking
            current_turn_id += 1
            messages.append({
                "role": "user",
                "content": user_input,
                "turn_id": current_turn_id,
                "timestamp": time.time()
            })

            # Plan Mode Manual Confirmation Handler (Confirm by user input only)
            if agent_mode in ('plan', 'plan_q'):
                _inp = user_input.lower().strip()
                # Support English and Korean confirmation
                if _inp in ('y', 'yes', 'confirm', 'proceed', '진행', '확인', 'ok', '네', '예', 'ㅇㅇ', 'yc'):
                    do_compress = (_inp == 'yc')
                    agent_mode = 'normal'
                    os.environ["PLAN_MODE"] = "false"
                    if messages and messages[0].get("role") == "system":
                        # Fully rebuild system prompt to restore tools and remove Plan Mode instructions
                        from core import tools
                        system_prompt_data = build_system_prompt(messages, allowed_tools=set(tools.AVAILABLE_TOOLS.keys()), agent_mode='normal')
                        if isinstance(system_prompt_data, dict):
                            # Optimized mode: combine static and dynamic blocks
                            _new_content = system_prompt_data.get("static", "") + system_prompt_data.get("dynamic", "")
                        else:
                            _new_content = system_prompt_data
                        messages[0]["content"] = _new_content

                    msg = "✅ Confirmed. Switching to Execution Mode..."
                    if do_compress:
                        msg += " (with History Compression)"
                    print(Color.success(f"\n[Plan] {msg}\n"))
                    
                    # Inject a direct instruction to start immediately instead of just "y"
                    user_input = "Confirmed. Perform ONLY the first task (Step 1) immediately. Do NOT attempt multiple tasks in one turn."
                    if config.DEBUG_MODE:
                        print(Color.info(f"  [Debug] Injected confirmation: {user_input}"))
                    messages[-1]["content"] = user_input
                    
                    if do_compress:
                        messages = compress_history(messages, todo_tracker=todo_tracker_main, force=True)
                    
                    if full_messages is not None:
                        full_messages = list(messages)
                    save_conversation_history(messages)
                elif _inp in ('n', 'no', 'cancel', '취소', '아니오', 'ㄴㄴ'):
                    print(Color.warning("\n[Plan] Execution cancelled. Staying in Plan Mode for further refinements.\n"))
                    user_input = "I've reviewed the plan and I'm NOT ready to execute yet. Let's refine it further or address my concerns."

            # Handle 'keep going' signal to resume from rejected state
            if config.ENABLE_TODO_TRACKING and todo_tracker_main:
                _inp = user_input.lower().strip()
                if any(x in _inp for x in ('keep going', 'continue', '진행', '계속')):
                    if todo_tracker_main.unprocess_rejected():
                        print(Color.success("\n[System] 'Keep going' detected. Resetting rejected tasks for retry.\n"))
                        # Merge reminder into user input for better context and cleaner output
                        reminder = todo_tracker_main.get_continuation_prompt()
                        if reminder:
                            user_input = f"{user_input}\n\n{reminder}"
                            messages[-1]["content"] = user_input
                            if config.DEBUG_MODE:
                                _rem_db = reminder.replace('\n', ' ')
                                print(Color.info(f"  [Debug] Merged reminder into user input: {_rem_db}"))

            # ReAct Loop: Smart Iteration Control with progress tracking
            tracker = IterationTracker(max_iterations=config.MAX_ITERATIONS)

            # Auto-compression: compress when non-system message count exceeds threshold
            if auto_compression_threshold > 0:
                non_sys_count = sum(1 for m in messages if m.get("role") != "system")
                if non_sys_count > auto_compression_threshold:
                    print(Color.info(f"\n[Auto-compress] {non_sys_count} msgs > {auto_compression_threshold}, compressing..."))
                    messages = compress_history(messages, todo_tracker=todo_tracker_main, force=True, quiet=True)
                    context_tracker.update_messages(messages, exclude_system=True)
                    save_conversation_history(messages)

            # Rolling window: pass trimmed view to LLM, keep full_messages as authoritative history
            if rolling_window_size > 0 and full_messages is not None:
                # First iteration: messages != full_messages, sync user message
                # Subsequent iterations: messages IS full_messages (same object), already synced
                if messages is not full_messages:
                    full_messages.append(messages[-1])
                sys_msgs = [m for m in full_messages if m.get("role") == "system"]
                non_sys = [m for m in full_messages if m.get("role") != "system"]
                window_msgs = sys_msgs + non_sys[-(rolling_window_size * 2):]
                window_msgs_result, agent_mode = run_react_agent(window_msgs, tracker, user_input, mode='interactive', agent_mode=agent_mode, todo_tracker=todo_tracker_main)
                # Append only newly added messages (assistant + tool responses) to full_messages
                new_msgs = window_msgs_result[len(window_msgs):]
                full_messages.extend(new_msgs)
                messages = full_messages
            else:
                # Run ReAct Agent
                messages, agent_mode = run_react_agent(messages, tracker, user_input, mode='interactive', agent_mode=agent_mode, todo_tracker=todo_tracker_main)
                
                # After the first turn, we enable auto-plan if there are pending todos
                is_first_turn = False

            # plan_q (first clarification turn) → plan (explore allowed next turn)
            if agent_mode == 'plan_q':
                agent_mode = 'plan'

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
            import os as _os
            _os._exit(0)  # 강제 종료 — ThreadPoolExecutor hang 방지
        except EOFError:
            # stdin closed (e.g., from echo pipe) - exit gracefully
            print(Color.info("\n[System] Input stream closed. Exiting..."))
            save_conversation_history(messages)
            break
        except Exception as e:
            import traceback
            print(Color.error(f"\nAn error occurred: {e}"))
            traceback.print_exc()
            pass

    # Save history on normal exit
    save_conversation_history(messages)
    try:
        on_conversation_end(messages)
    except Exception as e:
        print(Color.warning(f"[Warning] Failed to save knowledge: {e}"))

def _ensure_git_repo():
    """Check for .git walking up from cwd; run git init if none found."""
    cwd = os.getcwd()
    check = cwd
    while True:
        if os.path.exists(os.path.join(check, '.git')):
            return  # already inside a git repo
        parent = os.path.dirname(check)
        if parent == check:
            break
        check = parent
    subprocess.run(['git', 'init', cwd], capture_output=True)
    print(Color.system(f"[Git] Initialized new repository at {cwd}"))


if __name__ == "__main__":
    if getattr(config, 'GIT_VERSION_CONTROL_ENABLE', True):
        _ensure_git_repo()

    if "--check" in sys.argv:
        # Smoke test: verify all imports and initialization succeed
        print(f"OK: platform={platform.system()}, model={config.MODEL_NAME}")
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] == "--prompt":
        # One-shot mode with ReAct loop
        prompt = sys.argv[2]
        messages = [
            {"role": "system", "content": _build_system_prompt_str()},
            {"role": "user", "content": prompt}
        ]
        
        print(Color.user(f"User: {prompt}\n"))

        # ReAct loop: Smart Iteration Control with progress tracking
        # Initialize iteration tracker (oneshot mode)
        tracker = IterationTracker(max_iterations=config.MAX_ITERATIONS)

        # Run ReAct Agent
        messages, _ = run_react_agent(messages, tracker, prompt, mode='oneshot', todo_tracker=None)

        # Extract knowledge from conversation at end
        try:
            on_conversation_end(messages)
        except Exception as e:
            print(Color.warning(f"[Warning] Failed to save knowledge: {e}"))
    else:
        chat_loop()
