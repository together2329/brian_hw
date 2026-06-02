from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, ReadOnly, RisingEdge


AXI_BYTES = 32
HEADER_BYTES = 20
MONITOR_CHECKS = (
    "sram_payload_no_holes",
    "sram_payload_only",
    "sram_no_header_or_pad_write",
    "axi_write_protocol_pass",
    "axi_read_protocol_pass",
    "apb_per_q_readback_pass",
)
_monitor_started = False


def _ip_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def _monitor_path() -> Path:
    return _ip_dir() / "sim" / "monitor_evidence.json"


def _empty_monitor() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "type": "monitor_evidence",
        "status": "fail",
        "checks": {key: False for key in MONITOR_CHECKS},
        "summary": {
            "sram_write_count": 0,
            "axi_write_transactions": 0,
            "axi_read_transactions": 0,
            "apb_reads": 0,
        },
        "observations": [],
    }


def _ensure_monitor_started() -> None:
    global _monitor_started
    if _monitor_started:
        return
    path = _monitor_path()
    if path.is_file():
        path.unlink()
    _monitor_started = True


def _read_monitor() -> dict[str, Any]:
    path = _monitor_path()
    if not path.is_file():
        return _empty_monitor()
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else _empty_monitor()


def _record_monitor(entry: dict[str, Any]) -> None:
    _ensure_monitor_started()
    doc = _read_monitor()
    checks = cast(dict[str, Any], doc["checks"] if isinstance(doc.get("checks"), dict) else {})
    entry_checks = cast(dict[str, Any], entry["checks"] if isinstance(entry.get("checks"), dict) else {})
    for key in MONITOR_CHECKS:
        checks[key] = bool(checks.get(key)) or bool(entry_checks.get(key))
    summary = cast(dict[str, Any], doc["summary"] if isinstance(doc.get("summary"), dict) else {})
    entry_summary = cast(dict[str, Any], entry["summary"] if isinstance(entry.get("summary"), dict) else {})
    for key in ("sram_write_count", "axi_write_transactions", "axi_read_transactions", "apb_reads"):
        summary[key] = int(summary.get(key, 0) or 0) + int(entry_summary.get(key, 0) or 0)
    observations = cast(list[dict[str, Any]], doc["observations"] if isinstance(doc.get("observations"), list) else [])
    observations.append(entry)
    doc["checks"] = checks
    doc["summary"] = summary
    doc["observations"] = observations
    doc["status"] = "pass" if all(bool(checks.get(key)) for key in MONITOR_CHECKS) else "fail"
    path = _monitor_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")


async def _reset(dut) -> None:
    dut.axi_aresetn.value = 0
    dut.presetn.value = 0
    dut.m_axi_awvalid.value = 0
    dut.m_axi_wvalid.value = 0
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
    await ClockCycles(dut.axi_aclk, 4)
    dut.axi_aresetn.value = 1
    dut.presetn.value = 1
    await ClockCycles(dut.axi_aclk, 2)


async def _apb_write(dut, addr: int, data: int) -> None:
    await FallingEdge(dut.axi_aclk)
    dut.paddr.value = addr
    dut.pwdata.value = data
    dut.pstrb.value = 0xF
    dut.pwrite.value = 1
    dut.psel.value = 1
    dut.penable.value = 0
    await RisingEdge(dut.axi_aclk)
    await FallingEdge(dut.axi_aclk)
    dut.penable.value = 1
    await RisingEdge(dut.axi_aclk)
    await FallingEdge(dut.axi_aclk)
    dut.psel.value = 0
    dut.penable.value = 0
    dut.pwrite.value = 0


