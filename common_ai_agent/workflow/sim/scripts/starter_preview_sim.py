#!/usr/bin/env python3
"""Run a deterministic Starter RTL preview smoke simulation.

This is intentionally narrower than production tb-gen. It consumes the
Starter RTL preview contract, emits a tiny SystemVerilog testbench from direct
output_rules, runs iverilog/vvp, and writes sim evidence. Engineering and
Signoff still require the normal TB/sim evidence path.
"""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
import re
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET
from typing import Any

import yaml


CONTROL_INPUT_NAMES = {"clk", "clock", "pclk", "rst", "rst_n", "reset", "resetn", "aresetn", "presetn"}


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _ident(value: object) -> str:
    text = re.sub(r"\W+", "_", str(value or "")).strip("_")
    if not text or not re.match(r"^[A-Za-z_]", text):
        text = "sig_" + text
    return text


def _int_value(value: object, default: int = 0) -> int:
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
            digits = literal.split(base_tag, 1)[1].replace("x", "0").replace("z", "0")
            return int(digits, {"h": 16, "d": 10, "b": 2}.get(base_tag, 10))
        return int(text, 10)
    except Exception:
        return default


def _top_name(doc: dict[str, Any], fallback: str) -> str:
    top = doc.get("top_module") or doc.get("top") or fallback
    if isinstance(top, dict):
        top = top.get("name") or fallback
    return _ident(top)


def _port_width(port: dict[str, Any]) -> int:
    return max(_int_value(port.get("width"), 1), 1)


def _sv_range(width: int) -> str:
    width = max(int(width or 1), 1)
    return "" if width == 1 else f"[{width - 1}:0] "


def _sv_literal(width: int, value: int) -> str:
    width = max(int(width or 1), 1)
    value = int(value) & ((1 << width) - 1)
    return "1'b1" if width == 1 and value else "1'b0" if width == 1 else f"{width}'d{value}"


def _io_ports(doc: dict[str, Any]) -> list[dict[str, Any]]:
    ports: list[dict[str, Any]] = []
    io = doc.get("io_list") if isinstance(doc.get("io_list"), dict) else {}
    for section in ("clock_domains", "resets", "interfaces"):
        for item in io.get(section) or []:
            if not isinstance(item, dict):
                continue
            for port in item.get("ports") or []:
                if isinstance(port, dict) and port.get("name"):
                    ports.append(
                        {
                            "name": _ident(port["name"]),
                            "direction": str(port.get("direction") or "input").lower(),
                            "width": port.get("width", 1),
                        }
                    )
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for port in ports:
        if port["name"] in seen:
            continue
        seen.add(port["name"])
        unique.append(port)
    return unique


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _value_samples(width: int) -> list[int]:
    width = max(int(width or 1), 1)
    max_value = (1 << min(width, 16)) - 1
    samples = [0, 1, max_value]
    out: list[int] = []
    for value in samples:
        if value not in out:
            out.append(value)
    return out


def _stimulus_vectors(ports: list[dict[str, Any]], limit: int = 16) -> list[dict[str, int]]:
    inputs = [
        port for port in ports
        if str(port.get("direction") or "").lower() == "input"
        and str(port.get("name") or "").lower() not in CONTROL_INPUT_NAMES
    ]
    fixed = {
        str(port["name"]): 1 if str(port["name"]).lower().endswith("_n") else 0
        for port in ports
        if str(port.get("direction") or "").lower() == "input"
        and str(port.get("name") or "").lower() in CONTROL_INPUT_NAMES
    }
    if not inputs:
        return [fixed]
    sample_lists = [_value_samples(_port_width(port)) for port in inputs]
    vectors: list[dict[str, int]] = []
    for values in itertools.product(*sample_lists):
        vector = dict(fixed)
        for port, value in zip(inputs, values):
            vector[str(port["name"])] = int(value)
        vectors.append(vector)
        if len(vectors) >= limit:
            break
    return vectors


