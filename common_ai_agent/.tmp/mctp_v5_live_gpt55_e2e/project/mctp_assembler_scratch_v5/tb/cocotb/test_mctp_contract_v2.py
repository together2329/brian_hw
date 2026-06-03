from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Sequence

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, ReadOnly, RisingEdge


AXI_BYTES = 32
HEADER_BYTES = 20
PAYLOAD_COUNT_MASK = 0x1FFF


def _events_path() -> Path:
    return Path(os.environ["PROJECT_ROOT"]) / os.environ["IP_NAME"] / "sim" / "contract_v2_events.jsonl"


def _int(signal) -> int:
    return int(signal.value)


def _set_idle(dut) -> None:
    dut.m_axi_awvalid.value = 0
    dut.m_axi_wvalid.value = 0
    dut.m_axi_wlast.value = 0
    dut.m_axi_arvalid.value = 0
    dut.m_axi_bready.value = 1
    dut.m_axi_rready.value = 1
    dut.psel.value = 0
    dut.penable.value = 0
    dut.pwrite.value = 0
    dut.pstrb.value = 0xF
    dut.sram_wr_ready.value = 1
    dut.sram_rd_req_ready.value = 1
    dut.sram_rd_rsp_valid.value = 0
    dut.sram_rd_rsp_error.value = 0


async def _reset(dut) -> None:
    dut.axi_aresetn.value = 0
    dut.presetn.value = 0
    _set_idle(dut)
    await ClockCycles(dut.axi_aclk, 4)
    dut.axi_aresetn.value = 1
    dut.presetn.value = 1
    await ClockCycles(dut.axi_aclk, 4)


async def _apb_write(dut, addr: int, data: int) -> None:
    await FallingEdge(dut.pclk)
    dut.paddr.value = addr
    dut.pwdata.value = data
    dut.pstrb.value = 0xF
    dut.pwrite.value = 1
    dut.psel.value = 1
    dut.penable.value = 0
    await RisingEdge(dut.pclk)
    await FallingEdge(dut.pclk)
    dut.penable.value = 1
    await RisingEdge(dut.pclk)
    await FallingEdge(dut.pclk)
    dut.psel.value = 0
    dut.penable.value = 0
    dut.pwrite.value = 0


async def _apb_read(dut, addr: int) -> dict[str, int]:
    await FallingEdge(dut.pclk)
    dut.paddr.value = addr
    dut.pwdata.value = 0
    dut.pstrb.value = 0xF
    dut.pwrite.value = 0
    dut.psel.value = 1
    dut.penable.value = 0
    await RisingEdge(dut.pclk)
    await FallingEdge(dut.pclk)
    dut.penable.value = 1
    await RisingEdge(dut.pclk)
    await ReadOnly()
    data = _int(dut.prdata)
    ready = _int(dut.pready)
    error = _int(dut.pslverr)
    await FallingEdge(dut.pclk)
    dut.psel.value = 0
    dut.penable.value = 0
    return {"addr": addr, "data": data, "ready": ready, "error": error}


def _word_from_bytes(items: Sequence[int]) -> int:
    word = 0
    for index, value in enumerate(items):
        word |= (value & 0xFF) << (index * 8)
    return word


def _strobe(width: int) -> int:
    return (1 << width) - 1 if width > 0 else 0


def _tlp_stream(payload: bytes) -> bytes:
    word = bytearray(AXI_BYTES)
    for index, value in enumerate(payload[:HEADER_BYTES - 4]):
        word[index] = value
    word[16] = 0x01
    word[17] = 0x22
    word[18] = (1 << 7) | (1 << 6) | (1 << 3)
    word[19] = 0x7E
    word[28] = len(payload) & 0xFF
    word[29] = (len(payload) >> 8) & 0x1F
    return bytes(word)


