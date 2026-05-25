#!/usr/bin/env python3
"""Consolidate the key SSOT sections into ONE JSON for the SSOT explorer page.

interactive_ui/ssot-explorer.html embeds this and renders every section
(overview, block diagram, register map, function model, cycle model, FSM, and an
expected APB-write timing waveform) in a single navigable interactive document.

Usage:
  ssot_to_explorer.py atlas_flow_gpio_demo/yaml/atlas_flow_gpio_demo.ssot.yaml
"""
from __future__ import annotations

import argparse
import json
import sys

import yaml


def as_hex(v):
    if isinstance(v, int):
        return "0x%X" % v
    try:
        return "0x%X" % int(str(v), 0)
    except (ValueError, TypeError):
        return str(v)


def interfaces(ssot):
    out = []
    for iface in (ssot.get("io_list") or {}).get("interfaces", []) or []:
        ports = iface.get("ports") or iface.get("signals") or []
        if not ports:
            continue
        out.append({
            "name": iface.get("name"), "type": iface.get("type"), "role": iface.get("role"),
            "protocol": iface.get("protocol"),
            "ports": [{"name": p.get("name"), "width": p.get("width"), "dir": p.get("direction"),
                       "desc": p.get("description")} for p in ports],
        })
    return out


def blocks(ssot):
    units = (ssot.get("decomposition") or {}).get("units", []) or []
    stages = (ssot.get("cycle_model") or {}).get("pipeline", []) or []
    by_kind = {"control": stages[0], "datapath": stages[-1]} if stages else {}
    out = []
    for i, u in enumerate(units):
        st = by_kind.get(u.get("kind")) or (stages[min(i, len(stages) - 1)] if stages else {})
        out.append({"id": u.get("id"), "kind": u.get("kind"), "stage": st.get("stage"),
                    "cycle": st.get("cycle"), "action": st.get("action"),
                    "source_refs": u.get("source_refs", [])})
    return out


def registers(ssot):
    regs = ssot.get("registers") or {}
    out = []
    for r in regs.get("register_list", []) or []:
        fields = [{"name": f.get("name"), "msb": f.get("bits", [0, 0])[0], "lsb": f.get("bits", [0, 0])[1],
                   "access": f.get("access"), "reset": f.get("reset"),
                   "effect": f.get("write_effect"), "desc": f.get("description")}
                  for f in r.get("fields", []) or []]
        out.append({"name": r.get("name"), "offset": as_hex(r.get("offset", 0)), "width": r.get("width"),
                    "access": r.get("access"), "reset": r.get("reset"), "category": r.get("category"),
                    "desc": r.get("description"), "write_side_effects": r.get("write_side_effects", []),
                    "fields": fields})
    return {"config": regs.get("config"), "bit_order": regs.get("bit_order"), "register_list": out}


def expected_timing(ssot, reg=None, data="0x1"):
    """IP-agnostic expected APB(4) single-write waveform from the register map."""
    regs = (ssot.get("registers") or {}).get("register_list", []) or []
    target = None
    if reg:
        target = next((r for r in regs if r.get("name") == reg), None)
    if target is None:
        target = next((r for r in regs if (r.get("access") or "").lower() in ("rw", "wo", "w")), None)
    if target is None and regs:
        target = regs[0]
    name = target.get("name") if target else "REG"
    offset = as_hex(target.get("offset", 0)) if target else "0x0"
    return {
        "title": f"EXPECTED · APB write {data} → {name} @ {offset}",
        "note": "Setup phase (PSEL=1, PENABLE=0) then access phase (PENABLE=1); zero-wait PREADY (illustrative).",
        "signals": [
            {"name": "PCLK", "wave": "ppppp"},
            {"name": "PSEL", "wave": "01.0."},
            {"name": "PENABLE", "wave": "0.10."},
            {"name": "PWRITE", "wave": "x1.x."},
            {"name": "PADDR", "wave": "x=.x.", "data": [offset]},
            {"name": "PWDATA", "wave": "x=.x.", "data": [data]},
            {"name": "PREADY", "wave": "1...."},
        ],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ssot")
    args = ap.parse_args(argv)

    with open(args.ssot) as f:
        ssot = yaml.safe_load(f)

    top = ssot.get("top_module") or {}
    crd = ssot.get("clock_reset_domains") or {}
    dom = (crd.get("domains") or [{}])[0]
    rst = crd.get("reset_scheme") or {}
    fm = ssot.get("function_model") or {}
    cyc = ssot.get("cycle_model") or {}

    spec = {
        "overview": {
            "name": top.get("name"), "type": top.get("type"), "version": top.get("version"),
            "description": top.get("description"), "target": top.get("target"),
        },
        "clock_reset": {
            "clock": dom.get("name"), "freq_mhz": dom.get("frequency_mhz"),
            "reset": rst.get("signal"), "reset_polarity": rst.get("polarity"), "reset_type": rst.get("type"),
        },
        "features": ssot.get("features", []),
        "parameters": ssot.get("parameters", []),
        "interrupts": ssot.get("interrupts", {}),
        "interfaces": interfaces(ssot),
        "blocks": blocks(ssot),
        "dataflow": (ssot.get("dataflow") or {}).get("sequence", []),
        "registers": registers(ssot),
        "function_model": {
            "purpose": fm.get("purpose"),
            "state_variables": fm.get("state_variables", []),
            "transactions": fm.get("transactions", []),
            "invariants": fm.get("invariants", []),
        },
        "cycle_model": {
            "purpose": cyc.get("purpose"), "clock": cyc.get("clock"), "reset": cyc.get("reset"),
            "latency": cyc.get("latency"), "handshake_rules": cyc.get("handshake_rules"),
            "pipeline": cyc.get("pipeline"), "ordering": cyc.get("ordering"),
        },
        "fsm": ssot.get("fsm", {}),
        "timing_expected": expected_timing(ssot),
    }
    print(json.dumps(spec, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
