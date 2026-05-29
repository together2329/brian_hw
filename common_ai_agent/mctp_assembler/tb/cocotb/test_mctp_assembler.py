from __future__ import annotations

import json
import sys
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge

from agents import ApbMaster, AxiWriteMaster, SramMonitor
from scoreboard import MctpScoreboard
from tb_coverage import FunctionalCoverageCollector
from uvm_env import MctpEnv

_TB_DIR = Path(__file__).resolve().parent
_IP_DIR = _TB_DIR.parents[1]
_TC_DIR = _IP_DIR / "tc"
_MODEL_DIR = _IP_DIR / "model"
for path in (_TB_DIR, _TC_DIR, _MODEL_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from mctp_assembler_scenarios import (  # noqa: E402
    A_CONTROL,
    A_DESC_POP,
    A_DESC_STATUS,
    A_DESC_WORD0,
    A_DESC_WORD1,
    A_DESC_WORD2,
    A_DESC_WORD3,
    A_ERROR_STATUS,
    A_LOCAL_EID,
    A_PACKET_DROP_COUNT,
    A_ASSEMBLY_DROP_COUNT,
    A_STATUS,
    parse_status,
    smoke_scenarios,
)


def _load_manifest() -> dict:
    return json.loads((_IP_DIR / "tb" / "cocotb" / "tb_manifest.json").read_text(encoding="utf-8"))


async def _reset_dut(dut) -> None:
    dut.axi_aresetn.value = 0
    dut.presetn.value = 0
    dut.sram_wr_ready.value = 1
    apb = ApbMaster()
    apb.bind(dut, "pclk")
    axi = AxiWriteMaster()
    axi.bind(dut, "axi_aclk")
    await apb.reset_bus()
    await axi.reset_bus()
    await ClockCycles(dut.axi_aclk, 5)
    await ClockCycles(dut.pclk, 5)
    dut.axi_aresetn.value = 1
    dut.presetn.value = 1
    await ClockCycles(dut.axi_aclk, 5)
    await ClockCycles(dut.pclk, 5)


async def _wait_cdc(dut, axi_cycles: int = 20, apb_cycles: int = 10) -> None:
    await ClockCycles(dut.axi_aclk, axi_cycles)
    await ClockCycles(dut.pclk, apb_cycles)


async def _poll_descriptor(apb: ApbMaster, dut, timeout: int = 300) -> int:
    for _ in range(timeout):
        await RisingEdge(dut.pclk)
        status = await apb.read(A_DESC_STATUS)
        if status & 0xF:
            return status
    return 0


async def _drain_descriptors(apb: ApbMaster, dut, sb: MctpScoreboard | None = None, timeout: int = 32) -> int:
    drained = 0
    for _ in range(timeout):
        status = await apb.read(A_DESC_STATUS)
        if (status & 0xF) == 0:
            return drained
        await apb.write(A_DESC_POP, 0x1)
        await ClockCycles(dut.pclk, 2)
        drained += 1
        if sb is not None:
            sb.note_descriptor_drain(1)
    return drained


async def _collect_descriptors(apb: ApbMaster, dut, count: int, timeout: int = 500) -> list[tuple[int, int, int, int]]:
    collected: list[tuple[int, int, int, int]] = []
    for _ in range(count):
        status = await _poll_descriptor(apb, dut, timeout=timeout)
        if (status & 0xF) == 0:
            break
        w0 = await apb.read(A_DESC_WORD0)
        w1 = await apb.read(A_DESC_WORD1)
        w2 = await apb.read(A_DESC_WORD2)
        w3 = await apb.read(A_DESC_WORD3)
        collected.append((w0, w1, w2, w3))
        await apb.write(A_DESC_POP, 0x1)
        await ClockCycles(dut.pclk, 2)
    return collected


async def _pulse_soft_reset(apb: ApbMaster, dut) -> None:
    """Clear AXI-domain assembly state between directed scenarios."""
    await apb.write(A_CONTROL, 0x2)
    await ClockCycles(dut.axi_aclk, 32)
    await ClockCycles(dut.pclk, 32)
    await apb.write(A_CONTROL, 0x0)
    await ClockCycles(dut.axi_aclk, 32)
    await ClockCycles(dut.pclk, 32)


async def _run_scenario(env: MctpEnv, dut, scenario) -> None:
    sb = env.scoreboard
    cov = env.coverage
    apb = env.apb
    axi = env.axi
    sram = env.sram_monitor

    sb.reset_oracle()
    sram.memory.clear()
    sram.write_log.clear()
    if scenario.scenario_id != "SC_APB_REGS":
        await _pulse_soft_reset(apb, dut)

    if scenario.scenario_id == "SC_APB_REGS":
        control = await apb.read(A_CONTROL)
        sb.check_apb_regs(scenario.scenario_id, control)
        cov.sample(scenario.scenario_id, scenario.coverage_refs, True)
        await apb.write(A_LOCAL_EID, 0x22)
        sb.apply_apb_setup([])
        sb.fm.cfg_local_eid = 0x22
        readback = await apb.read(A_LOCAL_EID)
        passed = (readback & 0xFF) == 0x22
        sb.record(scenario.scenario_id, {"local_eid": readback}, passed, "" if passed else "local_eid readback failed")
        cov.sample(scenario.scenario_id, scenario.coverage_refs, passed)
        return

    for w in scenario.apb_setup:
        await apb.write(w.addr, w.data)
    sb.apply_apb_setup(scenario.apb_setup)
    await _wait_cdc(dut)
    await _drain_descriptors(apb, dut, sb)

    desc_words_list: list[tuple[int, int, int, int]] = []
    for idx, burst in enumerate(scenario.axi_bursts):
        await axi.write_burst(burst.awaddr, burst.beats)
        if idx < len(scenario.tlps):
            sb.feed_tlps([scenario.tlps[idx]])
        await ClockCycles(dut.axi_aclk, 80)
        status = await apb.read(A_STATUS)
        pkt_drop = await apb.read(A_PACKET_DROP_COUNT)
        for checkpoint in scenario.burst_checkpoints:
            if checkpoint.after_burst == idx:
                sb.check_burst_checkpoint(
                    scenario.scenario_id,
                    checkpoint=checkpoint,
                    status=status,
                    packet_drop_count=pkt_drop,
                )
        if idx in scenario.drain_descriptors_after_burst:
            drained = await _collect_descriptors(apb, dut, 8)
            desc_words_list.extend(drained)
            sb.note_descriptor_drain(len(drained))

    desc_status = 0
    desc_words = None
    expect_desc_n = scenario.expect_descriptor_count or (1 if scenario.expect_descriptor else 0)

    if expect_desc_n > 0:
        await _wait_cdc(dut, 120, 60)
        remaining = expect_desc_n - len(desc_words_list)
        if remaining > 0:
            desc_words_list.extend(await _collect_descriptors(apb, dut, remaining))
        desc_status = len(desc_words_list)
        desc_words = desc_words_list[0] if desc_words_list else None
    else:
        await _wait_cdc(dut, 100, 50)
        desc_status = await apb.read(A_DESC_STATUS)

    pkt_drop = await apb.read(A_PACKET_DROP_COUNT)
    asm_drop = await apb.read(A_ASSEMBLY_DROP_COUNT)
    error_status = await apb.read(A_ERROR_STATUS)
    status = await apb.read(A_STATUS)
    active_contexts = parse_status(status)["active_context_count"]

    sram_bytes = None
    sram_payloads: list[list[int] | None] = []
    if expect_desc_n == 1 and desc_words:
        payload_count = desc_words[1] & 0xFFFF
        start_addr = desc_words[2] & 0xFFFF
        sram_bytes = sram.read_bytes(start_addr, payload_count)
        sram_payloads = [sram_bytes]
    elif expect_desc_n > 1:
        for words in desc_words_list:
            payload_count = words[1] & 0xFFFF
            start_addr = words[2] & 0xFFFF
            sram_payloads.append(sram.read_bytes(start_addr, payload_count))

    if expect_desc_n > 1:
        sb.check_descriptors(
            scenario.scenario_id,
            desc_words_list=desc_words_list,
            sram_payloads=sram_payloads,
            expect_count=expect_desc_n,
            packet_drop_count=pkt_drop,
            assembly_drop_count=asm_drop,
            error_status=error_status,
            active_context_count=active_contexts,
            expect_final_active_contexts=scenario.expect_active_contexts,
        )
    else:
        sb.check_scenario(
            scenario.scenario_id,
            desc_status=desc_status if isinstance(desc_status, int) else (desc_status & 0xF),
            desc_words=desc_words,
            packet_drop_count=pkt_drop,
            assembly_drop_count=asm_drop,
            error_status=error_status,
            active_context_count=active_contexts,
            sram_bytes=sram_bytes,
            expect_descriptor=scenario.expect_descriptor,
            expect_packet_drop=scenario.expect_packet_drop,
            expect_assembly_drop=scenario.expect_assembly_drop,
            expect_active_contexts=scenario.expect_active_contexts,
        )
    passed = not any(e["scenario_id"] == scenario.scenario_id and not e["passed"] for e in sb.events)
    cov.sample(scenario.scenario_id, scenario.coverage_refs, passed)
    if expect_desc_n > 0 and desc_words_list:
        await _drain_descriptors(apb, dut, sb)

@cocotb.test()
async def mctp_ssot_scenarios(dut):
    manifest = _load_manifest()
    cocotb.start_soon(Clock(dut.axi_aclk, 10, units="ns").start())
    cocotb.start_soon(Clock(dut.pclk, 20, units="ns").start())
    await _reset_dut(dut)

    env = MctpEnv("env", _IP_DIR)
    env.bind(dut)
    env.scoreboard.begin_test_evidence()
    cocotb.start_soon(env.sram_monitor.run())

    for scenario in smoke_scenarios():
        await _run_scenario(env, dut, scenario)

    env.scoreboard.final_check()
    env.coverage.write(_IP_DIR)
