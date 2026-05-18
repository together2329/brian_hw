"""cocotb test entry point — runs all SSOT scenarios with pyuvm-style orchestration.

SSOT coverage:
  - test_requirements.scenarios[0..10] → SC01–SC11
  - All 11 scenarios executed and checked via DmaScoreboard + FunctionalCoverage

Usage:
    make SIM=icarus
    or:
    COCOTB_TESTCASE=test_all_scenarios pytest test_runner.py
"""

import cocotb
from cocotb.log import SimLog

from uvm_env import DmaEnv

# Import scenarios for single-test selection via COCOTB_TESTCASE
from sequences import SCENARIOS

SCENARIO_MAP = dict(SCENARIOS)


@cocotb.test()
async def test_reset_only(dut):
    """Bounded probe: reset defaults (SC01) only."""
    log = SimLog("test_reset_only")
    env = DmaEnv(dut)
    await env.setup()

    from sequences import sc01_reset_defaults
    ok = await sc01_reset_defaults(env.dut, env.csr_agent, env.rd_driver,
                                   env.sb, env.cov, log)
    env.scenario_results["SC01"] = ok

    assert ok, "SC01 reset_defaults FAILED"
    log.info("test_reset_only PASSED")


@cocotb.test()
async def test_single_beat(dut):
    """Bounded probe: SC01 + SC02 + SC05 (reset + CSR + single beat)."""
    log = SimLog("test_single_beat")
    env = DmaEnv(dut)
    await env.setup()

    from sequences import (sc01_reset_defaults, sc02_csr_programming_readback,
                           sc05_single_beat_copy)

    ok = await sc01_reset_defaults(env.dut, env.sb, env.cov, log)
    assert ok, "SC01 FAILED"

    ok = await sc02_csr_programming_readback(env.dut, env.csr_agent, env.rd_driver,
                                               env.sb, env.cov, log)
    assert ok, "SC02 FAILED"

    ok = await sc05_single_beat_copy(env.dut, env.csr_agent, env.rd_driver,
                                     env.sb, env.cov, log)
    assert ok, "SC05 FAILED"

    log.info("test_single_beat PASSED")


@cocotb.test()
async def test_all_scenarios(dut):
    """Full regression: all 11 SSOT scenarios (SC01–SC11).

    This is the signoff test. Any scenario failure or scoreboard mismatch
    raises AssertionError.
    """
    log = SimLog("test_all_scenarios")
    env = DmaEnv(dut)
    passed, total = await env.run_all()

    # Export coverage
    cov_path = "dma_scratch_ui_live_20260519a/cov/coverage_functional.json"
    env.cov.export_json(cov_path)

    # Export scoreboard events
    sb_path = "dma_scratch_ui_live_20260519a/sim/scoreboard_events.jsonl"
    env.sb.export_events_jsonl(sb_path)

    # Final assertion
    assert passed == total, (
        f"ONLY {passed}/{total} SCENARIOS PASSED. "
        f"Failures: {env.sb.all_failures}"
    )
    log.info(f"ALL {passed}/{total} SCENARIOS PASSED")
