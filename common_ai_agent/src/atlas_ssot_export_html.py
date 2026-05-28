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

def _ssot_html_block_diagram(data: dict) -> str:
    top = data.get("top_module") if isinstance(data.get("top_module"), dict) else {}
    top_name = str(top.get("name") or "TOP")
    top_desc = str(top.get("description") or top.get("purpose") or "").strip()
    submods = _ssot_html_submodules(data)
    interfaces = _ssot_html_interfaces(data)

    left_ifaces: list[dict] = []
    right_ifaces: list[dict] = []

    def iface_port_dirs(iface: dict) -> set[str]:
        ports = iface.get("ports")
        if not isinstance(ports, list):
            return set()
        dirs: set[str] = set()
        for port in ports:
            if not isinstance(port, dict):
                continue
            direction = str(port.get("direction") or "").strip().lower()
            if direction:
                dirs.add(direction)
        return dirs

    def iface_side(iface: dict) -> str:
        role = str(iface.get("role") or iface.get("direction") or "").strip().lower()
        if role in {"master", "source", "output", "out", "producer"}:
            return "right"
        if role in {"slave", "sink", "input", "in", "consumer"}:
            return "left"

        dirs = iface_port_dirs(iface)
        if dirs and dirs <= {"input", "in"}:
            return "left"
        if dirs and dirs <= {"output", "out"}:
            return "right"
        typ = str(iface.get("type") or iface.get("protocol") or "").strip().lower()
        if any(token in typ for token in ("axi", "apb", "ace", "chi")):
            return "right"
        return "left"

    def iface_flow(iface: dict) -> str:
        role = str(iface.get("role") or iface.get("direction") or "").strip().lower()
        if role in {"master", "slave"}:
            return "bi"
        if role in {"source", "output", "out", "producer"}:
            return "out"
        if role in {"sink", "input", "in", "consumer"}:
            return "in"

        dirs = iface_port_dirs(iface)
        if "inout" in dirs or (dirs & {"input", "in"} and dirs & {"output", "out"}):
            return "bi"
        if dirs and dirs <= {"input", "in"}:
            return "in"
        if dirs and dirs <= {"output", "out"}:
            return "out"
        return "bi"

    for iface in interfaces:
        if iface_side(iface) == "right":
            right_ifaces.append(iface)
        else:
            left_ifaces.append(iface)

    def iface_link(iface: dict, side: str) -> str:
        name = _ssot_html_escape(iface.get("name") or "(interface)")
        typ = _ssot_html_escape(iface.get("type") or iface.get("protocol") or iface.get("role") or "")
        ports = iface.get("ports")
        count = len(ports) if isinstance(ports, list) else 0
        meta = " · ".join(part for part in (typ, f"{count} ports" if count else "") if part)
        meta_html = f"<small>{meta}</small>" if meta else ""
        label = f"<div class=\"iface-label\"><strong>{name}</strong>{meta_html}</div>"
        wire = "<span class=\"iface-wire\" aria-hidden=\"true\"></span>"
        body = f"{label}{wire}" if side == "left" else f"{wire}{label}"
        return (
            f"<div class=\"iface-link {side} flow-{iface_flow(iface)}\">"
            f"{body}</div>"
        )

    left_html = "".join(iface_link(item, "left") for item in left_ifaces)
    right_html = "".join(iface_link(item, "right") for item in right_ifaces)

    if submods:
        module_html = "".join(
            "<div class=\"module-node\">"
            f"<strong>{_ssot_html_escape(_ssot_html_item_name(item, f'module_{idx}'))}</strong>"
            f"<small>{_ssot_html_escape(item.get('description') or item.get('role') or item.get('file') or '')}</small>"
            "</div>"
            for idx, item in enumerate(submods, start=1)
        )
    else:
        module_html = "<div class=\"module-node single\"><strong>single block</strong><small>no sub_modules declared</small></div>"

    top_desc_html = f"<div class=\"top-desc\">{_ssot_html_escape(top_desc)}</div>" if top_desc else ""
    return (
        "<section class=\"diagram-card\">"
        "<h3>Block Diagram</h3>"
        "<div class=\"block-graph\">"
        f"<div class=\"iface-column\">{left_html}</div>"
        "<div class=\"top-node\">"
        f"<div class=\"top-title\">{_ssot_html_escape(top_name)}</div>"
        f"{top_desc_html}"
        f"<div class=\"module-grid\">{module_html}</div>"
        "</div>"
        f"<div class=\"iface-column\">{right_html}</div>"
        "</div>"
        "</section>"
    )

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

