"""
DMA-330 IRQ Controller Tests
==============================
Tests for dma330_irq_controller.sv:
  - Reset state
  - Event set (INT_EVENT_RIS)
  - INTEN masking → INTMIS
  - INTCLR write-to-clear
  - Fault sticky + fault IRQ
  - Multiple concurrent events
"""

import cocotb
from cocotb.triggers import RisingEdge, ClockCycles, Timer
from cocotb.clock import Clock
import random

from testbase import ClockReset

NUM_EVENTS = 8


async def setup(dut):
    """Common setup: start clock, apply reset, idle inputs."""
    cr = ClockReset(dut, period_ns=10)
    cr.start_clock()
    # Idle all inputs
    dut.event_i.value = 0
    dut.fault_i.value = 0
    dut.inten_wdata.value = 0
    dut.inten_we.value = 0
    dut.intclr_wdata.value = 0
    dut.intclr_we.value = 0
    await cr.reset()
    return cr


# =============================================================================
# Test 1: Reset state — all registers zero, irq_o = 0
# =============================================================================
@cocotb.test(timeout_time=50, timeout_unit="us")
async def test_01_reset_state(dut):
    """Verify reset state: all outputs zero."""
    cr = await setup(dut)

    assert dut.int_event_ris_o.value.integer == 0, \
        f"RIS not zero after reset: {dut.int_event_ris_o.value.integer}"
    assert dut.intmis_o.value.integer == 0, \
        f"INTMIS not zero after reset: {dut.intmis_o.value.integer}"
    assert dut.irq_o.value.integer == 0, \
        f"irq_o not zero after reset: {dut.irq_o.value.integer}"


# =============================================================================
# Test 2: Event pulse sets INT_EVENT_RIS bit
# =============================================================================
@cocotb.test(timeout_time=50, timeout_unit="us")
async def test_02_event_set_ris(dut):
    """Event pulse sets corresponding INT_EVENT_RIS bit."""
    cr = await setup(dut)

    # Pulse event bit 2
    dut.event_i.value = 0x04
    await RisingEdge(dut.clk)
    dut.event_i.value = 0
    await RisingEdge(dut.clk)

    ris = dut.int_event_ris_o.value.integer
    assert ris & 0x04, f"Expected bit 2 set in RIS, got 0x{ris:08x}"

    # Pulse event bit 5 (should accumulate)
    dut.event_i.value = 0x20
    await RisingEdge(dut.clk)
    dut.event_i.value = 0
    await RisingEdge(dut.clk)

    ris = dut.int_event_ris_o.value.integer
    assert ris & 0x24, f"Expected bits 2 and 5 set in RIS, got 0x{ris:08x}"


# =============================================================================
# Test 3 & 4: INTEN masking → INTMIS = RIS & INTEN
# =============================================================================
@cocotb.test(timeout_time=50, timeout_unit="us")
async def test_03_inten_masking(dut):
    """INTMIS = INT_EVENT_RIS & INTEN."""
    cr = await setup(dut)

    # Set event bits 0, 3, 7
    for bit in [0, 3, 7]:
        dut.event_i.value = 1 << bit
        await RisingEdge(dut.clk)
        dut.event_i.value = 0
        await RisingEdge(dut.clk)

    ris = dut.int_event_ris_o.value.integer
    expected_ris = (1 << 0) | (1 << 3) | (1 << 7)
    assert ris == expected_ris, f"RIS=0x{ris:02x}, expected 0x{expected_ris:02x}"

    # INTMIS should be 0 (no INTEN set yet)
    assert dut.intmis_o.value.integer == 0, "INTMIS should be 0 without INTEN"

    # Write INTEN = bits 0, 7
    dut.inten_wdata.value = 0x81  # bits 0 and 7
    dut.inten_we.value = 1
    await RisingEdge(dut.clk)
    dut.inten_we.value = 0
    await RisingEdge(dut.clk)

    intmis = dut.intmis_o.value.integer
    expected_mis = expected_ris & 0x81  # = 0x81
    assert intmis == expected_mis, \
        f"INTMIS=0x{intmis:02x}, expected 0x{expected_mis:02x}"

    # IRQ outputs should reflect INTMIS for event bits
    irq = dut.irq_o.value.integer
    assert (irq & 0xFF) == expected_mis, \
        f"irq_o event bits=0x{irq & 0xFF:02x}, expected 0x{expected_mis:02x}"


# =============================================================================
# Test 5: INTCLR write-to-clear clears RIS bits
# =============================================================================
@cocotb.test(timeout_time=50, timeout_unit="us")
async def test_04_intclr_w1c(dut):
    """INTCLR write-to-clear clears RIS bits."""
    cr = await setup(dut)

    # Set bits 1, 3, 5
    dut.event_i.value = (1 << 1) | (1 << 3) | (1 << 5)
    await RisingEdge(dut.clk)
    dut.event_i.value = 0
    await RisingEdge(dut.clk)

    ris_before = dut.int_event_ris_o.value.integer
    assert ris_before == 0x2A, f"RIS before clear = 0x{ris_before:02x}"

    # Clear bit 3
    dut.intclr_wdata.value = 0x08  # bit 3
    dut.intclr_we.value = 1
    await RisingEdge(dut.clk)
    dut.intclr_we.value = 0
    await RisingEdge(dut.clk)

    ris_after = dut.int_event_ris_o.value.integer
    assert ris_after == 0x22, f"RIS after clearing bit 3 = 0x{ris_after:02x}, expected 0x22"


