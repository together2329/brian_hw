#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Optional, Union


JsonValue = Union[None, bool, int, float, str, list["JsonValue"], dict[str, "JsonValue"]]
JsonMap = dict[str, JsonValue]

CLASS_TOKENS: Final[dict[str, tuple[str, ...]]] = {
    "write": ("accept_axi_tlp", "axi_write", "one_tlp", "write_transaction", "tlp"),
    "single": ("single_packet", "valid_single"),
    "multi_assemble": ("multi_fragment", "multi assemble", "3pkt", "tu64"),
    "readback": ("readback", "axi_read"),
    "drop": ("drop", "_pd_", "_ad_", "malformed", "overflow", "timeout"),
    "memory_pack": ("sram", "memory", "pack", "payload"),
    "register": ("register", "apb", "csr", "control_status"),
    "boundary": ("max", "unaligned", "boundary", "trim", "4096", "64", "first_last", "short"),
    "interleave": ("interleave", "concurrent", "multi_key", "two_keys"),
    "protocol": ("protocol", "handshake", "ready_valid", "channels"),
    "fsm": ("fsm", "state"),
    "module": ("module",),
    "coverage": ("coverage",),
}


@dataclass(frozen=True)
class QualityResult:
    status: str
    rows: int
    classes: dict[str, int]
    required_observables: list[str]
    missing_observables: list[str]
    issues: list[str]


def _load_json(path: Path) -> JsonMap:
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"[simulation_quality] FAIL: invalid JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"[simulation_quality] FAIL: {path} root must be an object")
    return value


def _load_rows(path: Path) -> tuple[list[JsonMap], list[str]]:
    if not path.is_file():
        return [], [f"missing {path}"]
    rows: list[JsonMap] = []
    issues: list[str] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            issues.append(f"line {line_no}: invalid JSON: {exc}")
            continue
        if isinstance(value, dict):
            rows.append(value)
        else:
            issues.append(f"line {line_no}: row must be an object")
    return rows, issues


def _resolve_ip_dir(root: Path, ip: str) -> Path:
    raw_ip = Path(ip)
    if raw_ip.is_absolute():
        raise SystemExit(f"[simulation_quality] FAIL: ip path {ip} must stay under --root {root}")
    candidate = (root / raw_ip).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise SystemExit(f"[simulation_quality] FAIL: ip path {ip} must stay under --root {root}") from exc
    return candidate


def _as_map(value: JsonValue) -> JsonMap:
    return value if isinstance(value, dict) else {}


def _as_int(value: JsonValue) -> Optional[int]:
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


def _text(row: JsonMap) -> str:
    parts = [str(row.get("goal_id") or ""), str(row.get("scenario_id") or "")]
    stimulus = _as_map(row.get("stimulus"))
    for key in ("kind", "scenario_id", "op"):
        parts.append(str(stimulus.get(key) or ""))
    return " ".join(parts).replace("-", "_").lower()


def _expected_text(row: JsonMap) -> str:
    parts = [_text(row)]
    fl_expected = _as_map(row.get("fl_expected"))
    for key in ("title", "observables", "pass_criteria"):
        parts.append(str(fl_expected.get(key) or ""))
    return " ".join(parts).replace("-", "_").lower()


def _classes_for(row: JsonMap) -> set[str]:
    text = _text(row)
    return {
        name
        for name, tokens in CLASS_TOKENS.items()
        if any(token in text for token in tokens)
    }


def _required_observables(ip_dir: Path) -> list[str]:
    contract = _load_json(ip_dir / "verify" / "ip_contract.json")
    observability = _as_map(contract.get("observability"))
    raw = observability.get("required_rtl_observed")
    if not isinstance(raw, list):
        return []
    return sorted(str(item) for item in raw if isinstance(item, str) and item.strip())


