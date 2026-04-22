"""
DMA-330 APB Slave Tests
========================
Tests for dma330_apb_slave.sv.
Uses APBMaster VIP from testbase.py for both secure and non-secure ports.
"""

import cocotb
from cocotb.triggers import RisingEdge, ReadOnly
from testbase import ClockReset, APBMaster

# Register offsets (from dma330_pkg.sv)
DSR_OFFSET       = 0x000
DPC_OFFSET       = 0x004
INTEN_OFFSET     = 0x020
INT_EVENT_RIS    = 0x024
INTMIS_OFFSET    = 0x028
INTCLR_OFFSET    = 0x02C
FSRD_OFFSET      = 0x030  # secure-only
FSRC_OFFSET      = 0x034
FTRD_OFFSET      = 0x038  # secure-only
DBGSTATUS_OFFSET = 0xD00  # secure-only
DBGCMD_OFFSET    = 0xD04
DBGINST0_OFFSET  = 0xD08
DBGINST1_OFFSET  = 0xD0C
CR0_OFFSET       = 0xE00


async def setup(dut):
    cr = ClockReset(dut, clk_name="clk", rst_name="rst_n", period_ns=10)
    cr.start_clock()
    # Drive reg_rdata (input from register file)
    dut.reg_rdata.value = 0
    # Idle both APB ports
    dut.psel_s.value = 0; dut.penable_s.value = 0; dut.pwrite_s.value = 0
    dut.paddr_s.value = 0; dut.pwdata_s.value = 0
    dut.psel_ns.value = 0; dut.penable_ns.value = 0; dut.pwrite_ns.value = 0
    dut.paddr_ns.value = 0; dut.pwdata_ns.value = 0
    await cr.reset()
    apb_s  = APBMaster(dut, prefix="_s")
    apb_ns = APBMaster(dut, prefix="_ns")
    await apb_s.init()
    await apb_ns.init()
    return cr, apb_s, apb_ns


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_01_reset(dut):
    """After reset: pready high, no error on both ports."""
    cr, apb_s, apb_ns = await setup(dut)
    await RisingEdge(dut.clk)
    assert int(dut.pready_s.value) == 1,  "pready_s should be 1 after reset"
    assert int(dut.pready_ns.value) == 1, "pready_ns should be 1 after reset"
    assert int(dut.pslverr_s.value) == 0, "pslverr_s should be 0 after reset"
    assert int(dut.pslverr_ns.value) == 0, "pslverr_ns should be 0 after reset"


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_02_secure_write_read(dut):
    """Secure APB write then read to DPC register."""
    cr, apb_s, apb_ns = await setup(dut)

    # Write to DPC
    pready, pslverr = await apb_s.write(DPC_OFFSET, 0x00000100)
    assert pready == 1, f"pready={pready}, expected 1"
    assert pslverr == 0, f"pslverr={pslverr}, expected 0 (no error)"

    # Read back — set reg_rdata first so DUT captures it
    dut.reg_rdata.value = 0x00000100
    rdata, pready, pslverr = await apb_s.read(DPC_OFFSET)
    assert pready == 1
    assert pslverr == 0
    assert rdata == 0x00000100, f"rdata=0x{rdata:08x}, expected 0x00000100"


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_03_ns_write_read(dut):
    """Non-secure APB write then read to INTEN register."""
    cr, apb_s, apb_ns = await setup(dut)

    # Write to INTEN (not secure-only)
    pready, pslverr = await apb_ns.write(INTEN_OFFSET, 0x0000000F)
    assert pready == 1
    assert pslverr == 0

    # Read back
    dut.reg_rdata.value = 0x0000000F
    rdata, pready, pslverr = await apb_ns.read(INTEN_OFFSET)
    assert pready == 1
    assert pslverr == 0
    assert rdata == 0x0000000F, f"rdata=0x{rdata:08x}"


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_04_addr_decode(dut):
    """Address decode: reg_addr reflects the APB address."""
    cr, apb_s, apb_ns = await setup(dut)

    # Manually drive SETUP phase to observe reg_addr
    dut.paddr_s.value = INTCLR_OFFSET
    dut.pwrite_s.value = 1
    dut.pwdata_s.value = 0xFF
    dut.psel_s.value = 1
    dut.penable_s.value = 0
    await RisingEdge(dut.clk)
    await ReadOnly()
    addr = int(dut.reg_addr.value)
    assert addr == INTCLR_OFFSET, f"reg_addr=0x{addr:03x}, expected 0x{INTCLR_OFFSET:03x}"
    # Leave ReadOnly before writing
    await RisingEdge(dut.clk)
    dut.psel_s.value = 0
    dut.penable_s.value = 0
    await RisingEdge(dut.clk)


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_05_security_filter(dut):
    """NS access to secure-only register → PSLVERR; secure access OK."""
    cr, apb_s, apb_ns = await setup(dut)

    # NS write to DBGSTATUS (secure-only, not read-only) → PSLVERR
    pready, pslverr = await apb_ns.write(DBGSTATUS_OFFSET, 0x1)
    assert pready == 1, "pready should still be 1"
    assert pslverr == 1, f"pslverr={pslverr}, expected 1 (security violation)"

    # Secure write to DBGCMD (secure-only, writable) → no error
    pready, pslverr = await apb_s.write(DBGCMD_OFFSET, 0x3)
    assert pready == 1
    assert pslverr == 0, f"pslverr={pslverr}, expected 0 (secure access OK)"


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_06_back_to_back(dut):
    """Back-to-back APB transfers: two writes in sequence."""
    cr, apb_s, apb_ns = await setup(dut)

    pready1, err1 = await apb_s.write(DPC_OFFSET, 0x100)
    pready2, err2 = await apb_s.write(DPC_OFFSET, 0x200)
    assert pready1 == 1 and pready2 == 1, "Both transfers should complete"
    assert err1 == 0 and err2 == 0, "Both transfers should have no error"


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_07_write_read_data(dut):
    """Write data → reg_wdata, read data ← reg_rdata."""
    cr, apb_s, apb_ns = await setup(dut)

    # Write — check reg_wdata during the ACCESS phase
    test_val = 0xDEADBEEF
    dut.paddr_s.value = DPC_OFFSET
    dut.pwrite_s.value = 1
    dut.pwdata_s.value = test_val
    dut.psel_s.value = 1
    dut.penable_s.value = 0
    await RisingEdge(dut.clk)  # SETUP → ACCESS
    dut.penable_s.value = 1
    await ReadOnly()
    wdata = int(dut.reg_wdata.value)
    assert wdata == test_val, f"reg_wdata=0x{wdata:08x}, expected 0x{test_val:08x}"
    await RisingEdge(dut.clk)
    dut.psel_s.value = 0
    dut.penable_s.value = 0
    await RisingEdge(dut.clk)

    # Read — set reg_rdata before SETUP
    dut.reg_rdata.value = 0xCAFEBABE
    rdata, pready, pslverr = await apb_s.read(DPC_OFFSET)
    assert rdata == 0xCAFEBABE, f"rdata=0x{rdata:08x}, expected 0xCAFEBABE"
    assert pready == 1
    assert pslverr == 0


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_08_secure_access_flag(dut):
    """reg_secure_access flag: 1 for secure, 0 for NS."""
    cr, apb_s, apb_ns = await setup(dut)

    # Secure port SETUP — flag should be 1
    dut.paddr_s.value = DPC_OFFSET
    dut.pwrite_s.value = 1
    dut.pwdata_s.value = 0
    dut.psel_s.value = 1
    dut.penable_s.value = 0
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.reg_secure_access.value) == 1, "reg_secure_access should be 1 for secure"
    await RisingEdge(dut.clk)
    dut.psel_s.value = 0
    dut.penable_s.value = 0
    await RisingEdge(dut.clk)

    # NS port SETUP — flag should be 0
    dut.paddr_ns.value = DPC_OFFSET
    dut.pwrite_ns.value = 1
    dut.pwdata_ns.value = 0
    dut.psel_ns.value = 1
    dut.penable_ns.value = 0
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.reg_secure_access.value) == 0, "reg_secure_access should be 0 for NS"
    await RisingEdge(dut.clk)
    dut.psel_ns.value = 0
    dut.penable_ns.value = 0
    await RisingEdge(dut.clk)
