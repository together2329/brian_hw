"""cocotb FL-vs-RTL test for uart_tx.

Deep observation: the testbench drives APB stimulus, then DESERIALISES the
real serial `tx` line bit-by-bit at baud centres and compares the recovered
10-bit frame against the generated FunctionalModel via EquivalenceScoreboard.

After the first mutation-guard pass (kill_rate 61%) the surviving mutants
flagged unobserved behaviour. This revision closes those gaps:
  - PREADY / PSLVERR are FL-compared on every accepted transaction.
  - The idle-high `tx` invariant is checked after each frame (not only reset).
  - STATUS (busy/done) is checked full-word after completion (a cycle-level
    truth the untimed FL does not model, so it is a direct TB invariant).
"""
from __future__ import annotations

import os
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge

from equivalence_scoreboard import EquivalenceScoreboard  # runtime helper on python_search

DIV = 4  # clocks-per-bit used in this test

ADDR_CTRL = 0x0
ADDR_DIV = 0x4
ADDR_TXDATA = 0x8
ADDR_STATUS = 0xC


def _project_root() -> Path:
    return Path(os.environ.get("PROJECT_ROOT") or Path(__file__).resolve().parents[3])


async def _reset(dut):
    dut.PSEL.value = 0
    dut.PENABLE.value = 0
    dut.PWRITE.value = 0
    dut.PADDR.value = 0
    dut.PWDATA.value = 0
    dut.PRESETn.value = 0
    await ClockCycles(dut.PCLK, 4)
    await RisingEdge(dut.PCLK)
    dut.PRESETn.value = 1
    await RisingEdge(dut.PCLK)


async def apb_write(dut, addr, data):
    """Drive an APB-Lite write; return (PREADY, PSLVERR) sampled in access phase."""
    await RisingEdge(dut.PCLK)
    dut.PADDR.value = addr
    dut.PWDATA.value = data
    dut.PWRITE.value = 1
    dut.PSEL.value = 1
    dut.PENABLE.value = 0
    await RisingEdge(dut.PCLK)      # setup phase
    dut.PENABLE.value = 1           # access phase -> apb_write sampled this edge
    await RisingEdge(dut.PCLK)      # registered effect (busy/frame/regs) lands here
    pready = int(dut.PREADY.value) & 1
    pslverr = int(dut.PSLVERR.value) & 1
    dut.PSEL.value = 0
    dut.PENABLE.value = 0
    dut.PWRITE.value = 0
    return pready, pslverr


async def apb_read(dut, addr):
    """Drive an APB-Lite read; return (PRDATA, PREADY, PSLVERR)."""
    await RisingEdge(dut.PCLK)
    dut.PADDR.value = addr
    dut.PWRITE.value = 0
    dut.PSEL.value = 1
    dut.PENABLE.value = 0
    await RisingEdge(dut.PCLK)
    dut.PENABLE.value = 1
    await RisingEdge(dut.PCLK)
    val = int(dut.PRDATA.value)
    pready = int(dut.PREADY.value) & 1
    pslverr = int(dut.PSLVERR.value) & 1
    dut.PSEL.value = 0
    dut.PENABLE.value = 0
    return val, pready, pslverr


