
# ============================================================================
# tb.py — cocotb testbench for gpio_pad (no UVM) — All 9 Scenarios
# ============================================================================
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge
import logging

# APB register addresses
ADDR_DIR      = 0x000
ADDR_OUT      = 0x004
ADDR_IN       = 0x008
ADDR_INTEN    = 0x00C
ADDR_INTSTAT  = 0x010
ADDR_INTCLEAR = 0x014

async def apb_write(addr, data):
    """Drive APB write transaction."""
    dut = cocotb.top
    dut.paddr.value = addr
    dut.pwrite.value = 1
    dut.psel.value = 1
    dut.penable.value = 0
    dut.pwdata.value = data
    dut.pstrb.value = 0xF
    await RisingEdge(dut.pclk)
    dut.penable.value = 1
    await RisingEdge(dut.pclk)
    dut.psel.value = 0
    dut.penable.value = 0
    await RisingEdge(dut.pclk)

async def apb_read(addr):
    """Drive APB read transaction and return prdata."""
    dut = cocotb.top
    dut.paddr.value = addr
    dut.pwrite.value = 0
    dut.psel.value = 1
    dut.penable.value = 0
    await RisingEdge(dut.pclk)
    dut.penable.value = 1
    await RisingEdge(dut.pclk)
    result = int(dut.prdata.value)
    await RisingEdge(dut.pclk)
    dut.psel.value = 0
    dut.penable.value = 0
    return result

async def init_dut():
    """Start clock, apply reset, initialize signals."""
    dut = cocotb.top
    dut.psel.value = 0
    dut.penable.value = 0
    dut.pwrite.value = 0
    dut.paddr.value = 0
    dut.pwdata.value = 0
    dut.pstrb.value = 0
    dut.gpio_in.value = 0
    dut.presetn.value = 0
    cocotb.start_soon(Clock(dut.pclk, 10, units="ns").start())
    await ClockCycles(dut.pclk, 5)
    dut.presetn.value = 1
    await ClockCycles(dut.pclk, 3)

pass_cnt = 0
fail_cnt = 0
uvmlog = logging.getLogger("tb")

def check(name, got, expected):
    global pass_cnt, fail_cnt
    if got == expected:
        pass_cnt += 1
        uvmlog.info(f"[PASS] {name}: got=0x{got:08X} exp=0x{expected:08X}")
    else:
        fail_cnt += 1
        uvmlog.error(f"[FAIL] {name}: got=0x{got:08X} exp=0x{expected:08X}")

async def sw_reset():
    dut = cocotb.top
    dut.presetn.value = 0
    await ClockCycles(dut.pclk, 5)
    dut.presetn.value = 1
    await ClockCycles(dut.pclk, 3)
    # Clear any stale interrupt status from previous scenarios
    await apb_write(ADDR_INTCLEAR, 0xFFFFFFFF)
    await ClockCycles(dut.pclk, 2)

# SC1: Basic output and direction
async def sc1_basic_out():
    await apb_write(ADDR_DIR, 0xFFFFFFFF)
    test_val = 0xDEADBEEF
    await apb_write(ADDR_OUT, test_val)
    await ClockCycles(cocotb.top.pclk, 3)
    oe = int(cocotb.top.gpio_oe.value)
    out_val = int(cocotb.top.gpio_out.value)
    check("SC1 oe", oe, 0xFFFFFFFF)
    check("SC1 out", out_val, test_val)
    dir_rd = await apb_read(ADDR_DIR)
    out_rd = await apb_read(ADDR_OUT)
    check("SC1 dir_rb", dir_rd, 0xFFFFFFFF)
    check("SC1 out_rb", out_rd, test_val)

# SC2: Input read
async def sc2_input_read():
    await sw_reset()
    test_val = 0xCAFEBABE
    cocotb.top.gpio_in.value = test_val
    await ClockCycles(cocotb.top.pclk, 5)  # wait for synchronizer
    in_val = await apb_read(ADDR_IN)
    check("SC2 in", in_val, test_val)
    oe = int(cocotb.top.gpio_oe.value)
    check("SC2 oe", oe, 0)

