#!/usr/bin/env python3
"""
Functional Model for mctp_assembler.

SSOT authority: yaml/mctp_assembler.ssot.yaml
Transactions:
  FM_ACCEPT_AXI_TLP, FM_FILTER_VDM, FM_PARSE_MCTP,
  FM_ASSEMBLE_FRAGMENT, FM_WRITE_SRAM_AND_DESCRIPTOR, FM_CLASSIFY_DROP

This model is the behavioral oracle for scoreboards. It models packet
filtering, 15-way MCTP assembly interleaving, SRAM payload writes, descriptor
publication, and packet-drop versus assembly-drop classification.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple


AXI_DATA_WIDTH = 256
AXI_DATA_BYTES = AXI_DATA_WIDTH // 8
CONTEXT_COUNT = 15
MAX_MESSAGE_BYTES = 4096
DESCRIPTOR_FIFO_DEPTH = 8
SRAM_ADDR_WIDTH = 16
DEFAULT_SRAM_LIMIT = (1 << SRAM_ADDR_WIDTH) - 1

MSG_CODE_VDM_TYPE_1 = 0x7F
VENDOR_ID_DMTF = 0x1AB4
MCTP_VDM_CODE = 0
MCTP_HDR_VERSION = 1

DROP_NONE = "none"
PACKET_DROP = "packet_drop"
ASSEMBLY_DROP = "assembly_drop"

DROP_REASON_CODES = {
    "DROP_NONE": 0x00,
    "PD_DISABLED_DROP_MODE": 0x01,
    "PD_MALFORMED_TLP": 0x02,
    "PD_UNSUPPORTED_VDM": 0x03,
    "PD_BAD_MCTP_HEADER": 0x04,
    "PD_DEST_EID_REJECT": 0x05,
    "PD_UNEXPECTED_MIDDLE_END": 0x06,
    "PD_BAD_OR_EXPIRED_TAG": 0x07,
    "PD_BAD_PAD_OR_ALIGNMENT": 0x08,
    "AD_DUPLICATE_SOM": 0x40,
    "AD_SEQUENCE_MISMATCH": 0x41,
    "AD_MESSAGE_OVERFLOW": 0x42,
    "AD_SRAM_OVERFLOW": 0x43,
    "AD_DESCRIPTOR_FULL": 0x44,
    "AD_TIMEOUT": 0x45,
}


def _u8(value: int) -> int:
    return int(value) & 0xFF


def _u16(value: int) -> int:
    return int(value) & 0xFFFF


def _bytes_from_int(value: int, width_bytes: int = AXI_DATA_BYTES) -> List[int]:
    return [(int(value) >> (8 * idx)) & 0xFF for idx in range(width_bytes)]


def _pack_word_bytes(data: List[int], width_bytes: int = AXI_DATA_BYTES) -> Tuple[int, int]:
    word = 0
    strb = 0
    for idx, byte in enumerate(data[:width_bytes]):
        word |= _u8(byte) << (8 * idx)
        strb |= 1 << idx
    return word, strb


def build_mctp_pcie_vdm_packet(
    *,
    dest_eid: int = 0,
    source_eid: int = 1,
    som: int = 1,
    eom: int = 1,
    seq: int = 0,
    tag_owner: int = 1,
    message_tag: int = 0,
    payload: Iterable[int] = (0x7E,),
    vendor_id: int = VENDOR_ID_DMTF,
    message_code: int = MSG_CODE_VDM_TYPE_1,
    mctp_vdm_code: int = MCTP_VDM_CODE,
    hdr_version: int = MCTP_HDR_VERSION,
    requester_id: int = 0x1234,
    target_id: int = 0x0000,
    pad_len: Optional[int] = None,
) -> List[int]:
    """Build a byte-vector matching this SSOT model's PCIe VDM/MCTP layout."""
    payload_bytes = [_u8(x) for x in payload]
    if pad_len is None:
        pad_len = (4 - (len(payload_bytes) % 4)) % 4 if eom else 0
    tag_byte = (int(mctp_vdm_code) & 0xF) | ((int(pad_len) & 0x3) << 4)
    flags = (
        ((_u8(som) & 1) << 7)
        | ((_u8(eom) & 1) << 6)
        | ((_u8(seq) & 0x3) << 4)
        | ((_u8(tag_owner) & 1) << 3)
        | (_u8(message_tag) & 0x7)
    )
    header = [
        0x70,
        0x00,
        0x00,
        0x00,
        (requester_id >> 8) & 0xFF,
        requester_id & 0xFF,
        tag_byte,
        _u8(message_code),
        (target_id >> 8) & 0xFF,
        target_id & 0xFF,
        (vendor_id >> 8) & 0xFF,
        vendor_id & 0xFF,
        _u8(hdr_version),
        _u8(dest_eid),
        _u8(source_eid),
        flags,
    ]
    return header + payload_bytes + [0] * int(pad_len)


