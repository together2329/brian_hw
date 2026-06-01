#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO=$(cd "$SCRIPT_DIR/../../../.." && pwd)

cd "$REPO"

python3 workflow/wiki/build_graph.py --wiki doc/wiki --check --quiet

python3 - <<'PY'
import json
from pathlib import Path

repo = Path.cwd()
graph = json.loads((repo / "doc/wiki/_graph.json").read_text(encoding="utf-8"))
nodes = {node["id"]: node for node in graph["nodes"]}
node = nodes["sim-debug-requirements-2026-06-01"]
assert node["path"] == "doc/wiki/sim-debug-requirements-2026-06-01.md", node
assert "requirements" in node["tags"], node
assert "deep-test" in node["tags"], node

index = (repo / "doc/wiki/index.md").read_text(encoding="utf-8")
log = (repo / "doc/wiki/log.md").read_text(encoding="utf-8")
page = (repo / "doc/wiki/sim-debug-requirements-2026-06-01.md").read_text(encoding="utf-8")
assert "[[sim-debug-requirements-2026-06-01]]" in index
assert "[[sim-debug-requirements-2026-06-01]]" in log
assert "Deep Test Coverage Matrix" in page
assert "Requirement-Level Deep Evidence" in page
assert "frontend/atlas/__tests__/sim-debug-requirements-signals.test.tsx" in page
assert "frontend/atlas/__tests__/sim-debug-requirements-waveband.test.tsx" in page
assert "tests/test_simulation_quality_gate.py" in page
print("C001_WIKI_GRAPH_PASS node=sim-debug-requirements-2026-06-01 tags=" + ",".join(node["tags"]))
PY

echo "C001_QA_SCRIPT_DONE tmux_session=${ULW_TMUX_SESSION:-unknown}"
