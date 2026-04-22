"""
DMA-330 Peripheral Interface Tests
====================================
Tests for dma330_periph_intf.sv:
  - Per-peripheral state machine (IDLE → REQUESTED → ACKNOWLEDGED)
  - 2-flop synchronizer latency for dmareq_i (2 sync cycles + 1 FSM reaction = 3 total)
  - Round-robin arbitration for multi-channel → same peripheral
  - DMAFLUSHP clears state
  - Ack routing from peripheral back to owning channel

Timing note:
  dmareq_i is async, goes through 2-flop sync:
    Cycle 0: dmareq_i asserted (set after RisingEdge)
    Cycle 1: dmareq_meta <= dmareq_i (at RisingEdge)
    Cycle 2: dmareq_sync <= dmareq_meta (at RisingEdge)
    Cycle 3: FSM sees dmareq_sync = 1 → transitions to ACKNOWLEDGED (at RisingEdge)
  Total: 3 RisingEdges from setting dmareq_i to ACKNOWLEDGED state being visible.
"""

import cocotb
from cocotb.triggers import RisingEdge, ReadOnly, ClockCycles
from testbase import ClockReset

NUM_CH = 4
NUM_PERIPH = 4


async def setup_periph(dut):
    """Common setup: start clock, reset, clear all inputs."""
    cr = ClockReset(dut, clk_name="clk", rst_name="rst_n", period_ns=10)
    cr.start_clock()
    dut.dmareq_i.value = 0
    dut.ch_periph_req_i.value = 0
    dut.ch_periph_ack_i.value = 0
    dut.flush_req_i.value = 0
    dut.flush_periph_num_i.value = 0
    # Set default per-channel peripheral number mapping:
    # ch0->periph0, ch1->periph1, ch2->periph2, ch3->periph3
    for ch in range(NUM_CH):
        _set_periph_num(dut, ch, ch)
    await cr.reset()
    return cr


def _set_periph_num(dut, ch, periph):
    """Set ch_periph_num for a channel (handles unpacked array access)."""
    try:
        dut.ch_periph_num[ch].value = periph
    except (AttributeError, TypeError, KeyError, IndexError):
        getattr(dut, f"ch_periph_num_{ch}").value = periph


async def drive_to_requested(dut, channel, periph):
    """Drive a channel request and wait until peripheral is in REQUESTED state."""
    dut.ch_periph_req_i.value = (1 << channel)
    await RisingEdge(dut.clk)  # FSM sees request
    await RisingEdge(dut.clk)  # State transitions to REQUESTED


async def drive_to_acknowledged(dut, periph):
    """Assert dmareq for a peripheral and wait until ACKNOWLEDGED (3 cycles)."""
    dut.dmareq_i.value = (1 << periph)
    await RisingEdge(dut.clk)  # cycle 1: dmareq_meta updated
    await RisingEdge(dut.clk)  # cycle 2: dmareq_sync updated
    await RisingEdge(dut.clk)  # cycle 3: FSM transitions to ACKNOWLEDGED


# =============================================================================
# Test 1: Reset state
# =============================================================================
@cocotb.test(timeout_time=100, timeout_unit="us")
async def test_01_reset(dut):
    """After reset: all peripherals IDLE, dmaack_o=0, ch_periph_ack_o=0."""
    cr = await setup_periph(dut)

    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.dmaack_o.value == 0, f"dmaack_o={int(dut.dmaack_o.value)}, expected 0"
    assert dut.ch_periph_ack_o.value == 0, f"ch_periph_ack_o={int(dut.ch_periph_ack_o.value)}, expected 0"


# =============================================================================
# Test 2: IDLE → REQUESTED when channel requests
# =============================================================================
@cocotb.test(timeout_time=100, timeout_unit="us")
async def test_02_idle_to_requested(dut):
    """Channel requests peripheral -> state transitions to REQUESTED."""
    cr = await setup_periph(dut)

    await drive_to_requested(dut, 0, 0)
    await ReadOnly()
    # Should NOT be acknowledged yet (no dmareq)
    assert int(dut.dmaack_o.value) == 0, "dmaack_o should be 0 in REQUESTED state"

    # Cleanup
    await RisingEdge(dut.clk)
    dut.ch_periph_req_i.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)


