#!/usr/bin/env python3
"""Semantic validation of the LLM-authored FL (functional) model.

The fl-model-gen self-check (``emit_fl_model.run_self_check``) only runs the
generated model against itself and counts machine-evaluable invariants. It never
asks whether the FL transactions *faithfully implement the locked behavioral
contracts*. As a result a generic stateful "feature sequencer" template (state
variables, an FSM, ``state_updates``) can be projected onto a purely
combinational IP and flow all the way to the FL-vs-RTL scoreboard before failing
with a confusing false mismatch.

This module closes that hole with two layers:

1. A deterministic FAST-PATH backstop (no LLM required): a behavioral contract
   carrying ``cycle_model_waiver=true`` describes combinational / cycle-less
   behavior, so the FL model must not introduce state-control machinery tied to
   that contract's transactions — no ``state_updates``, no architectural
   ``state_variables`` beyond declared registers, and no state-control FSM. Any
   such fictional state is a CRITICAL violation and fails the gate.

2. An LLM-judge layer (optional, gated behind the same real-LLM conventions as
   the headless workers): for each locked behavioral contract the judge is shown
   the contract decision table and the corresponding FL transaction(s) and asked
   whether the transaction faithfully realizes the contract, returning a
   structured ``{faithful, violations[]}`` verdict.

The judge degrades safely: when the real LLM is unavailable the result records an
explicit ``semantic validation not run`` status. It never silently passes.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import yaml

WORKFLOW_ROOT = Path(__file__).resolve().parents[2]
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))

from behavioral_contracts import (  # noqa: E402
    BehavioralContractError,
    behavioral_contract_map,
    compare_behavioral_to_function_cycle,
    normalize_behavioral_contracts,
)
from judge_verdict_cache import judge_with_cache  # noqa: E402

REPO_ROOT = WORKFLOW_ROOT.parent
for candidate in (REPO_ROOT, REPO_ROOT / "src"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


# --------------------------------------------------------------------------- #
# IO helpers
# --------------------------------------------------------------------------- #
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
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [value]
    return [value]


def _present(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip()) and value.strip().lower() not in {"none", "n/a", "na", "tbd", "todo"}
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


# --------------------------------------------------------------------------- #
# Contract <-> transaction linkage
# --------------------------------------------------------------------------- #
_CONTRACT_REF_KEYS = (
    "contract_refs",
    "behavioral_contract_refs",
    "behavioral_contracts",
    "contract_ref",
    "behavioral_contract_id",
    "contracts",
)


def _transaction_contract_refs(tx: dict[str, Any]) -> set[str]:
    refs: set[str] = set()
    for key in _CONTRACT_REF_KEYS:
        value = tx.get(key)
        if isinstance(value, str) and value.strip():
            refs.add(value.strip())
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item.strip():
                    refs.add(item.strip())
    return refs


def _function_model(ssot: dict[str, Any]) -> dict[str, Any]:
    fm = ssot.get("function_model")
    return fm if isinstance(fm, dict) else {}


def _state_variable_names(ssot: dict[str, Any]) -> list[str]:
    fm = _function_model(ssot)
    names: list[str] = []
    for item in _as_list(fm.get("state_variables")):
        if isinstance(item, dict):
            name = item.get("name")
            if isinstance(name, str) and name.strip():
                names.append(name.strip())
        elif isinstance(item, str) and item.strip():
            names.append(item.strip())
    return names


def _declared_register_names(ssot: dict[str, Any]) -> set[str]:
    """Architectural registers declared in SSOT registers section.

    A waived (combinational) IP legitimately has no FSM/state-control, but a
    register-file style block may still carry declared register storage. Those
    names are allowed to appear as state; only *undeclared* state is fictional.
    """
    regs = ssot.get("registers") if isinstance(ssot.get("registers"), dict) else {}
    names: set[str] = set()
    for key in ("register_map", "register_list", "config"):
        for item in _as_list(regs.get(key)):
            if isinstance(item, dict):
                name = item.get("name")
                if isinstance(name, str) and name.strip():
                    names.add(name.strip())
    return names


def _fsm_states(ssot: dict[str, Any]) -> list[str]:
    fsm = ssot.get("fsm")
    states: list[str] = []
    if not isinstance(fsm, dict):
        return states

    def collect(block: dict[str, Any]) -> None:
        for st in _as_list(block.get("states")):
            if isinstance(st, dict):
                name = st.get("name") or st.get("id")
                if isinstance(name, str) and name.strip():
                    states.append(name.strip())
            elif isinstance(st, str) and st.strip():
                states.append(st.strip())
        for trn in _as_list(block.get("transitions")):
            if isinstance(trn, dict):
                for key in ("from", "to"):
                    name = trn.get(key)
                    if isinstance(name, str) and name.strip():
                        states.append(name.strip())

    if any(isinstance(v, dict) for v in fsm.values()):
        for block in fsm.values():
            if isinstance(block, dict):
                collect(block)
    collect(fsm)
    return sorted({s for s in states})


# --------------------------------------------------------------------------- #
# Deterministic FAST-PATH backstop
# --------------------------------------------------------------------------- #
def _deterministic_violations(
    *,
    contracts: dict[str, dict[str, Any]],
    ssot: dict[str, Any],
    waived_ids: set[str],
) -> list[dict[str, Any]]:
    """Return CRITICAL fictional-state violations independent of any LLM.

    A contract in ``waived_ids`` (``cycle_model_waiver=true``) is combinational /
    cycle-less. Its transactions must not carry ``state_updates``, and the IP as
    a whole must not introduce a state-control FSM or undeclared architectural
    ``state_variables`` to "implement" such a contract.
    """
    violations: list[dict[str, Any]] = []
    fm = _function_model(ssot)
    transactions = [tx for tx in _as_list(fm.get("transactions")) if isinstance(tx, dict)]
    declared_registers = _declared_register_names(ssot)
    fsm_states = _fsm_states(ssot)

    # Per-transaction: a waived contract's transaction must have no state_updates.
    waived_txn_present = False
    for idx, tx in enumerate(transactions):
        refs = _transaction_contract_refs(tx)
        waived_refs = refs & waived_ids
        if not waived_refs:
            continue
        waived_txn_present = True
        tx_name = str(tx.get("name") or tx.get("id") or f"transactions[{idx}]")
        state_updates = [su for su in _as_list(tx.get("state_updates")) if _present(su)]
        if state_updates:
            update_names = sorted(
                str(su.get("name")) if isinstance(su, dict) and su.get("name") else str(su)
                for su in state_updates
            )
            violations.append({
                "severity": "critical",
                "kind": "fictional_state",
                "contract_refs": sorted(waived_refs),
                "transaction": tx_name,
                "detail": (
                    f"transaction '{tx_name}' carries state_updates {update_names} but its behavioral "
                    f"contract(s) {sorted(waived_refs)} are cycle_model_waiver=true (combinational): a "
                    "cycle-waived contract has no architectural state to update"
                ),
            })

    if not waived_txn_present and not (waived_ids and transactions):
        # No waived contract drives any transaction — nothing combinational to guard.
        return violations

    # IP-level: a fully-waived IP must not declare a state-control FSM nor
    # undeclared architectural state variables.
    all_contracts_waived = bool(contracts) and set(contracts) == set(waived_ids)
    if all_contracts_waived:
        undeclared_state = [
            name for name in _state_variable_names(ssot) if name not in declared_registers
        ]
        if undeclared_state:
            violations.append({
                "severity": "critical",
                "kind": "fictional_state",
                "contract_refs": sorted(waived_ids),
                "transaction": None,
                "detail": (
                    f"function_model.state_variables {undeclared_state} declare architectural state, but "
                    f"every behavioral contract is cycle_model_waiver=true (combinational): a cycle-waived "
                    "IP must have no state-control state variables beyond declared registers"
                ),
            })
        if fsm_states:
            violations.append({
                "severity": "critical",
                "kind": "fictional_state",
                "contract_refs": sorted(waived_ids),
                "transaction": None,
                "detail": (
                    f"SSOT declares an fsm with states {fsm_states[:8]}, but every behavioral contract is "
                    "cycle_model_waiver=true (combinational): a cycle-waived IP must have no state-control FSM"
                ),
            })
    return violations


# --------------------------------------------------------------------------- #
# LLM judge
# --------------------------------------------------------------------------- #
_JUDGE_SYSTEM_PROMPT = (
    "You are a hardware verification judge. You are given ONE locked behavioral "
    "contract (a when->then decision table, plus a cycle_model_waiver flag) and the "
    "functional-model (FL) transaction(s) that are supposed to implement it, together "
    "with the SSOT state_variables and fsm. Decide whether the FL transaction(s) "
    "faithfully implement the contract.\n\n"
    "Rules:\n"
    "- FICTIONAL STATE: if cycle_model_waiver=true the contract is combinational; the "
    "transaction must have NO state_updates and the IP must have NO state-control FSM. "
    "Flag any state_updates / fsm states / state_variables the contract does not require "
    "as a CRITICAL violation.\n"
    "- UNREALIZED ROWS: each decision-table when->then row must be realized by the "
    "transaction's output_rules/state_updates. Flag unrealized rows.\n"
    "- UNJUSTIFIED TRANSACTION: flag a transaction that no contract row justifies.\n\n"
    "Respond with ONLY a JSON object: "
    '{"faithful": bool, "violations": [{"severity": "critical"|"warning", "kind": str, '
    '"detail": str}]}. No prose outside the JSON.'
)


def _contract_payload(contract: dict[str, Any], waived: bool) -> dict[str, Any]:
    return {
        "id": contract.get("id"),
        "cycle_model_waiver": waived,
        "decision_table": contract.get("decision_table"),
        "truth_table": contract.get("truth_table"),
        "state_transitions": contract.get("state_transitions"),
        "description": contract.get("description") or contract.get("intent"),
    }


def _transaction_payload(tx: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": tx.get("name"),
        "id": tx.get("id"),
        "inputs": tx.get("inputs"),
        "preconditions": tx.get("preconditions"),
        "output_rules": tx.get("output_rules"),
        "state_updates": tx.get("state_updates"),
        "contract_refs": sorted(_transaction_contract_refs(tx)),
    }


def _parse_judge_response(raw: str) -> dict[str, Any] | None:
    text = (raw or "").strip()
    if not text:
        return None
    # Tolerate ```json fences and leading/trailing prose.
    if "```" in text:
        chunks = text.split("```")
        for chunk in chunks:
            chunk = chunk.strip()
            if chunk.startswith("json"):
                chunk = chunk[4:].strip()
            if chunk.startswith("{"):
                text = chunk
                break
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


class _JudgeBlocked(Exception):
    """Raised inside a per-contract judge closure to signal a hard block.

    Used so the cache wrapper can run the judge closure transparently while the
    caller still distinguishes "blocked" (never silent-pass) from a real verdict.
    """

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def _run_llm_judge(
    *,
    contracts: dict[str, dict[str, Any]],
    ssot: dict[str, Any],
    waived_ids: set[str],
    llm_provider: Any,
    model: str,
    ip_dir: Path | None = None,
) -> dict[str, Any]:
    """Run the per-contract LLM judge. Returns a structured block.

    ``status`` is one of: ``pass`` (all faithful), ``fail`` (a critical violation),
    ``warning`` (non-critical only), or ``not_run`` (LLM unavailable / errored —
    never a silent pass).

    Each per-contract verdict is served from a content-keyed cache when available
    (``judge_verdict_cache``): an unchanged contract+content reuses the stored
    verdict and makes NO LLM call (``cache_hit=True``), so determinism is
    structural and redundant re-judging is eliminated.
    """
    fm = _function_model(ssot)
    transactions = [tx for tx in _as_list(fm.get("transactions")) if isinstance(tx, dict)]
    state_variables = _state_variable_names(ssot)
    fsm_states = _fsm_states(ssot)

    per_contract: list[dict[str, Any]] = []
    violations: list[dict[str, Any]] = []
    blocked_reason = ""
    judged = 0

    for contract_id, contract in sorted(contracts.items()):
        waived = contract_id in waived_ids
        linked_txns = [
            _transaction_payload(tx)
            for tx in transactions
            if contract_id in _transaction_contract_refs(tx)
        ]
        prompt_obj = {
            "behavioral_contract": _contract_payload(contract, waived),
            "fl_transactions": linked_txns,
            "ssot_state_variables": state_variables,
            "ssot_fsm_states": fsm_states,
        }

        def judge_call(_cid: str = contract_id, _obj: dict[str, Any] = prompt_obj) -> dict[str, Any]:
            prompt = (
                "Judge whether the FL transaction(s) faithfully implement the locked behavioral "
                "contract below.\n\n" + json.dumps(_obj, indent=2, sort_keys=True)
            )
            try:
                response = llm_provider.complete(
                    stage="fl-model-gen",
                    model=model,
                    system_prompt=_JUDGE_SYSTEM_PROMPT,
                    prompt=prompt,
                    context={"ip": ssot.get("ip"), "contract": _cid},
                )
            except Exception as exc:  # provider plumbing failure — never silent-pass
                raise _JudgeBlocked(f"LLM judge raised {type(exc).__name__}: {exc}") from exc
            if getattr(response, "status", "") == "blocked" or getattr(response, "error", ""):
                raise _JudgeBlocked(getattr(response, "error", "") or "LLM provider blocked")
            parsed = _parse_judge_response(getattr(response, "raw_response", ""))
            if parsed is None:
                raise _JudgeBlocked(f"LLM judge returned unparseable verdict for {_cid}")
            contract_violations = [v for v in _as_list(parsed.get("violations")) if isinstance(v, dict)]
            for v in contract_violations:
                v.setdefault("contract_refs", [_cid])
            return {
                "contract_id": _cid,
                "faithful": bool(parsed.get("faithful")),
                "violations": contract_violations,
            }

        try:
            verdict = judge_with_cache(
                ip_dir=ip_dir if ip_dir is not None else Path("."),
                domain="fl",
                contract_id=contract_id,
                contract=contract,
                judged_content=prompt_obj,
                model=model,
                judge_call=judge_call,
            )
        except _JudgeBlocked as blocked:
            blocked_reason = blocked.reason
            break
        judged += 1
        contract_violations = [
            v for v in _as_list(verdict.get("violations")) if isinstance(v, dict)
        ]
        violations.extend(contract_violations)
        per_contract.append(verdict)

    if blocked_reason:
        return {
            "status": "not_run",
            "ran": False,
            "model": model,
            "reason": blocked_reason,
            "contracts_judged": judged,
            "per_contract": per_contract,
            "violations": violations,
        }

    critical = [v for v in violations if str(v.get("severity")).lower() == "critical"]
    if critical:
        status = "fail"
    elif violations:
        status = "warning"
    else:
        status = "pass"
    return {
        "status": status,
        "ran": True,
        "model": model,
        "contracts_judged": judged,
        "per_contract": per_contract,
        "violations": violations,
    }


def _default_provider() -> tuple[Any, str]:
    """Best-effort construction of the headless RealLLMProvider.

    Returns ``(provider, model)``. ``provider`` is ``None`` when the headless
    plumbing cannot be imported, which is treated as "not run" (never a pass).
    """
    model = (
        os.getenv("ATLAS_FL_SEMANTIC_JUDGE_MODEL")
        or os.getenv("ATLAS_HEADLESS_LLM_MODEL")
        or "gpt-5.4"
    )
    try:
        try:
            from src.headless_workflow import RealLLMProvider
        except ModuleNotFoundError:
            from headless_workflow import RealLLMProvider
    except Exception:
        return None, model
    # Per-judge-call timeout cap (default 120s) so a single hung judge call cannot
    # wedge a worker for the full headless 600s budget. Falls back to the
    # provider's own default when the knob is unset/invalid.
    timeout_s: int | None = None
    raw_timeout = os.getenv("ATLAS_JUDGE_CALL_TIMEOUT_S", "120").strip()
    if raw_timeout:
        try:
            timeout_s = int(raw_timeout)
        except ValueError:
            timeout_s = None
    provider = RealLLMProvider(
        required_model=os.getenv("ATLAS_HEADLESS_REQUIRED_MODEL", ""),
        timeout_s=timeout_s,
    )
    return provider, model


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #
def validate_fl_semantics(
    ip: str,
    root: Path,
    *,
    llm_provider: Any = None,
    model: str | None = None,
    use_llm: bool | None = None,
) -> dict[str, Any]:
    """Validate the FL model semantics against locked behavioral contracts.

    The verdict ``passed`` is False iff a CRITICAL violation is found by either the
    deterministic backstop or the LLM judge. The LLM judge is advisory-on-absence:
    if it cannot run, ``llm_judge.status == "not_run"`` but the deterministic layer
    still gates. This never silently passes a missing judge — the status is
    explicit and surfaced in the report.
    """
    ip_dir = _resolve_ip_dir(root, ip)
    req_dir = ip_dir / "req"
    behavioral_path = req_dir / "behavioral_contracts.json"
    ssot_path = ip_dir / "yaml" / f"{ip}.ssot.yaml"

    base = {
        "schema_version": 1,
        "type": "fl_semantic_validation",
        "ip": ip,
    }

    if not behavioral_path.is_file():
        return {**base, "status": "inactive", "passed": True,
                "reason": "req/behavioral_contracts.json absent"}

    try:
        ssot = _load_yaml(ssot_path)
    except Exception as exc:
        return {**base, "status": "error", "passed": False,
                "reason": f"cannot load SSOT YAML: {type(exc).__name__}: {exc}"}

    try:
        obligations_path = req_dir / "obligations.json"
        obligation_ids = None
        if obligations_path.is_file():
            obl_doc = _load_json(obligations_path)
            obligation_ids = {
                str(o.get("obligation_id") or o.get("id"))
                for o in _as_list(obl_doc.get("obligations"))
                if isinstance(o, dict) and (o.get("obligation_id") or o.get("id"))
            } or None
        behavioral = normalize_behavioral_contracts(
            ip, _load_json(behavioral_path), known_obligation_ids=obligation_ids
        )
    except (BehavioralContractError, OSError, ValueError, json.JSONDecodeError) as exc:
        return {**base, "status": "error", "passed": False,
                "reason": f"invalid behavioral contract authority: {exc}"}

    contracts = behavioral_contract_map(behavioral)
    _proj_issues, projection = compare_behavioral_to_function_cycle(behavioral, ssot)
    waived_ids = {str(c) for c in _as_list(projection.get("cycle_model_waived"))}

    deterministic = _deterministic_violations(
        contracts=contracts, ssot=ssot, waived_ids=waived_ids
    )

    # LLM judge layer (optional). Default-on when a provider is constructible and
    # the real-LLM lane is enabled; otherwise records an explicit not_run status.
    if use_llm is None:
        use_llm = True
    llm_block: dict[str, Any]
    if not use_llm:
        llm_block = {"status": "not_run", "ran": False,
                     "reason": "LLM judge disabled by caller (use_llm=False)"}
    else:
        provider = llm_provider
        judge_model = model
        if provider is None:
            provider, default_model = _default_provider()
            judge_model = judge_model or default_model
        if provider is None:
            llm_block = {"status": "not_run", "ran": False,
                         "reason": "headless RealLLMProvider unavailable (import failed)"}
        else:
            llm_block = _run_llm_judge(
                contracts=contracts, ssot=ssot, waived_ids=waived_ids,
                llm_provider=provider, model=str(judge_model or "gpt-5.4"),
                ip_dir=ip_dir,
            )

    llm_critical = [
        v for v in _as_list(llm_block.get("violations"))
        if isinstance(v, dict) and str(v.get("severity")).lower() == "critical"
    ]
    critical = [v for v in deterministic if str(v.get("severity")).lower() == "critical"]
    critical.extend(llm_critical)
    passed = not critical

    reasons = [str(v.get("detail")) for v in critical if v.get("detail")]
    return {
        **base,
        "status": "fail" if not passed else "pass",
        "passed": passed,
        "contract_refs": sorted(contracts),
        "cycle_model_waived": sorted(waived_ids),
        "deterministic_backstop": {
            "status": "fail" if any(
                str(v.get("severity")).lower() == "critical" for v in deterministic
            ) else "pass",
            "violations": deterministic,
        },
        "llm_judge": llm_block,
        "violations": critical,
        "reason": "; ".join(reasons) if reasons else "FL model is semantically faithful to locked contracts",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ip")
    parser.add_argument("--root", default=".")
    parser.add_argument("--no-llm", action="store_true", help="run only the deterministic backstop")
    parser.add_argument("--model", default=None)
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    report = validate_fl_semantics(
        args.ip, root, model=args.model, use_llm=not args.no_llm
    )
    status = "PASS" if report.get("passed") else "FAIL"
    print(f"[validate_fl_semantics] {status} ip={args.ip} status={report.get('status')}")
    print(report.get("reason", ""))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
