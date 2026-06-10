#!/usr/bin/env python3
"""Emit Python constants from SSOT.timing_constraints for cocotb TB.

Produces <ip>/tb/cocotb/<ip>_timing.py so all cocotb sequences and
agents can `from <ip>_timing import T_CS_SETUP_NS, ...` instead of
hard-coding cycle counts. Removes the magic-number trap that lets a
TB silently encode an RTL bug into its waveform.

Source of truth: <ip>/yaml/<ip>.ssot.yaml.timing_constraints
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml


def _load_ssot(ip_dir: Path, ip: str) -> dict[str, Any]:
    path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    if not path.is_file():
        raise SystemExit(f"missing SSOT YAML: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _to_constant_name(key: str) -> str:
    """T_CS_setup -> T_CS_SETUP_NS (already _ns suffix preserved)."""
    name = key.upper()
    if not name.endswith("_NS") and not name.endswith("_CYCLES"):
        # If field is dict with min_ns key only, name keeps base form.
        pass
    return name


def _extract_value(field: Any) -> tuple[str, Any]:
    """Return (suffix, value) from a timing budget entry.

    Accepts:
      {min_ns: 100, ...}        -> ('_NS', 100)
      {max_cycles: 4, ...}      -> ('_CYCLES', 4)
      {min_ns: 100, max_ns: 200} -> ('_NS', 100)   (min wins)
    """
    if not isinstance(field, dict):
        return ("", field)
    for k in ("min_ns", "max_ns", "max_cycles", "min_cycles", "value"):
        if k in field and field[k] is not None:
            suffix = "_CYCLES" if "cycles" in k else "_NS"
            return (suffix, field[k])
    return ("", None)


def emit(ip: str, root: Path) -> Path:
    ip_dir = root / ip
    ssot = _load_ssot(ip_dir, ip)
    tc = ssot.get("timing_constraints")
    if not isinstance(tc, dict) or not tc:
        raise SystemExit(
            f"{ip}/yaml/{ip}.ssot.yaml has no timing_constraints. "
            "Run /ssot-interview to populate it before TB generation."
        )

    out_path = ip_dir / "tb" / "cocotb" / f"{ip}_timing.py"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append('"""AUTO-GENERATED from SSOT.timing_constraints. Do not edit.')
    lines.append("")
    lines.append(f"Source: {ip}/yaml/{ip}.ssot.yaml")
    lines.append(f"Generator: workflow/tb-gen/scripts/emit_timing_header.py")
    lines.append('"""')
    lines.append("")

    n_emitted = 0
    for key, value in tc.items():
        if key == "rationale":
            continue
        if not isinstance(value, dict):
            continue
        suffix, raw = _extract_value(value)
        if raw is None:
            continue
        const_name = _to_constant_name(key)
        # If the SSOT key already ends in _ns / _cycles we don't double-suffix.
        if not const_name.endswith(("_NS", "_CYCLES")):
            const_name = const_name + suffix
        descr = (value.get("description") or "").strip().splitlines()[0] if value.get("description") else ""
        if descr:
            lines.append(f"# {descr}")
        lines.append(f"{const_name} = {int(raw)}")
        lines.append("")
        n_emitted += 1

    lines.append("# Convenience: standard SPI / sys clock periods (kept as constants")
    lines.append("# so cocotb stops sourcing them from raw integers).")
    # Pull from io_list.clock_domains if present.
    io = ssot.get("io_list") or {}
    for cd in (io.get("clock_domains") or []):
        if not isinstance(cd, dict):
            continue
        name = cd.get("name", "").upper()
        freq = cd.get("frequency_mhz")
        if name and freq:
            period_ns = int(round(1000.0 / float(freq)))
            lines.append(f"{name}_PERIOD_NS = {period_ns}  # {freq} MHz")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("ip", help="IP directory name")
    p.add_argument("--root", default=".", help="project root")
    args = p.parse_args()

    out = emit(args.ip, Path(args.root).resolve())
    print(f"[emit_timing_header] wrote {out.relative_to(Path(args.root).resolve())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
