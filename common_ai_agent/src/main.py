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
_textual_emit_token_fn = None   # (in_tok, cache_tok, out_tok) → update cost sidebar directly
_textual_emit_tool_fn = None    # (text: str) → tool call header for web UI sidebar
_textual_emit_tool_result_fn = None  # (observation: str, tool: str) → tool result/observation for web UI
_textual_input_fn = None  # replaces input() when set
_textual_esc_check_fn = None # () → bool: TUI interrupt check
_textual_poll_human_input_fn = None  # () → str | None: poll mid-run human message
_textual_set_agent_running_fn = None  # (bool) → None: set agent_running flag on InputBridge
_textual_emit_slash_output_fn = None  # (text: str) → None: atlas-only safety-net emit for slash command output, bypasses streamBuffer pipeline
_textual_emit_mode_fn = None  # (mode: str) → None: notify frontend that agent_mode flipped (plan_q/plan/normal). Used to sync the UI mode pill when chat_loop's `y`/`yc` confirmation auto-promotes plan→normal — without this signal, the user typed "y", agent started executing, but the sidebar still showed PLAN.
_textual_active_session_fn = None  # () → str: read the per-thread active session (atlas_ui sets this; falls through to ATLAS_ACTIVE_SESSION env when None). Lets atlas_ui retire the per-request os.environ write that races between concurrent users.
_textual_active_ip_fn = None       # () → str: same idea for ATLAS_ACTIVE_IP — used by core/tools.py path validators.


def _get_active_session_str() -> str:
    """Return the active session triple ``owner/ip/workflow`` for *this*
    thread, preferring atlas_ui's contextvar via _textual_active_session_fn
    over the process-wide env var. The env fallback exists so terminal
    main.py runs (no atlas_ui hook installed) keep working unchanged.
    """
    fn = _textual_active_session_fn
    if fn is not None:
        try:
            v = fn()
        except Exception:
            v = ""
        if v:
            return str(v).strip().strip("/")
    return os.environ.get("ATLAS_ACTIVE_SESSION", "").strip().strip("/")


