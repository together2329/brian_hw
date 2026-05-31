from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from workflow.sim_debug import elab
from workflow.sim_debug.elab import DualElab, PyslangElab


def _write_dut(root: Path) -> Path:
    """A module with directional ports of varied width + one internal reg."""
    rtl = root / "rtl"
    rtl.mkdir()
    dut = rtl / "dut.sv"
    dut.write_text(
        """
module dut (
  input  logic       clk,
  input  logic [7:0] din,
  output logic [7:0] dout
);
  logic [7:0] acc;
  always_ff @(posedge clk) begin
    acc  <= din;
    dout <= acc;
  end
endmodule
""".lstrip(),
        encoding="utf-8",
    )
    return dut


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


def test_trace_reports_multiple_driver_lines_in_text_fallback(
    tmp_path: Path, monkeypatch
) -> None:
    rtl = tmp_path / "rtl"
    rtl.mkdir()
    src = rtl / "multi.sv"
    src.write_text(
        """
module multi (
  input logic a,
  input logic b,
  output logic y
);
  assign y = a;
  always_comb begin
    y = b;
  end
endmodule
""".lstrip(),
        encoding="utf-8",
    )
    backend = PyslangElab()
    monkeypatch.setattr(
        backend,
        "_compile",
        lambda _sources: ("error", "force text fallback"),
    )

    out = backend.trace_driver("multi", "y", [src])

    assert out["driver"]["file_line"].endswith("multi.sv:6")
    assert out["driver_count"] == 2
    assert [d["file_line"].rsplit(":", 1)[-1] for d in out["drivers"]] == ["6", "8"]


def test_dual_hierarchy_runs_pyslang_and_verilator(monkeypatch) -> None:
    calls: list[tuple[str, str]] = []

    class FakeBackend:
        def __init__(self, name: str) -> None:
            self.name = name

        def available(self) -> bool:
            return True

        def build_hierarchy(self, top: str, sources: list[Path]) -> dict:
            calls.append((self.name, "build_hierarchy"))
            return {
                "backend": self.name,
                "tree": {"name": top, "module": top, "children": []},
                "modules_found": [top],
                "module_files": {top: {"file": f"{self.name}.sv", "line": 1}},
            }

    monkeypatch.setitem(elab._BACKENDS, "pyslang", FakeBackend("pyslang"))
    monkeypatch.setitem(elab._BACKENDS, "verilator", FakeBackend("verilator"))

    out = DualElab().build_hierarchy("top", [])

    assert calls == [("pyslang", "build_hierarchy"), ("verilator", "build_hierarchy")]
    assert out["backend"] == "pyslang+verilator"
    assert out["primary_backend"] == "pyslang"
    assert out["module_files"]["top"]["file"] == "pyslang.sv"
    assert [r["backend"] for r in out["backend_results"]] == ["pyslang", "verilator"]
    assert out["crosscheck"]["status"] == "match"


def test_pyslang_module_signals_classifies_ports_and_internals(tmp_path: Path) -> None:
    backend = PyslangElab()
    if not backend.available():
        pytest.skip("pyslang not available")
    dut = _write_dut(tmp_path)

    out = backend.module_signals("dut", "dut", [dut])

    assert out["backend"] == "pyslang"
    by_name = {s["name"]: s for s in out["signals"]}
    # Ports carry their direction; internal reg is classified 'internal'.
    assert by_name["clk"]["direction"] == "in"
    assert by_name["din"]["direction"] == "in"
    assert by_name["dout"]["direction"] == "out"
    assert by_name["acc"]["direction"] == "internal"
    # Width parsed from the packed range.
    assert by_name["din"]["width"] == 8
    assert by_name["clk"]["width"] == 1
    # Ports re-appear as backing Variables — must be de-duplicated (shown once).
    assert [s["name"] for s in out["signals"]].count("dout") == 1
    assert out["counts"] == {"in": 2, "out": 1, "inout": 0, "internal": 1, "total": 4}
    # Every signal keeps a source location for click-to-source.
    assert by_name["acc"]["file_line"].endswith("dut.sv:6")
    assert by_name["acc"]["line"] == 6


