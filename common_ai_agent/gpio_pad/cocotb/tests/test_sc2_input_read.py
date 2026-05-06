
# ============================================================================
# test_sc2_input_read.py — SC2: Direction input + read pads
# ============================================================================
import cocotb
import logging
from cocotb.triggers import ClockCycles
from pyuvm import *
from env.gpio_env import GpioEnv
from sequences.apb_seq import apb_write, apb_read, ADDR_DIR, ADDR_IN, ADDR_OUT

@cocotb.test()
async def test_sc2_input_read(dut):
    """SC2: Keep DIR=0 (inputs), drive gpio_in, read IN register."""
    env = GpioEnv("env")
    await env.start_components()

    # Reset
    dut.presetn.value = 0
    await ClockCycles(dut.pclk, 5)
    dut.presetn.value = 1
    await ClockCycles(dut.pclk, 3)

    apb_seqr = env.apb_agent.sequencer

    # Keep DIR=0 (all inputs, default)
    # Drive gpio_in pattern
    test_val = 0xCAFEBABE
    dut.gpio_in.value = test_val
    # Wait for 2-DFF synchronizer (4 cycles to be safe)
    await ClockCycles(dut.pclk, 5)

    # Read IN register
    in_val = await apb_read(apb_seqr, ADDR_IN)

    uvmlog = logging.getLogger("SC2")
    if in_val == test_val:
        uvmlog.info(f"[PASS] SC2: IN register = 0x{in_val:08X} matches gpio_in")
    else:
        uvmlog.error(f"[FAIL] SC2: IN=0x{in_val:08X} expected 0x{test_val:08X}")

    # Verify gpio_oe=0 (no outputs driven)
    oe = int(dut.gpio_oe.value)
    assert oe == 0, f"gpio_oe should be 0 but got 0x{oe:08X}"
    uvmlog.info("[PASS] SC2: gpio_oe=0 confirmed")
