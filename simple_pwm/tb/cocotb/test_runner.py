"""
simple_pwm cocotb testbench — FL-vs-RTL equivalence scoreboard

Tests all 4 SSOT scenarios:
  SC1: Basic PWM generation
  SC2: Duty cycle variation
  SC3: Period rollover
  SC4: Disable behavior

Compares RTL observed pwm_out against FunctionalModel expected results.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer, FallingEdge
import json
import os

# ============================================================================
# Functional Model (FL) — Python reference matching SSOT function_model
# ============================================================================
class PWMFunctionalModel:
    """Cycle-accurate Python model of simple_pwm."""

    def __init__(self, counter_width=8):
        self.counter_width = counter_width
        self.counter = 0
        self.pwm_out = 0

    def step(self, enable, duty_cycle, period):
        """Advance one clock cycle. Returns expected pwm_out."""
        if not enable:
            # FM3: pwm_idle
            self.counter = 0
            self.pwm_out = 0
        else:
            if self.counter < duty_cycle:
                # FM1: pwm_active_high
                self.pwm_out = 1
            else:
                # FM2: pwm_active_low
                self.pwm_out = 0
            # Counter update: wrap at period
            if self.counter >= period - 1:
                self.counter = 0
            else:
                self.counter += 1
        return self.pwm_out

    def reset(self):
        self.counter = 0
        self.pwm_out = 0


# ============================================================================
# Scoreboard
# ============================================================================
class Scoreboard:
    def __init__(self):
        self.events = []
        self.passed = 0
        self.failed = 0

    def compare(self, cycle, expected, actual, transaction, context=""):
        match = (expected == actual)
        event = {
            "cycle": cycle,
            "transaction": transaction,
            "expected_pwm_out": expected,
            "actual_pwm_out": actual,
            "match": match,
            "context": context
        }
        self.events.append(event)
        if match:
            self.passed += 1
        else:
            self.failed += 1
        return match

    def summary(self):
        total = self.passed + self.failed
        return {
            "total": total,
            "passed": self.passed,
            "failed": self.failed,
            "match_rate": f"{self.passed}/{total}"
        }


# ============================================================================
# DUT helpers
# ============================================================================
async def reset_dut(dut):
    """Apply reset."""
    dut.rst_n.value = 0
    dut.enable.value = 0
    dut.duty_cycle.value = 0
    dut.period.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


# ============================================================================
# Test SC1: Basic PWM generation
# ============================================================================
@cocotb.test()
async def test_basic_pwm(dut):
    """SC1: Basic PWM generation — period=10, duty_cycle=3."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    fl = PWMFunctionalModel(counter_width=8)
    sb = Scoreboard()

    await reset_dut(dut)
    fl.reset()

    dut.period.value = 10
    dut.duty_cycle.value = 3
    dut.enable.value = 1

    # Run 3 complete periods (30 cycles)
    for cycle in range(30):
        await RisingEdge(dut.clk)
        expected = fl.step(enable=1, duty_cycle=3, period=10)
        actual = int(dut.pwm_out.value)
        txn = "FM1" if fl.counter <= 3 else "FM2"
        sb.compare(cycle, expected, actual, txn, "SC1: period=10 duty=3")

    result = sb.summary()
    dut._log.info(f"SC1 result: {result}")
    assert result["failed"] == 0, f"SC1 FAILED: {result['failed']} mismatches"


# ============================================================================
# Test SC2: Duty cycle variation
# ============================================================================
@cocotb.test()
async def test_duty_variation(dut):
    """SC2: Duty cycle variation — change duty mid-run."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    fl = PWMFunctionalModel(counter_width=8)
    sb = Scoreboard()

    await reset_dut(dut)
    fl.reset()

    dut.period.value = 10
    dut.duty_cycle.value = 3
    dut.enable.value = 1

    # First period: duty=3
    for cycle in range(10):
        await RisingEdge(dut.clk)
        expected = fl.step(enable=1, duty_cycle=3, period=10)
        actual = int(dut.pwm_out.value)
        sb.compare(cycle, expected, actual, "FM1/FM2", "SC2: duty=3")

    # Change duty to 7
    dut.duty_cycle.value = 7

    # Second period: duty=7
    for cycle in range(10, 20):
        await RisingEdge(dut.clk)
        expected = fl.step(enable=1, duty_cycle=7, period=10)
        actual = int(dut.pwm_out.value)
        sb.compare(cycle, expected, actual, "FM1/FM2", "SC2: duty=7")

    result = sb.summary()
    dut._log.info(f"SC2 result: {result}")
    assert result["failed"] == 0, f"SC2 FAILED: {result['failed']} mismatches"


# ============================================================================
# Test SC3: Period rollover
# ============================================================================
@cocotb.test()
async def test_period_rollover(dut):
    """SC3: Period rollover — period=5, duty_cycle=2, verify counter wraps."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    fl = PWMFunctionalModel(counter_width=8)
    sb = Scoreboard()

    await reset_dut(dut)
    fl.reset()

    dut.period.value = 5
    dut.duty_cycle.value = 2
    dut.enable.value = 1

    # Run 3 complete periods (15 cycles)
    for cycle in range(15):
        await RisingEdge(dut.clk)
        expected = fl.step(enable=1, duty_cycle=2, period=5)
        actual = int(dut.pwm_out.value)
        sb.compare(cycle, expected, actual, "FM1/FM2", "SC3: period=5 duty=2")

    result = sb.summary()
    dut._log.info(f"SC3 result: {result}")
    assert result["failed"] == 0, f"SC3 FAILED: {result['failed']} mismatches"


# ============================================================================
# Test SC4: Disable behavior
# ============================================================================
@cocotb.test()
async def test_disable(dut):
    """SC4: Disable behavior — verify pwm_out=0 and counter=0 when disabled."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    fl = PWMFunctionalModel(counter_width=8)
    sb = Scoreboard()

    await reset_dut(dut)
    fl.reset()

    dut.period.value = 10
    dut.duty_cycle.value = 3

    # Phase 1: Enable for 5 clocks
    dut.enable.value = 1
    for cycle in range(5):
        await RisingEdge(dut.clk)
        expected = fl.step(enable=1, duty_cycle=3, period=10)
        actual = int(dut.pwm_out.value)
        sb.compare(cycle, expected, actual, "FM1/FM2", "SC4: enabled phase 1")

    # Phase 2: Disable for 5 clocks
    dut.enable.value = 0
    for cycle in range(5, 10):
        await RisingEdge(dut.clk)
        expected = fl.step(enable=0, duty_cycle=3, period=10)
        actual = int(dut.pwm_out.value)
        sb.compare(cycle, expected, actual, "FM3", "SC4: disabled")

    # Phase 3: Re-enable for 10 clocks
    dut.enable.value = 1
    for cycle in range(10, 20):
        await RisingEdge(dut.clk)
        expected = fl.step(enable=1, duty_cycle=3, period=10)
        actual = int(dut.pwm_out.value)
        sb.compare(cycle, expected, actual, "FM1/FM2", "SC4: re-enabled")

    result = sb.summary()
    dut._log.info(f"SC4 result: {result}")
    assert result["failed"] == 0, f"SC4 FAILED: {result['failed']} mismatches"
