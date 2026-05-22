"""Cocotb test runner for dma_real using cocotb_test.simulator (Icarus backend).

Mirrors arm_m0_min/tb/cocotb/test_runner.py pattern.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

from cocotb_test.simulator import run


def _ip_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def _rtl_sources() -> list[str]:
    rtl = _ip_dir() / "rtl"
    return [
        str(rtl / "dma_real_irq.sv"),
        str(rtl / "dma_real_arbiter.sv"),
        str(rtl / "dma_real_ahb_master.sv"),
        str(rtl / "dma_real_channel.sv"),
        str(rtl / "dma_real_apb_cfg.sv"),
        str(rtl / "dma_real_top.sv"),
    ]


def _tb_wrapper() -> str:
    return str(_ip_dir() / "tb" / "cocotb" / "dma_real_tb.sv")


def main():
    ip = "dma_real"
    ip_dir = _ip_dir()
    sim_dir = ip_dir / "sim"
    sim_dir.mkdir(parents=True, exist_ok=True)

    sources = _rtl_sources() + [_tb_wrapper()]

    os.environ["COMMON_AI_AGENT_ROOT"] = str(ip_dir.parent)

    start = time.time()
    run(
        verilog_sources=sources,
        toplevel="dma_real_tb",
        module="test_dma_real",
        toplevel_lang="verilog",
        compilation_args=["-g2012"],
        workdir=str(sim_dir),
        testcase="",
        seed=os.environ.get("RANDOM_SEED", str(int(time.time()) % 2**31)),
    )
    elapsed = time.time() - start
    print(f"sim elapsed={elapsed:.1f}s")

    # Parse results
    results_xml = sim_dir / "results.xml"
    if results_xml.exists():
        tree = ET.parse(results_xml)
        root = tree.getroot()
        total = 0
        passed = 0
        failed = 0
        for ts in root.iter("testsuite"):
            for tc in ts.iter("testcase"):
                total += 1
                failures = tc.findall("failure")
                if failures:
                    failed += 1
                    for f in failures:
                        print(f"FAIL: {tc.attrib['name']} — {f.attrib.get('message', '')}")
                else:
                    passed += 1
        print(f"TESTS={total} PASS={passed} FAIL={failed}")
    else:
        print("WARNING: no results.xml found")


if __name__ == "__main__":
    main()
