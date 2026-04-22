import cocotb
from cocotb.triggers import RisingEdge, ReadOnly
from testbase import ClockReset

NUM_REQUESTERS = 6
REQ_DMAST = 2

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
async def test_debug_write(dut):
    cr = ClockReset(dut, clk_name="clk", rst_name="rst_n", period_ns=10)
    cr.start_clock()
    for i in range(NUM_REQUESTERS):
        dut.req_i[i].value = 0
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

    req_val = pack_axi_req(req_type=REQ_DMAST, addr=0x2000, data=0x12345678, burst_len=0, burst_size=2, xid=2, valid=1)
    dut._log.info(f"req_val = 0x{req_val:021X}")

    await RisingEdge(dut.clk)
    dut.req_i[2].value = req_val

    for cyc in range(20):
        await RisingEdge(dut.clk)
        await ReadOnly()
        awvalid = int(dut.m_awvalid.value)
        arvalid = int(dut.m_arvalid.value)
        dut._log.info(f"  cyc={cyc}: AWVALID={awvalid} ARVALID={arvalid}")
        if awvalid:
            dut._log.info("AWVALID detected!")
            break
    else:
        dut._log.error("AWVALID never went high!")
