from __future__ import annotations

from typing import Any


JsonDoc = dict[str, Any]


class StructuralContractError(ValueError):
    pass


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _non_empty_str(value: Any) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else ""


def _id_from(entry: JsonDoc, keys: tuple[str, ...]) -> str:
    for key in keys:
        value = _non_empty_str(entry.get(key))
        if value:
            return value
    return ""


def _string_refs(value: Any) -> list[str]:
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    if not isinstance(value, list):
        return []
    refs: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            refs.append(item.strip())
        elif isinstance(item, dict):
            name = _id_from(item, ("name", "id", "signal"))
            if name:
                refs.append(name)
    return sorted(dict.fromkeys(refs))


def _width(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value > 0:
        return value
    if isinstance(value, str):
        text = value.strip()
        if text.isdigit() and int(text) > 0:
            return int(text)
        if text.startswith("[") and text.endswith("]") and ":" in text:
            left, right = text.strip("[]").split(":", 1)
            if left.strip().isdigit() and right.strip().isdigit():
                return abs(int(left) - int(right)) + 1
    return None


def _direction(value: Any) -> str:
    text = _non_empty_str(value).lower()
    mapping = {
        "in": "input",
        "input": "input",
        "out": "output",
        "output": "output",
        "inout": "inout",
        "io": "inout",
    }
    return mapping.get(text, "")


def _timing_from(entry: JsonDoc) -> JsonDoc:
    raw = entry.get("timing")
    timing: JsonDoc = dict(raw) if isinstance(raw, dict) else {}
    for source, target in (
        ("timing_kind", "kind"),
        ("clock_domain", "clock_domain"),
        ("sample_edge", "sample_edge"),
        ("sync_to", "sync_to"),
        ("async_to", "async_to"),
        ("produced_on", "produced_on"),
    ):
        value = entry.get(source)
        if value is not None and target not in timing:
            timing[target] = value
    return timing


def _normalize_signal(raw: JsonDoc, issues: list[str], label: str) -> JsonDoc:
    name = _id_from(raw, ("name", "signal"))
    if not name:
        issues.append(f"{label} signal requires name")
        name = "<missing>"
    direction = _direction(raw.get("dir", raw.get("direction")))
    if not direction:
        issues.append(f"{label}.{name} requires dir/direction input|output|inout")
    width = _width(raw.get("width", 1))
    if width is None:
        issues.append(f"{label}.{name} requires positive integer width")
        width = 1
    item = dict(raw)
    item["name"] = name
    item["dir"] = direction
    item["width"] = width
    if "direction" in item:
        item.pop("direction", None)
    timing = _timing_from(raw)
    if timing:
        item["timing"] = timing
    return item


def _normalize_clock_domains(raw: Any, signal_names: set[str], issues: list[str], label: str) -> list[JsonDoc]:
    result: list[JsonDoc] = []
    seen: set[str] = set()
    for entry in _as_list(raw):
        if not isinstance(entry, dict):
            issues.append(f"{label}.clock_domains entries must be objects")
            continue
        domain_id = _id_from(entry, ("id", "name"))
        clock = _id_from(entry, ("clock_signal", "clock", "signal"))
        if not domain_id:
            issues.append(f"{label}.clock_domains entry requires id/name")
            continue
        if domain_id in seen:
            issues.append(f"{label}.clock_domains duplicate id {domain_id}")
        seen.add(domain_id)
        if not clock:
            issues.append(f"{label}.clock_domains.{domain_id} requires clock_signal/clock")
        elif clock not in signal_names:
            issues.append(f"{label}.clock_domains.{domain_id} references unknown signal {clock}")
        item = dict(entry)
        item["id"] = domain_id
        if clock:
            item["clock_signal"] = clock
        result.append(item)
    return result


def _normalize_reset_domains(
    raw: Any,
    signal_names: set[str],
    clock_domains: set[str],
    issues: list[str],
    label: str,
) -> list[JsonDoc]:
    result: list[JsonDoc] = []
    seen: set[str] = set()
    for entry in _as_list(raw):
        if not isinstance(entry, dict):
            issues.append(f"{label}.reset_domains entries must be objects")
            continue
        domain_id = _id_from(entry, ("id", "name"))
        reset = _id_from(entry, ("reset_signal", "reset", "signal"))
        if not domain_id:
            issues.append(f"{label}.reset_domains entry requires id/name")
            continue
        if domain_id in seen:
            issues.append(f"{label}.reset_domains duplicate id {domain_id}")
        seen.add(domain_id)
        if not reset:
            issues.append(f"{label}.reset_domains.{domain_id} requires reset_signal/reset")
        elif reset not in signal_names:
            issues.append(f"{label}.reset_domains.{domain_id} references unknown signal {reset}")
        clock_domain = _non_empty_str(entry.get("clock_domain"))
        if clock_domain and clock_domain not in clock_domains:
            issues.append(f"{label}.reset_domains.{domain_id} references unknown clock_domain {clock_domain}")
        item = dict(entry)
        item["id"] = domain_id
        if reset:
            item["reset_signal"] = reset
        result.append(item)
    return result


def _normalize_interfaces(
    raw: Any,
    signal_names: set[str],
    clock_domains: set[str],
    issues: list[str],
    label: str,
) -> list[JsonDoc]:
    result: list[JsonDoc] = []
    seen: set[str] = set()
    for entry in _as_list(raw):
        if not isinstance(entry, dict):
            issues.append(f"{label}.interfaces entries must be objects")
            continue
        iface_id = _id_from(entry, ("id", "name"))
        if not iface_id:
            issues.append(f"{label}.interfaces entry requires id/name")
            continue
        if iface_id in seen:
            issues.append(f"{label}.interfaces duplicate id {iface_id}")
        seen.add(iface_id)
        signal_refs = _string_refs(entry.get("signals"))
        if not signal_refs and isinstance(entry.get("ports"), list):
            signal_refs = _string_refs(entry.get("ports"))
        if not signal_refs:
            issues.append(f"{label}.interfaces.{iface_id} requires signals[]")
        for signal in signal_refs:
            if signal not in signal_names:
                issues.append(f"{label}.interfaces.{iface_id} references unknown signal {signal}")
        clock_domain = _non_empty_str(entry.get("clock_domain"))
        if clock_domain and clock_domain not in clock_domains:
            issues.append(f"{label}.interfaces.{iface_id} references unknown clock_domain {clock_domain}")
        item = dict(entry)
        item["id"] = iface_id
        item["signals"] = signal_refs
        item.pop("ports", None)
        result.append(item)
    return result


def _validate_signal_timing(signal: JsonDoc, clock_domains: set[str], issues: list[str], label: str) -> None:
    timing = signal.get("timing")
    if not isinstance(timing, dict):
        return
    kind = _non_empty_str(timing.get("kind")).lower()
    if not kind:
        return
    if kind not in {"sync", "async", "clock", "reset", "cross_domain"}:
        issues.append(f"{label}.{signal['name']} timing.kind {kind!r} is unsupported")
        return
    if kind == "sync":
        clock_domain = _non_empty_str(timing.get("clock_domain"))
        if not clock_domain:
            issues.append(f"{label}.{signal['name']} sync timing requires clock_domain")
        elif clock_domain not in clock_domains:
            issues.append(f"{label}.{signal['name']} references unknown clock_domain {clock_domain}")
    if kind == "async":
        sync_to = _non_empty_str(timing.get("sync_to"))
        if not sync_to:
            issues.append(f"{label}.{signal['name']} async timing requires sync_to")
        elif sync_to not in clock_domains:
            issues.append(f"{label}.{signal['name']} references unknown sync_to clock_domain {sync_to}")


def normalize_structural_contracts(
    ip: str,
    raw: Any,
    *,
    known_obligation_ids: set[str] | None = None,
) -> JsonDoc:
    issues: list[str] = []
    if isinstance(raw, dict):
        if raw.get("ip") not in (None, ip):
            issues.append(f"structural_contracts ip mismatch: expected {ip}, got {raw.get('ip')!r}")
        contracts_raw = raw.get("contracts")
    elif isinstance(raw, list):
        contracts_raw = raw
    else:
        contracts_raw = None
    if not isinstance(contracts_raw, list) or not contracts_raw:
        issues.append("structural_contracts requires non-empty contracts[]")
        contracts_raw = []

    contracts: list[JsonDoc] = []
    contract_ids: set[str] = set()
    global_signals: dict[str, tuple[str, int]] = {}
    for entry in contracts_raw:
        if not isinstance(entry, dict):
            issues.append("structural_contracts contracts[] entries must be objects")
            continue
        contract_id = _id_from(entry, ("id", "contract_id", "contract_ref_id"))
        if not contract_id:
            issues.append("structural contract requires id")
            contract_id = "<missing>"
        if contract_id in contract_ids:
            issues.append(f"duplicate structural contract id {contract_id}")
        contract_ids.add(contract_id)
        label = f"structural_contracts.{contract_id}"
        obligation_refs = _string_refs(entry.get("obligations", entry.get("obligation_refs")))
        if not obligation_refs:
            issues.append(f"{label} requires obligations[]")
        if known_obligation_ids is not None:
            for ref in obligation_refs:
                if ref not in known_obligation_ids:
                    issues.append(f"{label} references unknown obligation {ref}")

        signal_entries = _as_list(entry.get("signals"))
        signals = [
            _normalize_signal(signal, issues, label)
            for signal in signal_entries
            if isinstance(signal, dict)
        ]
        if len(signals) != len(signal_entries):
            issues.append(f"{label}.signals entries must be objects")
        if not signals:
            issues.append(f"{label} requires signals[]")
        signal_names = {signal["name"] for signal in signals}
        if len(signal_names) != len(signals):
            issues.append(f"{label}.signals contains duplicate names")

        clock_domains = _normalize_clock_domains(entry.get("clock_domains"), signal_names, issues, label)
        clock_ids = {domain["id"] for domain in clock_domains}
        reset_domains = _normalize_reset_domains(entry.get("reset_domains"), signal_names, clock_ids, issues, label)
        interfaces = _normalize_interfaces(entry.get("interfaces"), signal_names, clock_ids, issues, label)
        for signal in signals:
            sig_key = (signal["dir"], signal["width"])
            existing = global_signals.get(signal["name"])
            if existing is not None and existing != sig_key:
                issues.append(f"structural signal {signal['name']} is declared with conflicting dir/width")
            global_signals[signal["name"]] = sig_key
            _validate_signal_timing(signal, clock_ids, issues, label)

        item = dict(entry)
        item["id"] = contract_id
        item["obligations"] = obligation_refs
        item["signals"] = signals
        item["clock_domains"] = clock_domains
        item["reset_domains"] = reset_domains
        item["interfaces"] = interfaces
        item.pop("contract_id", None)
        item.pop("contract_ref_id", None)
        item.pop("obligation_refs", None)
        contracts.append(item)

    if issues:
        raise StructuralContractError("; ".join(issues))
    return {
        "schema_version": 1,
        "type": "structural_contracts",
        "ip": ip,
        "contracts": sorted(contracts, key=lambda item: str(item["id"])),
    }


def structural_contract_ids(doc: JsonDoc) -> set[str]:
    return {
        str(item["id"])
        for item in _as_list(doc.get("contracts"))
        if isinstance(item, dict) and _non_empty_str(item.get("id"))
    }


def structural_signal_map(doc: JsonDoc) -> dict[str, JsonDoc]:
    signals: dict[str, JsonDoc] = {}
    for contract in _as_list(doc.get("contracts")):
        if not isinstance(contract, dict):
            continue
        for signal in _as_list(contract.get("signals")):
            if isinstance(signal, dict) and _non_empty_str(signal.get("name")):
                signals[str(signal["name"])] = signal
    return signals


def _ssot_port_entries(doc: JsonDoc) -> list[tuple[JsonDoc, JsonDoc]]:
    io_raw = doc.get("io_list")
    io = io_raw if isinstance(io_raw, dict) else {}
    entries: list[tuple[JsonDoc, JsonDoc]] = []
    for port in _as_list(io.get("ports")):
        if isinstance(port, dict):
            entries.append(({}, port))
    for group_key in ("clock_domains", "resets"):
        for group in _as_list(io.get(group_key)):
            if not isinstance(group, dict):
                continue
            for port in _as_list(group.get("ports")):
                if isinstance(port, dict):
                    entries.append((group, port))
    for iface in _as_list(io.get("interfaces")):
        if not isinstance(iface, dict):
            continue
        for port in _as_list(iface.get("ports")):
            if isinstance(port, dict):
                entries.append((iface, port))
    return entries


def ssot_port_map(doc: JsonDoc) -> dict[str, JsonDoc]:
    ports: dict[str, JsonDoc] = {}
    for parent, raw in _ssot_port_entries(doc):
        name = _id_from(raw, ("name", "signal"))
        if not name:
            continue
        item = dict(raw)
        item["name"] = name
        item["dir"] = _direction(raw.get("dir", raw.get("direction")))
        width = _width(raw.get("width", 1))
        item["width"] = width if width is not None else raw.get("width")
        timing = _timing_from(raw)
        inherited_clock = _non_empty_str(parent.get("clock_domain"))
        if inherited_clock and "clock_domain" not in timing:
            timing["clock_domain"] = inherited_clock
        if inherited_clock and "kind" not in timing:
            timing["kind"] = "sync"
        if timing:
            item["timing"] = timing
        ports[name] = item
    return ports


def compare_structural_to_ssot(structural_doc: JsonDoc, ssot_doc: JsonDoc) -> tuple[list[str], JsonDoc]:
    issues: list[str] = []
    structural = structural_signal_map(structural_doc)
    ssot = ssot_port_map(ssot_doc)
    for name, expected in sorted(structural.items()):
        actual = ssot.get(name)
        if actual is None:
            lowered = {key.lower(): key for key in ssot}
            if name.lower() in lowered:
                issues.append(f"io_list port {lowered[name.lower()]!r} differs in case from structural signal {name!r}")
            else:
                issues.append(f"io_list missing structural signal {name}")
            continue
        if actual.get("dir") != expected.get("dir"):
            issues.append(f"io_list.{name} dir {actual.get('dir')!r} != structural {expected.get('dir')!r}")
        if actual.get("width") != expected.get("width"):
            issues.append(f"io_list.{name} width {actual.get('width')!r} != structural {expected.get('width')!r}")
        expected_timing = expected.get("timing") if isinstance(expected.get("timing"), dict) else {}
        actual_timing = actual.get("timing") if isinstance(actual.get("timing"), dict) else {}
        expected_kind = _non_empty_str(expected_timing.get("kind")).lower()
        if expected_kind:
            actual_kind = _non_empty_str(actual_timing.get("kind")).lower()
            if actual_kind != expected_kind:
                issues.append(f"io_list.{name} timing.kind {actual_kind!r} != structural {expected_kind!r}")
        for key in ("clock_domain", "sync_to"):
            expected_value = _non_empty_str(expected_timing.get(key))
            if expected_value and _non_empty_str(actual_timing.get(key)) != expected_value:
                issues.append(
                    f"io_list.{name} timing.{key} {_non_empty_str(actual_timing.get(key))!r} "
                    f"!= structural {expected_value!r}"
                )
    for name in sorted(set(ssot) - set(structural)):
        port = ssot[name]
        if port.get("structural_contract_waiver") or port.get("waiver"):
            continue
        issues.append(f"io_list extra port {name} is not covered by req/structural_contracts.json")
    summary: JsonDoc = {
        "structural_signals": sorted(structural),
        "ssot_ports": sorted(ssot),
        "matched": sorted(set(structural) & set(ssot)),
    }
    return issues, summary
