"""SSOT markdown + HTML export — extracted from src/atlas_ui.py.

Self-contained rendering module: section order, md/html renderers, dispatch
dict, and the `_ssot_to_markdown` / `_ssot_to_html` entry points. Pure
module-level functions (no closure capture). The custom-block file resolver
needs PROJECT_ROOT — atlas_ui calls `set_project_root(PROJECT_ROOT)` once at
startup so we avoid a top-level circular import.

Phase 1 of refactor/atlas-modular: move-only (no behavior change).
"""
from __future__ import annotations

import html as _html
import json as _json
import os
import re  # original atlas_ui code uses both bare `re` and alias `_re`
import re as _re
from pathlib import Path
from typing import Any, Optional

import yaml as _yaml

# ── PROJECT_ROOT lookup (dynamic, respects test monkeypatch) ──────────
def set_project_root(p: Path) -> None:
    """Kept as a no-op for backward compatibility — atlas_ui calls this at
    startup. The actual project root is read freshly by `_project_root()` so
    `monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)` in tests is
    respected without re-importing this module."""
    return None

def _project_root() -> Path:
    """Read PROJECT_ROOT from atlas_ui on every call. The deferred import
    avoids a top-level circular dep (atlas_ui imports this module) and is
    cheap (Python caches modules in sys.modules). Falls back to cwd if
    atlas_ui isn't importable yet."""
    try:
        from src.atlas_ui import PROJECT_ROOT
        return PROJECT_ROOT
    except Exception:
        return Path(os.getcwd())


_SSOT_EXPORT_SECTION_ORDER: list[tuple[str, str]] = [
    ("top_module", "Top Module"),
    ("sub_modules", "Sub-Modules"),
    ("decomposition", "Decomposition"),
    ("parameters", "Parameters"),
    ("io_list", "I/O List"),
    ("features", "Features"),
    ("dataflow", "Dataflow"),
    ("function_model", "Function Model"),
    ("cycle_model", "Cycle Model"),
    ("clock_reset_domains", "Clock / Reset Domains"),
    ("cdc_requirements", "CDC Requirements"),
    ("rdc_requirements", "RDC Requirements"),
    ("registers", "Registers"),
    ("memory", "Memory"),
    ("interrupts", "Interrupts"),
    ("fsm", "FSM"),
    ("rtl_contract", "RTL Contract"),
    ("timing", "Timing"),
    ("power", "Power"),
    ("security", "Security"),
    ("error_handling", "Error Handling"),
    ("debug_observability", "Debug / Observability"),
    ("integration", "Integration"),
    ("dft", "DFT"),
    ("synthesis", "Synthesis"),
    ("pnr", "PnR"),
    ("coding_rules", "Coding Rules"),
    ("reuse_modules", "Reuse Modules"),
    ("custom", "Custom"),
    ("dir_structure", "Directory Structure"),
    ("filelist", "Filelist"),
    ("test_requirements", "Test Requirements"),
    ("quality_gates", "Quality Gates"),
    ("traceability", "Traceability"),
    ("workflow_todos", "Workflow Todos"),
    ("generation_flow", "Generation Flow"),
]

def _ssot_md_escape_cell(value: Any) -> str:
    """Markdown table cells must not contain raw pipes or newlines."""
    text = "" if value is None else str(value)
    text = text.replace("|", "&#124;")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\n", "<br/>")
    return text

def _ssot_md_scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return str(value)

def _ssot_md_bit_range(value: Any) -> str:
    display, _lsb, _width = _ssot_bit_range_info(value)
    if display:
        return display
    if value in (None, "", [], {}):
        return ""
    return _ssot_md_scalar(value).strip()

