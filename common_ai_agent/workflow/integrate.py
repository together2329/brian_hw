"""
workflow/integrate.py — Patch verification helpers

Run this to verify that all common_ai_agent source patches are applied correctly.

Usage:
    cd common_ai_agent
    python workflow/integrate.py
    python workflow/integrate.py --workspace verilog
"""
from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path
from typing import Optional


# ──────────────────────────────────────────────────────
# Setup paths
# ──────────────────────────────────────────────────────

def _setup_paths():
    root = Path(__file__).parent.parent
    src = root / "src"
    for p in [str(root), str(src)]:
        if p not in sys.path:
            sys.path.insert(0, p)
    return root


# ──────────────────────────────────────────────────────
# Individual checks
# ──────────────────────────────────────────────────────

def check_config_patch(root: Path) -> tuple[bool, str]:
    """Verify _apply_workspace_env_early() is present in src/config.py."""
    cfg_path = root / "src" / "config.py"
    if not cfg_path.exists():
        return False, "src/config.py not found"
    text = cfg_path.read_text(encoding="utf-8")
    if "_apply_workspace_env_early" not in text:
        return False, "_apply_workspace_env_early() not found in src/config.py"
    return True, "_apply_workspace_env_early() present"


def check_main_patch(root: Path) -> tuple[bool, str]:
    """Verify _setup_workspace() and -w argparse are in src/main.py."""
    main_path = root / "src" / "main.py"
    if not main_path.exists():
        return False, "src/main.py not found"
    text = main_path.read_text(encoding="utf-8")
    missing = []
    if "_setup_workspace" not in text:
        missing.append("_setup_workspace()")
    if "--workspace" not in text:
        missing.append("-w/--workspace argparse")
    if missing:
        return False, f"Missing in src/main.py: {', '.join(missing)}"
    return True, "_setup_workspace() and -w argparse present"


def check_hooks_patch(root: Path) -> tuple[bool, str]:
    """Verify _get_hook_message() helper is in core/hooks.py."""
    hooks_path = root / "core" / "hooks.py"
    if not hooks_path.exists():
        return False, "core/hooks.py not found"
    text = hooks_path.read_text(encoding="utf-8")
    if "_get_hook_message" not in text:
        return False, "_get_hook_message() not found in core/hooks.py"
    return True, "_get_hook_message() present"


def check_compressor_patch(root: Path) -> tuple[bool, str]:
    """Verify _load_default_compression_prompt() is in core/compressor.py."""
    comp_path = root / "core" / "compressor.py"
    if not comp_path.exists():
        return False, "core/compressor.py not found"
    text = comp_path.read_text(encoding="utf-8")
    if "_load_default_compression_prompt" not in text:
        return False, "_load_default_compression_prompt() not found"
    return True, "_load_default_compression_prompt() present"


def check_skill_loader_patch(root: Path) -> tuple[bool, str]:
    """Verify extra_dirs attribute in core/skill_system/loader.py."""
    loader_path = root / "core" / "skill_system" / "loader.py"
    if not loader_path.exists():
        return False, "core/skill_system/loader.py not found"
    text = loader_path.read_text(encoding="utf-8")
    if "extra_dirs" not in text:
        return False, "extra_dirs not found in skill loader"
    return True, "extra_dirs present in SkillLoader"


def check_slash_commands_patch(root: Path) -> tuple[bool, str]:
    """Verify /todo template commands in core/slash_commands.py."""
    sc_path = root / "core" / "slash_commands.py"
    if not sc_path.exists():
        return False, "core/slash_commands.py not found"
    text = sc_path.read_text(encoding="utf-8")
    missing = []
    if "_todo_list_templates" not in text:
        missing.append("_todo_list_templates()")
    if "_todo_load_template" not in text:
        missing.append("_todo_load_template()")
    if missing:
        return False, f"Missing in slash_commands.py: {', '.join(missing)}"
    return True, "/todo template commands present"


