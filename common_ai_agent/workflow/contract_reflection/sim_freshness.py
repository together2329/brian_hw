from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from workflow.contract_reflection.evidence_contract_json import JsonList, JsonMap, JsonValue, as_list, as_map, json_strings, load_json, strings, text


SIM_FRESHNESS_REL: Final = "sim/evidence_freshness.json"
SIM_FRESHNESS_REPORT_REL: Final = "signoff/sim_evidence_freshness.json"
SIM_STAGE_RUN_REL: Final = "sim/sim_stage_run.json"
REQUIRED_STAMP_SOURCE: Final = "sim_stage"


@dataclass(frozen=True)
class FileFingerprint:
    path: str
    sha256: str
    mtime_ns: int

    def as_json(self) -> JsonMap:
        return {"mtime_ns": self.mtime_ns, "path": self.path, "sha256": self.sha256}


def resolve_ip_dir(root: Path, ip: str, label: str) -> Path:
    raw = Path(ip)
    if raw.is_absolute():
        raise SystemExit(f"[{label}] FAIL: ip path {ip} must stay under --root {root}")
    candidate = (root / raw).resolve()
    try:
        _ = candidate.relative_to(root)
    except ValueError as exc:
        raise SystemExit(f"[{label}] FAIL: ip path {ip} must stay under --root {root}") from exc
    return candidate


def write_sim_freshness_stamp(ip_dir: Path, stamp_source: str, sim_receipt: JsonMap | None = None) -> JsonMap:
    if stamp_source == REQUIRED_STAMP_SOURCE and sim_receipt is None and (ip_dir / SIM_STAGE_RUN_REL).is_file():
        sim_receipt = load_sim_stage_receipt(ip_dir, ip_dir / SIM_STAGE_RUN_REL)
    report = _build_current_freshness(ip_dir, stamp_source, sim_receipt)
    out = ip_dir / SIM_FRESHNESS_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    _ = out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def load_sim_stage_receipt(ip_dir: Path, receipt_path: Path) -> JsonMap:
    ip_root = ip_dir.resolve()
    observed = receipt_path.resolve()
    try:
        rel = observed.relative_to(ip_root).as_posix()
    except ValueError as exc:
        raise SystemExit(f"[sim_freshness] FAIL: sim_stage receipt must stay under {ip_dir}: {receipt_path}") from exc
    if rel != SIM_STAGE_RUN_REL:
        raise SystemExit(f"[sim_freshness] FAIL: sim_stage receipt must be {SIM_STAGE_RUN_REL}: {rel}")
    receipt = load_json(observed, "sim_freshness")
    issues = _sim_receipt_issues(receipt)
    if issues:
        raise SystemExit(f"[sim_freshness] FAIL: invalid sim_stage receipt: {'; '.join(issues)}")
    return receipt


def write_sim_freshness_check(ip_dir: Path) -> JsonMap:
    issues = sim_freshness_issues(ip_dir)
    issue_items: JsonList = json_strings(issues)
    report: JsonMap = {
        "generated_at": _utc(),
        "ip": ip_dir.name,
        "issues": issue_items,
        "schema_version": 1,
        "status": "pass" if not issues else "fail",
        "summary": {"issues": len(issues)},
        "type": "sim_evidence_freshness_report",
    }
    out = ip_dir / SIM_FRESHNESS_REPORT_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    _ = out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def sim_freshness_issues(ip_dir: Path) -> list[str]:
    manifest_path = ip_dir / SIM_FRESHNESS_REL
    if not manifest_path.is_file():
        return [f"missing {SIM_FRESHNESS_REL}"]
    manifest = load_json(manifest_path, "sim_freshness")
    current = _build_current_freshness(ip_dir, REQUIRED_STAMP_SOURCE)
    issues = [item for item in strings(current.get("issues"))]
    manifest_status = text(manifest.get("status"))
    if manifest_status != "pass":
        issues.append(f"sim evidence freshness stamp status is not pass: {manifest_status}")
    for issue in strings(manifest.get("issues")):
        issues.append(f"sim evidence freshness stamp recorded issue: {issue}")
    observed_source = text(manifest.get("stamp_source"))
    if observed_source != REQUIRED_STAMP_SOURCE:
        issues.append(f"sim evidence freshness stamp_source is not {REQUIRED_STAMP_SOURCE}: {observed_source}")
    else:
        issues.extend(_sim_receipt_issues(as_map(manifest.get("sim_receipt"))))
    issues.extend(_fingerprint_issues("metadata", manifest, current, "metadata_fingerprints"))
    issues.extend(_fingerprint_issues("input", manifest, current, "input_fingerprints"))
    issues.extend(_fingerprint_issues("artifact", manifest, current, "evidence_artifacts"))
    return issues


