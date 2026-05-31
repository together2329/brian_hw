#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Final, Mapping, Sequence, Union

JsonScalar = Union[str, int, bool, None]
JsonValue = Union[JsonScalar, Mapping[str, "JsonValue"], Sequence["JsonValue"]]

PACKET_DROPS: Final[tuple[str, ...]] = (
    "PD_DISABLED_DROP_MODE",
    "PD_MALFORMED_TLP",
    "PD_UNSUPPORTED_VDM",
    "PD_BAD_MCTP_HEADER",
    "PD_BAD_PAD_OR_ALIGNMENT",
    "PD_DEST_EID_REJECT",
    "PD_UNEXPECTED_MIDDLE_END",
    "PD_BAD_OR_EXPIRED_TAG",
)

ASSEMBLY_DROPS: Final[tuple[str, ...]] = (
    "AD_DUPLICATE_SOM",
    "AD_SEQUENCE_MISMATCH",
    "AD_MESSAGE_OVERFLOW",
    "AD_SRAM_OVERFLOW",
    "AD_DESCRIPTOR_FULL",
    "AD_TIMEOUT",
)


@dataclass(frozen=True)
class DirectedScenario:
    scenario_id: str
    description: str
    transaction_kind: str
    category: str
    payload_bytes: int
    packet_count: int
    expected_sram_writes: int
    expected_counter: str
    expected_drop_reason: str
    no_sram_write: bool
    no_descriptor_publish: bool
    notes: str

    @property
    def goal_id(self) -> str:
        return f"EQ_SCENARIO_{self.scenario_id}"

    @property
    def coverage_ref(self) -> str:
        return f"{self.scenario_id}_executed"

    def as_goal(self) -> Mapping[str, JsonValue]:
        observables = [
            "sram_wr_valid",
            "sram_write_valid",
            "packet_drop_count",
            "assembly_drop_count",
            "ctx_last_drop_reason",
            "descriptor_count",
            "debug_drop_pulse",
        ]
        return {
            "goal_id": self.goal_id,
            "title": f"Directed scenario {self.scenario_id}",
            "kind": "scenario",
            "scope": {"level": "top"},
            "scenario": self.scenario_id,
            "ssot_refs": ["test_requirements.scenarios", "req/mctp_assembler_scratch_requirements.md"],
            "coverage_refs": [self.coverage_ref],
            "stimulus_contract": {
                "transaction_type": self.transaction_kind,
                "required_fields": [
                    "kind",
                    "scenario_id",
                    "som",
                    "eom",
                    "packet_seq",
                    "source_eid",
                    "destination_eid",
                    "tag_owner",
                    "message_tag",
                    "payload_data_word",
                    "payload_byte_strobe",
                    "packet_drop_reason",
                    "assembly_drop_reason",
                ],
                "scenario_payload_bytes": self.payload_bytes,
                "scenario_packet_count": self.packet_count,
                "expected_drop_reason": self.expected_drop_reason,
                "machine_spec": {
                    "assign": {
                        "payload_data_word": 0xA5A50000 + self.payload_bytes,
                        "payload_byte_strobe": 0 if self.no_sram_write else 0xFFFF_FFFF,
                    }
                },
            },
            "expected_contract": {
                "model_api": "FunctionalModel.apply",
                "observables": observables,
                "state_updates": [
                    "no_sram_write" if self.no_sram_write else "payload_bytes_written",
                    self.expected_counter,
                    self.expected_drop_reason,
                ],
                "error_policy": (
                    f"no_sram_write={int(self.no_sram_write)}; "
                    f"sram_write_count == {self.expected_sram_writes}; "
                    f"payload_bytes_written == {0 if self.no_sram_write else self.payload_bytes}; "
                    f"drop_reason={self.expected_drop_reason}"
                ),
            },
            "pass_criteria": [
                "Scoreboard row uses this EQ_SCENARIO_* goal_id as primary authority",
                "rtl_observed is sampled from DUT signals, not copied from FL",
                f"sram_write_count == {self.expected_sram_writes}",
                f"payload_bytes_written == {0 if self.no_sram_write else self.payload_bytes}",
                f"{self.expected_counter} increments for {self.expected_drop_reason}",
            ],
            "owner_on_fail": {"default": "rtl", "possible": ["rtl", "tb", "fl_model", "ssot", "human"]},
            "blocked": False,
            "blocker": "",
            "unverified": False,
        }


