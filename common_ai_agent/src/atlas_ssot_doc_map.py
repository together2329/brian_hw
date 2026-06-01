from __future__ import annotations

from html import escape as _html_escape
from typing import Any

import yaml

JsonValue = Any
JsonMap = dict[str, Any]
PathToken = Any

SSOT_DOC_SECTION_LABELS: dict[str, str] = {
    "top_module": "Top Module",
    "sub_modules": "Sub-Modules",
    "decomposition": "Decomposition",
    "parameters": "Parameters",
    "io_list": "I/O List",
    "features": "Features",
    "dataflow": "Dataflow",
    "function_model": "Function Model",
    "cycle_model": "Cycle Model",
    "clock_reset_domains": "Clock / Reset Domains",
    "cdc_requirements": "CDC Requirements",
    "rdc_requirements": "RDC Requirements",
    "registers": "Registers",
    "memory": "Memory",
    "interrupts": "Interrupts",
    "fsm": "FSM",
    "rtl_contract": "RTL Contract",
    "timing": "Timing",
    "power": "Power",
    "security": "Security",
    "error_handling": "Error Handling",
    "debug_observability": "Debug / Observability",
    "integration": "Integration",
    "dft": "DFT",
    "synthesis": "Synthesis",
    "pnr": "PnR",
    "coding_rules": "Coding Rules",
    "reuse_modules": "Reuse Modules",
    "custom": "Custom",
    "dir_structure": "Directory Structure",
    "filelist": "Filelist",
    "test_requirements": "Test Requirements",
    "quality_gates": "Quality Gates",
    "traceability": "Traceability",
    "workflow_todos": "Workflow Todos",
    "generation_flow": "Generation Flow",
}


def ssot_doc_data_attrs(section: str, path: str, label: str, kind: str) -> str:
    attrs = {
        "data-ssot-section": section,
        "data-ssot-path": path,
        "data-ssot-label": label,
        "data-ssot-kind": kind,
    }
    return " ".join(f'{key}="{_html_escape(str(value), quote=True)}"' for key, value in attrs.items())


def ssot_doc_annotate_headings(html_body: str) -> str:
    import re

    result = html_body
    for section, label in SSOT_DOC_SECTION_LABELS.items():
        attrs = ssot_doc_data_attrs(section, section, label, "section")
        result = re.sub(
            rf"<h2\b([^>]*)>\s*{re.escape(label)}\s*</h2>",
            lambda m, label=label, attrs=attrs: f"<h2{m.group(1)} {attrs}>{label}</h2>",
            result,
            count=1,
            flags=re.IGNORECASE,
        )
    return result


def lookup_ssot_doc_source(
    doc: JsonMap,
    *,
    path: str,
    tokens: list[PathToken],
    ip: str,
    ssot_path: str,
) -> JsonMap:
    value = _value_at_path(doc, tokens)
    section = str(tokens[0]) if tokens and isinstance(tokens[0], str) else "custom"
    label, kind = _label_and_kind(doc, tokens, section)
    return {
        "ok": True,
        "ip": ip,
        "ssot_path": ssot_path,
        "section": section,
        "path": path,
        "label": label,
        "kind": kind,
        "value": value,
        "yaml": _yaml_snippet(value),
        "feedback": _feedback_for_path(doc, path),
    }


def _value_at_path(root: JsonValue, tokens: list[PathToken]) -> JsonValue:
    cur = root
    for token in tokens:
        if isinstance(token, int):
            if not isinstance(cur, list) or token < 0 or token >= len(cur):
                raise KeyError("path not found")
            cur = cur[token]
            continue
        if not isinstance(cur, dict) or token not in cur:
            raise KeyError("path not found")
        cur = cur[token]
    return cur


def _label_and_kind(doc: JsonMap, tokens: list[PathToken], section: str) -> tuple[str, str]:
    if not tokens:
        return "Custom", "section"
    if len(tokens) == 1:
        return SSOT_DOC_SECTION_LABELS.get(section, section), "section"
    if section == "registers":
        return _register_label_and_kind(doc, tokens)
    if section == "sub_modules" and len(tokens) >= 2 and isinstance(tokens[1], int):
        item = _safe_get(doc, ["sub_modules", tokens[1]])
        name = _item_name(item, f"module_{tokens[1] + 1}")
        return ".".join([name, *map(str, tokens[2:])]) if len(tokens) > 2 else name, "sub_module"
    if section == "io_list" and len(tokens) >= 3 and tokens[1] == "interfaces" and isinstance(tokens[2], int):
        item = _safe_get(doc, ["io_list", "interfaces", tokens[2]])
        name = _item_name(item, f"interface_{tokens[2] + 1}")
        return ".".join([name, *map(str, tokens[3:])]) if len(tokens) > 3 else name, "interface"
    return ".".join(map(str, tokens)), "value"


def _register_label_and_kind(doc: JsonMap, tokens: list[PathToken]) -> tuple[str, str]:
    if len(tokens) >= 3 and tokens[1] == "register_list" and isinstance(tokens[2], int):
        reg = _safe_get(doc, ["registers", "register_list", tokens[2]])
        reg_name = _item_name(reg, f"register_{tokens[2] + 1}")
        if len(tokens) >= 5 and tokens[3] == "fields" and isinstance(tokens[4], int):
            field = _safe_get(doc, ["registers", "register_list", tokens[2], "fields", tokens[4]])
            field_name = _item_name(field, f"field_{tokens[4] + 1}")
            rest = [str(part) for part in tokens[5:]]
            return ".".join([reg_name, field_name, *rest]) if rest else f"{reg_name}.{field_name}", "register_field"
        rest = [str(part) for part in tokens[3:]]
        return ".".join([reg_name, *rest]) if rest else reg_name, "register"
    return ".".join(map(str, tokens)), "registers"


def _safe_get(root: JsonValue, tokens: list[PathToken]) -> JsonValue:
    try:
        return _value_at_path(root, tokens)
    except KeyError:
        return {}


def _item_name(value: JsonValue, fallback: str) -> str:
    if isinstance(value, dict):
        for key in ("name", "id", "field", "signal", "port"):
            raw = value.get(key)
            if raw not in (None, "", [], {}):
                return str(raw)
    return fallback


def _yaml_snippet(value: JsonValue) -> str:
    if isinstance(value, str):
        return value
    return yaml.safe_dump(value, sort_keys=False, allow_unicode=True, width=120).strip()


def _feedback_for_path(doc: JsonMap, path: str) -> list[JsonMap]:
    custom = doc.get("custom")
    rows = custom.get("atlas_doc_feedback") if isinstance(custom, dict) else []
    if not isinstance(rows, list):
        return []
    out: list[JsonMap] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        row_path = str(row.get("path") or "")
        if row_path == path or row_path.startswith(f"{path}.") or path.startswith(f"{row_path}."):
            out.append(row)
    return out
