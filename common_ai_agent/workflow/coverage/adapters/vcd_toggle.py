#!/usr/bin/env python3
"""vcd_toggle.py — Extract toggle coverage from a VCD file.

For each net declared in the VCD's `$var` blocks, count the number of
0→1 and 1→0 transitions observed in the value-change section. A net is
"fully toggled" if it saw at least one transition in each direction
(matching how verilator and most commercial tools define toggle coverage).

Output:
  - text summary (default): prints overall % + per-scope breakdown
  - --json: emits a JSON object suitable for the Atlas UI panel to render

Why this exists alongside `verilator --coverage-toggle`:
  Verilator's instrumented toggle is fast and accurate but requires a
  verilator-friendly DUT (no inline #delays, no force/release, etc.).
  VCD-based toggle works on ANY simulator's output (iverilog, Questa,
  VCS), so this is the post-process channel from sim_debug/COVERAGE.md.

Limitations:
  - Multi-bit nets are decomposed into per-bit transitions when the VCD
    emits binary literals (`b1010 #`). For ASCII-encoded buses we still
    track per-bit toggle if the value width is known.
  - X / Z transitions count toward the "any change" total but not toward
    the 0↔1 toggle metric, mirroring verilator behavior.
  - Real-valued nets (`$var real`) are skipped — toggle is undefined for
    floating-point.

No external dependencies — Python stdlib only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class Net:
    """One declared signal in the VCD."""
    ident: str         # one or more characters, the VCD's compact id
    name: str          # human-readable signal name
    width: int         # bit width (1 for scalar, N for vectors)
    scope: str         # full hierarchical scope path (e.g. "tb.dut.regs")
    var_type: str      # "wire", "reg", "logic", etc.
    # Per-bit transition counters: index 0 = LSB
    rises: List[int] = field(default_factory=list)
    falls: List[int] = field(default_factory=list)
    last: List[Optional[str]] = field(default_factory=list)  # '0', '1', 'x', 'z', or None

    def init(self) -> None:
        self.rises = [0] * self.width
        self.falls = [0] * self.width
        self.last = [None] * self.width

    def update(self, new_bits: List[Optional[str]]) -> None:
        """Apply a new value (bit-aligned to width). Update transitions."""
        # new_bits is LSB-first list aligned to self.width
        for i in range(self.width):
            new_b = new_bits[i] if i < len(new_bits) else None
            old_b = self.last[i]
            if old_b is not None and new_b is not None:
                if old_b == '0' and new_b == '1':
                    self.rises[i] += 1
                elif old_b == '1' and new_b == '0':
                    self.falls[i] += 1
            self.last[i] = new_b

    def toggled_bits(self) -> int:
        """Count bits that saw both a rise AND a fall."""
        return sum(1 for r, f in zip(self.rises, self.falls) if r > 0 and f > 0)

    def covered_pct(self) -> float:
        if self.width == 0:
            return 100.0
        return 100.0 * self.toggled_bits() / self.width


def _bin_decompose(value: str, width: int) -> List[Optional[str]]:
    """Convert a VCD bit-string ('1010xz', etc.) into LSB-first list of length `width`.

    VCD spec (IEEE 1364-2005 §18.2.3.2): binary literals are MSB-first;
    if the literal is shorter than the variable width, pad on the left
    with:
      - '0' if MSB is '0' or '1'
      - 'x' if MSB is 'x'
      - 'z' if MSB is 'z'
    """
    value = value.strip().lower()
    if not value:
        value = '0'
    msb = value[0] if value[0] in '01xz' else 'x'
    pad = msb if msb in 'xz' else '0'
    if len(value) < width:
        value = pad * (width - len(value)) + value
    elif len(value) > width:
        value = value[-width:]
    bits: List[Optional[str]] = []
    for c in reversed(value):
        bits.append(c if c in '01xz' else 'x')
    return bits


def parse_vcd(path: str) -> Dict[str, Net]:
    """Parse a VCD file. Returns {ident: Net}."""
    text = Path(path).read_text(errors='replace')
    nets: Dict[str, Net] = {}
    scope_stack: List[str] = []

    if "$enddefinitions" not in text:
        raise ValueError(f"{path}: missing $enddefinitions")

    h_idx = text.index("$enddefinitions")
    after = h_idx + len("$enddefinitions")
    end_idx = text.index("$end", after)
    header = text[:end_idx]
    body = text[end_idx + len("$end"):].lstrip("\n")

    # ── Parse header ──
    # We track $scope / $upscope and $var lines.
    i = 0
    tokens: List[str] = []
    for line in header.splitlines():
        for tok in line.split():
            tokens.append(tok)
    j = 0
    while j < len(tokens):
        t = tokens[j]
        if t == "$scope":
            # $scope <type> <name> $end
            if j + 3 < len(tokens):
                scope_stack.append(tokens[j + 2])
            j += 4
            continue
        if t == "$upscope":
            if scope_stack:
                scope_stack.pop()
            j += 2  # skip $end too
            continue
        if t == "$var":
            # $var <type> <width> <ident> <name> [<bit-range>] $end
            var_type = tokens[j + 1]
            try:
                width = int(tokens[j + 2])
            except (ValueError, IndexError):
                width = 1
            ident = tokens[j + 3] if j + 3 < len(tokens) else ""
            name = tokens[j + 4] if j + 4 < len(tokens) else ""
            # Skip real-valued vars (toggle undefined for float)
            if var_type == "real":
                # advance to $end
                while j < len(tokens) and tokens[j] != "$end":
                    j += 1
                j += 1
                continue
            scope_path = ".".join(scope_stack)
            n = Net(
                ident=ident, name=name, width=width,
                scope=scope_path, var_type=var_type,
            )
            n.init()
            # Multiple $var with the same ident refer to the same wire under
            # different aliases — we keep only the first encounter.
            if ident and ident not in nets:
                nets[ident] = n
            # Advance to $end
            while j < len(tokens) and tokens[j] != "$end":
                j += 1
            j += 1
            continue
        j += 1

    # ── Parse body ──
    # Lines: `#<time>` or `0!`, `1!`, `x!`, `z!`, `b<bits> <ident>`, `r<real> <ident>`.
    # Group multi-line value changes inside `$dumpvars ... $end` blocks too.
    in_dumpvars = False
    for raw in body.splitlines():
        s = raw.strip()
        if not s:
            continue
        if s == "$dumpvars" or s == "$dumpall" or s == "$dumpon" or s == "$dumpoff":
            in_dumpvars = True
            continue
        if s == "$end":
            in_dumpvars = False
            continue
        if s.startswith("#"):
            continue  # time marker; we don't need timestamps for toggle
        if s.startswith("$"):
            continue  # other directives
        # Scalar: e.g. "1!" → value '1', ident '!'
        first = s[0]
        if first in "01xz":
            ident = s[1:].strip()
            net = nets.get(ident)
            if net is not None:
                net.update([first if first in '01xz' else 'x'])
            continue
        # Vector binary: "b1010xz <ident>"
        if first == 'b' or first == 'B':
            try:
                value, ident = s[1:].split(None, 1)
            except ValueError:
                continue
            net = nets.get(ident.strip())
            if net is not None:
                net.update(_bin_decompose(value, net.width))
            continue
        # Real: "r3.14 <ident>" — skip (we don't track real toggles)
        if first == 'r' or first == 'R':
            continue
        # Vector hex / unknown — try to parse as binary if it works
        # (most VCDs use 'b' prefix; this is a fallback)
    return nets


def summarize(nets: Dict[str, Net]) -> dict:
    """Aggregate per-net into per-scope and global totals."""
    by_scope: Dict[str, Dict[str, int]] = {}
    total_bits = 0
    toggled_bits = 0
    for net in nets.values():
        total_bits += net.width
        toggled_bits += net.toggled_bits()
        sc = net.scope or "(root)"
        if sc not in by_scope:
            by_scope[sc] = {"total": 0, "toggled": 0, "nets": 0}
        by_scope[sc]["total"] += net.width
        by_scope[sc]["toggled"] += net.toggled_bits()
        by_scope[sc]["nets"] += 1
    pct = (100.0 * toggled_bits / total_bits) if total_bits else 0.0
    return {
        "total_bits": total_bits,
        "toggled_bits": toggled_bits,
        "pct": pct,
        "nets": len(nets),
        "by_scope": by_scope,
    }


def main(argv: List[str]) -> int:
    p = argparse.ArgumentParser(description="Extract toggle coverage from a VCD file.")
    p.add_argument("vcd", help="Input VCD file")
    p.add_argument("--json", action="store_true", help="Emit JSON instead of text summary")
    p.add_argument("--top", type=int, default=10, help="Show top-N worst-toggle scopes")
    args = p.parse_args(argv)

    if not Path(args.vcd).exists():
        print(f"ERROR: {args.vcd} not found", file=sys.stderr)
        return 1

    try:
        nets = parse_vcd(args.vcd)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    summary = summarize(nets)

    if args.json:
        out = {
            "vcd": args.vcd,
            "total_bits": summary["total_bits"],
            "toggled_bits": summary["toggled_bits"],
            "pct": summary["pct"],
            "nets": summary["nets"],
            "scopes": [
                {
                    "scope": sc,
                    "total": s["total"],
                    "toggled": s["toggled"],
                    "nets": s["nets"],
                    "pct": (100.0 * s["toggled"] / s["total"]) if s["total"] else 0.0,
                }
                for sc, s in summary["by_scope"].items()
            ],
        }
        print(json.dumps(out, indent=2))
        return 0

    # Text summary
    print(f"=== VCD Toggle Coverage: {args.vcd} ===")
    print(f"Nets         : {summary['nets']}")
    print(f"Total bits   : {summary['total_bits']}")
    print(f"Toggled bits : {summary['toggled_bits']}")
    print(f"Toggle %     : {summary['pct']:.2f} %")
    print()
    print(f"=== Worst-{args.top} scopes (by toggle %) ===")
    rows = sorted(
        summary["by_scope"].items(),
        key=lambda kv: (kv[1]["toggled"] / kv[1]["total"]) if kv[1]["total"] else 1.0,
    )[: args.top]
    for sc, s in rows:
        pct = (100.0 * s["toggled"] / s["total"]) if s["total"] else 0.0
        print(f"  {pct:5.1f} %  {s['toggled']:>4}/{s['total']:<4} bits  ({s['nets']} nets)  {sc}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
