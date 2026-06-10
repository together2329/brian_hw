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


# Read-data signals this gate understands, by protocol. rtl_contract.json
# output_map (when present) is consulted first so a custom name still works.
_KNOWN_RDATA_SIGNALS = ("s_axi_rdata", "prdata", "rdata", "hrdata")


def _rdata_candidates(ip_dir: Path) -> list[str]:
    """Read-data signal candidates: rtl_contract output ports first, then the
    protocol-known set. The original gate hardcoded s_axi_rdata (AXI-only), so
    APB IPs (prdata) could never use this check at all."""
    out: list[str] = []
    contract_path = ip_dir / "rtl" / "rtl_contract.json"
    if contract_path.is_file():
        try:
            doc = json.loads(contract_path.read_text(encoding="utf-8"))
            contract = doc.get("contract") if isinstance(doc.get("contract"), dict) else doc
            output_map = contract.get("output_map") if isinstance(contract, dict) else {}
            for port in (output_map or {}).values():
                name = str(port).strip()
                if name.lower().endswith("rdata") and name not in out:
                    out.append(name)
        except (OSError, ValueError):
            pass
    for name in _KNOWN_RDATA_SIGNALS:
        if name not in out:
            out.append(name)
    return out


def _find_regs_file(ip_dir: Path, ip: str) -> tuple[Path, str]:
    """Pick the register-block RTL file and the read-data signal it drives."""
    rtl_dir = ip_dir / "rtl"
    rdata_names = _rdata_candidates(ip_dir)
    candidates = [
        rtl_dir / f"{ip}_regs.sv",
        rtl_dir / f"{ip}_regs.v",
        rtl_dir / "regs.sv",
    ]
    candidates += sorted(p for p in rtl_dir.glob("*_regs*.sv") if p not in candidates)
    candidates += sorted(p for p in rtl_dir.glob("*_regs*.v") if p not in candidates)
    ordered: list[Path] = []
    for c in candidates + sorted(rtl_dir.glob("*.sv")):
        if c.is_file() and c not in ordered:
            ordered.append(c)
    for f in ordered:
        text = f.read_text(encoding="utf-8", errors="ignore")
        for rdata in rdata_names:
            if re.search(rf"\b{re.escape(rdata)}\b\s*(\[[^\]]*\])?\s*<?=[^=]", text):
                return f, rdata
    raise SystemExit(
        f"no register RTL file found in {rtl_dir} "
        f"(looked for read-data writes to any of: {', '.join(rdata_names)})"
    )


def _macro_offsets(ip_dir: Path) -> dict[str, int]:
    """Map `define names to integer values from rtl/ headers and sources.

    Register decode case arms frequently use macros (`PC_ADDR_CTRL) instead
    of literal 8'hXX labels; without resolving them the gate sees no read
    path at all."""
    out: dict[str, int] = {}
    rtl_dir = ip_dir / "rtl"
    value_re = r"(?:\d+)?'(?:h([0-9a-fA-F_]+)|d(\d+)|b([01_]+))|(\d+)"
    define_re = re.compile(rf"`define\s+(\w+)\s+(?:{value_re})")
    localparam_re = re.compile(
        rf"\b(?:localparam|parameter)\b[^;=]*?\b(\w+)\s*=\s*(?:{value_re})\s*[;,]"
    )
    sources = (
        list(rtl_dir.glob("*.vh")) + list(rtl_dir.glob("*.svh"))
        + list(rtl_dir.glob("*.sv")) + list(rtl_dir.glob("*.v"))
    )
    for f in sorted(sources):
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern in (define_re, localparam_re):
            for name, hexv, decv, binv, plain in pattern.findall(text):
                try:
                    if hexv:
                        out[name] = int(hexv.replace("_", ""), 16)
                    elif decv:
                        out[name] = int(decv)
                    elif binv:
                        out[name] = int(binv.replace("_", ""), 2)
                    elif plain:
                        out[name] = int(plain)
                except ValueError:
                    continue
    return out


def _signal_widths(rtl_text: str) -> dict[str, int]:
    """Width of each declared signal/port in the file (1 when unranged)."""
    widths: dict[str, int] = {}
    decl_re = re.compile(
        r"\b(?:input|output|inout|wire|reg|logic)\b[^;=\n]*?"
        r"(?:\[\s*(\d+)\s*:\s*(\d+)\s*\]\s*)?"
        r"([A-Za-z_]\w*)\s*(?:[,;=)]|$)",
        re.MULTILINE,
    )
    for hi, lo, name in decl_re.findall(rtl_text):
        if name in ("input", "output", "inout", "wire", "reg", "logic", "signed"):
            continue
        if hi and lo:
            widths[name] = abs(int(hi) - int(lo)) + 1
        else:
            widths.setdefault(name, 1)
    return widths