@dataclass
class ParsedPacket:
    dest_eid: int
    source_eid: int
    som: int
    eom: int
    seq: int
    tag_owner: int
    message_tag: int
    payload: List[int]
    message_type: int
    requester_id: int
    target_id: int
    pad_len: int

    @property
    def key(self) -> Tuple[int, int, int]:
        return (self.source_eid, self.tag_owner, self.message_tag)


@dataclass
class AssemblyContext:
    key: Tuple[int, int, int]
    dest_eid: int
    expected_seq: int
    payload: List[int] = field(default_factory=list)
    start_addr: int = 0
    message_type: int = 0
    requester_id: int = 0
    context_id: int = 0
    age: int = 0


@dataclass
class Descriptor:
    source_eid: int
    dest_eid: int
    tag_owner: int
    message_tag: int
    message_type: int
    sram_start_addr: int
    payload_byte_count: int
    completion_status: str
    final_sequence: int
    context_id: int
    requester_id: int


class FunctionalModel:
    """Cycle-independent oracle for mctp_assembler."""

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        params = params or {}
        self.context_count = int(params.get("CONTEXT_COUNT", CONTEXT_COUNT))
        self.max_message_bytes = int(params.get("MAX_MESSAGE_BYTES", MAX_MESSAGE_BYTES))
        self.descriptor_fifo_depth = int(params.get("DESCRIPTOR_FIFO_DEPTH", DESCRIPTOR_FIFO_DEPTH))
        self.reset()

    def reset(self) -> Dict[str, Any]:
        self.enabled = False
        self.cfg_local_eid = 0
        self.cfg_dest_filter_enable = True
        self.cfg_mtu_bytes = 64
        self.cfg_max_message_bytes = self.max_message_bytes
        self.cfg_sram_base = 0
        self.cfg_sram_limit = 0
        self.cfg_timeout_cycles = 0
        self.drop_when_disabled = False
        self.accept_broadcast_eid = False
        self.accept_null_eid = False

        self.contexts: Dict[Tuple[int, int, int], AssemblyContext] = {}
        self.descriptor_fifo: List[Descriptor] = []
        self.sram_writes: List[Dict[str, Any]] = []
        self.sram_wr_ptr = 0
        self.interrupt_status: Dict[str, int] = {}
        self.error_status: Dict[str, int] = {}
        self.counters: Dict[str, int] = {
            "tlp_seen": 0,
            "tlp_accepted": 0,
            "tlp_rejected": 0,
            "messages_completed": 0,
            "bytes_written": 0,
            "packet_drop_count": 0,
            "assembly_drop_count": 0,
            "drop_count": 0,
            "sequence_error": 0,
            "overflow_error": 0,
            "timeout": 0,
        }
        self.last_drop_class = DROP_NONE
        self.last_drop_reason = "DROP_NONE"
        self.trace: List[Dict[str, Any]] = []
        return self.snapshot("reset")

    def configure(self, **kwargs: Any) -> Dict[str, Any]:
        for key, value in kwargs.items():
            if key == "enable":
                self.enabled = bool(value)
            elif key == "local_eid":
                self.cfg_local_eid = _u8(value)
            elif key == "dest_filter_enable":
                self.cfg_dest_filter_enable = bool(value)
            elif key == "sram_base":
                self.cfg_sram_base = int(value)
                self.sram_wr_ptr = int(value)
            elif key == "sram_limit":
                self.cfg_sram_limit = int(value)
            elif key == "max_message_bytes":
                self.cfg_max_message_bytes = int(value)
            elif key == "drop_when_disabled":
                self.drop_when_disabled = bool(value)
            elif key == "accept_broadcast_eid":
                self.accept_broadcast_eid = bool(value)
            elif key == "accept_null_eid":
                self.accept_null_eid = bool(value)
            elif key == "timeout_cycles":
                self.cfg_timeout_cycles = int(value)
        return self.snapshot("configure")

    def _record(self, label: str, **payload: Any) -> Dict[str, Any]:
        event = self.snapshot(label)
        event.update(payload)
        self.trace.append(event)
        return event

    def snapshot(self, label: str) -> Dict[str, Any]:
        return {
            "label": label,
            "enabled": self.enabled,
            "active_contexts": len(self.contexts),
            "descriptor_count": len(self.descriptor_fifo),
            "sram_write_count": len(self.sram_writes),
            "sram_wr_ptr": self.sram_wr_ptr,
            "last_drop_class": self.last_drop_class,
            "last_drop_reason": self.last_drop_reason,
            "counters": dict(self.counters),
            "interrupt_status": dict(self.interrupt_status),
            "error_status": dict(self.error_status),
        }

    def _classify_drop(self, drop_class: str, reason: str, key: Optional[Tuple[int, int, int]] = None) -> Dict[str, Any]:
        if drop_class not in {PACKET_DROP, ASSEMBLY_DROP}:
            drop_class = PACKET_DROP
        if reason not in DROP_REASON_CODES:
            reason = "PD_MALFORMED_TLP" if drop_class == PACKET_DROP else "AD_SEQUENCE_MISMATCH"

        self.last_drop_class = drop_class
        self.last_drop_reason = reason
        self.counters["drop_count"] += 1
        self.interrupt_status[drop_class] = 1
        self.error_status[f"{drop_class}_seen"] = 1

        if drop_class == PACKET_DROP:
            self.counters["packet_drop_count"] += 1
            self.counters["tlp_rejected"] += 1
        else:
            self.counters["assembly_drop_count"] += 1
            if key is not None:
                self.contexts.pop(key, None)

        if "SEQUENCE" in reason or "UNEXPECTED" in reason:
            self.counters["sequence_error"] += 1
        if "OVERFLOW" in reason or "FULL" in reason:
            self.counters["overflow_error"] += 1
        if reason == "AD_TIMEOUT":
            self.counters["timeout"] += 1

        return self._record(
            "FM_CLASSIFY_DROP",
            drop_class=drop_class,
            drop_reason=reason,
            drop_reason_code=DROP_REASON_CODES[reason],
            affected_key=key,
        )

    def _bytes_from_burst(self, txn: Dict[str, Any]) -> Tuple[Optional[List[int]], Optional[Dict[str, Any]]]:
        if "tlp_bytes" in txn:
            return [_u8(x) for x in txn.get("tlp_bytes", [])], None

        beats = txn.get("beats")
        if not beats:
            return None, {"reason": "PD_MALFORMED_TLP", "detail": "missing tlp_bytes or beats"}

        out: List[int] = []
        saw_last = False
        for idx, beat in enumerate(beats):
            if isinstance(beat, dict):
                data = beat.get("data", 0)
                wstrb = int(beat.get("wstrb", (1 << AXI_DATA_BYTES) - 1))
                wlast = bool(beat.get("wlast", idx == len(beats) - 1))
            else:
                data = beat
                wstrb = (1 << AXI_DATA_BYTES) - 1
                wlast = idx == len(beats) - 1
            if isinstance(data, (bytes, bytearray, list, tuple)):
                raw = [_u8(x) for x in data]
            else:
                raw = _bytes_from_int(int(data), AXI_DATA_BYTES)
            for byte_idx, byte in enumerate(raw[:AXI_DATA_BYTES]):
                if (wstrb >> byte_idx) & 1:
                    out.append(byte)
            if wlast:
                saw_last = True
                if idx != len(beats) - 1:
                    return None, {"reason": "PD_MALFORMED_TLP", "detail": "wlast before final supplied beat"}
        if not saw_last:
            return None, {"reason": "PD_MALFORMED_TLP", "detail": "missing wlast"}
        return out, None

    def accept_axi_tlp(self, txn: Dict[str, Any]) -> Dict[str, Any]:
        self.counters["tlp_seen"] += 1
        if not self.enabled:
            if self.drop_when_disabled:
                return self._classify_drop(PACKET_DROP, "PD_DISABLED_DROP_MODE")
            return self._record("FM_ACCEPT_AXI_TLP", accepted=False, backpressured=True)

        tlp_bytes, err = self._bytes_from_burst(txn)
        if err is not None:
            return self._classify_drop(PACKET_DROP, str(err["reason"]))
        if not tlp_bytes:
            return self._classify_drop(PACKET_DROP, "PD_MALFORMED_TLP")
        self.counters["tlp_accepted"] += 1
        return self._record("FM_ACCEPT_AXI_TLP", accepted=True, tlp_bytes=tlp_bytes, tlp_byte_count=len(tlp_bytes))

    def filter_vdm(self, tlp_bytes: List[int]) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        if len(tlp_bytes) < 16:
            return None, self._classify_drop(PACKET_DROP, "PD_MALFORMED_TLP")
        fmt_type = tlp_bytes[0]
        tag_byte = tlp_bytes[6]
        message_code = tlp_bytes[7]
        requester_id = (tlp_bytes[4] << 8) | tlp_bytes[5]
        target_id = (tlp_bytes[8] << 8) | tlp_bytes[9]
        vendor_id = (tlp_bytes[10] << 8) | tlp_bytes[11]
        mctp_vdm_code = tag_byte & 0xF
        pad_len = (tag_byte >> 4) & 0x3

        if (fmt_type & 0x70) != 0x70:
            return None, self._classify_drop(PACKET_DROP, "PD_UNSUPPORTED_VDM")
        if message_code != MSG_CODE_VDM_TYPE_1 or vendor_id != VENDOR_ID_DMTF or mctp_vdm_code != MCTP_VDM_CODE:
            return None, self._classify_drop(PACKET_DROP, "PD_UNSUPPORTED_VDM")

        accepted = {
            "tlp_bytes": tlp_bytes,
            "requester_id": requester_id,
            "target_id": target_id,
            "pad_len": pad_len,
        }
        return accepted, self._record("FM_FILTER_VDM", accepted=True, requester_id=requester_id, target_id=target_id, pad_len=pad_len)

    def parse_mctp(self, accepted_packet: Dict[str, Any]) -> Tuple[Optional[ParsedPacket], Optional[Dict[str, Any]]]:
        tlp_bytes = list(accepted_packet["tlp_bytes"])
        if len(tlp_bytes) < 16:
            return None, self._classify_drop(PACKET_DROP, "PD_BAD_MCTP_HEADER")
        hdr_version = tlp_bytes[12] & 0xF
        if hdr_version != MCTP_HDR_VERSION:
            return None, self._classify_drop(PACKET_DROP, "PD_BAD_MCTP_HEADER")
        dest_eid = tlp_bytes[13]
        source_eid = tlp_bytes[14]
        flags = tlp_bytes[15]
        som = (flags >> 7) & 1
        eom = (flags >> 6) & 1
        seq = (flags >> 4) & 0x3
        tag_owner = (flags >> 3) & 1
        message_tag = flags & 0x7
        pad_len = int(accepted_packet.get("pad_len", 0))
        payload = list(tlp_bytes[16:])

        if pad_len and not eom:
            return None, self._classify_drop(PACKET_DROP, "PD_BAD_PAD_OR_ALIGNMENT")
        if pad_len > len(payload):
            return None, self._classify_drop(PACKET_DROP, "PD_BAD_PAD_OR_ALIGNMENT")
        if pad_len:
            payload = payload[:-pad_len]

        if self.cfg_dest_filter_enable:
            allowed = dest_eid == self.cfg_local_eid
            allowed = allowed or (self.accept_broadcast_eid and dest_eid == 0xFF)
            allowed = allowed or (self.accept_null_eid and dest_eid == 0x00)
            if not allowed:
                return None, self._classify_drop(PACKET_DROP, "PD_DEST_EID_REJECT")

        pkt = ParsedPacket(
            dest_eid=dest_eid,
            source_eid=source_eid,
            som=som,
            eom=eom,
            seq=seq,
            tag_owner=tag_owner,
            message_tag=message_tag,
            payload=payload,
            message_type=payload[0] if payload else 0,
            requester_id=int(accepted_packet.get("requester_id", 0)),
            target_id=int(accepted_packet.get("target_id", 0)),
            pad_len=pad_len,
        )
        return pkt, self._record("FM_PARSE_MCTP", parsed=True, packet=asdict(pkt))

    def assemble_fragment(self, pkt: ParsedPacket) -> Dict[str, Any]:
        key = pkt.key
        if pkt.som and pkt.eom:
            if key in self.contexts:
                return self._classify_drop(ASSEMBLY_DROP, "AD_DUPLICATE_SOM", key)
            return self.write_sram_and_descriptor(pkt.payload, pkt, context_id=0)

        if pkt.som:
            if key in self.contexts:
                return self._classify_drop(ASSEMBLY_DROP, "AD_DUPLICATE_SOM", key)
            if len(self.contexts) >= self.context_count:
                return self._classify_drop(PACKET_DROP, "PD_BAD_OR_EXPIRED_TAG")
            if len(pkt.payload) > self.cfg_max_message_bytes:
                return self._classify_drop(ASSEMBLY_DROP, "AD_MESSAGE_OVERFLOW", key)
            context_id = self._next_context_id()
            self.contexts[key] = AssemblyContext(
                key=key,
                dest_eid=pkt.dest_eid,
                expected_seq=(pkt.seq + 1) & 0x3,
                payload=list(pkt.payload),
                start_addr=self.sram_wr_ptr,
                message_type=pkt.message_type,
                requester_id=pkt.requester_id,
                context_id=context_id,
            )
            self.sram_wr_ptr += self.cfg_max_message_bytes
            return self._record("FM_ASSEMBLE_FRAGMENT", action="allocate_context", key=key, context_id=context_id)

        ctx = self.contexts.get(key)
        if ctx is None:
            return self._classify_drop(PACKET_DROP, "PD_UNEXPECTED_MIDDLE_END")
        if pkt.seq != ctx.expected_seq:
            return self._classify_drop(ASSEMBLY_DROP, "AD_SEQUENCE_MISMATCH", key)
        next_payload = ctx.payload + list(pkt.payload)
        if len(next_payload) > self.cfg_max_message_bytes:
            return self._classify_drop(ASSEMBLY_DROP, "AD_MESSAGE_OVERFLOW", key)
        ctx.payload = next_payload
        ctx.expected_seq = (pkt.seq + 1) & 0x3
        if pkt.eom:
            self.contexts.pop(key, None)
            return self.write_sram_and_descriptor(ctx.payload, pkt, context_id=ctx.context_id, start_addr=ctx.start_addr)
        return self._record("FM_ASSEMBLE_FRAGMENT", action="append_payload", key=key, byte_count=len(ctx.payload))

    def _next_context_id(self) -> int:
        used = {ctx.context_id for ctx in self.contexts.values()}
        for idx in range(self.context_count):
            if idx not in used:
                return idx
        return self.context_count - 1

    def write_sram_and_descriptor(
        self,
        payload: List[int],
        pkt: ParsedPacket,
        *,
        context_id: int,
        start_addr: Optional[int] = None,
    ) -> Dict[str, Any]:
        if len(payload) > self.cfg_max_message_bytes:
            return self._classify_drop(ASSEMBLY_DROP, "AD_MESSAGE_OVERFLOW", pkt.key)
        if len(self.descriptor_fifo) >= self.descriptor_fifo_depth:
            return self._classify_drop(ASSEMBLY_DROP, "AD_DESCRIPTOR_FULL", pkt.key)
        base = self.sram_wr_ptr if start_addr is None else int(start_addr)
        limit = self.cfg_sram_limit
        if limit == 0:
            limit = DEFAULT_SRAM_LIMIT
        if base < self.cfg_sram_base or base + len(payload) - 1 > limit:
            return self._classify_drop(ASSEMBLY_DROP, "AD_SRAM_OVERFLOW", pkt.key)

        write_words: List[Dict[str, int]] = []
        for offset in range(0, len(payload), AXI_DATA_BYTES):
            chunk = payload[offset : offset + AXI_DATA_BYTES]
            data, strb = _pack_word_bytes(chunk)
            write = {"addr": base + offset, "data": data, "strb": strb, "bytes": list(chunk)}
            self.sram_writes.append(write)
            write_words.append(write)

        desc = Descriptor(
            source_eid=pkt.source_eid,
            dest_eid=pkt.dest_eid,
            tag_owner=pkt.tag_owner,
            message_tag=pkt.message_tag,
            message_type=payload[0] if payload else 0,
            sram_start_addr=base,
            payload_byte_count=len(payload),
            completion_status="ok",
            final_sequence=pkt.seq,
            context_id=context_id,
            requester_id=pkt.requester_id,
        )
        self.descriptor_fifo.append(desc)
        next_ptr = base + len(payload)
        if next_ptr > self.sram_wr_ptr:
            self.sram_wr_ptr = next_ptr
        self.counters["messages_completed"] += 1
        self.counters["bytes_written"] += len(payload)
        self.interrupt_status["desc_ready"] = 1
        return self._record("FM_WRITE_SRAM_AND_DESCRIPTOR", descriptor=asdict(desc), sram_writes=write_words)

    def process_tlp(self, txn: Dict[str, Any]) -> Dict[str, Any]:
        accept = self.accept_axi_tlp(txn)
        if not accept.get("accepted"):
            return accept
        accepted_packet, filter_event = self.filter_vdm(accept["tlp_bytes"])
        if accepted_packet is None:
            return filter_event or self.snapshot("filter_failed")
        pkt, parse_event = self.parse_mctp(accepted_packet)
        if pkt is None:
            return parse_event or self.snapshot("parse_failed")
        return self.assemble_fragment(pkt)

    def timeout_context(self, key: Tuple[int, int, int]) -> Dict[str, Any]:
        if key not in self.contexts:
            return self._classify_drop(PACKET_DROP, "PD_BAD_OR_EXPIRED_TAG")
        return self._classify_drop(ASSEMBLY_DROP, "AD_TIMEOUT", key)

    def apb_write(self, addr: int, data: int) -> Dict[str, Any]:
        addr = int(addr)
        data = int(data)
        if addr == 0x000:
            self.configure(
                enable=bool(data & 0x1),
                drop_when_disabled=bool(data & 0x8),
                dest_filter_enable=bool(data & 0x4),
                accept_broadcast_eid=bool(data & 0x10),
                accept_null_eid=bool(data & 0x20),
            )
            if data & 0x2:
                self.contexts.clear()
        elif addr == 0x008:
            self.cfg_local_eid = data & 0xFF
        elif addr == 0x010:
            self.cfg_max_message_bytes = data & 0xFFFF
        elif addr == 0x014:
            self.cfg_sram_base = data
            self.sram_wr_ptr = data
        elif addr == 0x018:
            self.cfg_sram_limit = data
        elif addr == 0x024:
            for name in list(self.interrupt_status):
                self.interrupt_status[name] = 0
        elif addr == 0x028:
            for name in list(self.error_status):
                self.error_status[name] = 0
        elif addr == 0x034 and (data & 1) and self.descriptor_fifo:
            self.descriptor_fifo.pop(0)
        return self._record("apb_write", addr=addr, data=data)

    def apb_read(self, addr: int) -> Dict[str, Any]:
        addr = int(addr)
        value = 0
        if addr == 0x004:
            value = (
                (1 if self.contexts else 0) << 1
                | (1 if self.descriptor_fifo else 0) << 2
                | (1 if any(self.error_status.values()) else 0) << 3
            )
        elif addr == 0x02C:
            value = (
                (1 if self.last_drop_class == PACKET_DROP else 0)
                | ((1 if self.last_drop_class == ASSEMBLY_DROP else 0) << 1)
                | ((1 if self.last_drop_class == PACKET_DROP else 2 if self.last_drop_class == ASSEMBLY_DROP else 0) << 4)
                | ((DROP_REASON_CODES.get(self.last_drop_reason, 0) & 0xFF) << 8)
            )
        elif addr == 0x030:
            value = len(self.descriptor_fifo) & 0xFF
        elif addr == 0x118:
            value = self.counters["packet_drop_count"]
        elif addr == 0x11C:
            value = self.counters["assembly_drop_count"]
        return self._record("apb_read", addr=addr, data=value)

    def apply(self, txn: Any) -> Dict[str, Any]:
        if not isinstance(txn, dict):
            txn = asdict(txn) if hasattr(txn, "__dataclass_fields__") else {"kind": str(txn)}
        kind = str(txn.get("kind") or txn.get("op") or "axi_tlp")
        kind_l = kind.lower()

        if kind_l in {"configure", "config"}:
            return self.configure(**dict(txn.get("config", txn)))
        if kind_l in {"apb_write", "fm_csr_write"}:
            return self.apb_write(int(txn.get("addr", 0)), int(txn.get("data", 0)))
        if kind_l in {"apb_read", "fm_csr_read"}:
            return self.apb_read(int(txn.get("addr", 0)))
        if kind_l in {"fm_accept_axi_tlp"}:
            if "tlp_bytes" not in txn and "beats" not in txn:
                txn = {**txn, "tlp_bytes": build_mctp_pcie_vdm_packet(dest_eid=self.cfg_local_eid)}
            return self.accept_axi_tlp(txn)
        if kind_l in {"fm_filter_vdm"}:
            tlp = list(txn.get("tlp_bytes") or build_mctp_pcie_vdm_packet(dest_eid=self.cfg_local_eid))
            _accepted, event = self.filter_vdm(tlp)
            return event or self.snapshot("FM_FILTER_VDM")
        if kind_l in {"fm_parse_mctp"}:
            tlp = list(txn.get("tlp_bytes") or build_mctp_pcie_vdm_packet(dest_eid=self.cfg_local_eid))
            accepted, event = self.filter_vdm(tlp)
            if accepted is None:
                return event or self.snapshot("FM_PARSE_MCTP")
            _pkt, parse_event = self.parse_mctp(accepted)
            return parse_event or self.snapshot("FM_PARSE_MCTP")
        if kind_l in {"fm_assemble_fragment"}:
            pkt = txn.get("packet")
            if not isinstance(pkt, ParsedPacket):
                payload = txn.get("payload", [0x7E, 0xAA])
                pkt = ParsedPacket(
                    dest_eid=int(txn.get("dest_eid", self.cfg_local_eid)),
                    source_eid=int(txn.get("source_eid", 1)),
                    som=int(txn.get("som", 1)),
                    eom=int(txn.get("eom", 0)),
                    seq=int(txn.get("seq", 0)),
                    tag_owner=int(txn.get("tag_owner", 1)),
                    message_tag=int(txn.get("message_tag", 1)),
                    payload=[_u8(x) for x in payload],
                    message_type=_u8(payload[0]) if payload else 0,
                    requester_id=int(txn.get("requester_id", 0)),
                    target_id=int(txn.get("target_id", 0)),
                    pad_len=0,
                )
            return self.assemble_fragment(pkt)
        if kind_l in {"fm_write_sram_and_descriptor"}:
            pkt = ParsedPacket(
                dest_eid=self.cfg_local_eid,
                source_eid=int(txn.get("source_eid", 2)),
                som=1,
                eom=1,
                seq=int(txn.get("seq", 0)),
                tag_owner=int(txn.get("tag_owner", 1)),
                message_tag=int(txn.get("message_tag", 2)),
                payload=[_u8(x) for x in txn.get("payload", [0x7E, 0x55])],
                message_type=_u8(txn.get("payload", [0x7E])[0]),
                requester_id=int(txn.get("requester_id", 0)),
                target_id=0,
                pad_len=0,
            )
            return self.write_sram_and_descriptor(pkt.payload, pkt, context_id=0)
        if kind_l in {"fm_classify_drop", "classify_drop"}:
            return self._classify_drop(str(txn.get("drop_class", PACKET_DROP)), str(txn.get("reason", "PD_MALFORMED_TLP")), txn.get("key"))
        if kind_l in {"timeout"}:
            return self.timeout_context(tuple(txn.get("key", (1, 1, 0))))
        return self.process_tlp(txn)

    def check_invariants(self) -> List[str]:
        issues: List[str] = []
        if len(self.contexts) > self.context_count:
            issues.append("context count exceeds configured assembly queue depth")
        for key, ctx in self.contexts.items():
            if key != ctx.key:
                issues.append(f"context key mismatch for {key}")
            if len(ctx.payload) > self.cfg_max_message_bytes:
                issues.append(f"context {key} exceeds max message bytes")
        if self.last_drop_class not in {DROP_NONE, PACKET_DROP, ASSEMBLY_DROP}:
            issues.append("invalid last_drop_class")
        return issues

    def run_self_check(self) -> Dict[str, Any]:
        transaction_results: Dict[str, str] = {}
        checks: Dict[str, str] = {}

        def run(name: str, fn) -> None:
            try:
                fn()
                checks[name] = "PASS"
            except Exception as exc:
                checks[name] = f"FAIL: {type(exc).__name__}: {exc}"

        def configured() -> "FunctionalModel":
            m = FunctionalModel()
            m.configure(enable=True, local_eid=0x22, sram_base=0, sram_limit=DEFAULT_SRAM_LIMIT)
            return m

        def sc_accept() -> None:
            m = configured()
            res = m.apply({"kind": "FM_ACCEPT_AXI_TLP", "tlp_bytes": build_mctp_pcie_vdm_packet(dest_eid=0x22)})
            assert res["accepted"] is True
            transaction_results["FM_ACCEPT_AXI_TLP"] = "PASS"

        def sc_filter() -> None:
            m = configured()
            res = m.apply({"kind": "FM_FILTER_VDM", "tlp_bytes": build_mctp_pcie_vdm_packet(dest_eid=0x22)})
            assert res["accepted"] is True
            transaction_results["FM_FILTER_VDM"] = "PASS"

        def sc_parse() -> None:
            m = configured()
            res = m.apply({"kind": "FM_PARSE_MCTP", "tlp_bytes": build_mctp_pcie_vdm_packet(dest_eid=0x22, source_eid=3, payload=[0x7E, 1])})
            assert res["packet"]["source_eid"] == 3
            transaction_results["FM_PARSE_MCTP"] = "PASS"

        def sc_assemble() -> None:
            m = configured()
            p0 = build_mctp_pcie_vdm_packet(dest_eid=0x22, source_eid=4, som=1, eom=0, seq=1, message_tag=1, payload=[0x7E, 0x10])
            p1 = build_mctp_pcie_vdm_packet(dest_eid=0x22, source_eid=4, som=0, eom=1, seq=2, message_tag=1, payload=[0x11, 0x12])
            assert m.apply({"tlp_bytes": p0})["action"] == "allocate_context"
            res = m.apply({"tlp_bytes": p1})
            assert res["descriptor"]["payload_byte_count"] == 4
            transaction_results["FM_ASSEMBLE_FRAGMENT"] = "PASS"

        def sc_write() -> None:
            m = configured()
            res = m.apply({"kind": "FM_WRITE_SRAM_AND_DESCRIPTOR", "payload": [0x7E, 0x55, 0xAA]})
            assert res["descriptor"]["payload_byte_count"] == 3
            assert m.descriptor_fifo
            transaction_results["FM_WRITE_SRAM_AND_DESCRIPTOR"] = "PASS"

        def sc_drop() -> None:
            m = configured()
            bad = build_mctp_pcie_vdm_packet(dest_eid=0x22, vendor_id=0xFFFF)
            res = m.apply({"tlp_bytes": bad})
            assert res["drop_class"] == PACKET_DROP
            p0 = build_mctp_pcie_vdm_packet(dest_eid=0x22, source_eid=5, som=1, eom=0, seq=0, message_tag=2, payload=[0x7E])
            p1 = build_mctp_pcie_vdm_packet(dest_eid=0x22, source_eid=5, som=0, eom=1, seq=2, message_tag=2, payload=[0x01])
            assert m.apply({"tlp_bytes": p0})["action"] == "allocate_context"
            res = m.apply({"tlp_bytes": p1})
            assert res["drop_class"] == ASSEMBLY_DROP
            transaction_results["FM_CLASSIFY_DROP"] = "PASS"

        def sc_interleaving_15() -> None:
            m = configured()
            for tag in range(15):
                pkt = build_mctp_pcie_vdm_packet(dest_eid=0x22, source_eid=tag + 1, som=1, eom=0, seq=0, message_tag=tag & 0x7, tag_owner=(tag >> 3) & 1, payload=[0x7E, tag])
                assert m.apply({"tlp_bytes": pkt})["action"] == "allocate_context"
            assert len(m.contexts) == 15
            overflow = build_mctp_pcie_vdm_packet(dest_eid=0x22, source_eid=31, som=1, eom=0, seq=0, message_tag=0, payload=[0x7E])
            assert m.apply({"tlp_bytes": overflow})["drop_class"] == PACKET_DROP

        for name, fn in {
            "FM_ACCEPT_AXI_TLP": sc_accept,
            "FM_FILTER_VDM": sc_filter,
            "FM_PARSE_MCTP": sc_parse,
            "FM_ASSEMBLE_FRAGMENT": sc_assemble,
            "FM_WRITE_SRAM_AND_DESCRIPTOR": sc_write,
            "FM_CLASSIFY_DROP": sc_drop,
            "SC_INTERLEAVING_15": sc_interleaving_15,
        }.items():
            run(name, fn)

        passed = all(v == "PASS" for v in checks.values()) and all(
            key in transaction_results for key in [
                "FM_ACCEPT_AXI_TLP",
                "FM_FILTER_VDM",
                "FM_PARSE_MCTP",
                "FM_ASSEMBLE_FRAGMENT",
                "FM_WRITE_SRAM_AND_DESCRIPTOR",
                "FM_CLASSIFY_DROP",
            ]
        )
        return {
            "passed": passed,
            "transaction_results": transaction_results,
            "checks": checks,
            "context_count": self.context_count,
            "drop_reason_codes": dict(DROP_REASON_CODES),
        }


def run_self_check() -> Dict[str, Any]:
    return FunctionalModel().run_self_check()


if __name__ == "__main__":
    print(json.dumps(run_self_check(), indent=2, sort_keys=True))
