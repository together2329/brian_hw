"""
DMA-330 Manager Thread Tests
=============================
Tests for dma330_manager_thread.sv.
Feeds decoded_instr_t directly. For tests needing MGR_EXECUTING,
the internal state_reg is forced via VPI since the module has no
external start input (started by APB debug writes in the full system).
"""

import cocotb
from cocotb.triggers import RisingEdge, ReadOnly, ClockCycles
from testbase import ClockReset

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MGR_STOPPED           = 0
MGR_EXECUTING         = 1
MGR_WAITING_FOR_EVENT = 2
MGR_FAULT_COMPLETING  = 3
MGR_FAULT_LOCKED      = 4

OPC_DMAEND  = 0x00
OPC_DMAKILL = 0x01
OPC_DMANOP  = 0x02
OPC_DMARMB  = 0x03
OPC_DMAWMB  = 0x04
OPC_DMALD   = 0x10
OPC_DMAST   = 0x20
OPC_DMAADDH = 0x30
OPC_DMALP   = 0x32
OPC_DMASEV  = 0x35
OPC_DMAWFE  = 0x36
OPC_DMAMOV  = 0x40
OPC_DMAGO   = 0x41

INSTR_LEN_1B = 1
INSTR_LEN_2B = 2

NUM_CHANNELS = 4


# ---------------------------------------------------------------------------
# Struct packing
# ---------------------------------------------------------------------------
def pack_decoded_instr(opcode=0, fault=0, valid=0, instr_len=0, reg_select=0,
                       imm32=0, imm16=0, loop_cntr_sel=0, periph_num=0,
                       event_num=0):
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def setup(dut):
    cr = ClockReset(dut, clk_name="clk", rst_name="rst_n", period_ns=10)
    cr.start_clock()
    dut.decoded_instr_i.value    = 0
    dut.decoded_valid_i.value    = 0
    dut.ch_start_ack.value       = 0
    dut.event_received.value     = 0
    dut.dbginject_valid.value    = 0
    dut.dbginject_instr.value    = 0
    dut.dbgcmd_clear_fault.value = 0
    await cr.reset()
    return cr


async def get_state(dut):
    return int(dut.mgr_state_o.value)


async def get_pc(dut):
    return int(dut.mgr_pc_o.value)


async def force_executing(dut, pc=0x100):
    """Force the manager into EXECUTING state via internal state_reg."""
    dut._id("state_reg", extended=False).value = MGR_EXECUTING
    dut._id("pc_reg", extended=False).value = pc
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)


async def feed_instr(dut, instr_val):
    """Feed one decoded instruction, wait for handshake."""
    await RisingEdge(dut.clk)
    dut.decoded_instr_i.value = instr_val
    dut.decoded_valid_i.value = 1
    await RisingEdge(dut.clk)
    dut.decoded_valid_i.value = 0
    # Keep decoded_instr_i stable (needed for DMAGO handshake, DMAWFE wait)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)


