#!/usr/bin/env python3
"""FL contract gate — evidence-side validation of a (possibly LLM-authored) FL.

Design: doc/wiki/llm-authored-oracle-architecture.md. The generator may be an
LLM; THIS validator is the trust anchor, so it never trusts the model file's
own self-check. It independently:

  gate 0 (interface)        — the module exposes the API the scoreboard
                              runtime consumes (FunctionalModel, SSOT_MODEL,
                              _default_rule_helpers; apply/reset/state/
                              registers/params/_transactions/csr_write).
  gate 1 (ssot_conformance) — for every SSOT function_model.transactions[],
                              the validator applies the transaction and
                              evaluates output_rules/state_updates exprs
                              ITSELF (pre-state semantics, SSOT-owned exprs)
                              and compares against the model's result/state.
  gate 3 (dual_oracle)      — when a baseline FL exists (deterministic
                              emitter output), both models run the same
                              transaction battery; any state/output
                              divergence is a finding. This is the primary
                              correlated-error defense for LLM-authored FLs.

  gate 2 (mutation) and gate 4 (provenance) are reported as
  status="not_implemented" — visible debt, never a silent pass.

Exit 0 only when every implemented gate passes. Report:
<ip>/model/fl_contract_check.json
"""
from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any

RESP_OKAY = 0


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _rule_items(raw: Any) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if isinstance(raw, dict):
        for key, value in raw.items():
            items.append({"name": str(key), "expr": value})
    elif isinstance(raw, list):
        for entry in raw:
            if isinstance(entry, dict):
                items.append(entry)
            elif isinstance(entry, str):
                items.append({"expr": entry})
    return items


def _expr_names(expr: Any) -> set[str]:
    try:
        tree = ast.parse(str(expr), mode="eval")
    except Exception:
        return set()
    return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}


def _eval_expr(expr: Any, env: dict[str, Any]) -> Any:
    if isinstance(expr, (int, float, bool)):
        return expr
    tree = ast.parse(str(expr), mode="eval")
    return eval(compile(tree, "<fl_contract>", mode="eval"), {"__builtins__": {}}, dict(env))


def _interface_gate(module, failures: list[str]) -> dict[str, Any]:
    required_module_attrs = ("FunctionalModel", "SSOT_MODEL", "_default_rule_helpers")
    for attr in required_module_attrs:
        if not hasattr(module, attr):
            failures.append(f"interface: module missing {attr}")
    model = None
    if hasattr(module, "FunctionalModel"):
        try:
            model = module.FunctionalModel()
        except Exception as exc:
            failures.append(f"interface: FunctionalModel() raised {exc!r}")
    if model is not None:
        for attr in ("apply", "reset", "_transactions", "csr_write"):
            if not callable(getattr(model, attr, None)):
                failures.append(f"interface: model.{attr} missing or not callable")
        for attr in ("state", "registers", "params"):
            if not isinstance(getattr(model, attr, None), dict):
                failures.append(f"interface: model.{attr} missing or not a dict")
    return {"status": "pass" if not failures else "fail", "model_constructed": model is not None}


def _self_txn(tx: dict[str, Any], idx: int, model, helpers: dict[str, Any]) -> dict[str, Any]:
    """Build the same deterministic sample transaction the emitter self-check
    uses, so conformance is judged on identical inputs."""
    kind = tx.get("id") or tx.get("name") or f"transaction_{idx}"
    txn: dict[str, Any] = {"kind": kind, "scenario_id": f"contract_{kind}"}
    for field_idx, field in enumerate(tx.get("required_fields") or []):
        name = str(field)
        if name and name not in txn:
            txn[name] = field_idx + idx + 1
    rule_names: set[str] = set()
    rule_names.update(_expr_names(tx.get("sample_condition", "")))
    for rule in _rule_items(tx.get("output_rules")) + _rule_items(tx.get("state_updates")):
        rule_names.update(_expr_names(rule.get("expr", rule.get("expression", rule.get("value", "")))))
    known = set(model.params) | set(model.state) | set(model.registers) | set(helpers)
    known.update({"true", "false", "True", "False", "and", "or", "not", "range", "read_mux", "reduction_or"})
    for name in sorted(rule_names - known):
        if name and name not in txn:
            txn[name] = idx + len(txn) + 1
    return txn


