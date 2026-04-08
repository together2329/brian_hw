#!/usr/bin/env python3
"""
pyslang Timing Path Analysis for counter.v
============================================
Estimates combinational logic depth and identifies deep timing paths.

Analyzes:
  1. assign statements (continuous combinational paths)
  2. always @(*) blocks (combinational logic depth)
  3. always @(posedge/negedge clk) blocks (registered path complexity)
  4. Operator chain depth in expressions (+1, -1, comparisons, muxes)
  5. Critical path estimation from input → register → output

Reports warnings for paths exceeding configurable depth threshold (default: 5).

Usage:
    python3 analysis/timing_analysis.py [--rtl counter.v] [--threshold 5] [--json] [--markdown]

Output:
    Console report + optional JSON/Markdown to analysis/reports/
"""

import sys
import os
import re
import json
import argparse
from pathlib import Path
from collections import defaultdict

# ── Paths ──────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

try:
    from pyslang import SyntaxTree
except ImportError:
    print("ERROR: pyslang not installed.  Run: pip3 install pyslang")
    sys.exit(1)


# ======================================================================
# Parsing Helpers
# ======================================================================

def _token_text(tok) -> str:
    if tok is None:
        return ""
    if hasattr(tok, 'kind') and 'Keyword' in tok.kind.name:
        return tok.kind.name.replace('Keyword', '').lower()
    return str(tok).strip()


def parse_module(rtl_path: str):
    """Parse and return (module_node, raw_text, tree)."""
    tree = SyntaxTree.fromFile(rtl_path)
    root = tree.root
    modules = [m for m in root.members if m.kind.name == 'ModuleDeclaration']
    if not modules:
        return None, "", tree
    with open(rtl_path) as f:
        raw_text = f.read()
    return modules[0], raw_text, tree


def extract_port_names(mod) -> dict:
    """Quick port extraction: {name: direction}."""
    ports = {}
    header = mod.header
    port_section = header.ports
    if not port_section:
        return ports
    for item in port_section:
        if item.kind.name != 'SeparatedList':
            continue
        for sub in item:
            if sub.kind.name != 'ImplicitAnsiPort':
                continue
            direction = _token_text(sub.header.direction)
            name = sub.declarator.name.value
            ports[name] = direction
    return ports


# ======================================================================
# Expression Depth Estimator
# ======================================================================

def estimate_expr_depth(expr: str) -> int:
    """Estimate the combinational logic depth of a Verilog expression.

    Heuristic: count nested operator levels.
      - Simple identifier → depth 0
      - a + 1 → depth 1
      - (a + b) * c → depth 2
      - Ternary (mux) counts as max(cond_depth, true_depth, false_depth) + 1
    """
    if not expr.strip():
        return 0

    depth = 0
    # Count ternary operators (mux2 → 1 level)
    ternary_count = expr.count('?')
    # Count arithmetic operators
    arith_ops = len(re.findall(r'[+\-*]|(?<!<)(?!<)(?<!>)(?!>)/', expr))
    # Count comparison operators
    cmp_ops = len(re.findall(r'==|!=|<=|>=|<|>', expr))
    # Count logical operators
    log_ops = len(re.findall(r'&&|\|\||!', expr))
    # Count bitwise operators
    bit_ops = len(re.findall(r'&|\||\^|~', expr))
    # Count concatenation/replication
    concat_ops = expr.count('{')

    # Simple depth heuristic: max nesting level
    total_ops = arith_ops + cmp_ops + log_ops + bit_ops + ternary_count
    depth = max(ternary_count, 1 if total_ops > 0 else 0)

    return depth