# =============================================================================
# Test 3: REQUESTED → ACKNOWLEDGED with 2-flop sync latency
# =============================================================================
@cocotb.test(timeout_time=100, timeout_unit="us")
async def test_03_requested_to_acknowledged(dut):
    """dmareq assertion -> 2-flop sync -> REQUESTED->ACKNOWLEDGED (3 cycle total)."""
    cr = await setup_periph(dut)

    # Get to REQUESTED
    await drive_to_requested(dut, 0, 0)

    # Assert dmareq and wait for ACKNOWLEDGED
    await drive_to_acknowledged(dut, 0)
    await ReadOnly()
    assert int(dut.dmaack_o.value) & 1, "Should be ACKNOWLEDGED after 3 cycles"

    # Cleanup
    await RisingEdge(dut.clk)
    dut.ch_periph_req_i.value = 0
    dut.dmareq_i.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)


# =============================================================================
# Test 4: dmaack_o asserted in ACKNOWLEDGED state
# =============================================================================
@cocotb.test(timeout_time=100, timeout_unit="us")
async def test_04_dmaack_output(dut):
    """dmaack_o[periph] = 1 when peripheral is in ACKNOWLEDGED state."""
    cr = await setup_periph(dut)

    await drive_to_requested(dut, 0, 0)
    await drive_to_acknowledged(dut, 0)
    await ReadOnly()

    ack = int(dut.dmaack_o.value)
    assert ack & (1 << 0), f"dmaack_o[0] should be 1, got dmaack_o=0x{ack:x}"
    assert not (ack & ~1), f"Only periph 0 should have ack, got 0x{ack:x}"

    # Cleanup
    await RisingEdge(dut.clk)
    dut.ch_periph_req_i.value = 0
    dut.dmareq_i.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)


# =============================================================================
# Test 5: ch_periph_ack_o routing to owning channel
# =============================================================================
@cocotb.test(timeout_time=100, timeout_unit="us")
async def test_05_ack_routing(dut):
    """ch_periph_ack_o[ch] = 1 when peripheral owned by ch is ACKNOWLEDGED."""
    cr = await setup_periph(dut)

    # Remap: ch2 → periph1
    _set_periph_num(dut, 2, 1)

    # Channel 2 requests peripheral 1
    await drive_to_requested(dut, 2, 1)
    await drive_to_acknowledged(dut, 1)
    await ReadOnly()

    ch_ack = int(dut.ch_periph_ack_o.value)
    assert ch_ack & (1 << 2), f"ch_periph_ack_o[2] should be 1, got 0x{ch_ack:x}"
    assert not (ch_ack & ~(1 << 2)), f"Only ch2 should have ack, got 0x{ch_ack:x}"

    # Cleanup
    await RisingEdge(dut.clk)
    dut.ch_periph_req_i.value = 0
    dut.dmareq_i.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)


# =============================================================================
# Test 6: ACKNOWLEDGED → IDLE when channel deasserts
# =============================================================================
@cocotb.test(timeout_time=100, timeout_unit="us")
async def test_06_ack_to_idle(dut):
    """Channel deasserts request -> ACKNOWLEDGED->IDLE, ack clears."""
    cr = await setup_periph(dut)

    await drive_to_requested(dut, 0, 0)
    await drive_to_acknowledged(dut, 0)
    await ReadOnly()
    assert int(dut.dmaack_o.value) & 1, "Should be ACKNOWLEDGED"

    # Channel deasserts
    await RisingEdge(dut.clk)
    dut.ch_periph_req_i.value = 0
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.dmaack_o.value) == 0, f"dmaack_o should be 0 after deassert, got {int(dut.dmaack_o.value)}"

    # Cleanup (exit ReadOnly before writing)
    await RisingEdge(dut.clk)
    dut.dmareq_i.value = 0
    await RisingEdge(dut.clk)


# =============================================================================
# Test 7: Round-robin arbitration
# =============================================================================
@cocotb.test(timeout_time=100, timeout_unit="us")
async def test_07_round_robin(dut):
    """Multiple channels request same peripheral -> round-robin selection."""
    cr = await setup_periph(dut)

    # Remap all channels to periph 0
    for ch in range(NUM_CH):
        _set_periph_num(dut, ch, 0)

    # --- Round 1: ch0 and ch1 request periph 0 ---
    await RisingEdge(dut.clk)
    dut.ch_periph_req_i.value = (1 << 0) | (1 << 1)  # ch0 + ch1
    await RisingEdge(dut.clk)  # FSM sees requests -> REQUESTED

    # Assert dmareq for periph 0 and wait for ACK
    await drive_to_acknowledged(dut, 0)
    await ReadOnly()
    # RR starts at 0, so ch0 should win first
    ch_ack = int(dut.ch_periph_ack_o.value)
    assert ch_ack & (1 << 0), f"Round 1: ch0 should win, ack=0x{ch_ack:x}"

    # Deassert ch0, keep ch1 requesting
    await RisingEdge(dut.clk)
    dut.ch_periph_req_i.value = (1 << 1)  # keep ch1
    dut.dmareq_i.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)  # ACKNOWLEDGED -> IDLE

    # --- Round 2: ch1 still requesting -> should get periph 0 ---
    await drive_to_acknowledged(dut, 0)
    await ReadOnly()
    ch_ack = int(dut.ch_periph_ack_o.value)
    assert ch_ack & (1 << 1), f"Round 2: ch1 should get ack, ack=0x{ch_ack:x}"

    # Cleanup
    await RisingEdge(dut.clk)
    dut.ch_periph_req_i.value = 0
    dut.dmareq_i.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)