def _split_concat(body: str) -> list[str]:
    """Split a concat body on top-level commas (depth-aware for nesting)."""
    elements: list[str] = []
    depth = 0
    current: list[str] = []
    for ch in body:
        if ch in "{([":
            depth += 1
        elif ch in "})]":
            depth -= 1
        if ch == "," and depth == 0:
            elements.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    tail = "".join(current).strip()
    if tail:
        elements.append(tail)
    return elements


def _balanced_concat_after(text: str, start: int) -> str | None:
    """Return the `{...}` expression starting at text[start] with balanced
    braces, or None. Regex with a lazy `}` cuts nested concats short."""
    if start >= len(text) or text[start] != "{":
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


def _concat_ranges(expr: str, widths: dict[str, int], reg_width: int) -> list[tuple[int, int, str]] | None:
    """Decompose `{a, b, 31'd0}` (or a single known-width signal) into
    MSB-first bit ranges. Returns None when any element width is unknown or
    the total does not cover the register."""
    # Concats are routinely annotated with `// [bit] name` comments per
    # element; strip comments so they don't glue onto the next element.
    expr = re.sub(r"//[^\n]*", "", expr)
    expr = re.sub(r"/\*.*?\*/", "", expr, flags=re.DOTALL)
    expr = expr.strip()
    if expr.startswith("{") and expr.endswith("}"):
        elements = _split_concat(expr[1:-1])
    else:
        elements = [expr]
    sized_literal = re.compile(r"^(\d+)\s*'\s*[hdbo]", re.IGNORECASE)
    resolved: list[tuple[str, int]] = []
    for element in elements:
        m = sized_literal.match(element)
        if m:
            resolved.append((element, int(m.group(1))))
            continue
        slice_m = re.search(r"\[\s*(\d+)\s*:\s*(\d+)\s*\]", element)
        if slice_m:
            resolved.append((element, abs(int(slice_m.group(1)) - int(slice_m.group(2))) + 1))
            continue
        name = element.split("[", 1)[0].strip()
        if re.fullmatch(r"[A-Za-z_]\w*", name) and name in widths:
            resolved.append((element, widths[name]))
            continue
        return None
    total = sum(w for _, w in resolved)
    if total != reg_width:
        return None
    out: list[tuple[int, int, str]] = []
    hi = reg_width - 1
    for sig, w in resolved:
        out.append((hi, hi - w + 1, sig))
        hi -= w
    return out


def _offset_case_labels(offset: int, macros: dict[str, int]) -> list[str]:
    """Regex alternatives that can label this offset in a case statement.

    Macro names appear backticked (`PC_ADDR_CTRL) when they come from `define,
    and bare (ADDR_CONTROL) when they are localparams/parameters."""
    labels = [
        rf"\d*'h0*{offset:x}",
        rf"\d*'d0*{offset}",
    ]
    for name, value in macros.items():
        if value == offset:
            labels.append(rf"`?{re.escape(name)}")
    return labels


def _extract_offset_assignments(
    rtl_text: str,
    offset: int,
    rdata: str = "s_axi_rdata",
    macros: dict[str, int] | None = None,
) -> list[tuple[int, int, str]]:
    """For a register at the given offset, return [(hi, lo, signal), ...].

    Supports both arm shapes for hex/decimal/macro labels:
      8'h<HH>: begin <rdata>[A:B] <= sig; ... end
      `ADDR_MACRO:      <rdata> <= expr;          (single statement, no begin)
    Whole-register assignments are returned as (-1, -1, "WHOLE:<expr>") for
    the caller to decompose against declared signal widths.
    """
    macros = macros or {}
    rdata_re = re.escape(rdata)
    labels = _offset_case_labels(offset, macros)
    bodies: list[str] = []
    for label in labels:
        case_re = re.compile(
            rf"(?:^|[\s,(]){label}\s*:\s*(begin(?:.*?)\bend|[^;]*?;)",
            re.IGNORECASE | re.DOTALL | re.MULTILINE,
        )
        for m in case_re.finditer(rtl_text):
            candidate = m.group(1)
            if re.search(rf"\b{rdata_re}\b", candidate):
                bodies.append(candidate)
    # if-arm style: `wire rd_x = ... (paddr == ADDR_Y) ...;` decode wires, then
    # `if (rd_x) <rdata> = expr;` (the mctp/regfile pattern). Resolve the
    # decode wires whose compare matches this offset and treat their if-arms
    # as the offset body.
    addr_alt = "|".join(labels)
    decode_re = re.compile(
        rf"\bwire\s+(\w+)\s*=\s*[^;]*?==\s*(?:{addr_alt})\b[^;]*;",
        re.IGNORECASE,
    )
    for wm in decode_re.finditer(rtl_text):
        wire_name = re.escape(wm.group(1))
        if_re = re.compile(
            rf"if\s*\(\s*{wire_name}\s*\)\s*(begin(?:.*?)\bend|[^;]*?;)",
            re.DOTALL,
        )
        for m in if_re.finditer(rtl_text):
            candidate = m.group(1)
            if re.search(rf"\b{rdata_re}\b", candidate):
                bodies.append(candidate)
    if not bodies:
        return []
    body = "\n".join(bodies)

    out: list[tuple[int, int, str]] = []
    # Both non-blocking (<=) and blocking (=) read-mux styles are real; the
    # original gate only understood `<=`.
    assign_op = r"<?="
    range_re = re.compile(
        rf"{rdata_re}\s*\[\s*(\d+)\s*:\s*(\d+)\s*\]\s*{assign_op}\s*(.+?)\s*;",
        re.DOTALL,
    )
    for hi, lo, sig in range_re.findall(body):
        out.append((int(hi), int(lo), sig.strip()))
    single_re = re.compile(
        rf"{rdata_re}\s*\[\s*(\d+)\s*\]\s*{assign_op}\s*(.+?)\s*;",
        re.DOTALL,
    )
    for bit, sig in single_re.findall(body):
        out.append((int(bit), int(bit), sig.strip()))
    whole_re = re.compile(
        rf"{rdata_re}\s*{assign_op}\s*(.+?)\s*;",
        re.DOTALL,
    )
    for sig in whole_re.findall(body):
        out.append((-1, -1, "WHOLE:" + sig.strip()))
    return out


