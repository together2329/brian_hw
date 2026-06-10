#!/usr/bin/env python3
"""run_synth.py — yosys generic synthesis + area/cell statistics.

Python port of run_synth.sh for native-Windows portability. Same CLI, exit
codes, generated yosys script, and ``yosys -p`` invocation.

Usage:
  run_synth.py <ip> [--root .] [--liberty <path>]

Generates:
  <ip>/syn/<ip>.netlist.v   — gate-level netlist
  <ip>/syn/<ip>.synth.json  — yosys JSON dump
  <ip>/syn/synth_report.txt — yosys stat output (cell count, area)
  <ip>/syn/synth.log        — full yosys log

Exit codes: 2 usage/bad flag/missing IP dir, 1 no RTL sources / yosys failed.
"""

from __future__ import annotations

import glob
import os
import subprocess
import sys
from pathlib import Path


def _parse_args(argv: list[str]) -> tuple[str, str, str] | int:
    """Replicate the shell while/case arg loop. Returns (ip, root, liberty)."""
    ip = ""
    root = "."
    liberty = ""
    i = 0
    n = len(argv)
    while i < n:
        arg = argv[i]
        if arg == "--root":
            root = argv[i + 1] if i + 1 < n else ""
            i += 2
        elif arg.startswith("--root="):
            root = arg.split("=", 1)[1]
            i += 1
        elif arg == "--liberty":
            liberty = argv[i + 1] if i + 1 < n else ""
            i += 2
        elif arg.startswith("--liberty="):
            liberty = arg.split("=", 1)[1]
            i += 1
        elif arg.startswith("-"):
            print(f"[run_synth] unknown flag: {arg}", file=sys.stderr)
            return 2
        else:
            ip = arg
            i += 1
    return ip, root, liberty


def _detect_top(ip_dir: Path, ip: str) -> str:
    """Mirror the embedded ``python3 - <<PY`` top-module heuristic (2>/dev/null).

    Returns "" if the SSOT can't be read (shell swallows stderr and TOP="").
    """
    try:
        import yaml

        with open(ip_dir / "yaml" / f"{ip}.ssot.yaml", encoding="utf-8") as handle:
            d = yaml.safe_load(handle)
        tm = d.get("top_module") or {}
        name = tm.get("name") or ip
        for sm in d.get("sub_modules") or []:
            if isinstance(sm, dict) and sm.get("wiring_only"):
                nm = (
                    (sm.get("file") or "")
                    .split("/")[-1]
                    .replace(".sv", "")
                    .replace(".v", "")
                )
                if nm:
                    return nm
        return str(name)
    except Exception:
        return ""


def _tail(text: str, n: int) -> str:
    lines = text.splitlines(keepends=True)
    return "".join(lines[-n:])


def main(argv: list[str]) -> int:
    parsed = _parse_args(argv)
    if isinstance(parsed, int):
        return parsed
    ip, root, liberty = parsed

    if not ip:
        print(
            "usage: run_synth.sh <ip> [--root .] [--liberty file.lib]",
            file=sys.stderr,
        )
        return 2
    try:
        root = str(Path(root).resolve(strict=True))
    except OSError:
        # `cd "$ROOT"` failure in the shell aborts; mirror with rc 2-ish. The
        # shell would emit a cd error and continue with set -u unset; keep it
        # simple and fail like a missing dir.
        print(f"missing IP dir: {Path(root) / ip}", file=sys.stderr)
        return 2
    ip_dir = Path(root) / ip
    if not ip_dir.is_dir():
        print(f"missing IP dir: {ip_dir}", file=sys.stderr)
        return 2

    syn_dir = ip_dir / "syn"
    syn_dir.mkdir(parents=True, exist_ok=True)

    netlist = syn_dir / f"{ip}.netlist.v"
    json_out = syn_dir / f"{ip}.synth.json"
    log = syn_dir / "synth.log"
    report = syn_dir / "synth_report.txt"

    # Collect RTL sources in dep order from filelist if present, else glob.
    sources: list[str] = []
    flist = ip_dir / "list" / f"{ip}.f"
    if flist.is_file():
        for line in flist.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line or line.startswith("#"):
                continue
            sources.append(f"{ip_dir}/{line}")
    else:
        for pattern in (f"{ip_dir}/rtl/*.sv", f"{ip_dir}/rtl/*.v"):
            sources.extend(sorted(glob.glob(pattern)))

    if not sources:
        print("[run_synth] no RTL sources found", file=sys.stderr)
        return 1

    # Top module: SSOT.top_module.name / wrapper / <ip>; "" → <ip>_wrapper.
    top = _detect_top(ip_dir, ip)
    if not top:
        top = f"{ip}_wrapper"

    inc = f"-I{ip_dir}/rtl"

    # `printf '"%s" ' "${SOURCES[@]}"` — quote each source, trailing space.
    sources_str = "".join(f'"{s}" ' for s in sources)

    yosys_script = (
        "# Auto-generated yosys script from workflow/syn/scripts/run_synth.sh\n"
        f"read_verilog -sv {inc} {sources_str}\n"
        f"hierarchy -check -top {top}\n"
        "proc\n"
        "flatten\n"
        "opt -fast\n"
        "fsm\n"
        "opt\n"
        "memory\n"
        "opt -fast"
    )

    if liberty and Path(liberty).is_file():
        yosys_script += "\n" + "techmap"
        yosys_script += "\n" + f'dfflibmap -liberty "{liberty}"'
        yosys_script += "\n" + f'abc -liberty "{liberty}"'
        yosys_script += "\n" + "clean"
        yosys_script += "\n" + f'stat -liberty "{liberty}"'
    else:
        yosys_script += "\n" + "techmap; opt"
        yosys_script += "\n" + "stat"

    yosys_script += "\n" + f'write_verilog -noattr -noexpr "{netlist}"'
    yosys_script += "\n" + f'write_json "{json_out}"'

    print(
        f"[run_synth] top={top}, sources={len(sources)}, "
        f"liberty={liberty or '<generic>'}"
    )
    print("[run_synth] running yosys...")

    # `yosys -p "$SCRIPT" 2>&1 | tee "$LOG" | tail -100 > "$REPORT"`
    # if-success = yosys exit 0 (pipefail makes the pipeline reflect tee/tail,
    # but tee/tail succeed here, so the gate is effectively yosys's rc).
    proc = subprocess.run(
        ["yosys", "-p", yosys_script],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    combined = proc.stdout or ""
    log.write_text(combined, encoding="utf-8")  # tee "$LOG"
    report.write_text(_tail(combined, 100), encoding="utf-8")  # tail -100 > REPORT

    if proc.returncode == 0:
        print("")
        print("[run_synth] === SYNTH STATS ===")
        # `grep -A 200 "Printing statistics" "$LOG" | head -80`
        log_lines = combined.splitlines()
        emitted: list[str] = []
        idx = 0
        while idx < len(log_lines):
            if "Printing statistics" in log_lines[idx]:
                block = log_lines[idx : idx + 201]
                emitted.extend(block)
            idx += 1
        for line in emitted[:80]:
            print(line)
        print("")
        print("[run_synth] OK")
        print(f"[run_synth]   netlist: {netlist}")
        print(f"[run_synth]   json:    {json_out}")
        print(f"[run_synth]   log:     {log}")
        return 0

    print(f"[run_synth] yosys failed — see {log}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
