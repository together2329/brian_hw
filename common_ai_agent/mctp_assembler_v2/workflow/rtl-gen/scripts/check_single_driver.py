#!/usr/bin/env python3
"""Check that every sequential signal/output is driven by exactly ONE always block.

Catches the SC3-style multi-driver race where the same reg gets NBA
assignments from two separate `always_ff @(posedge clk ...)` blocks,
producing simulator-dependent indeterminate behavior.

Strategy (regex-based, no external deps):
  1. For each .sv / .v file in <ip>/rtl/:
     a. Find all `reg`/`logic` declarations (also output reg/logic).
     b. Find all `always @(posedge ... or negedge ...)` blocks (and
        always_ff equivalents).
     c. For each always block, extract every `name <= expr;` NBA
        target on the LHS.
  2. Build a map name → list of always blocks that drive it.
  3. Any name with len(drivers) > 1 → R_SINGLE_DRIVER violation.

This is a heuristic (a real fix would use pyverilog or sv-parser AST),
but catches the bulk of common multi-driver patterns including the
SC3 spi_regs.sv `rxf_pop_en_reg` case.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


# ── Regex helpers ────────────────────────────────────────────────────

# `logic [...] name;` / `reg name;` / `output logic [...] name`
_STORAGE_DECL = re.compile(
    r"\b(?:output\s+)?(?:reg|logic)\b(?:\s*\[[^\]]*\])?\s+([A-Za-z_]\w*)\s*[,;)]",
)

# `always @(posedge sys_clk_i or negedge sys_resetn_i) begin ... end`
# We match block-level `always` blocks. To handle nested begin/end we
# must do a counting walk rather than non-greedy regex.
_ALWAYS_HEADER = re.compile(
    r"\balways\b\s*(?:@\s*\([^)]*\))?(?:\s+begin\b|\s+(?=if|case|for|@))",
    re.IGNORECASE,
)


def _strip_comments(src: str) -> str:
    src = re.sub(r"//[^\n]*", "", src)
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.DOTALL)
    return src


def _find_always_blocks(src: str) -> list[tuple[int, str]]:
    """Return [(start_line, body), ...] for every always block."""
    out: list[tuple[int, str]] = []
    src_clean = _strip_comments(src)

    # Locate every `always @(...) begin` and walk forward counting
    # begin/end pairs to find the matching end.
    for m in re.finditer(r"\balways\b[^@]*?@\s*\(", src_clean):
        i = m.end()
        # Find matching close paren of @(...)
        depth = 1
        while i < len(src_clean) and depth > 0:
            if src_clean[i] == "(":
                depth += 1
            elif src_clean[i] == ")":
                depth -= 1
            i += 1
        # Skip whitespace and find `begin` (or single statement form).
        rest = src_clean[i:]
        m2 = re.match(r"\s*begin\b", rest)
        if not m2:
            # Single-statement always: capture up to the next `;` at depth 0.
            stmt_end = rest.find(";")
            if stmt_end >= 0:
                start_line = src_clean[:m.start()].count("\n") + 1
                out.append((start_line, rest[:stmt_end + 1]))
            continue
        # Walk begin/end with counting.
        body_start = i + m2.end()
        j = body_start
        depth = 1
        while j < len(src_clean) and depth > 0:
            # Match whole word `begin` or `end` only.
            if src_clean[j:j+5] == "begin" and not (
                j > 0 and src_clean[j-1].isalnum()
            ) and not (j+5 < len(src_clean) and src_clean[j+5].isalnum()):
                depth += 1
                j += 5
                continue
            if src_clean[j:j+3] == "end" and not (
                j > 0 and src_clean[j-1].isalnum()
            ) and not (j+3 < len(src_clean) and src_clean[j+3].isalnum()):
                depth -= 1
                j += 3
                continue
            j += 1
        body = src_clean[body_start:j]
        start_line = src_clean[:m.start()].count("\n") + 1
        out.append((start_line, body))
    return out


def _extract_nba_targets(body: str) -> set[str]:
    """LHS names with `<=` NBA in the body. Indexed/sliced LHS reduces to base name."""
    out: set[str] = set()
    # `name <= ...;`  or `name[..] <= ...;`  or `name.field <= ...;`
    pat = re.compile(
        r"(?<![A-Za-z0-9_])([A-Za-z_]\w*)\s*(?:\[[^\]]*\])?\s*<=",
    )
    for m in pat.finditer(body):
        out.add(m.group(1))
    return out


# Names we never want to flag (built-ins, common parameters).
_IGNORED_NAMES = {
    "begin", "end", "if", "else", "case", "endcase", "for", "while",
    "always", "module", "endmodule", "input", "output", "inout",
    "wire", "reg", "logic", "parameter", "localparam", "assign",
    "default", "endcase",
}


def check_file(path: Path) -> dict[str, Any]:
    src = path.read_text(encoding="utf-8", errors="ignore")
    src_clean = _strip_comments(src)

    # Collect declared sequential-capable signal names.
    declared: set[str] = set()
    for m in _STORAGE_DECL.finditer(src_clean):
        nm = m.group(1)
        if nm not in _IGNORED_NAMES:
            declared.add(nm)

    # Find always blocks and their NBA targets.
    blocks = _find_always_blocks(src_clean)
    drivers: dict[str, list[int]] = {}
    for start_line, body in blocks:
        targets = _extract_nba_targets(body)
        for t in targets:
            if t in _IGNORED_NAMES:
                continue
            drivers.setdefault(t, []).append(start_line)

    # Multi-driver = >1 distinct always block lines drive the same name.
    violations: list[dict[str, Any]] = []
    for name, lines in drivers.items():
        unique_blocks = sorted(set(lines))
        if len(unique_blocks) > 1:
            # Only count if the name was declared as storage in this file
            # OR is a known output (we don't need to filter strictly —
            # multi-NBA-driven anything is a problem).
            violations.append({
                "signal": name,
                "always_block_start_lines": unique_blocks,
                "declared_in_this_file": name in declared,
            })

    return {
        "file": str(path),
        "regs_declared": len(declared),
        "storage_declared": len(declared),
        "always_blocks": len(blocks),
        "violations": violations,
    }


def check(ip: str, root: Path) -> dict[str, Any]:
    ip_dir = root / ip
    rtl_dir = ip_dir / "rtl"
    if not rtl_dir.is_dir():
        raise SystemExit(f"missing RTL dir: {rtl_dir}")

    file_results: list[dict[str, Any]] = []
    total_violations = 0
    for f in sorted(list(rtl_dir.glob("*.sv")) + list(rtl_dir.glob("*.v"))):
        r = check_file(f)
        # Pretty-relativize path
        try:
            r["file"] = str(f.relative_to(ip_dir.parent))
        except Exception:
            pass
        file_results.append(r)
        total_violations += len(r["violations"])

    overall = "fail" if total_violations else "pass"
    out = {
        "schema_version": 1,
        "type": "single_driver_check",
        "ip": ip,
        "status": overall,
        "total_violations": total_violations,
        "files": file_results,
    }

    out_path = ip_dir / "lint" / "single_driver.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("ip")
    p.add_argument("--root", default=".")
    args = p.parse_args()

    res = check(args.ip, Path(args.root).resolve())
    print(f"[single-driver] status={res['status']} "
          f"violations={res['total_violations']}")
    if res["status"] == "fail":
        for fr in res["files"]:
            for v in fr["violations"]:
                print(f"  {fr['file']}: signal '{v['signal']}' driven by "
                      f"{len(v['always_block_start_lines'])} always blocks "
                      f"at lines {v['always_block_start_lines']}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