def _ssot_html_timing_section(data: dict) -> str:
    timing = data.get("timing")
    cycle_model = data.get("cycle_model") if isinstance(data.get("cycle_model"), dict) else {}
    diagrams: list[dict] = []
    if isinstance(timing, dict):
        for key in ("diagrams", "timing_diagrams", "waveforms", "waves"):
            raw = timing.get(key)
            if isinstance(raw, list):
                for item in raw:
                    if isinstance(item, dict):
                        diagrams.append(item)
                break
        signals = timing.get("signals")
        if not diagrams and isinstance(signals, list):
            diagrams.append({"name": timing.get("name") or "timing", "signals": signals})
    elif isinstance(timing, list):
        diagrams = [item for item in timing if isinstance(item, dict)]

    blocks: list[str] = []
    for idx, diagram in enumerate(diagrams[:6], start=1):
        name = _ssot_html_escape(diagram.get("name") or diagram.get("id") or f"timing_{idx}")
        # Diagram-level reference: which clock the waveform is sampled on, plus an
        # optional description. Without a reference, signals can't be mapped to RTL.
        clock = diagram.get("clock") or diagram.get("reference_clock") or diagram.get("clk") or ""
        desc = diagram.get("description") or diagram.get("note") or ""
        sub_parts = []
        if clock:
            sub_parts.append(f"reference clock: <code>{_ssot_html_escape(clock)}</code>")
        if desc:
            sub_parts.append(_ssot_html_escape(desc))
        subtitle = (
            f"<p class=\"wave-sub\" style=\"color:var(--fg-mute);font-size:.85em;margin:2px 0 6px;\">"
            f"{' · '.join(sub_parts)}</p>"
            if sub_parts else ""
        )
        signals = diagram.get("signals") or diagram.get("waveforms") or diagram.get("waves")
        if not isinstance(signals, list):
            continue
        rows = []
        for signal in signals:
            if not isinstance(signal, dict):
                continue
            vals = _ssot_html_signal_values(signal)
            if not vals:
                continue
            cell_parts = []
            for v in vals:
                low_v = str(v).lower()
                cls = "high" if low_v in {"1", "h", "high", "assert"} else (
                    "low" if low_v in {"0", "l", "low"} else "mark"
                )
                cell_parts.append(f"<td class=\"wave-cell {cls}\">{_ssot_html_escape(v)}</td>")
            cells = "".join(cell_parts)
            # Source mapping: which module's boundary port OR internal signal this
            # row is, and its kind (port / reg / wire / logic / comb / ff). Makes the
            # waveform traceable to the io_list ports or a submodule's internal nets.
            src_mod = signal.get("module") or signal.get("instance") or ""
            is_port = bool(signal.get("port"))
            src_port = (
                signal.get("port") or signal.get("internal_signal")
                or signal.get("signal_ref") or signal.get("net") or ""
            )
            kind = str(signal.get("kind") or signal.get("type") or ("port" if is_port else "")).strip()
            label = _ssot_html_escape(
                signal.get("name") or signal.get("signal") or src_port or ""
            )
            ref = ".".join(p for p in (str(src_mod), str(src_port)) if p)
            tag = f" · {_ssot_html_escape(kind)}" if kind else ""
            src_html = (
                f"<span class=\"sig-src\" style=\"display:block;color:var(--fg-mute);font-size:.78em;font-weight:400;\">{_ssot_html_escape(ref)}{tag}</span>"
                if ref else ""
            )
            # Optional per-signal detail/description (what an internal reg means,
            # encoding, polarity…). Shown as a muted note + row tooltip when present.
            detail = signal.get("description") or signal.get("detail") or signal.get("note") or ""
            detail_html = (
                f"<span class=\"sig-detail\" style=\"display:block;color:var(--fg-mute);font-size:.72em;font-weight:400;font-style:italic;\">{_ssot_html_escape(detail)}</span>"
                if detail else ""
            )
            th_title = f" title=\"{_ssot_html_escape(detail)}\"" if detail else ""
            rows.append(
                "<tr>"
                f"<th style=\"text-align:left;\"{th_title}>{label}{src_html}{detail_html}</th>"
                f"{cells}"
                "</tr>"
            )
        if rows:
            blocks.append(
                f"<h4>{name}</h4>"
                f"{subtitle}"
                "<table class=\"wave-table\"><tbody>"
                + "".join(rows)
                + "</tbody></table>"
            )

    if not blocks:
        pipeline = cycle_model.get("pipeline") or cycle_model.get("stages")
        if isinstance(pipeline, list) and pipeline:
            rows = []
            for item in pipeline:
                if not isinstance(item, dict):
                    continue
                rows.append(
                    "<tr>"
                    f"<td>{_ssot_html_escape(item.get('cycle') or item.get('phase') or '')}</td>"
                    f"<td>{_ssot_html_escape(item.get('stage') or item.get('name') or item.get('id') or '')}</td>"
                    f"<td>{_ssot_html_escape(item.get('action') or item.get('description') or '')}</td>"
                    f"<td>{_ssot_html_escape(item.get('ready') or item.get('notes') or '')}</td>"
                    "</tr>"
                )
            if rows:
                blocks.append(
                    "<h4>Pipeline Timing</h4>"
                    "<table><thead><tr><th>Cycle</th><th>Stage</th><th>Action</th><th>Ready / Notes</th></tr></thead>"
                    f"<tbody>{''.join(rows)}</tbody></table>"
                )

    body = "".join(blocks) if blocks else "<p class=\"doc-empty\">Timing diagram not specified in SSOT.</p>"
    return f"<section class=\"diagram-card\"><h3>Timing Diagram</h3>{body}</section>"

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

