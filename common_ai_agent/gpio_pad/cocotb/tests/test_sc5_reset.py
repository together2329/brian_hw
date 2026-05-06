
# ============================================================================
# test_sc5_reset.py — SC5: Reset defaults verification
# ============================================================================
import cocotb
import logging
from cocotb.triggers import ClockCycles
from pyuvm import *
from env.gpio_env import GpioEnv
from sequences.apb_seq import apb_read, ADDR_DIR, ADDR_OUT, ADDR_IN, ADDR_INTEN, ADDR_INTSTAT, ADDR_INTCLEAR

@cocotb.test()
async def test_sc5_reset(dut):
    """SC5: Assert reset, verify all registers=0, gpio_oe=0, gpio_irq=0."""
    env = GpioEnv("env")
    await env.start_components()

    uvmlog = logging.getLogger("SC5")

    # Assert reset
    dut.presetn.value = 0
    await ClockCycles(dut.pclk, 10)

    # Check pad outputs during reset
    oe = int(dut.gpio_oe.value)
    gpio_out = int(dut.gpio_out.value)
    irq = int(dut.gpio_irq.value)

    failures = 0
    if oe != 0:
        uvmlog.error(f"[FAIL] SC5: gpio_oe=0x{oe:08X} expected 0 (during reset)")
        failures += 1
    if gpio_out != 0:
        uvmlog.error(f"[FAIL] SC5: gpio_out=0x{gpio_out:08X} expected 0 (during reset)")
        failures += 1
    if irq != 0:
        uvmlog.error(f"[FAIL] SC5: gpio_irq={irq} expected 0 (during reset)")
        failures += 1

    # Release reset
    dut.presetn.value = 1
    await ClockCycles(dut.pclk, 5)

    apb_seqr = env.apb_agent.sequencer

    # Read all registers — should be 0
    regs = {
        "DIR": await apb_read(apb_seqr, ADDR_DIR),
        "OUT": await apb_read(apb_seqr, ADDR_OUT),
        "IN": await apb_read(apb_seqr, ADDR_IN),
        "INTEN": await apb_read(apb_seqr, ADDR_INTEN),
        "INTSTAT": await apb_read(apb_seqr, ADDR_INTSTAT),
        "INTCLEAR": await apb_read(apb_seqr, ADDR_INTCLEAR),
    }

    for name, val in regs.items():
        if val != 0:
            uvmlog.error(f"[FAIL] SC5: {name} = 0x{val:08X} expected 0x00000000")
            failures += 1

    # Verify output state after reset release
    oe = int(dut.gpio_oe.value)
    irq = int(dut.gpio_irq.value)
    if oe != 0:
        uvmlog.error(f"[FAIL] SC5: gpio_oe=0x{oe:08X} after reset release, expected 0")
        failures += 1
    if irq != 0:
        uvmlog.error(f"[FAIL] SC5: gpio_irq={irq} after reset release, expected 0")
        failures += 1

    if failures == 0:
        uvmlog.info("[PASS] SC5: All registers and outputs at reset defaults")
    else:
        uvmlog.error(f"[FAIL] SC5: {failures} failure(s)")
