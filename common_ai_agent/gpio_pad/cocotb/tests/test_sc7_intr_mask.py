
# ============================================================================
# test_sc7_intr_mask.py — SC7: Interrupt mask blocks detection
# ============================================================================
import cocotb
import logging
from cocotb.triggers import ClockCycles
from pyuvm import *
from env.gpio_env import GpioEnv
from sequences.apb_seq import apb_write, apb_read, ADDR_DIR, ADDR_INTEN, ADDR_INTSTAT, ADDR_INTCLEAR

@cocotb.test()
async def test_sc7_intr_mask(dut):
    """SC7: With INTEN=0, toggle pin, verify no interrupt. Then enable."""
    env = GpioEnv("env")
    await env.start_components()

    # Reset
    dut.presetn.value = 0
    await ClockCycles(dut.pclk, 5)
    dut.presetn.value = 1
    await ClockCycles(dut.pclk, 3)

    apb_seqr = env.apb_agent.sequencer
    uvmlog = logging.getLogger("SC7")

    # Keep DIR=0 (inputs), INTEN=0 (all masked)
    await apb_write(apb_seqr, ADDR_DIR, 0x00000000)
    await apb_write(apb_seqr, ADDR_INTEN, 0x00000000)
    await apb_write(apb_seqr, ADDR_INTCLEAR, 0xFFFFFFFF)
    await ClockCycles(dut.pclk, 2)

    # Toggle gpio_in[0]
    dut.gpio_in.value = 0x00000001
    await ClockCycles(dut.pclk, 5)

    intstat = await apb_read(apb_seqr, ADDR_INTSTAT)
    irq = int(dut.gpio_irq.value)

    if (intstat & 1) == 0 and irq == 0:
        uvmlog.info(f"[PASS] SC7 (masked): INTSTAT=0x{intstat:08X} gpio_irq={irq} — correctly masked")
    else:
        uvmlog.error(f"[FAIL] SC7 (masked): INTSTAT=0x{intstat:08X} gpio_irq={irq}")

    # Now enable INTEN[0], toggle again
    await apb_write(apb_seqr, ADDR_INTEN, 0x00000001)
    dut.gpio_in.value = 0x00000000  # Back to 0
    await ClockCycles(dut.pclk, 5)
    dut.gpio_in.value = 0x00000001  # Edge 0→1 again
    await ClockCycles(dut.pclk, 5)

    intstat2 = await apb_read(apb_seqr, ADDR_INTSTAT)
    irq2 = int(dut.gpio_irq.value)

    if (intstat2 & 1) == 1 and irq2 == 1:
        uvmlog.info(f"[PASS] SC7 (enabled): INTSTAT=0x{intstat2:08X} gpio_irq={irq2} — correctly fired")
    else:
        uvmlog.error(f"[FAIL] SC7 (enabled): INTSTAT=0x{intstat2:08X} gpio_irq={irq2}")
