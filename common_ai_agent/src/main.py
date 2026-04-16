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
import threading

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
sys.path.insert(0, _project_root)  # common_ai_agent directory (for lib, core, workflow)

import config
import llm_client
from core import tools
from core.slash_commands import get_registry as get_slash_command_registry
from core.context_tracker import get_tracker as get_context_tracker
from core.session_manager import SessionManager, RecoveryPoint
from lib.display import Color, enable_windows_virtual_terminal
from llm_client import chat_completion_stream, call_llm_raw, estimate_message_tokens, get_actual_tokens, get_rate_limiter

# Enable Windows Virtual Terminal Processing so ANSI color codes render
# correctly instead of showing as raw '?[92m' garbage in cmd/PowerShell.
enable_windows_virtual_terminal()
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
from core.text_utils import strip_thinking_tags as _strip_thinking_tags
from core.action_parser import (
    sanitize_action_text,
    _strip_native_tool_tokens,
    _extract_annotation_ranges,
    parse_all_actions,
    parse_implicit_actions,
    parse_tool_arguments,
    parse_value,
)
from core.observation_processor import process_observation as _process_observation_impl
from core.history_manager import (
    save_conversation_history as _save_history_impl,
    load_conversation_history as _load_history_impl,
)
from core.prompt_builder import (
    PromptContext,
)
# Save the unpatched original so workspace switches always patch from a clean base
import core.prompt_builder as _prompt_builder_module
_ORIG_BUILD_SYSTEM_PROMPT = _prompt_builder_module.build_system_prompt

# Save originals for plan and compression prompts so repeated workspace switches
# always patch from clean base values, never accumulate.
def _save_prompt_originals():
    import config as _cfg
    import core.compressor as _comp
    _ORIG_PLAN_PROMPT = getattr(_cfg, 'PLAN_MODE_PROMPT', None)
    _ORIG_COMPRESSION_PROMPT = getattr(_comp, 'STRUCTURED_SUMMARY_PROMPT', None)
    return _ORIG_PLAN_PROMPT, _ORIG_COMPRESSION_PROMPT

_ORIG_PLAN_PROMPT, _ORIG_COMPRESSION_PROMPT = _save_prompt_originals()

# Save original todo rule loader so workspace switches always patch from a clean base
try:
    import lib.todo_tracker as _tt_module
    _ORIG_LOAD_TODO_RULE = _tt_module._load_todo_rule
except Exception:
    _ORIG_LOAD_TODO_RULE = None

from core.compressor import (
    compress_history as _compress_history_impl,
)
from core.react_loop import (
    run_react_agent_impl as _run_react_agent_impl,
    ReactLoopDeps,
)
from core.tool_dispatcher import (
    dispatch_tool as _dispatch_tool,
    _agent_metadata,
    get_last_agent_metadata,
)
from core.parallel_executor import (
    execute_actions_parallel as _execute_actions_parallel_impl,
    execute_batch_parallel as _execute_batch_parallel_impl,
    PARALLEL_ELIGIBLE_TOOLS as _PARALLEL_ELIGIBLE_TOOLS_IMPORTED,
)
from core.chat_loop import (
    ChatLoopState as _ChatLoopState,
    ChatLoopDeps as _ChatLoopDeps,
    process_chat_turn as _process_chat_turn,
)

# Deep Think (deprecated - replaced by plan agent in v2)
if getattr(config, 'ENABLE_DEEP_THINK', False) and not getattr(config, 'ENABLE_SUB_AGENTS', False):
    try:
        from lib.deep_think import DeepThinkEngine, DeepThinkResult, format_deep_think_output
    except ImportError:
        pass

# Textual TUI callbacks (set by textual_main.py before calling chat_loop())
_textual_emit_content_fn = None
_textual_emit_reasoning_fn = None
_textual_emit_todo_fn = None
_textual_emit_flush_fn = None   # () → signal stream done, flush content panel
_textual_emit_context_fn = None  # (tokens, max_tokens) → update context sidebar directly
_textual_input_fn = None  # replaces input() when set
_textual_esc_check_fn = None # () → bool: TUI interrupt check

# ChatLoopDeps instance (set inside chat_loop(); exposed for textual_main.py)
_loop_deps = None

# Active workspace configuration (set by _setup_workspace())
_workspace_config = None
_workspace_command_names = []       # track names so we can unregister on switch


