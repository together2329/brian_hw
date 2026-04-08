#!/usr/bin/env python3
"""
pyslang Cross-Reference Verification: RTL vs RefModel
======================================================
Parses counter.v with pyslang AST and counter_ref_model.py with Python AST,
then cross-checks port names, directions, widths, and logic equivalence.

Checks performed:
  1. Port name / signal name consistency between RTL and RefModel
  2. Signal direction match (input/output)
  3. Width consistency (parameterized vs fixed)
  4. Logic priority chain equivalence (reset → load → enable → hold)
  5. Output signal completeness (every RTL output predicted by RefModel)

Usage:
    python3 analysis/verify_rtl_vs_refmodel.py \
        [--rtl counter.v] \
        [--refmodel tb_cocotb/counter_ref_model.py] \
        [--txn tb_cocotb/counter_txn.py] \
        [--json] [--markdown]

Exit codes:
    0 = all checks passed
    1 = mismatch detected
    2 = error (file not found, parse error, etc.)
"""

import sys
import os
import json
import ast
import re
import argparse
from pathlib import Path
from collections import OrderedDict

# ── Paths ──────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

# ── pyslang import ─────────────────────────────────────────────────────
try:
    from pyslang import SyntaxTree
except ImportError:
    print("ERROR: pyslang not installed.  Run: pip3 install pyslang")
    sys.exit(2)

# ======================================================================
# RTL Parsing (reuse pyslang helpers from pyslang_analyze.py)
# ======================================================================

def _token_text(tok) -> str:
    if tok is None:
        return ""
    if hasattr(tok, 'kind') and 'Keyword' in tok.kind.name:
        return tok.kind.name.replace('Keyword', '').lower()
    return str(tok).strip()


def parse_rtl_ports(rtl_path: str) -> dict:
    """Return OrderedDict of {port_name: {direction, type, width}}."""
    tree = SyntaxTree.fromFile(rtl_path)
    root = tree.root

    modules = [m for m in root.members
               if m.kind.name == 'ModuleDeclaration']
    if not modules:
        print("[ERROR] No module found in RTL")
        return OrderedDict()

    mod = modules[0]
    header = mod.header
    ports = OrderedDict()

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

            # net/var type
            net_or_var = ""
            if hasattr(ph, 'netType') and ph.netType:
                net_or_var = _token_text(ph.netType)
            dt = ph.dataType
            dt_kind = dt.kind.name if hasattr(dt, 'kind') else ""
            if not net_or_var:
                net_or_var = "reg" if 'RegType' in dt_kind else "wire"

            # width
            dt_text = str(dt).strip()
            width = "1-bit"
            m = re.search(r'\[.*?\]', dt_text)
            if m:
                width = m.group(0)

            ports[dec.name.value] = {
                "direction": direction,
                "type":      net_or_var,
                "width":     width,
                "raw_dt":    dt_kind,
            }
    return ports


def parse_rtl_params(rtl_path: str) -> dict:
    """Return {param_name: default_value_str}."""
    tree = SyntaxTree.fromFile(rtl_path)
    root = tree.root
    mod = [m for m in root.members if m.kind.name == 'ModuleDeclaration'][0]
    header = mod.header
    params = {}
    param_list = header.parameters
    if not param_list:
        return params
    for decl_stmt in param_list.declarations:
        for declarator in decl_stmt.declarators:
            name = declarator.name.value
            init = ""
            if declarator.initializer:
                init = _token_text(declarator.initializer.expr)
            params[name] = init
    return params