async def _drive_axi_tlp(dut, payload: bytes) -> None:
    stream = _tlp_stream(payload)
    beats = (len(stream) + AXI_BYTES - 1) // AXI_BYTES
    padded = stream.ljust(beats * AXI_BYTES, b"\x00")
    await FallingEdge(dut.axi_aclk)
    dut.m_axi_awaddr.value = 0
    dut.m_axi_awlen.value = beats - 1
    dut.m_axi_awsize.value = 5
    dut.m_axi_awburst.value = 1
    dut.m_axi_awvalid.value = 1
    for beat in range(beats):
        chunk = padded[beat * AXI_BYTES : (beat + 1) * AXI_BYTES]
        valid_bytes = min(AXI_BYTES, len(stream) - beat * AXI_BYTES)
        dut.m_axi_wdata.value = _word_from_bytes(chunk)
        dut.m_axi_wstrb.value = _strobe(valid_bytes)
        dut.m_axi_wlast.value = 1 if beat == beats - 1 else 0
        dut.m_axi_wvalid.value = 1
        await RisingEdge(dut.axi_aclk)
        await FallingEdge(dut.axi_aclk)
        dut.m_axi_awvalid.value = 0
    dut.m_axi_wvalid.value = 0
    dut.m_axi_wlast.value = 0


async def _capture_backpressure(dut) -> dict[str, int]:
    for _ in range(80):
        await RisingEdge(dut.axi_aclk)
        await ReadOnly()
        active = _int(dut.sram_wr_valid) == 1 and _int(dut.sram_wr_ready) == 0
        if not active:
            continue
        first = {"addr": _int(dut.sram_wr_addr), "data": _int(dut.sram_wr_data), "strb": _int(dut.sram_wr_strb)}
        await RisingEdge(dut.axi_aclk)
        await ReadOnly()
        second = {"addr": _int(dut.sram_wr_addr), "data": _int(dut.sram_wr_data), "strb": _int(dut.sram_wr_strb)}
        assert _int(dut.sram_wr_valid) == 1
        assert _int(dut.sram_wr_ready) == 0
        assert second == first
        return {
            "sram_wr_addr": first["addr"],
            "sram_wr_data": first["data"],
            "sram_wr_ready": 0,
            "sram_wr_strb": first["strb"],
            "sram_wr_valid": 1,
        }
    raise AssertionError("no SRAM write backpressure window was observed")


async def _read_payload_count_after_update(dut, payload_len: int) -> dict[str, int]:
    for _ in range(80):
        result = await _apb_read(dut, 0x010C)
        payload_count = result["data"] & PAYLOAD_COUNT_MASK
        if result["ready"] == 1 and result["error"] == 0 and payload_count == payload_len:
            return {"payload_byte_count": payload_count, "prdata": result["data"], "pready": result["ready"]}
        await ClockCycles(dut.axi_aclk, 1)
    raise AssertionError("APB Q_PAYLOAD_COUNT did not expose updated payload count")


def _write_rows(backpressure: dict[str, int], apb: dict[str, int]) -> None:
    rows = [
        {
            "goal_id": "CONTRACT_V2_SRAM_BACKPRESSURE",
            "passed": True,
            "rtl_observed": backpressure,
            "scenario_id": "SC_CONTRACT_V2_SRAM_BACKPRESSURE",
        },
        {
            "goal_id": "CONTRACT_V2_APB_Q_PAYLOAD_COUNT_AFTER_UPDATE",
            "passed": True,
            "rtl_observed": apb,
            "scenario_id": "SC_CONTRACT_V2_APB_Q_PAYLOAD_COUNT_AFTER_UPDATE",
        },
    ]
    path = _events_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


@cocotb.test
async def contract_v2_backpressure_and_apb_visibility(dut) -> None:
    _ = cocotb.start_soon(Clock(dut.axi_aclk, 10, units="ns").start())
    _ = cocotb.start_soon(Clock(dut.pclk, 10, units="ns").start())
    await _reset(dut)
    await _apb_write(dut, 0x0000, 0x1 | (4096 << 3))
    await _apb_write(dut, 0x0014, 0xF)
    await ClockCycles(dut.axi_aclk, 4)
    payload = bytes(range(1, 18))
    dut.sram_wr_ready.value = 0
    await _drive_axi_tlp(dut, payload)
    backpressure = await _capture_backpressure(dut)
    await FallingEdge(dut.axi_aclk)
    dut.sram_wr_ready.value = 1
    await ClockCycles(dut.axi_aclk, 4)
    apb = await _read_payload_count_after_update(dut, len(payload))
    _write_rows(backpressure, apb)
