from __future__ import annotations

from typing import Any


def scenario_contract_value(goal: dict[str, Any], key: str) -> Any:
    contract = goal.get("stimulus_contract")
    if not isinstance(contract, dict):
        return None
    if key in contract:
        return contract[key]
    machine_spec = contract.get("machine_spec")
    if not isinstance(machine_spec, dict):
        return None
    metadata = machine_spec.get("metadata")
    if isinstance(metadata, dict):
        return metadata.get(key)
    return None


def apply_scenario_contract_defaults(goal: dict[str, Any], stimulus: dict[str, Any]) -> None:
    for contract_key, field in (
        ("scenario_source_eid", "source_eid"),
        ("scenario_destination_eid", "destination_eid"),
        ("scenario_tag_owner", "tag_owner"),
        ("scenario_message_tag", "message_tag"),
        ("scenario_packet_seq", "packet_seq"),
        ("scenario_som", "som"),
        ("scenario_eom", "eom"),
        ("scenario_payload_word", "payload_data_word"),
        ("scenario_force_valid_packet", "scenario_force_valid_packet"),
    ):
        value = scenario_contract_value(goal, contract_key)
        if value is not None:
            stimulus[field] = int(value)
    payload_len = scenario_contract_value(goal, "scenario_payload_len")
    if payload_len is None:
        payload_len = scenario_contract_value(goal, "scenario_payload_bytes")
    if payload_len is not None:
        stimulus["payload_len"] = int(payload_len)
        stimulus["payload_byte_count"] = int(payload_len)
    total_payload = scenario_contract_value(goal, "scenario_payload_bytes")
    if total_payload is not None:
        stimulus["scenario_payload_bytes"] = int(total_payload)
    packet_count = scenario_contract_value(goal, "scenario_packet_count")
    if packet_count is not None:
        stimulus["scenario_packet_count"] = int(packet_count)
