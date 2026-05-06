
# ============================================================================
# irq_monitor.py — Interrupt Monitor for gpio_irq
# ============================================================================
import cocotb
from cocotb.triggers import RisingEdge
from pyuvm import *


class IrqTransaction(uvm_sequence_item):
    """Transaction published when gpio_irq changes state."""
    def __init__(self, name="IrqTransaction"):
        super().__init__(name)
        self.irq_level = 0       # current gpio_irq value
        self.timestamp_ns = 0    # simulation time in ns
        self.rising_edge = False # True if this is a 0->1 transition

    def __str__(self):
        edge = "↑" if self.rising_edge else "↓"
        return f"IRQ{edge} level={self.irq_level} @ {self.timestamp_ns}ns"


class IrqMonitor(uvm_component):
    """Monitors gpio_irq for rising edges."""
    def __init__(self, name="IrqMonitor", parent=None):
        super().__init__(name, parent)
        self.ap = uvm_analysis_port("irq_ap", self)

    def build_phase(self):
        pass  # irq_ap already created in __init__

    async def run_phase(self):
        dut = cocotb.top
        prev_irq = 0

        while True:
            await RisingEdge(dut.pclk)
            current_irq = int(dut.gpio_irq.value)

            if current_irq != prev_irq:
                tr = IrqTransaction()
                tr.irq_level = current_irq
                tr.timestamp_ns = cocotb.utils.get_sim_time(units='ns')
                tr.rising_edge = (current_irq == 1 and prev_irq == 0)
                self.logger.debug(f"IRQ event: {tr}")
                self.ap.write(tr)

            prev_irq = current_irq
