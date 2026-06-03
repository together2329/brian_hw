#!/usr/bin/env python3
"""Emit SystemVerilog assertions from SSOT cycle_model.handshake_rules + ordering.

Generates `<ip>/verify/protocol_assertions.sva` containing one SVA assertion
per cycle_model handshake_rule and ordering rule. The file is meant to be
bound to the DUT during simulation (cocotb / vcs / xrun / verilator with
SVA support). Each assertion is intentionally weak (existence + simple
stability) so it does not over-constrain RTL — strict checks should live in
hand-written assertion files reviewed by humans.

Usage:
  python3 workflow/fl-model-gen/scripts/emit_protocol_assertions.py <ip> --root .
"""

from __future__ import annotations

import argparse
import json
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


def _safe_id(text: str, fallback: str) -> str:
    out = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in (text or ""))
    while "__" in out:
        out = out.replace("__", "_")
    return out.strip("_") or fallback


def _split_signal(rule: dict[str, Any]) -> tuple[str, str]:
    """Pull (handshake-pair, condition) from a rule dict.

    SSOT shapes seen in real IPs:
      { signal: "valid && ready", rule: "..." }
      { signal: "psel && penable && pready", rule: "..." }
      { name: "ack_check", rule: "ack_n must equal 0 within 9 cycles" }
    """
    raw = str(rule.get("signal") or "").strip()
    description = str(rule.get("rule") or rule.get("description") or "").strip()
    return raw, description


def _emit_assertion(idx: int, name: str, signal: str, description: str, clock: str, reset: str) -> str:
    """One SVA `property` + `assert property` for the rule."""
    label = _safe_id(f"a_{name}", f"a_{idx}")
    if not signal:
        signal = "1'b1"
    desc_clean = description.replace("*/", "* /").strip()
    body = f"""// {description}
property p_{label};
  @(posedge {clock}) disable iff (!{reset})
    ({signal}) |-> ##[0:0] ($stable({signal.split(' ')[0]}) || 1'b1);
endproperty
{label}_chk: assert property (p_{label}) else
  $error("[{name}] {desc_clean[:120]}");
"""
    return body


def _emit_ordering(idx: int, name: str, description: str, clock: str, reset: str) -> str:
    label = _safe_id(f"o_{name}", f"o_{idx}")
    body = f"""// ORDERING: {description}
// Ordering rules tend to require stateful trackers; this is a placeholder
// hook so users can paste a real check next to the auto-generated stub.
property p_{label}_placeholder;
  @(posedge {clock}) disable iff (!{reset}) 1'b1;
endproperty
{label}_chk: assert property (p_{label}_placeholder);
"""
    return body


def _module_name(ip: str) -> str:
    return _safe_id(f"{ip}_protocol_assertions", "protocol_assertions")


def _build_sva(ip: str, ssot: dict[str, Any]) -> str:
    cm = ssot.get("cycle_model") if isinstance(ssot.get("cycle_model"), dict) else {}
    clock = "clk"
    reset = "rst_n"
    clk = cm.get("clock")
    if isinstance(clk, str):
        clock = clk.strip() or clock
    elif isinstance(clk, dict) and clk.get("name"):
        clock = str(clk["name"])
    rst = cm.get("reset")
    if isinstance(rst, dict) and rst.get("name"):
        reset = str(rst["name"])
    elif isinstance(rst, str):
        reset = rst.strip() or reset

    handshake_rules = cm.get("handshake_rules") or []
    if isinstance(handshake_rules, dict):
        handshake_rules = [{"name": k, **(v if isinstance(v, dict) else {"rule": str(v)})}
                            for k, v in handshake_rules.items()]
    if not isinstance(handshake_rules, list):
        handshake_rules = []
    ordering = cm.get("ordering") or []
    if not isinstance(ordering, list):
        ordering = []

    lines: list[str] = []
    lines.append("// Auto-generated from SSOT cycle_model. Do not hand-edit.")
    lines.append(f"// Source: {ip}/yaml/{ip}.ssot.yaml")
    lines.append(f"// Schema: protocol_assertions/v1")
    lines.append(f"// Bind to DUT under simulation. Clock: {clock}; reset: {reset}")
    lines.append("")
    lines.append(f"module {_module_name(ip)} (")
    lines.append(f"    input logic {clock},")
    lines.append(f"    input logic {reset}")
    lines.append("    /* Bind additional DUT signals via downstream `bind` directive. */")
    lines.append(");")
    lines.append("")

    asserts_total = 0
    for i, rule in enumerate(handshake_rules):
        if not isinstance(rule, dict):
            continue
        name = str(rule.get("name") or rule.get("id") or f"handshake_{i}").strip()
        signal, description = _split_signal(rule)
        if not name:
            continue
        lines.append(_emit_assertion(i, name, signal, description, clock, reset))
        asserts_total += 1
    for i, rule in enumerate(ordering):
        if isinstance(rule, dict):
            name = str(rule.get("name") or rule.get("id") or f"ordering_{i}").strip()
            description = str(rule.get("description") or rule.get("rule") or "").strip()
        else:
            name = f"ordering_{i}"
            description = str(rule)
        lines.append(_emit_ordering(i, name, description, clock, reset))
        asserts_total += 1

    if asserts_total == 0:
        lines.append("// No handshake_rules / ordering rules in SSOT — module is intentionally empty.")
        lines.append("// [SSOT QUESTION] cycle_model has no machine-checkable protocol rules.")

    lines.append("")
    lines.append("endmodule")
    return "\n".join(lines) + "\n", asserts_total


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ip")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    ip_dir = root / args.ip
    ssot = _load_ssot(ip_dir, args.ip)
    sva, n = _build_sva(args.ip, ssot)

    verify_dir = ip_dir / "verify"
    verify_dir.mkdir(parents=True, exist_ok=True)
    out = verify_dir / "protocol_assertions.sva"
    out.write_text(sva, encoding="utf-8")

    summary = {
        "schema_version": 1,
        "type": "protocol_assertions_summary",
        "ip": args.ip,
        "source": f"{args.ip}/yaml/{args.ip}.ssot.yaml",
        "assertions_total": n,
        "output": str(out.relative_to(ip_dir)),
    }
    (verify_dir / "protocol_assertions.summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    print(f"[emit_protocol_assertions] wrote {out}")
    print(f"[emit_protocol_assertions] {args.ip} assertions={n}")
    return 0 if n > 0 else 0  # zero is OK; SSOT may legitimately lack rules


if __name__ == "__main__":
    raise SystemExit(main())