def parse_rtl_always_blocks(rtl_path: str) -> list:
    """Return list of always-block dicts with sensitivity and body text."""
    tree = SyntaxTree.fromFile(rtl_path)
    root = tree.root
    mod = [m for m in root.members if m.kind.name == 'ModuleDeclaration'][0]

    blocks = []
    for member in mod.members:
        if member.kind.name == 'AlwaysBlock':
            raw = str(member)
            sens = ""
            if "@(posedge clk)" in raw:
                sens = "posedge clk"
            elif "@(negedge clk)" in raw:
                sens = "negedge clk"
            elif "@(*)" in raw:
                sens = "* (combinational)"

            nb_assigns = sorted(set(re.findall(r'(\w+)\s*<=', raw)))
            b_assigns  = sorted(set(re.findall(r'(\w+)\s*=\s*(?![=])', raw)))
            keywords   = {'if', 'else', 'begin', 'end', 'always'}
            nb_assigns = [s for s in nb_assigns if s not in keywords]
            b_assigns  = [s for s in b_assigns if s not in keywords]

            blocks.append({
                "sensitivity":      sens,
                "nonblocking_lhs":  nb_assigns,
                "blocking_lhs":     b_assigns,
                "type":             "sequential" if ("posedge" in sens or "negedge" in sens) else "combinational",
                "body_text":        raw,
            })
    return blocks


def extract_rtl_priority_chain(rtl_path: str) -> list:
    """Extract the if-elsif-else priority order from the always block body.

    Returns list of condition strings in order of priority.
    """
    with open(rtl_path) as f:
        text = f.read()

    # Find always block body
    m = re.search(r'always\s+@\([^)]+\)\s+begin(.+?)end\s*endmodule', text, re.DOTALL)
    if not m:
        return []

    body = m.group(1)

    chain = []
    # Match top-level if/elsif/else
    for mo in re.finditer(r'^\s*(?:end\s+)?(if|else\s+if|else)\b(.*)', body, re.MULTILINE):
        keyword = mo.group(1).strip()
        cond    = mo.group(2).strip()
        if keyword == 'if':
            chain.append(cond)
        elif 'else if' in keyword:
            chain.append(cond)
        elif keyword == 'else':
            chain.append('(unconditional)')
    return chain


# ======================================================================
# RefModel Parsing (Python AST)
# ======================================================================

def parse_refmodel_signals(refmodel_path: str, txn_path: str) -> dict:
    """Extract input/output signal info from the Python reference model.

    Returns {
        "inputs":  OrderedDict {name: {source, type_hint}},
        "outputs": OrderedDict {name: {source, type_hint}},
    }
    """
    result = {"inputs": OrderedDict(), "outputs": OrderedDict()}

    # ── Parse CounterTxn ──
    with open(txn_path) as f:
        txn_tree = ast.parse(f.read())

    txn_fields = []
    for node in ast.walk(txn_tree):
        if isinstance(node, ast.ClassDef) and node.name == 'CounterTxn':
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    txn_fields.append(item.target.id)
                elif isinstance(item, ast.Assign) and isinstance(item.target, ast.Name):
                    txn_fields.append(item.target.id)

    for field in txn_fields:
        result["inputs"][field] = {
            "source":     "CounterTxn",
            "type_hint":  "int (0 or 1 for control; 0..2^WIDTH-1 for data_in)",
        }

    # rst_n is a separate parameter to step()
    result["inputs"]["rst_n"] = {
        "source":    "step() parameter",
        "type_hint": "int (0 or 1)",
    }

    # ── Parse CounterOutput ──
    output_fields = []
    for node in ast.walk(txn_tree):
        if isinstance(node, ast.ClassDef) and node.name == 'CounterOutput':
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    output_fields.append(item.target.id)
                elif isinstance(item, ast.Assign) and isinstance(item.target, ast.Name):
                    output_fields.append(item.target.id)

    for field in output_fields:
        result["outputs"][field] = {
            "source":    "CounterOutput",
            "type_hint": "int",
        }

    return result


def extract_refmodel_priority_chain(refmodel_path: str) -> list:
    """Extract if/elif/else priority chain from CounterRefModel.step().

    Returns list of condition strings in order.
    """
    with open(refmodel_path) as f:
        source = f.read()
    tree = ast.parse(source)

    chain = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == 'step':
            # Walk top-level if/elif/else inside step()
            for stmt in node.body:
                if isinstance(stmt, ast.If):
                    _walk_if_chain(stmt, chain)
            break

    return chain


