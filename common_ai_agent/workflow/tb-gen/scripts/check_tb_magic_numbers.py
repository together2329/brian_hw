#!/usr/bin/env python3
"""Lint cocotb TB for unjustified timing literals.

Catches the pattern where TB encodes RTL timing assumptions as bare
integer literals (e.g. `for _w in range(5)` to pre-warm spi_clk) instead
of importing a named constant from <ip>_timing.py.

Strategy: AST-walk every Python file under <ip>/tb/cocotb/, find
calls to known timing-relevant APIs:
  - cocotb Timer(N, ...)         — N must be a Name (constant), not Constant
  - cocotb ClockCycles(_, N, ...) — same
  - range(N) inside async functions where the loop appears alongside
    spi_clk / sys_clk writes

Allow:
  - Named constants imported from <ip>_timing.py (or any module ending
    in _timing).
  - Documented justification: a string literal at first place "(SSOT
    timing_constraints.X)" in surrounding context.
  - Sub-millisecond setup-time literals when explicitly used in
    Timer(K, units="ns") with K <= 2 — these are simulator-race
    workarounds, will be replaced by SSOT-driven values.

Output:
  <ip>/lint/tb_magic_numbers.json  (machine-readable)
  Stdout: human summary
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Any


# Known TB-side names that import their literals from a timing header.
ALLOWED_NAMES_BY_PREFIX = ("T_", "TIME_", "_NS", "_PERIOD_NS", "_CYCLES")
TIMING_MODULE_SUFFIX = "_timing"


class _MagicVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str, allowed_names: set[str]):
        self.file_path = file_path
        self.allowed_names = allowed_names
        self.findings: list[dict[str, Any]] = []
        # Track current function context so we know when we're inside
        # an async function (cocotb sequence/agent body).
        self._async_depth = 0

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._async_depth += 1
        self.generic_visit(node)
        self._async_depth -= 1

    def _looks_like_named_constant(self, n: ast.AST) -> bool:
        """The argument is a Name (e.g. T_CS_SETUP_NS) — fine."""
        if isinstance(n, ast.Name):
            name = n.id
            if name in self.allowed_names:
                return True
            for prefix in ALLOWED_NAMES_BY_PREFIX:
                if name.startswith(prefix) or name.endswith(prefix):
                    return True
            return False
        # Allow simple arithmetic over named constants
        # (e.g. T_CS_SETUP_NS // SPI_CLK_PERIOD_NS).
        if isinstance(n, ast.BinOp):
            return self._looks_like_named_constant(n.left) and self._looks_like_named_constant(n.right)
        return False

    def _arg_is_magic_literal(self, arg: ast.AST) -> tuple[bool, Any]:
        """Return (is_magic, raw_value)."""
        if isinstance(arg, ast.Constant) and isinstance(arg.value, (int, float)):
            return (True, arg.value)
        return (False, None)

    def visit_Call(self, node: ast.Call) -> None:
        # Cocotb Timer(N, units=...)
        func_name = self._call_name(node.func)
        is_timer = func_name in ("Timer", "cocotb.Timer", "cocotb.utils.Timer")
        is_clk_cyc = func_name in ("ClockCycles", "cocotb.triggers.ClockCycles")
        is_range = func_name == "range" and self._async_depth > 0

        if (is_timer or is_clk_cyc) and node.args:
            magic, val = self._arg_is_magic_literal(node.args[0])
            if magic:
                # Allow tiny setup-time literals (Timer(K, "ns") with K <= 2)
                # as a temporary simulator-race workaround. Flag as warning.
                if is_timer and isinstance(val, (int, float)) and val <= 2:
                    self.findings.append({
                        "file": self.file_path, "line": node.lineno,
                        "kind": "tiny_setup_literal",
                        "value": val, "func": func_name,
                        "severity": "info",
                    })
                else:
                    self.findings.append({
                        "file": self.file_path, "line": node.lineno,
                        "kind": "timer_magic_number",
                        "value": val, "func": func_name,
                        "severity": "warning",
                    })

        if is_range and node.args:
            # Only flag range(N) when N looks timing-relevant. Heuristic:
            # accept any literal here as suspicious if surrounding code
            # touches spi_clk / sys_clk / cs_n / mosi (we don't have
            # surrounding context cheaply, so be conservative — flag any
            # literal range inside async fn).
            magic, val = self._arg_is_magic_literal(node.args[0])
            # Skip range(N) where N is small AND the loop is over a list
            # — we can't easily distinguish, so report and let the
            # author decide.
            if magic and isinstance(val, int) and 2 <= val <= 50:
                self.findings.append({
                    "file": self.file_path, "line": node.lineno,
                    "kind": "range_in_async",
                    "value": val,
                    "severity": "info",
                })
        self.generic_visit(node)

    def _call_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return f"{self._call_name(node.value)}.{node.attr}"
        return ""


def _collect_imported_names(tree: ast.AST) -> set[str]:
    """Collect names imported from any *_timing module."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = (node.module or "")
            if mod.endswith(TIMING_MODULE_SUFFIX):
                for alias in node.names:
                    names.add(alias.asname or alias.name)
    return names


def lint_file(path: Path, ip_dir: Path) -> list[dict[str, Any]]:
    src = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError:
        return [{
            "file": str(path.relative_to(ip_dir.parent)),
            "line": 0,
            "kind": "parse_error",
            "severity": "warning",
        }]
    allowed = _collect_imported_names(tree)
    v = _MagicVisitor(str(path.relative_to(ip_dir.parent)), allowed)
    v.visit(tree)
    return v.findings


def lint(ip: str, root: Path) -> dict[str, Any]:
    ip_dir = root / ip
    tb_dir = ip_dir / "tb" / "cocotb"
    if not tb_dir.is_dir():
        raise SystemExit(f"missing TB dir {tb_dir}")
    findings: list[dict[str, Any]] = []
    files_checked = 0
    for py in sorted(tb_dir.glob("*.py")):
        if py.name.endswith("_timing.py"):
            continue  # don't lint generated headers
        files_checked += 1
        findings.extend(lint_file(py, ip_dir))

    summary = {
        "errors": sum(1 for f in findings if f.get("severity") == "error"),
        "warnings": sum(1 for f in findings if f.get("severity") == "warning"),
        "infos": sum(1 for f in findings if f.get("severity") == "info"),
    }
    overall = "fail" if summary["errors"] else (
        "warn" if summary["warnings"] else "pass"
    )
    out = {
        "schema_version": 1,
        "type": "tb_magic_numbers",
        "ip": ip,
        "status": overall,
        "files_checked": files_checked,
        "summary": summary,
        "findings": findings,
    }

    out_path = ip_dir / "lint" / "tb_magic_numbers.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("ip")
    p.add_argument("--root", default=".")
    args = p.parse_args()

    res = lint(args.ip, Path(args.root).resolve())
    print(f"[tb-magic] status={res['status']} "
          f"errors={res['summary']['errors']} "
          f"warnings={res['summary']['warnings']} "
          f"infos={res['summary']['infos']}")
    for f in res["findings"]:
        if f["severity"] in ("warning", "error"):
            print(f"  {f['file']}:{f['line']}: {f['kind']} value={f.get('value')} "
                  f"({f.get('severity')})")
    return 0 if res["status"] != "fail" else 1


if __name__ == "__main__":
    sys.exit(main())
