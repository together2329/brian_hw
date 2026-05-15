#!/usr/bin/env python3
"""Generic FL-vs-RTL scoreboard runtime for SSOT-derived testbenches.

Generated TBs should use this helper instead of hand-duplicating expected
behavior.  The helper loads:

- <ip>/verify/equivalence_goals.json
- <ip>/model/functional_model.py

and emits:

- <ip>/sim/scoreboard_events.jsonl

It is intentionally protocol-neutral.  A protocol-specific driver/monitor is
still responsible for converting DUT activity into a stimulus dictionary and an
rtl_observed dictionary.
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import re
import time
from pathlib import Path
from typing import Any


SCOREBOARD_FIELDS = [
    "goal_id",
    "scenario_id",
    "cycle",
    "stimulus",
    "fl_expected",
    "rtl_observed",
    "passed",
    "mismatch",
    "coverage_refs",
]


def _load_json(path: Path) -> dict[str, Any]:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"cannot parse {path}: {exc}") from exc
    if not isinstance(doc, dict):
        raise RuntimeError(f"{path} root must be a JSON object")
    return doc


def _norm(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def _word_tokens(value: Any) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", str(value or "").lower()))


def _deep_equal(left: Any, right: Any) -> bool:
    if isinstance(left, dict) and isinstance(right, dict):
        return left == right
    return left == right


def _dict_overlap_compare(expected: dict[str, Any], observed: dict[str, Any]) -> tuple[bool | None, str]:
    ignored = {"transaction_id", "transaction_name", "kind", "state", "state_updates", "reg", "addr"}
    compared = []
    mismatches = []
    for key, exp_value in expected.items():
        if key in ignored:
            continue
        if key not in observed:
            continue
        compared.append(key)
        if not _deep_equal(exp_value, observed.get(key)):
            mismatches.append(f"{key}: expected={exp_value!r} observed={observed.get(key)!r}")
    if not compared:
        return None, "no comparable overlapping observable keys"
    if mismatches:
        return False, "; ".join(mismatches[:8])
    return True, ""


def _expected_observable_view(
    model_result: dict[str, Any],
    observed: dict[str, Any],
    fl_expected: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Flatten FL result fields and add protocol-neutral observable aliases.

    Functional models can return architectural fields such as ``resp`` or nested
    ``state`` dictionaries, while RTL monitors observe concrete pins such as
    ``pslverr`` or ``busy``.  This view keeps the FL model as the source of
    truth but maps only when the DUT exposes the matching observable.
    """
    view = dict(model_result)
    for nested_key in ("state", "state_updates"):
        nested = model_result.get(nested_key)
        if isinstance(nested, dict):
            for key, value in nested.items():
                view.setdefault(str(key), value)

    fl_expected = fl_expected or {}
    txn = fl_expected.get("transaction") if isinstance(fl_expected.get("transaction"), dict) else {}
    context = " ".join(
        str(value or "")
        for value in (
            fl_expected.get("goal_id"),
            txn.get("kind"),
            txn.get("scenario_id"),
            txn.get("op"),
        )
    ).lower()
    is_memory = "memory" in context or "mem_" in context
    is_reset = "reset" in context
    register_hint_keys = {"reg", "addr_or_name", "paddr", "pwrite", "psel", "penable"}
    # Authoritative signal: the goal_id itself encodes scope. A goal id starting
    # with ``eq_register_`` is a register-access goal; anything else (transaction,
    # scenario, module-equivalence, …) is not, even if the boilerplate stimulus
    # carries ``addr_or_name``. Without this guard, ``resp`` from every
    # transaction maps to ``pready=1``, which then mismatches the idle APB bus
    # during non-register stimulus and fails goals that have no register intent.
    goal_id_lower = str(fl_expected.get("goal_id") or "").lower()
    goal_is_register = goal_id_lower.startswith("eq_register_")
    is_register = (
        goal_is_register
        or (
            not is_reset
            and not goal_id_lower.startswith("eq_transaction_")
            and not goal_id_lower.startswith("eq_scenario_")
            and (
                any(token in context for token in ("csr", "register", "control_status", "apb"))
                or any(key in txn for key in register_hint_keys)
                or any(key in model_result for key in {"reg", "addr_or_name"})
            )
        )
    )

    if "resp" in model_result:
        resp = model_result.get("resp")
        if is_register and not is_memory and "pslverr" in observed:
            view.setdefault("pslverr", 0 if resp in {0, "0", False} else 1)
        if is_register and not is_memory and "pready" in observed:
            view.setdefault("pready", 1)

    is_write = bool(model_result.get("write"))
    is_read = bool(model_result.get("read"))
    if is_memory and is_write:
        if "axi_awvalid" in observed:
            view.setdefault("axi_awvalid", 1)
        if "axi_wvalid" in observed:
            view.setdefault("axi_wvalid", 1)
    if is_memory and is_read:
        if "axi_arvalid" in observed:
            view.setdefault("axi_arvalid", 1)
    if is_register and is_read and "prdata" in observed and "value" in model_result:
            view.setdefault("prdata", model_result.get("value"))
    return view


