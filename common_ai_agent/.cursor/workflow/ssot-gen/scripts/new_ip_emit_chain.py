#!/usr/bin/env python3
# new_ip_emit_chain.sh — after /to-ssot has produced <ip>/yaml/<ip>.ssot.yaml,
# run the proven emit chain: FL model -> equivalence goals ->
# IP evidence contract -> cocotb scoreboard -> pre-sim TB Python compile ->
# simulation.
#
# Usage:
#   bash "$ATLAS_WORKFLOW_ROOT/ssot-gen/scripts/new_ip_emit_chain.sh" <ip> [--root <ip-parent>] [--workflow-root <workflow-dir>] [--ip-root <ip-dir>]
#
# --workflow-root points at common_ai_agent/workflow.
# --root/ATLAS_PROJECT_ROOT points at the parent directory containing <ip>.
# --ip-root/ATLAS_IP_ROOT can pin the active IP directory directly.
#
# Prereqs (under --root):
#   - <ip>/yaml/<ip>.ssot.yaml
#   - <ip>/rtl/<ip>.sv
#   - <ip>/rtl/rtl_contract.json
#   - <ip>/list/<ip>.f  (auto-generated from <ip>/rtl/*.sv if missing)
#
# Exit:
#   0 = cocotb TESTS=1 PASS=1 FAIL=0  AND  CL co-sim N/N 100% match
#   non-zero = some emit step or cocotb failed; stderr carries the cause.
#
# Python port of new_ip_emit_chain.sh — same CLI, exit codes, step order, and
# messages. bash `set -u` only (no -e/-pipefail); the `step` helper does the
# explicit rc check + stop-on-first-failure (exit 1). --help replicates
# `sed -n '2,21p' "$0"` by emitting THIS file's lines 2-21 (byte-identical to
# the shell header, which is reproduced verbatim above).

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _line_buffer_stdout() -> None:
    # bash line-buffers stdout; Python block-buffers it when not a TTY, which
    # reorders lines under a merged `2>&1`. Reconfigure to line buffering so
    # stdout/stderr interleave exactly as the shell original does.
    try:
        sys.stdout.reconfigure(line_buffering=True)  # type: ignore[attr-defined]
    except (AttributeError, ValueError):  # pragma: no cover - non-TextIO stdout
        pass


def _print_help() -> None:
    # sed -n '2,21p' "$0" — print lines 2..21 of this very file.
    lines = Path(__file__).read_text(encoding="utf-8").splitlines(keepends=True)
    # splitlines is 0-indexed; lines 2..21 inclusive == indices 1..20.
    sys.stdout.write("".join(lines[1:21]))


