# ============================================================================
# test_sc9_output_no_irq.py — SC9: Output pin does not generate interrupt
# ============================================================================
import cocotb
import logging
from cocotb.triggers import ClockCycles, RisingEdge
from pyuvm import *
from env.gpio_env import GpioEnv
from sequences.apb_seq import apb_write, apb_read
from sequences.apb_seq import (
    ADDR_DIR, ADDR_OUT, ADDR_INTEN, ADDR_INTSTAT, ADDR_INTCLEAR
)

@cocotb.test()
async def test_sc9_output_no_irq(dut):
    """SC9: When DIR=1 (output), pin toggles do NOT set INTSTAT or gpio_irq."""
    env = GpioEnv("env")
    await env.start_components()

    # Reset
    dut.presetn.value = 0
    await ClockCycles(dut.pclk, 5)
    dut.presetn.value = 1
    await ClockCycles(dut.pclk, 3)

    apb_seqr = env.apb_agent.sequencer
    uvmlog = logging.getLogger("SC9")

    # Configure pin 0 as output
    await apb_write(apb_seqr, ADDR_DIR, 0x00000001)
    # Write output data so pin toggles are visible on gpio_out
    await apb_write(apb_seqr, ADDR_OUT, 0x00000000)
    # Enable interrupt for pin 0
    await apb_write(apb_seqr, ADDR_INTEN, 0x00000001)
    # Clear any pending
    await apb_write(apb_seqr, ADDR_INTCLEAR, 0xFFFFFFFF)

    await ClockCycles(dut.pclk, 5)

    # Toggle the output by writing OUT register
    await apb_write(apb_seqr, ADDR_OUT, 0x00000001)
    await ClockCycles(dut.pclk, 3)
    await apb_write(apb_seqr, ADDR_OUT, 0x00000000)
    await ClockCycles(dut.pclk, 3)

    # Check gpio_irq is low
    irq_val = int(dut.gpio_irq.value)
    intstat = await apb_read(apb_seqr, ADDR_INTSTAT)

    all_pass = True
    if irq_val != 0:
        uvmlog.error(f"[FAIL] SC9: gpio_irq={irq_val} (expected 0) for output pin")
        all_pass = False
    else:
        uvmlog.info(f"[PASS] SC9: gpio_irq={irq_val} for output pin toggle")

    if intstat != 0:
        uvmlog.error(f"[FAIL] SC9: INTSTAT=0x{intstat:08X} (expected 0)")
        all_pass = False
    else:
        uvmlog.info(f"[PASS] SC9: INTSTAT=0 (no edge detect on output pin)")

    assert all_pass, "SC9 output pin no interrupt failed"
