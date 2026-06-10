#!/usr/bin/env python3
"""Compile generated cocotb Python files before running simulation.

This is a cheap pre-sim gate.  It catches broken generated strings and syntax
errors before cocotb/iverilog startup hides the root cause behind simulator
noise.  The gate writes a small JSON artifact so orchestrators can distinguish
"TB Python is syntactically valid" from "simulation passed".
"""

from __future__ import annotations

import argparse
import json
import py_compile
import time
from pathlib import Path


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _compile_files(paths: list[Path]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    for path in paths:
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(
                {
                    "file": str(path),
                    "error": exc.msg,
                }
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ip")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    ip_dir = root / args.ip
    tb_dir = ip_dir / "tb" / "cocotb"
    artifact = tb_dir / "tb_py_compile.json"

    result: dict[str, object] = {
        "schema_version": 1,
        "type": "tb_python_compile",
        "generated_at": _utc(),
        "ip": args.ip,
        "tb_dir": str(tb_dir.relative_to(root)) if tb_dir.exists() else str(tb_dir),
        "files": [],
        "errors": [],
        "passed": False,
    }

    if not ip_dir.is_dir():
        result["errors"] = [{"file": str(ip_dir), "error": "missing IP directory"}]
    elif not tb_dir.is_dir():
        result["errors"] = [{"file": str(tb_dir), "error": "missing cocotb TB directory"}]
    else:
        paths = sorted(tb_dir.glob("*.py"))
        result["files"] = [str(path.relative_to(root)) for path in paths]
        if not paths:
            result["errors"] = [{"file": str(tb_dir.relative_to(root)), "error": "no Python TB files"}]
        else:
            errors = _compile_files(paths)
            result["errors"] = errors
            result["passed"] = not errors

    tb_dir.mkdir(parents=True, exist_ok=True)
    artifact.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if result["passed"]:
        print(f"[check_tb_python_compile] PASS: compiled {len(result['files'])} file(s)")
        print(f"[check_tb_python_compile] wrote {artifact.relative_to(root)}")
        return 0

    print(f"[check_tb_python_compile] FAIL: wrote {artifact.relative_to(root)}")
    for error in result["errors"]:
        if isinstance(error, dict):
            print(f"[check_tb_python_compile]   {error.get('file')}: {error.get('error')}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
