# ============================================================================
# test_sc5_reset_default.py — SC5: Verify reset defaults on all registers
# ============================================================================
import cocotb
import logging
from cocotb.triggers import ClockCycles
from pyuvm import *
from env.gpio_env import GpioEnv
from sequences.apb_seq import apb_read
from sequences.apb_seq import (
    ADDR_DIR, ADDR_OUT, ADDR_IN, ADDR_INTEN, ADDR_INTSTAT, ADDR_INTCLEAR
)

@cocotb.test()
async def test_sc5_reset_default(dut):
    """SC5: After reset, verify all registers = reset value (0) and gpio_oe=0."""
    env = GpioEnv("env")
    await env.start_components()

    # Assert reset
    dut.presetn.value = 0
    await ClockCycles(dut.pclk, 5)

    # Hold reset, verify pads
    gpio_oe = int(dut.gpio_oe.value)
    all_pass = True
    uvmlog = logging.getLogger("SC5")

    # After reset deassertion, verify
    dut.presetn.value = 1
    await ClockCycles(dut.pclk, 3)

    apb_seqr = env.apb_agent.sequencer

    # Read all registers
    dir_rd     = await apb_read(apb_seqr, ADDR_DIR)
    out_rd     = await apb_read(apb_seqr, ADDR_OUT)
    in_rd_mode = await apb_read(apb_seqr, ADDR_IN)
    inten_rd   = await apb_read(apb_seqr, ADDR_INTEN)
    intstat_rd = await apb_read(apb_seqr, ADDR_INTSTAT)
    intclear_rd = await apb_read(apb_seqr, ADDR_INTCLEAR)

    gpio_oe_val = int(dut.gpio_oe.value)
    gpio_out_val = int(dut.gpio_out.value)

    # Check each expected reset value (all 0)
    checks = [
        ("DIR",      dir_rd,      0x00000000),
        ("OUT",      out_rd,      0x00000000),
        ("INTEN",    inten_rd,    0x00000000),
        ("INTSTAT",  intstat_rd,  0x00000000),
        ("INTCLEAR", intclear_rd, 0x00000000),
        ("gpio_oe",  gpio_oe_val, 0x00000000),
        ("gpio_out", gpio_out_val, 0x00000000),
    ]

    for name, got, exp in checks:
        if got != exp:
            uvmlog.error(f"[FAIL] SC5 {name}: got=0x{got:08X} exp=0x{exp:08X}")
            all_pass = False

    if all_pass:
        uvmlog.info(f"[PASS] SC5: All registers at reset value, gpio_oe=0, gpio_out=0")

    assert all_pass, "SC5 reset defaults failed"