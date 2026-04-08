#!/usr/bin/env python3
"""
pyslang AST Analysis Script for counter.v
==========================================
Parses counter.v using pyslang and extracts:
  - Module name, parameters, localparams
  - Port information (name, direction, type, width)
  - Always blocks (sensitivity list, signal assignments)
  - Internal signal declarations
  - Module hierarchy (submodule instances)
  - Line-of-code metrics

Usage:
    python3 analysis/pyslang_analyze.py [--rtl path/to/counter.v] [--json] [--markdown]

Output:
    Console report + optional JSON/Markdown to analysis/reports/
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Add project root to path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

try:
    from pyslang import (
        SyntaxTree, Compilation,
        SyntaxKind, TokenKind,
    )
except ImportError:
    print("ERROR: pyslang not installed. Run: pip3 install pyslang")
    sys.exit(1)


# ======================================================================
# Helpers
# ======================================================================

def _token_text(tok) -> str:
    """Safely extract text from a pyslang token (strips trivia)."""
    if tok is None:
        return ""
    # Use kind name for keyword tokens to avoid trivia pollution
    if hasattr(tok, 'kind') and 'Keyword' in tok.kind.name:
        return tok.kind.name.replace('Keyword', '').lower()
    return str(tok).strip()


def _kind_name(obj) -> str:
    """Return the SyntaxKind name as a string."""
    return obj.kind.name if hasattr(obj, 'kind') else str(obj)


# ======================================================================
# 1. Module Metadata
# ======================================================================

def extract_module_metadata(mod):
    """Extract module name and basic metadata."""
    header = mod.header
    # Use kind name to avoid trivia (comments) attached to moduleKeyword
    mk = header.moduleKeyword
    mk_text = mk.kind.name.replace('Keyword', '').lower() if hasattr(mk, 'kind') else str(mk).strip()
    return {
        "module_name": header.name.value,
        "module_keyword": mk_text,
    }


# ======================================================================
# 2. Parameters
# ======================================================================

def extract_parameters(mod):
    """Extract parameter declarations (from header)."""
    params = []
    header = mod.header
    param_list = header.parameters
    if not param_list:
        return params

    for decl_stmt in param_list.declarations:
        keyword = _token_text(decl_stmt.keyword)
        for declarator in decl_stmt.declarators:
            name = declarator.name.value
            init_val = ""
            if declarator.initializer:
                init_val = _token_text(declarator.initializer.expr)
            params.append({
                "name": name,
                "keyword": keyword,       # "parameter"
                "type": _token_text(decl_stmt.type),
                "default": init_val,
            })
    return params


# ======================================================================
# 3. Localparams (from module body members)
# ======================================================================

def extract_localparams(mod):
    """Extract localparam declarations from module body."""
    localparams = []
    for member in mod.members:
        if member.kind.name == 'ParameterDeclarationStatement':
            param_decl = member.parameter
            keyword = _token_text(param_decl.keyword)
            if 'localparam' in keyword:
                for declarator in param_decl.declarators:
                    name = declarator.name.value
                    init_val = ""
                    if declarator.initializer:
                        init_val = _token_text(declarator.initializer.expr)
                    localparams.append({
                        "name": name,
                        "type": _token_text(param_decl.type),
                        "value": init_val,
                    })
    return localparams


# ======================================================================
# 4. Ports
# ======================================================================

def extract_ports(mod):
    """Extract port information: name, direction, net/var type, width."""
    ports = []
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

            ph = sub.header
            decl = sub.declarator

            # Direction: use kind name to avoid trivia pollution
            direction = _token_text(ph.direction)

            # Determine type: wire vs reg (from netType or dataType kind)
            net_or_var = ""
            if hasattr(ph, 'netType') and ph.netType:
                net_or_var = _token_text(ph.netType)
            elif hasattr(ph, 'varKeyword') and ph.varKeyword:
                net_or_var = "var"

            # If netType empty, infer from dataType kind
            dt = ph.dataType
            dt_kind = _kind_name(dt)
            if not net_or_var:
                if 'RegType' in dt_kind:
                    net_or_var = "reg"
                else:
                    net_or_var = "wire"

            # Width: extract from dataType text (e.g. "[WIDTH-1:0]")
            dt_text = str(dt).strip()
            # Clean trivia from dt_text (may have embedded comments)
            # Just look for bracket expressions
            width_spec = "1-bit"
            if '[' in dt_text:
                import re
                m = re.search(r'\[.*?\]', dt_text)
                if m:
                    width_spec = m.group(0)

            port_name = decl.name.value

            ports.append({
                "name": port_name,
                "direction": direction,
                "type": net_or_var,
                "width": width_spec,
                "data_type_kind": dt_kind,
            })
    return ports


# ======================================================================
# 5. Always Blocks
# ======================================================================

def extract_always_blocks(mod):
    """Extract always blocks with sensitivity and assigned signals."""
    blocks = []
    for member in mod.members:
        if member.kind.name == 'AlwaysBlock':
            stmt = member.statement
            stmt_text = str(stmt).strip()

            # Find signal assignments (left-hand side of <= or =)
            assigned_signals = set()
            _find_assignments(stmt, assigned_signals)

            # Detect sensitivity from raw text (pyslang doesn't expose it cleanly)
            raw = str(member).strip()
            sensitivity = ""
            if "@(posedge clk)" in raw:
                sensitivity = "posedge clk"
            elif "@(negedge clk)" in raw:
                sensitivity = "negedge clk"
            elif "@(*)" in raw or "@ *" in raw:
                sensitivity = "* (combinational)"

            blocks.append({
                "sensitivity": sensitivity,
                "assigned_signals": sorted(assigned_signals),
                "line_count": raw.count('\n') + 1,
                "type": "sequential" if "posedge" in sensitivity or "negedge" in sensitivity else "combinational",
            })
    return blocks


def _find_assignments(node, signals: set, depth=0):
    """Recursively find signal names on LHS of assignments."""
    if depth > 50:
        return
    kind_name = _kind_name(node)

    # Look for NonblockingAssignmentStatement or BlockingAssignmentStatement
    if 'Assignment' in kind_name and 'Statement' in kind_name:
        if hasattr(node, 'left'):
            lhs_text = _token_text(node.left) if node.left else ""
            if lhs_text:
                # Extract just the signal name (before any [ or .)
                sig = lhs_text.split('[')[0].split('.')[0].strip()
                if sig and not sig.startswith('//'):
                    signals.add(sig)

    # Recurse into children
    for attr_name in dir(node):
        if attr_name.startswith('_') or attr_name in ('kind', 'parent', 'sourceRange', 'to_json'):
            continue
        try:
            child = getattr(node, attr_name)
            if child is None:
                continue
            if hasattr(child, 'kind'):
                _find_assignments(child, signals, depth + 1)
            elif hasattr(child, '__iter__'):
                try:
                    for item in child:
                        if hasattr(item, 'kind'):
                            _find_assignments(item, signals, depth + 1)
                except TypeError:
                    pass
        except Exception:
            pass


# ======================================================================
# 6. Module Hierarchy (submodule instances)
# ======================================================================

def extract_hierarchy(mod):
    """Find submodule instantiations."""
    instances = []
    for member in mod.members:
        kind = _kind_name(member)
        # Hierarchy instantiation in pyslang syntax tree
        if 'Instance' in kind:
            inst_text = str(member).strip()
            instances.append({
                "raw": inst_text[:200],
            })
    return instances


# ======================================================================
# 7. Code Metrics
# ======================================================================

def compute_metrics(rtl_path: str, mod):
    """Compute basic code metrics."""
    with open(rtl_path, 'r') as f:
        lines = f.readlines()

    total_lines = len(lines)
    code_lines = sum(1 for l in lines if l.strip() and not l.strip().startswith('//'))
    comment_lines = sum(1 for l in lines if l.strip().startswith('//'))
    blank_lines = total_lines - code_lines - comment_lines

    # Count always blocks, if-else branches, etc.
    raw_text = ''.join(lines)
    always_count = raw_text.count('always @')
    if_count = raw_text.count('if (') + raw_text.count('if(')
    assign_count = raw_text.count('<=') + raw_text.count('= ') - if_count

    return {
        "total_lines": total_lines,
        "code_lines": code_lines,
        "comment_lines": comment_lines,
        "blank_lines": blank_lines,
        "always_blocks": always_count,
        "if_branches": if_count,
        "nonblocking_assignments": raw_text.count('<='),
    }


# ======================================================================
# 8. Full Analysis Runner
# ======================================================================

def analyze_rtl(rtl_path: str) -> dict:
    """Run full pyslang analysis on a Verilog file."""
    print(f"[INFO] Parsing: {rtl_path}")

    tree = SyntaxTree.fromFile(rtl_path)
    root = tree.root

    # Find module declarations
    modules = []
    for member in root.members:
        if member.kind.name == 'ModuleDeclaration':
            modules.append(member)

    if not modules:
        print("[ERROR] No module declarations found!")
        return {}

    results = {}
    for mod in modules:
        metadata = extract_module_metadata(mod)
        mod_name = metadata["module_name"]

        print(f"[INFO] Analyzing module: {mod_name}")

        analysis = {
            "metadata": metadata,
            "parameters": extract_parameters(mod),
            "localparams": extract_localparams(mod),
            "ports": extract_ports(mod),
            "always_blocks": extract_always_blocks(mod),
            "hierarchy": extract_hierarchy(mod),
            "metrics": compute_metrics(rtl_path, mod),
        }
        results[mod_name] = analysis

    return results


# ======================================================================
# 9. Report Formatters
# ======================================================================

def print_console_report(results: dict):
    """Print analysis results to console."""
    for mod_name, data in results.items():
        print("\n" + "=" * 70)
        print(f"  PYSLANG AST ANALYSIS REPORT — Module: {mod_name}")
        print("=" * 70)

        # Metadata
        meta = data["metadata"]
        print(f"\n--- Metadata ---")
        for k, v in meta.items():
            print(f"  {k}: {v}")

        # Parameters
        params = data["parameters"]
        print(f"\n--- Parameters ({len(params)}) ---")
        if params:
            print(f"  {'Name':<12} {'Type':<10} {'Default':<10}")
            print(f"  {'-'*12} {'-'*10} {'-'*10}")
            for p in params:
                print(f"  {p['name']:<12} {p['type'] or 'integer':<10} {p['default']:<10}")
        else:
            print("  (none)")

        # Localparams
        lps = data["localparams"]
        print(f"\n--- Localparams ({len(lps)}) ---")
        if lps:
            print(f"  {'Name':<12} {'Type':<15} {'Value':<20}")
            print(f"  {'-'*12} {'-'*15} {'-'*20}")
            for lp in lps:
                print(f"  {lp['name']:<12} {lp['type'] or 'inferred':<15} {lp['value']:<20}")
        else:
            print("  (none)")

        # Ports
        ports = data["ports"]
        print(f"\n--- Ports ({len(ports)}) ---")
        if ports:
            print(f"  {'Name':<12} {'Dir':<8} {'Type':<6} {'Width':<15}")
            print(f"  {'-'*12} {'-'*8} {'-'*6} {'-'*15}")
            for p in ports:
                print(f"  {p['name']:<12} {p['direction']:<8} {p['type']:<6} {p['width']:<15}")
        else:
            print("  (none)")

        # Always Blocks
        always = data["always_blocks"]
        print(f"\n--- Always Blocks ({len(always)}) ---")
        for i, blk in enumerate(always, 1):
            print(f"  Block {i}:")
            print(f"    Sensitivity : {blk['sensitivity']}")
            print(f"    Type        : {blk['type']}")
            print(f"    Assigns     : {', '.join(blk['assigned_signals'])}")
            print(f"    Lines       : {blk['line_count']}")

        # Hierarchy
        hier = data["hierarchy"]
        print(f"\n--- Submodule Instances ({len(hier)}) ---")
        if hier:
            for inst in hier:
                print(f"  {inst['raw']}")
        else:
            print("  (no submodule instances — leaf module)")

        # Metrics
        metrics = data["metrics"]
        print(f"\n--- Code Metrics ---")
        for k, v in metrics.items():
            print(f"  {k}: {v}")

    print("\n" + "=" * 70)
    print("  ANALYSIS COMPLETE")
    print("=" * 70 + "\n")


def generate_markdown_report(results: dict) -> str:
    """Generate Markdown report."""
    lines = []
    lines.append("# pyslang AST Analysis Report\n")
    lines.append(f"**Source**: `counter.v`\n")

    for mod_name, data in results.items():
        lines.append(f"## Module: `{mod_name}`\n")

        # Parameters
        params = data["parameters"]
        lines.append(f"### Parameters ({len(params)})\n")
        if params:
            lines.append("| Name | Type | Default |")
            lines.append("|------|------|---------|")
            for p in params:
                lines.append(f"| `{p['name']}` | {p['type'] or 'integer'} | `{p['default']}` |")
            lines.append("")

        # Localparams
        lps = data["localparams"]
        lines.append(f"### Localparams ({len(lps)})\n")
        if lps:
            lines.append("| Name | Type | Value |")
            lines.append("|------|------|-------|")
            for lp in lps:
                lines.append(f"| `{lp['name']}` | {lp['type'] or 'inferred'} | `{lp['value']}` |")
            lines.append("")

        # Ports
        ports = data["ports"]
        lines.append(f"### Ports ({len(ports)})\n")
        if ports:
            lines.append("| Name | Direction | Type | Width |")
            lines.append("|------|-----------|------|-------|")
            for p in ports:
                lines.append(f"| `{p['name']}` | {p['direction']} | {p['type']} | `{p['width']}` |")
            lines.append("")

        # Always Blocks
        always = data["always_blocks"]
        lines.append(f"### Always Blocks ({len(always)})\n")
        for i, blk in enumerate(always, 1):
            lines.append(f"**Block {i}** — `{blk['sensitivity']}` ({blk['type']})")
            lines.append(f"- Assigned signals: {', '.join(f'`{s}`' for s in blk['assigned_signals'])}")
            lines.append(f"- Lines of code: {blk['line_count']}\n")

        # Hierarchy
        hier = data["hierarchy"]
        lines.append(f"### Hierarchy\n")
        if hier:
            lines.append("Submodule instances found:")
            for inst in hier:
                lines.append(f"- `{inst['raw']}`")
        else:
            lines.append("Leaf module — no submodule instances.")
        lines.append("")

        # Metrics
        metrics = data["metrics"]
        lines.append(f"### Code Metrics\n")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        for k, v in metrics.items():
            lines.append(f"| {k} | {v} |")
        lines.append("")

    return "\n".join(lines)


# ======================================================================
# Main
# ======================================================================

def main():
    parser = argparse.ArgumentParser(description="pyslang AST analysis for counter.v")
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

    results = analyze_rtl(args.rtl)

    # Console report
    print_console_report(results)

    # Save JSON
    if args.json:
        report_dir = SCRIPT_DIR / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        json_path = report_dir / "pyslang_analysis.json"
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"[INFO] JSON report saved: {json_path}")

    # Save Markdown
    if args.markdown:
        report_dir = SCRIPT_DIR / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        md_path = report_dir / "pyslang_analysis.md"
        md_text = generate_markdown_report(results)
        with open(md_path, 'w') as f:
            f.write(md_text)
        print(f"[INFO] Markdown report saved: {md_path}")

    return results


if __name__ == "__main__":
    main()