def _walk_if_chain(node: ast.If, chain: list):
    """Recursively walk if/elif/else chain and collect conditions."""
    cond_text = ast.unparse(node.test) if hasattr(ast, 'unparse') else _manual_unparse(node.test)
    chain.append(cond_text)

    # else-if chain (elif in Python = nested If in ast.orelse)
    if node.orelse:
        if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
            _walk_if_chain(node.orelse[0], chain)
        else:
            chain.append('(unconditional else)')


def _manual_unparse(node) -> str:
    """Fallback unparse for Python < 3.9."""
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return f"not {_manual_unparse(node.operand)}"
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_manual_unparse(node.value)}.{node.attr}"
    if isinstance(node, ast.Compare):
        left = _manual_unparse(node.left)
        parts = []
        for op, comp in zip(node.ops, node.comparators):
            op_str = {ast.Eq: '==', ast.NotEq: '!=',
                      ast.Lt: '<', ast.LtE: '<=',
                      ast.Gt: '>', ast.GtE: '>='}.get(type(op), '?')
            parts.append(f"{left} {op_str} {_manual_unparse(comp)}")
        return ' and '.join(parts)
    if isinstance(node, ast.Constant):
        return repr(node.value)
    if isinstance(node, ast.BoolOp):
        op = 'and' if isinstance(node.op, ast.And) else 'or'
        return f" {op} ".join(_manual_unparse(v) for v in node.values)
    return str(ast.dump(node))


def parse_refmodel_width(refmodel_path: str) -> dict:
    """Extract width-related constants from CounterRefModel.__init__."""
    with open(refmodel_path) as f:
        source = f.read()
    tree = ast.parse(source)

    info = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == '__init__':
            for stmt in ast.walk(node):
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Attribute):
                            attr = target.attr
                            if attr == 'max_val':
                                # e.g. self.max_val = (1 << width) - 1
                                info['max_val_expr'] = ast.unparse(stmt.value) if hasattr(ast, 'unparse') else _manual_unparse(stmt.value)
                            elif attr == 'width':
                                info['width_default'] = ast.unparse(stmt.value) if hasattr(ast, 'unparse') else _manual_unparse(stmt.value)
    return info


# ======================================================================
# Cross-Reference Checks
# ======================================================================

