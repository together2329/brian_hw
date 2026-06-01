#!/usr/bin/env zsh
set -euo pipefail
cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent

ROOT=$(mktemp -d /tmp/andes-wiki-c003.XXXXXX)
mkdir -p "$ROOT/demo_ip/hdl" "$ROOT/demo_ip/docs"

cat > "$ROOT/demo_ip/hdl/demo_ip.sv" <<'SV'
module demo_ip #(parameter WIDTH = 8) (
  input logic clk,
  input logic rst_n,
  input logic [WIDTH-1:0] a,
  output logic [WIDTH-1:0] y
);
  logic [1:0] state;
  logic [WIDTH-1:0] mem [0:3];
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) state <= 2'd0;
    else state <= state + 2'd1;
  end
  always_comb begin
    case (state)
      2'd0: y = a;
      default: y = mem[0];
    endcase
  end
endmodule
SV

cat > "$ROOT/demo_ip/docs/Demo_IP_User_Guide.md" <<'MD'
# Demo IP User Guide

The guide is linked into the RTL DB wiki for agent lookup.
MD

python3 scripts/build_andes_rtl_db_wiki.py --andes-root "$ROOT" --build-graph

ATLAS_RTL_DB_WIKI="$ROOT/wiki" \
ATLAS_RTL_DB_NO_REBUILD=1 \
ATLAS_PROJECT_ROOT="$ROOT" \
COMMON_AI_AGENT_HOME=/Users/brian/Desktop/Project/brian_hw/common_ai_agent \
python3 - <<'PY'
from core.tools import wiki_query

output = wiki_query(ip="rtl-db", topic="fsm register memory clock reset", depth=3, max_nodes=5)
print(output)
lower = output.lower()
assert "demo_ip" in output
for term in ("fsm", "register", "memory", "clock", "reset"):
    assert term in lower, term
doc_output = wiki_query(ip="andes", topic="user guide", depth=3, max_nodes=5)
print(doc_output)
assert "doc-demo_ip-demo-ip-user-guide" in doc_output or "Demo IP User Guide" in doc_output
print("C003 enabled query PASS")
PY

env -u ATLAS_RTL_DB_WIKI -u ATLAS_EXTERNAL_DB_WIKI -u ATLAS_RTL_DB_QUERY -u ATLAS_EXTERNAL_DB_QUERY \
  COMMON_AI_AGENT_HOME=/Users/brian/Desktop/Project/brian_hw/common_ai_agent \
  python3 - <<'PY'
from core.tools import wiki_query

output = wiki_query(ip="rtl-db", topic="uart")
print(output)
assert "ATLAS_RTL_DB_WIKI is not configured" in output
print("C003 disabled query PASS")
PY

rg -n "_rtl_facts|ATLAS_RTL_DB_WIKI|ATLAS_EXTERNAL_DB_WIKI|ATLAS_RTL_DB_QUERY|wiki_query\\(ip=\"external-db\"\\)|fsm|register|memory|clock|reset" \
  skills/external-db/SKILL.md \
  doc/wiki/andes-rtl-db-wiki-20260527.md \
  doc/wiki/external-rtl-db-integration-guide.md

python3 -m pytest \
  tests/test_wiki_query_tool.py::test_wiki_query_reads_external_rtl_db_wiki_without_ip_scope \
  tests/test_wiki_query_tool.py::test_wiki_query_external_builder_override_for_foreign_wiki \
  tests/test_wiki_query_tool.py::test_wiki_query_no_rebuild_trusts_shipped_graph \
  tests/test_wiki_query_tool.py::test_wiki_query_external_query_adapter_owns_lookup \
  -q

rm -rf "$ROOT"
echo "cleanup: removed $ROOT"
echo "__DONE__"
