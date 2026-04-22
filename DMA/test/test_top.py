"""
DMA-330 Top-Level Integration Tests
=====================================
Tests for dma330_top.sv.

Includes unit tests for reset, APB, AXI idle, and an end-to-end
integration test that exercises the full APB→cache→decoder→channel→AXI data path.
"""

import cocotb
from cocotb.triggers import RisingEdge, ReadOnly, Timer, First, Event
from testbase import ClockReset, APBMaster

# Register offsets
DSR_OFFSET       = 0x000
DPC_OFFSET       = 0x004
INTEN_OFFSET     = 0x020
FSRD_OFFSET      = 0x030
CR0_OFFSET       = 0xE00
DBGINST0_OFFSET  = 0xD08
DBGINST1_OFFSET  = 0xD0C
DBGCMD_OFFSET    = 0xD04


async def setup(dut):
    cr = ClockReset(dut, clk_name="clk", rst_name="rst_n", period_ns=10)
    cr.start_clock()
    # AXI slave defaults (ready to accept)
    dut.m_awready.value = 1
    dut.m_wready.value  = 1
    dut.m_arready.value = 1
    dut.m_bresp.value   = 0
    dut.m_bvalid.value  = 0
    dut.m_rdata.value   = 0
    dut.m_rresp.value   = 0
    dut.m_rlast.value   = 0
    dut.m_rvalid.value  = 0
    # Peripheral request defaults
    dut.dmareq.value    = 0
    # APB idle
    dut.psel_ns.value   = 0; dut.penable_ns.value = 0
    dut.pwrite_ns.value = 0; dut.paddr_ns.value   = 0
    dut.pwdata_ns.value = 0
    await cr.reset()
    apb_s = APBMaster(dut, prefix="_s")
    await apb_s.init()
    return cr, apb_s


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_01_reset(dut):
    """After reset: all outputs in known state."""
    cr, apb_s = await setup(dut)
    await RisingEdge(dut.clk)

    # APB ports: pready high, no error
    assert int(dut.pready_s.value) == 1,  "pready_s should be 1"
    assert int(dut.pslverr_s.value) == 0, "pslverr_s should be 0"

    # AXI: idle (no outstanding transactions)
    assert int(dut.m_awvalid.value) == 0, "AW channel should be idle"
    assert int(dut.m_arvalid.value) == 0, "AR channel should be idle"
    assert int(dut.m_wvalid.value) == 0,  "W channel should be idle"

    # IRQ: no interrupts
    for i in range(9):  # NUM_EVENTS+1 = 9
        assert (int(dut.irq.value) >> i) & 1 == 0, f"irq[{i}] should be 0"

    # DMAACK: no acknowledges
    assert int(dut.dmaack.value) == 0, "dmaack should be 0"


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_02_apb_write_read(dut):
    """APB write/read via secure port to DPC register."""
    cr, apb_s = await setup(dut)

    # Write to DPC
    pready, pslverr = await apb_s.write(DPC_OFFSET, 0x00000200)
    assert pready == 1, f"pready={pready}"
    assert pslverr == 0, f"pslverr={pslverr}"

    # Read back
    dut.reg_rdata = 0x00000200  # set by regfile internally
    rdata, pready, pslverr = await apb_s.read(DPC_OFFSET)
    assert pready == 1
    assert pslverr == 0


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_03_apb_config_register(dut):
    """APB write to config register CR0."""
    cr, apb_s = await setup(dut)

    pready, pslverr = await apb_s.write(CR0_OFFSET, 0x00100000)
    assert pready == 1
    assert pslverr == 0, f"pslverr={pslverr}"


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_04_apb_ns_access(dut):
    """Non-secure APB access to INTEN (non-secure register)."""
    cr, apb_s = await setup(dut)
    apb_ns = APBMaster(dut, prefix="_ns")
    await apb_ns.init()

    pready, pslverr = await apb_ns.write(INTEN_OFFSET, 0xFF)
    assert pready == 1
    assert pslverr == 0, f"NS write to INTEN should succeed: pslverr={pslverr}"


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_05_apb_security_filter(dut):
    """NS access to secure-only register → PSLVERR."""
    cr, apb_s = await setup(dut)
    apb_ns = APBMaster(dut, prefix="_ns")
    await apb_ns.init()

    pready, pslverr = await apb_ns.write(FSRD_OFFSET, 0x1)
    assert pready == 1
    assert pslverr == 1, f"NS access to FSRD should error: pslverr={pslverr}"


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_06_axi_idle(dut):
    """AXI master interface is idle when no DMA active."""
    cr, apb_s = await setup(dut)
    await RisingEdge(dut.clk)
    assert int(dut.m_awvalid.value) == 0, "AWVALID should be 0"
    assert int(dut.m_arvalid.value) == 0, "ARVALID should be 0"
    assert int(dut.m_wvalid.value) == 0,  "WVALID should be 0"
    assert int(dut.m_bready.value) == 0,  "BREADY should be 0"
    assert int(dut.m_rready.value) == 0,  "RREADY should be 0"


