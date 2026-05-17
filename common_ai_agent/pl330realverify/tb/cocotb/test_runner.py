#!/usr/bin/env python3
"""Pytest/cocotb runner for pl330realverify."""

from __future__ import annotations

import os
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from cocotb_test.simulator import run

IP = "pl330realverify"
ROOT = Path(__file__).resolve().parents[2]
TB_DIR = ROOT / "tb" / "cocotb"
SIM_DIR = ROOT / "sim"
SIM_DIR.mkdir(parents=True, exist_ok=True)
DUMP_SRC = SIM_DIR / "cocotb_vcd_dump.v"

RTL = [
    ROOT / "rtl" / "pl330realverify_param.vh",
    ROOT / "rtl" / "pl330realverify.sv",
    ROOT / "rtl" / "pl330realverify_regs.sv",
    ROOT / "rtl" / "pl330realverify_channel_fsm.sv",
    ROOT / "rtl" / "pl330realverify_axi_rd.sv",
    ROOT / "rtl" / "pl330realverify_axi_wr.sv",
    ROOT / "rtl" / "pl330realverify_datapath.sv",
    ROOT / "rtl" / "pl330realverify_event_irq.sv",
]


def _build_env():
    env = os.environ.copy()
    env["PYTHONPATH"] = str(TB_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    env["ATLAS_PROJECT_ROOT"] = str(ROOT.parent)
    env["COCOTB_RESULTS_FILE"] = str(SIM_DIR / "results.xml")
    env.setdefault("COCOTB_RESOLVE_X", "ZEROS")
    return env


def _write_vcd_dump_src():
    DUMP_SRC.write_text(
        "module atlas_vcd_dump();\n"
        "initial begin\n"
        f"  $dumpfile(\"{(SIM_DIR / f'{IP}.vcd').as_posix()}\");\n"
        f"  $dumpvars(0, {IP});\n"
        "end\n"
        "endmodule\n",
        encoding="utf-8",
    )


def _copy_latest_results(build_dir: Path):
    results = sorted(build_dir.glob("*_results.xml"), key=lambda p: p.stat().st_mtime)
    if results:
        canonical = SIM_DIR / "results.xml"
        shutil.copy2(results[-1], canonical)
        _normalize_results_xml(canonical)


def _normalize_results_xml(path: Path):
    tree = ET.parse(path)
    root = tree.getroot()
    suites = [node for node in root.iter() if node.tag.endswith("testsuite")]
    tests = sum(int(float(node.get("tests", 0) or 0)) for node in suites)
    failures = sum(int(float(node.get("failures", 0) or 0)) for node in suites)
    errors = sum(int(float(node.get("errors", 0) or 0)) for node in suites)
    cases = [node for node in root.iter() if node.tag.endswith("testcase")]
    if tests == 0 and cases:
        tests = len(cases)
    if failures == 0 and cases:
        failures = sum(
            1 for case in cases
            if any(child.tag.endswith("failure") for child in list(case))
        )
    if errors == 0 and cases:
        errors = sum(
            1 for case in cases
            if any(child.tag.endswith("error") for child in list(case))
        )
    root.set("tests", str(tests))
    root.set("failures", str(failures))
    root.set("errors", str(errors))
    tree.write(path, encoding="utf-8", xml_declaration=True)


def _run_once(testcase: str | None = None):
    sim = os.getenv("SIM", "icarus")
    env = _build_env()
    if testcase:
        env["COCOTB_TESTCASE"] = testcase
    _write_vcd_dump_src()
    build_dir = SIM_DIR / "sim_build" / (testcase or "full")

    run(
        python_search=[str(TB_DIR)],
        verilog_sources=[str(p) for p in [*RTL, DUMP_SRC]],
        toplevel=["pl330realverify", "atlas_vcd_dump"],
        module="test_pl330realverify",
        sim_build=str(build_dir),
        simulator=sim,
        waves=False,
        extra_env=env,
        compile_args=["-g2012"],
    )
    _copy_latest_results(build_dir)


@pytest.mark.parametrize("testcase", [os.getenv("COCOTB_TESTCASE", "")])
def test_pl330realverify(testcase):
    tc = testcase if testcase else None
    _run_once(tc)
