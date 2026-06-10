#!/usr/bin/env python3
"""coverage_vcd_toggle.py — Python port of coverage_vcd_toggle.sh (coverage).

Wrap ``adapters/vcd_toggle.py``: pick the merged VCD (from /coverage-vcd-merge)
or the first ``*.vcd`` under ``<DUT>/``, then emit toggle coverage and persist a
JSON snapshot to ``<DUT>/cov/toggle.json``.

CLI / env contract preserved:
  * If no args and ``$HOOK_CMD_ARGS`` set, the args come from word-splitting
    ``$HOOK_CMD_ARGS``.
  * Args: ``--json`` (show JSON), ``--top N``, ``--vcd PATH``; the first bare
    positional sets DUT (default ``gpio_pad``); spaces stripped from DUT.
  * Adapter = ``<script_dir>/../adapters/vcd_toggle.py``; missing ⇒ ERROR + 1.
  * ``--vcd PATH`` is validated: file must exist, end with ``.vcd`` (case
    insensitive), and resolve inside ``<DUT>/`` (else specific ERROR + 1).
  * Otherwise prefer ``<DUT>/cov/merged.vcd`` else first ``*.vcd`` (sorted).
    None ⇒ ERROR guidance + 1.
  * Always write the JSON snapshot (``adapter --json --top N TARGET`` →
    ``<DUT>/cov/toggle.json``); then either cat the JSON (``--json``) or pretty
    print a text summary.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _resolve(path: str) -> str:
    # python3 -c 'print(Path(arg).resolve())'
    return str(Path(path).resolve())


def _find_first_vcd(dut: str) -> str:
    # find "${DUT}" -name "*.vcd" | sort  → first
    results: "list[str]" = []
    for dirpath, _dirnames, filenames in os.walk(dut):
        for name in filenames:
            if name.endswith(".vcd"):
                results.append(str(Path(dirpath) / name))
    results.sort()
    return results[0] if results else ""


def main(argv: "list[str] | None" = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    # if [ "$#" -eq 0 ] && [ -n "$HOOK_CMD_ARGS" ]; then set -- $HOOK_CMD_ARGS; fi
    if not argv and os.environ.get("HOOK_CMD_ARGS"):
        argv = os.environ["HOOK_CMD_ARGS"].split()

    dut = "gpio_pad"
    want_json = False
    top = 10
    vcd_path = ""

    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--json":
            want_json = True
        elif arg == "--top":
            i += 1
            if i < len(argv):
                top = argv[i]
        elif arg == "--vcd":
            i += 1
            if i < len(argv):
                vcd_path = argv[i]
        else:
            if dut == "gpio_pad":
                dut = arg
        i += 1
    dut = dut.replace(" ", "")

    script_dir = Path(__file__).resolve().parent
    adapter = script_dir / ".." / "adapters" / "vcd_toggle.py"
    if not adapter.is_file():
        print(f"ERROR: adapter not found: {adapter}")
        return 1

    target = ""
    if vcd_path:
        if not Path(vcd_path).is_file():
            print(f"ERROR: VCD not found: {vcd_path}")
            return 1
        if not vcd_path.lower().endswith(".vcd"):
            print(f"ERROR: VCD path must end with .vcd: {vcd_path}")
            return 1
        dut_root = _resolve(dut)
        vcd_real = _resolve(vcd_path)
        if not (vcd_real == dut_root or vcd_real.startswith(dut_root + os.sep)):
            # Bash: case "${VCD_REAL}" in "${DUT_ROOT}"/*) ;; → must be *under*.
            print(f"ERROR: VCD outside DUT: {vcd_path}")
            return 1
        target = vcd_path
    elif (Path(dut) / "cov" / "merged.vcd").is_file():
        target = f"{dut}/cov/merged.vcd"
    else:
        target = _find_first_vcd(dut)

    if not target:
        print(f"ERROR: no VCD found under {dut}/")
        print("  Run a simulation first (with WAVES=1 or analogous), or run")
        print("  /coverage-vcd-merge to combine multiple VCDs.")
        return 1

    print(f"VCD: {target}")
    print("")

    cov_dir = Path(dut) / "cov"
    cov_dir.mkdir(parents=True, exist_ok=True)
    toggle_json_path = cov_dir / "toggle.json"

    # python3 "${ADAPTER}" --json --top "${TOP}" "${TARGET}" > toggle.json
    with open(toggle_json_path, "w", encoding="utf-8") as handle:
        subprocess.run(
            [sys.executable, str(adapter), "--json", "--top", str(top), target],
            stdout=handle,
        )
    print(f"JSON snapshot: {toggle_json_path}")

    if want_json:
        sys.stdout.write(toggle_json_path.read_text(encoding="utf-8"))
    else:
        # Pretty-print summary from the JSON we just wrote.
        doc = json.loads(toggle_json_path.read_text(encoding="utf-8"))
        print()
        print(f"=== VCD Toggle Coverage: {doc['vcd']} ===")
        print(f"Nets         : {doc['nets']}")
        print(f"Total bits   : {doc['total_bits']}")
        print(f"Toggled bits : {doc['toggled_bits']}")
        print(f"Toggle %     : {doc['pct']:.2f} %")
        print()
        print(f"=== Worst-{len(doc['scopes'])} scopes (by toggle %) ===")
        for s in sorted(doc["scopes"], key=lambda x: x["pct"])[:10]:
            print(
                f"  {s['pct']:5.1f} %  {s['toggled']:>4}/{s['total']:<4} bits  "
                f"({s['nets']} nets)  {s['scope']}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
