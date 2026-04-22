import cocotb
from cocotb.triggers import RisingEdge, ReadOnly
from testbase import ClockReset

NUM_REQUESTERS = 6
REQ_DMALD = 1

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

@cocotb.test(timeout_time=500, timeout_unit="us")
async def test_full_read(dut):
    cr = ClockReset(dut, clk_name="clk", rst_name="rst_n", period_ns=10)
    cr.start_clock()
    for i in range(NUM_REQUESTERS):
        dut.req_i[i].value = 0
    dut.m_arready.value = 0
    dut.m_rvalid.value = 0
    dut.m_rdata.value = 0
    dut.m_rresp.value = 0
    dut.m_rlast.value = 0
    dut.m_awready.value = 0
    dut.m_wready.value = 0
    dut.m_bvalid.value = 0
    dut.m_bresp.value = 0
    await cr.reset()

    clk = dut.clk

    # Issue read request
    dut._log.info("Step 1: Set request")
    await RisingEdge(clk)
    dut.req_i[0].value = pack_axi_req(req_type=REQ_DMALD, addr=0x1000, burst_len=0, burst_size=2, xid=0, valid=1)

    # Wait for ARVALID
    dut._log.info("Step 2: Wait for ARVALID")
    for i in range(20):
        await RisingEdge(clk)
        await ReadOnly()
        arvalid = int(dut.m_arvalid.value)
        dut._log.info(f"  iter {i}: ARVALID={arvalid}")
        if arvalid:
            break

    # Accept AR
    dut._log.info("Step 3: Accept AR")
    await RisingEdge(clk)
    dut.m_arready.value = 1
    await RisingEdge(clk)
    dut.m_arready.value = 0

    # Check RREADY
    dut._log.info("Step 4: Check RREADY")
    await RisingEdge(clk)
    await ReadOnly()
    rready = int(dut.m_rready.value)
    dut._log.info(f"  RREADY={rready}")
    assert rready, "RREADY should be asserted"

    # Drive R response
    dut._log.info("Step 5: Drive R response")
    dut.m_rdata.value = 0xDEADBEEF
    dut.m_rresp.value = 0
    dut.m_rlast.value = 1
    dut.m_rvalid.value = 1
    await RisingEdge(clk)
    await ReadOnly()

    # Wait for RREADY
    for i in range(10):
        rready = int(dut.m_rready.value)
        dut._log.info(f"  R beat iter {i}: RREADY={rready}")
        if rready:
            break
        await RisingEdge(clk)
        await ReadOnly()

    dut._log.info("Step 6: Deassert R")
    await RisingEdge(clk)
    dut.m_rvalid.value = 0
    dut.m_rlast.value = 0
    dut.req_i[0].value = 0

    # Read response
    await RisingEdge(clk)
    await ReadOnly()
    dut._log.info(f"  resp_o[0] = 0x{int(dut.resp_o[0].value):09X}")
    dut._log.info("PASS")
