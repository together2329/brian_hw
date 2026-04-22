"""
DMA-330 Channel Thread Tests
=============================
Tests for dma330_channel_thread.sv.
Feeds decoded_instr_t directly via decoded_instr_i port.

decoded_instr_t layout (71 bits, MSB first):
  bit  [70]      : valid
  bit  [69]      : fault
  bits [68:61]   : opcode         (8 bits)
  bits [60:59]   : instr_len      (2 bits)
  bits [58:57]   : reg_select     (2 bits)
  bits [56:25]   : imm32          (32 bits)
  bits [24:9]    : imm16          (16 bits)
  bit  [8]       : loop_cntr_sel
  bits [7:4]     : periph_num     (4 bits)
  bits [3:0]     : event_num      (4 bits)

channel_regs_t layout (209 bits, MSB first):
  SA[31:0] [208:177], DA[31:0] [176:145], CC[31:0] [144:113],
  PC[31:0] [112:81], LC0[7:0] [80:73], LC1[7:0] [72:65],
  loop0_start_PC[31:0] [64:33], loop1_start_PC[31:0] [32:1],
  security [0]
"""

import cocotb
from cocotb.triggers import RisingEdge, ReadOnly, ClockCycles
from testbase import ClockReset

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
# Channel states
CH_STOPPED            = 0
CH_EXECUTING          = 1
CH_CACHE_MISS         = 2
CH_UPDATING_PC        = 3
CH_WAITING_FOR_EVENT  = 4
CH_AT_BARRIER         = 5
CH_WAITING_FOR_PERIPH = 6
CH_FAULT_COMPLETING   = 7
CH_FAULT_LOCKED       = 8

# Opcodes (from dma330_pkg.sv)
OPC_DMAEND    = 0x00
OPC_DMAKILL   = 0x01
OPC_DMANOP    = 0x02
OPC_DMARMB    = 0x03
OPC_DMAWMB    = 0x04
OPC_DMALD     = 0x10
OPC_DMAST     = 0x20
OPC_DMAADDH   = 0x30
OPC_DMAADNH   = 0x31
OPC_DMALP     = 0x32
OPC_DMALPEND  = 0x33
OPC_DMASEV    = 0x35
OPC_DMAWFE    = 0x36
OPC_DMAMOV    = 0x40

# AXI request types
REQ_INSTR_FETCH = 0
REQ_DMALD       = 1
REQ_DMAST       = 2

# instr_len encoding as produced by the decoder:
#   1-byte instrs -> predicted_len=1 -> [1:0]=1
#   2-byte instrs -> predicted_len=2 -> [1:0]=2
#   6-byte instrs -> predicted_len=6 -> [1:0]=2
INSTR_LEN_1B = 1
INSTR_LEN_2B = 2

# ---------------------------------------------------------------------------
# Struct packing / unpacking
# ---------------------------------------------------------------------------

def pack_decoded_instr(opcode=0, fault=0, valid=0, instr_len=0, reg_select=0,
                       imm32=0, imm16=0, loop_cntr_sel=0, periph_num=0,
                       event_num=0):
    """Pack decoded_instr_t (71 bits)."""
    val  = 0
    val |= (valid & 0x1)   << 70
    val |= (fault & 0x1)   << 69
    val |= (opcode & 0xFF) << 61
    val |= (instr_len & 0x3) << 59
    val |= (reg_select & 0x3) << 57
    val |= (imm32 & 0xFFFFFFFF) << 25
    val |= (imm16 & 0xFFFF) << 9
    val |= (loop_cntr_sel & 0x1) << 8
    val |= (periph_num & 0xF) << 4
    val |= (event_num & 0xF)
    return val


def unpack_ch_regs(val):
    """Unpack channel_regs_t (209 bits)."""
    raw = int(val)
    return {
        'SA':             (raw >> 177) & 0xFFFFFFFF,
        'DA':             (raw >> 145) & 0xFFFFFFFF,
        'CC':             (raw >> 113) & 0xFFFFFFFF,
        'PC':             (raw >> 81)  & 0xFFFFFFFF,
        'LC0':            (raw >> 73)  & 0xFF,
        'LC1':            (raw >> 65)  & 0xFF,
        'loop0_start_PC': (raw >> 33)  & 0xFFFFFFFF,
        'loop1_start_PC': (raw >> 1)   & 0xFFFFFFFF,
        'security':       raw & 0x1,
    }