def analyze_always_block_timing(body_text: str, sensitivity: str) -> dict:
    """Analyze timing-relevant properties of an always block.

    Returns dict with:
      - block_type: sequential/combinational
      - paths: list of {from_signal, to_signal, depth, operators, expr}
      - max_depth: deepest combinational path within this block
    """
    block_type = "sequential" if ("posedge" in sensitivity or "negedge" in sensitivity) else "combinational"

    paths = []

    # Extract nonblocking assignments: signal <= expr;
    for mo in re.finditer(r'(\w+)\s*<=\s*(.+?)(?:;|\n)', body_text, re.DOTALL):
        lhs = mo.group(1)
        rhs = mo.group(2).strip()
        if lhs in ('if', 'else', 'begin', 'end'):
            continue

        # Identify input signals on RHS
        rhs_signals = set(re.findall(r'\b([a-zA-Z_]\w*)\b', rhs))
        rhs_signals -= {'if', 'else', 'begin', 'end', 'always', 'posedge',
                         'negedge', 'none', 'b0', 'b1'}

        # Estimate depth
        depth = estimate_expr_depth(rhs)

        # Identify operators used
        operators = []
        if re.search(r'[+\-]', rhs):
            operators.append("add/sub")
        if re.search(r'==|!=|<=|>=|<|>', rhs):
            operators.append("compare")
        if '?' in rhs:
            operators.append("mux(ternary)")
        if re.search(r'&|\||\^|~', rhs):
            operators.append("bitwise")
        if '{' in rhs:
            operators.append("concat/replicate")

        for src in rhs_signals:
            paths.append({
                "from":         src,
                "to":           lhs,
                "depth":        depth,
                "operators":    operators,
                "expression":   rhs[:80],
                "path_type":    "registered" if block_type == "sequential" else "combinational",
            })

    # Extract blocking assignments: signal = expr;
    for mo in re.finditer(r'(\w+)\s*=\s*(?![=<>])(.+?)(?:;|\n)', body_text, re.DOTALL):
        lhs = mo.group(1)
        rhs = mo.group(2).strip()
        if lhs in ('if', 'else', 'begin', 'end', 'always'):
            continue

        rhs_signals = set(re.findall(r'\b([a-zA-Z_]\w*)\b', rhs))
        rhs_signals -= {'if', 'else', 'begin', 'end', 'always', 'posedge',
                         'negedge', 'none', 'b0', 'b1'}

        depth = estimate_expr_depth(rhs)

        operators = []
        if re.search(r'[+\-]', rhs):
            operators.append("add/sub")
        if re.search(r'==|!=|<=|>=|<|>', rhs):
            operators.append("compare")
        if '?' in rhs:
            operators.append("mux(ternary)")
        if re.search(r'&|\||\^|~', rhs):
            operators.append("bitwise")

        for src in rhs_signals:
            paths.append({
                "from":       src,
                "to":         lhs,
                "depth":      depth,
                "operators":  operators,
                "expression": rhs[:80],
                "path_type":  "registered" if block_type == "sequential" else "combinational",
            })

    max_depth = max((p['depth'] for p in paths), default=0)

    return {
        "block_type":  block_type,
        "sensitivity": sensitivity,
        "paths":       paths,
        "max_depth":   max_depth,
        "path_count":  len(paths),
    }


# ======================================================================
# Full Timing Analysis
# ======================================================================

