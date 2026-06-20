from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPERS = ROOT / "frontend" / "atlas" / "sim-debug-helpers.tsx"
SIM_DEBUG = ROOT / "frontend" / "atlas" / "sim-debug.tsx"
INTENT_VITEST = ROOT / "frontend" / "atlas" / "__tests__" / "sim-debug-intent-hook.test.ts"
CTRLW_VITEST = ROOT / "frontend" / "atlas" / "__tests__" / "sim-debug-ctrlw-add.test.tsx"


def test_workspace_absolute_source_paths_normalize_to_session_relative() -> None:
    helper_src = HELPERS.read_text(encoding="utf-8")
    vitest_src = INTENT_VITEST.read_text(encoding="utf-8")

    assert "sessionParts.length >= 4 ? sessionParts.slice(0, 3).join('/')" in helper_src
    assert "const markerPath = `/${anchor}/`" in helper_src
    assert "return raw.slice(pos + 1)" in helper_src
    assert (
        "/Users/brian/Desktop/Project/NEW_WORKSPACE/brian_user_3/default/"
        "apb_timer_pwm_irq_v1/rtl/timer_core.sv:12"
    ) in vitest_src
    assert "'brian_user_3/default/apb_timer_pwm_irq_v1/rtl/timer_core.sv'" in vitest_src


def test_sim_debug_source_fetch_carries_active_session_scope() -> None:
    sim_debug_src = SIM_DEBUG.read_text(encoding="utf-8")
    vitest_src = CTRLW_VITEST.read_text(encoding="utf-8")

    assert "appendActiveSessionParam(new URLSearchParams({ path }))" in sim_debug_src
    assert "credentials: 'include'" in sim_debug_src
    assert "cache: 'no-store'" in sim_debug_src
    assert "loads module source through the active session scope" in vitest_src
    assert "session_id=workspace%2Fdemo_ip%2Fsim_debug" in vitest_src
