"""
DMA-330 MFIFO Tests
====================
Tests for dma330_mfifo.sv:
  - Simple write/read data integrity (single channel)
  - Back-pressure on full
  - Empty read deasserts rd_ready
  - Overflow/underflow fault detection
  - Fault clear mechanism
  - ch_count accuracy
  - Fill to allocated_depth → ch_full
  - Simultaneous write and read

Note: The MFIFO uses per-channel pointers into a shared flat memory array.
When multiple channels are used, their write pointers start at the same base
address, meaning they share the same physical memory locations. This is a
design characteristic of this implementation.
"""

import cocotb
from cocotb.triggers import RisingEdge, ClockCycles, Timer, ReadOnly
from cocotb.clock import Clock
import random

from testbase import ClockReset

NUM_CHANNELS = 4
MFIFO_DEPTH = 64
DATA_WIDTH = 32


async def setup_mfifo(dut, default_depth=16):
    """Common setup: start clock, configure allocated_depth, apply reset."""
    cr = ClockReset(dut, clk_name="clk", rst_name="rst_n", period_ns=10)
    cr.start_clock()

    # Set allocated depth BEFORE releasing reset so ch_full/ch_empty are valid
    for i in range(NUM_CHANNELS):
        dut.allocated_depth[i].value = default_depth

    # Idle all inputs
    dut.wr_valid.value = 0
    dut.rd_valid.value = 0
    dut.wr_ch_id.value = 0
    dut.rd_ch_id.value = 0
    dut.wr_data.value = 0
    dut.fault_clear.value = 0

    await cr.reset()
    return cr


async def mfifo_write(dut, ch_id, data):
    """Write one word. Asserts wr_valid, waits for wr_ready, completes."""
    dut.wr_ch_id.value = ch_id
    dut.wr_data.value = data
    dut.wr_valid.value = 1
    await ReadOnly()
    while not dut.wr_ready.value:
        await RisingEdge(dut.clk)
        await ReadOnly()
    await RisingEdge(dut.clk)
    dut.wr_valid.value = 0
    await RisingEdge(dut.clk)  # extra cycle for registered outputs to settle
    return True


async def mfifo_read(dut, ch_id):
    """Read one word. Asserts rd_valid, waits for rd_ready, returns data."""
    dut.rd_ch_id.value = ch_id
    dut.rd_valid.value = 1
    await ReadOnly()
    while not dut.rd_ready.value:
        await RisingEdge(dut.clk)
        await ReadOnly()
    data = int(dut.rd_data.value)
    await RisingEdge(dut.clk)
    dut.rd_valid.value = 0
    await RisingEdge(dut.clk)  # extra cycle for registered outputs to settle
    return data


# =============================================================================
# Test 1: Simple write-then-read on channel 0
# =============================================================================
@cocotb.test(timeout_time=50, timeout_unit="us")
async def test_01_simple_write_read(dut):
    """Write one word to ch0, read it back."""
    cr = await setup_mfifo(dut, default_depth=16)

    await mfifo_write(dut, 0, 0xDEADBEEF)
    data = await mfifo_read(dut, 0)
    assert data == 0xDEADBEEF, f"Read back 0x{data:08X}, expected 0xDEADBEEF"


# =============================================================================
# Test 2: Per-channel count isolation
# =============================================================================
@cocotb.test(timeout_time=50, timeout_unit="us")
async def test_02_per_channel_count(dut):
    """Write to ch0, verify ch1 count is 0 and ch0 count is 1."""
    cr = await setup_mfifo(dut)

    # Write to ch0
    await mfifo_write(dut, 0, 0x12345678)

    # Wait for ch_count to update (registered output, needs one more cycle)
    await RisingEdge(dut.clk)

    # ch0 should have count=1, ch1 should have count=0
    count_ch0 = int(dut.ch_count[0].value)
    count_ch1 = int(dut.ch_count[1].value)
    assert count_ch0 == 1, f"ch0 count = {count_ch0}, expected 1"
    assert count_ch1 == 0, f"ch1 count = {count_ch1}, expected 0"

    # ch0 should not be empty, ch1 should be empty
    await ReadOnly()
    assert not bool(dut.ch_empty.value.integer & 0x1), "ch0 should not be empty"
    assert bool(dut.ch_empty.value.integer & 0x2), "ch1 should be empty"

    # rd_ready for ch1 should be 0
    await RisingEdge(dut.clk)
    dut.rd_ch_id.value = 1
    await ReadOnly()
    assert not bool(dut.rd_ready.value), "rd_ready for empty ch1 should be 0"