def _ssot_html_function_model(data: dict) -> str:
    fm = data.get("function_model") if isinstance(data.get("function_model"), dict) else None
    if not isinstance(fm, dict) or not fm:
        return (
            "<section class=\"diagram-card function-model-doc\">"
            "<h3>Function Model</h3>"
            "<p class=\"doc-empty\">Function model not specified in SSOT.</p>"
            "</section>"
        )

    purpose = _ssot_pick(fm, "purpose", "description", "summary")
    header = (
        f"<p class=\"doc-lead\">{_ssot_html_escape(_ssot_html_scalar(purpose))}</p>"
        if purpose not in (None, "", [], {}) else ""
    )

    state_vars = fm.get("state_variables")
    invariants = fm.get("invariants")
    overview_parts = []
    if state_vars not in (None, "", [], {}):
        overview_parts.append(
            "<section class=\"doc-subsection\"><h4>State Variables</h4>"
            f"{_ssot_html_rule_cards(state_vars, 'state_variable')}</section>"
        )
    if invariants not in (None, "", [], {}):
        overview_parts.append(
            "<section class=\"doc-subsection\"><h4>Invariants</h4>"
            f"{_ssot_html_value_block(invariants)}</section>"
        )

    txs = fm.get("transactions")
    tx_cards: list[str] = []
    if isinstance(txs, list):
        for idx, tx in enumerate(txs, start=1):
            if not isinstance(tx, dict):
                tx_cards.append(
                    "<article class=\"transaction-card\">"
                    f"<h4>Transaction {idx}</h4>{_ssot_html_value_block(tx)}"
                    "</article>"
                )
                continue
            tx_id = _ssot_pick(tx, "id", "transaction_id") or f"TX{idx}"
            name = _ssot_pick(tx, "name", "kind", "type") or tx_id
            desc = _ssot_pick(tx, "description", "summary")
            panels = [
                ("Preconditions", tx.get("preconditions")),
                ("Inputs", tx.get("inputs")),
                ("Outputs", tx.get("outputs")),
                ("Output Rules", tx.get("output_rules")),
                ("State Updates", tx.get("state_updates")),
                ("Side Effects", tx.get("side_effects")),
                ("Error Cases", tx.get("error_cases")),
            ]
            panel_html = []
            for label, value in panels:
                if value in (None, "", [], {}):
                    continue
                if label in {"Output Rules", "State Updates"}:
                    body = _ssot_html_rule_cards(value, label.lower().replace(" ", "_"))
                else:
                    body = _ssot_html_value_block(value)
                panel_html.append(
                    "<section class=\"transaction-panel\">"
                    f"<h5>{_ssot_html_escape(label)}</h5>{body}"
                    "</section>"
                )
            known = {
                "id", "transaction_id", "name", "kind", "type", "description", "summary",
                "preconditions", "inputs", "outputs", "output_rules",
                "state_updates", "side_effects", "error_cases",
            }
            leftovers = {k: v for k, v in tx.items() if k not in known and v not in (None, "", [], {})}
            extra = (
                "<section class=\"transaction-panel wide\"><h5>Additional Contract</h5>"
                f"{_ssot_html_value_block(leftovers)}</section>"
                if leftovers else ""
            )
            desc_html = (
                f"<p class=\"tx-desc\">{_ssot_html_escape(_ssot_html_scalar(desc))}</p>"
                if desc not in (None, "", [], {}) else ""
            )
            tx_cards.append(
                "<article class=\"transaction-card\">"
                "<div class=\"transaction-title\">"
                f"<span class=\"tx-id\">{_ssot_html_escape(_ssot_html_scalar(tx_id))}</span>"
                f"<h4>{_ssot_html_escape(_ssot_html_scalar(name))}</h4>"
                "</div>"
                f"{desc_html}"
                f"<div class=\"transaction-grid\">{''.join(panel_html)}{extra}</div>"
                "</article>"
            )

    tx_body = (
        "<section class=\"doc-subsection\"><h4>Transactions</h4>"
        f"<div class=\"transaction-stack\">{''.join(tx_cards)}</div></section>"
        if tx_cards else
        "<section class=\"doc-subsection\"><h4>Transactions</h4>"
        "<p class=\"doc-empty\">No transactions declared.</p></section>"
    )

    leftover = {
        k: v for k, v in fm.items()
        if k not in ("purpose", "description", "summary", "state_variables", "invariants", "transactions")
        and v not in (None, "", [], {})
    }
    leftover_html = (
        "<section class=\"doc-subsection\"><h4>Additional Function-Model Fields</h4>"
        f"{_ssot_html_value_block(leftover)}</section>"
        if leftover else ""
    )
    return (
        "<section class=\"diagram-card function-model-doc\">"
        "<h3>Function Model</h3>"
        f"{header}{''.join(overview_parts)}{tx_body}{leftover_html}"
        "</section>"
    )

