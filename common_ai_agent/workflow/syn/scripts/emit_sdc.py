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


def emit(ip: str, root: Path) -> Path:
    ip_dir = root / ip
    ssot = _load_ssot(ip_dir, ip)

    clocks = _collect_clock_ports(ssot)
    if not clocks:
        raise SystemExit(f"no clock domains found in {ip}.ssot.yaml.io_list.clock_domains")

    tc = ssot.get("timing_constraints") or {}
    syn = ssot.get("synthesis") or {}

    # Pull SDC-relevant timing budgets
    t_mosi_setup = (tc.get("T_MOSI_setup_ns") or {}).get("min_ns", 5)
    t_miso_hold  = (tc.get("T_MISO_hold_ns") or {}).get("min_ns", 5)

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

    # ── Async clock groups (false-path between sys/spi) ──
    if len(clocks) >= 2:
        lines.append("# =========================================================")
        lines.append("# Asynchronous clock groups — sys_clk and spi_clk are")
        lines.append("# physically independent (CDC handled by spi_cdc_sync).")
        lines.append("# =========================================================")
        groups = " ".join(f"-group {{{c['domain']}}}" for c in clocks)
        lines.append(f"set_clock_groups -asynchronous {groups}")
        lines.append("")

    # ── Input delays (AXI4-Lite + SPI MOSI) ──
    lines.append("# =========================================================")
    lines.append("# Input delays")
    lines.append("# =========================================================")
    sys_clk = next((c for c in clocks if "sys" in (c.get("domain", "").lower())), clocks[0])
    spi_clk = next((c for c in clocks if "spi" in (c.get("domain", "").lower())), clocks[-1])

    # AXI4-Lite inputs — relative to sys_clk
    axi_input_ports = []
    for p in _ports_of_interface(ssot, "axi_lite_slave"):
        if p.get("direction") == "input":
            axi_input_ports.append(p["name"])
    if axi_input_ports:
        # Use 30% of period as conservative input delay
        ax_delay = round(sys_clk["period_ns"] * 0.3, 2)
        ports_list = " ".join(axi_input_ports)
        lines.append(f"# AXI4-Lite inputs — relative to {sys_clk['domain']}")
        lines.append(f"set_input_delay -clock {sys_clk['domain']} {ax_delay} [get_ports {{{ports_list}}}]")
    lines.append("")

    # SPI inputs — relative to spi_clk, MOSI setup from SSOT
    spi_input_ports = []
    for p in _ports_of_interface(ssot, "spi_slave"):
        if p.get("direction") == "input" and p.get("name") not in (spi_clk.get("port"),):
            spi_input_ports.append(p["name"])
    if spi_input_ports:
        ports_list = " ".join(spi_input_ports)
        lines.append(f"# SPI inputs (MOSI, CS) — relative to {spi_clk['domain']}")
        lines.append(f"# T_MOSI_setup_ns = {t_mosi_setup} from SSOT.timing_constraints")
        lines.append(f"set_input_delay -clock {spi_clk['domain']} -max {t_mosi_setup} [get_ports {{{ports_list}}}]")
    lines.append("")

    # ── Output delays ──
    lines.append("# =========================================================")
    lines.append("# Output delays")
    lines.append("# =========================================================")
    axi_output_ports = []
    for p in _ports_of_interface(ssot, "axi_lite_slave"):
        if p.get("direction") == "output":
            axi_output_ports.append(p["name"])
    if axi_output_ports:
        ax_out_delay = round(sys_clk["period_ns"] * 0.4, 2)
        ports_list = " ".join(axi_output_ports)
        lines.append(f"# AXI4-Lite outputs — relative to {sys_clk['domain']}")
        lines.append(f"set_output_delay -clock {sys_clk['domain']} {ax_out_delay} [get_ports {{{ports_list}}}]")

    spi_output_ports = []
    for p in _ports_of_interface(ssot, "spi_slave"):
        if p.get("direction") == "output":
            spi_output_ports.append(p["name"])
    if spi_output_ports:
        ports_list = " ".join(spi_output_ports)
        lines.append(f"# SPI outputs (MISO, MISO_OE) — relative to {spi_clk['domain']}")
        lines.append(f"# T_MISO_hold_ns = {t_miso_hold} from SSOT.timing_constraints")
        lines.append(f"set_output_delay -clock {spi_clk['domain']} -min {t_miso_hold} [get_ports {{{ports_list}}}]")
    # Interrupt
    lines.append(f"set_output_delay -clock {sys_clk['domain']} {round(sys_clk['period_ns'] * 0.4, 2)} [get_ports spi_irq_o]")
    lines.append("")

    # ── Async resets — false path ──
    lines.append("# =========================================================")
    lines.append("# Reset paths (async assert, sync deassert)")
    lines.append("# =========================================================")
    lines.append("set_false_path -from [get_ports sys_resetn_i]")
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
