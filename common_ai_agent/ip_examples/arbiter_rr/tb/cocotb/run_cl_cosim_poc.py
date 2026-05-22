"""Standalone runner for the CL co-simulation PoC.

Reuses the existing tb_manifest filelist but points cocotb at the
test_cl_cosim_poc module so we can iterate on the PoC without disturbing
the full goal-driven test_arbiter_rr flow.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from cocotb_test.simulator import run


def main() -> int:
    here = Path(__file__).resolve()
    ip_dir = here.parents[2]
    manifest = json.loads((ip_dir / "tb" / "cocotb" / "tb_manifest.json").read_text(encoding="utf-8"))
    sources = [str(ip_dir.parent / src) for src in manifest["rtl_sources"]]
    top = manifest["top"]
    build_dir = ip_dir / "sim" / "cocotb_build_cl_poc"
    build_dir.mkdir(parents=True, exist_ok=True)
    # Inject a timescale so cocotb's 10ns clock fits the simulator precision.
    ts_path = build_dir / "timescale.v"
    ts_path.write_text("`timescale 1ns/1ps\n", encoding="utf-8")

    run(
        verilog_sources=[str(ts_path)] + sources,
        toplevel=top,
        module="test_cl_cosim_poc",
        sim_build=str(build_dir),
        compile_args=["-g2012", f"-I{ip_dir}/rtl"],
        extra_env={"PYTHONPATH": str(here.parent)},
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