def _tb_source(ip: str, top: str, ports: list[dict[str, Any]], contract: dict[str, Any]) -> tuple[str, int]:
    tb_name = f"tb_{ip}"
    outputs = [item for item in contract.get("outputs") or [] if isinstance(item, dict)]
    vectors = _stimulus_vectors(ports)
    declarations: list[str] = []
    connections: list[str] = []
    for idx, port in enumerate(ports):
        name = str(port["name"])
        direction = str(port.get("direction") or "input").lower()
        kind = "logic" if direction == "input" else "wire"
        declarations.append(f"    {kind} {_sv_range(_port_width(port))}{name};")
        suffix = "," if idx < len(ports) - 1 else ""
        connections.append(f"        .{name}({name}){suffix}")

    lines: list[str] = [
        "`timescale 1ns/1ps",
        f"module {tb_name};",
        "    integer tests;",
        "    integer pass;",
        "    integer fail;",
        *declarations,
        "",
        f"    {top} dut (",
        *connections,
        "    );",
        "",
        "    initial begin",
        "        tests = 0;",
        "        pass = 0;",
        "        fail = 0;",
        f"        $dumpfile(\"sim/{ip}.vcd\");",
        f"        $dumpvars(0, {tb_name});",
    ]
    for idx, vector in enumerate(vectors):
        lines.append("")
        lines.append(f"        // vector {idx}")
        for port in ports:
            if str(port.get("direction") or "").lower() != "input":
                continue
            name = str(port["name"])
            value = vector.get(name, 1 if name.lower().endswith("_n") else 0)
            lines.append(f"        {name} = {_sv_literal(_port_width(port), value)};")
        lines.append("        #1;")
        for out_idx, output in enumerate(outputs):
            port = _ident(output.get("port") or output.get("name") or f"output_{out_idx}")
            expr = str(output.get("expr") or "0").strip() or "0"
            case_name = f"vector_{idx}_{port}"
            lines.extend(
                [
                    "        tests = tests + 1;",
                    f"        if ({port} !== ({expr})) begin",
                    f"            $display(\"[FAIL] {case_name} actual=%0h expected=%0h\", {port}, ({expr}));",
                    "            fail = fail + 1;",
                    "        end else begin",
                    f"            $display(\"[PASS] {case_name} actual=%0h\", {port});",
                    "            pass = pass + 1;",
                    "        end",
                ]
            )
    lines.extend(
        [
            "",
            "        $display(\"TESTS=%0d PASS=%0d FAIL=%0d\", tests, pass, fail);",
            "        if (fail != 0) begin",
            "            $fatal(1, \"[FAIL] starter sim\");",
            "        end",
            "        $display(\"[PASS] starter sim\");",
            "        $finish;",
            "    end",
            "endmodule",
            "",
        ]
    )
    return "\n".join(lines), len(vectors) * max(len(outputs), 1)


def _hier_state_expr(expr: object, state_names: set[str]) -> str:
    text = str(expr or "0").strip() or "0"
    for name in sorted(state_names, key=len, reverse=True):
        text = re.sub(rf"(?<![.$\w]){re.escape(name)}(?![$\w])", f"dut.{name}", text)
    return text