def _pick_int(observed: JsonMap, *keys: str) -> Optional[int]:
    for key in keys:
        if key in observed:
            parsed = _as_int(observed[key])
            if parsed is not None:
                return parsed
    return None


def _max_int(observed: JsonMap, *keys: str) -> Optional[int]:
    values = [
        parsed
        for key in keys
        if key in observed
        for parsed in [_as_int(observed[key])]
        if parsed is not None
    ]
    return max(values) if values else None


def _contiguous_nonzero(mask: int) -> bool:
    if mask <= 0:
        return False
    normalized = mask >> ((mask & -mask).bit_length() - 1)
    return (normalized & (normalized + 1)) == 0


def _expected_payload_bytes(row: JsonMap) -> Optional[int]:
    stimulus = _as_map(row.get("stimulus"))
    for key in ("scenario_payload_bytes", "payload_bytes"):
        parsed = _as_int(stimulus.get(key))
        if parsed is not None:
            return parsed
    fl_expected = _as_map(row.get("fl_expected"))
    contract = _as_map(fl_expected.get("stimulus_contract"))
    for key in ("scenario_payload_bytes", "payload_bytes"):
        parsed = _as_int(contract.get(key))
        if parsed is not None:
            return parsed
    text = _expected_text(row)
    for pattern in ("payload_count_equals_", "descriptor_byte_count_equals_"):
        if pattern in text:
            tail = text.split(pattern, 1)[1]
            digits = "".join(char for char in tail[:8] if char.isdigit())
            if digits:
                return int(digits)
    if "4096" in text and ("max_tu" in text or "maximum" in text):
        return 4096
    return None


def _semantic_issues(row: JsonMap) -> list[str]:
    text = _text(row)
    observed = _as_map(row.get("rtl_observed"))
    classes = _classes_for(row)
    issues: list[str] = []
    if row.get("passed") is not True:
        issues.append(f"{row.get('scenario_id')}: scoreboard row did not pass")
    if not observed:
        issues.append(f"{row.get('scenario_id')}: missing rtl_observed")
        return issues
    if "drop" in classes and "register" not in classes:
        write_valid = _pick_int(observed, "sram_wr_valid", "sram_write_valid")
        if write_valid not in (None, 0):
            issues.append(f"{row.get('scenario_id')}: drop scenario wrote SRAM")
    if "multi_assemble" in classes:
        payload = _max_int(observed, "ctx_payload_byte_count", "ctx_payload_count", "payload_byte_count")
        if payload is None or payload <= 32:
            issues.append(f"{row.get('scenario_id')}: multi assemble row lacks accumulated payload evidence")
    expected_payload = _expected_payload_bytes(row)
    if expected_payload is not None and expected_payload > 32:
        payload = _max_int(observed, "ctx_payload_byte_count", "ctx_payload_count", "payload_byte_count", "descriptor_bytes")
        if payload is None or payload < expected_payload:
            actual = "missing" if payload is None else str(payload)
            issues.append(f"{row.get('scenario_id')}: payload evidence {actual} below expected {expected_payload}")
    if "memory_pack" in classes and _pick_int(observed, "sram_wr_valid", "sram_write_valid") == 1:
        if _pick_int(observed, "sram_wr_addr", "sram_write_addr") is None:
            issues.append(f"{row.get('scenario_id')}: SRAM write missing address")
        if _pick_int(observed, "sram_wr_data", "sram_write_data") is None:
            issues.append(f"{row.get('scenario_id')}: SRAM write missing data")
        strobe = _pick_int(observed, "sram_wr_strb", "sram_write_strb")
        if strobe is None or not _contiguous_nonzero(strobe):
            issues.append(f"{row.get('scenario_id')}: SRAM write strobe is not contiguous/no-hole")
    if "readback" in classes and "protocol" not in classes:
        if _pick_int(observed, "readback_valid", "m_axi_rvalid", "axi_rvalid") is None:
            issues.append(f"{row.get('scenario_id')}: readback row missing valid observable")
        if "trim" in text and _pick_int(observed, "readback_last", "m_axi_rlast", "axi_rlast") != 1:
            issues.append(f"{row.get('scenario_id')}: readback trim did not assert last")
    if "register" in classes and _pick_int(observed, "pready", "apb_ready") is None:
        issues.append(f"{row.get('scenario_id')}: register/APB row missing ready observable")
    if "interleave" in classes and _pick_int(observed, "debug_context_key", "ctx_message_tag") is None:
        issues.append(f"{row.get('scenario_id')}: interleave row missing context key observable")
    if "interleave" in classes:
        drop = _pick_int(observed, "debug_drop_pulse", "debug_drop")
        error = _pick_int(observed, "ctx_error")
        if drop not in (None, 0) or error not in (None, 0):
            issues.append(f"{row.get('scenario_id')}: valid/interleave scenario asserted drop or error")
    return issues