def _check_one_register(
    reg: dict[str, Any],
    rtl_text: str,
    rdata: str = "s_axi_rdata",
    macros: dict[str, int] | None = None,
    widths: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Check one register from SSOT against parsed RTL assignments."""
    name = reg.get("name", "?")
    offset = reg.get("offset")
    if offset is None:
        return {
            "name": name, "status": "skip",
            "reason": "no offset in SSOT (likely write-only / virtual)"
        }
    if reg.get("repeat") or reg.get("stride") or reg.get("count"):
        # SSOT-declared banked/windowed register block (repeat/stride): the
        # read path is index-computed, not a static per-offset mux arm, so a
        # static layout check does not apply. The SSOT metadata, not an RTL
        # heuristic, authorizes this skip.
        return {
            "name": name, "offset": offset, "status": "skip-banked",
            "reason": "SSOT declares repeat/stride banked block; read path is index-computed",
        }
    offset_value = int(str(offset), 0)
    rtl_assigns = _extract_offset_assignments(rtl_text, offset_value, rdata, macros)
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
            "reason": f"no RTL read-path assignments at offset 0x{offset_value:02x}",
            "ssot_fields": [f.get("name") for f in fields],
        }

    # Whole-register writeback (`<rdata> <= {ctrl_rsvd, enable};` or
    # `<rdata> <= count_value;`): decompose the expression against declared
    # signal widths so concat-style read muxes get a REAL field-level check.
    # Only when no element width is resolvable do we fall back to skip-whole.
    whole_only = all(hi == -1 for (hi, _, _) in rtl_assigns)
    if whole_only:
        reg_width = int(reg.get("width") or 32)
        decomposed: list[tuple[int, int, str]] = []
        for (_, _, sig) in rtl_assigns:
            expr = sig.split(":", 1)[1]
            ranges = _concat_ranges(expr, widths or {}, reg_width)
            if ranges:
                decomposed = ranges
                break
        # One-hop indirection: `prdata = status_word;` where status_word is
        # itself assembled as `assign status_word = {a, b, ...};`. Follow the
        # intermediate signal once so packed status words still get a real
        # field-level comparison.
        if (
            len(decomposed) == 1
            and decomposed[0][0] == reg_width - 1
            and decomposed[0][1] == 0
            and re.fullmatch(r"[A-Za-z_]\w*", decomposed[0][2] or "")
        ):
            inner_name = decomposed[0][2]
            assemble_re = re.compile(
                rf"\b{re.escape(inner_name)}\s*<?=\s*\{{",
            )
            m = assemble_re.search(rtl_text)
            if m:
                concat = _balanced_concat_after(rtl_text, m.end() - 1)
                if concat:
                    inner = _concat_ranges(concat, widths or {}, reg_width)
                    if inner:
                        decomposed = inner
        if decomposed:
            rtl_assigns = decomposed
        else:
            return {
                "name": name, "offset": offset, "status": "skip-whole",
                "reason": "RTL uses whole-register read-back and the expression "
                          "could not be decomposed against declared signal widths",
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

    rtl_path, rdata = _find_regs_file(ip_dir, ip)
    rtl_text = rtl_path.read_text(encoding="utf-8", errors="ignore")
    macros = _macro_offsets(ip_dir)
    widths = _signal_widths(rtl_text)

    results = [_check_one_register(r, rtl_text, rdata, macros, widths) for r in regs]
    overall = "pass" if all(r["status"] in ("pass", "skip", "skip-wo", "skip-whole", "skip-banked") for r in results) else "fail"

    out = {
        "schema_version": 1,
        "type": "register_contract_check",
        "ip": ip,
        "rtl_file": str(rtl_path.relative_to(root)),
        "rdata_signal": rdata,
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