def check_todo_tracker_patch(root: Path) -> tuple[bool, str]:
    """Verify loop fields and get_active_form() in lib/todo_tracker.py."""
    tt_path = root / "lib" / "todo_tracker.py"
    if not tt_path.exists():
        return False, "lib/todo_tracker.py not found"
    text = tt_path.read_text(encoding="utf-8")
    missing = []
    for symbol in ["loop: bool", "max_loop_iterations", "exit_condition",
                   "loop_count", "loop_exit_reason", "get_active_form"]:
        if symbol not in text:
            missing.append(symbol)
    if missing:
        return False, f"Missing in todo_tracker.py: {', '.join(missing)}"
    return True, "Loop fields and get_active_form() present"


def check_workflow_files(root: Path) -> tuple[bool, str]:
    """Verify all required workflow files exist."""
    required = [
        "workflow/loader.py",
        "workflow/integrate.py",
        "workflow/prompts/format.md",
        "workflow/prompts/rules_normal.md",
        "workflow/prompts/rules_plan.md",
        "workflow/prompts/identity.md",
        "workflow/default/workspace.json",
        "workflow/default/system_prompt.md",
        "workflow/default/plan_prompt.md",
        "workflow/default/todo_prompt.md",
        "workflow/default/compression_prompt.md",
        "workflow/default/hook_messages.json",
        "workflow/default/rules/default.md",
        "workflow/default/todo_templates/bugfix.json",
        "workflow/default/todo_templates/feature.json",
        "workflow/default/todo_templates/refactor.json",
        "workflow/verilog/workspace.json",
        "workflow/verilog/scripts/hooks.json",
        "workflow/verilog/scripts/benchmark_tick.sh",
        "workflow/verilog/scripts/post_write.sh",
        "workflow/verilog/scripts/error_capture.sh",
        "workflow/verilog/scripts/benchmark_report.sh",
        "workflow/verilog/todo_templates/rtl-module.json",
        "workflow/verilog/todo_templates/testbench.json",
        "workflow/spec-review/workspace.json",
        "workflow/spec-review/scripts/hooks.json",
        "workflow/spec-review/scripts/post_session.sh",
        "workflow/spec-review/todo_templates/spec-analysis.json",
    ]
    missing = [f for f in required if not (root / f).exists()]
    if missing:
        return False, f"Missing files ({len(missing)}):\n  " + "\n  ".join(missing)
    return True, f"All {len(required)} required files present"


def check_todo_validator_support(root: Path) -> tuple[bool, str]:
    """Verify validator field and run_validator() are in lib/todo_tracker.py."""
    tt_path = root / "lib" / "todo_tracker.py"
    if not tt_path.exists():
        return False, "lib/todo_tracker.py not found"
    text = tt_path.read_text(encoding="utf-8")
    missing = []
    for symbol in ["validator: str", "run_validator", "Validator failed", "Validator timed out"]:
        if symbol not in text:
            missing.append(symbol)
    if missing:
        return False, f"Missing in todo_tracker.py: {', '.join(missing)}"
    return True, "validator field and run_validator() present"


def check_workspace_commands_support(root: Path) -> tuple[bool, str]:
    """Verify register_workspace_commands() is in workflow/loader.py and main.py."""
    missing = []
    loader_path = root / "workflow" / "loader.py"
    if loader_path.exists():
        text = loader_path.read_text(encoding="utf-8")
        if "register_workspace_commands" not in text:
            missing.append("register_workspace_commands() in loader.py")
        if "commands_dir" not in text:
            missing.append("commands_dir field in WorkspaceConfig")
    else:
        missing.append("workflow/loader.py not found")

    main_path = root / "src" / "main.py"
    if main_path.exists():
        text = main_path.read_text(encoding="utf-8")
        if "register_workspace_commands" not in text:
            missing.append("register_workspace_commands() call in main.py")
    else:
        missing.append("src/main.py not found")

    if missing:
        return False, f"Missing: {', '.join(missing)}"
    return True, "register_workspace_commands() wired in loader.py and main.py"


