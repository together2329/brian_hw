#!/usr/bin/env python3
"""Lightweight post-simulation static signoff checks for real_llm_counter_demo.

This script is intentionally kept under verify/ (not rtl/) because it is a
verification artifact. It checks structural RTL properties that are required by
the SSOT/signoff scope and then runs available static tooling.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

IP = "real_llm_counter_demo"
REPO_ROOT = Path(__file__).resolve().parents[2]
IP_ROOT = REPO_ROOT / IP
RTL_PATH = IP_ROOT / "rtl" / "real_llm_counter_demo.sv"
FILELIST = IP_ROOT / "list" / "real_llm_counter_demo.f"
OUT_PATH = IP_ROOT / "verify" / "static_signoff_results.json"
BUILD_DIR = IP_ROOT / "verify" / "build"


def normalize(text: str) -> str:
    text = re.sub(r"//.*", "", text)
    return re.sub(r"\s+", " ", text)


def run_cmd(name: str, cmd: list[str], cwd: Path) -> dict:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return {
        "name": name,
        "available": True,
        "command": " ".join(cmd),
        "cwd": str(cwd),
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "passed": proc.returncode == 0,
    }


def static_check(name: str, description: str, passed: bool, evidence: list[str], refs: list[str]) -> dict:
    return {
        "name": name,
        "description": description,
        "passed": bool(passed),
        "evidence": evidence,
        "refs": refs,
    }


def main() -> int:
    if not RTL_PATH.exists():
        raise FileNotFoundError(RTL_PATH)
    rtl = RTL_PATH.read_text()
    compact = normalize(rtl)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    checks: list[dict] = []

    checks.append(static_check(
        "cmd_ready_always_high",
        "cmd_ready must be tied high for always-ready valid/ready protocol.",
        bool(re.search(r"assign\s+cmd_ready\s*=\s*1'b1\s*;", rtl)),
        ["assign cmd_ready = 1'b1"],
        ["io_list.interfaces.command_if.protocol.always_ready", "equivalence_goals.EQ_CMD_READY_ALWAYS"],
    ))

    reset_patterns = [
        ("count_reg <= SAT_MIN_VAL", r"count_reg\s*<=\s*SAT_MIN_VAL\s*;"),
        ("accepted_count_reg <= 32'd0", r"accepted_count_reg\s*<=\s*32'd0\s*;"),
        ("last_cmd_reg <= 3'd0", r"last_cmd_reg\s*<=\s*3'd0\s*;"),
        ("async reset sensitivity", r"always\s*@\s*\(\s*posedge\s+clk\s+or\s+negedge\s+rst_n\s*\)"),
        ("active-low reset branch", r"if\s*\(\s*!\s*rst_n\s*\)"),
    ]
    checks.append(static_check(
        "reset_contract",
        "Active-low reset must clear count/status/accepted_count.",
        all(re.search(pattern, rtl) for _, pattern in reset_patterns),
        [label for label, _ in reset_patterns],
        ["clock_reset_domains.reset_behavior", "equivalence_goals.EQ_RESET"],
    ))

    range_patterns = [
        ("WIDTH parameter is 8", r"parameter\s+integer\s+WIDTH\s*=\s*8"),
        ("count port is WIDTH bits", r"output\s+logic\s*\[\s*WIDTH\s*-\s*1\s*:\s*0\s*\]\s*count"),
        ("count_reg is WIDTH bits", r"logic\s*\[\s*WIDTH\s*-\s*1\s*:\s*0\s*\]\s*count_reg"),
        ("SAT_MAX_VAL is all ones", r"localparam\s*\[\s*WIDTH\s*-\s*1\s*:\s*0\s*\]\s*SAT_MAX_VAL\s*=\s*\{\s*WIDTH\s*\{\s*1'b1\s*\}\s*\}"),
        ("SAT_MIN_VAL is all zeros", r"localparam\s*\[\s*WIDTH\s*-\s*1\s*:\s*0\s*\]\s*SAT_MIN_VAL\s*=\s*\{\s*WIDTH\s*\{\s*1'b0\s*\}\s*\}"),
        ("count output driven by count_reg", r"assign\s+count\s*=\s*count_reg\s*;"),
    ]
    checks.append(static_check(
        "counter_range_is_width_limited",
        "Counter range must be constrained to the 8-bit SSOT width and saturation constants.",
        all(re.search(pattern, rtl) for _, pattern in range_patterns),
        [label for label, _ in range_patterns],
        ["parameters.WIDTH", "parameters.SAT_MIN", "parameters.SAT_MAX"],
    ))

    inc_sat = bool(re.search(
        r"CMD_INC\s*:\s*count_next\s*=\s*\(\s*count_reg\s*==\s*SAT_MAX_VAL\s*\)\s*\?\s*SAT_MAX_VAL\s*:\s*count_reg\s*\+\s*1'b1\s*;",
        compact,
    ))
    checks.append(static_check(
        "increment_saturates_at_max",
        "INC at SAT_MAX must hold SAT_MAX rather than wrap.",
        inc_sat,
        ["CMD_INC: count_next = (count_reg == SAT_MAX_VAL) ? SAT_MAX_VAL : count_reg + 1'b1"],
        ["features.F001", "equivalence_goals.EQ_INC_SATURATE"],
    ))

    dec_sat = bool(re.search(
        r"CMD_DEC\s*:\s*count_next\s*=\s*\(\s*count_reg\s*==\s*SAT_MIN_VAL\s*\)\s*\?\s*SAT_MIN_VAL\s*:\s*count_reg\s*-\s*1'b1\s*;",
        compact,
    ))
    checks.append(static_check(
        "decrement_saturates_at_min",
        "DEC at SAT_MIN must hold SAT_MIN rather than wrap.",
        dec_sat,
        ["CMD_DEC: count_next = (count_reg == SAT_MIN_VAL) ? SAT_MIN_VAL : count_reg - 1'b1"],
        ["features.F002", "equivalence_goals.EQ_DEC_SATURATE"],
    ))

    checks.append(static_check(
        "accepted_count_increments_on_accept",
        "When cmd_valid accepts a command, accepted_count_reg increments by one and wraps naturally at 32 bits.",
        bool(re.search(r"else\s+if\s*\(\s*cmd_valid\s*\).*accepted_count_reg\s*<=\s*accepted_count_reg\s*\+\s*32'd1\s*;", compact)),
        ["else if (cmd_valid) accepted_count_reg <= accepted_count_reg + 32'd1"],
        ["features.F008", "equivalence_goals.EQ_ACCEPTED_COUNT_WRAP"],
    ))

    checks.append(static_check(
        "flags_are_combinational_functions_of_count",
        "zero/max must be combinational functions of count_reg at SAT_MIN/SAT_MAX.",
        bool(re.search(r"assign\s+zero\s*=\s*\(\s*count_reg\s*==\s*SAT_MIN_VAL\s*\)\s*;", rtl))
        and bool(re.search(r"assign\s+max\s*=\s*\(\s*count_reg\s*==\s*SAT_MAX_VAL\s*\)\s*;", rtl)),
        ["assign zero = (count_reg == SAT_MIN_VAL)", "assign max = (count_reg == SAT_MAX_VAL)"],
        ["features.F007", "equivalence_goals.EQ_FLAGS"],
    ))

    tool_availability = {tool: shutil.which(tool) for tool in ["iverilog", "vvp", "verilator", "yosys", "sby", "svlint"]}
    tool_runs: list[dict] = []

    if tool_availability["iverilog"]:
        tool_runs.append(run_cmd(
            "post_sim_dut_compile_iverilog",
            [tool_availability["iverilog"], "-g2012", "-Irtl", "-s", "real_llm_counter_demo", "-o", "verify/build/postsim_dut_compile.vvp", "-f", "list/real_llm_counter_demo.f"],
            IP_ROOT,
        ))
    else:
        tool_runs.append({"name": "post_sim_dut_compile_iverilog", "available": False, "passed": False, "waiver": "iverilog unavailable"})

    if tool_availability["verilator"]:
        tool_runs.append(run_cmd(
            "post_sim_dut_lint_verilator",
            [tool_availability["verilator"], "--lint-only", "-Wall", "-Irtl", "-f", "list/real_llm_counter_demo.f", "--top-module", "real_llm_counter_demo"],
            IP_ROOT,
        ))
    else:
        tool_runs.append({"name": "post_sim_dut_lint_verilator", "available": False, "passed": False, "waiver": "verilator unavailable"})

    if tool_availability["yosys"]:
        yosys_script = "read_verilog -sv rtl/real_llm_counter_demo.sv; hierarchy -check -top real_llm_counter_demo; proc; opt; check -assert"
        tool_runs.append(run_cmd(
            "yosys_static_elaboration_check",
            [tool_availability["yosys"], "-q", "-p", yosys_script],
            IP_ROOT,
        ))
    else:
        tool_runs.append({"name": "yosys_static_elaboration_check", "available": False, "passed": False, "waiver": "yosys unavailable"})

    waivers = []
    if not tool_availability["sby"]:
        waivers.append({
            "item": "symbiyosys_full_formal_proof",
            "rationale": "sby/SymbiYosys is not installed in this environment; lightweight static property checks plus yosys elaboration, iverilog compile, verilator lint, and passing scoreboard simulation are used instead.",
            "scope": "optional formal only; no waiver for required simulation/lint/compile evidence",
        })
    if not tool_availability["svlint"]:
        waivers.append({
            "item": "svlint_style_check",
            "rationale": "svlint is not installed; verilator lint and existing pyslang/verilator DUT lint are used for available static lint coverage.",
            "scope": "optional extra lint tool only",
        })

    all_static_checks_passed = all(c["passed"] for c in checks)
    required_tool_runs = [r for r in tool_runs if r.get("available")]
    all_available_tools_passed = all(r.get("passed") for r in required_tool_runs)

    report = {
        "schema_version": 1,
        "ip": IP,
        "type": "post_sim_static_signoff_checks",
        "artifact_location_policy": "All check artifacts live under verify/ and .session/, not under synthesizable rtl/.",
        "rtl_under_check": str(RTL_PATH.relative_to(REPO_ROOT)),
        "filelist": str(FILELIST.relative_to(REPO_ROOT)),
        "checks": checks,
        "tool_availability": tool_availability,
        "tool_runs": tool_runs,
        "waivers": waivers,
        "summary": {
            "static_property_checks": len(checks),
            "static_property_failures": [c["name"] for c in checks if not c["passed"]],
            "all_static_properties_passed": all_static_checks_passed,
            "available_tool_runs": len(required_tool_runs),
            "available_tool_failures": [r["name"] for r in required_tool_runs if not r.get("passed")],
            "all_available_tools_passed": all_available_tools_passed,
            "post_sim_compile_clean": any(r["name"] == "post_sim_dut_compile_iverilog" and r.get("passed") for r in tool_runs),
            "post_sim_lint_clean": any(r["name"] == "post_sim_dut_lint_verilator" and r.get("passed") for r in tool_runs),
            "signoff_pass": all_static_checks_passed and all_available_tools_passed,
        },
    }

    OUT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["summary"], indent=2))
    return 0 if report["summary"]["signoff_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
