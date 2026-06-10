#!/usr/bin/env python3
"""auto_dft.py — Port of auto_dft.sh. End-to-end DFT driver. Single entry point for /dft.

Args: <ip_name>
Pipeline: handoff gate → SSOT read → passthrough OR (tcl → openroad → parse →
optional ATPG) → report.

The bash original shells out to the sibling ``*.sh`` scripts; this port shells
out to the sibling ``*.py`` ports via ``sys.executable``.
"""

from __future__ import annotations

import glob
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _dft_common as common  # noqa: E402


_ENABLED_PY = r"""
import sys, pathlib
p = pathlib.Path(sys.argv[1])
if not p.is_file(): print("false"); sys.exit(0)
try:
    import yaml; d = yaml.safe_load(p.read_text(encoding="utf-8", errors="replace")) or {}
except Exception:
    d = {}
dft = d.get("dft", {}) or {}
print("true" if dft.get("enabled", False) else "false")
"""

_PASSTHROUGH_JSON_PY = r"""
import json, sys, pathlib
ip, out = sys.argv[1:3]
obj = {
  "top": ip, "tool": "passthrough", "scan_chains": [],
  "summary": {"total_ffs": None, "ffs_in_chains": 0, "ffs_skipped": 0,
              "chains": 0, "max_length": 0, "min_length": 0,
              "scan_enable_port": None, "mode": "passthrough"},
}
pathlib.Path(out, "scan_chains.json").write_text(json.dumps(obj, indent=2), encoding="utf-8")
"""

_ATPG_ENABLED_PY = r"""
import sys, pathlib
try:
    import yaml; d = yaml.safe_load(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")) or {}
except Exception: d = {}
atpg = ((d.get("dft") or {}).get("atpg") or {})
print("true" if atpg.get("enabled", False) else "false")
"""


def main(argv: "list[str]") -> int:
    common.load_pdk_env(os.environ)

    ip = argv[0] if argv else ""
    if not ip:
        print("[DFT] usage: auto_dft.sh <ip_name>", file=sys.stderr)
        return 2
    if not Path(ip).is_dir():
        print(f"[DFT] no such IP dir: {ip}", file=sys.stderr)
        return 2

    d = os.path.dirname(os.path.abspath(__file__))
    netlist = f"{ip}/syn/out/synth.v"
    out = f"{ip}/dft/out"
    ssot = f"{ip}/yaml/{ip}.ssot.yaml"
    Path(out).mkdir(parents=True, exist_ok=True)

    # Handoff gate
    if not (Path(netlist).is_file() and Path(netlist).stat().st_size > 0):
        print(f"[DFT HANDOFF MISSING] {netlist} — run /syn first", file=sys.stderr)
        return 5
    rtl_files = sorted(glob.glob(f"{ip}/rtl/*.sv")) + sorted(glob.glob(f"{ip}/rtl/*.v"))
    if rtl_files:
        # `ls -t *.sv *.v | head -1`: newest by mtime.
        newest_rtl = max(rtl_files, key=lambda p: Path(p).stat().st_mtime)
        if newest_rtl and Path(newest_rtl).stat().st_mtime > Path(netlist).stat().st_mtime:
            print(
                f"[DFT STALE NETLIST] {newest_rtl} newer than {netlist} — re-run /syn",
                file=sys.stderr,
            )
            return 6

    # Read dft.enabled from SSOT
    proc = common.run_embedded_py(_ENABLED_PY, [ssot], capture=True)
    enabled = proc.stdout.strip()

    if enabled != "true":
        shutil.copyfile(netlist, f"{out}/scan.v")
        common.run_embedded_py(_PASSTHROUGH_JSON_PY, [ip, out])
        subprocess.run([sys.executable, os.path.join(d, "write_report.py"), ip])  # || true
        print(f"[DFT DISABLED] passthrough — {netlist} copied to {out}/scan.v")
        return 0

    # Real scan-insert path: need OpenROAD + Liberty + scan_enable_port to exist
    if common.which("openroad") is None:
        print("[DFT TOOL MISSING] openroad not on PATH", file=sys.stderr)
        return 3
    lib = os.environ.get("SKY130_LIB", "")
    if not common.readable(lib):
        print(f"[DFT MISSING PDK] $SKY130_LIB unreadable: {lib}", file=sys.stderr)
        return 4
    os.environ["SKY130_LIB"] = lib

    for script in ("write_dft_tcl.py", "run_openroad_dft.py", "parse_chains.py"):
        rc = subprocess.run([sys.executable, os.path.join(d, script), ip]).returncode
        if rc != 0:
            return rc

    # Optional ATPG via Fault
    proc = common.run_embedded_py(_ATPG_ENABLED_PY, [ssot], capture=True)
    atpg_enabled = proc.stdout.strip()
    if atpg_enabled == "true":
        if common.which("fault") is not None:
            rc = subprocess.run(
                [sys.executable, os.path.join(d, "run_fault_atpg.py"), ip]
            ).returncode
            if rc != 0:
                print(
                    "[DFT] Fault ATPG step failed — continuing without coverage",
                    file=sys.stderr,
                )
        else:
            print(
                "[DFT] Fault not on PATH — skipping ATPG (set dft.atpg.enabled: false "
                "in SSOT to suppress this warning)",
                file=sys.stderr,
            )

    subprocess.run([sys.executable, os.path.join(d, "write_report.py"), ip])  # || true

    chains = _summary_field(f"{out}/scan_chains.json", "chains")
    ffs = _summary_field(f"{out}/scan_chains.json", "ffs_in_chains")
    print(f"[DFT HANDOFF] {out}/scan.v ready (chains={chains}, scan_ffs={ffs}) — run /pnr-fp")
    return 0


def _summary_field(path: str, field: str) -> str:
    """Mirror `python3 -c "...print(d['summary'][field])" 2>/dev/null || echo 0`."""
    try:
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        return str(d["summary"][field])
    except Exception:
        return "0"


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