def _setup_workspace(name: str) -> None:
    """
    Load and activate a named workspace from workflow/<name>/.
    Patches prompts, compression, hook messages, skill loader, and todo templates.
    Called from __main__ before chat_loop().
    """
    global _workspace_config, _workspace_command_names
    if not name or name == 'none':
        return

    # Locate workflow directory
    _script_dir_ws = os.path.dirname(os.path.abspath(__file__))
    _project_root_ws = os.path.dirname(_script_dir_ws)
    candidates = [
        os.path.join(os.path.dirname(_project_root_ws), "new_feature", "workflow"),
        os.path.join(_project_root_ws, "workflow"),
    ]
    workflow_root = None
    for c in candidates:
        if os.path.isdir(os.path.join(c, name)):
            workflow_root = c
            break
    if workflow_root is None:
        print(f"[Workspace] Warning: workspace '{name}' not found in any workflow directory.")
        return

    # Import loader
    sys.path.insert(0, os.path.dirname(workflow_root))
    try:
        from workflow.loader import (
            load_workspace, merge_prompt, patch_todo_rules,
            register_script_hooks, get_todo_template_registry,
            register_workspace_commands,
        )
    except ImportError as e:
        print(f"[Workspace] Cannot import workflow.loader: {e}")
        return

    ws = load_workspace(name, project_root=Path(workflow_root).parent)
    if ws is None:
        print(f"[Workspace] Failed to load workspace '{name}'.")
        return
    _workspace_config = ws

    # ── 1. Inject hook messages into builtins ─────────────────────────────
    import builtins as _b
    # Always reset to a fresh dict so stale keys from a previous workspace
    # don't leak.  Include _workspace_dir so _load_prompt_fragment() can
    # resolve workspace-specific prompt files.
    _b._WORKSPACE_HOOK_MESSAGES = {
        "_workspace_dir": str(ws.workspace_dir),
    }
    if ws.hook_messages:
        _b._WORKSPACE_HOOK_MESSAGES.update(ws.hook_messages)

    # ── 2. Patch system prompt ─────────────────────────────────────────────
    # Always patch from the unmodified original so repeated workspace switches
    # don't chain-patch and accumulate multiple workspace prompts.
    if ws.system_prompt_text:
        try:
            import core.prompt_builder as _pb
            _ws_text = ws.system_prompt_text
            _ws_mode = ws.system_prompt_mode
            _orig = _ORIG_BUILD_SYSTEM_PROMPT  # never changes between switches

            def _patched_build_system_prompt(ctx=None, **kwargs):
                base = _orig(ctx, **kwargs) if ctx is not None else _orig(**kwargs)
                if isinstance(base, dict):
                    base = (base.get("static", "") + "\n\n" + base.get("dynamic", "")).strip()
                return merge_prompt(base, _ws_text, _ws_mode)

            _pb.build_system_prompt = _patched_build_system_prompt
        except Exception:
            pass
    else:
        # Workspace has no system_prompt — restore the original so the previous
        # workspace's prompt doesn't bleed through.
        try:
            import core.prompt_builder as _pb
            _pb.build_system_prompt = _ORIG_BUILD_SYSTEM_PROMPT
        except Exception:
            pass

    # ── 3. Patch plan prompt ───────────────────────────────────────────────
    try:
        if ws.plan_prompt_text:
            if hasattr(config, 'PLAN_MODE_PROMPT') and _ORIG_PLAN_PROMPT is not None:
                config.PLAN_MODE_PROMPT = merge_prompt(
                    _ORIG_PLAN_PROMPT, ws.plan_prompt_text, ws.plan_prompt_mode
                )
        else:
            if _ORIG_PLAN_PROMPT is not None and hasattr(config, 'PLAN_MODE_PROMPT'):
                config.PLAN_MODE_PROMPT = _ORIG_PLAN_PROMPT
    except Exception:
        pass

    # ── 4. Patch compression prompt ────────────────────────────────────────
    try:
        import core.compressor as _comp
        if ws.compression_prompt_text:
            base_comp = _ORIG_COMPRESSION_PROMPT or getattr(_comp, 'STRUCTURED_SUMMARY_PROMPT', "")
            _comp.STRUCTURED_SUMMARY_PROMPT = merge_prompt(
                base_comp,
                ws.compression_prompt_text,
                "replace",
            )
            _b._WORKSPACE_HOOK_MESSAGES["compression_system"] = _comp.STRUCTURED_SUMMARY_PROMPT
        else:
            if _ORIG_COMPRESSION_PROMPT is not None:
                _comp.STRUCTURED_SUMMARY_PROMPT = _ORIG_COMPRESSION_PROMPT
    except Exception:
        pass

    # ── 5. Register script hooks ───────────────────────────────────────────
    # Clear any previously registered script hooks to avoid accumulation
    # across workspace switches.  We reuse the global hook_registry so hooks
    # actually fire during the ReAct loop.
    try:
        from core.hooks import HookRegistry, HookPoint
        # Remove old script hooks (priority 900) if present
        if hook_registry is not None:
            for hp in HookPoint:
                hook_registry._hooks[hp] = [
                    (p, fn) for p, fn in hook_registry._hooks[hp] if p != 900
                ]
        _target_registry = hook_registry if hook_registry is not None else HookRegistry()
        if ws.script_hooks:
            register_script_hooks(ws, _target_registry)
    except Exception:
        pass

    # ── 6. Patch todo rules ────────────────────────────────────────────────
    patch_todo_rules(ws, _base_rule_fn=_ORIG_LOAD_TODO_RULE)

    # ── 7. Register todo templates ─────────────────────────────────────────
    # Reset the singleton so stale templates from a previous workspace don't
    # accumulate.  Only the current workspace's templates should be active.
    try:
        registry = get_todo_template_registry()
        registry._templates.clear()           # wipe previous workspace's templates
        # Load global templates first (can be overridden by workspace-specific)
        registry.load_global_templates(Path.cwd())
        if ws.todo_templates_dir:
            registry.load_from_dir(ws.todo_templates_dir)
        _b._TODO_TEMPLATE_REGISTRY = registry
    except Exception:
        pass

    # ── 8. Register extra skills ───────────────────────────────────────────
    try:
        import core.skill_system as _ss
        if hasattr(_ss, '_loader') and hasattr(_ss._loader, 'extra_dirs'):
            # Remove previous workspace skill dirs, add current
            _ws_skill_dir = str(ws.extra_skills_dir) if ws.extra_skills_dir else None
            # Only keep dirs that don't belong to any workflow (user-added dirs)
            _ss._loader.extra_dirs = [
                d for d in _ss._loader.extra_dirs
                if '/workflow/' not in d.replace('\\', '/') or d == _ws_skill_dir
            ]
            if _ws_skill_dir and _ws_skill_dir not in _ss._loader.extra_dirs:
                _ss._loader.extra_dirs.append(_ws_skill_dir)
    except Exception:
        pass

    # ── 9. Force-activate / disable skills ────────────────────────────────
    # Replace (not append) so switching workspaces doesn't accumulate skills
    # from previous workspaces.
    if ws.force_skills:
        os.environ["FORCE_SKILLS"] = ",".join(ws.force_skills)
    else:
        os.environ.pop("FORCE_SKILLS", None)
    if ws.disable_skills:
        os.environ["DISABLE_SKILLS"] = ",".join(ws.disable_skills)
    else:
        os.environ.pop("DISABLE_SKILLS", None)

    # ── 10. Register workspace-specific slash commands ─────────────────────
    try:
        from core.slash_commands import get_registry as _get_slash_registry
        _slash_reg = _get_slash_registry()
        # Remove previous workspace's commands before registering new ones
        if _workspace_command_names:
            _slash_reg.unregister_many(_workspace_command_names)
            _workspace_command_names.clear()
        # Register and track new workspace commands
        _new_names = register_workspace_commands(ws, _slash_reg)
        _workspace_command_names.extend(_new_names)
    except Exception as e:
        print(f"[Workspace] Warning: could not register commands: {e}")

    # Store description so prompt_builder can include it in the identity line
    if ws.description:
        os.environ["ACTIVE_WORKSPACE_DESC"] = ws.description

    print(f"[Workspace] '{name}' loaded from {workflow_root}/{name}")


# Legacy Sub-Agent System (deprecated - replaced by background agent system in v2)
orchestrator = None

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

if getattr(config, 'ENABLE_WEB_TOOLS', False):
    try:
        from core.tools_web import WEB_TOOLS
        tools.AVAILABLE_TOOLS.update(WEB_TOOLS)
        if config.DEBUG_MODE:
            print(Color.system("[System] Web tools plugin loaded successfully 🌐"))
    except ImportError as e:
        print(Color.warning(f"[System] Failed to load web tools: {e}"))

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

# --- 3. History Management ---

def save_conversation_history(messages, silent=True):
    """Wrapper: delegates to core.history_manager."""
    _save_history_impl(messages, silent=silent)

def load_conversation_history():
    """Wrapper: delegates to core.history_manager."""
    return _load_history_impl()

# --- 4. ReAct Logic ---
# Parser functions imported from core.action_parser (see imports above)
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



# Thread-local storage for Agent communication metadata (lives in core/tool_dispatcher)

# Phase 3: Thread-local storage for SharedContext
import threading
_shared_context_storage = threading.local()


def get_shared_context():
    """Get current thread's SharedContext"""
    if not hasattr(_shared_context_storage, 'context'):
        _shared_context_storage.context = None
    return _shared_context_storage.context