# SC3: Register readback
async def sc3_readback():
    await sw_reset()
    dir_val = 0xAAAAAAAA
    out_val = 0x55555555
    inten_val = 0x0000FFFF
    await apb_write(ADDR_DIR, dir_val)
    await apb_write(ADDR_OUT, out_val)
    await apb_write(ADDR_INTEN, inten_val)
    await ClockCycles(cocotb.top.pclk, 2)
    dir_rd = await apb_read(ADDR_DIR)
    out_rd = await apb_read(ADDR_OUT)
    inten_rd = await apb_read(ADDR_INTEN)
    check("SC3 dir_rb", dir_rd, dir_val)
    check("SC3 out_rb", out_rd, out_val)
    check("SC3 inten_rb", inten_rd, inten_val)

# SC4: IN readback with patterns
async def sc4_in_read_patterns():
    await sw_reset()
    patterns = [0x00000000, 0xFFFFFFFF, 0xAAAAAAAA, 0x55555555, 0x12345678, 0xDEADBEEF]
    for pat in patterns:
        cocotb.top.gpio_in.value = pat
        await ClockCycles(cocotb.top.pclk, 5)
        in_val = await apb_read(ADDR_IN)
        check(f"SC4 in(0x{pat:08X})", in_val, pat)

# SC5: Reset defaults
async def sc5_reset_defaults():
    await sw_reset()
    dir_rd = await apb_read(ADDR_DIR)
    out_rd = await apb_read(ADDR_OUT)
    inten_rd = await apb_read(ADDR_INTEN)
    intstat_rd = await apb_read(ADDR_INTSTAT)
    intclear_rd = await apb_read(ADDR_INTCLEAR)
    gpio_oe = int(cocotb.top.gpio_oe.value)
    gpio_out = int(cocotb.top.gpio_out.value)
    check("SC5 dir", dir_rd, 0)
    check("SC5 out", out_rd, 0)
    check("SC5 inten", inten_rd, 0)
    check("SC5 intstat", intstat_rd, 0)
    check("SC5 intclear", intclear_rd, 0)
    check("SC5 gpio_oe", gpio_oe, 0)
    check("SC5 gpio_out", gpio_out, 0)

# SC6: Edge interrupt detection
async def sc6_edge_intr():
    await sw_reset()
    # Drive gpio_in to 0 FIRST before enabling edge detection
    cocotb.top.gpio_in.value = 0x00000000
    await ClockCycles(cocotb.top.pclk, 5)  # let synchronizer settle
    await apb_write(ADDR_DIR, 0x00000000)
    await apb_write(ADDR_INTEN, 0x00000001)
    # Clear any stale INTSTAT (should be 0 already, but be safe)
    await apb_write(ADDR_INTCLEAR, 0xFFFFFFFF)
    await ClockCycles(cocotb.top.pclk, 2)
    # Toggle to 1 (clean 0→1 edge on bit 0 only)
    cocotb.top.gpio_in.value = 0x00000001
    await ClockCycles(cocotb.top.pclk, 5)
    intstat = await apb_read(ADDR_INTSTAT)
    irq = int(cocotb.top.gpio_irq.value)
    check("SC6 intstat bit0", intstat & 1, 1)
    check("SC6 irq", irq, 1)
    check("SC6 other bits", intstat & 0xFFFFFFFE, 0)

# SC7: Mask blocks IRQ
async def sc7_mask_blocks():
    await sw_reset()
    await apb_write(ADDR_DIR, 0x00000000)
    await apb_write(ADDR_INTEN, 0x00000000)
    await apb_write(ADDR_INTCLEAR, 0xFFFFFFFF)
    await ClockCycles(cocotb.top.pclk, 3)
    cocotb.top.gpio_in.value = 0x00000001
    await ClockCycles(cocotb.top.pclk, 2)
    cocotb.top.gpio_in.value = 0x00000000
    await ClockCycles(cocotb.top.pclk, 2)
    irq_val = int(cocotb.top.gpio_irq.value)
    check("SC7 irq", irq_val, 0)