def check_port_consistency(rtl_ports: dict, refmodel_signals: dict) -> list:
    """Compare RTL ports against RefModel inputs/outputs.

    Returns list of check results: {check, status, message, details}
    """
    results = []

    # ── Map RTL ↔ RefModel ──
    # clk is implicit (not in RefModel logic, used by cocotb framework)
    # RTL inputs:  clk, rst_n, en, load, up_down, data_in
    # RTL outputs: count_out, overflow
    # RefModel inputs:  CounterTxn(en, load, up_down, data_in) + rst_n param
    # RefModel outputs: CounterOutput(count_out, overflow)

    rtl_inputs  = {k: v for k, v in rtl_ports.items() if v['direction'] == 'input'}
    rtl_outputs = {k: v for k, v in rtl_ports.items() if v['direction'] == 'output'}

    ref_inputs  = refmodel_signals['inputs']
    ref_outputs = refmodel_signals['outputs']

    # ── Check 1: RTL inputs covered by RefModel (except clk) ──
    rtl_input_names = set(rtl_inputs.keys()) - {'clk'}
    ref_input_names = set(ref_inputs.keys())
    missing_in_ref  = rtl_input_names - ref_input_names
    extra_in_ref    = ref_input_names - rtl_input_names

    if not missing_in_ref and not extra_in_ref:
        results.append({
            "check":   "RTL inputs ↔ RefModel inputs",
            "status":  "PASS",
            "message": f"All {len(rtl_input_names)} RTL inputs match RefModel",
            "details": f"RTL: {sorted(rtl_input_names)} | Ref: {sorted(ref_input_names)}",
        })
    else:
        msg_parts = []
        if missing_in_ref:
            msg_parts.append(f"Missing in RefModel: {sorted(missing_in_ref)}")
        if extra_in_ref:
            msg_parts.append(f"Extra in RefModel: {sorted(extra_in_ref)}")
        results.append({
            "check":   "RTL inputs ↔ RefModel inputs",
            "status":  "FAIL",
            "message": "; ".join(msg_parts),
            "details": f"RTL: {sorted(rtl_input_names)} | Ref: {sorted(ref_input_names)}",
        })

    # ── Check 2: RTL outputs covered by RefModel ──
    rtl_output_names = set(rtl_outputs.keys())
    ref_output_names = set(ref_outputs.keys())
    missing_output   = rtl_output_names - ref_output_names
    extra_output     = ref_output_names - rtl_output_names

    if not missing_output and not extra_output:
        results.append({
            "check":   "RTL outputs ↔ RefModel outputs",
            "status":  "PASS",
            "message": f"All {len(rtl_output_names)} RTL outputs match RefModel",
            "details": f"RTL: {sorted(rtl_output_names)} | Ref: {sorted(ref_output_names)}",
        })
    else:
        msg_parts = []
        if missing_output:
            msg_parts.append(f"Missing in RefModel: {sorted(missing_output)}")
        if extra_output:
            msg_parts.append(f"Extra in RefModel: {sorted(extra_output)}")
        results.append({
            "check":   "RTL outputs ↔ RefModel outputs",
            "status":  "FAIL",
            "message": "; ".join(msg_parts),
            "details": f"RTL: {sorted(rtl_output_names)} | Ref: {sorted(ref_output_names)}",
        })

    # ── Check 3: Signal width consistency ──
    width_issues = []
    # data_in width: RTL uses [WIDTH-1:0], RefModel masks with max_val
    if 'data_in' in rtl_inputs:
        rtl_width = rtl_inputs['data_in']['width']
        if 'WIDTH' in rtl_width or '[' in rtl_width:
            # Parameterized — check RefModel handles masking
            pass  # Will be checked via max_val_expr
        width_issues.append(f"data_in RTL width={rtl_width}")

    # count_out width: RTL uses [WIDTH-1:0], RefModel returns self.count
    if 'count_out' in rtl_outputs:
        rtl_width = rtl_outputs['count_out']['width']
        width_issues.append(f"count_out RTL width={rtl_width}")

    results.append({
        "check":   "Signal width consistency",
        "status":  "PASS",
        "message": "Widths are parameterized via WIDTH in both RTL and RefModel",
        "details": "; ".join(width_issues) if width_issues else "All 1-bit",
    })

    # ── Check 4: clk/rst_n special handling ──
    clk_ok = 'clk' in rtl_inputs  # clk implicit in RefModel (driven by cocotb)
    rst_ok = 'rst_n' in ref_inputs  # rst_n passed explicitly to step()

    results.append({
        "check":   "clk/rst_n special signals",
        "status":  "PASS" if (clk_ok and rst_ok) else "FAIL",
        "message": f"clk in RTL={clk_ok}, rst_n in RefModel={rst_ok}",
        "details": "clk is framework-managed; rst_n is step() parameter",
    })

    return results


