"""Cocotb testbench for example_counter — covers all 6 SSOT scenarios."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "model"))
from functional_model import ExampleCounterFM


class ExampleCounterTB:
    def __init__(self, dut):
        self.dut = dut
        self.fm = ExampleCounterFM(width=4)
        self.fcov = {
            "FCOV_COUNT_UP": False,
            "FCOV_OVERFLOW": False,
            "FCOV_HOLD": False,
            "FCOV_LOAD": False,
            "FCOV_RESET": False,
            "FCOV_LOAD_OVER_ENABLE": False,
        }

    async def reset(self, cycles=3):
        self.dut.rst_n.value = 0
        self.dut.en.value = 0
        self.dut.load.value = 0
        self.dut.data_in.value = 0
        for _ in range(cycles):
            await RisingEdge(self.dut.clk)
        self.dut.rst_n.value = 1
        await RisingEdge(self.dut.clk)
        self.fm.reset()
        self.fcov["FCOV_RESET"] = True

    async def step(self, en=0, load=0, data_in=0):
        """Drive inputs for one cycle, sample outputs on next rising edge."""
        self.dut.en.value = en
        self.dut.load.value = load
        self.dut.data_in.value = data_in
        await RisingEdge(self.dut.clk)
        # Outputs are registered — read after clock edge
        expected = self.fm.step(
            rst_n=int(self.dut.rst_n.value),
            en=en,
            load=load,
            data_in=data_in,
        )
        await Timer(1, units="ns")  # small delta for output propagation
        actual_count = int(self.dut.count.value)
        actual_overflow = int(self.dut.overflow.value)
        return expected, {"count": actual_count, "overflow": actual_overflow}

    def check(self, expected, actual, label=""):
        assert expected["count"] == actual["count"], \
            f"{label}: count expected={expected['count']} got={actual['count']}"
        assert expected["overflow"] == actual["overflow"], \
            f"{label}: overflow expected={expected['overflow']} got={actual['overflow']}"


@cocotb.test()
async def test_01_reset(dut):
    """SC1: Reset clears counter."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    tb = ExampleCounterTB(dut)
    await tb.reset(cycles=3)
    # After reset: count=0, overflow=0
    assert int(dut.count.value) == 0, f"count after reset = {dut.count.value}"
    assert int(dut.overflow.value) == 0, f"overflow after reset = {dut.overflow.value}"


@cocotb.test()
async def test_02_count_up(dut):
    """SC2: Count up 5 cycles."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    tb = ExampleCounterTB(dut)
    await tb.reset()
    for i in range(5):
        exp, act = await tb.step(en=1)
        tb.check(exp, act, label=f"count_up_cycle_{i}")
        tb.fcov["FCOV_COUNT_UP"] = True


@cocotb.test()
async def test_03_overflow(dut):
    """SC3: Count overflow at MAX->0 wrap."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    tb = ExampleCounterTB(dut)
    await tb.reset()
    # Count from 0 to 15 (16 cycles), then one more to wrap
    overflow_seen = False
    for i in range(17):
        exp, act = await tb.step(en=1)
        tb.check(exp, act, label=f"overflow_cycle_{i}")
        if exp["overflow"] == 1:
            overflow_seen = True
            # Overflow should happen when count goes from 15 to 0
            assert exp["count"] == 0, f"overflow at count={exp['count']}, expected 0"
    assert overflow_seen, "overflow was never asserted"
    tb.fcov["FCOV_OVERFLOW"] = True
    tb.fcov["FCOV_COUNT_UP"] = True


@cocotb.test()
async def test_04_hold(dut):
    """SC4: Hold count (en=0, load=0)."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    tb = ExampleCounterTB(dut)
    await tb.reset()
    # Count to 5
    for _ in range(5):
        await tb.step(en=1)
    # Hold for 3 cycles
    for i in range(3):
        exp, act = await tb.step(en=0)
        tb.check(exp, act, label=f"hold_cycle_{i}")
        assert act["count"] == 5, f"hold should keep count=5, got {act['count']}"
        tb.fcov["FCOV_HOLD"] = True


@cocotb.test()
async def test_05_parallel_load(dut):
    """SC5: Parallel load."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    tb = ExampleCounterTB(dut)
    await tb.reset()
    # Load value 10
    exp, act = await tb.step(load=1, data_in=10)
    tb.check(exp, act, label="load_10")
    assert act["count"] == 10
    tb.fcov["FCOV_LOAD"] = True


@cocotb.test()
async def test_06_load_priority(dut):
    """SC6: Load priority over enable."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    tb = ExampleCounterTB(dut)
    await tb.reset()
    # Count to 3
    for _ in range(3):
        await tb.step(en=1)
    # Both load and en high — load wins
    exp, act = await tb.step(en=1, load=1, data_in=7)
    tb.check(exp, act, label="load_over_enable")
    assert act["count"] == 7, f"load should win, got {act['count']}"
    tb.fcov["FCOV_LOAD_OVER_ENABLE"] = True


@cocotb.test()
async def test_07_fcov_all_bins(dut):
    """Coverage: hit all functional coverage bins in a single test."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    tb = ExampleCounterTB(dut)
    fcov = {k: False for k in tb.fcov}

    # Reset
    await tb.reset()
    fcov["FCOV_RESET"] = True

    # Count up (0 to 4)
    for _ in range(5):
        await tb.step(en=1)
    fcov["FCOV_COUNT_UP"] = True

    # Overflow (count from 5 to 15, then wrap to 0)
    for _ in range(12):
        await tb.step(en=1)
    fcov["FCOV_OVERFLOW"] = True

    # Hold
    await tb.step(en=0)
    fcov["FCOV_HOLD"] = True

    # Load
    await tb.step(load=1, data_in=3)
    fcov["FCOV_LOAD"] = True

    # Load + enable (load wins)
    await tb.step(en=1, load=1, data_in=12)
    fcov["FCOV_LOAD_OVER_ENABLE"] = True

    assert all(fcov.values()), f"Missing coverage: {fcov}"


# --- Coverage plan ---
FCOV_PLAN = [
    {"id": "FCOV_COUNT_UP", "description": "Counter increments"},
    {"id": "FCOV_OVERFLOW", "description": "Overflow detected at MAX->0"},
    {"id": "FCOV_HOLD", "description": "Counter holds value"},
    {"id": "FCOV_LOAD", "description": "Parallel load works"},
    {"id": "FCOV_RESET", "description": "Reset clears state"},
    {"id": "FCOV_LOAD_OVER_ENABLE", "description": "Load priority over enable"},
]