# SC8: W1C clear
async def sc8_w1c_clear():
    await sw_reset()
    await apb_write(ADDR_DIR, 0x00000000)
    await apb_write(ADDR_INTEN, 0x00000003)  # pins 0,1
    await apb_write(ADDR_INTCLEAR, 0xFFFFFFFF)
    await ClockCycles(cocotb.top.pclk, 2)
    cocotb.top.gpio_in.value = 0x00000003
    await ClockCycles(cocotb.top.pclk, 5)
    intstat = await apb_read(ADDR_INTSTAT)
    check("SC8 intstat both", intstat, 0x00000003)
    # Clear pin0 only
    await apb_write(ADDR_INTCLEAR, 0x00000001)
    await ClockCycles(cocotb.top.pclk, 2)
    intstat2 = await apb_read(ADDR_INTSTAT)
    check("SC8 partial clear", intstat2, 0x00000002)
    # Write-0 no-op
    await apb_write(ADDR_INTCLEAR, 0x00000000)
    await ClockCycles(cocotb.top.pclk, 2)
    intstat3 = await apb_read(ADDR_INTSTAT)
    check("SC8 no-op", intstat3, 0x00000002)
    # IRQ still active
    irq = int(cocotb.top.gpio_irq.value)
    check("SC8 irq active", irq, 1)
    # Clear pin1
    await apb_write(ADDR_INTCLEAR, 0x00000002)
    await ClockCycles(cocotb.top.pclk, 2)
    intstat4 = await apb_read(ADDR_INTSTAT)
    irq_final = int(cocotb.top.gpio_irq.value)
    check("SC8 final intstat", intstat4, 0)
    check("SC8 final irq", irq_final, 0)

# SC9: Output pin no IRQ
async def sc9_output_no_irq():
    await sw_reset()
    await apb_write(ADDR_DIR, 0x00000001)
    await apb_write(ADDR_OUT, 0x00000000)
    await apb_write(ADDR_INTEN, 0x00000001)
    await apb_write(ADDR_INTCLEAR, 0xFFFFFFFF)
    await ClockCycles(cocotb.top.pclk, 5)
    await apb_write(ADDR_OUT, 0x00000001)
    await ClockCycles(cocotb.top.pclk, 3)
    await apb_write(ADDR_OUT, 0x00000000)
    await ClockCycles(cocotb.top.pclk, 3)
    irq_val = int(cocotb.top.gpio_irq.value)
    intstat = await apb_read(ADDR_INTSTAT)
    check("SC9 irq", irq_val, 0)
    check("SC9 intstat", intstat, 0)

@cocotb.test()
async def tb_gpio_pad(dut):
    """Run all 9 gpio_pad test scenarios."""
    global pass_cnt, fail_cnt
    pass_cnt = 0
    fail_cnt = 0
    await init_dut()

    uvmlog.info("=== SC1: Direction output + write data ===")
    await sc1_basic_out()

    uvmlog.info("=== SC2: Input read ===")
    await sc2_input_read()

    uvmlog.info("=== SC3: APB readback ===")
    await sc3_readback()

    uvmlog.info("=== SC4: IN read pattern sweep ===")
    await sc4_in_read_patterns()

    uvmlog.info("=== SC5: Reset defaults ===")
    await sc5_reset_defaults()

    uvmlog.info("=== SC6: Edge interrupt detection ===")
    await sc6_edge_intr()

    uvmlog.info("=== SC7: Interrupt mask blocks ===")
    await sc7_mask_blocks()

    uvmlog.info("=== SC8: W1C clear ===")
    await sc8_w1c_clear()

    uvmlog.info("=== SC9: Output pin no interrupt ===")
    await sc9_output_no_irq()

    uvmlog.info(f"Result: {pass_cnt}/{pass_cnt+fail_cnt} tests passed")
    assert fail_cnt == 0, f"{fail_cnt} test(s) FAILED"