def run_timing_analysis(rtl_path: str, threshold: int = 5) -> dict:
    """Run full timing path analysis."""
    print(f"[INFO] Parsing: {rtl_path}")

    mod, raw_text, tree = parse_module(rtl_path)
    if mod is None:
        return {}

    module_name = mod.header.name.value
    ports = extract_port_names(mod)

    print(f"[INFO] Module: {module_name}")
    print(f"[INFO] Ports: {len(ports)}")

    # Find all always blocks
    block_analyses = []
    for member in mod.members:
        if member.kind.name != 'AlwaysBlock':
            continue

        raw = str(member)

        # Detect sensitivity
        sensitivity = ""
        if "@(posedge clk)" in raw:
            sensitivity = "posedge clk"
        elif "@(negedge clk)" in raw:
            sensitivity = "negedge clk"
        elif "@(*)" in raw:
            sensitivity = "* (combinational)"
        else:
            m = re.search(r'@\(([^)]+)\)', raw)
            sensitivity = m.group(1) if m else "unknown"

        analysis = analyze_always_block_timing(raw, sensitivity)
        block_analyses.append(analysis)

    # Find continuous assignments (assign statements)
    assign_paths = []
    for mo in re.finditer(r'assign\s+(\w+)\s*=\s*(.+?);', raw_text):
        lhs = mo.group(1)
        rhs = mo.group(2).strip()

        rhs_signals = set(re.findall(r'\b([a-zA-Z_]\w*)\b', rhs))
        rhs_signals -= {'if', 'else', 'begin', 'end'}

        depth = estimate_expr_depth(rhs)
        for src in rhs_signals:
            assign_paths.append({
                "from":       src,
                "to":         lhs,
                "depth":      depth,
                "expression": rhs[:80],
                "path_type":  "continuous_assign",
            })

    # Collect warnings for deep paths
    warnings = []
    all_paths = []
    for idx, ba in enumerate(block_analyses):
        for p in ba['paths']:
            all_paths.append(p)
            if p['depth'] > threshold:
                warnings.append({
                    "severity": "WARNING",
                    "category": "deep_timing_path",
                    "message":  f"Path {p['from']} → {p['to']} has depth {p['depth']} "
                                f"(exceeds threshold {threshold}) in block {idx}",
                    "details":  p,
                })

    for p in assign_paths:
        all_paths.append(p)
        if p['depth'] > threshold:
            warnings.append({
                "severity": "WARNING",
                "category": "deep_timing_path",
                "message":  f"Continuous assign path {p['from']} → {p['to']} "
                            f"has depth {p['depth']} (exceeds threshold {threshold})",
                "details":  p,
            })

    # Critical path estimation: input → register → output
    # For counter: data_in/en/load/up_down → [posedge clk] → count_out/overflow
    critical_path_inputs = ['data_in', 'en', 'load', 'up_down', 'rst_n']
    critical_path_outputs = ['count_out', 'overflow']

    critical_paths = []
    for p in all_paths:
        if p['from'] in critical_path_inputs and p['to'] in critical_path_outputs:
            critical_paths.append(p)

    # Overall max depth
    overall_max = max((p['depth'] for p in all_paths), default=0)

    # Unique operator types used
    all_operators = set()
    for p in all_paths:
        all_operators.update(p.get('operators', []))

    results = {
        "module":           module_name,
        "rtl_path":         str(rtl_path),
        "threshold":        threshold,
        "always_blocks":    block_analyses,
        "assign_paths":     assign_paths,
        "all_paths":        all_paths,
        "critical_paths":   critical_paths,
        "warnings":         warnings,
        "summary": {
            "total_paths":       len(all_paths),
            "combinational":     sum(1 for p in all_paths if p['path_type'] == 'combinational'),
            "registered":        sum(1 for p in all_paths if p['path_type'] == 'registered'),
            "continuous_assign": len(assign_paths),
            "max_depth":         overall_max,
            "operators_used":    sorted(all_operators),
            "warnings_count":    len(warnings),
            "threshold":         threshold,
        },
    }

    return results


# ======================================================================
# Report Formatters
# ======================================================================

def print_console_report(results: dict):
    """Print timing analysis results."""
    mod_name = results["module"]
    summary = results["summary"]

    print("\n" + "=" * 72)
    print(f"  TIMING PATH ANALYSIS — Module: {mod_name}")
    print("=" * 72)

    print(f"\n  Threshold: {summary['threshold']} levels")
    print(f"  Total paths analyzed: {summary['total_paths']}")
    print(f"    Registered (clk):   {summary['registered']}")
    print(f"    Combinational:      {summary['combinational']}")
    print(f"    Continuous assign:  {summary['continuous_assign']}")
    print(f"  Max combinational depth: {summary['max_depth']}")
    print(f"  Operators: {', '.join(summary['operators_used']) or 'none'}")

    # Warnings
    if results["warnings"]:
        print(f"\n  ⚠️  {len(results['warnings'])} WARNING(s) — deep paths detected:")
        for w in results["warnings"]:
            print(f"    - {w['message']}")
    else:
        print(f"\n  ✅ No paths exceed depth threshold ({summary['threshold']}).")

    # Always block details
    print(f"\n{'─' * 72}")
    print(f"  ALWAYS BLOCK PATH DETAILS")
    print(f"{'─' * 72}")
    for idx, ba in enumerate(results["always_blocks"]):
        print(f"\n  Block {idx}: @{ba['sensitivity']} ({ba['block_type']})")
        print(f"    Paths: {ba['path_count']}, Max depth: {ba['max_depth']}")
        for p in ba['paths']:
            ops = '+'.join(p['operators']) if p['operators'] else 'wire'
            print(f"      {p['from']:>12} → {p['to']:<12} depth={p['depth']} [{ops}]")

    # Continuous assigns
    if results["assign_paths"]:
        print(f"\n  CONTINUOUS ASSIGNMENTS")
        for p in results["assign_paths"]:
            print(f"    {p['from']:>12} → {p['to']:<12} depth={p['depth']}")

    # Critical paths
    if results["critical_paths"]:
        print(f"\n  CRITICAL PATHS (input → register → output):")
        for p in results["critical_paths"]:
            ops = '+'.join(p['operators']) if p['operators'] else 'wire'
            print(f"    {p['from']:>12} →[ CLK ]→ {p['to']:<12} depth={p['depth']} [{ops}]")

    # Verdict
    print(f"\n{'─' * 72}")
    if not results["warnings"]:
        print(f"  ✅ VERDICT: All paths within depth threshold. Timing is clean.")
    else:
        print(f"  ⚠️  VERDICT: {len(results['warnings'])} path(s) exceed threshold!")
    print(f"{'─' * 72}\n")


