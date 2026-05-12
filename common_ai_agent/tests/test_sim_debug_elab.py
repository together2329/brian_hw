from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from workflow.sim_debug.elab import PyslangElab


def _write_rtl(root: Path) -> list[Path]:
    rtl = root / "rtl"
    rtl.mkdir()
    child = rtl / "child.sv"
    top = rtl / "top.sv"
    child.write_text(
        """
module child (
  input  logic clk,
  input  logic din,
  output logic dout
);
  always_ff @(posedge clk) begin
    dout <= din;
  end
endmodule
""".lstrip(),
        encoding="utf-8",
    )
    top.write_text(
        """
module top (
  input  logic clk,
  input  logic din,
  output logic dout
);
  child u_child (
    .clk(clk),
    .din(din),
    .dout(dout)
  );
endmodule
""".lstrip(),
        encoding="utf-8",
    )
    return [child, top]


def test_pyslang_hierarchy_uses_text_fallback_when_syntax_tree_api_differs(
    tmp_path: Path, monkeypatch
) -> None:
    sources = _write_rtl(tmp_path)
    backend = PyslangElab()
    monkeypatch.setattr(
        backend,
        "_compile",
        lambda _sources: ("error", "module 'pyslang' has no attribute 'SyntaxTree'"),
    )

    out = backend.build_hierarchy("top", sources)

    assert out["backend"] == "pyslang-text-fallback"
    assert "SyntaxTree" in out["warning"]
    assert out["tree"]["module"] == "top"
    assert out["tree"]["children"][0]["name"] == "top.u_child"
    assert out["tree"]["children"][0]["module"] == "child"
    assert out["module_files"]["child"]["file"].endswith("child.sv")


def test_pyslang_trace_uses_text_fallback_when_compile_api_differs(
    tmp_path: Path, monkeypatch
) -> None:
    sources = _write_rtl(tmp_path)
    backend = PyslangElab()
    monkeypatch.setattr(
        backend,
        "_compile",
        lambda _sources: ("error", "module 'pyslang' has no attribute 'SyntaxTree'"),
    )

    out = backend.trace_driver("top", "dout", sources)

    assert out["backend"] == "pyslang-text-fallback"
    assert out["driver"]["file_line"].endswith("child.sv:7")
    assert out["sink_count"] >= 1
