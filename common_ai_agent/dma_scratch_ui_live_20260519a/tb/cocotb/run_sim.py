#!/usr/bin/env python3
"""Cocotb run script for DMA scratch UI verification.

Usage:
  Bounded probe:  python3 run_sim.py --test reset_only
  Full regression: python3 run_sim.py --test all
"""

import os
import sys
from pathlib import Path

# Ensure project root in sys.path and set PYTHONPATH for cocotb
SCRIPT_DIR = Path(__file__).resolve().parent  # tb/cocotb/
IP_DIR = SCRIPT_DIR.parents[1]  # dma_scratch_ui_live_20260519a/
PROJECT_ROOT = IP_DIR.parent  # common_ai_agent/
os.chdir(str(IP_DIR))

# Add IP dir parent to Python path so 'tb.cocotb.xxx' imports work
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ["PYTHONPATH"] = str(PROJECT_ROOT) + ":" + os.environ.get("PYTHONPATH", "")

from cocotb.runner import get_runner  # noqa: E402


def run_test(testcase: str):
    runner = get_runner("icarus")

    verilog_sources = [
        "rtl/csr_registers.sv",
        "rtl/dma_engine.sv",
        "rtl/irq_status.sv",
        "rtl/dma_scratch_ui_live_20260519a.sv",
    ]

    runner.build(
        verilog_sources=verilog_sources,
        includes=["rtl"],
        hdl_toplevel="dma_scratch_ui_live_20260519a",
        build_args=["-g2012"],
    )

    runner.test(
        hdl_toplevel="dma_scratch_ui_live_20260519a",
        test_module="dma_scratch_ui_live_20260519a.tb.cocotb.test_dma_scratch_ui_live_20260519a",
        hdl_toplevel_lang="verilog",
        testcase=testcase,
    )


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", default="test_reset_only",
                    choices=["test_reset_only", "test_single_beat", "test_all_scenarios"])
    args = ap.parse_args()
    run_test(args.test)
