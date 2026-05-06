
# ============================================================================
# apb_drv.py — Plain Python APB driver + monitor (no UVM)
# ============================================================================
import cocotb
from cocotb.triggers import RisingEdge


class ApbDriver:
    """Drives APB bus signals directly."""
    def __init__(self):
        self.dut = cocotb.top

    async def write(self, addr: int, data: int, strb: int = 0xF):
        dwrite(addr, data, strb)
    # These are convenience — actual driving is done via the module-level functions below.

    async def read(self, addr: int) -> int:
        return await dread(addr)


class ApbMonitor:
    """Monitors APB bus, prints transactions."""
    def __init__(self):
        self.dut = cocotb.top
        self._running = False

    async def run(self):
        self._running = True
        prev_penable = 0
        while self._running:
            await RisingEdge(self.dut.pclk)
            psel = int(self.dut.psel.value)
            penable = int(self.dut.penable.value)
            if psel == 1 and penable == 1 and prev_penable == 0:
                pass  # Could log here
            prev_penable = penable

    def stop(self):
        self._running = False


# ============================================================================
# Module-level APB functions (used by tests)
# ============================================================================
async def apb_write(addr: int, data: int, strb: int = 0xF):
    """Drive a single APB write transaction."""
    dut = cocotb.top
    # SETUP phase
    dut.paddr.value = addr
    dut.pwrite.value = 1
    dut.psel.value = 1
    dut.penable.value = 0
    dut.pwdata.value = data
    dut.pstrb.value = strb
    await RisingEdge(dut.pclk)
    # ACCESS phase
    dut.penable.value = 1
    await RisingEdge(dut.pclk)
    # Wait for pready (assume immediate) then deassert
    dut.psel.value = 0
    dut.penable.value = 0
    await RisingEdge(dut.pclk)


async def apb_read(addr: int) -> int:
    """Drive a single APB read transaction, return prdata."""
    dut = cocotb.top
    # SETUP phase
    dut.paddr.value = addr
    dut.pwrite.value = 0
    dut.psel.value = 1
    dut.penable.value = 0
    await RisingEdge(dut.pclk)
    # ACCESS phase
    dut.penable.value = 1
    await RisingEdge(dut.pclk)
    result = int(dut.prdata.value)
    await RisingEdge(dut.pclk)
    # Deassert
    dut.psel.value = 0
    dut.penable.value = 0
    return result


# Address constants (from SSOT registers)
ADDR_DIR      = 0x000
ADDR_OUT      = 0x004
ADDR_IN       = 0x008
ADDR_INTEN    = 0x00C
ADDR_INTSTAT  = 0x010
ADDR_INTCLEAR = 0x014