def _tb_source_sequential(ip: str, top: str, ports: list[dict[str, Any]], contract: dict[str, Any]) -> tuple[str, int]:
    tb_name = f"tb_{ip}"
    outputs = [item for item in contract.get("outputs") or [] if isinstance(item, dict)]
    state_vars = contract.get("state_vars") if isinstance(contract.get("state_vars"), dict) else {}
    state_names = {_ident(name) for name in state_vars}
    clock = _ident(contract.get("clock") or "clk")
    reset = _ident(contract.get("reset") or "rst_n")
    reset_active = str(contract.get("reset_active") or ("low" if reset.endswith("_n") else "high")).lower()
    reset_assert = "1'b0" if reset_active == "low" else "1'b1"
    reset_release = "1'b1" if reset_active == "low" else "1'b0"
    vectors = _stimulus_vectors(ports)
    declarations: list[str] = []
    init_lines: list[str] = []
    connections: list[str] = []
    for idx, port in enumerate(ports):
        name = str(port["name"])
        direction = str(port.get("direction") or "input").lower()
        kind = "logic" if direction == "input" else "wire"
        declarations.append(f"    {kind} {_sv_range(_port_width(port))}{name};")
        if direction == "input":
            init_lines.append(f"        {name} = {_sv_literal(_port_width(port), 0)};")
        suffix = "," if idx < len(ports) - 1 else ""
        connections.append(f"        .{name}({name}){suffix}")

    lines: list[str] = [
        "`timescale 1ns/1ps",
        f"module {tb_name};",
        "    integer tests;",
        "    integer pass;",
        "    integer fail;",
        *declarations,
        "",
        f"    {top} dut (",
        *connections,
        "    );",
        "",
        f"    initial {clock} = 1'b0;",
        f"    always #5 {clock} = ~{clock};",
        "",
        "    initial begin",
        "        tests = 0;",
        "        pass = 0;",
        "        fail = 0;",
        f"        $dumpfile(\"sim/{ip}.vcd\");",
        f"        $dumpvars(0, {tb_name});",
        *init_lines,
        f"        {reset} = {reset_assert};",
        "        repeat (2) @(posedge " + clock + ");",
        "        @(negedge " + clock + ");",
        f"        {reset} = {reset_release};",
    ]
    for idx, vector in enumerate(vectors):
        lines.append("")
        lines.append(f"        // sequential vector {idx}")
        lines.append(f"        @(negedge {clock});")
        for port in ports:
            if str(port.get("direction") or "").lower() != "input":
                continue
            name = str(port["name"])
            if name == clock:
                continue
            if name == reset:
                lines.append(f"        {name} = {reset_release};")
                continue
            value = vector.get(name, 1 if name.lower().endswith("_n") else 0)
            lines.append(f"        {name} = {_sv_literal(_port_width(port), value)};")
        lines.append(f"        @(posedge {clock});")
        lines.append("        #1;")
        for out_idx, output in enumerate(outputs):
            port = _ident(output.get("port") or output.get("name") or f"output_{out_idx}")
            expr = _hier_state_expr(output.get("expr") or "0", state_names)
            case_name = f"seq_vector_{idx}_{port}"
            lines.extend(
                [
                    "        tests = tests + 1;",
                    f"        if ({port} !== ({expr})) begin",
                    f"            $display(\"[FAIL] {case_name} actual=%0h expected=%0h\", {port}, ({expr}));",
                    "            fail = fail + 1;",
                    "        end else begin",
                    f"            $display(\"[PASS] {case_name} actual=%0h\", {port});",
                    "            pass = pass + 1;",
                    "        end",
                ]
            )
    lines.extend(
        [
            "",
            "        $display(\"TESTS=%0d PASS=%0d FAIL=%0d\", tests, pass, fail);",
            "        if (fail != 0) begin",
            "            $fatal(1, \"[FAIL] starter sim\");",
            "        end",
            "        $display(\"[PASS] starter sim\");",
            "        $finish;",
            "    end",
            "endmodule",
            "",
        ]
    )
    return "\n".join(lines), len(vectors) * max(len(outputs), 1)


def _write_results_xml(path: Path, tests: int, failures: int, errors: int) -> None:
    suite = ET.Element(
        "testsuite",
        {
            "name": "starter_preview_sim",
            "tests": str(tests),
            "failures": str(failures),
            "errors": str(errors),
            "skipped": "0",
        },
    )
    for idx in range(max(tests, 1)):
        case = ET.SubElement(suite, "testcase", {"classname": "starter_preview_sim", "name": f"check_{idx}"})
        if failures and idx == 0:
            ET.SubElement(case, "failure", {"message": "starter sim mismatch"}).text = "See sim/sim_report.txt"
        if errors and idx == 0:
            ET.SubElement(case, "error", {"message": "starter simulator error"}).text = "See sim/sim_report.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(suite).write(path, encoding="utf-8", xml_declaration=True)