def _get_active_ip_str() -> str:
    """Per-thread ATLAS_ACTIVE_IP resolver. Mirrors _get_active_session_str
    but for the IP-only field. core/tools.py uses this for IP-rooted path
    validation, so a stale env mirror would let one user's IP claim
    another user's path."""
    fn = _textual_active_ip_fn
    if fn is not None:
        try:
            v = fn()
        except Exception:
            v = ""
        if v:
            return str(v).strip()
    return (os.environ.get("ATLAS_ACTIVE_IP") or "").strip()

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
        _available = []
        for c in candidates:
            if os.path.isdir(c):
                _available.extend(
                    d for d in sorted(os.listdir(c))
                    if os.path.isdir(os.path.join(c, d))
                       and os.path.exists(os.path.join(c, d, "workspace.json"))
                )
        _avail_str = ", ".join(_available) if _available else "(none found)"
        print(f"[Workflow] ERROR: workflow '{name}' not found.")
        print(f"[Workflow] Available workflows: {_avail_str}")
        print(f"[Workflow] Aborting. Use a valid workflow name from the list above.")
        sys.exit(1)

    # Import loader
    sys.path.insert(0, os.path.dirname(workflow_root))
    try:
        from workflow.loader import (
            load_workspace, merge_prompt, patch_todo_rules,
            register_script_hooks, get_todo_template_registry,
            register_workspace_commands,
        )
    except ImportError as e:
        print(f"[Workflow] Cannot import workflow.loader: {e}")
        return

    ws = load_workspace(name, project_root=Path(workflow_root).parent)
    if ws is None:
        print(f"[Workflow] Failed to load workflow '{name}'.")
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
                merged = merge_prompt(base, _ws_text, _ws_mode)
                # Surface incremental-write directives at the top of
                # the system prompt so the active workspace prompt can
                # branch on mode without each tool call re-checking
                # env. SSOT and RTL each have their own toggle; ssot-
                # gen / rtl-gen system_prompt.md documents both
                # processes and just reads which one to run.
                try:
                    import config as _cfg
                    ssot_mode = "incremental" if getattr(_cfg, "SSOT_INCREMENTAL_WRITE", True) else "one-shot"
                    rtl_mode  = "incremental" if getattr(_cfg, "RTL_INCREMENTAL_WRITE",  True) else "one-shot"
                    merged = (
                        f"[SSOT_WRITE_MODE: {ssot_mode}]\n"
                        f"[RTL_WRITE_MODE: {rtl_mode}]\n\n"
                        + merged
                    )
                except Exception:
                    pass
                # Inject the active IP + its workspace root so the agent
                # always knows where its files live. Without this the
                # agent has to guess from the chat context whether
                # `rtl/foo.sv` means `./rtl/foo.sv` or
                # `<ip>/rtl/foo.sv`, and that guess is often wrong.
                # Also tells the agent which facts are inferable so it
                # stops Q&A-ing the user for things already on disk.
                try:
                    _active_ip = _get_active_ip_str()
                    _active_session = (os.environ.get("ATLAS_ACTIVE_SESSION") or "").strip("/")
                    _session_parts = [p for p in _active_session.split("/") if p]
                    _workspace = _session_parts[-1] if len(_session_parts) >= 3 else (name or "")
                    _project_root = (
                        os.environ.get("ATLAS_PROJECT_ROOT")
                        or os.environ.get("PROJECT_ROOT")
                        or os.getcwd()
                    )
                    if _active_ip and _active_ip != "default":
                        _ip_root = os.path.join(_project_root, _active_ip)
                        _is_ssot_gen = (_workspace or "").lower() == "ssot-gen"
                        _is_rtl_gen = (_workspace or "").lower() == "rtl-gen"
                        ssot_format_block = ""
                        if _is_ssot_gen:
                            ssot_format_block = (
                                f"[SSOT_FORMAT: Every chat turn in ssot-gen is "
                                f"governed by the canonical SSOT yaml schema. "
                                f"The active SSOT target is "
                                f"`{_active_ip}/yaml/{_active_ip}.ssot.yaml`. "
                                f"When you write, propose, or reason about an "
                                f"SSOT field, use this structure (key sections, "
                                f"non-exhaustive):\n"
                                f"  identification: ip_name, kind, owner, version\n"
                                f"  purpose:        one_liner, primary_use_cases[]\n"
                                f"  bus_interface:  protocol, width, endianness, addressing\n"
                                f"  register_map:   [{{offset, name, reset, access, fields[]}}]\n"
                                f"  clock_reset:    clocks[], resets[], domains[], crossings[]\n"
                                f"  parameters:     [{{name, default, range, description}}]\n"
                                f"  dataflow:       sources[], sinks[], pipelines[]\n"
                                f"  interrupts:     sources[], priority, masking, ack_protocol\n"
                                f"  error_handling: detection[], reporting[], recovery[]\n"
                                f"  test_requirements: scenarios[], coverage_goals[]\n"
                                f"  security_safety:   threats[], mitigations[], safety_level\n"
                                f"  power_management:  power_domains[], low_power_modes[]\n"
                                f"  sub_modules:    [{{name, ownership, ssot_path?}}]\n"
                                f"  function_model: states[], transitions[]\n"
                                f"  debug:          observable_signals[], breakpoints[]\n"
                                f"  timing:         latencies, critical_paths\n"
                                f"  lint_assertions: rules[], waivers[]\n"
                                f"Rules:\n"
                                f"  - Output anything SSOT-relevant in this exact "
                                f"shape (yaml-compatible keys, lower_snake_case).\n"
                                f"  - Quote register addresses, signal names, "
                                f"encodings, and table rows verbatim from "
                                f"sources.\n"
                                f"  - Every transcribed fact gets a "
                                f"`# source: <path> L<line>` citation.\n"
                                f"  - Where evidence is missing, leave the field "
                                f"empty + add a `# gap: <reason>` comment. Do "
                                f"NOT invent placeholders, do NOT stamp the "
                                f"full template, do NOT use `(TBD)` as a "
                                f"shortcut.\n"
                                f"  - The canonical schema reference lives at "
                                f"`workflow/ssot-gen/rules/ssot-template.yaml` "
                                f"— read it when you need a field name you "
                                f"don't recognize, but do NOT copy its empty "
                                f"placeholders into the SSOT.]\n"
                            )
                        rtl_format_block = ""
                        if _is_rtl_gen:
                            rtl_format_block = (
                                f"[RTL_FROM_SSOT_CONTRACT: rtl-gen authors "
                                f"synthesizable SystemVerilog under "
                                f"`{_active_ip}/rtl/` using the SSOT yaml as "
                                f"the single source of truth.\n"
                                f"Source-of-truth path: "
                                f"`{_active_ip}/yaml/{_active_ip}.ssot.yaml`\n"
                                f"Coding rules: "
                                f"`workflow/rtl-gen/rules/rtl-coding-rules.md` "
                                f"(synthesizable .sv subset — read this before "
                                f"writing any RTL).\n"
                                f"Rules:\n"
                                f"  1. Read the SSOT yaml first. Pull module "
                                f"name, port list (clk, rst_n, bus signals, "
                                f"interrupts, debug), parameter defaults, "
                                f"register map, FSM states, and clock/reset "
                                f"domains directly from it. Do NOT invent "
                                f"signal names or widths that aren't in the "
                                f"SSOT.\n"
                                f"  2. If an SSOT field is empty or marked "
                                f"`# gap: ...`, do NOT silently fabricate the "
                                f"RTL detail. Emit `// TODO: SSOT gap <field> "
                                f"— <reason>` in the RTL and stop on that "
                                f"unit; return a `[SSOT TBD REPORT]` to "
                                f"ssot-gen instead of guessing.\n"
                                f"  3. Quote register address/encoding/width "
                                f"verbatim from SSOT. Each register write "
                                f"should carry a `// source: yaml/<ip>.ssot.yaml "
                                f"register_map.<name>` comment.\n"
                                f"  4. RTL files live under `{_active_ip}/rtl/` "
                                f"(one file per top/sub_module). Filelist "
                                f"goes to `{_active_ip}/list/{_active_ip}.f`.\n"
                                f"  5. Do not write SSOT yaml, tests, or "
                                f"firmware from rtl-gen — that's ssot-gen / "
                                f"tb-gen territory. If you find the SSOT "
                                f"itself is wrong, return a `[SSOT TBD REPORT]` "
                                f"and stop, do not patch the SSOT yourself.\n"
                                f"  6. Emit `[RTL HANDOFF]` once each module "
                                f"compiles cleanly with the configured lint.]\n"
                            )
                        merged = (
                            f"[PROJECT_ROOT: {_project_root}]\n"
                            f"[ACTIVE_WORKSPACE: {_workspace or 'default'}]\n"
                            f"[ACTIVE_SESSION: {_active_session or 'default'}]\n"
                            f"[ACTIVE_IP: {_active_ip}]\n"
                            f"[IP_ROOT: {_ip_root}]\n"
                            f"[IP_FILES_HINT: All per-IP artifacts (rtl/, yaml/, tb/, "
                            f"req/, list/, sim/, sdc/, lint/, doc/, wiki/) live under "
                            f"{_active_ip}/. Use relative paths from IP_ROOT or "
                            f"prefix project-root paths with {_active_ip}/.]\n"
                            f"[PATH_SCOPE: Keep file reads, writes, edits, grep/find "
                            f"searches, and run_command cwd/paths inside {_active_ip}/ "
                            f"unless the user explicitly names another project path. "
                            f"If a path already starts with {_active_ip}/, use it once "
                            f"and do not rewrite it as {_active_ip}/{_active_ip}/... . "
                            f"For SSOT, the canonical path is "
                            f"{_active_ip}/yaml/{_active_ip}.ssot.yaml.]\n"
                            + ssot_format_block
                            + rtl_format_block +
                            f"[NO_QA_FOR_DERIVABLE_FACTS: Do not ask the user a "
                            f"question whose answer is already derivable from "
                            f"PROJECT_ROOT, ACTIVE_IP, IP_ROOT, the IP wiki "
                            f"({_active_ip}/wiki/), the imports directory "
                            f"({_active_ip}/req/imports/), the existing SSOT "
                            f"draft ({_active_ip}/yaml/{_active_ip}.ssot.yaml), "
                            f"or any file on disk you can read. Read the source "
                            f"first. Only ask for genuinely undetermined design "
                            f"decisions the user has not yet expressed in any "
                            f"form.]\n\n"
                            + merged
                        )
                    elif _workspace:
                        merged = (
                            f"[PROJECT_ROOT: {_project_root}]\n"
                            f"[ACTIVE_WORKSPACE: {_workspace}]\n\n"
                            + merged
                        )
                    else:
                        merged = f"[PROJECT_ROOT: {_project_root}]\n\n" + merged
                except Exception:
                    pass
                try:
                    merged = _pb.apply_memory_override(merged, memory_system, workflow=name)
                except Exception:
                    pass
                return merged

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
    # Default merge mode is "append" so workflow prompts extend the rich
    # default (universal preservation rules) instead of fully replacing it.
    # Writes BOTH the new "compression_user_instruction" key and the legacy
    # "compression_system" key for backward compatibility — see
    # compressor._load_default_compression_prompt for the read priority.
    try:
        import core.compressor as _comp
        if ws.compression_prompt_text:
            base_comp = _ORIG_COMPRESSION_PROMPT or getattr(_comp, 'STRUCTURED_SUMMARY_PROMPT', "")
            _comp.STRUCTURED_SUMMARY_PROMPT = merge_prompt(
                base_comp,
                ws.compression_prompt_text,
                getattr(ws, "compression_prompt_mode", "append"),
            )
            _b._WORKSPACE_HOOK_MESSAGES["compression_user_instruction"] = _comp.STRUCTURED_SUMMARY_PROMPT
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
        print(f"[Workflow] Warning: could not register commands: {e}")

    # Store description so prompt_builder can include it in the identity line
    if ws.description:
        os.environ["ACTIVE_WORKSPACE_DESC"] = ws.description

    print(f"[Workflow] '{name}' loaded from {workflow_root}/{name}")


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
# Initialize memory system if enabled. ENABLE_MEMORY_RULES keeps explicit
# /memory rules injectable even when auto preference extraction is off.
memory_system = None
if getattr(config, "ENABLE_MEMORY", False) or getattr(config, "ENABLE_MEMORY_RULES", True):
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