def _ssot_bit_range_info(value: Any) -> tuple[str, int | None, int | None]:
    """Normalize an SSOT bit spec into (display, lsb, width).

    SSOT register fields use hardware convention for ranges: `msb:lsb`.
    This helper accepts the common authoring forms (`[msb, lsb]`,
    `[lsb, msb]`, `msb:lsb`, `lsb, msb`) and renders them consistently so
    datasheets do not show ambiguous text like `39, 73`.
    """
    if value is None:
        return "", None, None

    def _range_from_ints(a: int, b: int) -> tuple[str, int, int]:
        msb, lsb = max(a, b), min(a, b)
        display = str(msb) if msb == lsb else f"{msb}:{lsb}"
        return display, lsb, (msb - lsb + 1)

    if isinstance(value, (list, tuple)) and len(value) == 2:
        try:
            return _range_from_ints(int(value[0]), int(value[1]))
        except (TypeError, ValueError):
            pass

    text = _ssot_md_scalar(value).strip()
    if not text:
        return "", None, None
    m = re.match(r"^\[?\s*(\d+)\s*(?:,|:|-|\.\.|\s+)\s*(\d+)\s*\]?$", text)
    if m:
        return _range_from_ints(int(m.group(1)), int(m.group(2)))
    m = re.match(r"^\[?\s*(\d+)\s*\]?$", text)
    if m:
        bit = int(m.group(1))
        return str(bit), bit, 1
    return "", None, None

def _ssot_md_is_short_scalar(value: Any) -> bool:
    if value is None or isinstance(value, bool) or isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        return len(value) <= 80 and "\n" not in value
    return False

def _ssot_md_yaml_block(value: Any) -> str:
    import yaml as _yaml  # type: ignore

    try:
        dumped = _yaml.safe_dump(value, allow_unicode=True, sort_keys=False).rstrip()
    except Exception as exc:
        dumped = f"(unable to render: {exc})"
    return "```yaml\n" + dumped + "\n```"

def _ssot_md_dict_table(rows: list, columns: list) -> str:
    """Render list[dict] as a markdown table with the given columns."""
    if not rows:
        return ""
    header = "| " + " | ".join(label for _, label in columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    lines = [header, sep]
    for row in rows:
        if not isinstance(row, dict):
            cells = [_ssot_md_escape_cell(row)] + [""] * (len(columns) - 1)
        else:
            cells = []
            for key, _label in columns:
                raw = row.get(key)
                if isinstance(raw, (list, dict)):
                    import yaml as _yaml  # type: ignore

                    cells.append(_ssot_md_escape_cell(
                        _yaml.safe_dump(raw, allow_unicode=True, sort_keys=False).strip()
                    ))
                else:
                    cells.append(_ssot_md_escape_cell(_ssot_md_scalar(raw)))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)

def _ssot_md_auto_table(rows: list) -> str:
    """Render list-of-dicts using all observed keys as columns."""
    if not rows or not all(isinstance(r, dict) for r in rows):
        return ""
    keys: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                keys.append(str(key))
    columns = [(k, k.replace("_", " ").title()) for k in keys]
    return _ssot_md_dict_table(rows, columns)

def _ssot_md_definition_list(data: dict) -> str:
    """Dict → markdown bulleted definition list with paragraph fallback."""
    if not isinstance(data, dict) or not data:
        return ""
    lines: list[str] = []
    paragraphs: list[str] = []
    for key, value in data.items():
        label = str(key).replace("_", " ")
        if _ssot_md_is_short_scalar(value):
            lines.append(f"- **{label}:** {_ssot_md_scalar(value)}")
        elif isinstance(value, str):
            paragraphs.append(f"**{label}:**\n\n{value}")
        elif isinstance(value, list) and value and all(isinstance(v, dict) for v in value):
            table = _ssot_md_auto_table(value)
            if table:
                paragraphs.append(f"**{label}:**\n\n{table}")
            else:
                paragraphs.append(f"**{label}:**\n\n" + _ssot_md_yaml_block(value))
        elif isinstance(value, list) and value and all(_ssot_md_is_short_scalar(v) for v in value):
            bullets = "\n".join(f"  - {_ssot_md_scalar(v)}" for v in value)
            lines.append(f"- **{label}:**\n{bullets}")
        elif isinstance(value, dict):
            inner = _ssot_md_definition_list(value)
            if inner:
                paragraphs.append(f"**{label}:**\n\n{inner}")
            else:
                paragraphs.append(f"**{label}:**\n\n" + _ssot_md_yaml_block(value))
        else:
            paragraphs.append(f"**{label}:**\n\n" + _ssot_md_yaml_block(value))
    out = "\n".join(lines)
    if paragraphs:
        if out:
            out += "\n\n"
        out += "\n\n".join(paragraphs)
    return out

