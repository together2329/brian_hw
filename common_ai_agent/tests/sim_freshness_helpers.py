from __future__ import annotations

import os
import subprocess
from pathlib import Path

from .contract_reflection_helpers import CONTRACT_CHECK_SCRIPT, REPO, STAMP_SIM_FRESHNESS_SCRIPT, make_contract_ip, write_json
from .test_semantic_contract_required_closure import _write_legacy_reflection, _write_stage_artifacts


def run_stamp(root: Path, source: str = "sim_stage") -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    if source:
        env["ATLAS_SIM_FRESHNESS_SOURCE"] = source
    else:
        env.pop("ATLAS_SIM_FRESHNESS_SOURCE", None)
    return subprocess.run(
        ["python3", str(STAMP_SIM_FRESHNESS_SCRIPT), "contract_ip", "--root", str(root)],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def run_contract_check(root: Path, require_contract_closure: bool = False) -> subprocess.CompletedProcess[str]:
    cmd = ["python3", str(CONTRACT_CHECK_SCRIPT), "contract_ip", "--root", str(root), "--require-sim-freshness"]
    if require_contract_closure:
        cmd.append("--require-contract-closure")
    return subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def make_reflected_ip(root: Path) -> Path:
    ip_dir = make_contract_ip(root)
    _write_stage_artifacts(ip_dir)
    _write_legacy_reflection(ip_dir)
    write_json(
        ip_dir / "sim" / "sim_stage_run.json",
        {
            "fail": 0,
            "generated_at": "2026-06-04T00:00:00Z",
            "pass": 1,
            "runner": "tb/cocotb/test_contract_ip.py",
            "schema_version": 1,
            "source": "sim_stage",
            "status": "pass",
            "type": "sim_stage_run",
        },
    )
    mark_evidence_newer_than_inputs(ip_dir)
    return ip_dir


def mark_evidence_newer_than_inputs(ip_dir: Path, extra: tuple[str, ...] = (), include_provenance: bool = True) -> None:
    inputs = [
        ip_dir / "verify" / "contract_reflection.json",
        ip_dir / "verify" / "evidence_contract.json",
        ip_dir / "yaml" / "contract_ip.ssot.yaml",
        ip_dir / "model" / "functional_model.py",
        ip_dir / "model" / "cycle_model.py",
        ip_dir / "rtl" / "contract_ip.sv",
        ip_dir / "tb" / "cocotb" / "test_contract_ip.py",
    ]
    newest_input = max(path.stat().st_mtime_ns for path in inputs)
    rels = ["sim/scoreboard_events.jsonl", "sim/contract_ip.vcd"]
    if include_provenance:
        rels.append("sim/sim_stage_run.json")
    rels.extend(extra)
    for offset, rel in enumerate(rels, 1):
        evidence = ip_dir / rel
        next_mtime = newest_input + offset * 1_000_000
        os.utime(evidence, ns=(next_mtime, next_mtime))


def mark_input_newer_than_evidence(ip_dir: Path, rel: str) -> None:
    evidence_paths = [ip_dir / "sim" / "scoreboard_events.jsonl", ip_dir / "sim" / "contract_ip.vcd", ip_dir / "sim" / "sim_stage_run.json"]
    newest_evidence = max(path.stat().st_mtime_ns for path in evidence_paths)
    changed = ip_dir / rel
    next_mtime = newest_evidence + 1_000_000
    os.utime(changed, ns=(next_mtime, next_mtime))


def append_text(path: Path) -> None:
    _ = path.write_text(path.read_text(encoding="utf-8") + "\nchanged\n", encoding="utf-8")