orchestrator = None  # Legacy sub-agent system deprecated; background agents are used instead.

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
        available_tools=tools.filtered_available_tools(),
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
    """Wrapper: delegates to core.compressor with main.py dependencies injected.
    Pre-compression analysis is handled inside core.compressor.compress_history
    (only runs after threshold checks confirm compression is needed).
    """
    result = _compress_history_impl(
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
    # Update sidebar immediately after any compression (auto or /compact)
    if _textual_emit_context_fn and not dry_run and result is not messages:
        _limit = config.MAX_CONTEXT_TOKENS
        _est = sum(estimate_message_tokens(m) for m in result)
        _textual_emit_context_fn(_est, _limit)
    return result


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
    effective_available_tools = tools.filtered_available_tools()
    # Native tool call mode: pass tools schemas to LLM API
    _native_tools = None
    if getattr(config, "ENABLE_NATIVE_TOOL_CALLS", False):
        try:
            from core.tool_schema import get_tool_schemas
            _compact = getattr(config, "TOOL_SCHEMA_COMPACT", False)
            _native_tools = get_tool_schemas(list(effective_available_tools.keys()), compact=_compact)
        except Exception:
            pass
    if _native_tools:
        _llm_fn = (lambda msg, stop=None, _t=_native_tools: chat_completion_stream(msg, stop=stop, suppress_spinner=True, tools=_t)) \
            if _is_tui else (lambda msg, stop=None, _t=_native_tools: chat_completion_stream(msg, stop=stop, tools=_t))
    else:
        _llm_fn = (lambda msg, stop=None: chat_completion_stream(msg, stop=stop, suppress_spinner=True)) \
            if _is_tui else chat_completion_stream
    # Orchestrator chat injector — best-effort. Built lazily so test
    # harnesses that don't import the atlas DB still work. The bridge
    # is resolved via the shared registry written by atlas_ui at boot;
    # standalone CLI runs without a bridge still get chat (the DB-level
    # chat_consumed ledger is the source of truth, bridge watermark is
    # just an in-memory fast path).
    try:
        from core.atlas_db import AtlasDB as _OrchDB
        from core.orchestrator_inject import (
            build_orchestrator_inject_fn,
            get_registered_bridge,
        )
        _orch_inject = build_orchestrator_inject_fn(
            _OrchDB(), get_registered_bridge()
        )
    except Exception:
        _orch_inject = None
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
        orchestrator_inject_fn=_orch_inject,
        orchestrator=orchestrator,
        procedural_memory=procedural_memory,
        graph_lite=graph_lite,
        hook_registry=hook_registry,
        available_tools=effective_available_tools,
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
        emit_token_fn=_textual_emit_token_fn,
        emit_tool_fn=_textual_emit_tool_fn,
        emit_tool_result_fn=_textual_emit_tool_result_fn,
        poll_human_input_fn=_textual_poll_human_input_fn,
        # Disable EscapeWatcher in Textual mode — Textual owns stdin; raw tty read
        # conflicts with Textual's input handling, causing false ESC triggers.
        # Instead, use the TUI's mapped escape key via the callback.
        esc_check_fn=_textual_esc_check_fn if _textual_input_fn is not None else None,
        esc_start_fn=(lambda: None) if _textual_input_fn is not None else None,
        esc_stop_fn=(lambda: None) if _textual_input_fn is not None else None,
    )
    if _textual_set_agent_running_fn:
        _textual_set_agent_running_fn(True)
    try:
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
    finally:
        if _textual_set_agent_running_fn:
            _textual_set_agent_running_fn(False)


# --- 7. Session Setup ---