def execute_tool(tool_name, args_str="", *, pre_parsed_kwargs=None):
    return _dispatch_tool(
        tool_name,
        args_str,
        pre_parsed_kwargs=pre_parsed_kwargs,
        available_tools=tools.AVAILABLE_TOOLS,
        debug=getattr(config, "DEBUG_MODE", False),
        hook_registry=hook_registry,
        global_timeout=getattr(config, "REACT_TOOL_GLOBAL_TIMEOUT", 300),
    )

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
            # No "skill" keyword → reuse existing active skill only (no LLM routing)
            routed = getattr(load_active_skills, '_active_skill', None)
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
                    print(f"  \033[38;5;208m[skill] {routed}\033[0m \033[2m(llm-routed)\033[0m")

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

        # forced skill print suppressed — shown in TUI sidebar instead

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
    """Wrapper: delegates to core.prompt_builder.
    
    IMPORTANT: Calls through the module attribute so workspace patches take effect.
    """
    ctx = PromptContext(
        memory_system=memory_system,
        graph_lite=graph_lite,
        procedural_memory=procedural_memory,
        hybrid_rag=hybrid_rag,
        todo_tracker=todo_tracker,
    )
    return _prompt_builder_module._build_system_prompt_str(
        context=ctx,
        load_skills_fn=load_active_skills if config.ENABLE_SKILL_SYSTEM else None,
        llm_call_fn=call_llm_raw,
        **kwargs,
    )


def build_system_prompt(messages=None, allowed_tools=None, agent_mode=None):
    """Wrapper: delegates to core.prompt_builder with global state injected.
    
    IMPORTANT: Calls through the module attribute (_prompt_builder_module.build_system_prompt)
    rather than the import-time binding, so workspace patches take effect.
    """
    ctx = PromptContext(
        memory_system=memory_system,
        graph_lite=graph_lite,
        procedural_memory=procedural_memory,
        hybrid_rag=hybrid_rag,
        todo_tracker=todo_tracker,
    )
    return _prompt_builder_module.build_system_prompt(
        messages=messages,
        allowed_tools=allowed_tools,
        agent_mode=agent_mode,
        context=ctx,
        load_skills_fn=load_active_skills if config.ENABLE_SKILL_SYSTEM else None,
        llm_call_fn=call_llm_raw,
    )

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
    if _textual_emit_content_fn is not None:
        return  # TUI mode: context shown in sidebar, skip bar output
    if use_actual:
        current_tokens = get_actual_tokens(messages)
        source = "actual" if llm_client.last_input_tokens > 0 else "estimated"
    else:
        current_tokens = sum(estimate_message_tokens(m) for m in messages)
        source = "estimated"

    limit_tokens = config.MAX_CONTEXT_TOKENS
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


# _find_hook and _hook_command moved to core.compressor
from core.compressor import _find_hook, _hook_command


def compress_history(messages, todo_tracker=None, force=False, instruction=None,
                     keep_recent=None, dry_run=False, quiet=False):
    """Wrapper: delegates to core.compressor with main.py dependencies injected."""
    return _compress_history_impl(
        messages,
        todo_tracker=todo_tracker,
        force=force,
        instruction=instruction,
        keep_recent=keep_recent,
        dry_run=dry_run,
        quiet=quiet,
        cfg=config,
        llm_call_fn=chat_completion_stream,
        estimate_tokens_fn=estimate_message_tokens,
        get_actual_tokens_fn=get_actual_tokens,
        last_input_tokens=llm_client.last_input_tokens,
        on_compressed_fn=lambda: setattr(llm_client, "last_input_tokens", 0),
        emit_fn=(
            (lambda md: (_textual_emit_content_fn(md), _textual_emit_flush_fn and _textual_emit_flush_fn()))
            if _textual_emit_content_fn else None
        ),
    )


def process_observation(observation, messages, todo_tracker=None):
    """Wrapper: delegates to core.observation_processor with main.py dependencies injected."""
    return _process_observation_impl(
        observation,
        messages,
        compress_fn=compress_history,
        todo_tracker=todo_tracker,
    )


# --- 6. ReAct Agent Logic ---

_PARALLEL_ELIGIBLE_TOOLS = _PARALLEL_ELIGIBLE_TOOLS_IMPORTED


def execute_actions_parallel(actions, tracker, agent_mode='normal'):
    return _execute_actions_parallel_impl(
        actions,
        tracker=tracker,
        agent_mode=agent_mode,
        cfg=config,
        execute_tool_fn=execute_tool,
        print_fn=lambda msg: print(Color.warning(msg) if msg.startswith("[") else Color.info(msg)),
    )


def _execute_batch_parallel(batch_actions):
    return _execute_batch_parallel_impl(
        batch_actions,
        execute_tool_fn=execute_tool,
        cfg=config,
    )


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


def _save_conv_snapshot(task_num: int, messages: list) -> None:
    """Save conversation snapshot keyed by task number (for rollback support)."""
    try:
        from core.session_snapshot import save_snapshot
        save_snapshot(messages, name=f"task_{task_num}_approved")
    except Exception:
        pass  # Non-critical: snapshot failure should not interrupt the agent loop


def _load_conv_snapshot(task_num: int) -> Optional[list]:
    """Load conversation snapshot for a given task number. Returns None if not found."""
    try:
        from core.session_snapshot import load_snapshot
        return load_snapshot(f"task_{task_num}_approved")
    except Exception:
        return None


def run_react_agent(messages, tracker, task_description, mode='interactive', preface_enabled=True, agent_mode='normal', todo_tracker=None):
    """Wrapper: delegates to core.react_loop with main.py live dependencies injected."""
    # In TUI mode suppress stderr spinner so it doesn't bleed through Textual's display
    _is_tui = _textual_emit_content_fn is not None
    # Native tool call mode: pass tools schemas to LLM API
    _native_tools = None
    if getattr(config, "ENABLE_NATIVE_TOOL_CALLS", False):
        try:
            from core.tool_schema import get_tool_schemas
            _native_tools = get_tool_schemas(list(tools.AVAILABLE_TOOLS.keys()))
        except Exception:
            pass
    if _native_tools:
        _llm_fn = (lambda msg, stop=None, _t=_native_tools: chat_completion_stream(msg, stop=stop, suppress_spinner=True, tools=_t)) \
            if _is_tui else (lambda msg, stop=None, _t=_native_tools: chat_completion_stream(msg, stop=stop, tools=_t))
    else:
        _llm_fn = (lambda msg, stop=None: chat_completion_stream(msg, stop=stop, suppress_spinner=True)) \
            if _is_tui else chat_completion_stream
    deps = ReactLoopDeps(
        cfg=config,
        llm_call_fn=_llm_fn,
        compress_fn=compress_history,
        build_prompt_fn=build_system_prompt,
        process_obs_fn=process_observation,
        execute_tool_fn=execute_tool,
        execute_parallel_fn=execute_actions_parallel,
        save_trajectory_fn=save_procedural_trajectory,
        show_context_usage_fn=show_context_usage,
        show_iteration_warning_fn=show_iteration_warning,
        strip_tokens_fn=_strip_native_tool_tokens,
        strip_thinking_fn=_strip_thinking_tags,
        parse_todo_fn=_parse_todo_markdown,
        detect_completion_fn=detect_completion_signal,
        get_turn_id_fn=lambda: current_turn_id,
        get_llm_usage_fn=llm_client.get_last_usage,
        get_llm_tokens_fn=lambda: (llm_client.last_input_tokens, llm_client.last_output_tokens),
        orchestrator=orchestrator,
        procedural_memory=procedural_memory,
        graph_lite=graph_lite,
        hook_registry=hook_registry,
        available_tools=tools.AVAILABLE_TOOLS,
        inject_strategy_fn=_maybe_inject_exploration_strategy,
        save_snapshot_fn=_save_conv_snapshot,
        load_snapshot_fn=_load_conv_snapshot,
        build_prompt_str_fn=_build_system_prompt_str,
        get_recovery_state_fn=lambda: (current_recovery_point, session_manager, current_session_id),
        # Textual TUI callbacks (None in normal terminal mode)
        emit_content_fn=_textual_emit_content_fn,
        emit_reasoning_fn=_textual_emit_reasoning_fn,
        emit_todo_fn=_textual_emit_todo_fn,
        emit_flush_fn=_textual_emit_flush_fn,
        # Disable EscapeWatcher in Textual mode — Textual owns stdin; raw tty read
        # conflicts with Textual's input handling, causing false ESC triggers.
        # Instead, use the TUI's mapped escape key via the callback.
        esc_check_fn=_textual_esc_check_fn if _textual_input_fn is not None else None,
        esc_start_fn=(lambda: None) if _textual_input_fn is not None else None,
        esc_stop_fn=(lambda: None) if _textual_input_fn is not None else None,
    )
    return _run_react_agent_impl(
        messages=messages,
        tracker=tracker,
        task_description=task_description,
        deps=deps,
        mode=mode,
        preface_enabled=preface_enabled,
        agent_mode=agent_mode,
        todo_tracker=todo_tracker,
    )