# ---------------------------------------------------------------------------
# AXI Slave Helper — minimal memory model for integration test
# ---------------------------------------------------------------------------
class AXIMemory:
    """Simplified AXI slave: responds to reads from a dict, records writes.
    Uses a cycle-by-cycle polling approach instead of nested loops to avoid
    cocotb coroutine scheduling issues with Icarus Verilog."""
    def __init__(self, dut, mem=None):
        self.dut = dut
        self.mem = mem or {}
        self.writes = []  # list of (addr, data) tuples

    async def run(self, clock_cycles=5000):
        """Main loop: poll AXI signals each cycle and respond.
        Provides read data at 1 beat/cycle without checking RREADY, since the
        AXI master has m_rready=1 throughout R_DATA. Uses a 1-cycle delay after
        AR capture to skip the AR_ADDR→R_DATA transition cycle."""
        dut = self.dut
        read_active = False
        read_addr = 0
        read_arlen = 0
        read_beat = 0
        read_delay = 0  # 1-cycle delay after AR capture

        for _ in range(clock_cycles):
            await RisingEdge(dut.clk)

            if read_delay > 0:
                read_delay -= 1

            # --- Read response: provide 1 beat per cycle unconditionally ---
            if read_active and read_delay == 0:
                beat_addr = read_addr + read_beat * 4
                data = self.mem.get(beat_addr, 0xDEADBEEF)
                dut.m_rdata.value = data
                dut.m_rvalid.value = 1
                dut.m_rlast.value = 1 if read_beat == read_arlen else 0
                dut.m_rresp.value = 0
                read_beat += 1
                if read_beat > read_arlen:
                    read_active = False

            # --- Start new read if AR valid and not already reading ---
            if not read_active:
                dut.m_rvalid.value = 0
                dut.m_rlast.value = 0
                try:
                    arvalid = int(dut.m_arvalid.value)
                except ValueError:
                    arvalid = 0
                if arvalid:
                    try:
                        read_addr = int(dut.m_araddr.value)
                        read_arlen = int(dut.m_arlen.value)
                        read_beat = 0
                        read_active = True
                        read_delay = 1
                    except ValueError:
                        pass

            # --- Write handling ---
            try:
                awvalid = int(dut.m_awvalid.value)
                awready = int(dut.m_awready.value)
            except ValueError:
                awvalid = 0
                awready = 0
            if awvalid and awready:
                try:
                    waddr = int(dut.m_awaddr.value)
                except ValueError:
                    continue
                try:
                    wvalid = int(dut.m_wvalid.value)
                    wready = int(dut.m_wready.value)
                except ValueError:
                    continue
                if wvalid and wready:
                    try:
                        wdata = int(dut.m_wdata.value)
                        wlast = int(dut.m_wlast.value)
                    except ValueError:
                        continue
                    self.writes.append((waddr, wdata))
                    if wlast:
                        dut.m_bvalid.value = 1
                        dut.m_bresp.value = 0
                        for _ in range(50):
                            await RisingEdge(dut.clk)
                            try:
                                if int(dut.m_bready.value):
                                    break
                            except ValueError:
                                pass
                        dut.m_bvalid.value = 0