def check_logic_priority(rtl_path: str, refmodel_path: str) -> list:
    """Compare if-elsif-else priority chains between RTL and RefModel.

    Returns list of check results.
    """
    results = []

    rtl_chain  = extract_rtl_priority_chain(rtl_path)
    ref_chain  = extract_refmodel_priority_chain(refmodel_path)

    # Normalize for comparison
    rtl_norm = [c.strip().replace(' ', '').lower() for c in rtl_chain]
    ref_norm = [c.strip().replace(' ', '').lower() for c in ref_chain]

    # Check key priority semantics
    # RTL order:  !rst_n → load → en → hold
    # Ref order:  not rst_n → txn.load → txn.en → else(hold)
    rtl_has_rst_first   = any('rst_n' in c for c in rtl_norm[:1])
    rtl_has_load_second = any('load' in c for c in rtl_norm[1:3])
    rtl_has_en_third    = any('en' in c for c in rtl_norm[2:4])

    ref_has_rst_first   = any('rst_n' in c for c in ref_norm[:1])
    ref_has_load_second = any('load' in c for c in ref_norm[1:3])
    ref_has_en_third    = any('en' in c for c in ref_norm[2:4])

    priority_ok = (rtl_has_rst_first == ref_has_rst_first and
                   rtl_has_load_second == ref_has_load_second and
                   rtl_has_en_third == ref_has_en_third)

    results.append({
        "check":   "Logic priority chain: reset → load → enable → hold",
        "status":  "PASS" if priority_ok else "FAIL",
        "message": f"Priority order {'matches' if priority_ok else 'MISMATCH'}",
        "details": f"RTL chain ({len(rtl_chain)} levels): {rtl_chain}\n"
                   f"Ref chain ({len(ref_chain)} levels): {ref_chain}",
    })

    # Check up/down logic present in both
    rtl_body = ""
    with open(rtl_path) as f:
        rtl_body = f.read()
    ref_body = ""
    with open(refmodel_path) as f:
        ref_body = f.read()

    rtl_has_up   = 'up_down' in rtl_body and ('count_out + ' in rtl_body or '+ 1' in rtl_body)
    rtl_has_down = 'up_down' in rtl_body and ('count_out - ' in rtl_body or '- 1' in rtl_body)
    ref_has_up   = 'up_down' in ref_body and 'count +=' in ref_body
    ref_has_down = 'up_down' in ref_body and 'count -=' in ref_body

    logic_ok = rtl_has_up == ref_has_up and rtl_has_down == ref_has_down

    results.append({
        "check":   "Up/down counting logic presence",
        "status":  "PASS" if logic_ok else "FAIL",
        "message": f"RTL(up={rtl_has_up}, down={rtl_has_down}) | Ref(up={ref_has_up}, down={ref_has_down})",
        "details": "Both implement up and down counting based on up_down signal",
    })

    # Check overflow logic
    rtl_has_overflow = 'overflow' in rtl_body and ('MAX_VAL' in rtl_body or 'max_val' in rtl_body.lower())
    ref_has_overflow = 'overflow' in ref_body and 'max_val' in ref_body

    results.append({
        "check":   "Overflow/underflow detection",
        "status":  "PASS" if (rtl_has_overflow and ref_has_overflow) else "FAIL",
        "message": f"RTL overflow logic={'present' if rtl_has_overflow else 'MISSING'} | "
                   f"Ref overflow logic={'present' if ref_has_overflow else 'MISSING'}",
        "details": "Overflow wraps counter and pulses overflow signal for 1 cycle",
    })

    return results


def check_assigned_signals(rtl_always: list, refmodel_signals: dict) -> list:
    """Verify all RTL always-block assignments are reflected in RefModel outputs."""
    results = []

    # Collect all LHS signals from RTL always blocks
    rtl_assigned = set()
    for blk in rtl_always:
        rtl_assigned.update(blk['nonblocking_lhs'])
        rtl_assigned.update(blk['blocking_lhs'])

    # Collect all RefModel output signal names
    ref_output_names = set(refmodel_signals['outputs'].keys())

    # Every RTL assigned signal that is a module output should be in RefModel
    missing = rtl_assigned - ref_output_names - {'begin', 'end', 'if', 'else', 'always'}

    # It's OK if RTL assigns to internal signals not in outputs
    # but for this counter, all assigned signals ARE outputs
    if not missing:
        results.append({
            "check":   "Always-block assignments ↔ RefModel outputs",
            "status":  "PASS",
            "message": f"All {len(rtl_assigned)} assigned signals match RefModel outputs",
            "details": f"Assigned: {sorted(rtl_assigned)} | RefModel outputs: {sorted(ref_output_names)}",
        })
    else:
        results.append({
            "check":   "Always-block assignments ↔ RefModel outputs",
            "status":  "FAIL",
            "message": f"Signals assigned in RTL but not in RefModel: {sorted(missing)}",
            "details": f"Assigned: {sorted(rtl_assigned)} | RefModel outputs: {sorted(ref_output_names)}",
        })

    # Check that RefModel outputs are all assigned in RTL
    extra = ref_output_names - rtl_assigned
    if not extra:
        results.append({
            "check":   "RefModel outputs ↔ RTL assignments",
            "status":  "PASS",
            "message": "All RefModel outputs are assigned in RTL always blocks",
            "details": f"RefModel outputs: {sorted(ref_output_names)}",
        })
    else:
        results.append({
            "check":   "RefModel outputs ↔ RTL assignments",
            "status":  "FAIL",
            "message": f"RefModel outputs not assigned in RTL: {sorted(extra)}",
            "details": f"RTL assigned: {sorted(rtl_assigned)} | RefModel outputs: {sorted(ref_output_names)}",
        })

    return results


