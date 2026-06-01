"""SSOT HTML rendering helpers — extracted from src/atlas_ssot_export.py.

Phase 24 of refactor/atlas-modular: split atlas_ssot_export.py
(1,795 lines) into the smaller `markdown + canonical` half and this
HTML-rendering half. Both halves re-export through atlas_ssot_export.py
so existing import paths (`from src.atlas_ssot_export import _ssot_to_html`
etc.) keep working.

Self-contained: imports atlas_ssot_export at function-body level for
the non-HTML helpers (avoids circular import while preserving the
markdown helpers as the source of truth for `_ssot_md_*`).
"""
from __future__ import annotations

from __future__ import annotations
import html as _html
import json as _json
import os
import re  # original atlas_ui code uses both bare `re` and alias `_re`
import re as _re
from pathlib import Path
from typing import Any, Optional
import yaml as _yaml

from src.atlas_ssot_doc_map import ssot_doc_data_attrs

# Helper functions imported lazily (from atlas_ssot_export module-globals)
# to avoid the circular import; resolved at call time.
def _import_ssot_export_helpers():
    """Lazy hydrate non-HTML helpers from atlas_ssot_export."""
    g = globals()
    if g.get("_HELPERS_HYDRATED"): return
    from src import atlas_ssot_export as _se
    for name in (
        "_project_root",
        "_ssot_md_scalar",
        "_ssot_fsm_machines",
        "_ssot_mermaid_state_id",
        "_ssot_mermaid_label",
        "_ssot_pick",
        "_ssot_field_bit_info",
        "_ssot_resolve_custom_file",
    ):
        if hasattr(_se, name): g[name] = getattr(_se, name)
    g["_HELPERS_HYDRATED"] = True

# (no module constants from atlas_ssot_export are referenced by these
# HTML helpers — only the 8 helper functions hydrated above.)

_import_ssot_export_helpers()

def _ssot_html_escape(value: Any) -> str:
    import html as _html

    return _html.escape("" if value is None else str(value), quote=True)

def _ssot_html_item_name(item: Any, fallback: str = "") -> str:
    if isinstance(item, dict):
        for key in ("name", "id", "module", "label", "signal", "path"):
            val = item.get(key)
            if val not in (None, "", [], {}):
                return str(val)
    if item not in (None, "", [], {}):
        return str(item)
    return fallback

def _ssot_html_submodules(data: dict) -> list[dict]:
    raw = data.get("sub_modules")
    if not isinstance(raw, list):
        return []
    modules: list[dict] = []
    for idx, item in enumerate(raw, start=1):
        if isinstance(item, dict):
            modules.append(item)
        else:
            modules.append({"name": str(item), "description": f"sub-module {idx}"})
    return modules

def _ssot_html_interfaces(data: dict) -> list[dict]:
    io_list = data.get("io_list")
    if isinstance(io_list, dict):
        interfaces = io_list.get("interfaces")
        if isinstance(interfaces, list):
            return [item for item in interfaces if isinstance(item, dict)]
        ports = io_list.get("ports")
        if isinstance(ports, list):
            return [{"name": "ports", "type": "port list", "ports": ports}]
    if isinstance(io_list, list):
        return [{"name": "ports", "type": "port list", "ports": io_list}]
    return []


