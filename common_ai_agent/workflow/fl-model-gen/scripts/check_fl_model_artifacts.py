#!/usr/bin/env python3
"""Validate worker-authored FL model artifacts without generating them."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover - reported in main()
    yaml = None


FORBIDDEN_TEXT_MARKERS = (
    "TODO",
    "TBD",
    "PLACEHOLDER",
    "Auto-injected",
    "fabricated_state",
    "[SSOT QUESTION]",
)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_ssot(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required to validate SSOT YAML")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not parse to a YAML object")
    return data


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _transaction_keys(ssot: dict[str, Any]) -> list[str]:
    fm = ssot.get("function_model") if isinstance(ssot.get("function_model"), dict) else {}
    keys: list[str] = []
    for idx, tx in enumerate(_as_list(fm.get("transactions"))):
        if not isinstance(tx, dict):
            continue
        tid = str(tx.get("id") or "").strip()
        name = str(tx.get("name") or "").strip()
        keys.append(tid or name or f"transaction_{idx}")
    return keys


def _string_blob(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=True)
    except TypeError:
        return str(value)


def _extract_check_keys(value: Any) -> set[str]:
    seen: set[str] = set()

    def visit(item: Any) -> None:
        if isinstance(item, dict):
            for key in ("id", "transaction_id", "txn_id", "name", "transaction_name"):
                val = item.get(key)
                if isinstance(val, str) and val.strip():
                    seen.add(val.strip())
            for child in item.values():
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)
        elif isinstance(item, str) and item.strip():
            seen.add(item.strip())

    if isinstance(value, dict):
        for key in (
            "transaction_results",
            "transactions",
            "covered_transactions",
            "trace",
            "checks",
            "results",
        ):
            if key in value:
                visit(value[key])
    visit(value)
    return seen


def _import_functional_model(path: Path):
    spec = importlib.util.spec_from_file_location("atlas_fl_model_gate_target", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _run_self_check(module: Any) -> dict[str, Any]:
    if callable(getattr(module, "run_self_check", None)):
        result = module.run_self_check()
    else:
        cls = getattr(module, "FunctionalModel", None)
        if cls is None:
            raise AttributeError("functional_model.py must define FunctionalModel")
        inst = cls()
        if not callable(getattr(inst, "run_self_check", None)):
            raise AttributeError("functional_model.py must expose run_self_check()")
        result = inst.run_self_check()
    if not isinstance(result, dict):
        raise TypeError("run_self_check() must return a dict")
    return result


def _coverage_blob(bin_item: Any) -> str:
    if isinstance(bin_item, dict):
        return " ".join(
            str(bin_item.get(key) or "")
            for key in ("id", "source", "source_ref", "transaction", "scenario", "description")
        )
    return str(bin_item)


def validate(ip: str, root: Path) -> dict[str, Any]:
    ip_dir = root / ip
    paths = {
        "ssot": ip_dir / "yaml" / f"{ip}.ssot.yaml",
        "functional_model": ip_dir / "model" / "functional_model.py",
        "decomposition": ip_dir / "model" / "decomposition.json",
        "fl_model_check": ip_dir / "model" / "fl_model_check.json",
        "fcov_plan": ip_dir / "cov" / "fcov_plan.json",
    }
    issues: list[str] = []
    evidence: dict[str, Any] = {"ip": ip, "paths": {k: str(v) for k, v in paths.items()}}

    for name, path in paths.items():
        if not path.is_file():
            issues.append(f"missing {name}: {path}")

    if issues:
        return {"ok": False, "passed": False, "issues": issues, "evidence": evidence}

    ssot = _load_ssot(paths["ssot"])
    tx_keys = _transaction_keys(ssot)
    evidence["ssot_transactions"] = tx_keys
    if not tx_keys:
        issues.append("SSOT has no function_model.transactions entries")

    for name in ("functional_model", "decomposition", "fl_model_check", "fcov_plan"):
        text = paths[name].read_text(encoding="utf-8", errors="replace")
        for marker in FORBIDDEN_TEXT_MARKERS:
            if marker in text:
                issues.append(f"{name} contains forbidden marker {marker!r}")

    try:
        module = _import_functional_model(paths["functional_model"])
        cls = getattr(module, "FunctionalModel", None)
        if cls is None:
            issues.append("functional_model.py must define FunctionalModel")
        elif not callable(getattr(cls, "apply", None)):
            issues.append("FunctionalModel.apply(txn) is missing")
        self_check = _run_self_check(module)
    except Exception as exc:
        self_check = {"passed": False, "error": f"{type(exc).__name__}: {exc}"}
        issues.append(f"run_self_check failed: {type(exc).__name__}: {exc}")
    evidence["self_check"] = self_check
    if not bool(self_check.get("passed")):
        issues.append("run_self_check() did not return passed=true")
    self_check_keys = _extract_check_keys(self_check)
    missing_self_check = [key for key in tx_keys if key not in self_check_keys]
    if missing_self_check:
        issues.append(
            "run_self_check transaction trace missing: " + ", ".join(missing_self_check)
        )

    try:
        fl_check = _load_json(paths["fl_model_check"])
    except Exception as exc:
        fl_check = {}
        issues.append(f"fl_model_check.json parse failed: {type(exc).__name__}: {exc}")
    evidence["fl_model_check"] = fl_check
    if not isinstance(fl_check, dict) or not bool(fl_check.get("passed")):
        issues.append("fl_model_check.json must be an object with passed=true")
    fl_check_keys = _extract_check_keys(fl_check)
    missing_fl_check = [key for key in tx_keys if key not in fl_check_keys]
    if missing_fl_check:
        issues.append(
            "fl_model_check transaction trace missing: " + ", ".join(missing_fl_check)
        )

    try:
        decomp = _load_json(paths["decomposition"])
    except Exception as exc:
        decomp = {}
        issues.append(f"decomposition.json parse failed: {type(exc).__name__}: {exc}")
    evidence["decomposition_units"] = len(_as_list(decomp.get("units") if isinstance(decomp, dict) else None))
    if not isinstance(decomp, dict):
        issues.append("decomposition.json must be a JSON object")
    else:
        if not _as_list(decomp.get("units")):
            issues.append("decomposition.json must contain non-empty units[]")
        if decomp.get("complete") is not True:
            issues.append("decomposition.json complete must be true")

    try:
        fcov = _load_json(paths["fcov_plan"])
    except Exception as exc:
        fcov = {}
        issues.append(f"fcov_plan.json parse failed: {type(exc).__name__}: {exc}")
    bins = _as_list(fcov.get("bins") if isinstance(fcov, dict) else None)
    evidence["fcov_bins"] = len(bins)
    if not isinstance(fcov, dict):
        issues.append("fcov_plan.json must be a JSON object")
    else:
        if fcov.get("planned_before_rtl") is not True:
            issues.append("fcov_plan.json planned_before_rtl must be true")
        if not bins:
            issues.append("fcov_plan.json must contain non-empty bins[]")
        bin_text = "\n".join(_coverage_blob(item) for item in bins)
        missing_fcov = [key for key in tx_keys if key not in bin_text]
        if missing_fcov:
            issues.append("fcov_plan bins missing transactions: " + ", ".join(missing_fcov))

    return {"ok": not issues, "passed": not issues, "issues": issues, "evidence": evidence}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ip")
    parser.add_argument("--root", default=".")
    parser.add_argument("--no-report", action="store_true")
    args = parser.parse_args()

    report = validate(args.ip, Path(args.root).resolve())
    if not args.no_report:
        report_path = Path(args.root).resolve() / args.ip / "logs" / "gates" / "fl_model_gate.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        report["report_path"] = str(report_path)

    status = "PASS" if report["passed"] else "FAIL"
    print(f"[check_fl_model_artifacts] {status} ip={args.ip}")
    if report.get("issues"):
        for issue in report["issues"]:
            print(f"- {issue}")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
