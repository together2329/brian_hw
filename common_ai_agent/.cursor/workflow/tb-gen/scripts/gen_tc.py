#!/usr/bin/env python3
"""gen_tc.py — Python port of gen_tc.sh (tb-gen).

Generate a ``tc_<module>.sv`` skeleton from a DUT source file.

CLI / env contract preserved:
  * MODULE = ``$HOOK_CMD_ARGS`` else first positional argument; if empty, pick
    the first ``./*.sv`` (maxdepth 1) excluding ``tb_*`` / ``tc_*`` with the
    ``.sv`` suffix stripped.
  * ``SRC = ${MODULE}.sv`` (NOTE: unlike coverage.sh this does *not* strip an
    existing ``.sv``, so passing ``foo.sv`` looks for ``foo.sv.sv``).  Missing
    SRC ⇒ ``DUT not found: <src>`` and exit 1.
  * If ``tc_<module>.sv`` already exists ⇒ "already exists" message, exit 0
    (no overwrite).
  * Otherwise write the fixed skeleton, then print "Generated: ..." plus the
    DUT input/output port names.

Faithful port note: input/output port extraction uses the same
``grep -oP '...\\K\\w+'`` commands as the ``.sh``.  ``\\K`` is a GNU-PCRE
feature absent from BSD grep, so the port shells out to the identical commands
to match the ``.sh`` on whatever host runs it (the grep error, when ``-P`` is
unsupported, goes to stderr exactly as in the original).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


TC_TEMPLATE = """\
// tc_{module}.sv — Test cases for {module}
// Generated skeleton — fill in stimulus and assertions

task automatic tc_reset(
    ref logic clk, rst_n,
    ref integer pass_cnt, fail_cnt
);
    // Reset assertion
    rst_n = 0;
    repeat(3) @(posedge clk);
    rst_n = 1;
    @(posedge clk);
    // TODO: assert reset values
    $display("[PASS] tc_reset"); pass_cnt++;
endtask

task automatic tc_normal_op(
    ref logic clk, rst_n,
    // TODO: add port refs
    ref integer pass_cnt, fail_cnt
);
    // TODO: apply normal stimulus
    // TODO: check expected output
    $display("[PASS] tc_normal_op"); pass_cnt++;
endtask

task automatic tc_boundary(
    ref logic clk, rst_n,
    // TODO: add port refs
    ref integer pass_cnt, fail_cnt
);
    // TODO: min/max parameter values
    $display("[PASS] tc_boundary"); pass_cnt++;
endtask

task automatic tc_edge_case(
    ref logic clk, rst_n,
    // TODO: add port refs
    ref integer pass_cnt, fail_cnt
);
    // TODO: edge case from spec
    $display("[PASS] tc_edge_case"); pass_cnt++;
endtask
"""


def _find_default_module() -> str:
    proc = subprocess.run(
        ["/bin/sh", "-c",
         r"""find . -maxdepth 1 -name "*.sv" | grep -v "tb_\|tc_" | head -1 | sed 's|./||;s|\.sv||' """],
        capture_output=True, text=True,
    )
    return proc.stdout.strip()


def _grep_op(pattern: str, path: str) -> str:
    """Run ``grep -oP <pattern> <path>`` and return stdout (errors → stderr)."""
    proc = subprocess.run(
        ["grep", "-oP", pattern, path],
        capture_output=True,
        text=True,
    )
    # Forward the grep diagnostic to our stderr so it surfaces exactly like the
    # original (where the uncaptured grep error printed to the terminal).
    if proc.stderr:
        sys.stderr.write(proc.stderr)
    return proc.stdout


def main(argv: "list[str] | None" = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    module = os.environ.get("HOOK_CMD_ARGS") or (argv[0] if argv else "")
    if not module:
        module = _find_default_module()

    src = f"{module}.sv"
    out = f"tc_{module}.sv"

    if not Path(src).is_file():
        print(f"DUT not found: {src}")
        return 1
    if Path(out).is_file():
        print(f"{out} already exists — edit it directly.")
        return 0

    inputs = _grep_op(r"input\s+logic\s+(\[\d+:\d+\]\s+)?\K\w+", src)
    outputs = _grep_op(r"output\s+logic\s+(\[\d+:\d+\]\s+)?\K\w+", src)

    Path(out).write_text(TC_TEMPLATE.format(module=module), encoding="utf-8")

    # Bash captured the port names via $(...) command substitution, which
    # strips trailing newlines, then echoed inside double quotes so any interior
    # newlines are PRESERVED.  Replicate: drop only trailing newlines.
    inputs_val = inputs.rstrip("\n")
    outputs_val = outputs.rstrip("\n")

    print(f"Generated: {out}")
    print("Ports found in DUT:")
    print(f"  Inputs : {inputs_val}")
    print(f"  Outputs: {outputs_val}")
    print()
    print("Fill in stimulus and assertions in each task.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
