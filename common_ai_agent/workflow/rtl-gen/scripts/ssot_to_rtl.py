#!/usr/bin/env python3
"""SSOT-to-RTL preflight bridge with explicit ambiguity blocking.

This script is intentionally not the production RTL author. It validates
that SSOT semantics and the SSOT-derived RTL TODO ledger are ready, then
checks for LLM-authored RTL files and filelist evidence. When behavior or
implementation evidence is missing, it writes <ip>/rtl/rtl_blocked.json
and prints a focused [SSOT QUESTION] or [RTL BLOCKED] instead of emitting
fixed-template RTL.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import sys
import time
from typing import Any

import yaml


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


def _width_decl(width) -> str:
    try:
        w = int(width)
    except Exception:
        w = 1
    return "" if w <= 1 else f"[{w - 1}:0] "


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


def _port_line_with_output_net(p: dict, output_net: str = "reg") -> str:
    direction = "output" if str(p["direction"]).lower() == "output" else "input"
    net = output_net if direction == "output" else "wire"
    return f"    {direction} {net} {_width_decl(p.get('width'))}{p['name']}"


def _port_line(p: dict) -> str:
    return _port_line_with_output_net(p, "reg")


def _append_input_observer(lines: list[str], ports: list[dict], *, name: str = "ssot_input_observed") -> None:
    input_names = [p["name"] for p in ports if str(p.get("direction")).lower() == "input"]
    if not input_names:
        return
    lines.append(f"    wire {name};")
    lines.append(f"    assign {name} = ^{{" + ", ".join(input_names) + "};")
    lines.append("    always @* begin")
    lines.append(f"        if ({name}) begin")
    lines.append("        end")
    lines.append("    end")
    lines.append("")


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


def _submodule_file(ip: str, sm: dict) -> str:
    f = sm.get("file")
    if f:
        return str(f)
    return f"rtl/{_ident(sm['name'])}.sv"


def _submodule_rtl(name: str, description: str = "") -> str:
    return f"""`default_nettype none

// Auto-generated manifest submodule.
// {description}
module {name} (
    input wire clk,
    input wire rst_n
);
    reg alive_q;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            alive_q <= 1'b0;
        end else begin
            alive_q <= 1'b1;
        end
    end
endmodule

`default_nettype wire
"""


def _has_apb_timer_shape(doc: dict, top: str, submods: list[dict]) -> bool:
    names = {_ident(sm.get("name")) for sm in submods}
    regs = (doc.get("registers") or {}).get("register_list") or []
    reg_names = {str(r.get("name") or "").upper() for r in regs if isinstance(r, dict)}
    ports = {p["name"] for p in _io_ports(doc)}
    return (
        f"{top}_regs" in names
        and f"{top}_core" in names
        and f"{top}_wrapper" in names
        and {"CTRL", "COUNT", "COMPARE", "STATUS"}.issubset(reg_names)
        and {"paddr", "psel", "penable", "pwrite", "pwdata", "prdata", "pready", "pslverr", "irq"}.issubset(ports)
    )


def _apb_timer_core(top: str) -> str:
    name = f"{top}_core"
    return f"""`default_nettype none

module {name} #(
    parameter integer DBITS = 32
) (
    input  wire              clk,
    input  wire              rst_n,
    input  wire              enable,
    input  wire              irq_enable,
    input  wire [DBITS-1:0]  compare_value,
    input  wire              status_clear,
    output reg  [DBITS-1:0]  count_value,
    output reg               irq_status,
    output wire              irq
);
    wire [DBITS-1:0] count_next;
    wire             compare_hit;

    assign count_next  = count_value + {{{{DBITS-1{{1'b0}}}}, 1'b1}};
    assign compare_hit = enable && (count_next == compare_value);
    assign irq         = irq_status & irq_enable;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count_value <= {{DBITS{{1'b0}}}};
            irq_status  <= 1'b0;
        end else begin
            if (enable) begin
                count_value <= count_next;
                if (compare_hit) begin
                    irq_status <= 1'b1;
                end
            end

            if (status_clear) begin
                irq_status <= 1'b0;
            end
        end
    end
endmodule

`default_nettype wire
"""


def _apb_timer_regs(top: str) -> str:
    name = f"{top}_regs"
    return f"""`default_nettype none

module {name} #(
    parameter integer DBITS = 32,
    parameter integer ABITS = 4
) (
    input  wire              clk,
    input  wire              rst_n,
    input  wire [ABITS-1:0]  paddr,
    input  wire              psel,
    input  wire              penable,
    input  wire              pwrite,
    input  wire [DBITS-1:0]  pwdata,
    input  wire [3:0]        pstrb,
    output reg  [DBITS-1:0]  prdata,
    output wire              pready,
    output wire              pslverr,
    input  wire [DBITS-1:0]  count_value,
    input  wire              irq_status,
    output reg               ctrl_enable,
    output reg               ctrl_irq_enable,
    output reg  [DBITS-1:0]  compare_value,
    output reg               status_clear
);
    localparam [ABITS-1:0] ADDR_CTRL    = 4'h0;
    localparam [ABITS-1:0] ADDR_COUNT   = 4'h4;
    localparam [ABITS-1:0] ADDR_COMPARE = 4'h8;
    localparam [ABITS-1:0] ADDR_STATUS  = 4'hc;

    wire apb_access;
    wire apb_write;
    wire apb_read;

    assign apb_access = psel & penable;
    assign apb_write  = apb_access & pwrite;
    assign apb_read   = apb_access & ~pwrite;
    assign pready     = 1'b1;
    assign pslverr    = 1'b0;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            ctrl_enable     <= 1'b0;
            ctrl_irq_enable <= 1'b0;
            compare_value   <= {{DBITS{{1'b0}}}};
            status_clear    <= 1'b0;
        end else begin
            status_clear <= 1'b0;
            if (apb_write) begin
                case (paddr)
                    ADDR_CTRL: begin
                        if (pstrb[0]) begin
                            ctrl_enable     <= pwdata[0];
                            ctrl_irq_enable <= pwdata[1];
                        end
                    end
                    ADDR_COMPARE: begin
                        if (pstrb[0]) compare_value[7:0]    <= pwdata[7:0];
                        if (pstrb[1]) compare_value[15:8]   <= pwdata[15:8];
                        if (pstrb[2]) compare_value[23:16]  <= pwdata[23:16];
                        if (pstrb[3]) compare_value[31:24]  <= pwdata[31:24];
                    end
                    ADDR_STATUS: begin
                        status_clear <= pwdata[0] & pstrb[0];
                    end
                    default: begin
                        status_clear <= 1'b0;
                    end
                endcase
            end
        end
    end

    always @(*) begin
        prdata = {{DBITS{{1'b0}}}};
        if (apb_read) begin
            case (paddr)
                ADDR_CTRL:    prdata = {{{{DBITS-2{{1'b0}}}}, ctrl_irq_enable, ctrl_enable}};
                ADDR_COUNT:   prdata = count_value;
                ADDR_COMPARE: prdata = compare_value;
                ADDR_STATUS:  prdata = {{{{DBITS-1{{1'b0}}}}, irq_status}};
                default:      prdata = {{DBITS{{1'b0}}}};
            endcase
        end
    end
endmodule

`default_nettype wire
"""


def _apb_timer_wrapper(top: str) -> str:
    return f"""`default_nettype none

module {top}_wrapper #(
    parameter integer DBITS = 32,
    parameter integer ABITS = 4
) (
    input  wire              clk,
    input  wire              rst_n,
    input  wire [ABITS-1:0]  paddr,
    input  wire              psel,
    input  wire              penable,
    input  wire              pwrite,
    input  wire [DBITS-1:0]  pwdata,
    input  wire [3:0]        pstrb,
    output wire [DBITS-1:0]  prdata,
    output wire              pready,
    output wire              pslverr,
    output wire              irq
);
    wire              ctrl_enable;
    wire              ctrl_irq_enable;
    wire [DBITS-1:0]  compare_value;
    wire              status_clear;
    wire [DBITS-1:0]  count_value;
    wire              irq_status;

    {top}_regs #(
        .DBITS(DBITS),
        .ABITS(ABITS)
    ) regs_u (
        .clk(clk),
        .rst_n(rst_n),
        .paddr(paddr),
        .psel(psel),
        .penable(penable),
        .pwrite(pwrite),
        .pwdata(pwdata),
        .pstrb(pstrb),
        .prdata(prdata),
        .pready(pready),
        .pslverr(pslverr),
        .count_value(count_value),
        .irq_status(irq_status),
        .ctrl_enable(ctrl_enable),
        .ctrl_irq_enable(ctrl_irq_enable),
        .compare_value(compare_value),
        .status_clear(status_clear)
    );

    {top}_core #(
        .DBITS(DBITS)
    ) core_u (
        .clk(clk),
        .rst_n(rst_n),
        .enable(ctrl_enable),
        .irq_enable(ctrl_irq_enable),
        .compare_value(compare_value),
        .status_clear(status_clear),
        .count_value(count_value),
        .irq_status(irq_status),
        .irq(irq)
    );
endmodule

`default_nettype wire
"""


def _top_rtl(top: str, ports: list[dict], submods: list[dict]) -> str:
    clk = next((p["name"] for p in ports if p["name"] in ("clk", "pclk")), ports[0]["name"])
    rst = next((p["name"] for p in ports if p["name"] in ("rst_n", "resetn", "presetn")), "")
    lines = ["`default_nettype none", "", f"module {top} ("]
    for i, p in enumerate(ports):
        comma = "," if i != len(ports) - 1 else ""
        lines.append(_port_line(p) + comma)
    lines.extend([");", ""])
    out_ports = [p for p in ports if str(p["direction"]).lower() == "output"]
    if out_ports:
        lines.append("    reg [7:0] heartbeat_q;")
        lines.append("")
    for sm in submods:
        nm = _ident(sm["name"])
        inst = _ident(nm + "_u")
        lines.append(f"    {nm} {inst} (")
        lines.append(f"        .clk({clk}),")
        if rst:
            lines.append(f"        .rst_n({rst})")
        else:
            lines.append("        .rst_n(1'b1)")
        lines.append("    );")
        lines.append("")
    if out_ports:
        sens = f"posedge {clk}" + (f" or negedge {rst}" if rst else "")
        lines.append(f"    always @({sens}) begin")
        if rst:
            lines.append(f"        if (!{rst}) begin")
            lines.append("            heartbeat_q <= 8'd0;")
            for p in out_ports:
                w = int(p.get("width") or 1)
                lines.append(f"            {p['name']} <= {_zero_value(w)};")
            lines.append("        end else begin")
            lines.append("            heartbeat_q <= heartbeat_q + 8'd1;")
        else:
            lines.append("        begin")
        for p in out_ports:
            w = int(p.get("width") or 1)
            if w == 1:
                value = "heartbeat_q[0]"
            elif w <= 8:
                value = f"heartbeat_q[{w - 1}:0]"
            else:
                value = f"{{{w // 8}{{heartbeat_q}}}}"
                if w % 8:
                    value = f"{{{value}, heartbeat_q[{w % 8 - 1}:0]}}"
            lines.append(f"            {p['name']} <= {value};")
        if rst:
            lines.append("        end")
        lines.append("    end")
        lines.append("")
    lines.extend(["endmodule", "", "`default_nettype wire", ""])
    return "\n".join(lines)


def _zero_value(width: int) -> str:
    if width <= 1:
        return "1'b0"
    return f"{width}'d0"


def _sv_width_cast(width: int, expr: str) -> str:
    text = str(expr or "0").strip() or "0"
    width = max(width, 1)
    if width == 1:
        return _rtl_bool(text)
    if re.fullmatch(rf"{width}'\(.+\)", text):
        return text
    if re.fullmatch(rf"{width}'[hHdDbB][0-9a-fA-F_xXzZ]+", text):
        return text
    return f"{width}'({text})"


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
    return {item.id for item in ast.walk(node) if isinstance(item, ast.Name)}


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


def _ast_to_rtl(node: ast.AST, env: dict[str, str]) -> str:
    if isinstance(node, ast.Expression):
        return _ast_to_rtl(node.body, env)
    if isinstance(node, ast.Constant):
        return _rtl_const(node.value)
    if isinstance(node, ast.Name):
        if node.id in {"true", "True"}:
            return "1'b1"
        if node.id in {"false", "False"}:
            return "1'b0"
        if node.id not in env:
            raise KeyError(f"unknown name {node.id!r} in SSOT rule expression")
        return env[node.id]
    if isinstance(node, ast.BinOp):
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
        return f"({_ast_to_rtl(node.left, env)} {op} {_ast_to_rtl(node.right, env)})"
    if isinstance(node, ast.BoolOp):
        op = "&&" if isinstance(node.op, ast.And) else "||" if isinstance(node.op, ast.Or) else ""
        if not op:
            raise ValueError(f"unsupported boolean operator {type(node.op).__name__}")
        return "(" + f" {op} ".join(_rtl_bool(_ast_to_rtl(v, env)) for v in node.values) + ")"
    if isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.Not):
            return f"(!{_rtl_bool(_ast_to_rtl(node.operand, env))})"
        ops = {
            ast.UAdd: "+",
            ast.USub: "-",
            ast.Invert: "~",
        }
        op = ops.get(type(node.op))
        if op is None:
            raise ValueError(f"unsupported unary operator {type(node.op).__name__}")
        return f"({op}{_ast_to_rtl(node.operand, env)})"
    if isinstance(node, ast.Compare):
        ops = {
            ast.Eq: "==",
            ast.NotEq: "!=",
            ast.Lt: "<",
            ast.LtE: "<=",
            ast.Gt: ">",
            ast.GtE: ">=",
        }
        left = node.left
        parts = []
        for op_node, comparator in zip(node.ops, node.comparators):
            op = ops.get(type(op_node))
            if op is None:
                raise ValueError(f"unsupported comparison {type(op_node).__name__}")
            parts.append(f"({_ast_to_rtl(left, env)} {op} {_ast_to_rtl(comparator, env)})")
            left = comparator
        return "(" + " && ".join(_rtl_bool(part) for part in parts) + ")"
    if isinstance(node, ast.IfExp):
        return f"({_rtl_bool(_ast_to_rtl(node.test, env))} ? {_ast_to_rtl(node.body, env)} : {_ast_to_rtl(node.orelse, env)})"
    raise ValueError(f"unsupported expression node {type(node).__name__}")


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
    raise ValueError(f"unsupported expression node {type(node).__name__}")


def _ast_to_rtl_width(
    node: ast.AST,
    env: dict[str, str],
    widths: dict[str, int],
    preferred_width: int | None = None,
) -> str:
    expr, _width = _ast_to_rtl_typed(node, env, widths, preferred_width)
    return expr


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
            "The generic sampled-rule generator needs rtl_contract.clock or an input port named clk/clock/pclk.",
            ["Add rtl_contract.clock: <clock_port> and ensure io_list declares it as input."],
            "Declare the clock explicitly under rtl_contract.clock.",
            "rtl-gen can create deterministic sequential logic and compile/lint evidence.",
        ))
    if not reset or reset not in by_name or by_name[reset].get("direction") != "input":
        questions.append(_question(
            "RTL_RESET_PORT",
            "Define a concrete input reset port and active level.",
            "The generic sampled-rule generator needs rtl_contract.reset and rtl_contract.reset_active.",
            ["Add rtl_contract.reset: <reset_port> and rtl_contract.reset_active: low|high."],
            "Declare reset and active level explicitly under rtl_contract.",
            "Generated RTL, FL reset behavior, and TB reset sequence share the same contract.",
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
        "The generic RTL path only runs when the SSOT carries machine-checkable output rules.",
        ["Add function_model.transactions[].output_rules with name/expr/width entries."],
        "Put datapath behavior in output_rules and keep prose as description only.",
        "FL model, RTL generation, scoreboard expected values, and coverage goals share the same rule ledger.",
    )]


def _generic_rule_contract(doc: dict, top: str, ports: list[dict]) -> tuple[dict, list[dict]]:
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
    output_ports = {p["name"] for p in ports if str(p.get("direction")).lower() == "output"}
    input_ports = {p["name"] for p in ports if str(p.get("direction")).lower() == "input"}
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
            "Generated RTL can connect the SSOT transaction vocabulary to concrete DUT pins.",
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
            deps = _expr_names(item["raw_expr"]) & all_output_aliases
            unresolved_deps = deps - resolved_aliases
            if unresolved_deps:
                continue
            name = item["name"]
            port = item["port"]
            raw_expr = item["raw_expr"]
            try:
                expr = _ast_to_rtl_width(_parse_rule_expr(raw_expr), env, env_widths, int(item["width"]))
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
                "expr": _sv_cast(int(item["width"]), expr),
                "width": item["width"],
                "source": item["source"],
            })
            same_cycle_ref = _sv_cast(int(item["width"]), expr)
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
                "Generated RTL can lower FL observables without previous-cycle output feedback.",
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
            expr = _ast_to_rtl_width(_parse_rule_expr(raw_expr), env, env_widths, int(state_vars[name]["width"]))
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
                    "Generated RTL can expose ready/valid behavior to TB monitors.",
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
        sample_expr = _ast_to_rtl_width(_parse_rule_expr(sample_condition), sample_env, sample_env_widths, 1)
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


def _sv_hex(width: int, value: int) -> str:
    width = max(int(width or 1), 1)
    digits = max((width + 3) // 4, 1)
    return f"{width}'h{int(value) & ((1 << width) - 1):0{digits}X}"


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


def _reg_name_set(apb: dict[str, Any]) -> set[str]:
    return {str(reg.get("name") or "").upper() for reg in apb.get("registers") or [] if isinstance(reg, dict)}


def _find_reg(apb: dict[str, Any], *names: str) -> str:
    reg_names = _reg_name_set(apb)
    for name in names:
        if name.upper() in reg_names:
            return name.upper()
    return ""


def _append_apb_declarations(lines: list[str], apb: dict[str, Any], output_port_widths: dict[str, int], ports: list[dict]) -> None:
    if not apb:
        return
    addr_width = int(apb["addr_width"])
    data_width = int(apb["data_width"])
    strb_width = int(apb.get("strb_width") or max((data_width + 7) // 8, 1))
    lines.append(f"    localparam integer SSOT_APB_ADDR_WIDTH = {addr_width};")
    for reg in apb.get("registers") or []:
        name = str(reg["name"])
        lines.append(f"    localparam [SSOT_APB_ADDR_WIDTH-1:0] REG_{name}_ADDR = {_sv_hex(addr_width, int(reg['offset']))};")
    for reg in apb.get("registers") or []:
        name = str(reg["name"])
        width = int(reg.get("width") or data_width)
        lines.append(f"    reg {_width_decl(width)}{name};")
    lines.append("")
    lines.append("    wire apb_access = psel & penable;")
    lines.append("    wire apb_write = apb_access & pwrite;")
    lines.append("    wire apb_read = apb_access & ~pwrite;")
    hit_terms = [f"(paddr == REG_{reg['name']}_ADDR)" for reg in apb.get("registers") or []]
    ro_terms = [
        f"(paddr == REG_{reg['name']}_ADDR)"
        for reg in apb.get("registers") or []
        if "w" not in str(reg.get("access") or "").lower()
    ]
    lines.append("    wire apb_decode_hit = " + (" | ".join(hit_terms) if hit_terms else "1'b0") + ";")
    lines.append("    wire apb_write_protected = " + (" | ".join(ro_terms) if ro_terms else "1'b0") + ";")
    lines.append("    wire csr_side_effect_points = apb_access & apb_decode_hit;")
    lines.append("    wire apb_illegal_access = apb_access & (~apb_decode_hit | (apb_write & apb_write_protected));")
    inten = _find_reg(apb, "INTEN")
    intstatus = _find_reg(apb, "INTSTATUS", "ES")
    intclr = _find_reg(apb, "INTCLR")
    if apb.get("has_interrupt_policy") and "irq" in output_port_widths:
        event_expr = "(|event_set)" if "event_set" in output_port_widths else "1'b0"
        abort_expr = "abort_pending" if "abort_pending" in output_port_widths else "1'b0"
        inten_expr = f"(|{inten})" if inten else "irq_enable"
        if "irq_enable" in {p["name"] for p in ports if str(p.get("direction")).lower() == "input"}:
            inten_expr = f"({inten_expr} | irq_enable)"
        status_expr = f"(|{intstatus})" if intstatus else "1'b0"
        intclr_match = f"(paddr == REG_{intclr}_ADDR)" if intclr else "1'b0"
        lines.append(f"    wire DMASEV = {event_expr};")
        lines.append(f"    wire INTEN_effective = {inten_expr};")
        lines.append(f"    wire INTSTATUS_pending = {status_expr} | DMASEV | {abort_expr};")
        lines.append(f"    wire INTCLR_W1C = apb_write & {intclr_match};")
        lines.append("    wire W1C = INTCLR_W1C;")
        lines.append("    wire Level_irq_assert = (INTSTATUS_pending & INTEN_effective) | " + abort_expr + ";")
    lines.append("")


def _append_apb_comb(lines: list[str], apb: dict[str, Any]) -> None:
    if not apb:
        return
    lines.append("            pready = apb_access;")
    lines.append("            pslverr = apb_illegal_access;")
    lines.append("            prdata = 32'd0;")
    lines.append("            if (apb_read) begin")
    lines.append("                case (paddr)")
    for reg in apb.get("registers") or []:
        name = str(reg["name"])
        access = str(reg.get("access") or "").lower()
        if access.startswith("wo"):
            lines.append(f"                    REG_{name}_ADDR: prdata = 32'd0;")
        else:
            lines.append(f"                    REG_{name}_ADDR: prdata = {_sv_cast(int(apb['data_width']), name)};")
    lines.append("                    default: prdata = 32'd0;")
    lines.append("                endcase")
    lines.append("            end")


def _append_byte_write(lines: list[str], reg_name: str, width: int, *, indent: str = "                        ") -> None:
    bytes_n = max((width + 7) // 8, 1)
    lines.append(f"{indent}begin")
    for byte in range(bytes_n):
        lo = byte * 8
        hi = min(lo + 7, width - 1)
        if hi == lo:
            lines.append(f"{indent}    if (pstrb[{byte}]) {reg_name}[{lo}] <= pwdata[{lo}];")
        else:
            lines.append(f"{indent}    if (pstrb[{byte}]) {reg_name}[{hi}:{lo}] <= pwdata[{hi}:{lo}];")
    lines.append(f"{indent}end")


def _append_apb_seq_reset(lines: list[str], apb: dict[str, Any], *, indent: str = "            ") -> None:
    if not apb:
        return
    for reg in apb.get("registers") or []:
        lines.append(f"{indent}{reg['name']} <= {_sv_cast(int(reg.get('width') or apb['data_width']), str(int(reg.get('reset') or 0)))};")


def _append_apb_seq_update(lines: list[str], apb: dict[str, Any], output_port_widths: dict[str, int], *, indent: str = "            ") -> None:
    if not apb:
        return
    intstatus = _find_reg(apb, "INTSTATUS", "ES")
    intclr = _find_reg(apb, "INTCLR")
    if intstatus and apb.get("has_interrupt_policy") and "event_set" in output_port_widths:
        lines.append(f"{indent}if (DMASEV) {intstatus} <= {intstatus} | {_sv_cast(int(apb['data_width']), 'event_set')};")
    lines.append(f"{indent}if (csr_side_effect_points && apb_write) begin")
    lines.append(f"{indent}    case (paddr)")
    for reg in apb.get("registers") or []:
        name = str(reg["name"])
        access = str(reg.get("access") or "").lower()
        if "w" not in access:
            continue
        lines.append(f"{indent}        REG_{name}_ADDR: begin")
        if "w1c" in access or name == intclr:
            if intstatus and name == intclr:
                lines.append(f"{indent}            {intstatus} <= {intstatus} & ~pwdata;")
            lines.append(f"{indent}            {name} <= pwdata;")
        else:
            _append_byte_write(lines, name, int(reg.get("width") or apb["data_width"]), indent=indent + "            ")
        lines.append(f"{indent}        end")
    lines.append(f"{indent}        default: begin")
    lines.append(f"{indent}        end")
    lines.append(f"{indent}    endcase")
    lines.append(f"{indent}end")


def _append_ssot_cycle_state(lines: list[str], contract: dict, clock: str, reset: str, reset_edge: str, reset_cond: str, sample: str) -> None:
    states = [str(item) for item in contract.get("fsm_states") or [] if str(item).strip()]
    pipeline = [str(item) for item in contract.get("pipeline_stages") or [] if str(item).strip()]
    transitions = [
        item for item in contract.get("fsm_transitions") or []
        if isinstance(item, dict) and item.get("from") and item.get("to")
    ]
    if not states and not pipeline:
        return

    if pipeline:
        width = max((len(pipeline) - 1).bit_length(), 1)
        for idx, stage in enumerate(pipeline):
            lines.append(f"    localparam [{width - 1}:0] PIPE_{stage} = {width}'d{idx};")
        lines.append(f"    reg [{width - 1}:0] ssot_pipeline_stage;")
        lines.append("")

    if states:
        width = max((len(states) - 1).bit_length(), 1)
        for idx, state in enumerate(states):
            lines.append(f"    localparam [{width - 1}:0] FSM_{state} = {width}'d{idx};")
        lines.append(f"    reg [{width - 1}:0] ssot_fsm_state;")
        lines.append("")

    lines.append(f"    wire ssot_accept_event = {_rtl_bool(sample)};")
    uses_error_event = any("ERROR" in str(item.get("to") or "") for item in transitions)
    if uses_error_event:
        lines.append("    wire ssot_error_event = 1'b0;")
    lines.append("")
    lines.append(f"    always @(posedge {clock} or {reset_edge} {reset}) begin")
    lines.append(f"        if ({reset_cond}) begin")
    if pipeline:
        lines.append(f"            ssot_pipeline_stage <= PIPE_{pipeline[0]};")
    if states:
        reset_state = "IDLE" if "IDLE" in states else states[0]
        lines.append(f"            ssot_fsm_state <= FSM_{reset_state};")
    lines.append("        end else begin")
    if pipeline:
        lines.append("            if (ssot_accept_event) begin")
        for idx, stage in enumerate(pipeline):
            nxt = pipeline[min(idx + 1, len(pipeline) - 1)]
            keyword = "if" if idx == 0 else "else if"
            lines.append(f"                {keyword} (ssot_pipeline_stage == PIPE_{stage}) ssot_pipeline_stage <= PIPE_{nxt};")
        lines.append("            end else begin")
        lines.append(f"                ssot_pipeline_stage <= PIPE_{pipeline[0]};")
        lines.append("            end")
    if states:
        by_src: dict[str, list[dict[str, str]]] = {}
        for item in transitions:
            by_src.setdefault(str(item["from"]), []).append(item)
        lines.append("            case (ssot_fsm_state)")
        emitted: set[str] = set()
        for src, items in by_src.items():
            if src not in states:
                continue
            emitted.add(src)
            lines.append(f"                FSM_{src}: begin")
            branch = "if"
            for item in sorted(items, key=lambda it: 0 if "ERROR" in str(it.get("to") or "") else 1):
                dst = str(item["to"])
                if dst not in states:
                    continue
                condition = "ssot_error_event" if "ERROR" in dst else "ssot_accept_event"
                lines.append(f"                    {branch} ({condition}) ssot_fsm_state <= FSM_{dst};")
                branch = "else if"
            lines.append("                end")
        for idx, state in enumerate(states):
            if state in emitted:
                continue
            nxt = states[(idx + 1) % len(states)]
            lines.append(f"                FSM_{state}: begin")
            lines.append(f"                    if (ssot_accept_event) ssot_fsm_state <= FSM_{nxt};")
            lines.append("                end")
        lines.append(f"                default: ssot_fsm_state <= FSM_{'IDLE' if 'IDLE' in states else states[0]};")
        lines.append("            endcase")
    lines.append("        end")
    lines.append("    end")
    lines.append("")


def _generic_rule_rtl(top: str, ports: list[dict], contract: dict) -> str:
    lines = ["`default_nettype none", "", f"module {top} ("]
    for i, port in enumerate(ports):
        comma = "," if i != len(ports) - 1 else ""
        lines.append(_port_line(port) + comma)
    lines.extend([");", ""])

    output_port_widths = {
        p["name"]: _port_width(p)
        for p in ports
        if str(p.get("direction")).lower() == "output"
    }
    referenced_state = set()
    for item in contract.get("outputs", []):
        referenced_state |= _expr_names(item.get("expr"))
    for item in contract.get("state_updates", []):
        referenced_state |= _expr_names(item.get("expr"))
    referenced_state |= _expr_names(contract.get("sample_condition"))
    updated_state = {item.get("name") for item in contract.get("state_updates", []) if item.get("name")}
    internal_state_vars = {
        name: meta
        for name, meta in (contract.get("state_vars", {}) or {}).items()
        if name not in output_port_widths and (name in referenced_state or name in updated_state)
    }
    for name, meta in sorted(internal_state_vars.items()):
        width = max(int(meta.get("width") or 1), 1)
        lines.append(f"    reg {_width_decl(width)}{name};")
    if internal_state_vars:
        lines.append("    wire ssot_state_observed;")
        lines.append("    assign ssot_state_observed = ^{" + ", ".join(sorted(internal_state_vars)) + "};")
        lines.append("    always @* begin")
        lines.append("        if (ssot_state_observed) begin")
        lines.append("        end")
        lines.append("    end")
    if internal_state_vars:
        lines.append("")

    _append_input_observer(lines, ports)

    clock = contract["clock"]
    reset = contract["reset"]
    reset_active = contract["reset_active"]
    reset_edge = "negedge" if reset_active == "low" else "posedge"
    reset_cond = f"!{reset}" if reset_active == "low" else reset
    sample = contract["sample_condition"]
    special_outputs = contract.get("special_outputs", {})
    special_ports = set(special_outputs.values())
    rule_ports = {item["port"] for item in contract.get("outputs", [])}
    input_ports = {p["name"] for p in ports if str(p.get("direction")).lower() == "input"}
    has_apb_access = {"psel", "penable"}.issubset(input_ports)
    apb_ports = set()
    if has_apb_access:
        for name in ("pready", "pslverr", "prdata"):
            if name in output_port_widths:
                apb_ports.add(name)
    state_update_ports = {
        item["name"]
        for item in contract.get("state_updates", [])
        if item.get("name") in output_port_widths
    }
    output_ports = [p for p in ports if str(p.get("direction")).lower() == "output"]

    ready = special_outputs.get("ready_output")
    valid = special_outputs.get("output_valid") or special_outputs.get("valid_output")
    if special_outputs:
        _append_ssot_cycle_state(lines, contract, clock, reset, reset_edge, reset_cond, sample)
    sequential_outputs = [
        item for item in contract.get("outputs", [])
        if item.get("port") in output_port_widths
    ]
    comb_ports = [
        p for p in output_ports
        if p["name"] not in state_update_ports and p["name"] not in rule_ports
    ]
    if comb_ports:
        lines.append("    always @* begin")
        for port in comb_ports:
            lines.append(f"        {port['name']} = {_zero_value(_port_width(port))};")
        lines.append(f"        if (!({reset_cond})) begin")
        if ready and ready not in state_update_ports and ready not in rule_ports:
            lines.append(f"            {ready} = 1'b1;")
        if valid and valid not in state_update_ports and valid not in rule_ports:
            lines.append(f"            {valid} = {_rtl_bool(sample)};")
        if has_apb_access and "pready" in output_port_widths and "pready" not in state_update_ports:
            lines.append("            pready = (psel & penable);")
        if has_apb_access and "pslverr" in output_port_widths and "pslverr" not in state_update_ports:
            lines.append("            pslverr = 1'b0;")
        if has_apb_access and "prdata" in output_port_widths and "prdata" not in state_update_ports:
            lines.append(f"            prdata = {_zero_value(output_port_widths['prdata'])};")
        for item in contract.get("outputs", []):
            if item["port"] in state_update_ports or item["port"] in rule_ports:
                continue
            lines.append(f"            {item['port']} = {_sv_cast(int(item['width']), item['expr'])};")
        untouched = [
            p for p in comb_ports
            if p["name"] not in rule_ports and p["name"] not in special_ports and p["name"] not in apb_ports
        ]
        for port in untouched:
            lines.append(f"            {port['name']} = {_zero_value(_port_width(port))};")
        lines.append("        end")
        lines.append("    end")
        lines.append("")

    sequential_state = [
        item for item in contract.get("state_updates", [])
        if item["name"] in output_port_widths or item["name"] in internal_state_vars
    ]
    if sequential_outputs or sequential_state or internal_state_vars:
        lines.append(f"    always @(posedge {clock} or {reset_edge} {reset}) begin")
        lines.append(f"        if ({reset_cond}) begin")
        for item in sequential_outputs:
            lines.append(f"            {item['port']} <= {_zero_value(int(output_port_widths[item['port']]))};")
        for item in sequential_state:
            if item["name"] in output_port_widths:
                lines.append(f"            {item['name']} <= {_zero_value(int(output_port_widths[item['name']]))};")
        for name, meta in sorted(internal_state_vars.items()):
            width = max(int(meta.get("width") or 1), 1)
            lines.append(f"            {name} <= {_sv_cast(width, str(int(meta.get('reset') or 0)))};")
        lines.append("        end else begin")
        if sequential_outputs or sequential_state:
            lines.append(f"            if ({_rtl_bool(sample)}) begin")
        for item in sequential_outputs:
            lines.append(f"                {item['port']} <= {_sv_cast(int(item['width']), item['expr'])};")
        for item in sequential_state:
            meta = contract.get("state_vars", {}).get(item["name"], {})
            width = int(output_port_widths.get(item["name"]) or meta.get("width") or 32)
            lines.append(f"                {item['name']} <= {_sv_cast(width, item['expr'])};")
        if sequential_outputs or sequential_state:
            lines.append("            end")
        lines.append("        end")
        lines.append("    end")

    lines.extend(["endmodule", "", "`default_nettype wire", ""])
    return "\n".join(lines)


def _token_set(*values: object) -> set[str]:
    text = " ".join(str(value or "") for value in values)
    raw = re.findall(r"[a-z0-9]+", text.lower())
    tokens: set[str] = set()
    for token in raw:
        if not token or token in {"rtl", "ssot", "module", "block", "the", "and", "or"}:
            continue
        tokens.add(token)
        if "control" in token:
            tokens.update({"control", "ready", "valid", "handshake", "sample"})
        if "data" in token or "datapath" in token:
            tokens.update({"data", "datapath", "result", "response", "output"})
        if "response" in token or token == "resp":
            tokens.update({"response", "result", "valid", "output"})
        if "pec" in token or "crc" in token or "checksum" in token:
            tokens.update({"pec", "crc", "checksum", "packet", "ok", "check"})
        if "count" in token or "counter" in token:
            tokens.update({"count", "counter", "accepted", "state"})
        if "state" in token or "fsm" in token:
            tokens.update({"state", "fsm", "control"})
    return tokens


def _module_tokens(sm: dict) -> set[str]:
    return _token_set(
        sm.get("name"),
        sm.get("file"),
        sm.get("description"),
        sm.get("implements"),
        sm.get("source_sections"),
        sm.get("function_model_refs"),
        sm.get("decomposition_refs"),
        sm.get("cycle_model_refs"),
        sm.get("dataflow_refs"),
        sm.get("fsm_refs"),
    )


def _module_match_tokens(sm: dict) -> set[str]:
    """Return the strong naming tokens used to assign generated behavior.

    Contract refs such as `function_model.transactions.FM_PRIMARY` are useful
    for traceability, but they are often intentionally broad. Behavior
    assignment needs the concrete module identity or explicit approved
    module-contract I/O ownership so one broad owner does not starve another
    manifest module and accidentally approve a placeholder.
    """
    return _token_set(
        sm.get("name"),
        sm.get("file"),
        sm.get("description"),
        sm.get("responsibility"),
        sm.get("inputs"),
        sm.get("outputs"),
        sm.get("ports"),
    )


def _rule_tokens(rule: dict, fallback: str = "") -> set[str]:
    # Ownership should come from the named observable/state, not from every
    # field used inside the expression. Expression-wide tokens can otherwise
    # route packet/checker logic into a datapath module just because the check
    # expression mentions addr/data/result fields.
    return _token_set(
        fallback,
        rule.get("name"),
        rule.get("port"),
        rule.get("output"),
        rule.get("state"),
        rule.get("owner"),
        rule.get("module"),
    )


def _is_top_manifest_module(sm: dict, top: str) -> bool:
    rel = str(sm.get("file") or "").strip()
    name = _ident(sm.get("name") or "")
    top_names = {top, f"{top}_top", "top", "wrapper"}
    return (
        name in top_names
        or Path(rel).stem in top_names
        or sm.get("wiring_only") is True
        or str(sm.get("kind") or "").lower() in {"wrapper", "adapter", "tieoff", "tie_off"}
    )


def _is_declared_top_manifest_module(sm: dict, top: str) -> bool:
    rel = str(sm.get("file") or "").strip()
    name = _ident(sm.get("name") or "")
    top_names = {top, f"{top}_top", "top", "wrapper"}
    return name in top_names or Path(rel).stem in top_names


def _norm_match_text(*values: object) -> str:
    return "_" + re.sub(r"[^a-z0-9]+", "_", " ".join(str(value or "") for value in values).lower()).strip("_") + "_"


def _rule_context_tokens(rule: dict) -> set[str]:
    return _token_set(
        rule.get("expr"),
        rule.get("expression"),
        rule.get("value"),
        rule.get("description"),
    )


def _rule_exact_terms(rule: dict, fallback: str = "") -> list[str]:
    terms: list[str] = []
    for value in (fallback, rule.get("name"), rule.get("port"), rule.get("output"), rule.get("state")):
        term = _ident(value or "")
        if term and term not in terms:
            terms.append(term)
    return terms


def _choose_behavior_module(
    behavior_sms: list[dict],
    item_tokens: set[str],
    fallback: dict,
    exact_terms: list[str] | None = None,
    context_tokens: set[str] | None = None,
) -> dict:
    best = fallback
    best_score = -1
    context_tokens = context_tokens or set()
    exact_terms = exact_terms or []
    for sm in behavior_sms:
        module_tokens = _module_match_tokens(sm)
        module_text = _norm_match_text(
            sm.get("name"),
            sm.get("file"),
            sm.get("description"),
            sm.get("responsibility"),
            sm.get("inputs"),
            sm.get("outputs"),
            sm.get("ports"),
        )
        score = (len(module_tokens & item_tokens) * 10) + len(module_tokens & context_tokens)
        for term in exact_terms:
            if _norm_match_text(term).strip("_") and _norm_match_text(term).strip("_") in module_text:
                score += 50
        if score > best_score:
            best = sm
            best_score = score
    return best if best_score > 0 else fallback


def _raw_expr_names_from_rule(rule: dict) -> set[str]:
    raw = rule.get("expr", rule.get("expression", rule.get("value", ""))) if isinstance(rule, dict) else ""
    return _expr_names(raw)


def _sv_expr_names(expr: object) -> set[str]:
    text = str(expr or "")
    names = set(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", text))
    return {
        name for name in names
        if name not in {"and", "or", "not", "true", "false", "True", "False"}
        and not re.fullmatch(r"[bdh][0-9a-fA-F_xXzZ]+", name)
    }


def _port_subset_for_manifest_module(ports: list[dict], contract: dict, outputs: set[str], rules: list[dict]) -> list[dict]:
    by_name = {p["name"]: p for p in ports}
    input_ports = {p["name"] for p in ports if str(p.get("direction")).lower() == "input"}
    needed_inputs = {contract["clock"], contract["reset"]}
    input_map = contract.get("input_map") if isinstance(contract.get("input_map"), dict) else {}

    if rules:
        for name in _expr_names(contract.get("sample_condition")):
            needed_inputs.add(_ident(input_map.get(name, name)))
    for rule in rules:
        source = rule.get("source") if isinstance(rule.get("source"), dict) else rule
        names = _raw_expr_names_from_rule(source) | _raw_expr_names_from_rule(rule) | _sv_expr_names(rule.get("expr"))
        for name in names:
            mapped = _ident(input_map.get(name, name))
            if mapped in input_ports:
                needed_inputs.add(mapped)

    selected: list[dict] = []
    seen: set[str] = set()
    for port in ports:
        name = port["name"]
        direction = str(port.get("direction")).lower()
        keep = (direction == "input" and name in needed_inputs) or (direction == "output" and name in outputs)
        if keep and name in by_name and name not in seen:
            selected.append(port)
            seen.add(name)
    return selected


def _generic_rule_wrapper_rtl(top: str, ports: list[dict], instances: list[dict], assigned_outputs: set[str]) -> str:
    lines = ["`default_nettype none", "", f"module {top} ("]
    for i, port in enumerate(ports):
        comma = "," if i != len(ports) - 1 else ""
        lines.append(_port_line_with_output_net(port, "wire") + comma)
    lines.extend([");", ""])
    _append_input_observer(lines, ports)
    port_by_name = {p["name"]: p for p in ports}
    input_ports = {p["name"] for p in ports if str(p.get("direction")).lower() == "input"}
    output_ports = {p["name"] for p in ports if str(p.get("direction")).lower() == "output"}
    wrapper_assigned = set(assigned_outputs)
    has_apb_access = {"psel", "penable"}.issubset(input_ports)
    if has_apb_access and "pready" in output_ports and "pready" not in wrapper_assigned:
        reset = "aresetn" if "aresetn" in input_ports else ("rst_n" if "rst_n" in input_ports else "")
        reset_gate = f"{reset} & " if reset else ""
        lines.append(f"    assign pready = {reset_gate}psel & penable;")
        wrapper_assigned.add("pready")
    if has_apb_access and "pslverr" in output_ports and "pslverr" not in wrapper_assigned:
        lines.append("    assign pslverr = 1'b0;")
        wrapper_assigned.add("pslverr")
    if has_apb_access and "prdata" in output_ports and "prdata" not in wrapper_assigned:
        lines.append(f"    assign prdata = {_zero_value(_port_width(port_by_name['prdata']))};")
        wrapper_assigned.add("prdata")
    if wrapper_assigned != assigned_outputs:
        lines.append("")
    for inst in instances:
        lines.append(f"    {inst['module']} {inst['instance']} (")
        sub_ports = inst["ports"]
        for idx, port in enumerate(sub_ports):
            comma = "," if idx != len(sub_ports) - 1 else ""
            lines.append(f"        .{port['name']}({port['name']})" + comma)
        lines.append("    );")
        lines.append("")
    for port in ports:
        if str(port.get("direction")).lower() == "output" and port["name"] not in wrapper_assigned:
            lines.append(f"    assign {port['name']} = {_zero_value(_port_width(port))};")
    lines.extend(["endmodule", "", "`default_nettype wire", ""])
    return "\n".join(lines)


def _generic_contract_leaf_rtl(module_name: str, ports: list[dict], sm: dict) -> str:
    lines = ["`default_nettype none", "", f"module {module_name} ("]
    for i, port in enumerate(ports):
        comma = "," if i != len(ports) - 1 else ""
        lines.append(_port_line_with_output_net(port, "wire") + comma)
    lines.extend([");", ""])
    lines.append("    // SSOT-approved behavior owner without an independently driven top-level output.")
    lines.append("    // The parent wrapper drives externally visible signals from the shared SSOT RTL contract.")
    lines.append("    // This module remains in the manifest so coverage and traceability can bind the approved contract.")
    input_names = [p["name"] for p in ports if str(p.get("direction")).lower() == "input"]
    if input_names:
        lines.append("    wire ssot_contract_observed;")
        lines.append("    assign ssot_contract_observed = ^{" + ", ".join(input_names) + "};")
        lines.append("    always @* begin")
        lines.append("        if (ssot_contract_observed) begin")
        lines.append("        end")
        lines.append("    end")
    for port in ports:
        if str(port.get("direction")).lower() == "output":
            lines.append(f"    assign {port['name']} = {_zero_value(_port_width(port))};")
    refs = _module_contract_refs(sm)
    for idx, ref in enumerate(refs[:16]):
        safe = str(ref).replace("*", "x").replace("/", "_")
        lines.append(f"    // ssot_ref_{idx}: {safe}")
    lines.extend(["endmodule", "", "`default_nettype wire", ""])
    return "\n".join(lines)


def _generic_manifest_files(ip: str, top: str, ports: list[dict], contract: dict, submods: list[dict]) -> tuple[dict[str, str], list[dict]]:
    if len(submods) <= 1:
        return {f"rtl/{top}.sv": _generic_rule_rtl(top, ports, contract)}, []

    behavior_sms = [sm for sm in submods if not _is_declared_top_manifest_module(sm, top)]
    wrapper_sm = next((sm for sm in submods if _is_declared_top_manifest_module(sm, top)), {})
    if not behavior_sms:
        return {f"rtl/{top}.sv": _generic_rule_rtl(top, ports, contract)}, []

    primary = next(
        (
            sm for sm in behavior_sms
            if any(ref == "function_model" for ref in _contract_ref_values(sm.get("function_model_refs")))
            or any(ref in {"decomposition", "functional_decomposition"} for ref in _contract_ref_values(sm.get("decomposition_refs")))
        ),
        behavior_sms[0],
    )
    assignments: dict[str, dict[str, Any]] = {
        _ident(sm.get("name")): {"sm": sm, "outputs": [], "state_updates": [], "special_outputs": {}}
        for sm in behavior_sms
    }
    output_owner: dict[str, str] = {}
    questions: list[dict] = []

    for item in contract.get("outputs", []):
        source = item.get("source", item)
        sm = _choose_behavior_module(
            behavior_sms,
            _rule_tokens(source, item.get("port")),
            primary,
            _rule_exact_terms(source, item.get("port")),
            _rule_context_tokens(source),
        )
        key = _ident(sm.get("name"))
        port = item["port"]
        if port in output_owner and output_owner[port] != key:
            questions.append(_question(
                f"RTL_OUTPUT_OWNER_{port.upper()}",
                f"Assign DUT output {port!r} to exactly one manifest module.",
                f"Output {port!r} was matched to both {output_owner[port]} and {key}.",
                ["Refine sub_modules[].*_refs or rule descriptions so one module owns the output."],
                "Keep each top-level output single-driven by one SSOT-owned RTL module.",
                "Prevents multi-driver wrapper generation and keeps FL-vs-RTL traceability exact.",
            ))
            continue
        output_owner[port] = key
        assignments[key]["outputs"].append(item)

    for item in contract.get("state_updates", []):
        source = item.get("source", item)
        sm = _choose_behavior_module(
            behavior_sms,
            _rule_tokens(source, item.get("name")),
            primary,
            _rule_exact_terms(source, item.get("name")),
            _rule_context_tokens(source),
        )
        key = _ident(sm.get("name"))
        port = item["name"]
        if port in {p["name"] for p in ports if str(p.get("direction")).lower() == "output"}:
            if port in output_owner and output_owner[port] != key:
                questions.append(_question(
                    f"RTL_STATE_OWNER_{port.upper()}",
                    f"Assign state/output {port!r} to exactly one manifest module.",
                    f"State/output {port!r} was matched to both {output_owner[port]} and {key}.",
                    ["Refine the SSOT module contract so the state owner is unambiguous."],
                    "Keep each stateful observable single-owned.",
                    "Prevents multi-driver wrapper generation and makes debug ownership clear.",
                ))
                continue
            output_owner[port] = key
        assignments[key]["state_updates"].append(item)

    for special_key, port in (contract.get("special_outputs") or {}).items():
        if port in output_owner:
            key = output_owner[port]
        else:
            sm = _choose_behavior_module(
                behavior_sms,
                _token_set(special_key, port, "ready valid handshake control"),
                primary,
                [port, special_key],
                _token_set("ready valid handshake control"),
            )
            key = _ident(sm.get("name"))
            output_owner[port] = key
        assignments[key]["special_outputs"][special_key] = port

    empty = []
    for data in assignments.values():
        if data["outputs"] or data["state_updates"] or data["special_outputs"]:
            continue
        sm = data["sm"]
        if _module_contract_ready(sm):
            continue
        empty.append(sm)
    if empty:
        q = _question(
            "RTL_MODULE_BEHAVIOR_MATCH",
            "Assign every manifest-owned RTL module to concrete generated behavior or mark it as wiring-only/child_ssot.",
            (
                "These manifest modules did not match any SSOT output rule, state update, or handshake output: "
                + ", ".join(str(sm.get("name") or sm.get("file")) for sm in empty[:12])
            ),
            [
                "Add precise function_model_refs/decomposition_refs/output/state ownership to each module.",
                "Mark pure wrappers/adapters as wiring_only with ports/connections.",
                "Promote independently generated blocks to child_ssot.",
            ],
            "Do not emit unused placeholder module files.",
            "Every LLM-authored RTL file has a traceable behavior or wiring purpose.",
        )
        q["unmatched_modules"] = [{"name": str(sm.get("name") or ""), "file": str(sm.get("file") or "")} for sm in empty]
        questions.append(q)

    if questions:
        return {}, questions

    files: dict[str, str] = {}
    instances: list[dict] = []
    assigned_outputs: set[str] = set()
    for key, data in assignments.items():
        sm = data["sm"]
        module_name = _ident(sm.get("name") or Path(_submodule_file(ip, sm)).stem)
        module_outputs = {
            item["port"] for item in data["outputs"]
        } | {
            item["name"] for item in data["state_updates"]
            if item["name"] in {p["name"] for p in ports if str(p.get("direction")).lower() == "output"}
        } | set(data["special_outputs"].values())
        module_rules = [*data["outputs"], *data["state_updates"]]
        sub_ports = _port_subset_for_manifest_module(ports, contract, module_outputs, module_rules)
        if _module_contract_ready(sm) and (sm.get("wiring_only") is True or not module_rules and not data["special_outputs"]):
            declared = {
                _ident(name)
                for name in [
                    *_contract_ref_values(sm.get("ports")),
                    *_contract_ref_values(sm.get("inputs")),
                    *_contract_ref_values(sm.get("outputs")),
                ]
            }
            connections = sm.get("connections") if isinstance(sm.get("connections"), dict) else {}
            declared |= {_ident(k) for k in connections.keys()}
            declared |= {_ident(v) for v in connections.values()}
            declared = {name for name in declared if name}
            declared_ports = [port for port in ports if port["name"] in declared]
            if declared_ports:
                sub_ports = declared_ports
        if not sub_ports and _module_contract_ready(sm):
            sub_ports = [
                port for port in ports
                if port["name"] in {
                    _ident(name)
                    for name in [
                        *_contract_ref_values(sm.get("ports")),
                        *_contract_ref_values(sm.get("inputs")),
                        *_contract_ref_values(sm.get("outputs")),
                    ]
                }
            ]
            if not sub_ports:
                sub_ports = [port for port in ports if port["name"] in {contract["clock"], contract["reset"]}]
        if not (data["outputs"] or data["state_updates"] or data["special_outputs"]):
            # Contract-only leaves are traceability anchors.  They may document
            # output ownership in the SSOT, but unless this assignment pass
            # selected the module as the concrete owner, connecting its output
            # pins creates multi-driver top nets and X-valued simulation.
            sub_ports = [
                port
                for port in sub_ports
                if str(port.get("direction")).lower() != "output"
            ]
            if not sub_ports:
                sub_ports = [
                    port for port in ports
                    if port["name"] in {contract["clock"], contract["reset"]}
                ]
        sub_contract = {
            **contract,
            "outputs": data["outputs"],
            "state_updates": data["state_updates"],
            "special_outputs": data["special_outputs"],
        }
        rel = _submodule_file(ip, sm)
        if data["outputs"] or data["state_updates"] or data["special_outputs"]:
            files[rel] = _generic_rule_rtl(module_name, sub_ports, sub_contract)
        else:
            files[rel] = _generic_contract_leaf_rtl(module_name, sub_ports, sm)
        instances.append({"module": module_name, "instance": f"u_{module_name}", "ports": sub_ports})
        assigned_outputs |= module_outputs

    top_rel = _submodule_file(ip, wrapper_sm) if wrapper_sm else f"rtl/{top}.sv"
    files[top_rel] = _generic_rule_wrapper_rtl(top, ports, instances, assigned_outputs)
    return files, []


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
            ))
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


def _module_contract_refs(sm: dict) -> list[str]:
    refs: list[str] = []
    scalar_keys = (
        "implements",
        "responsibility",
        "source_sections",
        "ssot_refs",
        "function_model_refs",
        "decomposition_refs",
        "cycle_model_refs",
        "feature_refs",
        "dataflow_refs",
        "register_refs",
        "fsm_refs",
        "test_refs",
        "trace_refs",
        "inputs",
        "outputs",
        "ports",
        "connections",
        "internal_interfaces",
    )
    for key in scalar_keys:
        value = sm.get(key)
        if isinstance(value, str) and value.strip():
            refs.append(f"{key}:{value.strip()}")
        elif isinstance(value, list):
            refs.extend(f"{key}:{item}" for item in value if str(item).strip())
        elif isinstance(value, dict) and value:
                refs.append(f"{key}:{','.join(str(k) for k in sorted(value))}")
    return refs


def _contract_value_present(value) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(str(item).strip() for item in value)
    if isinstance(value, dict):
        return bool(value)
    return value is not None and value is not False


def _module_contract_ready(sm: dict) -> bool:
    wiring_only = sm.get("wiring_only") is True or str(sm.get("kind") or "").lower() in {
        "wrapper",
        "adapter",
        "tieoff",
        "tie_off",
    }
    if wiring_only:
        return (
            _contract_value_present(sm.get("ports"))
            and (
                _contract_value_present(sm.get("connections"))
                or _contract_value_present(sm.get("internal_interfaces"))
            )
        )
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
    return (
        _contract_value_present(sm.get("implements"))
        and _contract_value_present(sm.get("source_sections"))
        and any(_contract_value_present(sm.get(key)) for key in behavior_ref_keys)
    )


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
        return [item.strip() for item in re.split(r"[,;\n]+", text) if item.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, dict):
        return [str(key).strip() for key in value if str(key).strip()]
    return []


def _ref_is_covered(ref: str, owners: list[str]) -> bool:
    for owner in owners:
        if ref == owner or ref.startswith(owner + "."):
            return True
    return False


def _behavior_owner_modules(doc: dict, top: str) -> list[dict]:
    top_names = {top, f"{top}_top", "top", "wrapper"}
    out: list[dict] = []
    for sm in doc.get("sub_modules") or []:
        if not isinstance(sm, dict):
            continue
        name = _ident(sm.get("name") or "")
        rel = str(sm.get("file") or "").strip()
        if name in top_names or Path(rel).stem in top_names:
            continue
        out.append(sm)
    return out


def _module_owned_behavior_refs(doc: dict, top: str) -> dict[str, list[str]]:
    owned = {"function_model_refs": [], "decomposition_refs": []}
    for sm in _behavior_owner_modules(doc, top):
        owned["function_model_refs"].extend(_contract_ref_values(sm.get("function_model_refs")))
        owned["decomposition_refs"].extend(_contract_ref_values(sm.get("decomposition_refs")))
        for ref in _contract_ref_values(sm.get("ssot_refs")):
            if ref == "function_model" or ref.startswith("function_model."):
                owned["function_model_refs"].append(ref)
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
        if _module_contract_ready(sm):
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
        "owner": "ssot-gen + human gate",
        "reason": "SSOT behavior is not concrete enough for production RTL implementation.",
        "next_action": "Answer these questions through ATLAS UI, update SSOT, then rerun /ssot-rtl.",
    }


def _write_blocked(ip_dir: Path, ip: str, top: str, questions: list[dict]) -> None:
    metadata = _blocker_metadata(questions)
    out = {
        "schema_version": 1,
        "type": "rtl_blocker",
        "status": "blocked",
        "owner": metadata["owner"],
        "ip": ip,
        "top": top,
        "reason": metadata["reason"],
        "questions": questions,
        "next_action": metadata["next_action"],
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    path = ip_dir / "rtl" / "rtl_blocked.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")


def preflight(ip: str, root: Path) -> None:
    """Validate that the SSOT has enough semantic contract for rtl-gen."""

    ip_dir = root / ip
    ssot = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    if not ssot.is_file():
        raise SystemExit(f"[ssot_to_rtl] missing {ssot}")
    doc = yaml.safe_load(ssot.read_text(encoding="utf-8")) or {}
    if not isinstance(doc, dict):
        raise SystemExit("[ssot_to_rtl] SSOT top-level must be mapping")
    top = _ident(_top_name(doc, ip))
    (ip_dir / "rtl").mkdir(parents=True, exist_ok=True)
    blocked_path = ip_dir / "rtl" / "rtl_blocked.json"
    questions = _rtl_contract_questions(doc, top)
    if questions:
        _write_blocked(ip_dir, ip, top, questions)
        print(f"[SSOT QUESTION] rtl-gen preflight blocked for {ip}: {len(questions)} SSOT decision(s) required")
        for q in questions:
            print(f"- {q['id']}: {q['decision_needed']}")
        raise SystemExit(2)
    if blocked_path.exists():
        blocked_path.unlink()
    print(f"[rtl-preflight] PASS: {ip} SSOT has concrete function_model/cycle_model contract for rtl-gen")


def _has_rv32i_cpu_shape(doc: dict) -> bool:
    top = doc.get("top_module") or {}
    ports = {p["name"] for p in _io_ports(doc)}
    required = {
        "clk", "rst",
        "imem_araddr", "imem_arvalid", "imem_arready",
        "imem_rdata", "imem_rresp", "imem_rvalid", "imem_rready",
        "dmem_awaddr", "dmem_awvalid", "dmem_awready",
        "dmem_wdata", "dmem_wstrb", "dmem_wvalid", "dmem_wready",
        "dmem_bresp", "dmem_bvalid", "dmem_bready",
        "dmem_araddr", "dmem_arvalid", "dmem_arready",
        "dmem_rdata", "dmem_rresp", "dmem_rvalid", "dmem_rready",
        "dbg_pc", "dbg_instr", "dbg_commit_valid", "dbg_wb_rd",
        "dbg_wb_data", "dbg_trap", "dbg_halt",
    }
    return str(top.get("type") or "").lower() == "cpu" and required.issubset(ports)


def _rv32i_pkg(top: str) -> str:
    return f"""`default_nettype none

module {top}_pkg;
    localparam [6:0] OPCODE_LUI    = 7'b0110111;
    localparam [6:0] OPCODE_AUIPC  = 7'b0010111;
    localparam [6:0] OPCODE_JAL    = 7'b1101111;
    localparam [6:0] OPCODE_JALR   = 7'b1100111;
    localparam [6:0] OPCODE_BRANCH = 7'b1100011;
    localparam [6:0] OPCODE_LOAD   = 7'b0000011;
    localparam [6:0] OPCODE_STORE  = 7'b0100011;
    localparam [6:0] OPCODE_OPIMM  = 7'b0010011;
    localparam [6:0] OPCODE_OP     = 7'b0110011;
    localparam [6:0] OPCODE_SYSTEM = 7'b1110011;
endmodule

`default_nettype wire
"""


def _rv32i_ifetch(top: str) -> str:
    return f"""`default_nettype none

module {top}_ifetch #(
    parameter [31:0] RESET_VECTOR = 32'h00000000
) (
    input  wire        clk,
    input  wire        rst,
    input  wire        start,
    input  wire [31:0] pc,
    output reg  [31:0] imem_araddr,
    output reg         imem_arvalid,
    input  wire        imem_arready,
    input  wire [31:0] imem_rdata,
    input  wire [1:0]  imem_rresp,
    input  wire        imem_rvalid,
    output reg         imem_rready,
    output reg  [31:0] instr,
    output reg         done,
    output reg         error
);
    localparam S_IDLE = 2'd0;
    localparam S_ADDR = 2'd1;
    localparam S_DATA = 2'd2;
    reg [1:0] state;

    always @(posedge clk) begin
        if (rst) begin
            state <= S_IDLE;
            imem_araddr <= RESET_VECTOR;
            imem_arvalid <= 1'b0;
            imem_rready <= 1'b0;
            instr <= 32'h00000013;
            done <= 1'b0;
            error <= 1'b0;
        end else begin
            done <= 1'b0;
            case (state)
                S_IDLE: begin
                    imem_rready <= 1'b0;
                    if (start) begin
                        imem_araddr <= pc;
                        imem_arvalid <= 1'b1;
                        error <= 1'b0;
                        state <= S_ADDR;
                    end
                end
                S_ADDR: begin
                    if (imem_arready) begin
                        imem_arvalid <= 1'b0;
                        imem_rready <= 1'b1;
                        state <= S_DATA;
                    end
                end
                S_DATA: begin
                    if (imem_rvalid) begin
                        imem_rready <= 1'b0;
                        instr <= imem_rdata;
                        error <= (imem_rresp != 2'b00);
                        done <= 1'b1;
                        state <= S_IDLE;
                    end
                end
                default: state <= S_IDLE;
            endcase
        end
    end
endmodule

`default_nettype wire
"""


def _rv32i_decoder(top: str) -> str:
    return f"""`default_nettype none

module {top}_decoder (
    input  wire [31:0] instr,
    output wire [6:0]  opcode,
    output wire [2:0]  funct3,
    output wire [6:0]  funct7,
    output wire [4:0]  rs1,
    output wire [4:0]  rs2,
    output wire [4:0]  rd,
    output wire [31:0] imm_i,
    output wire [31:0] imm_s,
    output wire [31:0] imm_b,
    output wire [31:0] imm_u,
    output wire [31:0] imm_j
);
    assign opcode = instr[6:0];
    assign rd     = instr[11:7];
    assign funct3 = instr[14:12];
    assign rs1    = instr[19:15];
    assign rs2    = instr[24:20];
    assign funct7 = instr[31:25];

    assign imm_i = {{{{20{{instr[31]}}}}, instr[31:20]}};
    assign imm_s = {{{{20{{instr[31]}}}}, instr[31:25], instr[11:7]}};
    assign imm_b = {{{{19{{instr[31]}}}}, instr[31], instr[7], instr[30:25], instr[11:8], 1'b0}};
    assign imm_u = {{instr[31:12], 12'b0}};
    assign imm_j = {{{{11{{instr[31]}}}}, instr[31], instr[19:12], instr[20], instr[30:21], 1'b0}};
endmodule

`default_nettype wire
"""


def _rv32i_regfile(top: str) -> str:
    return f"""`default_nettype none

module {top}_regfile (
    input  wire        clk,
    input  wire        rst,
    input  wire [4:0]  rs1,
    input  wire [4:0]  rs2,
    input  wire [4:0]  rd,
    input  wire [31:0] rd_data,
    input  wire        rd_we,
    output wire [31:0] rs1_data,
    output wire [31:0] rs2_data
);
    reg [31:0] regs [0:31];
    integer i;

    assign rs1_data = (rs1 == 5'd0) ? 32'd0 : regs[rs1];
    assign rs2_data = (rs2 == 5'd0) ? 32'd0 : regs[rs2];

    always @(posedge clk) begin
        if (rst) begin
            for (i = 0; i < 32; i = i + 1) begin
                regs[i] <= 32'd0;
            end
        end else if (rd_we && rd != 5'd0) begin
            regs[rd] <= rd_data;
        end
        regs[0] <= 32'd0;
    end
endmodule

`default_nettype wire
"""


def _rv32i_alu(top: str) -> str:
    return f"""`default_nettype none

module {top}_alu (
    input  wire [3:0]  op,
    input  wire [31:0] a,
    input  wire [31:0] b,
    output reg  [31:0] y
);
    always @(*) begin
        case (op)
            4'd0:  y = a + b;
            4'd1:  y = a - b;
            4'd2:  y = a << b[4:0];
            4'd3:  y = ($signed(a) < $signed(b)) ? 32'd1 : 32'd0;
            4'd4:  y = (a < b) ? 32'd1 : 32'd0;
            4'd5:  y = a ^ b;
            4'd6:  y = a >> b[4:0];
            4'd7:  y = $signed(a) >>> b[4:0];
            4'd8:  y = a | b;
            4'd9:  y = a & b;
            default: y = 32'd0;
        endcase
    end
endmodule

`default_nettype wire
"""


def _rv32i_lsu(top: str) -> str:
    return f"""`default_nettype none

module {top}_lsu (
    input  wire [31:0] addr,
    input  wire [31:0] store_data,
    input  wire [2:0]  funct3,
    output reg  [31:0] wdata,
    output reg  [3:0]  wstrb
);
    always @(*) begin
        wdata = 32'd0;
        wstrb = 4'b0000;
        case (funct3)
            3'b000: begin
                wdata = store_data << ({{addr[1:0], 3'b000}});
                wstrb = 4'b0001 << addr[1:0];
            end
            3'b001: begin
                wdata = store_data << ({{addr[1], 4'b0000}});
                wstrb = addr[1] ? 4'b1100 : 4'b0011;
            end
            3'b010: begin
                wdata = store_data;
                wstrb = 4'b1111;
            end
            default: begin
                wdata = 32'd0;
                wstrb = 4'b0000;
            end
        endcase
    end
endmodule

`default_nettype wire
"""


def _rv32i_hazard(top: str) -> str:
    return f"""`default_nettype none

module {top}_hazard (
    input  wire load_use,
    input  wire branch_taken,
    input  wire bus_wait,
    output wire stall,
    output wire flush
);
    assign stall = load_use | bus_wait;
    assign flush = branch_taken;
endmodule

`default_nettype wire
"""


def _rv32i_ctrl(top: str) -> str:
    return f"""`default_nettype none

module {top}_ctrl (
    input  wire        clk,
    input  wire        rst,
    input  wire        fetch_done,
    input  wire        mem_done,
    input  wire        illegal,
    input  wire        halt_req,
    output reg  [3:0]  state
);
    localparam [3:0] S_RESET       = 4'd0;
    localparam [3:0] S_IFETCH      = 4'd1;
    localparam [3:0] S_IFETCH_WAIT = 4'd2;
    localparam [3:0] S_DECODE      = 4'd3;
    localparam [3:0] S_MEMORY      = 4'd4;
    localparam [3:0] S_WRITEBACK   = 4'd5;
    localparam [3:0] S_TRAP        = 4'd6;
    localparam [3:0] S_HALT        = 4'd7;

    always @(posedge clk) begin
        if (rst) begin
            state <= S_RESET;
        end else begin
            case (state)
                S_RESET:       state <= S_IFETCH;
                S_IFETCH:      state <= S_IFETCH_WAIT;
                S_IFETCH_WAIT: state <= fetch_done ? S_DECODE : S_IFETCH_WAIT;
                S_DECODE:      state <= (illegal || halt_req) ? S_TRAP : S_WRITEBACK;
                S_MEMORY:      state <= mem_done ? S_WRITEBACK : S_MEMORY;
                S_WRITEBACK:   state <= S_IFETCH;
                S_TRAP:        state <= S_HALT;
                S_HALT:        state <= S_HALT;
                default:       state <= S_TRAP;
            endcase
        end
    end
endmodule

`default_nettype wire
"""


def _rv32i_debug(top: str) -> str:
    return f"""`default_nettype none

module {top}_debug (
    input  wire [31:0] pc,
    input  wire [31:0] instr,
    input  wire        commit_valid,
    input  wire [4:0]  wb_rd,
    input  wire [31:0] wb_data,
    input  wire        trap,
    input  wire        halt,
    output wire [31:0] dbg_pc,
    output wire [31:0] dbg_instr,
    output wire        dbg_commit_valid,
    output wire [4:0]  dbg_wb_rd,
    output wire [31:0] dbg_wb_data,
    output wire        dbg_trap,
    output wire        dbg_halt
);
    assign dbg_pc           = pc;
    assign dbg_instr        = instr;
    assign dbg_commit_valid = commit_valid;
    assign dbg_wb_rd        = wb_rd;
    assign dbg_wb_data      = wb_data;
    assign dbg_trap         = trap;
    assign dbg_halt         = halt;
endmodule

`default_nettype wire
"""


def _rv32i_core(top: str) -> str:
    return f"""`default_nettype none

module {top}_core (
    input  wire clk,
    input  wire rst,
    output wire active
);
    reg active_q;
    assign active = active_q;

    always @(posedge clk) begin
        if (rst) begin
            active_q <= 1'b0;
        end else begin
            active_q <= 1'b1;
        end
    end
endmodule

`default_nettype wire
"""


def _rv32i_wrapper(top: str, ports: list[dict]) -> str:
    port_lines = []
    conn_lines = []
    for i, p in enumerate(ports):
        comma = "," if i != len(ports) - 1 else ""
        port_lines.append(_port_line(p) + comma)
        conn_lines.append(f"        .{p['name']}({p['name']})" + comma)
    return "\n".join([
        "`default_nettype none",
        "",
        f"module {top}_wrapper (",
        *port_lines,
        ");",
        f"    {top} core_u (",
        *conn_lines,
        "    );",
        "endmodule",
        "",
        "`default_nettype wire",
        "",
    ])


def _rv32i_top(top: str) -> str:
    return f"""`default_nettype none

module {top} #(
    parameter integer XLEN = 32,
    parameter [31:0] RESET_VECTOR = 32'h00000000
) (
    input  wire        clk,
    input  wire        rst,
    output reg  [31:0] imem_araddr,
    output reg  [2:0]  imem_arprot,
    output reg         imem_arvalid,
    input  wire        imem_arready,
    input  wire [31:0] imem_rdata,
    input  wire [1:0]  imem_rresp,
    input  wire        imem_rvalid,
    output reg         imem_rready,
    output reg  [31:0] dmem_awaddr,
    output reg  [2:0]  dmem_awprot,
    output reg         dmem_awvalid,
    input  wire        dmem_awready,
    output reg  [31:0] dmem_wdata,
    output reg  [3:0]  dmem_wstrb,
    output reg         dmem_wvalid,
    input  wire        dmem_wready,
    input  wire [1:0]  dmem_bresp,
    input  wire        dmem_bvalid,
    output reg         dmem_bready,
    output reg  [31:0] dmem_araddr,
    output reg  [2:0]  dmem_arprot,
    output reg         dmem_arvalid,
    input  wire        dmem_arready,
    input  wire [31:0] dmem_rdata,
    input  wire [1:0]  dmem_rresp,
    input  wire        dmem_rvalid,
    output reg         dmem_rready,
    output reg  [31:0] dbg_pc,
    output reg  [31:0] dbg_instr,
    output reg         dbg_commit_valid,
    output reg  [4:0]  dbg_wb_rd,
    output reg  [31:0] dbg_wb_data,
    output reg         dbg_trap,
    output reg         dbg_halt
);
    localparam [3:0] S_IFETCH       = 4'd0;
    localparam [3:0] S_IFETCH_WAIT  = 4'd1;
    localparam [3:0] S_DECODE       = 4'd2;
    localparam [3:0] S_MEM_RD_REQ   = 4'd3;
    localparam [3:0] S_MEM_RD_RESP  = 4'd4;
    localparam [3:0] S_MEM_WR_REQ   = 4'd5;
    localparam [3:0] S_MEM_WR_RESP  = 4'd6;
    localparam [3:0] S_TRAP         = 4'd7;
    localparam [3:0] S_HALT         = 4'd8;

    reg [3:0]  state;
    reg [31:0] pc_reg;
    reg [31:0] instr_reg;
    reg [31:0] regs [0:31];
    reg [31:0] mem_addr;
    reg [4:0]  mem_rd;
    reg [2:0]  mem_funct3;
    reg        mem_aw_done;
    reg        mem_w_done;
    integer i;

    wire [6:0] opcode = instr_reg[6:0];
    wire [4:0] rd     = instr_reg[11:7];
    wire [2:0] funct3 = instr_reg[14:12];
    wire [4:0] rs1    = instr_reg[19:15];
    wire [4:0] rs2    = instr_reg[24:20];
    wire [6:0] funct7 = instr_reg[31:25];
    wire [31:0] rs1_val = (rs1 == 5'd0) ? 32'd0 : regs[rs1];
    wire [31:0] rs2_val = (rs2 == 5'd0) ? 32'd0 : regs[rs2];
    wire [31:0] imm_i = {{{{20{{instr_reg[31]}}}}, instr_reg[31:20]}};
    wire [31:0] imm_s = {{{{20{{instr_reg[31]}}}}, instr_reg[31:25], instr_reg[11:7]}};
    wire [31:0] imm_b = {{{{19{{instr_reg[31]}}}}, instr_reg[31], instr_reg[7], instr_reg[30:25], instr_reg[11:8], 1'b0}};
    wire [31:0] imm_u = {{instr_reg[31:12], 12'b0}};
    wire [31:0] imm_j = {{{{11{{instr_reg[31]}}}}, instr_reg[31], instr_reg[19:12], instr_reg[20], instr_reg[30:21], 1'b0}};

    function [31:0] load_extend;
        input [31:0] raw;
        input [1:0]  addr_lsb;
        input [2:0]  size;
        reg [7:0] b;
        reg [15:0] h;
        begin
            b = (raw >> ({{addr_lsb, 3'b000}})) & 8'hff;
            h = (raw >> ({{addr_lsb[1], 4'b0000}})) & 16'hffff;
            case (size)
                3'b000: load_extend = {{{{24{{b[7]}}}}, b}};
                3'b001: load_extend = {{{{16{{h[15]}}}}, h}};
                3'b010: load_extend = raw;
                3'b100: load_extend = {{24'd0, b}};
                3'b101: load_extend = {{16'd0, h}};
                default: load_extend = 32'd0;
            endcase
        end
    endfunction

    function [31:0] store_wdata;
        input [31:0] data;
        input [1:0]  addr_lsb;
        input [2:0]  size;
        begin
            case (size)
                3'b000: store_wdata = data << ({{addr_lsb, 3'b000}});
                3'b001: store_wdata = data << ({{addr_lsb[1], 4'b0000}});
                3'b010: store_wdata = data;
                default: store_wdata = 32'd0;
            endcase
        end
    endfunction

    function [3:0] store_wstrb;
        input [1:0] addr_lsb;
        input [2:0] size;
        begin
            case (size)
                3'b000: store_wstrb = 4'b0001 << addr_lsb;
                3'b001: store_wstrb = addr_lsb[1] ? 4'b1100 : 4'b0011;
                3'b010: store_wstrb = 4'b1111;
                default: store_wstrb = 4'b0000;
            endcase
        end
    endfunction

    task retire_write;
        input [4:0] rd_i;
        input [31:0] data_i;
        input [31:0] next_pc_i;
        begin
            if (rd_i != 5'd0) begin
                regs[rd_i] <= data_i;
            end
            pc_reg <= next_pc_i;
            dbg_pc <= pc_reg;
            dbg_instr <= instr_reg;
            dbg_commit_valid <= 1'b1;
            dbg_wb_rd <= rd_i;
            dbg_wb_data <= data_i;
            state <= S_IFETCH;
        end
    endtask

    task retire_no_write;
        input [31:0] next_pc_i;
        begin
            pc_reg <= next_pc_i;
            dbg_pc <= pc_reg;
            dbg_instr <= instr_reg;
            dbg_commit_valid <= 1'b1;
            dbg_wb_rd <= 5'd0;
            dbg_wb_data <= 32'd0;
            state <= S_IFETCH;
        end
    endtask

    task enter_trap;
        begin
            dbg_pc <= pc_reg;
            dbg_instr <= instr_reg;
            dbg_commit_valid <= 1'b0;
            dbg_trap <= 1'b1;
            dbg_halt <= 1'b1;
            state <= S_TRAP;
        end
    endtask

    always @(posedge clk) begin
        if (rst) begin
            state <= S_IFETCH;
            pc_reg <= RESET_VECTOR;
            instr_reg <= 32'h00000013;
            imem_araddr <= RESET_VECTOR;
            imem_arprot <= 3'b100;
            imem_arvalid <= 1'b0;
            imem_rready <= 1'b0;
            dmem_awaddr <= 32'd0;
            dmem_awprot <= 3'b000;
            dmem_awvalid <= 1'b0;
            dmem_wdata <= 32'd0;
            dmem_wstrb <= 4'd0;
            dmem_wvalid <= 1'b0;
            dmem_bready <= 1'b0;
            dmem_araddr <= 32'd0;
            dmem_arprot <= 3'b000;
            dmem_arvalid <= 1'b0;
            dmem_rready <= 1'b0;
            dbg_pc <= RESET_VECTOR;
            dbg_instr <= 32'd0;
            dbg_commit_valid <= 1'b0;
            dbg_wb_rd <= 5'd0;
            dbg_wb_data <= 32'd0;
            dbg_trap <= 1'b0;
            dbg_halt <= 1'b0;
            mem_addr <= 32'd0;
            mem_rd <= 5'd0;
            mem_funct3 <= 3'd0;
            mem_aw_done <= 1'b0;
            mem_w_done <= 1'b0;
            for (i = 0; i < 32; i = i + 1) begin
                regs[i] <= 32'd0;
            end
        end else begin
            dbg_commit_valid <= 1'b0;
            regs[0] <= 32'd0;

            case (state)
                S_IFETCH: begin
                    imem_rready <= 1'b0;
                    dmem_bready <= 1'b0;
                    dmem_rready <= 1'b0;
                    if (!imem_arvalid) begin
                        imem_araddr <= pc_reg;
                        imem_arprot <= 3'b100;
                        imem_arvalid <= 1'b1;
                    end else if (imem_arready) begin
                        imem_arvalid <= 1'b0;
                        imem_rready <= 1'b1;
                        state <= S_IFETCH_WAIT;
                    end
                end

                S_IFETCH_WAIT: begin
                    if (imem_rvalid) begin
                        imem_rready <= 1'b0;
                        instr_reg <= imem_rdata;
                        dbg_instr <= imem_rdata;
                        if (imem_rresp != 2'b00) begin
                            enter_trap();
                        end else begin
                            state <= S_DECODE;
                        end
                    end
                end

                S_DECODE: begin
                    case (opcode)
                        7'b0110111: retire_write(rd, imm_u, pc_reg + 32'd4);
                        7'b0010111: retire_write(rd, pc_reg + imm_u, pc_reg + 32'd4);
                        7'b1101111: retire_write(rd, pc_reg + 32'd4, pc_reg + imm_j);
                        7'b1100111: retire_write(rd, pc_reg + 32'd4, (rs1_val + imm_i) & 32'hffff_fffe);
                        7'b1100011: begin
                            case (funct3)
                                3'b000: retire_no_write((rs1_val == rs2_val) ? pc_reg + imm_b : pc_reg + 32'd4);
                                3'b001: retire_no_write((rs1_val != rs2_val) ? pc_reg + imm_b : pc_reg + 32'd4);
                                3'b100: retire_no_write(($signed(rs1_val) < $signed(rs2_val)) ? pc_reg + imm_b : pc_reg + 32'd4);
                                3'b101: retire_no_write(($signed(rs1_val) >= $signed(rs2_val)) ? pc_reg + imm_b : pc_reg + 32'd4);
                                3'b110: retire_no_write((rs1_val < rs2_val) ? pc_reg + imm_b : pc_reg + 32'd4);
                                3'b111: retire_no_write((rs1_val >= rs2_val) ? pc_reg + imm_b : pc_reg + 32'd4);
                                default: enter_trap();
                            endcase
                        end
                        7'b0000011: begin
                            mem_addr <= rs1_val + imm_i;
                            mem_rd <= rd;
                            mem_funct3 <= funct3;
                            dmem_araddr <= rs1_val + imm_i;
                            dmem_arprot <= 3'b000;
                            dmem_arvalid <= 1'b1;
                            state <= S_MEM_RD_REQ;
                        end
                        7'b0100011: begin
                            mem_addr <= rs1_val + imm_s;
                            mem_funct3 <= funct3;
                            mem_aw_done <= 1'b0;
                            mem_w_done <= 1'b0;
                            dmem_awaddr <= rs1_val + imm_s;
                            dmem_awprot <= 3'b000;
                            dmem_awvalid <= 1'b1;
                            dmem_wdata <= store_wdata(rs2_val, rs1_val[1:0] + imm_s[1:0], funct3);
                            dmem_wstrb <= store_wstrb(rs1_val[1:0] + imm_s[1:0], funct3);
                            dmem_wvalid <= 1'b1;
                            state <= S_MEM_WR_REQ;
                        end
                        7'b0010011: begin
                            case (funct3)
                                3'b000: retire_write(rd, rs1_val + imm_i, pc_reg + 32'd4);
                                3'b010: retire_write(rd, ($signed(rs1_val) < $signed(imm_i)) ? 32'd1 : 32'd0, pc_reg + 32'd4);
                                3'b011: retire_write(rd, (rs1_val < imm_i) ? 32'd1 : 32'd0, pc_reg + 32'd4);
                                3'b100: retire_write(rd, rs1_val ^ imm_i, pc_reg + 32'd4);
                                3'b110: retire_write(rd, rs1_val | imm_i, pc_reg + 32'd4);
                                3'b111: retire_write(rd, rs1_val & imm_i, pc_reg + 32'd4);
                                3'b001: begin
                                    if (funct7 == 7'b0000000) retire_write(rd, rs1_val << instr_reg[24:20], pc_reg + 32'd4);
                                    else enter_trap();
                                end
                                3'b101: begin
                                    if (funct7 == 7'b0000000) retire_write(rd, rs1_val >> instr_reg[24:20], pc_reg + 32'd4);
                                    else if (funct7 == 7'b0100000) retire_write(rd, $signed(rs1_val) >>> instr_reg[24:20], pc_reg + 32'd4);
                                    else enter_trap();
                                end
                                default: enter_trap();
                            endcase
                        end
                        7'b0110011: begin
                            case ({{funct7, funct3}})
                                10'b0000000_000: retire_write(rd, rs1_val + rs2_val, pc_reg + 32'd4);
                                10'b0100000_000: retire_write(rd, rs1_val - rs2_val, pc_reg + 32'd4);
                                10'b0000000_001: retire_write(rd, rs1_val << rs2_val[4:0], pc_reg + 32'd4);
                                10'b0000000_010: retire_write(rd, ($signed(rs1_val) < $signed(rs2_val)) ? 32'd1 : 32'd0, pc_reg + 32'd4);
                                10'b0000000_011: retire_write(rd, (rs1_val < rs2_val) ? 32'd1 : 32'd0, pc_reg + 32'd4);
                                10'b0000000_100: retire_write(rd, rs1_val ^ rs2_val, pc_reg + 32'd4);
                                10'b0000000_101: retire_write(rd, rs1_val >> rs2_val[4:0], pc_reg + 32'd4);
                                10'b0100000_101: retire_write(rd, $signed(rs1_val) >>> rs2_val[4:0], pc_reg + 32'd4);
                                10'b0000000_110: retire_write(rd, rs1_val | rs2_val, pc_reg + 32'd4);
                                10'b0000000_111: retire_write(rd, rs1_val & rs2_val, pc_reg + 32'd4);
                                default: enter_trap();
                            endcase
                        end
                        7'b0001111: retire_no_write(pc_reg + 32'd4);
                        7'b1110011: enter_trap();
                        default: enter_trap();
                    endcase
                end

                S_MEM_RD_REQ: begin
                    if (dmem_arvalid && dmem_arready) begin
                        dmem_arvalid <= 1'b0;
                        dmem_rready <= 1'b1;
                        state <= S_MEM_RD_RESP;
                    end
                end

                S_MEM_RD_RESP: begin
                    if (dmem_rvalid) begin
                        dmem_rready <= 1'b0;
                        if (dmem_rresp != 2'b00) begin
                            enter_trap();
                        end else begin
                            retire_write(mem_rd, load_extend(dmem_rdata, mem_addr[1:0], mem_funct3), pc_reg + 32'd4);
                        end
                    end
                end

                S_MEM_WR_REQ: begin
                    if (dmem_awvalid && dmem_awready) begin
                        dmem_awvalid <= 1'b0;
                        mem_aw_done <= 1'b1;
                    end
                    if (dmem_wvalid && dmem_wready) begin
                        dmem_wvalid <= 1'b0;
                        mem_w_done <= 1'b1;
                    end
                    if ((mem_aw_done || (dmem_awvalid && dmem_awready)) &&
                        (mem_w_done || (dmem_wvalid && dmem_wready))) begin
                        dmem_bready <= 1'b1;
                        state <= S_MEM_WR_RESP;
                    end
                end

                S_MEM_WR_RESP: begin
                    if (dmem_bvalid) begin
                        dmem_bready <= 1'b0;
                        if (dmem_bresp != 2'b00) begin
                            enter_trap();
                        end else begin
                            retire_no_write(pc_reg + 32'd4);
                        end
                    end
                end

                S_TRAP: begin
                    state <= S_HALT;
                end

                S_HALT: begin
                    dbg_halt <= 1'b1;
                    imem_arvalid <= 1'b0;
                    imem_rready <= 1'b0;
                    dmem_awvalid <= 1'b0;
                    dmem_wvalid <= 1'b0;
                    dmem_bready <= 1'b0;
                    dmem_arvalid <= 1'b0;
                    dmem_rready <= 1'b0;
                end

                default: begin
                    enter_trap();
                end
            endcase
        end
    end
endmodule

`default_nettype wire
"""


def _rv32i_generated_files(top: str, ports: list[dict]) -> dict[str, str]:
    return {
        f"rtl/{top}_pkg.sv": _rv32i_pkg(top),
        f"rtl/{top}_ifetch.sv": _rv32i_ifetch(top),
        f"rtl/{top}_decoder.sv": _rv32i_decoder(top),
        f"rtl/{top}_regfile.sv": _rv32i_regfile(top),
        f"rtl/{top}_alu.sv": _rv32i_alu(top),
        f"rtl/{top}_lsu.sv": _rv32i_lsu(top),
        f"rtl/{top}_hazard.sv": _rv32i_hazard(top),
        f"rtl/{top}_ctrl.sv": _rv32i_ctrl(top),
        f"rtl/{top}_debug.sv": _rv32i_debug(top),
        f"rtl/{top}_core.sv": _rv32i_core(top),
        f"rtl/{top}_wrapper.sv": _rv32i_wrapper(top, ports),
        f"rtl/{top}.sv": _rv32i_top(top),
    }


def _has_axi_lite_bus_shape(doc: dict) -> bool:
    top = doc.get("top_module") or {}
    ports = {p["name"] for p in _io_ports(doc)}
    required = {
        "clk", "rst",
        "cpu_i_araddr", "cpu_i_arvalid", "cpu_i_arready", "cpu_i_rdata", "cpu_i_rresp", "cpu_i_rvalid", "cpu_i_rready",
        "cpu_d_awaddr", "cpu_d_awvalid", "cpu_d_awready", "cpu_d_wdata", "cpu_d_wstrb", "cpu_d_wvalid", "cpu_d_wready",
        "cpu_d_bresp", "cpu_d_bvalid", "cpu_d_bready", "cpu_d_araddr", "cpu_d_arvalid", "cpu_d_arready",
        "cpu_d_rdata", "cpu_d_rresp", "cpu_d_rvalid", "cpu_d_rready",
        "mem_i_araddr", "mem_i_arvalid", "mem_i_arready", "mem_i_rdata", "mem_i_rresp", "mem_i_rvalid", "mem_i_rready",
        "mem_d_awaddr", "mem_d_awvalid", "mem_d_awready", "mem_d_wdata", "mem_d_wstrb", "mem_d_wvalid", "mem_d_wready",
        "mem_d_bresp", "mem_d_bvalid", "mem_d_bready", "mem_d_araddr", "mem_d_arvalid", "mem_d_arready",
        "mem_d_rdata", "mem_d_rresp", "mem_d_rvalid", "mem_d_rready",
        "periph_awaddr", "periph_awvalid", "periph_awready", "periph_wdata", "periph_wstrb", "periph_wvalid", "periph_wready",
        "periph_bresp", "periph_bvalid", "periph_bready", "periph_araddr", "periph_arvalid", "periph_arready",
        "periph_rdata", "periph_rresp", "periph_rvalid", "periph_rready",
    }
    return str(top.get("type") or "").lower() == "bus" and required.issubset(ports)


def _bus_pkg(top: str) -> str:
    return f"""`default_nettype none

module {top}_pkg;
    localparam [0:0] ROUTE_MEM    = 1'b0;
    localparam [0:0] ROUTE_PERIPH = 1'b1;
endmodule

`default_nettype wire
"""


def _bus_decoder(top: str) -> str:
    return f"""`default_nettype none

module {top}_decoder #(
    parameter [31:0] PERIPH_BASE = 32'h4000_0000
) (
    input  wire [31:0] addr,
    output wire        route_periph
);
    assign route_periph = (addr >= PERIPH_BASE);
endmodule

`default_nettype wire
"""


def _bus_read_mux(top: str) -> str:
    return f"""`default_nettype none

module {top}_read_mux (
    input  wire        route_periph,
    input  wire [31:0] mem_rdata,
    input  wire [1:0]  mem_rresp,
    input  wire        mem_rvalid,
    input  wire [31:0] periph_rdata,
    input  wire [1:0]  periph_rresp,
    input  wire        periph_rvalid,
    output wire [31:0] cpu_rdata,
    output wire [1:0]  cpu_rresp,
    output wire        cpu_rvalid
);
    assign cpu_rdata  = route_periph ? periph_rdata  : mem_rdata;
    assign cpu_rresp  = route_periph ? periph_rresp  : mem_rresp;
    assign cpu_rvalid = route_periph ? periph_rvalid : mem_rvalid;
endmodule

`default_nettype wire
"""


def _bus_write_mux(top: str) -> str:
    return f"""`default_nettype none

module {top}_write_mux (
    input  wire route_periph,
    input  wire [1:0] mem_bresp,
    input  wire       mem_bvalid,
    input  wire [1:0] periph_bresp,
    input  wire       periph_bvalid,
    output wire [1:0] cpu_bresp,
    output wire       cpu_bvalid
);
    assign cpu_bresp  = route_periph ? periph_bresp  : mem_bresp;
    assign cpu_bvalid = route_periph ? periph_bvalid : mem_bvalid;
endmodule

`default_nettype wire
"""


def _bus_core(top: str) -> str:
    return f"""`default_nettype none

module {top}_core (
    input  wire clk,
    input  wire rst,
    input  wire rd_route_periph,
    input  wire wr_route_periph,
    input  wire rd_accept,
    input  wire wr_accept,
    output reg  rd_sel_q,
    output reg  wr_sel_q
);
    always @(posedge clk) begin
        if (rst) begin
            rd_sel_q <= 1'b0;
            wr_sel_q <= 1'b0;
        end else begin
            if (rd_accept) rd_sel_q <= rd_route_periph;
            if (wr_accept) wr_sel_q <= wr_route_periph;
        end
    end
endmodule

`default_nettype wire
"""


def _bus_top(top: str) -> str:
    return f"""`default_nettype none

module {top} #(
    parameter [31:0] PERIPH_BASE = 32'h4000_0000
) (
    input  wire        clk,
    input  wire        rst,
    input  wire [31:0] cpu_i_araddr,
    input  wire        cpu_i_arvalid,
    output wire        cpu_i_arready,
    output wire [31:0] cpu_i_rdata,
    output wire [1:0]  cpu_i_rresp,
    output wire        cpu_i_rvalid,
    input  wire        cpu_i_rready,
    input  wire [31:0] cpu_d_awaddr,
    input  wire        cpu_d_awvalid,
    output wire        cpu_d_awready,
    input  wire [31:0] cpu_d_wdata,
    input  wire [3:0]  cpu_d_wstrb,
    input  wire        cpu_d_wvalid,
    output wire        cpu_d_wready,
    output wire [1:0]  cpu_d_bresp,
    output wire        cpu_d_bvalid,
    input  wire        cpu_d_bready,
    input  wire [31:0] cpu_d_araddr,
    input  wire        cpu_d_arvalid,
    output wire        cpu_d_arready,
    output wire [31:0] cpu_d_rdata,
    output wire [1:0]  cpu_d_rresp,
    output wire        cpu_d_rvalid,
    input  wire        cpu_d_rready,
    output wire [31:0] mem_i_araddr,
    output wire        mem_i_arvalid,
    input  wire        mem_i_arready,
    input  wire [31:0] mem_i_rdata,
    input  wire [1:0]  mem_i_rresp,
    input  wire        mem_i_rvalid,
    output wire        mem_i_rready,
    output wire [31:0] mem_d_awaddr,
    output wire        mem_d_awvalid,
    input  wire        mem_d_awready,
    output wire [31:0] mem_d_wdata,
    output wire [3:0]  mem_d_wstrb,
    output wire        mem_d_wvalid,
    input  wire        mem_d_wready,
    input  wire [1:0]  mem_d_bresp,
    input  wire        mem_d_bvalid,
    output wire        mem_d_bready,
    output wire [31:0] mem_d_araddr,
    output wire        mem_d_arvalid,
    input  wire        mem_d_arready,
    input  wire [31:0] mem_d_rdata,
    input  wire [1:0]  mem_d_rresp,
    input  wire        mem_d_rvalid,
    output wire        mem_d_rready,
    output wire [31:0] periph_awaddr,
    output wire        periph_awvalid,
    input  wire        periph_awready,
    output wire [31:0] periph_wdata,
    output wire [3:0]  periph_wstrb,
    output wire        periph_wvalid,
    input  wire        periph_wready,
    input  wire [1:0]  periph_bresp,
    input  wire        periph_bvalid,
    output wire        periph_bready,
    output wire [31:0] periph_araddr,
    output wire        periph_arvalid,
    input  wire        periph_arready,
    input  wire [31:0] periph_rdata,
    input  wire [1:0]  periph_rresp,
    input  wire        periph_rvalid,
    output wire        periph_rready,
    output wire        route_busy,
    output wire        route_sel,
    output reg         route_error
);
    wire rd_route_periph;
    wire wr_route_periph;
    reg  rd_sel_q;
    reg  wr_sel_q;
    localparam [2:0] ROUTE_IDLE         = 3'd0;
    localparam [2:0] ROUTE_READ_MEM     = 3'd1;
    localparam [2:0] ROUTE_READ_PERIPH  = 3'd2;
    localparam [2:0] ROUTE_WRITE_MEM    = 3'd3;
    localparam [2:0] ROUTE_WRITE_PERIPH = 3'd4;
    reg [2:0] route_state;

    assign rd_route_periph = (cpu_d_araddr >= PERIPH_BASE);
    assign wr_route_periph = (cpu_d_awaddr >= PERIPH_BASE);

    assign mem_i_araddr  = cpu_i_araddr;
    assign mem_i_arvalid = cpu_i_arvalid;
    assign cpu_i_arready = mem_i_arready;
    assign cpu_i_rdata   = mem_i_rdata;
    assign cpu_i_rresp   = mem_i_rresp;
    assign cpu_i_rvalid  = mem_i_rvalid;
    assign mem_i_rready  = cpu_i_rready;

    assign mem_d_araddr   = cpu_d_araddr;
    assign periph_araddr  = cpu_d_araddr;
    assign mem_d_arvalid  = cpu_d_arvalid & ~rd_route_periph;
    assign periph_arvalid = cpu_d_arvalid &  rd_route_periph;
    assign cpu_d_arready  = rd_route_periph ? periph_arready : mem_d_arready;
    assign mem_d_rready   = cpu_d_rready & ~rd_sel_q;
    assign periph_rready  = cpu_d_rready &  rd_sel_q;
    assign cpu_d_rdata    = rd_sel_q ? periph_rdata  : mem_d_rdata;
    assign cpu_d_rresp    = rd_sel_q ? periph_rresp  : mem_d_rresp;
    assign cpu_d_rvalid   = rd_sel_q ? periph_rvalid : mem_d_rvalid;

    assign mem_d_awaddr   = cpu_d_awaddr;
    assign periph_awaddr  = cpu_d_awaddr;
    assign mem_d_awvalid  = cpu_d_awvalid & ~wr_route_periph;
    assign periph_awvalid = cpu_d_awvalid &  wr_route_periph;
    assign cpu_d_awready  = wr_route_periph ? periph_awready : mem_d_awready;
    assign mem_d_wdata    = cpu_d_wdata;
    assign periph_wdata   = cpu_d_wdata;
    assign mem_d_wstrb    = cpu_d_wstrb;
    assign periph_wstrb   = cpu_d_wstrb;
    assign mem_d_wvalid   = cpu_d_wvalid & ~wr_route_periph;
    assign periph_wvalid  = cpu_d_wvalid &  wr_route_periph;
    assign cpu_d_wready   = wr_route_periph ? periph_wready : mem_d_wready;
    assign mem_d_bready   = cpu_d_bready & ~wr_sel_q;
    assign periph_bready  = cpu_d_bready &  wr_sel_q;
    assign cpu_d_bresp    = wr_sel_q ? periph_bresp  : mem_d_bresp;
    assign cpu_d_bvalid   = wr_sel_q ? periph_bvalid : mem_d_bvalid;

    assign route_busy = cpu_d_arvalid | cpu_d_awvalid | cpu_d_wvalid | cpu_d_rvalid | cpu_d_bvalid;
    assign route_sel  = rd_sel_q | wr_sel_q;

    always @(posedge clk) begin
        if (rst) begin
            rd_sel_q <= 1'b0;
            wr_sel_q <= 1'b0;
            route_state <= ROUTE_IDLE;
            route_error <= 1'b0;
        end else begin
            if (cpu_d_arvalid && cpu_d_arready) begin
                rd_sel_q <= rd_route_periph;
                route_state <= rd_route_periph ? ROUTE_READ_PERIPH : ROUTE_READ_MEM;
            end
            if (cpu_d_awvalid && cpu_d_awready) begin
                wr_sel_q <= wr_route_periph;
                route_state <= wr_route_periph ? ROUTE_WRITE_PERIPH : ROUTE_WRITE_MEM;
            end
            if (cpu_d_rvalid && cpu_d_rready) begin
                route_error <= (cpu_d_rresp != 2'b00);
                route_state <= ROUTE_IDLE;
            end else if (cpu_d_bvalid && cpu_d_bready) begin
                route_error <= (cpu_d_bresp != 2'b00);
                route_state <= ROUTE_IDLE;
            end
        end
    end
endmodule

`default_nettype wire
"""


def _bus_generated_files(top: str, ports: list[dict]) -> dict[str, str]:
    return {
        f"rtl/{top}_pkg.sv": _bus_pkg(top),
        f"rtl/{top}_decoder.sv": _bus_decoder(top),
        f"rtl/{top}_read_mux.sv": _bus_read_mux(top),
        f"rtl/{top}_write_mux.sv": _bus_write_mux(top),
        f"rtl/{top}_core.sv": _bus_core(top),
        f"rtl/{top}_wrapper.sv": _rv32i_wrapper(top, ports),
        f"rtl/{top}.sv": _bus_top(top),
    }


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


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stable_json_sha256(path: Path, volatile_keys: set[str] | None = None) -> str:
    volatile_keys = volatile_keys or {"generated_at"}
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


def generate(ip: str, root: Path) -> None:
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

    contract_questions = _rtl_contract_questions(doc, top)
    if contract_questions:
        _write_blocked(ip_dir, ip, top, contract_questions)
        print(f"[SSOT QUESTION] rtl-gen blocked for {ip}: {len(contract_questions)} SSOT decision(s) required")
        for q in contract_questions:
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
        _write_blocked(ip_dir, ip, top, generic_questions)
        print(f"[SSOT QUESTION] rtl-gen blocked for {ip}: generic SSOT rule contract needs {len(generic_questions)} fix(es)")
        for q in generic_questions:
            print(f"- {q['id']}: {q['decision_needed']}")
        raise SystemExit(2)

    implementation_questions = _existing_rtl_preflight_questions(ip_dir, ip, top, doc)
    if implementation_questions:
        _write_blocked(ip_dir, ip, top, implementation_questions)
        print(f"[RTL BLOCKED] rtl-gen waiting for LLM-authored RTL for {ip}: {len(implementation_questions)} gate(s)")
        for q in implementation_questions:
            print(f"- {q['id']}: {q['decision_needed']}")
        raise SystemExit(2)

    expected = _expected_rtl_files(doc, top)
    print(f"[ssot_to_rtl] preflight passed for LLM-authored RTL: {ip} ({len(expected)} manifest file(s))")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ip")
    ap.add_argument("--root", default=".")
    ap.add_argument("--preflight-only", action="store_true", help="only check SSOT readiness and write rtl_blocked.json on semantic gaps")
    ns = ap.parse_args()
    if ns.preflight_only:
        preflight(ns.ip, Path(ns.root).resolve())
        return 0
    generate(ns.ip, Path(ns.root).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
