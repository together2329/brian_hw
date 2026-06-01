set -euo pipefail
REPO="/Users/brian/Desktop/Project/brian_hw/common_ai_agent"
ANDES="/Users/brian/Desktop/andes"
cd "$REPO"
python3 scripts/build_andes_rtl_db_wiki.py --andes-root "$ANDES" --build-graph
python3 - "$ANDES" <<'PY'
import json
import sys
from pathlib import Path
root = Path(sys.argv[1])
wiki = root / "wiki"
hdl_roots = sorted(path for path in root.rglob("hdl") if path.is_dir() and "wiki" not in path.parts)
coverage = json.loads((wiki / "_coverage.json").read_text())
graph = json.loads((wiki / "_graph.json").read_text())
entries = {entry["hdl_root"]: entry for entry in coverage["entries"]}
missing_roots = [path.relative_to(root).as_posix() for path in hdl_roots if path.relative_to(root).as_posix() not in entries]
broken = [node for node in graph["nodes"] if node.get("broken_refs")]
assert not missing_roots, missing_roots[:10]
assert coverage["summary"]["total_hdl_roots"] == len(hdl_roots)
assert coverage["summary"]["missing_pages"] == []
assert coverage["summary"]["missing_facts"] == []
assert not broken, broken[:3]
empty = [entry for entry in entries.values() if entry["status"] == "empty"]
assert all(entry["diagnostics"] for entry in empty)
print("hdl_roots", len(hdl_roots))
print("coverage_summary", coverage["summary"])
print("empty_roots", len(empty))
print("graph", graph["node_count"], graph["edge_count"], "broken_refs", len(broken))
PY
echo "PASS C002 all corpus coverage"