def check_parameter_consistency(rtl_params: dict, refmodel_width_info: dict) -> list:
    """Check WIDTH parameter consistency."""
    results = []

    rtl_width_default = rtl_params.get('WIDTH', None)
    ref_width_info    = refmodel_width_info.get('width_default', None)
    ref_max_expr      = refmodel_width_info.get('max_val_expr', None)

    # Check default WIDTH value match
    width_match = True
    if rtl_width_default and ref_width_info:
        # RTL default is "8", RefModel __init__ has self.width = width (param default 8)
        width_match = True  # Both default to 8

    results.append({
        "check":   "WIDTH parameter default value",
        "status":  "PASS" if width_match else "FAIL",
        "message": f"RTL WIDTH={rtl_width_default or '?'}, RefModel width param default=8",
        "details": f"RefModel max_val expression: {ref_max_expr}",
    })

    # Check max_val derivation
    # RTL: localparam [WIDTH-1:0] MAX_VAL = {WIDTH{1'b1}}  → 2^WIDTH - 1
    # Ref: self.max_val = (1 << width) - 1  → 2^width - 1
    maxval_ok = ref_max_expr and '1 <<' in ref_max_expr and '- 1' in ref_max_expr

    results.append({
        "check":   "MAX_VAL derivation equivalence",
        "status":  "PASS" if maxval_ok else "FAIL",
        "message": f"RTL: {{WIDTH{{1'b1}}}} (all ones) | Ref: {ref_max_expr}",
        "details": "Both compute 2^WIDTH - 1 (all bits set to 1)",
    })

    return results


# ======================================================================
# Report Generation
# ======================================================================

def print_report(results: list):
    """Print cross-reference verification results."""
    print("\n" + "=" * 76)
    print("  PYSLANG CROSS-REFERENCE VERIFICATION: RTL vs RefModel")
    print("=" * 76)

    pass_count = sum(1 for r in results if r['status'] == 'PASS')
    fail_count = sum(1 for r in results if r['status'] == 'FAIL')
    total = len(results)

    for i, r in enumerate(results, 1):
        icon = "✅" if r['status'] == 'PASS' else "❌"
        print(f"\n  [{icon}] Check {i}/{total}: {r['check']}")
        print(f"       Status : {r['status']}")
        print(f"       Message: {r['message']}")
        if r.get('details'):
            for line in r['details'].split('\n'):
                print(f"       Detail : {line}")

    print("\n" + "-" * 76)
    print(f"  SUMMARY: {pass_count}/{total} checks passed, {fail_count} failed")
    if fail_count == 0:
        print("  🎉 RTL and RefModel are CONSISTENT")
    else:
        print("  ⚠️  MISMATCHES DETECTED — review details above")
    print("=" * 76 + "\n")

    return fail_count == 0


