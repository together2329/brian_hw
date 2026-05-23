#!/usr/bin/env python3
"""Extract a rich architecture/block-diagram spec from an SSOT YAML.

Emits JSON consumed by interactive_ui/architecture-diagram.html: interfaces +
ports, internal blocks (decomposition units mapped onto cycle_model pipeline
stages), the register bit-field map, dataflow paths with bit-widths, the
behavioral contract (function_model transactions + output rules), latency, and
the clock/reset domain.

Usage:
  ssot_to_archspec.py atlas_flow_gpio_demo/yaml/atlas_flow_gpio_demo.ssot.yaml
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


def map_blocks(ssot):
    """Decomposition units, each tagged with a matching cycle_model pipeline stage."""
    units = (ssot.get("decomposition") or {}).get("units", []) or []
    stages = (ssot.get("cycle_model") or {}).get("pipeline", []) or []
    # control unit -> earliest (decode) stage; datapath -> later (update) stage.
    by_kind = {}
    if stages:
        by_kind["control"] = stages[0]
        by_kind["datapath"] = stages[-1]
    blocks = []
    for i, u in enumerate(units):
        stage = by_kind.get(u.get("kind")) or (stages[min(i, len(stages) - 1)] if stages else {})
        blocks.append({
            "id": u.get("id"),
            "kind": u.get("kind"),
            "stage": stage.get("stage"),
            "cycle": stage.get("cycle"),
            "action": stage.get("action"),
            "source_refs": u.get("source_refs", []),
        })
    return blocks


def map_registers(ssot):
    out = []
    for r in (ssot.get("registers") or {}).get("register_list", []) or []:
        fields = []
        for f in r.get("fields", []) or []:
            bits = f.get("bits", [0, 0])
            fields.append({
                "name": f.get("name"),
                "msb": bits[0], "lsb": bits[1],
                "access": f.get("access"),
                "reset": f.get("reset"),
                "effect": f.get("write_effect"),
                "desc": f.get("description"),
            })
        out.append({
            "name": r.get("name"),
            "offset": as_hex(r.get("offset", 0)),
            "width": r.get("width"),
            "access": r.get("access"),
            "reset": r.get("reset"),
            "desc": r.get("description"),
            "write_side_effects": r.get("write_side_effects", []),
            "fields": fields,
        })
    return out


def port_width(ssot, port_name):
    for iface in (ssot.get("io_list") or {}).get("interfaces", []) or []:
        for p in iface.get("ports", []) or []:
            if p.get("name", "").lower() == port_name.lower():
                return p.get("width")
    return None


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

    interfaces = []
    for iface in (ssot.get("io_list") or {}).get("interfaces", []) or []:
        ports = iface.get("ports") or iface.get("signals") or []
        if not ports:
            continue
        interfaces.append({
            "name": iface.get("name"),
            "type": iface.get("type"),
            "role": iface.get("role"),
            "ports": [{"name": p.get("name"), "width": p.get("width"), "dir": p.get("direction")} for p in ports],
        })

    dataflow = []
    for d in (ssot.get("dataflow") or {}).get("sequence", []) or []:
        src, snk = d.get("source", ""), d.get("sink", "")
        dataflow.append({
            "source": src, "sink": snk, "path": d.get("path"),
            "width_in": port_width(ssot, src), "width_out": port_width(ssot, snk),
        })

    transactions = []
    for t in fm.get("transactions", []) or []:
        transactions.append({
            "id": t.get("id"), "name": t.get("name"),
            "preconditions": t.get("preconditions", []),
            "inputs": t.get("inputs", []),
            "outputs": t.get("outputs", []),
            "output_rules": [{"port": r.get("port"), "expr": r.get("expr"), "width": r.get("width"),
                              "desc": r.get("description")} for r in t.get("output_rules", []) or []],
        })

    spec = {
        "top": top.get("name"),
        "description": top.get("description"),
        "clock_reset": {
            "clock": dom.get("name"), "freq_mhz": dom.get("frequency_mhz"),
            "reset": rst.get("signal"), "reset_polarity": rst.get("polarity"),
            "reset_type": rst.get("type"),
        },
        "interfaces": interfaces,
        "blocks": map_blocks(ssot),
        "registers": map_registers(ssot),
        "dataflow": dataflow,
        "transactions": transactions,
        "latency": cyc.get("latency", {}),
    }
    print(json.dumps(spec, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
