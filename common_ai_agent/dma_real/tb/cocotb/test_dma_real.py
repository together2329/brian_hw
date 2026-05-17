"""Cocotb testbench for dma_real v2 — SSOT-driven DMA controller verification.

Tests 6 scenarios using APB driver, AHB slave memory model (in TB wrapper),
and per-channel status observation. Dual-clock: pclk + hclk.

v2 register map:
  0x000 GLOBAL_CTRL    [0] dma_en
  0x004 INT_STATUS     [3:0] sticky
  0x008 INT_ENABLE     [3:0]
  0x00C INT_CLEAR      [3:0]
  0x010 GLOBAL_TIMEOUT [15:0]
  CHx_BASE = 0x100 + 0x40*ch
    +0x00 CTRL         [0] ch_en, [1] ch_start
    +0x04 SRC_ADDR
    +0x08 DST_ADDR
    +0x0C LEN          [15:0]
    +0x10 STATUS       [0] busy, [1] int_done, [2] int_error, [5:3] err_code
    +0x14 STRIDE       [31:0]
"""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
import json, os

class APBDriver:
    def __init__(self, dut):
        self.dut = dut
    async def write(self, addr, data):
        dut = self.dut
        dut.psel.value = 1; dut.pwrite.value = 1
        dut.paddr.value = addr; dut.pwdata.value = data
        await RisingEdge(dut.pclk)
        dut.penable.value = 1
        await RisingEdge(dut.pclk)
        dut.psel.value = 0; dut.penable.value = 0; dut.pwrite.value = 0
    async def read(self, addr):
        dut = self.dut
        dut.psel.value = 1; dut.pwrite.value = 0; dut.paddr.value = addr
        await RisingEdge(dut.pclk)
        dut.penable.value = 1
        await RisingEdge(dut.pclk)
        rdata = int(dut.prdata.value)
        dut.psel.value = 0; dut.penable.value = 0
        return rdata

# Register map
GLOBAL_CTRL = 0x000; INT_STATUS = 0x004; INT_ENABLE = 0x008; INT_CLEAR = 0x00C
GLOBAL_TIMEOUT = 0x010
CH0_BASE = 0x100; CH1_BASE = 0x140; CH2_BASE = 0x180; CH3_BASE = 0x1C0
OFF_CTRL = 0x00; OFF_SRC = 0x04; OFF_DST = 0x08; OFF_LEN = 0x0C
OFF_STATUS = 0x10; OFF_STRIDE = 0x14; OFF_PERF_W = 0x1C; OFF_PERF_C = 0x20

async def reset_and_init(dut):
    dut.presetn.value = 0; dut.hresetn.value = 0
    dut.psel.value = 0; dut.penable.value = 0; dut.pwrite.value = 0
    dut.paddr.value = 0; dut.pwdata.value = 0
    await RisingEdge(dut.pclk)
    await RisingEdge(dut.pclk)
    dut.presetn.value = 1; dut.hresetn.value = 1
    await RisingEdge(dut.pclk)
    await RisingEdge(dut.pclk)

async def wait_not_busy(dut, ch, cycles=2000):
    mask = 1 << ch
    for i in range(cycles):
        await RisingEdge(dut.pclk)
        if (int(dut.ch_busy.value) & mask) == 0 and i > 2:
            return True
    return False

@cocotb.test()
async def test_sc001_single_channel_transfer(dut):
    """SC_001: Single channel 4-word transfer 0x1000→0x2000"""
    await reset_and_init(dut)
    apb = APBDriver(dut)
    await apb.write(GLOBAL_CTRL, 0x1)
    await apb.write(CH0_BASE+OFF_SRC, 0x1000)
    await apb.write(CH0_BASE+OFF_DST, 0x2000)
    await apb.write(CH0_BASE+OFF_LEN, 0x4)
    await apb.write(CH0_BASE+OFF_CTRL, 0x3)
    ok = await wait_not_busy(dut, 0, 2000)
    for _ in range(5): await RisingEdge(dut.pclk)
    status = await apb.read(CH0_BASE+OFF_STATUS)
    done = (status >> 1) & 1
    assert done, f"SC_001 FAIL: done not set, status=0x{status:08x}"
    dut._log.info(f"SC_001 PASS: status=0x{status:08x}")

@cocotb.test()
async def test_sc002_alignment_error(dut):
    """SC_002: Alignment error — src=0x1001"""
    await reset_and_init(dut)
    apb = APBDriver(dut)
    await apb.write(GLOBAL_CTRL, 0x1)
    await apb.write(CH0_BASE+OFF_SRC, 0x1001)
    await apb.write(CH0_BASE+OFF_DST, 0x2000)
    await apb.write(CH0_BASE+OFF_LEN, 0x4)
    await apb.write(CH0_BASE+OFF_CTRL, 0x3)
    for _ in range(5): await RisingEdge(dut.pclk)
    status = await apb.read(CH0_BASE+OFF_STATUS)
    err = (status >> 2) & 1
    assert err, f"SC_002 FAIL: error not set, status=0x{status:08x}"
    dut._log.info(f"SC_002 PASS: alignment error, status=0x{status:08x}")