def _ssot_md_section_top_module(data: Any) -> str:
    if not isinstance(data, dict):
        return _ssot_md_yaml_block(data)
    desc = data.get("description")
    rest = {k: v for k, v in data.items() if k != "description"}
    out = _ssot_md_definition_list(rest)
    if desc:
        out = (out + "\n\n" if out else "") + f"_{desc}_"
    return out

def _ssot_md_section_sub_modules(data: Any) -> str:
    if isinstance(data, list) and all(isinstance(r, dict) for r in data):
        cols = [
            ("name", "Name"),
            ("file", "File"),
            ("ownership", "Ownership"),
            ("description", "Description"),
        ]
        return _ssot_md_dict_table(data, cols)
    return _ssot_md_yaml_block(data)

def _ssot_md_section_parameters(data: Any) -> str:
    if isinstance(data, list) and all(isinstance(r, dict) for r in data):
        cols = [
            ("name", "Name"),
            ("default", "Default"),
            ("type", "Type"),
            ("description", "Description"),
        ]
        return _ssot_md_dict_table(data, cols)
    return _ssot_md_yaml_block(data)

def _ssot_md_section_io_list(data: Any) -> str:
    if not isinstance(data, dict):
        return _ssot_md_yaml_block(data)
    parts: list[str] = []
    cd = data.get("clock_domains")
    if cd:
        parts.append("### Clock Domains")
        parts.append(_ssot_md_auto_table(cd) if isinstance(cd, list) else _ssot_md_yaml_block(cd))
    rst = data.get("resets")
    if rst:
        parts.append("### Resets")
        parts.append(_ssot_md_auto_table(rst) if isinstance(rst, list) else _ssot_md_yaml_block(rst))
    ifs = data.get("interfaces")
    if isinstance(ifs, list):
        parts.append("### Interfaces")
        for iface in ifs:
            if not isinstance(iface, dict):
                parts.append(_ssot_md_yaml_block(iface))
                continue
            name = iface.get("name") or "(unnamed)"
            parts.append(f"#### {name}")
            meta = {k: v for k, v in iface.items() if k != "ports"}
            inner = _ssot_md_definition_list(meta)
            if inner:
                parts.append(inner)
            ports = iface.get("ports")
            if isinstance(ports, list) and ports:
                cols = [
                    ("name", "Name"),
                    ("width", "Width"),
                    ("direction", "Direction"),
                    ("description", "Description"),
                ]
                parts.append(_ssot_md_dict_table(ports, cols))
    leftover = {k: v for k, v in data.items()
                if k not in ("clock_domains", "resets", "interfaces")}
    if leftover:
        parts.append(_ssot_md_definition_list(leftover))
    return "\n\n".join(p for p in parts if p)

def _ssot_md_section_features(data: Any) -> str:
    if not isinstance(data, list):
        return _ssot_md_yaml_block(data)
    parts: list[str] = []
    for feat in data:
        if not isinstance(feat, dict):
            parts.append(_ssot_md_yaml_block(feat))
            continue
        name = feat.get("name") or "(unnamed feature)"
        parts.append(f"### {name}")
        rest = {k: v for k, v in feat.items() if k != "name"}
        inner = _ssot_md_definition_list(rest)
        if inner:
            parts.append(inner)
    return "\n\n".join(parts)

def _ssot_md_section_registers(data: Any) -> str:
    if not isinstance(data, dict):
        return _ssot_md_yaml_block(data)
    parts: list[str] = []
    cfg = data.get("config")
    if isinstance(cfg, dict) and cfg:
        parts.append("### Config")
        parts.append(_ssot_md_definition_list(cfg))
    reg_list = data.get("register_list")
    if isinstance(reg_list, list) and reg_list:
        parts.append("### Register List")
        cols = [
            ("name", "Name"),
            ("offset", "Offset"),
            ("access", "Access"),
            ("reset", "Reset"),
            ("description", "Description"),
        ]
        parts.append(_ssot_md_dict_table(reg_list, cols))
        for reg in reg_list:
            if not isinstance(reg, dict):
                continue
            fields = reg.get("fields")
            if isinstance(fields, list) and fields:
                parts.append(f"#### {reg.get('name') or '(unnamed reg)'} — fields")
                parts.append(_ssot_md_auto_table(fields))
    leftover = {k: v for k, v in data.items() if k not in ("config", "register_list")}
    if leftover:
        parts.append(_ssot_md_definition_list(leftover))
    return "\n\n".join(p for p in parts if p)

