from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Literal, Optional, Union

from typing_extensions import TypeAlias, TypeGuard

JsonScalar: TypeAlias = Union[str, int, float, bool, None]
JsonValue: TypeAlias = Union[JsonScalar, list["JsonValue"], dict[str, "JsonValue"]]
JsonMap: TypeAlias = Mapping[str, JsonValue]
KpiDot: TypeAlias = Literal["pass", "warn", "fail", "idle"]
_JSON_LOADS: Callable[[str], object] = json.loads


def _is_json_map(value: object) -> TypeGuard[JsonMap]:
    return isinstance(value, dict)


def _read_report(ip_dir: Path) -> Optional[JsonMap]:
    path = ip_dir / "lint" / "dut_lint.json"
    try:
        data = _JSON_LOADS(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return data if _is_json_map(data) else None


def _text_field(doc: JsonMap, key: str) -> str:
    value = doc.get(key)
    return value if isinstance(value, str) else ""


def _bool_field(doc: JsonMap, key: str) -> Optional[bool]:
    value = doc.get(key)
    return value if isinstance(value, bool) else None


def _int_field(doc: JsonMap, *keys: str, default: int = 0) -> int:
    for key in keys:
        value = doc.get(key)
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            try:
                return int(value.strip())
            except ValueError:
                continue
    return default


def _tool_results(report: JsonMap) -> list[JsonMap]:
    raw = report.get("tool_results")
    if not isinstance(raw, list):
        return []
    return [item for item in raw if _is_json_map(item)]


def _result_dot(result: JsonMap) -> KpiDot:
    if _bool_field(result, "available") is False:
        return "fail"
    passed = _bool_field(result, "passed")
    if passed is True:
        return "pass"
    if passed is False:
        return "fail"
    if (
        _int_field(result, "returncode", default=1) == 0
        and _int_field(result, "errors") == 0
        and _int_field(result, "warnings") == 0
    ):
        return "pass"
    return "fail"


def _diagnostics_dot(items: list[JsonValue]) -> KpiDot:
    saw_warning = False
    for item in items:
        if not _is_json_map(item):
            continue
        severity = _text_field(item, "severity").strip().lower()
        if severity in {"error", "fatal"}:
            return "fail"
        if severity in {"warning", "warn"}:
            saw_warning = True
    return "warn" if saw_warning else "pass"


def _legacy_tool_dot(report: JsonMap, tool_name: str) -> Optional[KpiDot]:
    value = report.get(tool_name)
    if isinstance(value, bool):
        return "pass" if value else "fail"
    if _is_json_map(value):
        return _result_dot(value)
    if isinstance(value, list):
        return _diagnostics_dot(value)
    return None


def _tool_dot(report: JsonMap, tool_name: str) -> KpiDot:
    for result in _tool_results(report):
        if _text_field(result, "tool").strip().lower() != tool_name:
            continue
        return _result_dot(result)

    legacy_dot = _legacy_tool_dot(report, tool_name)
    if legacy_dot is not None:
        return legacy_dot
    tool_text = f"{_text_field(report, 'tool')} {_text_field(report, 'command')}".lower()
    if tool_name not in tool_text:
        return "idle"
    return "pass" if _bool_field(report, "passed") is True else "fail"


def lint_kpi_dots(ip_dir: Path) -> list[KpiDot]:
    report = _read_report(ip_dir)
    if report is None:
        return ["idle"] * 5
    errors = _int_field(report, "errors", "error_count", default=1)
    warnings = _int_field(report, "warnings", "warning_count")
    waivers = _int_field(report, "waived_warnings", "waivers", "waiver_count", "warning_budget")
    policy_issues = (
        _int_field(report, "suppression_violation_count", "suppression_violations")
        + _int_field(report, "style_violation_count", "style_violations")
    )
    return [
        _tool_dot(report, "pyslang"),
        _tool_dot(report, "verilator"),
        "pass" if errors == 0 else "fail",
        "pass" if warnings <= waivers else "warn",
        "pass" if policy_issues == 0 else "fail",
    ]
