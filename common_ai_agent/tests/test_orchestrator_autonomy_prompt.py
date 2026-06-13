"""Prompt contract for a less prescriptive orchestrator harness.

The orchestrator should expose a small set of calls and let the model choose
the process. Hardness belongs at evidence boundaries, especially final
completion, not at every intermediate reasoning step.
"""

from src.orchestrator.prompts import build_system_prompt, tool_schemas


def test_orchestrator_prompt_treats_tools_as_capabilities_not_a_script():
    prompt = build_system_prompt()

    assert "Tool calls are capabilities, not a fixed script" in prompt
    assert "Do not force read_pipeline_state before every dispatch" in prompt
    assert "Do not lock into a single repair flow too early" in prompt
    assert "read state \u2192 dispatch / classify / repair / ask_user" not in prompt


def test_orchestrator_prompt_keeps_hardness_at_evidence_boundaries():
    prompt = build_system_prompt()

    assert "Hard enforcement belongs at evidence boundaries" in prompt
    assert "final completed gate" in prompt
    assert "Never claim a stage passed without checking current state" in prompt
    assert 'workflow="__final__"' in prompt


def test_orchestrator_tool_surface_is_shared_and_not_duplicated():
    names = [schema["function"]["name"] for schema in tool_schemas()]

    assert len(names) == len(set(names))
    assert names == [
        "read_pipeline_state",
        "dispatch_workflow",
        "wait_job",
        "ask_user",
        "yield_run",
        "import_document",
        "read_artifact",
        "classify_failure",
        "write_handoff",
        "mark_downstream_stale",
        "web_search",
        "web_fetch",
    ]
