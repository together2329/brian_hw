
# ============================================================================
# gpio_agent.py — GPIO Pad UVM Agent (Driver + Monitor)
# ============================================================================
import cocotb
from cocotb.triggers import RisingEdge, ClockCycles
from cocotb.binary import BinaryValue
from pyuvm import *


class GpioTransaction(uvm_sequence_item):
    """GPIO pad transaction: input value applied by driver or output observed by monitor."""
    def __init__(self, name="GpioTransaction"):
        super().__init__(name)
        self.value = 0    # 32-bit pad input value (for driver)
        self.oe = 0       # 32-bit output enable (observed by monitor)
        self.out_val = 0  # 32-bit output value (observed by monitor)

    def __str__(self):
        return f"GPIO val=0x{self.value:08X} oe=0x{self.oe:08X} out=0x{self.out_val:08X}"


class GpioDriver(uvm_driver):
    """Drives gpio_in pads from sequence items."""

    def __init__(self, name="GpioDriver", parent=None):
        super().__init__(name, parent)

    async def run_phase(self):
        dut = cocotb.top
        # Initialize
        dut.gpio_in.value = 0

        while True:
            item = await self.seq_item_port.get_next_item()
            dut.gpio_in.value = item.value
            await RisingEdge(dut.pclk)
            self.seq_item_port.item_done()


class GpioMonitor(uvm_component):
    """Monitors gpio_out and gpio_oe signals."""
    def __init__(self, name="GpioMonitor", parent=None):
        super().__init__(name, parent)
        self.ap = uvm_analysis_port("gpio_ap", self)

    def build_phase(self):
        pass  # ap created in __init__

    async def run_phase(self):
        dut = cocotb.top
        while True:
            await RisingEdge(dut.pclk)
            tr = GpioTransaction()
            tr.value = int(dut.gpio_in.value) if dut.gpio_in.value.is_resolvable else 0
            tr.oe = int(dut.gpio_oe.value) if dut.gpio_oe.value.is_resolvable else 0
            tr.out_val = int(dut.gpio_out.value) if dut.gpio_out.value.is_resolvable else 0
            self.ap.write(tr)


class GpioSequencer(uvm_sequencer):
    """GPIO input stimulus sequencer."""
    def __init__(self, name="GpioSequencer", parent=None):
        super().__init__(name, parent)


class GpioAgent(uvm_agent):
    """GPIO agent — drives gpio_in, monitors gpio_out/oe."""
    def __init__(self, name="GpioAgent", parent=None):
        super().__init__(name, parent)
        self.driver = None
        self.monitor = None
        self.sequencer = None

    def build_phase(self):
        self.sequencer = GpioSequencer("gpio_seqr", self)
        cfg = ConfigDB().get(self, "", "GPIO_ACTIVE")
        if cfg.get("is_active", True):
            self.driver = GpioDriver("gpio_drv", self)
        self.monitor = GpioMonitor("gpio_mon", self)

    def connect_phase(self):
        if self.driver is not None:
            self.driver.seq_item_port.connect(self.sequencer.seq_item_export)
