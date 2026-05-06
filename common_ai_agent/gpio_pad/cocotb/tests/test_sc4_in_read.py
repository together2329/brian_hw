
# ============================================================================
# test_sc4_in_read.py — SC4: APB read IN register during input changes
# ============================================================================
import cocotb
import logging
from cocotb.triggers import ClockCycles
from pyuvm import *
from env.gpio_env import GpioEnv
from sequences.apb_seq import apb_read, ADDR_IN

@cocotb.test()
async def test_sc4_in_read(dut):
    """SC4: Drive gpio_in with toggling patterns, read IN register each time."""
    env = GpioEnv("env")
    await env.start_components()

    # Reset
    dut.presetn.value = 0
    await ClockCycles(dut.pclk, 5)
    dut.presetn.value = 1
    await ClockCycles(dut.pclk, 3)

    apb_seqr = env.apb_agent.sequencer
    uvmlog = logging.getLogger("SC4")

    patterns = [
        0x00000000,
        0xFFFFFFFF,
        0xAAAAAAAA,
        0x55555555,
        0x12345678,
        0xDEADBEEF,
    ]

    failures = 0
    for pat in patterns:
        dut.gpio_in.value = pat
        # Wait for 2-DFF sync (3-4 cycles)
        await ClockCycles(dut.pclk, 5)
        in_val = await apb_read(apb_seqr, ADDR_IN)
        if in_val != pat:
            uvmlog.error(f"[FAIL] SC4: gpio_in=0x{pat:08X} IN=0x{in_val:08X}")
            failures += 1

    if failures == 0:
        uvmlog.info(f"[PASS] SC4: All {len(patterns)} IN readback patterns match")
    else:
        uvmlog.error(f"[FAIL] SC4: {failures} mismatch(es)")
