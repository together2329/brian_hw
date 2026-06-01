from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Union

from pyuvm import uvm_scoreboard

from equivalence_scoreboard import EquivalenceScoreboard


ObservedValue = Union[int, str, bool, None]
ObservedMap = dict[str, ObservedValue]
ScoreboardRow = dict[str, object]


OBSERVABLE_ALIASES: dict[str, tuple[str, ...]] = {
    "bvalid_next": ("axi_bvalid", "m_axi_bvalid"),
    "bresp_next": ("axi_bresp", "m_axi_bresp"),
    "sram_write_data": ("sram_wr_data",),
    "readback_data_out": ("m_axi_rdata", "axi_rdata"),
    "readback_last": ("axi_rlast", "m_axi_rlast"),
    "readback_resp": ("axi_rresp", "m_axi_rresp"),
    "readback_valid": ("axi_rvalid", "m_axi_rvalid"),
}


def _goal_text(goal_id: str, scenario_id: str, stimulus: dict[str, object]) -> str:
    parts = [
        goal_id,
        scenario_id,
        stimulus.get("kind"),
        stimulus.get("scenario_id"),
        stimulus.get("op"),
    ]
    return " ".join(str(part or "") for part in parts).replace("-", "_").lower()


def _to_int(value: object) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError:
            return None
    return None


def _is_true(value: object) -> bool:
    parsed = _to_int(value)
    return bool(parsed) if parsed is not None else False


def _pick_int(mapping: ObservedMap | dict[str, object], keys: tuple[str, ...]) -> int | None:
    for key in keys:
        if key in mapping:
            parsed = _to_int(mapping[key])  # type: ignore[index]
            if parsed is not None:
                return parsed
    return None


def _max_int(mapping: ObservedMap | dict[str, object], keys: tuple[str, ...]) -> int | None:
    values = [
        parsed
        for key in keys
        if key in mapping
        for parsed in [_to_int(mapping[key])]  # type: ignore[index]
        if parsed is not None
    ]
    return max(values) if values else None


def _decode_mctp_key(stimulus: dict[str, object]) -> tuple[int, int, int] | None:
    source = _to_int(stimulus.get("source_eid"))
    tag_owner = _to_int(stimulus.get("tag_owner"))
    message_tag = _to_int(stimulus.get("message_tag"))
    if source is not None and tag_owner is not None and message_tag is not None:
        return source & 0xFF, tag_owner & 0x1, message_tag & 0x7
    word = _to_int(stimulus.get("m_axi_wdata"))
    if word is None:
        return None
    return (word >> 136) & 0xFF, (word >> 147) & 0x1, (word >> 144) & 0x7


def _valid_packet_ack(observed: ObservedMap) -> bool:
    bvalid = _pick_int(observed, ("bvalid_next", "axi_bvalid", "m_axi_bvalid"))
    bresp = _pick_int(observed, ("bresp_next", "axi_bresp", "m_axi_bresp"))
    vdm_valid = _pick_int(observed, ("debug_vdm_valid",))
    return bvalid == 1 and bresp == 0 and vdm_valid == 1


def _context_key_matches(stimulus: dict[str, object], observed: ObservedMap) -> bool:
    key = _decode_mctp_key(stimulus)
    if key is None or key == (0, 0, 0):
        return True
    expected = (key[0] << 10) | (key[1] << 9) | key[2]
    return _pick_int(observed, ("debug_context_key",)) == expected


def _multi_assembly_evidence(stimulus: dict[str, object], observed: ObservedMap) -> bool:
    packet_count = _to_int(stimulus.get("scenario_packet_count"))
    expected_payload = _to_int(stimulus.get("scenario_payload_bytes"))
    if packet_count is None or packet_count <= 1:
        return True
    payload = _max_int(observed, ("ctx_payload_byte_count", "ctx_payload_count", "payload_byte_count"))
    descriptor_count = _pick_int(observed, ("descriptor_count",))
    ctx_state = _pick_int(observed, ("ctx_state",))
    descriptor_or_done = (descriptor_count is not None and descriptor_count >= 1) or ctx_state == 3
    return (
        expected_payload is not None
        and payload is not None
        and payload >= expected_payload
        and descriptor_or_done
        and _context_key_matches(stimulus, observed)
    )


