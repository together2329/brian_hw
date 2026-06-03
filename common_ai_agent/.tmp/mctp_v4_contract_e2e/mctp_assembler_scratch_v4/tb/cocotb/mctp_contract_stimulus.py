from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from mctp_assembler_scratch.tb.cocotb.mctp_scenario_stimulus import apply_scenario_contract_defaults


BOOL_EXACT = {
    "axi_aw_accept",
    "axi_ar_accept",
    "axi_wlast_seen",
    "context_accept",
    "context_alloc",
    "descriptor_publish",
    "descriptor_ready",
    "eom",
    "payload_valid",
    "read_has_descriptor",
    "read_last",
    "som",
    "tag_owner",
    "word_full",
}

BOOL_SUFFIXES = (
    "_accept",
    "_alloc",
    "_enable",
    "_pending",
    "_publish",
    "_ready",
    "_seen",
    "_valid",
)

PACKET_WORDS = (
    "accept_axi_tlp",
    "assembly_drop",
    "assemble",
    "complete_message",
    "drop",
    "fragment",
    "interleave",
    "mctp",
    "packet",
    "parse",
    "pd_",
    "sram_pack",
    "tlp",
    "tu64",
    "vdm",
)

APB_ONLY_WORDS = ("apb", "csr", "register")
READBACK_WORDS = ("axi_readback", "readback")


def normalize_mctp_stimulus(goal: dict[str, Any], stimulus: dict[str, Any]) -> dict[str, Any]:
    out = dict(stimulus)
    pre_idle = dict(out)
    for key, value in list(out.items()):
        if _is_bool_field(key):
            out[key] = 1 if int(value or 0) else 0

    text = _goal_text(goal, out)
    apply_scenario_contract_defaults(goal, out)
    if "sc_max_tu_4096" in text:
        out["scenario_payload_bytes"] = 4096
        out["payload_len"] = 4096
        out["payload_byte_count"] = 4096
        out["m_axi_awlen"] = 128
    if "filter_vdm" in text and int(out.get("vdm_supported", 1) or 0):
        out["packet_drop_reason"] = 0
    _idle_axi(out)
    if _is_readback_goal(text):
        if "readback_after_multi_assemble" in text:
            out["payload_len"] = int(out.get("scenario_payload_bytes", 76) or 76)
            out["payload_byte_count"] = out["payload_len"]
            out["som"] = 1
            out["eom"] = 1
            _apply_axi_write_defaults(out, malformed=False)
            _encode_mctp_word(out)
            out["m_axi_arvalid"] = 1
            out["m_axi_arsize"] = 5
            out["m_axi_arburst"] = 1
            out["m_axi_arlen"] = 0
            out["sram_rd_rsp_valid"] = 1
            out["sram_rd_rsp_error"] = 0
            return out
        _apply_readback_defaults(out)
        return out
    if _is_apb_only_goal(text):
        _apply_apb_defaults(out, pre_idle)
        return out
    if _is_packet_goal(text):
        _apply_axi_write_defaults(out, malformed=_is_malformed_packet_goal(text, out))
        _apply_packet_contract_defaults(out)
        _encode_mctp_word(out)
    return out


def _is_bool_field(name: str) -> bool:
    low = name.lower()
    return low in BOOL_EXACT or low.endswith(BOOL_SUFFIXES)


def _goal_text(goal: dict[str, Any], stimulus: dict[str, Any]) -> str:
    pieces: list[str] = []
    for key in ("goal_id", "title", "kind", "scenario", "intent"):
        if goal.get(key):
            pieces.append(str(goal[key]))
    contract = goal.get("stimulus_contract")
    if isinstance(contract, dict):
        for key in ("transaction_type", "constraints", "required_fields"):
            if contract.get(key):
                pieces.append(str(contract[key]))
    for key in ("kind", "scenario_id", "op"):
        if stimulus.get(key):
            pieces.append(str(stimulus[key]))
    return " ".join(pieces).replace("-", "_").lower()


def _is_apb_only_goal(text: str) -> bool:
    return any(word in text for word in APB_ONLY_WORDS) and not _is_packet_goal(text)


def _is_readback_goal(text: str) -> bool:
    if any(token in text for token in ("accept_axi_tlp", "one_tlp", "write_transaction", "perf_throughput")):
        return False
    return any(word in text for word in READBACK_WORDS)


