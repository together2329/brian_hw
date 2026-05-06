from __future__ import annotations

from pathlib import Path

from src.headless_workflow import _structured_ssot_yaml
from src.workflow_stage_surface import is_common_stage, run_common_stage_surface

SOURCE_ROOT = Path(__file__).resolve().parents[1]


def _write_ssot(root: Path, ip: str) -> None:
    ssot = root / ip / "yaml" / f"{ip}.ssot.yaml"
    ssot.parent.mkdir(parents=True, exist_ok=True)
    ssot.write_text(_structured_ssot_yaml(ip, "double sampled input on valid transactions"), encoding="utf-8")


def test_common_surface_recognizes_all_ui_aliases():
    assert is_common_stage("sfm")
    assert is_common_stage("ssot-rtl")
    assert is_common_stage("tb")
    assert is_common_stage("cov")
    assert is_common_stage("sd")
    assert not is_common_stage("signoff")


def test_common_surface_runs_engine_and_names_session(tmp_path: Path):
    ip = "surface_probe"
    _write_ssot(tmp_path, ip)

    surface = run_common_stage_surface(
        project_root=tmp_path,
        source_root=None,
        alias="sfm",
        ip=ip,
    )

    assert surface.handled
    assert surface.alias == "ssot-fl-model"
    assert surface.workflow == "fl-model-gen"
    assert surface.session == f"{ip}/fl-model-gen"
    assert surface.status == "pass"
    assert "[ssot-fl-model]" in surface.message
    assert not surface.queue_prompts


def test_legacy_direct_command_entrypoints_are_removed():
    removed = [
        "workflow/rtl-gen/commands/new-ip-rtl.json",
        "workflow/rtl-gen/commands/legacy-ip-rtl.json",
        "workflow/tb-gen/commands/new-ip-tb.json",
        "workflow/tb-gen/commands/legacy-ip-tb.json",
        "workflow/mas-gen/commands/legacy-ip.json",
    ]
    for rel in removed:
        assert not (SOURCE_ROOT / rel).exists(), rel


def test_common_commands_route_to_stage_handler():
    expected = {
        "workflow/rtl-gen/commands/ssot-rtl.json": "stage:ssot-rtl",
        "workflow/fl-model-gen/commands/ssot-fl-model.json": "stage:ssot-fl-model",
        "workflow/fl-model-gen/commands/ssot-equiv-goals.json": "stage:ssot-equiv-goals",
        "workflow/tb-gen/commands/ssot-tb.json": "stage:ssot-tb-cocotb",
        "workflow/tb-gen/commands/ssot-tb-cocotb.json": "stage:ssot-tb-cocotb",
        "workflow/tb-gen/commands/sim.json": "stage:sim",
        "workflow/tb-gen/commands/coverage.json": "stage:coverage",
        "workflow/sim_debug/commands/sim-debug.json": "stage:sim-debug",
        "workflow/sim_debug/commands/goal-audit.json": "stage:goal-audit",
    }
    for rel, handler in expected.items():
        text = (SOURCE_ROOT / rel).read_text(encoding="utf-8")
        assert f'"handler": "{handler}"' in text