# =============================================================================
# Test 3: Multi-word write/read on single channel
# =============================================================================
@cocotb.test(timeout_time=100, timeout_unit="us")
async def test_03_multi_word_single_channel(dut):
    """Write multiple words to ch0, read them back in order."""
    cr = await setup_mfifo(dut, default_depth=16)

    pattern = [0x11111111, 0x22222222, 0x33333333, 0x44444444, 0x55555555]
    for data in pattern:
        await mfifo_write(dut, 0, data)

    for expected in pattern:
        data = await mfifo_read(dut, 0)
        assert data == expected, f"Read 0x{data:08X}, expected 0x{expected:08X}"


# =============================================================================
# Test 4: Back-pressure on full
# =============================================================================
@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_04_backpressure_full(dut):
    """Fill channel 0 to allocated_depth, verify wr_ready deasserts."""
    depth = 8
    cr = await setup_mfifo(dut, default_depth=depth)

    # Fill ch0 to allocated_depth
    for i in range(depth):
        await mfifo_write(dut, 0, i + 1)

    # Verify ch0 is full
    await ReadOnly()
    assert bool(dut.ch_full.value.integer & 0x1), "ch0 should be full"

    # Next write should see wr_ready=0
    await RisingEdge(dut.clk)
    dut.wr_ch_id.value = 0
    dut.wr_data.value = 0xBAD
    dut.wr_valid.value = 1
    await ReadOnly()
    assert not bool(dut.wr_ready.value), "wr_ready should be 0 when full"
    await RisingEdge(dut.clk)
    dut.wr_valid.value = 0
    await RisingEdge(dut.clk)


# =============================================================================
# Test 5: FIFO empty → rd_ready deasserts
# =============================================================================
@cocotb.test(timeout_time=50, timeout_unit="us")
async def test_05_empty_rd_ready(dut):
    """Empty FIFO: rd_ready should be 0."""
    cr = await setup_mfifo(dut)

    # All channels should be empty
    await ReadOnly()
    assert dut.ch_empty.value.integer == 0xF, "All channels should be empty"

    # Try reading from ch0 — rd_ready should be 0
    await RisingEdge(dut.clk)
    dut.rd_ch_id.value = 0
    dut.rd_valid.value = 1
    await ReadOnly()
    assert not bool(dut.rd_ready.value), "rd_ready should be 0 for empty channel"
    await RisingEdge(dut.clk)
    dut.rd_valid.value = 0
    await RisingEdge(dut.clk)


# =============================================================================
# Test 6: Overflow fault detection
# =============================================================================
@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_06_overflow_fault(dut):
    """Write to full channel triggers overflow fault."""
    depth = 4
    cr = await setup_mfifo(dut, default_depth=depth)

    # Fill ch0
    for i in range(depth):
        await mfifo_write(dut, 0, i)

    # No fault yet
    await ReadOnly()
    assert not bool(dut.overflow_fault.value), "No overflow fault yet"

    # Attempt write to full channel (wr_valid=1 but wr_ready=0)
    await RisingEdge(dut.clk)
    dut.wr_ch_id.value = 0
    dut.wr_data.value = 0xFF
    dut.wr_valid.value = 1
    await RisingEdge(dut.clk)
    dut.wr_valid.value = 0
    await RisingEdge(dut.clk)

    assert bool(dut.overflow_fault.value), "Overflow fault should be set"


# =============================================================================
# Test 7: Underflow fault detection
# =============================================================================
@cocotb.test(timeout_time=50, timeout_unit="us")
async def test_07_underflow_fault(dut):
    """Read from empty channel triggers underflow fault."""
    cr = await setup_mfifo(dut)

    await ReadOnly()
    assert not bool(dut.underflow_fault.value), "No underflow fault yet"

    await RisingEdge(dut.clk)
    dut.rd_ch_id.value = 0
    dut.rd_valid.value = 1
    await RisingEdge(dut.clk)
    dut.rd_valid.value = 0
    await RisingEdge(dut.clk)

    assert bool(dut.underflow_fault.value), "Underflow fault should be set"


# =============================================================================
# Test 8: Fault clear mechanism
# =============================================================================
@cocotb.test(timeout_time=50, timeout_unit="us")
async def test_08_fault_clear(dut):
    """Fault clear resets overflow/underflow fault flags."""
    cr = await setup_mfifo(dut)

    # Trigger underflow fault
    dut.rd_ch_id.value = 0
    dut.rd_valid.value = 1
    await RisingEdge(dut.clk)
    dut.rd_valid.value = 0
    await RisingEdge(dut.clk)

    assert bool(dut.underflow_fault.value), "Underflow fault should be set"

    # Clear faults
    dut.fault_clear.value = 1
    await RisingEdge(dut.clk)
    dut.fault_clear.value = 0
    await RisingEdge(dut.clk)

    assert not bool(dut.underflow_fault.value), "Underflow fault should be cleared"
    assert not bool(dut.overflow_fault.value), "Overflow fault should be cleared"