# --- 7. Session Setup ---

def _migrate_old_session(session_dir: Path):
    """Migrate old .session/ layouts to v2 flat project structure.

    v0 (original flat):
      .session/<name>/conversation_history.json
      .session/<name>/current_todos.json
      .session/<name>/full_conversation_history.json

    v1 (primary/sub):
      .session/<name>/primary/conversation.json
      .session/<name>/primary/full_conversation.json
      .session/<name>/primary/<workflow>/todo.json
      .session/<name>/sub/agent<N>_<wf>/...

    v2 (target — flat project):
      .session/<name>/conversation.json
      .session/<name>/full_conversation.json
      .session/<name>/todo.json
      .session/<name>/jobs/job<N>/...
    """
    import shutil

    # ── v1 → v2: move files out of primary/ first (newer, more authoritative) ──
    primary_dir = session_dir / 'primary'
    if primary_dir.is_dir():
        # Move conversation files from primary/ to session root (newer wins)
        for fname in ('conversation.json', 'full_conversation.json'):
            src = primary_dir / fname
            dst = session_dir / fname
            if src.exists():
                if not dst.exists() or src.stat().st_mtime > dst.stat().st_mtime:
                    shutil.move(str(src), str(dst))

        # Move data files from any primary/<workflow>/ to session root (newer wins)
        if primary_dir.is_dir():
            for wf_dir in primary_dir.iterdir():
                if not wf_dir.is_dir():
                    continue
                for data_name in ('todo.json', 'todo_error.json', 'input_history.txt'):
                    src = wf_dir / data_name
                    dst = session_dir / data_name
                    if src.exists():
                        if not dst.exists() or src.stat().st_mtime > dst.stat().st_mtime:
                            shutil.move(str(src), str(dst))

        # Remove primary/ tree (all data already moved or intentionally older)
        try:
            shutil.rmtree(primary_dir, ignore_errors=True)
        except Exception:
            pass

    # ── v1 → v2: rename sub/agent<N>_<wf>/ → jobs/job<N>/ ─────────────
    sub_dir = session_dir / 'sub'
    jobs_dir = session_dir / 'jobs'
    if sub_dir.is_dir():
        jobs_dir.mkdir(parents=True, exist_ok=True)

        # Determine next job counter
        existing_jobs = [d for d in jobs_dir.iterdir() if d.is_dir() and d.name.startswith('job')]
        counter = len(existing_jobs) + 1

        # Move each agent dir → job dir
        for agent_dir in sorted(sub_dir.iterdir()):
            if not agent_dir.is_dir():
                continue
            if agent_dir.name == '.counter':
                continue
            job_dir = jobs_dir / f'job{counter}'
            counter += 1
            if not job_dir.exists():
                shutil.move(str(agent_dir), str(job_dir))

        # Clean up old sub/ directory
        try:
            shutil.rmtree(sub_dir, ignore_errors=True)
        except Exception:
            pass

    # ── v0 → v2: rename old flat files (fallback if no v1 data) ────────
    v0_moves = [
        ('conversation_history.json',       'conversation.json'),
        ('full_conversation_history.json',  'full_conversation.json'),
        ('current_todos.json',              'todo.json'),
        ('current_todos_error.json',        'todo_error.json'),
    ]
    for old_name, new_name in v0_moves:
        old = session_dir / old_name
        if old.exists() and not (session_dir / new_name).exists():
            shutil.move(str(old), str(session_dir / new_name))
        elif old.exists():
            # v1 already filled the target — just remove the old v0 file
            old.unlink()


def _setup_session(project: str = 'default', workflow: str = '') -> Path:
    """Create .session/<project>/ flat layout and redirect config paths.

    Layout (v2 — flat project):
      .session/<project>/conversation.json       ← HISTORY_FILE
      .session/<project>/full_conversation.json  ← append-only history
      .session/<project>/todo.json               ← TODO_FILE
      .session/<project>/todo_error.json         ← TODO_ERROR_FILE
      .session/<project>/input_history.txt       ← readline history
      .session/<project>/jobs/job<N>/            ← sub-agent persistence

    Args:
        project:  Project name (maps to .session/<project>/).
        workflow: Ignored (kept for backward compat with v1 callers).
    """
    session_dir = Path.cwd() / '.session' / project
    session_dir.mkdir(parents=True, exist_ok=True)

    # Migrate old layouts (v0 flat or v1 primary/sub) → v2 flat
    _migrate_old_session(session_dir)

    # Set config paths to flat project layout
    config.HISTORY_FILE    = str(session_dir / 'conversation.json')
    config.TODO_FILE       = str(session_dir / 'todo.json')
    config.TODO_ERROR_FILE = str(session_dir / 'todo_error.json')
    config.SESSION_DIR     = str(session_dir)
    config.ACTIVE_PROJECT  = project

    # Patch todo_tracker module-level TODO_FILE
    import lib.todo_tracker as _tt
    _tt.TODO_FILE = session_dir / 'todo.json'

    return session_dir


# --- 8. Main Loop ---

