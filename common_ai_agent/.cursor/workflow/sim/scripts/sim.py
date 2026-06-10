#!/usr/bin/env python3
"""sim.py — Python port of sim.sh (sim).

Compile and run a simulation, parse a simple errors/warnings/pass/fail summary,
append a benchmark log line, and exit PASS/FAIL.

CLI / env contract preserved (bash ``set -u``):
  * TB = ``$HOOK_CMD_ARGS`` else first positional argument; if empty, the
    default search is:
      - ``find . -maxdepth 4 -path '*/tb/cocotb/test_runner.py' -o -path
        '*/tb/test_runner.py' | head -1``, then
      - ``find . -maxdepth 3 -name 'tb_*.sv' -o -name 'tb_*.v' | head -1``.
    Empty ⇒ guidance and exit 1.
  * ``.py`` TB ⇒ cocotb Python flow (run the runner directly when it has an
    ``if __name__`` guard, else ``pytest -q``); non-zero rc ⇒ FAIL + log + exit.
  * Else iverilog compile+vvp (``/tmp/_sim.vvp``); else verilator ``--binary``;
    else "No simulator found." exit 1.
  * Counts via the original grep idioms; for the cocotb flow the warning count
    excludes the two known cocotb runner notices.  A ``TESTS=.. PASS=.. FAIL=..``
    summary (last) overrides pass/fail.  STATUS = PASS iff errors==0 && fail==0.
    On PASS print "0 errors, 0 warnings" and exit 0.

Faithful port note: the error/warning grep idiom is ``grep -c -i "^.*error"``
which, like the ``.sh``, counts any line containing the substring
(case-insensitive).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


_ERROR_RE = re.compile(r"error", re.IGNORECASE)
_WARNING_RE = re.compile(r"warning", re.IGNORECASE)
_PASS_RE = re.compile(r"\[PASS\]| passed| PASS=")
_FAIL_RE = re.compile(r"\[FAIL\]| failed| FAIL=[1-9]")
_SUMMARY_RE = re.compile(r"TESTS=[0-9]+ PASS=[0-9]+ FAIL=[0-9]+")


def _count_lines(pattern: "re.Pattern[str]", text: str) -> int:
    if not text:
        return 0
    return sum(1 for line in text.splitlines() if pattern.search(line))


def _find_tb() -> str:
    # find . -maxdepth 4 -path "*/tb/cocotb/test_runner.py"
    #                    -o -path "*/tb/test_runner.py" | head -1
    runner = subprocess.run(
        ["/bin/sh", "-c",
         'find . -maxdepth 4 -path "*/tb/cocotb/test_runner.py" '
         '-o -path "*/tb/test_runner.py" | head -1'],
        capture_output=True, text=True,
    ).stdout.strip()
    if runner:
        return runner
    # find . -maxdepth 3 -name "tb_*.sv" -o -name "tb_*.v" | head -1
    return subprocess.run(
        ["/bin/sh", "-c",
         'find . -maxdepth 3 -name "tb_*.sv" -o -name "tb_*.v" | head -1'],
        capture_output=True, text=True,
    ).stdout.strip()


def main(argv: "list[str] | None" = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    tb = os.environ.get("HOOK_CMD_ARGS") or (argv[0] if argv else "")
    log = os.environ.get("BENCHMARK_LOG", ".benchmark")
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")

    if not tb:
        tb = _find_tb()
    if not tb:
        print("No testbench found. Use /sim <test_runner.py|tb_<module>.sv>")
        return 1

    out = ""
    py_flow = False

    if tb.endswith(".py"):
        py_flow = True
        print(f"Running cocotb Python runner: {tb}")
        tb_dir = str(Path(tb).resolve().parent)
        ip_dir = str(Path(tb_dir).parent)
        if Path(ip_dir).name == "tb":
            ip_dir = str(Path(ip_dir).parent)

        env = dict(os.environ)
        env["PYTHONPATH"] = f"{tb_dir}:{ip_dir}:" + os.environ.get("PYTHONPATH", "")

        tb_text = Path(tb).read_text(encoding="utf-8", errors="replace")
        if "if __name__" in tb_text:
            proc = subprocess.run(
                ["python3", Path(tb).name],
                cwd=tb_dir, env=env, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            )
        else:
            proc = subprocess.run(
                ["python3", "-m", "pytest", "-q", tb, "--tb=short"],
                env=env, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            )
        rc = proc.returncode
        out = (proc.stdout or "").rstrip("\n")
        print(out)
        if rc != 0:
            print("Simulation FAILED")
            with open(log, "a", encoding="utf-8") as handle:
                handle.write(f"{ts} sim=FAIL stage=cocotb rc={rc}\n")
            return rc
    elif shutil.which("iverilog") is not None:
        print(f"Compiling: {tb}")
        comp = subprocess.run(
            ["iverilog", "-g2012", "-Wall", "-o", "/tmp/_sim.vvp", tb],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        sys.stdout.write(comp.stdout or "")
        if comp.returncode != 0:
            print("Compile FAILED")
            with open(log, "a", encoding="utf-8") as handle:
                handle.write(f"{ts} sim=FAIL stage=compile\n")
            return 1
        print("Running...")
        runp = subprocess.run(
            ["vvp", "/tmp/_sim.vvp"], text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        out = (runp.stdout or "").rstrip("\n")
        print(out)
    elif shutil.which("verilator") is not None:
        print(f"Compiling: {tb}")
        build = subprocess.run(
            ["/bin/sh", "-c",
             f'verilator --binary --build -j 0 "{tb}" -o /tmp/_vsim 2>&1 '
             f'&& /tmp/_vsim 2>&1'],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        out = (build.stdout or "").rstrip("\n")
        print(out)
    else:
        print("No simulator found.")
        return 1

    errors = _count_lines(_ERROR_RE, out)
    warnings = _count_lines(_WARNING_RE, out)
    passes = _count_lines(_PASS_RE, out)
    fails = _count_lines(_FAIL_RE, out)

    if py_flow:
        # grep -i "warning" | grep -vi "UserWarning: Python runners"
        #   | grep -vi "experimental feature" | wc -l
        warnings = sum(
            1
            for line in out.splitlines()
            if _WARNING_RE.search(line)
            and "userwarning: python runners" not in line.lower()
            and "experimental feature" not in line.lower()
        )

    summary_matches = _SUMMARY_RE.findall(out)
    if summary_matches:
        summary = summary_matches[-1]
        passes = summary.split("PASS=", 1)[1].split(" ", 1)[0]
        fails = summary.split("FAIL=", 1)[1].split(" ", 1)[0]

    # STATUS="FAIL"; [ "${ERRORS}" -eq 0 ] && [ "${FAIL}" -eq 0 ] && STATUS="PASS"
    status = "FAIL"
    if errors == 0 and int(fails) == 0:
        status = "PASS"

    print()
    print(
        f"Result: {errors} errors, {warnings} warnings | "
        f"{passes} PASS, {fails} FAIL"
    )
    with open(log, "a", encoding="utf-8") as handle:
        handle.write(
            f"{ts} sim={status} errors={errors} warnings={warnings} "
            f"pass={passes} fail={fails} tb={tb}\n"
        )

    if status == "PASS":
        print("0 errors, 0 warnings")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