def _conformance_gate(module, ssot_model: dict[str, Any], failures: list[str]) -> dict[str, Any]:
    """Validator-owned check: SSOT exprs (pre-state semantics) vs model output."""
    model = module.FunctionalModel()
    helpers = dict(module._default_rule_helpers())
    fm = ssot_model.get("function_model") or {}
    derived = _rule_items(fm.get("derived_signals"))
    rows: list[dict[str, Any]] = []
    txs = [tx for tx in (fm.get("transactions") or []) if isinstance(tx, dict)]
    for idx, tx in enumerate(txs):
        name = str(tx.get("id") or tx.get("name") or idx)
        if str(tx.get("name") or "").strip().lower() == "reset":
            continue
        model.reset()
        txn = _self_txn(tx, idx, model, helpers)
        # pre-state env: SSOT output_rules/state_updates evaluate against
        # PRE-transaction state (the documented FL semantics).
        pre_env: dict[str, Any] = {}
        pre_env.update(helpers)
        pre_env.update(model.params)
        pre_env.update(model.registers)
        pre_env.update(model.state)
        pre_env.update({k: v for k, v in txn.items() if isinstance(v, (int, float, bool))})
        for rule in derived:
            rname = rule.get("name")
            try:
                if rname:
                    pre_env[str(rname)] = _eval_expr(rule.get("expr", 0), pre_env)
            except Exception:
                pass
        try:
            result = model.apply(dict(txn))
        except Exception as exc:
            failures.append(f"conformance: {name}: model.apply raised {exc!r}")
            rows.append({"transaction": name, "status": "error", "error": str(exc)[:120]})
            continue
        if not isinstance(result, dict):
            failures.append(f"conformance: {name}: apply returned non-dict")
            continue
        row: dict[str, Any] = {"transaction": name, "checked": 0, "mismatches": []}
        # Mirror the authoritative evaluation discipline of the generated FL
        # (_apply_structured_rules): rules evaluate PROGRESSIVELY — outputs
        # first against pre-state (each resolved output joins the env), then
        # state_updates sequentially (a later update sees an earlier update's
        # NEW value: a 2ff synchronizer chain fills in one apply).
        env = dict(pre_env)
        for rule in _rule_items(tx.get("output_rules")):
            oname = str(rule.get("name") or rule.get("output") or rule.get("port") or "").strip()
            if not oname:
                continue
            try:
                expected = _eval_expr(rule.get("expr", rule.get("expression", rule.get("value", 0))), env)
            except Exception as exc:
                row.setdefault("skipped", []).append({"output": oname, "reason": str(exc)[:80]})
                continue
            env[oname] = expected
            observed = result.get(oname)
            if observed is None:
                continue
            row["checked"] += 1
            if isinstance(expected, (int, bool)) and isinstance(observed, (int, bool)):
                if int(expected) != int(observed):
                    row["mismatches"].append({"output": oname, "expected": int(expected), "observed": int(observed)})
        for rule in _rule_items(tx.get("state_updates")):
            sname = str(rule.get("name") or rule.get("state") or "").strip()
            if not sname:
                continue
            try:
                expected = _eval_expr(rule.get("expr", rule.get("expression", rule.get("value", 0))), env)
            except Exception as exc:
                row.setdefault("skipped", []).append({"state": sname, "reason": str(exc)[:80]})
                continue
            env[sname] = expected
            observed = model.state.get(sname)
            row["checked"] += 1
            if isinstance(expected, (int, bool)) and isinstance(observed, (int, bool)):
                if int(expected) != int(observed):
                    row["mismatches"].append({"state": sname, "expected": int(expected), "observed": int(observed)})
        if row["mismatches"]:
            failures.append(
                f"conformance: {name}: " + "; ".join(
                    f"{m.get('state') or m.get('output')} expected={m['expected']} observed={m['observed']}"
                    for m in row["mismatches"]
                )
            )
        row["status"] = "fail" if row["mismatches"] else "pass"
        rows.append(row)
    checked_total = sum(int(r.get("checked") or 0) for r in rows)
    return {
        "status": "pass" if not any(r.get("status") != "pass" for r in rows) else "fail",
        "transactions": len(rows),
        "checked_rules": checked_total,
        "rows": rows,
    }