def _ssot_html_fsm_mermaid(machine: dict, reset_state: str, transitions_raw: list) -> str:
    """Build a mermaid stateDiagram-v2 from a machine's transitions.

    Returns "" when there are no usable transitions so the caller can
    fall back to the rail/table-only rendering.
    """
    edges: list[str] = []
    id_map: dict[str, str] = {}

    def state_id(name: Any) -> str:
        label = "" if name is None else str(name)
        ident = _ssot_mermaid_state_id(label)
        if ident not in id_map and label and label != ident:
            id_map[ident] = label
        else:
            id_map.setdefault(ident, label)
        return ident

    for item in transitions_raw:
        if not isinstance(item, dict):
            continue
        src = item.get("from") or item.get("source") or item.get("current") or ""
        dst = item.get("to") or item.get("dest") or item.get("target") or item.get("next") or ""
        if not src or not dst:
            continue
        cond = item.get("condition") or item.get("event") or item.get("trigger") or ""
        src_id = state_id(src)
        dst_id = state_id(dst)
        label = _ssot_mermaid_label(cond)
        if label:
            edges.append(f"    {src_id} --> {dst_id} : {_ssot_html_escape(label)}")
        else:
            edges.append(f"    {src_id} --> {dst_id}")

    if not edges:
        return ""

    lines = ["stateDiagram-v2"]
    # Stable, deterministic alias declarations for ids whose label differs.
    for ident, label in id_map.items():
        if label and label != ident:
            lines.append(f"    {ident} : {_ssot_html_escape(label)}")
    if reset_state:
        lines.append(f"    [*] --> {state_id(reset_state)}")
    lines.extend(edges)
    body = "\n".join(lines)
    return f"<pre class=\"mermaid\">{body}</pre>"

def _ssot_html_fsm_section(data: dict) -> str:
    machines = _ssot_fsm_machines(data.get("fsm"))
    if not machines:
        return (
            "<section class=\"diagram-card\">"
            "<h3>FSM</h3>"
            "<p class=\"doc-empty\">FSM not specified in SSOT.</p>"
            "</section>"
        )

    chunks: list[str] = []
    for idx, machine in enumerate(machines, start=1):
        name = _ssot_html_escape(machine.get("name") or f"fsm_{idx}")
        reset_state = machine.get("reset_state") or machine.get("initial_state") or ""
        states_raw = machine.get("states") if isinstance(machine.get("states"), list) else []
        transitions_raw = machine.get("transitions") if isinstance(machine.get("transitions"), list) else []
        states: list[str] = []
        seen: set[str] = set()
        for item in states_raw:
            state = _ssot_html_item_name(item)
            if state and state not in seen:
                seen.add(state)
                states.append(state)
        for item in transitions_raw:
            if not isinstance(item, dict):
                continue
            for key in ("from", "source", "current", "to", "dest", "target", "next"):
                state = item.get(key)
                if state not in (None, "", [], {}) and str(state) not in seen:
                    seen.add(str(state))
                    states.append(str(state))

        rows: list[str] = []
        for item in transitions_raw:
            if isinstance(item, dict):
                src = item.get("from") or item.get("source") or item.get("current") or ""
                cond = item.get("condition") or item.get("event") or item.get("trigger") or ""
                dst = item.get("to") or item.get("dest") or item.get("target") or item.get("next") or ""
                action = item.get("action") or item.get("output") or item.get("description") or ""
                rows.append(
                    "<tr>"
                    f"<td>{_ssot_html_escape(src)}</td>"
                    f"<td>{_ssot_html_escape(cond)}</td>"
                    f"<td>{_ssot_html_escape(dst)}</td>"
                    f"<td>{_ssot_html_escape(action)}</td>"
                    "</tr>"
                )
        flow_rows = []
        for item in transitions_raw:
            if not isinstance(item, dict):
                continue
            src = item.get("from") or item.get("source") or item.get("current") or ""
            cond = item.get("condition") or item.get("event") or item.get("trigger") or ""
            dst = item.get("to") or item.get("dest") or item.get("target") or item.get("next") or ""
            action = item.get("action") or item.get("output") or item.get("description") or ""
            if not src and not dst:
                continue
            action_html = f"<small>{_ssot_html_escape(action)}</small>" if action else ""
            flow_rows.append(
                "<div class=\"fsm-flow-row\">"
                f"<span class=\"fsm-flow-state{' reset' if src == reset_state else ''}\">{_ssot_html_escape(src)}</span>"
                "<span class=\"fsm-flow-edge\">"
                f"<span>{_ssot_html_escape(cond or 'transition')}</span>"
                "</span>"
                f"<span class=\"fsm-flow-state{' reset' if dst == reset_state else ''}\">{_ssot_html_escape(dst)}</span>"
                f"{action_html}"
                "</div>"
            )
        table = (
            "<table><thead><tr><th>Current</th><th>Condition</th><th>Next</th><th>Action</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>"
            if rows else "<p class=\"doc-empty small\">no transitions declared</p>"
        )
        reset_html = f"<p class=\"reset-note\">reset: {_ssot_html_escape(reset_state)}</p>" if reset_state else ""

        # Native HTML transition map avoids Mermaid's runtime sizing/cropping
        # problems in iframe/export contexts while keeping the full transition
        # table as a precise fallback below.
        diagram_html = (
            "<div class=\"fsm-flow-map\">"
            f"{''.join(flow_rows)}"
            "</div>"
            if flow_rows else
            "<div class=\"fsm-rail\">" + (
                "".join(
                    f"<span class=\"fsm-state{' reset' if state == reset_state else ''}\">{_ssot_html_escape(state)}</span>"
                    + ("<span class=\"fsm-arrow\">&rarr;</span>" if pos < len(states) - 1 else "")
                    for pos, state in enumerate(states[:12])
                )
                or "<span class=\"doc-empty small\">no states declared</span>"
            ) + "</div>"
        )

        chunks.append(
            "<div class=\"fsm-machine\">"
            f"<h4>{name}</h4>"
            f"{reset_html}"
            f"{diagram_html}"
            f"{table}"
            "</div>"
        )
    return "<section class=\"diagram-card\"><h3>FSM</h3>" + "".join(chunks) + "</section>"

