
# ============================================================================
# test_sc1_basic_out.py — SC1: Direction output + write data
# ============================================================================
import cocotb
import logging
from cocotb.triggers import ClockCycles, RisingEdge
from pyuvm import *
from env.gpio_env import GpioEnv
from sequences.apb_seq import apb_write, apb_read, ADDR_DIR, ADDR_OUT

@cocotb.test()
async def test_sc1_basic_out(dut):
    """SC1: Set direction to output, write data, verify pads."""
    env = GpioEnv("env")
    await env.start_components()

    # Reset
    dut.presetn.value = 0
    await ClockCycles(dut.pclk, 5)
    dut.presetn.value = 1
    await ClockCycles(dut.pclk, 3)

    # Get APB sequencer handle
    apb_seqr = env.apb_agent.sequencer

    # Set all pads as outputs
    await apb_write(apb_seqr, ADDR_DIR, 0xFFFFFFFF)
    # Write output data
    test_val = 0xDEADBEEF
    await apb_write(apb_seqr, ADDR_OUT, test_val)

    # Wait for output to stabilize
    await ClockCycles(dut.pclk, 3)

    # Verify pad outputs
    oe = int(dut.gpio_oe.value)
    out_val = int(dut.gpio_out.value)

    uvmlog = logging.getLogger("SC1")
    if oe == 0xFFFFFFFF and out_val == test_val:
        uvmlog.info(f"[PASS] SC1: gpio_oe=0x{oe:08X} gpio_out=0x{out_val:08X}")
    else:
        uvmlog.error(f"[FAIL] SC1: gpio_oe=0x{oe:08X} gpio_out=0x{out_val:08X} exp_oe=0xFFFFFFFF exp_out=0x{test_val:08X}")

    # Read back DIR and OUT registers
    dir_rd = await apb_read(apb_seqr, ADDR_DIR)
    out_rd = await apb_read(apb_seqr, ADDR_OUT)
    assert dir_rd == 0xFFFFFFFF, f"DIR readback mismatch: {dir_rd:#x}"
    assert out_rd == test_val, f"OUT readback mismatch: {out_rd:#x}"

    uvmlog.info("[PASS] SC1 register readback OK")
