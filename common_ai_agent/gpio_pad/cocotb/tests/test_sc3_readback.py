
# ============================================================================
# test_sc3_readback.py — SC3: APB read back DIR/OUT/INTEN registers
# ============================================================================
import cocotb
import logging
from cocotb.triggers import ClockCycles
from pyuvm import *
from env.gpio_env import GpioEnv
from sequences.apb_seq import apb_write, apb_read, ADDR_DIR, ADDR_OUT, ADDR_INTEN

@cocotb.test()
async def test_sc3_readback(dut):
    """SC3: Write DIR/OUT/INTEN, then read back each via APB."""
    env = GpioEnv("env")
    await env.start_components()

    # Reset
    dut.presetn.value = 0
    await ClockCycles(dut.pclk, 5)
    dut.presetn.value = 1
    await ClockCycles(dut.pclk, 3)

    # Get APB sequencer handle
    apb_seqr = env.apb_agent.sequencer
    uvmlog = logging.getLogger("SC3")

    # Values to test
    dir_val  = 0xAAAAAAAA  # alternating bits for direction
    out_val  = 0x55555555  # complementary pattern for output
    inten_val = 0x0000FFFF  # lower 16 interrupts enabled

    # Write registers
    await apb_write(apb_seqr, ADDR_DIR, dir_val)
    await apb_write(apb_seqr, ADDR_OUT, out_val)
    await apb_write(apb_seqr, ADDR_INTEN, inten_val)

    await ClockCycles(dut.pclk, 2)

    # Read back each register
    dir_rd  = await apb_read(apb_seqr, ADDR_DIR)
    out_rd  = await apb_read(apb_seqr, ADDR_OUT)
    inten_rd = await apb_read(apb_seqr, ADDR_INTEN)

    # Verify readback matches written value
    all_pass = True
    if dir_rd != dir_val:
        uvmlog.error(f"[FAIL] SC3 DIR readback: wrote 0x{dir_val:08X}, got 0x{dir_rd:08X}")
        all_pass = False
    if out_rd != out_val:
        uvmlog.error(f"[FAIL] SC3 OUT readback: wrote 0x{out_val:08X}, got 0x{out_rd:08X}")
        all_pass = False
    if inten_rd != inten_val:
        uvmlog.error(f"[FAIL] SC3 INTEN readback: wrote 0x{inten_val:08X}, got 0x{inten_rd:08X}")
        all_pass = False

    if all_pass:
        uvmlog.info(f"[PASS] SC3: DIR=0x{dir_rd:08X} OUT=0x{out_rd:08X} INTEN=0x{inten_rd:08X}")

    assert all_pass, "SC3 readback failed"
