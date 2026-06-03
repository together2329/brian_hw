from __future__ import annotations

from typing import Mapping, Sequence, Union


JsonScalar = Union[str, int, bool, None]
JsonValue = Union[JsonScalar, Mapping[str, "JsonValue"], Sequence["JsonValue"]]


def payload_strobe(payload_bytes: int) -> int:
    return (1 << max(1, min(payload_bytes, 32))) - 1


def mctp_word(
    *,
    source_eid: int,
    destination_eid: int,
    tag_owner: int,
    message_tag: int,
    packet_seq: int,
    som: int,
    eom: int,
    payload_bytes: int,
    payload_word: int,
) -> int:
    word = 0
    word |= (destination_eid & 0xFF) << 128
    word |= (source_eid & 0xFF) << 136
    word |= (message_tag & 0x7) << 144
    word |= (tag_owner & 0x1) << 147
    word |= (packet_seq & 0x3) << 148
    word |= (eom & 0x1) << 150
    word |= (som & 0x1) << 151
    word |= 0x7E << 152
    word |= (payload_word & ((1 << 96) - 1)) << 160
    word |= (payload_bytes & 0x1FFF) << 224
    return word


def axi_write_assign(
    *,
    source_eid: int,
    destination_eid: int,
    tag_owner: int,
    message_tag: int,
    packet_seq: int,
    som: int,
    eom: int,
    payload_bytes: int,
    payload_word: int,
) -> Mapping[str, JsonValue]:
    return {
        "m_axi_awvalid": 1,
        "m_axi_awlen": 0,
        "m_axi_awsize": 5,
        "m_axi_awburst": 1,
        "m_axi_wvalid": 1,
        "m_axi_wlast": 1,
        "m_axi_bready": 1,
        "m_axi_rready": 1,
        "sram_wr_ready": 1,
        "sram_rd_req_ready": 1,
        "m_axi_wstrb": ((payload_strobe(payload_bytes) << 20) | 0x000F_FFFF) & 0xFFFF_FFFF,
        "m_axi_wdata": mctp_word(
            source_eid=source_eid,
            destination_eid=destination_eid,
            tag_owner=tag_owner,
            message_tag=message_tag,
            packet_seq=packet_seq,
            som=som,
            eom=eom,
            payload_bytes=payload_bytes,
            payload_word=payload_word,
        ),
    }


def idle_axi_assign() -> Mapping[str, JsonValue]:
    return {
        "m_axi_awvalid": 0,
        "m_axi_wvalid": 0,
        "m_axi_wlast": 0,
        "m_axi_wstrb": 0,
        "m_axi_arvalid": 0,
        "sram_wr_ready": 1,
        "sram_rd_req_ready": 1,
    }


def fragment_timeline(*fragments: Mapping[str, JsonValue]) -> tuple[Mapping[str, JsonValue], ...]:
    steps: list[Mapping[str, JsonValue]] = []
    for fragment in fragments:
        steps.extend(({"assign": fragment}, {"wait_cycles": 1}, {"assign": idle_axi_assign()}, {"wait_cycles": 5}))
    return tuple(steps)
