
# ============================================================================
# test_sc6_edge_intr.py — SC6: Edge detect triggers interrupt
# ============================================================================
import cocotb
import logging
from cocotb.triggers import ClockCycles
from pyuvm import *
from env.gpio_env import GpioEnv
from sequences.apb_seq import apb_write, apb_read, ADDR_DIR, ADDR_INTEN, ADDR_INTSTAT, ADDR_INTCLEAR

@cocotb.test()
async def test_sc6_edge_intr(dut):
    """SC6: Enable interrupt on pin 0, toggle gpio_in[0], verify INTSTAT+IRQ."""
    env = GpioEnv("env")
    await env.start_components()

    # Reset
    dut.presetn.value = 0
    await ClockCycles(dut.pclk, 5)
    dut.presetn.value = 1
    await ClockCycles(dut.pclk, 3)

    apb_seqr = env.apb_agent.sequencer
    uvmlog = logging.getLogger("SC6")

    # Keep DIR[0]=0 (input), enable interrupt on pin 0
    await apb_write(apb_seqr, ADDR_DIR, 0x00000000)
    await apb_write(apb_seqr, ADDR_INTEN, 0x00000001)

    # Clear any pending status
    await apb_write(apb_seqr, ADDR_INTCLEAR, 0xFFFFFFFF)
    await ClockCycles(dut.pclk, 2)

    # Toggle gpio_in[0] from 0 to 1 (edge)
    dut.gpio_in.value = 0x00000001
    await ClockCycles(dut.pclk, 5)  # Wait for sync + edge detect

    # Read INTSTAT
    intstat = await apb_read(apb_seqr, ADDR_INTSTAT)
    irq = int(dut.gpio_irq.value)

    if (intstat & 1) == 1 and irq == 1:
        uvmlog.info(f"[PASS] SC6: INTSTAT=0x{intstat:08X} gpio_irq={irq}")
    else:
        uvmlog.error(f"[FAIL] SC6: INTSTAT=0x{intstat:08X} (bit0={'X' if (intstat&1) else '0'}) gpio_irq={irq}")

    # Verify other pins unchanged
    if (intstat & 0xFFFFFFFE) != 0:
        uvmlog.error(f"[FAIL] SC6: Other INTSTAT bits set unexpectedly")
    else:
        uvmlog.info("[PASS] SC6: Only pin 0 interrupt set")
