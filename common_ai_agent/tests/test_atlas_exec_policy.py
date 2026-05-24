from core.atlas_exec_policy import (
    EXEC_MODE_ORCHESTRATOR,
    EXEC_MODE_SINGLE,
    apply_exec_mode_env,
    current_exec_mode,
    exec_policy_payload,
    initial_workflow_for_exec_mode,
    normalize_exec_mode,
    schedule_for_exec_mode,
)


def test_normalize_exec_mode_accepts_cli_and_ui_aliases() -> None:
    assert normalize_exec_mode("s") == EXEC_MODE_SINGLE
    assert normalize_exec_mode("single worker") == EXEC_MODE_SINGLE
    assert normalize_exec_mode("multi_worker") == EXEC_MODE_ORCHESTRATOR
    assert normalize_exec_mode("orch") == EXEC_MODE_ORCHESTRATOR
    assert normalize_exec_mode("unknown") == ""


def test_current_exec_mode_prefers_explicit_policy_over_legacy_single_flag() -> None:
    assert current_exec_mode({"ATLAS_SINGLE_MAIN_LOOP": "1"}) == EXEC_MODE_SINGLE
    assert current_exec_mode({
        "ATLAS_EXEC_MODE": "orchestrator",
        "ATLAS_SINGLE_MAIN_LOOP": "1",
    }) == EXEC_MODE_ORCHESTRATOR
    assert current_exec_mode({
        "ATLAS_ORCHESTRATOR_MODE": "0",
        "ATLAS_EXEC_MODE": "orchestrator",
    }) == EXEC_MODE_SINGLE


def test_exec_mode_controls_initial_workflow_and_auto_schedule() -> None:
    assert initial_workflow_for_exec_mode(EXEC_MODE_ORCHESTRATOR) == "orchestrator"
    assert initial_workflow_for_exec_mode(EXEC_MODE_SINGLE) == "ssot-gen"
    assert initial_workflow_for_exec_mode(EXEC_MODE_SINGLE, "orchestrator") == "orchestrator"
    assert schedule_for_exec_mode(EXEC_MODE_SINGLE, "auto", ["a", "b"]) == "serial"
    assert schedule_for_exec_mode(EXEC_MODE_ORCHESTRATOR, "auto", ["a"]) == "serial"
    assert schedule_for_exec_mode(EXEC_MODE_ORCHESTRATOR, "auto", ["a", "b"]) == "dag"
    assert schedule_for_exec_mode(EXEC_MODE_SINGLE, "dag", ["a"]) == "dag"


def test_exec_policy_payload_and_env_application() -> None:
    env: dict[str, str] = {}
    values = apply_exec_mode_env("single", env)
    assert values["ATLAS_EXEC_MODE"] == EXEC_MODE_SINGLE
    assert env["ATLAS_SINGLE_MAIN_LOOP"] == "1"

    payload = exec_policy_payload(env=env)
    assert payload["exec_mode"] == EXEC_MODE_SINGLE
    assert payload["initial_workflow"] == "ssot-gen"
    assert payload["worker_strategy"] == "single-main-loop"
    assert payload["preserve_running_on_workflow_switch"] is False
