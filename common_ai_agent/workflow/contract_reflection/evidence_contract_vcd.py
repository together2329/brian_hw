from __future__ import annotations

from pathlib import Path
from typing import Final

from workflow.contract_reflection.evidence_contract_json import JsonMap, JsonValue, as_map, strings, text


VCD_CONDITION_KINDS: Final[set[str]] = {"vcd_event_order", "vcd_signal_ever_equals", "vcd_stable_while"}
SignalSamples = dict[str, list[tuple[int, int]]]


def vcd_observable_names(condition: JsonMap) -> set[str]:
    kind = text(condition.get("kind"))
    if kind == "vcd_signal_ever_equals":
        signal = text(condition.get("signal"))
        return {signal} if signal else set()
    if kind == "vcd_stable_while":
        names = set(strings(condition.get("stable_signals")))
        when_signal = text(as_map(condition.get("when")).get("signal"))
        while_signal = text(as_map(condition.get("while")).get("signal"))
        if when_signal:
            names.add(when_signal)
        if while_signal:
            names.add(while_signal)
        return names
    if kind == "vcd_event_order":
        first_signal = text(as_map(condition.get("first")).get("signal"))
        second_signal = text(as_map(condition.get("second")).get("signal"))
        return {name for name in (first_signal, second_signal) if name}
    return set()


def check_vcd_condition(ip_dir: Path, condition: JsonMap) -> tuple[bool, str]:
    kind = text(condition.get("kind"))
    if kind == "vcd_signal_ever_equals":
        return _check_ever_equals(ip_dir, condition)
    if kind == "vcd_stable_while":
        return _check_stable_while(ip_dir, condition)
    if kind == "vcd_event_order":
        return _check_event_order(ip_dir, condition)
    return False, f"unknown VCD condition kind {kind}"


def sampled_vcd_signals(ip_dir: Path, artifact: str, signals: set[str]) -> tuple[set[str], list[str]]:
    path, issue = _artifact_path(ip_dir, artifact)
    if path is None:
        return set(), [issue]
    samples = _read_samples(path, signals)
    sampled = {name for name, values in samples.items() if values}
    missing = sorted(name for name, values in samples.items() if not values)
    if missing:
        return sampled, [f"VCD missing samples for {', '.join(missing)}"]
    return sampled, []


def _artifact_path(ip_dir: Path, artifact: str) -> tuple[Path | None, str]:
    raw = Path(artifact)
    if not artifact or raw.is_absolute():
        return None, "VCD artifact path escapes IP root"
    path = (ip_dir / raw).resolve()
    try:
        _ = path.relative_to(ip_dir.resolve())
    except ValueError:
        return None, "VCD artifact path escapes IP root"
    if not path.is_file():
        return None, f"missing VCD artifact {artifact}"
    return path, ""


def _parse_bits(raw: str) -> int | None:
    lowered = raw.lower().replace("_", "")
    if not lowered or any(bit not in {"0", "1"} for bit in lowered):
        return None
    return int(lowered, 2)


def _base_signal(name: str) -> str:
    return name.split("[", 1)[0]


def _read_samples(path: Path, wanted: set[str]) -> SignalSamples:
    symbol_names: dict[str, set[str]] = {}
    samples: SignalSamples = {name: [] for name in wanted}
    time = 0
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("$var "):
            parts = line.split()
            if len(parts) >= 5:
                name = _base_signal(parts[4])
                if name in wanted:
                    symbol_names.setdefault(parts[3], set()).add(name)
            continue
        if line.startswith("#"):
            if line[1:].isdigit():
                time = int(line[1:])
            continue
        if line[0] in {"b", "B"}:
            parts = line.split()
            if len(parts) != 2:
                continue
            value = _parse_bits(parts[0][1:])
            if value is None:
                continue
            for name in symbol_names.get(parts[1], set()):
                samples[name].append((time, value))
            continue
        if line[0] in {"0", "1"}:
            value = _parse_bits(line[0])
            if value is None:
                continue
            for name in symbol_names.get(line[1:].strip(), set()):
                samples[name].append((time, value))
    return samples