def generate_markdown_report(results: dict) -> str:
    """Generate Markdown timing analysis report."""
    lines = []
    mod_name = results["module"]
    summary = results["summary"]

    lines.append("# pyslang Timing Path Analysis Report\n")
    lines.append(f"**Module**: `{mod_name}`  ")
    lines.append(f"**Source**: `{results['rtl_path']}`  ")
    lines.append(f"**Depth Threshold**: {summary['threshold']} levels\n")

    # Summary table
    lines.append("## Summary\n")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total paths | {summary['total_paths']} |")
    lines.append(f"| Registered paths | {summary['registered']} |")
    lines.append(f"| Combinational paths | {summary['combinational']} |")
    lines.append(f"| Continuous assigns | {summary['continuous_assign']} |")
    lines.append(f"| Max combinational depth | {summary['max_depth']} |")
    lines.append(f"| Deep path warnings | {summary['warnings_count']} |")
    lines.append(f"| Operators used | {', '.join(summary['operators_used']) or 'none'} |")
    lines.append("")

    if not results["warnings"]:
        lines.append("> ✅ **All paths within depth threshold. No timing concerns.**\n")
    else:
        lines.append(f"> ⚠️ **{len(results['warnings'])} path(s) exceed threshold!**\n")

    # Always block paths
    lines.append("## Always Block Path Analysis\n")
    for idx, ba in enumerate(results["always_blocks"]):
        lines.append(f"### Block {idx}: `@{ba['sensitivity']}` ({ba['block_type']})\n")
        lines.append(f"- **Paths**: {ba['path_count']}")
        lines.append(f"- **Max depth**: {ba['max_depth']}\n")

        if ba['paths']:
            lines.append("| From | To | Depth | Operators |")
            lines.append("|------|----|-------|-----------|")
            for p in ba['paths']:
                ops = '+'.join(p['operators']) if p['operators'] else 'wire'
                lines.append(f"| `{p['from']}` | `{p['to']}` | {p['depth']} | {ops} |")
            lines.append("")

    # Critical paths
    if results["critical_paths"]:
        lines.append("## Critical Paths (Input → Register → Output)\n")
        lines.append("| From | Through | To | Depth | Operators |")
        lines.append("|------|---------|----|-------|-----------|")
        for p in results["critical_paths"]:
            ops = '+'.join(p['operators']) if p['operators'] else 'wire'
            lines.append(f"| `{p['from']}` | CLK | `{p['to']}` | {p['depth']} | {ops} |")
        lines.append("")

    return "\n".join(lines)


# ======================================================================
# Main
# ======================================================================

def main():
    parser = argparse.ArgumentParser(
        description="pyslang timing path analysis for counter.v")
    parser.add_argument("--rtl", default=str(PROJECT_ROOT / "counter.v"),
                        help="Path to Verilog RTL file")
    parser.add_argument("--threshold", type=int, default=5,
                        help="Depth threshold for warnings (default: 5)")
    parser.add_argument("--json", action="store_true",
                        help="Save results as JSON")
    parser.add_argument("--markdown", action="store_true",
                        help="Save results as Markdown")
    args = parser.parse_args()

    if not os.path.exists(args.rtl):
        print(f"[ERROR] RTL file not found: {args.rtl}")
        sys.exit(1)

    results = run_timing_analysis(args.rtl, args.threshold)
    if not results:
        print("[ERROR] Analysis failed — no results")
        sys.exit(1)

    print_console_report(results)

    if args.json:
        report_dir = SCRIPT_DIR / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        json_path = report_dir / "timing_analysis.json"
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"[INFO] JSON report saved: {json_path}")

    if args.markdown:
        report_dir = SCRIPT_DIR / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        md_path = report_dir / "timing_analysis.md"
        md_text = generate_markdown_report(results)
        with open(md_path, 'w') as f:
            f.write(md_text)
        print(f"[INFO] Markdown report saved: {md_path}")

    sys.exit(0 if not results["warnings"] else 1)


if __name__ == "__main__":
    main()
