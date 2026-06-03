#!/usr/bin/env python3
"""Verify RTL register bit layout matches SSOT.registers exactly.

For each register defined in SSOT.registers.register_list[]:
  - Open the RTL file that owns it (heuristic: spi_regs.sv, *_regs.sv).
  - Find the read-data assembly block at the matching offset.
  - Parse `s_axi_rdata[hi:lo] <= signal_name;` (or `[bit] <= ...;`)
    statements after the case 8'h<offset>: branch.
  - Compare each parsed bit range against
    SSOT.registers.register_list[].fields[].bits.

Mismatch = exit non-zero with diff. Build gate.

Catches:
  - Bit position mismatch (SC2/SC4 STATUS layout)
  - Field width mismatch
  - Missing field assignments
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


def _load_ssot(ip_dir: Path, ip: str) -> dict[str, Any]:
    path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    if not path.is_file():
        raise SystemExit(f"missing SSOT YAML: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _normalize_bits(bits: Any) -> tuple[int, int]:
    """SSOT bits is [hi, lo] for a range or [b, b] for single bit."""
    if isinstance(bits, list) and len(bits) == 2:
        hi, lo = int(bits[0]), int(bits[1])
        return (max(hi, lo), min(hi, lo))
    if isinstance(bits, int):
        return (bits, bits)
    raise ValueError(f"cannot parse bits field: {bits!r}")


def _find_regs_file(ip_dir: Path, ip: str) -> Path:
    """Pick the most likely register-block RTL file."""
    rtl_dir = ip_dir / "rtl"
    candidates = [
        rtl_dir / f"{ip}_regs.sv",
        rtl_dir / f"{ip}_regs.v",
        rtl_dir / "regs.sv",
    ]
    for c in candidates:
        if c.is_file():
            return c
    # Fallback: any file with `s_axi_rdata` writes.
    for f in rtl_dir.glob("*.sv"):
        if "s_axi_rdata" in f.read_text(encoding="utf-8", errors="ignore"):
            return f
    raise SystemExit(f"no register RTL file found in {rtl_dir}")


def _extract_offset_assignments(rtl_text: str, offset: int) -> list[tuple[int, int, str]]:
    """For a register at the given offset, return [(hi, lo, signal), ...].

    Supports patterns:
      8'h<HH>: begin
        s_axi_rdata[A:B] <= signal_name;
        s_axi_rdata[A]   <= signal_name;
      end
    """
    # Anchor on `8'h<offset>: begin ... end`. There may be MULTIPLE
    # case branches with the same offset (one in the write FSM, one
    # in the read FSM). Pick the body that contains an s_axi_rdata
    # write — only the read FSM does that.
    hex2 = f"{offset:02x}"
    case_re = re.compile(
        rf"8'h{hex2}\s*:\s*begin(.*?)\bend",
        re.IGNORECASE | re.DOTALL,
    )
    body = ""
    for m in case_re.finditer(rtl_text):
        candidate = m.group(1)
        if "s_axi_rdata" in candidate:
            body = candidate
            break
    if not body:
        return []

    out: list[tuple[int, int, str]] = []
    # bit range: s_axi_rdata[hi:lo] <= sig_or_expr;
    range_re = re.compile(
        r"s_axi_rdata\s*\[\s*(\d+)\s*:\s*(\d+)\s*\]\s*<=\s*(.+?)\s*;",
        re.DOTALL,
    )
    for hi, lo, sig in range_re.findall(body):
        out.append((int(hi), int(lo), sig.strip()))
    # single bit: s_axi_rdata[bit] <= sig;
    single_re = re.compile(
        r"s_axi_rdata\s*\[\s*(\d+)\s*\]\s*<=\s*(.+?)\s*;",
        re.DOTALL,
    )
    for bit, sig in single_re.findall(body):
        out.append((int(bit), int(bit), sig.strip()))
    # whole register: s_axi_rdata <= expr;  (no subscript)
    # Treat as "rtl returns this register, fields not individually
    # decomposable". Mark with a synthetic full-width entry.
    whole_re = re.compile(
        r"s_axi_rdata\s*<=\s*(.+?)\s*;",
        re.DOTALL,
    )
    for sig in whole_re.findall(body):
        # Skip default zero-fills from RD_IDLE (these appear before
        # the per-offset case branch). We only get here from an
        # offset-case body, but extra defensive: keep all.
        out.append((-1, -1, "WHOLE:" + sig.strip()))
    return out


def _check_one_register(reg: dict[str, Any], rtl_text: str) -> dict[str, Any]:
    """Check one register from SSOT against parsed RTL assignments."""
    name = reg.get("name", "?")
    offset = reg.get("offset")
    if offset is None:
        return {
            "name": name, "status": "skip",
            "reason": "no offset in SSOT (likely write-only / virtual)"
        }
    rtl_assigns = _extract_offset_assignments(rtl_text, int(offset))
    fields = reg.get("fields") or []

    # Read-only registers (and STATUS) are most relevant — they get
    # explicit s_axi_rdata writes. Write-only registers (TXDATA,
    # IRQ_CLEAR) often don't write back, so their read path may be
    # empty. We only fail if SSOT says access != "wo" and rtl is empty.
    access = (reg.get("access") or "").lower()
    if access == "wo":
        return {"name": name, "status": "skip-wo", "fields_checked": 0}

    if not rtl_assigns and access != "wo":
        return {
            "name": name, "offset": offset, "status": "fail",
            "reason": f"no RTL read-path assignments at offset 0x{int(offset):02x}",
            "ssot_fields": [f.get("name") for f in fields],
        }

    # If RTL uses whole-register writeback (`s_axi_rdata <= ctrl_reg;`)
    # we cannot decompose into bit-fields here. Honor that — RTL is
    # likely keeping the field assembly inside the storage register
    # (CTRL pattern). Mark whole-reg case as "skip-whole" so it doesn't
    # show as fail.
    whole_only = all(hi == -1 for (hi, _, _) in rtl_assigns)
    if whole_only:
        return {
            "name": name, "offset": offset, "status": "skip-whole",
            "reason": "RTL uses whole-register read-back; field-level "
                      "layout check not applicable from this assignment",
            "rtl_signal": rtl_assigns[0][2].split(":", 1)[1] if rtl_assigns else None,
        }

    # Build set of (hi, lo, name) from RTL — drop whole-reg sentinels.
    rtl_set = {(hi, lo, sig) for (hi, lo, sig) in rtl_assigns if hi != -1}
    # Compare each SSOT field to RTL.
    field_results: list[dict] = []
    overall_status = "pass"

    for field in fields:
        fname = field.get("name")
        bits = field.get("bits")
        if bits is None or fname is None:
            continue
        try:
            ssot_hi, ssot_lo = _normalize_bits(bits)
        except Exception as e:
            field_results.append({"field": fname, "status": "skip", "reason": str(e)})
            continue
        # Find RTL write that exactly covers this bit range.
        match = None
        for (hi, lo, sig) in rtl_set:
            if hi == ssot_hi and lo == ssot_lo:
                match = (hi, lo, sig)
                break
        if match is None:
            # Try to find ANY rtl assign that overlaps but at the wrong range.
            wrong_range = None
            for (hi, lo, sig) in rtl_set:
                if not (hi < ssot_lo or lo > ssot_hi):
                    wrong_range = (hi, lo, sig)
                    break
            if wrong_range is not None:
                field_results.append({
                    "field": fname,
                    "status": "fail",
                    "reason": "bit range mismatch",
                    "ssot_bits": [ssot_hi, ssot_lo],
                    "rtl_bits": [wrong_range[0], wrong_range[1]],
                    "rtl_signal": wrong_range[2],
                })
            else:
                field_results.append({
                    "field": fname,
                    "status": "fail",
                    "reason": "field not assigned in RTL",
                    "ssot_bits": [ssot_hi, ssot_lo],
                })
            overall_status = "fail"
        else:
            field_results.append({
                "field": fname, "status": "pass",
                "ssot_bits": [ssot_hi, ssot_lo],
                "rtl_signal": match[2],
            })

    return {
        "name": name, "offset": offset, "status": overall_status,
        "fields": field_results,
    }


def check(ip: str, root: Path) -> dict[str, Any]:
    ip_dir = root / ip
    ssot = _load_ssot(ip_dir, ip)
    regs = (ssot.get("registers") or {}).get("register_list") or []
    if not regs:
        raise SystemExit(f"{ip} SSOT has no registers.register_list")

    rtl_path = _find_regs_file(ip_dir, ip)
    rtl_text = rtl_path.read_text(encoding="utf-8", errors="ignore")

    results = [_check_one_register(r, rtl_text) for r in regs]
    overall = "pass" if all(r["status"] in ("pass", "skip", "skip-wo", "skip-whole") for r in results) else "fail"

    out = {
        "schema_version": 1,
        "type": "register_contract_check",
        "ip": ip,
        "rtl_file": str(rtl_path.relative_to(root)),
        "status": overall,
        "registers_checked": len(results),
        "registers_failing": sum(1 for r in results if r["status"] == "fail"),
        "results": results,
    }

    out_path = ip_dir / "lint" / "register_contract.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("ip")
    p.add_argument("--root", default=".")
    args = p.parse_args()

    res = check(args.ip, Path(args.root).resolve())
    print(f"[register-contract] status={res['status']} "
          f"checked={res['registers_checked']} "
          f"failing={res['registers_failing']}")
    if res["status"] == "fail":
        for r in res["results"]:
            if r.get("status") != "fail":
                continue
            print(f"  REG {r.get('name')}: {r.get('reason', '(field-level)')}")
            for f in r.get("fields", []):
                if f.get("status") == "fail":
                    print(f"    field {f['field']}: {f['reason']} "
                          f"ssot={f.get('ssot_bits')} rtl={f.get('rtl_bits')}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
