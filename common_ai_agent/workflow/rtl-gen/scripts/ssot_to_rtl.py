#!/usr/bin/env python3
"""SSOT-to-RTL preflight bridge with explicit ambiguity blocking.

This script validates that SSOT semantics and the SSOT-derived RTL TODO ledger
are ready, then checks for authored RTL files, filelist evidence, and RTL
authoring provenance. It does not turn SSOT rules into RTL by default; when
behavior or implementation evidence is missing, the script writes
<ip>/rtl/rtl_blocked.json and prints a focused [SSOT QUESTION] or
[RTL BLOCKED] instead of emitting fixed-template RTL.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
from typing import Any

import yaml


RUN_MODES = {"starter", "engineering", "signoff"}


def _normalize_run_mode(value: object) -> str:
    text = str(value or "signoff").strip().lower().replace("_", "-")
    aliases = {
        "eng": "engineering",
        "sign-off": "signoff",
        "preview": "starter",
    }
    text = aliases.get(text, text)
    if text not in RUN_MODES:
        raise SystemExit("[ssot_to_rtl] --mode must be starter, engineering, or signoff")
    return text


def _top_name(doc: dict, fallback: str) -> str:
    top = doc.get("top_module") or doc.get("top") or fallback
    if isinstance(top, dict):
        top = top.get("name") or fallback
    return str(top)


def _ident(s: str) -> str:
    s = re.sub(r"\W+", "_", str(s or "")).strip("_")
    if not s or not re.match(r"^[A-Za-z_]", s):
        s = "sig_" + s
    return s


def _as_ports(doc: dict) -> list[dict]:
    ports = []
    for p in doc.get("ports") or []:
        if isinstance(p, dict) and p.get("name"):
            ports.append({
                "name": _ident(p["name"]),
                "direction": str(p.get("direction") or "input").lower(),
                "width": p.get("width", 1),
            })
    if ports:
        return ports

    # Fallback for architect-style compact SSOTs.
    ports = [
        {"name": "clk", "direction": "input", "width": 1},
        {"name": "rst_n", "direction": "input", "width": 1},
    ]
    for bi in doc.get("busInterfaces") or []:
        if not isinstance(bi, dict):
            continue
        base = _ident(str(bi.get("name") or "bus").lower())
        role = str(bi.get("role") or "").lower()
        is_master = role == "master"
        ports.extend([
            {"name": f"{base}_addr", "direction": "output" if is_master else "input", "width": 16},
            {"name": f"{base}_wdata", "direction": "output" if is_master else "input", "width": 32},
            {"name": f"{base}_rdata", "direction": "input" if is_master else "output", "width": 32},
            {"name": f"{base}_valid", "direction": "output" if is_master else "input", "width": 1},
            {"name": f"{base}_write", "direction": "output" if is_master else "input", "width": 1},
            {"name": f"{base}_ready", "direction": "input" if is_master else "output", "width": 1},
        ])
    return ports


def _io_ports(doc: dict) -> list[dict]:
    ports: list[dict] = []
    io = doc.get("io_list") or {}
    if not isinstance(io, dict):
        return ports
    for cd in io.get("clock_domains") or []:
        for p in (cd or {}).get("ports") or []:
            if isinstance(p, dict) and p.get("name"):
                ports.append({
                    "name": _ident(p["name"]),
                    "direction": str(p.get("direction") or "input").lower(),
                    "width": p.get("width", 1),
                })
    for rst in io.get("resets") or []:
        for p in (rst or {}).get("ports") or []:
            if isinstance(p, dict) and p.get("name"):
                ports.append({
                    "name": _ident(p["name"]),
                    "direction": str(p.get("direction") or "input").lower(),
                    "width": p.get("width", 1),
                })
    for intf in io.get("interfaces") or []:
        for p in (intf or {}).get("ports") or []:
            if isinstance(p, dict) and p.get("name"):
                ports.append({
                    "name": _ident(p["name"]),
                    "direction": str(p.get("direction") or "input").lower(),
                    "width": p.get("width", 1),
                })
    seen = set()
    uniq = []
    for p in ports:
        if p["name"] in seen:
            continue
        seen.add(p["name"])
        uniq.append(p)
    return uniq


def _manifest_submodules(doc: dict) -> list[dict]:
    out = []
    for sm in doc.get("sub_modules") or []:
        if not isinstance(sm, dict) or not sm.get("name"):
            continue
        ownership = str(sm.get("ownership") or "manifest").strip().lower()
        if ownership in {"child_ssot", "conceptual", "verification", "coverage"} or sm.get("ssot"):
            continue
        if sm.get("rtl_emit") is False:
            continue
        out.append(sm)
    return out


def _sv_width_cast(width: int, expr: str) -> str:
    text = str(expr or "0").strip() or "0"
    width = max(width, 1)
    if width == 1:
        return _rtl_bool(text)
    cast_match = re.fullmatch(r"[0-9]+'\((.+)\)", text)
    if cast_match:
        return f"({cast_match.group(1)})"
    if re.fullmatch(rf"{width}'[hHdDbB][0-9a-fA-F_xXzZ]+", text):
        return text
    return f"({text})"


def _int_value(value, default: int = 0) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    text = str(value or "").strip().replace("_", "")
    if not text:
        return default
    try:
        if text.lower().startswith("0x"):
            return int(text, 16)
        if "'" in text:
            literal = text.lower()
            base_tag = literal.split("'", 1)[1][0]
            digits = literal.split(base_tag, 1)[1]
            digits = digits.replace("x", "0").replace("z", "0")
            return int(digits, {"h": 16, "d": 10, "b": 2}.get(base_tag, 10))
        return int(text, 10)
    except Exception:
        return default


def _rule_items(value) -> list[dict]:
    if isinstance(value, dict):
        return [{"name": key, "expr": expr} for key, expr in value.items()]
    return [item for item in value or [] if isinstance(item, dict)]


def _derived_signal_items(fm: dict) -> list[dict]:
    items: list[dict] = []
    for key in ("derived_signals", "intermediate_signals", "internal_signals", "combinational_signals"):
        raw = fm.get(key) if isinstance(fm, dict) else None
        for item in _rule_items(raw):
            if item not in items:
                items.append(item)
    return items


def _param_items(value) -> list[dict]:
    if isinstance(value, dict):
        return [{"name": key, "default": default} for key, default in value.items()]
    return [item for item in value or [] if isinstance(item, dict)]


def _normal_expr(expr) -> str:
    text = str(expr or "").strip()
    text = text.replace("&&", " and ").replace("||", " or ")
    return re.sub(r"(?<![=!<>])!(?!=)", " not ", text)


def _parse_rule_expr(expr: object) -> ast.AST:
    if isinstance(expr, bool):
        expr = "1" if expr else "0"
    elif isinstance(expr, int):
        expr = str(expr)
    text = _normal_expr(expr)
    if not text:
        text = "0"
    return ast.parse(text, mode="eval").body


def _expr_names(expr: object) -> set[str]:
    try:
        node = _parse_rule_expr(expr)
    except Exception:
        return set()
    names: set[str] = set()

    class Visitor(ast.NodeVisitor):
        def visit_Call(self, item: ast.Call) -> None:  # noqa: N802 - ast visitor API
            # Direct helper/function names such as reduction_or(expr) are not
            # transaction fields and must not become rtl_contract.input_map keys.
            for arg in item.args:
                self.visit(arg)
            for keyword in item.keywords:
                self.visit(keyword.value)

        def visit_Name(self, item: ast.Name) -> None:  # noqa: N802 - ast visitor API
            names.add(item.id)

    Visitor().visit(node)
    return names


def _rtl_const(value: object) -> str:
    if isinstance(value, bool):
        return "1'b1" if value else "1'b0"
    if isinstance(value, int):
        return str(value)
    text = str(value).strip()
    if re.fullmatch(r"[0-9]*'[hHdDbB][0-9a-fA-F_xXzZ]+", text):
        return text
    if re.fullmatch(r"0x[0-9a-fA-F_]+", text):
        return str(int(text.replace("_", ""), 16))
    if re.fullmatch(r"[0-9][0-9_]*", text):
        return text.replace("_", "")
    raise ValueError(f"unsupported constant {value!r}")


def _const_width(value: object) -> int:
    if isinstance(value, bool):
        return 1
    if isinstance(value, int):
        return max(value.bit_length(), 1)
    text = str(value).strip()
    match = re.fullmatch(r"([0-9]+)'[hHdDbB][0-9a-fA-F_xXzZ]+", text)
    if match:
        return max(int(match.group(1)), 1)
    if re.fullmatch(r"0x[0-9a-fA-F_]+", text):
        return max(int(text.replace("_", ""), 16).bit_length(), 1)
    if re.fullmatch(r"[0-9][0-9_]*", text):
        return max(int(text.replace("_", ""), 10).bit_length(), 1)
    return 32


def _ast_to_rtl_typed(
    node: ast.AST,
    env: dict[str, str],
    widths: dict[str, int],
    preferred_width: int | None = None,
) -> tuple[str, int]:
    if isinstance(node, ast.Expression):
        return _ast_to_rtl_typed(node.body, env, widths, preferred_width)
    if isinstance(node, ast.Constant):
        return _rtl_const(node.value), _const_width(node.value)
    if isinstance(node, ast.Name):
        if node.id in {"true", "True"}:
            return "1'b1", 1
        if node.id in {"false", "False"}:
            return "1'b0", 1
        if node.id not in env:
            raise KeyError(f"unknown name {node.id!r} in SSOT rule expression")
        return env[node.id], max(int(widths.get(node.id, 32) or 32), 1)
    if isinstance(node, ast.BinOp):
        left, left_w = _ast_to_rtl_typed(node.left, env, widths, preferred_width)
        right, right_w = _ast_to_rtl_typed(node.right, env, widths, preferred_width)
        ops = {
            ast.Add: "+",
            ast.Sub: "-",
            ast.Mult: "*",
            ast.FloorDiv: "/",
            ast.Div: "/",
            ast.Mod: "%",
            ast.LShift: "<<",
            ast.RShift: ">>",
            ast.BitAnd: "&",
            ast.BitOr: "|",
            ast.BitXor: "^",
        }
        op = ops.get(type(node.op))
        if op is None:
            raise ValueError(f"unsupported binary operator {type(node.op).__name__}")
        if isinstance(node.op, (ast.BitAnd, ast.BitOr, ast.BitXor)):
            width = max(left_w, right_w, int(preferred_width or 0), 1)
            return f"({_sv_width_cast(width, left)} {op} {_sv_width_cast(width, right)})", width
        if isinstance(node.op, (ast.LShift, ast.RShift)):
            width = max(left_w, int(preferred_width or 0), 1)
            return f"({_sv_width_cast(width, left)} {op} {right})", width
        width = max(left_w, right_w, int(preferred_width or 0), 1)
        return f"({left} {op} {right})", width
    if isinstance(node, ast.BoolOp):
        op = "&&" if isinstance(node.op, ast.And) else "||" if isinstance(node.op, ast.Or) else ""
        if not op:
            raise ValueError(f"unsupported boolean operator {type(node.op).__name__}")
        values = [_rtl_bool(_ast_to_rtl_typed(v, env, widths, 1)[0]) for v in node.values]
        return "(" + f" {op} ".join(values) + ")", 1
    if isinstance(node, ast.UnaryOp):
        operand, width = _ast_to_rtl_typed(node.operand, env, widths, preferred_width)
        if isinstance(node.op, ast.Not):
            return f"(!{_rtl_bool(operand)})", 1
        ops = {
            ast.UAdd: "+",
            ast.USub: "-",
            ast.Invert: "~",
        }
        op = ops.get(type(node.op))
        if op is None:
            raise ValueError(f"unsupported unary operator {type(node.op).__name__}")
        width = max(width, int(preferred_width or 0), 1)
        return f"({op}{_sv_width_cast(width, operand)})", width
    if isinstance(node, ast.Subscript):
        value, _value_w = _ast_to_rtl_typed(node.value, env, widths, None)
        slice_node = node.slice
        if isinstance(slice_node, ast.Constant):
            index = _rtl_const(slice_node.value)
            return f"{value}[{index}]", 1
        if isinstance(slice_node, ast.UnaryOp) and isinstance(slice_node.op, (ast.UAdd, ast.USub)):
            index, _index_w = _ast_to_rtl_typed(slice_node, env, widths, None)
            return f"{value}[{index}]", 1
        if isinstance(slice_node, ast.Slice):
            if slice_node.lower is None or slice_node.upper is None or slice_node.step is not None:
                raise ValueError("unsupported subscript slice")
            low, _low_w = _ast_to_rtl_typed(slice_node.lower, env, widths, None)
            high_exclusive, _high_w = _ast_to_rtl_typed(slice_node.upper, env, widths, None)
            if not re.fullmatch(r"[0-9]+", low) or not re.fullmatch(r"[0-9]+", high_exclusive):
                raise ValueError("unsupported dynamic subscript slice")
            high = max(int(high_exclusive) - 1, int(low))
            return f"{value}[{high}:{low}]", max(high - int(low) + 1, 1)
        index, _index_w = _ast_to_rtl_typed(slice_node, env, widths, None)
        return f"{value}[{index}]", 1
    if isinstance(node, ast.Compare):
        ops = {
            ast.Eq: "==",
            ast.NotEq: "!=",
            ast.Lt: "<",
            ast.LtE: "<=",
            ast.Gt: ">",
            ast.GtE: ">=",
        }
        left_node = node.left
        left, left_w = _ast_to_rtl_typed(left_node, env, widths, None)
        parts = []
        for op_node, comparator in zip(node.ops, node.comparators):
            op = ops.get(type(op_node))
            if op is None:
                raise ValueError(f"unsupported comparison {type(op_node).__name__}")
            right, right_w = _ast_to_rtl_typed(comparator, env, widths, None)
            width = max(left_w, right_w, 1)
            parts.append(f"({_sv_width_cast(width, left)} {op} {_sv_width_cast(width, right)})")
            left, left_w = right, right_w
        return "(" + " && ".join(_rtl_bool(part) for part in parts) + ")", 1
    if isinstance(node, ast.IfExp):
        test, _test_w = _ast_to_rtl_typed(node.test, env, widths, 1)
        body, body_w = _ast_to_rtl_typed(node.body, env, widths, preferred_width)
        other, other_w = _ast_to_rtl_typed(node.orelse, env, widths, preferred_width)
        width = max(body_w, other_w, int(preferred_width or 0), 1)
        return f"({_rtl_bool(test)} ? {_sv_width_cast(width, body)} : {_sv_width_cast(width, other)})", width
    if isinstance(node, ast.Call):
        func = node.func.id if isinstance(node.func, ast.Name) else ""
        args = list(node.args)
        if func in {"reduction_or", "reduce_or"} and len(args) == 1:
            arg, arg_w = _ast_to_rtl_typed(args[0], env, widths, None)
            return f"(|{_sv_width_cast(arg_w, arg)})", 1
        if func == "parity" and len(args) == 1:
            arg, arg_w = _ast_to_rtl_typed(args[0], env, widths, None)
            return f"(^{_sv_width_cast(arg_w, arg)})", 1
        raise ValueError(f"unsupported expression call {func or type(node.func).__name__}")
    raise ValueError(f"unsupported expression node {type(node).__name__}")


def _ast_to_rtl_width(
    node: ast.AST,
    env: dict[str, str],
    widths: dict[str, int],
    preferred_width: int | None = None,
) -> str:
    expr, _width = _ast_to_rtl_typed(node, env, widths, preferred_width)
    return expr


def _starter_wrap_nested(node: ast.AST, expr: str) -> str:
    if isinstance(node, (ast.Name, ast.Constant, ast.Subscript, ast.Call, ast.UnaryOp)):
        return expr
    return f"({expr})"


def _starter_cast(width: int, expr: str, expr_width: int | None = None) -> str:
    text = str(expr or "0").strip() or "0"
    width = max(int(width or 1), 1)
    if expr_width == width:
        return text
    if width == 1:
        return text if expr_width == 1 else f"(|{_sv_width_cast(max(int(expr_width or 1), 1), text)})"
    return _sv_width_cast(width, text)


def _starter_bool_expr(node: ast.AST, env: dict[str, str], widths: dict[str, int]) -> str:
    expr, width = _starter_ast_to_rtl_typed(node, env, widths, 1)
    if width == 1:
        return _starter_wrap_nested(node, expr)
    return f"(|{_sv_width_cast(width, expr)})"


def _starter_ast_to_rtl_typed(
    node: ast.AST,
    env: dict[str, str],
    widths: dict[str, int],
    preferred_width: int | None = None,
) -> tuple[str, int]:
    """Lower Starter rule expressions to reviewable RTL expressions.

    The LLM authoring contract and smoke harness share this readable expression
    form; this helper does not write a full RTL artifact.
    """

    if isinstance(node, ast.Expression):
        return _starter_ast_to_rtl_typed(node.body, env, widths, preferred_width)
    if isinstance(node, ast.Constant):
        return _rtl_const(node.value), _const_width(node.value)
    if isinstance(node, ast.Name):
        if node.id in {"true", "True"}:
            return "1'b1", 1
        if node.id in {"false", "False"}:
            return "1'b0", 1
        if node.id not in env:
            raise KeyError(f"unknown name {node.id!r} in SSOT rule expression")
        return env[node.id], max(int(widths.get(node.id, 32) or 32), 1)
    if isinstance(node, ast.BoolOp):
        op = "&" if isinstance(node.op, ast.And) else "|" if isinstance(node.op, ast.Or) else ""
        if not op:
            raise ValueError(f"unsupported boolean operator {type(node.op).__name__}")
        parts = [_starter_bool_expr(value, env, widths) for value in node.values]
        return f" {op} ".join(parts), 1
    if isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.Not):
            return f"~{_starter_bool_expr(node.operand, env, widths)}", 1
        operand, width = _starter_ast_to_rtl_typed(node.operand, env, widths, preferred_width)
        ops = {ast.UAdd: "+", ast.USub: "-", ast.Invert: "~"}
        op = ops.get(type(node.op))
        if op is None:
            raise ValueError(f"unsupported unary operator {type(node.op).__name__}")
        width = max(width, int(preferred_width or 0), 1)
        return f"{op}{_sv_width_cast(width, operand)}", width
    if isinstance(node, ast.BinOp):
        left, left_w = _starter_ast_to_rtl_typed(node.left, env, widths, preferred_width)
        right, right_w = _starter_ast_to_rtl_typed(node.right, env, widths, preferred_width)
        ops = {
            ast.Add: "+",
            ast.Sub: "-",
            ast.Mult: "*",
            ast.FloorDiv: "/",
            ast.Div: "/",
            ast.Mod: "%",
            ast.LShift: "<<",
            ast.RShift: ">>",
            ast.BitAnd: "&",
            ast.BitOr: "|",
            ast.BitXor: "^",
        }
        op = ops.get(type(node.op))
        if op is None:
            raise ValueError(f"unsupported binary operator {type(node.op).__name__}")
        if isinstance(node.op, (ast.BitAnd, ast.BitOr, ast.BitXor)):
            width = max(left_w, right_w, int(preferred_width or 0), 1)
            if width == left_w == right_w == 1:
                return f"{_starter_wrap_nested(node.left, left)} {op} {_starter_wrap_nested(node.right, right)}", 1
            return f"({_starter_cast(width, left, left_w)} {op} {_starter_cast(width, right, right_w)})", width
        if isinstance(node.op, (ast.LShift, ast.RShift)):
            width = max(left_w, int(preferred_width or 0), 1)
            return f"({_starter_cast(width, left, left_w)} {op} {right})", width
        width = max(left_w, right_w, int(preferred_width or 0), 1)
        return f"({left} {op} {right})", width
    if isinstance(node, ast.Compare):
        ops = {
            ast.Eq: "==",
            ast.NotEq: "!=",
            ast.Lt: "<",
            ast.LtE: "<=",
            ast.Gt: ">",
            ast.GtE: ">=",
        }
        left_node = node.left
        left, left_w = _starter_ast_to_rtl_typed(left_node, env, widths, None)
        parts: list[str] = []
        for op_node, comparator in zip(node.ops, node.comparators):
            op = ops.get(type(op_node))
            if op is None:
                raise ValueError(f"unsupported comparison {type(op_node).__name__}")
            right, right_w = _starter_ast_to_rtl_typed(comparator, env, widths, None)
            parts.append(f"{left} {op} {right}")
            left, left_w = right, right_w
        return " & ".join(f"({part})" for part in parts), 1
    if isinstance(node, ast.IfExp):
        test = _starter_bool_expr(node.test, env, widths)
        body, body_w = _starter_ast_to_rtl_typed(node.body, env, widths, preferred_width)
        other, other_w = _starter_ast_to_rtl_typed(node.orelse, env, widths, preferred_width)
        width = max(body_w, other_w, int(preferred_width or 0), 1)
        return f"({test} ? {_starter_cast(width, body, body_w)} : {_starter_cast(width, other, other_w)})", width
    if isinstance(node, ast.Subscript):
        value, _value_w = _starter_ast_to_rtl_typed(node.value, env, widths, None)
        slice_node = node.slice
        if isinstance(slice_node, ast.Constant):
            index = _rtl_const(slice_node.value)
            return f"{value}[{index}]", 1
        if isinstance(slice_node, ast.UnaryOp) and isinstance(slice_node.op, (ast.UAdd, ast.USub)):
            index, _index_w = _starter_ast_to_rtl_typed(slice_node, env, widths, None)
            return f"{value}[{index}]", 1
        if isinstance(slice_node, ast.Slice):
            if slice_node.lower is None or slice_node.upper is None or slice_node.step is not None:
                raise ValueError("unsupported subscript slice")
            low, _low_w = _starter_ast_to_rtl_typed(slice_node.lower, env, widths, None)
            high_exclusive, _high_w = _starter_ast_to_rtl_typed(slice_node.upper, env, widths, None)
            if not re.fullmatch(r"[0-9]+", low) or not re.fullmatch(r"[0-9]+", high_exclusive):
                raise ValueError("unsupported dynamic subscript slice")
            high = max(int(high_exclusive) - 1, int(low))
            return f"{value}[{high}:{low}]", max(high - int(low) + 1, 1)
        index, _index_w = _starter_ast_to_rtl_typed(slice_node, env, widths, None)
        return f"{value}[{index}]", 1
    if isinstance(node, ast.Call):
        func = node.func.id if isinstance(node.func, ast.Name) else ""
        args = list(node.args)
        if func in {"reduction_or", "reduce_or"} and len(args) == 1:
            arg, arg_w = _starter_ast_to_rtl_typed(args[0], env, widths, None)
            return f"(|{_sv_width_cast(arg_w, arg)})", 1
        if func == "parity" and len(args) == 1:
            arg, arg_w = _starter_ast_to_rtl_typed(args[0], env, widths, None)
            return f"(^{_sv_width_cast(arg_w, arg)})", 1
        raise ValueError(f"unsupported expression call {func or type(node.func).__name__}")
    raise ValueError(f"unsupported expression node {type(node).__name__}")


def _starter_assign_expr(
    node: ast.AST,
    env: dict[str, str],
    widths: dict[str, int],
    output_width: int,
) -> str:
    expr, expr_width = _starter_ast_to_rtl_typed(node, env, widths, output_width)
    output_width = max(int(output_width or 1), 1)
    if output_width == expr_width:
        return expr
    return _starter_cast(output_width, expr, expr_width)


def _rtl_bool(expr: str) -> str:
    text = str(expr or "").strip()
    if text in {"1'b1", "1", "true", "True"}:
        return "1'b1"
    if text in {"1'b0", "0", "false", "False"}:
        return "1'b0"
    return f"(({text}) != 0)"


def _rtl_eval_ref(name: str, width: int) -> str:
    return name


def _port_width(port: dict) -> int:
    return max(_int_value(port.get("width"), 1), 1)


def _find_clock_reset(ports: list[dict], contract: dict) -> tuple[str, str, str, list[dict]]:
    by_name = {p["name"]: p for p in ports}
    clock = _ident(contract.get("clock") or contract.get("clk") or "")
    if not clock:
        clock = next((p["name"] for p in ports if p["name"].lower() in {"clk", "clock", "pclk"}), "")
    reset = _ident(contract.get("reset") or contract.get("rst") or "")
    if not reset:
        reset = next((p["name"] for p in ports if p["name"].lower() in {"rst_n", "resetn", "presetn", "rst", "reset"}), "")
    reset_active = str(contract.get("reset_active") or ("low" if reset.endswith("_n") or reset.endswith("n") else "high")).lower()
    questions = []
    if not clock or clock not in by_name or by_name[clock].get("direction") != "input":
        questions.append(_question(
            "RTL_CLOCK_PORT",
            "Define a concrete input clock port for generated sequential RTL.",
            "The RTL authoring contract needs rtl_contract.clock or an input port named clk/clock/pclk.",
            ["Add rtl_contract.clock: <clock_port> and ensure io_list declares it as input."],
            "Declare the clock explicitly under rtl_contract.clock.",
            "rtl-gen can hand precise clocking context to the LLM author and compile/lint evidence.",
        ))
    if not reset or reset not in by_name or by_name[reset].get("direction") != "input":
        questions.append(_question(
            "RTL_RESET_PORT",
            "Define a concrete input reset port and active level.",
            "The RTL authoring contract needs rtl_contract.reset and rtl_contract.reset_active.",
            ["Add rtl_contract.reset: <reset_port> and rtl_contract.reset_active: low|high."],
            "Declare reset and active level explicitly under rtl_contract.",
            "LLM-authored RTL, FL reset behavior, and TB reset sequence share the same contract.",
        ))
    if reset_active not in {"low", "high"}:
        questions.append(_question(
            "RTL_RESET_ACTIVE_LEVEL",
            "Choose reset active level.",
            f"rtl_contract.reset_active={reset_active!r} is not low or high.",
            ["low", "high"],
            "Use low for *_n reset ports and high otherwise.",
            "Generated RTL reset sensitivity and TB reset driving become unambiguous.",
        ))
    return clock, reset, reset_active, questions


def _find_rule_transaction(doc: dict, contract: dict) -> tuple[dict, list[dict]]:
    fm = doc.get("function_model") if isinstance(doc.get("function_model"), dict) else {}
    if _rule_items(fm.get("output_rules")) or _rule_items(fm.get("state_updates")):
        return fm, []
    transactions = [tx for tx in fm.get("transactions") or [] if isinstance(tx, dict)]
    requested = str(contract.get("transaction") or contract.get("transaction_id") or "").strip().lower()
    selected: dict = {}
    if requested:
        for tx in transactions:
            if str(tx.get("id") or "").strip().lower() == requested or str(tx.get("name") or "").strip().lower() == requested:
                selected = tx
                break
    if not selected:
        for tx in transactions:
            if _rule_items(tx.get("output_rules")):
                selected = tx
                break
    if selected:
        return selected, []
    return {}, [_question(
        "FM_OUTPUT_RULES",
        "Define executable function_model output_rules for at least one transaction.",
        "The RTL authoring contract needs machine-checkable output rules before implementation can be verified.",
        ["Add function_model.transactions[].output_rules with name/expr/width entries."],
        "Put datapath behavior in output_rules and keep prose as description only.",
        "FL model, LLM-authored RTL, scoreboard expected values, and coverage goals share the same rule ledger.",
    )]


def _lower_rule_expr(
    raw_expr: object,
    env: dict[str, str],
    widths: dict[str, int],
    output_width: int,
    *,
    readable: bool = False,
) -> str:
    node = _parse_rule_expr(raw_expr)
    if readable:
        return _starter_assign_expr(node, env, widths, output_width)
    return _ast_to_rtl_width(node, env, widths, output_width)


def _cast_rule_expr(width: int, expr: str, *, readable: bool = False) -> str:
    text = str(expr or "0").strip() or "0"
    if readable:
        return text
    width = max(int(width or 1), 1)
    if width == 1:
        return _rtl_bool(text)
    if re.fullmatch(rf"{width}'[hHdDbB][0-9a-fA-F_xXzZ]+", text):
        return text
    if re.fullmatch(r"[0-9]+'\(.+\)", text):
        return text
    return f"{width}'({text})"


def _generic_rule_contract(
    doc: dict,
    top: str,
    ports: list[dict],
    *,
    readable: bool = False,
) -> tuple[dict, list[dict]]:
    contract = doc.get("rtl_contract") if isinstance(doc.get("rtl_contract"), dict) else {}
    tx, questions = _find_rule_transaction(doc, contract)
    if questions:
        return {}, questions

    output_rules = _rule_items(contract.get("output_rules")) or _rule_items(tx.get("output_rules"))
    state_updates = _rule_items(contract.get("state_updates")) or _rule_items(tx.get("state_updates"))
    if not output_rules:
        return {}, [_question(
            "RTL_OUTPUT_RULES",
            "Define at least one output rule that maps a FunctionalModel observable to a DUT output port.",
            "Structured state updates alone are not enough to produce externally checkable RTL.",
            ["Add output_rules entries with name, expr, width, and port."],
            "Each output rule should identify the DUT output port it drives.",
            "RTL and scoreboard evidence can compare the same named observable.",
        )]

    by_name = {p["name"]: p for p in ports}
    output_ports = {p["name"] for p in ports if str(p.get("direction")).lower() in {"output", "inout"}}
    input_ports = {p["name"] for p in ports if str(p.get("direction")).lower() in {"input", "inout"}}
    clock, reset, reset_active, clock_reset_questions = _find_clock_reset(ports, contract)
    questions.extend(clock_reset_questions)

    input_map = contract.get("input_map") if isinstance(contract.get("input_map"), dict) else {}
    output_map = contract.get("output_map") if isinstance(contract.get("output_map"), dict) else {}
    env: dict[str, str] = {"true": "1'b1", "false": "1'b0", "True": "1'b1", "False": "1'b0"}
    sample_env: dict[str, str] = {"true": "1'b1", "false": "1'b0", "True": "1'b1", "False": "1'b0"}
    env_widths: dict[str, int] = {"true": 1, "false": 1, "True": 1, "False": 1}
    sample_env_widths: dict[str, int] = {"true": 1, "false": 1, "True": 1, "False": 1}
    port_widths = {p["name"]: _port_width(p) for p in ports}
    for port in ports:
        env[port["name"]] = _rtl_eval_ref(port["name"], _port_width(port))
        sample_env[port["name"]] = port["name"]
        env_widths[port["name"]] = _port_width(port)
        sample_env_widths[port["name"]] = _port_width(port)
    for param in _param_items(doc.get("parameters")):
        name = _ident(param.get("name") or "")
        if not name:
            continue
        value = _int_value(param.get("default", param.get("value", 0)), 0)
        env[name] = str(value)
        sample_env[name] = str(value)
        width = max(int(value).bit_length(), 1)
        env_widths[name] = width
        sample_env_widths[name] = width
    for field, port in input_map.items():
        port_name = _ident(port)
        env[_ident(field)] = _rtl_eval_ref(port_name, port_widths.get(port_name, 32))
        sample_env[_ident(field)] = port_name
        env_widths[_ident(field)] = port_widths.get(port_name, 32)
        sample_env_widths[_ident(field)] = port_widths.get(port_name, 32)

    state_vars: dict[str, dict] = {}
    fm = doc.get("function_model") if isinstance(doc.get("function_model"), dict) else {}
    for idx, item in enumerate(fm.get("state_variables") or []):
        if not isinstance(item, dict):
            continue
        name = _ident(item.get("name") or f"state_{idx}")
        width = _port_width(by_name[name]) if name in by_name else max(_int_value(item.get("width"), 32), 1)
        state_vars[name] = {
            "width": width,
            "reset": _int_value(item.get("reset"), 0),
        }
        env[name] = _rtl_eval_ref(name, int(state_vars[name]["width"]))
        sample_env[name] = name
        env_widths[name] = int(state_vars[name]["width"])
        sample_env_widths[name] = int(state_vars[name]["width"])
    for idx, rule in enumerate(state_updates):
        name = _ident(rule.get("name") or rule.get("state") or f"state_{idx}")
        state_vars.setdefault(name, {
            "width": _port_width(by_name[name]) if name in by_name else max(_int_value(rule.get("width"), 32), 1),
            "reset": _int_value(rule.get("reset"), 0),
        })
        env[name] = _rtl_eval_ref(name, int(state_vars[name]["width"]))
        sample_env[name] = name
        env_widths[name] = int(state_vars[name]["width"])
        sample_env_widths[name] = int(state_vars[name]["width"])

    derived_pending: list[dict] = []
    for item in _derived_signal_items(fm):
        name = _ident(item.get("name") or item.get("signal") or item.get("id") or "")
        raw_expr = item.get("expr", item.get("expression", item.get("value")))
        if not name or raw_expr is None or str(raw_expr).strip() == "":
            continue
        derived_pending.append({
            "name": name,
            "raw_expr": raw_expr,
            "width": max(_int_value(item.get("width"), 32), 1),
        })
    derived_names = {item["name"] for item in derived_pending}
    unresolved_derived_errors: dict[str, str] = {}
    while derived_pending:
        progressed = False
        next_pending: list[dict] = []
        for item in derived_pending:
            name = item["name"]
            raw_expr = item["raw_expr"]
            width = int(item["width"])
            missing_derived_deps = (_expr_names(raw_expr) & derived_names) - set(env)
            if missing_derived_deps:
                next_pending.append(item)
                continue
            try:
                expr = _lower_rule_expr(raw_expr, env, env_widths, width, readable=readable)
            except Exception as exc:
                still_missing = (_expr_names(raw_expr) & derived_names) - set(env)
                if still_missing:
                    next_pending.append(item)
                    continue
                unresolved_derived_errors[name] = str(exc)
                continue
            casted = _sv_cast(width, expr)
            env[name] = casted
            sample_env[name] = casted
            env_widths[name] = width
            sample_env_widths[name] = width
            progressed = True
        if not next_pending:
            break
        if progressed:
            derived_pending = next_pending
            continue
        for item in next_pending:
            deps = sorted((_expr_names(item["raw_expr"]) & derived_names) - set(env))
            unresolved_derived_errors[item["name"]] = (
                f"unresolved derived signal dependency: {', '.join(deps)}"
                if deps
                else "derived signal expression could not be lowered"
            )
        break

    # Infer field-to-port bindings only when the SSOT uses the same name for
    # the transaction field and DUT input. Ambiguous names remain blockers.
    needed_names: set[str] = set()
    for rule in output_rules + state_updates:
        needed_names |= _expr_names(rule.get("expr", rule.get("expression", rule.get("value", 0))))
    def _default_sample_condition() -> str:
        for name in ("cfg_valid", "valid", "in_valid"):
            if name in input_ports:
                return name
        return next((name for name in sorted(input_ports) if name.endswith("_valid")), "1")

    def _default_output_expr() -> str:
        for name in ("cfg_data", "data_in", "input_data", "in_data"):
            if name in input_ports:
                return name
        wide_inputs = [
            p["name"] for p in ports
            if str(p.get("direction")).lower() == "input"
            and p["name"] not in {clock, reset}
            and _port_width(p) > 1
        ]
        return wide_inputs[0] if wide_inputs else "0"

    sample_condition = contract.get("sample_condition") or _default_sample_condition()
    needed_names |= _expr_names(sample_condition)
    for name in sorted(needed_names):
        if name in env or name in {"true", "false", "True", "False"}:
            continue
        if name in derived_names:
            questions.append(_question(
                f"RTL_DERIVED_EXPR_{_ident(name).upper()}",
                f"Rewrite derived signal {name!r} using the supported expression DSL.",
                unresolved_derived_errors.get(name, f"Derived signal {name!r} could not be lowered to RTL."),
                ["Use integer, field names, helper names, +, -, *, /, %, <<, >>, &, |, ^, comparisons, if/else expressions, and Python-style and/or/not."],
                "Keep derived_signals machine-checkable and order-independent.",
                "Output rules can reuse SSOT helper signals without treating them as DUT input ports.",
            ))
            continue
        if name in input_ports:
            env[name] = _rtl_eval_ref(name, port_widths.get(name, 32))
            sample_env[name] = name
            env_widths[name] = port_widths.get(name, 32)
            sample_env_widths[name] = port_widths.get(name, 32)
            continue
        questions.append(_question(
            f"RTL_INPUT_MAP_{_ident(name).upper()}",
            f"Map transaction field/expression name {name!r} to a DUT input port.",
            f"Rule expressions reference {name!r}, but rtl_contract.input_map does not bind it to an input port.",
            [f"Add rtl_contract.input_map.{name}: <input_port>."],
            "Use explicit input_map entries for every transaction field used by output_rules/sample_condition.",
            "RTL authoring can connect the SSOT transaction vocabulary to concrete DUT pins.",
        ))

    pending_outputs: list[dict] = []
    all_output_aliases: set[str] = set()
    for idx, rule in enumerate(output_rules):
        name = _ident(rule.get("name") or rule.get("output") or rule.get("port") or f"output_{idx}")
        port = _ident(rule.get("port") or output_map.get(name) or output_map.get(rule.get("name")) or name)
        if port not in output_ports:
            questions.append(_question(
                f"RTL_OUTPUT_MAP_{name.upper()}",
                f"Map output rule {name!r} to a DUT output port.",
                f"Rule {name!r} targets port {port!r}, but io_list does not declare that output port.",
                [f"Add rtl_contract.output_map.{name}: <output_port> or set output_rules[{idx}].port."],
                "Make every FunctionalModel observable land on a named DUT output.",
                "Scoreboard rows can compare FL expected observables to RTL observed output pins.",
            ))
            continue
        raw_expr = rule.get("expr", rule.get("expression", rule.get("value")))
        if raw_expr is None or str(raw_expr).strip() == "":
            raw_expr = _default_output_expr()
        item = {
            "idx": idx,
            "name": name,
            "port": port,
            "raw_expr": raw_expr,
            "width": _port_width(by_name[port]),
            "source": rule,
            "aliases": {alias for alias in {name, port} if alias},
        }
        pending_outputs.append(item)
        all_output_aliases |= set(item["aliases"])

    resolved_outputs: list[dict] = []
    resolved_aliases: set[str] = set()
    while pending_outputs:
        progressed = False
        for item in list(pending_outputs):
            self_state_aliases = set(item["aliases"]) & set(state_vars)
            deps = (_expr_names(item["raw_expr"]) & all_output_aliases) - self_state_aliases
            unresolved_deps = deps - resolved_aliases
            if unresolved_deps:
                continue
            name = item["name"]
            port = item["port"]
            raw_expr = item["raw_expr"]
            try:
                expr = _lower_rule_expr(raw_expr, env, env_widths, int(item["width"]), readable=readable)
            except Exception as exc:
                questions.append(_question(
                    f"RTL_EXPR_{name.upper()}",
                    f"Rewrite output rule {name!r} using the supported expression DSL.",
                    str(exc),
                    ["Use integer, field names, +, -, *, /, %, <<, >>, &, |, ^, comparisons, and Python-style and/or/not."],
                    "Keep output_rules machine-checkable and free of prose.",
                    "The same expression can be evaluated by the FL model and lowered to RTL.",
                ))
                pending_outputs.remove(item)
                progressed = True
                continue
            resolved_outputs.append({
                "name": name,
                "port": port,
                "expr": _cast_rule_expr(int(item["width"]), expr, readable=readable),
                "width": item["width"],
                "source": item["source"],
            })
            same_cycle_ref = _cast_rule_expr(int(item["width"]), expr, readable=readable)
            for alias in item["aliases"]:
                env[alias] = same_cycle_ref
                sample_env[alias] = same_cycle_ref
                env_widths[alias] = int(item["width"])
                sample_env_widths[alias] = int(item["width"])
            resolved_aliases |= set(item["aliases"])
            pending_outputs.remove(item)
            progressed = True
        if progressed:
            continue
        for item in pending_outputs:
            deps = sorted((_expr_names(item["raw_expr"]) & all_output_aliases) - resolved_aliases)
            questions.append(_question(
                f"RTL_OUTPUT_DEP_{item['name'].upper()}",
                f"Break or order output-rule dependency for {item['name']!r}.",
                f"Rule expression references unresolved output rule(s): {', '.join(deps) or 'unknown cycle'}.",
                ["Define combinational helper expressions before dependent outputs or remove cyclic output dependencies."],
                "Output rules must form an acyclic same-cycle expression graph.",
                "LLM-authored RTL can implement FL observables without previous-cycle output feedback.",
            ))
        break

    resolved_updates: list[dict] = []
    for idx, rule in enumerate(state_updates):
        name = _ident(rule.get("name") or rule.get("state") or f"state_{idx}")
        raw_expr = rule.get("expr", rule.get("expression", rule.get("value")))
        if raw_expr is None or str(raw_expr).strip() == "":
            continue
        state_vars.setdefault(name, {"width": max(_int_value(rule.get("width"), 32), 1), "reset": _int_value(rule.get("reset"), 0)})
        env[name] = _rtl_eval_ref(name, int(state_vars[name]["width"]))
        sample_env[name] = name
        env_widths[name] = int(state_vars[name]["width"])
        sample_env_widths[name] = int(state_vars[name]["width"])
        try:
            expr = _lower_rule_expr(raw_expr, env, env_widths, int(state_vars[name]["width"]), readable=readable)
        except Exception as exc:
            questions.append(_question(
                f"RTL_STATE_EXPR_{name.upper()}",
                f"Rewrite state update {name!r} using the supported expression DSL.",
                str(exc),
                ["Use integer, input field names, existing state names, and simple arithmetic/boolean operators."],
                "Keep state_updates machine-checkable and free of prose.",
                "The same state ledger feeds FL model, RTL, and debug evidence.",
            ))
            continue
        resolved_updates.append({"name": name, "expr": expr, "source": rule})

    special_outputs: dict[str, str] = {}
    for key in ("ready_output", "output_valid", "valid_output"):
        value = contract.get(key)
        if value:
            port = _ident(value)
            if port not in output_ports:
                questions.append(_question(
                    f"RTL_SPECIAL_OUTPUT_{key.upper()}",
                    f"Declare {key} port {port!r} as a DUT output.",
                    f"rtl_contract.{key} references {port!r}, but io_list does not declare it as output.",
                    [f"Add {port} to io_list as output or remove rtl_contract.{key}."],
                    "Keep handshake/control outputs explicit in io_list.",
                    "LLM-authored RTL can expose ready/valid behavior to TB monitors.",
                ))
            else:
                special_outputs[key] = port
                sample_env.setdefault(port, port)
                sample_env_widths.setdefault(port, port_widths.get(port, 1))

    sample_names = _expr_names(sample_condition)
    ready_port = special_outputs.get("ready_output") or _ident(contract.get("ready_output") or "")
    valid_like_inputs = {
        name for name in sample_names
        if name in input_ports and (name.endswith("valid") or name == "valid")
    }
    if (
        ready_port
        and ready_port in output_ports
        and _valid_ready_contract_required(doc)
        and ready_port not in sample_names
        and valid_like_inputs
    ):
        questions.append(_question(
            "RTL_VALID_READY_SAMPLE_CONDITION",
            "Reconcile valid/ready acceptance between rtl_contract.sample_condition and cycle_model.",
            (
                f"cycle_model/io_list describes valid-ready acceptance through {ready_port!r}, "
                f"but sample_condition={sample_condition!r} does not include that ready phase."
            ),
            [
                f"Set rtl_contract.sample_condition to ({sample_condition}) and {ready_port}.",
                "If ready is intentionally ignored, remove valid_ready protocol semantics from cycle_model/io_list and document the non-backpressured protocol.",
            ],
            f"Use ({sample_condition}) and {ready_port} so FL model, RTL, TB, and coverage share the same acceptance event.",
            "Prevents state updates and result_valid from firing on valid-only cycles when the SSOT says valid/ready.",
        ))
        questions[-1]["current_sample_condition"] = sample_condition
        questions[-1]["ready_port"] = ready_port
        questions[-1]["valid_like_inputs"] = sorted(valid_like_inputs)

    driven_outputs = {item["port"] for item in resolved_outputs}
    driven_outputs |= {item["name"] for item in resolved_updates if item["name"] in output_ports}
    driven_outputs |= set(special_outputs.values())
    missing_observable_state = [
        name
        for name in sorted(state_vars)
        if name in output_ports and name not in driven_outputs
    ]
    if missing_observable_state:
        question = _question(
            "RTL_OBSERVABLE_STATE_RULES",
            "Define machine-checkable rules for every externally observable function_model state variable.",
            (
                "These function_model state variables are DUT output ports but have no output_rule, "
                "state_update, or special-output rule: "
                + ", ".join(missing_observable_state[:16])
            ),
            [
                "Add function_model.transactions.FM_PRIMARY.output_rules/state_updates for each listed observable state.",
                "Remove the output port if the state is internal-only and not a required debug/status observable.",
                "Move ambiguous error/status policy back to ssot-gen/human review until it has an executable rule.",
            ],
            "Use SSOT machine rules as the only authority; do not let rtl-gen tie observable state outputs to constants.",
            "Prevents LLM-authored RTL from hiding missing behavior behind zero tie-offs.",
        )
        question["missing_observable_state"] = missing_observable_state
        question["required_fields"] = [
            "function_model.transactions[].output_rules",
            "function_model.transactions[].state_updates",
            "rtl_contract.output_map",
        ]
        question["answer_schema"] = {
            "format": "YAML or JSON",
            "root_key": "observable_state_rules",
            "row_fields": ["name", "port", "expr", "width", "rule_type: output_rule|state_update"],
            "rule": "Every listed observable state must receive an executable expression or be removed from output ports.",
        }
        questions.append(question)

    try:
        sample_expr = _lower_rule_expr(sample_condition, sample_env, sample_env_widths, 1, readable=readable)
    except Exception as exc:
        questions.append(_question(
            "RTL_SAMPLE_CONDITION",
            "Rewrite rtl_contract.sample_condition using the supported expression DSL.",
            str(exc),
            ["Use input port names or input_map fields with and/or/not, comparisons, and bitwise operators."],
            "Make sampling eligibility machine-checkable.",
            "RTL, TB driver, and cycle model observe the same transaction acceptance condition.",
        ))
        sample_expr = "1'b0"

    if questions:
        return {}, questions
    dataflow = doc.get("dataflow") if isinstance(doc.get("dataflow"), dict) else {}
    apb_registers = _apb_register_contract(doc, ports)
    return {
        "top": top,
        "transaction": tx.get("id") or tx.get("name"),
        "clock": clock,
        "reset": reset,
        "reset_active": reset_active,
        "sample_condition": sample_expr,
        "outputs": resolved_outputs,
        "state_vars": state_vars,
        "state_updates": resolved_updates,
        "special_outputs": special_outputs,
        "pipeline_stages": _pipeline_stage_names(doc),
        "fsm_states": _fsm_state_names(doc),
        "fsm_transitions": _fsm_transition_items(doc),
        "input_map": {str(k): _ident(v) for k, v in input_map.items()},
        "apb_registers": apb_registers,
        "source": "rtl_contract + function_model.output_rules",
    }, []


def _function_model_output_rules(fm: dict) -> list[dict]:
    rules: list[dict] = []
    if not isinstance(fm, dict):
        return rules
    rules.extend(_rule_items(fm.get("output_rules")))
    for tx in fm.get("transactions") or []:
        if isinstance(tx, dict):
            rules.extend(_rule_items(tx.get("output_rules")))
    return rules


def _function_model_state_updates(fm: dict) -> list[dict]:
    updates: list[dict] = []
    if not isinstance(fm, dict):
        return updates
    updates.extend(_rule_items(fm.get("state_updates")))
    for tx in fm.get("transactions") or []:
        if isinstance(tx, dict):
            updates.extend(_rule_items(tx.get("state_updates")))
    return updates


def _starter_sequential_intent(doc: dict) -> bool:
    fm = doc.get("function_model") if isinstance(doc.get("function_model"), dict) else {}
    return bool(_function_model_state_updates(fm) or (fm.get("state_variables") if isinstance(fm, dict) else []))


def _starter_preview_contract(doc: dict, top: str, ports: list[dict]) -> tuple[dict, list[dict], list[dict]]:
    """Build the lowest-risk Starter RTL authoring contract.

    Starter is a fast feedback lane, not signoff. It accepts a compact SSOT
    with top_module/io_list/function_model and turns direct output_rules into
    a worker handoff contract. The LLM/worker writes the RTL; this path only
    reports missing context as hard/soft/deferred gate evidence.
    """

    fm = doc.get("function_model") if isinstance(doc.get("function_model"), dict) else {}
    hard_questions: list[dict] = []
    soft_gates: list[dict] = []
    if not ports:
        hard_questions.append(_question(
            "STARTER_IO_LIST_PORTS",
            "Declare at least one concrete DUT port before Starter RTL authoring.",
            "io_list did not contain parsable ports.",
            ["Add io_list.interfaces[].ports[] with name, direction, and width."],
            "Keep Starter input small, but make pin names explicit.",
            "The LLM author needs a concrete compile-checkable module port list.",
        ))
        return {}, hard_questions, soft_gates

    if not _contract_value_present(doc.get("cycle_model")):
        soft_gates.append({
            "id": "STARTER_CYCLE_MODEL_DEFERRED",
            "severity": "warning",
            "status": "deferred",
            "message": "cycle_model is missing; Starter treats direct output_rules as same-cycle authoring hints only.",
        })

    state_updates = _function_model_state_updates(fm)
    state_vars = fm.get("state_variables") if isinstance(fm, dict) else []
    if state_updates or state_vars:
        hard_questions.append(_question(
            "STARTER_SEQUENTIAL_CONTRACT",
            "Add clock/reset or use Engineering mode for sequential Starter authoring.",
            "function_model has state_variables/state_updates, so the LLM author needs explicit sequential timing context.",
            ["Add rtl_contract.clock/reset/reset_active and rerun.", "Use --mode engineering for the full rtl-gen authoring loop."],
            "Keep Starter sequential behavior explicit when state is present.",
            "Prevents a fast Starter run from pretending stateful RTL is complete.",
        ))

    by_name = {p["name"]: p for p in ports}
    input_ports = {p["name"] for p in ports if str(p.get("direction") or "").lower() in {"input", "inout"}}
    output_ports = {p["name"] for p in ports if str(p.get("direction") or "").lower() in {"output", "inout"}}
    if not output_ports:
        hard_questions.append(_question(
            "STARTER_OUTPUT_PORT",
            "Declare at least one DUT output port before Starter RTL authoring.",
            "io_list has no output/inout port that output_rules can drive.",
            ["Add an output port under io_list.interfaces[].ports[]."],
            "Expose the observable behavior as a DUT output.",
            "The authored RTL can compile and be inspected immediately.",
        ))

    contract = doc.get("rtl_contract") if isinstance(doc.get("rtl_contract"), dict) else {}
    output_map = contract.get("output_map") if isinstance(contract.get("output_map"), dict) else {}
    input_map = contract.get("input_map") if isinstance(contract.get("input_map"), dict) else {}
    env: dict[str, str] = {"true": "1'b1", "false": "1'b0", "True": "1'b1", "False": "1'b0"}
    widths: dict[str, int] = {"true": 1, "false": 1, "True": 1, "False": 1}
    for port in ports:
        env[port["name"]] = port["name"]
        widths[port["name"]] = _port_width(port)
    for field, port in input_map.items():
        port_name = _ident(port)
        env[_ident(field)] = port_name
        widths[_ident(field)] = widths.get(port_name, 32)
    for param in _param_items(doc.get("parameters")):
        name = _ident(param.get("name") or "")
        if not name:
            continue
        value = _int_value(param.get("default", param.get("value", 0)), 0)
        env[name] = str(value)
        widths[name] = max(int(value).bit_length(), 1)

    raw_rules = _function_model_output_rules(fm)
    if not raw_rules:
        hard_questions.append(_question(
            "STARTER_OUTPUT_RULES",
            "Add direct function_model.output_rules before Starter RTL authoring.",
            "Starter needs machine-checkable output_rules to guide and verify LLM-authored RTL.",
            ["Add function_model.output_rules[] or function_model.transactions[].output_rules[] with name/expr/port."],
            "Use prose for context, but put executable behavior in output_rules.",
            "The authored RTL and later FL/TB checks share the same expression contract.",
        ))

    outputs: list[dict] = []
    driven: set[str] = set()
    for idx, rule in enumerate(raw_rules):
        name = _ident(rule.get("name") or rule.get("output") or rule.get("port") or f"output_{idx}")
        port = _ident(rule.get("port") or output_map.get(name) or output_map.get(rule.get("name")) or name)
        if port not in output_ports:
            hard_questions.append(_question(
                f"STARTER_OUTPUT_MAP_{name.upper()}",
                f"Map Starter output rule {name!r} to a declared DUT output.",
                f"Rule targets {port!r}, but io_list does not declare that output port.",
                [f"Set output_rules[{idx}].port or rtl_contract.output_map.{name} to a declared output."],
                "Make every Starter rule land on a concrete DUT pin.",
                "The authored RTL can compile without inventing output ports.",
            ))
            continue
        raw_expr = rule.get("expr", rule.get("expression", rule.get("value")))
        if raw_expr is None or str(raw_expr).strip() == "":
            hard_questions.append(_question(
                f"STARTER_EXPR_{name.upper()}",
                f"Give Starter output rule {name!r} an executable expression.",
                "The rule has no expr/expression/value.",
                ["Use input names, constants, arithmetic, bitwise, comparison, and/or/not expressions."],
                "Keep Starter authoring deterministic and checkable.",
                "The expression can be used directly by the LLM author and verification harness.",
            ))
            continue
        missing = sorted(_expr_names(raw_expr) - set(env) - {"true", "false", "True", "False"})
        for missing_name in missing:
            hard_questions.append(_question(
                f"STARTER_INPUT_MAP_{_ident(missing_name).upper()}",
                f"Map expression name {missing_name!r} to a declared input port.",
                f"Rule {name!r} references {missing_name!r}, but no matching port or rtl_contract.input_map exists.",
                [f"Rename the expression to a declared input port or add rtl_contract.input_map.{missing_name}: <port>."],
                "Keep Starter expressions tied to concrete DUT pins.",
                "The preview can compile without guessing interface vocabulary.",
            ))
        if missing:
            continue
        try:
            expr = _starter_assign_expr(_parse_rule_expr(raw_expr), env, widths, _port_width(by_name[port]))
        except Exception as exc:
            hard_questions.append(_question(
                f"STARTER_EXPR_{name.upper()}",
                f"Rewrite Starter output rule {name!r} using the supported expression DSL.",
                str(exc),
                ["Use constants, input names, +, -, *, /, %, <<, >>, &, |, ^, comparisons, if/else, and/or/not."],
                "Keep Starter authoring hints machine-checkable.",
                "The LLM author and simulator harness can share the same rule.",
            ))
            continue
        outputs.append({
            "name": name,
            "port": port,
            "expr": expr,
            "width": _port_width(by_name[port]),
            "source": rule,
        })
        driven.add(port)

    undriven = sorted(output_ports - driven)
    if undriven:
        soft_gates.append({
            "id": "STARTER_UNDRIVEN_OUTPUTS_DEFAULT_ZERO",
            "severity": "warning",
            "status": "deferred",
            "message": "Starter contract has outputs without output_rules; LLM author must implement or justify them before promotion.",
            "ports": undriven,
        })

    if hard_questions:
        return {}, hard_questions, soft_gates
    return {
        "top": top,
        "outputs": outputs,
        "undriven_outputs": undriven,
        "source": "starter:function_model.output_rules",
    }, [], soft_gates


def _sv_cast(width: int, expr: str) -> str:
    return _sv_width_cast(width, expr)


def _pipeline_stage_names(doc: dict) -> list[str]:
    cm = doc.get("cycle_model") if isinstance(doc.get("cycle_model"), dict) else {}
    out: list[str] = []
    for idx, item in enumerate(cm.get("pipeline") or []):
        if isinstance(item, dict):
            raw = item.get("stage") or item.get("name") or f"PIPE_{idx}"
        else:
            raw = item or f"PIPE_{idx}"
        name = _ident(str(raw)).upper()
        if name and name not in out:
            out.append(name)
    return out


def _fsm_state_names(doc: dict) -> list[str]:
    fsm = doc.get("fsm") if isinstance(doc.get("fsm"), dict) else {}
    control = fsm.get("control") if isinstance(fsm.get("control"), dict) else fsm
    out: list[str] = []
    for idx, item in enumerate(control.get("states") or []):
        if isinstance(item, dict):
            raw = item.get("name") or item.get("state") or f"STATE_{idx}"
        else:
            raw = item or f"STATE_{idx}"
        name = _ident(str(raw)).upper()
        if name and name not in out:
            out.append(name)
    return out


def _fsm_transition_items(doc: dict) -> list[dict[str, str]]:
    fsm = doc.get("fsm") if isinstance(doc.get("fsm"), dict) else {}
    control = fsm.get("control") if isinstance(fsm.get("control"), dict) else fsm
    out: list[dict[str, str]] = []
    for item in control.get("transitions") or []:
        if not isinstance(item, dict):
            continue
        src = _ident(str(item.get("from") or item.get("src") or "")).upper()
        dst = _ident(str(item.get("to") or item.get("dst") or "")).upper()
        if src and dst:
            out.append({"from": src, "to": dst, "condition": str(item.get("condition") or "")})
    return out


def _apb_register_contract(doc: dict, ports: list[dict]) -> dict[str, Any]:
    by_name = {p["name"]: p for p in ports}
    required = {"paddr", "psel", "penable", "pwrite", "pwdata", "prdata", "pready", "pslverr"}
    if not required.issubset(by_name):
        return {}
    regs_doc = doc.get("registers") if isinstance(doc.get("registers"), dict) else {}
    regs: list[dict[str, Any]] = []
    for idx, reg in enumerate(regs_doc.get("register_list") or []):
        if not isinstance(reg, dict) or not reg.get("name"):
            continue
        name = _ident(str(reg.get("name"))).upper()
        if not name:
            continue
        regs.append({
            "name": name,
            "offset": _int_value(reg.get("offset"), idx * 4),
            "width": max(_int_value(reg.get("width"), _port_width(by_name["prdata"])), 1),
            "access": str(reg.get("access") or "rw").lower(),
            "reset": _int_value(reg.get("reset"), 0),
            "description": str(reg.get("description") or ""),
        })
    if not regs:
        return {}
    text = _text_blob(regs_doc) + "\n" + _text_blob(doc.get("interrupts") if isinstance(doc, dict) else {})
    upper = text.upper()
    return {
        "addr_width": _port_width(by_name["paddr"]),
        "data_width": _port_width(by_name["prdata"]),
        "strb_width": _port_width(by_name.get("pstrb", {"width": 0})),
        "registers": regs,
        "has_interrupt_policy": "INTEN" in upper or "INTSTATUS" in upper or "INTCLR" in upper or "DMASEV" in upper,
    }


def _text_blob(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return "\n".join(_text_blob(v) for v in value)
    if isinstance(value, dict):
        return "\n".join(f"{k}: {_text_blob(v)}" for k, v in value.items())
    return str(value)


def _interface_types(doc: dict) -> set[str]:
    out: set[str] = set()
    io = doc.get("io_list") if isinstance(doc, dict) else {}
    interfaces = io.get("interfaces") if isinstance(io, dict) else []
    if isinstance(interfaces, list):
        for intf in interfaces:
            if isinstance(intf, dict):
                out.add(str(intf.get("type") or "").lower())
                out.add(str(intf.get("name") or "").lower())
    return {x for x in out if x}


def _valid_ready_contract_required(doc: dict) -> bool:
    io = doc.get("io_list") if isinstance(doc, dict) else {}
    cm = doc.get("cycle_model") if isinstance(doc, dict) else {}
    text = "\n".join([_text_blob(io), _text_blob(cm)]).lower()
    return (
        any("valid_ready" in item or "valid-ready" in item for item in _interface_types(doc))
        or "valid && ready" in text
        or "valid and ready" in text
        or "valid_ready" in text
        or "valid-ready" in text
    )


def _has_resolved_optional_policy(doc: dict) -> bool:
    """Return true when ssot-gen has converted optional prose into policy.

    The generic blocker intentionally stops on unresolved "optional" prose,
    but the resolution artifact itself may still contain the word optional
    while defining parameterized or unsupported behavior. Do not re-block on
    that evidence once ATLAS/ssot-gen has captured a concrete policy.
    """
    custom = doc.get("custom") if isinstance(doc, dict) else {}
    if isinstance(custom, dict):
        policy = custom.get("optional_behavior_policy")
        if isinstance(policy, dict) and str(policy.get("resolution") or "").strip():
            return True
        rows = custom.get("rtl_blocker_resolutions")
        if isinstance(rows, list):
            for row in rows:
                if not isinstance(row, dict):
                    continue
                if row.get("id") == "OPTIONAL_BEHAVIOR_POLICY" and str(row.get("answer") or "").strip():
                    return True
    return False


def _has_explicit_apb_illegal_access_policy(doc: dict, regs: object, low: str) -> bool:
    """Detect concrete APB error policy already captured in SSOT.

    This gate should ask a human only when the SSOT mentions illegal/unmapped
    APB accesses without saying what the bus-visible response is. Accept the
    policy when the SSOT explicitly defines pslverr plus at least one concrete
    response surface such as read data, ready timing, or state side effects.
    """
    rtl_contract = doc.get("rtl_contract") if isinstance(doc, dict) else {}
    if isinstance(rtl_contract, dict):
        for key in ("apb_illegal_access_policy", "illegal_access_policy", "unmapped_access_policy"):
            policy = rtl_contract.get(key)
            if not isinstance(policy, dict):
                continue
            response = policy.get("response") if isinstance(policy.get("response"), dict) else policy
            has_error = _scalar_one(response.get("pslverr")) or _scalar_one(response.get("error"))
            has_surface = (
                _scalar_one(response.get("pready"))
                or _scalar_zero(response.get("prdata"))
                or str(policy.get("state_update") or policy.get("state_updates") or "").strip().lower() in {
                    "none",
                    "no state update",
                    "no state updates",
                }
            )
            if has_error and has_surface:
                return True

    text = "\n".join(
        [
            low,
            _text_blob(regs).lower(),
            _text_blob(rtl_contract).lower(),
            _text_blob(doc.get("function_model") if isinstance(doc, dict) else {}).lower(),
            _text_blob(doc.get("error_handling") if isinstance(doc, dict) else {}).lower(),
            _text_blob(doc.get("requirements") if isinstance(doc, dict) else {}).lower(),
            _text_blob(doc.get("custom") if isinstance(doc, dict) else {}).lower(),
        ]
    )
    if not any(tok in text for tok in ("illegal address", "illegal access", "unsupported address", "unmapped")):
        return False

    pslverr_policy = "pslverr_on_decode_error" in text or (
        "pslverr" in text
        and any(
            tok in text
            for tok in (
                "pslverr=1",
                "pslverr = 1",
                "pslverr: 1",
                "forces pslverr",
                "assert pslverr",
                "pslverr asserts",
                "pslverr asserted",
            )
        )
    )
    read_policy = any(
        tok in text
        for tok in (
            "illegal_read_returns",
            "unmapped_read_data",
            "prdata=0",
            "prdata = 0",
            "prdata: 0",
            "read returns prdata=0",
            "read returns 0",
            "unmapped reads return 0",
            "read data zero",
            "returns zero",
            "read as zero",
        )
    )
    ready_policy = "pready" in text and any(
        tok in text
        for tok in (
            "pready=1",
            "pready = 1",
            "pready: 1",
            "pready asserted",
            "no slave backpressure",
        )
    )
    state_policy = "illegal_write_policy" in text or any(
        tok in text
        for tok in (
            "no state update",
            "no state updates",
            "do not modify state",
            "does not modify state",
            "without changing",
            "writes ignored",
            "illegal writes are ignored",
            "no side effect",
            "no side effects",
        )
    )
    return pslverr_policy and (read_policy or ready_policy or state_policy)


def _scalar_one(value: object) -> bool:
    if value is True:
        return True
    if isinstance(value, (int, float)) and value == 1:
        return True
    return str(value).strip().lower() in {"1", "1'b1", "true", "assert", "asserted", "yes"}


def _scalar_zero(value: object) -> bool:
    if value is False:
        return True
    if isinstance(value, (int, float)) and value == 0:
        return True
    return str(value).strip().lower() in {"0", "0'b0", "false", "zero", "none"}


def _question(qid: str, decision: str, evidence: str, options: list[str], recommended: str, effect: str) -> dict:
    return {
        "id": qid,
        "decision_needed": decision,
        "evidence": evidence,
        "options": options,
        "recommended_default": recommended,
        "downstream_effect": effect,
    }


def _rtl_contract_questions(doc: dict, top: str) -> list[dict]:
    """Return human/SSOT decisions required before production RTL.

    The checks are feature- and protocol-oriented, not IP-name-oriented.
    They prevent fixed fallback templates from being mistaken for an RTL
    implementation when the SSOT still carries prose-only behavior.
    """

    fm = doc.get("function_model") if isinstance(doc, dict) else {}
    cm = doc.get("cycle_model") if isinstance(doc, dict) else {}
    err = doc.get("error_handling") if isinstance(doc, dict) else {}
    regs = doc.get("registers") if isinstance(doc, dict) else {}
    text = "\n".join([
        _text_blob(doc.get("top_module") if isinstance(doc, dict) else {}),
        _text_blob(fm),
        _text_blob(cm),
        _text_blob(err),
        _text_blob(doc.get("integration") if isinstance(doc, dict) else {}),
    ])
    low = text.lower()
    ports = {p["name"].lower() for p in _io_ports(doc)}
    intf_types = _interface_types(doc)
    questions: list[dict] = []
    module_questions = _module_contract_questions(doc, top)
    questions.extend(module_questions)
    if not any(q.get("id") == "RTL_MODULE_CONTRACTS" for q in module_questions):
        questions.extend(_ssot_behavior_ownership_questions(doc, top))

    transactions = fm.get("transactions") if isinstance(fm, dict) else []
    primary = {}
    if isinstance(transactions, list):
        for txn in transactions:
            if isinstance(txn, dict) and str(txn.get("id") or txn.get("name") or "").lower() in {
                "fm_primary",
                "primary_behavior",
            }:
                primary = txn
                break
    primary_text = _text_blob(primary)
    has_structured_effects = any(
        isinstance(primary.get(key), list) and primary.get(key)
        for key in ("state_updates", "output_rules", "counter_rules", "event_rules")
    ) if isinstance(primary, dict) else False
    if primary and not has_structured_effects and len(primary_text) > 120:
        questions.append(_question(
            "FM_PRIMARY_STRUCTURED_RULES",
            "Convert prose-only primary behavior into structured state/output/counter/event rules.",
            (
                "function_model.transactions.FM_PRIMARY exists, but it describes behavior as prose. "
                "rtl-gen needs machine-checkable rules before it can prove LLM-authored RTL against the FL model."
            ),
            [
                "Add state_updates/output_rules/counter_rules/event_rules under FM_PRIMARY.",
                "Declare this IP register-only/control-only if no streaming/datapath behavior is required.",
            ],
            "Add structured rules, because they become the RTL ledger and TB scoreboard contract.",
            "ssot-gen updates function_model; fl-model-gen, rtl-gen, tb-gen, and fcov regenerate from that contract.",
        ))

    has_axis = any("axis" in x or "axi4-stream" in x for x in intf_types) or any(p.startswith("s_axis_") for p in ports)
    if has_axis and "crc" in low:
        crc_policy_tokens = (
            "refin", "refout", "xorout", "final_xor", "bit_order", "byte_order",
            "include_trailer", "exclude_trailer", "expected_crc_source",
            "trailer_endianness", "residue",
        )
        if not any(tok in low for tok in crc_policy_tokens):
            questions.append(_question(
                "CRC_STREAM_POLICY",
                "Define the CRC stream comparison contract.",
                (
                    "SSOT mentions CRC/CRC32 and an AXI4-Stream packet, but does not define expected CRC source, "
                    "trailer width/endian, whether trailer bytes are included in the CRC, reflection, xorout, or residue."
                ),
                [
                    "Last 4 valid packet bytes are expected CRC, excluded from CRC calculation, network byte order.",
                    "No trailer compare; compute CRC only and expose result/status through CSRs.",
                    "Expected CRC arrives on a sideband signal; SSOT must add that interface.",
                ],
                "Use an explicit trailer policy only if that is the intended product behavior; otherwise choose compute-only.",
                "rtl-gen can implement the datapath and tb-gen can compare RTL-vs-FL only after this is represented in SSOT.",
            ))
        if "tkeep" in low or "s_axis_tkeep" in ports:
            keep_policy_tokens = ("tkeep_byte_order", "little_endian_lane", "big_endian_lane", "invalid_tkeep", "sparse_tkeep")
            if not any(tok in low for tok in keep_policy_tokens):
                questions.append(_question(
                    "AXIS_TKEEP_POLICY",
                    "Define AXI4-Stream tkeep byte-lane and malformed-packet policy.",
                    (
                        "SSOT has AXI4-Stream tdata/tkeep/tlast, but does not define byte-lane order or whether sparse/zero "
                        "tkeep before tlast is legal, ignored, or malformed."
                    ),
                    [
                        "Lane 0 is least-significant byte; non-contiguous tkeep is malformed; zero tkeep beat is ignored unless tlast.",
                        "Lane 0 is most-significant byte; non-contiguous tkeep is malformed.",
                        "All tkeep masks are legal and CRC consumes enabled lanes in lane-index order.",
                    ],
                    "Lane 0 least-significant byte with non-contiguous masks malformed is the common AXI-stream policy.",
                    "Updates cycle_model, function_model malformed rules, RTL parser, and coverage bins.",
                ))

    has_apb = any("apb" in x for x in intf_types) or {"paddr", "psel", "penable", "pwrite"}.issubset(ports)
    if has_apb:
        reg_text = _text_blob(regs).lower()
        if "unsupported address" in low or "illegal access" in low:
            explicit_error = any(tok in reg_text or tok in low for tok in (
                "pslverr_on_decode_error",
                "illegal_read_returns",
                "illegal_write_policy",
                "unmapped_read_data",
            )) or _has_explicit_apb_illegal_access_policy(doc, regs, low)
            if not explicit_error:
                questions.append(_question(
                    "APB_ILLEGAL_ACCESS_POLICY",
                    "Define APB unmapped/illegal access behavior.",
                    (
                        "error_handling references unsupported address or illegal CSR access, but the SSOT does not say whether "
                        "pready/pslverr asserts, what prdata returns, or whether a status/interrupt bit is set."
                    ),
                    [
                        "pready=1, pslverr=1 for unmapped/illegal access; prdata=0; set error/malformed status.",
                        "pready=1, pslverr=0; unmapped reads return 0; illegal writes are ignored.",
                    ],
                    "Use pslverr=1 for unmapped/illegal access when APB error visibility is required.",
                    "Updates APB register RTL, FL CSR transaction behavior, TB negative tests, and coverage bins.",
                ))

    # Avoid duplicate generic optional blocker if a more specific CRC policy
    # question already explains the optional behavior.
    if (
        "optional" in low
        and not _has_resolved_optional_policy(doc)
        and not any(q["id"] == "CRC_STREAM_POLICY" for q in questions)
    ):
        questions.append(_question(
            "OPTIONAL_BEHAVIOR_POLICY",
            "Resolve optional behavior into a required, disabled, or parameterized feature.",
            "SSOT contains the word 'optional', which is not a synthesizable/signoff policy by itself.",
            [
                "Feature is required and must be implemented.",
                "Feature is not implemented in this IP revision.",
                "Feature is controlled by an explicit parameter/register field with reset default.",
            ],
            "Represent optional behavior as an explicit parameter/register-controlled feature.",
            "Updates SSOT feature contract and all downstream generators.",
        ))

    return questions


def _contract_value_present(value) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(str(item).strip() for item in value)
    if isinstance(value, dict):
        return bool(value)
    return value is not None and value is not False


SSOT_REF_PREFIXES = (
    "function_model",
    "cycle_model",
    "decomposition",
    "functional_decomposition",
    "features",
    "dataflow",
    "registers",
    "fsm",
    "memory",
    "interrupts",
    "error_handling",
    "debug_observability",
    "test_requirements",
    "traceability",
)


def _looks_like_ssot_ref(ref: str) -> bool:
    text = str(ref or "").strip()
    if not text or text.startswith("."):
        return False
    return text in SSOT_REF_PREFIXES or text.startswith(tuple(prefix + "." for prefix in SSOT_REF_PREFIXES))


def _module_declared_refs(sm: dict) -> list[str]:
    refs: list[str] = []
    for key in (
        "implements",
        "source_sections",
        "function_model_refs",
        "decomposition_refs",
        "cycle_model_refs",
        "feature_refs",
        "dataflow_refs",
        "register_refs",
        "fsm_refs",
        "test_refs",
        "trace_refs",
        "ssot_refs",
    ):
        refs.extend(_contract_ref_values(sm.get(key)))
    seen: set[str] = set()
    out: list[str] = []
    for ref in refs:
        if ref and ref not in seen:
            seen.add(ref)
            out.append(ref)
    return out


def _module_behavior_owner_refs(sm: dict) -> list[str]:
    refs: list[str] = []
    for key in ("implements", "function_model_refs", "decomposition_refs"):
        refs.extend(_contract_ref_values(sm.get(key)))
    seen: set[str] = set()
    out: list[str] = []
    for ref in refs:
        if ref and ref not in seen:
            seen.add(ref)
            out.append(ref)
    return out


def _source_sections_from_refs(refs: list[str]) -> set[str]:
    sections: set[str] = set()
    for ref in refs:
        if _looks_like_ssot_ref(ref):
            sections.add(ref.split(".", 1)[0])
    return sections


def _module_contract_ready(sm: dict, doc: dict | None = None) -> bool:
    wiring_only = sm.get("wiring_only") is True or str(sm.get("kind") or "").lower() in {
        "wrapper",
        "adapter",
        "tieoff",
        "tie_off",
    }
    if wiring_only:
        direct_contract = (
            _contract_value_present(sm.get("ports"))
            and (
                _contract_value_present(sm.get("connections"))
                or _contract_value_present(sm.get("internal_interfaces"))
            )
        )
        if direct_contract:
            return True
        refs = _module_declared_refs(sm)
        has_wiring_refs = any(ref == "integration" or ref.startswith("integration.") for ref in refs)
        return bool(has_wiring_refs and doc is not None and _module_has_global_integration_connections(doc, str(sm.get("name") or "")))
    behavior_ref_keys = (
        "function_model_refs",
        "decomposition_refs",
        "cycle_model_refs",
        "feature_refs",
        "dataflow_refs",
        "register_refs",
        "fsm_refs",
        "test_refs",
        "trace_refs",
        "ssot_refs",
    )
    refs = _module_declared_refs(sm)
    has_keyed_section_refs = any(_contract_value_present(sm.get(key)) for key in behavior_ref_keys)
    has_source_sections = (
        _contract_value_present(sm.get("source_sections"))
        or bool(_source_sections_from_refs(refs))
        or has_keyed_section_refs
    )
    has_behavior_refs = (
        has_keyed_section_refs
        or any(_looks_like_ssot_ref(ref) for ref in _contract_ref_values(sm.get("implements")))
    )
    return (
        _contract_value_present(sm.get("implements"))
        and has_source_sections
        and has_behavior_refs
    )


def _module_has_global_integration_connections(doc: dict, module_name: str) -> bool:
    if not module_name:
        return False
    integration = doc.get("integration") if isinstance(doc, dict) else {}
    rows = integration.get("connections") if isinstance(integration, dict) else []
    if not isinstance(rows, list):
        return False
    for row in rows:
        if not isinstance(row, dict):
            continue
        participants = {
            str(row.get("module") or "").strip(),
            str(row.get("from_module") or "").strip(),
            str(row.get("to_module") or "").strip(),
        }
        if module_name not in participants:
            continue
        has_signal = _contract_value_present(row.get("signal"))
        has_port = (
            _contract_value_present(row.get("port"))
            or _contract_value_present(row.get("from_port"))
            or _contract_value_present(row.get("to_port"))
            or _contract_value_present(row.get("port_map"))
        )
        if has_signal and has_port:
            return True
    return False


def _collect_named_refs(items, prefix: str, key: str = "name", limit: int = 32) -> list[str]:
    refs: list[str] = []
    for idx, item in enumerate(items or []):
        if not isinstance(item, dict):
            continue
        raw = item.get(key) or item.get("id") or item.get("stage") or idx
        name = _ident(str(raw))
        refs.append(f"{prefix}.{name}")
        if len(refs) >= limit:
            break
    return refs


def _ref_token(item, idx: int) -> str:
    if isinstance(item, dict):
        for key in ("id", "name", "state", "signal", "port", "stage", "field", "event", "condition"):
            if str(item.get(key) or "").strip():
                return _ident(str(item.get(key)))[:96]
    elif str(item or "").strip():
        return _ident(str(item))[:96]
    return f"item_{idx}"


def _collect_refs_from_items(items, prefix: str, *, key: str = "name", limit: int = 128) -> list[str]:
    refs: list[str] = []
    if isinstance(items, dict):
        iterable = list(items.items())
        for idx, (name, value) in enumerate(iterable):
            token = _ident(str(name or _ref_token(value, idx)))[:96]
            refs.append(f"{prefix}.{token}")
            if len(refs) >= limit:
                break
        return refs
    if not isinstance(items, list):
        return refs
    for idx, item in enumerate(items):
        if isinstance(item, dict):
            raw = item.get(key) or item.get("id") or item.get("name") or item.get("state") or item.get("signal") or idx
            token = _ident(str(raw))[:96]
        else:
            token = _ref_token(item, idx)
        refs.append(f"{prefix}.{token}")
        if len(refs) >= limit:
            break
    return refs


def _ssot_function_model_refs(doc: dict) -> list[str]:
    fm = doc.get("function_model") if isinstance(doc.get("function_model"), dict) else {}
    refs: list[str] = []
    transactions = fm.get("transactions")
    if isinstance(transactions, list):
        for idx, txn in enumerate(transactions):
            if not isinstance(txn, dict):
                continue
            tid = _ident(str(txn.get("id") or txn.get("name") or idx))[:96]
            base = f"function_model.transactions.{tid}"
            refs.append(base)
            for key in (
                "preconditions",
                "inputs",
                "outputs",
                "side_effects",
                "state_updates",
                "output_rules",
                "counter_rules",
                "event_rules",
                "error_cases",
            ):
                value = txn.get(key)
                if isinstance(value, (list, dict)) and value:
                    refs.extend(_collect_refs_from_items(value, f"{base}.{key}"))
    refs.extend(_collect_refs_from_items(fm.get("state_variables"), "function_model.state_variables"))
    refs.extend(_collect_refs_from_items(fm.get("outputs"), "function_model.outputs"))
    refs.extend(_collect_refs_from_items(fm.get("inputs"), "function_model.inputs"))
    seen: set[str] = set()
    out: list[str] = []
    for ref in refs:
        if ref not in seen:
            seen.add(ref)
            out.append(ref)
    return out


def _ssot_decomposition_refs(doc: dict) -> list[str]:
    refs: list[str] = []
    for section_name in ("decomposition", "functional_decomposition"):
        section = doc.get(section_name)
        if not _contract_value_present(section):
            continue
        if isinstance(section, dict):
            section_had_children = False
            for key, value in section.items():
                if isinstance(value, list) and value:
                    refs.extend(_collect_refs_from_items(value, f"{section_name}.{key}"))
                    section_had_children = True
                elif isinstance(value, dict) and value:
                    for child_key, child_value in value.items():
                        token = _ident(str(child_key or _ref_token(child_value, len(refs))))[:96]
                        refs.append(f"{section_name}.{key}.{token}")
                    section_had_children = True
            if not section_had_children:
                refs.append(section_name)
        elif isinstance(section, list):
            refs.extend(_collect_refs_from_items(section, f"{section_name}.items"))
        else:
            refs.append(section_name)
    seen: set[str] = set()
    out: list[str] = []
    for ref in refs:
        if ref not in seen:
            seen.add(ref)
            out.append(ref)
    return out


def _ssot_behavior_inventory(doc: dict) -> dict[str, list[str]]:
    return {
        "function_model_refs": _ssot_function_model_refs(doc),
        "decomposition_refs": _ssot_decomposition_refs(doc),
    }


def _module_contract_available_refs(doc: dict) -> dict:
    fm = doc.get("function_model") if isinstance(doc.get("function_model"), dict) else {}
    cm = doc.get("cycle_model") if isinstance(doc.get("cycle_model"), dict) else {}
    regs = doc.get("registers") if isinstance(doc.get("registers"), dict) else {}
    fsm = doc.get("fsm") if isinstance(doc.get("fsm"), dict) else {}
    tests = doc.get("test_requirements") if isinstance(doc.get("test_requirements"), dict) else {}
    io = doc.get("io_list") if isinstance(doc.get("io_list"), dict) else {}
    dataflow = doc.get("dataflow") if isinstance(doc.get("dataflow"), dict) else {}
    ports = [p["name"] for p in _io_ports(doc)]
    present_sections = [
        key for key in (
            "top_module",
            "features",
            "io_list",
            "parameters",
            "registers",
            "function_model",
            "cycle_model",
            "dataflow",
            "fsm",
            "error_handling",
            "test_requirements",
            "quality_gates",
        )
        if _contract_value_present(doc.get(key))
    ]
    behavior_inventory = _ssot_behavior_inventory(doc)
    return {
        "source_sections": present_sections,
        "function_model_refs": behavior_inventory["function_model_refs"][:128],
        "decomposition_refs": behavior_inventory["decomposition_refs"][:128],
        "cycle_model_refs": _collect_named_refs(cm.get("pipeline"), "cycle_model.pipeline", "stage")
        + _collect_named_refs(cm.get("handshake_rules"), "cycle_model.handshake_rules", "signal")
        + [key for key in ("cycle_model.clock", "cycle_model.reset", "cycle_model.latency") if key.split(".")[-1] in cm],
        "feature_refs": _collect_named_refs(doc.get("features"), "features"),
        "dataflow_refs": [f"dataflow.{key}" for key in ("source", "sequence", "sinks", "notes") if key in dataflow],
        "register_refs": _collect_named_refs(regs.get("register_list"), "registers.register_list"),
        "fsm_refs": [f"fsm.{key}" for key in sorted(fsm) if _contract_value_present(fsm.get(key))],
        "test_refs": _collect_named_refs(tests.get("scenarios"), "test_requirements.scenarios", "id"),
        "ports": ports[:64],
        "interfaces": [
            str(item.get("name") or item.get("type") or "").strip()
            for item in (io.get("interfaces") or [])
            if isinstance(item, dict) and str(item.get("name") or item.get("type") or "").strip()
        ][:32],
    }


def _contract_ref_values(value) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        return _expand_relative_refs([item.strip() for item in re.split(r"[,;\n]+", text) if item.strip()])
    if isinstance(value, list):
        return _expand_relative_refs([str(item).strip() for item in value if str(item).strip()])
    if isinstance(value, dict):
        return _expand_relative_refs([str(key).strip() for key in value if str(key).strip()])
    return []


def _expand_relative_refs(refs: list[str]) -> list[str]:
    """Expand shorthand SSOT refs like `.decode` using the prior ref prefix."""

    out: list[str] = []
    base_prefix = ""
    for raw in refs:
        ref = str(raw or "").strip()
        if not ref:
            continue
        if ref.startswith(".") and base_prefix:
            ref = base_prefix + ref
        if not ref.startswith(".") and "." in ref:
            base_prefix = ref.rsplit(".", 1)[0]
        out.append(ref)
    return out


def _ref_is_covered(ref: str, owners: list[str]) -> bool:
    for owner in owners:
        ref_l = str(ref or "").lower()
        owner_l = str(owner or "").lower()
        if (
            ref == owner
            or ref.startswith(owner + ".")
            or ref_l == owner_l
            or ref_l.startswith(owner_l + ".")
            or _ref_leaf_strong_match(ref, owner)
        ):
            return True
    return False


def _ref_leaf_strong_match(ref: str, owner_ref: str) -> bool:
    ref_parent, _, ref_leaf = str(ref or "").rpartition(".")
    owner_parent, _, owner_leaf = str(owner_ref or "").rpartition(".")
    if not ref_parent or ref_parent != owner_parent:
        return False
    ref_parts = {part for part in re.split(r"[_\\W]+", ref_leaf.lower()) if len(part) > 1}
    owner_parts = {part for part in re.split(r"[_\\W]+", owner_leaf.lower()) if len(part) > 1}
    if not ref_parts or not owner_parts:
        return False
    return owner_parts.issubset(ref_parts) or ref_parts.issubset(owner_parts)


def _behavior_owner_modules(doc: dict, top: str) -> list[dict]:
    top_names = {top, f"{top}_top", "top", "wrapper"}
    out: list[dict] = []
    for sm in doc.get("sub_modules") or []:
        if not isinstance(sm, dict):
            continue
        name = _ident(sm.get("name") or "")
        rel = str(sm.get("file") or "").strip()
        path_stem = _ident(Path(rel).stem) if rel else ""
        is_top = name in top_names or path_stem in top_names
        wiring_only = sm.get("wiring_only") is True or str(sm.get("kind") or "").lower() in {
            "wrapper",
            "adapter",
            "tieoff",
            "tie_off",
        }
        declared_refs = _module_behavior_owner_refs(sm)
        owns_behavior = any(
            ref == "function_model"
            or ref.startswith("function_model.")
            or ref in {"decomposition", "functional_decomposition"}
            or ref.startswith(("decomposition.", "functional_decomposition."))
            for ref in declared_refs
        )
        if is_top and (wiring_only or not owns_behavior):
            continue
        out.append(sm)
    return out


def _module_owned_behavior_refs(doc: dict, top: str) -> dict[str, list[str]]:
    owned = {"function_model_refs": [], "decomposition_refs": []}
    for sm in _behavior_owner_modules(doc, top):
        owned["function_model_refs"].extend(_contract_ref_values(sm.get("function_model_refs")))
        owned["decomposition_refs"].extend(_contract_ref_values(sm.get("decomposition_refs")))
        for ref in _module_behavior_owner_refs(sm):
            if ref == "function_model" or ref.startswith("function_model."):
                owned["function_model_refs"].append(ref)
            if ref in {"decomposition", "functional_decomposition"} or ref.startswith(("decomposition.", "functional_decomposition.")):
                owned["decomposition_refs"].append(ref)
    # Wiring-only top wrappers still own structural integration intent. They
    # must not satisfy function_model ownership, but their decomposition_refs
    # should close structural refs such as decomposition.units.top_integration.
    for sm in _manifest_submodules(doc):
        if not isinstance(sm, dict):
            continue
        name = _ident(sm.get("name") or "")
        rel = str(sm.get("file") or "").strip()
        path_stem = _ident(Path(rel).stem) if rel else ""
        wiring_only = sm.get("wiring_only") is True or str(sm.get("kind") or "").lower() in {
            "wrapper",
            "adapter",
            "tieoff",
            "tie_off",
        }
        if not wiring_only and name not in {top, f"{top}_top", "top", "wrapper"} and path_stem not in {top, f"{top}_top", "top", "wrapper"}:
            continue
        owned["decomposition_refs"].extend(_contract_ref_values(sm.get("decomposition_refs")))
        for ref in _module_behavior_owner_refs(sm):
            if ref in {"decomposition", "functional_decomposition"} or ref.startswith(("decomposition.", "functional_decomposition.")):
                owned["decomposition_refs"].append(ref)
    return {
        key: sorted({ref for ref in refs if ref})
        for key, refs in owned.items()
    }


def _ssot_behavior_ownership_questions(doc: dict, top: str) -> list[dict]:
    """Require every SSOT behavior ref to have an RTL owner before generation.

    The source of truth is the SSOT YAML document only. Derived artifacts such
    as model/decomposition.json can be evidence, but they are not read here and
    cannot authorize RTL ownership.
    """

    if not _manifest_submodules(doc):
        return []
    owner_modules = _behavior_owner_modules(doc, top)
    if not owner_modules:
        return []
    inventory = _ssot_behavior_inventory(doc)
    owned = _module_owned_behavior_refs(doc, top)
    orphan_refs: list[str] = []
    for key, refs in inventory.items():
        for ref in refs:
            if not _ref_is_covered(ref, owned.get(key, [])):
                orphan_refs.append(ref)
    if not orphan_refs:
        return []

    question = _question(
        "SSOT_BEHAVIOR_OWNERSHIP",
        "Assign every SSOT function/decomposition behavior to an RTL module contract.",
        (
            "These SSOT refs have no owning RTL module contract: "
            + ", ".join(orphan_refs[:16])
            + (" ..." if len(orphan_refs) > 16 else "")
        ),
        [
            "Add function_model_refs/decomposition_refs to the manifest module that implements each orphan behavior.",
            "Split or refine the SSOT decomposition if one behavior is too broad for a single RTL owner.",
            "Move non-RTL-only intent into verification/coverage sections with explicit traceability instead of leaving it as implementation behavior.",
        ],
        "Keep SSOT as the single source: update sub_modules[] contracts with concrete function_model_refs and decomposition_refs.",
        "rtl-gen, lint, tb-gen, and coverage can trace each LLM-authored RTL module back to SSOT behavior with no orphan function-level intent.",
    )
    question["orphan_refs"] = orphan_refs[:128]
    question["owned_refs"] = owned
    question["candidate_modules"] = [
        {"name": str(sm.get("name") or ""), "file": str(sm.get("file") or "")}
        for sm in owner_modules[:32]
    ]
    question["required_fields"] = [
        "sub_modules[].function_model_refs",
        "sub_modules[].decomposition_refs",
    ]
    question["answer_schema"] = {
        "format": "YAML or JSON",
        "root_key": "module_contracts",
        "active_module_required": [
            "name",
            "file",
            "function_model_refs and/or decomposition_refs covering every orphan_ref",
        ],
        "rule": "Do not use generated model/decomposition.json as authority; every owner ref must be present in the SSOT YAML.",
    }
    question["available_refs"] = _module_contract_available_refs(doc)
    question["yaml_patch_hint"] = (
        "For each orphan_refs entry, add the exact ref or a parent ref under the owning sub_modules[] row. "
        "Parent refs cover child refs by dotted-prefix ownership."
    )
    return [question]


def _module_contract_questions(doc: dict, top: str) -> list[dict]:
    """Gate multi-file manifest RTL on per-module SSOT contracts.

    A leaf SSOT may legitimately generate a single top module from a
    structured `rtl_contract`. Once it declares multiple manifest-owned RTL
    files, each non-top file must say what behavior or wiring it owns. Without
    that, a generator can only emit empty shells, which is exactly the fake
    completion path this flow must reject.
    """

    if not isinstance(doc, dict):
        return []
    submods = _manifest_submodules(doc)
    if not submods:
        return []
    filelist = doc.get("filelist") if isinstance(doc.get("filelist"), dict) else {}
    listed = {
        str(item).strip()
        for item in (filelist.get("rtl") or [])
        if str(item).strip()
    }
    missing_files: list[str] = []
    missing_contracts: list[str] = []
    top_names = {top, f"{top}_top", "top", "wrapper"}
    for sm in submods:
        name = _ident(sm.get("name") or "")
        rel = str(sm.get("file") or "").strip()
        if not rel:
            missing_files.append(name or "<unnamed>")
            continue
        if listed and rel not in listed:
            missing_files.append(f"{name}:{rel}")
        is_top = name in top_names or Path(rel).stem in top_names
        if is_top:
            continue
        if _module_contract_ready(sm, doc):
            continue
        missing_contracts.append(f"{name}:{rel}")
    questions: list[dict] = []
    if missing_files:
        questions.append(_question(
            "RTL_MANIFEST_FILELIST_SYNC",
            "Reconcile sub_modules[].file with filelist.rtl before RTL generation.",
            (
                "Manifest-owned RTL entries are missing a file path or are absent from filelist.rtl: "
                + ", ".join(missing_files[:12])
            ),
            [
                "Add every manifest-owned sub_modules[].file to filelist.rtl.",
                "Remove stale manifest entries or promote independently verified blocks to child_ssot.",
            ],
            "Keep sub_modules[].file and filelist.rtl identical for manifest-owned files.",
            "ATLAS can verify that each SSOT-owned RTL file exists, is listed, compiles, and lints.",
        ))
    if missing_contracts:
        question = _question(
            "RTL_MODULE_CONTRACTS",
            "Define per-module implementation contracts for manifest-owned RTL files.",
            (
                "These manifest modules have only names/descriptions, so rtl-gen cannot know which "
                "function_model, cycle_model, dataflow, register, FSM, error, or debug behavior each file owns: "
                + ", ".join(missing_contracts[:12])
            ),
            [
                "Add implements/source_sections/function_model_refs/decomposition_refs/cycle_model_refs/feature_refs/dataflow_refs to each active module.",
                "For wiring-only wrappers/adapters, set wiring_only: true and provide ports/connections.",
                "For reusable complex blocks, set ownership: child_ssot and provide sub_modules[].ssot.",
            ],
            "Have ssot-gen repair sub_modules into a module contract ledger before rerunning rtl-gen.",
            "rtl-gen can write every manifest file from SSOT evidence instead of emitting fixed templates or placeholder shells.",
        )
        question["missing_modules"] = [
            {"name": item.split(":", 1)[0], "file": item.split(":", 1)[1]}
            for item in missing_contracts
            if ":" in item
        ]
        question["required_fields"] = [
            "implements",
            "source_sections",
            "function_model_refs",
            "decomposition_refs",
            "cycle_model_refs",
            "feature_refs",
            "dataflow_refs",
            "register_refs",
            "fsm_refs",
            "ports",
            "connections",
            "wiring_only",
        ]
        question["answer_schema"] = {
            "format": "YAML or JSON",
            "root_key": "module_contracts",
            "active_module_required": [
                "name",
                "file",
                "implements",
                "source_sections",
                "one_or_more_of(function_model_refs, decomposition_refs, cycle_model_refs, feature_refs, dataflow_refs, register_refs, fsm_refs, test_refs, trace_refs, ssot_refs)",
            ],
            "wiring_only_required": ["name", "file", "wiring_only: true", "ports", "connections or internal_interfaces"],
            "rule": "Do not approve a module from its name alone; every row must point at SSOT evidence it owns.",
        }
        question["available_refs"] = _module_contract_available_refs(doc)
        question["yaml_patch_hint"] = (
            "For each missing sub_modules[] row, add implements/source_sections plus concrete refs, "
            "or set wiring_only: true with ports/connections, or promote to child_ssot with ssot path."
        )
        questions.append(question)
    return questions


def _blocker_metadata(questions: list[dict]) -> dict[str, str]:
    rtl_impl_blockers = {
        "RTL_TODO_PLAN_MISSING",
        "DETERMINISTIC_RTL_ARTIFACT_NOT_APPROVED",
        "LLM_RTL_IMPLEMENTATION_REQUIRED",
        "COMMON_AI_AGENT_RTL_PROVENANCE_REQUIRED",
    }
    ids = {str(q.get("id") or "") for q in questions if isinstance(q, dict)}
    if ids and ids <= rtl_impl_blockers:
        return {
            "owner": "rtl-gen LLM authoring loop",
            "reason": "LLM-authored RTL evidence is missing or stale.",
            "next_action": "Run rtl-gen against rtl_todo_plan.json, replace stale generated artifacts, then rerun /ssot-rtl.",
        }
    if ids & rtl_impl_blockers:
        return {
            "owner": "ssot-gen + rtl-gen",
            "reason": "SSOT semantics and LLM-authored RTL evidence both need repair before approval.",
            "next_action": "Resolve SSOT questions first, then run rtl-gen against rtl_todo_plan.json and rerun /ssot-rtl.",
        }
    return {
        "owner": "ssot-gen",
        "reason": "SSOT behavior is not concrete enough for production RTL implementation.",
        "next_action": (
            "Answer the rtl_blocked.json questions inline so SSOT-gen can record them, "
            "update SSOT, then rerun /ssot-rtl."
        ),
    }


def _read_json_dict(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return doc if isinstance(doc, dict) else {}


def _connection_contract_gap(ip_dir: Path, plan: dict[str, Any]) -> dict[str, Any]:
    """Return the production connection-contract gap from authoring/plan evidence."""

    authoring = _read_json_dict(ip_dir / "rtl" / "rtl_authoring_plan.json")
    policy = authoring.get("execution_policy") if isinstance(authoring.get("execution_policy"), dict) else {}
    if isinstance(policy.get("connection_contract_gap"), dict):
        return dict(policy.get("connection_contract_gap") or {})

    for key in ("execution_policy", "policy"):
        container = plan.get(key) if isinstance(plan.get(key), dict) else {}
        if isinstance(container.get("connection_contract_gap"), dict):
            return dict(container.get("connection_contract_gap") or {})

    summary = plan.get("summary") if isinstance(plan.get("summary"), dict) else {}
    plan_policy = plan.get("policy") if isinstance(plan.get("policy"), dict) else {}
    quality_profile = str(plan_policy.get("rtl_quality_profile") or summary.get("rtl_quality_profile") or "standard")
    top = str(plan.get("top") or "")
    owner_modules = summary.get("owner_modules") if isinstance(summary.get("owner_modules"), list) else []
    child_count = sum(
        1
        for item in owner_modules
        if isinstance(item, dict) and str(item.get("name") or "") != top and not item.get("wiring_only")
    )
    contracts = plan.get("ssot_connection_contracts") if isinstance(plan.get("ssot_connection_contracts"), list) else []
    required = quality_profile == "production" and child_count > 0
    return {
        "status": "missing" if required and not contracts else "ok",
        "required_for_profile": required,
        "machine_readable_contract_count": len(contracts),
        "reason": (
            "Production-profile multi-module RTL requires machine-readable integration.connections "
            "or sub_modules[].connections before top integration or signoff can close."
        ),
    }


def _connection_contract_suggestions(ip_dir: Path, plan: dict[str, Any]) -> dict[str, Any]:
    suggestions = plan.get("connection_contract_suggestions") if isinstance(plan.get("connection_contract_suggestions"), dict) else {}
    if not suggestions:
        suggestions = _read_json_dict(ip_dir / "rtl" / "connection_contract_suggestions.json")
    rows = suggestions.get("rows") if isinstance(suggestions.get("rows"), list) else []
    summary = suggestions.get("summary") if isinstance(suggestions.get("summary"), dict) else {}
    if not rows:
        return {}
    return {
        "path": "rtl/connection_contract_suggestions.json",
        "summary": summary,
        "sample_rows": [
            {
                key: row.get(key)
                for key in ("module", "instance", "port", "signal", "direction", "confidence", "review_status")
                if key in row
            }
            for row in rows[:16]
            if isinstance(row, dict)
        ],
        "rule": suggestions.get("rule"),
    }


def _reference_scale_gap(ip_dir: Path, plan: dict[str, Any]) -> dict[str, Any]:
    gap = plan.get("reference_scale_gap") if isinstance(plan.get("reference_scale_gap"), dict) else {}
    if not gap:
        gap = _read_json_dict(ip_dir / "rtl" / "reference_scale_gap.json")
    metrics = gap.get("metrics") if isinstance(gap.get("metrics"), dict) else {}
    if not metrics:
        return {}
    compact_metrics = {}
    for key in ("source_files", "modules", "lines", "instances", "procedural_blocks", "nonconstant_assigns"):
        item = metrics.get(key)
        if isinstance(item, dict):
            compact_metrics[key] = {
                field: item.get(field)
                for field in ("current", "reference", "ratio", "percent")
                if field in item
            }
    return {
        "path": "rtl/reference_scale_gap.json",
        "status": gap.get("status"),
        "reference_basis": gap.get("reference_basis"),
        "metrics": compact_metrics,
        "below_reference": gap.get("below_reference")[:12] if isinstance(gap.get("below_reference"), list) else [],
        "rule": gap.get("rule"),
    }


def _target_scale_policy_requires_review(ip_dir: Path, plan: dict[str, Any]) -> bool:
    """Return true only when target-scale review has real reference evidence.

    Target scale is a production signoff policy. It should not stop draft RTL
    or ordinary small-IP pipeline runs when no calibration/reference profile is
    present. If a reference candidate or scale-gap report exists, keep the
    human lock/waiver requirement.
    """
    reference_profile = plan.get("reference_profile") if isinstance(plan.get("reference_profile"), dict) else {}
    candidate = (
        reference_profile.get("suggested_ssot_target_scale")
        if isinstance(reference_profile.get("suggested_ssot_target_scale"), dict)
        else {}
    )
    gap = _reference_scale_gap(ip_dir, plan)
    summary = plan.get("summary") if isinstance(plan.get("summary"), dict) else {}
    return bool(candidate or gap or summary.get("reference_profile_present"))


def _connection_contract_gap_blocks_human_gate(ip_dir: Path, plan: dict[str, Any]) -> bool:
    gap = _connection_contract_gap(ip_dir, plan)
    return gap.get("required_for_profile") is True and gap.get("status") == "missing"


def _dynamic_todo_blocker_ids(ip_dir: Path) -> set[str]:
    """Return currently-applicable dynamic TODO blocker IDs.

    `derive_rtl_todos.py` owns the full TODO ledger. This preflight script
    may run immediately after it, so do not discard its broader blocker
    questions when adding semantic SSOT questions. Stale dynamic blockers are
    preserved only when the current `rtl_todo_plan.json` still reports the
    matching blocker condition.
    """

    plan = _read_json_dict(ip_dir / "rtl" / "rtl_todo_plan.json")
    summary = plan.get("summary") if isinstance(plan.get("summary"), dict) else {}
    ids: set[str] = set()
    if int(summary.get("orphan_tasks") or 0) > 0:
        ids.add("RTL_DYNAMIC_TODO_OWNERSHIP")
    blockers = plan.get("blockers") if isinstance(plan.get("blockers"), list) else []
    if blockers:
        ids.add("RTL_DYNAMIC_TODO_SSOT_REQUIRED_SECTIONS")
    for task in plan.get("tasks") if isinstance(plan.get("tasks"), list) else []:
        if not isinstance(task, dict):
            continue
        gate = task.get("gate_todo") if isinstance(task.get("gate_todo"), dict) else {}
        completion = task.get("todo_completion") if isinstance(task.get("todo_completion"), dict) else {}
        if gate.get("kind") == "target_scale_policy" and completion.get("status") != "pass":
            target_scale = plan.get("target_scale") if isinstance(plan.get("target_scale"), dict) else {}
            waiver = plan.get("target_scale_waiver") if isinstance(plan.get("target_scale_waiver"), dict) else {}
            if (
                _target_scale_policy_requires_review(ip_dir, plan)
                and not target_scale
                and not (waiver.get("approved") is True and waiver.get("reason"))
            ):
                ids.add("RTL_TARGET_SCALE_POLICY")
        if (
            gate.get("kind") == "manifest_connection_contract_evidence"
            and completion.get("status") != "pass"
            and _connection_contract_gap_blocks_human_gate(ip_dir, plan)
        ):
            ids.add("RTL_RESOLVE_CONNECTION_CONTRACTS")
    return ids


def _orphan_groups(orphans: list[dict[str, Any]], limit: int = 24) -> list[dict[str, Any]]:
    field_by_section = {
        "function_model": "function_model_refs",
        "cycle_model": "cycle_model_refs",
        "registers": "register_refs",
        "dataflow": "dataflow_refs",
        "features": "feature_refs",
        "fsm": "fsm_refs",
    }
    groups: dict[tuple[str, str, str], dict[str, Any]] = {}
    for item in orphans:
        if not isinstance(item, dict):
            continue
        source_ref = str(item.get("source_ref") or "").strip()
        category = str(item.get("category") or "").strip()
        section = source_ref.split(".", 1)[0] if "." in source_ref else source_ref
        field = field_by_section.get(section, "ssot_refs")
        key = (section, category, field)
        group = groups.setdefault(
            key,
            {
                "section_id": section,
                "category": category,
                "required_field": f"sub_modules[].{field}",
                "count": 0,
                "sample_refs": [],
            },
        )
        group["count"] += 1
        if source_ref and len(group["sample_refs"]) < 12:
            group["sample_refs"].append(source_ref)
    return sorted(groups.values(), key=lambda item: (-int(item["count"]), item["section_id"], item["category"]))[:limit]


def _merge_existing_dynamic_blocker_questions(ip_dir: Path, questions: list[dict]) -> list[dict]:
    allowed = _dynamic_todo_blocker_ids(ip_dir)
    if not allowed:
        return questions
    plan = _read_json_dict(ip_dir / "rtl" / "rtl_todo_plan.json")
    summary = plan.get("summary") if isinstance(plan.get("summary"), dict) else {}
    existing = _read_json_dict(ip_dir / "rtl" / "rtl_blocked.json")
    prior_questions = existing.get("questions") if isinstance(existing.get("questions"), list) else []
    merged = list(questions)
    seen = {str(q.get("id") or "") for q in merged if isinstance(q, dict)}
    for q in prior_questions:
        if not isinstance(q, dict):
            continue
        qid = str(q.get("id") or "").strip()
        if qid in allowed and qid not in seen:
            if qid == "RTL_DYNAMIC_TODO_OWNERSHIP" and "orphan_groups" not in q:
                orphans = plan.get("orphans") if isinstance(plan.get("orphans"), list) else []
                q = {**q, "orphan_groups": _orphan_groups(orphans)}
            merged.append(q)
            seen.add(qid)
    if "RTL_DYNAMIC_TODO_OWNERSHIP" in allowed and "RTL_DYNAMIC_TODO_OWNERSHIP" not in seen:
        orphans = plan.get("orphans") if isinstance(plan.get("orphans"), list) else []
        owner_modules = summary.get("owner_modules") if isinstance(summary.get("owner_modules"), list) else []
        merged.append({
            "id": "RTL_DYNAMIC_TODO_OWNERSHIP",
            "decision_needed": "Assign every SSOT-derived function/cycle/register/dataflow/FSM task to an RTL module owner.",
            "evidence": "rtl/rtl_todo_plan.json orphans",
            "options": [
                "Add exact sub_modules[].*_refs ownership for each orphan source_ref.",
                "Split or refine SSOT decomposition until each behavior has one RTL owner.",
                "Promote independently verified blocks to child_ssot with an explicit SSOT path.",
            ],
            "recommended_default": "Patch sub_modules[] with function_model_refs, cycle_model_refs, register_refs, dataflow_refs, and fsm_refs.",
            "orphan_refs": [item.get("source_ref") for item in orphans[:128] if isinstance(item, dict)],
            "orphan_groups": _orphan_groups(orphans),
            "candidate_modules": owner_modules[:32],
            "required_fields": [
                "sub_modules[].function_model_refs",
                "sub_modules[].cycle_model_refs",
                "sub_modules[].register_refs",
                "sub_modules[].dataflow_refs",
                "sub_modules[].fsm_refs",
            ],
            "answer_schema": {
                "format": "YAML or JSON",
                "root_key": "module_contracts",
                "rule": "Every orphan source_ref must be covered by an exact ref or a dotted parent ref in the owning sub_modules[] row.",
            },
        })
        seen.add("RTL_DYNAMIC_TODO_OWNERSHIP")
    if "RTL_DYNAMIC_TODO_SSOT_REQUIRED_SECTIONS" in allowed and "RTL_DYNAMIC_TODO_SSOT_REQUIRED_SECTIONS" not in seen:
        blockers = plan.get("blockers") if isinstance(plan.get("blockers"), list) else []
        merged.append({
            "id": "RTL_DYNAMIC_TODO_SSOT_REQUIRED_SECTIONS",
            "decision_needed": "Repair the SSOT so rtl-gen has mandatory source sections and well-formed SSOT-defined workflow todos.",
            "evidence": "rtl/rtl_todo_plan.json blockers",
            "options": [
                "Update SSOT with structured function_model and cycle_model sections.",
                "Update workflow_todos.rtl-gen[] entries so every item has content, detail, and criteria.",
                "Move non-RTL intent out of RTL implementation sections and rerun /ssot-rtl.",
            ],
            "recommended_default": "Use ssot-gen to fill function_model, cycle_model, workflow_todos.rtl-gen content/detail/criteria, decomposition, DV plan, and coverage from the requirement.",
            "blocking_items": blockers[:32],
        })
        seen.add("RTL_DYNAMIC_TODO_SSOT_REQUIRED_SECTIONS")
    if "RTL_TARGET_SCALE_POLICY" in allowed and "RTL_TARGET_SCALE_POLICY" not in seen:
        reference_profile = plan.get("reference_profile") if isinstance(plan.get("reference_profile"), dict) else {}
        scale_gap = _reference_scale_gap(ip_dir, plan)
        candidate = (
            reference_profile.get("suggested_ssot_target_scale")
            if isinstance(reference_profile.get("suggested_ssot_target_scale"), dict)
            else {}
        )
        target_scale_example = {
            key: value
            for key, value in candidate.items()
            if key
            in {
                "source_files_min",
                "modules_min",
                "lines_min",
                "depth_score_min",
                "nonconstant_assigns_min",
                "procedural_blocks_min",
                "instances_min",
                "basis",
            }
        }
        if not any(key.endswith("_min") for key in target_scale_example):
            target_scale_example = {
                "source_files_min": 4,
                "modules_min": 8,
                "lines_min": 1200,
                "depth_score_min": 120,
                "basis": "Human-approved architecture review calibrated from rtl_reference_profile.json.",
            }
        merged.append({
            "id": "RTL_TARGET_SCALE_POLICY",
            "decision_needed": "Lock or explicitly waive production RTL target scale before PL330-level PASS claims.",
            "evidence": "rtl/rtl_todo_plan.json target_scale_policy gate",
            "options": [
                "Review the reference-derived suggested_ssot_target_scale and copy approved positive minima into quality_gates.rtl_gen.target_scale.",
                "Provide edited human-approved target_scale minima calibrated from architecture review.",
                "If this IP intentionally does not enforce reference scale, set quality_gates.rtl_gen.target_scale_waiver.approved=true with a reason.",
            ],
            "recommended_default": "Treat suggested_ssot_target_scale as a review candidate only; lock it in SSOT target_scale only after human architecture approval.",
            "suggested_ssot_target_scale": candidate,
            "reference_scale_gap": scale_gap,
            "current_target_scale": plan.get("target_scale") if isinstance(plan.get("target_scale"), dict) else {},
            "current_target_scale_waiver": plan.get("target_scale_waiver") if isinstance(plan.get("target_scale_waiver"), dict) else {},
            "answer_schema": {
                "format": "YAML or JSON",
                "root_key": "target_scale or target_scale_waiver",
                "target_scale_example": target_scale_example,
                "waiver_example": {"approved": True, "reason": "architecture review intentionally targets a smaller implementation"},
                "rule": "Do not lock a reference-derived candidate without human review; do not copy reference RTL.",
            },
        })
        seen.add("RTL_TARGET_SCALE_POLICY")
    if "RTL_RESOLVE_CONNECTION_CONTRACTS" in allowed and "RTL_RESOLVE_CONNECTION_CONTRACTS" not in seen:
        connection_gap = _connection_contract_gap(ip_dir, plan)
        connection_suggestions = _connection_contract_suggestions(ip_dir, plan)
        owner_modules = summary.get("owner_modules") if isinstance(summary.get("owner_modules"), list) else []
        active_children = [
            {"name": item.get("name"), "file": item.get("file")}
            for item in owner_modules
            if isinstance(item, dict) and item.get("name") != plan.get("top") and not item.get("wiring_only")
        ][:32]
        merged.append({
            "id": "RTL_RESOLVE_CONNECTION_CONTRACTS",
            "decision_needed": "Resolve production multi-module connection contracts before top integration signoff.",
            "evidence": "rtl/rtl_todo_plan.json manifest_connection_contract_evidence gate",
            "options": [
                "Add machine-readable integration.connections rows with module, port, and signal.",
                "Add sub_modules[].connections port maps for every active child module port that participates in top integration.",
                "Defer top PASS/signoff while child module drafts continue from their owner packets.",
            ],
            "recommended_default": "Answer with YAML/JSON connection_contracts rows; option clicks alone do not approve wiring.",
            "connection_contract_gap": connection_gap,
            "pending_connection_contract_suggestions": connection_suggestions,
            "active_child_modules": active_children,
            "required_fields": ["integration.connections[].module", "integration.connections[].port", "integration.connections[].signal"],
            "answer_schema": {
                "format": "YAML or JSON",
                "root_key": "connection_contracts",
                "item_required_fields": ["module", "port", "signal"],
                "item_optional_fields": [
                    "instance",
                    "direction",
                    "source_ref",
                    "allow_constant",
                    "allow_unused",
                    "tieoff",
                    "reason",
                ],
                "rule": "Only approved rows become SSOT wiring contracts; do not infer missing wiring from RTL.",
            },
        })
        seen.add("RTL_RESOLVE_CONNECTION_CONTRACTS")
    return merged


def _write_blocked(ip_dir: Path, ip: str, top: str, questions: list[dict]) -> None:
    question_ids = {
        str(question.get("id") or "")
        for question in questions
        if isinstance(question, dict)
    }
    next_action = "Answer SSOT questions or complete the RTL authoring evidence, then rerun /ssot-rtl."
    if "RTL_RESOLVE_CONNECTION_CONTRACTS" in question_ids:
        next_action = (
            "Run prepare_rtl_human_review.py to review connection_contracts suggestions, "
            "record approved wiring in SSOT, then rerun /ssot-rtl."
        )
    out = {
        "schema_version": 1,
        "type": "rtl_blocker",
        "status": "blocked",
        "owner": "ssot-gen",
        "ip": ip,
        "top": top,
        "reason": "RTL preflight requires SSOT decision or LLM-authored RTL evidence.",
        "questions": questions,
        "next_action": next_action,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    path = ip_dir / "rtl" / "rtl_blocked.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def preflight(ip: str, root: Path, mode: str = "signoff") -> None:
    """Validate that the SSOT has enough semantic contract for rtl-gen."""

    mode = _normalize_run_mode(mode)
    ip_dir = root / ip
    ssot = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    if not ssot.is_file():
        raise SystemExit(f"[ssot_to_rtl] missing {ssot}")
    doc = yaml.safe_load(ssot.read_text(encoding="utf-8")) or {}
    if not isinstance(doc, dict):
        raise SystemExit("[ssot_to_rtl] SSOT top-level must be mapping")
    top = _ident(_top_name(doc, ip))
    ports = _io_ports(doc) or _as_ports(doc)
    (ip_dir / "rtl").mkdir(parents=True, exist_ok=True)
    blocked_path = ip_dir / "rtl" / "rtl_blocked.json"
    if mode == "starter":
        if _starter_sequential_intent(doc):
            contract, hard_questions = _generic_rule_contract(doc, top, ports, readable=True)
            soft_gates = []
        else:
            contract, hard_questions, soft_gates = _starter_preview_contract(doc, top, ports)
        soft_gates = [
            *soft_gates,
            {
                "id": "STARTER_LLM_RTL_AUTHORING_REQUIRED",
                "severity": "warning",
                "status": "handoff",
                "message": "Starter contract is ready for LLM-authored RTL; Starter gates are relaxed but RTL must be real authored RTL.",
            },
        ]
        deferred_questions = _rtl_contract_questions(doc, top) + _merge_existing_dynamic_blocker_questions(ip_dir, [])
        if hard_questions:
            _write_blocked(ip_dir, ip, top, hard_questions)
            print(f"[SSOT QUESTION] starter rtl handoff blocked for {ip}: {len(hard_questions)} hard gate(s)")
            for q in hard_questions:
                print(f"- {q['id']}: {q['decision_needed']}")
            raise SystemExit(2)
        _write_starter_llm_handoff_artifacts(ip_dir, ip, top, contract, soft_gates, deferred_questions)
        if blocked_path.exists():
            blocked_path.unlink()
        print(
            f"[rtl-preflight] PASS: {ip} starter contract ready for LLM-authored RTL "
            f"(soft={len(soft_gates)} deferred={len(deferred_questions)})"
        )
        return
    questions = _rtl_contract_questions(doc, top)
    if questions:
        merged_questions = _merge_existing_dynamic_blocker_questions(ip_dir, questions)
        _write_blocked(ip_dir, ip, top, merged_questions)
        print(f"[SSOT QUESTION] rtl-gen preflight blocked for {ip}: {len(merged_questions)} SSOT decision(s) required")
        for q in merged_questions:
            print(f"- {q['id']}: {q['decision_needed']}")
        raise SystemExit(2)
    dynamic_questions = _merge_existing_dynamic_blocker_questions(ip_dir, [])
    if dynamic_questions:
        _write_blocked(ip_dir, ip, top, dynamic_questions)
        print(f"[SSOT QUESTION] rtl-gen preflight blocked for {ip}: {len(dynamic_questions)} dynamic TODO decision(s) required")
        for q in dynamic_questions:
            print(f"- {q['id']}: {q['decision_needed']}")
        raise SystemExit(2)
    if blocked_path.exists() and not _dynamic_todo_blocker_ids(ip_dir):
        blocked_path.unlink()
    print(f"[rtl-preflight] PASS: {ip} SSOT has concrete function_model/cycle_model contract for rtl-gen")


def _expected_rtl_files(doc: dict, top: str) -> list[str]:
    """Return the SSOT-declared RTL manifest without generating any RTL."""
    files: list[str] = []
    for submod in _manifest_submodules(doc):
        rel = str(submod.get("file") or "").strip()
        if rel:
            files.append(rel)
    filelist = doc.get("filelist") if isinstance(doc.get("filelist"), dict) else {}
    for rel in filelist.get("rtl") or []:
        if isinstance(rel, str) and rel.strip():
            files.append(rel.strip())
    if not files:
        files.append(f"rtl/{top}.sv")
    seen: set[str] = set()
    unique: list[str] = []
    for rel in files:
        rel = rel.strip()
        if not rel or rel in seen:
            continue
        seen.add(rel)
        unique.append(rel)
    return unique


def _requirements_authority_present(ip_dir: Path) -> bool:
    path = ip_dir / "req" / "requirements.md"
    if not path.is_file():
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return len(re.findall(r"[A-Za-z0-9_]+", text)) >= 24


def _generic_rule_seed_owned(ip_dir: Path, expected_files: list[str]) -> bool:
    provenance = ip_dir / "rtl" / "rtl_authoring_provenance.json"
    if not provenance.is_file():
        return False
    try:
        doc = json.loads(provenance.read_text(encoding="utf-8"))
    except Exception:
        return False
    if doc.get("generator") != "generic_ssot_rule_seed":
        return False
    rtl_files = doc.get("rtl_files") if isinstance(doc.get("rtl_files"), list) else []
    return all(rel in rtl_files for rel in expected_files)


def _can_write_generic_rule_seed(ip_dir: Path, expected_files: list[str], top: str) -> bool:
    if expected_files != [f"rtl/{top}.sv"]:
        return False
    existing = [rel for rel in expected_files if (ip_dir / rel).exists()]
    return not existing or _generic_rule_seed_owned(ip_dir, expected_files)


def _generic_rule_seed_allowed(ip_dir: Path, top: str, contract: dict, expected_files: list[str]) -> bool:
    # Policy: Starter/Engineering/Signoff differ by gate strictness, not by
    # whether RTL is real. Keep the rule contract helpers for authoring,
    # scoreboard, and compatibility, but do not write generated RTL here.
    return False


def _sv_range(width: int) -> str:
    width = max(int(width or 1), 1)
    return "" if width == 1 else f"[{width - 1}:0] "


def _sv_zero(width: int) -> str:
    width = max(int(width or 1), 1)
    return "1'b0" if width == 1 else f"{width}'d0"


def _sv_int_literal(width: int, value: object) -> str:
    width = max(int(width or 1), 1)
    parsed = _int_value(value, 0)
    if width == 1:
        return "1'b1" if parsed & 1 else "1'b0"
    mask = (1 << width) - 1
    return f"{width}'d{parsed & mask}"


def _sv_port_decl(port: dict, procedural_outputs: set[str] | None = None) -> str:
    direction = str(port.get("direction") or "input").lower()
    if direction not in {"input", "output", "inout"}:
        direction = "input"
    name = str(port["name"])
    net_type = "wire" if direction == "inout" else "logic"
    return f"{direction} {net_type} {_sv_range(_port_width(port))}{name}"


def _sv_marker_names(doc: dict, contract: dict) -> list[str]:
    raw: list[str] = []
    for item in doc.get("features") or []:
        if isinstance(item, dict):
            raw.append(str(item.get("name") or ""))
    cm = doc.get("cycle_model") if isinstance(doc.get("cycle_model"), dict) else {}
    for item in cm.get("handshake_rules") or []:
        if isinstance(item, dict):
            raw.append(str(item.get("name") or item.get("id") or ""))
    fm_tx = contract.get("transaction")
    if fm_tx:
        raw.append(str(fm_tx))
    tr = doc.get("test_requirements") if isinstance(doc.get("test_requirements"), dict) else {}
    for item in tr.get("scenarios") or []:
        if isinstance(item, dict):
            raw.append(str(item.get("id") or item.get("name") or ""))
    cov = tr.get("coverage_goals") if isinstance(tr.get("coverage_goals"), dict) else {}
    for item in cov.get("planned_bins") or []:
        if isinstance(item, dict):
            raw.append(str(item.get("id") or item.get("name") or ""))
    seen: set[str] = set()
    out: list[str] = []
    for value in raw:
        ident = _ident(value)
        if not ident or ident in seen:
            continue
        seen.add(ident)
        out.append(ident)
    return out[:16]


def _generic_rule_rtl_source(ip: str, top: str, ports: list[dict], contract: dict, doc: dict) -> str:
    by_name = {p["name"]: p for p in ports}
    output_ports = {p["name"] for p in ports if str(p.get("direction") or "").lower() == "output"}
    net_keyword = "wire"
    reg_keyword = "logic"
    always_keyword = "always"
    clock = _ident(contract.get("clock") or "clk")
    reset = _ident(contract.get("reset") or "rst_n")
    reset_active = str(contract.get("reset_active") or "low").lower()
    reset_edge = "negedge" if reset_active == "low" else "posedge"
    reset_test = f"!{reset}" if reset_active == "low" else reset
    reset_inactive = f"{reset}" if reset_active == "low" else f"!{reset}"
    special = contract.get("special_outputs") if isinstance(contract.get("special_outputs"), dict) else {}
    ready_port = _ident(special.get("ready_output") or "")
    valid_port = _ident(special.get("output_valid") or special.get("valid_output") or "")
    state_vars = contract.get("state_vars") if isinstance(contract.get("state_vars"), dict) else {}
    state_updates = [item for item in contract.get("state_updates") or [] if isinstance(item, dict)]
    output_rules = [item for item in contract.get("outputs") or [] if isinstance(item, dict)]
    marker_names = _sv_marker_names(doc, contract)

    driven: set[str] = set()
    for item in output_rules:
        port = _ident(item.get("port") or item.get("name") or "")
        if port:
            driven.add(port)
    for item in state_updates:
        name = _ident(item.get("name") or "")
        if name in output_ports:
            driven.add(name)
    if ready_port:
        driven.add(ready_port)
    if valid_port:
        driven.add(valid_port)

    declared_internal: set[str] = set()
    lines: list[str] = [
        f"module {top} (",
    ]
    for idx, port in enumerate(ports):
        suffix = "," if idx < len(ports) - 1 else ""
        lines.append(f"    {_sv_port_decl(port, driven)}{suffix}")
    lines += [
        ");",
        "",
    ]

    for name, spec in sorted(state_vars.items()):
        state_name = _ident(name)
        if state_name in output_ports:
            continue
        width = max(_int_value((spec or {}).get("width"), 32) if isinstance(spec, dict) else 32, 1)
        lines.append(f"    {reg_keyword} {_sv_range(width)}{state_name};")
        declared_internal.add(state_name)
    if state_vars:
        lines.append("")

    marker_terms: list[str] = []
    for marker in marker_names:
        wire = f"ssot_{marker}_marker"
        lines.append(f"    {net_keyword} {wire};")
        lines.append(f"    assign {wire} = 1'b1;")
        marker_terms.append(wire)
    if marker_terms:
        lines.append("")

    lines.append(f"    {net_keyword} ssot_requirements_guard;")
    guard_expr = " && ".join(["1'b1", *marker_terms])
    lines.append(f"    assign ssot_requirements_guard = {guard_expr};")
    lines.append("")
    lines.append(f"    {net_keyword} sample_fire;")
    sample_condition = str(contract.get("sample_condition") or "1'b1")
    lines.append(f"    assign sample_fire = {_rtl_bool(sample_condition)} && ssot_requirements_guard;")
    if ready_port:
        lines.append(f"    {net_keyword} ready_live;")
        lines.append("    assign ready_live = sample_fire || !sample_fire;")
    lines.append("")

    lines.append(f"    {always_keyword} @(posedge {clock} or {reset_edge} {reset}) begin")
    lines.append(f"        if ({reset_test}) begin")
    for item in output_rules:
        port = _ident(item.get("port") or item.get("name") or "")
        if not port:
            continue
        width = _port_width(by_name.get(port, {"width": item.get("width", 1)}))
        lines.append(f"            {port} <= {_sv_zero(width)};")
    for name, spec in sorted(state_vars.items()):
        state_name = _ident(name)
        width = _port_width(by_name.get(state_name, {"width": (spec or {}).get("width", 32) if isinstance(spec, dict) else 32}))
        reset_value = (spec or {}).get("reset", 0) if isinstance(spec, dict) else 0
        lines.append(f"            {state_name} <= {_sv_int_literal(width, reset_value)};")
    if ready_port:
        lines.append(f"            {ready_port} <= 1'b0;")
    if valid_port and valid_port not in {ready_port}:
        lines.append(f"            {valid_port} <= 1'b0;")
    lines.append("        end else begin")
    lines.append(f"            if ({reset_inactive}) begin")
    if ready_port:
        lines.append(f"                {ready_port} <= ready_live;")
    if valid_port:
        lines.append(f"                {valid_port} <= 1'b0;")
    lines.append("                if (sample_fire) begin")
    for item in output_rules:
        port = _ident(item.get("port") or item.get("name") or "")
        if not port:
            continue
        width = _port_width(by_name.get(port, {"width": item.get("width", 1)}))
        lines.append(f"                    {port} <= {_sv_width_cast(width, str(item.get('expr') or '0'))};")
    for item in state_updates:
        name = _ident(item.get("name") or "")
        if not name:
            continue
        spec = state_vars.get(name) if isinstance(state_vars, dict) else {}
        width = _port_width(by_name.get(name, {"width": (spec or {}).get("width", item.get("width", 32)) if isinstance(spec, dict) else item.get("width", 32)}))
        lines.append(f"                    {name} <= {_sv_width_cast(width, str(item.get('expr') or '0'))};")
    if valid_port:
        lines.append(f"                    {valid_port} <= sample_fire;")
    lines.append("                end")
    lines.append("            end")
    lines.append("        end")
    lines.append("    end")

    undriven = sorted(output_ports - driven)
    if undriven:
        lines.append("")
        for port in undriven:
            width = _port_width(by_name.get(port, {"width": 1}))
            lines.append(f"    assign {port} = {_sv_zero(width)};")

    lines += [
        "endmodule",
        "",
    ]
    return "\n".join(lines)


def _generic_rule_rtl(top: str, ports: list[dict], contract: dict) -> str:
    """Legacy Verilog helper kept for unit-level contract checks."""

    by_name = {p["name"]: p for p in ports}
    output_ports = {p["name"] for p in ports if str(p.get("direction") or "").lower() == "output"}
    clock = _ident(contract.get("clock") or "clk")
    reset = _ident(contract.get("reset") or "rst_n")
    reset_active = str(contract.get("reset_active") or "low").lower()
    reset_edge = "negedge" if reset_active == "low" else "posedge"
    reset_test = f"!{reset}" if reset_active == "low" else reset
    reset_inactive = f"!(!{reset})" if reset_active == "low" else f"!({reset})"
    sample_condition = str(contract.get("sample_condition") or "1'b1").strip() or "1'b1"
    state_vars = contract.get("state_vars") if isinstance(contract.get("state_vars"), dict) else {}
    state_updates = [item for item in contract.get("state_updates") or [] if isinstance(item, dict)]
    output_rules = [item for item in contract.get("outputs") or [] if isinstance(item, dict)]
    updated_names = {_ident(item.get("name") or "") for item in state_updates if _ident(item.get("name") or "")}
    apb_default = {"psel", "penable", "pready"}.issubset(set(by_name))

    def _legacy_port_decl(port: dict) -> str:
        direction = str(port.get("direction") or "input").lower()
        name = str(port["name"])
        rng = _sv_range(_port_width(port)).strip()
        prefix = f"{direction} "
        if direction == "output":
            prefix += "reg "
        return (prefix + (rng + " " if rng else "") + name).strip()

    lines = [f"module {top} ("]
    for idx, port in enumerate(ports):
        suffix = "," if idx < len(ports) - 1 else ""
        lines.append(f"    {_legacy_port_decl(port)}{suffix}")
    lines += [");", ""]

    for name, spec in sorted(state_vars.items()):
        state_name = _ident(name)
        if state_name in output_ports or state_name not in updated_names:
            continue
        width = max(_int_value((spec or {}).get("width"), 32) if isinstance(spec, dict) else 32, 1)
        lines.append(f"    reg {_sv_range(width)}{state_name};")
    if len(lines) > 3 and lines[-1].startswith("    reg "):
        lines.append("")

    lines.append(f"    always @(posedge {clock} or {reset_edge} {reset}) begin")
    lines.append(f"        if ({reset_test}) begin")
    reset_targets = sorted(output_ports | (updated_names - output_ports))
    for name in reset_targets:
        spec = state_vars.get(name) if isinstance(state_vars, dict) else {}
        width = _port_width(by_name.get(name, {"width": (spec or {}).get("width", 32) if isinstance(spec, dict) else 32}))
        reset_value = (spec or {}).get("reset", 0) if isinstance(spec, dict) else 0
        lines.append(f"            {name} <= {_sv_int_literal(width, reset_value)};")
    lines.append("        end else begin")
    lines.append(f"            if ({reset_inactive}) begin")
    if apb_default:
        if "pready" in output_ports:
            lines.append(f"                pready = {sample_condition};")
        for port in ("pslverr", "prdata"):
            if port in output_ports:
                lines.append(f"                {port} = {_sv_zero(_port_width(by_name[port]))};")
    for item in output_rules:
        port = _ident(item.get("port") or item.get("name") or "")
        if not port:
            continue
        width = _port_width(by_name.get(port, {"width": item.get("width", 1)}))
        lines.append(f"                {port} <= {_sv_width_cast(width, str(item.get('expr') or '0'))};")
    if state_updates:
        lines.append(f"                if ({_rtl_bool(sample_condition)}) begin")
        for item in state_updates:
            name = _ident(item.get("name") or "")
            if not name:
                continue
            spec = state_vars.get(name) if isinstance(state_vars, dict) else {}
            width = _port_width(by_name.get(name, {"width": (spec or {}).get("width", item.get("width", 32)) if isinstance(spec, dict) else item.get("width", 32)}))
            lines.append(f"                    {name} <= {_sv_width_cast(width, str(item.get('expr') or '0'))};")
        lines.append("                end")
    lines += ["            end", "        end", "    end", "endmodule", ""]
    return "\n".join(lines)


def _write_generic_rule_artifacts(ip_dir: Path, ip: str, top: str, ports: list[dict], contract: dict, doc: dict) -> None:
    rtl_dir = ip_dir / "rtl"
    list_dir = ip_dir / "list"
    rtl_dir.mkdir(parents=True, exist_ok=True)
    list_dir.mkdir(parents=True, exist_ok=True)
    rtl_rel = f"rtl/{top}.sv"
    rtl_path = ip_dir / rtl_rel
    rtl_path.write_text(_generic_rule_rtl_source(ip, top, ports, contract, doc), encoding="utf-8")
    (list_dir / f"{ip}.f").write_text(f"{rtl_rel}\n", encoding="utf-8")

    _write_generic_rule_contract_artifact(ip_dir, ip, top, contract)

    traceability = {
        "schema_version": 1,
        "type": "rtl_traceability",
        "ip": ip,
        "top": top,
        "rtl_files": [rtl_rel],
        "requirements_authority": f"{ip}/req/requirements.md",
        "source_refs": [
            "rtl_contract",
            "function_model.transactions",
            "function_model.state_variables",
            "cycle_model.handshake_rules",
            "test_requirements",
        ],
        "rule": "Generated only from executable SSOT rules with requirements authority.",
    }
    (rtl_dir / "rtl_traceability.json").write_text(json.dumps(traceability, indent=2) + "\n", encoding="utf-8")

    todo_plan = rtl_dir / "rtl_todo_plan.json"
    provenance = {
        "schema_version": 1,
        "type": "rtl_authoring_provenance",
        "agent": "common_ai_agent",
        "workflow": "rtl-gen",
        "surface": "headless_common_engine",
        "generator": "generic_ssot_rule_seed",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "todo_plan_sha256": _stable_json_sha256(todo_plan) if todo_plan.is_file() else "",
        "rtl_files": [rtl_rel],
        "authoring_packets": ["generic_ssot_rule_seed"],
    }
    (rtl_dir / "rtl_authoring_provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")


def _write_generic_rule_contract_artifact(ip_dir: Path, ip: str, top: str, contract: dict) -> None:
    rtl_dir = ip_dir / "rtl"
    rtl_dir.mkdir(parents=True, exist_ok=True)
    contract_doc = {
        "schema_version": 1,
        "type": "generic_ssot_rule_rtl_contract",
        "ip": ip,
        "top": top,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "contract": contract,
    }
    (rtl_dir / "rtl_contract.json").write_text(json.dumps(contract_doc, indent=2) + "\n", encoding="utf-8")


def _write_starter_llm_handoff_artifacts(
    ip_dir: Path,
    ip: str,
    top: str,
    contract: dict,
    soft_gates: list[dict],
    deferred_questions: list[dict],
) -> None:
    rtl_dir = ip_dir / "rtl"
    rtl_dir.mkdir(parents=True, exist_ok=True)
    contract_doc = {
        "schema_version": 1,
        "type": "starter_llm_rtl_authoring_contract",
        "ip": ip,
        "top": top,
        "mode": "starter",
        "contract": contract,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "rule": "Starter RTL must be authored by an LLM/worker and verified by gates; this file is an authoring contract, not generated RTL.",
    }
    (rtl_dir / "rtl_contract.json").write_text(json.dumps(contract_doc, indent=2) + "\n", encoding="utf-8")
    handoff = {
        "schema_version": 1,
        "type": "starter_llm_rtl_handoff",
        "ip": ip,
        "top": top,
        "mode": "starter",
        "target_rtl": f"rtl/{top}.sv",
        "target_filelist": f"list/{ip}.f",
        "authoring_surface": "llm_worker",
        "instructions": [
            "Author RTL directly from rtl/rtl_contract.json and the SSOT.",
            "Do not use rule-to-RTL generation for Starter IP.",
            "Write rtl_authoring_provenance.json after authoring.",
            "Run rtl_compile_report.py and starter_preview_sim.py before promoting the result.",
        ],
        "source_refs": [
            "top_module",
            "io_list",
            "rtl_contract",
            "function_model.state_variables",
            "function_model.transactions[].state_updates",
            "function_model.transactions[].output_rules",
        ],
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    (rtl_dir / "starter_llm_rtl_handoff.json").write_text(json.dumps(handoff, indent=2) + "\n", encoding="utf-8")
    gates = _starter_preview_gate_report(ip, top, soft_gates, deferred_questions, status="handoff")
    gates["hard_gates"].append({
        "id": "STARTER_LLM_RTL_AUTHORING_REQUIRED",
        "status": "required",
        "message": "Stateful Starter RTL must be authored by an LLM/worker before compile/sim gates can run.",
    })
    (rtl_dir / "rtl_preview_gates.json").write_text(json.dumps(gates, indent=2) + "\n", encoding="utf-8")


def _starter_preview_gate_report(
    ip: str,
    top: str,
    soft_gates: list[dict],
    deferred_questions: list[dict],
    *,
    status: str = "pass",
) -> dict[str, Any]:
    deferred = [
        {
            "id": str(q.get("id") or ""),
            "severity": "deferred",
            "status": "deferred",
            "decision_needed": q.get("decision_needed"),
            "evidence": q.get("evidence"),
        }
        for q in deferred_questions
        if isinstance(q, dict)
    ]
    return {
        "schema_version": 1,
        "type": "starter_rtl_preview_gates",
        "ip": ip,
        "top": top,
        "mode": "starter",
        "status": status,
        "hard_gates": [
            {"id": "STARTER_TOP_MODULE", "status": "pass"},
            {"id": "STARTER_IO_LIST", "status": "pass"},
            {"id": "STARTER_FUNCTION_MODEL", "status": "pass"},
            {"id": "STARTER_RTL_AUTHORING", "status": "pass" if status == "pass" else status},
        ],
        "soft_gates": soft_gates,
        "deferred_gates": deferred,
        "policy": (
            "Starter produces real LLM-authored RTL with relaxed gates. Deferred gates remain non-blocking "
            "in Starter and become blocking in Engineering/Signoff as applicable."
        ),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


RTL_TODO_HASH_VOLATILE_KEYS = {
    "connection_contract_suggestions",
    "contract_implementation_evidence",
    "generated_at",
    "gate",
    "manifest_hierarchy_evidence",
    "manifest_signal_flow_evidence",
    "owner_logic_evidence",
    "reference_profile",
    "reference_scale_gap",
    "rtl_implementation_depth_evidence",
    "rtl_placeholder_free_evidence",
    "static_evidence",
    "static_rtl_evidence",
    "todo_completion",
    "top_input_consumption_evidence",
    "top_io_contract_evidence",
    "top_output_drive_evidence",
}


def _stable_json_sha256(path: Path, volatile_keys: set[str] | None = None) -> str:
    volatile_keys = volatile_keys or RTL_TODO_HASH_VOLATILE_KEYS
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return ""

    def normalize(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                str(key): normalize(item)
                for key, item in value.items()
                if str(key) not in volatile_keys
            }
        if isinstance(value, list):
            return [normalize(item) for item in value]
        return value

    payload = json.dumps(normalize(data), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _rtl_authoring_provenance_issues(ip_dir: Path, expected_files: list[str]) -> list[str]:
    path = ip_dir / "rtl" / "rtl_authoring_provenance.json"
    todo_plan = ip_dir / "rtl" / "rtl_todo_plan.json"
    if not path.is_file():
        return ["missing rtl/rtl_authoring_provenance.json"]
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"rtl/rtl_authoring_provenance.json is not valid JSON: {exc}"]
    issues: list[str] = []
    if doc.get("type") != "rtl_authoring_provenance":
        issues.append("type must be rtl_authoring_provenance")
    if doc.get("agent") != "common_ai_agent":
        issues.append("agent must be common_ai_agent")
    if doc.get("workflow") != "rtl-gen":
        issues.append("workflow must be rtl-gen")
    if doc.get("surface") not in {"atlas_ui", "textual_ui", "headless_common_engine"}:
        issues.append("surface must be atlas_ui, textual_ui, or headless_common_engine")
    if todo_plan.is_file() and doc.get("todo_plan_sha256") not in {
        _sha256_file(todo_plan),
        _stable_json_sha256(todo_plan),
    }:
        issues.append("todo_plan_sha256 does not match current rtl_todo_plan.json")
    rtl_files = doc.get("rtl_files") if isinstance(doc.get("rtl_files"), list) else []
    missing_from_provenance = [rel for rel in expected_files if rel not in rtl_files]
    if missing_from_provenance:
        issues.append("provenance rtl_files does not list: " + ", ".join(missing_from_provenance[:12]))
    return issues


def _existing_rtl_preflight_questions(ip_dir: Path, ip: str, top: str, doc: dict) -> list[dict]:
    """Gate LLM-authored RTL presence. This script must not fill gaps with templates."""
    questions: list[dict] = []
    todo_plan = ip_dir / "rtl" / "rtl_todo_plan.json"
    if not todo_plan.is_file():
        questions.append(
            _question(
                "RTL_TODO_PLAN_MISSING",
                "Run SSOT-to-RTL TODO derivation before RTL implementation.",
                f"{todo_plan.relative_to(ip_dir)} is missing, so rtl-gen has no SSOT-derived content/detail/criteria ledger.",
                [f"Run derive_rtl_todos.py {ip} --root <project-root> before invoking the RTL authoring loop."],
                "Create the TODO plan from SSOT, then implement RTL against that ledger.",
                "Keeps implementation driven by SSOT TODO criteria instead of a fixed template.",
            )
        )

    expected = _expected_rtl_files(doc, top)
    missing = [rel for rel in expected if not (ip_dir / rel).is_file()]
    filelist = ip_dir / "list" / f"{ip}.f"
    if missing or not filelist.is_file():
        detail = []
        if missing:
            detail.append("missing RTL files: " + ", ".join(missing[:12]))
        if not filelist.is_file():
            detail.append(f"missing filelist: {filelist.relative_to(ip_dir)}")
        questions.append(
            _question(
                "LLM_RTL_IMPLEMENTATION_REQUIRED",
                "Generate real RTL from SSOT-derived TODOs before compile/lint/audit.",
                "; ".join(detail),
                [
                    "Read yaml/<ip>.ssot.yaml and rtl/rtl_todo_plan.json.",
                    "Write each SSOT-declared RTL file with traceable implementation for all required TODO criteria.",
                    "Write list/<ip>.f listing the LLM-authored RTL files in compile order.",
                    "Rerun /ssot-rtl so compile, DUT-only lint, and TODO audit can close the gates.",
                ],
                "LLM writes the RTL; scripts only derive TODOs, preflight manifests, and validate evidence.",
                "General-purpose IP generation cannot depend on hardcoded RTL templates.",
            )
        )
    else:
        provenance_issues = _rtl_authoring_provenance_issues(ip_dir, expected)
        if provenance_issues:
            questions.append(
                _question(
                    "COMMON_AI_AGENT_RTL_PROVENANCE_REQUIRED",
                    "Prove the RTL was authored by the common_ai_agent rtl-gen workflow, not by the operator.",
                    "; ".join(provenance_issues),
                    [
                        "Run rtl-gen through ATLAS UI, Textual UI, or headless common engine using rtl_todo_plan.json.",
                        "Have common_ai_agent write rtl/rtl_authoring_provenance.json after it writes RTL.",
                        "Include agent=common_ai_agent, workflow=rtl-gen, surface, todo_plan_sha256, and rtl_files.",
                    ],
                    "Operator-authored RTL is not valid evidence for this workflow.",
                    "Keeps the tool usable as a general RTL engineer workflow instead of relying on manual Codex edits.",
                )
            )
    return questions


def generate(ip: str, root: Path, mode: str = "signoff") -> None:
    mode = _normalize_run_mode(mode)
    ip_dir = root / ip
    ssot = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    if not ssot.is_file():
        raise SystemExit(f"[ssot_to_rtl] missing {ssot}")
    doc = yaml.safe_load(ssot.read_text(encoding="utf-8")) or {}
    if not isinstance(doc, dict):
        raise SystemExit("[ssot_to_rtl] SSOT top-level must be mapping")
    top = _ident(_top_name(doc, ip))
    ports = _io_ports(doc) or _as_ports(doc)
    (ip_dir / "rtl").mkdir(parents=True, exist_ok=True)
    (ip_dir / "list").mkdir(parents=True, exist_ok=True)
    blocked_path = ip_dir / "rtl" / "rtl_blocked.json"

    if mode == "starter":
        if _starter_sequential_intent(doc):
            contract, hard_questions = _generic_rule_contract(doc, top, ports, readable=True)
            soft_gates = []
        else:
            contract, hard_questions, soft_gates = _starter_preview_contract(doc, top, ports)
        soft_gates = [
            *soft_gates,
            {
                "id": "STARTER_LLM_RTL_AUTHORING_REQUIRED",
                "severity": "warning",
                "status": "handoff",
                "message": "Starter contract is ready for LLM-authored RTL; Starter gates are relaxed but RTL must be real authored RTL.",
            },
        ]
        deferred_questions = _rtl_contract_questions(doc, top) + _merge_existing_dynamic_blocker_questions(ip_dir, [])
        if hard_questions:
            _write_blocked(ip_dir, ip, top, hard_questions)
            print(f"[SSOT QUESTION] starter rtl handoff blocked for {ip}: {len(hard_questions)} hard gate(s)")
            for q in hard_questions:
                print(f"- {q['id']}: {q['decision_needed']}")
            raise SystemExit(2)
        implementation_questions = _existing_rtl_preflight_questions(ip_dir, ip, top, doc)
        if not implementation_questions:
            if blocked_path.exists():
                blocked_path.unlink()
            gates = _starter_preview_gate_report(ip, top, soft_gates, deferred_questions, status="pass")
            gates["hard_gates"].append({
                "id": "STARTER_LLM_RTL_AUTHORING_REQUIRED",
                "status": "pass",
                "message": "common_ai_agent rtl-gen provenance covers the Starter RTL manifest.",
            })
            (ip_dir / "rtl" / "rtl_preview_gates.json").write_text(
                json.dumps(gates, indent=2) + "\n",
                encoding="utf-8",
            )
            expected = _expected_rtl_files(doc, top)
            print(f"[ssot_to_rtl] starter preflight passed for LLM-authored RTL: {ip} ({len(expected)} manifest file(s))")
            return
        _write_starter_llm_handoff_artifacts(ip_dir, ip, top, contract, soft_gates, deferred_questions)
        _write_blocked(ip_dir, ip, top, [_question(
            "LLM_RTL_IMPLEMENTATION_REQUIRED",
            "Author Starter RTL with an LLM/worker, then run compile and sim gates.",
            "Starter relaxes gate depth only. RTL must be real LLM-authored RTL, not template output or rule-compiled YAML.",
            [
                f"Have the RTL worker author rtl/{top}.sv from rtl/starter_llm_rtl_handoff.json.",
                f"Write list/{ip}.f and rtl/rtl_authoring_provenance.json.",
                "Run rtl_compile_report.py and starter_preview_sim.py after authoring.",
            ],
            "Use LLM-authored RTL for Starter IP; keep rule contracts as authoring and verification evidence.",
            "Prevents Starter from becoming a YAML-to-RTL generator DSL while preserving relaxed Starter gates.",
        )])
        print(f"[RTL BLOCKED] [RTL HANDOFF] starter needs LLM-authored RTL for {ip}: rtl/starter_llm_rtl_handoff.json")
        raise SystemExit(2)

    contract_questions = _rtl_contract_questions(doc, top)
    if contract_questions:
        merged_questions = _merge_existing_dynamic_blocker_questions(ip_dir, contract_questions)
        _write_blocked(ip_dir, ip, top, merged_questions)
        print(f"[SSOT QUESTION] rtl-gen blocked for {ip}: {len(merged_questions)} SSOT decision/gate(s) required")
        for q in merged_questions:
            print(f"- {q['id']}: {q['decision_needed']}")
        raise SystemExit(2)

    if blocked_path.exists():
        blocked_path.unlink()

    fm_doc = doc.get("function_model") if isinstance(doc.get("function_model"), dict) else {}
    has_structured_rule_intent = bool(doc.get("rtl_contract")) or any(
        _rule_items(tx.get("output_rules"))
        for tx in (fm_doc.get("transactions") or [])
        if isinstance(tx, dict)
    )
    _generic_contract, generic_questions = _generic_rule_contract(doc, top, ports)
    if generic_questions and has_structured_rule_intent:
        merged_questions = _merge_existing_dynamic_blocker_questions(ip_dir, generic_questions)
        _write_blocked(ip_dir, ip, top, merged_questions)
        print(f"[SSOT QUESTION] rtl-gen blocked for {ip}: generic SSOT rule contract needs {len(merged_questions)} fix/gate(s)")
        for q in merged_questions:
            print(f"- {q['id']}: {q['decision_needed']}")
        raise SystemExit(2)
    if not generic_questions:
        _write_generic_rule_contract_artifact(ip_dir, ip, top, _generic_contract)

    expected = _expected_rtl_files(doc, top)
    if _generic_rule_seed_allowed(ip_dir, top, _generic_contract, expected):
        _write_generic_rule_artifacts(ip_dir, ip, top, ports, _generic_contract, doc)

    implementation_questions = _existing_rtl_preflight_questions(ip_dir, ip, top, doc)
    if implementation_questions:
        merged_questions = _merge_existing_dynamic_blocker_questions(ip_dir, implementation_questions)
        _write_blocked(ip_dir, ip, top, merged_questions)
        print(f"[RTL BLOCKED] rtl-gen waiting for LLM-authored RTL for {ip}: {len(merged_questions)} gate(s)")
        for q in merged_questions:
            print(f"- {q['id']}: {q['decision_needed']}")
        raise SystemExit(2)

    dynamic_questions = _merge_existing_dynamic_blocker_questions(ip_dir, [])
    if dynamic_questions:
        _write_blocked(ip_dir, ip, top, dynamic_questions)
        print(f"[SSOT QUESTION] rtl-gen blocked for {ip}: {len(dynamic_questions)} dynamic TODO decision(s) required")
        for q in dynamic_questions:
            print(f"- {q['id']}: {q['decision_needed']}")
        raise SystemExit(2)

    print(f"[ssot_to_rtl] preflight passed for LLM-authored RTL: {ip} ({len(expected)} manifest file(s))")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ip")
    ap.add_argument("--root", default=".")
    ap.add_argument("--mode", default="", help="starter, engineering, or signoff; defaults to ATLAS_RUN_MODE/signoff")
    ap.add_argument("--preflight-only", action="store_true", help="only check SSOT readiness and write rtl_blocked.json on semantic gaps")
    ns = ap.parse_args()
    mode = _normalize_run_mode(ns.mode or os.environ.get("ATLAS_RUN_MODE") or "signoff")
    if ns.preflight_only:
        preflight(ns.ip, Path(ns.root).resolve(), mode=mode)
        return 0
    generate(ns.ip, Path(ns.root).resolve(), mode=mode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
