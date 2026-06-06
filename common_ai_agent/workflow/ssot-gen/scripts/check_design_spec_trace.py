#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Final

import yaml


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
            if str(key) in {"source_refs", "contract_refs", "contract_ref", "locked_truth_projection"}:
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


def check_design_spec_trace(ip: str, root: Path) -> tuple[bool, list[str], dict[str, Any]]:
    ip_dir = root / ip
    ssot = _find_ssot(root, ip)
    doc = _load_yaml(ssot)
    req_dir = ip_dir / "req"
    manifest = _load_json(req_dir / "approval_manifest.json")
    requirements = _load_json(req_dir / "requirements_index.json")
    contracts = _load_json(req_dir / "contract_refs.json")

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

    reflected = _collect_refs(doc)
    required_reqs = _required_requirement_ids(requirements)
    missing_reqs = sorted(required_reqs - reflected)
    if missing_reqs:
        issues.append(f"missing required requirement refs: {', '.join(missing_reqs)}")

    required_contracts = _contract_ids(contracts)
    missing_contracts = sorted(required_contracts - reflected)
    if missing_contracts:
        issues.append(f"missing contract refs: {', '.join(missing_contracts)}")

    report: dict[str, Any] = {
        "schema_version": 1,
        "type": "design_spec_trace_check",
        "ip": ip,
        "ssot": str(ssot.relative_to(ip_dir) if ssot.is_relative_to(ip_dir) else ssot),
        "status": "fail" if issues else "pass",
        "requirements": sorted(required_reqs),
        "contract_refs": sorted(required_contracts),
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
            f"requirements={len(report['requirements'])} contracts={len(report['contract_refs'])}"
        )
        return 0
    print(f"[check_design_spec_trace] FAIL {args.ip}")
    for issue in issues:
        print(f"- {issue}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
