"""
workflow/loader.py — Workspace configuration loader

워크스페이스 디렉토리에서 설정·프롬프트·훅·템플릿을 로드하고
common_ai_agent에 런타임 패치를 적용하는 핵심 모듈.

Usage (in common_ai_agent src/main.py):
    from workflow.loader import load_workspace, register_script_hooks, patch_todo_rules
    ws = load_workspace("verilog", Path(__file__).parent.parent)
    register_script_hooks(ws, hook_registry, todo_tracker=todo_tracker)
    patch_todo_rules(ws)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ─────────────────────────────────────────────────────────────
# Trigger → HookPoint name mapping (string-based, no HookPoint import needed)
# ─────────────────────────────────────────────────────────────

TRIGGER_TO_HOOKPOINT_NAME = {
    "before_llm":       "BEFORE_LLM_CALL",
    "after_llm":        "AFTER_LLM_CALL",
    "before_tool":      "BEFORE_TOOL_EXEC",
    "after_tool":       "AFTER_TOOL_EXEC",
    "on_error":         "ON_ERROR",
    "on_session_start": "ON_SESSION_START",
    "on_session_end":   "ON_SESSION_END",
}

# Fallback filename → trigger mapping (when hooks.json is absent)
_FILENAME_TO_TRIGGER = {
    "pre_tool_exec":  "before_tool",
    "post_tool_exec": "after_tool",
    "pre_llm":        "before_llm",
    "post_llm":       "after_llm",
    "on_error":       "on_error",
    "on_session_start": "on_session_start",
    "on_session_end": "on_session_end",
}


# ─────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────

@dataclass
class ScriptHookSpec:
    """Single script hook entry loaded from hooks.json (or filename pattern)."""
    script: Path
    trigger: str                        # "after_tool", "before_llm", etc.
    conditions: dict = field(default_factory=dict)


@dataclass
class WorkspaceConfig:
    """Complete workspace configuration loaded from a workspace directory."""
    name: str
    workspace_dir: Path
    description: str = ""

    # Env overrides (applied before load_env_file)
    env_overrides: dict = field(default_factory=dict)

    # Prompts (None = use default)
    system_prompt_text: Optional[str] = None
    system_prompt_mode: str = "append"      # "prepend" | "append" | "replace"
    plan_prompt_text: Optional[str] = None
    plan_prompt_mode: str = "append"
    compression_prompt_text: Optional[str] = None

    # Hook message overrides {key: template_string}
    hook_messages: dict = field(default_factory=dict)

    # Directory paths
    rules_dir: Optional[Path] = None
    todo_templates_dir: Optional[Path] = None
    scripts_dir: Optional[Path] = None
    hooks_module_path: Optional[Path] = None     # Python hooks.py
    extra_skills_dir: Optional[Path] = None

    # Skill control
    force_skills: list = field(default_factory=list)
    disable_skills: list = field(default_factory=list)

    # Script hook specs (populated during load)
    script_hooks: list = field(default_factory=list)

    # Custom slash commands directory (workflow/<name>/commands/)
    commands_dir: Optional[Path] = None


# ─────────────────────────────────────────────────────────────
# Loader
# ─────────────────────────────────────────────────────────────

def load_workspace(name: str, project_root: Path) -> WorkspaceConfig:
    """
    Load workspace from <project_root>/workflow/<name>/workspace.json.
    Reads .md prompt files and hook_messages.json automatically.
    Raises FileNotFoundError if workspace directory does not exist.
    """
    ws_dir = project_root / "workflow" / name
    if not ws_dir.exists():
        raise FileNotFoundError(f"Workspace '{name}' not found at {ws_dir}")

    # Parse workspace.json
    ws_json = ws_dir / "workspace.json"
    data: dict = {}
    if ws_json.exists():
        data = json.loads(ws_json.read_text(encoding="utf-8"))

    # Support both nested {"prompt": {...}} and flat root-level keys
    prompt_cfg = data.get("prompt", {})
    # Flat root-level keys take precedence if nested "prompt" block is absent
    if not prompt_cfg:
        prompt_cfg = data
    skills_cfg = data.get("skills", {})

    def _read_md(filename: str) -> Optional[str]:
        p = ws_dir / filename
        return p.read_text(encoding="utf-8").strip() if p.exists() else None

    def _opt_dir(dirname: str) -> Optional[Path]:
        p = ws_dir / dirname
        return p if p.is_dir() else None

    # Load hook_messages.json
    hm_path = ws_dir / "hook_messages.json"
    hook_messages: dict = {}
    if hm_path.exists():
        hook_messages = json.loads(hm_path.read_text(encoding="utf-8"))

    ws = WorkspaceConfig(
        name=name,
        workspace_dir=ws_dir,
        description=data.get("description", ""),
        env_overrides=data.get("env", {}),
        system_prompt_text=_read_md("system_prompt.md"),
        system_prompt_mode=prompt_cfg.get("system_prompt_mode", "append"),
        plan_prompt_text=_read_md("plan_prompt.md"),
        plan_prompt_mode=prompt_cfg.get("plan_prompt_mode", "append"),
        compression_prompt_text=_read_md("compression_prompt.md"),
        hook_messages=hook_messages,
        rules_dir=_opt_dir("rules"),
        todo_templates_dir=_opt_dir("todo_templates"),
        scripts_dir=_opt_dir("scripts"),
        hooks_module_path=(ws_dir / "hooks.py") if (ws_dir / "hooks.py").exists() else None,
        extra_skills_dir=_opt_dir("skills"),
        force_skills=skills_cfg.get("force_activate", []),
        disable_skills=skills_cfg.get("disable", []),
        commands_dir=_opt_dir("commands"),
    )

    # Load script hooks
    if ws.scripts_dir:
        ws.script_hooks = _load_script_hooks(ws.scripts_dir)

    return ws


# ─────────────────────────────────────────────────────────────
# Prompt merging
# ─────────────────────────────────────────────────────────────

def merge_prompt(base: str, text: str, mode: str) -> str:
    """Merge workspace prompt text into base using the specified mode."""
    if not text:
        return base
    if mode == "replace":
        return text
    if mode == "prepend":
        return text + "\n\n" + base
    # append (default)
    return base + "\n\n" + text


# ─────────────────────────────────────────────────────────────
# Hook message resolution
# ─────────────────────────────────────────────────────────────

def get_hook_message(key: str, default: str, **kwargs) -> str:
    """
    Resolve a hook message by key from builtins._WORKSPACE_HOOK_MESSAGES,
    falling back to default. Performs {VAR} substitution.

    _setup_workspace() registers the workspace hook_messages dict at startup.
    Designed to be called from core/hooks.py without passing ws explicitly.
    """
    import builtins
    messages: dict = getattr(builtins, "_WORKSPACE_HOOK_MESSAGES", {})
    template = messages.get(key, default)
    try:
        return template.format(**kwargs)
    except (KeyError, ValueError):
        return template


# ─────────────────────────────────────────────────────────────
# Early env override (called before config.py load_env_file)
# ─────────────────────────────────────────────────────────────

def apply_workspace_env_early(project_root: Path) -> Optional[str]:
    """
    Parse -w/--workspace from sys.argv and inject workspace.json [env]
    into os.environ BEFORE load_env_file() runs, giving workspace vars
    the highest config priority (below shell env vars).

    Returns workspace name, or None if not specified.
    """
    ws_name = _parse_workspace_arg()
    if not ws_name:
        return None

    ws_json = project_root / "workflow" / ws_name / "workspace.json"
    if not ws_json.exists():
        return ws_name  # name only; actual load happens in _setup_workspace

    try:
        data = json.loads(ws_json.read_text(encoding="utf-8"))
        for key, value in data.get("env", {}).items():
            if key not in os.environ:       # shell env vars take priority
                os.environ[key] = str(value)
    except Exception:
        pass

    return ws_name


def _parse_workspace_arg() -> Optional[str]:
    """Extract -w / --workspace value from sys.argv."""
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg.startswith("--workspace="):
            return arg.split("=", 1)[1]
        if arg in ("-w", "--workspace") and i + 1 < len(args):
            return args[i + 1]
    return None


# ─────────────────────────────────────────────────────────────
# Python hook module registration
# ─────────────────────────────────────────────────────────────

def register_workspace_hooks(ws: WorkspaceConfig, registry) -> None:
    """
    Import workspace hooks.py and call register_hooks(registry).
    Safe no-op if hooks.py is absent.
    """
    if ws.hooks_module_path is None or not ws.hooks_module_path.exists():
        return
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        f"_workspace_{ws.name}_hooks", ws.hooks_module_path
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if hasattr(mod, "register_hooks"):
        mod.register_hooks(registry)


# ─────────────────────────────────────────────────────────────
# Script hooks — load, condition check, registration
# ─────────────────────────────────────────────────────────────

def _load_script_hooks(scripts_dir: Path) -> list:
    """
    Load ScriptHookSpec list from scripts/hooks.json.
    Falls back to filename pattern matching if hooks.json is absent.
    """
    hooks_json = scripts_dir / "hooks.json"
    if hooks_json.exists():
        data = json.loads(hooks_json.read_text(encoding="utf-8"))
        specs = []
        for entry in data.get("hooks", []):
            script_path = scripts_dir / entry["script"]
            if script_path.exists():
                specs.append(ScriptHookSpec(
                    script=script_path,
                    trigger=entry["trigger"],
                    conditions=entry.get("conditions", {}),
                ))
        return specs

    # Fallback: match by filename stem
    specs = []
    for sh in sorted(scripts_dir.glob("*.sh")):
        trigger = _FILENAME_TO_TRIGGER.get(sh.stem)
        if trigger:
            specs.append(ScriptHookSpec(script=sh, trigger=trigger))
    return specs


def _check_script_conditions(spec: ScriptHookSpec, context) -> bool:
    """
    Evaluate all conditions in spec.conditions against HookContext.
    Returns True only when ALL conditions pass.

    Supported condition keys:
      tool_names: list[str]          — tool must be in list
      file_extensions: list[str]     — tool_args path must end with ext
      every_n_iterations: int        — run every N iterations
      min_iteration: int             — only after N iterations
      max_iteration: int             — only before N iterations
      output_contains: list[str]     — tool_output must contain any string
      output_not_contains: list[str] — tool_output must not contain any string
    """
    c = spec.conditions
    iter_n: int = getattr(context, "iteration", 0) or 0
    tool_name: str = getattr(context, "tool_name", "") or ""
    tool_args: str = getattr(context, "tool_args", "") or ""
    tool_output: str = getattr(context, "tool_output", "") or ""

    if "tool_names" in c and tool_name not in c["tool_names"]:
        return False

    if "file_extensions" in c:
        if not any(tool_args.endswith(ext) for ext in c["file_extensions"]):
            return False

    if "every_n_iterations" in c:
        n = int(c["every_n_iterations"])
        if n > 0 and iter_n % n != 0:
            return False

    if "min_iteration" in c and iter_n < int(c["min_iteration"]):
        return False

    if "max_iteration" in c and iter_n > int(c["max_iteration"]):
        return False

    if "output_contains" in c:
        if not any(s in tool_output for s in c["output_contains"]):
            return False

    if "output_not_contains" in c:
        if any(s in tool_output for s in c["output_not_contains"]):
            return False

    return True


def register_script_hooks(ws: WorkspaceConfig, registry,
                           todo_tracker=None) -> None:
    """
    Register all ws.script_hooks into HookRegistry.
    Creates .benchmark/ directory automatically.
    Each script receives workspace context via environment variables.
    """
    if not ws.script_hooks:
        return

    try:
        from core.hooks import HookPoint
    except ImportError:
        return

    trigger_map = {
        name: getattr(HookPoint, point_name)
        for name, point_name in TRIGGER_TO_HOOKPOINT_NAME.items()
        if hasattr(HookPoint, point_name)
    }

    benchmark_log = ws.workspace_dir / ".benchmark"
    benchmark_log.mkdir(exist_ok=True)

    for spec in ws.script_hooks:
        hook_point = trigger_map.get(spec.trigger)
        if hook_point is None:
            continue

        def _make_hook(s=spec, bm_log=benchmark_log, tt=todo_tracker):
            def _script_hook(context):
                if not _check_script_conditions(s, context):
                    return context

                todo_idx = ""
                todo_content = ""
                if tt and hasattr(tt, "current_index") and tt.current_index >= 0:
                    t = tt.todos[tt.current_index]
                    todo_idx = str(tt.current_index + 1)
                    todo_content = t.content

                env = {
                    **os.environ,
                    "HOOK_TOOL_NAME":    getattr(context, "tool_name", "") or "",
                    "HOOK_TOOL_ARGS":    getattr(context, "tool_args", "") or "",
                    "HOOK_TOOL_OUTPUT":  getattr(context, "tool_output", "") or "",
                    "HOOK_ITERATION":    str(getattr(context, "iteration", 0) or 0),
                    "HOOK_SESSION":      ws.name,
                    "HOOK_WORKSPACE":    ws.name,
                    "HOOK_TODO_INDEX":   todo_idx,
                    "HOOK_TODO_CONTENT": todo_content,
                    "BENCHMARK_LOG":     str(bm_log),
                }
                try:
                    subprocess.run(
                        ["bash", str(s.script)],
                        env=env,
                        capture_output=True,
                        timeout=5,
                    )
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass
                return context

            return _script_hook

        registry.register(hook_point, _make_hook(), priority=900)


# ─────────────────────────────────────────────────────────────
# Todo rule extension (monkey-patch)
# ─────────────────────────────────────────────────────────────

def patch_todo_rules(ws: WorkspaceConfig) -> None:
    """
    Monkey-patch lib.todo_tracker._load_todo_rule so that workspace
    rules/*.md files are appended to the project-level rules.
    Safe no-op if rules_dir is absent.
    """
    if not ws.rules_dir or not ws.rules_dir.exists():
        return

    try:
        import lib.todo_tracker as _tt
    except ImportError:
        return

    _orig = _tt._load_todo_rule

    def _patched():
        base = _orig()
        extra_parts = []
        for f in sorted(ws.rules_dir.glob("*.md")):
            content = f.read_text(encoding="utf-8").strip()
            if content:
                extra_parts.append(f"## [{f.stem}]\n{content}")
        extra = "\n\n".join(extra_parts)
        if base and extra:
            return base + "\n\n" + extra
        return extra or base

    _tt._load_todo_rule = _patched


# ─────────────────────────────────────────────────────────────
# Todo template registry
# ─────────────────────────────────────────────────────────────

class TodoTemplateRegistry:
    """Load and serve todo task templates from todo_templates/ directories."""

    def __init__(self):
        self._templates: dict = {}      # stem -> parsed JSON dict

    def load_from_dir(self, templates_dir: Path) -> None:
        """Load all *.json files from templates_dir."""
        for f in sorted(templates_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                self._templates[f.stem] = data
            except Exception:
                pass

    def list(self) -> list:
        return list(self._templates.keys())

    def list_templates(self) -> list:
        return self.list()

    def get(self, name: str) -> Optional[dict]:
        return self._templates.get(name)

    def get_template(self, name: str) -> Optional[dict]:
        return self.get(name)

    def get_tasks(self, name: str) -> Optional[list]:
        tmpl = self.get(name)
        return tmpl.get("tasks") if tmpl else None


# Global singleton
_todo_template_registry = TodoTemplateRegistry()


def get_todo_template_registry() -> TodoTemplateRegistry:
    return _todo_template_registry


# ─────────────────────────────────────────────────────────────
# Custom slash commands
# ─────────────────────────────────────────────────────────────

def _make_command_handler(spec: dict, ws: "WorkspaceConfig"):
    """
    Build a callable handler from a command spec dict.

    handler types:
      bash:<script>          — run scripts/<script> via bash, return stdout
      todo:template:<name>   — return INJECT_TODO_TEMPLATE:<name> signal
      prompt:<text>          — return INJECT_PROMPT:<text> signal
      python:<fn>            — call register_hooks-style fn from workspace hooks.py
    """
    handler_str = spec.get("handler", "")

    if handler_str.startswith("bash:"):
        script_rel = handler_str[5:]
        script_path = (ws.scripts_dir / script_rel) if ws.scripts_dir else None

        def _bash_handler(args: str, _s=script_path, _ws=ws) -> str:
            if _s is None or not _s.exists():
                return f"[Error] Script not found: {script_rel}"
            env = {
                **os.environ,
                "HOOK_WORKSPACE": _ws.name,
                "HOOK_CMD_ARGS": args or "",
                "BENCHMARK_LOG": str(_ws.workspace_dir / ".benchmark"),
            }
            try:
                r = subprocess.run(
                    ["bash", str(_s)], env=env,
                    capture_output=True, text=True, timeout=30,
                )
                return (r.stdout or r.stderr or "(no output)").strip()
            except subprocess.TimeoutExpired:
                return "[Error] Script timed out (30s)"
            except Exception as e:
                return f"[Error] {e}"

        return _bash_handler

    if handler_str.startswith("todo:template:"):
        tmpl_name = handler_str[14:]

        def _tmpl_handler(args: str, _n=tmpl_name) -> str:
            return f"INJECT_TODO_TEMPLATE:{_n}"

        return _tmpl_handler

    if handler_str.startswith("prompt:"):
        text = handler_str[7:]

        def _prompt_handler(args: str, _t=text) -> str:
            return f"INJECT_PROMPT:{_t}"

        return _prompt_handler

    # Unknown — return error string
    return lambda args: f"[Error] Unknown handler type: {handler_str}"


def register_workspace_commands(ws: "WorkspaceConfig", slash_registry) -> None:
    """
    Load commands/*.json from the workspace and register each as a slash command.

    JSON format:
    {
      "name": "lint",
      "description": "Run RTL lint",
      "aliases": ["l"],
      "handler": "bash:scripts/lint.sh",
      "usage": "/lint [file.v]"
    }
    """
    if ws.commands_dir is None or not ws.commands_dir.exists():
        return

    for f in sorted(ws.commands_dir.glob("*.json")):
        try:
            spec = json.loads(f.read_text(encoding="utf-8"))
            handler = _make_command_handler(spec, ws)
            slash_registry.register(
                name=spec["name"],
                handler=handler,
                description=spec.get("description", ""),
                aliases=spec.get("aliases", []),
                usage=spec.get("usage", f"/{spec['name']}"),
            )
        except Exception as e:
            # Non-fatal: log and continue
            import sys as _sys
            print(f"[Workspace] Failed to load command {f.name}: {e}", file=_sys.stderr)
