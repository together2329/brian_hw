#!/usr/bin/env python3
"""sim.py — Compile and run simulation for tb_gen workspace.

Faithful Python port of sim.sh.  This is a heavy runner that drives cocotb
(Python) or SystemVerilog (iverilog/verilator) simulation, parses errors /
warnings / pass-fail counts, appends a benchmark log line, and (on a passing
cocotb run with a contract_reflection.json present) writes a sim-stage run
marker and stamps sim-evidence freshness.

Inputs (env vars, matching the .sh):
  HOOK_CMD_ARGS / argv[1] — testbench path (.py runner or tb_*.sv/.v).
  BENCHMARK_LOG           — benchmark log file (default ".benchmark").
  SIM_TIMEOUT_SEC         — per-run timeout in seconds (default 120).
  ATLAS_SIM_ALLOW_ERROR_MASK — "1" opts into legacy permissive error masking.

RISK / FLAGGED NOTES (see final report): this 1:1 port reproduces the original's
ordering, env handling, timeout fallback chain (timeout -> gtimeout -> python),
and verdict text.  Behavioral edge cases inherited verbatim from the .sh:
  * iverilog branch uses a fixed /tmp/_tb_sim.vvp output path.
  * find-based TB auto-detection relies on shell glob precedence (-o operators).
  * the final "0 errors, 0 warnings" line + exit status mirror the .sh exactly.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


def _now_ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


def _run_bounded(seconds: int, cmd: "list[str]", cwd: "str | None" = None,
                 env: "dict[str, str] | None" = None) -> "tuple[int, str]":
    """Run cmd with a wall-clock bound, capturing stdout+stderr combined.

    Mirrors the run_bounded() helper: prefer `timeout`, then `gtimeout`, then a
    pure-Python subprocess timeout that exits 124 on expiry.
    """
    timeout_bin = shutil.which("timeout") or shutil.which("gtimeout")
    if timeout_bin is not None:
        full = [timeout_bin, str(seconds), *cmd]
        proc = subprocess.run(
            full, cwd=cwd, env=env, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        return proc.returncode, proc.stdout or ""
    try:
        proc = subprocess.run(
            cmd, cwd=cwd, env=env, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=seconds,
        )
        return proc.returncode, proc.stdout or ""
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or ""
        if isinstance(out, bytes):
            out = out.decode(errors="replace")
        out += f"TIMEOUT: command exceeded {seconds}s: {' '.join(cmd)}\n"
        return 124, out


def _count_errors(out: str) -> int:
    count = 0
    for raw in out.splitlines():
        line = raw.strip()
        low = line.lower()
        if not line:
            continue
        if re.search(r"\b0\s+errors?\b|\berrors?\s*[:=]\s*0\b|\bno\s+errors?\b", low):
            continue
        if re.search(r"\b(error|fatal|traceback|assertionerror)\b", low):
            count += 1
    return count


def _count_warnings(out: str, py_flow: bool) -> int:
    count = 0
    for raw in out.splitlines():
        line = raw.strip()
        low = line.lower()
        if not line:
            continue
        if py_flow and ("userwarning: python runners" in low or "experimental feature" in low):
            continue
        if re.search(r"\b0\s+warnings?\b|\bwarnings?\s*[:=]\s*0\b|\bno\s+warnings?\b", low):
            continue
        if re.search(r"\b(warning|warn)\b", low):
            count += 1
    return count


def _grep_count(out: str, pattern: str) -> int:
    rx = re.compile(pattern)
    return sum(1 for line in out.splitlines() if rx.search(line))


def _find_tb() -> str:
    # [ -z TB ] && TB=$(find . -maxdepth 4 -path "*/tb/cocotb/test_runner.py"
    #                   -o -path "*/tb/test_runner.py" | head -1)
    for path in sorted(Path(".").glob("*/tb/cocotb/test_runner.py")):
        return str(path)
    for path in sorted(Path(".").glob("*/tb/test_runner.py")):
        return str(path)
    # find . -maxdepth 2 -name "tb_*.sv" -o -name "tb_*.v" | head -1
    sv_candidates = []
    for path in Path(".").glob("*/tb_*.sv"):
        sv_candidates.append(str(path))
    for path in Path(".").glob("tb_*.sv"):
        sv_candidates.append(str(path))
    for path in Path(".").glob("*/tb_*.v"):
        sv_candidates.append(str(path))
    for path in Path(".").glob("tb_*.v"):
        sv_candidates.append(str(path))
    if sv_candidates:
        return sorted(sv_candidates)[0]
    return ""


def _write_run_marker(out_path: Path, runner: str, pass_cnt: int, fail_cnt: int) -> None:
    import json

    payload = {
        "fail": int(fail_cnt),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pass": int(pass_cnt),
        "runner": runner,
        "schema_version": 1,
        "source": "sim_stage",
        "status": "pass",
        "type": "sim_stage_run",
    }
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    tb = os.environ.get("HOOK_CMD_ARGS") or (sys.argv[1] if len(sys.argv) > 1 else "")
    log = os.environ.get("BENCHMARK_LOG", ".benchmark")
    ts = _now_ts()
    sim_timeout = int(os.environ.get("SIM_TIMEOUT_SEC", "120"))

    if not tb:
        tb = _find_tb()
    if not tb:
        print("No testbench found. Use /sim <test_runner.py|tb_<module>.sv>")
        return 1

    out = ""
    py_flow = False
    ip_dir = ""

    if tb.endswith(".py"):
        py_flow = True
        print(f"Running cocotb Python runner: {tb}")
        tb_dir = str(Path(tb).resolve().parent)
        ip_dir = str(Path(tb_dir).parent)
        if Path(ip_dir).name == "tb":
            ip_dir = str(Path(ip_dir).parent)
        env = dict(os.environ)
        pythonpath = f"{tb_dir}:{ip_dir}:" + os.environ.get("PYTHONPATH", "")
        env["PYTHONPATH"] = pythonpath
        tb_text = Path(tb).read_text(encoding="utf-8", errors="replace")
        if "if __name__" in tb_text:
            rc, out = _run_bounded(
                sim_timeout, ["python3", Path(tb).name], cwd=tb_dir, env=env
            )
        else:
            rc, out = _run_bounded(
                sim_timeout,
                ["python3", "-m", "pytest", "-q", tb, "--tb=short"],
                env=env,
            )
        out = out.rstrip("\n")  # OUT=$(...) strips trailing newlines in bash
        print(out)
        if rc != 0:
            print("Simulation FAILED")
            with open(log, "a", encoding="utf-8") as fh:
                fh.write(f"{ts} sim=FAIL stage=cocotb rc={rc}\n")
            return rc
    elif shutil.which("iverilog") is not None:
        print(f"Compiling: {tb}")
        comp = subprocess.run(
            ["iverilog", "-g2012", "-Wall", "-o", "/tmp/_tb_sim.vvp", tb],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        print(comp.stdout or "", end="")
        if comp.returncode != 0:
            print("Compile FAILED")
            with open(log, "a", encoding="utf-8") as fh:
                fh.write(f"{ts} sim=FAIL stage=compile\n")
            return 1
        _rc, out = _run_bounded(sim_timeout, ["vvp", "/tmp/_tb_sim.vvp"])
        out = out.rstrip("\n")  # OUT=$(...) strips trailing newlines in bash
        print(out)
    elif shutil.which("verilator") is not None:
        print(f"Compiling: {tb}")
        build = subprocess.run(
            ["verilator", "--binary", "--build", "-j", "0", tb, "-o", "/tmp/_tb_verilator"],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        out = build.stdout or ""
        if build.returncode == 0:
            runp = subprocess.run(
                ["/tmp/_tb_verilator"], text=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            )
            out += runp.stdout or ""
        out = out.rstrip("\n")  # OUT=$(...) strips trailing newlines in bash
        print(out)
    else:
        print("No sim tool found.")
        return 1

    errors = _count_errors(out)
    warnings = _count_warnings(out, py_flow)
    pass_cnt = _grep_count(out, r"\[PASS\]| passed| PASS=")
    fail_cnt = _grep_count(out, r"\[FAIL\]| failed| FAIL=[1-9]")

    summary_matches = re.findall(r"TESTS=[0-9]+ PASS=[0-9]+ FAIL=[0-9]+", out)
    if summary_matches:
        summary = summary_matches[-1]
        pass_cnt = int(re.search(r"PASS=([0-9]+)", summary).group(1))
        fail_cnt = int(re.search(r"FAIL=([0-9]+)", summary).group(1))

    allow_error_mask = os.environ.get("ATLAS_SIM_ALLOW_ERROR_MASK", "0")
    if py_flow and fail_cnt == 0 and allow_error_mask == "1":
        errors = 0

    print("")
    print(f"Simulation: {errors} errors, {warnings} warnings")
    print(f"Tests: {pass_cnt} passed, {fail_cnt} failed")

    status = "FAIL"
    if errors == 0 and fail_cnt == 0:
        status = "PASS"

    with open(log, "a", encoding="utf-8") as fh:
        fh.write(
            f"{ts} sim={status} errors={errors} warnings={warnings} "
            f"pass={pass_cnt} fail={fail_cnt} tb={tb}\n"
        )

    if (
        status == "PASS"
        and py_flow
        and ip_dir
        and (Path(ip_dir) / "verify" / "contract_reflection.json").is_file()
    ):
        run_marker = Path(ip_dir) / "sim" / "sim_stage_run.json"
        run_marker.parent.mkdir(parents=True, exist_ok=True)
        _write_run_marker(run_marker, tb, pass_cnt, fail_cnt)

        # Search upward for stamp_sim_evidence_freshness.py.
        script_dir = Path(__file__).resolve().parent
        search_root = script_dir
        stamp_script = ""
        while str(search_root) != "/":
            candidate = (
                search_root
                / "workflow"
                / "contract-reflection"
                / "scripts"
                / "stamp_sim_evidence_freshness.py"
            )
            if candidate.is_file():
                stamp_script = str(candidate)
                break
            search_root = search_root.parent
        if not stamp_script:
            print("[sim_freshness] fail: stamp script not found")
            return 1
        stamp_env = dict(os.environ)
        stamp_env["ATLAS_SIM_FRESHNESS_SOURCE"] = "sim_stage"
        stamp = subprocess.run(
            [
                "python3",
                stamp_script,
                Path(ip_dir).name,
                "--root",
                str(Path(ip_dir).parent),
            ],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=stamp_env,
        )
        # STAMP_OUT=$(...) strips trailing newlines; echo re-adds one.
        print((stamp.stdout or "").rstrip("\n"))
        if stamp.returncode != 0:
            return stamp.returncode

    if status == "PASS":
        print("0 errors, 0 warnings")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