async def wait_cycles(dut, n):
    for _ in range(n):
        await RisingEdge(dut.clk)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_01_reset(dut):
    """After reset: MGR_STOPPED, PC=0."""
    cr = await setup(dut)
    await RisingEdge(dut.clk)
    assert await get_state(dut) == MGR_STOPPED
    assert await get_pc(dut) == 0


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_02_dmago(dut):
    """DMAGO: ch_start_req[channel] asserted, ch_start_pc set from imm32."""
    cr = await setup(dut)
    await force_executing(dut, pc=0x200)

    # DMAGO channel 2, start_pc=0x1000
    instr = pack_decoded_instr(opcode=OPC_DMAGO, instr_len=INSTR_LEN_2B,
                               periph_num=2, imm32=0x1000)
    await RisingEdge(dut.clk)
    dut.decoded_instr_i.value = instr
    dut.decoded_valid_i.value = 1
    await RisingEdge(dut.clk)  # handshake
    dut.decoded_valid_i.value = 0

    # ch_start_req[2] should pulse
    await ReadOnly()
    req = int(dut.ch_start_req.value)
    assert (req >> 2) & 1, f"ch_start_req={req:04b}, expected bit 2 set"

    # Provide ack so manager can advance PC
    await RisingEdge(dut.clk)
    dut.ch_start_ack.value = 1 << 2
    await wait_cycles(dut, 4)
    dut.ch_start_ack.value = 0


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_03_dmakill(dut):
    """DMAKILL: ch_kill_req[channel] asserted."""
    cr = await setup(dut)
    await force_executing(dut, pc=0x200)

    # DMAKILL channel 1
    instr = pack_decoded_instr(opcode=OPC_DMAKILL, instr_len=INSTR_LEN_1B,
                               periph_num=1)
    await RisingEdge(dut.clk)
    dut.decoded_instr_i.value = instr
    dut.decoded_valid_i.value = 1
    await RisingEdge(dut.clk)  # handshake + process
    dut.decoded_valid_i.value = 0

    # ch_kill_req[1] should pulse
    found = False
    for _ in range(5):
        await ReadOnly()
        kill = int(dut.ch_kill_req.value)
        if (kill >> 1) & 1:
            found = True
            break
        await RisingEdge(dut.clk)
    assert found, f"ch_kill_req never asserted for ch1, got {int(dut.ch_kill_req.value):04b}"


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_04_dmawfe(dut):
    """DMAWFE: transition to MGR_WAITING_FOR_EVENT."""
    cr = await setup(dut)
    await force_executing(dut, pc=0x200)

    instr = pack_decoded_instr(opcode=OPC_DMAWFE, instr_len=INSTR_LEN_2B,
                               event_num=3)
    # Feed and hold the instruction on the bus (cur_instr used while waiting)
    await RisingEdge(dut.clk)
    dut.decoded_instr_i.value = instr
    dut.decoded_valid_i.value = 1
    await RisingEdge(dut.clk)
    dut.decoded_valid_i.value = 0
    await wait_cycles(dut, 2)

    assert await get_state(dut) == MGR_WAITING_FOR_EVENT, \
        f"State={await get_state(dut)}, expected WAITING_FOR_EVENT"


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_05_event_received(dut):
    """Event received → back to EXECUTING, PC advanced."""
    cr = await setup(dut)
    await force_executing(dut, pc=0x200)

    instr = pack_decoded_instr(opcode=OPC_DMAWFE, instr_len=INSTR_LEN_2B,
                               event_num=5)
    await RisingEdge(dut.clk)
    dut.decoded_instr_i.value = instr
    dut.decoded_valid_i.value = 1
    await RisingEdge(dut.clk)
    dut.decoded_valid_i.value = 0
    await wait_cycles(dut, 3)
    assert await get_state(dut) == MGR_WAITING_FOR_EVENT

    # Send event 5
    pc_before = await get_pc(dut)
    await RisingEdge(dut.clk)
    dut.event_received.value = 1 << 5
    await wait_cycles(dut, 3)
    dut.event_received.value = 0

    assert await get_state(dut) == MGR_EXECUTING, \
        f"State after event={await get_state(dut)}, expected EXECUTING"
    pc_after = await get_pc(dut)
    assert pc_after > pc_before, f"PC should advance: before={pc_before:#x} after={pc_after:#x}"


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_06_dmaend(dut):
    """DMAEND: MGR_EXECUTING → MGR_STOPPED."""
    cr = await setup(dut)
    await force_executing(dut, pc=0x200)

    instr = pack_decoded_instr(opcode=OPC_DMAEND, instr_len=INSTR_LEN_1B)
    await feed_instr(dut, instr)
    await wait_cycles(dut, 2)

    assert await get_state(dut) == MGR_STOPPED, \
        f"State after DMAEND={await get_state(dut)}, expected STOPPED"


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_07_fault(dut):
    """Fault on invalid instruction: FAULT_COMPLETING → FAULT_LOCKED."""
    cr = await setup(dut)
    await force_executing(dut, pc=0x200)

    # Feed instruction with fault=1
    instr = pack_decoded_instr(opcode=OPC_DMANOP, fault=1, instr_len=INSTR_LEN_1B)
    await feed_instr(dut, instr)
    await wait_cycles(dut, 4)

    st = await get_state(dut)
    assert st == MGR_FAULT_LOCKED, \
        f"State after fault={st}, expected FAULT_LOCKED ({MGR_FAULT_LOCKED})"

    await ReadOnly()
    fault = int(dut.fault_o.value)
    assert fault == 1, f"fault_o={fault}, expected 1 (held high in LOCKED)"


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_08_dbginject(dut):
    """Debug injection: DMAGO from STOPPED via dbginject."""
    cr = await setup(dut)
    assert await get_state(dut) == MGR_STOPPED

    # Inject DMAGO channel 0, PC=0x5000
    inj = pack_decoded_instr(opcode=OPC_DMAGO, periph_num=0, imm32=0x5000)
    await RisingEdge(dut.clk)
    dut.dbginject_instr.value = inj
    dut.dbginject_valid.value = 1
    await RisingEdge(dut.clk)
    dut.dbginject_valid.value = 0

    # Check ch_start_req[0] pulsed
    found = False
    for _ in range(5):
        await ReadOnly()
        req = int(dut.ch_start_req.value)
        if req & 1:
            found = True
            break
        await RisingEdge(dut.clk)
    assert found, f"ch_start_req[0] not asserted after dbginject DMAGO"

    # State should still be STOPPED (injection doesn't change state)
    assert await get_state(dut) == MGR_STOPPED


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_09_clear_fault(dut):
    """dbgcmd_clear_fault: FAULT_LOCKED → STOPPED."""
    cr = await setup(dut)
    await force_executing(dut, pc=0x200)

    # Trigger fault
    instr = pack_decoded_instr(opcode=OPC_DMANOP, fault=1, instr_len=INSTR_LEN_1B)
    await feed_instr(dut, instr)
    await wait_cycles(dut, 4)
    assert await get_state(dut) == MGR_FAULT_LOCKED

    # Clear fault
    await RisingEdge(dut.clk)
    dut.dbgcmd_clear_fault.value = 1
    await RisingEdge(dut.clk)
    dut.dbgcmd_clear_fault.value = 0
    await wait_cycles(dut, 3)

    assert await get_state(dut) == MGR_STOPPED, \
        f"State after clear_fault={await get_state(dut)}, expected STOPPED"
    assert int(dut.fault_o.value) == 0, "fault_o should be 0 after clear"


