#!/usr/bin/env python3
"""
pyslang + scapy Integrated Verification Runner
================================================
Master script that orchestrates ALL analysis stages:

  Step 1: pyslang RTL Parsing          (pyslang_analyze.py)
  Step 2: Static Analysis              (static_analysis.py)
  Step 3: Timing Path Analysis         (timing_analysis.py)
  Step 4: RTL vs RefModel Cross-check  (verify_rtl_vs_refmodel.py)
  Step 5: scapy Frame Encap/Decap      (scapy_counter_frame.py)
  Step 6: scapy Packet Verification    (scapy_packet_verify.py)
  Step 7: scapy Integrity Verification (scapy_integrity.py)

Collects exit-codes, JSON results and produces a unified report.

Usage:
    python3 analysis/run_all_analysis.py [--json] [--markdown] [--width 8]
"""

import sys
import os
import json
import time
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# ── Paths ──────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
REPORT_DIR   = SCRIPT_DIR / "reports"

# ── Analysis stages (script name, display label) ───────────────────────
STAGES = [
    {
        "id":       "pyslang",
        "script":   "pyslang_analyze.py",
        "label":    "Step 1/7: pyslang RTL Parsing",
        "extra_args": ["--rtl"],
    },
    {
        "id":       "static",
        "script":   "static_analysis.py",
        "label":    "Step 2/7: Static Analysis",
        "extra_args": ["--rtl"],
    },
    {
        "id":       "timing",
        "script":   "timing_analysis.py",
        "label":    "Step 3/7: Timing Path Analysis",
        "extra_args": ["--rtl"],
    },
    {
        "id":       "xref",
        "script":   "verify_rtl_vs_refmodel.py",
        "label":    "Step 4/7: RTL vs RefModel Cross-check",
        "extra_args": [],
    },
    {
        "id":       "frame",
        "script":   "scapy_counter_frame.py",
        "label":    "Step 5/7: scapy Frame Encap/Decap",
        "extra_args": [],
    },
    {
        "id":       "packet",
        "script":   "scapy_packet_verify.py",
        "label":    "Step 6/7: scapy Packet Verification",
        "extra_args": [],
    },
    {
        "id":       "integrity",
        "script":   "scapy_integrity.py",
        "label":    "Step 7/7: scapy Integrity Verification",
        "extra_args": [],
    },
]


# ======================================================================
# Runner
# ======================================================================

