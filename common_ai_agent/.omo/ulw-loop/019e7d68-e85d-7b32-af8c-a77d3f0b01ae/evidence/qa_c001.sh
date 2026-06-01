#!/usr/bin/env zsh
set -euo pipefail
cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent

ROOT=$(mktemp -d /tmp/andes-wiki-c001.XXXXXX)
mkdir -p "$ROOT/demo_ip/hdl" "$ROOT/demo_ip/docs"

cat > "$ROOT/demo_ip/hdl/demo_ip.sv" <<'SV'
module demo_ip #(parameter WIDTH = 8) (
  input logic clk,
  input logic rst_n,
  input logic [WIDTH-1:0] a,
  output logic [WIDTH-1:0] y
);
  localparam logic [1:0] ST_IDLE = 2'd0;
  localparam logic [1:0] ST_RUN = 2'd1;
  logic [1:0] state, next_state;
  logic [WIDTH-1:0] acc;
  logic [WIDTH-1:0] mem [0:3];
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= ST_IDLE;
      acc <= '0;
    end else begin
      state <= next_state;
      acc <= a;
    end
  end
  always_comb begin
    next_state = state;
    case (state)
      ST_IDLE: next_state = ST_RUN;
      ST_RUN: next_state = ST_IDLE;
      default: next_state = ST_IDLE;
    endcase
    y = acc + mem[0];
  end
endmodule
SV

cat > "$ROOT/demo_ip/docs/Demo_IP_User_Guide.md" <<'MD'
# Demo IP User Guide

The demo_ip block documents FSM, datapath, register, memory, clock, and reset behavior.
MD

python3 scripts/build_andes_rtl_db_wiki.py --andes-root "$ROOT" --build-graph
python3 - "$ROOT" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
wiki = root / "wiki"
facts = json.loads((wiki / "_rtl_facts" / "demo_ip.json").read_text())
graph = json.loads((wiki / "_graph.json").read_text())
page = (wiki / "demo_ip.md").read_text()

assert facts["block"] == "demo_ip"
assert "demo_ip/hdl/demo_ip.sv" in facts["ast_extracted_files"]
assert facts["ast_kind_counts"]["ModuleDeclaration"] >= 1
assert facts["ast_kind_counts"]["AlwaysFFBlock"] >= 1
for key, value in {
    "modules": "demo_ip",
    "clocks": "clk",
    "resets": "rst_n",
    "registers": "state",
    "memories": "mem",
}.items():
    assert value in facts[key], (key, facts[key])
assert any(p["name"] == "WIDTH" for p in facts["parameters"])
assert any(p["name"] == "y" and p["direction"] == "output" for p in facts["ports"])
assert "AST RTL facts" in page and "_rtl_facts/demo_ip.json" in page
node_ids = {node["id"] for node in graph["nodes"]}
assert "demo_ip" in node_ids
assert "doc-demo-ip-demo-ip-user-guide" in node_ids or "doc-inventory" in node_ids

print("C001 PASS synthetic AST/doc wiki")
print("features=", facts["features"])
print("ast_extracted_files=", facts["ast_extracted_files"])
print("graph_nodes=", graph["node_count"], "graph_edges=", graph["edge_count"])
PY

rm -rf "$ROOT"
echo "cleanup: removed $ROOT"
echo "__DONE__"