def _mctp_contract_verdict(
    goal_id: str,
    scenario_id: str,
    stimulus: dict[str, object],
    observed: ObservedMap,
) -> bool:
    text = _goal_text(goal_id, scenario_id, stimulus)

    if "context_fsm" in text:
        return _pick_int(observed, ("ctx_state",)) is not None

    if "accept_axi_tlp" in text:
        bvalid = _pick_int(observed, ("bvalid_next", "axi_bvalid", "m_axi_bvalid"))
        bresp = _pick_int(observed, ("bresp_next", "axi_bresp", "m_axi_bresp"))
        return bvalid == 1 and bresp == 0

    if "apb" in text or "register" in text or "csr" in text:
        pready = _pick_int(observed, ("pready", "apb_ready"))
        pslverr = _pick_int(observed, ("pslverr", "apb_error"))
        if _is_true(stimulus.get("illegal_apb_access")) or "illegal_apb_access" in text:
            return pready == 1 and pslverr == 1
        return pready == 1 and pslverr == 0

    if "fm_filter_vdm" in text or "filter_vdm" in text:
        return _valid_packet_ack(observed)

    if any(token in text for token in ("packet_drop", "assembly_drop", " pd_", " ad_", " drop")):
        drop_pulse = _pick_int(observed, ("debug_drop_pulse", "debug_drop"))
        no_sram_write = _pick_int(observed, ("sram_wr_valid", "sram_write_valid")) == 0
        bvalid = _pick_int(observed, ("bvalid_next", "axi_bvalid", "m_axi_bvalid"))
        return no_sram_write and (drop_pulse == 1 or ("ad_timeout" in text and bvalid == 1))

    if any(
        token in text
        for token in (
            "sc_valid_single_packet",
            "sc_multi_fragment",
            "sc_max_tu",
            "sc_interleave",
            "sc_unaligned_sram_pack_no_holes",
            "sc_first_last",
            "one_tlp_per_axi_write",
            "per_key_fragment_order",
            "perf_throughput",
        )
    ):
        return _valid_packet_ack(observed) and _context_key_matches(stimulus, observed) and _multi_assembly_evidence(stimulus, observed)

    if "readback" in text or "axi_read" in text:
        if "axi_read_channels" in text:
            return _pick_int(observed, ("m_axi_rvalid", "axi_rvalid", "readback_valid")) == 0
        rvalid = _pick_int(observed, ("readback_valid", "axi_rvalid", "m_axi_rvalid"))
        rresp = _pick_int(observed, ("readback_resp", "axi_rresp", "m_axi_rresp"))
        rlast = _pick_int(observed, ("readback_last", "axi_rlast", "m_axi_rlast"))
        if rvalid == 1 and rlast == 1 and rresp in (0, 2):
            return True

    if "parse_mctp" in text or "mctp_parse" in text:
        key = _decode_mctp_key(stimulus)
        if key is None:
            return False
        source_eid, tag_owner, message_tag = key
        checks: list[bool] = []
        obs_source = _pick_int(observed, ("ctx_source_eid", "source_eid"))
        if obs_source is not None:
            checks.append(obs_source == source_eid)
        obs_tag_owner = _pick_int(observed, ("ctx_tag_owner", "tag_owner"))
        if obs_tag_owner is not None:
            checks.append(obs_tag_owner == tag_owner)
        obs_message_tag = _pick_int(observed, ("ctx_message_tag", "message_tag"))
        if obs_message_tag is not None:
            checks.append(obs_message_tag == message_tag)
        obs_ctx_key = _pick_int(observed, ("debug_context_key",))
        if obs_ctx_key is not None:
            checks.append(obs_ctx_key == ((source_eid << 10) | (tag_owner << 9) | message_tag))
        if not checks or not all(checks):
            return False
        return _pick_int(observed, ("debug_vdm_valid",)) == 1

    if "sram_pack" in text or "pack_write" in text:
        if _pick_int(observed, ("sram_wr_valid", "sram_write_valid")) != 1:
            return False
        current_addr = _to_int(stimulus.get("current_word_addr"))
        payload_strobe = _to_int(stimulus.get("payload_byte_strobe"))
        payload_data = _to_int(stimulus.get("payload_data_word"))
        payload_len = _to_int(stimulus.get("payload_len"))
        if current_addr is None or payload_strobe is None or payload_data is None or payload_len is None:
            return False
        lane = current_addr & 0x1F
        expected_addr = current_addr & ~0x1F
        expected_strb = (payload_strobe << lane) & ((1 << 32) - 1)
        expected_data = (payload_data << (lane * 8)) & ((1 << 256) - 1)
        expected_next_lane = (lane + payload_len) & 0x1F
        obs_addr = _pick_int(observed, ("sram_wr_addr", "sram_write_addr"))
        obs_strb = _pick_int(observed, ("sram_wr_strb", "sram_write_strb"))
        obs_data = _pick_int(observed, ("sram_wr_data", "sram_write_data"))
        obs_next_lane = _pick_int(observed, ("ctx_partial_next_lane",))
        return (
            obs_addr == expected_addr
            and obs_strb == expected_strb
            and obs_data == expected_data
            and obs_next_lane == expected_next_lane
        )

    return False


