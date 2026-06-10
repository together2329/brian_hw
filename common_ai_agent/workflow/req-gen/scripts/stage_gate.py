#!/usr/bin/env python3
# =============================================================================
# stage_gate.py <stage> <ip> --root <root>   (Python port of stage_gate.sh)
# -----------------------------------------------------------------------------
# Deterministic VCM gate for the tb / sim / lint stages, with a detect-and-skip
# policy: pure python/bash checks are HARD; checks that need an external tool
# (iverilog / verilator / cocotb / pyslang) run only when that tool is present,
# otherwise they SKIP with a warning. EXCEPTION: the `sim` stage BLOCKS (exit 2)
# when no simulator is installed — running the simulator is the whole point of
# the stage, so a missing simulator must not silently pass.
#
# Stage scopes (closure_stage aware): tb/lint check stage-local deliverables;
# full obligation closure (check_evidence_contract.py) runs at the sim stage,
# where runtime evidence exists.
#
# Exit: 0 = all hard checks passed (skips allowed) ; 1 = a hard check failed
#       2 = blocked (sim stage, no simulator)
# =============================================================================
"""Python port of stage_gate.sh — same CLI, exit codes, and stdout/stderr.

bash `set -uo pipefail` (no -e): hard checks accumulate `status` rather than
aborting; replicated with explicit return-code accumulation. Sub-checks are
invoked via sys.executable / bash exactly as the shell did, inheriting cwd=ROOT.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def _line_buffer_stdout() -> None:
    # bash line-buffers stdout; Python block-buffers it when not a TTY, which
    # reorders lines under a merged `2>&1`. Line buffering keeps the gate
    # progress lines and any child output interleaved as the shell does.
    try:
        sys.stdout.reconfigure(line_buffering=True)  # type: ignore[attr-defined]
    except (AttributeError, ValueError):  # pragma: no cover - non-TextIO stdout
        pass


def have_tool(name: str) -> bool:
    """command -v "$1" >/dev/null 2>&1"""
    return shutil.which(name) is not None


def have_py(module: str) -> bool:
    """python3 -c "import $1" >/dev/null 2>&1"""
    return (
        subprocess.run(
            [sys.executable, "-c", f"import {module}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0
    )


def main(argv: list[str]) -> int:
    _line_buffer_stdout()
    # STAGE="${1:-}"; shift || true
    stage = argv[0] if argv else ""
    rest = argv[1:]

    ip = ""
    root = "."
    i = 0
    while i < len(rest):
        arg = rest[i]
        if arg == "--root":
            # ROOT="$2"; shift 2
            root = rest[i + 1] if i + 1 < len(rest) else ""
            i += 2
        elif arg.startswith("--root="):
            root = arg[len("--root="):]
            i += 1
        elif arg.startswith("-"):
            print(f"[stage_gate] unknown flag: {arg}", file=sys.stderr)
            return 2
        else:
            if not ip:
                ip = arg
            i += 1

    if not stage or not ip:
        print("usage: stage_gate.sh <tb|sim|lint> <ip> --root <root>", file=sys.stderr)
        return 2

    # SCRIPTS_DIR / WF (workflow/, script lives in workflow/req-gen/scripts)
    scripts_dir = Path(__file__).resolve().parent
    wf = (scripts_dir / ".." / "..").resolve()

    # ROOT="$(cd "$ROOT" 2>/dev/null && pwd || echo "$ROOT")"
    # os.path.abspath mirrors bash's *logical* pwd (symlinks like /tmp kept);
    # on a missing dir we keep the literal value, exactly as the `|| echo` does.
    if Path(root).is_dir():
        root_resolved = os.path.abspath(root)
    else:
        root_resolved = root
    # cd "$ROOT" || { echo "[stage_gate] cannot cd to root: $ROOT" >&2; exit 2; }
    try:
        os.chdir(root_resolved)
    except OSError:
        print(f"[stage_gate] cannot cd to root: {root_resolved}", file=sys.stderr)
        return 2

    status = 0

    def run_hard(name: str, *cmd: str) -> None:
        nonlocal status
        print(f"▸ {name}")
        proc = subprocess.run(list(cmd))
        if proc.returncode == 0:
            print(f"  ✓ {name}")
        else:
            print(f"  ✗ {name} failed (rc={proc.returncode})")
            status = 1

    def run_skip(cond: bool, name: str, *cmd: str) -> None:
        if cond:
            run_hard(name, *cmd)
        else:
            print(f"  [skip] {name}: required tooling absent")

    if stage == "tb":
        run_hard(
            "tb_python_compile",
            sys.executable,
            str(wf / "tb-gen" / "scripts" / "check_tb_python_compile.py"),
            ip,
            "--root",
            ".",
        )
        run_hard(
            "scoreboard_source",
            sys.executable,
            str(wf / "tb-gen" / "scripts" / "check_scoreboard_events.py"),
            ip,
            "--root",
            ".",
            "--source-check",
        )
        run_hard(
            "scoreboard_self_check",
            sys.executable,
            str(wf / "tb-gen" / "runtime" / "equivalence_scoreboard.py"),
            ip,
            "--root",
            ".",
            "--self-check",
        )
        run_skip(
            have_py("cocotb"),
            "pyuvm_structure",
            "bash",
            str(wf / "tb-gen" / "scripts" / "check_pyuvm_structure.sh"),
            ip,
        )
    elif stage == "lint":
        run_skip(
            have_tool("verilator") or have_py("pyslang"),
            "dut_lint",
            sys.executable,
            str(wf / "lint" / "scripts" / "dut_lint_report.py"),
            ip,
            "--root",
            ".",
        )
    elif stage == "sim":
        if not have_tool("iverilog") and not have_tool("verilator"):
            print("  \U0001f6d1 sim BLOCKED: no simulator (iverilog/verilator) installed")
            return 2
        run_hard("sim_run", "bash", str(wf / "tb-gen" / "scripts" / "sim.sh"), ip)
        run_hard(
            "sim_evidence",
            "bash",
            str(wf / "tb-gen" / "scripts" / "check_tb_sim_evidence.sh"),
            ip,
        )
        run_hard(
            "evidence_contract_closure",
            sys.executable,
            str(wf / "contract-reflection" / "scripts" / "check_evidence_contract.py"),
            ip,
            "--root",
            ".",
            "--require-nonempty",
        )
    else:
        print(f"[stage_gate] unknown stage: {stage}", file=sys.stderr)
        return 2

    if status == 0:
        print(f"▣ stage_gate({stage}) PASS")
    else:
        print(f"▣ stage_gate({stage}) FAILED")
    return status


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
