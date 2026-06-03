from __future__ import annotations

import json
import os
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from cocotb_test.simulator import run


JsonValue = object
JsonMap = dict[str, object]


def _ip_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def _as_map(value: JsonValue) -> JsonMap:
    return value if isinstance(value, dict) else {}


def _strings(value: JsonValue) -> list[str]:
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


def _manifest() -> JsonMap:
    value = json.loads((_ip_dir() / "tb" / "cocotb" / "tb_manifest.json").read_text(encoding="utf-8"))
    return _as_map(value)


def _with_icarus_vcd_dump(sources: list[str], build_dir: Path, top: str) -> tuple[list[str], list[str]]:
    dump_module = "atlas_contract_v2_vcd_dump"
    dump_src = build_dir / f"{dump_module}.v"
    _ = dump_src.write_text(
        f"module {dump_module}();\n"
        "initial begin\n"
        "  $dumpfile(\"contract_v2.vcd\");\n"
        f"  $dumpvars(0, {top});\n"
        "end\n"
        "endmodule\n",
        encoding="utf-8",
    )
    return [*sources, str(dump_src)], [top, dump_module]


def _copy_contract_v2_wave(build_dir: Path, sim_dir: Path) -> None:
    waves = sorted(build_dir.rglob("contract_v2.vcd"))
    if not waves:
        raise FileNotFoundError("contract_v2.vcd")
    shutil.copy2(waves[0], sim_dir / "contract_v2.vcd")


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


def main() -> int:
    ip_dir = _ip_dir()
    project_root = ip_dir.parent
    manifest = _manifest()
    ip = str(manifest.get("ip") or ip_dir.name)
    top = str(manifest.get("top") or ip)
    common_root = Path(os.environ.get("COMMON_AI_AGENT_ROOT") or str(manifest.get("common_ai_agent_root") or project_root)).resolve()
    tb_dir = ip_dir / "tb" / "cocotb"
    sim_dir = ip_dir / "sim"
    build_dir = sim_dir / "contract_v2_build"
    sim_dir.mkdir(parents=True, exist_ok=True)
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)
    for stale in (sim_dir / "contract_v2_events.jsonl", sim_dir / "contract_v2.vcd", sim_dir / "contract_v2_results.xml"):
        stale.unlink(missing_ok=True)

    sources = [str(Path(src).resolve()) for src in _strings(manifest.get("rtl_sources"))]
    runtime_dir = common_root / "workflow" / "tb-gen" / "runtime"
    simulator = os.environ.get("SIM", "icarus")
    run_sources = sources
    run_top = top
    waves = True
    if simulator == "icarus":
        run_sources, run_top = _with_icarus_vcd_dump(sources, build_dir, top)
        waves = False
    raw_results = run(
        simulator=simulator,
        verilog_sources=run_sources,
        toplevel=run_top,
        module="test_mctp_contract_v2",
        python_search=[str(tb_dir), str(runtime_dir)],
        sim_build=str(build_dir),
        timescale="1ns/1ps",
        waves=waves,
        force_compile=True,
        extra_env={
            "COMMON_AI_AGENT_ROOT": str(common_root),
            "IP_NAME": ip,
            "PROJECT_ROOT": str(project_root),
            "PYTHONUNBUFFERED": "1",
        },
        includes=[str(ip_dir / "rtl")],
    )
    if raw_results is None:
        raise RuntimeError("cocotb did not return a results file")
    results_file = Path(raw_results)
    canonical = sim_dir / "contract_v2_results.xml"
    shutil.copy2(results_file, canonical)
    if simulator == "icarus":
        _copy_contract_v2_wave(build_dir, sim_dir)
    tests, failures, errors = _parse_results(canonical)
    print(f"CONTRACT_V2_TESTS={tests} PASS={tests - failures - errors} FAIL={failures + errors}")
    return 0 if tests > 0 and failures == 0 and errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