def _build_current_freshness(ip_dir: Path, stamp_source: str, sim_receipt: JsonMap | None = None) -> JsonMap:
    reflection = load_json(ip_dir / "verify" / "contract_reflection.json", "sim_freshness")
    evidence_contract_path = ip_dir / "verify" / "evidence_contract.json"
    evidence_contract = load_json(evidence_contract_path, "sim_freshness") if evidence_contract_path.is_file() else {}
    input_paths, input_path_issues = _input_paths(reflection)
    evidence_paths, evidence_path_issues = _evidence_paths(reflection, evidence_contract)
    metadata, metadata_issues = _fingerprints(ip_dir, _metadata_paths(evidence_contract_path), "metadata")
    inputs, input_issues = _fingerprints(ip_dir, input_paths, "input")
    evidence, evidence_issues = _fingerprints(ip_dir, evidence_paths, "evidence")
    issues = metadata_issues + input_path_issues + evidence_path_issues + input_issues + evidence_issues
    if stamp_source != REQUIRED_STAMP_SOURCE:
        issues.append(f"sim evidence freshness stamp_source is not {REQUIRED_STAMP_SOURCE}: {stamp_source}")
    issues.extend(_stale_evidence_issues(inputs, evidence))
    issues.extend(_sim_stage_run_issues(ip_dir, stamp_source, inputs))
    evidence_items: JsonList = [item.as_json() for item in evidence]
    input_items: JsonList = [item.as_json() for item in inputs]
    metadata_items: JsonList = [item.as_json() for item in metadata]
    issue_items: JsonList = json_strings(issues)
    return {
        "evidence_artifacts": evidence_items,
        "generated_at": _utc(),
        "input_fingerprints": input_items,
        "ip": ip_dir.name,
        "issues": issue_items,
        "metadata_fingerprints": metadata_items,
        "schema_version": 1,
        "sim_receipt": sim_receipt or {},
        "status": "pass" if not issues else "fail",
        "stamp_source": stamp_source,
        "summary": {"evidence_artifacts": len(evidence), "inputs": len(inputs), "issues": len(issues), "metadata": len(metadata)},
        "type": "sim_evidence_freshness",
    }


def _fingerprint_issues(label: str, manifest: JsonMap, current: JsonMap, key: str) -> list[str]:
    observed = _fingerprint_map(manifest.get(key))
    issues: list[str] = []
    for item in as_list(current.get(key)):
        data = as_map(item)
        path = text(data.get("path"))
        sha256 = text(data.get("sha256"))
        stamped = observed.get(path)
        if stamped is None:
            issues.append(f"missing sim evidence {label} fingerprint: {path}")
        elif stamped != sha256:
            issues.append(f"sim evidence {label} fingerprint mismatch: {path}")
    current_paths = {text(as_map(item).get("path")) for item in as_list(current.get(key))}
    for path in sorted(observed):
        if path not in current_paths:
            issues.append(f"stamped sim evidence {label} fingerprint no longer required: {path}")
    return issues


def _fingerprint_map(value: JsonValue) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in as_list(value):
        data = as_map(item)
        path = text(data.get("path"))
        sha256 = text(data.get("sha256"))
        if path and sha256:
            out[path] = sha256
    return out


def _fingerprints(ip_dir: Path, rel_paths: list[str], label: str) -> tuple[list[FileFingerprint], list[str]]:
    fingerprints: list[FileFingerprint] = []
    issues: list[str] = []
    for rel in rel_paths:
        path = ip_dir / rel
        if not path.is_file():
            issues.append(f"missing sim evidence {label}: {rel}")
            continue
        fingerprints.append(FileFingerprint(rel, hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns))
    return fingerprints, issues


def _stale_evidence_issues(inputs: list[FileFingerprint], evidence: list[FileFingerprint]) -> list[str]:
    if not inputs or not evidence:
        return []
    newest_input = max(inputs, key=lambda item: item.mtime_ns)
    return [
        f"sim evidence artifact older than input: {artifact.path} predates {newest_input.path}"
        for artifact in evidence
        if artifact.mtime_ns < newest_input.mtime_ns
    ]


