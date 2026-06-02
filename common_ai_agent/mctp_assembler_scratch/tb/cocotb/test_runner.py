from __future__ import annotations

import json
import os
import shutil
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from cocotb_test.simulator import run


def _ip_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def _manifest() -> dict[str, Any]:
    return json.loads((_ip_dir() / "tb" / "cocotb" / "tb_manifest.json").read_text(encoding="utf-8"))


def _copy_waveforms(build_dir: Path, sim_dir: Path, ip: str) -> list[Path]:
    copied = []
    for path in sorted(list(build_dir.glob("*.fst")) + list(build_dir.glob("*.vcd"))):
        dst = sim_dir / f"{ip}{path.suffix}"
        shutil.copy2(path, dst)
        copied.append(dst)
    return copied


def _with_icarus_vcd_dump(sources: list[str], build_dir: Path, top: str, ip: str) -> tuple[list[str], list[str]]:
    """Create an Icarus-only VCD dump helper without wrapping the DUT.

    Icarus/vvp has no Tcl wave-control layer. To keep Atlas' browser VCD
    viewer source-traceable, dump the real RTL top scope directly and add the
    helper as a second top-level root that the UI can ignore.
    """
    dump_module = "atlas_iverilog_vcd_dump"
    dump_src = build_dir / f"{dump_module}.v"
    dump_src.write_text(
        f"module {dump_module}();\n"
        "initial begin\n"
        f"  $dumpfile(\"{ip}.vcd\");\n"
        f"  $dumpvars(0, {top});\n"
        "end\n"
        "endmodule\n",
        encoding="utf-8",
    )
    return [*sources, str(dump_src)], [top, dump_module]


def _verilator_compile_args(simulator: str) -> list[str]:
    if simulator != "verilator":
        return []
    enabled = os.environ.get("ATLAS_VERILATOR_COVERAGE", "1").strip().lower()
    if enabled in {"0", "false", "no", "off"}:
        return []
    return [
        "--coverage",
        "--coverage-line",
        "--coverage-expr",
        "--coverage-toggle",
    ]


def _parse_results(path: Path) -> tuple[int, int, int]:
    root = ET.parse(path).getroot()
    tests = failures = errors = 0
    suites = [root, *root.findall(".//testsuite")]
    for node in suites:
        tests += int(float(node.attrib.get("tests", 0) or 0))
        failures += int(float(node.attrib.get("failures", 0) or 0))
        errors += int(float(node.attrib.get("errors", 0) or 0))
    if tests == 0:
        cases = root.findall(".//testcase")
        tests = len(cases)
        failures = sum(1 for case in cases if case.find("failure") is not None)
        errors = sum(1 for case in cases if case.find("error") is not None)
    return tests, failures, errors


def _scoreboard_escalations(path: Path) -> list[str]:
    if not path.is_file():
        return []
    failed = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except Exception as exc:
            failed.append(("PARSE_ERROR", f"scoreboard_events.jsonl parse error: {exc}"))
            continue
        if isinstance(row, dict) and row.get("passed") is False:
            failed.append((str(row.get("goal_id") or "UNKNOWN"), str(row.get("mismatch") or "mismatch without detail")))
    if not failed:
        return []
    preview = "; ".join(f"{goal}: {mismatch}" for goal, mismatch in failed[:8])
    suffix = "" if len(failed) <= 8 else f"; ... +{len(failed) - 8} more"
    return [
        f"[SIM ESCALATE] scoreboard_failed={len(failed)} owner=sim_debug evidence={path}",
        f"[SIM ESCALATE] reason=FL-vs-RTL scoreboard mismatch: {preview}{suffix}",
    ]