def _write_report(path: Path, payload: dict[str, Any], stdout: str, stderr: str) -> None:
    status = payload["status"]
    lines = [
        f"Starter simulation: {status}",
        f"Timestamp: {payload['timestamp']}",
        f"IP: {payload['ip']}",
        f"Top: {payload['top']}",
        f"Command: {' '.join(payload['command'])}",
        f"Tests: {payload['tests']} PASS={payload['pass']} FAIL={payload['fail']}",
        f"Errors: {payload['errors']}",
        "0 errors, 0 warnings" if status == "PASS" else "Simulation failed",
        "",
        "stdout:",
        stdout,
        "",
        "stderr:",
        stderr,
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(ip: str, root: Path) -> dict[str, Any]:
    ip_dir = root / ip
    ssot = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    contract_path = ip_dir / "rtl" / "rtl_contract.json"
    if not ssot.is_file():
        raise SystemExit(f"[starter_preview_sim] missing {ssot}")
    if not contract_path.is_file():
        raise SystemExit("[starter_preview_sim] missing rtl/rtl_contract.json; run ssot_to_rtl.py --mode starter first")
    if not shutil.which("iverilog") or not shutil.which("vvp"):
        raise SystemExit("[starter_preview_sim] missing simulator: require iverilog and vvp")

    doc = yaml.safe_load(ssot.read_text(encoding="utf-8")) or {}
    if not isinstance(doc, dict):
        raise SystemExit("[starter_preview_sim] SSOT top-level must be mapping")
    contract_doc = _load_json(contract_path)
    contract_type = str(contract_doc.get("type") or "")
    if contract_type not in {
        "starter_llm_rtl_authoring_contract",
    }:
        raise SystemExit("[starter_preview_sim] rtl_contract.json is not a Starter LLM authoring contract")
    contract = contract_doc.get("contract") if isinstance(contract_doc.get("contract"), dict) else {}
    top = _top_name(doc, ip)
    ports = _io_ports(doc)
    if not ports:
        raise SystemExit("[starter_preview_sim] SSOT io_list has no concrete ports")
    if not contract.get("outputs"):
        raise SystemExit("[starter_preview_sim] Starter contract has no output checks")

    tb_dir = ip_dir / "tb"
    sim_dir = ip_dir / "sim"
    tb_dir.mkdir(parents=True, exist_ok=True)
    sim_dir.mkdir(parents=True, exist_ok=True)
    has_sequential_contract = bool(contract.get("state_vars") or contract.get("state_updates") or contract.get("clock"))
    if contract_type == "starter_llm_rtl_authoring_contract" and has_sequential_contract:
        tb_source, planned_tests = _tb_source_sequential(ip, top, ports, contract)
    else:
        tb_source, planned_tests = _tb_source(ip, top, ports, contract)
    tb_path = tb_dir / f"tb_{ip}.sv"
    tb_path.write_text(tb_source, encoding="utf-8")
    out_path = sim_dir / f"{ip}.out"
    command = [
        "iverilog",
        "-g2012",
        "-Wall",
        "-s",
        f"tb_{ip}",
        "-o",
        str(out_path.relative_to(ip_dir)),
        "-f",
        f"list/{ip}.f",
        str(tb_path.relative_to(ip_dir)),
    ]
    compile_proc = subprocess.run(
        command,
        cwd=ip_dir,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )
    stdout = compile_proc.stdout or ""
    stderr = compile_proc.stderr or ""
    run_stdout = ""
    run_stderr = ""
    returncode = compile_proc.returncode
    if compile_proc.returncode == 0:
        run_proc = subprocess.run(
            ["vvp", str(out_path.relative_to(ip_dir))],
            cwd=ip_dir,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
        )
        run_stdout = run_proc.stdout or ""
        run_stderr = run_proc.stderr or ""
        returncode = run_proc.returncode
    combined = "\n".join([stdout, stderr, run_stdout, run_stderr])
    match = re.search(r"TESTS=(\d+)\s+PASS=(\d+)\s+FAIL=(\d+)", combined)
    tests = int(match.group(1)) if match else planned_tests
    passed = int(match.group(2)) if match else 0
    failed = int(match.group(3)) if match else (tests if returncode else 0)
    errors = 0 if returncode == 0 and failed == 0 else 1
    status = "PASS" if returncode == 0 and failed == 0 and tests > 0 else "FAIL"
    payload = {
        "schema_version": 1,
        "type": "starter_preview_sim",
        "ip": ip,
        "top": top,
        "status": status,
        "timestamp": _utc(),
        "command": command,
        "run_command": ["vvp", str(out_path.relative_to(ip_dir))],
        "tests": tests,
        "pass": passed,
        "fail": failed,
        "errors": errors,
        "returncode": returncode,
        "tb": str(tb_path.relative_to(ip_dir)),
        "binary": str(out_path.relative_to(ip_dir)),
        "stdout": run_stdout,
        "stderr": stderr + run_stderr,
    }
    (sim_dir / "starter_preview_sim.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _write_results_xml(sim_dir / "results.xml", tests, failed, errors)
    _write_report(sim_dir / "sim_report.txt", payload, run_stdout or stdout, stderr + run_stderr)
    return payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ip")
    ap.add_argument("--root", default=".")
    ns = ap.parse_args()
    payload = run(ns.ip, Path(ns.root).resolve())
    print(
        "[starter_preview_sim] "
        f"{ns.ip}: status={payload['status']} tests={payload['tests']} "
        f"pass={payload['pass']} fail={payload['fail']} errors={payload['errors']}"
    )
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