async def deserialize_frame(dut):
    """Sample tx at the centre of each of the 10 bit periods.

    Returns (frame, bits, busy_mid). bit0 = first transmitted bit (start)."""
    bits = []
    await ClockCycles(dut.PCLK, DIV // 2)      # move to centre of start bit
    busy_mid = int(dut.tx_busy.value) & 1       # busy is high throughout the frame
    for _ in range(10):
        bits.append(int(dut.tx.value) & 1)
        await ClockCycles(dut.PCLK, DIV)        # advance to next bit centre
    frame = 0
    for i, b in enumerate(bits):
        frame |= (b & 1) << i
    return frame, bits, busy_mid


@cocotb.test()
async def fl_vs_rtl(dut):
    root = _project_root()
    sb = EquivalenceScoreboard(ip="uart_tx", root=str(root), reset_events=True)
    failures: list[str] = []

    def expect(cond, msg):
        if not cond:
            dut._log.error(f"INVARIANT FAIL {msg}")
            failures.append(msg)

    def check(goal_id, *, stimulus, rtl_observed, scenario_id="", coverage_refs=None):
        row = sb.record(
            goal_id,
            scenario_id=scenario_id or goal_id,
            stimulus=stimulus,
            rtl_observed=rtl_observed,
            coverage_refs=coverage_refs,
        )
        tag = f"{goal_id}/{scenario_id or goal_id}"
        if row["passed"]:
            dut._log.info(f"PASS {tag} observed={rtl_observed}")
        else:
            dut._log.error(f"FAIL {tag} mismatch={row['mismatch']} observed={rtl_observed}")
            failures.append(f"{tag}: {row['mismatch']}")
        return row

    cocotb.start_soon(Clock(dut.PCLK, 10, units="ns").start())
    await _reset(dut)

    # ---- SC1: reset / idle (idle line MUST be high) ------------------------
    idle_tx = int(dut.tx.value) & 1
    idle_busy = int(dut.tx_busy.value) & 1
    expect(idle_tx == 1, "SC1: tx must idle high after reset")
    expect(idle_busy == 0, "SC1: tx_busy must be 0 after reset")
    check("EQ_SCENARIO_SC1",
          scenario_id="SC1",
          stimulus={"pwdata": 0, "paddr": ADDR_STATUS, "psel": 0, "penable": 0, "pwrite": 0},
          rtl_observed={"tx": idle_tx, "tx_busy": idle_busy})

    # ---- enable + set divisor (handshake observed) -------------------------
    pr, pe = await apb_write(dut, ADDR_CTRL, 0x1)
    expect(pr == 1 and pe == 0, "CTRL write: PREADY=1/PSLVERR=0")
    pr, pe = await apb_write(dut, ADDR_DIV, DIV)
    expect(pr == 1 and pe == 0, "DIV write: PREADY=1/PSLVERR=0")
    sb.model.csr_write(ADDR_CTRL, 0x1)
    sb.model.csr_write(ADDR_DIV, DIV)

    ctrl_rb, pr, pe = await apb_read(dut, ADDR_CTRL)
    expect(pr == 1 and pe == 0, "CTRL read: PREADY=1/PSLVERR=0")
    check("EQ_REGISTER_CTRL",
          stimulus={"op": "read", "addr": ADDR_CTRL, "paddr": ADDR_CTRL, "psel": 1, "penable": 1, "pwrite": 0},
          rtl_observed={"PRDATA": ctrl_rb})
    div_rb, _, _ = await apb_read(dut, ADDR_DIV)
    check("EQ_REGISTER_DIV",
          stimulus={"op": "read", "addr": ADDR_DIV, "paddr": ADDR_DIV, "psel": 1, "penable": 1, "pwrite": 0},
          rtl_observed={"PRDATA": div_rb})

    # ---- transmit boundary/representative bytes; deep serial compare -------
    for scen, byte in (("SC2", 0xA5), ("SC3", 0x00), ("SC4", 0xFF)):
        while int(dut.tx_busy.value) & 1:
            await RisingEdge(dut.PCLK)
        w_pready, w_pslverr = await apb_write(dut, ADDR_TXDATA, byte)
        frame, bits, busy_mid = await deserialize_frame(dut)
        dut._log.info(f"{scen} byte=0x{byte:02X} deser_frame=0x{frame:03X} bits={bits} busy_mid={busy_mid}")
        stim = {"pwdata": byte, "paddr": ADDR_TXDATA, "psel": 1, "penable": 1, "pwrite": 1}
        # FL-compared: frame + busy + handshake lines
        obs = {"tx_frame": frame, "tx_busy": busy_mid, "PREADY": w_pready, "PSLVERR": w_pslverr}
        check("EQ_TRANSACTION_FM_TX_LOAD", scenario_id=scen, stimulus=stim, rtl_observed=obs)
        check(f"EQ_SCENARIO_{scen}", scenario_id=scen, stimulus=stim, rtl_observed=obs)

        # cycle-level invariants the untimed FL does not model -> direct checks
        while int(dut.tx_busy.value) & 1:
            await RisingEdge(dut.PCLK)
        await ClockCycles(dut.PCLK, 2)
        expect(int(dut.tx.value) == 1, f"{scen}: tx must return to idle-high after frame")
        status, pr, pe = await apb_read(dut, ADDR_STATUS)
        expect(pr == 1 and pe == 0, f"{scen}: STATUS read PREADY=1/PSLVERR=0")
        # STATUS = {done, busy} at bits[1:0]; after completion busy=0, done=1 -> 0b10
        expect(status == 0b10, f"{scen}: STATUS must read busy=0,done=1 after frame (got 0x{status:X})")

    # ---- SC5: write while busy is ignored ----------------------------------
    while int(dut.tx_busy.value) & 1:
        await RisingEdge(dut.PCLK)
    await apb_write(dut, ADDR_TXDATA, 0xA5)
    await ClockCycles(dut.PCLK, DIV)
    await apb_write(dut, ADDR_TXDATA, 0x3C)         # must be ignored
    busy_mid = int(dut.tx_busy.value) & 1
    check("EQ_TRANSACTION_FM_TX_IGNORE",
          scenario_id="SC5",
          stimulus={"pwdata": 0x3C, "paddr": ADDR_TXDATA, "psel": 1, "penable": 1, "pwrite": 1, "busy_q": 1, "enable_q": 1},
          rtl_observed={"tx_busy": busy_mid})

    # ---- SC6: write while disabled is ignored ------------------------------
    while int(dut.tx_busy.value) & 1:
        await RisingEdge(dut.PCLK)
    await apb_write(dut, ADDR_CTRL, 0x0)            # disable
    await apb_write(dut, ADDR_TXDATA, 0xA5)         # must be ignored
    await ClockCycles(dut.PCLK, 2)
    busy_dis = int(dut.tx_busy.value) & 1
    tx_dis = int(dut.tx.value) & 1
    expect(busy_dis == 0, "SC6: disabled write must not start a frame")
    expect(tx_dis == 1, "SC6: tx stays idle-high when disabled")
    check("EQ_TRANSACTION_FM_TX_IGNORE",
          scenario_id="SC6",
          stimulus={"pwdata": 0xA5, "paddr": ADDR_TXDATA, "psel": 1, "penable": 1, "pwrite": 1, "busy_q": 0, "enable_q": 0},
          rtl_observed={"tx_busy": busy_dis, "tx": tx_dis})

    dut._log.info(f"covered goals = {sorted(sb.covered_goal_ids)}")
    dut._log.info(f"missing required goals = {sb.missing_required_goals()}")

    assert not failures, "FL-vs-RTL / invariant failures:\n" + "\n".join(failures)
