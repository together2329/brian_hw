# ============================================================================
# test_sc7_mask_blocks_irq.py — SC7: Interrupt mask blocks detection
# ============================================================================
import cocotb
import logging
from cocotb.triggers import ClockCycles, RisingEdge
from pyuvm import *
from env.gpio_env import GpioEnv
from sequences.apb_seq import apb_write, apb_read
from sequences.apb_seq import (
    ADDR_DIR, ADDR_INTEN, ADDR_INTSTAT, ADDR_INTCLEAR
)

@cocotb.test()
async def test_sc7_mask_blocks_irq(dut):
    """SC7: Toggle input pin with INTEN=0, verify gpio_irq stays low."""
    env = GpioEnv("env")
    await env.start_components()

    # Reset
    dut.presetn.value = 0
    await ClockCycles(dut.pclk, 5)
    dut.presetn.value = 1
    await ClockCycles(dut.pclk, 3)

    apb_seqr = env.apb_agent.sequencer
    uvmlog = logging.getLogger("SC7")

    # Set pin 0 as input (DIR=0)
    await apb_write(apb_seqr, ADDR_DIR, 0x00000000)

    # Disable all interrupts
    await apb_write(apb_seqr, ADDR_INTEN, 0x00000000)
    # Clear any pending
    await apb_write(apb_seqr, ADDR_INTCLEAR, 0xFFFFFFFF)

    await ClockCycles(dut.pclk, 3)

    # Toggle pin 0
    pin_mask = 0x00000001
    dut.gpio_in.value = pin_mask
    await ClockCycles(dut.pclk, 2)
    dut.gpio_in.value = 0x00000000
    await ClockCycles(dut.pclk, 2)

    # Check IRQ is low
    irq_val = int(dut.gpio_irq.value)
    if irq_val != 0:
        uvmlog.error(f"[FAIL] SC7: gpio_irq={irq_val} (expected 0) when INTEN=0")
    else:
        uvmlog.info(f"[PASS] SC7: gpio_irq={irq_val} when INTEN=0")

    # INTSTAT may be set (edge detection fires regardless of INTEN mask;
    # only IRQ output is gated). This is correct DUT behavior.
    intstat = await apb_read(apb_seqr, ADDR_INTSTAT)
    if intstat != 0:
        uvmlog.info(f"[INFO] SC7 INTSTAT=0x{intstat:08X} (edge detected; IRQ correctly gated)")

    assert irq_val == 0, "IRQ asserted despite INTEN=0"