def unpack_axi_req(val):
    """Unpack axi_req_t (83 bits)."""
    raw = int(val)
    return {
        'req_type':   (raw >> 81) & 0x3,
        'addr':       (raw >> 49) & 0xFFFFFFFF,
        'data':       (raw >> 17) & 0xFFFFFFFF,
        'burst_len':  (raw >> 9)  & 0xFF,
        'burst_size': (raw >> 6)  & 0x7,
        'id':         (raw >> 2)  & 0xF,
        'valid':      bool((raw >> 1) & 1),
        'security':   bool(raw & 1),
    }


def pack_axi_resp(data=0, last=1, resp=0, valid=0, error=0):
    """Pack axi_resp_t (37 bits)."""
    val  = 0
    val |= (data & 0xFFFFFFFF) << 5
    val |= (last & 0x1)  << 4
    val |= (resp & 0x3)  << 2
    val |= (valid & 0x1) << 1
    val |= (error & 0x1)
    return val


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

async def setup(dut):
    """Common setup: start clock, reset, init inputs."""
    cr = ClockReset(dut, clk_name="clk", rst_name="rst_n", period_ns=10)
    cr.start_clock()
    # Initialize all inputs
    dut.start_i.value            = 0
    dut.start_pc_i.value         = 0
    dut.start_security_i.value   = 0
    dut.kill_i.value             = 0
    dut.decoded_instr_i.value    = 0
    dut.decoded_valid_i.value    = 0
    dut.axi_resp_i.value         = 0
    dut.mfifo_wr_ready.value     = 1
    dut.mfifo_rd_data.value      = 0xAAAABBBB
    dut.mfifo_rd_ready.value     = 1
    dut.periph_req_i.value       = 0
    dut.event_recv_i.value       = 0
    dut.barrier_ack_i.value      = 0
    await cr.reset()
    return cr


async def get_state(dut):
    return int(dut.ch_state_o.value)


async def get_regs(dut):
    return unpack_ch_regs(dut.ch_regs_o.value)


async def start_channel(dut, pc=0x100, security=0):
    """Start channel: assert start_i for one cycle, wait until CH_EXECUTING."""
    await RisingEdge(dut.clk)
    dut.start_pc_i.value       = pc
    dut.start_security_i.value = security
    dut.start_i.value          = 1
    await RisingEdge(dut.clk)
    dut.start_i.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)


async def feed_instr(dut, instr_val):
    """Feed one instruction (handshake), deassert valid, keep instr on bus.
    Returns after 2 clock edges so register updates are visible."""
    await RisingEdge(dut.clk)
    dut.decoded_instr_i.value = instr_val
    dut.decoded_valid_i.value = 1
    await RisingEdge(dut.clk)  # handshake happens here
    dut.decoded_valid_i.value = 0
    # keep decoded_instr_i stable (needed by WFE / xfer_fsm)
    await RisingEdge(dut.clk)  # register updates propagate
    await RisingEdge(dut.clk)  # settle