def _analyze(ip_dir: Path, require_classes: list[str]) -> QualityResult:
    rows, issues = _load_rows(ip_dir / "sim" / "scoreboard_events.jsonl")
    classes = {name: 0 for name in CLASS_TOKENS}
    observed_names: set[str] = set()
    for row in rows:
        observed_names.update(_as_map(row.get("rtl_observed")).keys())
        for class_name in _classes_for(row):
            classes[class_name] += 1
        issues.extend(_semantic_issues(row))
    required_observables = _required_observables(ip_dir)
    missing_observables = sorted(set(required_observables) - observed_names)
    if missing_observables:
        issues.append("missing required observable(s): " + ", ".join(missing_observables))
    for class_name in require_classes:
        if class_name not in CLASS_TOKENS:
            issues.append(f"unknown required class {class_name}")
        elif classes[class_name] <= 0:
            issues.append(f"missing required simulation class {class_name}")
    return QualityResult(
        status="fail" if issues else "pass",
        rows=len(rows),
        classes=classes,
        required_observables=required_observables,
        missing_observables=missing_observables,
        issues=issues,
    )


def _write_report(ip_dir: Path, result: QualityResult) -> None:
    sim_dir = ip_dir / "sim"
    sim_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "type": "simulation_quality",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": result.status,
        "summary": {
            "rows": result.rows,
            "class_count": sum(1 for count in result.classes.values() if count > 0),
            "issues": len(result.issues),
            "missing_required_observables": len(result.missing_observables),
        },
        "classes": result.classes,
        "required_observables": result.required_observables,
        "missing_observables": result.missing_observables,
        "issues": result.issues,
    }
    (sim_dir / "simulation_quality.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Simulation Quality",
        "",
        f"- status: `{result.status}`",
        f"- rows: `{result.rows}`",
        f"- classes hit: `{sum(1 for count in result.classes.values() if count > 0)}`",
        f"- issues: `{len(result.issues)}`",
        "",
        "## Classes",
        "",
    ]
    lines.extend(f"- `{name}`: {count}" for name, count in sorted(result.classes.items()))
    if result.issues:
        lines.extend(["", "## Issues", ""])
        lines.extend(f"- {issue}" for issue in result.issues)
    (sim_dir / "simulation_quality.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ip")
    parser.add_argument("--root", default=".")
    parser.add_argument("--require-class", action="append", default=[])
    args = parser.parse_args()

    root = Path(args.root).resolve()
    ip_dir = _resolve_ip_dir(root, str(args.ip))
    result = _analyze(ip_dir, [str(item) for item in args.require_class])
    _write_report(ip_dir, result)
    print(
        "[simulation_quality] "
        f"status={result.status} rows={result.rows} issues={len(result.issues)} "
        f"classes={sum(1 for count in result.classes.values() if count > 0)}/{len(CLASS_TOKENS)}"
    )
    for issue in result.issues[:12]:
        print(f"[simulation_quality] issue: {issue}")
    return 0 if result.status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
