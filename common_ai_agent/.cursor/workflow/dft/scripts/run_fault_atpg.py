#!/usr/bin/env python3
"""run_fault_atpg.py — Port of run_fault_atpg.sh. Optional Fault ATPG step.

Reads scan.v + SSOT, produces <ip>/dft/out/<ip>.test and
<ip>/dft/out/coverage.json.  Args: <ip_name>

Best-effort: a Fault failure is non-fatal — auto_dft continues without coverage
and emits a [DFT COVERAGE LOW] / [DFT ATPG SKIPPED] hint.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _dft_common as common  # noqa: E402


_PARAMS_PY = r"""
import sys, pathlib
ssot, ip = sys.argv[1:3]
try:
    import yaml; d = yaml.safe_load(pathlib.Path(ssot).read_text(encoding="utf-8", errors="replace")) or {}
except Exception: d = {}
_t = d.get("top_module")
if isinstance(_t, dict): _t = _t.get("name")
top = _t or d.get("top") or ip
atpg = ((d.get("dft") or {}).get("atpg") or {})
print(atpg.get("fault_model", "stuck_at"), top, atpg.get("target_coverage", 0.90))
"""

_COVERAGE_PY = r"""
import json, re, sys, pathlib
log_p, tgt, out = sys.argv[1:4]
text = pathlib.Path(log_p).read_text(encoding="utf-8", errors="replace") if pathlib.Path(log_p).exists() else ""
m = re.search(r"(?:fault\s+)?coverage[: ]\s*([\d.]+)\s*%", text, re.I)
cov = float(m.group(1))/100.0 if m else None
target = float(tgt)
obj = {
  "fault_model": None, "coverage": cov, "target": target,
  "below_target": (cov is not None and cov < target),
  "patterns_path": None,
}
pathlib.Path(out).write_text(json.dumps(obj, indent=2), encoding="utf-8")
if cov is not None and cov < target:
    print(f"[DFT COVERAGE LOW] {cov*100:.2f}% < target {target*100:.0f}% — investigate untested logic")
"""


def main(argv: "list[str]") -> int:
    common.load_pdk_env(os.environ)

    ip = argv[0] if argv else ""
    if not ip:
        print("[DFT] usage: run_fault_atpg.sh <ip_name>", file=sys.stderr)
        return 2

    out = f"{ip}/dft/out"
    scan = f"{out}/scan.v"
    ssot = f"{ip}/yaml/{ip}.ssot.yaml"
    test = f"{out}/{ip}.test"
    cov = f"{out}/coverage.json"
    log = f"{out}/fault.log"

    if common.which("fault") is None:
        print("[DFT] Fault not on PATH — skipping ATPG", file=sys.stderr)
        return 0
    if not (Path(scan).is_file() and Path(scan).stat().st_size > 0):
        print(f"[DFT] missing {scan}", file=sys.stderr)
        return 2

    proc = common.run_embedded_py(_PARAMS_PY, [ssot, ip], capture=True)
    model, top, target = proc.stdout.split()

    sky130_lib = os.environ.get("SKY130_LIB", "")

    # `fault -m <model> -t <top> -l <lib> -o <test_out> <netlist> 2>&1 | tee <log> || true`
    # then RC=${PIPESTATUS[0]:-1}.
    fproc = subprocess.run(
        ["fault", "-m", model, "-t", top, "-l", sky130_lib, "-o", test, scan],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=dict(os.environ),
    )
    fout = fproc.stdout or b""
    sys.stdout.buffer.write(fout)
    sys.stdout.buffer.flush()
    with open(log, "wb") as fh:  # tee (truncate)
        fh.write(fout)
    rc = fproc.returncode

    # Extract coverage (best-effort, `|| true`).
    common.run_embedded_py(_COVERAGE_PY, [log, target, cov])
    print(f"[DFT] Fault rc={rc} log={log}")
    return 0  # ATPG is best-effort


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