def _is_packet_goal(text: str) -> bool:
    if any(word in text for word in APB_ONLY_WORDS):
        return False
    return text.startswith("eq_transaction_fm_accept_axi_tlp") or any(word in text for word in PACKET_WORDS)


def _is_malformed_packet_goal(text: str, stimulus: dict[str, Any]) -> bool:
    if int(stimulus.get("scenario_force_valid_packet", 0) or 0):
        return False
    if "filter_vdm" in text:
        return False
    if "ad_duplicate_som" in text or "ad_sram_overflow" in text:
        return False
    if any(token in text for token in ("packet_drop", "_pd_", "_ad_", "assembly_drop")):
        return True
    reason = int(stimulus.get("packet_drop_reason") or 0)
    return "malformed" in text or reason == 2


def _idle_axi(stimulus: dict[str, Any]) -> None:
    stimulus["m_axi_awvalid"] = 0
    stimulus["m_axi_wvalid"] = 0
    stimulus["m_axi_wlast"] = 0
    stimulus["m_axi_arvalid"] = 0
    stimulus["m_axi_bready"] = 1
    stimulus["m_axi_rready"] = 1
    stimulus["psel"] = 0
    stimulus["penable"] = 0
    stimulus["pwrite"] = 0
    stimulus["sram_wr_ready"] = 1
    stimulus["sram_rd_req_ready"] = 1
    stimulus["sram_rd_rsp_valid"] = 0
    stimulus["sram_rd_rsp_error"] = 0


def _apply_axi_write_defaults(stimulus: dict[str, Any], *, malformed: bool) -> None:
    stimulus["m_axi_awvalid"] = 1
    stimulus["m_axi_wvalid"] = 1
    stimulus["m_axi_wlast"] = 1
    stimulus["m_axi_awsize"] = 5
    stimulus["m_axi_awburst"] = 1
    stimulus["m_axi_awlen"] = 0
    stimulus["m_axi_arvalid"] = 0
    stimulus["m_axi_bready"] = 1
    stimulus["m_axi_rready"] = 1
    stimulus["sram_wr_ready"] = 1
    stimulus["sram_rd_req_ready"] = 1
    stimulus["sram_rd_rsp_valid"] = int(stimulus.get("sram_rd_rsp_valid", 1) or 1)
    stimulus["sram_rd_rsp_error"] = int(stimulus.get("sram_rd_rsp_error", 0) or 0)
    payload_len = int(stimulus.get("payload_len", stimulus.get("payload_byte_count", 16)) or 16)
    payload_len = max(1, min(payload_len, 32))
    default_strobe = (1 << payload_len) - 1
    payload_strobe = int(stimulus.get("payload_byte_strobe", default_strobe) or default_strobe) & ((1 << 32) - 1)
    if payload_strobe <= 0 or not _is_contiguous_strobe(payload_strobe):
        payload_strobe = default_strobe
    stimulus["payload_byte_strobe"] = payload_strobe
    stimulus["m_axi_wstrb"] = 0 if malformed else ((payload_strobe << 20) | 0x000FFFFF)


def _is_contiguous_strobe(value: int) -> bool:
    normalized = value >> ((value & -value).bit_length() - 1)
    return (normalized & (normalized + 1)) == 0


def _apply_readback_defaults(stimulus: dict[str, Any]) -> None:
    axi_ar_accept = 1 if int(stimulus.get("axi_ar_accept", 1) or 0) else 0
    read_last = 1 if int(stimulus.get("read_last", 1) or 0) else 0
    stimulus["axi_ar_accept"] = axi_ar_accept
    stimulus["read_last"] = read_last
    stimulus["m_axi_awvalid"] = 0
    stimulus["m_axi_wvalid"] = 0
    stimulus["m_axi_wlast"] = 0
    stimulus["m_axi_arvalid"] = axi_ar_accept
    stimulus["m_axi_arsize"] = 5
    stimulus["m_axi_arburst"] = 1
    stimulus["m_axi_arlen"] = 0
    stimulus["m_axi_rready"] = 1
    stimulus["sram_rd_req_ready"] = 1
    stimulus["sram_rd_rsp_valid"] = axi_ar_accept
    stimulus["sram_rd_rsp_error"] = 0 if int(stimulus.get("read_has_descriptor", 0) or 0) else 1
    stimulus["sram_rd_rsp_data"] = int(stimulus.get("readback_data", stimulus.get("sram_rd_rsp_data", 0)) or 0)


