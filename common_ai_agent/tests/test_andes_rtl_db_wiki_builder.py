from __future__ import annotations

import importlib
import json
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUILDER = PROJECT_ROOT / "scripts" / "build_andes_rtl_db_wiki.py"


def _run_builder(andes_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(BUILDER), "--andes-root", str(andes_root), "--build-graph"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def _write_demo_ip(root: Path) -> Path:
    hdl = root / "demo_ip" / "hdl"
    hdl.mkdir(parents=True)
    (hdl / "demo_ip.sv").write_text(
        """
module demo_ip #(
    parameter WIDTH = 8
) (
    input clk,
    input rst_n,
    input [WIDTH-1:0] a,
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
""".strip()
        + "\n",
        encoding="utf-8",
    )
    docs = root / "demo_ip" / "docs"
    docs.mkdir()
    (docs / "Demo_IP_User_Guide.md").write_text(
        "# Demo IP User Guide\n\nThe demo_ip block documents FSM and datapath behavior.\n",
        encoding="utf-8",
    )
    return root / "wiki"


def test_build_andes_wiki_emits_ast_rtl_facts_and_doc_links(tmp_path: Path) -> None:
    # Given: a small SystemVerilog IP with parameters, ports, registers, FSM, memory, and docs.
    wiki = _write_demo_ip(tmp_path)

    # When: the Andes RTL DB wiki builder runs with graph generation.
    result = _run_builder(tmp_path)

    # Then: the run succeeds and publishes AST-derived facts plus doc graph nodes.
    assert result.returncode == 0, result.stderr
    facts_path = wiki / "_rtl_facts" / "demo_ip.json"
    assert facts_path.is_file(), result.stdout + result.stderr

    facts = json.loads(facts_path.read_text(encoding="utf-8"))
    assert facts.get("schema_version") or facts.get("version")
    assert facts.get("block") == "demo_ip"
    assert "demo_ip" in facts.get("modules", [])
    assert any(item.get("name") == "WIDTH" for item in facts.get("parameters", []))
    ports = {item.get("name"): item.get("direction") for item in facts.get("ports", [])}
    assert ports == {"clk": "input", "rst_n": "input", "a": "input", "y": "output"}
    assert "clk" in facts.get("clocks", [])
    assert "rst_n" in facts.get("resets", [])
    assert {"state", "acc"}.issubset(set(facts.get("registers", [])))
    assert "mem" in facts.get("memories", [])
    fsm_text = json.dumps(facts.get("fsm_candidates", []))
    assert "state" in fsm_text and ("case" in fsm_text or "ST_IDLE" in fsm_text)
    datapath_text = json.dumps(facts.get("datapaths", facts.get("assignments", [])))
    assert "y" in datapath_text and "acc" in datapath_text and "mem" in datapath_text

    block_page = (wiki / "demo_ip.md").read_text(encoding="utf-8")
    assert "AST RTL facts" in block_page
    assert "_rtl_facts/demo_ip.json" in block_page

    doc_pages = [path for path in wiki.glob("*.md") if "guide" in path.stem.lower()]
    assert doc_pages
    assert any("[[demo_ip]]" in path.read_text(encoding="utf-8") for path in doc_pages)

    graph = json.loads((wiki / "_graph.json").read_text(encoding="utf-8"))
    node_ids = {node["id"] for node in graph["nodes"]}
    assert "demo_ip" in node_ids
    assert any("guide" in node_id or node_id == "doc-inventory" for node_id in node_ids)


def test_build_andes_wiki_reports_diagnostics_for_malformed_and_empty_blocks(tmp_path: Path) -> None:
    # Given: one malformed RTL block, one empty HDL block, and a doc file.
    broken_hdl = tmp_path / "broken_ip" / "hdl"
    broken_hdl.mkdir(parents=True)
    (broken_hdl / "broken_ip.sv").write_text(
        "module broken_ip(input clk\nalways_ff @(posedge clk) begin\n",
        encoding="utf-8",
    )
    (tmp_path / "empty_ip" / "hdl").mkdir(parents=True)
    docs = tmp_path / "broken_ip" / "docs"
    docs.mkdir()
    (docs / "Broken_IP_User_Guide.md").write_text("# Broken IP\n", encoding="utf-8")

    # When: the builder indexes the imperfect corpus.
    result = _run_builder(tmp_path)

    # Then: it exits cleanly and records diagnostics instead of dropping blocks.
    assert result.returncode == 0, result.stderr
    wiki = tmp_path / "wiki"
    facts_path = wiki / "_rtl_facts" / "broken_ip.json"
    assert facts_path.is_file(), result.stdout + result.stderr
    facts = json.loads(facts_path.read_text(encoding="utf-8"))
    assert facts.get("diagnostics")
    assert (wiki / "empty_ip.md").is_file()
    assert (wiki / "_graph.json").is_file()


def test_wiki_query_surfaces_generated_ast_terms_for_andes_rtl_db(
    tmp_path: Path,
    monkeypatch,
) -> None:
    # Given: a generated external RTL DB wiki with AST facts and no rebuild during query.
    wiki = _write_demo_ip(tmp_path)
    result = _run_builder(tmp_path)
    assert result.returncode == 0, result.stderr
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("COMMON_AI_AGENT_HOME", str(PROJECT_ROOT))
    monkeypatch.setenv("ATLAS_RTL_DB_WIKI", str(wiki))
    monkeypatch.setenv("ATLAS_RTL_DB_NO_REBUILD", "1")
    monkeypatch.delenv("ATLAS_RTL_DB_BUILDER", raising=False)
    monkeypatch.delenv("ATLAS_ACTIVE_IP", raising=False)

    # When: ATLAS queries for implementation-level RTL structure.
    wiki_query = importlib.import_module("core.tools").wiki_query
    output = wiki_query(ip="rtl-db", topic="demo_ip fsm register memory clk rst", depth=3)

    # Then: the result includes the demo IP and AST-derived summary terms.
    assert "demo_ip" in output
    assert "fsm" in output.lower()
    assert "register" in output.lower()
    assert "memory" in output.lower()
    assert "clk" in output.lower()
    assert "rst" in output.lower()
