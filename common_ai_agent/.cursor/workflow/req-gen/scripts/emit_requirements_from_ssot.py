#!/usr/bin/env python3
"""Emit a traceable requirements ledger from an existing SSOT YAML.

This is a recovery/audit path for projects that already have SSOT but only a
placeholder req file. The normal flow remains conversational REQ capture before
SSOT generation; this script makes the REQ artifact explicit and reviewable so
ATLAS progress can gate on real requirement content instead of prose claims.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Any

import yaml


def _load_ssot(ip_dir: Path, ip: str) -> dict[str, Any]:
    path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    if not path.is_file():
        raise SystemExit(f"missing SSOT YAML: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"invalid SSOT YAML root: {path}")
    return data


def _text(value: Any, default: str = "N/A") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "yes" if value else "no"
    text = str(value).strip()
    return text if text else default


def _table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    if rows:
        for row in rows:
            out.append("| " + " | ".join(_text(v).replace("\n", " ") for v in row) + " |")
    else:
        out.append("| " + " | ".join(["N/A"] * len(headers)) + " |")
    return out


def _bullets(items: Any, field: str | None = None) -> list[str]:
    if not isinstance(items, list) or not items:
        return ["- N/A"]
    out: list[str] = []
    for item in items:
        if isinstance(item, dict):
            name = item.get("name") or item.get("id") or item.get("signal") or item.get("stage") or item.get("from")
            desc = item.get(field) if field else (
                item.get("description") or item.get("rule") or item.get("action") or item.get("expected") or item
            )
            out.append(f"- **{_text(name, 'item')}**: {_text(desc)}")
        else:
            out.append(f"- {_text(item)}")
    return out


def _flatten_ports(ssot: dict[str, Any]) -> list[list[Any]]:
    io_list = ssot.get("io_list") if isinstance(ssot.get("io_list"), dict) else {}
    rows: list[list[Any]] = []
    for iface in io_list.get("interfaces") or []:
        if not isinstance(iface, dict):
            continue
        domain = iface.get("clock") or "aclk"
        for port in iface.get("ports") or []:
            if isinstance(port, dict):
                rows.append([
                    port.get("name"),
                    port.get("width"),
                    port.get("direction"),
                    domain,
                    f"{iface.get('name', 'interface')}: {port.get('description', '')}",
                ])
    for clk in io_list.get("clock_domains") or []:
        if isinstance(clk, dict):
            for port in clk.get("ports") or []:
                if isinstance(port, dict):
                    rows.append([port.get("name"), port.get("width"), port.get("direction"), clk.get("name"), port.get("description")])
    for rst in io_list.get("resets") or []:
        if isinstance(rst, dict):
            for port in rst.get("ports") or []:
                if isinstance(port, dict):
                    rows.append([port.get("name"), port.get("width"), port.get("direction"), rst.get("sync_async"), port.get("description")])
    return rows


def _scenario_rows(ssot: dict[str, Any]) -> list[list[Any]]:
    tr = ssot.get("test_requirements") if isinstance(ssot.get("test_requirements"), dict) else {}
    rows: list[list[Any]] = []
    for sc in tr.get("scenarios") or []:
        if isinstance(sc, dict):
            rows.append([
                sc.get("id"),
                sc.get("name"),
                sc.get("stimulus"),
                sc.get("expected"),
                sc.get("checker"),
                sc.get("coverage"),
            ])
    return rows


def _render(ip: str, ssot: dict[str, Any]) -> str:
    top = ssot.get("top_module") if isinstance(ssot.get("top_module"), dict) else {}
    io_list = ssot.get("io_list") if isinstance(ssot.get("io_list"), dict) else {}
    registers = ssot.get("registers") if isinstance(ssot.get("registers"), dict) else {}
    memory = ssot.get("memory") if isinstance(ssot.get("memory"), dict) else {}
    interrupts = ssot.get("interrupts") if isinstance(ssot.get("interrupts"), dict) else {}
    timing = ssot.get("timing") if isinstance(ssot.get("timing"), dict) else {}
    function_model = ssot.get("function_model") if isinstance(ssot.get("function_model"), dict) else {}
    cycle_model = ssot.get("cycle_model") if isinstance(ssot.get("cycle_model"), dict) else {}
    quality = ssot.get("quality_gates") if isinstance(ssot.get("quality_gates"), dict) else {}

    lines: list[str] = [
        f"# {ip} - Requirements",
        "",
        "> Generated by `req-gen/scripts/emit_requirements_from_ssot.py` from the current SSOT for audit/recovery.",
        "> Normal production flow should capture this requirement ledger before SSOT authoring.",
        "",
        "## Module Info",
        f"- **Name**: {_text(top.get('name'), ip)}",
        f"- **Purpose**: {_text(top.get('description'))}",
        f"- **Type**: {_text(top.get('type'))}",
        f"- **Target clock**: {_text((top.get('target') or {}).get('clock_freq_mhz') if isinstance(top.get('target'), dict) else None)} MHz",
        f"- **Source SSOT**: `{ip}/yaml/{ip}.ssot.yaml`",
        "",
        "## Interface Requirements",
        "",
        "### Clock And Reset",
    ]
    lines.extend(_table(
        ["Signal", "Type", "Frequency / Policy", "Description"],
        [
            [clk.get("name"), "clock", clk.get("frequency_mhz"), clk.get("description")]
            for clk in (io_list.get("clock_domains") or [])
            if isinstance(clk, dict)
        ] + [
            [rst.get("name"), "reset", f"{rst.get('polarity')} / {rst.get('sync_async')}", rst.get("description")]
            for rst in (io_list.get("resets") or [])
            if isinstance(rst, dict)
        ],
    ))
    lines.extend(["", "### Ports"])
    lines.extend(_table(["Name", "Width", "Dir", "Domain", "Description"], _flatten_ports(ssot)))
    lines.extend(["", "### Parameters"])
    lines.extend(_table(
        ["Name", "Default", "Type", "Description"],
        [[p.get("name"), p.get("default"), p.get("type"), p.get("description")] for p in ssot.get("parameters") or [] if isinstance(p, dict)],
    ))

    lines.extend(["", "## Functional Requirements", "", "### Features"])
    lines.extend(_bullets(ssot.get("features"), "output"))
    lines.extend(["", "### Function Model Contract"])
    lines.append(f"- **Purpose**: {_text(function_model.get('purpose'))}")
    lines.extend(_table(
        ["ID", "Transaction", "Preconditions", "Inputs", "Outputs", "Side Effects", "Errors"],
        [
            [
                tx.get("id"),
                tx.get("name"),
                "; ".join(map(str, tx.get("preconditions") or [])),
                "; ".join(map(str, tx.get("inputs") or [])),
                "; ".join(map(str, tx.get("outputs") or [])),
                "; ".join(map(str, tx.get("side_effects") or [])),
                "; ".join(_text(e.get("condition")) + " -> " + _text(e.get("result")) for e in (tx.get("error_cases") or []) if isinstance(e, dict)),
            ]
            for tx in (function_model.get("transactions") or [])
            if isinstance(tx, dict)
        ],
    ))
    lines.extend(["", "### Cycle Model Contract"])
    lines.append(f"- **Clock**: {_text(cycle_model.get('clock'))}")
    lines.append(f"- **Reset**: {_text(cycle_model.get('reset'))}")
    lines.extend(_bullets(cycle_model.get("handshake_rules")))
    lines.extend(["", "### Pipeline / Ordering"])
    lines.extend(_bullets(cycle_model.get("pipeline")))
    lines.extend(_bullets(cycle_model.get("ordering")))

    lines.extend(["", "## Register Map"])
    lines.append(f"- **Policy**: {_text(registers.get('policy'))}")
    lines.extend(_table(
        ["Name", "Offset", "Access", "Reset", "Description"],
        [[r.get("name"), r.get("offset"), r.get("access"), r.get("reset"), r.get("description")] for r in registers.get("register_list") or [] if isinstance(r, dict)],
    ))

    lines.extend(["", "## Memory Requirements"])
    lines.extend(_table(
        ["Instance", "Type", "Depth", "Width", "Mask", "Reset"],
        [[m.get("name"), m.get("type"), m.get("depth"), m.get("width"), m.get("write_mask"), m.get("reset")] for m in memory.get("instances") or [] if isinstance(m, dict)],
    ))
    lines.append(f"- **Addressing**: {_text(memory.get('addressing'))}")
    lines.append(f"- **Storage policy**: {_text(memory.get('storage_policy'))}")

    lines.extend(["", "## Interrupt Requirements"])
    lines.append(f"- **Present**: {_text(interrupts.get('present'))}")
    lines.extend(_bullets(interrupts.get("sources")))

    lines.extend(["", "## Timing Requirements"])
    lines.extend(_table(
        ["Clock", "MHz", "Period ns", "Uncertainty ns"],
        [[c.get("name"), c.get("frequency_mhz"), c.get("period_ns"), c.get("uncertainty_ns")] for c in timing.get("target_clocks") or [] if isinstance(c, dict)],
    ))
    lines.append(f"- **Latency budget**: {_text(timing.get('latency_budget'))}")

    lines.extend(["", "## DV Requirements", "", "### Test Scenarios"])
    lines.extend(_table(["ID", "Name", "Stimulus", "Expected", "Checker", "Coverage"], _scenario_rows(ssot)))
    tr = ssot.get("test_requirements") if isinstance(ssot.get("test_requirements"), dict) else {}
    lines.append(f"- **Scoreboard checks**: {_text(tr.get('scoreboard_checks'))}")
    lines.append(f"- **Coverage goals**: {_text(tr.get('coverage_goals'))}")

    lines.extend(["", "## Quality Gates"])
    for name, gate in quality.items():
        if isinstance(gate, dict):
            lines.append(f"- **{name}**: pass={_text(gate.get('pass'))}; evidence={_text(gate.get('evidence'))}")

    lines.extend([
        "",
        "## Traceability",
        f"- `function_model` transactions drive `model/functional_model.py` and cocotb scoreboard expected results.",
        f"- `cycle_model` handshake/pipeline rules drive RTL control, waveform checks, and protocol coverage.",
        f"- `test_requirements.scenarios` drive cocotb/pyuvm scenarios and functional coverage bins.",
        f"- `quality_gates` drive ATLAS `/api/progress?scope={ip}` signoff.",
        "",
        "## Open Items",
        "- None recorded in this generated ledger. Any new ambiguity must be captured here before SSOT or RTL changes.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ip")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    ip_dir = root / args.ip
    ssot = _load_ssot(ip_dir, args.ip)
    req_dir = ip_dir / "req"
    req_dir.mkdir(parents=True, exist_ok=True)
    out = req_dir / f"{args.ip}_requirements.md"
    content = _render(args.ip, ssot)
    out.write_text(content, encoding="utf-8")
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    print(f"[emit_requirements_from_ssot] wrote {out} at {stamp} bytes={out.stat().st_size}")
    return 0 if out.stat().st_size >= 1000 else 1


if __name__ == "__main__":
    raise SystemExit(main())
