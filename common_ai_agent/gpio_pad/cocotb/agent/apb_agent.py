
# ============================================================================
# apb_agent.py — APB UVM Agent (Driver + Monitor + Sequencer)
# ============================================================================
import cocotb
from cocotb.triggers import RisingEdge, ClockCycles, Event
from cocotb.binary import BinaryValue
from pyuvm import *
import random

# ============================================================================
# APB Transaction
# ============================================================================
class ApbTransaction(uvm_sequence_item):
    """APB bus transaction item."""
    def __init__(self, name="ApbTransaction"):
        super().__init__(name)
        self.addr = 0      # 12-bit address
        self.data = 0      # 32-bit data
        self.write = True  # True=write, False=read
        self.strb = 0xF    # byte strobes

    def __str__(self):
        op = "WR" if self.write else "RD"
        return f"APB {op} addr=0x{self.addr:03X} data=0x{self.data:08X}"


# ============================================================================
# APB Sequence Item (minimal, compatible with pyuvm)
# ============================================================================
class ApbSeqItem(uvm_sequence_item):
    """Simple APB item for sequencer."""
    def __init__(self, name="ApbSeqItem"):
        super().__init__(name)
        self.addr = 0
        self.data = 0
        self.write = True

    def __str__(self):
        op = "WR" if self.write else "RD"
        return f"SeqItem {op} 0x{self.addr:03X}=0x{self.data:08X}"


# ============================================================================
# APB Monitor Transaction (output analysis)
# ============================================================================
class ApbMonitorTransaction(uvm_sequence_item):
    """Transaction observed by APB monitor."""
    def __init__(self, name="ApbMonTransaction"):
        super().__init__(name)
        self.addr = 0
        self.data = 0
        self.write = True
        self.pready = 0
        self.pslverr = 0

    def __str__(self):
        return f"Mon {super().__str__()}"


# ============================================================================
# APB Driver
# ============================================================================
class ApbDriver(uvm_driver):
    """Drives APB bus signals per APB4 protocol (no wait states)."""

    def __init__(self, name="ApbDriver", parent=None):
        super().__init__(name, parent)

    async def run_phase(self):
        """Wait for sequence items and drive APB bus."""
        while True:
            item = await self.seq_item_port.get_next_item()
            await self._drive_transaction(item)
            self.seq_item_port.item_done()

    async def _drive_transaction(self, item):
        """Execute a single APB read or write transaction."""
        dut = cocotb.top

        if item.write:
            # APB Write: SETUP -> ACCESS
            # SETUP phase
            dut.paddr.value   = item.addr
            dut.pwrite.value  = 1
            dut.psel.value    = 1
            dut.penable.value = 0
            dut.pwdata.value  = item.data
            dut.pstrb.value   = getattr(item, 'strb', 0xF)
            await RisingEdge(dut.pclk)

            # ACCESS phase
            dut.penable.value = 1
            await RisingEdge(dut.pclk)

            # Wait for pready (or assume immediate)
            # De-assert
            dut.psel.value    = 0
            dut.penable.value = 0
            await RisingEdge(dut.pclk)

        else:
            # APB Read: SETUP -> ACCESS
            # SETUP phase
            dut.paddr.value   = item.addr
            dut.pwrite.value  = 0
            dut.psel.value    = 1
            dut.penable.value = 0
            await RisingEdge(dut.pclk)

            # ACCESS phase
            dut.penable.value = 1
            await RisingEdge(dut.pclk)

            # Sample read data
            item.data = int(dut.prdata.value)
            await RisingEdge(dut.pclk)

            # De-assert
            dut.psel.value    = 0
            dut.penable.value = 0

    async def reset(self):
        """Idle APB bus."""
        dut = cocotb.top
        dut.paddr.value   = 0
        dut.pwrite.value  = 0
        dut.psel.value    = 0
        dut.penable.value = 0
        dut.pwdata.value  = 0
        dut.pstrb.value   = 0


# ============================================================================
# APB Monitor
# ============================================================================
class ApbMonitor(uvm_component):
    """Monitors APB bus and publishes transactions via analysis port."""

    def __init__(self, name="ApbMonitor", parent=None):
        super().__init__(name, parent)
        self.ap = uvm_analysis_port("apb_ap", self)

    def build_phase(self):
        pass  # ap created in __init__

    async def run_phase(self):
        """Watch APB bus for transactions."""
        dut = cocotb.top
        prev_psel = 0
        prev_penable = 0

        while True:
            await RisingEdge(dut.pclk)

            psel = int(dut.psel.value)
            penable = int(dut.penable.value)
            pwrite = int(dut.pwrite.value)

            # Detect start of ACCESS phase: psel=1, penable=1 rising
            if psel == 1 and penable == 1 and prev_penable == 0:
                tr = ApbMonitorTransaction()
                tr.addr   = int(dut.paddr.value)
                tr.write  = (pwrite == 1)
                tr.pready = int(dut.pready.value)
                tr.pslverr = int(dut.pslverr.value)

                if tr.write:
                    tr.data = int(dut.pwdata.value)
                else:
                    tr.data = int(dut.prdata.value)

                self.logger.debug(f"Monitor observed: {tr}")
                self.ap.write(tr)

            prev_psel = psel
            prev_penable = penable


# ============================================================================
# APB Sequencer
# ============================================================================
class ApbSequencer(uvm_sequencer):
    """APB sequencer — provides ApbSeqItem to driver."""
    def __init__(self, name="ApbSequencer", parent=None):
        super().__init__(name, parent)


# ============================================================================
# APB Agent
# ============================================================================
class ApbAgent(uvm_agent):
    """APB agent containing driver, monitor, and sequencer."""

    def __init__(self, name="ApbAgent", parent=None):
        super().__init__(name, parent)
        self.driver = None
        self.monitor = None
        self.sequencer = None

    def build_phase(self):
        self.sequencer = ApbSequencer("apb_seqr", self)
        cfg = ConfigDB().get(self, "", "APB_ACTIVE")
        if cfg.get("is_active", True):
            self.driver = ApbDriver("apb_drv", self)
        self.monitor = ApbMonitor("apb_mon", self)

    def connect_phase(self):
        if self.driver is not None:
            self.driver.seq_item_port.connect(self.sequencer.seq_item_export)
