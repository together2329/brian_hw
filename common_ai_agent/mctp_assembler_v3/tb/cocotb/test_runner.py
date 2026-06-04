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


def _write_assertion_failures(results_path: Path, output_path: Path, scoreboard_path: Path | None = None) -> int:
    root = ET.parse(results_path).getroot()
    records = []
    for case in root.findall(".//testcase"):
        testcase = case.attrib.get("name") or "unknown"
        for kind in ("failure", "error"):
            for node in case.findall(kind):
                records.append(
                    {
                        "detail": (node.text or "").strip(),
                        "kind": kind,
                        "message": node.attrib.get("message") or "",
                        "source": str(results_path),
                        "testcase": testcase,
                    }
                )
    if scoreboard_path is not None:
        records.extend(_scoreboard_failure_records(scoreboard_path))
    output_path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
    return len(records)


def _write_assertion_exception(output_path: Path, message: str) -> None:
    record = {
        "detail": message,
        "kind": "error",
        "message": "simulation exception",
        "source": "cocotb_test.simulator.run",
        "testcase": "simulation",
    }
    output_path.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")


def _scoreboard_failure_records(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    records: list[dict[str, str]] = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            records.append({
                "detail": f"scoreboard_events.jsonl parse error: {exc}",
                "kind": "scoreboard_parse_error",
                "message": "scoreboard parse error",
                "source": str(path),
                "testcase": "PARSE_ERROR",
            })
            continue
        if isinstance(row, dict) and row.get("passed") is False:
            records.append({
                "detail": str(row.get("mismatch") or "mismatch without detail"),
                "kind": "scoreboard",
                "message": "scoreboard row failed",
                "source": str(path),
                "testcase": str(row.get("goal_id") or "UNKNOWN"),
            })
    return records


def _scoreboard_escalations(path: Path) -> list[str]:
    failed = _scoreboard_failure_records(path)
    if not failed:
        return []
    preview = "; ".join(f"{record['testcase']}: {record['detail']}" for record in failed[:8])
    suffix = "" if len(failed) <= 8 else f"; ... +{len(failed) - 8} more"
    return [
        f"[SIM ESCALATE] scoreboard_failed={len(failed)} owner=sim_debug evidence={path}",
        f"[SIM ESCALATE] reason=FL-vs-RTL scoreboard mismatch: {preview}{suffix}",
    ]


def _sim_exit_code(tests: int, failures: int, errors: int, scoreboard_failures: int) -> int:
    return 0 if failures == 0 and errors == 0 and scoreboard_failures == 0 and tests > 0 else 1


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
    modules = os.environ.get("COCOTB_MODULES") or (
        f"test_{ip},test_mctp_datapath,test_pl_readback,"
        "test_sram_write_monitor,test_apb_desc_readback,test_safety_properties")
    check_scoreboard = "test_mctp_datapath" in {part.strip() for part in modules.split(",")}
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
            module=modules,
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
        _write_assertion_exception(sim_dir / "assertion_failures.jsonl", str(exc))
        (sim_dir / "sim_report.txt").write_text(
            f"TESTS=1 PASS=0 FAIL=1\nSimulation exception: {exc}\n",
            encoding="utf-8",
        )
        print("TESTS=1 PASS=0 FAIL=1")
        print(f"Simulation exception: {exc}")
        return 1

    canonical = sim_dir / "results.xml"
    if results_file is None:
        _write_assertion_exception(sim_dir / "assertion_failures.jsonl", "missing cocotb results file")
        (sim_dir / "sim_report.txt").write_text(
            "TESTS=1 PASS=0 FAIL=1\nSimulation exception: missing cocotb results file\n",
            encoding="utf-8",
        )
        print("TESTS=1 PASS=0 FAIL=1")
        print("Simulation exception: missing cocotb results file")
        return 1
    result_path = Path(results_file)
    shutil.copy2(result_path, canonical)
    shutil.copy2(result_path, tb_dir / "results.xml")
    scoreboard_path = sim_dir / "scoreboard_events.jsonl"
    scoreboard_records = _scoreboard_failure_records(scoreboard_path) if check_scoreboard else []
    assertion_failures = _write_assertion_failures(
        canonical,
        sim_dir / "assertion_failures.jsonl",
        scoreboard_path if check_scoreboard else None,
    )
    waves = _copy_waveforms(build_dir, sim_dir, ip)
    tests, failures, errors = _parse_results(canonical)
    passed = tests - failures - errors
    scoreboard_failures = len(scoreboard_records)
    total_failures = failures + errors + scoreboard_failures
    escalations = _scoreboard_escalations(scoreboard_path) if check_scoreboard else []
    report = [
        f"TESTS={tests} PASS={passed} FAIL={total_failures}",
        f"results={canonical.relative_to(project_root)}",
        f"scoreboard={ip}/sim/scoreboard_events.jsonl",
        f"coverage_functional={ip}/cov/coverage_functional.json",
        f"waveforms={','.join(str(path.relative_to(project_root)) for path in waves) if waves else 'none'}",
        "0 errors, 0 warnings" if total_failures == 0 else f"{errors} errors, {failures} failures, {scoreboard_failures} scoreboard failures",
        f"assertion_failures={assertion_failures}",
    ]
    report.extend(escalations)
    (sim_dir / "sim_report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"TESTS={tests} PASS={passed} FAIL={total_failures}")
    print("0 errors, 0 warnings" if total_failures == 0 else f"{errors} errors, {failures} failures, {scoreboard_failures} scoreboard failures")
    for line in escalations:
        print(line)

    # Regenerate the verification-hardening bundle from the REAL evidence this
    # run just produced (cocotb verdicts in results.xml + the monitor evidence
    # JSONs the readback/SRAM/APB/safety tests emitted). Each emitter derives its
    # JSON from genuine artifacts; it never hand-writes a pass. Best-effort: a
    # failing emitter prints its reason and the signoff gate (run separately)
    # reflects the real status — the emitters do not gate the sim itself.
    _run_verification_hardening_emitters(tb_dir)

    # FINAL step: emit a genuine sim-stage freshness stamp. Only a real, fully
    # passing authoritative run may attest freshness — so this is gated on the
    # sim having genuinely passed (tests ran, zero failures incl. scoreboard) and
    # the contract_reflection metadata being present. It writes a fresh
    # sim/sim_stage_run.json receipt (real pass/fail counts) then stamps
    # sim/evidence_freshness.json with stamp_source=sim_stage, fingerprinting the
    # CURRENT inputs + evidence artifacts. It MUST run after all sim evidence and
    # the emitters so every input/artifact mtime precedes the stamp.
    sim_passed = (tests > 0 and total_failures == 0)
    _stamp_sim_freshness(ip_dir, sim_dir, sim_passed, passed, total_failures)

    return _sim_exit_code(tests, failures, errors, scoreboard_failures)


def _stamp_sim_freshness(ip_dir: Path, sim_dir: Path, sim_passed: bool,
                         pass_count: int, fail_count: int) -> None:
    """Write a fresh sim_stage_run.json receipt and stamp evidence_freshness.json
    with stamp_source=sim_stage — the LAST step of the authoritative run.

    Mirrors the receipt format and stamp invocation in
    workflow/tb-gen/scripts/sim.sh so the contract_sim_freshness gate sees a
    genuine, fresh attestation. Gated on a real PASS: a non-passing run does NOT
    stamp (freshness can only be attested by a genuine fully-passing sim).
    """
    import subprocess

    reflection = ip_dir / "verify" / "contract_reflection.json"
    if not sim_passed:
        print("[sim_freshness] skip: sim did not fully pass; not attesting freshness")
        return
    if not reflection.is_file():
        print(f"[sim_freshness] skip: missing {reflection.relative_to(ip_dir)} (no contract to fingerprint)")
        return

    # Locate the repo root that holds workflow/contract-reflection/scripts.
    stamp_script = None
    search = Path(__file__).resolve()
    for parent in search.parents:
        candidate = parent / "workflow" / "contract-reflection" / "scripts" / "stamp_sim_evidence_freshness.py"
        if candidate.is_file():
            stamp_script = candidate
            repo_root = parent
            break
    if stamp_script is None:
        print("[sim_freshness] fail: stamp_sim_evidence_freshness.py not found")
        return

    # Fresh receipt with the REAL counts from this run (must be the last evidence
    # written before the stamp so its mtime is current).
    receipt = {
        "fail": int(fail_count),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pass": int(pass_count),
        "runner": "mctp_assembler_v3/tb/cocotb/test_runner.py",
        "schema_version": 1,
        "source": "sim_stage",
        "status": "pass",
        "type": "sim_stage_run",
    }
    (sim_dir / "sim_stage_run.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    env = dict(os.environ)
    env["ATLAS_SIM_FRESHNESS_SOURCE"] = "sim_stage"
    try:
        proc = subprocess.run(
            [sys.executable, str(stamp_script), ip_dir.name, "--root", str(repo_root)],
            capture_output=True, text=True, timeout=120, env=env)
        out = (proc.stdout or "").strip()
        err = (proc.stderr or "").strip()
        if out:
            print(out)
        if err:
            print(f"[sim_freshness] {err}")
        if proc.returncode != 0:
            print(f"[sim_freshness] stamp returned non-zero ({proc.returncode})")
    except Exception as exc:  # pragma: no cover - stamping must not break the sim
        print(f"[sim_freshness] stamp error: {exc}")


def _run_verification_hardening_emitters(tb_dir: Path) -> None:
    """Run the genuine verification-hardening emitters after the sim, so the
    scenario_e2e_summary / monitor_evidence / formal_status artifacts regenerate
    from the just-produced evidence on every authoritative run."""
    import subprocess

    for script in ("emit_scenario_e2e_summary.py", "emit_monitor_evidence.py",
                   "emit_formal_status.py"):
        path = tb_dir / script
        if not path.is_file():
            continue
        try:
            proc = subprocess.run([sys.executable, str(path)],
                                  capture_output=True, text=True, timeout=120)
            out = (proc.stdout or "").strip()
            err = (proc.stderr or "").strip()
            if out:
                print(out)
            if err:
                print(f"[{script}] {err}")
        except Exception as exc:  # pragma: no cover - emitter must not break the sim
            print(f"[{script}] emitter error: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())
