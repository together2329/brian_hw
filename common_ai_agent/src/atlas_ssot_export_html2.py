"""SSOT HTML rendering — split-out chunk (Phase 25 of refactor/atlas-modular).

Five largest functions from atlas_ssot_export_html.py moved here to keep
both files under 1000 lines. Same lazy-hydration pattern as Phase 24:
helpers from the sibling are pulled in at first call to dodge the
circular import chain (atlas_ssot_export → this → back).
"""
from __future__ import annotations

import json
import re
from typing import Any


def _import_html_helpers():
    g = globals()
    if g.get("_HELPERS_HYDRATED"): return
    from src import atlas_ssot_export_html as _h
    from src import atlas_ssot_export as _se
    for name in (
        "_ssot_html_custom_blocks_for",
        "_ssot_html_escape",
        "_ssot_html_insert_after_section",
        "_ssot_html_interfaces",
        "_ssot_html_item_name",
        "_ssot_html_mermaid_runtime",
        "_ssot_html_normalize_mermaid_fences",
        "_ssot_html_registers",
        "_ssot_html_rule_cards",
        "_ssot_html_scalar",
        "_ssot_html_signal_values",
        "_ssot_html_submodules",
        "_ssot_html_value_block",
    ):
        if hasattr(_h, name): g[name] = getattr(_h, name)
        elif hasattr(_se, name): g[name] = getattr(_se, name)
    g["_HELPERS_HYDRATED"] = True


_import_html_helpers()

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

