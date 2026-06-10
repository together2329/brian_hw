#!/usr/bin/env python3
"""preflight.py — Diagnose synthesis tool/PDK/IP inputs before running yosys.

Python port of preflight.sh for native-Windows portability. Same CLI, exit
codes, and stdout/stderr ordering.

Falls back to HOOK_CMD_ARGS for the IP name when no positional arg is given
(matching the shell original). Sources pdk_env semantics via pdk_env.py.

Exit codes (last assignment wins, mirroring the shell STATUS accumulator):
  0 OK, 2 IP/SSOT/filelist problem, 3 required tool missing, 4 PDK file missing.
"""

from __future__ import annotations

import os
import pathlib
import shlex
import shutil
import sys
from pathlib import Path

# Import the pdk_env port (mirrors `source pdk_env.sh`).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
import pdk_env  # noqa: E402


def _resolve_ip(argv: list[str]) -> str:
    args = list(argv)
    if not args and os.environ.get("HOOK_CMD_ARGS", ""):
        args = shlex.split(os.environ["HOOK_CMD_ARGS"])
    return args[0] if args else ""


def _check_ip_inputs(ip: str) -> int:
    """Embedded-Python SSOT/filelist/RTL check. Mirrors the heredoc verbatim."""
    ip_path = pathlib.Path(ip)
    ssot = ip_path / "yaml" / f"{ip_path.name}.ssot.yaml"
    flist = ip_path / "list" / f"{ip_path.name}.f"
    status = 0

    def report(ok: bool, label: str, path: pathlib.Path) -> None:
        nonlocal status
        if ok:
            print(f"[SYN PREFLIGHT] {label}: OK {path}")
        else:
            print(f"[SYN PREFLIGHT] {label}: MISSING {path}", file=sys.stderr)
            status = 2

    report(ssot.is_file(), "SSOT", ssot)
    report(flist.is_file(), "filelist", flist)

    if flist.is_file():
        missing: list[str] = []
        entries: list[pathlib.Path] = []
        for raw in flist.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.split("//", 1)[0].split("#", 1)[0].strip()
            if not line or line.startswith(("+", "-")):
                continue
            if not line.endswith((".v", ".sv", ".vh", ".svh")):
                continue
            p = pathlib.Path(line)
            candidates = (
                [p] if p.is_absolute() else [ip_path / p, pathlib.Path.cwd() / p]
            )
            hit = next((c for c in candidates if c.is_file()), None)
            if hit is None:
                missing.append(line)
            else:
                entries.append(hit)
        print(f"[SYN PREFLIGHT] filelist RTL entries: {len(entries)}")
        if missing:
            print("[SYN PREFLIGHT] missing RTL entries:", file=sys.stderr)
            for item in missing[:20]:
                print(f"  - {item}", file=sys.stderr)
            status = 2
        elif not entries:
            print("[SYN PREFLIGHT] filelist has no RTL entries", file=sys.stderr)
            status = 2

    return status


def main(argv: list[str]) -> int:
    ip = _resolve_ip(argv)

    directory = str(Path(__file__).resolve().parent)
    pdk_env.apply_pdk_env(os.environ)

    status = 0

    def check_file(label: str, path: str) -> None:
        nonlocal status
        if path and os.access(path, os.R_OK):
            print(f"[SYN PREFLIGHT] {label}: OK {path}")
        else:
            print(f"[SYN PREFLIGHT] {label}: MISSING {path}", file=sys.stderr)
            status = 4

    def check_tool(tool: str, required: str) -> None:
        nonlocal status
        found = shutil.which(tool)
        if found:
            print(f"[SYN PREFLIGHT] tool {tool}: OK {found}")
        elif required == "required":
            print(f"[SYN TOOL MISSING] {tool} not on PATH", file=sys.stderr)
            status = 3
        else:
            print(f"[SYN PREFLIGHT] tool {tool}: not found (optional here)")

    print(f"[SYN PREFLIGHT] cwd={os.getcwd()}")
    print(f"[SYN PREFLIGHT] scripts={directory}")
    print(f"[SYN PREFLIGHT] PDK_ROOT={os.environ.get('PDK_ROOT', '')}")
    print(f"[SYN PREFLIGHT] SKY130_PDK_ROOT={os.environ.get('SKY130_PDK_ROOT', '')}")
    print(f"[SYN PREFLIGHT] PDK_LIB_PATH={os.environ.get('PDK_LIB_PATH', '')}")

    check_tool("yosys", "required")
    check_tool("sta", "optional")
    check_tool("openroad", "optional")

    check_file("SKY130_LIB", os.environ.get("SKY130_LIB", ""))
    check_file("SKY130_TLEF", os.environ.get("SKY130_TLEF", ""))
    check_file("SKY130_LEF", os.environ.get("SKY130_LEF", ""))
    check_file("SKY130_TRACKS", os.environ.get("SKY130_TRACKS", ""))

    if ip:
        if not Path(ip).is_dir():
            print(f"[SYN PREFLIGHT] IP dir: MISSING {ip}", file=sys.stderr)
            status = 2
        else:
            print(f"[SYN PREFLIGHT] IP dir: OK {ip}")
            rc = _check_ip_inputs(ip)
            if rc:
                status = rc
    else:
        print(
            "[SYN PREFLIGHT] IP dir: skipped "
            "(pass <ip> to check SSOT/filelist/RTL)"
        )

    if status == 0:
        print("[SYN PREFLIGHT] OK")
    else:
        print(f"[SYN PREFLIGHT] FAILED rc={status}", file=sys.stderr)
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