def chat_loop():
    # Pre-warm TCP+SSL connection in parallel while the rest of startup runs
    _warmup_thread = threading.Thread(target=llm_client.warmup_connection, daemon=True, name="llm-warmup")
    _warmup_thread.start()

    # Initialize session manager (for recovery system)
    global session_manager, current_session_id, current_recovery_point, todo_tracker

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
            if not _textual_emit_content_fn:
                print(Color.warning(f"[System] Session manager initialization failed: {e}"))
                print(Color.warning("[System] Continuing without session recovery..."))
            session_manager = None

    # Default mode
    agent_mode = 'normal'

    # Try to load existing conversation history
    loaded_messages = load_conversation_history()
    if loaded_messages:
        messages = loaded_messages
        # Always refresh the system prompt so workspace/flow context is current.
        # Saved history may carry a stale prompt from a previous workspace or session.
        _current_system_prompt = _build_system_prompt_str(agent_mode=agent_mode)
        if messages and messages[0].get("role") == "system":
            messages[0]["content"] = _current_system_prompt
        else:
            messages.insert(0, {"role": "system", "content": _current_system_prompt})
        if not _textual_emit_content_fn:
            print(Color.system("[System] Resuming from previous conversation.\n"))
    else:
        messages = [
            {"role": "system", "content": _build_system_prompt_str(agent_mode=agent_mode)}
        ]

    # Initialize context tracker
    max_tokens = config.MAX_CONTEXT_TOKENS
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
            if not _textual_emit_content_fn:
                print(Color.info(f"[System] Created default .UPD_RULE.md at {_default_path}"))
        except Exception as e:
            if not _textual_emit_content_fn:
                print(Color.warning(f"[System] Could not create .UPD_RULE.md: {e}"))
    else:
        _loaded = [str(p) for p in _upd_rule_paths if p.exists()]
        if config.DEBUG_MODE:
            print(Color.system(f"[System] .UPD_RULE.md loaded: {', '.join(_loaded)}"))

    # Perform Memory Healing (One-time check on startup)
    if config.ENABLE_GRAPH and graph_lite:
        graph_lite.heal_embeddings()

    if not _textual_emit_content_fn:
        # Compact startup banner
        from lib.display import format_startup_banner
        from src.llm_client import get_active_model
        _rl = get_rate_limiter()
        _rl_info = f"TPM={config.TPM_LIMIT} RPM={config.RPM_LIMIT}" if _rl.active else f"delay={config.RATE_LIMIT_DELAY}s"
        print(format_startup_banner(
            base_url=config.BASE_URL if not getattr(config, "CURSOR_AGENT_ENABLE", False) else "cursor-agent",
            model=get_active_model(),
            features={
                'rate_limit': _rl_info,
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
    # Sync global so _get_todo_tracker() in tools.py returns the same instance
    if todo_tracker_main is not None:
        todo_tracker = todo_tracker_main

    # Auto RAG Indexing on startup
    if config.ENABLE_RAG_AUTO_INDEX:
        try:
            from tools import rag_index
            mode_str = "(fine-grained)" if config.RAG_FINE_GRAINED else ""
            if not _textual_emit_content_fn:
                print(Color.system(f"[RAG] Checking for Verilog files to index... {mode_str}"))
            result = rag_index(".", fine_grained=config.RAG_FINE_GRAINED)
            if not _textual_emit_content_fn:
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

    # ── ChatLoopState / Deps for core/chat_loop delegation ──
    _loop_state = _ChatLoopState(
        messages=messages,
        agent_mode=agent_mode,
        rolling_window_size=rolling_window_size,
        full_messages=full_messages,
        auto_compression_threshold=auto_compression_threshold,
        conversation_count=conversation_count,
        is_first_turn=is_first_turn,
        todo_tracker=todo_tracker_main,
    )
    global _loop_deps
    _loop_deps = _ChatLoopDeps(
        cfg=config,
        run_react_agent_fn=run_react_agent,
        compress_fn=compress_history,
        save_history_fn=save_conversation_history,
        on_conversation_end_fn=on_conversation_end,
        build_system_prompt_fn=build_system_prompt,
        show_context_usage_fn=show_context_usage,
        slash_registry=slash_registry,
        context_tracker=context_tracker,
        curator=curator,
        hook_registry=hook_registry,
        input_fn=_textual_input_fn,  # None in terminal mode; set by textual_main.py
    )

    # ── Multiline input setup ──
    _multiline_prompt = None
    if config.ENABLE_MULTILINE_INPUT and _textual_input_fn is None:
        try:
            # Add vendored packages to path (use resolve() for absolute path on all platforms)
            _vendor_dir = str(Path(__file__).resolve().parent.parent / 'vendor')
            if _vendor_dir not in sys.path:
                sys.path.insert(0, _vendor_dir)
            from prompt_toolkit import PromptSession, ANSI
            from prompt_toolkit.key_binding import KeyBindings
            from prompt_toolkit.history import FileHistory, InMemoryHistory
            from prompt_toolkit.completion import Completer, Completion
            import os as _os_comp, glob as _glob_comp

            _kb = KeyBindings()

            def _do_exit(label="ESC"):
                print(f"\n[{label}] Saving & exiting...")
                save_conversation_history(messages, silent=True)
                import os as _os
                _os._exit(0)

            # ── ESC handler ─────────────────────────────────────────────────────
            # Double-ESC to exit (with debounce to avoid triggering on terminal
            # focus events like ^[[O / ^[[I sent when switching terminal tabs).
            # Focus events arrive as ESC + bracket sequence in < 50ms.
            # We require: first ESC → wait >200ms → second ESC = deliberate.
            _last_esc_time = [0.0]
            _esc_pending_msg = [False]

            @_kb.add('escape')
            def _esc_handler(event):
                import time
                now = time.time()
                gap = now - _last_esc_time[0]
                _last_esc_time[0] = now
                # Gap too short (<200ms) = terminal artifact (focus event, etc.)
                if gap < 0.20:
                    _esc_pending_msg[0] = False
                    return
                if gap < 1.5 and _esc_pending_msg[0]:
                    _do_exit("ESC×2")
                else:
                    _esc_pending_msg[0] = True
                    event.app.output.write_raw("\n  ⎋ Press ESC again to exit, or wait...\n")
                    event.app.output.flush()
                    def _clear():
                        _esc_pending_msg[0] = False
                    try:
                        import asyncio
                        asyncio.get_event_loop().call_later(1.5, _clear)
                    except Exception:
                        pass

            @_kb.add('c-q')
            def _ctrlq_exit(event):
                _do_exit("Ctrl+Q")

            class _AtFileCompleter(Completer):
                """Auto-complete: '/' → slash commands, '@' → file/folder paths."""

                def _slash_completions(self, text):
                    """Yield slash command completions when input starts with '/'."""
                    try:
                        try:
                            from core.slash_commands import get_registry
                        except ImportError:
                            from slash_commands import get_registry
                        reg = get_registry()
                        all_cmds = reg.get_completions()  # e.g. ['/help', '/plan', ...]
                    except Exception:
                        return
                    for cmd in all_cmds:
                        if cmd.lower().startswith(text.lower()):
                            yield Completion(
                                cmd,
                                start_position=-len(text),
                                display=cmd,
                            )

                def _file_completions(self, text):
                    """Yield file/folder completions for the path after '@'."""
                    at_pos = text.rfind('@')
                    if at_pos == -1:
                        return
                    partial = text[at_pos + 1:]
                    if '/' in partial:
                        dir_part, stem = partial.rsplit('/', 1)
                        base_dir = _os_comp.path.join('.', dir_part)
                    else:
                        dir_part = ''
                        stem = partial
                        base_dir = '.'
                    try:
                        entries = _os_comp.listdir(base_dir)
                    except OSError:
                        return
                    for name in sorted(entries):
                        if name.startswith('.'):
                            continue
                        if stem and not name.lower().startswith(stem.lower()):
                            continue
                        full = _os_comp.path.join(dir_part, name) if dir_part else name
                        is_dir = _os_comp.path.isdir(_os_comp.path.join(base_dir, name))
                        completion_text = full + '/' if is_dir else full
                        yield Completion(
                            completion_text,
                            start_position=-len(partial),
                            display=name + '/' if is_dir else name,
                            display_meta='dir' if is_dir else '',
                        )

                def get_completions(self, document, complete_event):
                    text = document.text_before_cursor
                    # Slash command: only when input starts with '/'
                    if text.startswith('/'):
                        yield from self._slash_completions(text)
                    # @ file completion
                    elif '@' in text:
                        yield from self._file_completions(text)

            # Input history: persist to project root so ↑/↓ works across sessions
            try:
                _history_file = Path(config.SESSION_DIR) / "input_history.txt"
                _history = FileHistory(str(_history_file))
            except Exception:
                _history = InMemoryHistory()

            from prompt_toolkit.shortcuts import CompleteStyle

            from prompt_toolkit.filters import is_done
            from prompt_toolkit.keys import Keys

            @_kb.add('enter')
            def _enter_submit(event):
                """Enter = submit."""
                event.current_buffer.validate_and_handle()

            @_kb.add('escape', 'enter')
            def _alt_enter_newline(event):
                """Alt+Enter (Esc→Enter) = insert newline."""
                event.current_buffer.insert_text('\n')

            _multiline_prompt = PromptSession(
                multiline=True,
                key_bindings=_kb,
                history=_history,
                completer=_AtFileCompleter(),
                complete_while_typing=True,
                complete_style=CompleteStyle.COLUMN,
                prompt_continuation=lambda width, line_number, wrap_count: '... ',
            )
            _prompt_text = ANSI(Color.user("> ") + Color.RESET)
        except Exception as e:
            print(Color.warning(f"  [Multiline] prompt_toolkit unavailable ({type(e).__name__}: {e}) — falling back to single-line input"))

    if _textual_input_fn is None:
        print(Color.info("\nType 'exit' or 'quit' to stop."))
        print(Color.info("Type /help for available slash commands.\n"))

    # Wait up to 1s for warmup message to print before the first > prompt.
    # Prevents the [LLM] connected message from overwriting the prompt line.
    _warmup_thread.join(timeout=1.0)

    while True:
        try:
            if config.ENABLE_TODO_TRACKING:
                todo_tracker_main = TodoTracker.load(Path(config.TODO_FILE))
                # Sync global so _get_todo_tracker() in tools.py returns the same instance
                todo_tracker = todo_tracker_main

            try:
                if _multiline_prompt:
                    is_plan_turn = (agent_mode in ('plan', 'plan_q'))

                    if agent_mode == 'plan_q':
                        _plan_prompt = ANSI(Color.warning("Plan Mode ") + Color.CYAN + "> " + Color.RESET)
                        user_input = _multiline_prompt.prompt(_plan_prompt, multiline=False)
                    elif agent_mode == 'plan':
                        _has_non_approved = todo_tracker_main and any(
                            t.status != 'approved' for t in todo_tracker_main.todos
                        ) if todo_tracker_main else False
                        if _has_non_approved:
                            print(f"{Color.YELLOW}[Plan Mode]{Color.RESET} Plan ready. Confirm to execute or give feedback.")
                            print(f"  {Color.DIM}y        → execute plan now")
                            print(f"  yc       → execute + compress context (clean up conversation)")
                            print(f"  n        → cancel / revise")
                            print(f"  <other>  → feedback / refinement{Color.RESET}")
                            _plan_prompt = ANSI(Color.warning("Plan Confirmation [y/yc/n/feedback] ") + Color.CYAN + "> " + Color.RESET)
                            user_input = _multiline_prompt.prompt(_plan_prompt, multiline=False)
                        else:
                            user_input = _multiline_prompt.prompt(_prompt_text)
                    else:
                        user_input = _multiline_prompt.prompt(_prompt_text)
                else:
                    is_plan_turn = (agent_mode in ('plan', 'plan_q'))

                    _input_fn = _loop_deps.input_fn or input
                    if agent_mode == 'plan_q':
                        user_input = _input_fn(Color.warning("Plan Mode ") + Color.CYAN + "> " + Color.RESET)
                    elif agent_mode == 'plan':
                        _has_non_approved = todo_tracker_main and any(
                            t.status != 'approved' for t in todo_tracker_main.todos
                        ) if todo_tracker_main else False
                        if _has_non_approved:
                            print(f"{Color.YELLOW}[Plan Mode]{Color.RESET} Plan ready. Confirm to execute or give feedback.")
                            print(f"  {Color.DIM}y        → execute plan now")
                            print(f"  yc       → execute + compress context (clean up conversation)")
                            print(f"  n        → cancel / revise")
                            print(f"  <other>  → feedback / refinement{Color.RESET}")
                            user_input = _input_fn(Color.warning("Plan Confirmation [y/yc/n/feedback] ") + Color.CYAN + "> " + Color.RESET)
                        else:
                            user_input = _input_fn(Color.user("> ") + Color.RESET)
                    else:
                        _em = getattr(config, 'EXECUTION_MODE', 'agent')
                        if _em == 'chat':
                            _ci = getattr(config, 'CHAT_MAX_ITERATIONS', 1)
                            _em_prefix = f"[chat:{_ci}] "
                        elif _em != 'agent':
                            _em_prefix = f"[{_em}] "
                        else:
                            _em_prefix = ""
                        user_input = _input_fn(_em_prefix + Color.user("> ") + Color.RESET)
            except KeyboardInterrupt:
                # Real user Ctrl+C — re-raise to outer handler
                raise

            if user_input.lower() in ["exit", "quit"]:
                break

            if not user_input.strip():
                if getattr(config, "DEBUG_MODE", False):
                    print(f"[Keepalive] DEBUG: user_input was empty/whitespace, skipping: {repr(user_input[:80])}")
                continue

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

                # Handle /skills commands
                if user_input.startswith('/skills') and (len(user_input) == 7 or user_input[7] == ' '):
                    from core.skill_commands import handle_skills_command
                    skill_arg = user_input[8:].strip() if len(user_input) > 8 else ""
                    handle_skills_command(skill_arg, load_active_skills)
                    if _textual_emit_todo_fn:
                        # Refresh sidebar: reload todo and send current state (don't wipe it)
                        _tt = TodoTracker.load(Path(config.TODO_FILE)) if Path(config.TODO_FILE).exists() else None
                        if _tt and _tt.todos:
                            _textual_emit_todo_fn(_tt.format_simple())
                        else:
                            _textual_emit_todo_fn("")
                    continue

                result = slash_registry.execute(user_input)

                if result is not None:
                    # Check for special commands
                    if result == "CLEAR_ALL":
                        # 1. Delete .git directory
                        try:
                            curr = Path(os.path.abspath("."))
                            git_dir = next(
                                (p / ".git" for p in [curr] + list(curr.parents) if (p / ".git").exists()),
                                None)
                            if git_dir:
                                import shutil
                                shutil.rmtree(git_dir)
                        except Exception:
                            pass
                        # 2. Delete todo file
                        _todo_f = Path(config.TODO_FILE)
                        if _todo_f.exists():
                            _todo_f.unlink()
                        # 3. Reset conversation
                        system_msg = {"role": "system", "content": _build_system_prompt_str(agent_mode=agent_mode)}
                        messages = [system_msg]
                        save_conversation_history(messages)
                        print(Color.success("\n✅ All cleared: git + todo + conversation.\n"))
                        continue

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
                        if _textual_emit_context_fn:
                            _limit = config.MAX_CONTEXT_TOKENS
                            _est = sum(estimate_message_tokens(m) for m in messages)
                            _textual_emit_context_fn(_est, _limit)
                        if _textual_emit_todo_fn:
                            _textual_emit_todo_fn("")  # reset sidebar: tokens=0, clear todo
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

                    if result.startswith("PLAN_AND_RUN:"):
                        # Enter plan mode AND immediately run with the given task
                        task = result[len("PLAN_AND_RUN:"):]
                        agent_mode = "plan_q"
                        os.environ["PLAN_MODE"] = "true"
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
                        user_input = task  # fall through to LLM call

                    elif result.startswith("AGENT_MODE:"):
                        agent_mode = result.split(":", 1)[1]
                        if agent_mode == "plan":
                            agent_mode = "plan_q"  # first turn: questions only, tools blocked
                            os.environ["PLAN_MODE"] = "true"
                            print(Color.success("\n✅ Plan mode: clarify → explore → refine → user confirms → execute.\n"))
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
                            os.environ.pop("_PLAN_TODO_WRITE_COUNT", None)  # reset plan loop counter
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

                    if result.startswith("EXECUTION_MODE:"):
                        _em_parts = result.split(":", 2)
                        em = _em_parts[1]
                        _em_n = int(_em_parts[2]) if len(_em_parts) > 2 else 1
                        config.EXECUTION_MODE = em
                        config.STEP_BY_STEP_MODE = (em == 'step')
                        if em == 'chat':
                            config.CHAT_MAX_ITERATIONS = _em_n
                            if _em_n == 0:
                                _mode_label = "Chat (respond only, no tools)"
                            elif _em_n == 1:
                                _mode_label = "Chat (1 iteration with tools)"
                            else:
                                _mode_label = f"Chat ({_em_n} iterations with tools)"
                        else:
                            labels = {'agent': 'Agent (loop)', 'step': 'Step (1-action)'}
                            _mode_label = labels.get(em, em)
                        print(Color.success(f"\n✅ Mode: {_mode_label}\n"))
                        continue

                    if result.startswith("TODO_REVERT:"):
                        # Format: "TODO_REVERT:{N}:hard={True|False}:reset_conv={True|False}:{reason}"
                        _parts = result.split(":", 4)
                        _revert_n = int(_parts[1])
                        _hard = _parts[2].endswith("True")
                        _reset_conv = _parts[3].endswith("True")
                        _revert_reason = _parts[4] if len(_parts) > 4 else ""

                        import subprocess as _sp

                        # 1. Find approved tag
                        _tag_pattern = f"todo_{_revert_n}_approved*"
                        _tag_list = _sp.run(
                            ["git", "tag", "-l", _tag_pattern], capture_output=True, text=True
                        ).stdout.strip().splitlines()

                        if not _tag_list:
                            print(Color.error(f"\n❌ No approved git tag found for task {_revert_n}.\n"
                                              f"   (Pattern: {_tag_pattern})\n"))
                            continue

                        _tag = _tag_list[-1]

                        # 2. Show commits to be affected
                        _log_out = _sp.run(
                            ["git", "log", "--oneline", f"{_tag}..HEAD"],
                            capture_output=True, text=True
                        ).stdout.strip()

                        # 3. Show diff stat
                        _stat_out = _sp.run(
                            ["git", "diff", "--stat", f"{_tag}..HEAD"],
                            capture_output=True, text=True
                        ).stdout.strip()

                        # 4. Preview
                        _mode_label = "reset --hard" if _hard else "revert (new commit)"
                        print(Color.warning(f"\n⚠️  Revert Task {_revert_n} via git {_mode_label} to {_tag}"))
                        if _log_out:
                            print(Color.DIM + "\nCommits affected:")
                            for _line in _log_out.splitlines():
                                print(f"  {_line}")
                        if _stat_out:
                            print(Color.DIM + "\nFiles affected:")
                            for _line in _stat_out.splitlines()[-10:]:
                                print(f"  {_line}")
                        print(Color.RESET)

                        # 5. Confirm
                        _confirm = input(Color.warning("Proceed with rollback? [y/N] ")).strip().lower()
                        if _confirm != 'y':
                            print(Color.info("Cancelled.\n"))
                            continue

                        # 6. Git rollback
                        if _hard:
                            _sp.run(["git", "reset", "--hard", _tag], check=True)
                        else:
                            _rv = _sp.run(
                                ["git", "revert", "--no-commit", f"{_tag}..HEAD"],
                                capture_output=True, text=True
                            )
                            if _rv.returncode != 0:
                                _sp.run(["git", "revert", "--abort"])
                                print(Color.error(f"\n❌ Merge conflicts during revert. Try --hard flag.\n"))
                                continue
                            _sp.run(["git", "commit", "-m",
                                     f"rollback: task {_revert_n} - {_revert_reason or 'manual revert'}"])

                        # 7. Update todo status
                        _todo_path = Path(config.TODO_FILE)
                        if _todo_path.exists():
                            _tracker = TodoTracker.load(_todo_path)
                            _idx = _revert_n - 1
                            if 0 <= _idx < len(_tracker.todos):
                                _item = _tracker.todos[_idx]
                                _item.status = "pending"
                                _item.rejection_reason = f"↩ Rolled back: {_revert_reason}" if _revert_reason else "↩ Rolled back"
                                _item.approved_reason = ""
                                _tracker.current_index = _idx
                                _tracker.save()

                        _rollback_notice = (
                            f"[System] Rollback applied: Task {_revert_n} reverted to pending.\n"
                            f"Git tag: {_tag}\n"
                            f"Commits affected:\n{_log_out or '(none)'}\n"
                            f"Reason: {_revert_reason or '(none)'}\n"
                            f"The codebase has been rolled back. Re-read modified files before continuing."
                        )

                        # 8. Update conversation
                        if _reset_conv:
                            _snap = _load_conv_snapshot(_revert_n)
                            if _snap:
                                messages = _snap
                                messages.append({"role": "user", "content": _rollback_notice})
                                messages.append({"role": "assistant", "content": f"Understood. Conversation and code both restored to task {_revert_n} approval point."})
                                print(Color.success(f"\n✅ Rolled back to {_tag}. Task {_revert_n} → pending. Conversation restored.\n"))
                            else:
                                print(Color.warning(f"\n⚠️  No conversation snapshot found for task {_revert_n}. Keeping current conversation.\n"))
                                messages.append({"role": "user", "content": _rollback_notice})
                                messages.append({"role": "assistant", "content": "Understood. Code rolled back. No conversation snapshot available."})
                        else:
                            messages.append({"role": "user", "content": _rollback_notice})
                            messages.append({"role": "assistant", "content": f"Understood. Task {_revert_n} has been rolled back to pending state. I'll re-examine the codebase before retrying."})
                            print(Color.success(f"\n✅ Rolled back to {_tag}. Task {_revert_n} → pending.\n"))

                        save_conversation_history(messages)
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

                    elif result.startswith("WORKSPACE_SWITCH:"):
                        ws_name = result.split(":", 1)[1].strip()
                        try:
                            # Switch session context — flat project layout (single param)
                            _setup_session(ws_name)
                            # Load new workspace config (prompts, hooks, commands…)
                            _setup_workspace(ws_name)
                            # Mark active workspace in env
                            os.environ["ACTIVE_WORKSPACE"] = ws_name
                            # Rebuild system prompt with new workspace context
                            _new_sys = _build_system_prompt_str(agent_mode=agent_mode)
                            # Try to resume existing history for this workspace
                            _loaded = load_conversation_history()
                            if _loaded:
                                messages = _loaded
                                if messages and messages[0].get("role") == "system":
                                    messages[0]["content"] = _new_sys
                                else:
                                    messages.insert(0, {"role": "system", "content": _new_sys})
                                print(Color.success(f"\n✅ Workspace switched to '{ws_name}' (resumed existing context).\n"))
                            else:
                                messages = [{"role": "system", "content": _new_sys}]
                                print(Color.success(f"\n✅ Workspace switched to '{ws_name}' (new context).\n"))
                            # Persist and refresh context tracker
                            save_conversation_history(messages)
                            if messages and messages[0].get("role") == "system":
                                context_tracker.update_system_prompt(messages[0]["content"])
                            context_tracker.update_tools("")
                            context_tracker.update_memory({})
                            context_tracker.update_messages(messages, exclude_system=True)
                        except Exception as _ws_err:
                            print(Color.error(f"\n❌ Failed to switch workspace: {_ws_err}\n"))
                        continue

                    elif result.startswith("MODEL_SWITCH:"):
                        target = result.split(":", 1)[1]
                        if target == "1":
                            config.MODEL_NAME = config.PRIMARY_MODEL
                        elif target == "2":
                            config.MODEL_NAME = config.SECONDARY_MODEL
                        else:
                            config.MODEL_NAME = target
                        print(Color.success(f"\n✅ Model switched to: {config.MODEL_NAME}\n"))
                        if _textual_emit_todo_fn:
                            # Refresh sidebar: reload todo and send current state (don't wipe it)
                            _tt = TodoTracker.load(Path(config.TODO_FILE)) if Path(config.TODO_FILE).exists() else None
                            if _tt and _tt.todos:
                                _textual_emit_todo_fn(_tt.format_simple())
                            else:
                                _textual_emit_todo_fn("")
                        continue

                    if result.startswith("INJECT_TODO_TEMPLATE:"):
                        # Load template tasks and inject them into the todo tracker
                        tmpl_name = result[len("INJECT_TODO_TEMPLATE:"):]
                        try:
                            from workflow.loader import get_todo_template_registry
                            _reg = get_todo_template_registry()
                            _tasks = _reg.get_tasks(tmpl_name)
                            if _tasks:
                                _todo_path = Path(config.TODO_FILE)
                                if todo_tracker_main is None:
                                    todo_tracker_main = TodoTracker(_todo_path)
                                else:
                                    todo_tracker_main.clear()
                                todo_tracker_main.add_todos(_tasks)
                                todo_tracker_main.save()
                                print(Color.success(f"✅ Todo template '{tmpl_name}' loaded — {len(_tasks)} tasks"))
                                if _textual_emit_todo_fn:
                                    _textual_emit_todo_fn(todo_tracker_main.format_simple())
                            else:
                                print(Color.warning(f"⚠ Template '{tmpl_name}' not found. Available: {_reg.list()}"))
                        except Exception as _te:
                            print(Color.warning(f"⚠ Could not load template '{tmpl_name}': {_te}"))
                        continue

                    if result.startswith("INJECT_PROMPT:"):
                        # Replace user_input with the injected prompt and fall through to LLM
                        user_input = result[len("INJECT_PROMPT:"):]
                        # (do NOT continue — fall through to LLM call below)

                    elif not result.startswith("PLAN_AND_RUN:"):
                        # Regular command output (PLAN_AND_RUN already set user_input above — fall through)
                        if result:
                            print(result)
                        # Refresh Textual sidebar after any slash command that may change todo state
                        if _textual_emit_todo_fn and todo_tracker_main:
                            todo_tracker_main = TodoTracker.load(Path(config.TODO_FILE)) if Path(config.TODO_FILE).exists() else None
                            if todo_tracker_main and todo_tracker_main.todos:
                                _textual_emit_todo_fn(todo_tracker_main.format_simple())
                            else:
                                _textual_emit_todo_fn("")  # signal sidebar to clear
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
                except Exception:
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

            # Reset rejection counts on all todos — user input means fresh attempt.
            # This prevents stale rejection_count from triggering livelock guard
            # after the user has provided new guidance.
            if todo_tracker_main and todo_tracker_main.todos:
                for _t in todo_tracker_main.todos:
                    _t.rejection_count = 0

            # Add user message with turn tracking
            current_turn_id += 1
            messages.append({
                "role": "user",
                "content": user_input,
                "turn_id": current_turn_id,
                "timestamp": time.time(),
            })

            # --- Delegate per-turn logic to core/chat_loop.py ---
            _loop_state.messages = messages
            _loop_state.agent_mode = agent_mode
            _loop_state.todo_tracker = todo_tracker_main

            # Delegate per-turn processing to core/chat_loop
            _loop_state, _ctrl = _process_chat_turn(user_input, _loop_state, _loop_deps)

            messages = _loop_state.messages
            agent_mode = _loop_state.agent_mode
            rolling_window_size = _loop_state.rolling_window_size
            full_messages = _loop_state.full_messages
            auto_compression_threshold = _loop_state.auto_compression_threshold
            conversation_count = _loop_state.conversation_count
            is_first_turn = _loop_state.is_first_turn
            todo_tracker_main = _loop_state.todo_tracker

            if _ctrl == "break":
                break
            if _ctrl == "skip":
                continue

        except KeyboardInterrupt:
            print(Color.warning("\nExiting..."))
            save_conversation_history(messages, silent=False)
            try:
                on_conversation_end(messages)
            except Exception as e:
                print(Color.warning(f"[Warning] Failed to save knowledge: {e}"))
            import os as _os
            _os._exit(0)  # 강제 종료 — ThreadPoolExecutor hang 방지
        except EOFError:
            # stdin closed (e.g., from echo pipe) - exit gracefully
            print(Color.info("\n[System] Input stream closed. Exiting..."))
            save_conversation_history(messages, silent=False)
            break
        except Exception as e:
            import traceback
            print(Color.error(f"\nAn error occurred: {e}"))
            traceback.print_exc()
            pass

    # Save history on normal exit
    save_conversation_history(messages, silent=False)
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
    import argparse as _argparse
    _parser = _argparse.ArgumentParser(add_help=False)
    _parser.add_argument('-s', '--session', default=None)
    _parser.add_argument('-w', '--workspace', default=None,
                         help='Workspace name (e.g. default, verilog, spec-review)')
    _args, _ = _parser.parse_known_args()

    # Each project gets its own session context:
    # if -s is not explicitly given, use the workspace name as the project name
    # so each workspace maintains a separate conversation history.
    _project_name = _args.session or _args.workspace or 'default'
    _setup_session(_project_name)

    if _args.workspace:
        _setup_workspace(_args.workspace)

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
        print(Color.system(f"[Session] {_args.session}"))
        chat_loop()
