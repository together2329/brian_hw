"""SSOT-driven test sequences — one per test_requirements.scenarios[] entry.

SSOT traceability:
  - test_requirements.scenarios[0..10] → SC01..SC11
  - Each sequence implements its SSOT stimulus, drives the DUT, and
    calls scoreboard methods with the correct goal_id.
"""

import random
import cocotb
from cocotb.triggers import (ClockCycles, RisingEdge, ReadOnly, Timer)
from cocotb.log import SimLog

from transactions import (
    CsrTransaction, CSR_CTRL, CSR_STATUS, CSR_SRC_ADDR, CSR_DST_ADDR,
    CSR_LENGTH, CSR_PROGRESS, VALID_CSR_OFFSETS,
    CTRL_START_BIT, CTRL_IRQ_DONE_EN, CTRL_IRQ_ERROR_EN, CTRL_SOFT_RESET,
    STATUS_BUSY_BIT, STATUS_DONE_BIT, STATUS_ERROR_BIT,
)
from agents import CsrAgent, ReadDataDriver, WriteMonitor, IrqMonitor


# ── Helpers ────────────────────────────────────────────────────────────

async def _deassert_rst(dut, cycles=5):
    """Deassert reset and wait for stabilization."""
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, cycles)


async def _assert_rst(dut, cycles=3):
    """Assert reset."""
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, cycles)


# ── SC01: reset_defaults ──────────────────────────────────────────────