def _ssot_html_cycle_model(data: dict) -> str:
    cm = data.get("cycle_model") if isinstance(data.get("cycle_model"), dict) else None
    if not isinstance(cm, dict) or not cm:
        return (
            "<section class=\"diagram-card cycle-model-doc\">"
            "<h3>Cycle Model</h3>"
            "<p class=\"doc-empty\">Cycle model not specified in SSOT.</p>"
            "</section>"
        )

    purpose = _ssot_pick(cm, "purpose", "description", "summary")
    lead = (
        f"<p class=\"doc-lead\">{_ssot_html_escape(_ssot_html_scalar(purpose))}</p>"
        if purpose not in (None, "", [], {}) else ""
    )
    contract_rows = {
        "clock": _ssot_pick(cm, "clock", "clock_domain"),
        "reset": _ssot_pick(cm, "reset", "reset_domain"),
        "latency": cm.get("latency") or cm.get("latencies"),
        "ordering": cm.get("ordering"),
        "throughput": _ssot_pick(cm, "throughput", "performance"),
    }
    contract_rows = {k: v for k, v in contract_rows.items() if v not in (None, "", [], {})}
    contract_html = (
        "<section class=\"doc-subsection\"><h4>Cycle Contract</h4>"
        f"{_ssot_html_value_block(contract_rows)}</section>"
        if contract_rows else ""
    )

    pipeline = cm.get("pipeline") or cm.get("stages")
    stage_cards: list[str] = []
    if isinstance(pipeline, list):
        for idx, stage in enumerate(pipeline, start=1):
            if isinstance(stage, dict):
                title = _ssot_pick(stage, "stage", "name", "id", "phase") or f"stage_{idx}"
                cycle = _ssot_pick(stage, "cycle", "phase", "latency")
                action = _ssot_pick(stage, "action", "description", "operation", "work")
                ready = _ssot_pick(stage, "ready", "backpressure", "stall", "notes", "note")
                known = {"stage", "name", "id", "phase", "cycle", "latency", "action", "description", "operation", "work", "ready", "backpressure", "stall", "notes", "note"}
                extra = {k: v for k, v in stage.items() if k not in known and v not in (None, "", [], {})}
            else:
                title = stage
                cycle = ""
                action = stage
                ready = ""
                extra = {}
            chip = (
                f"<span class=\"doc-chip\">{_ssot_html_escape(_ssot_html_scalar(cycle))}</span>"
                if cycle not in (None, "", [], {}) else ""
            )
            action_html = (
                f"<p>{_ssot_html_escape(_ssot_html_scalar(action))}</p>"
                if action not in (None, "", [], {}) and action != title else ""
            )
            ready_html = (
                f"<div class=\"cycle-note\"><strong>ready/backpressure</strong>{_ssot_html_value_block(ready)}</div>"
                if ready not in (None, "", [], {}) else ""
            )
            extra_html = _ssot_html_value_block(extra, "") if extra else ""
            stage_cards.append(
                "<div class=\"cycle-stage\">"
                "<div class=\"cycle-stage-head\">"
                f"<strong>{_ssot_html_escape(_ssot_html_scalar(title))}</strong>{chip}"
                "</div>"
                f"{action_html}{ready_html}{extra_html}"
                "</div>"
            )

    stage_joiner = "<span class=\"cycle-arrow\">&rarr;</span>"
    pipeline_html = (
        "<section class=\"doc-subsection\"><h4>Pipeline</h4>"
        f"<div class=\"cycle-flow\">{stage_joiner.join(stage_cards)}</div>"
        "</section>"
        if stage_cards else ""
    )

    handshake = cm.get("handshake_rules") or cm.get("handshake")
    backpressure = cm.get("backpressure")
    scenario_like = cm.get("scenarios") or cm.get("examples")
    behavior_parts = []
    if handshake not in (None, "", [], {}):
        behavior_parts.append(
            "<section class=\"doc-subsection\"><h4>Handshake Rules</h4>"
            f"{_ssot_html_rule_cards(handshake, 'handshake_rule')}</section>"
        )
    if backpressure not in (None, "", [], {}):
        behavior_parts.append(
            "<section class=\"doc-subsection\"><h4>Backpressure</h4>"
            f"{_ssot_html_value_block(backpressure)}</section>"
        )
    if scenario_like not in (None, "", [], {}):
        behavior_parts.append(
            "<section class=\"doc-subsection\"><h4>Scenarios</h4>"
            f"{_ssot_html_value_block(scenario_like)}</section>"
        )

    leftover = {
        k: v for k, v in cm.items()
        if k not in {
            "purpose", "description", "summary", "clock", "clock_domain", "reset", "reset_domain",
            "latency", "latencies", "ordering", "throughput", "performance", "pipeline", "stages",
            "handshake_rules", "handshake", "backpressure", "scenarios", "examples",
        }
        and v not in (None, "", [], {})
    }
    leftover_html = (
        "<section class=\"doc-subsection\"><h4>Additional Cycle-Model Fields</h4>"
        f"{_ssot_html_value_block(leftover)}</section>"
        if leftover else ""
    )
    return (
        "<section class=\"diagram-card cycle-model-doc\">"
        "<h3>Cycle Model</h3>"
        f"{lead}{contract_html}{pipeline_html}{''.join(behavior_parts)}{leftover_html}"
        "</section>"
    )