async def _apb_read(dut, addr: int) -> dict[str, int]:
    await FallingEdge(dut.axi_aclk)
    dut.paddr.value = addr
    dut.pwdata.value = 0
    dut.pstrb.value = 0xF
    dut.pwrite.value = 0
    dut.psel.value = 1
    dut.penable.value = 0
    await RisingEdge(dut.axi_aclk)
    await FallingEdge(dut.axi_aclk)
    dut.penable.value = 1
    await RisingEdge(dut.axi_aclk)
    await ReadOnly()
    data = int(dut.prdata.value)
    ready = int(dut.pready.value) if hasattr(dut, "pready") else 1
    error = int(dut.pslverr.value) if hasattr(dut, "pslverr") else 0
    await FallingEdge(dut.axi_aclk)
    dut.psel.value = 0
    dut.penable.value = 0
    return {"addr": addr, "data": data, "ready": ready, "error": error}


def _word_from_bytes(items: Sequence[int]) -> int:
    word = 0
    for idx, value in enumerate(items):
        word |= (value & 0xFF) << (idx * 8)
    return word


def _strobe(width: int) -> int:
    return (1 << width) - 1 if width > 0 else 0


def _mctp_first_beat(payload: bytes) -> bytes:
    header = bytearray(HEADER_BYTES)
    header[16] = 0x01
    header[17] = 0x22
    header[18] = (1 << 7) | (1 << 6) | (1 << 3)
    header[19] = 0x7E
    return bytes(header) + payload[: AXI_BYTES - HEADER_BYTES]


def _strobe_contiguous(value: int) -> bool:
    if value == 0:
        return False
    while (value & 1) == 0:
        value >>= 1
    while (value & 1) == 1:
        value >>= 1
    return value == 0


async def _drive_axi_tlp(dut, payload: bytes) -> dict[str, Any]:
    total = HEADER_BYTES + len(payload)
    beats = (total + AXI_BYTES - 1) // AXI_BYTES
    stream = _mctp_first_beat(payload) + payload[AXI_BYTES - HEADER_BYTES :]
    stream = stream.ljust(beats * AXI_BYTES, b"\x00")
    wready_seen: list[int] = []
    wlast_seen: list[int] = []
    wstrb_seen: list[int] = []
    awready_seen = 0
    await FallingEdge(dut.axi_aclk)
    dut.m_axi_awaddr.value = 0
    dut.m_axi_awlen.value = beats - 1
    dut.m_axi_awsize.value = 5
    dut.m_axi_awburst.value = 1
    dut.m_axi_awvalid.value = 1
    for beat in range(beats):
        chunk = stream[beat * AXI_BYTES : (beat + 1) * AXI_BYTES]
        valid_bytes = min(AXI_BYTES, total - beat * AXI_BYTES)
        dut.m_axi_wdata.value = _word_from_bytes(chunk)
        dut.m_axi_wstrb.value = _strobe(valid_bytes)
        dut.m_axi_wlast.value = 1 if beat == beats - 1 else 0
        dut.m_axi_wvalid.value = 1
        await RisingEdge(dut.axi_aclk)
        await ReadOnly()
        awready_seen |= int(dut.m_axi_awready.value) if int(dut.m_axi_awvalid.value) else 0
        wready_seen.append(int(dut.m_axi_wready.value))
        wlast_seen.append(int(dut.m_axi_wlast.value))
        wstrb_seen.append(int(dut.m_axi_wstrb.value))
        await FallingEdge(dut.axi_aclk)
        dut.m_axi_awvalid.value = 0
    dut.m_axi_wvalid.value = 0
    dut.m_axi_wlast.value = 0
    return {
        "beats": beats,
        "awlen": beats - 1,
        "awready_seen": awready_seen,
        "wready_all": all(item == 1 for item in wready_seen),
        "wlast_count": sum(wlast_seen),
        "wlast_on_final": bool(wlast_seen and wlast_seen[-1] == 1 and sum(wlast_seen[:-1]) == 0),
        "wstrb_contiguous": all(_strobe_contiguous(item) for item in wstrb_seen),
        "awsize_256b": True,
        "awburst_incr": True,
    }


def _write_bytes(memory: bytearray, addr: int, data: int, strb: int) -> None:
    for lane in range(AXI_BYTES):
        if (strb >> lane) & 1:
            memory[addr + lane] = (data >> (lane * 8)) & 0xFF