def test_module_signals_text_fallback_when_compile_fails(
    tmp_path: Path, monkeypatch
) -> None:
    dut = _write_dut(tmp_path)
    backend = PyslangElab()
    monkeypatch.setattr(
        backend, "_compile",
        lambda _sources: ("error", "module 'pyslang' has no attribute 'Compilation'"),
    )

    out = backend.module_signals("dut", "dut", [dut])

    assert out["backend"] == "pyslang-text-fallback"
    by_name = {s["name"]: s for s in out["signals"]}
    assert by_name["din"]["direction"] == "in"
    assert by_name["dout"]["direction"] == "out"
    assert by_name["din"]["width"] == 8
    # Internal reg picked up by the declaration scan.
    assert by_name["acc"]["direction"] == "internal"


def test_module_signals_cached_routes_through_pyslang(tmp_path: Path) -> None:
    backend = PyslangElab()
    if not backend.available():
        pytest.skip("pyslang not available")
    dut = _write_dut(tmp_path)
    out = elab.module_signals_cached("", "dut", "dut", [dut])
    assert out["backend"] in ("pyslang", "pyslang-text-fallback")
    assert out["counts"]["total"] == 4


def test_pyslang_trace_driver_lands_on_exact_assignment_line(tmp_path: Path) -> None:
    backend = PyslangElab()
    if not backend.available():
        pytest.skip("pyslang not available")
    dut = _write_dut(tmp_path)  # always_ff: acc<=din (L8), dout<=acc (L9)

    out = backend.trace_driver("dut", "acc", [dut])

    # Driver must point at the `acc <= din;` statement (line 8), NOT the
    # `always_ff` keyword on line 7.
    assert out["driver"]["file_line"].endswith("dut.sv:8"), out["driver"]
    # `acc` is read on `dout <= acc;` (line 9) → recorded as a load.
    sink_lines = {s["file_line"].rsplit(":", 1)[-1] for s in out["sinks"]}
    assert "9" in sink_lines, out["sinks"]


def test_pyslang_trace_load_in_condition_is_found(tmp_path: Path) -> None:
    """A read inside an `if (...)` condition counts as a load (the old
    RHS-only splitter missed these)."""
    backend = PyslangElab()
    if not backend.available():
        pytest.skip("pyslang not available")
    rtl = tmp_path / "rtl"
    rtl.mkdir()
    src = rtl / "cond.sv"
    src.write_text(
        """
module cond (
  input  logic clk,
  input  logic en,
  output logic q
);
  always_ff @(posedge clk) begin
    if (en)
      q <= 1'b1;
  end
endmodule
""".lstrip(),
        encoding="utf-8",
    )

    out = backend.trace_driver("cond", "en", [src])

    # `en` is read only inside the `if (en)` condition (line 7) — must appear
    # as a load even though it is never on an assignment RHS.
    sink_lines = {s["file_line"].rsplit(":", 1)[-1] for s in out["sinks"]}
    assert "7" in sink_lines, out["sinks"]


def test_cached_hierarchy_preserves_dual_backend_label(monkeypatch) -> None:
    class FakeDual:
        name = "dual"

        def build_hierarchy(self, top: str, sources: list[Path]) -> dict:
            return {
                "backend": "pyslang+verilator",
                "tree": {"name": top, "module": top, "children": []},
            }

    monkeypatch.setattr(elab, "get_backend", lambda _prefer: FakeDual())
    monkeypatch.setattr(elab, "_cache_get", lambda _key: None)
    monkeypatch.setattr(elab, "_cache_put", lambda _key, _data: None)

    out = elab.build_hierarchy_cached("", "top", [])

    assert out["backend"] == "pyslang+verilator"
