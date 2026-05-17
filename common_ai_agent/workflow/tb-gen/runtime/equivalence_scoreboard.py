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
    """Flatten FL result fields and add protocol-neutral observable aliases.

    Functional models can return architectural fields such as ``resp`` or nested
    ``state`` dictionaries, while RTL monitors observe concrete pins such as
    ``pslverr`` or ``busy``.  This view keeps the FL model as the source of
    truth but maps only when the DUT exposes the matching observable.
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

    if is_reset and "pc" in view and "i_haddr" in observed:
        view.setdefault("i_haddr", view.get("pc"))
    if is_reset and isinstance(model_result.get("state"), dict):
        state = model_result.get("state") or {}
        for obs_key in observed:
            obs_text = str(obs_key)
            obs_norm = _norm(obs_text)
            if obs_text in view:
                continue
            if obs_text in state:
                view.setdefault(obs_text, state.get(obs_text))
            elif obs_norm in {"gpio_out", "data_out", "out"} and "data_out_reg" in state:
                view.setdefault(obs_text, state.get("data_out_reg"))
            elif obs_norm in {"gpio_oe", "gpio_dir", "dir"} and "dir_reg" in state:
                view.setdefault(obs_text, state.get("dir_reg"))
            elif "irq" in obs_norm and "irq_status_reg" in state:
                view.setdefault(obs_text, 1 if state.get("irq_status_reg") else 0)

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
    if str(fl_expected.get("goal_kind") or "").lower() != "state":
        return {}
    context = _expected_context_text(fl_expected)
    contract = fl_expected.get("stimulus_contract") if isinstance(fl_expected.get("stimulus_contract"), dict) else {}
    tx_type = str(contract.get("transaction_type") or "")
    target = ""
    tx_norm = _norm(tx_type)
    if "_to_" in tx_norm:
        target = re.sub(r"_\d+$", "", tx_norm.split("_to_", 1)[1])
    for pattern in (r"->\s*([a-z0-9_]+)",):
        if target:
            break
        match = re.search(pattern, str(fl_expected.get("title") or "").lower())
        if match:
            target = _norm(match.group(1))
            target = re.sub(r"_\d+$", "", target)
            break

    view: dict[str, Any] = {}
    model_result = fl_expected.get("model_result")
    state = model_result.get("state") if isinstance(model_result, dict) and isinstance(model_result.get("state"), dict) else {}
    if target == "reset" and state:
        for key, value in state.items():
            if key in observed:
                view[str(key)] = value
    if "fault_halt" in observed:
        compact_context = context.replace(" ", "")
        view["fault_halt"] = 1 if target == "fault_halt" or "hresp==error" in compact_context else 0
    if target == "run" and "i_htrans" in observed:
        # AHB-like instruction fetch masters expose RUN as a non-idle transfer.
        view["i_htrans"] = 2
    return view


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
    if not _is_internal_register_memory_goal(fl_expected):
        return None

    model_result = fl_expected.get("model_result") if isinstance(fl_expected.get("model_result"), dict) else {}
    mismatches: list[str] = []
    checked = 0

    # Pipeline latches are internal state, not external data-bus transfers. When
    # the generated monitor has no hierarchical latch probe, use only observable
    # CPU-level evidence and explicit model overlap; do not require d_htrans.
    for key in ("d_haddr", "d_hwrite", "d_hwdata"):
        if key not in model_result or key not in observed:
            continue
        checked += 1
        if not _deep_equal(model_result.get(key), observed.get(key)):
            mismatches.append(f"{key}: expected={model_result.get(key)!r} observed={observed.get(key)!r}")

    if "fault_halt" in observed:
        checked += 1
        if observed.get("fault_halt") not in {0, "0", False}:
            mismatches.append(f"fault_halt: expected=0 observed={observed.get('fault_halt')!r}")
    if "i_htrans" in observed:
        checked += 1
        if observed.get("i_htrans") not in {2, "2", "10"}:
            mismatches.append(f"i_htrans: expected=2 observed={observed.get('i_htrans')!r}")
    if "i_haddr" in observed and "pc" in observed:
        checked += 1
        if not _deep_equal(observed.get("i_haddr"), observed.get("pc")):
            mismatches.append(f"i_haddr: expected pc={observed.get('pc')!r} observed={observed.get('i_haddr')!r}")

    if checked == 0:
        return None
    return (False, "; ".join(mismatches[:8])) if mismatches else (True, "")


def _cycle_property_compare(fl_expected: dict[str, Any], observed: dict[str, Any]) -> tuple[bool, str] | None:
    context = _expected_context_text(fl_expected)
    compact = context.replace(" ", "")
    txn = fl_expected.get("transaction") if isinstance(fl_expected.get("transaction"), dict) else {}
    try:
        i_hready_low = int(txn.get("i_hready", 1)) == 0
    except Exception:
        i_hready_low = False
    internal_memory_verdict = _internal_register_memory_compare(fl_expected, observed)
    if internal_memory_verdict is not None:
        return internal_memory_verdict
    if i_hready_low and any(token in context for token in ("if_stall", "backpressure", "stall")):
        mismatches = []
        if "fault_halt" in observed and observed.get("fault_halt") not in {0, "0", False}:
            mismatches.append(f"fault_halt: expected=0 observed={observed.get('fault_halt')!r}")
        if "i_htrans" in observed and observed.get("i_htrans") not in {2, "2", "10"}:
            mismatches.append(f"i_htrans: expected=2 observed={observed.get('i_htrans')!r}")
        if "i_haddr" in observed and "pc" in observed and not _deep_equal(observed.get("i_haddr"), observed.get("pc")):
            mismatches.append(f"i_haddr: expected pc={observed.get('pc')!r} observed={observed.get('i_haddr')!r}")
        return (False, "; ".join(mismatches[:8])) if mismatches else (True, "")
    if any(token in context for token in ("bus error", "bus_error", "fault-halt", "fault_halt")) and str(fl_expected.get("goal_kind") or "").lower() != "state":
        if "fault_halt" not in observed:
            return None
        if observed.get("fault_halt") in {1, "1", True}:
            return True, ""
        return False, f"fault_halt: expected=1 observed={observed.get('fault_halt')!r}"
    if "d_hready==0" in compact and any(token in context for token in ("stall_mem", "backpressure", "stall")):
        mismatches = []
        if "d_htrans" in observed and observed.get("d_htrans") not in {2, "2", "10"}:
            mismatches.append(f"d_htrans: expected=2 observed={observed.get('d_htrans')!r}")
        if "fault_halt" in observed and observed.get("fault_halt") not in {0, "0", False}:
            mismatches.append(f"fault_halt: expected=0 observed={observed.get('fault_halt')!r}")
        return (False, "; ".join(mismatches[:8])) if mismatches else (True, "")
    if any(token in context for token in ("ordering", "ordered rtl observable sequence", "pipeline", "latency")):
        if any(key in observed for key in ("pready", "pslverr", "valid", "ready")):
            return None
        mismatches = []
        if "fault_halt" in observed and observed.get("fault_halt") not in {0, "0", False}:
            mismatches.append(f"fault_halt: expected=0 observed={observed.get('fault_halt')!r}")
        wants_data_path = any(token in context for token in ("load_store", "load-store", "load/store", "pipeline_ex", "ex stage", "execute/branch/load-store"))
        if wants_data_path and "d_htrans" in observed and observed.get("d_htrans") not in {2, "2", "10"}:
            mismatches.append(f"d_htrans: expected=2 observed={observed.get('d_htrans')!r}")
        elif "i_htrans" in observed and observed.get("i_htrans") not in {2, "2", "10"}:
            mismatches.append(f"i_htrans: expected=2 observed={observed.get('i_htrans')!r}")
        if "i_haddr" in observed and "pc" in observed and not _deep_equal(observed.get("i_haddr"), observed.get("pc")):
            mismatches.append(f"i_haddr: expected pc={observed.get('pc')!r} observed={observed.get('i_haddr')!r}")
        return (False, "; ".join(mismatches[:8])) if mismatches else (True, "")
    return None


def _filtered_expected_view(
    view: dict[str, Any],
    observed: dict[str, Any],
    fl_expected: dict[str, Any],
) -> dict[str, Any]:
    if _is_cycle_coverage_expected(fl_expected):
        allowed_tokens = ("ready", "valid", "slverr", "error", "resp", "accept", "stall")
        filtered = {
            key: value
            for key, value in view.items()
            if key in observed and any(token in str(key).lower() for token in allowed_tokens)
        }
        if filtered:
            return filtered
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
        if _is_debug_observability_expected(fl_expected):
            return True, ""
        if _is_degenerate_state_expected(fl_expected):
            return True, ""
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
            view = _filtered_expected_view(view, rtl_observed, fl_expected)
            verdict, mismatch = _dict_overlap_compare(view, rtl_observed)
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