def _sim_stage_run_issues(ip_dir: Path, stamp_source: str, inputs: list[FileFingerprint]) -> list[str]:
    if stamp_source != REQUIRED_STAMP_SOURCE:
        return []
    marker = ip_dir / SIM_STAGE_RUN_REL
    if not marker.is_file():
        return []
    if not inputs:
        return []
    newest_input = max(inputs, key=lambda item: item.mtime_ns)
    if marker.stat().st_mtime_ns < newest_input.mtime_ns:
        return [f"sim stage run marker older than input: {SIM_STAGE_RUN_REL} predates {newest_input.path}"]
    return []


def _sim_receipt_issues(receipt: JsonMap) -> list[str]:
    if not receipt:
        return [f"missing sim stage receipt: {SIM_STAGE_RUN_REL}"]
    issues: list[str] = []
    schema_version = receipt.get("schema_version")
    if schema_version != 1:
        issues.append(f"sim stage receipt schema_version is not 1: {schema_version}")
    receipt_type = text(receipt.get("type"))
    if receipt_type != "sim_stage_run":
        issues.append(f"sim stage receipt type is not sim_stage_run: {receipt_type}")
    source = text(receipt.get("source"))
    if source != REQUIRED_STAMP_SOURCE:
        issues.append(f"sim stage receipt source is not {REQUIRED_STAMP_SOURCE}: {source}")
    status = text(receipt.get("status")).lower()
    if status != "pass":
        issues.append(f"sim stage receipt status is not pass: {status}")
    passed = receipt.get("pass")
    if not isinstance(passed, int) or isinstance(passed, bool) or passed <= 0:
        issues.append(f"sim stage receipt pass count is not positive: {passed}")
    failed = receipt.get("fail")
    if not isinstance(failed, int) or isinstance(failed, bool) or failed != 0:
        issues.append(f"sim stage receipt fail count is not zero: {failed}")
    runner = text(receipt.get("runner"))
    if not runner:
        issues.append("sim stage receipt missing runner")
    return issues


def _input_paths(reflection: JsonMap) -> tuple[list[str], list[str]]:
    out: set[str] = set()
    issues: list[str] = []
    for item in as_list(reflection.get("contract_refs")):
        data = as_map(item)
        for stage in ("ssot", "fl", "cl", "tb"):
            _add_rel(out, issues, text(as_map(data.get(stage)).get("path")), f"{stage}.path")
        for owner in strings(as_map(data.get("rtl")).get("owner_files")):
            _add_rel(out, issues, owner, "rtl.owner_files")
    return sorted(out), issues


def _metadata_paths(evidence_contract_path: Path) -> list[str]:
    paths = ["verify/contract_reflection.json"]
    if evidence_contract_path.is_file():
        paths.append("verify/evidence_contract.json")
    paths.append(SIM_STAGE_RUN_REL)
    return paths


def _evidence_paths(reflection: JsonMap, evidence_contract: JsonMap) -> tuple[list[str], list[str]]:
    out: set[str] = set()
    issues: list[str] = []
    for item in as_list(reflection.get("contract_refs")):
        sim = as_map(as_map(item).get("sim"))
        _add_rel(out, issues, text(sim.get("scoreboard")), "sim.scoreboard")
        _add_rel(out, issues, text(sim.get("wave")), "sim.wave")
    for item in as_list(evidence_contract.get("obligations")):
        obligation = as_map(item)
        evidence_rows = as_list(obligation.get("evidence_rows"))
        if not evidence_rows:
            _add_rel(out, issues, "sim/scoreboard_events.jsonl", "evidence_rows.default")
        for row_ref in evidence_rows:
            artifact = text(as_map(row_ref).get("artifact")) or "sim/scoreboard_events.jsonl"
            _add_rel(out, issues, artifact, "evidence_rows.artifact")
        for condition in as_list(obligation.get("pass_conditions")):
            _add_rel(out, issues, text(as_map(condition).get("artifact")), "pass_conditions.artifact")
    return sorted(out), issues


def _add_rel(out: set[str], issues: list[str], rel: str, label: str) -> None:
    path = Path(rel)
    if not rel:
        return
    if path.is_absolute() or ".." in path.parts:
        issues.append(f"invalid sim evidence path {label}: {rel}")
        return
    out.add(rel)


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