def main(argv: list[str]) -> int:
    _line_buffer_stdout()
    ip = ""
    # ROOT="${ATLAS_PROJECT_ROOT:-${ATLAS_ROOT:-}}"
    root = os.environ.get("ATLAS_PROJECT_ROOT") or os.environ.get("ATLAS_ROOT") or ""
    workflow_root = os.environ.get("ATLAS_WORKFLOW_ROOT") or ""
    ip_root = os.environ.get("ATLAS_IP_ROOT") or ""

    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--root":
            root = argv[i + 1] if i + 1 < len(argv) else ""
            i += 2
        elif arg.startswith("--root="):
            root = arg[len("--root="):]
            i += 1
        elif arg in ("--workflow-root", "--workflow_root"):
            workflow_root = argv[i + 1] if i + 1 < len(argv) else ""
            i += 2
        elif arg.startswith("--workflow-root=") or arg.startswith("--workflow_root="):
            workflow_root = arg.split("=", 1)[1]
            i += 1
        elif arg in ("--ip-root", "--ip_root"):
            ip_root = argv[i + 1] if i + 1 < len(argv) else ""
            i += 2
        elif arg.startswith("--ip-root=") or arg.startswith("--ip_root="):
            ip_root = arg.split("=", 1)[1]
            i += 1
        elif arg in ("--help", "-h"):
            _print_help()
            return 0
        else:
            if not ip:
                ip = arg
            i += 1

    if ip_root:
        # [ -d "$IP_ROOT" ] || { echo ...; exit 1; }
        if not Path(ip_root).is_dir():
            print(f"[emit-chain] FAIL: --ip-root {ip_root} does not exist", file=sys.stderr)
            return 1
        # cd "$IP_ROOT" && pwd — logical pwd (no symlink resolution).
        ip_root = os.path.abspath(ip_root)
        if not ip:
            ip = os.path.basename(ip_root)
        if not root:
            root = os.path.dirname(ip_root)

    if not ip:
        print(
            f"[emit-chain] usage: {sys.argv[0]} <ip_name> [--root <ip-parent>] "
            "[--workflow-root <workflow-dir>] [--ip-root <ip-dir>]",
            file=sys.stderr,
        )
        return 2

    if not root:
        root = os.getcwd()
    if not Path(root).is_dir():
        print(f"[emit-chain] FAIL: --root {root} does not exist", file=sys.stderr)
        return 1
    # ROOT="$(cd "$ROOT" && pwd)" — logical pwd (no symlink resolution).
    root = os.path.abspath(root)

    if not workflow_root:
        # WORKFLOW_ROOT="$(cd "$(dirname "$0")/../.." && pwd)" — logical pwd.
        workflow_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    if Path(f"{workflow_root}/workflow/ssot-gen").is_dir():
        workflow_root = os.path.abspath(f"{workflow_root}/workflow")
    elif Path(f"{workflow_root}/ssot-gen").is_dir():
        workflow_root = os.path.abspath(workflow_root)
    else:
        print(
            f"[emit-chain] FAIL: --workflow-root {workflow_root} does not contain ssot-gen/",
            file=sys.stderr,
        )
        return 1

    print(f"[emit-chain] resolved PROJECT_ROOT = {root}")
    print(f"[emit-chain] resolved WORKFLOW_ROOT = {workflow_root}")

    ssot = f"{root}/{ip}/yaml/{ip}.ssot.yaml"
    if not Path(ssot).is_file():
        print(f"[emit-chain] FAIL: {ssot} missing — run /to-ssot first", file=sys.stderr)
        return 1

    # Auto-generate filelist if missing (P3). Sourced from <ip>/rtl/*.sv .
    filelist = f"{root}/{ip}/list/{ip}.f"
    if not Path(filelist).is_file():
        rtl_dir = f"{root}/{ip}/rtl"
        if not Path(rtl_dir).is_dir():
            print(
                f"[emit-chain] FAIL: {rtl_dir} missing — cannot synthesize filelist",
                file=sys.stderr,
            )
            return 1
        Path(f"{root}/{ip}/list").mkdir(parents=True, exist_ok=True)
        body_lines = [
            "// Auto-generated by new_ip_emit_chain.sh — DUT-only filelist",
            "+incdir+rtl",
        ]
        # for sv in "${RTL_DIR}"/*.sv  — shell glob order is sorted (LC_COLLATE);
        # `[ -f "$sv" ] || continue` skips non-files (and the literal-glob case
        # when no match exists). sorted(glob) mirrors the default shell ordering.
        for sv in sorted(Path(rtl_dir).glob("*.sv")):
            if sv.is_file():
                body_lines.append(f"rtl/{sv.name}")
        Path(filelist).write_text("\n".join(body_lines) + "\n", encoding="utf-8")
        # echo "[emit-chain] auto-generated ... ($(wc -l < "$FILELIST" | tr -d ' ') lines)"
        nlines = Path(filelist).read_text(encoding="utf-8").count("\n")
        print(f"[emit-chain] auto-generated {ip}/list/{ip}.f ({nlines} lines)")

    def step(label: str, *cmd: str) -> None:
        print(f"[emit-chain] {label}")
        if subprocess.run(list(cmd)).returncode != 0:
            print(f"[emit-chain] FAIL at {label}", file=sys.stderr)
            raise SystemExit(1)

    step(
        "1/6 emit_fl_model",
        sys.executable,
        f"{workflow_root}/fl-model-gen/scripts/emit_fl_model.py",
        ip,
        "--root",
        root,
    )
    step(
        "2/6 emit_equivalence_goals",
        sys.executable,
        f"{workflow_root}/fl-model-gen/scripts/emit_equivalence_goals.py",
        ip,
        "--root",
        root,
    )
    step(
        "3/6 derive_ip_contract",
        sys.executable,
        f"{workflow_root}/ip-contract/scripts/derive_ip_contract.py",
        ip,
        "--root",
        root,
    )
    step(
        "4/6 emit_goal_scoreboard",
        sys.executable,
        f"{workflow_root}/tb-gen/scripts/emit_goal_scoreboard_cocotb.py",
        ip,
        "--root",
        root,
    )
    step(
        "5/6 tb_python_compile",
        sys.executable,
        f"{workflow_root}/tb-gen/scripts/check_tb_python_compile.py",
        ip,
        "--root",
        root,
    )
    step(
        "6/6 cocotb sim",
        sys.executable,
        f"{root}/{ip}/tb/cocotb/test_runner.py",
    )

    print(
        f"[emit-chain] done — inspect {ip}/sim/scoreboard_events.jsonl and "
        "CL_COSIM line above"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