def _ssot_md_section_raw_yaml(data: Any) -> str:
    """Render complex behavioral sections as source, not fragile diagrams."""

    return _ssot_md_yaml_block(data)

def _ssot_md_section_generic(data: Any) -> str:
    """Fallback renderer for arbitrary nested structures."""
    if data is None:
        return ""
    if isinstance(data, dict):
        inner = _ssot_md_definition_list(data)
        return inner or _ssot_md_yaml_block(data)
    if isinstance(data, list):
        if not data:
            return ""
        if all(isinstance(r, dict) for r in data):
            table = _ssot_md_auto_table(data)
            if table:
                return table
        if all(_ssot_md_is_short_scalar(r) for r in data):
            return "\n".join(f"- {_ssot_md_scalar(r)}" for r in data)
        return _ssot_md_yaml_block(data)
    if _ssot_md_is_short_scalar(data):
        return _ssot_md_scalar(data)
    return _ssot_md_yaml_block(data)

_SSOT_MD_SECTION_RENDERERS: dict = {
    "top_module": _ssot_md_section_top_module,
    "sub_modules": _ssot_md_section_sub_modules,
    "parameters": _ssot_md_section_parameters,
    "io_list": _ssot_md_section_io_list,
    "features": _ssot_md_section_features,
    "function_model": _ssot_md_section_raw_yaml,
    "cycle_model": _ssot_md_section_raw_yaml,
    "registers": _ssot_md_section_registers,
    "fsm": _ssot_md_section_raw_yaml,
    "timing": _ssot_md_section_raw_yaml,
}

def _ssot_section_is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, (list, dict, str)) and not value:
        return True
    return False






def _ssot_fsm_machines(value: Any) -> list[dict]:
    machines: list[dict] = []
    if isinstance(value, dict):
        raw = value.get("machines") or value.get("fsm_list") or value.get("list")
        if isinstance(raw, list):
            machines = [item for item in raw if isinstance(item, dict)]
        else:
            for key, item in value.items():
                if isinstance(item, dict) and (item.get("states") or item.get("transitions")):
                    machine = dict(item)
                    machine.setdefault("name", key)
                    machines.append(machine)
    elif isinstance(value, list):
        machines = [item for item in value if isinstance(item, dict)]
    return machines

def _ssot_mermaid_state_id(value: Any) -> str:
    """Map an arbitrary state name to a mermaid-safe identifier.

    Mermaid state ids must be simple tokens — keep alnum/underscore,
    replace everything else with underscore, and prefix a leading
    digit so the token never starts with a number.
    """
    import re as _re

    raw = "" if value is None else str(value)
    token = _re.sub(r"[^0-9A-Za-z_]", "_", raw).strip("_")
    if not token:
        token = "s"
    if token[0].isdigit():
        token = f"s_{token}"
    return token

def _ssot_mermaid_label(value: Any) -> str:
    """Sanitize an edge label so it can't break mermaid syntax."""
    import re as _re

    raw = "" if value is None else str(value)
    raw = raw.replace("-->", "to").replace('"', "'")
    raw = _re.sub(r"[\r\n]+", " ", raw)
    raw = raw.replace(":", " -").replace(";", ",")
    return _re.sub(r"\s+", " ", raw).strip()





def _ssot_pick(item: dict, *keys: str) -> Any:
    """First present value among `keys` (treats 0/False as present; skips empty)."""
    for key in keys:
        val = item.get(key)
        if val is None or val == "" or val == [] or val == {}:
            continue
        return val
    return None