def _ssot_html_signal_values(signal: dict) -> list[str]:
    values = signal.get("values")
    if isinstance(values, list):
        return [str(item) for item in values[:48]]
    wave = signal.get("wave") or signal.get("pattern")
    if isinstance(wave, str) and wave:
        return list(wave[:48])
    return []


def _ssot_html_is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))

def _ssot_html_scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)

def _ssot_html_yaml_pre(value: Any) -> str:
    import yaml as _yaml  # type: ignore

    try:
        dumped = _yaml.safe_dump(value, allow_unicode=True, sort_keys=False).strip()
    except Exception:
        dumped = _ssot_html_scalar(value)
    return f"<pre class=\"mini-yaml\">{_ssot_html_escape(dumped)}</pre>"

def _ssot_html_value_block(value: Any, empty: str = "—") -> str:
    """Render arbitrary SSOT values without forcing them into wide table cells."""
    if value is None or value == "" or value == [] or value == {}:
        return f"<span class=\"doc-empty small\">{_ssot_html_escape(empty)}</span>"
    if _ssot_html_is_scalar(value):
        text = _ssot_html_escape(_ssot_html_scalar(value))
        if "\n" in _ssot_html_scalar(value):
            return f"<pre class=\"mini-yaml\">{text}</pre>"
        return text
    if isinstance(value, list):
        if all(_ssot_html_is_scalar(item) for item in value):
            items = "".join(f"<li>{_ssot_html_escape(_ssot_html_scalar(item))}</li>" for item in value)
            return f"<ul class=\"doc-list compact\">{items}</ul>"
        return "<div class=\"doc-stack\">" + "".join(
            f"<div class=\"doc-nested-item\">{_ssot_html_value_block(item)}</div>"
            for item in value
        ) + "</div>"
    if isinstance(value, dict):
        rows = []
        for key, val in value.items():
            if val in (None, "", [], {}):
                continue
            rows.append(
                "<div class=\"kv-row\">"
                f"<dt>{_ssot_html_escape(str(key).replace('_', ' '))}</dt>"
                f"<dd>{_ssot_html_value_block(val)}</dd>"
                "</div>"
            )
        return f"<dl class=\"kv-list\">{''.join(rows)}</dl>" if rows else _ssot_html_yaml_pre(value)
    return _ssot_html_yaml_pre(value)