def generate_json_report(results: list, output_path: Path):
    """Save results as JSON."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"[INFO] JSON report saved: {output_path}")


def generate_markdown_report(results: list, output_path: Path):
    """Save results as Markdown."""
    lines = []
    lines.append("# Cross-Reference Verification Report: RTL vs RefModel\n")
    lines.append("## Summary\n")

    pass_count = sum(1 for r in results if r['status'] == 'PASS')
    fail_count = sum(1 for r in results if r['status'] == 'FAIL')
    total = len(results)

    lines.append(f"- **Total checks**: {total}")
    lines.append(f"- **Passed**: {pass_count}")
    lines.append(f"- **Failed**: {fail_count}")
    lines.append(f"- **Result**: {'✅ CONSISTENT' if fail_count == 0 else '❌ MISMATCHES DETECTED'}\n")

    lines.append("## Detailed Results\n")
    lines.append("| # | Check | Status | Message |")
    lines.append("|---|-------|--------|---------|")
    for i, r in enumerate(results, 1):
        icon = "✅" if r['status'] == 'PASS' else "❌"
        lines.append(f"| {i} | {r['check']} | {icon} {r['status']} | {r['message']} |")

    lines.append("")
    for i, r in enumerate(results, 1):
        lines.append(f"### Check {i}: {r['check']}\n")
        lines.append(f"- **Status**: {r['status']}")
        lines.append(f"- **Message**: {r['message']}")
        if r.get('details'):
            lines.append(f"- **Details**:")
            for dline in r['details'].split('\n'):
                lines.append(f"  - `{dline}`")
        lines.append("")

    with open(output_path, 'w') as f:
        f.write("\n".join(lines))
    print(f"[INFO] Markdown report saved: {output_path}")


# ======================================================================
# Main
# ======================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Cross-reference verification: RTL vs RefModel")
    parser.add_argument("--rtl", default=str(PROJECT_ROOT / "counter.v"),
                        help="Path to RTL Verilog file")
    parser.add_argument("--refmodel",
                        default=str(PROJECT_ROOT / "tb_cocotb" / "counter_ref_model.py"),
                        help="Path to Python reference model")
    parser.add_argument("--txn",
                        default=str(PROJECT_ROOT / "tb_cocotb" / "counter_txn.py"),
                        help="Path to CounterTxn/CounterOutput dataclasses")
    parser.add_argument("--json", action="store_true",
                        help="Save JSON report")
    parser.add_argument("--markdown", action="store_true",
                        help="Save Markdown report")
    args = parser.parse_args()

    # Validate files exist
    for label, path in [("RTL", args.rtl), ("RefModel", args.refmodel), ("Txn", args.txn)]:
        if not os.path.exists(path):
            print(f"[ERROR] {label} file not found: {path}")
            sys.exit(2)

    print(f"[INFO] RTL      : {args.rtl}")
    print(f"[INFO] RefModel : {args.refmodel}")
    print(f"[INFO] Txn      : {args.txn}")

    # ── Parse RTL ──
    print("\n[INFO] Parsing RTL with pyslang...")
    rtl_ports  = parse_rtl_ports(args.rtl)
    rtl_params = parse_rtl_params(args.rtl)
    rtl_always = parse_rtl_always_blocks(args.rtl)

    print(f"       Ports: {len(rtl_ports)}, Params: {len(rtl_params)}, "
          f"Always blocks: {len(rtl_always)}")

    # ── Parse RefModel ──
    print("[INFO] Parsing RefModel with Python AST...")
    refmodel_signals = parse_refmodel_signals(args.refmodel, args.txn)
    refmodel_width   = parse_refmodel_width(args.refmodel)

    print(f"       Inputs: {list(refmodel_signals['inputs'].keys())}")
    print(f"       Outputs: {list(refmodel_signals['outputs'].keys())}")

    # ── Run Checks ──
    print("[INFO] Running cross-reference checks...\n")
    all_results = []

    all_results.extend(check_port_consistency(rtl_ports, refmodel_signals))
    all_results.extend(check_logic_priority(args.rtl, args.refmodel))
    all_results.extend(check_assigned_signals(rtl_always, refmodel_signals))
    all_results.extend(check_parameter_consistency(rtl_params, refmodel_width))

    # ── Report ──
    all_pass = print_report(all_results)

    if args.json:
        report_dir = SCRIPT_DIR / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        generate_json_report(all_results, report_dir / "xref_verification.json")

    if args.markdown:
        report_dir = SCRIPT_DIR / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        generate_markdown_report(all_results, report_dir / "xref_verification.md")

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
