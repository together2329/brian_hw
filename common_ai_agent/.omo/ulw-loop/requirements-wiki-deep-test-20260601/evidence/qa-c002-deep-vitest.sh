#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO=$(cd "$SCRIPT_DIR/../../../.." && pwd)

cd "$REPO/frontend/atlas"
npm test -- --run __tests__/sim-debug-requirements-deep.test.tsx --reporter verbose

cd "$REPO"
python3 - <<'PY'
from pathlib import Path

repo = Path.cwd()
signals = (repo / "frontend/atlas/__tests__/sim-debug-requirements-signals.test.tsx").read_text(encoding="utf-8")
waveband = (repo / "frontend/atlas/__tests__/sim-debug-requirements-waveband.test.tsx").read_text(encoding="utf-8")
required = [
    "SDR-007",
    "SDR-008",
    "SDR-009",
    "SDR-011",
    "SDR-012",
    "SDR-013",
    "SDR-014",
    "SDR-015",
    "SDR-016",
    "SDR-017",
    "SDR-018",
    "SDR-019",
    "SDR-020",
    "SDR-021",
    "SDR-022",
    "SDR-023",
]
combined = signals + "\n" + waveband
missing = [item for item in required if item not in combined]
assert not missing, missing
print("C002_DEEP_VITEST_PASS requirements=" + ",".join(required))
PY

echo "C002_QA_SCRIPT_DONE tmux_session=${ULW_TMUX_SESSION:-unknown}"