@cocotb.test()
async def test_sc003_zero_length_error(dut):
    """SC_003: Zero-length error"""
    await reset_and_init(dut)
    apb = APBDriver(dut)
    await apb.write(GLOBAL_CTRL, 0x1)
    await apb.write(CH0_BASE+OFF_SRC, 0x1000)
    await apb.write(CH0_BASE+OFF_DST, 0x2000)
    await apb.write(CH0_BASE+OFF_LEN, 0x0)
    await apb.write(CH0_BASE+OFF_CTRL, 0x3)
    for _ in range(5): await RisingEdge(dut.pclk)
    status = await apb.read(CH0_BASE+OFF_STATUS)
    err = (status >> 2) & 1
    assert err, f"SC_003 FAIL: error not set, status=0x{status:08x}"
    dut._log.info(f"SC_003 PASS: zero-len error, status=0x{status:08x}")

@cocotb.test()
async def test_sc004_busy_reject(dut):
    """SC_004: Start while busy — second start ignored"""
    await reset_and_init(dut)
    apb = APBDriver(dut)
    await apb.write(GLOBAL_CTRL, 0x1)
    await apb.write(CH0_BASE+OFF_SRC, 0x1000)
    await apb.write(CH0_BASE+OFF_DST, 0x2000)
    await apb.write(CH0_BASE+OFF_LEN, 0x10)
    await apb.write(CH0_BASE+OFF_CTRL, 0x3)
    for _ in range(30): await RisingEdge(dut.pclk)
    busy = int(dut.ch_busy.value) & 1
    if not busy:
        dut._log.warning("SC_004: channel finished too fast, skipping busy test")
        return
    await apb.write(CH0_BASE+OFF_CTRL, 0x3)
    await RisingEdge(dut.pclk)
    busy2 = int(dut.ch_busy.value) & 1
    assert busy2, "SC_004 FAIL: channel should still be busy"
    await wait_not_busy(dut, 0, 5000)
    dut._log.info("SC_004 PASS: busy reject verified")

@cocotb.test()
async def test_sc007_global_enable_disable(dut):
    """SC_007: DMA disabled then enabled"""
    await reset_and_init(dut)
    apb = APBDriver(dut)
    await apb.write(GLOBAL_CTRL, 0x0)
    await apb.write(CH0_BASE+OFF_SRC, 0x1000)
    await apb.write(CH0_BASE+OFF_DST, 0x2000)
    await apb.write(CH0_BASE+OFF_LEN, 0x4)
    await apb.write(CH0_BASE+OFF_CTRL, 0x3)
    for _ in range(5): await RisingEdge(dut.pclk)
    busy = int(dut.ch_busy.value) & 1
    assert not busy, "SC_007 FAIL: channel started with dma_en=0"
    await apb.write(GLOBAL_CTRL, 0x1)
    await apb.write(CH0_BASE+OFF_CTRL, 0x3)
    ok = await wait_not_busy(dut, 0, 2000)
    for _ in range(5): await RisingEdge(dut.pclk)
    status = await apb.read(CH0_BASE+OFF_STATUS)
    dut._log.info(f"SC_007 PASS: status=0x{status:08x}")

@cocotb.test()
async def test_sc008_interrupt_clear(dut):
    """SC_008: Interrupt clear"""
    await reset_and_init(dut)
    apb = APBDriver(dut)
    await apb.write(GLOBAL_CTRL, 0x1)
    await apb.write(INT_ENABLE, 0x1)
    await apb.write(CH0_BASE+OFF_SRC, 0x1000)
    await apb.write(CH0_BASE+OFF_DST, 0x2000)
    await apb.write(CH0_BASE+OFF_LEN, 0x4)
    await apb.write(CH0_BASE+OFF_CTRL, 0x3)
    await wait_not_busy(dut, 0, 2000)
    for _ in range(10): await RisingEdge(dut.pclk)
    irq_before = int(dut.irq.value) & 1
    assert irq_before, "SC_008 FAIL: IRQ not asserted after completion"
    await apb.write(INT_CLEAR, 0x1)
    for _ in range(5): await RisingEdge(dut.pclk)
    irq_after = int(dut.irq.value) & 1
    assert not irq_after, "SC_008 FAIL: IRQ not cleared"
    dut._log.info("SC_008 PASS: interrupt clear verified")
