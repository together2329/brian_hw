from __future__ import annotations

import json
import os
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from cocotb_test.simulator import run


def _ip_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def _manifest() -> dict:
    return json.loads((_ip_dir() / "tb" / "cocotb" / "tb_manifest.json").read_text(encoding="utf-8"))


def _resolve_rtl_sources(ip_dir: Path, manifest: dict) -> list[str]:
    out = []
    for src in manifest.get("rtl_sources") or []:
        path = Path(src)
        if not path.is_absolute():
            path = ip_dir / path
        out.append(str(path.resolve()))
    return out


def _with_icarus_vcd_dump(sources: list[str], build_dir: Path, top: str, ip: str) -> tuple[list[str], list[str]]:
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


def _parse_results(path: Path) -> tuple[int, int, int]:
    root = ET.parse(path).getroot()
    tests = failures = errors = 0
    for node in [root, *root.findall(".//testsuite")]:
        tests += int(float(node.attrib.get("tests", 0) or 0))
        failures += int(float(node.attrib.get("failures", 0) or 0))
        errors += int(float(node.attrib.get("errors", 0) or 0))
    if tests == 0:
        cases = root.findall(".//testcase")
        tests = len(cases)
        failures = sum(1 for c in cases if c.find("failure") is not None)
        errors = sum(1 for c in cases if c.find("error") is not None)
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
            failed.append(f"PARSE_ERROR: {exc}")
            continue
        if isinstance(row, dict) and row.get("passed") is False:
            failed.append(f"{row.get('goal_id')}: {row.get('mismatch')}")
    if not failed:
        return []
    preview = "; ".join(failed[:8])
    suffix = "" if len(failed) <= 8 else f"; ... +{len(failed) - 8} more"
    return [f"[SIM ESCALATE] scoreboard_failed={len(failed)}: {preview}{suffix}"]


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
    tc_dir = ip_dir / "tc"
    model_dir = ip_dir / "model"
    sources = _resolve_rtl_sources(ip_dir, manifest)
    if not sources:
        (sim_dir / "sim_report.txt").write_text("TESTS=0 PASS=0 FAIL=1\nno RTL sources\n", encoding="utf-8")
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
        results_file = run(
            simulator=simulator,
            verilog_sources=run_sources,
            toplevel=run_top,
            module="test_mctp_assembler",
            python_search=[str(tb_dir), str(tc_dir), str(model_dir), str(runtime_dir)],
            sim_build=str(build_dir),
            timescale="1ns/1ps",
            waves=waves,
            force_compile=True,
            extra_env=env,
            includes=[str(ip_dir / "rtl")],
        )
    except BaseException as exc:
        (sim_dir / "sim_report.txt").write_text(f"TESTS=1 PASS=0 FAIL=1\nSimulation exception: {exc}\n", encoding="utf-8")
        print(f"Simulation exception: {exc}")
        return 1

    canonical = sim_dir / "results.xml"
    shutil.copy2(results_file, canonical)
    shutil.copy2(results_file, tb_dir / "results.xml")
    tests, failures, errors = _parse_results(canonical)
    passed = tests - failures - errors
    escalations = _scoreboard_escalations(sim_dir / "scoreboard_events.jsonl")
    report = [
        f"TESTS={tests} PASS={passed} FAIL={failures + errors}",
        f"results={canonical.relative_to(project_root)}",
        f"scoreboard={ip}/sim/scoreboard_events.jsonl",
    ]
    report.extend(escalations)
    (sim_dir / "sim_report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"TESTS={tests} PASS={passed} FAIL={failures + errors}")
    for line in escalations:
        print(line)
    return 0 if failures == 0 and errors == 0 and tests > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