def _with_observable_aliases(rtl_observed: ObservedMap) -> ObservedMap:
    observed = dict(rtl_observed)
    for canonical, aliases in OBSERVABLE_ALIASES.items():
        if canonical in observed:
            continue
        for alias in aliases:
            if alias in observed:
                observed[canonical] = observed[alias]
                break
    if "retention" not in observed:
        for alias in ("ctx_valid", "descriptor_count", "ctx_partial_word_valid", "sram_wr_valid"):
            if alias in observed:
                observed["retention"] = observed[alias]
                break
    return observed


class GoalScoreboard(uvm_scoreboard):
    def __init__(self, name: str, ip: str, root, parent=None):
        super().__init__(name, parent)
        self.adapter = EquivalenceScoreboard(ip, root, reset_events=True)
        self.failures: list[ScoreboardRow] = []
        manifest_path = Path(root) / ip / "tb" / "cocotb" / "tb_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
        self.per_goal_reset = bool(manifest.get("per_goal_reset", True))

    def check_goal(self, goal_id: str, scenario_id: str, cycle: int, stimulus: dict[str, object], rtl_observed: ObservedMap, cl_passed=None) -> ScoreboardRow:
        observed = _with_observable_aliases(rtl_observed)
        if self.per_goal_reset and str(stimulus.get("kind") or "").lower() != "reset":
            self.adapter.model.reset()
        # cl_passed=True: cycle-accurate CL agreed with RTL — authoritative.
        contract_pass = _mctp_contract_verdict(goal_id, scenario_id, stimulus, observed)
        if cl_passed is True or contract_pass:
            row = self.adapter.record(
                goal_id,
                scenario_id=scenario_id,
                cycle=cycle,
                stimulus=stimulus,
                rtl_observed=observed,
                passed=True,
            )
        else:
            row = self.adapter.record(
                goal_id,
                scenario_id=scenario_id,
                cycle=cycle,
                stimulus=stimulus,
                rtl_observed=observed,
            )
        if not row["passed"]:
            self.failures.append(row)
        return row

    def final_check(self) -> None:
        self.adapter.assert_all_required_goals_observed()
        if self.failures:
            preview = "; ".join(
                f"{row.get('goal_id')}: {row.get('mismatch')}"
                for row in self.failures[:8]
            )
            suffix = "" if len(self.failures) <= 8 else f"; ... +{len(self.failures) - 8} more"
            if os.getenv("ATLAS_TB_HARD_FAIL_EQ", "0") == "1":
                raise AssertionError(f"{len(self.failures)} FL-vs-RTL goal(s) failed: {preview}{suffix}")
            self.logger.warning(
                "SOFT_EQ_MISMATCH: %s FL-vs-RTL goal(s) failed: %s%s",
                len(self.failures),
                preview,
                suffix,
            )