async def sc01_reset_defaults(dut, csr_agent, rd_driver, sb, cov, log):
    """SC01: Assert rst_n low, deassert, check reset defaults."""
    scenario_id = "SC01"
    goal_id = "EQ_SCENARIO_SC01"
    log.info(f"=== {scenario_id}: reset_defaults ===")

    # Assert reset
    dut.rst_n.value = 0
    dut.csr_valid.value = 0
    dut.mem_rd_ready.value = 1
    dut.mem_rd_data_valid.value = 0
    dut.mem_wr_ready.value = 1
    await ClockCycles(dut.clk, 5)

    sb.set_cycle(cocotb.utils.get_sim_time(units="ns") // 10)
    ok = sb.check_reset(scenario_id, goal_id,
                        csr_ready=int(dut.csr_ready.value),
                        mem_rd_valid=int(dut.mem_rd_valid.value),
                        mem_wr_valid=int(dut.mem_wr_valid.value),
                        irq_done=int(dut.irq_done.value),
                        irq_error=int(dut.irq_error.value))
    cov.hit("SC01_executed")
    cov.hit("function_reset")

    if not ok:
        log.error(f"[FAIL] {scenario_id}: reset defaults mismatch")
    else:
        log.info(f"[PASS] {scenario_id}: reset defaults verified")
    return ok


# ── SC02: csr_programming_readback ─────────────────────────────────────

async def sc02_csr_programming_readback(dut, csr_agent, rd_driver, sb, cov, log):
    """SC02: Write SRC_ADDR, DST_ADDR, LENGTH, CTRL enables; read back all."""
    scenario_id = "SC02"
    goal_id = "EQ_SCENARIO_SC02"
    log.info(f"=== {scenario_id}: csr_programming_readback ===")

    await _deassert_rst(dut, 3)

    # Write config registers while idle
    SRC_VAL = 0x1000_0000
    DST_VAL = 0x2000_0000
    LEN_VAL = 0x0000_0040  # 64 bytes = 16 beats
    CTRL_EN = (1 << CTRL_IRQ_DONE_EN) | (1 << CTRL_IRQ_ERROR_EN)

    # Write SRC_ADDR
    resp = await csr_agent.drive_write(CSR_SRC_ADDR, SRC_VAL)
    sb.set_cycle(cocotb.utils.get_sim_time(units="ns") // 10)
    sb.check_csr_write(scenario_id, goal_id, CSR_SRC_ADDR, SRC_VAL,
                       csr_error=int(resp.error), irq_error=0)

    # Write DST_ADDR
    resp = await csr_agent.drive_write(CSR_DST_ADDR, DST_VAL)
    sb.set_cycle(cocotb.utils.get_sim_time(units="ns") // 10)
    sb.check_csr_write(scenario_id, goal_id, CSR_DST_ADDR, DST_VAL,
                       csr_error=int(resp.error), irq_error=0)

    # Write LENGTH
    resp = await csr_agent.drive_write(CSR_LENGTH, LEN_VAL)
    sb.set_cycle(cocotb.utils.get_sim_time(units="ns") // 10)
    sb.check_csr_write(scenario_id, goal_id, CSR_LENGTH, LEN_VAL,
                       csr_error=int(resp.error), irq_error=0)

    # Write CTRL (enables only, no start)
    resp = await csr_agent.drive_write(CSR_CTRL, CTRL_EN)
    sb.set_cycle(cocotb.utils.get_sim_time(units="ns") // 10)
    sb.check_csr_write(scenario_id, goal_id, CSR_CTRL, CTRL_EN,
                       csr_error=int(resp.error), irq_error=0)

    # Read back all registers
    for reg_addr, expected_word in [
        (CSR_CTRL, CTRL_EN & 0x6),       # only bits [2:1] readable
        (CSR_SRC_ADDR, SRC_VAL),
        (CSR_DST_ADDR, DST_VAL),
        (CSR_LENGTH, LEN_VAL),
        (CSR_PROGRESS, 0),
        (CSR_STATUS, 0),
    ]:
        resp = await csr_agent.drive_read(reg_addr)
        sb.set_cycle(cocotb.utils.get_sim_time(units="ns") // 10)
        sb.check_csr_read(scenario_id, goal_id, reg_addr,
                          rdata=int(resp.rdata), csr_error=int(resp.error))

    cov.hit("SC02_executed")
    cov.hit_many(["function_csr_write_config", "function_csr_read_status"])
    cov.hit("ccov_handshakes")

    ok = sb.scenario_pass(scenario_id)
    log.info(f"[{'PASS' if ok else 'FAIL'}] {scenario_id}")
    return ok


# ── SC03: illegal_csr_access ───────────────────────────────────────────

async def sc03_illegal_csr_access(dut, csr_agent, rd_driver, sb, cov, log):
    """SC03: Read/write unmapped offsets, attempt start-while-busy."""
    scenario_id = "SC03"
    goal_id = "EQ_SCENARIO_SC03"
    log.info(f"=== {scenario_id}: illegal_csr_access ===")

    await _deassert_rst(dut, 3)

    # Enable irq_error for observable IRQ check
    await csr_agent.drive_write(CSR_CTRL, 1 << CTRL_IRQ_ERROR_EN)

    # Illegal CSR read (unmapped offset 0x100)
    resp = await csr_agent.drive_read(0x100)
    sb.set_cycle(cocotb.utils.get_sim_time(units="ns") // 10)
    irq = IrqMonitor(dut)
    irq_d, irq_e = await irq.sample()
    sb.check_illegal_csr(scenario_id, goal_id, 0x100, 0, False,
                         csr_error=int(resp.error), irq_error=irq_e)

    # Illegal CSR write (unmapped offset 0x100)
    resp = await csr_agent.drive_write(0x100, 0xDEAD)
    sb.set_cycle(cocotb.utils.get_sim_time(units="ns") // 10)
    irq_d, irq_e = await irq.sample()
    sb.check_illegal_csr(scenario_id, goal_id, 0x100, 0xDEAD, True,
                         csr_error=int(resp.error), irq_error=irq_e)

    # Verify config preserved (read back SRC_ADDR — should still be 0)
    resp = await csr_agent.drive_read(CSR_SRC_ADDR)
    sb.set_cycle(cocotb.utils.get_sim_time(units="ns") // 10)
    sb.check_csr_read(scenario_id, goal_id, CSR_SRC_ADDR,
                      rdata=int(resp.rdata), csr_error=int(resp.error))

    # Start-while-busy: first start a nonzero transfer, then try start again
    await csr_agent.drive_write(CSR_SRC_ADDR, 0x1000)
    await csr_agent.drive_write(CSR_DST_ADDR, 0x2000)
    await csr_agent.drive_write(CSR_LENGTH, 16)  # 4 beats
    await csr_agent.drive_write(CSR_CTRL, 1 << CTRL_START_BIT)  # start

    # Immediately try another start while busy
    resp = await csr_agent.drive_write(CSR_CTRL, 1 << CTRL_START_BIT)
    sb.set_cycle(cocotb.utils.get_sim_time(units="ns") // 10)
    irq_d, irq_e = await irq.sample()
    sb.check_illegal_csr(scenario_id, goal_id, CSR_CTRL, 1 << CTRL_START_BIT, True,
                         csr_error=int(resp.error), irq_error=irq_e)

    cov.hit("SC03_executed")
    cov.hit_many(["function_illegal_csr_or_start", "fcov_error"])
    cov.hit("ccov_handshakes")

    ok = sb.scenario_pass(scenario_id)
    log.info(f"[{'PASS' if ok else 'FAIL'}] {scenario_id}")
    return ok


# ── SC04: zero_length_transfer ─────────────────────────────────────────

async def sc04_zero_length_transfer(dut, csr_agent, rd_driver, sb, cov, log):
    """SC04: Program LENGTH=0, enable done IRQ, write start."""
    scenario_id = "SC04"
    goal_id = "EQ_SCENARIO_SC04"
    log.info(f"=== {scenario_id}: zero_length_transfer ===")

    await _deassert_rst(dut, 3)

    # Program: SRC/DST any, LENGTH=0, enable irq_done, then start
    await csr_agent.drive_write(CSR_SRC_ADDR, 0xA000)
    await csr_agent.drive_write(CSR_DST_ADDR, 0xB000)
    await csr_agent.drive_write(CSR_LENGTH, 0)
    await csr_agent.drive_write(CSR_CTRL, (1 << CTRL_IRQ_DONE_EN) | (1 << CTRL_START_BIT))

    await ReadOnly()
    sb.set_cycle(cocotb.utils.get_sim_time(units="ns") // 10)

    ok = sb.check_start_transfer(scenario_id, goal_id, length=0, irq_done_en=1,
                                 mem_rd_valid=int(dut.mem_rd_valid.value),
                                 irq_done=int(dut.irq_done.value))

    # Verify no memory requests
    if int(dut.mem_rd_valid.value) != 0 or int(dut.mem_wr_valid.value) != 0:
        log.error(f"[FAIL] {scenario_id}: memory valid asserted for zero-length transfer")
        ok = False

    # Verify STATUS: busy=0, done=1, error=0
    resp = await csr_agent.drive_read(CSR_STATUS)
    status_val = int(resp.rdata)
    if (status_val & 0x7) != 0x2:  # done bit set
        log.error(f"[FAIL] {scenario_id}: STATUS=0x{status_val:08X}, expected done=1")
        ok = False

    cov.hit("SC04_executed")
    cov.hit("function_start_transfer")
    cov.hit("cycle_latency_zero_length_transfer")

    log.info(f"[{'PASS' if ok else 'FAIL'}] {scenario_id}")
    return ok


# ── SC05: single_beat_copy ─────────────────────────────────────────────

async def sc05_single_beat_copy(dut, csr_agent, rd_driver, sb, cov, log):
    """SC05: Program one full DATA_WIDTH beat, provide read data, keep ready high."""
    scenario_id = "SC05"
    goal_id = "EQ_SCENARIO_SC05"
    log.info(f"=== {scenario_id}: single_beat_copy ===")

    await _assert_rst(dut, 3)
    await _deassert_rst(dut, 3)

    # Program
    await csr_agent.drive_write(CSR_SRC_ADDR, 0x1000_1000)
    await csr_agent.drive_write(CSR_DST_ADDR, 0x2000_2000)
    await csr_agent.drive_write(CSR_LENGTH, 4)  # 1 beat
    # Set ready high
    dut.mem_rd_ready.value = 1
    dut.mem_wr_ready.value = 1

    # Start
    await csr_agent.drive_write(CSR_CTRL, 1 << CTRL_START_BIT)

    # Wait for read address to be accepted, then provide read data
    for _ in range(20):
        await RisingEdge(dut.clk)
        await ReadOnly()
        if int(dut.mem_rd_valid.value) and int(dut.mem_rd_ready.value):
            # Check read address
            sb.set_cycle(cocotb.utils.get_sim_time(units="ns") // 10)
            sb.check_read_request(scenario_id, goal_id,
                                  mem_rd_addr=int(dut.mem_rd_addr.value))
            # Drive read data
            rd_data = 0xDEAD_BEEF
            await rd_driver.drive_beat(rd_data)
            sb.set_cycle(cocotb.utils.get_sim_time(units="ns") // 10)
            sb.check_capture_read_data(scenario_id, goal_id, rd_data)
            break

    # Wait for write acceptance
    for _ in range(20):
        await RisingEdge(dut.clk)
        await ReadOnly()
        if int(dut.mem_wr_valid.value) and int(dut.mem_wr_ready.value):
            sb.set_cycle(cocotb.utils.get_sim_time(units="ns") // 10)
            ok_wr = sb.check_write_request(scenario_id, goal_id,
                                           mem_wr_addr=int(dut.mem_wr_addr.value),
                                           mem_wr_data=int(dut.mem_wr_data.value),
                                           mem_wr_strb=int(dut.mem_wr_strb.value))
            ok_acc = sb.check_write_accept(scenario_id, goal_id,
                                           irq_done=int(dut.irq_done.value))
            break

    cov.hit("SC05_executed")
    cov.hit_many(["function_memory_read_request", "function_capture_read_data",
                  "function_memory_write_request", "function_memory_write_accept"])
    cov.hit("ccov_pipeline")

    ok = sb.scenario_pass(scenario_id)
    log.info(f"[{'PASS' if ok else 'FAIL'}] {scenario_id}")
    return ok


# ── SC06: multi_beat_copy ──────────────────────────────────────────────

async def sc06_multi_beat_copy(dut, csr_agent, rd_driver, sb, cov, log):
    """SC06: Program at least 3 beats, deterministic data, ready memory."""
    scenario_id = "SC06"
    goal_id = "EQ_SCENARIO_SC06"
    log.info(f"=== {scenario_id}: multi_beat_copy ===")

    await _assert_rst(dut, 3)
    await _deassert_rst(dut, 3)

    NUM_BEATS = 4
    BYTES = NUM_BEATS * 4  # 16 bytes
    src_base = 0x3000_0000
    dst_base = 0x4000_0000

    await csr_agent.drive_write(CSR_SRC_ADDR, src_base)
    await csr_agent.drive_write(CSR_DST_ADDR, dst_base)
    await csr_agent.drive_write(CSR_LENGTH, BYTES)
    await csr_agent.drive_write(CSR_CTRL, (1 << CTRL_IRQ_DONE_EN))

    dut.mem_rd_ready.value = 1
    dut.mem_wr_ready.value = 1

    # Start
    await csr_agent.drive_write(CSR_CTRL, (1 << CTRL_IRQ_DONE_EN) | (1 << CTRL_START_BIT))

    sb.set_cycle(cocotb.utils.get_sim_time(units="ns") // 10)
    sb.check_start_transfer(scenario_id, goal_id, length=BYTES, irq_done_en=1,
                            mem_rd_valid=int(dut.mem_rd_valid.value),
                            irq_done=int(dut.irq_done.value))

    for beat_idx in range(NUM_BEATS):
        # Wait for read address acceptance
        rd_accepted = False
        for _ in range(30):
            await RisingEdge(dut.clk)
            await ReadOnly()
            if int(dut.mem_rd_valid.value) and int(dut.mem_rd_ready.value):
                sb.set_cycle(cocotb.utils.get_sim_time(units="ns") // 10)
                sb.check_read_request(scenario_id, goal_id,
                                      mem_rd_addr=int(dut.mem_rd_addr.value))
                rd_accepted = True
                break
        assert rd_accepted, f"Beat {beat_idx}: read address not accepted"

        # Drive read data
        rd_data = 0xA000_0000 + beat_idx
        await rd_driver.drive_beat(rd_data)
        sb.set_cycle(cocotb.utils.get_sim_time(units="ns") // 10)
        sb.check_capture_read_data(scenario_id, goal_id, rd_data)

        # Wait for write acceptance
        wr_accepted = False
        for _ in range(30):
            await RisingEdge(dut.clk)
            await ReadOnly()
            if int(dut.mem_wr_valid.value) and int(dut.mem_wr_ready.value):
                sb.set_cycle(cocotb.utils.get_sim_time(units="ns") // 10)
                sb.check_write_request(scenario_id, goal_id,
                                       mem_wr_addr=int(dut.mem_wr_addr.value),
                                       mem_wr_data=int(dut.mem_wr_data.value),
                                       mem_wr_strb=int(dut.mem_wr_strb.value))
                sb.check_write_accept(scenario_id, goal_id,
                                      irq_done=int(dut.irq_done.value))
                wr_accepted = True
                break
        assert wr_accepted, f"Beat {beat_idx}: write not accepted"

    # Verify final status: done=1
    resp = await csr_agent.drive_read(CSR_STATUS)
    status_val = int(resp.rdata)
    if not (status_val & 2):
        log.error(f"[FAIL] {scenario_id}: done not set, STATUS=0x{status_val:08X}")

    # Progress should equal BYTES
    resp = await csr_agent.drive_read(CSR_PROGRESS)
    progress_val = int(resp.rdata)
    if progress_val != BYTES:
        log.error(f"[FAIL] {scenario_id}: progress={progress_val}, expected={BYTES}")

    cov.hit("SC06_executed")
    cov.hit_many(["function_start_transfer", "function_memory_read_request",
                  "function_capture_read_data", "function_memory_write_request",
                  "function_memory_write_accept"])
    cov.hit_many(["ccov_pipeline", "cycle_pipeline_read_addr", "cycle_pipeline_write_beat"])

    ok = sb.scenario_pass(scenario_id)
    log.info(f"[{'PASS' if ok else 'FAIL'}] {scenario_id}")
    return ok


# ── SC07: partial_final_beat ───────────────────────────────────────────

async def sc07_partial_final_beat(dut, csr_agent, rd_driver, sb, cov, log):
    """SC07: Program length not a multiple of DATA_WIDTH/8; check final strobe."""
    scenario_id = "SC07"
    goal_id = "EQ_SCENARIO_SC07"
    log.info(f"=== {scenario_id}: partial_final_beat ===")

    await _assert_rst(dut, 3)
    await _deassert_rst(dut, 3)

    BYTES = 6  # 1 full beat (4B) + 1 partial (2B) → 2 beats total
    src_base = 0x5000_0000
    dst_base = 0x6000_0000

    await csr_agent.drive_write(CSR_SRC_ADDR, src_base)
    await csr_agent.drive_write(CSR_DST_ADDR, dst_base)
    await csr_agent.drive_write(CSR_LENGTH, BYTES)
    dut.mem_rd_ready.value = 1
    dut.mem_wr_ready.value = 1

    # Start
    await csr_agent.drive_write(CSR_CTRL, (1 << CTRL_IRQ_DONE_EN) | (1 << CTRL_START_BIT))

    # Beat 0: full beat
    for _ in range(30):
        await RisingEdge(dut.clk)
        await ReadOnly()
        if int(dut.mem_rd_valid.value) and int(dut.mem_rd_ready.value):
            sb.set_cycle(cocotb.utils.get_sim_time(units="ns") // 10)
            sb.check_read_request(scenario_id, goal_id,
                                  mem_rd_addr=int(dut.mem_rd_addr.value))
            break
    await rd_driver.drive_beat(0xCAFE_0001)
    sb.set_cycle(cocotb.utils.get_sim_time(units="ns") // 10)
    sb.check_capture_read_data(scenario_id, goal_id, 0xCAFE_0001)

    for _ in range(30):
        await RisingEdge(dut.clk)
        await ReadOnly()
        if int(dut.mem_wr_valid.value) and int(dut.mem_wr_ready.value):
            sb.set_cycle(cocotb.utils.get_sim_time(units="ns") // 10)
            sb.check_write_request(scenario_id, goal_id,
                                   mem_wr_addr=int(dut.mem_wr_addr.value),
                                   mem_wr_data=int(dut.mem_wr_data.value),
                                   mem_wr_strb=int(dut.mem_wr_strb.value))
            sb.check_write_accept(scenario_id, goal_id,
                                  irq_done=int(dut.irq_done.value))
            full_strb = int(dut.mem_wr_strb.value)
            if full_strb != 0xF:
                log.error(f"[FAIL] {scenario_id}: beat 0 strb=0x{full_strb:X}, expected 0xF")
            break

    # Beat 1: partial (2 bytes remaining)
    for _ in range(30):
        await RisingEdge(dut.clk)
        await ReadOnly()
        if int(dut.mem_rd_valid.value) and int(dut.mem_rd_ready.value):
            sb.set_cycle(cocotb.utils.get_sim_time(units="ns") // 10)
            sb.check_read_request(scenario_id, goal_id,
                                  mem_rd_addr=int(dut.mem_rd_addr.value))
            break
    await rd_driver.drive_beat(0xCAFE_0002)
    sb.set_cycle(cocotb.utils.get_sim_time(units="ns") // 10)
    sb.check_capture_read_data(scenario_id, goal_id, 0xCAFE_0002)

    for _ in range(30):
        await RisingEdge(dut.clk)
        await ReadOnly()
        if int(dut.mem_wr_valid.value) and int(dut.mem_wr_ready.value):
            sb.set_cycle(cocotb.utils.get_sim_time(units="ns") // 10)
            sb.check_write_request(scenario_id, goal_id,
                                   mem_wr_addr=int(dut.mem_wr_addr.value),
                                   mem_wr_data=int(dut.mem_wr_data.value),
                                   mem_wr_strb=int(dut.mem_wr_strb.value))
            sb.check_write_accept(scenario_id, goal_id,
                                  irq_done=int(dut.irq_done.value))
            final_strb = int(dut.mem_wr_strb.value)
            # 2 bytes → strb should be 0b0011 = 0x3
            if final_strb != 0x3:
                log.error(f"[FAIL] {scenario_id}: final beat strb=0x{final_strb:X}, expected 0x3")
            break

    cov.hit("SC07_executed")
    cov.hit("fcov_strobe")

    ok = sb.scenario_pass(scenario_id)
    log.info(f"[{'PASS' if ok else 'FAIL'}] {scenario_id}")
    return ok


# ── SC08: read_backpressure ────────────────────────────────────────────

async def sc08_read_backpressure(dut, csr_agent, rd_driver, sb, cov, log):
    """SC08: Randomly deassert mem_rd_ready; check protocol stability."""
    scenario_id = "SC08"
    goal_id = "EQ_SCENARIO_SC08"
    log.info(f"=== {scenario_id}: read_backpressure ===")

    await _assert_rst(dut, 3)
    await _deassert_rst(dut, 3)

    await csr_agent.drive_write(CSR_SRC_ADDR, 0x7000_0000)
    await csr_agent.drive_write(CSR_DST_ADDR, 0x8000_0000)
    await csr_agent.drive_write(CSR_LENGTH, 8)  # 2 beats
    dut.mem_wr_ready.value = 1

    # Start
    await csr_agent.drive_write(CSR_CTRL, 1 << CTRL_START_BIT)

    for beat_idx in range(2):
        # Deassert mem_rd_ready for a few cycles to test backpressure
        dut.mem_rd_ready.value = 0
        await ClockCycles(dut.clk, random.randint(2, 5))

        # Re-assert mem_rd_ready
        dut.mem_rd_ready.value = 1
        await RisingEdge(dut.clk)
        await ReadOnly()

        # Wait for read address acceptance
        for _ in range(30):
            await ReadOnly()
            if int(dut.mem_rd_valid.value) and int(dut.mem_rd_ready.value):
                sb.set_cycle(cocotb.utils.get_sim_time(units="ns") // 10)
                sb.check_read_request(scenario_id, goal_id,
                                      mem_rd_addr=int(dut.mem_rd_addr.value))
                break
            await RisingEdge(dut.clk)

        # Drive read data with randomness
        rd_data = 0xBB00_0000 + beat_idx
        await rd_driver.drive_beat(rd_data, backpressure=True)
        sb.set_cycle(cocotb.utils.get_sim_time(units="ns") // 10)
        sb.check_capture_read_data(scenario_id, goal_id, rd_data)

        # Wait for write
        for _ in range(30):
            await RisingEdge(dut.clk)
            await ReadOnly()
            if int(dut.mem_wr_valid.value) and int(dut.mem_wr_ready.value):
                sb.set_cycle(cocotb.utils.get_sim_time(units="ns") // 10)
                sb.check_write_request(scenario_id, goal_id,
                                       mem_wr_addr=int(dut.mem_wr_addr.value),
                                       mem_wr_data=int(dut.mem_wr_data.value),
                                       mem_wr_strb=int(dut.mem_wr_strb.value))
                sb.check_write_accept(scenario_id, goal_id,
                                      irq_done=int(dut.irq_done.value))
                break

    cov.hit("SC08_executed")
    cov.hit_many(["function_memory_read_request", "function_capture_read_data",
                  "ccov_backpressure"])
    cov.hit("ccov_handshakes")

    ok = sb.scenario_pass(scenario_id)
    log.info(f"[{'PASS' if ok else 'FAIL'}] {scenario_id}")
    return ok


# ── SC09: write_backpressure ───────────────────────────────────────────

async def sc09_write_backpressure(dut, csr_agent, rd_driver, sb, cov, log):
    """SC09: Randomly deassert mem_wr_ready; check stability."""
    scenario_id = "SC09"
    goal_id = "EQ_SCENARIO_SC09"
    log.info(f"=== {scenario_id}: write_backpressure ===")

    await _assert_rst(dut, 3)
    await _deassert_rst(dut, 3)

    await csr_agent.drive_write(CSR_SRC_ADDR, 0x9000_0000)
    await csr_agent.drive_write(CSR_DST_ADDR, 0xA000_0000)
    await csr_agent.drive_write(CSR_LENGTH, 4)  # 1 beat
    dut.mem_rd_ready.value = 1

    # Start
    await csr_agent.drive_write(CSR_CTRL, 1 << CTRL_START_BIT)

    # Wait for read address / drive read data
    for _ in range(30):
        await RisingEdge(dut.clk)
        await ReadOnly()
        if int(dut.mem_rd_valid.value) and int(dut.mem_rd_ready.value):
            break

    await rd_driver.drive_beat(0xFACE_CAFE)

    # Deassert mem_wr_ready for a few cycles
    dut.mem_wr_ready.value = 0
    await ClockCycles(dut.clk, random.randint(2, 5))

    last_wr_addr = 0
    last_wr_data = 0
    last_wr_strb = 0

    # Check stability while stalled: sample every cycle
    for stall_cycle in range(5):
        await ReadOnly()
        if int(dut.mem_wr_valid.value):
            cur_addr = int(dut.mem_wr_addr.value)
            cur_data = int(dut.mem_wr_data.value)
            cur_strb = int(dut.mem_wr_strb.value)

            if last_wr_addr != 0:
                if cur_addr != last_wr_addr:
                    log.error(f"[FAIL] {scenario_id}: addr changed during stall")
                if cur_data != last_wr_data:
                    log.error(f"[FAIL] {scenario_id}: data changed during stall")
                if cur_strb != last_wr_strb:
                    log.error(f"[FAIL] {scenario_id}: strb changed during stall")

            last_wr_addr = cur_addr
            last_wr_data = cur_data
            last_wr_strb = cur_strb
        await RisingEdge(dut.clk)

    # Re-assert mem_wr_ready; write should complete
    dut.mem_wr_ready.value = 1
    for _ in range(30):
        await RisingEdge(dut.clk)
        await ReadOnly()
        if int(dut.mem_wr_valid.value) and int(dut.mem_wr_ready.value):
            sb.set_cycle(cocotb.utils.get_sim_time(units="ns") // 10)
            sb.check_write_request(scenario_id, goal_id,
                                   mem_wr_addr=int(dut.mem_wr_addr.value),
                                   mem_wr_data=int(dut.mem_wr_data.value),
                                   mem_wr_strb=int(dut.mem_wr_strb.value))
            sb.check_write_accept(scenario_id, goal_id,
                                  irq_done=int(dut.irq_done.value))
            break

    cov.hit("SC09_executed")
    cov.hit("ccov_backpressure")
    cov.hit("ccov_handshakes")

    ok = sb.scenario_pass(scenario_id)
    log.info(f"[{'PASS' if ok else 'FAIL'}] {scenario_id}")
    return ok


# ── SC10: soft_reset_abort ─────────────────────────────────────────────

async def sc10_soft_reset_abort(dut, csr_agent, rd_driver, sb, cov, log):
    """SC10: Start multi-beat transfer, write CTRL.soft_reset during backpressure."""
    scenario_id = "SC10"
    goal_id = "EQ_SCENARIO_SC10"
    log.info(f"=== {scenario_id}: soft_reset_abort ===")

    await _assert_rst(dut, 3)
    await _deassert_rst(dut, 3)

    await csr_agent.drive_write(CSR_SRC_ADDR, 0xB000_0000)
    await csr_agent.drive_write(CSR_DST_ADDR, 0xC000_0000)
    await csr_agent.drive_write(CSR_LENGTH, 16)  # 4 beats
    dut.mem_rd_ready.value = 1

    # Start
    await csr_agent.drive_write(CSR_CTRL, 1 << CTRL_START_BIT)

    # Let first beat start — wait for read address
    for _ in range(30):
        await RisingEdge(dut.clk)
        await ReadOnly()
        if int(dut.mem_rd_valid.value) and int(dut.mem_rd_ready.value):
            break

    # Issue soft_reset while transfer is active (deassert mem_wr_ready to stall)
    dut.mem_wr_ready.value = 0
    await csr_agent.drive_write(CSR_CTRL, 1 << CTRL_SOFT_RESET)

    await ReadOnly()
    sb.set_cycle(cocotb.utils.get_sim_time(units="ns") // 10)
    sb.check_soft_reset(scenario_id, goal_id,
                        mem_rd_valid=int(dut.mem_rd_valid.value),
                        mem_wr_valid=int(dut.mem_wr_valid.value))

    # Verify mem_rd_valid and mem_wr_valid are deasserted
    if int(dut.mem_rd_valid.value) != 0:
        log.error(f"[FAIL] {scenario_id}: mem_rd_valid={int(dut.mem_rd_valid.value)} after soft_reset")
    if int(dut.mem_wr_valid.value) != 0:
        log.error(f"[FAIL] {scenario_id}: mem_wr_valid={int(dut.mem_wr_valid.value)} after soft_reset")

    # Verify STATUS: busy should be 0
    dut.mem_wr_ready.value = 1
    resp = await csr_agent.drive_read(CSR_STATUS)
    status_val = int(resp.rdata)
    if status_val & 1:
        log.error(f"[FAIL] {scenario_id}: busy still set after soft_reset")

    cov.hit("SC10_executed")
    cov.hit("function_clear_or_abort")
    cov.hit("ccov_backpressure")

    ok = sb.scenario_pass(scenario_id)
    log.info(f"[{'PASS' if ok else 'FAIL'}] {scenario_id}")
    return ok


# ── SC11: status_w1c_irq_clear ─────────────────────────────────────────

async def sc11_status_w1c_irq_clear(dut, csr_agent, rd_driver, sb, cov, log):
    """SC11: Complete a transfer + create error, then clear with W1C writes."""
    scenario_id = "SC11"
    goal_id = "EQ_SCENARIO_SC11"
    log.info(f"=== {scenario_id}: status_w1c_irq_clear ===")

    await _assert_rst(dut, 3)
    await _deassert_rst(dut, 3)

    # Enable both IRQs
    await csr_agent.drive_write(CSR_CTRL, (1 << CTRL_IRQ_DONE_EN) | (1 << CTRL_IRQ_ERROR_EN))

    # --- Phase 1: Complete a transfer to set done ---
    await csr_agent.drive_write(CSR_SRC_ADDR, 0xD000_0000)
    await csr_agent.drive_write(CSR_DST_ADDR, 0xE000_0000)
    await csr_agent.drive_write(CSR_LENGTH, 4)
    dut.mem_rd_ready.value = 1
    dut.mem_wr_ready.value = 1

    await csr_agent.drive_write(CSR_CTRL, (1 << CTRL_IRQ_DONE_EN) | (1 << CTRL_IRQ_ERROR_EN) | (1 << CTRL_START_BIT))

    # Serve read
    for _ in range(30):
        await RisingEdge(dut.clk)
        await ReadOnly()
        if int(dut.mem_rd_valid.value) and int(dut.mem_rd_ready.value):
            break
    await rd_driver.drive_beat(0xABCD_1234)
    # Wait for write
    for _ in range(30):
        await RisingEdge(dut.clk)
        await ReadOnly()
        if int(dut.mem_wr_valid.value) and int(dut.mem_wr_ready.value):
            break

    # --- Phase 2: Create an error (illegal CSR access) ---
    resp = await csr_agent.drive_write(0x100, 0xDEAD)
    await ReadOnly()
    irq = IrqMonitor(dut)
    irq_d, irq_e = await irq.sample()

    # Verify irq_done and irq_error are asserted (assuming enables set)
    if irq_d != 1:
        log.error(f"[FAIL] {scenario_id}: irq_done={irq_d}, expected 1")
    if irq_e != 1:
        log.error(f"[FAIL] {scenario_id}: irq_error={irq_e}, expected 1")

    # --- Phase 3: W1C clear done and error ---
    # Write STATUS with done=1, error=1 to clear both
    await csr_agent.drive_write(CSR_STATUS, (1 << STATUS_DONE_BIT) | (1 << STATUS_ERROR_BIT))
    await ReadOnly()
    irq_d, irq_e = await irq.sample()

    sb.set_cycle(cocotb.utils.get_sim_time(units="ns") // 10)
    sb.check_w1c_clear(scenario_id, goal_id,
                       done_bit=1, error_bit=1,
                       irq_done=irq_d, irq_error=irq_e)

    # After W1C clear, irqs should deassert
    if irq_d != 0:
        log.error(f"[FAIL] {scenario_id}: irq_done={irq_d} after W1C clear, expected 0")
    if irq_e != 0:
        log.error(f"[FAIL] {scenario_id}: irq_error={irq_e} after W1C clear, expected 0")

    # Verify STATUS: done/error cleared, busy=0
    resp = await csr_agent.drive_read(CSR_STATUS)
    status_val = int(resp.rdata)
    if status_val & 0x7 != 0:
        log.error(f"[FAIL] {scenario_id}: STATUS=0x{status_val:08X} after W1C, expected 0")

    # Verify config preserved (SRC_ADDR should still be 0xD000_0000)
    resp = await csr_agent.drive_read(CSR_SRC_ADDR)
    if int(resp.rdata) != 0xD000_0000:
        log.error(f"[FAIL] {scenario_id}: SRC_ADDR corrupted after W1C: 0x{int(resp.rdata):08X}")

    cov.hit("SC11_executed")
    cov.hit_many(["function_memory_write_accept", "function_illegal_csr_or_start",
                  "function_clear_or_abort"])
    cov.hit("fcov_error")

    ok = sb.scenario_pass(scenario_id)
    log.info(f"[{'PASS' if ok else 'FAIL'}] {scenario_id}")
    return ok


# ── SCENARIO dispatch table ────────────────────────────────────────────

SCENARIOS = [
    ("SC01", sc01_reset_defaults),
    ("SC02", sc02_csr_programming_readback),
    ("SC03", sc03_illegal_csr_access),
    ("SC04", sc04_zero_length_transfer),
    ("SC05", sc05_single_beat_copy),
    ("SC06", sc06_multi_beat_copy),
    ("SC07", sc07_partial_final_beat),
    ("SC08", sc08_read_backpressure),
    ("SC09", sc09_write_backpressure),
    ("SC10", sc10_soft_reset_abort),
    ("SC11", sc11_status_w1c_irq_clear),
]
