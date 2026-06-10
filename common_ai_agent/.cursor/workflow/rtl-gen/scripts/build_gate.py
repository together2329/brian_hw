#!/usr/bin/env python3
# =============================================================================
# build_gate.py — RTL build-time gate orchestrator (Python port of build_gate.sh)
# =============================================================================
# Runs all SSOT-driven contract checks BEFORE the simulator gets to
# touch the design. Any failure here aborts the loop with a clear
# repair_prompt and avoids burning sim cycles on an already-broken
# build.
#
# Usage:
#   build_gate.py <ip> [--root .]
#
# Gates (in order):
#   G1  YAML validity                    (yaml.safe_load)
#   G2  SSOT completeness                (timing_constraints / invariants /
#                                         forbidden_states / forbidden_environment
#                                         non-empty)
#   G3  Register layout contract         (check_register_contract.py)
#   G4  TB magic-number lint             (check_tb_magic_numbers.py)
#   G5  RTL lint (verilator --lint-only) (single-driver, latch, etc.)
#   G6  Formal property emit (no run)    (emit_formal_properties.py)
#   G7  Timing header emit               (emit_timing_header.py)
#   G8  Single-driver check              (check_single_driver.py)
#
# Exit codes:
#   0  all gates pass (or skip-allowed)
#   1  any gate failed
#   2  bad usage / missing dirs
# =============================================================================
"""Python port of build_gate.sh — same CLI, exit codes, stdout/stderr, JSON.

bash `set -uo pipefail` (no -e): a failing gate is recorded and accumulates into
`gate_status`, the chain keeps running. Replicated faithfully here. The inline
G1/G2 `python3 -c` checks are executed as subprocess `-c` invocations using the
identical source so their stdout is byte-identical. G5's verilator block is run
via the same `bash -c` script when verilator is on PATH.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _line_buffer_stdout() -> None:
    # bash line-buffers stdout; Python block-buffers it when not a TTY, which
    # reorders lines under a merged `2>&1`. Line buffering keeps the colored
    # gate banners and child gate output interleaved as the shell does.
    try:
        sys.stdout.reconfigure(line_buffering=True)  # type: ignore[attr-defined]
    except (AttributeError, ValueError):  # pragma: no cover - non-TextIO stdout
        pass


def cyan(msg: str) -> None:
    sys.stdout.write(f"\033[1;36m{msg}\033[0m\n")


def red(msg: str) -> None:
    sys.stdout.write(f"\033[1;31m{msg}\033[0m\n")


def green(msg: str) -> None:
    sys.stdout.write(f"\033[1;32m{msg}\033[0m\n")


def main(argv: list[str]) -> int:
    _line_buffer_stdout()
    ip = ""
    root = "."
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--root":
            root = argv[i + 1] if i + 1 < len(argv) else ""
            i += 2
        elif arg.startswith("--root="):
            root = arg[len("--root="):]
            i += 1
        elif arg.startswith("-"):
            print(f"[build_gate] unknown flag: {arg}", file=sys.stderr)
            return 2
        else:
            if not ip:
                ip = arg
                i += 1
            else:
                print(f"[build_gate] extra positional: {arg}", file=sys.stderr)
                return 2

    if not ip:
        print("usage: build_gate.sh <ip> [--root .]", file=sys.stderr)
        return 2

    # ROOT="$(cd "$ROOT" && pwd)"  — bash: if the dir is missing, the command
    # substitution yields an empty string (cd's error goes to stderr). We mirror
    # the observable contract: a non-existent root collapses ROOT to "" so the
    # subsequent IP_DIR check fails with exit 2. os.path.abspath (not resolve)
    # mirrors bash's *logical* `pwd` — symlinks like /tmp are NOT collapsed to
    # /private/tmp.
    if Path(root).is_dir():
        root = os.path.abspath(root)
    else:
        root = ""
    ip_dir = f"{root}/{ip}"

    if not Path(ip_dir).is_dir():
        print(f"[build_gate] missing IP dir: {ip_dir}", file=sys.stderr)
        return 2

    scripts_dir = Path(__file__).resolve().parent
    workflow_dir = (scripts_dir / ".." / "..").resolve()

    Path(f"{ip_dir}/lint").mkdir(parents=True, exist_ok=True)
    gate_json = Path(f"{ip_dir}/lint/build_gate.json")

    gate_status = "pass"
    gate_log: list[str] = []

    def run_gate(name: str, *cmd: str) -> None:
        nonlocal gate_status
        cyan(f"▸ {name}")
        proc = subprocess.run(list(cmd))
        if proc.returncode == 0:
            gate_log.append(f'"{name}":"pass"')
        else:
            rc = proc.returncode
            red(f"  ✗ {name} failed (rc={rc})")
            gate_log.append(f'"{name}":"fail"')
            gate_status = "fail"

    # G1 — YAML validity
    g1_src = (
        "\n"
        "import yaml, sys\n"
        f"yaml.safe_load(open('{ip_dir}/yaml/{ip}.ssot.yaml'))\n"
        "print('[G1] YAML parses')\n"
    )
    run_gate("G1_yaml_valid", sys.executable, "-c", g1_src)

    # G2 — SSOT negative spec presence
    g2_src = (
        "\n"
        "import yaml, sys\n"
        f"d = yaml.safe_load(open('{ip_dir}/yaml/{ip}.ssot.yaml'))\n"
        "required = ['timing_constraints', 'invariants', 'forbidden_states',\n"
        "            'forbidden_environment']\n"
        "missing = [k for k in required if not d.get(k)]\n"
        "if missing:\n"
        "    print('[G2] missing/empty negative spec:', missing); sys.exit(1)\n"
        'print(f\'[G2] negative spec OK ({len(d["invariants"])} invariants, \'\n'
        '      f\'{len(d["forbidden_states"])} forbidden_states, \'\n'
        '      f\'{len(d["forbidden_environment"])} forbidden_env)\')\n'
    )
    run_gate("G2_ssot_negative_spec", sys.executable, "-c", g2_src)

    # G3 — Register layout contract
    run_gate(
        "G3_register_contract",
        sys.executable,
        str(workflow_dir / "rtl-gen" / "scripts" / "check_register_contract.py"),
        ip,
        "--root",
        root,
    )

    # G4 — TB magic numbers (warning-only is OK; only error fails)
    run_gate(
        "G4_tb_magic_numbers",
        sys.executable,
        str(workflow_dir / "tb-gen" / "scripts" / "check_tb_magic_numbers.py"),
        ip,
        "--root",
        root,
    )

    # G5 — RTL lint (verilator if available)
    import shutil as _shutil

    if _shutil.which("verilator") is not None:
        g5_script = (
            "\n"
            "set -e\n"
            f"cd '{ip_dir}'\n"
            "RTL_FILES=$(ls rtl/*.sv 2>/dev/null)\n"
            'if [ -z "$RTL_FILES" ]; then\n'
            "    echo '[G5] no RTL files'\n"
            "    exit 1\n"
            "fi\n"
            "verilator --lint-only --Wall -Wno-fatal -Irtl $RTL_FILES 2>&1 | tee lint/verilator_lint.log\n"
            "LINT_RC=${PIPESTATUS[0]}\n"
            'if [ "$LINT_RC" -ne 0 ]; then\n'
            "    echo '[G5] verilator lint reported issues (see lint/verilator_lint.log)'\n"
            "    # don't fail immediately on warnings; only error-level matters.\n"
            "    if grep -qE '%Error' lint/verilator_lint.log; then\n"
            "        exit 1\n"
            "    fi\n"
            "fi\n"
            "echo '[G5] RTL lint OK'\n"
        )
        run_gate("G5_rtl_lint", "bash", "-c", g5_script)
    else:
        print("[G5] verilator not in PATH — skipping RTL lint")
        gate_log.append('"G5_rtl_lint":"skip"')

    # G6 — Formal property emit (parse only)
    run_gate(
        "G6_formal_emit",
        sys.executable,
        str(workflow_dir / "fl-model-gen" / "scripts" / "emit_formal_properties.py"),
        ip,
        "--root",
        root,
    )

    # G7 — Timing header emit
    run_gate(
        "G7_timing_header",
        sys.executable,
        str(workflow_dir / "tb-gen" / "scripts" / "emit_timing_header.py"),
        ip,
        "--root",
        root,
    )

    # G8 — Single-driver check
    run_gate(
        "G8_single_driver",
        sys.executable,
        str(workflow_dir / "rtl-gen" / "scripts" / "check_single_driver.py"),
        ip,
        "--root",
        root,
    )

    # Write gate JSON — byte-identical to the shell printf sequence.
    gates_joined = ",".join(gate_log)
    json_text = (
        "{\n"
        '  "schema_version": 1,\n'
        '  "type": "build_gate",\n'
        f'  "ip": "{ip}",\n'
        f'  "overall_status": "{gate_status}",\n'
        '  "gates": {\n'
        f"    {gates_joined}\n"
        "  }\n"
        "}\n"
    )
    gate_json.write_text(json_text, encoding="utf-8")

    if gate_status == "pass":
        green(f"▣ build_gate ALL PASS  ({gate_json})")
        return 0
    else:
        red(f"▣ build_gate FAILED  ({gate_json})")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