def _write_scenario_e2e_summary(ip_dir: Path, sim_dir: Path) -> None:
    goals_path = ip_dir / "verify" / "equivalence_goals.json"
    manifest_path = ip_dir / "tc" / "scenario_manifest.json"
    scoreboard_path = sim_dir / "scoreboard_events.jsonl"
    out_path = sim_dir / "scenario_e2e_summary.json"

    issues: list[str] = []
    if not goals_path.is_file():
        issues.append(f"missing {goals_path}")
    if not manifest_path.is_file():
        issues.append(f"missing {manifest_path}")
    if not scoreboard_path.is_file():
        issues.append(f"missing {scoreboard_path}")

    scenario_ids: list[str] = []
    rows_by_goal: dict[str, dict[str, Any]] = {}
    if not issues:
        manifest_doc = json.loads(manifest_path.read_text(encoding="utf-8"))
        raw_scenarios = manifest_doc.get("scenarios")
        if not isinstance(raw_scenarios, list):
            issues.append("scenario_manifest.json scenarios[] missing")
        else:
            for scenario in raw_scenarios:
                if isinstance(scenario, dict) and scenario.get("scenario_id"):
                    scenario_ids.append(str(scenario["scenario_id"]))

        goals_doc = json.loads(goals_path.read_text(encoding="utf-8"))
        raw_goals = goals_doc.get("goals")
        if not isinstance(raw_goals, list):
            issues.append("equivalence_goals.json goals[] missing")
        else:
            goal_ids = {
                str(goal.get("goal_id") or "")
                for goal in raw_goals
                if isinstance(goal, dict)
            }
            missing_goals = [f"EQ_SCENARIO_{scenario_id}" for scenario_id in scenario_ids if f"EQ_SCENARIO_{scenario_id}" not in goal_ids]
            issues.extend(f"missing directed goal for {goal_id}" for goal_id in missing_goals)

        for raw in scoreboard_path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(row, dict):
                continue
            goal_id = str(row.get("goal_id") or "")
            if goal_id.startswith("EQ_SCENARIO_") and goal_id not in rows_by_goal:
                rows_by_goal[goal_id] = row

    scenarios: list[dict[str, object]] = []
    missing_scenarios: list[str] = []
    failed_scenarios: list[str] = []
    for scenario_key in scenario_ids:
        goal_id = f"EQ_SCENARIO_{scenario_key}"
        row = rows_by_goal.get(goal_id, {})
        rtl_observed = row.get("rtl_observed")
        scoreboard_passed = row.get("passed") is True
        dut_observed = isinstance(rtl_observed, dict) and bool(rtl_observed)
        scoreboard_scenario_id = str(row.get("scenario_id") or "")
        rtl_observable_count = len(rtl_observed) if isinstance(rtl_observed, dict) else 0
        if not row:
            issues.append(f"missing scoreboard row for {goal_id}")
            missing_scenarios.append(scenario_key)
        elif not scoreboard_scenario_id:
            issues.append(f"missing scenario_id for {goal_id}")
            failed_scenarios.append(scenario_key)
        elif not scoreboard_passed:
            issues.append(f"scoreboard failed for {goal_id}")
            failed_scenarios.append(scenario_key)
        elif not dut_observed:
            issues.append(f"dut_observed missing for {goal_id}")
            failed_scenarios.append(scenario_key)
        scenarios.append(
            {
                "goal_id": goal_id,
                "scenario_id": scenario_key,
                "scoreboard_scenario_id": scoreboard_scenario_id,
                "scoreboard_passed": scoreboard_passed,
                "dut_observed": dut_observed,
                "rtl_observable_count": rtl_observable_count,
                "cycle": row.get("cycle"),
                "coverage_refs": row.get("coverage_refs") if isinstance(row.get("coverage_refs"), list) else [],
            }
        )

    unique_scenario_ids = {entry["scenario_id"] for entry in scenarios if isinstance(entry.get("scenario_id"), str) and entry["scenario_id"]}
    if len(scenario_ids) != 26:
        issues.append(f"expected 26 scenario manifest entries, found {len(scenario_ids)}")
    if len(scenarios) != 26:
        issues.append(f"expected 26 directed scenario rows, found {len(scenarios)}")
    if len(unique_scenario_ids) != 26:
        issues.append(f"expected 26 unique scenario_id values, found {len(unique_scenario_ids)}")

    payload = {
        "schema_version": 1,
        "type": "scenario_e2e_summary",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "pass" if not issues else "fail",
        "total_directed_scenarios": len(scenarios),
        "observed_directed_scenarios": len(rows_by_goal),
        "missing_scenarios": missing_scenarios,
        "failed_scenarios": failed_scenarios,
        "scenarios": scenarios,
        "issues": issues,
        "source_artifacts": {
            "equivalence_goals": str(goals_path.relative_to(ip_dir.parent)),
            "scenario_manifest": str(manifest_path.relative_to(ip_dir.parent)),
            "scoreboard_events": str(scoreboard_path.relative_to(ip_dir.parent)),
        },
    }
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    ip_dir = _ip_dir()
    project_root = ip_dir.parent
    manifest = _manifest()
    ip = manifest["ip"]
    tb_dir = ip_dir / "tb" / "cocotb"
    sim_dir = ip_dir / "sim"
    sim_dir.mkdir(parents=True, exist_ok=True)
    build_dir = sim_dir / "cocotb_build"
    build_dir.mkdir(parents=True, exist_ok=True)

    common_root = Path(os.environ.get("COMMON_AI_AGENT_ROOT") or manifest["common_ai_agent_root"]).resolve()
    runtime_dir = common_root / "workflow" / "tb-gen" / "runtime"
    sources = [str(Path(src).resolve()) for src in manifest.get("rtl_sources") or []]
    if not sources:
        (sim_dir / "sim_report.txt").write_text("TESTS=0 PASS=0 FAIL=1\nno RTL sources\n", encoding="utf-8")
        print("TESTS=0 PASS=0 FAIL=1")
        print("no RTL sources")
        return 1

    env = {
        "IP_NAME": ip,
        "PROJECT_ROOT": str(project_root),
        "COMMON_AI_AGENT_ROOT": str(common_root),
        "PYTHONUNBUFFERED": "1",
    }
    os.environ.pop("COCOTB_RESULTS_FILE", None)
    try:
        simulator = os.environ.get("SIM", "icarus")
        run_sources = sources
        run_top = manifest["top"]
        waves = True
        if simulator == "icarus":
            run_sources, run_top = _with_icarus_vcd_dump(sources, build_dir, manifest["top"], ip)
            waves = False
        test_modules = f"test_{ip},test_mctp_payload_datapath"
        results_file = run(
            simulator=simulator,
            verilog_sources=run_sources,
            toplevel=run_top,
            module=test_modules,
            python_search=[str(tb_dir), str(runtime_dir)],
            sim_build=str(build_dir),
            timescale="1ns/1ps",
            waves=waves,
            force_compile=True,
            extra_env=env,
            includes=[str(ip_dir / "rtl")],
            verilog_compile_args=_verilator_compile_args(simulator),
        )
    except BaseException as exc:
        (sim_dir / "sim_report.txt").write_text(
            f"TESTS=1 PASS=0 FAIL=1\nSimulation exception: {exc}\n",
            encoding="utf-8",
        )
        print("TESTS=1 PASS=0 FAIL=1")
        print(f"Simulation exception: {exc}")
        return 1

    canonical = sim_dir / "results.xml"
    shutil.copy2(results_file, canonical)
    shutil.copy2(results_file, tb_dir / "results.xml")
    waves = _copy_waveforms(build_dir, sim_dir, ip)
    tests, failures, errors = _parse_results(canonical)
    passed = tests - failures - errors
    escalations = _scoreboard_escalations(sim_dir / "scoreboard_events.jsonl")
    report = [
        f"TESTS={tests} PASS={passed} FAIL={failures + errors}",
        f"results={canonical.relative_to(project_root)}",
        f"scoreboard={ip}/sim/scoreboard_events.jsonl",
        f"coverage_functional={ip}/cov/coverage_functional.json",
        f"waveforms={','.join(str(path.relative_to(project_root)) for path in waves) if waves else 'none'}",
        "0 errors, 0 warnings" if failures == 0 and errors == 0 else f"{errors} errors, {failures} failures",
    ]
    report.extend(escalations)
    (sim_dir / "sim_report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    _write_scenario_e2e_summary(ip_dir, sim_dir)
    print(f"TESTS={tests} PASS={passed} FAIL={failures + errors}")
    print("0 errors, 0 warnings" if failures == 0 and errors == 0 else f"{errors} errors, {failures} failures")
    for line in escalations:
        print(line)
    return 0 if failures == 0 and errors == 0 and tests > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
