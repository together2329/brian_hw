from __future__ import annotations

import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from core.pyslang_compat import PyslangCompileResult


def _write_sv(tmp_path: Path) -> Path:
    path = tmp_path / "top.sv"
    path.write_text(
        """
module child(input logic a, output logic y);
  assign y = a;
endmodule

module top(input logic clk, input logic din, output logic dout);
  child u_child(
    .a(din),
    .y(dout)
  );
endmodule
""".lstrip(),
        encoding="utf-8",
    )
    return path


def test_sv_get_ports_falls_back_to_regex_when_pyslang_api_drifts(tmp_path, monkeypatch):
    import core.tools_verilog as tools_verilog

    path = _write_sv(tmp_path)
    monkeypatch.setattr(tools_verilog, "HAS_PYSLANG", True)
    monkeypatch.setattr(
        tools_verilog,
        "compile_pyslang_files",
        lambda _files: PyslangCompileResult(error="module 'pyslang' has no attribute 'SyntaxTree'"),
    )

    ports = tools_verilog.sv_get_ports(str(path))

    assert {p["name"] for p in ports} == {"clk", "din", "dout"}
    assert all(p["backend"] == "regex-fallback" for p in ports)
    assert all("SyntaxTree" in p["warning"] for p in ports)


def test_sv_get_hierarchy_falls_back_to_regex_when_pyslang_api_drifts(tmp_path, monkeypatch):
    import core.tools_verilog as tools_verilog

    path = _write_sv(tmp_path)
    monkeypatch.setattr(tools_verilog, "HAS_PYSLANG", True)
    monkeypatch.setattr(
        tools_verilog,
        "compile_pyslang_files",
        lambda _files: PyslangCompileResult(error="module 'pyslang' has no attribute 'SyntaxTree'"),
    )

    hierarchy = tools_verilog.sv_get_hierarchy(str(path))

    assert hierarchy["backend"] == "regex-fallback"
    assert hierarchy["top"] == "top"
    assert hierarchy["instances"] == [{"instance": "u_child", "module": "child"}]
    assert "SyntaxTree" in hierarchy["warning"]


def test_simple_linter_reports_pyslang_setup_failure_without_crashing(tmp_path, monkeypatch):
    import core.simple_linter as simple_linter

    path = _write_sv(tmp_path)
    monkeypatch.setattr(simple_linter, "HAS_PYSLANG", True)
    monkeypatch.setattr(
        simple_linter,
        "compile_pyslang_files",
        lambda _files: PyslangCompileResult(error="module 'pyslang' has no attribute 'SyntaxTree'"),
    )

    linter = simple_linter.SimpleLinter()
    linter.tools["pyslang"] = True
    errors = linter.check_file(str(path))

    assert len(errors) == 1
    assert errors[0].severity == "warning"
    assert "SyntaxTree" in errors[0].message


def test_fold_extractor_returns_empty_folds_for_incomplete_pyslang_binding(monkeypatch):
    import core.fold_extractor as fold_extractor

    class FakePyslang:
        pass

    monkeypatch.setattr(fold_extractor, "import_pyslang", lambda: (FakePyslang(), ""))

    assert fold_extractor.extract_verilog_folds("module top; endmodule\n") == []