def _ssot_html_rule_cards(value: Any, kind: str) -> str:
    if value is None or value == "" or value == [] or value == {}:
        return f"<span class=\"doc-empty small\">no {kind.replace('_', ' ')} declared</span>"
    if not isinstance(value, list):
        return _ssot_html_value_block(value)
    cards: list[str] = []
    for idx, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            cards.append(f"<li>{_ssot_html_escape(_ssot_html_scalar(item))}</li>")
            continue
        name = _ssot_pick(item, "name", "id", "signal", "port", "target", "state") or f"{kind}_{idx}"
        port = _ssot_pick(item, "port", "target", "signal", "state", "register")
        expr = _ssot_pick(item, "expr", "expression", "value", "rule", "condition", "action")
        width = _ssot_pick(item, "width", "bits")
        desc = _ssot_pick(item, "description", "notes", "note", "side_effect")
        chips = []
        if port is not None and str(port) != str(name):
            chips.append(f"<span class=\"doc-chip\">{_ssot_html_escape(_ssot_html_scalar(port))}</span>")
        if width is not None:
            chips.append(f"<span class=\"doc-chip\">{_ssot_html_escape(_ssot_html_scalar(width))}b</span>")
        expr_html = (
            f"<div class=\"rule-expr\"><span>expr</span><code>{_ssot_html_escape(_ssot_html_scalar(expr))}</code></div>"
            if expr not in (None, "", [], {}) else ""
        )
        desc_html = (
            f"<p>{_ssot_html_escape(_ssot_html_scalar(desc))}</p>"
            if desc not in (None, "", [], {}) else ""
        )
        leftovers = {
            k: v for k, v in item.items()
            if k not in {
                "name", "id", "signal", "port", "target", "state", "register",
                "expr", "expression", "value", "rule", "condition", "action",
                "width", "bits", "description", "notes", "note", "side_effect",
            }
            and v not in (None, "", [], {})
        }
        extra_html = _ssot_html_value_block(leftovers, "") if leftovers else ""
        cards.append(
            "<div class=\"rule-card\">"
            "<div class=\"rule-head\">"
            f"<strong>{_ssot_html_escape(_ssot_html_scalar(name))}</strong>"
            f"<span>{''.join(chips)}</span>"
            "</div>"
            f"{expr_html}{desc_html}{extra_html}"
            "</div>"
        )
    if cards and all(card.startswith("<li>") for card in cards):
        return f"<ul class=\"doc-list compact\">{''.join(cards)}</ul>"
    return "<div class=\"rule-grid\">" + "".join(cards) + "</div>"



def _ssot_html_field_bits(field: dict) -> tuple[str, int | None]:
    """Compatibility wrapper for callers that only need display + lsb."""
    display, lsb, _width = _ssot_field_bit_info(field)
    return display, lsb

def _ssot_html_register_field_table(reg: dict, reg_index: int) -> str:
    """Bit-field table: Field | Bits | Width | Access | Reset | Description."""
    fields = reg.get("fields")
    if not isinstance(fields, list) or not fields:
        return ""
    parsed: list[tuple[int, int | None, dict, str, int | None]] = []
    for order, field in enumerate(fields):
        if not isinstance(field, dict):
            continue
        bits_disp, lsb, width = _ssot_field_bit_info(field)
        parsed.append((order, lsb, field, bits_disp, width))
    if not parsed:
        return ""
    # Sort by lsb descending (msb first) when positions are known; preserve
    # declaration order for fields whose position is unknown.
    if all(p[1] is not None for p in parsed):
        parsed.sort(key=lambda p: p[1], reverse=True)  # type: ignore[arg-type]
    rows: list[str] = []
    for order, _lsb, field, bits_disp, width in parsed:
        reset = _ssot_pick(field, "reset", "reset_value", "default")
        name = field.get("name") or field.get("id") or f"field_{order + 1}"
        attrs = ssot_doc_data_attrs(
            "registers",
            f"registers.register_list.{reg_index}.fields.{order}",
            str(name),
            "register_field",
        )
        rows.append(
            f"<tr {attrs}>"
            f"<td>{_ssot_html_escape(name)}</td>"
            f"<td>{_ssot_html_escape(bits_disp)}</td>"
            f"<td>{_ssot_html_escape('' if width is None else width)}</td>"
            f"<td>{_ssot_html_escape(field.get('access') or field.get('rw') or '')}</td>"
            f"<td>{_ssot_html_escape('' if reset is None else reset)}</td>"
            f"<td>{_ssot_html_escape(field.get('description') or field.get('desc') or '')}</td>"
            "</tr>"
        )
    return (
        "<table class=\"register-fields\"><thead><tr>"
        "<th>Field</th><th>Bits</th><th>Width</th><th>Access</th><th>Reset</th><th>Description</th>"
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )

def _ssot_html_register_block(reg: dict, idx: int) -> str:
    """Per-register properties table + bit-field table."""
    if not isinstance(reg, dict):
        return ""
    reg_index = max(idx - 1, 0)
    name = reg.get("name") or reg.get("id") or f"register_{idx}"
    prop_keys = [
        (("offset", "address", "addr"), "Offset"),
        (("width", "size"), "Width"),
        (("access", "rw"), "Access"),
        (("reset", "reset_value", "default"), "Reset value"),
    ]
    prop_rows: list[str] = []
    for keys, label in prop_keys:
        val = _ssot_pick(reg, *keys)
        if val is None:
            continue
        if label in ("Offset", "Reset value"):
            val = _ssot_html_hex(val)
        prop_rows.append(
            f"<tr><th>{_ssot_html_escape(label)}</th>"
            f"<td>{_ssot_html_escape(val)}</td></tr>"
        )
    description = reg.get("description") or reg.get("desc") or ""
    desc_html = (
        f"<p class=\"reg-desc\">{_ssot_html_escape(description)}</p>" if description else ""
    )
    prop_html = (
        "<table class=\"register-props\"><tbody>" + "".join(prop_rows) + "</tbody></table>"
        if prop_rows else ""
    )
    field_html = _ssot_html_register_field_table(reg, reg_index)
    attrs = ssot_doc_data_attrs(
        "registers",
        f"registers.register_list.{reg_index}",
        str(name),
        "register",
    )
    return (
        f"<div class=\"register-block\" {attrs}>"
        f"<h4>{_ssot_html_escape(name)}</h4>"
        f"{desc_html}{prop_html}{field_html}"
        "</div>"
    )

def _ssot_html_hex(value: Any) -> str:
    """Format integer-like values as 0x-hex; pass through other scalars."""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return f"0x{value:X}"
    if isinstance(value, str):
        text = value.strip()
        if re.match(r"^(0[xX])?[0-9a-fA-F]+$", text) and not text.lower().startswith("0x"):
            try:
                return f"0x{int(text):X}" if text.isdigit() else text
            except ValueError:
                return text
        return text
    return _ssot_md_scalar(value)

def _ssot_html_registers(data: dict) -> str:
    """Render the `registers` section as clean register-map tables.

    Each register becomes a properties table plus a bit-field table. The
    whole thing is wrapped in the same `diagram-card` styling used by the
    FSM / timing sections so the datasheet stays visually consistent.
    """
    registers = data.get("registers") if isinstance(data, dict) else None
    reg_list: list = []
    if isinstance(registers, dict):
        raw = registers.get("register_list")
        if isinstance(raw, list):
            reg_list = raw
    elif isinstance(registers, list):
        reg_list = registers

    reg_list = [r for r in reg_list if isinstance(r, dict)]
    if not reg_list:
        return (
            "<section class=\"diagram-card\">"
            "<h3>Register Map</h3>"
            "<p class=\"doc-empty\">No registers specified in SSOT.</p>"
            "</section>"
        )
    blocks = "".join(_ssot_html_register_block(reg, idx) for idx, reg in enumerate(reg_list, start=1))
    return "<section class=\"diagram-card\"><h3>Register Map</h3>" + blocks + "</section>"

def _ssot_html_insert_after_section(html_body: str, heading_text: str, html: str) -> str:
    """Insert `html` after the `<h2>heading_text</h2>` section, replacing its body.

    The markdown `## <heading_text>` renders as `<h2 ...>heading_text</h2>`.
    Everything between that heading and the next `<h2` is the section body;
    it is replaced by `html` (so the plain markdown register table is dropped
    in favour of the rich tables). If the heading is absent, append `html` so
    it never disappears.
    """
    import re as _re

    if not html:
        return html_body
    heading = _re.search(
        rf"<h2\b[^>]*>\s*{_re.escape(heading_text)}\s*</h2>", html_body, _re.IGNORECASE
    )
    if not heading:
        return html_body + html
    next_h2 = _re.search(r"<h2\b", html_body[heading.end():], _re.IGNORECASE)
    if next_h2:
        body_end = heading.end() + next_h2.start()
    else:
        body_end = len(html_body)
    return html_body[:heading.end()] + html + html_body[body_end:]