from core.session_setup import setup_session as _setup_session


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
        _backend_url = config.BASE_URL
        if getattr(config, "CURSOR_AGENT_ENABLE", False):
            _backend_url = "cursor-agent"
        elif getattr(config, "CLAUDE_CLI_ENABLE", False):
            _backend_url = "claude-cli"
        print(format_startup_banner(
            base_url=_backend_url,
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
        headless=bool(getattr(config, "HEADLESS_MODE", False)),
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
    # Headless mode (``--headless`` / ``--prompt-file``) needs builtin ``input()``
    # because ``PromptSession.prompt()`` does not raise ``EOFError`` reliably when
    # stdin is a redirected regular file at EOF — the chat loop would then idle
    # forever after consuming the seed instead of writing ``exit.json`` and
    # terminating cleanly. Skipping ``PromptSession`` falls through to the
    # ``_input_fn = _loop_deps.input_fn or input`` branch below, where ``input()``
    # raises ``EOFError`` on file EOF and the existing handler at the bottom of
    # ``chat_loop`` writes ``exit.json`` and breaks.
    if config.ENABLE_MULTILINE_INPUT and _textual_input_fn is None and not bool(getattr(config, "HEADLESS_MODE", False)):
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

            # ── Exit: Ctrl+Q only ───────────────────────────────────────────────
            # NOTE: Double-ESC removed — macOS Terminal sends ESC sequences
            # (^[[O focus-out, ^[[I focus-in) when switching tabs, and these
            # can be seconds apart, making reliable debounce impossible.
            # Use Ctrl+Q to exit instead.

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
                            # Emit to BOTH terminal (colored) and Atlas/Textual
                            # (plain via _textual_emit_content_fn) so the Atlas
                            # web UI sees the plan-confirmation menu instead of
                            # nothing — same one-or-the-other pattern used for
                            # the mode-flip banner. The user types `y` (or
                            # clicks via the existing y-bypass-scope-prefix
                            # path) to approve and trigger plan→normal flip.
                            _plan_menu_lines = [
                                "[Plan Mode] Plan ready. Confirm to execute or give feedback.",
                                "  y        → execute plan now",
                                "  yc       → execute + compress context (clean up conversation)",
                                "  n        → cancel / revise",
                                "  <other>  → feedback / refinement",
                            ]
                            if _textual_emit_content_fn is not None:
                                try:
                                    for _l in _plan_menu_lines:
                                        _textual_emit_content_fn(_l)
                                    if _textual_emit_flush_fn is not None:
                                        _textual_emit_flush_fn()
                                except Exception: pass
                            else:
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
                            # Emit to BOTH terminal (colored) and Atlas/Textual
                            # (plain via _textual_emit_content_fn) so the Atlas
                            # web UI sees the plan-confirmation menu instead of
                            # nothing — same one-or-the-other pattern used for
                            # the mode-flip banner. The user types `y` (or
                            # clicks via the existing y-bypass-scope-prefix
                            # path) to approve and trigger plan→normal flip.
                            _plan_menu_lines = [
                                "[Plan Mode] Plan ready. Confirm to execute or give feedback.",
                                "  y        → execute plan now",
                                "  yc       → execute + compress context (clean up conversation)",
                                "  n        → cancel / revise",
                                "  <other>  → feedback / refinement",
                            ]
                            if _textual_emit_content_fn is not None:
                                try:
                                    for _l in _plan_menu_lines:
                                        _textual_emit_content_fn(_l)
                                    if _textual_emit_flush_fn is not None:
                                        _textual_emit_flush_fn()
                                except Exception: pass
                            else:
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

            _atlas_active_session = _get_active_session_str()
            if _atlas_active_session and _atlas_active_session != os.environ.get("ATLAS_SESSION_APPLIED", ""):
                try:
                    _setup_session(_atlas_active_session)
                    os.environ["ATLAS_SESSION_APPLIED"] = _atlas_active_session
                    _new_sys = _build_system_prompt_str(agent_mode=agent_mode)
                    _loaded = load_conversation_history()
                    if _loaded:
                        messages = _loaded
                        if messages and messages[0].get("role") == "system":
                            messages[0]["content"] = _new_sys
                        else:
                            messages.insert(0, {"role": "system", "content": _new_sys})
                    else:
                        messages = [{"role": "system", "content": _new_sys}]
                    save_conversation_history(messages)
                    if config.ENABLE_TODO_TRACKING:
                        todo_tracker_main = (
                            TodoTracker.load(Path(config.TODO_FILE))
                            if Path(config.TODO_FILE).exists()
                            else TodoTracker(Path(config.TODO_FILE))
                        )
                        todo_tracker = todo_tracker_main
                        if _textual_emit_todo_fn is not None:
                            try:
                                _textual_emit_todo_fn(
                                    todo_tracker_main.format_simple()
                                    if todo_tracker_main and todo_tracker_main.todos
                                    else ""
                                )
                            except Exception:
                                pass
                    if messages and messages[0].get("role") == "system":
                        context_tracker.update_system_prompt(messages[0]["content"])
                    context_tracker.update_messages(messages, exclude_system=True)
                except Exception as _atlas_session_err:
                    if _textual_emit_content_fn is not None:
                        try:
                            _textual_emit_content_fn(f"[Session] failed to switch to {_atlas_active_session}: {_atlas_session_err}")
                            if _textual_emit_flush_fn is not None:
                                _textual_emit_flush_fn()
                        except Exception:
                            pass

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
                    # Refresh the SKILL sidebar immediately so the user
                    # sees the activation/deactivation reflected without
                    # waiting for the next LLM call. Pass (0, 0) — the
                    # emitter reads the current token count internally.
                    if _textual_emit_context_fn:
                        try:
                            _textual_emit_context_fn(0, 0)
                        except Exception:
                            pass
                    # Emit the skills list text to the chat feed so the
                    # browser shows the updated list (atlas WS path).
                    # Without this the slash handler only refreshes the
                    # sidebar and the chat feed stays blank for /skills.
                    _skills_result = slash_registry.execute(user_input)
                    if _skills_result and _textual_emit_content_fn is not None:
                        try:
                            import re as _re_sk
                            _ansi_sk = _re_sk.compile(r"\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)")
                            _clean_sk = _ansi_sk.sub("", _skills_result).rstrip("\n")
                            _longest_sk = max((len(m.group(0)) for m in re.finditer(r"`+", _clean_sk)), default=0)
                            _fence_sk = "`" * max(3, _longest_sk + 1)
                            _payload_sk = f"{_fence_sk}\n" + "\n".join(_clean_sk.splitlines() or [""]) + f"\n{_fence_sk}\n"
                            _textual_emit_content_fn(_payload_sk)
                            if _textual_emit_slash_output_fn is not None:
                                try:
                                    _textual_emit_slash_output_fn(_payload_sk)
                                except Exception:
                                    pass
                            if _textual_emit_flush_fn is not None:
                                _textual_emit_flush_fn()
                        except Exception:
                            pass
                    if _textual_set_agent_running_fn is not None:
                        try:
                            _textual_set_agent_running_fn(False)
                        except Exception:
                            pass
                    continue

                result = slash_registry.execute(user_input)

                if result is not None:
                    if user_input.split(maxsplit=1)[0] in ("/memory", "/mem"):
                        try:
                            _new_sys = _build_system_prompt_str(agent_mode=agent_mode)
                            if messages and messages[0].get("role") == "system":
                                messages[0]["content"] = _new_sys
                            else:
                                messages.insert(0, {"role": "system", "content": _new_sys})
                            save_conversation_history(messages)
                            context_tracker.update_system_prompt(_new_sys)
                            context_tracker.update_messages(messages, exclude_system=True)
                        except Exception as _mem_err:
                            print(Color.warning(f"\n⚠ Memory updated, but prompt refresh failed: {_mem_err}\n"))

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
                            proc = subprocess.run(
                                ["git", "diff"],
                                capture_output=True,
                                text=True,
                                encoding="utf-8",
                                errors="replace",
                            )
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
                            _msg = "✅ Plan mode: clarify → explore → refine → user confirms → execute."
                            # Avoid double-rendering in Textual/Atlas mode —
                            # print() also lands in the Textual RichLog (or
                            # the Atlas log file/stdout), and _emit_content
                            # already renders as a markdown card. Pick ONE.
                            if _textual_emit_content_fn is not None:
                                try: _textual_emit_content_fn(_msg)
                                except Exception: pass
                            else:
                                print(Color.success("\n" + _msg + "\n"))
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
                            _msg = "✅ Normal mode — tools enabled."
                            if _textual_emit_content_fn is not None:
                                try: _textual_emit_content_fn(_msg)
                                except Exception: pass
                            else:
                                print(Color.success("\n" + _msg + "\n"))
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

                    if result.startswith("ASK_USER_MODE:"):
                        ask_mode = result.split(":", 1)[1].strip().lower()
                        if ask_mode not in ("interactive", "pipeline", "ci", "auto-select"):
                            print(Color.error(f"\n❌ Invalid ask_user mode: {ask_mode}\n"))
                            continue
                        os.environ["ASK_USER_EXEC_MODE"] = ask_mode
                        _labels = {
                            "interactive": "Interactive (ask_user enabled)",
                            "pipeline": "Pipeline (ask_user blocked, continue)",
                            "ci": "CI (ask_user blocked, fail-fast)",
                            "auto-select": "Auto-select (ask_user answers recommended defaults and records approved QA)",
                        }
                        print(Color.success(f"\n✅ AskUser mode: {_labels.get(ask_mode, ask_mode)}\n"))
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
                            ["git", "tag", "-l", _tag_pattern],
                            capture_output=True,
                            text=True,
                            encoding="utf-8",
                            errors="replace",
                        ).stdout.strip().splitlines()

                        if not _tag_list:
                            print(Color.error(f"\n❌ No approved git tag found for task {_revert_n}.\n"
                                              f"   (Pattern: {_tag_pattern})\n"))
                            continue

                        _tag = _tag_list[-1]

                        # 2. Show commits to be affected
                        _log_out = _sp.run(
                            ["git", "log", "--oneline", f"{_tag}..HEAD"],
                            capture_output=True,
                            text=True,
                            encoding="utf-8",
                            errors="replace",
                        ).stdout.strip()

                        # 3. Show diff stat
                        _stat_out = _sp.run(
                            ["git", "diff", "--stat", f"{_tag}..HEAD"],
                            capture_output=True,
                            text=True,
                            encoding="utf-8",
                            errors="replace",
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
                                capture_output=True,
                                text=True,
                                encoding="utf-8",
                                errors="replace",
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
                            if _textual_emit_context_fn:
                                _limit = config.MAX_CONTEXT_TOKENS
                                _est = sum(estimate_message_tokens(m) for m in messages)
                                _textual_emit_context_fn(_est, _limit)

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

                        def _ws_emit(line: str) -> None:
                            """Mirror workspace-switch status to the right
                            sink. In Textual/Atlas mode the explicit
                            emit feeds the chat; print() would *also*
                            fire because stdout is captured and routed
                            into the chat → the same line appears twice
                            (once plain, once as a bordered panel). So
                            we only print() in plain-CLI mode."""
                            if _textual_emit_content_fn is not None:
                                try:
                                    import re as _re
                                    _ansi = _re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)")
                                    for _l in _ansi.sub("", line).splitlines() or [""]:
                                        _textual_emit_content_fn(_l)
                                except Exception:
                                    pass
                            else:
                                print(line)

                        try:
                            # Switch session context. Atlas can select a
                            # scoped session such as mcu_top/rtl-gen; keep
                            # that namespace instead of collapsing every IP
                            # into the flat workflow name.
                            _active_session = _get_active_session_str()
                            # Session paths normally carry three
                            # segments — <owner>/<ip>/<workflow>. Pad
                            # missing segments with "default" so the
                            # switch always works even before the user
                            # picks an IP; nothing downstream cares if
                            # the IP slot is literally "default".
                            _parts = [p for p in (_active_session or "").split("/") if p]
                            _owner = _parts[0] if len(_parts) >= 1 and _parts[0] else "default"
                            _ip = _parts[1] if len(_parts) >= 2 and _parts[1] else "default"
                            _target_session = f"{_owner}/{_ip}/{ws_name}"
                            _setup_session(_target_session)
                            if _active_session:
                                os.environ["ATLAS_SESSION_APPLIED"] = _active_session
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
                                _ws_emit(Color.success(f"\n✅ Workflow switched to '{ws_name}' (resumed existing context).\n"))
                            else:
                                messages = [{"role": "system", "content": _new_sys}]
                                _ws_emit(Color.success(f"\n✅ Workflow switched to '{ws_name}' (new context).\n"))
                            # Persist and refresh context tracker
                            save_conversation_history(messages)
                            if messages and messages[0].get("role") == "system":
                                context_tracker.update_system_prompt(messages[0]["content"])
                            context_tracker.update_tools("")
                            context_tracker.update_memory({})
                            context_tracker.update_messages(messages, exclude_system=True)

                            # Reload todo_tracker_main from the NEW workspace's
                            # todo.json. Without this, the agent keeps operating
                            # on the OLD workspace's todos because the tracker
                            # was bound at boot to the old TODO_FILE path.
                            # _setup_session above already changed config.TODO_FILE
                            # to .session/<ws_name>/todo.json — we just need to
                            # rebind the in-memory tracker accordingly.
                            if config.ENABLE_TODO_TRACKING:
                                _new_todo_path = Path(config.TODO_FILE)
                                todo_tracker_main = (
                                    TodoTracker.load(_new_todo_path)
                                    if _new_todo_path.exists()
                                    else TodoTracker(_new_todo_path)
                                )
                                # Mirror to the module-level `todo_tracker`
                                # global. core/tools.py's _get_todo_tracker
                                # reads `main.todo_tracker` (not _main), so
                                # without this rebind every todo_write after
                                # a workspace switch would keep targeting the
                                # OLD workspace's todo.json (.session/default/
                                # vs .session/default/<ip>/<wf>/), and the
                                # panel showed an empty list because UI was
                                # reading the new path while writes went
                                # somewhere else. chat_loop has no `global`
                                # declaration so a plain `todo_tracker = ...`
                                # would only rebind a local — go through
                                # sys.modules to update the real attribute.
                                try:
                                    import sys as _sys_ws
                                    _main_mod = _sys_ws.modules.get('main') or _sys_ws.modules.get('src.main')
                                    if _main_mod is not None:
                                        _main_mod.todo_tracker = todo_tracker_main
                                except Exception:
                                    pass
                                # Push the new workspace's todos to the sidebar
                                # (clears stale entries, shows new ones if any).
                                if _textual_emit_todo_fn is not None:
                                    try:
                                        if todo_tracker_main and todo_tracker_main.todos:
                                            _textual_emit_todo_fn(todo_tracker_main.format_simple())
                                        else:
                                            _textual_emit_todo_fn("")
                                    except Exception: pass
                        except Exception as _ws_err:
                            _ws_emit(Color.error(f"\n❌ Failed to switch workflow: {_ws_err}\n"))
                        if _textual_emit_flush_fn is not None:
                            try: _textual_emit_flush_fn()
                            except Exception: pass
                        if _textual_set_agent_running_fn is not None:
                            try:
                                _textual_set_agent_running_fn(False)
                            except Exception:
                                pass
                        continue

                    elif result.startswith("MODEL_SWITCH:"):
                        target = result.split(":", 1)[1]
                        if target == "1":
                            _mark_override = getattr(config, "mark_runtime_model_override", None)
                            if callable(_mark_override):
                                _mark_override()
                            config.MODEL_NAME = config.PRIMARY_MODEL
                            os.environ["LLM_MODEL_NAME"] = config.MODEL_NAME
                            os.environ["MODEL_NAME"] = config.MODEL_NAME
                            print(Color.success(f"\n✅ Model switched to: {config.MODEL_NAME}\n"))
                        elif target == "2":
                            _mark_override = getattr(config, "mark_runtime_model_override", None)
                            if callable(_mark_override):
                                _mark_override()
                            config.MODEL_NAME = config.SECONDARY_MODEL
                            os.environ["LLM_MODEL_NAME"] = config.MODEL_NAME
                            os.environ["MODEL_NAME"] = config.MODEL_NAME
                            print(Color.success(f"\n✅ Model switched to: {config.MODEL_NAME}\n"))
                        elif target.startswith("profile:"):
                            # Multi-provider profile switch — flip BASE_URL,
                            # API_KEY, and MODEL_NAME atomically. set_active_profile
                            # also mirrors to os.environ so cmux workers pick up
                            # the new credentials on their next call.
                            _pname = target.split(":", 1)[1]
                            if config.set_active_profile(_pname):
                                print(Color.success(
                                    f"\n✅ Profile '{_pname}' active "
                                    f"→ {config.MODEL_NAME} @ {config.BASE_URL}\n"))
                            else:
                                print(Color.warning(
                                    f"\n⚠ Profile '{_pname}' not defined "
                                    f"(no PROFILE_{_pname}_MODEL in .env)\n"))
                        elif target.startswith("cli:"):
                            _cli_name = target.split(":", 1)[1]
                            if config.activate_cli_backend(_cli_name):
                                from src.llm_client import get_active_model as _get_active_model
                                print(Color.success(
                                    f"\n✅ CLI backend active → {_get_active_model()}\n"))
                            else:
                                print(Color.error(f"\n❌ Unknown CLI backend: {_cli_name}\n"))
                        elif target.startswith("opencode:"):
                            # /model gpt | /model gpt-5.5 — route to ChatGPT OAuth.
                            # activate_opencode_oauth swaps BASE_URL → Codex,
                            # MODEL_NAME → bare, and sets USE_RESPONSES_API=True.
                            _bare = target.split(":", 1)[1]
                            if config.activate_opencode_oauth(_bare):
                                print(Color.success(
                                    f"\n✅ Opencode-OAuth active → "
                                    f"{config.MODEL_NAME} @ {config.BASE_URL}\n"))
                            else:
                                print(Color.error(
                                    f"\n❌ '{_bare}' needs ChatGPT OAuth but no "
                                    f"opencode credential is available.\n"
                                    f"   Run: python -m src.opencode_backend login\n"))
                        else:
                            # Bare model name override (no provider switch)
                            _deact_cli = getattr(config, "deactivate_cli_backends", None)
                            if callable(_deact_cli):
                                _deact_cli()
                            _mark_override = getattr(config, "mark_runtime_model_override", None)
                            if callable(_mark_override):
                                _mark_override()
                            config.MODEL_NAME = target
                            os.environ["LLM_MODEL_NAME"] = config.MODEL_NAME
                            os.environ["MODEL_NAME"] = config.MODEL_NAME
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
                            _tmpl = _reg.get(tmpl_name) or {}
                            _tasks = _reg.get_tasks(tmpl_name)
                            if _tasks:
                                _todo_path = Path(config.TODO_FILE)
                                if todo_tracker_main is None:
                                    todo_tracker_main = TodoTracker(_todo_path)
                                else:
                                    todo_tracker_main.clear()
                                todo_tracker_main.add_todos(_tasks)
                                todo_tracker_main.save()
                                _lock = bool(_tmpl.get("lock_additions", True))
                                if _lock:
                                    os.environ["TODO_TEMPLATE_LOCK_ADDITIONS"] = "1"
                                    os.environ["TODO_TEMPLATE_LOCK_NAME"] = tmpl_name
                                else:
                                    os.environ.pop("TODO_TEMPLATE_LOCK_ADDITIONS", None)
                                    os.environ.pop("TODO_TEMPLATE_LOCK_NAME", None)
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
                            # Mirror slash output to the web UI — print()
                            # only hits stdout (and the uvicorn log file in
                            # atlas mode), which leaves the browser blank.
                            if _textual_emit_content_fn is not None:
                                try:
                                    import re as _re
                                    # Strip ANSI escapes — they show up as
                                    # garbage like ⎵[2m in the markdown
                                    # rendered HTML.
                                    _ansi = _re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)")
                                    _clean = _ansi.sub("", result).rstrip("\n")
                                    # Browser-friendly fallback for the
                                    # "fancy" glyphs the terminal Color
                                    # helpers use — boxes, pause/play, eye-
                                    # check, etc. don't render cleanly in
                                    # browser default fonts and the user
                                    # sees them as tofu / wrong widths.
                                    _glyph = {
                                        "──":  "──",  # box drawing already wide-supported
                                        "⏸":  "[ ]",  # pending
                                        "▶":  "[>]",  # in-progress
                                        "👀":  "[.]",  # completed
                                        "✅":  "[v]",  # approved
                                        "❌":  "[x]",  # rejected
                                        "⎿":  "└─",   # tool brief
                                    }
                                    for _src, _dst in _glyph.items():
                                        _clean = _clean.replace(_src, _dst)
                                    # Wrap in a fenced code block so
                                    # whitespace, table layouts, and `*` /
                                    # `#` characters render verbatim instead
                                    # of being parsed as markdown emphasis
                                    # / headings.
                                    # Emit as a single payload with explicit
                                    # newlines between every line. Per-call
                                    # emits used to ship lines without a
                                    # trailing "\n", so the WS bridge
                                    # concatenated them into one long string
                                    # ("```Line1Line2```") and the browser
                                    # rendered it as continuous text.
                                    # Nesting-safe fence: pick a backtick run
                                    # length one longer than the longest run
                                    # already present in the body, so any
                                    # embedded ``` doesn't terminate our wrap
                                    # early (which previously caused marked.js
                                    # to split the block into ~10 fragments).
                                    _longest = max((len(m.group(0)) for m in _re.finditer(r"`+", _clean)), default=0)
                                    _fence = "`" * max(3, _longest + 1)
                                    _payload = f"{_fence}\n" + "\n".join(_clean.splitlines() or [""]) + f"\n{_fence}\n"
                                    # Emit through the streaming pipeline
                                    # (token → slash_output → flush).
                                    # Order matters: slash_output is a
                                    # safety net that deduplicates against
                                    # streamBufferRef in workspace.jsx —
                                    # it MUST fire after token (so the
                                    # payload is in the buffer) but BEFORE
                                    # flush (which parks/clears the buffer).
                                    # Token        → appends to streamBufferRef
                                    # slash_output → checks buffer, skips if found
                                    # flush        → parks buffer into feed
                                    _textual_emit_content_fn(_payload)
                                    if _textual_emit_slash_output_fn is not None:
                                        try:
                                            _textual_emit_slash_output_fn(_payload)
                                        except Exception:
                                            pass
                                    if _textual_emit_tool_result_fn is not None:
                                        try:
                                            _textual_emit_tool_result_fn(_clean, "slash")
                                        except Exception:
                                            pass
                                    if _textual_emit_flush_fn is not None:
                                        _textual_emit_flush_fn()
                                except Exception:
                                    pass
                            # Slash commands don't run the LLM, so the
                            # agent_state(running:true/false) bracket never
                            # fires. Frontend submitMsg optimistically sets
                            # streaming=true for every prompt — without an
                            # explicit running:false here, the "Agent is
                            # working / streaming…" banner stays stuck after
                            # /context, /help, /skills, etc. Emit it now so
                            # workspace.jsx's agent_state handler can call
                            # turnEnd() and park the slash output.
                            if _textual_set_agent_running_fn is not None:
                                try:
                                    _textual_set_agent_running_fn(False)
                                except Exception:
                                    pass
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
                    active_memory = (
                        memory_system.for_user(_get_active_session_str())
                        if hasattr(memory_system, "for_user")
                        else memory_system
                    )
                    result = active_memory.auto_extract_and_update(user_input)
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

    # Headless mode: emit a structured exit.json next to the session state so
    # an external driver (CI, parent agent, shell script) can inspect the run
    # outcome without parsing ANSI logs.
    if bool(getattr(config, "HEADLESS_MODE", False)):
        _write_exit_json(messages)


