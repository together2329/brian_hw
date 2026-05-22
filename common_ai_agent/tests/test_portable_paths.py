from pathlib import Path
import os
import shutil
import subprocess
import sys


def test_runtime_files_do_not_pin_developer_checkout_paths():
    source_root = Path(__file__).resolve().parents[1]
    runtime_files = [
        ".config",
        "src/config.py",
        "src/atlas_ui.py",
        "src/atlas_api_jobs.py",
        "src/headless_workflow.py",
        "src/workflow_stage_engine.py",
        "workflow/loader.py",
        "workflow/syn/scripts/run_sta.sh",
        "workflow/tb-gen/scripts/emit_goal_scoreboard_cocotb.py",
        "workflow/rtl-gen/scripts/derive_rtl_todos.py",
        "workflow/ssot-gen/scripts/verify_ssot.py",
        "workflow/ssot-gen/scripts/repair_ssot_schema.py",
        "workflow/sim_debug/scripts/compare_fl_rtl_results.py",
        "tests/test_e2e_api.py",
        "tests/test_integration/test_claude_code_integration.py",
        "tests/verify_single_user_compat.py",
        "tests/data/test_main_context.sh",
    ]

    forbidden = "/Users/" + "brian/Desktop"
    for rel in runtime_files:
        text = (source_root / rel).read_text(encoding="utf-8", errors="replace")
        assert forbidden not in text, rel


def test_project_config_resolves_to_copied_checkout(tmp_path):
    source_root = Path(__file__).resolve().parents[1]
    checkout = tmp_path / "common_ai_agent"
    (checkout / "src").mkdir(parents=True)
    (checkout / "workflow" / "ssot-gen").mkdir(parents=True)
    shutil.copy2(source_root / ".config", checkout / ".config")
    shutil.copy2(source_root / "src" / "config.py", checkout / "src" / "config.py")

    env = {
        **os.environ,
        "HOME": str(tmp_path / "home"),
        "PYTHONPATH": str(checkout),
    }
    script = """
import os
import src.config  # noqa: F401
source = os.environ["ATLAS_SOURCE_ROOT"]
workflow = os.environ["ATLAS_WORKFLOW_ROOT"]
assert source.endswith("/common_ai_agent"), source
assert workflow == source + "/workflow", workflow
assert "/Users/" + "brian/Desktop" not in source
assert "/Users/" + "brian/Desktop" not in workflow
"""

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(tmp_path),
        env=env,
        text=True,
        capture_output=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
