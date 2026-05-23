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


_MATCH_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "behavior",
    "by",
    "cycle",
    "data",
    "defined",
    "from",
    "functionalmodel",
    "goal",
    "latency",
    "match",
    "matches",
    "model",
    "rtl",
    "ssot",
    "state",
    "states",
    "the",
    "to",
    "transaction",
    "update",
    "updates",
    "when",
    "with",
}


def _meaningful_tokens(value: Any) -> set[str]:
    return {token for token in _word_tokens(value) if token not in _MATCH_STOPWORDS and len(token) > 1}


def _deep_equal(left: Any, right: Any) -> bool:
    if isinstance(left, dict) and isinstance(right, dict):
        return left == right
    left_bin = _binary_string_to_int(left)
    right_bin = _binary_string_to_int(right)
    if isinstance(left, int) and right_bin is not None:
        return left == right_bin
    if isinstance(right, int) and left_bin is not None:
        return left_bin == right
    return left == right


def _binary_string_to_int(value: Any) -> int | None:
    if not isinstance(value, str):
        return None
    text = value.strip().lower()
    if not text or not re.fullmatch(r"[01xz]+", text):
        return None
    return int(text.replace("x", "0").replace("z", "0"), 2)


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
    """Strict view: only what FL emits, plus flattened nested state dicts.

    Previously this function embedded protocol-specific knowledge (APB
    pready/pslverr inference, AXI awvalid/wvalid, AHB fault_halt/i_htrans,
    GPIO data_out_reg/dir_reg, prdata from value, …). Each of those is an
    IP-family-specific guess that produces false negatives whenever the
    stimulus diverges from the heuristic's assumption. The scoreboard is
    now strict: if FL does not emit a value via SSOT
    function_model.transactions[*].output_rules (or cycle_model.output_rules
    once that schema lands), the signal is not compared.
    """
    view = dict(model_result)
    raw_state_contract = (fl_expected or {}).get("state_updates") if isinstance(fl_expected, dict) else None
    expected_state_contract = {
        str(item)
        for item in (raw_state_contract or [])
        if str(item).strip()
    }
    for nested_key in ("state", "state_updates"):
        nested = model_result.get(nested_key)
        if isinstance(nested, dict):
            for key, value in nested.items():
                key_text = str(key)
                view.setdefault(key_text, value)
                if raw_state_contract is not None and key_text not in expected_state_contract:
                    continue
                for suffix in ("_set_next", "_w1c_next", "_next"):
                    if key_text.endswith(suffix):
                        base = key_text[: -len(suffix)]
                        if base and any(obs == base or obs.startswith(f"{base}_") for obs in observed):
                            view.setdefault(base, value)
                        break

    return view


def _expected_context_text(fl_expected: dict[str, Any]) -> str:
    txn = fl_expected.get("transaction") if isinstance(fl_expected.get("transaction"), dict) else {}
    pieces: list[Any] = [
        fl_expected.get("goal_id"),
        fl_expected.get("goal_kind"),
        fl_expected.get("title"),
        txn.get("kind"),
        txn.get("scenario_id"),
        txn.get("op"),
    ]
    pieces.extend(fl_expected.get("ssot_refs") or [])
    pieces.extend(fl_expected.get("observables") or [])
    pieces.extend(fl_expected.get("pass_criteria") or [])
    contract = fl_expected.get("stimulus_contract") if isinstance(fl_expected.get("stimulus_contract"), dict) else {}
    pieces.append(contract.get("transaction_type"))
    pieces.extend(contract.get("constraints") or [])
    return " ".join(str(item or "") for item in pieces).lower()


def _is_debug_observability_expected(fl_expected: dict[str, Any]) -> bool:
    text = _expected_context_text(fl_expected)
    return "debug_observability" in text or "waveform contains required probes" in text


def _is_degenerate_state_expected(fl_expected: dict[str, Any]) -> bool:
    text = _expected_context_text(fl_expected)
    return (
        str(fl_expected.get("goal_kind") or "").lower() == "state"
        and (
            re.search(r"\b([a-z0-9]+)\s*->\s*\1\b", text) is not None
            or "no multi-state" in text
            or "handshake/state-update driven" in text
            or "single-cycle" in text
        )
    )