def _normal_expr(expr: Any) -> str:
    text = str(expr or "").strip()
    text = text.replace("&&", " and ").replace("||", " or ")
    return re.sub(r"(?<![=!<>])!(?!=)", " not ", text)


def _expr_names(expr: Any) -> set[str]:
    try:
        node = ast.parse(_normal_expr(expr), mode="eval")
    except Exception:
        return set()
    return {item.id for item in ast.walk(node) if isinstance(item, ast.Name)}


def _rule_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [{"name": str(key), "expr": expr} for key, expr in value.items()]
    return [item for item in value or [] if isinstance(item, dict)]


class EquivalenceScoreboard:
    """Small adapter between generated TB monitors and the SSOT FunctionalModel."""

    def __init__(
        self,
        ip: str,
        root: str | Path = ".",
        events_path: str | Path | None = None,
        *,
        reset_events: bool = False,
    ) -> None:
        self.ip = ip
        self.root = Path(root).resolve()
        self.ip_dir = self.root / ip
        self.goals_path = self.ip_dir / "verify" / "equivalence_goals.json"
        self.model_path = self.ip_dir / "model" / "functional_model.py"
        self.events_path = Path(events_path) if events_path else self.ip_dir / "sim" / "scoreboard_events.jsonl"
        if not self.events_path.is_absolute():
            self.events_path = self.root / self.events_path

        self.goals_doc = _load_json(self.goals_path)
        self.goals = self._load_goals()
        self.required_goal_ids = {gid for gid, goal in self.goals.items() if goal.get("blocked") is not True}
        self.covered_goal_ids: set[str] = set()
        self.model = self._load_model()
        self.model_transaction_aliases = self._model_transaction_aliases()

        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        if reset_events:
            self.events_path.write_text("", encoding="utf-8")

    def _load_goals(self) -> dict[str, dict[str, Any]]:
        raw_goals = self.goals_doc.get("goals")
        if not isinstance(raw_goals, list):
            raise RuntimeError(f"{self.goals_path} missing goals[]")
        goals: dict[str, dict[str, Any]] = {}
        for idx, goal in enumerate(raw_goals):
            if not isinstance(goal, dict):
                raise RuntimeError(f"{self.goals_path} goals[{idx}] is not an object")
            gid = str(goal.get("goal_id") or "").strip()
            if not gid:
                raise RuntimeError(f"{self.goals_path} goals[{idx}] missing goal_id")
            if gid in goals:
                raise RuntimeError(f"{self.goals_path} duplicate goal_id {gid}")
            goals[gid] = goal
        return goals

    def _load_model(self) -> Any:
        if not self.model_path.is_file():
            raise RuntimeError(f"missing generated FunctionalModel: {self.model_path}")
        spec = importlib.util.spec_from_file_location(f"{self.ip}_functional_model", self.model_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot import generated FunctionalModel: {self.model_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.model_module = module
        model_cls = getattr(module, "FunctionalModel", None)
        if model_cls is None:
            raise RuntimeError(f"{self.model_path} does not define FunctionalModel")
        return model_cls()

    def _model_transaction_aliases(self) -> dict[str, str]:
        aliases: dict[str, str] = {}
        try:
            txs = self.model._transactions()  # type: ignore[attr-defined]
        except Exception:
            txs = []
        for tx in txs if isinstance(txs, list) else []:
            if not isinstance(tx, dict):
                continue
            preferred = str(tx.get("id") or tx.get("name") or "").strip()
            for value in (tx.get("id"), tx.get("name")):
                key = _norm(value)
                if key and preferred:
                    aliases[key] = preferred
        return aliases

    def _best_model_kind(self, goal: dict[str, Any], stimulus: dict[str, Any]) -> str:
        explicit = stimulus.get("kind") or stimulus.get("op") or stimulus.get("transaction")
        if _norm(explicit) in self.model_transaction_aliases:
            return self.model_transaction_aliases[_norm(explicit)]

        contract = goal.get("stimulus_contract") if isinstance(goal.get("stimulus_contract"), dict) else {}
        candidates = [contract.get("transaction_type"), goal.get("goal_id"), goal.get("title"), goal.get("kind")]
        text = " ".join(
            str(item)
            for item in candidates
            + goal.get("ssot_refs", [])
            + goal.get("pass_criteria", [])
            if item is not None
        ).lower()
        text_tokens = _word_tokens(text)

        for candidate in candidates:
            key = _norm(candidate)
            if key in self.model_transaction_aliases:
                return self.model_transaction_aliases[key]

        text_norm = _norm(text)
        for key, preferred in sorted(self.model_transaction_aliases.items(), key=lambda item: len(item[0]), reverse=True):
            if key and (key in text_norm or key.replace("_", " ") in text):
                return preferred

        goal_kind = _norm(goal.get("kind"))
        if "reset" in text or goal_kind == "reset":
            for preferred in ("fm_reset", "reset"):
                key = _norm(preferred)
                if key in self.model_transaction_aliases:
                    return self.model_transaction_aliases[key]
        if goal_kind == "register":
            for preferred in ("fm_csr", "control_status_access", "csr"):
                key = _norm(preferred)
                if key in self.model_transaction_aliases:
                    return self.model_transaction_aliases[key]
        if goal_kind in {"protocol", "timing", "datapath", "state", "memory", "interrupt", "coverage", "error"}:
            for preferred in ("fm_primary", "primary_behavior"):
                key = _norm(preferred)
                if key in self.model_transaction_aliases:
                    return self.model_transaction_aliases[key]

        token_map = [
            (("reset", "rst"), ("fm_reset", "reset")),
            (("csr", "register", "control", "status", "apb", "read", "write"), ("fm_csr", "control_status_access", "csr")),
            (("memory", "protocol", "timing", "scenario", "transaction", "datapath", "packet", "axis"), ("fm_primary", "primary_behavior")),
        ]
        for tokens, preferred_keys in token_map:
            if any(token in text_tokens for token in tokens):
                for preferred in preferred_keys:
                    key = _norm(preferred)
                    if key in self.model_transaction_aliases:
                        return self.model_transaction_aliases[key]

        if "primary" in text_tokens:
            for key, preferred in self.model_transaction_aliases.items():
                if not any(token in key for token in ("reset", "clear", "hold", "idle", "error")):
                    return preferred

        if self.model_transaction_aliases:
            return next(iter(self.model_transaction_aliases.values()))
        return str(contract.get("transaction_type") or goal.get("goal_id") or "unknown")

    def transaction_for_goal(
        self,
        goal_id: str,
        stimulus: dict[str, Any] | None = None,
        scenario_id: str = "",
    ) -> dict[str, Any]:
        goal = self.goals.get(goal_id)
        if goal is None:
            raise KeyError(f"unknown equivalence goal_id {goal_id}")
        txn = dict(stimulus or {})
        txn.setdefault("goal_id", goal_id)
        if scenario_id:
            txn.setdefault("scenario_id", scenario_id)
        txn["kind"] = self._best_model_kind(goal, txn)
        self._normalize_goal_transaction(goal, txn)
        self._seed_rule_fields(txn)
        return txn

    def _normalize_goal_transaction(self, goal: dict[str, Any], txn: dict[str, Any]) -> None:
        goal_kind = _norm(goal.get("kind"))
        contract = goal.get("stimulus_contract") if isinstance(goal.get("stimulus_contract"), dict) else {}
        tx_type = _norm(contract.get("transaction_type"))
        if goal_kind == "register" or tx_type in {"csr_access", "register_access", "control_status_access"}:
            raw_op = _norm(txn.get("op") or "")
            if raw_op not in {"read", "rd", "csr_read", "write", "wr", "csr_write"}:
                txn["op"] = "read" if "read" in _norm(goal.get("title")) and "write" not in _norm(goal.get("title")) else "write"
            if "addr_or_name" in txn:
                txn.setdefault("addr", txn["addr_or_name"])
                txn.setdefault("reg", txn["addr_or_name"])
            txn.setdefault("addr", 0)
            txn.setdefault("reg", txn.get("addr", 0))
            txn.setdefault("data", txn.get("value", 1))
            txn.setdefault("value", txn.get("data", 1))
        elif goal_kind == "memory" or tx_type in {"memory_access", "mem_access"}:
            raw_op = _norm(txn.get("op") or "")
            if raw_op not in {"read", "rd", "write", "wr"}:
                txn["op"] = "read" if "read" in _norm(goal.get("title")) and "write" not in _norm(goal.get("title")) else "write"
            if "addr_or_name" in txn:
                txn.setdefault("addr", txn["addr_or_name"])
            txn.setdefault("addr", 0)
            txn.setdefault("data", txn.get("value", 1))

    def _transaction_doc_for_kind(self, kind: Any) -> dict[str, Any]:
        try:
            txs = self.model._transactions()  # type: ignore[attr-defined]
        except Exception:
            txs = []
        for tx in txs if isinstance(txs, list) else []:
            if not isinstance(tx, dict):
                continue
            aliases = {_norm(tx.get("id")), _norm(tx.get("name"))}
            if _norm(kind) in aliases:
                return tx
        return {}

    def _seed_rule_fields(self, txn: dict[str, Any]) -> None:
        tx = self._transaction_doc_for_kind(txn.get("kind"))
        output_rules = _rule_items(tx.get("output_rules"))
        state_updates = _rule_items(tx.get("state_updates"))
        names = _expr_names(tx.get("sample_condition", ""))
        for rule in output_rules + state_updates:
            names.update(_expr_names(rule.get("expr", rule.get("expression", rule.get("value", "")))))
        output_names = {
            str(rule.get("name") or rule.get("output") or rule.get("port"))
            for rule in output_rules
            if rule.get("name") or rule.get("output") or rule.get("port")
        }
        update_names = {
            str(rule.get("name") or rule.get("state"))
            for rule in state_updates
            if rule.get("name") or rule.get("state")
        }
        known = set(getattr(self.model, "params", {}))
        known.update(getattr(self.model, "state", {}))
        known.update(getattr(self.model, "registers", {}))
        known.update(output_names)
        known.update(update_names)
        known.update({"true", "false", "True", "False", "and", "or", "not"})
        helpers_fn = getattr(self.model_module, "_default_rule_helpers", None)
        if callable(helpers_fn):
            try:
                known.update(helpers_fn().keys())
            except Exception:
                pass
        known.update({"read_mux", "reduction_or"})
        for name in sorted(names - known):
            if name and name not in txn:
                txn[name] = len(txn) + 1

    def expected_for_goal(
        self,
        goal_id: str,
        stimulus: dict[str, Any] | None = None,
        scenario_id: str = "",
    ) -> dict[str, Any]:
        goal = self.goals.get(goal_id)
        if goal is None:
            raise KeyError(f"unknown equivalence goal_id {goal_id}")
        txn = self.transaction_for_goal(goal_id, stimulus, scenario_id)
        try:
            model_result = self.model.apply(txn)
            model_error = ""
        except Exception as exc:
            model_result = {}
            model_error = str(exc)
        expected_contract = goal.get("expected_contract") if isinstance(goal.get("expected_contract"), dict) else {}
        return {
            "goal_id": goal_id,
            "model_api": "FunctionalModel.apply",
            "transaction": txn,
            "model_result": model_result,
            "model_error": model_error,
            "observables": expected_contract.get("observables") or [],
            "latency": expected_contract.get("latency", ""),
            "state_updates": expected_contract.get("state_updates") or [],
            "error_policy": expected_contract.get("error_policy", ""),
            "ssot_refs": goal.get("ssot_refs") or [],
        }

    def compare(self, fl_expected: dict[str, Any], rtl_observed: Any) -> tuple[bool, str]:
        if not isinstance(rtl_observed, dict):
            return False, "rtl_observed must be a dictionary of named observables"
        if not rtl_observed:
            return False, "rtl_observed must contain DUT signal observations"
        model_result = fl_expected.get("model_result")
        if set(rtl_observed) == {"model_result"}:
            return False, "rtl_observed must be DUT signal observations, not FunctionalModel model_result"
        if rtl_observed == fl_expected:
            return False, "rtl_observed must not copy the full fl_expected payload"
        if isinstance(model_result, dict):
            verdict, mismatch = _dict_overlap_compare(_expected_observable_view(model_result, rtl_observed, fl_expected), rtl_observed)
            if verdict is not None:
                return verdict, mismatch
        return False, "no comparable RTL observable for FunctionalModel result"

    def record(
        self,
        goal_id: str,
        *,
        scenario_id: str = "",
        cycle: int | float = 0,
        stimulus: dict[str, Any] | None = None,
        rtl_observed: dict[str, Any] | None = None,
        passed: bool | None = None,
        mismatch: str = "",
        coverage_refs: list[str] | None = None,
    ) -> dict[str, Any]:
        goal = self.goals.get(goal_id)
        if goal is None:
            raise KeyError(f"unknown equivalence goal_id {goal_id}")
        if goal.get("blocked"):
            raise RuntimeError(f"equivalence goal {goal_id} is blocked: {goal.get('blocker')}")

        fl_expected = self.expected_for_goal(goal_id, stimulus or {}, scenario_id)
        observed = dict(rtl_observed or {})
        if passed is None:
            passed, auto_mismatch = self.compare(fl_expected, observed)
            mismatch = mismatch or auto_mismatch
        elif passed is True:
            mismatch = ""
        elif not mismatch:
            mismatch = "scoreboard marked failure without mismatch detail"

        row = {
            "goal_id": goal_id,
            "scope": goal.get("scope") or {"level": "top"},
            "scenario_id": scenario_id or str((stimulus or {}).get("scenario_id") or goal_id),
            "cycle": cycle,
            "stimulus": stimulus or {},
            "fl_expected": fl_expected,
            "rtl_observed": observed,
            "passed": bool(passed),
            "mismatch": mismatch,
            "coverage_refs": coverage_refs if coverage_refs is not None else list(goal.get("coverage_refs") or []),
        }
        self._validate_row(row)
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
        self.covered_goal_ids.add(goal_id)
        return row

    def _validate_row(self, row: dict[str, Any]) -> None:
        missing = [key for key in SCOREBOARD_FIELDS if key not in row]
        if missing:
            raise RuntimeError(f"scoreboard row missing fields: {', '.join(missing)}")
        if row["goal_id"] not in self.goals:
            raise RuntimeError(f"unknown scoreboard goal_id {row['goal_id']}")
        if not isinstance(row["passed"], bool):
            raise RuntimeError("scoreboard row passed must be boolean")
        if not isinstance(row["mismatch"], str):
            raise RuntimeError("scoreboard row mismatch must be string")
        if row["passed"] is False and not row["mismatch"].strip():
            raise RuntimeError("failing scoreboard row must include mismatch text")
        if row["passed"] is True and row["mismatch"].strip():
            raise RuntimeError("passing scoreboard row must not include mismatch text")
        if not isinstance(row["coverage_refs"], list):
            raise RuntimeError("scoreboard row coverage_refs must be a list")

    def missing_required_goals(self) -> list[str]:
        return sorted(self.required_goal_ids - self.covered_goal_ids)

    def assert_all_required_goals_observed(self) -> None:
        missing = self.missing_required_goals()
        if missing:
            preview = ", ".join(missing[:12])
            suffix = "" if len(missing) <= 12 else f", ... +{len(missing) - 12}"
            raise AssertionError(f"missing scoreboard evidence for required goals: {preview}{suffix}")

    def self_check(self) -> dict[str, Any]:
        checked = 0
        unsupported = 0
        model_errors = 0
        samples: list[dict[str, Any]] = []
        for gid in sorted(self.required_goal_ids):
            goal = self.goals[gid]
            stimulus: dict[str, Any] = {"scenario_id": f"self_{gid}"}
            kind = self._best_model_kind(goal, stimulus)
            stimulus["kind"] = kind

            required_fields: list[str] = []
            contract = goal.get("stimulus_contract") if isinstance(goal.get("stimulus_contract"), dict) else {}
            for field in contract.get("required_fields") or []:
                if str(field).strip() and str(field) not in required_fields:
                    required_fields.append(str(field))
            try:
                txs = self.model._transactions()  # type: ignore[attr-defined]
            except Exception:
                txs = []
            tx = self._transaction_doc_for_kind(kind)
            for field in tx.get("required_fields") or []:
                if str(field).strip() and str(field) not in required_fields:
                    required_fields.append(str(field))
            for idx, field in enumerate(required_fields, start=1):
                if field in stimulus:
                    continue
                low = field.lower()
                if field == "kind":
                    stimulus[field] = kind
                elif field == "scenario_id":
                    stimulus[field] = f"self_{gid}"
                elif low in {"cycle"}:
                    stimulus[field] = idx
                elif low in {"observed_signals", "signals"}:
                    stimulus[field] = {}
                else:
                    stimulus[field] = idx

            expected = self.expected_for_goal(gid, stimulus, f"self_{gid}")
            checked += 1
            result = expected.get("model_result")
            if isinstance(result, dict) and result.get("resp") == 2 and result.get("error") == "unsupported_transaction":
                unsupported += 1
            if expected.get("model_error"):
                model_errors += 1
            if len(samples) < 8:
                samples.append({
                    "goal_id": gid,
                    "kind": expected.get("transaction", {}).get("kind"),
                    "model_result": result,
                    "model_error": expected.get("model_error"),
                })
        return {
            "ip": self.ip,
            "goals": len(self.goals),
            "required_goals": len(self.required_goal_ids),
            "checked": checked,
            "unsupported_transactions": unsupported,
            "model_errors": model_errors,
            "events_path": str(self.events_path),
            "sample": samples,
            "passed": checked > 0 and model_errors == 0,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ip")
    parser.add_argument("--root", default=".")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()

    scoreboard = EquivalenceScoreboard(args.ip, args.root)
    if args.self_check:
        report = scoreboard.self_check()
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report.get("passed") else 1
    print(f"loaded {len(scoreboard.goals)} equivalence goals for {args.ip}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
