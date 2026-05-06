
# ============================================================================
# test_sc3_reg_readback.py — SC3: APB readback of DIR/OUT/INTEN registers
# ============================================================================
import cocotb
import logging
from cocotb.triggers import ClockCycles
from pyuvm import *
from env.gpio_env import GpioEnv
from sequences.apb_seq import apb_write, apb_read, ADDR_DIR, ADDR_OUT, ADDR_IN, ADDR_INTEN, ADDR_INTSTAT, ADDR_INTCLEAR

@cocotb.test()
async def test_sc3_reg_readback(dut):
    """SC3: Write all R/W registers, read back, verify."""
    env = GpioEnv("env")
    await env.start_components()

    # Reset
    dut.presetn.value = 0
    await ClockCycles(dut.pclk, 5)
    dut.presetn.value = 1
    await ClockCycles(dut.pclk, 3)

    apb_seqr = env.apb_agent.sequencer
    uvmlog = logging.getLogger("SC3")

    # Write patterns to all writable registers
    pat_dir  = 0xAAAAAAAA
    pat_out  = 0x55555555
    pat_inten = 0xFFFFFFFF

    await apb_write(apb_seqr, ADDR_DIR, pat_dir)
    await apb_write(apb_seqr, ADDR_OUT, pat_out)
    await apb_write(apb_seqr, ADDR_INTEN, pat_inten)

    # Read back and verify
    rd_dir  = await apb_read(apb_seqr, ADDR_DIR)
    rd_out  = await apb_read(apb_seqr, ADDR_OUT)
    rd_inten = await apb_read(apb_seqr, ADDR_INTEN)

    failures = 0
    if rd_dir != pat_dir:
        uvmlog.error(f"[FAIL] DIR: wrote 0x{pat_dir:08X} read 0x{rd_dir:08X}")
        failures += 1
    if rd_out != pat_out:
        uvmlog.error(f"[FAIL] OUT: wrote 0x{pat_out:08X} read 0x{rd_out:08X}")
        failures += 1
    if rd_inten != pat_inten:
        uvmlog.error(f"[FAIL] INTEN: wrote 0x{pat_inten:08X} read 0x{rd_inten:08X}")
        failures += 1

    # RO registers should read 0 at this point (no edges, no signals)
    rd_in = await apb_read(apb_seqr, ADDR_IN)
    rd_stat = await apb_read(apb_seqr, ADDR_INTSTAT)
    rd_clear = await apb_read(apb_seqr, ADDR_INTCLEAR)

    if failures == 0:
        uvmlog.info(f"[PASS] SC3: All R/W register readbacks match")
    else:
        uvmlog.error(f"[FAIL] SC3: {failures} register mismatch(es)")

    uvmlog.info(f"SC3: IN=0x{rd_in:08X} INTSTAT=0x{rd_stat:08X} INTCLEAR_rd=0x{rd_clear:08X}")