async def wait_cycles(dut, n):
    for _ in range(n):
        await RisingEdge(dut.clk)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_01_reset(dut):
    """After reset: CH_STOPPED, all regs zero."""
    cr = await setup(dut)
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert await get_state(dut) == CH_STOPPED, "State should be CH_STOPPED after reset"
    r = await get_regs(dut)
    assert r['SA'] == 0, f"SA={r['SA']:08x}, expected 0"
    assert r['DA'] == 0, f"DA={r['DA']:08x}, expected 0"
    assert r['CC'] == 0
    assert r['PC'] == 0
    assert r['LC0'] == 0
    assert r['LC1'] == 0


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_02_start(dut):
    """start_i → CH_EXECUTING, PC=start_pc_i."""
    cr = await setup(dut)
    await start_channel(dut, pc=0x200)
    await ReadOnly()
    assert await get_state(dut) == CH_EXECUTING, "Should be EXECUTING after start"
    r = await get_regs(dut)
    assert r['PC'] == 0x200, f"PC={r['PC']:08x}, expected 0x00000200"


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_03_dmamov(dut):
    """DMAMOV writes SA, DA, CC correctly."""
    cr = await setup(dut)
    await start_channel(dut, pc=0x100)

    # DMAMOV SA = 0xDEAD0000
    instr = pack_decoded_instr(opcode=OPC_DMAMOV, instr_len=INSTR_LEN_2B,
                               reg_select=0, imm32=0xDEAD0000)
    await feed_instr(dut, instr)
    r = await get_regs(dut)
    assert r['SA'] == 0xDEAD0000, f"SA={r['SA']:08x}"

    # DMAMOV DA = 0xBEEF1000
    instr = pack_decoded_instr(opcode=OPC_DMAMOV, instr_len=INSTR_LEN_2B,
                               reg_select=1, imm32=0xBEEF1000)
    await feed_instr(dut, instr)
    r = await get_regs(dut)
    assert r['DA'] == 0xBEEF1000, f"DA={r['DA']:08x}"

    # DMAMOV CC = 0x0000C001
    instr = pack_decoded_instr(opcode=OPC_DMAMOV, instr_len=INSTR_LEN_2B,
                               reg_select=2, imm32=0x0000C001)
    await feed_instr(dut, instr)
    r = await get_regs(dut)
    assert r['CC'] == 0x0000C001, f"CC={r['CC']:08x}"


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_04_dmaaddh(dut):
    """DMAADDH: SA[31:16] += imm16."""
    cr = await setup(dut)
    await start_channel(dut, pc=0x100)

    # First set SA to known value via DMAMOV
    instr = pack_decoded_instr(opcode=OPC_DMAMOV, instr_len=INSTR_LEN_2B,
                               reg_select=0, imm32=0x00010000)
    await feed_instr(dut, instr)

    # DMAADDH SA, 0x0005  → SA[31:16] += 5
    instr = pack_decoded_instr(opcode=OPC_DMAADDH, instr_len=INSTR_LEN_2B,
                               reg_select=0, imm16=0x0005)
    await feed_instr(dut, instr)
    r = await get_regs(dut)
    assert r['SA'] == 0x00060000, f"SA after ADDH={r['SA']:08x}"


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_05_dmaadnh(dut):
    """DMAADNH: SA[31:16] -= imm16."""
    cr = await setup(dut)
    await start_channel(dut, pc=0x100)

    # Set SA = 0x000A0000
    instr = pack_decoded_instr(opcode=OPC_DMAMOV, instr_len=INSTR_LEN_2B,
                               reg_select=0, imm32=0x000A0000)
    await feed_instr(dut, instr)

    # DMAADNH SA, 0x0003 → SA[31:16] -= 3
    instr = pack_decoded_instr(opcode=OPC_DMAADNH, instr_len=INSTR_LEN_2B,
                               reg_select=0, imm16=0x0003)
    await feed_instr(dut, instr)
    r = await get_regs(dut)
    assert r['SA'] == 0x00070000, f"SA after ADNH={r['SA']:08x}"


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_06_dmalp(dut):
    """DMALP: LC0/LC1 initialized, loop_start_PC saved."""
    cr = await setup(dut)
    await start_channel(dut, pc=0x100)

    # DMALP LC0, loop_count=10  (imm16=10)
    instr = pack_decoded_instr(opcode=OPC_DMALP, instr_len=INSTR_LEN_2B,
                               loop_cntr_sel=0, imm16=10)
    await feed_instr(dut, instr)
    r = await get_regs(dut)
    assert r['LC0'] == 10, f"LC0={r['LC0']}, expected 10"
    # loop0_start_PC should be PC_before + instr_len + 1
    # PC was 0x100 before this instr, instr_len=2 → advance by 3
    assert r['loop0_start_PC'] == 0x100 + INSTR_LEN_2B + 1, \
        f"loop0_start_PC={r['loop0_start_PC']:08x}"

    # DMALP LC1, loop_count=5
    instr = pack_decoded_instr(opcode=OPC_DMALP, instr_len=INSTR_LEN_2B,
                               loop_cntr_sel=1, imm16=5)
    await feed_instr(dut, instr)
    r = await get_regs(dut)
    assert r['LC1'] == 5, f"LC1={r['LC1']}, expected 5"


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_07_dmalpend(dut):
    """DMALPEND: counter decrements, PC jumps back."""
    cr = await setup(dut)
    await start_channel(dut, pc=0x100)

    # DMALP LC0 = 2
    instr = pack_decoded_instr(opcode=OPC_DMALP, instr_len=INSTR_LEN_2B,
                               loop_cntr_sel=0, imm16=2)
    await feed_instr(dut, instr)
    r = await get_regs(dut)
    loop_start = r['loop0_start_PC']

    # DMALPEND LC0 — first iteration: LC0>0 → decrement, jump back
    instr = pack_decoded_instr(opcode=OPC_DMALPEND, instr_len=INSTR_LEN_2B,
                               loop_cntr_sel=0)
    await feed_instr(dut, instr)
    r = await get_regs(dut)
    assert r['LC0'] == 1, f"LC0 after 1st LPEND={r['LC0']}, expected 1"
    assert r['PC'] == loop_start, f"PC should jump to loop_start, got {r['PC']:08x}"

    # DMALPEND LC0 — second iteration: LC0>0 → decrement, jump back
    await feed_instr(dut, instr)
    r = await get_regs(dut)
    assert r['LC0'] == 0, f"LC0 after 2nd LPEND={r['LC0']}, expected 0"
    assert r['PC'] == loop_start, f"PC should jump to loop_start, got {r['PC']:08x}"

    # DMALPEND LC0 — third iteration: LC0==0 → exit loop, PC advances
    await feed_instr(dut, instr)
    r = await get_regs(dut)
    assert r['LC0'] == 0, f"LC0 after 3rd LPEND={r['LC0']}, expected 0"
    # PC should have advanced past the DMALPEND (not jumped back)
    assert r['PC'] != loop_start, "PC should advance past loop on exit"


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_08_nested_loops(dut):
    """Nested loops: LC0 outer, LC1 inner."""
    cr = await setup(dut)
    await start_channel(dut, pc=0x100)

    # DMALP LC0 = 2
    instr = pack_decoded_instr(opcode=OPC_DMALP, instr_len=INSTR_LEN_2B,
                               loop_cntr_sel=0, imm16=2)
    await feed_instr(dut, instr)
    r = await get_regs(dut)
    outer_start = r['loop0_start_PC']

    # DMALP LC1 = 3
    instr = pack_decoded_instr(opcode=OPC_DMALP, instr_len=INSTR_LEN_2B,
                               loop_cntr_sel=1, imm16=3)
    await feed_instr(dut, instr)
    r = await get_regs(dut)
    inner_start = r['loop1_start_PC']

    lpend_lc1 = pack_decoded_instr(opcode=OPC_DMALPEND, instr_len=INSTR_LEN_2B,
                                   loop_cntr_sel=1)
    lpend_lc0 = pack_decoded_instr(opcode=OPC_DMALPEND, instr_len=INSTR_LEN_2B,
                                   loop_cntr_sel=0)

    # Inner loop: 4 iterations (LC1=3 → 3→2→1→0)
    for i in range(4):
        await feed_instr(dut, lpend_lc1)

    r = await get_regs(dut)
    assert r['LC1'] == 0, f"LC1 after inner loop={r['LC1']}"

    # Outer loop end: LC0 2→1 → jump back to outer_start
    await feed_instr(dut, lpend_lc0)
    r = await get_regs(dut)
    assert r['LC0'] == 1, f"LC0 after 1st outer LPEND={r['LC0']}"

    # Re-enter inner loop (LC1 was 0, need DMALP again)
    instr = pack_decoded_instr(opcode=OPC_DMALP, instr_len=INSTR_LEN_2B,
                               loop_cntr_sel=1, imm16=3)
    await feed_instr(dut, instr)
    # Run inner loop again
    for i in range(4):
        await feed_instr(dut, lpend_lc1)
    r = await get_regs(dut)
    assert r['LC1'] == 0, f"LC1 after 2nd inner loop={r['LC1']}"

    # Outer loop end: LC0 1→0 → exit
    await feed_instr(dut, lpend_lc0)
    r = await get_regs(dut)
    assert r['LC0'] == 0, f"LC0 after 2nd outer LPEND={r['LC0']}"


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_09_dmald(dut):
    """DMALD: AXI read request from SA."""
    cr = await setup(dut)
    await start_channel(dut, pc=0x100)

    # Set SA = 0x5000
    instr = pack_decoded_instr(opcode=OPC_DMAMOV, instr_len=INSTR_LEN_2B,
                               reg_select=0, imm32=0x5000)
    await feed_instr(dut, instr)

    # DMALD
    instr = pack_decoded_instr(opcode=OPC_DMALD, instr_len=INSTR_LEN_1B)
    await RisingEdge(dut.clk)
    dut.decoded_instr_i.value = instr
    dut.decoded_valid_i.value = 1
    await RisingEdge(dut.clk)  # handshake
    dut.decoded_valid_i.value = 0
    # Keep instr stable for xfer_fsm

    # Wait for AXI request to appear (xfer_fsm: XFER_REQ_AXI)
    found = False
    for _ in range(10):
        await RisingEdge(dut.clk)
        await ReadOnly()
        req = unpack_axi_req(dut.axi_req_o.value)
        if req['valid']:
            found = True
            break
    assert found, "AXI read request never became valid"
    assert req['req_type'] == REQ_DMALD, f"req_type={req['req_type']}, expected REQ_DMALD"
    assert req['addr'] == 0x5000, f"AXI addr={req['addr']:08x}, expected 0x00005000"

    # Provide AXI response
    await RisingEdge(dut.clk)
    dut.axi_resp_i.value = pack_axi_resp(data=0x12345678, last=1, valid=1)
    await RisingEdge(dut.clk)
    dut.axi_resp_i.value = pack_axi_resp(valid=0)
    # Wait for XFER_COMPLETE + settle
    await wait_cycles(dut, 4)


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_10_dmast(dut):
    """DMAST: AXI write request to DA."""
    cr = await setup(dut)
    await start_channel(dut, pc=0x100)

    # Set DA = 0xA000
    instr = pack_decoded_instr(opcode=OPC_DMAMOV, instr_len=INSTR_LEN_2B,
                               reg_select=1, imm32=0xA000)
    await feed_instr(dut, instr)

    # DMAST
    instr = pack_decoded_instr(opcode=OPC_DMAST, instr_len=INSTR_LEN_1B)
    await RisingEdge(dut.clk)
    dut.decoded_instr_i.value = instr
    dut.decoded_valid_i.value = 1
    await RisingEdge(dut.clk)  # handshake
    dut.decoded_valid_i.value = 0

    # Wait for AXI write request (DMAST goes through MFIFO_RD then REQ_AXI)
    found = False
    for _ in range(15):
        await RisingEdge(dut.clk)
        await ReadOnly()
        req = unpack_axi_req(dut.axi_req_o.value)
        if req['valid']:
            found = True
            break
    assert found, "AXI write request never became valid"
    assert req['req_type'] == REQ_DMAST, f"req_type={req['req_type']}, expected REQ_DMAST"
    assert req['addr'] == 0xA000, f"AXI addr={req['addr']:08x}, expected 0x0000A000"

    # Provide AXI response
    await RisingEdge(dut.clk)
    dut.axi_resp_i.value = pack_axi_resp(last=1, valid=1)
    await RisingEdge(dut.clk)
    dut.axi_resp_i.value = pack_axi_resp(valid=0)
    await wait_cycles(dut, 4)


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_11_dmasev(dut):
    """DMASEV: event_send_o pulse with correct event_num."""
    cr = await setup(dut)
    await start_channel(dut, pc=0x100)

    instr = pack_decoded_instr(opcode=OPC_DMASEV, instr_len=INSTR_LEN_2B,
                               event_num=7)
    await feed_instr(dut, instr)
    # event_send_o should reflect event_num (may be pulsed for 1 cycle)
    # Check during the cycles after feed
    found = False
    for _ in range(5):
        await ReadOnly()
        ev = int(dut.event_send_o.value)
        if ev == 7:
            found = True
            break
        await RisingEdge(dut.clk)
    assert found, f"event_send_o={int(dut.event_send_o.value)}, expected 7"


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_12_dmawfe(dut):
    """DMAWFE: block in CH_WAITING_FOR_EVENT until event_recv_i."""
    cr = await setup(dut)
    await start_channel(dut, pc=0x100)

    # DMAWFE event 3
    instr = pack_decoded_instr(opcode=OPC_DMAWFE, instr_len=INSTR_LEN_2B,
                               event_num=3)
    # Feed instruction (keep it on bus for the whole wait period)
    await RisingEdge(dut.clk)
    dut.decoded_instr_i.value = instr
    dut.decoded_valid_i.value = 1
    await RisingEdge(dut.clk)  # handshake
    dut.decoded_valid_i.value = 0
    await wait_cycles(dut, 2)

    # Should be in CH_WAITING_FOR_EVENT
    await ReadOnly()
    assert await get_state(dut) == CH_WAITING_FOR_EVENT, \
        f"State={await get_state(dut)}, expected WAITING_FOR_EVENT"

    # Send event 3
    await RisingEdge(dut.clk)
    dut.event_recv_i.value = (1 << 3)
    await wait_cycles(dut, 3)

    # Should be back to CH_EXECUTING
    await ReadOnly()
    assert await get_state(dut) == CH_EXECUTING, \
        f"State after event={await get_state(dut)}, expected EXECUTING"


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_13_dmaend(dut):
    """DMAEND: CH_EXECUTING → CH_STOPPED."""
    cr = await setup(dut)
    await start_channel(dut, pc=0x100)

    instr = pack_decoded_instr(opcode=OPC_DMAEND, instr_len=INSTR_LEN_1B)
    await feed_instr(dut, instr)
    await wait_cycles(dut, 2)

    await ReadOnly()
    assert await get_state(dut) == CH_STOPPED, \
        f"State after DMAEND={await get_state(dut)}, expected STOPPED"


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_14_kill(dut):
    """kill_i: immediate CH_STOPPED from CH_EXECUTING."""
    cr = await setup(dut)
    await start_channel(dut, pc=0x100)

    # Assert kill
    await RisingEdge(dut.clk)
    dut.kill_i.value = 1
    await RisingEdge(dut.clk)
    dut.kill_i.value = 0
    await wait_cycles(dut, 2)

    await ReadOnly()
    assert await get_state(dut) == CH_STOPPED, \
        f"State after kill={await get_state(dut)}, expected STOPPED"


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_15_fault(dut):
    """Fault instr → CH_FAULT_COMPLETING → CH_FAULT_LOCKED."""
    cr = await setup(dut)
    await start_channel(dut, pc=0x100)

    # Feed instruction with fault=1
    instr = pack_decoded_instr(opcode=OPC_DMANOP, fault=1, instr_len=INSTR_LEN_1B)
    await feed_instr(dut, instr)
    await wait_cycles(dut, 2)

    # Should have gone through FAULT_COMPLETING → FAULT_LOCKED
    await ReadOnly()
    st = await get_state(dut)
    assert st == CH_FAULT_LOCKED, \
        f"State after fault={st}, expected FAULT_LOCKED ({CH_FAULT_LOCKED})"


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_16_autoincrement(dut):
    """Address auto-increment after DMALD (src_inc=1 in CC)."""
    cr = await setup(dut)
    await start_channel(dut, pc=0x100)

    # Set SA = 0x1000
    instr = pack_decoded_instr(opcode=OPC_DMAMOV, instr_len=INSTR_LEN_2B,
                               reg_select=0, imm32=0x1000)
    await feed_instr(dut, instr)

    # Set CC: burst_size=0 (1B), burst_len=0 (1 transfer), src_inc=1 (CC[14]=1)
    # CC = (1 << 14) = 0x00004000
    instr = pack_decoded_instr(opcode=OPC_DMAMOV, instr_len=INSTR_LEN_2B,
                               reg_select=2, imm32=0x00004000)
    await feed_instr(dut, instr)

    sa_before = (await get_regs(dut))['SA']

    # DMALD
    instr = pack_decoded_instr(opcode=OPC_DMALD, instr_len=INSTR_LEN_1B)
    await RisingEdge(dut.clk)
    dut.decoded_instr_i.value = instr
    dut.decoded_valid_i.value = 1
    await RisingEdge(dut.clk)  # handshake
    dut.decoded_valid_i.value = 0

    # Wait for AXI request
    for _ in range(10):
        await RisingEdge(dut.clk)
        await ReadOnly()
        req = unpack_axi_req(dut.axi_req_o.value)
        if req['valid']:
            break

    # Provide AXI response
    await RisingEdge(dut.clk)
    dut.axi_resp_i.value = pack_axi_resp(data=0xAAAAAAAA, last=1, valid=1)
    await RisingEdge(dut.clk)
    dut.axi_resp_i.value = pack_axi_resp(valid=0)

    # Wait for XFER_COMPLETE and auto-increment
    await wait_cycles(dut, 6)

    r = await get_regs(dut)
    # burst_size_bytes = 1 (CC[3:0]=0 → decoded 1), burst_len=0 → total=1*(0+1)=1
    # SA should have incremented by 1
    assert r['SA'] == sa_before + 1, \
        f"SA after auto-inc={r['SA']:08x}, expected {sa_before+1:08x}"