def _ssot_html_append_to_section(html_body: str, heading_text: str, html: str) -> str:
    import re as _re

    if not html:
        return html_body
    heading = _re.search(
        rf"<h2\b[^>]*>\s*{_re.escape(heading_text)}\s*</h2>", html_body, _re.IGNORECASE
    )
    if not heading:
        return html_body + html
    next_h2 = _re.search(r"<h2\b", html_body[heading.end():], _re.IGNORECASE)
    insert_at = heading.end() + next_h2.start() if next_h2 else len(html_body)
    return html_body[:insert_at] + html + html_body[insert_at:]

def _ssot_html_design_views(data: dict, ip: str) -> str:
    if not isinstance(data, dict):
        return ""
    # Design Views groups the datasheet diagrams (FSM + Timing). The block
    # diagram is injected separately, directly under the Top Module section.
    return (
        "<section class=\"design-views\">"
        "<h2>Design Views</h2>"
        f"<p class=\"design-note\">Derived deterministically from <code>{_ssot_html_escape(ip)}/yaml/{_ssot_html_escape(ip)}.ssot.yaml</code>.</p>"
        f"{_ssot_html_fsm_section(data)}"
        f"{_ssot_html_timing_section(data)}"
        "</section>"
    )

def _ssot_html_insert_after_top_module(html_body: str, block_diagram: str) -> str:
    """Insert `block_diagram` right after the rendered Top Module section.

    The markdown `## Top Module` heading renders (via the toc extension) as
    an `<h2 ...>Top Module</h2>`. Find that heading, then insert the block
    diagram just before the next `<h2` (i.e. at the end of the Top Module
    section's content). If the heading isn't found, place the block diagram
    at the very top of the body so it never crashes / disappears.
    """
    import re as _re

    if not block_diagram:
        return html_body

    heading = _re.search(r"<h2\b[^>]*>\s*Top Module\s*</h2>", html_body, _re.IGNORECASE)
    if not heading:
        return block_diagram + html_body

    next_h2 = _re.search(r"<h2\b", html_body[heading.end():], _re.IGNORECASE)
    if next_h2:
        insert_at = heading.end() + next_h2.start()
    else:
        insert_at = len(html_body)
    return html_body[:insert_at] + block_diagram + html_body[insert_at:]

def _ssot_html_normalize_mermaid_fences(html_body: str) -> str:
    """Keep mermaid fences as readable source in the conservative DOC export."""

    return html_body

def _ssot_html_mermaid_runtime() -> str:
    """Load and run Mermaid reliably for exported HTML served under /api/ssot."""

    return (
        "<script>"
        "(function(){"
        "function render(){"
        "var nodes=document.querySelectorAll('.mermaid');"
        "if(!nodes.length||!window.mermaid){return;}"
        "try{"
        # securityLevel:'loose' is required so flowchart htmlLabels takes effect
        # (mermaid v11 forces htmlLabels off under the default 'strict' level,
        # falling back to SVG <text> whose width is measured before fonts settle
        # — that mis-sizes node boxes and clips labels like "R capture (FIFO)").
        # HTML labels are foreignObject <div>s that size to their content, so the
        # box grows to fit the text. useMaxWidth keeps diagrams responsive.
        "window.mermaid.initialize({startOnLoad:false,theme:'neutral',"
        "securityLevel:'loose',flowchart:{htmlLabels:true,useMaxWidth:true}});"
        "var result=window.mermaid.run"
        "?window.mermaid.run({querySelector:'.mermaid'})"
        ":window.mermaid.init(undefined,nodes);"
        "if(result&&typeof result.catch==='function'){"
        "result.catch(function(err){console.error('SSOT mermaid render failed',err);});"
        "}"
        "}catch(err){console.error('SSOT mermaid render failed',err);}"
        "}"
        "window.__ssotRenderMermaid=render;"
        "function whenReady(){"
        "if(document.readyState==='loading'){"
        "document.addEventListener('DOMContentLoaded',render,{once:true});"
        "}else{render();}"
        "}"
        "window.__ssotMermaidReady=whenReady;"
        "document.addEventListener('DOMContentLoaded',render,{once:true});"
        "window.addEventListener('load',render,{once:true});"
        "})();"
        "</script>"
        "<script src=\"../../vendor/mermaid.min.js\" defer "
        "onload=\"window.__ssotMermaidReady&&window.__ssotMermaidReady()\" "
        "onerror=\"this.onerror=null;this.src='/vendor/mermaid.min.js';\"></script>"
    )