def _ssot_field_bit_info(field: dict) -> tuple[str, int | None, int | None]:
    """Return (display, lsb, width) for a register field.

    `display` is `msb:lsb` for a range, a single number for 1-bit fields,
    or "". `lsb` is used for msb-first sorting; `width` is shown in docs
    when known.
    """
    # Explicit range string / list (bits | bit_range | range).
    for key in ("bits", "bit_range", "range"):
        raw = field.get(key)
        if raw in (None, "", [], {}):
            continue
        disp, lsb, width = _ssot_bit_range_info(raw)
        return (disp if disp else _ssot_md_scalar(raw), lsb, width)
    # msb / lsb pair.
    msb_v, lsb_v = field.get("msb"), field.get("lsb")
    if msb_v is not None and lsb_v is not None:
        try:
            msb, lsb = int(msb_v), int(lsb_v)
            disp, low, width = _ssot_bit_range_info([msb, lsb])
            return disp, low, width
        except (TypeError, ValueError):
            pass
    # lsb + width (msb = lsb + width - 1).
    if lsb_v is not None and field.get("width") is not None:
        try:
            lsb = int(lsb_v)
            width = int(field.get("width"))
            msb = lsb + width - 1
            disp = str(msb) if msb == lsb else f"{msb}:{lsb}"
            return disp, lsb, width
        except (TypeError, ValueError):
            pass
    # Single bit position.
    bit_v = field.get("bit")
    if bit_v is not None:
        try:
            b = int(bit_v)
            return str(b), b, 1
        except (TypeError, ValueError):
            return _ssot_md_scalar(bit_v), None, None
    return "", None, None








def _ssot_to_markdown(data: dict, ip: str) -> str:
    from datetime import datetime, timezone

    top = data.get("top_module") if isinstance(data, dict) else None
    version = ""
    if isinstance(top, dict):
        version = str(top.get("version") or "").strip()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines: list[str] = []
    lines.append(f"# {ip}")
    lines.append("")
    lines.append(f"> SSOT specification — generated from `{ip}/yaml/{ip}.ssot.yaml`")
    lines.append(f"> Export timestamp: {ts}")
    lines.append(f"> Source SSOT version: {version or 'unspecified'}")
    lines.append("")

    if not isinstance(data, dict):
        lines.append(_ssot_md_yaml_block(data))
        return "\n".join(lines)

    for key, label in _SSOT_EXPORT_SECTION_ORDER:
        if key not in data:
            continue
        value = data.get(key)
        if _ssot_section_is_empty(value):
            continue
        lines.append(f"## {label}")
        lines.append("")
        renderer = _SSOT_MD_SECTION_RENDERERS.get(key, _ssot_md_section_generic)
        try:
            body = renderer(value)
        except Exception as exc:
            body = f"_(render error: {exc})_\n\n" + _ssot_md_yaml_block(value)
        if body:
            lines.append(body)
        lines.append("")

    known = {key for key, _ in _SSOT_EXPORT_SECTION_ORDER}
    extras = [k for k in data.keys() if k not in known]
    if extras:
        lines.append("## Other Sections")
        lines.append("")
        for key in extras:
            value = data.get(key)
            if _ssot_section_is_empty(value):
                continue
            lines.append(f"### {key}")
            lines.append("")
            lines.append(_ssot_md_section_generic(value))
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"




def _ssot_resolve_custom_file(rel: str) -> "Path | None":
    """Resolve an IP-relative custom-block file path safely under _project_root().

    Rejects paths that escape _project_root() (no `..` traversal) and missing files.
    """
    from pathlib import Path
    rel = str(rel or "").strip()
    if not rel:
        return None
    try:
        p = (_project_root() / rel).resolve()
        p.relative_to(_project_root().resolve())
    except (ValueError, OSError):
        return None
    return p if p.is_file() else None





# Phase 24: HTML rendering helpers extracted to atlas_ssot_export_html.py.
# Re-export so existing `from src.atlas_ssot_export import _ssot_to_html` etc work.
from src.atlas_ssot_export_html import (
    _ssot_html_escape,
    _ssot_html_item_name,
    _ssot_html_submodules,
    _ssot_html_interfaces,
    _ssot_html_block_diagram,
    _ssot_html_fsm_mermaid,
    _ssot_html_fsm_section,
    _ssot_html_signal_values,
    _ssot_html_timing_section,
    _ssot_html_is_scalar,
    _ssot_html_scalar,
    _ssot_html_yaml_pre,
    _ssot_html_value_block,
    _ssot_html_rule_cards,
    _ssot_html_function_model,
    _ssot_html_cycle_model,
    _ssot_html_field_bits,
    _ssot_html_register_field_table,
    _ssot_html_register_block,
    _ssot_html_hex,
    _ssot_html_registers,
    _ssot_html_insert_after_section,
    _ssot_html_design_views,
    _ssot_html_insert_after_top_module,
    _ssot_html_normalize_mermaid_fences,
    _ssot_html_mermaid_runtime,
    _ssot_html_render_custom_block,
    _ssot_html_custom_blocks_for,
    _ssot_to_html,
)