def _encode_mctp_word(stimulus: dict[str, Any]) -> None:
    source_eid = int(stimulus.get("source_eid", 0)) & 0xFF
    destination_eid = int(stimulus.get("destination_eid", 1)) & 0xFF
    tag_owner = int(stimulus.get("tag_owner", 0)) & 0x1
    message_tag = int(stimulus.get("message_tag", stimulus.get("context_id", 0))) & 0x7
    packet_seq = int(stimulus.get("packet_seq", 0)) & 0x3
    wants_assembling = "assemble_fragment" in str(stimulus.get("kind", "")).lower() or "assemble_fragment" in str(stimulus.get("scenario_id", "")).lower()
    som = int(stimulus.get("som", 1)) & 0x1
    eom = int(stimulus.get("eom", 0 if wants_assembling else 1)) & 0x1
    message_type = int(stimulus.get("message_type", 0x7E)) & 0xFF
    payload = int(stimulus.get("payload_data_word", stimulus.get("m_axi_wdata", 0x11))) & ((1 << 96) - 1)
    payload_len = int(stimulus.get("payload_len", stimulus.get("payload_byte_count", 16)) or 16) & 0x1FFF

    word = int(stimulus.get("m_axi_wdata", 0)) & ((1 << 128) - 1)
    word |= destination_eid << 128
    word |= source_eid << 136
    word |= message_tag << 144
    word |= tag_owner << 147
    word |= packet_seq << 148
    word |= eom << 150
    word |= som << 151
    word |= message_type << 152
    word |= payload << 160
    word |= payload_len << 224
    stimulus["m_axi_wdata"] = word
    stimulus["source_eid"] = source_eid
    stimulus["tag_owner"] = tag_owner
    stimulus["message_tag"] = message_tag
    stimulus["packet_seq"] = packet_seq
    stimulus["som"] = som
    stimulus["eom"] = eom


def _apply_apb_defaults(stimulus: dict[str, Any], pre_idle: dict[str, Any]) -> None:
    stimulus["apb_access"] = 1 if int(pre_idle.get("apb_access", 1) or 0) else 0
    apb_write = 1 if int(pre_idle.get("apb_write", pre_idle.get("pwrite", 0)) or 0) else 0
    stimulus["apb_write"] = apb_write
    stimulus["psel"] = 1
    stimulus["penable"] = 1
    stimulus["pwrite"] = apb_write
    stimulus["pstrb"] = int(pre_idle.get("pstrb", stimulus.get("pstrb", 0xF)) or 0xF)
    apb_wdata = int(pre_idle.get("apb_wdata", pre_idle.get("pwdata", 0)) or 0)
    stimulus["apb_wdata"] = apb_wdata
    stimulus["pwdata"] = apb_wdata
    paddr = int(pre_idle.get("paddr", pre_idle.get("addr", 0)) or 0)
    if int(pre_idle.get("illegal_apb_access", 0) or 0):
        illegal_addr = (paddr | 0x8000) if paddr else 0xFFFF
        stimulus["paddr"] = illegal_addr
        stimulus["addr"] = illegal_addr
        stimulus["illegal_apb_access"] = 1
    else:
        stimulus["paddr"] = paddr
        stimulus["addr"] = paddr
        stimulus["illegal_apb_access"] = 0


def _apply_packet_contract_defaults(stimulus: dict[str, Any]) -> None:
    stimulus["vdm_supported"] = 1 if int(stimulus.get("vdm_supported", 1) or 0) else 0
    stimulus["payload_valid"] = 1 if int(stimulus.get("payload_valid", 1) or 0) else 0
    stimulus["descriptor_publish"] = 1 if int(stimulus.get("descriptor_publish", 1) or 0) else 0
    if "apb_wdata" not in stimulus:
        stimulus["apb_wdata"] = int(stimulus.get("pwdata", stimulus.get("m_axi_wdata", 0)) or 0) & 0xFFFFFFFF