def _expected_int(value: JsonValue) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _first_time(samples: SignalSamples, signal: str, expected: int) -> int | None:
    for sample_time, value in samples.get(signal, []):
        if value == expected:
            return sample_time
    return None


def _check_ever_equals(ip_dir: Path, condition: JsonMap) -> tuple[bool, str]:
    signal = text(condition.get("signal"))
    expected = _expected_int(condition.get("value"))
    path, issue = _artifact_path(ip_dir, text(condition.get("artifact")))
    if path is None:
        return False, issue
    if not signal:
        return False, "condition missing signal"
    if expected is None:
        return False, "condition value must be an integer"
    samples = _read_samples(path, {signal})
    if not samples.get(signal):
        return False, f"VCD signal {signal} was not sampled"
    if any(value == expected for _, value in samples[signal]):
        return True, ""
    return False, f"VCD signal {signal} never reached {expected!r}"


def _check_event_order(ip_dir: Path, condition: JsonMap) -> tuple[bool, str]:
    first = as_map(condition.get("first"))
    second = as_map(condition.get("second"))
    first_signal = text(first.get("signal"))
    second_signal = text(second.get("signal"))
    first_value = _expected_int(first.get("value"))
    second_value = _expected_int(second.get("value"))
    path, issue = _artifact_path(ip_dir, text(condition.get("artifact")))
    if path is None:
        return False, issue
    if not first_signal or not second_signal or first_value is None or second_value is None:
        return False, "event-order condition is incomplete"
    samples = _read_samples(path, {first_signal, second_signal})
    missing = sorted(name for name, values in samples.items() if not values)
    if missing:
        return False, f"VCD missing samples for {', '.join(missing)}"
    first_time = _first_time(samples, first_signal, first_value)
    second_time = _first_time(samples, second_signal, second_value)
    if first_time is None:
        return False, f"VCD event {first_signal}={first_value} was not observed"
    if second_time is None:
        return False, f"VCD event {second_signal}={second_value} was not observed"
    relation = text(condition.get("relation")) or "after"
    relations = {"after": second_time > first_time, "same_or_after": second_time >= first_time}
    if relation not in relations:
        return False, f"unknown event-order relation {relation}"
    passed = relations[relation]
    if passed:
        return True, ""
    return False, f"{second_signal}={second_value} at {second_time} is not {relation} {first_signal}={first_value} at {first_time}"


def _check_stable_while(ip_dir: Path, condition: JsonMap) -> tuple[bool, str]:
    when = as_map(condition.get("when"))
    while_rule = as_map(condition.get("while"))
    when_signal = text(when.get("signal"))
    while_signal = text(while_rule.get("signal"))
    when_value = _expected_int(when.get("value"))
    while_value = _expected_int(while_rule.get("value"))
    stable_signals = strings(condition.get("stable_signals"))
    path, issue = _artifact_path(ip_dir, text(condition.get("artifact")))
    if path is None:
        return False, issue
    if not when_signal or not while_signal or when_value is None or while_value is None or not stable_signals:
        return False, "stable-while condition is incomplete"
    wanted = {when_signal, while_signal, *stable_signals}
    samples = _read_samples(path, wanted)
    missing = sorted(name for name, values in samples.items() if not values)
    if missing:
        return False, f"VCD missing samples for {', '.join(missing)}"
    current: dict[str, int] = {}
    active_anchor: dict[str, int] | None = None
    active_seen = False
    for sample_time in sorted({time for values in samples.values() for time, _ in values}):
        for name, values in samples.items():
            for time, value in values:
                if time == sample_time:
                    current[name] = value
        active = current.get(when_signal) == when_value and current.get(while_signal) == while_value
        if not active:
            active_anchor = None
            continue
        active_seen = True
        if active_anchor is None:
            active_anchor = {name: current[name] for name in stable_signals if name in current}
        for name in stable_signals:
            if name not in active_anchor or current.get(name) != active_anchor[name]:
                return False, f"{name} changed while {when_signal}={when_value} and {while_signal}={while_value}"
    if not active_seen:
        return False, f"no active window where {when_signal}={when_value} and {while_signal}={while_value}"
    return True, ""