def _valid_scenarios() -> tuple[DirectedScenario, ...]:
    return (
        DirectedScenario("SC_VALID_SINGLE_PACKET", "SOM/EOM in one TLP", "FM_COMPLETE_MESSAGE", "valid", 32, 1, 1, "descriptor_count", "DROP_NONE", False, False, "single complete descriptor"),
        DirectedScenario("SC_MULTI_FRAGMENT_TU64", "64B TU split over two fragments", "FM_ASSEMBLE_FRAGMENT", "valid", 64, 2, 2, "descriptor_count", "DROP_NONE", False, False, "nonfinal TU is exactly 64B"),
        DirectedScenario("SC_MAX_TU_4096_129_BEATS", "4096B TU plus headers in 129 AXI beats", "FM_ACCEPT_AXI_TLP", "valid", 4096, 1, 128, "collected_tlp_count", "DROP_NONE", False, False, "max burst boundary"),
        DirectedScenario("SC_INTERLEAVE_TWO_KEYS", "Two active contexts interleave by EID/tag", "FM_ASSEMBLE_FRAGMENT", "valid", 128, 4, 4, "active_context_count", "DROP_NONE", False, False, "independent Q FSMs"),
        DirectedScenario("SC_UNALIGNED_SRAM_PACK_NO_HOLES", "Final short payload is packed without SRAM holes", "FM_SRAM_PACK_WRITE", "valid", 52, 2, 2, "ctx_partial_next_lane", "DROP_NONE", False, False, "32B SRAM width with compact byte packing"),
        DirectedScenario("SC_FIRST_LAST_TLP_HEADERS", "First and last 16B TLP headers are retained", "FM_COMPLETE_MESSAGE", "valid", 96, 3, 3, "descriptor_count", "DROP_NONE", False, False, "header snapshots visible per Q"),
        DirectedScenario("SC_AXI_READBACK_TRIM", "AXI readback trims the final shorter beat", "FM_AXI_READBACK", "valid", 68, 1, 3, "read_error_count", "DROP_NONE", False, False, "firmware read path uses descriptor length"),
        DirectedScenario("SC_APB_REGS_PER_Q", "APB exposes each Q state and SRAM base", "FM_APB_ACCESS", "valid", 0, 0, 0, "apb_read_data", "DROP_NONE", False, False, "register visibility scenario"),
    )


def _drop_scenario(drop_id: str, index: int, *, assembly: bool) -> DirectedScenario:
    prefix = "assembly" if assembly else "packet"
    kind = "FM_ASSEMBLY_DROP" if assembly else "FM_PACKET_DROP"
    counter = "assembly_drop_count" if assembly else "packet_drop_count"
    return DirectedScenario(
        drop_id,
        f"{prefix} drop {drop_id} increments {counter} without SRAM payload write",
        kind,
        prefix,
        16 + index * 4,
        1,
        0,
        counter,
        drop_id,
        True,
        True,
        "negative scenario: no_sram_write, sram_write_count == 0, payload_bytes_written == 0",
    )


DIRECTED_SCENARIOS: Final[tuple[DirectedScenario, ...]] = (
    *_valid_scenarios(),
    *tuple(_drop_scenario(drop_id, index, assembly=False) for index, drop_id in enumerate(PACKET_DROPS)),
    *tuple(_drop_scenario(drop_id, index, assembly=True) for index, drop_id in enumerate(ASSEMBLY_DROPS)),
)


def scenario_ids() -> tuple[str, ...]:
    return tuple(scenario.scenario_id for scenario in DIRECTED_SCENARIOS)


def scenario_goals() -> list[Mapping[str, JsonValue]]:
    return [scenario.as_goal() for scenario in DIRECTED_SCENARIOS]


def scenario_manifest() -> Mapping[str, JsonValue]:
    return {
        "schema_version": 1,
        "ip": "mctp_assembler_scratch",
        "scenario_count": len(DIRECTED_SCENARIOS),
        "packet_drop_count": len(PACKET_DROPS),
        "assembly_drop_count": len(ASSEMBLY_DROPS),
        "scenarios": [asdict(scenario) for scenario in DIRECTED_SCENARIOS],
    }


if __name__ == "__main__":
    print(json.dumps(scenario_manifest(), indent=2, sort_keys=True))