def run_stage(stage: dict, rtl_path: str, width: int) -> dict:
    """Execute a single analysis stage as a subprocess.

    Returns dict with:
        id, label, exit_code, elapsed_s, json_data (or None), stdout, stderr
    """
    script_path = SCRIPT_DIR / stage["script"]
    if not script_path.exists():
        return {
            "id": stage["id"],
            "label": stage["label"],
            "exit_code": -1,
            "elapsed_s": 0,
            "json_data": None,
            "stdout": "",
            "stderr": f"Script not found: {script_path}",
        }

    cmd = [sys.executable, str(script_path), "--json", "--markdown"]
    if "--rtl" in stage["extra_args"]:
        cmd += ["--rtl", rtl_path]
    if stage["id"] in ("frame", "packet", "integrity"):
        cmd += ["--width", str(width)]

    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        elapsed = time.time() - t0
        return {
            "id": stage["id"],
            "label": stage["label"],
            "exit_code": -2,
            "elapsed_s": round(elapsed, 2),
            "json_data": None,
            "stdout": "",
            "stderr": "TIMEOUT (120s)",
        }
    elapsed = time.time() - t0

    # Load JSON report if produced
    json_data = None
    json_path = REPORT_DIR / f"{stage['id']}_report.json"
    # Map stage id → actual report filenames
    json_name_map = {
        "pyslang":   "pyslang_analysis.json",
        "static":    "static_analysis.json",
        "timing":    "timing_analysis.json",
        "xref":      "xref_verification.json",
        "frame":     "scapy_counter_frame.json",
        "packet":    "scapy_packet_verify.json",
        "integrity": "scapy_integrity.json",
    }
    actual_json = REPORT_DIR / json_name_map.get(stage["id"], f"{stage['id']}.json")
    if actual_json.exists():
        try:
            with open(actual_json) as f:
                json_data = json.load(f)
        except json.JSONDecodeError:
            json_data = None

    return {
        "id": stage["id"],
        "label": stage["label"],
        "exit_code": proc.returncode,
        "elapsed_s": round(elapsed, 2),
        "json_data": json_data,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


# ======================================================================
# Summary Extraction
# ======================================================================

def extract_summary(stage_result: dict) -> dict:
    """Extract a concise pass/fail summary from each stage's JSON data."""
    sid = stage_result["id"]
    jd  = stage_result["json_data"]
    info = {"id": sid, "exit_code": stage_result["exit_code"]}

    if stage_result["exit_code"] == -1:
        info["status"] = "MISSING"
        info["detail"] = "Script not found"
        return info
    if stage_result["exit_code"] == -2:
        info["status"] = "TIMEOUT"
        info["detail"] = "Exceeded 120s"
        return info
    if jd is None:
        info["status"] = "PASS" if stage_result["exit_code"] == 0 else "FAIL"
        info["detail"] = "No JSON data"
        return info

    # ── Per-stage summary extraction ──
    if sid == "pyslang":
        info["status"] = "PASS" if stage_result["exit_code"] == 0 else "FAIL"
        # pyslang JSON is {"counter": {"metadata": {...}, "ports": [...], ...}}
        mod_data = jd.get("counter", jd)
        meta = mod_data.get("metadata", {})
        ports = mod_data.get("ports", [])
        params = mod_data.get("parameters", [])
        info["detail"] = (f"module={meta.get('module_name','?')} "
                          f"ports={len(ports)} params={len(params)}")

    elif sid == "static":
        s = jd.get("summary", {})
        crit = s.get("critical", "?")
        warn = s.get("warning", "?")
        info["status"] = "PASS" if stage_result["exit_code"] == 0 else "FAIL"
        info["detail"] = f"critical={crit} warnings={warn}"

    elif sid == "timing":
        n_warn = len(jd.get("warnings", []))
        info["status"] = "PASS" if stage_result["exit_code"] == 0 else "FAIL"
        info["detail"] = f"timing_warnings={n_warn}"

    elif sid == "xref":
        results_list = jd if isinstance(jd, list) else jd.get("results", [])
        total = len(results_list)
        passed = sum(1 for r in results_list if r.get("status") == "PASS")
        info["status"] = "PASS" if stage_result["exit_code"] == 0 else "FAIL"
        info["detail"] = f"checks={total} passed={passed}"

    elif sid in ("frame", "packet", "integrity"):
        s = jd.get("summary", {})
        tp = s.get("total_passed", "?")
        tf = s.get("total_failed", "?")
        info["status"] = "PASS" if stage_result["exit_code"] == 0 else "FAIL"
        info["detail"] = f"tests={tp}+{tf} (pass+fail)"

    else:
        info["status"] = "PASS" if stage_result["exit_code"] == 0 else "FAIL"
        info["detail"] = f"exit={stage_result['exit_code']}"

    return info


# ======================================================================
# Report Generators
# ======================================================================

def print_console_report(stages: list, summaries: list):
    """Print unified console summary."""
    print("\n" + "=" * 76)
    print("  INTEGRATED VERIFICATION REPORT — counter")
    print("=" * 76)
    print(f"  Timestamp : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Stages    : {len(stages)}")

    total_time = sum(s["elapsed_s"] for s in stages)
    print(f"  Total time: {total_time:.2f}s")

    print(f"\n  ┌─────┬───────────────────────────────────────────┬──────┬───────┬────────────────────────────┐")
    print(f"  │  #  │ Stage                                     │ Exit │ Time  │ Detail                     │")
    print(f"  ├─────┼───────────────────────────────────────────┼──────┼───────┼────────────────────────────┤")

    for i, (stg, sm) in enumerate(zip(stages, summaries), 1):
        icon = "✅" if sm["status"] == "PASS" else "❌"
        label = stg["label"]
        detail = sm.get("detail", "")[:28]
        print(f"  │  {i}  │ {icon} {label:<40s} │ {stg['exit_code']:>4} │ {stg['elapsed_s']:>5.2f}s │ {detail:<28s} │")

    print(f"  ├─────┼───────────────────────────────────────────┼──────┼───────┼────────────────────────────┤")

    n_pass = sum(1 for s in summaries if s["status"] == "PASS")
    n_fail = len(summaries) - n_pass
    overall = "✅ ALL PASS" if n_fail == 0 else f"❌ {n_fail} FAILED"
    print(f"  │     │ TOTAL  ({n_pass}/{len(summaries)} passed)                    │      │ {total_time:>5.2f}s │ {overall:<28s} │")
    print(f"  └─────┴───────────────────────────────────────────┴──────┴───────┴────────────────────────────┘")

    if n_fail == 0:
        print(f"\n  ✅ VERDICT: All {len(summaries)} analysis stages PASSED.\n")
    else:
        print(f"\n  ❌ VERDICT: {n_fail} stage(s) FAILED.\n")
        for sm in summaries:
            if sm["status"] != "PASS":
                print(f"     • {sm['id']}: {sm.get('detail', 'see log above')}")


def generate_markdown_report(stages: list, summaries: list) -> str:
    """Generate unified Markdown report."""
    n_pass = sum(1 for s in summaries if s["status"] == "PASS")
    n_fail = len(summaries) - n_pass
    total_time = sum(s["elapsed_s"] for s in stages)

    lines = [
        "# Integrated Verification Report — counter\n",
        f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
        f"**Total stages**: {len(stages)}  ",
        f"**Total time**: {total_time:.2f}s\n",
        "## Stage Summary\n",
        "| # | Stage | Status | Exit | Time | Detail |",
        "|---|-------|--------|------|------|--------|",
    ]

    for i, (stg, sm) in enumerate(zip(stages, summaries), 1):
        icon = "✅ PASS" if sm["status"] == "PASS" else "❌ FAIL"
        detail = sm.get("detail", "")
        lines.append(
            f"| {i} | {stg['label']} | {icon} | {stg['exit_code']} | "
            f"{stg['elapsed_s']:.2f}s | {detail} |"
        )

    overall = "✅ ALL PASS" if n_fail == 0 else f"❌ {n_fail} FAILED"
    lines.extend([
        f"| | **TOTAL** ({n_pass}/{len(summaries)}) | **{overall}** | | "
        f"**{total_time:.2f}s** | |\n",
    ])

    # ── Per-stage detail sections ──
    for stg in stages:
        jd = stg["json_data"]
        if jd is None:
            continue
        lines.append(f"## {stg['label']} — Detail\n")

        if stg["id"] == "pyslang" and isinstance(jd, dict):
            mod_data = jd.get("counter", jd)
            meta = mod_data.get("metadata", {})
            ports = mod_data.get("ports", [])
            params = mod_data.get("parameters", [])
            always_blocks = mod_data.get("always_blocks", [])
            lines.append(f"- Module: `{meta.get('module_name', '?')}`")
            lines.append(f"- Ports: {len(ports)}")
            lines.append(f"- Parameters: {len(params)}")
            lines.append(f"- Always blocks: {len(always_blocks)}\n")

        elif stg["id"] == "static" and isinstance(jd, dict):
            s = jd.get("summary", {})
            lines.append(f"- Critical: {s.get('critical', '?')}")
            lines.append(f"- Warnings: {s.get('warning', '?')}")
            lines.append(f"- Info: {s.get('info', '?')}\n")

        elif stg["id"] == "timing" and isinstance(jd, dict):
            lines.append(f"- Timing warnings: {len(jd.get('warnings', []))}")
            lines.append(f"- Paths analyzed: {jd.get('total_paths', '?')}\n")

        elif stg["id"] == "xref":
            results_list = jd if isinstance(jd, list) else jd.get("results", [])
            lines.append("| Check | Status | Detail |")
            lines.append("|-------|--------|--------|")
            for r in results_list:
                st = "✅" if r.get("status") == "PASS" else "❌"
                lines.append(f"| {r.get('check','?')} | {st} | {r.get('detail','')} |")
            lines.append("")

        elif stg["id"] in ("frame", "packet", "integrity") and isinstance(jd, dict):
            s = jd.get("summary", {})
            lines.append(f"- Total tests: {s.get('total_tests', '?')}")
            lines.append(f"- Passed: {s.get('total_passed', '?')}")
            lines.append(f"- Failed: {s.get('total_failed', '?')}\n")

    if n_fail == 0:
        lines.append(
            f"> ✅ **All {len(summaries)} stages passed.** "
            "Counter module is verified via pyslang RTL parsing, static/timing "
            "analysis, refmodel cross-check, and scapy packet integrity.\n"
        )

    return "\n".join(lines)


# ======================================================================
# Main
# ======================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Integrated pyslang + scapy verification for counter.v")
    parser.add_argument("--rtl", default=str(PROJECT_ROOT / "counter.v"),
                        help="Path to counter.v (default: auto-detect)")
    parser.add_argument("--width", type=int, default=8,
                        help="Counter WIDTH parameter (default: 8)")
    parser.add_argument("--json", action="store_true",
                        help="Save unified JSON report")
    parser.add_argument("--markdown", action="store_true",
                        help="Save unified Markdown report")
    args = parser.parse_args()

    if not os.path.exists(args.rtl):
        print(f"[ERROR] RTL file not found: {args.rtl}")
        sys.exit(1)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 76)
    print("  pyslang + scapy INTEGRATED VERIFICATION — counter")
    print("=" * 76)
    print(f"  RTL   : {args.rtl}")
    print(f"  WIDTH : {args.width}")
    print(f"  Stages: {len(STAGES)}")
    print()

    # ── Run each stage ──────────────────────────────────────────────
    stage_results = []
    for stage in STAGES:
        print(f"  ▶ {stage['label']} ...")
        result = run_stage(stage, args.rtl, args.width)
        stage_results.append(result)
        icon = "✅" if result["exit_code"] == 0 else "❌"
        print(f"    {icon} exit={result['exit_code']}  "
              f"time={result['elapsed_s']:.2f}s")
        # Show stdout last 10 lines for context
        if result["stdout"]:
            out_lines = result["stdout"].strip().splitlines()
            for line in out_lines[-6:]:
                if line.strip():
                    print(f"       {line.rstrip()}")
        if result["stderr"]:
            err_lines = result["stderr"].strip().splitlines()
            for line in err_lines[-3:]:
                if line.strip():
                    print(f"       ⚠ {line.rstrip()}")

    # ── Summaries ───────────────────────────────────────────────────
    summaries = [extract_summary(r) for r in stage_results]

    # ── Console report ──────────────────────────────────────────────
    print_console_report(stage_results, summaries)

    # ── Unified JSON ────────────────────────────────────────────────
    unified = {
        "module": "counter",
        "timestamp": datetime.now().isoformat(),
        "rtl_path": args.rtl,
        "width": args.width,
        "stages": summaries,
        "stage_details": [],
    }
    for r in stage_results:
        entry = {
            "id": r["id"],
            "label": r["label"],
            "exit_code": r["exit_code"],
            "elapsed_s": r["elapsed_s"],
        }
        # Include key JSON data
        jd = r["json_data"]
        if jd:
            if r["id"] in ("frame", "packet", "integrity"):
                entry["summary"] = jd.get("summary")
            elif r["id"] == "static":
                entry["summary"] = jd.get("summary")
            elif r["id"] == "timing":
                entry["warning_count"] = len(jd.get("warnings", []))
            elif r["id"] == "pyslang":
                mod_data = jd.get("counter", jd)
                meta = mod_data.get("metadata", {})
                entry["module_info"] = {
                    "module_name": meta.get("module_name", "?"),
                    "port_count": len(mod_data.get("ports", [])),
                    "param_count": len(mod_data.get("parameters", [])),
                    "always_block_count": len(mod_data.get("always_blocks", [])),
                }
            elif r["id"] == "xref":
                results_list = jd if isinstance(jd, list) else jd.get("results", [])
                entry["check_count"] = len(results_list)
                entry["check_pass"] = sum(
                    1 for x in results_list if x.get("status") == "PASS")
        unified["stage_details"].append(entry)

    n_pass = sum(1 for s in summaries if s["status"] == "PASS")
    unified["overall_pass"] = n_pass == len(summaries)

    if args.json:
        json_path = REPORT_DIR / "run_all_analysis.json"
        with open(json_path, 'w') as f:
            json.dump(unified, f, indent=2, default=str)
        print(f"[INFO] Unified JSON report: {json_path}")

    # ── Unified Markdown ────────────────────────────────────────────
    if args.markdown:
        md_text = generate_markdown_report(stage_results, summaries)
        md_path = REPORT_DIR / "run_all_analysis.md"
        with open(md_path, 'w') as f:
            f.write(md_text)
        print(f"[INFO] Unified Markdown report: {md_path}")

    sys.exit(0 if unified["overall_pass"] else 1)


if __name__ == "__main__":
    main()
