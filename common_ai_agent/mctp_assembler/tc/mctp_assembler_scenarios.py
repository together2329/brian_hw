"""Directed scenario stimulus for mctp_assembler cocotb/pyuvm TB."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, List, Tuple

import sys
from pathlib import Path

_MODEL_DIR = Path(__file__).resolve().parents[1] / "model"
if str(_MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(_MODEL_DIR))

from functional_model import (  # noqa: E402
    AXI_DATA_BYTES,
    CONTEXT_COUNT,
    build_mctp_pcie_vdm_packet,
)

# APB byte offsets (12-bit address space, word-aligned)
A_CONTROL = 0x000
A_STATUS = 0x004
A_LOCAL_EID = 0x008
A_MTU_TIMEOUT = 0x00C
A_MAX_MSG = 0x010
A_SRAM_BASE = 0x014
A_SRAM_LIMIT = 0x018
A_SRAM_WR_PTR = 0x01C
A_INTR_ENABLE = 0x020
A_INTR_STATUS = 0x024
A_ERROR_STATUS = 0x028
A_DROP_STATUS = 0x02C
A_DESC_STATUS = 0x030
A_DESC_POP = 0x034
A_DESC_WORD0 = 0x038
A_DESC_WORD1 = 0x03C
A_DESC_WORD2 = 0x040
A_DESC_WORD3 = 0x044
A_PACKET_DROP_COUNT = 0x118
A_ASSEMBLY_DROP_COUNT = 0x11C

DEFAULT_LOCAL_EID = 0x22
DEFAULT_SRAM_BASE = 0x0000
DEFAULT_SRAM_LIMIT = 0xFFFF
DEFAULT_MAX_MSG = 4096
DEFAULT_AXI_AWADDR = 0x1000


@dataclass
class ApbWrite:
    addr: int
    data: int


@dataclass
class AxiBeat:
    data: int
    wstrb: int
    wlast: bool


@dataclass
class AxiTlpBurst:
    awaddr: int = DEFAULT_AXI_AWADDR
    beats: List[AxiBeat] = field(default_factory=list)


@dataclass
class BurstCheckpoint:
    """Expectations sampled on APB after burst index completes (0-based)."""

    after_burst: int
    active_context_count: int | None = None
    packet_drop_count: int | None = None


@dataclass
class AxiReadBurst:
    araddr: int = 0
    arlen: int = 0
    arsize: int = 5
    arburst: int = 1
    byte_count: int = 0


@dataclass
class Scenario:
    scenario_id: str
    description: str
    apb_setup: List[ApbWrite] = field(default_factory=list)
    tlps: List[List[int]] = field(default_factory=list)
    axi_bursts: List[AxiTlpBurst] = field(default_factory=list)
    axi_reads: List[AxiReadBurst] = field(default_factory=list)
    expect_descriptor: bool = False
    expect_descriptor_count: int = 0
    expect_packet_drop: bool = False
    expect_assembly_drop: bool = False
    expect_active_contexts: int | None = None
    burst_checkpoints: List[BurstCheckpoint] = field(default_factory=list)
    drain_descriptors_after_burst: List[int] = field(default_factory=list)
    coverage_refs: List[str] = field(default_factory=list)


def tlp_bytes_to_axi_beats(tlp_bytes: Iterable[int]) -> List[AxiBeat]:
    """Pack TLP bytes into AXI write beats (little-endian lane order)."""
    raw = [int(b) & 0xFF for b in tlp_bytes]
    beats: List[AxiBeat] = []
    idx = 0
    while idx < len(raw):
        chunk = raw[idx : idx + AXI_DATA_BYTES]
        data = 0
        wstrb = 0
        for lane, byte in enumerate(chunk):
            data |= byte << (8 * lane)
            wstrb |= 1 << lane
        idx += len(chunk)
        beats.append(AxiBeat(data=data, wstrb=wstrb, wlast=idx >= len(raw)))
    if not beats:
        beats.append(AxiBeat(data=0, wstrb=0, wlast=True))
    return beats


def burst_from_tlp(tlp_bytes: List[int], awaddr: int = DEFAULT_AXI_AWADDR) -> AxiTlpBurst:
    return AxiTlpBurst(awaddr=awaddr, beats=tlp_bytes_to_axi_beats(tlp_bytes))


def parse_status(status: int) -> dict[str, int]:
    return {
        "ingress_busy": status & 0x1,
        "context_active_any": (status >> 1) & 0x1,
        "error_pending": (status >> 2) & 0x1,
        "descriptor_available": (status >> 3) & 0x1,
        "desc_fifo_full": (status >> 4) & 0x1,
        "active_context_count": (status >> 5) & 0xF,
        "timeout_armed": (status >> 9) & 0x1,
    }


def context_key(slot: int) -> Tuple[int, int, int]:
    """Map slot 0..14 to unique (source_eid, tag_owner, message_tag)."""
    source_eid = (slot % CONTEXT_COUNT) + 1
    tag_owner = (slot >> 3) & 0x1
    message_tag = slot & 0x7
    return source_eid, tag_owner, message_tag


def som_fragment(slot: int) -> List[int]:
    source_eid, tag_owner, message_tag = context_key(slot)
    return build_mctp_pcie_vdm_packet(
        dest_eid=DEFAULT_LOCAL_EID,
        source_eid=source_eid,
        som=1,
        eom=0,
        seq=0,
        tag_owner=tag_owner,
        message_tag=message_tag,
        payload=[0x7E, slot & 0xFF],
    )


def eom_fragment(slot: int, seq: int = 1) -> List[int]:
    source_eid, tag_owner, message_tag = context_key(slot)
    return build_mctp_pcie_vdm_packet(
        dest_eid=DEFAULT_LOCAL_EID,
        source_eid=source_eid,
        som=0,
        eom=1,
        seq=seq,
        tag_owner=tag_owner,
        message_tag=message_tag,
        payload=[0x10 | (slot & 0xF)],
    )


def default_apb_setup(
    local_eid: int = DEFAULT_LOCAL_EID,
    enable: bool = True,
) -> List[ApbWrite]:
    control = 0x0000_0004  # dest_filter_enable reset default
    if enable:
        control |= 0x1
    return [
        ApbWrite(A_SRAM_BASE, DEFAULT_SRAM_BASE),
        ApbWrite(A_SRAM_LIMIT, DEFAULT_SRAM_LIMIT),
        ApbWrite(A_MAX_MSG, DEFAULT_MAX_MSG),
        ApbWrite(A_MTU_TIMEOUT, 64),
        ApbWrite(A_LOCAL_EID, local_eid & 0xFF),
        ApbWrite(A_CONTROL, control),
    ]


def _scenario_apb_regs() -> Scenario:
    return Scenario(
        scenario_id="SC_APB_REGS",
        description="APB reset defaults and basic read/write",
        apb_setup=[],
        coverage_refs=["SC_APB_REGS"],
    )


def _scenario_valid_single() -> Scenario:
    tlp = build_mctp_pcie_vdm_packet(dest_eid=DEFAULT_LOCAL_EID, source_eid=3, payload=[0x7E, 0x55, 0xAA])
    return Scenario(
        scenario_id="SC_VALID_SINGLE_PACKET",
        description="Single-packet SOM+EOM message completes with descriptor",
        apb_setup=default_apb_setup(),
        tlps=[tlp],
        axi_bursts=[burst_from_tlp(tlp)],
        expect_descriptor=True,
        coverage_refs=["SC_VALID_SINGLE_PACKET", "SC_AXI_ONE_BURST_ONE_TLP"],
    )


def _scenario_wrong_vendor() -> Scenario:
    tlp = build_mctp_pcie_vdm_packet(dest_eid=DEFAULT_LOCAL_EID, vendor_id=0xFFFF)
    return Scenario(
        scenario_id="SC_DROP_WRONG_VENDOR",
        description="Non-DMTF vendor ID is packet-dropped",
        apb_setup=default_apb_setup(),
        tlps=[tlp],
        axi_bursts=[burst_from_tlp(tlp)],
        expect_packet_drop=True,
        coverage_refs=["SC_DROP_WRONG_VENDOR"],
    )


def _scenario_multi_packet() -> Scenario:
    p0 = build_mctp_pcie_vdm_packet(
        dest_eid=DEFAULT_LOCAL_EID,
        source_eid=4,
        som=1,
        eom=0,
        seq=1,
        message_tag=1,
        payload=[0x7E, 0x10],
    )
    p1 = build_mctp_pcie_vdm_packet(
        dest_eid=DEFAULT_LOCAL_EID,
        source_eid=4,
        som=0,
        eom=1,
        seq=2,
        message_tag=1,
        payload=[0x11, 0x12],
    )
    return Scenario(
        scenario_id="SC_MULTI_PACKET",
        description="Two-fragment message assembles in order",
        apb_setup=default_apb_setup(),
        tlps=[p0, p1],
        axi_bursts=[burst_from_tlp(p0), burst_from_tlp(p1)],
        expect_descriptor=True,
        coverage_refs=["SC_MULTI_PACKET"],
    )


def _scenario_interleave_two() -> Scenario:
    a0 = build_mctp_pcie_vdm_packet(
        dest_eid=DEFAULT_LOCAL_EID,
        source_eid=6,
        som=1,
        eom=0,
        seq=1,
        message_tag=3,
        payload=[0x7E, 0xA0],
    )
    b0 = build_mctp_pcie_vdm_packet(
        dest_eid=DEFAULT_LOCAL_EID,
        source_eid=7,
        som=1,
        eom=0,
        seq=1,
        message_tag=4,
        payload=[0x7E, 0xB0],
    )
    a1 = build_mctp_pcie_vdm_packet(
        dest_eid=DEFAULT_LOCAL_EID,
        source_eid=6,
        som=0,
        eom=1,
        seq=2,
        message_tag=3,
        payload=[0xA1],
    )
    b1 = build_mctp_pcie_vdm_packet(
        dest_eid=DEFAULT_LOCAL_EID,
        source_eid=7,
        som=0,
        eom=1,
        seq=2,
        message_tag=4,
        payload=[0xB1],
    )
    tlps = [a0, b0, a1, b1]
    return Scenario(
        scenario_id="SC_INTERLEAVE_TWO",
        description="Two fragmented messages interleave at TLP boundaries",
        apb_setup=default_apb_setup(),
        tlps=tlps,
        axi_bursts=[burst_from_tlp(tlp) for tlp in tlps],
        expect_descriptor=True,
        expect_descriptor_count=2,
        coverage_refs=["SC_INTERLEAVE_TWO", "SC_INTERLEAVED_TAGS", "fcov_interleaving_15_contexts"],
    )


def _scenario_interleaved_tags() -> Scenario:
    som_tlps = [som_fragment(slot) for slot in range(CONTEXT_COUNT)]
    eom_tlps = [eom_fragment(slot) for slot in range(CONTEXT_COUNT)]
    tlps = som_tlps + eom_tlps
    checkpoints = [
        BurstCheckpoint(after_burst=CONTEXT_COUNT - 1, active_context_count=CONTEXT_COUNT),
    ]
    return Scenario(
        scenario_id="SC_INTERLEAVED_TAGS",
        description="Fifteen distinct assembly keys complete without cross-contamination",
        apb_setup=default_apb_setup(),
        tlps=tlps,
        axi_bursts=[burst_from_tlp(tlp) for tlp in tlps],
        expect_descriptor=True,
        expect_descriptor_count=CONTEXT_COUNT,
        expect_active_contexts=0,
        burst_checkpoints=checkpoints,
        drain_descriptors_after_burst=[CONTEXT_COUNT + 7],
        coverage_refs=["SC_INTERLEAVED_TAGS", "fcov_interleaving_15_contexts"],
    )


def _scenario_context_full() -> Scenario:
    som_tlps = [som_fragment(slot) for slot in range(CONTEXT_COUNT)]
    overflow = build_mctp_pcie_vdm_packet(
        dest_eid=DEFAULT_LOCAL_EID,
        source_eid=31,
        som=1,
        eom=0,
        seq=0,
        tag_owner=1,
        message_tag=7,
        payload=[0x7E, 0xFF],
    )
    tlps = som_tlps + [overflow]
    checkpoints = [
        BurstCheckpoint(after_burst=CONTEXT_COUNT - 1, active_context_count=CONTEXT_COUNT),
        BurstCheckpoint(after_burst=CONTEXT_COUNT, packet_drop_count=1),
    ]
    return Scenario(
        scenario_id="SC_CONTEXT_FULL",
        description="Sixteenth SOM is rejected when all 15 context slots are occupied",
        apb_setup=default_apb_setup(),
        tlps=tlps,
        axi_bursts=[burst_from_tlp(tlp) for tlp in tlps],
        expect_packet_drop=True,
        expect_active_contexts=CONTEXT_COUNT,
        burst_checkpoints=checkpoints,
        coverage_refs=["SC_CONTEXT_FULL", "fcov_interleaving_15_contexts"],
    )


def _scenario_seq_error() -> Scenario:
    p0 = build_mctp_pcie_vdm_packet(
        dest_eid=DEFAULT_LOCAL_EID,
        source_eid=5,
        som=1,
        eom=0,
        seq=0,
        message_tag=2,
        payload=[0x7E],
    )
    p1 = build_mctp_pcie_vdm_packet(
        dest_eid=DEFAULT_LOCAL_EID,
        source_eid=5,
        som=0,
        eom=1,
        seq=2,
        message_tag=2,
        payload=[0x01],
    )
    return Scenario(
        scenario_id="SC_SEQ_ERROR",
        description="Wrong continuation sequence triggers assembly drop",
        apb_setup=default_apb_setup(),
        tlps=[p0, p1],
        axi_bursts=[burst_from_tlp(p0), burst_from_tlp(p1)],
        expect_assembly_drop=True,
        coverage_refs=["SC_SEQ_ERROR"],
    )


def _payload_bytes(count: int, seed: int = 0) -> List[int]:
    return [0x7E] + [(seed + idx) & 0xFF for idx in range(max(0, count - 1))]


def _scenario_mtu_per_fragment() -> Scenario:
    setup = default_apb_setup()
    setup = [w for w in setup if w.addr != A_MTU_TIMEOUT] + [ApbWrite(A_MTU_TIMEOUT, 32)]
    tlp = build_mctp_pcie_vdm_packet(
        dest_eid=DEFAULT_LOCAL_EID,
        source_eid=9,
        som=1,
        eom=1,
        payload=_payload_bytes(40),
    )
    return Scenario(
        scenario_id="SC_MTU_PER_FRAGMENT",
        description="Single fragment larger than configured MTU is rejected",
        apb_setup=setup,
        tlps=[tlp],
        axi_bursts=[burst_from_tlp(tlp)],
        expect_assembly_drop=True,
        coverage_refs=["SC_MTU_PER_FRAGMENT"],
    )


def _scenario_multi_fragment_over_64b() -> Scenario:
    p0 = build_mctp_pcie_vdm_packet(
        dest_eid=DEFAULT_LOCAL_EID,
        source_eid=10,
        som=1,
        eom=0,
        seq=0,
        message_tag=5,
        payload=_payload_bytes(40),
    )
    p1 = build_mctp_pcie_vdm_packet(
        dest_eid=DEFAULT_LOCAL_EID,
        source_eid=10,
        som=0,
        eom=1,
        seq=1,
        message_tag=5,
        payload=_payload_bytes(40, seed=0x20),
    )
    return Scenario(
        scenario_id="SC_MULTI_FRAGMENT_OVER_64B",
        description="Two fragments each within MTU assemble to >64B total payload",
        apb_setup=default_apb_setup(),
        tlps=[p0, p1],
        axi_bursts=[burst_from_tlp(p0), burst_from_tlp(p1)],
        expect_descriptor=True,
        coverage_refs=["SC_MULTI_FRAGMENT_OVER_64B", "SC_MULTI_PACKET"],
    )


def _scenario_axi_read_single() -> Scenario:
    tlp = build_mctp_pcie_vdm_packet(dest_eid=DEFAULT_LOCAL_EID, source_eid=3, payload=[0x7E, 0x55, 0xAA])
    return Scenario(
        scenario_id="SC_AXI_READ_SINGLE",
        description="After message completion, read assembled payload through AXI read slave",
        apb_setup=default_apb_setup(),
        tlps=[tlp],
        axi_bursts=[burst_from_tlp(tlp)],
        expect_descriptor=True,
        axi_reads=[AxiReadBurst(araddr=0, arlen=0, arsize=2, arburst=1, byte_count=3)],
        coverage_refs=["SC_AXI_READ_SINGLE", "AXI_SRAM_READ", "SC_VALID_SINGLE_PACKET"],
    )


def _scenario_axi_read_burst() -> Scenario:
    p0 = build_mctp_pcie_vdm_packet(
        dest_eid=DEFAULT_LOCAL_EID,
        source_eid=11,
        som=1,
        eom=0,
        seq=0,
        message_tag=6,
        payload=_payload_bytes(20, seed=0x40),
    )
    p1 = build_mctp_pcie_vdm_packet(
        dest_eid=DEFAULT_LOCAL_EID,
        source_eid=11,
        som=0,
        eom=1,
        seq=1,
        message_tag=6,
        payload=_payload_bytes(16, seed=0x60),
    )
    return Scenario(
        scenario_id="SC_AXI_READ_BURST",
        description="Multi-beat AXI read burst retrieves payload spanning multiple RDATA beats",
        apb_setup=default_apb_setup(),
        tlps=[p0, p1],
        axi_bursts=[burst_from_tlp(p0), burst_from_tlp(p1)],
        expect_descriptor=True,
        axi_reads=[AxiReadBurst(araddr=0, arlen=1, arsize=5, arburst=1, byte_count=36)],
        coverage_refs=["SC_AXI_READ_BURST", "AXI_SRAM_READ", "SC_MULTI_PACKET"],
    )


def _scenario_wstrb_final() -> Scenario:
    tlp = build_mctp_pcie_vdm_packet(dest_eid=DEFAULT_LOCAL_EID, source_eid=6, payload=[0x7E, 0x01])
    beats = tlp_bytes_to_axi_beats(tlp)
    if len(beats) >= 2:
        beats[-1] = AxiBeat(data=beats[-1].data, wstrb=0x3, wlast=True)
    return Scenario(
        scenario_id="SC_AXI_WSTRB_FINAL",
        description="Final beat WSTRB masks unused byte lanes",
        apb_setup=default_apb_setup(),
        tlps=[tlp[:18]],
        axi_bursts=[AxiTlpBurst(beats=beats)],
        expect_descriptor=True,
        coverage_refs=["SC_AXI_WSTRB_FINAL"],
    )


SCENARIOS: dict[str, Scenario] = {
    s.scenario_id: s
    for s in [
        _scenario_apb_regs(),
        _scenario_valid_single(),
        _scenario_wrong_vendor(),
        _scenario_multi_packet(),
        _scenario_interleave_two(),
        _scenario_interleaved_tags(),
        _scenario_context_full(),
        _scenario_seq_error(),
        _scenario_mtu_per_fragment(),
        _scenario_multi_fragment_over_64b(),
        _scenario_axi_read_single(),
        _scenario_axi_read_burst(),
        _scenario_wstrb_final(),
    ]
}


def smoke_scenarios() -> List[Scenario]:
    return [
        SCENARIOS["SC_APB_REGS"],
        SCENARIOS["SC_VALID_SINGLE_PACKET"],
        SCENARIOS["SC_AXI_READ_SINGLE"],
        SCENARIOS["SC_AXI_READ_BURST"],
        SCENARIOS["SC_AXI_WSTRB_FINAL"],
        SCENARIOS["SC_DROP_WRONG_VENDOR"],
        SCENARIOS["SC_MULTI_PACKET"],
        SCENARIOS["SC_INTERLEAVE_TWO"],
        SCENARIOS["SC_SEQ_ERROR"],
        SCENARIOS["SC_INTERLEAVED_TAGS"],
        SCENARIOS["SC_CONTEXT_FULL"],
    ]


def queue_scenarios() -> List[Scenario]:
    """Context-queue / interleaving directed scenarios."""
    return [
        SCENARIOS["SC_INTERLEAVE_TWO"],
        SCENARIOS["SC_INTERLEAVED_TAGS"],
        SCENARIOS["SC_CONTEXT_FULL"],
    ]


def parse_descriptor_words(w0: int, w1: int, w2: int, w3: int) -> dict[str, Any]:
    return {
        "message_type": (w0 >> 24) & 0xFF,
        "tag_owner": (w0 >> 19) & 0x1,
        "message_tag": (w0 >> 16) & 0x7,
        "dest_eid": (w0 >> 8) & 0xFF,
        "source_eid": w0 & 0xFF,
        "requester_id": (w1 >> 16) & 0xFFFF,
        "payload_byte_count": w1 & 0xFFFF,
        "sram_start_addr": w2 & 0xFFFF,
        "context_id": (w3 >> 12) & 0xF,
        "final_sequence": (w3 >> 8) & 0x3,
    }
