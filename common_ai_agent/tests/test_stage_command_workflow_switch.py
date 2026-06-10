"""Stage slash commands must land the UI in their home workflow.

Regression for: `/to-ssot` switched the workflow (it queues an explicit
"/wf ssot-gen") but `/gen-rtl` stayed pinned on ssot-gen — the shared stage
dispatcher (`_run_stage_command`) only carried a "/wf <stage>" line inside the
LLM-authoring branches of run_common_stage_surface (rtl x2, tb-repair x1).
Every other branch (deterministic engine result, check stages like /lint,
/sim, /coverage) queued nothing, so the UI workflow never followed the stage
even though stage history is appended to the stage's own lane.

The fix is one central guard in `_run_stage_command`: queue
"/wf {surface.workflow}" whenever the surface's queue_prompts don't already
contain a "/wf " line. The rtl_blocked early-return intentionally stays in the
current workflow (its [SSOT QUESTION] is answered in the ssot context).
"""
import inspect
import sys
from pathlib import Path
from unittest.mock import MagicMock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))


def _split_slash(text):
    raw = (text or "").strip()
    if not raw:
        return "", ""
    parts = raw.split(None, 1)
    return parts[0].lstrip("/").lower(), (parts[1] if len(parts) > 1 else "").strip()


def _build_run_stage_command(tmp_path, queued):
    """Construct _run_stage_command with minimal real deps, rest MagicMock."""
    import src.atlas_slash_handlers as mod

    ip_dir = tmp_path / "demo_ip"
    (ip_dir / "yaml").mkdir(parents=True, exist_ok=True)
    ssot = ip_dir / "yaml" / "demo_ip.ssot.yaml"
    ssot.write_text("top_module:\n  name: demo_ip\n", encoding="utf-8")

    stage_runners = {
        "ssot-rtl": {"workflow": "rtl-gen", "template": "ssot-rtl", "artifact_hint": "rtl/"},
        "lint": {"workflow": "lint", "template": "lint-fix", "artifact_hint": "lint/"},
    }

    overrides = {
        "PROJECT_ROOT": tmp_path,
        "SOURCE_ROOT": tmp_path,
        "WORKFLOW_ROOT": tmp_path / "workflow",
        "_STAGE_RUNNERS": stage_runners,
        "_split_slash": _split_slash,
        "_command_ip": lambda args, client_session=None: "demo_ip",
        "_valid_ip_name": lambda name: bool(name) and name != "default",
        "_ip_root": lambda ip: ip_dir,
        "_ip_root_for_session": lambda ip, client_session=None: ip_dir,
        "_ssot_yaml_path": lambda ip: ssot,
        "_ssot_yaml_path_for_session": lambda ip, client_session=None: ssot,
        "_script_project_root": lambda ip=None: tmp_path,
        "_script_project_root_for_session": lambda ip=None, client_session=None: tmp_path,
        "_queue_prompt_for_session": lambda client_session, text: queued.append(text),
    }
    kwargs = {}
    for name in inspect.signature(mod.make_slash_handlers).parameters:
        kwargs[name] = overrides.get(name, MagicMock(name=name))
    handlers = mod.make_slash_handlers(**kwargs)
    return handlers["_run_stage_command"]


def _surface(workflow, alias, *, queue_prompts=(), rtl_blocked=False):
    from src.workflow_stage_surface import StageSurfaceResult

    return StageSurfaceResult(
        handled=True,
        alias=alias,
        workflow=workflow,
        session=f"demo_ip/{workflow}",
        message="stage ran",
        status="pass",
        queue_prompts=list(queue_prompts),
        rtl_blocked=rtl_blocked,
    )


def _patch_surface(monkeypatch, surface):
    import src.workflow_stage_surface as wss

    monkeypatch.setattr(wss, "is_common_stage", lambda alias: True)
    monkeypatch.setattr(
        wss, "run_common_stage_surface", lambda **kwargs: surface
    )


def _client():
    cs = MagicMock()
    cs.session_id = "alice/s1/demo_ip/ssot-gen"
    return cs


def test_gen_rtl_deterministic_result_switches_to_rtl_gen(tmp_path, monkeypatch):
    """The reported bug: engine ran, nothing queued -> UI stayed on ssot-gen."""
    queued = []
    run = _build_run_stage_command(tmp_path, queued)
    _patch_surface(monkeypatch, _surface("rtl-gen", "ssot-rtl"))

    assert run("/gen-rtl demo_ip", client_session=_client()) is True
    assert "/wf rtl-gen" in queued


def test_llm_branch_with_own_wf_line_is_not_duplicated(tmp_path, monkeypatch):
    queued = []
    run = _build_run_stage_command(tmp_path, queued)
    _patch_surface(
        monkeypatch,
        _surface(
            "rtl-gen",
            "ssot-rtl",
            queue_prompts=["/mode normal", "/wf rtl-gen", "/clear", "implement RTL"],
        ),
    )

    assert run("/gen-rtl demo_ip", client_session=_client()) is True
    assert queued.count("/wf rtl-gen") == 1
    # surface prompts queued in order, nothing prepended before them
    assert queued == ["/mode normal", "/wf rtl-gen", "/clear", "implement RTL"]


def test_rtl_blocked_stays_in_current_workflow(tmp_path, monkeypatch):
    """[SSOT QUESTION] blockers are answered in the ssot context: no switch."""
    queued = []
    run = _build_run_stage_command(tmp_path, queued)
    _patch_surface(monkeypatch, _surface("rtl-gen", "ssot-rtl", rtl_blocked=True))

    assert run("/gen-rtl demo_ip", client_session=_client()) is True
    assert not any(p.startswith("/wf ") for p in queued)


def test_check_stage_lint_also_lands_in_its_workflow(tmp_path, monkeypatch):
    """Uniform rule: check stages follow the same switch as generator stages."""
    queued = []
    run = _build_run_stage_command(tmp_path, queued)
    _patch_surface(monkeypatch, _surface("lint", "lint"))

    assert run("/lint demo_ip", client_session=_client()) is True
    assert "/wf lint" in queued
