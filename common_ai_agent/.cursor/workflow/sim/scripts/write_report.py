#!/usr/bin/env python3
"""write_report.py — Python port of write_report.sh (sim).

Render ``sim_report.txt`` from the benchmark log's most recent simulation run.

CLI / env contract preserved:
  * LOG = ``$BENCHMARK_LOG`` (default ``.benchmark``); OUT = ``sim_report.txt``.
  * LAST = last log line containing ``sim=`` but not ``stage=compile``.
  * Field extraction uses the same ``grep -oP 'k=\\K...'`` commands as the
    ``.sh`` (with the same ``|| echo "?"`` / ``UNKNOWN`` defaults).  ``\\K`` is
    a GNU-PCRE feature absent from BSD grep, so the extractions are shelled out
    verbatim to match the ``.sh`` on whatever host runs it.
  * ITERS = ``grep -c "sim_capture="``; TOOL = ``iverilog+vvp`` if ``iverilog``
    is on PATH else ``verilator``.
  * Write the report (including the masked ``[FAIL details]`` grep pipeline),
    print ``Written: <out>`` and the report body.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time


def _sh(cmd: str, log: str) -> str:
    proc = subprocess.run(
        ["/bin/sh", "-c", cmd],
        capture_output=True,
        text=True,
        env={**os.environ, "LOG": log},
    )
    return proc.stdout


def main(argv: "list[str] | None" = None) -> int:
    log = os.environ.get("BENCHMARK_LOG", ".benchmark")
    out_path = "sim_report.txt"
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")

    # LAST=$(grep "sim=" "${LOG}" | grep -v "stage=compile" | tail -1)
    last = _sh('grep "sim=" "$LOG" 2>/dev/null | grep -v "stage=compile" | tail -1', log)
    last = last.rstrip("\n")

    def _field(cmd: str) -> str:
        # Run with LAST exported so the extraction greps the same text.
        proc = subprocess.run(
            ["/bin/sh", "-c", cmd],
            capture_output=True,
            text=True,
            env={**os.environ, "LAST": last, "LOG": log},
        )
        return proc.stdout.rstrip("\n")

    status = _field(r'echo "$LAST" | grep -oP "sim=\K\w+" || echo "UNKNOWN"')
    errors = _field(r'echo "$LAST" | grep -oP "errors=\K\d+" || echo "?"')
    warnings = _field(r'echo "$LAST" | grep -oP "warnings=\K\d+" || echo "?"')
    passes = _field(r'echo "$LAST" | grep -oP "pass=\K\d+" || echo "?"')
    fails = _field(r'echo "$LAST" | grep -oP "fail=\K\d+" || echo "?"')
    tb = _field(r'echo "$LAST" | grep -oP "tb=\K\S+" || echo "?"')

    # ITERS=$(grep -c "sim_capture=" "${LOG}" 2>/dev/null || echo "?")
    iters = _field('grep -c "sim_capture=" "$LOG" 2>/dev/null || echo "?"')

    tool = "iverilog+vvp" if shutil.which("iverilog") is not None else "verilator"

    # [FAIL details] uses a masked pipeline: grep ... | tail -20 || echo "NONE".
    fail_details = _sh(
        r'grep -E "\[FAIL\]|FAILED|failed|ERROR" "$LOG" 2>/dev/null | tail -20 '
        r'|| echo "NONE"',
        log,
    )
    fail_details = fail_details.rstrip("\n")

    body = (
        "=== Simulation Report ===\n"
        f"Date      : {ts}\n"
        f"TB        : {tb}\n"
        f"Tool      : {tool}\n"
        f"Result    : {status}\n"
        f"Errors    : {errors}\n"
        f"Warnings  : {warnings}\n"
        f"Tests     : {passes} passed, {fails} failed\n"
        f"Iterations: {iters}\n"
        "\n"
        "[FAIL details]\n"
        f"{fail_details}\n"
    )

    with open(out_path, "w", encoding="utf-8") as handle:
        handle.write(body)

    print(f"Written: {out_path}")
    sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