@cocotb.test(timeout_time=1000, timeout_unit="us")
async def test_07_dma_memcpy_integration(dut):
    """End-to-end: APB debug injection -> DMAGO -> channel starts -> AXI activity.

    Validates the complete control path:
      1. APB writes DBGINST0/DBGINST1 with a DMAGO instruction
      2. APB writes DBGCMD to trigger injection
      3. Manager starts channel 0
      4. Channel fetches program via cache, decodes, executes
      5. AXI slave responds, channel completes transfer
    """
    cr, apb_s = await setup(dut)

    SRC_ADDR = 0x0000_2000
    DST_ADDR = 0x0000_3000
    PROG_ADDR = 0x0000_1000
    SRC_DATA = 0xBAAD_F00D

    # Build DMA program bytes for the cache line (64 bytes = 16 words)
    # PL330 opcodes:
    #   DMAMOV = 0xBC, byte1[1:0]: 0=SAR, 1=DAR, 2=CCR
    #   DMALD  = 0x04, DMAST = 0x08, DMAEND = 0x00
    cache_line = bytearray(64)
    offset = 0

    # DMAMOV SAR, SRC_ADDR (6 bytes)
    cache_line[offset]   = 0xBC;  cache_line[offset+1] = 0x00  # reg_select[1:0]=0 -> SAR
    cache_line[offset+2] = SRC_ADDR & 0xFF
    cache_line[offset+3] = (SRC_ADDR >> 8) & 0xFF
    cache_line[offset+4] = (SRC_ADDR >> 16) & 0xFF
    cache_line[offset+5] = (SRC_ADDR >> 24) & 0xFF
    offset += 6

    # DMAMOV DAR, DST_ADDR (6 bytes)
    cache_line[offset]   = 0xBC;  cache_line[offset+1] = 0x01  # reg_select[1:0]=1 -> DAR
    cache_line[offset+2] = DST_ADDR & 0xFF
    cache_line[offset+3] = (DST_ADDR >> 8) & 0xFF
    cache_line[offset+4] = (DST_ADDR >> 16) & 0xFF
    cache_line[offset+5] = (DST_ADDR >> 24) & 0xFF
    offset += 6

    # DMAMOV CCR, 0x00000002 (6 bytes) — burst_size=2 (4 bytes), burst_len=0 (1 beat)
    # CC[3:0]=2 -> burst_size 4 bytes, CC[11:4]=0 -> burst_len 1 transfer
    cache_line[offset]   = 0xBC;  cache_line[offset+1] = 0x02  # reg_select[1:0]=2 -> CCR
    cache_line[offset+2] = 0x02   # CC[3:0] = 2 (4-byte bursts)
    cache_line[offset+3] = 0x00
    cache_line[offset+4] = 0x00
    cache_line[offset+5] = 0x00
    offset += 6

    # DMALD (1 byte) — load from SAR to MFIFO
    cache_line[offset] = 0x04; offset += 1
    # DMAST (1 byte) — store from MFIFO to DAR
    cache_line[offset] = 0x08; offset += 1
    # DMAEND (1 byte) — stop channel
    cache_line[offset] = 0x00; offset += 1

    # Convert to 32-bit AXI words (little-endian)
    axi_words = []
    for i in range(0, 64, 4):
        word = (cache_line[i] | (cache_line[i+1] << 8) |
                (cache_line[i+2] << 16) | (cache_line[i+3] << 24))
        axi_words.append(word)

    # Populate memory model: program + source data
    mem = {}
    for i, word in enumerate(axi_words):
        mem[PROG_ADDR + i * 4] = word
    mem[SRC_ADDR] = SRC_DATA

    axi_writes = []  # list of (addr, data) tuples

    # Helper: safely read a cocotb signal, returning default on 'x'/'z'
    def safe_int(sig, default=0):
        try:
            return int(sig.value)
        except (ValueError, TypeError):
            return default

    # Inject DMAGO via APB debug
    # DBGINST0[31:24]=byte0=0xA0 (DMAGO), [23:16]=byte1, [15:8]=byte2, [7:0]=byte3
    # DBGINST1[31:24]=byte4, [23:16]=byte5
    # PL330 little-endian: byte2=addr[7:0], byte3=addr[15:8], byte4=addr[23:16], byte5=addr[31:24]
    addr_b2 = PROG_ADDR & 0xFF
    addr_b3 = (PROG_ADDR >> 8) & 0xFF
    addr_b4 = (PROG_ADDR >> 16) & 0xFF
    addr_b5 = (PROG_ADDR >> 24) & 0xFF
    dbginst0 = (0xA0 << 24) | (0x00 << 16) | (addr_b2 << 8) | addr_b3
    dbginst1 = (addr_b4 << 24) | (addr_b5 << 16)

    await apb_s.write(DBGINST0_OFFSET, dbginst0)
    await RisingEdge(dut.clk)
    await apb_s.write(DBGINST1_OFFSET, dbginst1)
    await RisingEdge(dut.clk)
    await apb_s.write(DBGCMD_OFFSET, 0x00000000)
    await RisingEdge(dut.clk)

    dut._log.info("Debug injection complete, running AXI slave + monitor...")

    # --- Combined AXI slave + channel monitor loop ---
    # The AXI slave MUST run from the start to catch the first AR request
    # that happens when the channel starts and triggers a cache miss.
    read_active = False
    read_addr = 0
    read_arlen = 0
    read_beat = 0
    read_delay = 0
    # Extra cycle hold: after the last beat, hold m_rvalid/m_rlast for
    # one more cycle so the DUT can capture it at the next RisingEdge.
    hold_last = False

    ch0_stopped = False
    ch0_executing_seen = False

    # AXI write slave state
    write_addr_captured = False
    write_addr = 0

    for i in range(3000):
        await RisingEdge(dut.clk)

        # Hold last beat for one extra cycle (let DUT capture final beat)
        if hold_last:
            hold_last = False
            # Don't clear m_rvalid yet — let DUT capture first
            # We'll clear it next iteration in the 'if not read_active' branch
            continue

        # --- Inline AXI read slave ---
        if read_delay > 0:
            read_delay -= 1

        # Provide read data beats when active
        if read_active and read_delay == 0:
            beat_addr = read_addr + read_beat * 4
            data = mem.get(beat_addr, 0xDEADBEEF)
            dut.m_rdata.value = data
            dut.m_rvalid.value = 1
            dut.m_rlast.value = 1 if read_beat == read_arlen else 0
            dut.m_rresp.value = 0
            read_beat += 1
            if read_beat > read_arlen:
                read_active = False
                hold_last = True  # Hold m_rvalid for one more DUT clock edge

        # Capture new read requests
        if not read_active and not hold_last:
            dut.m_rvalid.value = 0
            dut.m_rlast.value = 0
            arvalid = safe_int(dut.m_arvalid, 0)
            if arvalid:
                read_addr = safe_int(dut.m_araddr, 0)
                read_arlen = safe_int(dut.m_arlen, 0)
                dut._log.info(
                    f"  AXI AR captured: addr=0x{read_addr:08x} arlen={read_arlen}"
                )
                read_beat = 0
                read_active = True
                read_delay = 1

        # --- Inline AXI write slave (independent AW / W / B phases) ---
        # AW phase: capture write address
        awvalid = safe_int(dut.m_awvalid, 0)
        if awvalid and not write_addr_captured:
            dut.m_awready.value = 1
            write_addr = safe_int(dut.m_awaddr, 0)
            write_addr_captured = True
            dut._log.info(f"  AXI AW captured: addr=0x{write_addr:08x}")
        elif write_addr_captured:
            dut.m_awready.value = 0

        # W phase: capture write data
        wvalid = safe_int(dut.m_wvalid, 0)
        if wvalid and write_addr_captured:
            wdata = safe_int(dut.m_wdata, 0)
            wlast = safe_int(dut.m_wlast, 0)
            axi_writes.append((write_addr, wdata))
            dut._log.info(f"  AXI write: addr=0x{write_addr:08x} data=0x{wdata:08x} last={wlast}")
            dut.m_wready.value = 1
            if wlast:
                write_addr_captured = False
                dut.m_bvalid.value = 1
                dut.m_bresp.value = 0
        else:
            dut.m_wready.value = 0

        # Clear BVALID after master accepts
        if safe_int(dut.m_bvalid, 0) and safe_int(dut.m_bready, 0):
            dut.m_bvalid.value = 0

        # --- Monitor channel state ---
        ch0_state = safe_int(dut.gen_ch[0].u_ch_thread.state_reg, 0xFF)
        if ch0_state == 1:  # CH_EXECUTING
            ch0_executing_seen = True

        if i < 30 or (28 <= i <= 55) or i % 50 == 49:
            feed_st = safe_int(dut.feed_state, 0)
            cache_st = safe_int(dut.u_instr_cache.cache_state, 0)
            arv = safe_int(dut.m_arvalid, 0)
            rv = safe_int(dut.m_rvalid, 0)
            # AXI master internal state
            r_st = safe_int(dut.u_axi_master.r_state, 0)
            r_gid = safe_int(dut.u_axi_master.r_grant_id, 0)
            # Check if AXI master sees channel request
            try:
                ch_axi_req_raw = int(dut.gen_ch[0].ch_axi_req_w)
                ch_axi_req_valid = (ch_axi_req_raw >> 1) & 1
                # Also check top-level axi_req[2]
                try:
                    axi_req_2_raw = int(dut.axi_req[2])
                    axi_req_2_valid = (axi_req_2_raw >> 1) & 1
                except Exception:
                    axi_req_2_valid = -2
                # Check AXI master internal
                try:
                    req_i_2_raw = int(dut.u_axi_master.req_i[2])
                    req_i_2_valid = (req_i_2_raw >> 1) & 1
                except Exception:
                    req_i_2_valid = -3
            except Exception:
                ch_axi_req_valid = -1
                axi_req_2_valid = -2
                req_i_2_valid = -3
            m_rready_v = safe_int(dut.m_rready, 0)
            # Cache AXI response (raw value)
            try:
                cache_resp_raw = int(dut.cache_axi_resp)
            except (ValueError, TypeError):
                cache_resp_raw = -1
            cache_resp_valid = (cache_resp_raw >> 1) & 1 if cache_resp_raw >= 0 else -1
            cache_resp_last = (cache_resp_raw >> 4) & 1 if cache_resp_raw >= 0 else -1
            cache_beat_cnt = safe_int(dut.u_instr_cache.beat_cnt, 0)
            # Channel 0 PC via channel output port (bypass unpacked array)
            try:
                ch0_pc_raw = int(dut.gen_ch[0].u_ch_thread.ch_regs_o) >> 81 & 0xFFFFFFFF
            except Exception:
                try:
                    ch0_pc_raw = int(dut.gen_ch[0].u_ch_thread.ch_regs_w) >> 81 & 0xFFFFFFFF
                except Exception:
                    ch0_pc_raw = 0
            ch0_xfer = safe_int(dut.gen_ch[0].u_ch_thread.xfer_state, 0)
            ch0_dec_rdy = safe_int(dut.gen_ch[0].u_ch_thread.decoded_ready_r, 0)
            saved_ilen = safe_int(dut.gen_ch[0].u_ch_thread.saved_instr_len, 0)
            # Check channel's actual response port
            try:
                ch_resp_actual = int(dut.gen_ch[0].u_ch_thread.axi_resp_i)
                ch_resp_valid = (ch_resp_actual >> 1) & 1
            except Exception:
                ch_resp_valid = -1
            # Check MFIFO write ready (for DMALD → MFIFO push)
            mfifo_rdy = safe_int(dut.gen_ch[0].u_ch_thread.mfifo_wr_ready, 0)
            w_st = safe_int(dut.u_axi_master.w_state, 0)
            awv = safe_int(dut.m_awvalid, 0)
            wv = safe_int(dut.m_wvalid, 0)
            dut._log.info(
                f"  C{i}: ch0={ch0_state} feed={feed_st} cache={cache_st} "
                f"pc=0x{ch0_pc_raw:08x} xfer={ch0_xfer} dec_rdy={ch0_dec_rdy} "
                f"r_st={r_st} r_gid={r_gid} ch_v={ch_axi_req_valid} "
                f"resp_v={ch_resp_valid} mfifo_rdy={mfifo_rdy} "
                f"saved_ilen={saved_ilen} "
                f"w_st={w_st} awv={awv} wv={wv} "
                f"wr_cnt={len(axi_writes)}"
            )

        if ch0_state == 0 and i > 10:  # CH_STOPPED after having been executing
            if ch0_executing_seen:
                ch0_stopped = True
                break

    # Log results
    dut._log.info(f"AXI writes captured: {len(axi_writes)}")
    for addr, data in axi_writes:
        dut._log.info(f"  Write: addr=0x{addr:08x} data=0x{data:08x}")

    # Assert: channel reached CH_STOPPED after executing
    assert ch0_executing_seen, \
        "Channel should have entered CH_EXECUTING after DMAGO injection"
    assert ch0_stopped, \
        "Channel should have reached CH_STOPPED after DMAEND"
    dut._log.info("Channel lifecycle verified: EXECUTING → CH_STOPPED")

    # Assert: AXI write occurred at destination
    dst_writes = [(a, d) for a, d in axi_writes
                  if DST_ADDR <= a <= DST_ADDR + 256]
    assert len(dst_writes) > 0, \
        f"Expected at least one AXI write to DST_ADDR 0x{DST_ADDR:08x}, got {len(axi_writes)} total writes"

    # Assert: data integrity
    written_data = dst_writes[0][1]
    assert written_data == SRC_DATA, \
        f"Data mismatch: wrote 0x{written_data:08x}, expected 0x{SRC_DATA:08x}"
    dut._log.info("Integration test PASSED: memory-to-memory copy verified!")