# =============================================================================
# Test 6: Fault input sets fault_ris sticky, irq_o[NUM_EVENTS] = 1
# =============================================================================
@cocotb.test(timeout_time=50, timeout_unit="us")
async def test_05_fault_sticky(dut):
    """Fault input sets sticky fault bit, irq_o[NUM_EVENTS] = 1."""
    cr = await setup(dut)

    # Assert fault for one cycle
    dut.fault_i.value = 1
    await RisingEdge(dut.clk)
    dut.fault_i.value = 0
    await RisingEdge(dut.clk)

    # Fault IRQ should be set (bit NUM_EVENTS)
    irq = dut.irq_o.value.integer
    assert irq & (1 << NUM_EVENTS), \
        f"Fault IRQ (bit {NUM_EVENTS}) not set, irq=0x{irq:03x}"

    # Fault should be sticky — check it persists
    await ClockCycles(dut.clk, 5)
    irq = dut.irq_o.value.integer
    assert irq & (1 << NUM_EVENTS), \
        f"Fault IRQ not sticky after 5 cycles, irq=0x{irq:03x}"


# =============================================================================
# Test 7: Fault clear via intclr bit NUM_EVENTS
# =============================================================================
@cocotb.test(timeout_time=50, timeout_unit="us")
async def test_06_fault_clear(dut):
    """Fault clear via intclr write to bit NUM_EVENTS."""
    cr = await setup(dut)

    # Trigger fault
    dut.fault_i.value = 1
    await RisingEdge(dut.clk)
    dut.fault_i.value = 0
    await RisingEdge(dut.clk)

    assert dut.irq_o.value.integer & (1 << NUM_EVENTS), "Fault not set"

    # Clear fault via intclr
    dut.intclr_wdata.value = 1 << NUM_EVENTS
    dut.intclr_we.value = 1
    await RisingEdge(dut.clk)
    dut.intclr_we.value = 0
    await RisingEdge(dut.clk)

    irq = dut.irq_o.value.integer
    assert not (irq & (1 << NUM_EVENTS)), \
        f"Fault IRQ still set after clear, irq=0x{irq:03x}"


# =============================================================================
# Test 8: Multiple simultaneous events
# =============================================================================
@cocotb.test(timeout_time=50, timeout_unit="us")
async def test_07_multiple_events(dut):
    """Multiple simultaneous events set all corresponding RIS bits."""
    cr = await setup(dut)

    # Assert all event bits simultaneously
    all_events = (1 << NUM_EVENTS) - 1  # 0xFF
    dut.event_i.value = all_events
    await RisingEdge(dut.clk)
    dut.event_i.value = 0
    await RisingEdge(dut.clk)

    ris = dut.int_event_ris_o.value.integer
    assert ris == all_events, \
        f"All-event RIS=0x{ris:02x}, expected 0x{all_events:02x}"

    # Enable all → all should be in INTMIS
    dut.inten_wdata.value = all_events
    dut.inten_we.value = 1
    await RisingEdge(dut.clk)
    dut.inten_we.value = 0
    await RisingEdge(dut.clk)

    intmis = dut.intmis_o.value.integer
    assert intmis == all_events, \
        f"INTMIS=0x{intmis:02x}, expected 0x{all_events:02x}"


# =============================================================================
# Test 9: Random event/enable/clear sequences
# =============================================================================
@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_08_random_stress(dut):
    """Randomized stress: random events, enables, clears."""
    cr = await setup(dut)
    rng = random.Random(42)

    expected_ris = 0
    expected_inten = 0

    for _ in range(200):
        # Random event pulse
        event = rng.randint(0, (1 << NUM_EVENTS) - 1)
        dut.event_i.value = event
        await RisingEdge(dut.clk)
        dut.event_i.value = 0

        expected_ris |= event

        # Random INTEN write
        if rng.random() < 0.1:
            expected_inten = rng.randint(0, (1 << NUM_EVENTS) - 1)
            dut.inten_wdata.value = expected_inten
            dut.inten_we.value = 1
            await RisingEdge(dut.clk)
            dut.inten_we.value = 0

        # Random INTCLR write
        if rng.random() < 0.1:
            clear_mask = rng.randint(0, (1 << NUM_EVENTS) - 1)
            dut.intclr_wdata.value = clear_mask
            dut.intclr_we.value = 1
            await RisingEdge(dut.clk)
            dut.intclr_we.value = 0
            expected_ris &= ~clear_mask

        await RisingEdge(dut.clk)

        # Verify RIS
        actual_ris = dut.int_event_ris_o.value.integer
        assert actual_ris == expected_ris & ((1 << NUM_EVENTS) - 1), \
            f"RIS mismatch: got 0x{actual_ris:02x}, expected 0x{expected_ris & 0xFF:02x}"

        # Verify INTMIS
        actual_inten = dut.intmis_o.value.integer
        expected_mis = expected_ris & expected_inten & ((1 << NUM_EVENTS) - 1)
        assert actual_inten == expected_mis, \
            f"INTMIS mismatch: got 0x{actual_inten:02x}, expected 0x{expected_mis:02x}"