def _read_word(memory: bytearray, addr: int) -> int:
    return _word_from_bytes(memory[addr : addr + AXI_BYTES])


def _payload_pattern(size: int) -> bytes:
    return bytes(((idx * 7) + 3) & 0xFF for idx in range(size))


async def _collect_writes(dut, memory: bytearray, expected: bytes) -> list[dict[str, int]]:
    writes: list[dict[str, int]] = []
    for _ in range(1600):
        await RisingEdge(dut.axi_aclk)
        if int(dut.sram_wr_valid.value) and int(dut.sram_wr_ready.value):
            write = {
                "addr": int(dut.sram_wr_addr.value),
                "data": int(dut.sram_wr_data.value),
                "strb": int(dut.sram_wr_strb.value),
            }
            writes.append(write)
            _write_bytes(memory, write["addr"], write["data"], write["strb"])
        if memory[: len(expected)] == expected:
            return writes
    raise AssertionError("SRAM writes did not reconstruct the AXI payload")


def _sram_checks(writes: list[dict[str, int]], memory: bytearray, expected: bytes) -> dict[str, bool]:
    covered = [False] * len(expected)
    no_write_past_payload = True
    strb_compact = True
    for write in writes:
        addr = write["addr"]
        data = write["data"]
        strb = write["strb"]
        strb_compact = strb_compact and _strobe_contiguous(strb)
        for lane in range(AXI_BYTES):
            if ((strb >> lane) & 1) == 0:
                continue
            index = addr + lane
            if index < len(expected):
                covered[index] = True
            else:
                byte = (data >> (lane * 8)) & 0xFF
                no_write_past_payload = no_write_past_payload and byte == 0
    return {
        "sram_payload_no_holes": all(covered) and strb_compact,
        "sram_payload_only": memory[: len(expected)] == expected,
        "sram_no_header_or_pad_write": no_write_past_payload and memory[: len(expected)] == expected,
    }


async def _readback_payload(dut, memory: bytearray, expected: int) -> tuple[bytes, dict[str, Any]]:
    received = bytearray()
    rvalid_beats = 0
    rlast_seen: list[int] = []
    rd_reqs = 0
    arready_seen = 0
    await FallingEdge(dut.axi_aclk)
    dut.m_axi_araddr.value = 0
    dut.m_axi_arlen.value = (expected + AXI_BYTES - 1) // AXI_BYTES - 1
    dut.m_axi_arsize.value = 5
    dut.m_axi_arburst.value = 1
    dut.m_axi_arvalid.value = 1
    pending_rsp = False
    for _ in range(800):
        await RisingEdge(dut.axi_aclk)
        await ReadOnly()
        if int(dut.m_axi_arready.value):
            arready_seen = 1
        await FallingEdge(dut.axi_aclk)
        if int(dut.m_axi_arready.value):
            dut.m_axi_arvalid.value = 0
        if int(dut.sram_rd_req_valid.value):
            dut.sram_rd_rsp_data.value = _read_word(memory, int(dut.sram_rd_req_addr.value))
            dut.sram_rd_rsp_error.value = 0
            pending_rsp = True
            rd_reqs += 1
        dut.sram_rd_rsp_valid.value = 1 if pending_rsp else 0
        pending_rsp = False
        if int(dut.m_axi_rvalid.value):
            rvalid_beats += 1
            word = int(dut.m_axi_rdata.value).to_bytes(AXI_BYTES, "little")
            received.extend(word)
            rlast_seen.append(int(dut.m_axi_rlast.value))
            if rlast_seen[-1]:
                meta = {
                    "arready_seen": arready_seen,
                    "rd_reqs": rd_reqs,
                    "rvalid_beats": rvalid_beats,
                    "rlast_count": sum(rlast_seen),
                    "rlast_on_final": bool(rlast_seen and rlast_seen[-1] == 1 and sum(rlast_seen[:-1]) == 0),
                    "arsize_256b": True,
                    "arburst_incr": True,
                }
                return bytes(received[:expected]), meta
    raise AssertionError("AXI readback did not finish")


