#!/usr/bin/env python3
"""Gate locked behavioral contracts through SSOT FL/CL model artifacts.

This script has two valid modes:

- strict FL/CL model closure: model artifacts must exist and cover every
  locked behavioral contract projected into function_model/cycle_model.
- direct RTL mode: with --allow-direct-rtl, a missing FL/CL model is allowed,
  but only after locked behavioral contracts have already been projected into
  concrete SSOT Function/Cycle Model rows. RTL must then close contracts
  directly through rtl-gen gates.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml


WORKFLOW_ROOT = Path(__file__).resolve().parents[2]
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))

from behavioral_contracts import (  # noqa: E402
    BehavioralContractError,
    behavioral_contract_ids,
    compare_behavioral_to_function_cycle,
    normalize_behavioral_contracts,
)

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from emit_model_signature import _build_payload as _build_model_signature  # noqa: E402


def _resolve_ip_dir(root: Path, ip: str) -> Path:
    root = root.resolve()
    if root.name == ip and (root / "yaml" / f"{ip}.ssot.yaml").is_file():
        return root
    return root / ip


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _extract_ids(doc: dict[str, Any], key: str, id_keys: tuple[str, ...]) -> set[str]:
    ids: set[str] = set()
    for item in _as_list(doc.get(key)):
        if not isinstance(item, dict):
            continue
        for id_key in id_keys:
            value = item.get(id_key)
            if isinstance(value, str) and value.strip():
                ids.add(value.strip())
                break
    return ids


def _strings(value: Any) -> set[str]:
    if isinstance(value, str):
        return {value}
    if isinstance(value, dict):
        result: set[str] = set()
        for key, child in value.items():
            if isinstance(key, str) and key.strip():
                result.add(key.strip())
            result.update(_strings(child))
        return result
    if isinstance(value, list):
        result: set[str] = set()
        for child in value:
            result.update(_strings(child))
        return result
    return set()


def _extract_check_keys(value: Any) -> set[str]:
    keys = _strings(value)

    def visit(item: Any) -> None:
        if isinstance(item, dict):
            for key in ("id", "name", "transaction_id", "txn_id", "goal_id", "source_ref", "source"):
                val = item.get(key)
                if isinstance(val, str) and val.strip():
                    keys.add(val.strip())
            for child in item.values():
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)

    visit(value)
    return keys


def _path_tokens(paths: list[str], contract_id: str) -> set[str]:
    tokens = {contract_id}
    for path in paths:
        if not path:
            continue
        tokens.add(path)
        dotted = path.replace("[", ".").replace("]", "")
        parts = [part for part in dotted.split(".") if part]
        tokens.update(parts)
        if len(parts) >= 3:
            tokens.add(".".join(parts[-2:]))
    return {token for token in tokens if token and token not in {"function_model", "cycle_model"}}


def _text_has_any(text: str, tokens: set[str]) -> bool:
    return any(token in text for token in tokens)


def _keys_have_any(keys: set[str], tokens: set[str]) -> bool:
    return bool(keys & tokens)


def _signature_issue(ip: str, ssot: dict[str, Any], signature: dict[str, Any]) -> str:
    expected = _build_model_signature(ip, ssot)
    for key, expected_value in expected.items():
        if signature.get(key) != expected_value:
            return f"model/model_signature.json drift at {key}"
    return ""


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _direct_rtl_report(
    *,
    ip: str,
    contract_ids: set[str],
    projection: dict[str, Any],
    issues: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "type": "model_contract_trace",
        "ip": ip,
        "mode": "direct_rtl",
        "passed": not issues,
        "direct_rtl_allowed": True,
        "contract_refs": sorted(contract_ids),
        "ssot_projection": projection,
        "artifact_closure": {
            "status": "skipped_direct_rtl",
            "reason": (
                "FL/CL executable artifacts are absent by policy. rtl-gen must close the same "
                "locked contracts directly against SSOT and RTL evidence."
            ),
        },
        "issues": issues,
    }


def validate(ip: str, root: Path, *, allow_direct_rtl: bool = False) -> dict[str, Any]:
    ip_dir = _resolve_ip_dir(root, ip)
    req_dir = ip_dir / "req"
    ssot_path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    behavioral_path = req_dir / "behavioral_contracts.json"
    issues: list[str] = []

    if not behavioral_path.is_file():
        return {
            "schema_version": 1,
            "type": "model_contract_trace",
            "ip": ip,
            "mode": "inactive",
            "passed": True,
            "direct_rtl_allowed": allow_direct_rtl,
            "contract_refs": [],
            "issues": [],
            "reason": "req/behavioral_contracts.json absent",
        }

    try:
        ssot = _load_yaml(ssot_path)
    except Exception as exc:
        return {
            "schema_version": 1,
            "type": "model_contract_trace",
            "ip": ip,
            "mode": "error",
            "passed": False,
            "direct_rtl_allowed": allow_direct_rtl,
            "contract_refs": [],
            "issues": [f"cannot load SSOT YAML: {type(exc).__name__}: {exc}"],
        }

    try:
        obligations_doc = _load_json(req_dir / "obligations.json") if (req_dir / "obligations.json").is_file() else {}
        obligation_ids = _extract_ids(obligations_doc, "obligations", ("obligation_id", "id"))
        behavioral_raw = _load_json(behavioral_path)
        behavioral = normalize_behavioral_contracts(
            ip,
            behavioral_raw,
            known_obligation_ids=obligation_ids or None,
        )
    except (BehavioralContractError, OSError, ValueError, json.JSONDecodeError) as exc:
        return {
            "schema_version": 1,
            "type": "model_contract_trace",
            "ip": ip,
            "mode": "error",
            "passed": False,
            "direct_rtl_allowed": allow_direct_rtl,
            "contract_refs": [],
            "issues": [f"invalid behavioral contract authority: {exc}"],
        }

    contract_ids = behavioral_contract_ids(behavioral)
    projection_issues, projection = compare_behavioral_to_function_cycle(behavioral, ssot)
    issues.extend(projection_issues)

    paths = {
        "functional_model": ip_dir / "model" / "functional_model.py",
        "fl_model_check": ip_dir / "model" / "fl_model_check.json",
        "model_signature": ip_dir / "model" / "model_signature.json",
        "cycle_model": ip_dir / "model" / "cycle_model.py",
        "cl_model_check": ip_dir / "model" / "cl_model_check.json",
    }
    existing = {name: path.is_file() for name, path in paths.items()}
    any_model_artifact = any(existing.values())
    if not any_model_artifact and allow_direct_rtl:
        return _direct_rtl_report(ip=ip, contract_ids=contract_ids, projection=projection, issues=issues)

    missing_fl = [name for name in ("functional_model", "fl_model_check", "model_signature") if not existing[name]]
    if missing_fl:
        issues.append("missing FL model contract artifact(s): " + ", ".join(missing_fl))

    fl_check: dict[str, Any] = {}
    fl_keys: set[str] = set()
    if existing["fl_model_check"]:
        try:
            fl_check = _load_json(paths["fl_model_check"])
            fl_keys = _extract_check_keys(fl_check)
            if fl_check.get("passed") is not True:
                issues.append("model/fl_model_check.json must have passed=true")
        except Exception as exc:
            issues.append(f"cannot parse model/fl_model_check.json: {type(exc).__name__}: {exc}")

    if existing["model_signature"]:
        try:
            signature = _load_json(paths["model_signature"])
            drift = _signature_issue(ip, ssot, signature)
            if drift:
                issues.append(drift)
        except Exception as exc:
            issues.append(f"cannot verify model/model_signature.json: {type(exc).__name__}: {exc}")

    fl_source = _read_text(paths["functional_model"]) if existing["functional_model"] else ""
    function_hits = projection.get("function_model_hits") if isinstance(projection.get("function_model_hits"), dict) else {}
    for contract_id in sorted(contract_ids):
        hit_paths = [str(item) for item in _as_list(function_hits.get(contract_id))]
        tokens = _path_tokens(hit_paths, contract_id)
        if hit_paths and not (_keys_have_any(fl_keys, tokens) or _text_has_any(fl_source, tokens)):
            issues.append(
                f"behavioral contract {contract_id} function_model rows are not represented in FL artifacts: "
                + ", ".join(hit_paths)
            )

    cycle_required_contracts = sorted(
        set(contract_ids)
        - set(_as_list(projection.get("cycle_model_waived")))
    )
    missing_cl = [name for name in ("cycle_model", "cl_model_check") if not existing[name]]
    if cycle_required_contracts and missing_cl:
        issues.append("missing CL model contract artifact(s): " + ", ".join(missing_cl))

    cl_check: dict[str, Any] = {}
    cl_keys: set[str] = set()
    if existing["cl_model_check"]:
        try:
            cl_check = _load_json(paths["cl_model_check"])
            cl_keys = _extract_check_keys(cl_check)
            if cl_check.get("passed") is not True:
                issues.append("model/cl_model_check.json must have passed=true")
        except Exception as exc:
            issues.append(f"cannot parse model/cl_model_check.json: {type(exc).__name__}: {exc}")

    cl_source = _read_text(paths["cycle_model"]) if existing["cycle_model"] else ""
    cycle_hits = projection.get("cycle_model_hits") if isinstance(projection.get("cycle_model_hits"), dict) else {}
    for contract_id in cycle_required_contracts:
        hit_paths = [str(item) for item in _as_list(cycle_hits.get(contract_id))]
        tokens = _path_tokens(hit_paths, contract_id)
        if hit_paths and not (_keys_have_any(cl_keys, tokens) or _text_has_any(cl_source, tokens)):
            issues.append(
                f"behavioral contract {contract_id} cycle_model rows are not represented in CL artifacts: "
                + ", ".join(hit_paths)
            )

    return {
        "schema_version": 1,
        "type": "model_contract_trace",
        "ip": ip,
        "mode": "fl_cl_model",
        "passed": not issues,
        "direct_rtl_allowed": allow_direct_rtl,
        "contract_refs": sorted(contract_ids),
        "ssot_projection": projection,
        "artifact_closure": {
            "status": "pass" if not issues else "fail",
            "artifacts_present": existing,
            "fl_model_check_passed": fl_check.get("passed") is True,
            "cl_model_check_passed": cl_check.get("passed") is True if cycle_required_contracts else None,
            "cycle_required_contracts": cycle_required_contracts,
        },
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ip")
    parser.add_argument("--root", default=".")
    parser.add_argument("--allow-direct-rtl", action="store_true")
    parser.add_argument("--no-report", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    report = validate(args.ip, root, allow_direct_rtl=args.allow_direct_rtl)
    if not args.no_report:
        ip_dir = _resolve_ip_dir(root, args.ip)
        report_path = ip_dir / "logs" / "gates" / "model_contract_trace.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        report["report_path"] = str(report_path)

    status = "PASS" if report.get("passed") else "FAIL"
    print(f"[check_model_contract_trace] {status} ip={args.ip} mode={report.get('mode')}")
    for issue in _as_list(report.get("issues")):
        print(f"- {issue}")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
