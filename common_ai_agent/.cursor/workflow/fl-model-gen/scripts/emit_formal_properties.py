#!/usr/bin/env python3
"""Emit SystemVerilog Assertions (SVA) from SSOT negative spec.

Reads:
  <ip>/yaml/<ip>.ssot.yaml.invariants[]            -> assert property
  <ip>/yaml/<ip>.ssot.yaml.forbidden_states[]      -> assert (!cond)
  <ip>/yaml/<ip>.ssot.yaml.forbidden_environment[] -> assume property

Writes:
  <ip>/verify/<ip>_assertions.sv

The output module is meant to be `bind`-instantiated against the DUT
top so a formal verifier (yosys-smtbmc, jaspergold, ...) or simulator
with assertion support can verify them.

Each invariant entry can carry a `formal_property: |` SVA-syntax block
that overrides the default heuristic. Otherwise we emit a placeholder
that prints the statement as a comment + a TODO assertion that the
RTL author can fill in.
"""

from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path
from typing import Any

import yaml


def _load_ssot(ip_dir: Path, ip: str) -> dict[str, Any]:
    path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    if not path.is_file():
        raise SystemExit(f"missing SSOT YAML: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _wrap_block_comment(text: str, indent: str = "    ") -> str:
    """Convert multi-line text into // comment lines."""
    out: list[str] = []
    for line in text.strip().splitlines():
        out.append(f"{indent}// {line}")
    return "\n".join(out)


def _heuristic_property_for_invariant(inv: dict[str, Any]) -> str:
    """Best-effort SVA template when invariant has no formal_property."""
    inv_id = inv.get("id", "I_UNNAMED")
    return textwrap.dedent(f"""\
        // {inv_id} — TODO: author-provided SVA placeholder.
        // Default placeholder asserts a constant true (no enforcement).
        // Edit the SSOT entry's `formal_property:` block to populate.
        property p_{inv_id};
            @(posedge sys_clk_i) disable iff (!sys_resetn_i)
            1'b1;
        endproperty
        a_{inv_id}: assert property (p_{inv_id})
            else $error("[FORMAL] {inv_id} violation");\
    """)


def _format_invariant(inv: dict[str, Any]) -> str:
    inv_id = inv.get("id", "I_UNNAMED")
    statement = inv.get("statement", "")
    formal = inv.get("formal_property")

    parts: list[str] = []
    parts.append(f"// =============================================================")
    parts.append(f"// {inv_id}")
    parts.append(f"// =============================================================")
    if statement:
        parts.append(_wrap_block_comment(statement))
    parts.append("")

    if formal:
        # SSOT-author SVA. Emit verbatim with minimal wrapper.
        parts.append("// Author-provided property:")
        parts.append(textwrap.indent(formal.strip(), ""))
    else:
        parts.append(_heuristic_property_for_invariant(inv))
    return "\n".join(parts)


def _format_forbidden_state(fs: dict[str, Any]) -> str:
    fs_id = fs.get("id", "F_UNNAMED")
    statement = fs.get("statement", "")
    return textwrap.dedent(f"""\
        // -------------------------------------------------------------
        // {fs_id} — forbidden internal state
        // {statement.strip()}
        // -------------------------------------------------------------
        // SVA template: replace `1'b0` with a boolean expression that
        // captures the forbidden condition; assertion fires when true.
        property p_{fs_id};
            @(posedge sys_clk_i) disable iff (!sys_resetn_i)
            !(1'b0 /* TODO: encode "{statement.replace(chr(34), "'")}" */);
        endproperty
        a_{fs_id}: assert property (p_{fs_id})
            else $error("[FORMAL] forbidden state {fs_id} reachable");\
    """)


def _format_forbidden_env(fe: dict[str, Any]) -> str:
    fe_id = fe.get("id", "E_UNNAMED")
    statement = fe.get("statement", "")
    # Forbidden environment maps to `assume property` so formal solvers
    # constrain the input space. TB still asserts at runtime.
    return textwrap.dedent(f"""\
        // -------------------------------------------------------------
        // {fe_id} — forbidden environment behavior (TB must respect)
        // {statement.strip()}
        // -------------------------------------------------------------
        property p_{fe_id};
            @(posedge sys_clk_i) disable iff (!sys_resetn_i)
            !(1'b0 /* TODO: encode "{statement.replace(chr(34), "'")}" */);
        endproperty
        m_{fe_id}: assume property (p_{fe_id});\
    """)


def emit(ip: str, root: Path) -> Path:
    ip_dir = root / ip
    ssot = _load_ssot(ip_dir, ip)

    invariants = ssot.get("invariants") or []
    forbidden_states = ssot.get("forbidden_states") or []
    forbidden_env = ssot.get("forbidden_environment") or []

    if not (invariants or forbidden_states or forbidden_env):
        raise SystemExit(
            f"{ip}/yaml/{ip}.ssot.yaml has no invariants / forbidden_states / "
            "forbidden_environment. Nothing to emit."
        )

    out_path = ip_dir / "verify" / f"{ip}_assertions.sv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append("`default_nettype none")
    lines.append("")
    lines.append("// AUTO-GENERATED from SSOT negative spec. Do not edit.")
    lines.append(f"// Source: {ip}/yaml/{ip}.ssot.yaml")
    lines.append("// Generator: workflow/fl-model-gen/scripts/emit_formal_properties.py")
    lines.append("//")
    lines.append("// Bind this module to the DUT top via:")
    lines.append(f"//   bind {ssot.get('top_module', {}).get('name', ip)} "
                 f"{ip}_assertions u_{ip}_assertions (.*);")
    lines.append("")
    lines.append(f"module {ip}_assertions (")
    lines.append("    input wire sys_clk_i,")
    lines.append("    input wire sys_resetn_i")
    lines.append("    // (additional DUT signals: extend as authored properties require)")
    lines.append(");")
    lines.append("")

    if invariants:
        lines.append("    // ─── Invariants ─────────────────────────────────")
        for inv in invariants:
            if not isinstance(inv, dict):
                continue
            lines.append(textwrap.indent(_format_invariant(inv), "    "))
            lines.append("")

    if forbidden_states:
        lines.append("    // ─── Forbidden internal states ──────────────────")
        for fs in forbidden_states:
            if not isinstance(fs, dict):
                continue
            lines.append(textwrap.indent(_format_forbidden_state(fs), "    "))
            lines.append("")

    if forbidden_env:
        lines.append("    // ─── Forbidden environment behaviors ────────────")
        for fe in forbidden_env:
            if not isinstance(fe, dict):
                continue
            lines.append(textwrap.indent(_format_forbidden_env(fe), "    "))
            lines.append("")

    lines.append("endmodule")
    lines.append("")
    lines.append("`default_nettype wire")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("ip", help="IP directory name")
    p.add_argument("--root", default=".", help="project root")
    args = p.parse_args()

    out = emit(args.ip, Path(args.root).resolve())
    print(f"[emit_formal_properties] wrote {out.relative_to(Path(args.root).resolve())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
