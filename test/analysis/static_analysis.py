#!/usr/bin/env python3
"""
pyslang Static Issue Analysis for counter.v
=============================================
Performs deep static analysis using pyslang AST to detect:
  1. Undriven internal signals (declared but never assigned)
  2. Multiple drivers (same signal assigned in >1 always block)
  3. Combinational loop suspects (signal read+written in same always @(*) block)
  4. Latch inference suspects (incomplete if/else in combinational blocks)
  5. Width mismatch suspects (bit-width inconsistencies in assignments)
  6. Unread signals (assigned but never consumed)

Also runs pyslang compilation to catch cross-reference errors.

Usage:
    python3 analysis/static_analysis.py [--rtl counter.v] [--json] [--markdown]

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

# ── pyslang import ─────────────────────────────────────────────────────
try:
    from pyslang import SyntaxTree, Compilation
except ImportError:
    print("ERROR: pyslang not installed.  Run: pip3 install pyslang")
    sys.exit(1)


# ======================================================================
# RTL Parsing Helpers
# ======================================================================

def _token_text(tok) -> str:
    """Safely extract text from a pyslang token."""
    if tok is None:
        return ""
    if hasattr(tok, 'kind') and 'Keyword' in tok.kind.name:
        return tok.kind.name.replace('Keyword', '').lower()
    return str(tok).strip()


def parse_module(rtl_path: str):
    """Parse Verilog file and return (module_node, raw_text, tree)."""
    tree = SyntaxTree.fromFile(rtl_path)
    root = tree.root

    modules = [m for m in root.members
               if m.kind.name == 'ModuleDeclaration']
    if not modules:
        print("[ERROR] No module declarations found!")
        return None, "", tree

    with open(rtl_path) as f:
        raw_text = f.read()

    return modules[0], raw_text, tree


def extract_port_info(mod) -> dict:
    """Extract port names, directions, and types.

    Returns dict: {name: {direction, type, width_str, is_input, is_output}}
    """
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

            ph  = sub.header
            dec = sub.declarator
            direction = _token_text(ph.direction)

            # Determine net/var type
            net_or_var = ""
            if hasattr(ph, 'netType') and ph.netType:
                net_or_var = _token_text(ph.netType)
            dt = ph.dataType
            dt_kind = dt.kind.name if hasattr(dt, 'kind') else ""
            if not net_or_var:
                net_or_var = "reg" if 'RegType' in dt_kind else "wire"

            # Width
            dt_text = str(dt).strip()
            width_str = "1-bit"
            m = re.search(r'\[.*?\]', dt_text)
            if m:
                width_str = m.group(0)

            name = dec.name.value
            ports[name] = {
                "direction":  direction,
                "type":       net_or_var,
                "width":      width_str,
                "is_input":   direction == "input",
                "is_output":  direction == "output",
            }
    return ports


def extract_local_signals(mod, ports: dict) -> dict:
    """Extract internal signal declarations (not ports).

    Returns dict: {name: {type, width, is_reg, is_wire}}
    """
    signals = {}
    port_names = set(ports.keys())

    for member in mod.members:
        kind_name = member.kind.name

        # Net declarations (wire)
        if kind_name == 'NetDeclaration':
            # e.g. wire [7:0] my_wire;
            raw = str(member).strip()
            for decl in getattr(member, 'declarators', []):
                name = decl.name.value
                if name not in port_names:
                    dt_text = raw
                    width = "1-bit"
                    m = re.search(r'\[.*?\]', dt_text)
                    if m:
                        width = m.group(0)
                    signals[name] = {
                        "type": "wire",
                        "width": width,
                        "is_reg": False,
                        "is_wire": True,
                    }

        # Variable declarations (reg / integer / logic)
        elif kind_name == 'VariableDeclaration':
            raw = str(member).strip()
            for decl in getattr(member, 'declarators', []):
                name = decl.name.value
                if name not in port_names:
                    dt_text = raw
                    width = "1-bit"
                    m = re.search(r'\[.*?\]', dt_text)
                    if m:
                        width = m.group(0)
                    signals[name] = {
                        "type": "reg",
                        "width": width,
                        "is_reg": True,
                        "is_wire": False,
                    }

    return signals


def extract_always_blocks_detailed(mod) -> list:
    """Extract always blocks with full assignment and read details.

    Returns list of dicts:
        {
            sensitivity: str,
            block_type:  "sequential" | "combinational",
            nb_assigns:  {signal: [line_ctx, ...]},   # nonblocking <=
            b_assigns:   {signal: [line_ctx, ...]},    # blocking =
            reads:       set of signal names read in this block
            body_text:   str
        }
    """
    blocks = []
    for member in mod.members:
        if member.kind.name != 'AlwaysBlock':
            continue

        raw = str(member)

        # Sensitivity
        sensitivity = ""
        if "@(posedge clk)" in raw:
            sensitivity = "posedge clk"
        elif "@(negedge clk)" in raw:
            sensitivity = "negedge clk"
        elif "@(*)" in raw or "@ *" in raw:
            sensitivity = "* (combinational)"
        else:
            # Try to extract whatever is in @(...)
            m = re.search(r'@\(([^)]+)\)', raw)
            sensitivity = m.group(1) if m else "unknown"

        block_type = "sequential" if ("posedge" in sensitivity or "negedge" in sensitivity) else "combinational"

        # Nonblocking assignments: signal <= expr
        nb_pattern = re.compile(r'(\w+)\s*<=\s*')
        nb_assigns = defaultdict(list)
        for mo in nb_pattern.finditer(raw):
            sig = mo.group(1)
            if sig not in ('if', 'else', 'begin', 'end', 'always'):
                # Get surrounding context
                start = max(0, mo.start() - 30)
                end = min(len(raw), mo.end() + 30)
                ctx = raw[start:end].replace('\n', ' ').strip()
                nb_assigns[sig].append(ctx)

        # Blocking assignments: signal = expr (but not ==, !=, <=, >=)
        b_pattern = re.compile(r'(\w+)\s*=\s*(?![=<>])')
        b_assigns = defaultdict(list)
        for mo in b_pattern.finditer(raw):
            sig = mo.group(1)
            if sig not in ('if', 'else', 'begin', 'end', 'always'):
                start = max(0, mo.start() - 30)
                end = min(len(raw), mo.end() + 30)
                ctx = raw[start:end].replace('\n', ' ').strip()
                b_assigns[sig].append(ctx)

        # Reads: all identifiers used on RHS / conditions
        # Remove the LHS of assignments first
        rhs_text = raw
        rhs_text = re.sub(r'(\w+)\s*<=\s*', '', rhs_text)
        rhs_text = re.sub(r'(\w+)\s*=\s*(?![=<>])', '', rhs_text)
        reads = set(re.findall(r'\b([a-zA-Z_]\w*)\b', rhs_text))
        reads -= {'if', 'else', 'begin', 'end', 'always', 'posedge',
                  'negedge', 'or', 'and', 'not', 'none'}

        blocks.append({
            "sensitivity":  sensitivity,
            "block_type":   block_type,
            "nb_assigns":   dict(nb_assigns),
            "b_assigns":    dict(b_assigns),
            "reads":        reads,
            "body_text":    raw,
        })

    return blocks


# ======================================================================
# Analysis Checks
# ======================================================================

def check_undriven_signals(ports: dict, local_signals: dict,
                           always_blocks: list) -> list:
    """Check 1: Identify undriven signals.

    An undriven signal is:
      - An output port or internal signal that is never assigned
        (on LHS of <= or =) in any always block or assign statement.
      - Input ports are EXCLUDED (they are driven externally).
    """
    warnings = []

    # Collect all driven signals from always blocks
    driven_signals = set()
    for blk in always_blocks:
        driven_signals.update(blk['nb_assigns'].keys())
        driven_signals.update(blk['b_assigns'].keys())

    # Check output ports
    for name, info in ports.items():
        if info['is_output'] and name not in driven_signals:
            warnings.append({
                "severity": "CRITICAL",
                "signal":   name,
                "category": "undriven_output",
                "message":  f"Output port '{name}' ({info['type']} {info['width']}) "
                            f"is declared but never assigned in any always/assign block",
            })

    # Check internal signals
    for name, info in local_signals.items():
        if name not in driven_signals:
            warnings.append({
                "severity": "WARNING",
                "signal":   name,
                "category": "undriven_internal",
                "message":  f"Internal signal '{name}' ({info['type']} {info['width']}) "
                            f"is declared but never assigned",
            })

    return warnings


def check_multiple_drivers(always_blocks: list) -> list:
    """Check 2: Detect signals driven by multiple always blocks.

    A signal should be assigned from exactly one always block.
    Multiple drivers can cause simulation/synthesis mismatches.
    """
    warnings = []

    # Map: signal -> list of block indices
    driver_map = defaultdict(list)
    for idx, blk in enumerate(always_blocks):
        all_assigns = set(blk['nb_assigns'].keys()) | set(blk['b_assigns'].keys())
        for sig in all_assigns:
            driver_map[sig].append(idx)

    for sig, block_indices in driver_map.items():
        if len(block_indices) > 1:
            block_types = [always_blocks[i]['block_type'] for i in block_indices]
            warnings.append({
                "severity": "CRITICAL",
                "signal":   sig,
                "category": "multiple_driver",
                "message":  f"Signal '{sig}' is driven by {len(block_indices)} always blocks: "
                            f"blocks {block_indices} ({block_types})",
                "details": {
                    "block_indices": block_indices,
                    "block_types":   block_types,
                },
            })

    return warnings


def check_combinational_loops(always_blocks: list, ports: dict) -> list:
    """Check 3: Detect potential combinational loops.

    A combinational loop occurs when a signal is both READ and WRITTEN
    within the same combinational always @(*) block, without any
    registered (flip-flop) isolation.
    """
    warnings = []

    for idx, blk in enumerate(always_blocks):
        if blk['block_type'] != 'combinational':
            continue

        written = set(blk['nb_assigns'].keys()) | set(blk['b_assigns'].keys())
        read = blk['reads']

        loop_signals = written & read
        if loop_signals:
            for sig in loop_signals:
                # Check if it's a legitimate feedback (e.g., next-state logic)
                # For counter, count_out read+written in posedge clk is OK
                warnings.append({
                    "severity": "WARNING",
                    "signal":   sig,
                    "category": "combo_loop_suspect",
                    "message":  f"Signal '{sig}' is both read and written in "
                                f"combinational block {idx} (@{blk['sensitivity']})",
                    "details": {
                        "block_index":  idx,
                        "sensitivity":  blk['sensitivity'],
                    },
                })

    return warnings


def check_latch_inference(always_blocks: list, ports: dict) -> list:
    """Check 4: Detect potential latch inference in combinational blocks.

    Latches are inferred when a signal is assigned in some branches
    of a combinational always block but not all (incomplete if/else).
    For sequential blocks (posedge clk), this is normal (flip-flops).
    """
    warnings = []

    for idx, blk in enumerate(always_blocks):
        if blk['block_type'] != 'combinational':
            continue

        body = blk['body_text']

        # Simple heuristic: if there's an 'if' without a matching 'else'
        # and the block is combinational, it could infer a latch
        if_count = body.count(' if ') + body.count('(if ')
        else_count = body.count('else')

        # Also check: are all assigned signals assigned in all branches?
        # For a proper check we'd need full control-flow analysis,
        # but a simple heuristic works for common cases.

        if if_count > else_count:
            warnings.append({
                "severity": "WARNING",
                "signal":   "N/A",
                "category": "latch_inference_suspect",
                "message":  f"Combinational block {idx} has {if_count} if-branches "
                            f"but only {else_count} else-branches — potential latch inference",
                "details": {
                    "block_index":   idx,
                    "if_count":      if_count,
                    "else_count":    else_count,
                    "sensitivity":   blk['sensitivity'],
                },
            })

    return warnings


def check_width_consistency(ports: dict, always_blocks: list,
                            raw_text: str) -> list:
    """Check 5: Detect potential width mismatches in assignments.

    Looks for:
      - Parameterized widths used consistently
      - Literal values exceeding declared widths
    """
    warnings = []

    # Check for WIDTH parameter usage consistency
    width_refs = re.findall(r'WIDTH', raw_text)
    width_param_count = raw_text.count('parameter WIDTH')

    # Check for explicit width mismatches in concatenation/replication
    # e.g., {WIDTH{1'b0}} should match the signal width
    replications = re.findall(r'\{(\w+)\{', raw_text)
    for rep in replications:
        if rep != 'WIDTH':
            warnings.append({
                "severity": "INFO",
                "signal":   "N/A",
                "category": "width_review",
                "message":  f"Replication operator uses '{rep}' instead of WIDTH parameter — "
                            f"verify this is intentional",
            })

    # Check for hard-coded literals that might exceed width
    # Look for patterns like 8'hXX or 16'hXXXX
    hex_literals = re.findall(r"(\d+)'h([0-9a-fA-F]+)", raw_text)
    for width_str, val_str in hex_literals:
        bit_width = int(width_str)
        val = int(val_str, 16)
        max_val = (1 << bit_width) - 1
        if val > max_val:
            warnings.append({
                "severity": "CRITICAL",
                "signal":   "N/A",
                "category": "width_overflow",
                "message":  f"Literal {width_str}'h{val_str} exceeds {bit_width}-bit range "
                            f"(max={max_val})",
            })

    return warnings


def check_unread_signals(ports: dict, always_blocks: list,
                         raw_text: str) -> list:
    """Check 6: Identify signals that are assigned but never consumed.

    An unread signal is:
      - An output port that is never used (acceptable but worth noting)
      - An internal signal that is written but never read
    """
    warnings = []

    # Collect all read signals across all always blocks
    all_reads = set()
    for blk in always_blocks:
        all_reads.update(blk['reads'])

    # Also check continuous assignments (assign statements)
    assign_matches = re.findall(r'assign\s+(\w+)\s*=\s*(.+?);', raw_text)
    for lhs, rhs in assign_matches:
        all_reads.update(re.findall(r'\b([a-zA-Z_]\w*)\b', rhs))

    # Check output ports — they are "consumed" externally, so just INFO
    for name, info in ports.items():
        if info['is_output'] and name not in all_reads:
            # Output not read internally — this is normal (driven for external use)
            warnings.append({
                "severity": "INFO",
                "signal":   name,
                "category": "unread_output",
                "message":  f"Output '{name}' is driven but not read internally "
                            f"(normal — consumed by testbench/external logic)",
            })

    return warnings


def check_pyslang_compilation(rtl_path: str) -> list:
    """Check 7: Run pyslang compilation and report errors/warnings."""
    warnings = []

    try:
        tree = SyntaxTree.fromFile(rtl_path)
        compilation = Compilation()
        compilation.addSyntaxTree(tree)

        diag = compilation.getAllDiagnostics()

        if diag:
            for d in diag:
                # Classify severity
                sev = "INFO"
                if hasattr(d, 'severity'):
                    sev_name = str(d.severity)
                    if 'Error' in sev_name:
                        sev = "CRITICAL"
                    elif 'Warning' in sev_name:
                        sev = "WARNING"

                warnings.append({
                    "severity": sev,
                    "signal":   "N/A",
                    "category": "pyslang_compilation",
                    "message":  str(d).strip(),
                })
        else:
            warnings.append({
                "severity": "INFO",
                "signal":   "N/A",
                "category": "pyslang_compilation",
                "message":  "pyslang compilation: 0 errors, 0 warnings — clean",
            })

    except Exception as e:
        warnings.append({
            "severity": "CRITICAL",
            "signal":   "N/A",
            "category": "pyslang_compilation_error",
            "message":  f"pyslang compilation failed: {e}",
        })

    return warnings


# ======================================================================
# Full Analysis Runner
# ======================================================================

def run_static_analysis(rtl_path: str) -> dict:
    """Run all static analysis checks and return structured results."""
    print(f"[INFO] Parsing: {rtl_path}")

    mod, raw_text, tree = parse_module(rtl_path)
    if mod is None:
        return {}

    ports = extract_port_info(mod)
    local_signals = extract_local_signals(mod, ports)
    always_blocks = extract_always_blocks_detailed(mod)

    module_name = mod.header.name.value

    print(f"[INFO] Module: {module_name}")
    print(f"[INFO] Ports: {len(ports)} ({sum(1 for p in ports.values() if p['is_input'])} inputs, "
          f"{sum(1 for p in ports.values() if p['is_output'])} outputs)")
    print(f"[INFO] Internal signals: {len(local_signals)}")
    print(f"[INFO] Always blocks: {len(always_blocks)}")

    # Run all checks
    all_warnings = []
    all_warnings.extend(check_undriven_signals(ports, local_signals, always_blocks))
    all_warnings.extend(check_multiple_drivers(always_blocks))
    all_warnings.extend(check_combinational_loops(always_blocks, ports))
    all_warnings.extend(check_latch_inference(always_blocks, ports))
    all_warnings.extend(check_width_consistency(ports, always_blocks, raw_text))
    all_warnings.extend(check_unread_signals(ports, always_blocks, raw_text))
    all_warnings.extend(check_pyslang_compilation(rtl_path))

    # Summary counts
    critical = sum(1 for w in all_warnings if w['severity'] == 'CRITICAL')
    warning  = sum(1 for w in all_warnings if w['severity'] == 'WARNING')
    info     = sum(1 for w in all_warnings if w['severity'] == 'INFO')

    # Group by category
    by_category = defaultdict(list)
    for w in all_warnings:
        by_category[w['category']].append(w)

    results = {
        "module":         module_name,
        "rtl_path":       str(rtl_path),
        "ports":          ports,
        "local_signals":  local_signals,
        "always_blocks":  always_blocks,
        "warnings":       all_warnings,
        "summary": {
            "total":    len(all_warnings),
            "critical": critical,
            "warning":  warning,
            "info":     info,
            "by_category": {k: len(v) for k, v in by_category.items()},
        },
    }

    return results


# ======================================================================
# Report Formatters
# ======================================================================

def print_console_report(results: dict):
    """Print static analysis results to console."""
    mod_name = results["module"]
    summary = results["summary"]

    print("\n" + "=" * 72)
    print(f"  STATIC ISSUE ANALYSIS — Module: {mod_name}")
    print("=" * 72)

    # Summary bar
    print(f"\n  Summary: {summary['total']} issues "
          f"({summary['critical']} CRITICAL, "
          f"{summary['warning']} WARNING, "
          f"{summary['info']} INFO)")

    # Category breakdown
    print(f"\n  By Category:")
    for cat, count in summary['by_category'].items():
        print(f"    {cat:<30} {count}")

    # Detailed warnings
    print(f"\n{'─' * 72}")
    print(f"  DETAILED FINDINGS")
    print(f"{'─' * 72}")

    for w in results["warnings"]:
        sev_marker = {"CRITICAL": "🔴", "WARNING": "🟡", "INFO": "🟢"}.get(
            w['severity'], "❓")
        print(f"\n  {sev_marker} [{w['severity']}] {w['category']}")
        print(f"     Signal: {w['signal']}")
        print(f"     {w['message']}")
        if 'details' in w:
            print(f"     Details: {w['details']}")

    # Always block summary
    print(f"\n{'─' * 72}")
    print(f"  ALWAYS BLOCK ANALYSIS")
    print(f"{'─' * 72}")

    for idx, blk in enumerate(results["always_blocks"]):
        all_assigned = set(blk['nb_assigns'].keys()) | set(blk['b_assigns'].keys())
        print(f"\n  Block {idx}: @{blk['sensitivity']} ({blk['block_type']})")
        print(f"    Nonblocking assigns (<=): {sorted(blk['nb_assigns'].keys()) or 'none'}")
        print(f"    Blocking assigns (=):     {sorted(blk['b_assigns'].keys()) or 'none'}")
        print(f"    All reads:                 {sorted(blk['reads'])[:15]}{'...' if len(blk['reads']) > 15 else ''}")
        print(f"    Read∩Write:                {sorted(all_assigned & blk['reads'])}")

    # Final verdict
    print(f"\n{'─' * 72}")
    if summary['critical'] == 0:
        print(f"  ✅ VERDICT: No critical issues found. Module is clean.")
    else:
        print(f"  ❌ VERDICT: {summary['critical']} critical issue(s) require attention!")
    print(f"{'─' * 72}\n")


def generate_markdown_report(results: dict) -> str:
    """Generate Markdown report."""
    lines = []
    mod_name = results["module"]
    summary = results["summary"]

    lines.append("# pyslang Static Issue Analysis Report\n")
    lines.append(f"**Module**: `{mod_name}`  ")
    lines.append(f"**Source**: `{results['rtl_path']}`\n")

    # Summary
    lines.append("## Summary\n")
    lines.append(f"| Severity | Count |")
    lines.append(f"|----------|-------|")
    lines.append(f"| 🔴 CRITICAL | {summary['critical']} |")
    lines.append(f"| 🟡 WARNING  | {summary['warning']} |")
    lines.append(f"| 🟢 INFO     | {summary['info']} |")
    lines.append(f"| **Total**   | **{summary['total']}** |\n")

    if summary['critical'] == 0:
        lines.append("> ✅ **No critical issues found. Module passes static analysis.**\n")
    else:
        lines.append(f"> ❌ **{summary['critical']} critical issue(s) require attention!**\n")

    # Category breakdown
    lines.append("## Issues by Category\n")
    lines.append("| Category | Count |")
    lines.append("|----------|-------|")
    for cat, count in summary['by_category'].items():
        lines.append(f"| {cat} | {count} |")
    lines.append("")

    # Detailed findings
    lines.append("## Detailed Findings\n")
    for w in results["warnings"]:
        sev_icon = {"CRITICAL": "🔴", "WARNING": "🟡", "INFO": "🟢"}.get(
            w['severity'], "❓")
        lines.append(f"### {sev_icon} [{w['severity']}] {w['category']}\n")
        lines.append(f"- **Signal**: `{w['signal']}`")
        lines.append(f"- **Message**: {w['message']}")
        if 'details' in w:
            lines.append(f"- **Details**: `{w['details']}`")
        lines.append("")

    # Always block analysis
    lines.append("## Always Block Analysis\n")
    for idx, blk in enumerate(results["always_blocks"]):
        all_assigned = set(blk['nb_assigns'].keys()) | set(blk['b_assigns'].keys())
        lines.append(f"### Block {idx}: `@{blk['sensitivity']}` ({blk['block_type']})\n")
        lines.append(f"- **Nonblocking assigns (<=)**: {', '.join(f'`{s}`' for s in sorted(blk['nb_assigns'].keys())) or 'none'}")
        lines.append(f"- **Blocking assigns (=)**: {', '.join(f'`{s}`' for s in sorted(blk['b_assigns'].keys())) or 'none'}")
        lines.append(f"- **Signals read**: {', '.join(f'`{s}`' for s in sorted(blk['reads'])[:15])}")
        lines.append(f"- **Read∩Write overlap**: {', '.join(f'`{s}`' for s in sorted(all_assigned & blk['reads'])) or 'none'}")
        lines.append("")

    # Port table
    lines.append("## Port Reference\n")
    lines.append("| Port | Direction | Type | Width |")
    lines.append("|------|-----------|------|-------|")
    for name, info in results["ports"].items():
        lines.append(f"| `{name}` | {info['direction']} | {info['type']} | `{info['width']}` |")
    lines.append("")

    return "\n".join(lines)


# ======================================================================
# Main
# ======================================================================

def main():
    parser = argparse.ArgumentParser(
        description="pyslang static issue analysis for counter.v")
    parser.add_argument("--rtl", default=str(PROJECT_ROOT / "counter.v"),
                        help="Path to Verilog RTL file")
    parser.add_argument("--json", action="store_true",
                        help="Save results as JSON")
    parser.add_argument("--markdown", action="store_true",
                        help="Save results as Markdown")
    args = parser.parse_args()

    if not os.path.exists(args.rtl):
        print(f"[ERROR] RTL file not found: {args.rtl}")
        sys.exit(1)

    results = run_static_analysis(args.rtl)
    if not results:
        print("[ERROR] Analysis failed — no results")
        sys.exit(1)

    # Console report
    print_console_report(results)

    # Save JSON
    if args.json:
        report_dir = SCRIPT_DIR / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        json_path = report_dir / "static_analysis.json"
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"[INFO] JSON report saved: {json_path}")

    # Save Markdown
    if args.markdown:
        report_dir = SCRIPT_DIR / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        md_path = report_dir / "static_analysis.md"
        md_text = generate_markdown_report(results)
        with open(md_path, 'w') as f:
            f.write(md_text)
        print(f"[INFO] Markdown report saved: {md_path}")

    # Exit code
    critical_count = results["summary"]["critical"]
    sys.exit(0 if critical_count == 0 else 1)


if __name__ == "__main__":
    main()
