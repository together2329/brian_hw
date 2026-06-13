from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPERS = ROOT / "frontend" / "atlas" / "sim-debug-helpers.tsx"
VITEST = ROOT / "frontend" / "atlas" / "__tests__" / "sim-debug-requirements-signals.test.tsx"


def test_param_radix_excludes_width_size_config_constants() -> None:
    helper_src = HELPERS.read_text(encoding="utf-8")
    test_src = VITEST.read_text(encoding="utf-8")

    assert "CONFIG_PARAM_RE" in helper_src
    assert "CONFIG_PARAM_RE.test(name)" in helper_src
    for token in ("WIDTH", "SIZE", "DEPTH", "NUM"):
        assert token in helper_src

    assert "SDR-015b excludes width/size/config params from the FSM/PARAM value map" in test_src
    assert "expect(valueMap[8]).toBeUndefined()" in test_src
    assert "expect(valueMap[32]).toBeUndefined()" in test_src
    assert "expect(valueMap[16]).toBeUndefined()" in test_src
    assert "expect(valueMap[4]).toBeUndefined()" in test_src
    assert "expect(valueMap[0]).toBe('IDLE')" in test_src
