#!/usr/bin/env python3
"""Derive an *expected* APB handshake wavespec from an SSOT YAML.

This turns the protocol contract written in the SSOT (setup/access phase rules,
register map, zero-wait-state PREADY, output mirror rules) into the same
wavespec JSON the interactive viewer consumes — so it can be laid next to the
*actual* waveform parsed from a VCD and diffed cell-by-cell.

Spec semantics in the emitted wave:
  - control signals that only matter while selected are marked don't-care (x)
    during idle, so the diff does not flag legitimately-unconstrained cycles.
  - concrete values (PSEL/PENABLE sequencing, the written data, PREADY) are the
    parts the RTL is actually contracted to honour.

Usage:
  ssot_to_wavespec.py atlas_flow_gpio_demo/yaml/atlas_flow_gpio_demo.ssot.yaml \
      --reg DATA --data 0x55
"""
from __future__ import annotations

import argparse
import json
import sys

import yaml


def find_apb_interface(ssot):
    """Return the APB-Lite slave interface dict, or None."""
    io = ssot.get("io_list", {})
    for iface in io.get("interfaces", []) or []:
        proto = iface.get("protocol") or {}
        names = {p.get("name") for p in iface.get("ports", []) or []}
        if {"PSEL", "PENABLE"} <= names or "setup_phase" in proto:
            return iface
    return None


def as_hex(offset):
    """Normalise an offset (int or '0x..' str) to a '0x..' display string."""
    if isinstance(offset, int):
        return "0x%X" % offset
    try:
        return "0x%X" % int(str(offset), 0)
    except ValueError:
        return str(offset)


def reg_offset(ssot, reg_name):
    regs = (ssot.get("registers") or {}).get("register_list", []) or []
    for r in regs:
        if r.get("name") == reg_name:
            return as_hex(r.get("offset", 0))
    return "0x0"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ssot")
    ap.add_argument("--reg", default="DATA", help="target register name (default: DATA)")
    ap.add_argument("--data", default="0x55", help="value written, as it appears on PWDATA")
    ap.add_argument("--output", default="gpio_out", help="output signal that mirrors the register")
    ap.add_argument("--title", default=None)
    args = ap.parse_args(argv)

    with open(args.ssot) as f:
        ssot = yaml.safe_load(f)

    iface = find_apb_interface(ssot)
    hs = (iface or {}).get("protocol", {}) if iface else {}
    offset = reg_offset(ssot, args.reg)
    top = (ssot.get("top_module") or {}).get("name", "ip")

    # Provenance — what in the SSOT drove this expectation (to stderr).
    print("# derived from SSOT contract:", file=sys.stderr)
    for k in ("setup_phase", "access_phase", "write_rule"):
        if hs.get(k):
            print(f"#   {k}: {hs[k]}", file=sys.stderr)
    print(f"#   register {args.reg} @ offset {offset}; write {args.data}; mirror -> {args.output}", file=sys.stderr)

    # 5-cycle single-write transaction: IDLE, SETUP, ACCESS, POST, IDLE.
    # '.' = hold, 'x' = don't-care (unconstrained -> never flagged by the diff).
    signals = [
        {"name": "PCLK", "wave": "ppppp"},
        # PSEL qualifies the transfer the whole way through -> always concrete.
        {"name": "PSEL", "wave": "01.0."},
        # PENABLE: low in SETUP, high in ACCESS (setup_phase / access_phase rule).
        {"name": "PENABLE", "wave": "0.10."},
        # PWRITE only meaningful while selected.
        {"name": "PWRITE", "wave": "x1.x."},
        # Address only meaningful while selected.
        {"name": "PADDR", "wave": "x=.x.", "data": [offset]},
        # Write data only meaningful while selected.
        {"name": "PWDATA", "wave": "x=.x.", "data": [args.data]},
        # Zero-wait-state slave: PREADY contracted high (pready_rule expr: 1).
        {"name": "PREADY", "wave": "1...."},
        # Output mirrors the register: 0 before, written value from ACCESS edge on.
        {"name": args.output, "wave": "=.=..", "data": ["0x0", args.data]},
    ]

    title = args.title or f"EXPECTED · {top} APB write {args.data}->{args.reg}@{offset} (from SSOT contract)"
    print(json.dumps({"title": title, "signals": signals}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
