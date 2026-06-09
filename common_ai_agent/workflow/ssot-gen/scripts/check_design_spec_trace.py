#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Final

import yaml

WORKFLOW_ROOT = Path(__file__).resolve().parents[2]
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))

from behavioral_contracts import (
    BehavioralContractError,
    behavioral_contract_ids,
    compare_behavioral_content_to_ssot,
    compare_behavioral_to_function_cycle,
    compare_behavioral_to_ssot,
    normalize_behavioral_contracts,
)
from structural_contracts import (
    StructuralContractError,
    compare_structural_to_ssot,
    normalize_structural_contracts,
    structural_contract_ids,
)


DESCRIPTION: Final[str] = "Check that Design Spec YAML traces back to locked truth authority."


def _resolve_project_root(root: str, ip_root: str, ip: str) -> Path:
    project_root = Path(root or ".").expanduser().resolve()
    raw_ip_root = ip_root.strip()
    if raw_ip_root:
        candidate = Path(raw_ip_root).expanduser()
        if not candidate.is_absolute():
            candidate = project_root / candidate
        candidate = candidate.resolve()
        if candidate.name == ip or (candidate / "yaml").is_dir():
            return candidate.parent
    return project_root


def _find_ssot(root: Path, ip: str) -> Path:
    for base in (root / ip, root):
        for name in (f"{ip}.ssot.yaml", f"{ip}_ssot.yaml", f"{ip}.ssot.yml"):
            candidate = base / "yaml" / name
            if candidate.is_file():
                return candidate
    return root / ip / "yaml" / f"{ip}.ssot.yaml"


