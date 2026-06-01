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


def _write_minimal_top_level_ip(root: Path) -> Path:
    hdl = root / "demo_ip" / "hdl"
    hdl.mkdir(parents=True)
    (hdl / "demo_ip.sv").write_text(
        """
module demo_ip #(parameter WIDTH = 8) (
    input clk,
    input rst_n,
    input scan_enable,
    output logic y
);
    logic child_reg;
    logic [WIDTH-1:0] child_mem [0:1];

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) child_reg <= 1'b0;
        else child_reg <= scan_enable ^ child_mem[0][0];
    end

    demo_child #(.CHILD_PARAM(WIDTH)) u_child(.clk(clk), .y(y));
endmodule

module demo_child #(parameter CHILD_PARAM = 4)(input clk, output y);
    assign y = clk;
endmodule
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return root / "wiki"


def test_build_andes_wiki_disambiguates_nested_hdl_slug_collisions(tmp_path: Path) -> None:
    # Given: two nested HDL roots whose path slugs collapse to the same text.
    wiki = _write_minimal_top_level_ip(tmp_path)
    for rel, module in (("platform/a/b-c/hdl", "first_core"), ("platform/a-b/c/hdl", "second_core")):
        hdl = tmp_path / rel
        hdl.mkdir(parents=True)
        (hdl / f"{module}.sv").write_text(f"module {module}(input clk); endmodule\n", encoding="utf-8")

    # When: the builder emits the coverage wiki.
    result = _run_builder(tmp_path)

    # Then: each nested root gets a distinct page and fact sidecar.
    assert result.returncode == 0, result.stderr
    coverage = json.loads((wiki / "_coverage.json").read_text(encoding="utf-8"))
    nested = [entry for entry in coverage["entries"] if entry["hdl_root"] in {"platform/a/b-c/hdl", "platform/a-b/c/hdl"}]
    assert len(nested) == 2
    ids = [entry["id"] for entry in nested]
    assert len(set(ids)) == 2
    for entry in nested:
        assert (wiki / entry["page"]).is_file()
        assert (wiki / entry["fact"]).is_file()


def test_wiki_query_finds_top_level_sub_module_terms(tmp_path: Path, monkeypatch) -> None:
    # Given: a top-level IP whose wiki page and facts know about a child module.
    wiki = _write_minimal_top_level_ip(tmp_path)
    result = _run_builder(tmp_path)
    assert result.returncode == 0, result.stderr
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("COMMON_AI_AGENT_HOME", str(PROJECT_ROOT))
    monkeypatch.setenv("ATLAS_EXTERNAL_DB_WIKI", str(wiki))
    monkeypatch.setenv("ATLAS_EXTERNAL_DB_NO_REBUILD", "1")
    monkeypatch.delenv("ATLAS_RTL_DB_WIKI", raising=False)
    monkeypatch.delenv("ATLAS_RTL_DB_NO_REBUILD", raising=False)
    monkeypatch.delenv("ATLAS_EXTERNAL_DB_BUILDER", raising=False)
    monkeypatch.delenv("ATLAS_EXTERNAL_DB_QUERY", raising=False)
    monkeypatch.delenv("ATLAS_RTL_DB_BUILDER", raising=False)
    monkeypatch.delenv("ATLAS_RTL_DB_QUERY", raising=False)
    monkeypatch.delenv("ATLAS_ACTIVE_IP", raising=False)

    # When: an agent asks with natural "sub module" wording.
    wiki_query = importlib.import_module("core.tools").wiki_query
    output = wiki_query(ip="external-db", topic="demo ip sub module", depth=3)

    # Then: the external DB graph points back to the top-level IP page.
    assert "demo_ip" in output
    assert "matches=0" not in output


def test_wiki_query_finds_exact_top_level_fact_terms(tmp_path: Path, monkeypatch) -> None:
    # Given: a top-level IP with exact AST fact names in its sidecar.
    wiki = _write_minimal_top_level_ip(tmp_path)
    result = _run_builder(tmp_path)
    assert result.returncode == 0, result.stderr
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("COMMON_AI_AGENT_HOME", str(PROJECT_ROOT))
    monkeypatch.setenv("ATLAS_EXTERNAL_DB_WIKI", str(wiki))
    monkeypatch.setenv("ATLAS_EXTERNAL_DB_NO_REBUILD", "1")
    monkeypatch.delenv("ATLAS_RTL_DB_WIKI", raising=False)
    monkeypatch.delenv("ATLAS_RTL_DB_NO_REBUILD", raising=False)
    monkeypatch.delenv("ATLAS_EXTERNAL_DB_BUILDER", raising=False)
    monkeypatch.delenv("ATLAS_EXTERNAL_DB_QUERY", raising=False)
    monkeypatch.delenv("ATLAS_RTL_DB_BUILDER", raising=False)
    monkeypatch.delenv("ATLAS_RTL_DB_QUERY", raising=False)
    monkeypatch.delenv("ATLAS_ACTIVE_IP", raising=False)

    # When: an agent asks for concrete fact names from the generated answer key.
    wiki_query = importlib.import_module("core.tools").wiki_query
    outputs = [
        wiki_query(ip="external-db", topic=f"demo ip {term}", depth=3)
        for term in ("CHILD_PARAM", "scan_enable", "child_reg", "child_mem")
    ]

    # Then: every exact fact query resolves through the external DB graph.
    for output in outputs:
        assert "demo_ip" in output
        assert "matches=0" not in output