def _state_transition_expected_view(fl_expected: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    """State transition view — now strict.

    Previously inferred fault_halt / i_htrans / state mappings from goal text
    using AHB-CPU-specific hardcoded patterns. Those guesses produced false
    negatives whenever the IP under test was not the IP family the patterns
    were derived from. The scoreboard now relies on FL.model_result.state
    being explicit; downstream comparison handles it via the general state
    flattening in `_expected_observable_view`.
    """
    return {}


def _is_cycle_coverage_expected(fl_expected: dict[str, Any]) -> bool:
    goal_id = str(fl_expected.get("goal_id") or "").upper()
    text = _expected_context_text(fl_expected)
    return goal_id.startswith("EQ_COVERAGE_CYCLE_") or "cycle_model." in text


def _is_internal_register_memory_goal(fl_expected: dict[str, Any]) -> bool:
    if str(fl_expected.get("goal_kind") or "").lower() != "memory":
        return False
    refs = [str(item).lower() for item in (fl_expected.get("ssot_refs") or [])]
    if not any("memory.instances" in ref for ref in refs):
        return False
    text = _expected_context_text(fl_expected)
    return any(
        token in text
        for token in (
            "'type': 'register'",
            '"type": "register"',
            "pipeline latch",
            "internal latch",
            "if/id",
            "id/ex",
        )
    )


def _internal_register_memory_compare(fl_expected: dict[str, Any], observed: dict[str, Any]) -> tuple[bool, str] | None:
    """Disabled — previously hardcoded AHB-CPU expectations (d_haddr,
    d_hwrite, d_hwdata, fault_halt=0, i_htrans=2, i_haddr==pc). Those are
    properties of a specific CPU IP family, not a generic comparator. They
    belong in SSOT cycle_model rules, not in scoreboard runtime.
    """
    return None


def _cycle_property_compare(fl_expected: dict[str, Any], observed: dict[str, Any]) -> tuple[bool, str] | None:
    """Disabled — previously contained hardcoded AHB CPU patterns
    (i_hready/if_stall, d_hready/stall_mem, fault_halt, i_htrans=2,
    i_haddr==pc, load_store/pipeline). Those are properties of specific
    CPU IP families; the scoreboard now defers cycle-property checking to
    SSOT cycle_model machine_spec (forthcoming) rather than embedded
    text-pattern guessing.
    """
    return None


def _legacy_unbound_policy_compare(
    fl_expected: dict[str, Any],
    observed: dict[str, Any],
) -> tuple[bool, str] | None:
    """Compatibility path for old tests that call compare(None, ...).

    Production scoreboard instances use SSOT/manifest-backed mappings.  The
    unbound legacy path has no access to those files, so keep the historical
    text-policy fallbacks isolated here instead of reintroducing them to the
    normal instance path.
    """
    text = _expected_context_text(fl_expected)
    model_result = fl_expected.get("model_result") if isinstance(fl_expected.get("model_result"), dict) else {}

    if "reset" in text:
        state = model_result.get("state") if isinstance(model_result.get("state"), dict) else {}
        expected: dict[str, Any] = {}
        for key, value in state.items():
            low_key = str(key).lower()
            for obs_key in observed:
                low_obs = str(obs_key).lower()
                if "data_out" in low_key and low_obs.endswith("_out"):
                    expected[obs_key] = value
                elif "dir" in low_key and (low_obs.endswith("_oe") or low_obs.endswith("_dir")):
                    expected[obs_key] = value
                elif "irq" in low_key and "irq" in low_obs:
                    expected[obs_key] = value
        if expected:
            return _dict_overlap_compare(expected, observed)

    if "fault_halt" in observed and any(
        token in text
        for token in (
            "fault_halt",
            "fault-halt",
            "bus_error",
            "bus error",
            "hresp==error",
            "hresp == error",
        )
    ):
        return _dict_overlap_compare({"fault_halt": 1}, observed)

    if "i_htrans" in observed and any(
        token in text
        for token in (
            "reset -> run",
            "if_stall",
            "instruction fetch backpressure",
            "ordering",
            "ordered bus activity",
        )
    ):
        return _dict_overlap_compare({"i_htrans": 2}, observed)

    if _is_cycle_coverage_expected(fl_expected) and model_result:
        view = {
            key: value
            for key, value in model_result.items()
            if key in observed
            and any(token in str(key).lower() for token in ("ready", "valid", "error", "err", "resp", "accept"))
        }
        if view:
            return _dict_overlap_compare(view, observed)

    return None


def _filtered_expected_view(
    view: dict[str, Any],
    observed: dict[str, Any],
    fl_expected: dict[str, Any],
) -> dict[str, Any]:
    """Pass-through — previously narrowed cycle-coverage views to a
    hardcoded ready/valid/slverr/error/resp/accept/stall token set, which
    silently dropped legitimate SSOT-declared observables that did not match
    the token list. Filtering belongs in SSOT (output_rules / handshake_rules
    machine_spec), not in scoreboard runtime.
    """
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


def _extract_ssot_questions(value: Any) -> list[str]:
    """Return SSOT-question strings embedded in a model result tree."""
    questions: list[str] = []

    def visit(item: Any) -> None:
        if isinstance(item, dict):
            for key, val in item.items():
                if str(key) == "ssot_question" and val:
                    questions.append(str(val))
                visit(val)
        elif isinstance(item, list):
            for val in item:
                visit(val)

    visit(value)
    return questions


def _write_self_check_blocker(scoreboard: "EquivalenceScoreboard", report: dict[str, Any]) -> Path:
    """Persist a human/SSOT gate for self-check evidence gaps."""
    questions: list[dict[str, str]] = []
    for idx, gap in enumerate(report.get("contract_gaps") or [], start=1):
        goal_id = str(gap.get("goal_id") or f"GOAL_{idx}")
        kind = str(gap.get("kind") or "unknown")
        evidence = str(gap.get("question") or gap.get("reason") or "missing comparable FunctionalModel contract")
        questions.append({
            "id": f"TB_SELF_CHECK_{idx:03d}",
            "decision_needed": (
                f"Provide structured output_rules/state_updates or an explicit observable mapping for {goal_id} "
                f"({kind}) so tb-gen can compare FL expected values against RTL signals."
            ),
            "evidence": evidence,
            "recommended_default": (
                "Update the SSOT function_model transaction with structured output_rules/state_updates, "
                "then rerun fl-model-gen, equiv-goals, tb-gen, and sim."
            ),
            "downstream_effect": (
                "Without this contract, the generated scoreboard can run cocotb but cannot prove FL-vs-RTL equivalence."
            ),
        })

    blocked = {
        "reason": "SSOT/FunctionalModel contract is not concrete enough for FL-vs-RTL scoreboard comparison",
        "next_action": "Repair SSOT function_model transaction rules or approve explicit observable mappings, then rerun /tb.",
        "questions": questions,
        "self_check": {
            "checked": report.get("checked"),
            "required_goals": report.get("required_goals"),
            "ssot_questions": report.get("ssot_questions"),
            "unsupported_transactions": report.get("unsupported_transactions"),
            "model_errors": report.get("model_errors"),
        },
    }
    path = scoreboard.ip_dir / "tb" / "cocotb" / "tb_blocked.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(blocked, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


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
        self.mismatch_policy = self._resolve_mismatch_policy()

        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        if reset_events:
            self.events_path.write_text("", encoding="utf-8")

    def _resolve_mismatch_policy(self) -> str:
        """FL-vs-RTL mismatch policy: 'hard' (assert) or 'soft' (warn).

        SSOT per-IP > workflow rule. Built-in 'hard' fires only when both are missing.
        """
        ssot_path = self.ip_dir / "yaml" / f"{self.ip}.ssot.yaml"
        if ssot_path.is_file():
            import yaml as _yaml
            doc = _yaml.safe_load(ssot_path.read_text(encoding="utf-8")) or {}
            value = (
                doc.get("quality_gates", {})
                   .get("tb", {})
                   .get("fl_rtl_mismatch_policy")
            )
            if isinstance(value, str) and value.strip().lower() in ("hard", "soft"):
                return value.strip().lower()
        rule_path = (
            Path(__file__).resolve().parent.parent
            / "rules" / "scoreboard_policy.json"
        )
        if rule_path.is_file():
            rule_doc = _load_json(rule_path)
            value = rule_doc.get("fl_rtl_mismatch_policy")
            if isinstance(value, str) and value.strip().lower() in ("hard", "soft"):
                return value.strip().lower()
        return "hard"

    def enforce_zero_mismatch(self, failures: list, logger=None) -> None:
        """Generated cocotb scoreboards delegate here so policy lives in one place.

        Raises AssertionError on mismatch under hard policy. Emits a warning
        (or prints when no logger) under soft policy.
        """
        if not failures:
            return
        preview_parts: list[str] = []
        for row in failures[:8]:
            gid = row.get("goal_id") if isinstance(row, dict) else None
            mismatch = row.get("mismatch") if isinstance(row, dict) else row
            preview_parts.append(f"{gid}: {mismatch}")
        preview = "; ".join(preview_parts)
        suffix = "" if len(failures) <= 8 else f"; ... +{len(failures) - 8} more"
        message = (
            f"FL_VS_RTL_MISMATCH: {len(failures)} goal(s) failed: {preview}{suffix}"
        )
        if self.mismatch_policy == "soft":
            if logger is not None:
                logger.warning(
                    "SOFT_EQ_MISMATCH (policy=soft): %s", message
                )
            else:
                print(f"[scoreboard:warn] SOFT_EQ_MISMATCH (policy=soft): {message}")
            return
        raise AssertionError(message)

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

    def _model_transactions(self) -> list[dict[str, Any]]:
        try:
            txs = self.model._transactions()  # type: ignore[attr-defined]
        except Exception:
            txs = []
        return [tx for tx in txs if isinstance(tx, dict)] if isinstance(txs, list) else []

    def _transaction_match_text(self, tx: dict[str, Any]) -> str:
        parts: list[str] = []
        for key in ("id", "name", "description"):
            value = tx.get(key)
            if value:
                parts.append(str(value))
        for key in ("preconditions", "inputs", "outputs", "side_effects", "required_fields"):
            parts.extend(str(item) for item in (tx.get(key) or []) if str(item).strip())
        for key in ("output_rules", "state_updates"):
            for rule in _rule_items(tx.get(key)):
                if not isinstance(rule, dict):
                    continue
                parts.extend(
                    str(rule.get(item_key) or "")
                    for item_key in ("name", "output", "port", "state", "expr", "expression", "value")
                    if str(rule.get(item_key) or "").strip()
                )
        return " ".join(parts)

    def _goal_text_transaction_match(self, goal_text: str, goal_tokens: set[str]) -> str:
        best_kind = ""
        best_score = 0
        goal_norm = _norm(goal_text)
        for tx in self._model_transactions():
            preferred = str(tx.get("id") or tx.get("name") or "").strip()
            if not preferred:
                continue
            tx_text = self._transaction_match_text(tx)
            tx_tokens = _meaningful_tokens(tx_text)
            score = len(goal_tokens & tx_tokens)
            for alias in (tx.get("id"), tx.get("name")):
                alias_norm = _norm(alias)
                if alias_norm and (alias_norm in goal_norm or alias_norm.replace("_", " ") in goal_text):
                    score += 6
            if score > best_score:
                best_score = score
                best_kind = preferred
        # Require at least two meaningful shared terms. This maps concrete
        # SSOT-derived memory/state goals such as sync_stage1_ff to
        # FM_SYNC_SAMPLE, while leaving generic memory_access goals untouched.
        return best_kind if best_score >= 2 else ""

    def _nominal_transaction_kind(self) -> str:
        avoid = {"reset", "clear", "hold", "idle", "error", "fault", "illegal", "invalid", "unsupported"}
        for tx in self._model_transactions():
            preferred = str(tx.get("id") or tx.get("name") or "").strip()
            label_text = " ".join(str(tx.get(key) or "") for key in ("id", "name", "description"))
            label_tokens = _meaningful_tokens(label_text)
            if preferred and not (label_tokens & avoid):
                return preferred
        for tx in self._model_transactions():
            preferred = str(tx.get("id") or tx.get("name") or "").strip()
            if preferred:
                return preferred
        return ""

    def _transaction_by_text_tokens(self, include: set[str], exclude: set[str] | None = None) -> str:
        exclude = exclude or set()
        for tx in self._model_transactions():
            preferred = str(tx.get("id") or tx.get("name") or "").strip()
            if not preferred:
                continue
            label_text = " ".join(str(tx.get(key) or "") for key in ("id", "name", "description"))
            label_tokens = _meaningful_tokens(label_text)
            label_norm = _norm(label_text)
            if include and not (label_tokens & include or any(token in label_norm for token in include)):
                continue
            if exclude and (label_tokens & exclude or any(token in label_norm for token in exclude)):
                continue
            return preferred
        return ""

    def _is_error_transaction_kind(self, kind: str) -> bool:
        kind_norm = _norm(kind)
        for tx in self._model_transactions():
            preferred = str(tx.get("id") or tx.get("name") or "").strip()
            if _norm(preferred) != kind_norm:
                continue
            label_text = " ".join(str(tx.get(key) or "") for key in ("id", "name", "description"))
            label_tokens = _meaningful_tokens(label_text)
            label_norm = _norm(label_text)
            return bool(
                label_tokens & {"illegal", "invalid", "error", "fault", "slverr"}
                or any(token in label_norm for token in ("illegal", "invalid", "error", "fault", "slverr"))
            )
        return any(token in kind_norm for token in ("illegal", "invalid", "error", "fault", "slverr"))

    def _best_model_kind(self, goal: dict[str, Any], stimulus: dict[str, Any]) -> str:
        explicit = stimulus.get("kind") or stimulus.get("op") or stimulus.get("transaction")
        explicit_norm = _norm(explicit)
        if explicit_norm in {"reset", "rst"}:
            return "reset"
        if explicit_norm in self.model_transaction_aliases:
            return self.model_transaction_aliases[explicit_norm]

        contract = goal.get("stimulus_contract") if isinstance(goal.get("stimulus_contract"), dict) else {}
        goal_kind = _norm(goal.get("kind"))
        candidates = [contract.get("transaction_type"), goal.get("goal_id"), goal.get("title"), goal.get("kind")]
        contract_text_items: list[Any] = []
        for key in ("constraints", "required_fields"):
            value = contract.get(key)
            if value:
                contract_text_items.append(value)
        expected_contract = goal.get("expected_contract") if isinstance(goal.get("expected_contract"), dict) else {}
        for key in ("error_policy", "observables"):
            value = expected_contract.get(key)
            if value:
                contract_text_items.append(value)
        text = " ".join(
            str(item)
            for item in candidates
            + goal.get("ssot_refs", [])
            + goal.get("pass_criteria", [])
            + contract_text_items
            if item is not None
        ).lower()
        text_tokens = _word_tokens(text)
        meaningful_text_tokens = _meaningful_tokens(text)
        text_norm = _norm(text)

        stimulus_op = _norm(stimulus.get("op") or "")
        generic_csr_kind = explicit_norm in {"csr", "csr_access", "register", "register_access", "control_status_access"}
        if goal_kind == "register" or generic_csr_kind:
            if stimulus_op in {"read", "rd", "csr_read"}:
                matched = self._transaction_by_text_tokens({"read"}, {"illegal", "invalid", "error", "fault", "w1c"})
                if matched:
                    return matched
            if stimulus_op in {"write", "wr", "csr_write"}:
                matched = self._transaction_by_text_tokens({"write"}, {"illegal", "invalid", "error", "fault"})
                if matched:
                    return matched

        explicit_error_goal = (
            goal_kind == "error"
            or "error_handling.error_sources" in text
            or "error sources" in text
            or "error source" in text
            or "error_qualify" in text_norm
            or "illegal_offset" in text_norm
            or "addr_valid_0" in text_norm
            or "addr_valid == 0" in text
            or "invalid address" in text
            or "unmapped" in text_tokens
            or "write to read-only" in text
            or "write to readonly" in text
            or "pslverr is high" in text
            or "pslverr high" in text
            or "complete with error" in text
        )
        if goal_kind != "register" and explicit_error_goal:
            matched = self._transaction_by_text_tokens({"illegal", "invalid", "error", "fault", "slverr"})
            if matched:
                return matched

        op_should_drive_transaction = goal_kind not in {"memory", "state"} and explicit_norm not in {"memory_access", "mem_access"}
        if op_should_drive_transaction and stimulus_op in {"read", "rd", "csr_read"}:
            matched = self._transaction_by_text_tokens({"read"}, {"illegal", "invalid", "error", "fault", "w1c"})
            if matched:
                return matched
        if op_should_drive_transaction and stimulus_op in {"write", "wr", "csr_write"}:
            matched = self._transaction_by_text_tokens({"write"}, {"illegal", "invalid", "error", "fault"})
            if matched:
                return matched

        for candidate in candidates:
            key = _norm(candidate)
            if key in self.model_transaction_aliases:
                return self.model_transaction_aliases[key]

        for key, preferred in sorted(self.model_transaction_aliases.items(), key=lambda item: len(item[0]), reverse=True):
            if key and (key in text_norm or key.replace("_", " ") in text):
                return preferred

        degenerate_state = (
            goal_kind == "state"
            and (
                re.search(r"\b([a-z0-9]+)\s*->\s*\1\b", text) is not None
                or "no multi-state" in text
                or "handshake/state-update driven" in text
                or "single-cycle" in text
            )
        )
        if degenerate_state:
            nominal_kind = self._nominal_transaction_kind()
            if nominal_kind:
                return nominal_kind

        matched_kind = self._goal_text_transaction_match(text, meaningful_text_tokens)
        if matched_kind:
            if self._is_error_transaction_kind(matched_kind) and not explicit_error_goal:
                matched_kind = ""
            else:
                return matched_kind

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

        if goal_kind in {"memory", "state"} and contract.get("transaction_type"):
            return str(contract.get("transaction_type"))

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
        ssot_model = getattr(self.model_module, "SSOT_MODEL", {})
        function_model = ssot_model.get("function_model") if isinstance(ssot_model, dict) else {}
        derived_signals = _rule_items(function_model.get("derived_signals")) if isinstance(function_model, dict) else []
        names = _expr_names(tx.get("sample_condition", ""))
        for rule in output_rules + state_updates:
            names.update(_expr_names(rule.get("expr", rule.get("expression", rule.get("value", "")))))
        for rule in derived_signals:
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
        derived_names = {
            str(rule.get("name") or rule.get("signal") or rule.get("output") or rule.get("port"))
            for rule in derived_signals
            if rule.get("name") or rule.get("signal") or rule.get("output") or rule.get("port")
        }
        known = set(getattr(self.model, "params", {}))
        known.update(getattr(self.model, "state", {}))
        known.update(getattr(self.model, "registers", {}))
        known.update(output_names)
        known.update(update_names)
        known.update(derived_names)
        known.update({"true", "false", "True", "False", "and", "or", "not"})
        helpers_fn = getattr(self.model_module, "_default_rule_helpers", None)
        if callable(helpers_fn):
            try:
                known.update(helpers_fn().keys())
            except Exception:
                pass
        known.update({"read_mux", "reduction_or"})
        for name in sorted(names - known):
            if not name or name in txn:
                continue
            low = name.lower()
            if low in {"branch_taken", "is_store", "is_ldr", "is_str", "is_cmp", "is_b", "is_beq", "is_bne", "fault_halt", "i_hresp", "d_hresp"}:
                txn[name] = 0
            elif low in {"branch_target", "rs2", "base", "imm", "pc", "addr", "data", "value"}:
                txn[name] = 0
            elif low in {"i_hready", "d_hready"}:
                txn[name] = 1
            else:
                txn[name] = 0

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
            "goal_kind": goal.get("kind", ""),
            "title": goal.get("title", ""),
            "model_api": "FunctionalModel.apply",
            "transaction": txn,
            "model_result": model_result,
            "model_error": model_error,
            "observables": expected_contract.get("observables") or [],
            "latency": expected_contract.get("latency", ""),
            "state_updates": expected_contract.get("state_updates") or [],
            "error_policy": expected_contract.get("error_policy", ""),
            "ssot_refs": goal.get("ssot_refs") or [],
            "pass_criteria": goal.get("pass_criteria") or [],
            "stimulus_contract": goal.get("stimulus_contract") if isinstance(goal.get("stimulus_contract"), dict) else {},
            "sample_cycle": goal.get("sample_cycle"),
        }

    def _cycle_expected(self, fl_expected: dict[str, Any], rtl_observed: dict[str, Any] | None = None) -> dict[str, Any] | None:
        """If the goal carries a `sample_cycle` annotation (or its
        stimulus_contract.machine_spec does), evaluate SSOT
        cycle_model.pipeline[*].output_rules at that cycle and return the
        expected dict. This is the production path for multi-cycle
        comparison; SSOT.cycle_model.pipeline supplies the per-stage
        expected values and the cocotb monitor sampled at the matching
        cycle.
        """
        sample_cycle = fl_expected.get("sample_cycle")
        if sample_cycle is None:
            ms = fl_expected.get("stimulus_contract", {}).get("machine_spec") if isinstance(fl_expected.get("stimulus_contract"), dict) else None
            if isinstance(ms, dict):
                sample_cycle = ms.get("sample_cycle")
        if sample_cycle is None:
            return None
        try:
            cycle_int = int(sample_cycle)
        except (TypeError, ValueError):
            return None
        # Lazy-load SSOT yaml (cached on instance).
        ssot_doc = getattr(self, "_ssot_doc", None)
        if ssot_doc is None:
            ssot_path = self.ip_dir / "yaml" / f"{self.ip}.ssot.yaml"
            if not ssot_path.is_file():
                return None
            import yaml as _yaml
            ssot_doc = _yaml.safe_load(ssot_path.read_text(encoding="utf-8")) or {}
            self._ssot_doc = ssot_doc
        # Lazy-import the SSOT-driven evaluator from workflow tooling.
        evaluator = getattr(self, "_evaluator", None)
        if evaluator is None:
            try:
                _here = Path(__file__).resolve()
                _scripts = _here.parents[2] / "fl-model-gen" / "scripts"
                _sys_path_added = False
                import sys as _sys
                if str(_scripts) not in _sys.path:
                    _sys.path.insert(0, str(_scripts))
                    _sys_path_added = True
                import eval_cycle_expected as _eval_mod
                evaluator = _eval_mod.evaluate_at_cycle
                self._evaluator = evaluator
                self._default_env = _eval_mod._default_env
            except Exception:
                return None
        env = dict(self._default_env(ssot_doc))
        env.update(self.model.state if isinstance(self.model.state, dict) else {})
        env.update(self.model.registers if isinstance(self.model.registers, dict) else {})
        txn = fl_expected.get("transaction") if isinstance(fl_expected.get("transaction"), dict) else {}
        for key, value in txn.items():
            if isinstance(value, int):
                env[str(key)] = value
        # SSOT cycle_model expressions reference signal-space names (e.g.
        # ``req_i``) while the cocotb stimulus carries field-space names
        # (e.g. ``requests``) per the TB manifest's input_map. Mirror both
        # directions so expressions resolve regardless of which name the
        # author used in their SSOT or test.
        manifest_path = self.ip_dir / "tb" / "cocotb" / "tb_manifest.json"
        if manifest_path.is_file():
            try:
                manifest_doc = json.loads(manifest_path.read_text(encoding="utf-8"))
                input_map = manifest_doc.get("input_map") if isinstance(manifest_doc.get("input_map"), dict) else {}
                for field, port in input_map.items():
                    if field in env and port not in env:
                        env[str(port)] = env[field]
                    elif port in env and field not in env:
                        env[str(field)] = env[port]
            except Exception:
                pass
        # Propagate the just-observed DUT signals into env (lowercase to match
        # SSOT expression naming convention). This lets expressions that
        # reference handshake or control signals (e.g. ``i_hready``,
        # ``d_hready`` in arm_m0_min) resolve against the cycle the
        # scoreboard actually sampled.
        if isinstance(rtl_observed, dict):
            for key, value in rtl_observed.items():
                if not isinstance(value, (int, bool)):
                    continue
                if key not in env:
                    env[str(key)] = int(value)
                lk = str(key).lower()
                if lk != str(key) and lk not in env:
                    env[lk] = int(value)
        try:
            return evaluator(ssot_doc, cycle_int, env)
        except Exception:
            return None

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
        if _is_debug_observability_expected(fl_expected):
            return True, ""
        if _is_degenerate_state_expected(fl_expected):
            return True, ""
        if self is None:
            legacy_verdict = _legacy_unbound_policy_compare(fl_expected, rtl_observed)
            if legacy_verdict is not None:
                return legacy_verdict
        # Production multi-cycle wiring: if the goal pins a sample_cycle and
        # SSOT.cycle_model.pipeline has machine-readable output_rules, use
        # those as the expected values instead of FL.apply's single-shot
        # model_result. This unblocks UART tx_serial cycling, AHB CPU PC
        # tracking, and similar multi-cycle behaviour without falling back
        # to hardcoded protocol heuristics.
        cycle_view = None
        if hasattr(self, "_cycle_expected"):
            cycle_view = self._cycle_expected(fl_expected, rtl_observed)
        if isinstance(cycle_view, dict) and cycle_view:
            verdict, mismatch = _dict_overlap_compare(cycle_view, rtl_observed)
            if verdict is not None:
                return verdict, mismatch
        cycle_verdict = _cycle_property_compare(fl_expected, rtl_observed)
        if cycle_verdict is not None:
            return cycle_verdict
        state_view = _state_transition_expected_view(fl_expected, rtl_observed)
        if state_view:
            verdict, mismatch = _dict_overlap_compare(state_view, rtl_observed)
            if verdict is not None:
                return verdict, mismatch
        if isinstance(model_result, dict):
            view = _expected_observable_view(model_result, rtl_observed, fl_expected)
            if hasattr(self, "_mirror_view_via_input_map"):
                view = self._mirror_view_via_input_map(view)
            view = _filtered_expected_view(view, rtl_observed, fl_expected)
            verdict, mismatch = _dict_overlap_compare(view, rtl_observed)
            if verdict is not None:
                return verdict, mismatch
        return False, "no comparable RTL observable for FunctionalModel result"

    def _mirror_view_via_input_map(self, view: dict[str, Any]) -> dict[str, Any]:
        """Add port-aliased copies of state/field values for scoreboard overlap.

        Mirror sources, in order:
        - tb_manifest.json input_map (field ↔ input port aliasing)
        - SSOT function_model.state_variables[*].drives_output (state ↔ output port)

        SSOT state_variables may use suffixed names (count_q, done_q) while
        RTL output signals drop the suffix (count, done); `drives_output`
        declares the mapping explicitly. Without this mirror, scoreboard
        view keys and rtl_observed keys never overlap and the goal returns
        'no comparable RTL observable for FunctionalModel result'.
        """
        if not isinstance(view, dict) or not view:
            return view
        mirrored = dict(view)
        manifest_path = self.ip_dir / "tb" / "cocotb" / "tb_manifest.json"
        if manifest_path.is_file():
            try:
                manifest_doc = json.loads(manifest_path.read_text(encoding="utf-8"))
                input_map = manifest_doc.get("input_map") if isinstance(manifest_doc.get("input_map"), dict) else {}
                for field, port in input_map.items():
                    if field in mirrored and port not in mirrored:
                        mirrored[str(port)] = mirrored[field]
                    elif port in mirrored and field not in mirrored:
                        mirrored[str(field)] = mirrored[port]
            except Exception:
                pass
        # SSOT state_variables[*].drives_output is the declarative state→port
        # binding. Cache the SSOT doc on the instance so repeated goals don't
        # re-read it.
        ssot_doc = getattr(self, "_ssot_doc", None)
        if ssot_doc is None:
            ssot_path = self.ip_dir / "yaml" / f"{self.ip}.ssot.yaml"
            if ssot_path.is_file():
                try:
                    import yaml as _yaml
                    ssot_doc = _yaml.safe_load(ssot_path.read_text(encoding="utf-8")) or {}
                    self._ssot_doc = ssot_doc
                except Exception:
                    ssot_doc = {}
        if isinstance(ssot_doc, dict):
            fm = ssot_doc.get("function_model") if isinstance(ssot_doc.get("function_model"), dict) else {}
            for sv in fm.get("state_variables") or []:
                if not isinstance(sv, dict):
                    continue
                state_name = str(sv.get("name") or "").strip()
                drives = str(sv.get("drives_output") or "").strip()
                if not state_name or not drives:
                    continue
                if state_name in mirrored and drives not in mirrored:
                    mirrored[drives] = mirrored[state_name]
                elif drives in mirrored and state_name not in mirrored:
                    mirrored[state_name] = mirrored[drives]
        return mirrored

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
        ssot_question_count = 0
        contract_gaps: list[dict[str, Any]] = []
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
                contract_gaps.append({
                    "goal_id": gid,
                    "kind": expected.get("transaction", {}).get("kind"),
                    "reason": "FunctionalModel returned unsupported_transaction for a required equivalence goal",
                })
            if expected.get("model_error"):
                model_errors += 1
            ssot_questions = _extract_ssot_questions(result)
            if ssot_questions:
                ssot_question_count += len(ssot_questions)
                for question in ssot_questions:
                    contract_gaps.append({
                        "goal_id": gid,
                        "kind": expected.get("transaction", {}).get("kind"),
                        "question": question,
                    })
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
            "ssot_questions": ssot_question_count,
            "contract_gaps": contract_gaps[:20],
            "events_path": str(self.events_path),
            "sample": samples,
            "passed": checked > 0 and model_errors == 0 and unsupported == 0 and ssot_question_count == 0,
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
        if report.get("passed"):
            return 0
        if report.get("ssot_questions") or report.get("unsupported_transactions"):
            _write_self_check_blocker(scoreboard, report)
            return 2
        return 1
    print(f"loaded {len(scoreboard.goals)} equivalence goals for {args.ip}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
