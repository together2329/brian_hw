#!/usr/bin/env python3
"""preflight.py — Port of preflight.sh. Validate OpenROAD/PDK/handoff inputs before PnR.

Args: <ip>
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _pnr_common as common  # noqa: E402


# Inline python heredoc from preflight.sh: validate + emit pnr.* params.
_PARAMS_PY = r"""
import pathlib, sys

try:
    import yaml
except Exception as exc:
    print(f"[PNR PREFLIGHT] PyYAML required to read SSOT: {exc}", file=sys.stderr)
    raise SystemExit(2)

doc = yaml.safe_load(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")) or {}
pnr = doc.get("pnr") or {}
required = [
    "utilization_pct",
    "aspect_ratio",
    "core_space_um",
    "global_density",
    "io_layers.horizontal",
    "io_layers.vertical",
]
missing = []
for key in required:
    cur = pnr
    for part in key.split("."):
        cur = cur.get(part) if isinstance(cur, dict) else None
    if cur in (None, ""):
        missing.append(f"pnr.{key}")
if missing:
    print("[PNR SSOT TBD REPORT] missing physical constraints:", file=sys.stderr)
    for item in missing:
        print(f"  - {item}", file=sys.stderr)
    raise SystemExit(7)
io = pnr.get("io_layers") or {}
cts = pnr.get("cts_buf_list") or "sky130_fd_sc_hd__clkbuf_4 sky130_fd_sc_hd__clkbuf_8"
if isinstance(cts, list):
    cts = ",".join(str(item).strip() for item in cts if str(item).strip())
else:
    cts = ",".join(str(cts).replace(",", " ").split())
print(
    pnr.get("utilization_pct"),
    pnr.get("aspect_ratio"),
    pnr.get("core_space_um"),
    pnr.get("global_density"),
    io.get("horizontal"),
    io.get("vertical"),
    cts,
)
"""


def main(argv: "list[str]") -> int:
    argv = common.argv_from_hook(argv)
    common.load_pdk_env(os.environ)

    ip = argv[0] if argv else ""
    if not ip:
        print("[PNR PREFLIGHT] usage: preflight.sh <ip>", file=sys.stderr)
        return 2

    print(f"[PNR PREFLIGHT] cwd={os.getcwd()}")
    print(f"[PNR PREFLIGHT] PDK_ROOT={os.environ.get('PDK_ROOT', '')}")
    print(f"[PNR PREFLIGHT] SKY130_PDK_ROOT={os.environ.get('SKY130_PDK_ROOT', '')}")

    rc = common.check_tools()
    if rc != 0:
        return rc

    if not Path(ip).is_dir():
        print(f"[PNR PREFLIGHT] IP dir missing: {ip}", file=sys.stderr)
        return 2
    ssot = f"{ip}/yaml/{ip}.ssot.yaml"
    if not Path(ssot).is_file():
        print(f"[PNR PREFLIGHT] SSOT missing: {ssot}", file=sys.stderr)
        return 2
    netlist, rc = common.check_handoff(ip)
    if rc != 0:
        return rc
    print(f"[PNR PREFLIGHT] netlist={netlist}")
    print(f"[PNR PREFLIGHT] sdc={ip}/sta/out/{ip}.sdc")

    proc = common.run_embedded_py(_PARAMS_PY, [ssot], capture=True)
    sys.stderr.write(proc.stderr)
    if proc.returncode != 0:
        return proc.returncode
    params = proc.stdout

    # `read UTIL AR CSPACE DENSITY HOR VER CTS_BUF <<< "$PARAMS"`: split on
    # whitespace into 7 fields (last field absorbs the remainder, but cts here
    # is comma-joined so it is a single token).
    fields = params.split()
    util, ar, cspace, density, hor, ver, cts_buf = fields[:7]

    rc = common.check_io_layers(hor, ver)
    if rc != 0:
        return rc

    print(
        f"[PNR PREFLIGHT] utilization={util}% aspect_ratio={ar} "
        f"core_space={cspace}um density={density}"
    )
    print(f"[PNR PREFLIGHT] io_layers horizontal={hor} vertical={ver}")
    print(f"[PNR PREFLIGHT] cts_buf_list={cts_buf.replace(',', ' ')}")
    print("[PNR PREFLIGHT] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