def _write_exit_json(messages: list) -> None:
    """Write a session-scoped ``exit.json`` summarising the headless run.

    Schema kept deliberately small; downstream consumers depend on stable
    field names. ``status`` is best-effort — refined once the workflow stage
    engine starts feeding richer signals (gate result, blocker count, etc.).
    """
    try:
        import json as _json
        import datetime as _datetime
        session_dir = getattr(config, "SESSION_DIR", None)
        if not session_dir:
            return
        os.makedirs(session_dir, exist_ok=True)
        exit_path = os.path.join(session_dir, "exit.json")
        payload = {
            "status": "ok",
            "session": os.path.basename(session_dir),
            "messages": len(messages or []),
            "model": getattr(config, "MODEL_NAME", ""),
            "ended_at": _datetime.datetime.utcnow().isoformat() + "Z",
        }
        tmp_path = exit_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            _json.dump(payload, f, indent=2)
        os.replace(tmp_path, exit_path)
        print(Color.info(f"[--headless] wrote {exit_path}"))
    except Exception as exc:
        print(Color.warning(f"[--headless] failed to write exit.json: {exc}"))

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

    _effort_aliases = {
        'l': 'low',
        'm': 'medium',
        'med': 'medium',
        'mid': 'medium',
        'h': 'high',
        'hi': 'high',
        'x': 'xhigh',
        'xh': 'xhigh',
        'xhi': 'xhigh',
        'max': 'xhigh',
    }

    _parser = _argparse.ArgumentParser(add_help=False)
    _parser.add_argument('-s', '--session', default=None)
    _parser.add_argument('-w', '--workspace', '-wf', '--workflow', default=None,
                         help='Workflow name (e.g. ssot-gen, rtl-gen, tb-gen)')
    _parser.add_argument('--effort', default='',
                         help='Responses API reasoning effort: none|low|medium|high|xhigh')
    _parser.add_argument('--serve', action='store_true',
                         help='Start as HTTP server (agent-to-agent mode)')
    _parser.add_argument('--host', default='0.0.0.0',
                         help='HTTP server bind host (default: 0.0.0.0, requires --serve)')
    _parser.add_argument('--port', type=int, default=8000,
                         help='HTTP server port (default: 8000, requires --serve)')
    _parser.add_argument('--verbose', action='store_true',
                         help='Print ReAct log to terminal in real-time (requires --serve)')
    _parser.add_argument('--all-workflows', '--accept-any-workflow',
                         dest='all_workflows', action='store_true',
                         help='Workflow-agnostic worker (May-12 single-main-loop): '
                              'one --serve process accepts /run for any workflow and '
                              'switches workspace per dispatch via _setup_workspace().')
    _parser.add_argument('--coordinator', type=str, default='',
                         help='Coordinator URL to register with (e.g. http://localhost:8000)')
    _parser.add_argument('--worker-name', type=str, default='',
                         help='Name to register as (e.g. lint_worker, requires --coordinator)')
    _parser.add_argument('--model', type=str, default='',
                         help='Active LLM profile or bare model name. Profiles '
                              '(PROFILE_<name>_BASE_URL/API_KEY/MODEL in .env) switch '
                              'all three at once; cursor-cli/claude-cli use local CLI backends; '
                              'bare names only override LLM_MODEL_NAME.')
    _parser.add_argument('--headless', action='store_true',
                         help='Run the chat loop without interactive prompts: max-iterations '
                              'auto-stops instead of prompting (y/n), EOFError on stdin is a '
                              'normal termination, and an exit.json with status/counts is '
                              'written to the session directory on exit.')
    _parser.add_argument('--prompt-file', type=str, default='',
                         help='Read user prompts from the given file instead of stdin. '
                              'Each line is consumed as a separate user turn (slash commands '
                              'work the same as in stdin mode). Useful with --headless.')
    _args, _ = _parser.parse_known_args()

    # --model: switch profile (BASE_URL+API_KEY+MODEL) or bare model name.
    # Done after config import on purpose — config has already loaded .env;
    # we mutate config.MODEL_NAME (+ profile trio) in-place so dispatch and
    # UI both see the override without a re-import.
    if getattr(_args, 'model', ''):
        _m = _args.model.strip()
        if config.set_active_profile(_m):
            print(Color.success(
                f"[--model] profile '{_m}' active "
                f"→ {config.MODEL_NAME} @ {config.BASE_URL}"))
        elif config.activate_cli_backend(_m):
            from src.llm_client import get_active_model as _get_active_model
            print(Color.success(
                f"[--model] CLI backend active → {_get_active_model()}"))
        elif config.is_opencode_model(_m) and config.auto_opencode_oauth_allowed():
            # gpt-5* / *codex* → ChatGPT OAuth via opencode auth.json.
            # Strip any provider prefix ("openai/gpt-5.5" → "gpt-5.5").
            _bare = _m.split("/", 1)[-1]
            if config.activate_opencode_oauth(_bare):
                print(Color.success(
                    f"[--model] opencode-OAuth active → "
                    f"{config.MODEL_NAME} @ {config.BASE_URL}"))
            else:
                print(Color.error(
                    f"[--model] '{_m}' looks like an OpenAI model but "
                    f"no opencode credential is available. "
                    f"Run: python -m src.opencode_backend login"))
        else:
            # Not a known profile and not gpt-5* — bare name override.
            _deact_cli = getattr(config, "deactivate_cli_backends", None)
            if callable(_deact_cli):
                _deact_cli()
            _mark_override = getattr(config, "mark_runtime_model_override", None)
            if callable(_mark_override):
                _mark_override()
            config.MODEL_NAME = _m
            os.environ['LLM_MODEL_NAME'] = _m
            os.environ['MODEL_NAME'] = _m
            print(Color.warning(
                f"[--model] '{_m}' is not a defined profile; "
                f"applied as bare LLM_MODEL_NAME override "
                f"(BASE_URL/API_KEY unchanged)."))

    # --effort: set runtime reasoning effort for Responses API.
    # Mirrors `/effort` command behavior (same aliases + env updates),
    # but applies only for this process before first API call.
    if getattr(_args, 'effort', ''):
        _raw_effort = _args.effort.strip().lower()
        _effort = _effort_aliases.get(_raw_effort, _raw_effort)
        if _effort in ('none', 'low', 'medium', 'high', 'xhigh'):
            config.REASONING_MODE = _effort
            config.REASONING_EFFORT = _effort
            config.GLM_THINKING_TYPE = 'disabled' if _effort == 'none' else 'enabled'
            os.environ['REASONING_MODE'] = _effort
            os.environ['REASONING_EFFORT'] = _effort
            os.environ['GLM_THINKING_TYPE'] = config.GLM_THINKING_TYPE
            print(f"[--effort] reasoning effort set to {_effort} (provider-specific mapping applies at request time)")
        else:
            print(f"[--effort] unknown effort: {_raw_effort}. Allowed: none, low, medium, high, xhigh")

    # --headless: drive the chat loop without interactive prompts. Stored on
    # config so chat_loop's ChatLoopState picks it up and so iteration_control
    # sees `mode='oneshot'` at max iters (no `(y/n)` prompt). exit.json is
    # written from the bottom of chat_loop when this is set.
    if getattr(_args, 'headless', False):
        config.HEADLESS_MODE = True
        print("[--headless] interactive prompts disabled; exit.json will be written on termination")

    # --prompt-file: read user turns from a file instead of stdin. Each line
    # is consumed as a separate REPL turn (slash commands behave the same as
    # in stdin mode). After the file is exhausted the chat loop sees EOFError
    # and terminates — combined with --headless this produces a clean,
    # scriptable, non-interactive run.
    if getattr(_args, 'prompt_file', ''):
        _prompt_path = _args.prompt_file.strip()
        if _prompt_path and os.path.exists(_prompt_path):
            sys.stdin = open(_prompt_path, "r", encoding="utf-8")
            print(f"[--prompt-file] reading user turns from {_prompt_path}")
        else:
            print(f"[--prompt-file] file not found: {_prompt_path} — falling back to stdin")

    # Each project gets its own session context:
    # if -s is not explicitly given, use the workspace name as the project name
    # so each workspace maintains a separate conversation history.
    _project_name = _args.session or _args.workspace or 'default'
    _setup_session(_project_name)

    if _args.workspace:
        _setup_workspace(_args.workspace)
        os.environ['ATLAS_WORKFLOW'] = _args.workspace

    if getattr(config, 'GIT_VERSION_CONTROL_ENABLE', True):
        _ensure_git_repo()

    if "--check" in sys.argv:
        # Smoke test: verify all imports and initialization succeed
        print(f"OK: platform={platform.system()}, model={config.MODEL_NAME}")
        sys.exit(0)

    if getattr(_args, 'serve', False):
        # Server mode: start HTTP API for agent-to-agent communication
        from core.agent_server import serve as _agent_serve
        from core.agent_client import set_coordinator as _set_coordinator
        coordinator = getattr(_args, 'coordinator', '')
        if coordinator:
            _set_coordinator(coordinator)
        _agent_serve(
            host=_args.host,
            port=_args.port,
            verbose=getattr(_args, 'verbose', False),
            coordinator=coordinator,
            worker_name=getattr(_args, 'worker_name', ''),
            session_name=_args.session or '',
            startup_workflow=getattr(_args, 'workspace', '') or '',
            all_workflows=getattr(_args, 'all_workflows', False),
        )
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
        # Register a stdin-based ask_user callback so plain CLI runs can
        # answer the LLM's ask_user(...) tool calls. Skip if some upstream
        # UI (textual / atlas) already registered one.
        try:
            from core import tools as _cli_tools_for_ask
            if getattr(_cli_tools_for_ask, "_ask_user_callback", None) is None:
                def _cli_ask_user(question, options, kind, subtitle, questions=None):
                    """Render ask_user prompts in the CLI and read stdin.

                    For batched questions: ask each in turn, prefix with [Q<i>].
                    For single questions: number the options, accept a 1-based
                    index OR free text. `kind=multi` accepts comma-separated
                    indices (e.g. `1,3`); `kind=input` reads a free-form line.
                    Returns a plain-text summary the LLM can quote back.
                    """
                    def _show(qtext, opts, qkind, sub):
                        if sub:
                            print(Color.system(f"\n  ({sub})"))
                        print(Color.system(f"\n┃ {qtext}"))
                        if qkind in ("single", "multi") and opts:
                            for j, opt in enumerate(opts, 1):
                                lbl = opt.get("label") or opt.get("id") or str(opt)
                                detail = opt.get("detail") or ""
                                print(f"  {j}. {lbl}" + (f"   — {detail}" if detail else ""))
                        if qkind == "multi":
                            print(Color.dim("    (comma-separated indices, e.g. 1,3)"))
                        elif qkind == "input":
                            print(Color.dim("    (free-form text)"))
                    def _resolve(raw, opts, qkind):
                        raw = (raw or "").strip()
                        if not raw:
                            return ""
                        if qkind == "input":
                            return raw
                        # Try comma-separated indices for multi
                        if qkind == "multi":
                            picks = []
                            for tok in raw.split(","):
                                tok = tok.strip()
                                try:
                                    idx = int(tok) - 1
                                    if 0 <= idx < len(opts):
                                        picks.append(opts[idx].get("label") or opts[idx].get("id") or "")
                                except ValueError:
                                    if tok:
                                        picks.append(tok)
                            return ", ".join(p for p in picks if p)
                        # single — try index, else echo text
                        try:
                            idx = int(raw) - 1
                            if 0 <= idx < len(opts):
                                return opts[idx].get("label") or opts[idx].get("id") or raw
                        except ValueError:
                            pass
                        return raw
                    if questions:
                        parts = []
                        for i, q in enumerate(questions, 1):
                            qtext = q.get("question", "")
                            qopts = q.get("options") or []
                            qkind = (q.get("kind") or "single").lower()
                            qsub = q.get("subtitle") or ""
                            print(Color.system(f"\n── ask_user [Q{i}/{len(questions)}] ──"))
                            _show(qtext, qopts, qkind, qsub)
                            try:
                                raw = input(f"answer Q{i}> ")
                            except (EOFError, KeyboardInterrupt):
                                return f"[ask_user CLI: aborted at Q{i}]"
                            parts.append(f"Q{i}: {_resolve(raw, qopts, qkind)}")
                        return "\n".join(parts)
                    print(Color.system("\n── ask_user ──"))
                    _show(question, options or [], (kind or "single").lower(), subtitle or "")
                    try:
                        raw = input("> ")
                    except (EOFError, KeyboardInterrupt):
                        return "[ask_user CLI: aborted]"
                    return _resolve(raw, options or [], (kind or "single").lower())
                _cli_tools_for_ask.set_ask_user_callback(_cli_ask_user)
        except Exception as _ask_err:
            print(Color.warning(f"[Warning] could not register CLI ask_user callback: {_ask_err}"))
        chat_loop()
