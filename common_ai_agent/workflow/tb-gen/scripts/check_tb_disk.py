#!/usr/bin/env python3
"""check_tb_disk.py — Disk-truth validator for tb-gen tasks.

Python port of check_tb_disk.sh for native-Windows portability.

Verifies the deliverables that a TB-gen task CLAIMS to have produced
actually exist on disk with non-trivial size. Replaces the previous
stdout-grep-only validator that lets agents fake completions by
echoing "0 errors, 0 warnings" without running anything.

Supports four verification surfaces:
  - cocotb/Python: <ip>/tb/cocotb/test_<ip>.py + test_runner.py
  - cocotb flat:   <ip>/tb/test_<ip>.py + test_runner.py
  - cocotb sim:    <ip>/sim/test_<ip>.py + <ip>/sim/Makefile (Makefile IS the runner)
  - legacy SV:     <ip>/tb/tb_<ip>.sv + <ip>/tc/tc_<ip>.sv + list/<ip>.f

Inputs (env vars):
  IP_NAME — IP root name (default: derived from current working directory).
  MIN_PY  — minimum bytes for cocotb Python files (default 500)
  MIN_TC  — minimum bytes for tc_<ip>.sv (default 1000)
  MIN_TB  — minimum bytes for tb_<ip>.sv (default 500)
  MIN_F   — minimum bytes for list/<ip>.f (default 50)

Exit 0 = real artifacts on disk meet thresholds; tracker may approve.
Exit 1 = disk reality contradicts claimed completion; tracker rejects.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path


def _auto_detect_ip() -> str:
    """Replicate: find . -maxdepth 3 -type f -name '*.ssot.yaml'
    | sort -t/ -k2 | head -1 | awk -F/ '{print $(NF-2)}'."""
    root = Path(".")
    matches: list[str] = []
    for pat in ("*/*/*.ssot.yaml", "*/*.ssot.yaml", "*.ssot.yaml"):
        for path in root.glob(pat):
            matches.append("./" + path.as_posix())

    def sort_key(item: str) -> str:
        parts = item.split("/")
        return parts[1] if len(parts) > 1 else ""

    matches.sort(key=sort_key)
    if not matches:
        return ""
    fields = matches[0].split("/")
    return fields[-3] if len(fields) >= 3 else ""


def _size(path: Path) -> int:
    """Port of _size(): file size in bytes, or 0 if not a regular file."""
    return path.stat().st_size if path.is_file() else 0


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def _grep_eq(pattern: str, path: Path, ignore_case: bool = False) -> bool:
    """grep -Eq — true if any line matches the extended-regex pattern."""
    flags = re.IGNORECASE if ignore_case else 0
    rx = re.compile(pattern, flags)
    return any(rx.search(line) for line in _read(path).splitlines())


def _grep_q_fixed(needle: str, path: Path) -> bool:
    """grep -q (no -E) — fixed/basic match; needle here has no regex metachars
    apart from the literal brackets, so substring test is faithful."""
    return needle in _read(path)


class Ctx:
    def __init__(self, ip: str) -> None:
        self.ip = ip
        self.MIN_PY = int(os.environ.get("MIN_PY", "500"))
        self.MIN_TC = int(os.environ.get("MIN_TC", "1000"))
        self.MIN_TB = int(os.environ.get("MIN_TB", "500"))
        self.MIN_F = int(os.environ.get("MIN_F", "50"))
        self.MAKEFILE = Path(ip) / "Makefile"


def _check_cocotb_layout(ctx: Ctx, test_path: Path, runner_path: Path, layout: str) -> bool:
    test_sz = _size(test_path)
    runner_sz = _size(runner_path)
    fail = 0
    if test_sz < ctx.MIN_PY:
        print(f"[check_tb_disk] FAIL: {test_path.as_posix()} = {test_sz}B (need ≥{ctx.MIN_PY})")
        fail = 1
    if runner_sz < ctx.MIN_PY:
        print(f"[check_tb_disk] FAIL: {runner_path.as_posix()} = {runner_sz}B (need ≥{ctx.MIN_PY})")
        fail = 1
    if fail != 0:
        return False

    if not _grep_eq(r"^[ \t]*(import cocotb|from cocotb)", test_path):
        print(f"[check_tb_disk] FAIL: {test_path.as_posix()} does not import cocotb")
        return False
    if not _grep_eq(r"get_runner|cocotb_test|pytest|cocotb", runner_path):
        print(f"[check_tb_disk] FAIL: {runner_path.as_posix()} is not a recognizable cocotb runner")
        return False
    if _grep_q_fixed("[FAIL]", test_path) and not _grep_eq(
        r"raise[ \t]+AssertionError|assert[ \t]+[^=]", test_path
    ):
        print(f"[check_tb_disk] FAIL: {test_path.as_posix()} logs [FAIL] but has no assertion/raise path")
        print("  Hint: SSOT scenario failures must fail cocotb, not only increment counters or log text.")
        return False
    if ctx.MAKEFILE.is_file() and _grep_eq(
        rf"tb_{re.escape(ctx.ip)}\.sv|tc_{re.escape(ctx.ip)}\.sv|tb/.*\.sv|tc/.*\.sv", ctx.MAKEFILE
    ):
        print(f"[check_tb_disk] FAIL: {ctx.MAKEFILE.as_posix()} references legacy SV TB while cocotb layout is present")
        return False

    print(f"[check_tb_disk] PASS: {layout} cocotb test={test_sz}B runner={runner_sz}B")
    return True


def _check_uvm_layout(ctx: Ctx, dir_path: Path) -> bool:
    files = sorted(
        p
        for p in dir_path.glob("*")
        if p.is_file() and p.suffix in (".sv", ".svh", ".f")
    )
    if not files:
        print(f"[check_tb_disk] FAIL: {dir_path.as_posix()} has no UVM source files")
        return False

    all_text = "".join(_read(p) for p in files)
    # `printf '%s\n' "$all_text" | wc -c` adds one trailing newline byte.
    byte_count = len(all_text.encode("utf-8", errors="replace")) + 1
    if byte_count < 1000:
        print(f"[check_tb_disk] FAIL: {dir_path.as_posix()} UVM sources are too small to be a real environment")
        return False

    fail = 0
    text_lines = all_text.splitlines()

    def require_uvm_pattern(label: str, pattern: str) -> None:
        nonlocal fail
        rx = re.compile(pattern, re.IGNORECASE)
        if not any(rx.search(line) for line in text_lines):
            print(f"[check_tb_disk] FAIL: UVM layout missing {label} ({pattern})")
            fail = 1

    require_uvm_pattern("uvm package/import", r'`include[ \t]+"uvm_macros\.svh"|import[ \t]+uvm_pkg::\*')
    require_uvm_pattern("interface or virtual interface", r"interface[ \t]|virtual[ \t]+.*interface")
    require_uvm_pattern("sequence item / transaction", r"uvm_sequence_item|class[ \t].*(transaction|item)")
    require_uvm_pattern("sequence", r"uvm_sequence|class[ \t].*sequence")
    require_uvm_pattern("driver", r"uvm_driver|class[ \t].*driver")
    require_uvm_pattern("monitor", r"uvm_monitor|class[ \t].*monitor")
    require_uvm_pattern("scoreboard", r"uvm_scoreboard|class[ \t].*scoreboard|expected.*got|got.*expected")
    require_uvm_pattern("coverage collector", r"covergroup|coverage|coverpoint")
    require_uvm_pattern("environment", r"uvm_env|class[ \t].*env")
    require_uvm_pattern("test", r"uvm_test|class[ \t].*test")
    require_uvm_pattern("assertion/fatal failure path", r"`uvm_error|`uvm_fatal|\$fatal|assert[ \t]*\(")

    if fail != 0:
        return False
    print(f"[check_tb_disk] PASS: tb/uvm UVM structure exists under {dir_path.as_posix()}")
    return True


def _check_sim_cocotb_layout(ctx: Ctx, test_path: Path, makefile_path: Path) -> bool:
    test_sz = _size(test_path)
    makefile_sz = _size(makefile_path)
    fail = 0
    if test_sz < ctx.MIN_PY:
        print(f"[check_tb_disk] FAIL: {test_path.as_posix()} = {test_sz}B (need ≥{ctx.MIN_PY})")
        fail = 1
    if makefile_sz < ctx.MIN_F:
        print(f"[check_tb_disk] FAIL: {makefile_path.as_posix()} = {makefile_sz}B (need ≥{ctx.MIN_F})")
        fail = 1
    if fail != 0:
        return False

    if not _grep_eq(r"^[ \t]*(import cocotb|from cocotb)", test_path):
        print(f"[check_tb_disk] FAIL: {test_path.as_posix()} does not import cocotb")
        return False

    # Makefile must reference cocotb-compatible settings.
    if not _grep_eq(r"(MODULE|TOPLEVEL_LANG|cocotb|COCOTB)", makefile_path):
        print(
            f"[check_tb_disk] FAIL: {makefile_path.as_posix()} does not reference cocotb settings "
            "(MODULE, TOPLEVEL_LANG, COCOTB)"
        )
        return False

    if _grep_q_fixed("[FAIL]", test_path) and not _grep_eq(
        r"raise[ \t]+AssertionError|assert[ \t]+[^=]", test_path
    ):
        print(f"[check_tb_disk] FAIL: {test_path.as_posix()} logs [FAIL] but has no assertion/raise path")
        print("  Hint: SSOT scenario failures must fail cocotb, not only increment counters or log text.")
        return False

    if _grep_eq(
        rf"tb_{re.escape(ctx.ip)}\.sv|tc_{re.escape(ctx.ip)}\.sv|tb/.*\.sv|tc/.*\.sv", makefile_path
    ):
        print(f"[check_tb_disk] FAIL: {makefile_path.as_posix()} references legacy SV TB while cocotb layout is present")
        return False

    print(f"[check_tb_disk] PASS: sim/ cocotb test={test_sz}B makefile={makefile_sz}B")
    return True


def main(argv: list[str]) -> int:
    ip = os.environ.get("IP_NAME") or (argv[0] if argv else "")
    if not ip:
        ip = _auto_detect_ip()

    if not ip or not Path(ip).is_dir():
        print(f"[check_tb_disk] FAIL: cannot locate IP directory (IP={ip or 'unset'})")
        return 1

    ctx = Ctx(ip)

    tc = Path(ip) / "tc" / f"tc_{ip}.sv"
    tb = Path(ip) / "tb" / f"tb_{ip}.sv"
    list_path = Path(ip) / "list" / f"{ip}.f"
    cocotb_test = Path(ip) / "tb" / "cocotb" / f"test_{ip}.py"
    cocotb_runner = Path(ip) / "tb" / "cocotb" / "test_runner.py"
    cocotb_run_tests = Path(ip) / "tb" / "cocotb" / "run_tests.py"
    flat_cocotb_test = Path(ip) / "tb" / f"test_{ip}.py"
    flat_cocotb_runner = Path(ip) / "tb" / "test_runner.py"
    flat_cocotb_run_tests = Path(ip) / "tb" / "run_tests.py"
    uvm_dir = Path(ip) / "tb" / "uvm"

    if cocotb_test.is_file() or cocotb_runner.is_file() or cocotb_run_tests.is_file():
        if not cocotb_runner.is_file() and cocotb_run_tests.is_file():
            cocotb_runner = cocotb_run_tests
        if _check_cocotb_layout(ctx, cocotb_test, cocotb_runner, "tb/cocotb"):
            return 0
        print("[check_tb_disk] Disk reality contradicts claimed cocotb completion. Run write_file/run_command for real.")
        return 1

    if flat_cocotb_test.is_file() or flat_cocotb_runner.is_file() or flat_cocotb_run_tests.is_file():
        if not flat_cocotb_runner.is_file() and flat_cocotb_run_tests.is_file():
            flat_cocotb_runner = flat_cocotb_run_tests
        if _check_cocotb_layout(ctx, flat_cocotb_test, flat_cocotb_runner, "tb"):
            return 0
        print("[check_tb_disk] Disk reality contradicts claimed cocotb completion. Run write_file/run_command for real.")
        return 1

    if uvm_dir.is_dir():
        if _check_uvm_layout(ctx, uvm_dir):
            return 0
        print("[check_tb_disk] Disk reality contradicts claimed UVM completion. Run write_file/run_command for real.")
        return 1

    # Layout: sim/ Makefile-based cocotb.
    sim_cocotb_test = Path(ip) / "sim" / f"test_{ip}.py"
    sim_makefile = Path(ip) / "sim" / "Makefile"

    if sim_cocotb_test.is_file() and sim_makefile.is_file():
        if _check_sim_cocotb_layout(ctx, sim_cocotb_test, sim_makefile):
            return 0
        print("[check_tb_disk] Disk reality contradicts claimed cocotb completion. Run write_file/run_command for real.")
        return 1

    tc_sz = _size(tc)
    tb_sz = _size(tb)
    f_sz = _size(list_path)

    fail = 0
    if tc_sz < ctx.MIN_TC:
        print(f"[check_tb_disk] FAIL: {tc.as_posix()} = {tc_sz}B (need ≥{ctx.MIN_TC})")
        fail = 1
    if tb_sz < ctx.MIN_TB:
        print(f"[check_tb_disk] FAIL: {tb.as_posix()} = {tb_sz}B (need ≥{ctx.MIN_TB})")
        fail = 1
    if f_sz < ctx.MIN_F:
        print(f"[check_tb_disk] FAIL: {list_path.as_posix()} = {f_sz}B (need ≥{ctx.MIN_F})")
        fail = 1

    # Filelist must reference both tb and tc.
    if f_sz >= ctx.MIN_F:
        if not _grep_q_fixed(f"tb_{ip}", list_path):
            print(f"[check_tb_disk] FAIL: {list_path.as_posix()} does not reference tb_{ip}")
            fail = 1

    if fail != 0:
        print("[check_tb_disk] Disk reality contradicts claimed completion. Run write_file/run_command for real.")
        return 1

    print(f"[check_tb_disk] PASS: tc={tc_sz}B tb={tb_sz}B list={f_sz}B")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