def check_prompt_fragment_support(root: Path) -> tuple[bool, str]:
    """Verify _load_prompt_fragment() is in src/config.py."""
    cfg_path = root / "src" / "config.py"
    if not cfg_path.exists():
        return False, "src/config.py not found"
    text = cfg_path.read_text(encoding="utf-8")
    if "_load_prompt_fragment" not in text:
        return False, "_load_prompt_fragment() not found in src/config.py"
    return True, "_load_prompt_fragment() present — workflow/prompts/ wired into build_base_system_prompt()"


def check_workspace_loadable(root: Path, workspace_name: str) -> tuple[bool, str]:
    """Try loading a workspace via loader.py."""
    try:
        sys.path.insert(0, str(root))
        from workflow.loader import load_workspace
        ws = load_workspace(workspace_name, project_root=root)
        info = (
            f"Workspace '{workspace_name}' loaded — "
            f"system_prompt={'yes' if ws.system_prompt_text else 'no'}, "
            f"hook_messages={len(ws.hook_messages)}, "
            f"script_hooks={len(ws.script_hooks)}, "
            f"force_skills={ws.force_skills}"
        )
        return True, info
    except Exception as e:
        return False, f"load_workspace('{workspace_name}') failed: {e}"


def check_template_registry(root: Path, workspace_name: str) -> tuple[bool, str]:
    """Verify todo templates load and registry methods work."""
    try:
        sys.path.insert(0, str(root))
        from workflow.loader import load_workspace, get_todo_template_registry
        ws = load_workspace(workspace_name, project_root=root)
        reg = get_todo_template_registry()
        if ws.todo_templates_dir:
            reg.load_from_dir(ws.todo_templates_dir)
        names = reg.list_templates()
        return True, f"Templates for '{workspace_name}': {names}"
    except Exception as e:
        return False, f"Template registry check failed: {e}"


# ──────────────────────────────────────────────────────
# Runner
# ──────────────────────────────────────────────────────

def run_checks(workspace: Optional[str] = None) -> int:
    root = _setup_paths()
    print(f"\n{'='*60}")
    print(f"  Workflow Integration Check — {root.name}")
    print(f"{'='*60}\n")

    checks = [
        ("config.py patch",         lambda: check_config_patch(root)),
        ("main.py patch",           lambda: check_main_patch(root)),
        ("hooks.py patch",          lambda: check_hooks_patch(root)),
        ("compressor.py patch",     lambda: check_compressor_patch(root)),
        ("skill_loader patch",      lambda: check_skill_loader_patch(root)),
        ("slash_commands patch",    lambda: check_slash_commands_patch(root)),
        ("todo_tracker patch",      lambda: check_todo_tracker_patch(root)),
        ("todo validator support",  lambda: check_todo_validator_support(root)),
        ("workspace commands",      lambda: check_workspace_commands_support(root)),
        ("prompt fragment loader",  lambda: check_prompt_fragment_support(root)),
        ("workflow files",          lambda: check_workflow_files(root)),
    ]

    ws_name = workspace or "default"
    checks += [
        (f"load workspace '{ws_name}'",        lambda n=ws_name: check_workspace_loadable(root, n)),
        (f"templates '{ws_name}'",             lambda n=ws_name: check_template_registry(root, n)),
    ]

    passed = 0
    failed = 0
    for label, fn in checks:
        ok, msg = fn()
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {status}  {label}")
        if not ok or True:  # always show detail
            for line in msg.splitlines():
                print(f"          {line}")
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"  Result: {passed} passed, {failed} failed")
    print(f"{'='*60}\n")
    return failed


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Verify workflow integration patches")
    parser.add_argument("-w", "--workspace", default=None,
                        help="Workspace to test loading (default: 'default')")
    args = parser.parse_args()
    sys.exit(run_checks(workspace=args.workspace))
