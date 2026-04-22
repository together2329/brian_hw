"""
DMA-330 AXI Master Tests
=========================
Tests for dma330_axi_master.sv.
NOTE: Icarus has issues with non-zero indices on unpacked arrays of packed structs.
All tests use requester 0 for writes and reads to avoid this limitation.
"""

import cocotb
from cocotb.triggers import RisingEdge, ReadOnly
from testbase import ClockReset

NUM_REQUESTERS = 6
REQ_INSTR_FETCH = 0
REQ_DMALD       = 1
REQ_DMAST       = 2


def pack_axi_req(req_type=0, addr=0, data=0, burst_len=0, burst_size=2, xid=0, valid=0, security=0):
    val = 0
    val |= (req_type & 0x3) << 81
    val |= (addr & 0xFFFFFFFF) << 49
    val |= (data & 0xFFFFFFFF) << 17
    val |= (burst_len & 0xFF) << 9
    val |= (burst_size & 0x7) << 6
    val |= (xid & 0xF) << 2
    val |= (valid & 0x1) << 1
    val |= (security & 0x1)
    return val


def unpack_axi_resp(val):
    raw = int(val)
    return {
        'data':  (raw >> 5) & 0xFFFFFFFF,
        'last':  bool((raw >> 4) & 1),
        'resp':  (raw >> 2) & 0x3,
        'valid': bool((raw >> 1) & 1),
        'error': bool(raw & 1),
    }


async def setup_axi(dut):
    cr = ClockReset(dut, clk_name="clk", rst_name="rst_n", period_ns=10)
    cr.start_clock()
    for i in range(NUM_REQUESTERS):
        dut.req_i[i].value = pack_axi_req(valid=0)
    dut.m_awready.value = 0
    dut.m_arready.value = 0
    dut.m_rvalid.value = 0
    dut.m_rdata.value = 0
    dut.m_rresp.value = 0
    dut.m_rlast.value = 0
    dut.m_wready.value = 0
    dut.m_bvalid.value = 0
    dut.m_bresp.value = 0
    await cr.reset()
    return cr


