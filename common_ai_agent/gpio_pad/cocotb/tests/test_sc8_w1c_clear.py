
# ============================================================================
# test_sc8_w1c_clear.py — SC8: Write-1-to-clear INTSTAT
# ============================================================================
import cocotb
import logging
from cocotb.triggers import ClockCycles
from pyuvm import *
from env.gpio_env import GpioEnv
from sequences.apb_seq import apb_write, apb_read, ADDR_DIR, ADDR_INTEN, ADDR_INTSTAT, ADDR_INTCLEAR

@cocotb.test()
async def test_sc8_w1c_clear(dut):
    """SC8: Trigger interrupt, clear via W1C, verify partial clear and write-0 no-op."""
    env = GpioEnv("env")
    await env.start_components()

    # Reset
    dut.presetn.value = 0
    await ClockCycles(dut.pclk, 5)
    dut.presetn.value = 1
    await ClockCycles(dut.pclk, 3)

    apb_seqr = env.apb_agent.sequencer
    uvmlog = logging.getLogger("SC8")

    # Enable interrupts on pins 0 and 1
    await apb_write(apb_seqr, ADDR_DIR, 0x00000000)
    await apb_write(apb_seqr, ADDR_INTEN, 0x00000003)
    await apb_write(apb_seqr, ADDR_INTCLEAR, 0xFFFFFFFF)
    await ClockCycles(dut.pclk, 2)

    # Trigger edges on both pins
    dut.gpio_in.value = 0x00000003
    await ClockCycles(dut.pclk, 5)

    intstat = await apb_read(apb_seqr, ADDR_INTSTAT)
    if intstat != 0x00000003:
        uvmlog.error(f"[FAIL] SC8: INTSTAT after edges=0x{intstat:08X}, expected 0x00000003")

    # W1C only pin 0
    await apb_write(apb_seqr, ADDR_INTCLEAR, 0x00000001)
    await ClockCycles(dut.pclk, 2)
    intstat2 = await apb_read(apb_seqr, ADDR_INTSTAT)

    if intstat2 == 0x00000002:
        uvmlog.info(f"[PASS] SC8 (partial): Cleared pin0, INTSTAT=0x{intstat2:08X}")
    else:
        uvmlog.error(f"[FAIL] SC8 (partial): INTSTAT=0x{intstat2:08X}, expected 0x00000002")

    # Write-0 to un-cleared pin1 → should NOT clear
    await apb_write(apb_seqr, ADDR_INTCLEAR, 0x00000000)
    await ClockCycles(dut.pclk, 2)
    intstat3 = await apb_read(apb_seqr, ADDR_INTSTAT)

    if intstat3 == 0x00000002:
        uvmlog.info(f"[PASS] SC8 (no-op): Write-0 did not clear, INTSTAT=0x{intstat3:08X}")
    else:
        uvmlog.error(f"[FAIL] SC8 (no-op): Write-0 changed INTSTAT to 0x{intstat3:08X}")

    # Check IRQ is deasserted (only pin1 active)
    irq = int(dut.gpio_irq.value)
    if irq == 1:
        uvmlog.info(f"[PASS] SC8: gpio_irq={irq} (pin1 still pending)")
    else:
        uvmlog.error(f"[FAIL] SC8: gpio_irq={irq}, expected 1")

    # Clear pin1 too
    await apb_write(apb_seqr, ADDR_INTCLEAR, 0x00000002)
    await ClockCycles(dut.pclk, 2)
    intstat4 = await apb_read(apb_seqr, ADDR_INTSTAT)
    irq_final = int(dut.gpio_irq.value)

    if intstat4 == 0 and irq_final == 0:
        uvmlog.info(f"[PASS] SC8: All cleared — INTSTAT=0, gpio_irq=0")
    else:
        uvmlog.error(f"[FAIL] SC8 final: INTSTAT=0x{intstat4:08X} gpio_irq={irq_final}")