def _load_json(path: Path) -> dict[str, Any]:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SystemExit(f"cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"cannot parse {path}: {exc}") from exc
    if not isinstance(doc, dict):
        raise SystemExit(f"{path} must contain a JSON object")
    return doc


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SystemExit(f"cannot read {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise SystemExit(f"cannot parse {path}: {exc}") from exc
    if not isinstance(doc, dict):
        raise SystemExit(f"{path} must contain one YAML mapping")
    return doc


def _strings(value: Any) -> set[str]:
    if isinstance(value, str):
        return {value}
    if isinstance(value, list):
        result: set[str] = set()
        for item in value:
            result.update(_strings(item))
        return result
    if isinstance(value, dict):
        result: set[str] = set()
        for item in value.values():
            result.update(_strings(item))
        return result
    return set()


def _collect_refs(value: Any) -> set[str]:
    if isinstance(value, dict):
        result: set[str] = set()
        for key, item in value.items():
            if str(key) in {
                "source_refs",
                "contract_refs",
                "contract_ref",
                "behavioral_contract_refs",
                "behavioral_contracts",
                "evidence_refs",
                "locked_truth_projection",
            }:
                result.update(_strings(item))
            result.update(_collect_refs(item))
        return result
    if isinstance(value, list):
        result: set[str] = set()
        for item in value:
            result.update(_collect_refs(item))
        return result
    return set()


def _required_requirement_ids(requirements_doc: dict[str, Any]) -> set[str]:
    raw = requirements_doc.get("requirements")
    if not isinstance(raw, list):
        return set()
    ids: set[str] = set()
    for item in raw:
        if isinstance(item, dict) and item.get("required") is not False:
            value = item.get("requirement_id")
            if isinstance(value, str) and value.strip():
                ids.add(value.strip())
    return ids


def _contract_ids(contract_doc: dict[str, Any]) -> set[str]:
    raw = contract_doc.get("contract_refs")
    if not isinstance(raw, list):
        return set()
    ids: set[str] = set()
    for item in raw:
        if isinstance(item, dict):
            value = item.get("contract_ref_id")
            if isinstance(value, str) and value.strip():
                ids.add(value.strip())
    return ids


def _authority(doc: dict[str, Any]) -> dict[str, Any]:
    custom = doc.get("custom")
    if not isinstance(custom, dict):
        return {}
    authority = custom.get("locked_truth_authority")
    return authority if isinstance(authority, dict) else {}


def _projection_files(value: Any) -> set[str]:
    if isinstance(value, str) and value.strip():
        return {value.strip()}
    if isinstance(value, list):
        result: set[str] = set()
        for item in value:
            result.update(_projection_files(item))
        return result
    return set()


def check_design_spec_trace(ip: str, root: Path) -> tuple[bool, list[str], dict[str, Any]]:
    ip_dir = root / ip
    ssot = _find_ssot(root, ip)
    doc = _load_yaml(ssot)
    req_dir = ip_dir / "req"
    manifest = _load_json(req_dir / "approval_manifest.json")
    requirements = _load_json(req_dir / "requirements_index.json")
    contracts = _load_json(req_dir / "contract_refs.json")
    obligations = _load_json(req_dir / "obligations.json")
    structural_raw = _load_json(req_dir / "structural_contracts.json")
    behavioral_raw = _load_json(req_dir / "behavioral_contracts.json")

    issues: list[str] = []
    if manifest.get("status") != "requirements_locked":
        issues.append("approval_manifest status is not requirements_locked")

    authority = _authority(doc)
    if authority.get("kind") != "locked_truth_projection":
        issues.append("custom.locked_truth_authority.kind must be locked_truth_projection")
    if authority.get("approval_manifest") != "req/approval_manifest.json":
        issues.append("custom.locked_truth_authority.approval_manifest must be req/approval_manifest.json")
    if authority.get("bundle_sha256") != manifest.get("bundle_sha256"):
        issues.append("bundle_sha256 mismatch")
    expected_projection_files = {
        "req/requirements_index.json",
        "req/obligations.json",
        "req/contract_refs.json",
        "req/structural_contracts.json",
        "req/behavioral_contracts.json",
        "req/evidence_plan.json",
    }
    missing_projection_files = sorted(expected_projection_files - _projection_files(authority.get("projected_files")))
    if missing_projection_files:
        issues.append(f"custom.locked_truth_authority.projected_files missing: {', '.join(missing_projection_files)}")

    reflected = _collect_refs(doc)
    required_reqs = _required_requirement_ids(requirements)
    missing_reqs = sorted(required_reqs - reflected)
    if missing_reqs:
        issues.append(f"missing required requirement refs: {', '.join(missing_reqs)}")

    required_contracts = _contract_ids(contracts)
    missing_contracts = sorted(required_contracts - reflected)
    if missing_contracts:
        issues.append(f"missing contract refs: {', '.join(missing_contracts)}")

    obligation_ids = {
        str(item["obligation_id"])
        for item in obligations.get("obligations", [])
        if isinstance(item, dict) and isinstance(item.get("obligation_id"), str) and item.get("obligation_id").strip()
    }
    structural_summary: dict[str, Any] = {"active": False}
    try:
        structural = normalize_structural_contracts(ip, structural_raw, known_obligation_ids=obligation_ids)
        structural_ref_ids = structural_contract_ids(structural)
        structural_summary = {"active": True, "contract_refs": sorted(structural_ref_ids)}
        missing_structural_refs = sorted(structural_ref_ids - reflected)
        if missing_structural_refs:
            issues.append(f"missing structural contract refs: {', '.join(missing_structural_refs)}")
        structural_issues, structural_compare = compare_structural_to_ssot(structural, doc)
        structural_summary.update(structural_compare)
        issues.extend(structural_issues)
    except StructuralContractError as exc:
        issues.append(str(exc))

    behavioral_summary: dict[str, Any] = {"active": False}
    try:
        behavioral = normalize_behavioral_contracts(ip, behavioral_raw, known_obligation_ids=obligation_ids)
        behavioral_ref_ids = behavioral_contract_ids(behavioral)
        behavioral_summary = {"active": True, "contract_refs": sorted(behavioral_ref_ids)}
        missing_behavioral_refs = sorted(behavioral_ref_ids - reflected)
        if missing_behavioral_refs:
            issues.append(f"missing behavioral contract refs: {', '.join(missing_behavioral_refs)}")
        behavioral_issues, behavioral_compare = compare_behavioral_to_ssot(behavioral, doc)
        behavioral_summary.update(behavioral_compare)
        issues.extend(behavioral_issues)
        function_cycle_issues, function_cycle_compare = compare_behavioral_to_function_cycle(behavioral, doc)
        behavioral_summary["function_cycle_projection"] = function_cycle_compare
        issues.extend(function_cycle_issues)
        content_issues, content_compare = compare_behavioral_content_to_ssot(behavioral, doc)
        behavioral_summary["content_projection"] = content_compare
        issues.extend(content_issues)
    except BehavioralContractError as exc:
        issues.append(str(exc))

    report: dict[str, Any] = {
        "schema_version": 1,
        "type": "design_spec_trace_check",
        "ip": ip,
        "ssot": str(ssot.relative_to(ip_dir) if ssot.is_relative_to(ip_dir) else ssot),
        "status": "fail" if issues else "pass",
        "requirements": sorted(required_reqs),
        "contract_refs": sorted(required_contracts),
        "structural_contracts": structural_summary,
        "behavioral_contracts": behavioral_summary,
        "reflected_refs": sorted(reflected),
        "issues": issues,
    }
    out = req_dir / "design_spec_trace.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return not issues, issues, report


def main() -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("ip")
    parser.add_argument("--root", default=".")
    parser.add_argument("--ip-root", default="")
    args = parser.parse_args()
    root = _resolve_project_root(args.root, args.ip_root, args.ip)
    passed, issues, report = check_design_spec_trace(args.ip, root)
    if passed:
        print(
            f"[check_design_spec_trace] PASS {args.ip} "
            f"requirements={len(report['requirements'])} contracts={len(report['contract_refs'])} "
            f"structural_contracts={len(report['structural_contracts'].get('contract_refs', []))} "
            f"behavioral_contracts={len(report['behavioral_contracts'].get('contract_refs', []))}"
        )
        return 0
    print(f"[check_design_spec_trace] FAIL {args.ip}")
    for issue in issues:
        print(f"- {issue}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