def _ssot_html_field_bits(field: dict) -> tuple[str, int | None]:
    """Compatibility wrapper for callers that only need display + lsb."""
    display, lsb, _width = _ssot_field_bit_info(field)
    return display, lsb

def _ssot_html_register_field_table(reg: dict) -> str:
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
    for _order, _lsb, field, bits_disp, width in parsed:
        reset = _ssot_pick(field, "reset", "reset_value", "default")
        rows.append(
            "<tr>"
            f"<td>{_ssot_html_escape(field.get('name') or field.get('id') or '')}</td>"
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
    field_html = _ssot_html_register_field_table(reg)
    return (
        "<div class=\"register-block\">"
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

def _ssot_to_html(md_text: str, ip: str, data: dict | None = None) -> str:
    import markdown as _mod  # type: ignore

    html_body = _mod.markdown(
        md_text,
        extensions=["tables", "fenced_code", "toc"],
    )
    html_body = _ssot_html_normalize_mermaid_fences(html_body)
    css = (
        "body { font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", "
        "system-ui, sans-serif; max-width: 1180px; margin: 2em auto; "
        "padding: 0 1em; line-height: 1.55; color: #222; } "
        "h1, h2, h3 { border-bottom: 1px solid #eee; padding-bottom: .2em; } "
        "table { border-collapse: collapse; margin: .8em 0; width: 100%; } "
        "th, td { border: 1px solid #ddd; padding: .35em .6em; "
        "text-align: left; vertical-align: top; } "
        "th { background: #f7f7f7; } "
        "code, pre { font-family: \"SF Mono\", Menlo, Consolas, monospace; "
        "font-size: .92em; } "
        "pre { background: #f6f8fa; padding: .8em; border-radius: 4px; "
        "overflow-x: auto; } "
        "blockquote { border-left: 3px solid #ccc; margin: 1em 0; "
        "padding: .3em .8em; color: #555; background: #fafafa; } "
        ".design-views { margin: 1.5em 0 2em; padding: 1em; border: 1px solid #d8dee9; "
        "border-radius: 8px; background: #fbfcff; } "
        ".design-note, .doc-empty { color: #5d6778; } "
        ".doc-empty.small { font-size: .86em; } "
        ".diagram-card { margin: 1em 0; padding: 1em; border: 1px solid #e3e7ef; "
        "border-radius: 8px; background: #fff; overflow-x: auto; } "
        ".diagram-card h3 { margin-top: 0; } "
        ".doc-lead { color: #475569; margin: .25em 0 1em; } "
        ".doc-subsection { margin: 1em 0 1.15em; } "
        ".doc-subsection h4 { margin: 0 0 .55em; font-size: 1.05em; border-bottom: 1px solid #edf0f5; padding-bottom: .25em; } "
        ".doc-list.compact { margin: .25em 0; padding-left: 1.2em; } "
        ".doc-stack { display: grid; gap: .45em; } "
        ".doc-nested-item { border: 1px solid #e5e9f0; border-radius: 6px; background: #fbfcff; padding: .55em .65em; } "
        ".mini-yaml { margin: .2em 0; padding: .55em .65em; background: #f7f9fc; border: 1px solid #e5e9f0; border-radius: 6px; white-space: pre-wrap; } "
        ".kv-list { display: grid; gap: .35em; margin: .25em 0; } "
        ".kv-row { display: grid; grid-template-columns: minmax(120px, .32fr) minmax(0, 1fr); gap: .75em; align-items: start; } "
        ".kv-row dt { color: #64748b; font-weight: 700; text-transform: none; } "
        ".kv-row dd { margin: 0; min-width: 0; } "
        ".doc-chip { display: inline-flex; align-items: center; border: 1px solid #cbd5e1; border-radius: 999px; padding: .08em .45em; "
        "background: #f8fafc; color: #334155; font: 700 .82em \"SF Mono\", Menlo, Consolas, monospace; white-space: nowrap; } "
        ".rule-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: .55em; } "
        ".rule-card { border: 1px solid #dbe3ee; border-radius: 7px; padding: .6em .7em; background: #fbfdff; min-width: 0; } "
        ".rule-head { display: flex; justify-content: space-between; gap: .5em; align-items: center; margin-bottom: .35em; } "
        ".rule-head strong { overflow-wrap: anywhere; } "
        ".rule-head span { display: inline-flex; gap: .25em; flex-wrap: wrap; justify-content: flex-end; } "
        ".rule-card p { margin: .35em 0 0; color: #475569; } "
        ".rule-expr { display: grid; grid-template-columns: 3.5em minmax(0,1fr); gap: .4em; align-items: start; margin-top: .25em; } "
        ".rule-expr span { color: #64748b; font-size: .82em; font-weight: 700; text-transform: uppercase; } "
        ".rule-expr code { display: block; white-space: pre-wrap; overflow-wrap: anywhere; background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 5px; padding: .22em .38em; } "
        ".transaction-stack { display: grid; gap: 1em; } "
        ".transaction-card { border: 1px solid #d9e0ea; border-left: 4px solid #315fdc; border-radius: 8px; background: #fff; padding: .85em; } "
        ".transaction-title { display: flex; align-items: baseline; gap: .65em; flex-wrap: wrap; margin-bottom: .35em; } "
        ".transaction-title h4 { margin: 0; border: 0; padding: 0; font-size: 1.05em; } "
        ".tx-id { font: 800 .86em \"SF Mono\", Menlo, Consolas, monospace; color: #315fdc; background: #eef4ff; border: 1px solid #c8d8ff; border-radius: 5px; padding: .12em .45em; } "
        ".tx-desc { color: #475569; margin: .25em 0 .75em; } "
        ".transaction-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: .7em; align-items: start; } "
        ".transaction-panel { border: 1px solid #e5e9f0; border-radius: 7px; background: #fbfcff; padding: .65em; min-width: 0; } "
        ".transaction-panel.wide { grid-column: 1 / -1; } "
        ".transaction-panel h5 { margin: 0 0 .4em; color: #334155; font-size: .86em; text-transform: uppercase; letter-spacing: .03em; } "
        ".cycle-flow { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: .65em; align-items: stretch; } "
        ".cycle-stage { position: relative; border: 1px solid #bfd0ea; border-radius: 8px; background: #f8fbff; padding: .75em; min-width: 0; } "
        ".cycle-stage-head { display: flex; justify-content: space-between; gap: .5em; align-items: center; margin-bottom: .35em; } "
        ".cycle-stage-head strong { overflow-wrap: anywhere; } "
        ".cycle-stage p { margin: .25em 0; color: #475569; } "
        ".cycle-note { margin-top: .45em; padding-top: .45em; border-top: 1px solid #dbe5f2; color: #475569; } "
        ".cycle-note strong { display: block; color: #64748b; font-size: .78em; text-transform: uppercase; margin-bottom: .2em; } "
        ".cycle-arrow { display: none; } "
        ".register-block { margin: .8em 0 1.1em; } "
        ".register-block h4 { margin: .2em 0; } "
        ".reg-desc { color: #475569; margin: .1em 0 .55em; } "
        ".register-props { margin: .35em 0 .55em; } "
        ".register-props th { width: 9em; text-align: left; } "
        ".register-fields { width: 100%; } "
        ".register-fields th:nth-child(2), .register-fields td:nth-child(2), "
        ".register-fields th:nth-child(3), .register-fields td:nth-child(3) { "
        "text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; } "
        ".block-graph { display: grid; grid-template-columns: minmax(170px, 1fr) minmax(280px, 2fr) minmax(170px, 1fr); "
        "gap: 0; align-items: center; } "
        ".iface-column { display: grid; gap: .75em; align-content: center; } "
        ".iface-link { display: grid; align-items: center; min-height: 3em; } "
        ".iface-link.left { grid-template-columns: minmax(120px, 1fr) minmax(44px, .35fr); } "
        ".iface-link.right { grid-template-columns: minmax(44px, .35fr) minmax(120px, 1fr); } "
        ".iface-label { color: #1f2937; padding: .2em .45em; line-height: 1.25; } "
        ".iface-link.left .iface-label { text-align: right; } "
        ".iface-label strong { display: block; font-weight: 800; } "
        ".iface-label small, .module-node small { display: block; color: #64748b; margin-top: .2em; } "
        ".iface-wire { display: block; position: relative; height: 2px; min-width: 42px; background: #315fdc; } "
        ".iface-wire::before, .iface-wire::after { content: \"\"; display: none; position: absolute; top: 50%; "
        "width: .55em; height: .55em; border-top: 2px solid #315fdc; border-right: 2px solid #315fdc; } "
        ".iface-link.flow-out.left .iface-wire::before, .iface-link.flow-in.right .iface-wire::before, "
        ".iface-link.flow-bi .iface-wire::before { display: block; left: 0; transform: translateY(-50%) rotate(225deg); } "
        ".iface-link.flow-in.left .iface-wire::after, .iface-link.flow-out.right .iface-wire::after, "
        ".iface-link.flow-bi .iface-wire::after { display: block; right: 0; transform: translateY(-50%) rotate(45deg); } "
        ".top-node { border: 2px solid #315fdc; border-radius: 10px; padding: 1em; background: #f4f7ff; text-align: center; } "
        ".top-title { font-weight: 800; font-size: 1.15em; } "
        ".top-desc { color: #475569; margin-top: .3em; } "
        ".module-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: .65em; margin-top: 1em; } "
        ".module-node { border: 1px solid #b8c5dd; border-radius: 6px; padding: .65em; background: #fff; min-height: 3.4em; } "
        ".module-node.single { max-width: 280px; margin: 0 auto; } "
        ".fsm-machine { margin: .8em 0 1.1em; } "
        ".fsm-machine h4 { margin: .2em 0; } "
        ".reset-note { color: #475569; margin: .1em 0 .6em; } "
        ".fsm-rail { display: flex; flex-wrap: wrap; align-items: center; gap: .4em; margin: .55em 0 .8em; } "
        ".fsm-state { border: 1px solid #b8c5dd; border-radius: 999px; padding: .35em .7em; background: #f8fafc; font-family: monospace; } "
        ".fsm-state.reset { border-color: #16a34a; background: #ecfdf3; } "
        ".fsm-arrow { color: #64748b; } "
        ".fsm-flow-map { display: grid; gap: .5em; margin: .6em 0 .9em; min-width: 520px; } "
        ".fsm-flow-row { display: grid; grid-template-columns: minmax(110px,.7fr) minmax(180px,1.35fr) minmax(110px,.7fr); "
        "gap: .65em; align-items: center; border: 1px solid #e1e7f0; border-radius: 7px; background: #fbfcff; padding: .5em .6em; } "
        ".fsm-flow-row small { grid-column: 2 / -1; color: #64748b; } "
        ".fsm-flow-state { display: inline-flex; justify-content: center; border: 1px solid #b8c5dd; border-radius: 999px; "
        "padding: .3em .65em; background: #fff; font: 800 .9em \"SF Mono\", Menlo, Consolas, monospace; overflow-wrap: anywhere; text-align: center; } "
        ".fsm-flow-state.reset { border-color: #16a34a; background: #ecfdf3; } "
        ".fsm-flow-edge { display: flex; align-items: center; justify-content: center; color: #475569; min-width: 0; } "
        ".fsm-flow-edge::before, .fsm-flow-edge::after { content: \"\"; height: 1px; background: #94a3b8; flex: 1; min-width: 18px; } "
        ".fsm-flow-edge span { border: 1px solid #d4dbe8; border-radius: 5px; background: #fff; padding: .18em .42em; margin: 0 .35em; overflow-wrap: anywhere; text-align: center; } "
        ".wave-table { width: 100%; table-layout: fixed; } "
        ".wave-table th { width: 9em; } "
        ".wave-cell { text-align: center; font-family: monospace; padding: .25em .35em; } "
        ".wave-cell.high { background: #dff7e7; border-top: 3px solid #16a34a; } "
        ".wave-cell.low { background: #f8fafc; border-bottom: 3px solid #64748b; } "
        ".wave-cell.mark { background: #fff7d6; } "
        ".mermaid { margin: .6em 0 .9em; } "
        ".mermaid-source { margin: .6em 0 .9em; white-space: pre-wrap; overflow-wrap: anywhere; } "
        "@media (min-width: 920px) { .cycle-flow { display: flex; overflow-x: auto; padding-bottom: .2em; } "
        ".cycle-stage { flex: 1 0 190px; } .cycle-arrow { display: inline-flex; align-items: center; color: #64748b; font-weight: 900; } } "
        "@media (max-width: 760px) { .block-graph { grid-template-columns: 1fr; gap: .8em; } "
        ".kv-row { grid-template-columns: 1fr; gap: .15em; } "
        ".transaction-grid { grid-template-columns: 1fr; } "
        ".fsm-flow-map { min-width: 0; } .fsm-flow-row { grid-template-columns: 1fr; } "
        ".fsm-flow-row small { grid-column: auto; } "
        ".iface-link.left, .iface-link.right { grid-template-columns: minmax(44px, .25fr) minmax(120px, 1fr); } "
        ".iface-link.left .iface-wire { order: 1; } .iface-link.left .iface-label { order: 2; } "
        ".wave-table { table-layout: auto; } }"
    )
    safe_ip = str(ip).replace("<", "&lt;").replace(">", "&gt;")

    if isinstance(data, dict):
        # Replace the plain markdown "Registers" section body with the
        # rich register-map tables (per-register props + bit-field tables).
        registers_html = _ssot_html_registers(data)
        html_body = _ssot_html_insert_after_section(html_body, "Registers", registers_html)
        # Custom blocks: inject user-authored content (markdown / mermaid /
        # html; inline or file ref) after its anchor section. Source lives in
        # SSOT (data["custom_blocks"]) so it survives regeneration.
        if isinstance(data.get("custom_blocks"), list):
            for _key, _label in _SSOT_EXPORT_SECTION_ORDER:
                _cb = _ssot_html_custom_blocks_for(data, _key, ip)
                if _cb:
                    html_body = _ssot_html_insert_after_section(html_body, _label, _cb)

    mermaid_head = _ssot_html_mermaid_runtime() if 'class="mermaid"' in html_body else ""
    return (
        "<!DOCTYPE html>\n"
        "<html><head><meta charset=\"utf-8\">"
        f"<title>{safe_ip} — SSOT</title>"
        f"<style>{css}</style>"
        f"{mermaid_head}</head><body>"
        f"{html_body}"
        "</body></html>"
    )

