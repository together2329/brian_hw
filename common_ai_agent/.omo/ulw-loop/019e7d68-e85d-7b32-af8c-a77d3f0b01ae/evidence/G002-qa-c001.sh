set -euo pipefail
REPO="/Users/brian/Desktop/Project/brian_hw/common_ai_agent"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
cd "$REPO"
mkdir -p "$TMP/demo_ip/hdl" "$TMP/demo_ip/docs" "$TMP/platform/demo_soc/andes_ip/custom_core/top/hdl"
cat > "$TMP/demo_ip/hdl/demo_ip.sv" <<'SV'
module demo_ip #(parameter WIDTH = 8) (
    input clk,
    input rst_n,
    input [WIDTH-1:0] a,
    output logic [WIDTH-1:0] y
);
    logic [WIDTH-1:0] acc;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) acc <= '0;
        else acc <= a;
    end
    assign y = acc;
endmodule
SV
cat > "$TMP/platform/demo_soc/andes_ip/custom_core/top/hdl/custom_core_top.sv" <<'SV'
module custom_core_top (
    input logic core_clk,
    input logic core_rst_n,
    input logic req_valid,
    output logic rsp_valid
);
    logic [1:0] state;
    always_ff @(posedge core_clk or negedge core_rst_n) begin
        if (!core_rst_n) begin
            state <= 2'b00;
            rsp_valid <= 1'b0;
        end else begin
            state <= state + 2'b01;
            rsp_valid <= req_valid;
        end
    end
endmodule
SV
printf '%s\n' '# Demo IP User Guide' 'Nested custom core smoke doc.' > "$TMP/demo_ip/docs/Demo_IP_User_Guide.md"
python3 scripts/build_andes_rtl_db_wiki.py --andes-root "$TMP" --build-graph
python3 - "$TMP" <<'PY'
import json
import sys
from pathlib import Path
root = Path(sys.argv[1])
wiki = root / "wiki"
nested = "rtlroot-platform-demo-soc-andes-ip-custom-core-top"
coverage = json.loads((wiki / "_coverage.json").read_text())
assert coverage["summary"]["total_hdl_roots"] == 2, coverage["summary"]
assert coverage["summary"]["missing_pages"] == []
assert coverage["summary"]["missing_facts"] == []
assert (wiki / "coverage.md").is_file()
assert (wiki / "rtl-query-cookbook.md").is_file()
assert (wiki / f"{nested}.md").is_file()
facts = json.loads((wiki / "_rtl_facts" / f"{nested}.json").read_text())
assert "custom_core_top" in facts["modules"]
graph = json.loads((wiki / "_graph.json").read_text())
node_ids = {node["id"] for node in graph["nodes"]}
assert {"coverage", "rtl-query-cookbook", nested}.issubset(node_ids)
print("coverage_summary", coverage["summary"])
print("graph", graph["node_count"], graph["edge_count"])
PY
ATLAS_PROJECT_ROOT="$TMP" COMMON_AI_AGENT_HOME="$REPO" ATLAS_RTL_DB_WIKI="$TMP/wiki" ATLAS_RTL_DB_NO_REBUILD=1 python3 - <<'PY'
import importlib
wiki_query = importlib.import_module("core.tools").wiki_query
out = wiki_query(ip="rtl-db", topic="custom core coverage module", depth=3, max_nodes=5)
print(out)
assert "custom_core_top" in out or "rtlroot-platform-demo-soc-andes-ip-custom-core-top" in out
assert "coverage" in out.lower()
PY
echo "PASS C001 practical wiki"