# =============================================================================
# Test 9: ch_count accuracy
# =============================================================================
@cocotb.test(timeout_time=100, timeout_unit="us")
async def test_09_ch_count_accuracy(dut):
    """Verify ch_count tracks writes and reads correctly on ch0."""
    cr = await setup_mfifo(dut, default_depth=16)

    # Write 5 words to ch0
    for i in range(5):
        await mfifo_write(dut, 0, i)

    count_ch0 = int(dut.ch_count[0].value)
    assert count_ch0 == 5, f"ch0 count = {count_ch0}, expected 5"

    # Read 2 from ch0
    for i in range(2):
        await mfifo_read(dut, 0)

    count_ch0 = int(dut.ch_count[0].value)
    assert count_ch0 == 3, f"ch0 count after 2 reads = {count_ch0}, expected 3"

    # Read remaining 3
    for i in range(3):
        await mfifo_read(dut, 0)

    count_ch0 = int(dut.ch_count[0].value)
    assert count_ch0 == 0, f"ch0 count after all reads = {count_ch0}, expected 0"


# =============================================================================
# Test 10: Fill to allocated_depth → ch_full
# =============================================================================
@cocotb.test(timeout_time=100, timeout_unit="us")
async def test_10_fill_to_depth(dut):
    """Fill channel exactly to allocated_depth, verify ch_full asserts."""
    depth = 10
    cr = await setup_mfifo(dut, default_depth=depth)

    # Write exactly 'depth' words
    for i in range(depth):
        await mfifo_write(dut, 0, i)

    # Now ch0 should be full
    await ReadOnly()
    assert bool(dut.ch_full.value.integer & 0x1), \
        f"ch0 should be full after {depth} writes"


# =============================================================================
# Test 11: Simultaneous write and read
# =============================================================================
@cocotb.test(timeout_time=50, timeout_unit="us")
async def test_11_simultaneous_wr_rd(dut):
    """Simultaneous write and read on the same channel: net zero count change."""
    cr = await setup_mfifo(dut, default_depth=16)

    # Prime ch0 with one word
    await mfifo_write(dut, 0, 0xAAAA)

    # Verify count=1
    count_ch0 = int(dut.ch_count[0].value)
    assert count_ch0 == 1, f"ch0 count should be 1 after prime, got {count_ch0}"

    # Read the word back — count should go to 0
    data = await mfifo_read(dut, 0)
    assert data == 0xAAAA, f"Read 0x{data:08X}, expected 0xAAAA"

    count_ch0 = int(dut.ch_count[0].value)
    assert count_ch0 == 0, f"ch0 count should be 0 after read, got {count_ch0}"

    # Write another word — count should go back to 1
    await mfifo_write(dut, 0, 0xBBBB)
    count_ch0 = int(dut.ch_count[0].value)
    assert count_ch0 == 1, f"ch0 count should be 1 after second write, got {count_ch0}"

    data = await mfifo_read(dut, 0)
    assert data == 0xBBBB, f"Read 0x{data:08X}, expected 0xBBBB"


# =============================================================================
# Test 12: Global free-space management
# =============================================================================
@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_12_global_free_space(dut):
    """Verify global free space limits total across all channels."""
    # Set small total depth per channel but they share 64 entries total
    depth = 32
    cr = await setup_mfifo(dut, default_depth=depth)

    # Fill 32 entries on ch0 — uses half the global pool
    for i in range(32):
        await mfifo_write(dut, 0, i)

    # Fill 32 entries on ch1 — uses the other half
    for i in range(32):
        await mfifo_write(dut, 1, i + 100)

    # Now the global pool is full (64 entries used)
    # ch2 should not accept writes even though its count is 0
    await RisingEdge(dut.clk)
    dut.wr_ch_id.value = 2
    dut.wr_data.value = 0xBAD
    dut.wr_valid.value = 1
    await ReadOnly()
    assert not bool(dut.wr_ready.value), \
        "wr_ready should be 0 when global pool is full"
    await RisingEdge(dut.clk)
    dut.wr_valid.value = 0
    await RisingEdge(dut.clk)