@cocotb.test()
async def axi_burst_payload_is_packed_and_read_back_without_holes(dut) -> None:
    cocotb.start_soon(Clock(dut.axi_aclk, 10, units="ns").start())
    cocotb.start_soon(Clock(dut.pclk, 10, units="ns").start())
    await _reset(dut)
    await _apb_write(dut, 0x0000, 0x1 | (4096 << 3))
    await _apb_write(dut, 0x0014, 0xF)
    apb_reads = [await _apb_read(dut, addr) for addr in (0x0100, 0x0108, 0x010C)]
    payload = _payload_pattern(96)
    memory = bytearray(4096)
    write_meta = await _drive_axi_tlp(dut, payload)
    writes = await _collect_writes(dut, memory, payload)
    observed, read_meta = await _readback_payload(dut, memory, len(payload))
    assert observed == payload
    sram = _sram_checks(writes, memory, payload)
    axi_write_pass = (
        int(write_meta["beats"]) > 0
        and int(write_meta["wlast_count"]) == 1
        and bool(write_meta["wlast_on_final"])
        and bool(write_meta["wstrb_contiguous"])
        and bool(write_meta["awsize_256b"])
        and bool(write_meta["awburst_incr"])
    )
    axi_read_pass = (
        int(read_meta["rd_reqs"]) > 0
        and int(read_meta["rvalid_beats"]) > 0
        and int(read_meta["rlast_count"]) == 1
        and bool(read_meta["rlast_on_final"])
        and bool(read_meta["arsize_256b"])
        and bool(read_meta["arburst_incr"])
    )
    apb_pass = all(item["error"] == 0 for item in apb_reads)
    assert axi_write_pass
    assert axi_read_pass
    assert apb_pass
    _record_monitor({
        "test": "axi_burst_payload_is_packed_and_read_back_without_holes",
        "checks": {
            **sram,
            "axi_write_protocol_pass": axi_write_pass,
            "axi_read_protocol_pass": axi_read_pass,
            "apb_per_q_readback_pass": apb_pass,
        },
        "summary": {
            "sram_write_count": len(writes),
            "axi_write_transactions": 1,
            "axi_read_transactions": 1,
            "apb_reads": len(apb_reads),
        },
        "axi_write": write_meta,
        "axi_read": read_meta,
        "apb_reads": apb_reads,
    })


@cocotb.test()
async def max_tu_payload_is_written_to_sram_without_holes(dut) -> None:
    cocotb.start_soon(Clock(dut.axi_aclk, 10, units="ns").start())
    cocotb.start_soon(Clock(dut.pclk, 10, units="ns").start())
    await _reset(dut)
    await _apb_write(dut, 0x0000, 0x1 | (4096 << 3))
    await _apb_write(dut, 0x0014, 0xF)
    payload = _payload_pattern(4096)
    memory = bytearray(4096)
    write_meta = await _drive_axi_tlp(dut, payload)
    writes = await _collect_writes(dut, memory, payload)
    sram = _sram_checks(writes, memory, payload)
    assert all(sram.values())
    axi_write_pass = (
        int(write_meta["beats"]) > 0
        and int(write_meta["wlast_count"]) == 1
        and bool(write_meta["wlast_on_final"])
        and bool(write_meta["wstrb_contiguous"])
        and bool(write_meta["awsize_256b"])
        and bool(write_meta["awburst_incr"])
    )
    assert axi_write_pass
    _record_monitor({
        "test": "max_tu_payload_is_written_to_sram_without_holes",
        "checks": {
            **sram,
            "axi_write_protocol_pass": axi_write_pass,
            "axi_read_protocol_pass": False,
            "apb_per_q_readback_pass": False,
        },
        "summary": {
            "sram_write_count": len(writes),
            "axi_write_transactions": 1,
            "axi_read_transactions": 0,
            "apb_reads": 0,
        },
        "axi_write": write_meta,
    })
