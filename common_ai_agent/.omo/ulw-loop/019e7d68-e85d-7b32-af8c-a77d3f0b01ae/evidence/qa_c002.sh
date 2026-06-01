#!/usr/bin/env zsh
set -euo pipefail
cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent

ROOT=$(mktemp -d /tmp/andes-wiki-c002.XXXXXX)
mkdir -p "$ROOT/broken_ip/hdl" "$ROOT/broken_ip/docs" "$ROOT/empty_ip/hdl"

cat > "$ROOT/broken_ip/hdl/broken_ip.sv" <<'SV'
module broken_ip(input clk
always_ff @(posedge clk) begin
SV

cat > "$ROOT/broken_ip/docs/Broken_IP_User_Guide.md" <<'MD'
# Broken IP

This document must still become a wiki page when RTL has parser diagnostics.
MD

python3 scripts/build_andes_rtl_db_wiki.py --andes-root "$ROOT" --build-graph
python3 - "$ROOT" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
wiki = root / "wiki"
broken = json.loads((wiki / "_rtl_facts" / "broken_ip.json").read_text())
empty = json.loads((wiki / "_rtl_facts" / "empty_ip.json").read_text())
graph = json.loads((wiki / "_graph.json").read_text())

assert broken["diagnostics"], broken
assert empty["diagnostics"], empty
assert (wiki / "empty_ip.md").is_file()
assert any(path.name.endswith("broken-ip-user-guide.md") for path in wiki.glob("doc-*.md"))
assert graph["node_count"] >= 5, graph["node_count"]

print("C002 PASS malformed/empty corpus")
print("broken_diagnostics=", broken["diagnostics"][:2])
print("empty_diagnostics=", empty["diagnostics"])
print("graph_nodes=", graph["node_count"], "graph_edges=", graph["edge_count"])
PY

rm -rf "$ROOT"
echo "cleanup: removed $ROOT"
echo "__DONE__"