# =============================================================================
# Test 8: DMAFLUSHP clears peripheral state
# =============================================================================
@cocotb.test(timeout_time=100, timeout_unit="us")
async def test_08_flush(dut):
    """DMAFLUSHP clears peripheral state from ACKNOWLEDGED to IDLE."""
    cr = await setup_periph(dut)

    # Get periph 0 to ACKNOWLEDGED
    await drive_to_requested(dut, 0, 0)
    await drive_to_acknowledged(dut, 0)
    await ReadOnly()
    assert int(dut.dmaack_o.value) & 1, "Should be ACKNOWLEDGED before flush"

    # Issue DMAFLUSHP for periph 0
    await RisingEdge(dut.clk)
    dut.flush_req_i.value = 1
    dut.flush_periph_num_i.value = 0
    await RisingEdge(dut.clk)
    await ReadOnly()
    # State should be cleared to IDLE
    assert int(dut.dmaack_o.value) == 0, f"dmaack_o should be 0 after flush, got {int(dut.dmaack_o.value)}"

    # Cleanup
    await RisingEdge(dut.clk)
    dut.flush_req_i.value = 0
    dut.ch_periph_req_i.value = 0
    dut.dmareq_i.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)


# =============================================================================
# Test 9: 2-flop synchronizer latency (detailed cycle-by-cycle check)
# =============================================================================
@cocotb.test(timeout_time=100, timeout_unit="us")
async def test_09_sync_latency(dut):
    """Verify dmareq_i takes exactly 3 clock cycles to reach ACKNOWLEDGED."""
    cr = await setup_periph(dut)

    # Get periph 0 to REQUESTED state
    await drive_to_requested(dut, 0, 0)

    # Assert dmareq_i[0]
    await RisingEdge(dut.clk)
    dut.dmareq_i.value = (1 << 0)

    # Cycle 1: dmareq_meta gets the value
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.dmaack_o.value) == 0, "NOT ACKNOWLEDGED at cycle 1"

    # Cycle 2: dmareq_sync gets the value
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.dmaack_o.value) == 0, "NOT ACKNOWLEDGED at cycle 2 (sync updated, FSM hasn't reacted)"

    # Cycle 3: FSM sees dmareq_sync = 1 and transitions
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.dmaack_o.value) & 1, "ACKNOWLEDGED at cycle 3"

    # Cleanup
    await RisingEdge(dut.clk)
    dut.ch_periph_req_i.value = 0
    dut.dmareq_i.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)


# =============================================================================
# Test 10: Multiple peripherals simultaneously
# =============================================================================
@cocotb.test(timeout_time=100, timeout_unit="us")
async def test_10_multiple_periphs(dut):
    """Two channels request two different peripherals simultaneously."""
    cr = await setup_periph(dut)

    # ch0->periph0, ch1->periph1 (default mapping)
    await RisingEdge(dut.clk)
    dut.ch_periph_req_i.value = (1 << 0) | (1 << 1)
    await RisingEdge(dut.clk)  # Both transition to REQUESTED

    # Assert dmareq for both peripherals
    dut.dmareq_i.value = (1 << 0) | (1 << 1)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await ReadOnly()

    ack = int(dut.dmaack_o.value)
    assert ack & (1 << 0), f"periph 0 ack should be set, dmaack_o=0x{ack:x}"
    assert ack & (1 << 1), f"periph 1 ack should be set, dmaack_o=0x{ack:x}"

    ch_ack = int(dut.ch_periph_ack_o.value)
    assert ch_ack & (1 << 0), f"ch0 ack should be set, ch_ack=0x{ch_ack:x}"
    assert ch_ack & (1 << 1), f"ch1 ack should be set, ch_ack=0x{ch_ack:x}"

    # Cleanup
    await RisingEdge(dut.clk)
    dut.ch_periph_req_i.value = 0
    dut.dmareq_i.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