@cocotb.test(timeout_time=200, timeout_unit="us")
async def test_10_dmago_dmakill_sequence(dut):
    """Sequence: DMAGO ch0 → DMAKILL ch0."""
    cr = await setup(dut)
    await force_executing(dut, pc=0x200)

    # DMAGO channel 0, start_pc=0x8000
    instr = pack_decoded_instr(opcode=OPC_DMAGO, instr_len=INSTR_LEN_2B,
                               periph_num=0, imm32=0x8000)
    await RisingEdge(dut.clk)
    dut.decoded_instr_i.value = instr
    dut.decoded_valid_i.value = 1
    await RisingEdge(dut.clk)
    dut.decoded_valid_i.value = 0

    # Wait for start_req pulse
    for _ in range(5):
        await ReadOnly()
        if int(dut.ch_start_req.value) & 1:
            break
        await RisingEdge(dut.clk)

    # Ack the DMAGO
    await RisingEdge(dut.clk)
    dut.ch_start_ack.value = 1
    await wait_cycles(dut, 4)
    dut.ch_start_ack.value = 0

    # Now in EXECUTING with dmago_active=0
    assert await get_state(dut) == MGR_EXECUTING

    # DMAKILL channel 0 — poll for the single-cycle pulse during feed
    instr = pack_decoded_instr(opcode=OPC_DMAKILL, instr_len=INSTR_LEN_1B,
                               periph_num=0)
    await RisingEdge(dut.clk)
    dut.decoded_instr_i.value = instr
    dut.decoded_valid_i.value = 1

    found = False
    for _ in range(10):
        await RisingEdge(dut.clk)
        if int(dut.ch_kill_req.value) & 1:
            found = True
            break
    await RisingEdge(dut.clk)
    dut.decoded_valid_i.value = 0
    assert found, "ch_kill_req[0] not asserted"