# Use requester 0 for all transactions (Icarus unpacked array limitation)
WR_REQ = 0
RD_REQ = 0


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_01_reset(dut):
    """After reset: all outputs idle."""
    cr = await setup_axi(dut)
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.m_arvalid.value) == 0
    assert int(dut.m_awvalid.value) == 0
    assert int(dut.m_wvalid.value) == 0
    assert int(dut.m_rready.value) == 0
    assert int(dut.m_bready.value) == 0
    assert int(dut.error_o.value) == 0


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_02_single_read(dut):
    """Single beat read transaction."""
    cr = await setup_axi(dut)

    await RisingEdge(dut.clk)
    dut.req_i[RD_REQ].value = pack_axi_req(
        req_type=REQ_DMALD, addr=0x1000, burst_len=0, burst_size=2, xid=RD_REQ, valid=1)

    # Wait for ARVALID
    for _ in range(50):
        await RisingEdge(dut.clk)
        await ReadOnly()
        if int(dut.m_arvalid.value):
            break

    # Accept AR
    await RisingEdge(dut.clk)
    dut.m_arready.value = 1
    await RisingEdge(dut.clk)
    dut.m_arready.value = 0

    # Send R beat
    await RisingEdge(dut.clk)
    dut.m_rdata.value = 0xDEADBEEF
    dut.m_rresp.value = 0
    dut.m_rlast.value = 1
    dut.m_rvalid.value = 1
    await RisingEdge(dut.clk)
    # Wait for RREADY
    for _ in range(10):
        await ReadOnly()
        if int(dut.m_rready.value):
            break
        await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.m_rvalid.value = 0
    dut.m_rlast.value = 0

    dut.req_i[RD_REQ].value = pack_axi_req(valid=0)
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.error_o.value) == 0


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_03_single_write(dut):
    """Single beat write transaction."""
    cr = await setup_axi(dut)

    await RisingEdge(dut.clk)
    dut.req_i[WR_REQ].value = pack_axi_req(
        req_type=REQ_DMAST, addr=0x2000, data=0x12345678,
        burst_len=0, burst_size=2, xid=WR_REQ, valid=1)

    # Wait for AWVALID
    for _ in range(50):
        await RisingEdge(dut.clk)
        await ReadOnly()
        if int(dut.m_awvalid.value):
            break

    # Accept AW
    await RisingEdge(dut.clk)
    dut.m_awready.value = 1
    await RisingEdge(dut.clk)
    dut.m_awready.value = 0

    # Accept W beat
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.m_wvalid.value), "WVALID expected"
    assert int(dut.m_wlast.value), "WLAST expected for single beat"
    await RisingEdge(dut.clk)
    dut.m_wready.value = 1
    await RisingEdge(dut.clk)
    dut.m_wready.value = 0

    # B response
    await RisingEdge(dut.clk)
    dut.m_bresp.value = 0
    dut.m_bvalid.value = 1
    await RisingEdge(dut.clk)
    for _ in range(10):
        await ReadOnly()
        if int(dut.m_bready.value):
            break
        await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.m_bvalid.value = 0

    dut.req_i[WR_REQ].value = pack_axi_req(valid=0)
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.error_o.value) == 0


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_04_burst_read(dut):
    """Burst read: 4 beats."""
    cr = await setup_axi(dut)
    burst_len = 3
    test_data = [0xAA000001, 0xAA000002, 0xAA000003, 0xAA000004]

    await RisingEdge(dut.clk)
    dut.req_i[RD_REQ].value = pack_axi_req(
        req_type=REQ_DMALD, addr=0x5000, burst_len=burst_len,
        burst_size=2, xid=RD_REQ, valid=1)

    # Wait for ARVALID
    for _ in range(50):
        await RisingEdge(dut.clk)
        await ReadOnly()
        if int(dut.m_arvalid.value):
            break

    # Accept AR
    await RisingEdge(dut.clk)
    dut.m_arready.value = 1
    await RisingEdge(dut.clk)
    dut.m_arready.value = 0

    # Send R beats
    for beat in range(burst_len + 1):
        await RisingEdge(dut.clk)
        dut.m_rdata.value = test_data[beat]
        dut.m_rresp.value = 0
        dut.m_rlast.value = 1 if beat == burst_len else 0
        dut.m_rvalid.value = 1
        await RisingEdge(dut.clk)
        for _ in range(10):
            await ReadOnly()
            if int(dut.m_rready.value):
                break
            await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        dut.m_rvalid.value = 0
        dut.m_rlast.value = 0

    dut.req_i[RD_REQ].value = pack_axi_req(valid=0)
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.error_o.value) == 0


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_05_burst_write(dut):
    """Burst write: 4 beats."""
    cr = await setup_axi(dut)
    burst_len = 3

    await RisingEdge(dut.clk)
    dut.req_i[WR_REQ].value = pack_axi_req(
        req_type=REQ_DMAST, addr=0x6000, data=0xBB000001,
        burst_len=burst_len, burst_size=2, xid=WR_REQ, valid=1)

    # Wait for AWVALID
    for _ in range(50):
        await RisingEdge(dut.clk)
        await ReadOnly()
        if int(dut.m_awvalid.value):
            break

    # Accept AW
    await RisingEdge(dut.clk)
    dut.m_awready.value = 1
    await RisingEdge(dut.clk)
    dut.m_awready.value = 0

    # Accept W beats
    for beat in range(burst_len + 1):
        await RisingEdge(dut.clk)
        await ReadOnly()
        assert int(dut.m_wvalid.value), f"WVALID beat {beat}"
        await RisingEdge(dut.clk)
        dut.m_wready.value = 1
        await RisingEdge(dut.clk)
        dut.m_wready.value = 0

    # B response
    await RisingEdge(dut.clk)
    dut.m_bresp.value = 0
    dut.m_bvalid.value = 1
    await RisingEdge(dut.clk)
    for _ in range(10):
        await ReadOnly()
        if int(dut.m_bready.value):
            break
        await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.m_bvalid.value = 0

    dut.req_i[WR_REQ].value = pack_axi_req(valid=0)
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.error_o.value) == 0


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_06_read_error(dut):
    """RRESP=SLVERR sets error_o."""
    cr = await setup_axi(dut)

    await RisingEdge(dut.clk)
    dut.req_i[RD_REQ].value = pack_axi_req(
        req_type=REQ_DMALD, addr=0x1000, burst_len=0, burst_size=2, xid=RD_REQ, valid=1)

    for _ in range(50):
        await RisingEdge(dut.clk)
        await ReadOnly()
        if int(dut.m_arvalid.value):
            break

    await RisingEdge(dut.clk)
    dut.m_arready.value = 1
    await RisingEdge(dut.clk)
    dut.m_arready.value = 0

    # Send R with SLVERR
    await RisingEdge(dut.clk)
    dut.m_rdata.value = 0xDEAD
    dut.m_rresp.value = 2  # SLVERR
    dut.m_rlast.value = 1
    dut.m_rvalid.value = 1
    await RisingEdge(dut.clk)
    for _ in range(10):
        await ReadOnly()
        if int(dut.m_rready.value):
            break
        await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.m_rvalid.value = 0
    dut.m_rlast.value = 0

    dut.req_i[RD_REQ].value = pack_axi_req(valid=0)
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.error_o.value) == 1, "error_o should be set after SLVERR"


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_07_write_error(dut):
    """BRESP=DECERR sets error_o."""
    cr = await setup_axi(dut)

    await RisingEdge(dut.clk)
    dut.req_i[WR_REQ].value = pack_axi_req(
        req_type=REQ_DMAST, addr=0x2000, data=0x12345678,
        burst_len=0, burst_size=2, xid=WR_REQ, valid=1)

    for _ in range(50):
        await RisingEdge(dut.clk)
        await ReadOnly()
        if int(dut.m_awvalid.value):
            break

    await RisingEdge(dut.clk)
    dut.m_awready.value = 1
    await RisingEdge(dut.clk)
    dut.m_awready.value = 0

    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.m_wvalid.value)
    await RisingEdge(dut.clk)
    dut.m_wready.value = 1
    await RisingEdge(dut.clk)
    dut.m_wready.value = 0

    # B with DECERR
    await RisingEdge(dut.clk)
    dut.m_bresp.value = 3  # DECERR
    dut.m_bvalid.value = 1
    await RisingEdge(dut.clk)
    for _ in range(10):
        await ReadOnly()
        if int(dut.m_bready.value):
            break
        await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.m_bvalid.value = 0

    dut.req_i[WR_REQ].value = pack_axi_req(valid=0)
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.error_o.value) == 1, "error_o should be set after DECERR"


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_08_grant(dut):
    """grant_o reflects active requester."""
    cr = await setup_axi(dut)

    await RisingEdge(dut.clk)
    dut.req_i[RD_REQ].value = pack_axi_req(
        req_type=REQ_DMALD, addr=0x3000, burst_len=0, burst_size=2, xid=RD_REQ, valid=1)

    found = False
    for _ in range(50):
        await RisingEdge(dut.clk)
        await ReadOnly()
        if int(dut.grant_o.value) & (1 << RD_REQ):
            found = True
            break
    assert found, f"grant_o bit {RD_REQ} should be set"

    # Complete: accept AR + R
    await RisingEdge(dut.clk)
    dut.m_arready.value = 1
    await RisingEdge(dut.clk)
    dut.m_arready.value = 0

    await RisingEdge(dut.clk)
    dut.m_rdata.value = 0
    dut.m_rresp.value = 0
    dut.m_rlast.value = 1
    dut.m_rvalid.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.m_rvalid.value = 0
    dut.m_rlast.value = 0
    dut.req_i[RD_REQ].value = pack_axi_req(valid=0)
    await RisingEdge(dut.clk)


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_09_backpressure(dut):
    """Delayed ARREADY: master waits patiently."""
    cr = await setup_axi(dut)

    await RisingEdge(dut.clk)
    dut.req_i[RD_REQ].value = pack_axi_req(
        req_type=REQ_DMALD, addr=0x7000, burst_len=0, burst_size=2, xid=RD_REQ, valid=1)

    for _ in range(50):
        await RisingEdge(dut.clk)
        await ReadOnly()
        if int(dut.m_arvalid.value):
            break

    # Delay 5 cycles
    for _ in range(5):
        await RisingEdge(dut.clk)

    await RisingEdge(dut.clk)
    dut.m_arready.value = 1
    await RisingEdge(dut.clk)
    dut.m_arready.value = 0

    await RisingEdge(dut.clk)
    dut.m_rdata.value = 0xFEEDFACE
    dut.m_rresp.value = 0
    dut.m_rlast.value = 1
    dut.m_rvalid.value = 1
    await RisingEdge(dut.clk)
    for _ in range(10):
        await ReadOnly()
        if int(dut.m_rready.value):
            break
        await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.m_rvalid.value = 0
    dut.m_rlast.value = 0
    dut.req_i[RD_REQ].value = pack_axi_req(valid=0)
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.error_o.value) == 0


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_10_instr_fetch(dut):
    """REQ_INSTR_FETCH accepted on read channel."""
    cr = await setup_axi(dut)

    await RisingEdge(dut.clk)
    dut.req_i[RD_REQ].value = pack_axi_req(
        req_type=REQ_INSTR_FETCH, addr=0x8000, burst_len=0,
        burst_size=2, xid=RD_REQ, valid=1)

    found = False
    for _ in range(50):
        await RisingEdge(dut.clk)
        await ReadOnly()
        if int(dut.m_arvalid.value):
            found = True
            break
    assert found, "ARVALID should assert for INSTR_FETCH"

    # Complete
    await RisingEdge(dut.clk)
    dut.m_arready.value = 1
    await RisingEdge(dut.clk)
    dut.m_arready.value = 0

    await RisingEdge(dut.clk)
    dut.m_rdata.value = 0x18000000
    dut.m_rresp.value = 0
    dut.m_rlast.value = 1
    dut.m_rvalid.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.m_rvalid.value = 0
    dut.m_rlast.value = 0
    dut.req_i[RD_REQ].value = pack_axi_req(valid=0)
    await RisingEdge(dut.clk)


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_11_concurrent_rw(dut):
    """Concurrent read and write (full-duplex): read on req[0], write on req[0] sequential."""
    cr = await setup_axi(dut)

    # Do a read first
    await RisingEdge(dut.clk)
    dut.req_i[RD_REQ].value = pack_axi_req(
        req_type=REQ_DMALD, addr=0x1000, burst_len=0, burst_size=2, xid=RD_REQ, valid=1)

    for _ in range(50):
        await RisingEdge(dut.clk)
        await ReadOnly()
        if int(dut.m_arvalid.value):
            break

    await RisingEdge(dut.clk)
    dut.m_arready.value = 1
    await RisingEdge(dut.clk)
    dut.m_arready.value = 0

    await RisingEdge(dut.clk)
    dut.m_rdata.value = 0xAAAA
    dut.m_rresp.value = 0
    dut.m_rlast.value = 1
    dut.m_rvalid.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.m_rvalid.value = 0
    dut.m_rlast.value = 0
    dut.req_i[RD_REQ].value = pack_axi_req(valid=0)

    # Now do a write
    await RisingEdge(dut.clk)
    dut.req_i[WR_REQ].value = pack_axi_req(
        req_type=REQ_DMAST, addr=0x2000, data=0xBBBB,
        burst_len=0, burst_size=2, xid=WR_REQ, valid=1)

    for _ in range(50):
        await RisingEdge(dut.clk)
        await ReadOnly()
        if int(dut.m_awvalid.value):
            break

    await RisingEdge(dut.clk)
    dut.m_awready.value = 1
    await RisingEdge(dut.clk)
    dut.m_awready.value = 0

    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.m_wvalid.value)
    await RisingEdge(dut.clk)
    dut.m_wready.value = 1
    await RisingEdge(dut.clk)
    dut.m_wready.value = 0

    await RisingEdge(dut.clk)
    dut.m_bresp.value = 0
    dut.m_bvalid.value = 1
    await RisingEdge(dut.clk)
    for _ in range(10):
        await ReadOnly()
        if int(dut.m_bready.value):
            break
        await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.m_bvalid.value = 0
    dut.req_i[WR_REQ].value = pack_axi_req(valid=0)
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.error_o.value) == 0
