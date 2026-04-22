"""
DMA-330 Cocotb Test Infrastructure
===================================
Common base classes, clock/reset helpers, and lightweight VIP bus models
for testing DMA-330 RTL modules with cocotb.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer, ReadOnly, ClockCycles
from cocotb.handle import ModifiableObject, NonHierarchyIndexableObject
from cocotb.utils import get_sim_time


# =============================================================================
# Clock / Reset Helpers
# =============================================================================

class ClockReset:
    """Starts a clock and provides async reset helpers."""

    def __init__(self, dut, clk_name="clk", rst_name="rst_n", period_ns=10, reset_active_low=True):
        self.dut = dut
        self.clk_name = clk_name
        self.rst_name = rst_name
        self.period_ns = period_ns
        self.reset_active_low = reset_active_low

    def start_clock(self):
        """Start the clock."""
        clk_sig = getattr(self.dut, self.clk_name)
        cocotb.start_soon(Clock(clk_sig, self.period_ns, units="ns").start())

    async def assert_reset(self, cycles=5):
        """Assert reset for a number of cycles."""
        rst_sig = getattr(self.dut, self.rst_name)
        if self.reset_active_low:
            rst_sig.value = 0
        else:
            rst_sig.value = 1
        await ClockCycles(getattr(self.dut, self.clk_name), cycles)

    async def deassert_reset(self):
        """Deassert reset."""
        rst_sig = getattr(self.dut, self.rst_name)
        if self.reset_active_low:
            rst_sig.value = 1
        else:
            rst_sig.value = 0
        await RisingEdge(getattr(self.dut, self.clk_name))

    async def reset(self, cycles=5):
        """Full reset sequence: assert then deassert."""
        await self.assert_reset(cycles)
        await self.deassert_reset()
        # Wait a couple more cycles for things to settle
        await ClockCycles(getattr(self.dut, self.clk_name), 2)


# =============================================================================
# Lightweight APB Master VIP
# =============================================================================

class APBMaster:
    """
    Lightweight APB master driver for cocotb.
    Drives PSEL, PENABLE, PWRITE, PADDR, PWDATA and samples PRDATA, PREADY, PSLVERR.

    Usage:
        apb = APBMaster(dut, prefix="")           # secure port
        apb = APBMaster(dut, prefix="_ns")         # non-secure port
        await apb.init()
        data = await apb.read(0x100)
        await apb.write(0x100, 0xDEADBEEF)
    """

    def __init__(self, dut, clk_name="clk", prefix=""):
        self.dut = dut
        self.clk_name = clk_name
        self.prefix = prefix
        # Signal references (resolved in init)
        self._psel = None
        self._penable = None
        self._pwrite = None
        self._paddr = None
        self._pwdata = None
        self._prdata = None
        self._pready = None
        self._pslverr = None

    async def init(self):
        """Resolve signal references and idle the bus."""
        pfx = self.prefix
        self._psel = getattr(self.dut, f"psel{pfx}")
        self._penable = getattr(self.dut, f"penable{pfx}")
        self._pwrite = getattr(self.dut, f"pwrite{pfx}")
        self._paddr = getattr(self.dut, f"paddr{pfx}")
        self._pwdata = getattr(self.dut, f"pwdata{pfx}")
        self._prdata = getattr(self.dut, f"prdata{pfx}")
        self._pready = getattr(self.dut, f"pready{pfx}")
        self._pslverr = getattr(self.dut, f"pslverr{pfx}")
        self._idle()

    def _idle(self):
        """Drive APB bus to idle state."""
        self._psel.value = 0
        self._penable.value = 0
        self._pwrite.value = 0
        self._paddr.value = 0
        self._pwdata.value = 0

    async def write(self, addr, data):
        """
        APB write: SETUP → ACCESS → complete.
        Returns (pready, pslverr).
        """
        clk = getattr(self.dut, self.clk_name)
        # SETUP phase
        self._psel.value = 1
        self._penable.value = 0
        self._pwrite.value = 1
        self._paddr.value = addr
        self._pwdata.value = data
        await RisingEdge(clk)

        # ACCESS phase
        self._penable.value = 1
        await ReadOnly()
        # Wait for PREADY
        while not self._pready.value:
            await RisingEdge(clk)
            await ReadOnly()
        pready = int(self._pready.value)
        pslverr = int(self._pslverr.value)

        # Return to idle (must leave ReadOnly first)
        await RisingEdge(clk)
        self._idle()
        await RisingEdge(clk)
        return (pready, pslverr)

    async def read(self, addr):
        """
        APB read: SETUP → ACCESS → complete.
        Returns (rdata, pready, pslverr).
        """
        clk = getattr(self.dut, self.clk_name)
        # SETUP phase
        self._psel.value = 1
        self._penable.value = 0
        self._pwrite.value = 0
        self._paddr.value = addr
        self._pwdata.value = 0
        await RisingEdge(clk)

        # ACCESS phase
        self._penable.value = 1
        await ReadOnly()
        # Wait for PREADY
        while not self._pready.value:
            await RisingEdge(clk)
            await ReadOnly()
        rdata = int(self._prdata.value)
        pready = int(self._pready.value)
        pslverr = int(self._pslverr.value)

        # Return to idle (must leave ReadOnly first)
        await RisingEdge(clk)
        self._idle()
        await RisingEdge(clk)
        return (rdata, pready, pslverr)


# =============================================================================
# Lightweight AXI4 RAM Slave VIP
# =============================================================================

class AXI4RamSlave:
    """
    Lightweight AXI4 slave that emulates a simple memory.
    Responds to AR/R (read) and AW/W/B (write) channels.

    Usage:
        ram = AXI4RamSlave(dut, prefix="m_")
        cocotb.start_soon(ram.run())
        ram.write_word(0x1000, 0x12345678)
        data = ram.read_word(0x1000)
    """

    def __init__(self, dut, prefix="m_", clk_name="clk", addr_width=32, data_width=32):
        self.dut = dut
        self.prefix = prefix
        self.clk_name = clk_name
        self.addr_width = addr_width
        self.data_width = data_width
        self.memory = {}
        self._running = False

        # Resolve signals
        self._araddr = getattr(dut, f"{prefix}araddr")
        self._arlen = getattr(dut, f"{prefix}arlen")
        self._arsize = getattr(dut, f"{prefix}arsize")
        self._arvalid = getattr(dut, f"{prefix}arvalid")
        self._arready = getattr(dut, f"{prefix}arready")
        self._rdata = getattr(dut, f"{prefix}rdata")
        self._rresp = getattr(dut, f"{prefix}rresp")
        self._rlast = getattr(dut, f"{prefix}rlast")
        self._rvalid = getattr(dut, f"{prefix}rvalid")
        self._rready = getattr(dut, f"{prefix}rready")

        self._awaddr = getattr(dut, f"{prefix}awaddr")
        self._awlen = getattr(dut, f"{prefix}awlen")
        self._awsize = getattr(dut, f"{prefix}awsize")
        self._awvalid = getattr(dut, f"{prefix}awvalid")
        self._awready = getattr(dut, f"{prefix}awready")
        self._wdata = getattr(dut, f"{prefix}wdata")
        self._wstrb = getattr(dut, f"{prefix}wstrb")
        self._wlast = getattr(dut, f"{prefix}wlast")
        self._wvalid = getattr(dut, f"{prefix}wvalid")
        self._wready = getattr(dut, f"{prefix}wready")
        self._bresp = getattr(dut, f"{prefix}bresp")
        self._bvalid = getattr(dut, f"{prefix}bvalid")
        self._bready = getattr(dut, f"{prefix}bready")

    def write_word(self, addr, data):
        """Write a word into the RAM model."""
        self.memory[addr] = data & ((1 << self.data_width) - 1)

    def read_word(self, addr):
        """Read a word from the RAM model."""
        return self.memory.get(addr, 0)

    def _bytes_per_beat(self, size):
        return 1 << size

    async def run(self):
        """Main loop: fork read and write handlers."""
        self._running = True
        self._arready.value = 0
        self._rvalid.value = 0
        self._awready.value = 0
        self._wready.value = 0
        self._bvalid.value = 0

        rd_task = cocotb.start_soon(self._read_handler())
        wr_task = cocotb.start_soon(self._write_handler())
        # Keep running until stopped
        while self._running:
            await Timer(100, units="ns")

    async def _read_handler(self):
        """Handle AXI read channel (AR/R)."""
        clk = getattr(self.dut, self.clk_name)
        while self._running:
            # Wait for ARVALID
            self._arready.value = 1
            await RisingEdge(clk)
            await ReadOnly()
            while not self._arvalid.value:
                await RisingEdge(clk)
                await ReadOnly()

            # Capture read request
            addr = int(self._araddr.value)
            arlen = int(self._arlen.value)
            arsize = int(self._arsize.value)
            self._arready.value = 0

            # Send R beats
            bytes_per_beat = self._bytes_per_beat(arsize)
            for beat in range(arlen + 1):
                beat_addr = addr + beat * bytes_per_beat
                rdata = self.memory.get(beat_addr, 0)
                self._rdata.value = rdata
                self._rresp.value = 0  # OKAY
                self._rlast.value = 1 if (beat == arlen) else 0
                self._rvalid.value = 1

                await RisingEdge(clk)
                await ReadOnly()
                while not self._rready.value:
                    await RisingEdge(clk)
                    await ReadOnly()
                self._rvalid.value = 0

    async def _write_handler(self):
        """Handle AXI write channel (AW/W/B)."""
        clk = getattr(self.dut, self.clk_name)
        while self._running:
            # Wait for AWVALID
            self._awready.value = 1
            await RisingEdge(clk)
            await ReadOnly()
            while not self._awvalid.value:
                await RisingEdge(clk)
                await ReadOnly()

            # Capture write request
            addr = int(self._awaddr.value)
            awlen = int(self._awlen.value)
            awsize = int(self._awsize.value)
            self._awready.value = 0

            # Receive W beats
            bytes_per_beat = self._bytes_per_beat(awsize)
            for beat in range(awlen + 1):
                self._wready.value = 1
                await RisingEdge(clk)
                await ReadOnly()
                while not self._wvalid.value:
                    await RisingEdge(clk)
                    await ReadOnly()

                wdata = int(self._wdata.value)
                beat_addr = addr + beat * bytes_per_beat
                self.memory[beat_addr] = wdata
                is_last = bool(self._wlast.value)
                self._wready.value = 0

            # Send B response
            self._bresp.value = 0  # OKAY
            self._bvalid.value = 1
            await RisingEdge(clk)
            await ReadOnly()
            while not self._bready.value:
                await RisingEdge(clk)
                await ReadOnly()
            self._bvalid.value = 0


# =============================================================================
# Packed struct helpers for cocotb signal mapping
# =============================================================================

def pack_axi_req(req_type=0, addr=0, data=0, burst_len=0, burst_size=0, xid=0, valid=0, security=0):
    """Pack an axi_req_t struct into an integer for cocotb signal assignment.

    axi_req_t layout (from dma330_pkg.sv):
      req_type  [1:0]    - bits 63:62
      addr      [31:0]   - bits 61:30
      data      [31:0]   - bits 29:0... wait, let me recalculate.

    Actually axi_req_t is:
      req_type  : axi_req_type_t (2 bits)   = bits [71:70]
      addr      : logic[31:0]               = bits [69:38]
      data      : logic[31:0]               = bits [37:6]
      burst_len : logic[7:0]                = bits [5:0]... 

    Since this is packed struct, layout is:
      struct packed { req_type, addr, data, burst_len, burst_size, id, valid, security }

    Let's compute from MSB:
      req_type[1:0]  = 2 bits
      addr[31:0]     = 32 bits
      data[31:0]     = 32 bits
      burst_len[7:0] = 8 bits
      burst_size[2:0]= 3 bits
      id[3:0]        = 4 bits
      valid          = 1 bit
      security       = 1 bit
    Total = 2+32+32+8+3+4+1+1 = 83 bits

    MSB-first layout:
      bits [82:81] = req_type
      bits [80:49] = addr
      bits [48:17] = data
      bits [16:9]  = burst_len
      bits [8:6]   = burst_size
      bits [5:2]   = id
      bit  [1]     = valid
      bit  [0]     = security
    """
    val = 0
    val = (val << 2) | (req_type & 0x3)
    val = (val << 32) | (addr & 0xFFFFFFFF)
    val = (val << 32) | (data & 0xFFFFFFFF)
    val = (val << 8) | (burst_len & 0xFF)
    val = (val << 3) | (burst_size & 0x7)
    val = (val << 4) | (xid & 0xF)
    val = (val << 1) | (valid & 0x1)
    val = (val << 1) | (security & 0x1)
    return val


def unpack_axi_resp(val):
    """Unpack axi_resp_t from integer.

    axi_resp_t layout:
      data[31:0]   = 32 bits   bits [68:37]
      last         = 1 bit     bit  [36]
      valid        = 1 bit     bit  [35]
      resp[1:0]    = 2 bits    bits [34:33]
      error        = 1 bit     bit  [32]

    Wait, packed struct order:
      struct packed { data[31:0], last, valid, resp[1:0], error }
    Total = 32+1+1+2+1 = 37 bits

    MSB-first:
      bits [36:5]  = data
      bit  [4]     = last
      bit  [3]     = valid
      bits [2:1]   = resp
      bit  [0]     = error
    """
    if isinstance(val, int):
        raw = val
    else:
        raw = int(val)
    error = (raw >> 0) & 0x1
    resp = (raw >> 1) & 0x3
    valid = (raw >> 3) & 0x1
    last = (raw >> 4) & 0x1
    data = (raw >> 5) & 0xFFFFFFFF
    return {
        'data': data,
        'last': bool(last),
        'valid': bool(valid),
        'resp': resp,
        'error': bool(error),
    }


def pack_decoded_instr(opcode=0, fault=0, valid=0, instr_len=0, reg_select=0,
                       imm32=0, imm16=0, event_num=0, periph_num=0,
                       loop_cntr_sel=0, security=0):
    """Pack decoded_instr_t struct into integer.

    decoded_instr_t layout (packed struct, MSB first):
      valid          1 bit
      fault          1 bit
      opcode[7:0]    8 bits
      instr_len[2:0] 3 bits
      reg_select[1:0] 2 bits
      imm32[31:0]    32 bits
      imm16[15:0]    16 bits
      event_num[3:0] 4 bits
      periph_num[3:0] 4 bits
      loop_cntr_sel  1 bit
      security       1 bit
    Total = 1+1+8+3+2+32+16+4+4+1+1 = 73 bits

    MSB-first:
      bit  [72]      = valid
      bit  [71]      = fault
      bits [70:63]   = opcode
      bits [62:60]   = instr_len
      bits [59:58]   = reg_select
      bits [57:26]   = imm32
      bits [25:10]   = imm16
      bits [9:6]     = event_num
      bits [5:2]     = periph_num
      bit  [1]       = loop_cntr_sel
      bit  [0]       = security
    """
    val = 0
    val = (val << 1) | (valid & 0x1)
    val = (val << 1) | (fault & 0x1)
    val = (val << 8) | (opcode & 0xFF)
    val = (val << 3) | (instr_len & 0x7)
    val = (val << 2) | (reg_select & 0x3)
    val = (val << 32) | (imm32 & 0xFFFFFFFF)
    val = (val << 16) | (imm16 & 0xFFFF)
    val = (val << 4) | (event_num & 0xF)
    val = (val << 4) | (periph_num & 0xF)
    val = (val << 1) | (loop_cntr_sel & 0x1)
    val = (val << 1) | (security & 0x1)
    return val


# =============================================================================
# Common test decorators
# =============================================================================

def dma330_test(timeout_us=100):
    """Decorator: sets a cocotb test timeout."""
    def decorator(func):
        return cocotb.test(timeout_time=timeout_us, timeout_unit="us")(func)
    return decorator