def _ssot_html_render_custom_block(blk: dict, ip: str) -> str:
    """Render one SSOT custom_block (markdown | mermaid | html; inline | file).

    The block source lives in the SSOT, so the datasheet survives regeneration.
    File refs are read at render time and constrained to _project_root(). html files
    are embedded via an <iframe src=/api/file/raw> for natural style isolation
    (trusted, user-authored — no hard sandbox in Phase 1).
    """
    if not isinstance(blk, dict):
        return ""
    btype = str(blk.get("type") or "markdown").strip().lower()
    title = str(blk.get("title") or "").strip()
    title_html = f"<h3>{_ssot_html_escape(title)}</h3>" if title else ""
    inline = blk.get("inline")
    file_rel = str(blk.get("file") or "").strip()

    if btype == "html":
        if file_rel:
            if _ssot_resolve_custom_file(file_rel) is None:
                body = f"<p class=\"doc-empty\">custom html file not found: {_ssot_html_escape(file_rel)}</p>"
            else:
                from urllib.parse import quote
                body = (
                    f"<iframe src=\"/api/file/raw?path={quote(file_rel)}\" "
                    "style=\"width:100%;min-height:420px;border:1px solid #ddd;border-radius:6px;\" "
                    f"title=\"{_ssot_html_escape(title or file_rel)}\"></iframe>"
                )
        elif isinstance(inline, str) and inline.strip():
            body = inline  # trusted, user-authored HTML embedded as-is
        else:
            body = "<p class=\"doc-empty\">empty html block</p>"
        return f"<section class=\"diagram-card\">{title_html}{body}</section>"

    # markdown / mermaid → need the text content (inline or file)
    content = ""
    if isinstance(inline, str) and inline.strip():
        content = inline
    elif file_rel:
        target = _ssot_resolve_custom_file(file_rel)
        if target is None:
            return (f"<section class=\"diagram-card\">{title_html}"
                    f"<p class=\"doc-empty\">custom file not found: {_ssot_html_escape(file_rel)}</p></section>")
        try:
            content = target.read_text(encoding="utf-8")
        except Exception:
            content = ""
    if btype == "mermaid":
        body = (
            "<pre class=\"mermaid-source\"><code>"
            f"{_ssot_html_escape(content)}"
            "</code></pre>"
        )
    else:
        try:
            import markdown as _cbmod  # type: ignore
            body = _cbmod.markdown(content, extensions=["tables", "fenced_code"])
        except Exception:
            body = f"<pre>{_ssot_html_escape(content)}</pre>"
    return f"<section class=\"diagram-card\">{title_html}{body}</section>"

def _ssot_html_custom_blocks_for(data: dict, anchor_key: str, ip: str) -> str:
    """Render all custom_blocks anchored after `anchor_key`, in order."""
    blocks = data.get("custom_blocks") if isinstance(data, dict) else None
    if not isinstance(blocks, list):
        return ""
    out = [
        _ssot_html_render_custom_block(blk, ip)
        for blk in blocks
        if isinstance(blk, dict) and str(blk.get("after") or "").strip() == anchor_key
    ]
    return "".join(out)



# Phase 25: 5 biggest html fns extracted to atlas_ssot_export_html2.py.
from src.atlas_ssot_export_html2 import (
    _ssot_html_block_diagram,
    _ssot_html_timing_section,
    _ssot_html_function_model,
    _ssot_html_cycle_model,
    _ssot_to_html,
)
