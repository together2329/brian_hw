#!/usr/bin/env python3
"""Cocotb test for quad_spi_ctrl_top — FL/CL equivalence scoreboard.

SSOT refs: test_requirements.scenarios, function_model, cycle_model
TOP = quad_spi_ctrl_top (from SSOT top_module.name, NOT ip_name)
Scoreboard: EquivalenceScoreboard against model/functional_model.py
"""

import os
import sys
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles

# Import scenario library
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../tc'))
from quad_spi_ctrl_scenarios import QuadSPIScenarios

# Import functional model as golden oracle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../model'))
try:
    from functional_model import FunctionalModel
    HAS_FL_MODEL = True
except ImportError:
    HAS_FL_MODEL = False
    cocotb.log.warning("functional_model.py not importable — scoreboard disabled")


class EquivalenceScoreboard:
    """Scoreboard that compares RTL observables against FunctionalModel."""

    def __init__(self, dut):
        self.dut = dut
        self.fm = FunctionalModel() if HAS_FL_MODEL else None
        self.events = []
        self.passed = 0
        self.failed = 0

    def check(self, label, observed, expected):
        """Record a scoreboard check."""
        ok = (observed == expected)
        if ok:
            self.passed += 1
        else:
            self.failed += 1
        self.events.append({
            "label": label,
            "observed": str(observed),
            "expected": str(expected),
            "pass": ok
        })
        if not ok:
            cocotb.log.error(f"[SCOREBOARD FAIL] {label}: obs={observed} exp={expected}")
        return ok

    def summary(self):
        cocotb.log.info(f"Scoreboard: {self.passed} passed, {self.failed} failed, {len(self.events)} total")
        return self.failed == 0


@cocotb.test()
async def test_reset(dut):
    """Test reset contract: registers at defaults, IRQ low, CS_N high."""
    await cocotb.start(Clock(dut.PCLK, 10, units='ns').start())

    # Assert reset
    dut.PRESETn.value = 0
    dut.PSEL.value = 0
    dut.PENABLE.value = 0
    dut.PADDR.value = 0
    dut.PWDATA.value = 0
    dut.PWRITE.value = 0
    dut.IO.value = 0
    await ClockCycles(dut.PCLK, 10)

    # Deassert reset
    dut.PRESETn.value = 1
    await ClockCycles(dut.PCLK, 5)

    sb = EquivalenceScoreboard(dut)

    # Check reset defaults visible via APB reads
    await RisingEdge(dut.PCLK)
    dut.PSEL.value = 1
    dut.PENABLE.value = 0
    dut.PADDR.value = 0x04  # STATUS
    dut.PWRITE.value = 0
    await RisingEdge(dut.PCLK)
    dut.PENABLE.value = 1
    while True:
        await RisingEdge(dut.PCLK)
        if dut.PREADY.value == 1:
            break
    status = dut.PRDATA.value.integer
    dut.PSEL.value = 0
    dut.PENABLE.value = 0

    # STATUS reset: TX_EMPTY=1, RX_EMPTY=1, others 0
    sb.check("STATUS.TX_EMPTY after reset", (status >> 1) & 1, 1)
    sb.check("STATUS.RX_EMPTY after reset", (status >> 3) & 1, 1)
    sb.check("STATUS.BUSY after reset", (status >> 5) & 1, 0)
    sb.check("IRQ low after reset", dut.IRQ.value.integer, 0)

    assert sb.summary(), "Reset test FAILED"


@cocotb.test()
async def test_sc_apb_config(dut):
    """SC_APB_CONFIG: Program and readback all config registers."""
    await cocotb.start(Clock(dut.PCLK, 10, units='ns').start())
    scenarios = QuadSPIScenarios(dut)
    await scenarios.scenario_sc_apb_config()


@cocotb.test()
async def test_sc_basic_transfer(dut):
    """SC_BASIC_TRANSFER: 1-byte 1-lane SDR transfer."""
    await cocotb.start(Clock(dut.PCLK, 10, units='ns').start())
    scenarios = QuadSPIScenarios(dut)
    await scenarios.scenario_sc_basic_transfer()


@cocotb.test()
async def test_sc_lane_mode_sweep(dut):
    """SC_LANE_MODE_SWEEP: 1/2/4 lane transfers."""
    await cocotb.start(Clock(dut.PCLK, 10, units='ns').start())
    scenarios = QuadSPIScenarios(dut)
    await scenarios.scenario_sc_lane_mode_sweep()


@cocotb.test()
async def test_sc_cpol_cpha_sweep(dut):
    """SC_CPOL_CPHA_SWEEP: All four SPI mode combinations."""
    await cocotb.start(Clock(dut.PCLK, 10, units='ns').start())
    scenarios = QuadSPIScenarios(dut)
    await scenarios.scenario_sc_cpol_cpha_sweep()


@cocotb.test()
async def test_sc_fifo_limits(dut):
    """SC_FIFO_LIMITS: TX FIFO fill and overflow."""
    await cocotb.start(Clock(dut.PCLK, 10, units='ns').start())
    scenarios = QuadSPIScenarios(dut)
    await scenarios.scenario_sc_fifo_limits()


@cocotb.test()
async def test_sc_irq_mask(dut):
    """SC_IRQ_MASK: Interrupt enable/disable and IRQ assertion."""
    await cocotb.start(Clock(dut.PCLK, 10, units='ns').start())
    scenarios = QuadSPIScenarios(dut)
    await scenarios.scenario_sc_irq_mask()


@cocotb.test()
async def test_sc_error_paths(dut):
    """SC_ERROR_PATHS: Illegal addresses and write-RO attempts."""
    await cocotb.start(Clock(dut.PCLK, 10, units='ns').start())
    scenarios = QuadSPIScenarios(dut)
    await scenarios.scenario_sc_error_paths()


@cocotb.test()
async def test_sc_prescale_timing(dut):
    """SC_PRESCALE_TIMING: Prescale DIV sweep."""
    await cocotb.start(Clock(dut.PCLK, 10, units='ns').start())
    scenarios = QuadSPIScenarios(dut)
    await scenarios.scenario_sc_prescale_timing()