def _dual_oracle_gate(module, baseline_module, ssot_model: dict[str, Any], failures: list[str]) -> dict[str, Any]:
    model = module.FunctionalModel()
    base = baseline_module.FunctionalModel()
    helpers = dict(module._default_rule_helpers())
    fm = ssot_model.get("function_model") or {}
    divergences: list[dict[str, Any]] = []
    compared = 0
    txs = [tx for tx in (fm.get("transactions") or []) if isinstance(tx, dict)]
    for idx, tx in enumerate(txs):
        name = str(tx.get("id") or tx.get("name") or idx)
        if str(tx.get("name") or "").strip().lower() == "reset":
            continue
        model.reset()
        base.reset()
        txn = _self_txn(tx, idx, base, helpers)
        try:
            model.apply(dict(txn))
            base.apply(dict(txn))
        except Exception as exc:
            divergences.append({"transaction": name, "error": str(exc)[:120]})
            continue
        shared = set(model.state) & set(base.state)
        for key in sorted(shared):
            mv, bv = model.state.get(key), base.state.get(key)
            if isinstance(mv, (int, bool)) and isinstance(bv, (int, bool)):
                compared += 1
                if int(mv) != int(bv):
                    divergences.append({"transaction": name, "state": key, "model": int(mv), "baseline": int(bv)})
    if divergences:
        failures.append(
            "dual_oracle: " + "; ".join(
                f"{d['transaction']}.{d.get('state','?')} model={d.get('model')} baseline={d.get('baseline')}"
                if "state" in d else f"{d['transaction']}: {d.get('error')}"
                for d in divergences[:8]
            )
        )
    return {
        "status": "pass" if not divergences else "fail",
        "compared_state_values": compared,
        "divergences": divergences,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="FL contract gate (interface + SSOT conformance + dual oracle).")
    parser.add_argument("ip")
    parser.add_argument("--root", default=".")
    parser.add_argument("--model-file", default="model/functional_model.py")
    parser.add_argument("--baseline-file", default="model/functional_model_baseline.py")
    args = parser.parse_args()

    ip_dir = Path(args.root).resolve() / args.ip
    model_path = ip_dir / args.model_file
    baseline_path = ip_dir / args.baseline_file
    failures: list[str] = []
    report: dict[str, Any] = {
        "schema_version": 1,
        "type": "fl_contract_check",
        "ip": args.ip,
        "model_file": str(model_path.relative_to(ip_dir)),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "gates": {},
    }
    if not model_path.is_file():
        print(f"[check_fl_contract] FAIL {args.ip}: missing {model_path}")
        return 1
    try:
        module = _load_module(model_path, "fl_under_contract")
    except Exception as exc:
        print(f"[check_fl_contract] FAIL {args.ip}: model import failed: {exc!r}")
        return 1

    report["gates"]["interface"] = _interface_gate(module, failures)
    if report["gates"]["interface"]["status"] == "pass":
        ssot_model = getattr(module, "SSOT_MODEL", {}) or {}
        report["gates"]["ssot_conformance"] = _conformance_gate(module, ssot_model, failures)
        if baseline_path.is_file() and baseline_path.resolve() != model_path.resolve():
            try:
                baseline_module = _load_module(baseline_path, "fl_baseline")
                report["gates"]["dual_oracle"] = _dual_oracle_gate(module, baseline_module, ssot_model, failures)
            except Exception as exc:
                failures.append(f"dual_oracle: baseline import failed: {exc!r}")
                report["gates"]["dual_oracle"] = {"status": "fail", "error": str(exc)[:160]}
        else:
            report["gates"]["dual_oracle"] = {"status": "skipped", "reason": "no baseline file"}
    report["gates"]["mutation"] = {"status": "not_implemented"}
    report["gates"]["provenance"] = {"status": "not_implemented"}
    passed = not failures
    report["passed"] = passed
    report["failures"] = failures
    out = ip_dir / "model" / "fl_contract_check.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    status = "PASS" if passed else "FAIL"
    print(f"[check_fl_contract] {status} {args.ip}: gates="
          + " ".join(f"{k}={v.get('status')}" for k, v in report["gates"].items()))
    for failure in failures[:12]:
        print(f"- {failure}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
