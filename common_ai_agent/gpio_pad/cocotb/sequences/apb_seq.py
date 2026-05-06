
# ============================================================================
# apb_seq.py — APB Sequence Library
# ============================================================================
import cocotb
from cocotb.triggers import RisingEdge, ClockCycles
from pyuvm import *
from agent.apb_agent import ApbSeqItem


# ============================================================================
# Register Address Constants (from SSOT §9)
# ============================================================================
ADDR_DIR      = 0x000
ADDR_OUT      = 0x004
ADDR_IN       = 0x008
ADDR_INTEN    = 0x00C
ADDR_INTSTAT  = 0x010
ADDR_INTCLEAR = 0x014


class ApbWriteSeq(uvm_sequence):
    """Write a value to an APB register."""
    def __init__(self, name="ApbWriteSeq"):
        super().__init__(name)
        self.addr = 0
        self.data = 0

    async def body(self):
        item = ApbSeqItem("write_item")
        item.addr = self.addr
        item.data = self.data
        item.write = True
        await self.start_item(item)
        await self.finish_item(item)


class ApbReadSeq(uvm_sequence):
    """Read from an APB register. Result stored in self.data after body()."""
    def __init__(self, name="ApbReadSeq"):
        super().__init__(name)
        self.addr = 0
        self.data = 0

    async def body(self):
        item = ApbSeqItem("read_item")
        item.addr = self.addr
        item.write = False
        item.data = 0
        await self.start_item(item)
        await self.finish_item(item)
        # Driver sets item.data with read result
        self.data = item.data


class ApbPollSeq(uvm_sequence):
    """Poll a register until it matches expected value or timeout."""
    def __init__(self, name="ApbPollSeq"):
        super().__init__(name)
        self.addr = 0
        self.expected = 0
        self.mask = 0xFFFFFFFF
        self.timeout_cycles = 100

    async def body(self):
        for _ in range(self.timeout_cycles):
            read_seq = ApbReadSeq("poll_read")
            read_seq.addr = self.addr
            await read_seq.start(self.m_sequencer)
            if (read_seq.data & self.mask) == (self.expected & self.mask):
                self.data = read_seq.data
                return
            await ClockCycles(cocotb.top.pclk, 1)
        self.logger.error(f"Poll timeout: addr=0x{self.addr:03X} expected=0x{self.expected:08X}")
        self.data = 0


class ApbResetSeq(uvm_sequence):
    """Assert and deassert reset."""
    def __init__(self, name="ApbResetSeq"):
        super().__init__(name)
        self.hold_cycles = 5

    async def body(self):
        dut = cocotb.top
        dut.presetn.value = 0
        await ClockCycles(dut.pclk, self.hold_cycles)
        dut.presetn.value = 1
        await ClockCycles(dut.pclk, 3)


# ============================================================================
# Convenience: High-level APB access via sequencer handle
# ============================================================================
async def apb_write(sequencer, addr, data):
    """Helper: write register via sequencer."""
    seq = ApbWriteSeq("wr")
    seq.addr = addr
    seq.data = data
    await seq.start(sequencer)


async def apb_read(sequencer, addr):
    """Helper: read register via sequencer, return data."""
    seq = ApbReadSeq("rd")
    seq.addr = addr
    await seq.start(sequencer)
    return seq.data
