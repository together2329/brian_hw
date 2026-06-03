#!/usr/bin/env python3
"""Emit SDC from SSOT timing + timing_constraints + synthesis sections.

Reads:
  <ip>/yaml/<ip>.ssot.yaml.timing.clock_targets[]
  <ip>/yaml/<ip>.ssot.yaml.timing_constraints.T_*
  <ip>/yaml/<ip>.ssot.yaml.synthesis.constraints[]
  <ip>/yaml/<ip>.ssot.yaml.io_list.interfaces[].ports[]

Writes:
  <ip>/sdc/<ip>.sdc

The SDC is consumed by OpenSTA, OpenROAD, or any STA flow that
follows the Synopsys Design Constraints standard.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


def _load_ssot(ip_dir: Path, ip: str) -> dict[str, Any]:
    p = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    if not p.is_file():
        raise SystemExit(f"missing SSOT YAML: {p}")
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def _collect_clock_ports(ssot: dict[str, Any]) -> list[dict[str, Any]]:
    """Return [{port_name, freq_mhz, period_ns, domain, description}, ...]."""
    out = []
    io = ssot.get("io_list") or {}
    domains = (ssot.get("timing") or {}).get("clock_targets") or []
    domain_freq = {d.get("domain"): d.get("target_freq_mhz") for d in domains if isinstance(d, dict)}
    for cd in (io.get("clock_domains") or []):
        if not isinstance(cd, dict):
            continue
        name = cd.get("name", "")
        freq = cd.get("frequency_mhz") or domain_freq.get(name) or 100.0
        period = round(1000.0 / float(freq), 3)
        for port in (cd.get("ports") or []):
            if isinstance(port, dict) and port.get("direction") == "input":
                out.append({
                    "port": port.get("name"),
                    "freq_mhz": freq,
                    "period_ns": period,
                    "domain": name,
                    "description": cd.get("description") or "",
                })
    return out


def _ports_of_interface(ssot: dict[str, Any], iface_name: str) -> list[dict[str, Any]]:
    io = ssot.get("io_list") or {}
    for iface in (io.get("interfaces") or []):
        if isinstance(iface, dict) and iface.get("name") == iface_name:
            return [p for p in (iface.get("ports") or []) if isinstance(p, dict)]
    return []


def _interface_clock(ssot: dict[str, Any], iface_name: str, clocks: list[dict[str, Any]]) -> dict[str, Any]:
    io = ssot.get("io_list") or {}
    for iface in (io.get("interfaces") or []):
        if not isinstance(iface, dict) or iface.get("name") != iface_name:
            continue
        domain = iface.get("clock_domain")
        for clock in clocks:
            if clock.get("domain") == domain:
                return clock
    return clocks[0]


def _reset_ports(ssot: dict[str, Any]) -> list[str]:
    ports: list[str] = []
    io = ssot.get("io_list") or {}
    for rst in (io.get("resets") or []):
        if not isinstance(rst, dict):
            continue
        for port in rst.get("ports") or []:
            if isinstance(port, dict) and port.get("name"):
                ports.append(str(port["name"]))
    return ports


def emit(ip: str, root: Path) -> Path:
    ip_dir = root / ip
    ssot = _load_ssot(ip_dir, ip)

    clocks = _collect_clock_ports(ssot)
    if not clocks:
        raise SystemExit(f"no clock domains found in {ip}.ssot.yaml.io_list.clock_domains")

    timing = ssot.get("timing") if isinstance(ssot.get("timing"), dict) else {}

    out_path = ip_dir / "sdc" / f"{ip}.sdc"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append(f"# AUTO-GENERATED from SSOT. Do not edit.")
    lines.append(f"# Source: {ip}/yaml/{ip}.ssot.yaml")
    lines.append(f"# Generator: workflow/syn/scripts/emit_sdc.py")
    lines.append(f"# SDC for OpenSTA / OpenROAD / generic STA flows.")
    lines.append("")

    # ── Clocks ──
    lines.append("# =========================================================")
    lines.append("# Clock definitions")
    lines.append("# =========================================================")
    for ck in clocks:
        port = ck["port"]
        period = ck["period_ns"]
        lines.append(f"# {ck['domain']} — {ck['description']}")
        lines.append(f"create_clock -name {ck['domain']} -period {period} [get_ports {port}]")
    lines.append("")

    # ── Clock relationships ──
    relationships = timing.get("clock_relationships") if isinstance(timing.get("clock_relationships"), list) else []
    sync_groups = [
        rel for rel in relationships
        if isinstance(rel, dict) and str(rel.get("type", "")).lower() in {"synchronous_ratio", "generated", "synchronous"}
    ]
    if sync_groups:
        lines.append("# =========================================================")
        lines.append("# Clock relationships")
        lines.append("# =========================================================")
        for rel in sync_groups:
            clocks_text = " ".join(str(c) for c in rel.get("clocks", []))
            ratio = rel.get("ratio", "")
            lines.append(f"# synchronous clocks: {clocks_text} ratio={ratio}")
        lines.append("")
    elif len(clocks) >= 2:
        lines.append("# =========================================================")
        lines.append("# Asynchronous clock groups")
        lines.append("# =========================================================")
        groups = " ".join(f"-group {{{c['domain']}}}" for c in clocks)
        lines.append(f"set_clock_groups -asynchronous {groups}")
        lines.append("")

    # ── Input delays ──
    lines.append("# =========================================================")
    lines.append("# Input delays")
    lines.append("# =========================================================")
    io_delays = timing.get("io_delays") if isinstance(timing.get("io_delays"), list) else []
    for item in io_delays:
        if not isinstance(item, dict) or not item.get("interface"):
            continue
        iface_name = str(item["interface"])
        clk = _interface_clock(ssot, iface_name, clocks)
        delay = item.get("input_delay_ns")
        input_ports = [
            str(p["name"]) for p in _ports_of_interface(ssot, iface_name)
            if p.get("direction") == "input" and p.get("name") not in {clk.get("port"), *(_reset_ports(ssot))}
        ]
        if delay is not None and input_ports:
            lines.append(f"# {iface_name} inputs — relative to {clk['domain']}")
            lines.append(f"set_input_delay -clock {clk['domain']} {delay} [get_ports {{{' '.join(input_ports)}}}]")
    lines.append("")

    # ── Output delays ──
    lines.append("# =========================================================")
    lines.append("# Output delays")
    lines.append("# =========================================================")
    for item in io_delays:
        if not isinstance(item, dict) or not item.get("interface"):
            continue
        iface_name = str(item["interface"])
        clk = _interface_clock(ssot, iface_name, clocks)
        delay = item.get("output_delay_ns")
        output_ports = [
            str(p["name"]) for p in _ports_of_interface(ssot, iface_name)
            if p.get("direction") == "output" and p.get("name")
        ]
        if delay is not None and output_ports:
            lines.append(f"# {iface_name} outputs — relative to {clk['domain']}")
            lines.append(f"set_output_delay -clock {clk['domain']} {delay} [get_ports {{{' '.join(output_ports)}}}]")
    lines.append("")

    # ── Async resets — false path ──
    lines.append("# =========================================================")
    lines.append("# Reset paths (async assert, sync deassert)")
    lines.append("# =========================================================")
    for port in _reset_ports(ssot):
        lines.append(f"set_false_path -from [get_ports {port}]")
    lines.append("")

    # ── Loose driving cell + capacitance defaults ──
    lines.append("# =========================================================")
    lines.append("# Driving cell / load defaults (override per technology)")
    lines.append("# =========================================================")
    lines.append("set_load 0.05 [all_outputs]")
    lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("ip")
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    out = emit(args.ip, Path(args.root).resolve())
    print(f"[emit_sdc] wrote {out.relative_to(Path(args.root).resolve())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
