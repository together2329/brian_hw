#!/usr/bin/env python3
"""Validate worker-authored FL model artifacts without generating them."""

from __future__ import annotations

import argparse
import ast
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


def _func_has_executable_body(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """True if a function body has a statement beyond a docstring/``pass``/``return None``.

    Mirrors the ast floor used by workflow/tb-gen/scripts/derive_tb_todos.py
    (``_has_executable_body``), specialised to a single function definition so a
    zero-logic ``apply`` that only ``pass``/``return``/``return None`` is rejected.
    """
    for stmt in node.body:
        if isinstance(stmt, ast.Pass):
            continue
        if (
            isinstance(stmt, ast.Expr)
            and isinstance(stmt.value, ast.Constant)
            and isinstance(stmt.value.value, str)
        ):
            continue  # docstring
        if isinstance(stmt, ast.Return) and (
            stmt.value is None
            or (isinstance(stmt.value, ast.Constant) and stmt.value.value is None)
        ):
            continue  # bare `return` / `return None`
        return True
    return False


def _apply_executable_issue(text: str) -> str:
    """Return an issue string if FunctionalModel.apply lacks a real body, else ''."""
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return f"functional_model.py does not parse: {exc}"
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "FunctionalModel":
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name == "apply":
                    if not _func_has_executable_body(child):
                        return (
                            "FunctionalModel.apply(txn) has no executable body "
                            "(only pass/docstring/return None); a zero-logic model is rejected"
                        )
                    return ""
            return "FunctionalModel.apply(txn) is missing"
    return "functional_model.py must define FunctionalModel"


def _structured_result_entries(value: Any) -> list[dict[str, Any]]:
    """Collect structured per-transaction result dicts.

    Looks at ``transaction_results``/``results`` both at the top level and nested
    under ``self_check`` (the real authoring convention nests them). Bare string
    mentions are intentionally ignored — only dict rows count as structured
    evidence.
    """
    entries: list[dict[str, Any]] = []
    scopes: list[Any] = [value]
    if isinstance(value, dict) and isinstance(value.get("self_check"), dict):
        scopes.append(value["self_check"])
    for scope in scopes:
        if not isinstance(scope, dict):
            continue
        for key in ("transaction_results", "results"):
            for item in _as_list(scope.get(key)):
                if isinstance(item, dict):
                    entries.append(item)
    return entries


def _entry_ids(entry: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for key in ("id", "transaction_id", "txn_id", "name", "transaction_name", "kind"):
        val = entry.get(key)
        if isinstance(val, str) and val.strip():
            ids.add(val.strip())
    return ids


def _inner_consistency_issue(label: str, entries: list[dict[str, Any]]) -> str:
    """Return an issue if any structured entry lies (passed!=true or actual!=expected)."""
    for entry in entries:
        if entry.get("passed") is not True:
            return (
                f"{label} self-check lies: top passed=true but inner entry "
                f"{sorted(_entry_ids(entry)) or '<unidentified>'} has passed={entry.get('passed')!r}"
            )
        if "actual" in entry and "expected" in entry and entry.get("actual") != entry.get("expected"):
            return (
                f"{label} self-check lies: top passed=true but inner entry "
                f"{sorted(_entry_ids(entry)) or '<unidentified>'} has actual!=expected "
                f"({entry.get('actual')!r} != {entry.get('expected')!r})"
            )
    return ""


def _structured_coverage_issue(label: str, tx_keys: list[str], entries: list[dict[str, Any]]) -> str:
    """Return an issue if any SSOT transaction lacks a structured (dict) result row."""
    if not tx_keys:
        # No SSOT transactions to cover: coverage is vacuously satisfied. The
        # missing-transactions condition is reported separately by validate().
        return ""
    if not entries:
        return f"{label} has no structured per-transaction results[]; bare string mentions do not count"
    covered: set[str] = set()
    for entry in entries:
        covered.update(_entry_ids(entry))
    missing = [key for key in tx_keys if key not in covered]
    if missing:
        return (
            f"{label} structured per-transaction results missing (id+passed required for each): "
            + ", ".join(missing)
        )
    return ""


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

    fl_source = paths["functional_model"].read_text(encoding="utf-8", errors="replace")
    apply_issue = _apply_executable_issue(fl_source)
    if apply_issue:
        issues.append(apply_issue)

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
    self_check_entries = _structured_result_entries(self_check)
    sc_lie = _inner_consistency_issue("run_self_check", self_check_entries)
    if sc_lie:
        issues.append(sc_lie)
    sc_cover = _structured_coverage_issue("run_self_check", tx_keys, self_check_entries)
    if sc_cover:
        issues.append(sc_cover)

    try:
        fl_check = _load_json(paths["fl_model_check"])
    except Exception as exc:
        fl_check = {}
        issues.append(f"fl_model_check.json parse failed: {type(exc).__name__}: {exc}")
    evidence["fl_model_check"] = fl_check
    if not isinstance(fl_check, dict) or not bool(fl_check.get("passed")):
        issues.append("fl_model_check.json must be an object with passed=true")
    fl_check_entries = _structured_result_entries(fl_check)
    fl_lie = _inner_consistency_issue("fl_model_check", fl_check_entries)
    if fl_lie:
        issues.append(fl_lie)
    fl_cover = _structured_coverage_issue("fl_model_check", tx_keys, fl_check_entries)
    if fl_cover:
        issues.append(fl_cover)

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
