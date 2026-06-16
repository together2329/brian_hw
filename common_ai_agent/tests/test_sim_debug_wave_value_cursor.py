from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def test_wave_value_column_is_driven_by_cursor_a():
    wave = (REPO / "frontend/atlas/sim-debug-wave.tsx").read_text(encoding="utf-8")
    shared = (REPO / "frontend/atlas/debug-shared.tsx").read_text(encoding="utf-8")

    assert "valueTime={waveCursor}" in wave
    assert "function traceValueAt" in shared
    assert "const shownVal = traceValueAt(trace, valueTime);" in shared
    assert "const valStr = fmtWaveValue(shownVal" in shared
