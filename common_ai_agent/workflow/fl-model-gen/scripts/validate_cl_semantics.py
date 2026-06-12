#!/usr/bin/env python3
"""Semantic validation of the LLM/template-authored CL (cycle) model.

The cl-model-gen self-check (``emit_cycle_model.run_self_check``) only runs the
generated CycleModel against itself: it counts that the declared transaction
kinds were observed and that the coverage bins were hit. It never asks whether
the cycle-level behaviour (latency / handshake / ordering / outstanding) is
*justified by the locked behavioral contracts*. As a result the same generic
stateful template that injects a fictional FSM into the FL model also injects
fictional **timing** into the CL model — a combinational IP gets a valid/ready
handshake, clock-edge ordering tied to an FSM terminal state, and unbounded
``max_cycles: null`` latency — and that fiction flows all the way to the
FL-vs-RTL scoreboard before failing as a confusing false mismatch.

This module is the cycle-domain twin of ``validate_fl_semantics`` and closes the
hole with the same two layers:

1. A deterministic FAST-PATH backstop (no LLM required): a behavioral contract
   carrying ``cycle_model_waiver=true`` describes combinational / cycle-less
   behaviour. When *every* behavioral contract is waived the IP has no cycle
   semantics, so the SSOT ``cycle_model`` must not declare handshake rules,
   ordering/arbitration rules, a pipeline, backpressure, ``outstanding>1`` or
   multi-cycle / unbounded latency. Any such fictional timing is a CRITICAL
   violation and fails the gate.

2. An LLM-judge layer (optional, same real-LLM conventions as the headless
   workers): for each locked behavioral contract the judge is shown the contract
   decision table (plus its ``cycle_model_waiver`` flag and any declared
   state_transitions / latency) and the corresponding CL timing, and asked
   whether the cycle model faithfully realises the contract, returning a
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
# IO helpers (mirror validate_fl_semantics)
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


def _nonempty(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


# --------------------------------------------------------------------------- #
# Contract <-> transaction linkage (shared shape with validate_fl_semantics)
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


def _cycle_model(ssot: dict[str, Any]) -> dict[str, Any]:
    cm = ssot.get("cycle_model")
    return cm if isinstance(cm, dict) else {}


# --------------------------------------------------------------------------- #
# Cycle-timing extraction — the fictional-timing surface
# --------------------------------------------------------------------------- #
def _multi_cycle_latency(cm: dict[str, Any]) -> list[str]:
    """Return latency entries that imply non-combinational timing.

    An entry is fictional-for-combinational when its ``max_cycles`` is null
    (unbounded / variable, i.e. it waits for something) or any declared bound is
    > 1 (multi-cycle). A flat single-cycle registered output (``max_cycles`` <= 1)
    is tolerated — a combinational result may legitimately be registered once.
    """
    latency = cm.get("latency")
    flagged: list[str] = []
    if not isinstance(latency, dict):
        return flagged
    for tx_name, spec in latency.items():
        if tx_name == "default":
            continue
        if isinstance(spec, dict):
            max_c = spec.get("max_cycles")
            min_c = spec.get("min_cycles")
            if max_c is None:
                flagged.append(f"{tx_name}(max_cycles=null/unbounded)")
                continue
            for label, val in (("max_cycles", max_c), ("min_cycles", min_c)):
                try:
                    if val is not None and int(val) > 1:
                        flagged.append(f"{tx_name}({label}={val})")
                        break
                except (TypeError, ValueError):
                    # Symbolic/parameterized latency expr — treat as multi-cycle.
                    flagged.append(f"{tx_name}({label}={val!r})")
                    break
        else:
            try:
                if int(spec) > 1:
                    flagged.append(f"{tx_name}({spec})")
            except (TypeError, ValueError):
                flagged.append(f"{tx_name}({spec!r})")
    return flagged


def _cycle_timing_summary(cm: dict[str, Any]) -> dict[str, Any]:
    """Machine-readable summary of the cycle-level timing the CL declares."""
    outstanding = cm.get("outstanding")
    perf = cm.get("performance") if isinstance(cm.get("performance"), dict) else {}
    perf_outstanding = perf.get("outstanding") if isinstance(perf, dict) else None
    out_val = None
    if isinstance(outstanding, int):
        out_val = outstanding
    elif isinstance(perf_outstanding, int):
        out_val = perf_outstanding
    return {
        "handshake_rules": cm.get("handshake_rules"),
        "ordering": cm.get("ordering"),
        "pipeline": cm.get("pipeline"),
        "backpressure": cm.get("backpressure"),
        "arbitration": cm.get("arbitration"),
        "outstanding": out_val,
        "latency": cm.get("latency"),
        "multi_cycle_latency": _multi_cycle_latency(cm),
    }


# --------------------------------------------------------------------------- #
# Deterministic FAST-PATH backstop
# --------------------------------------------------------------------------- #
def _deterministic_violations(
    *,
    contracts: dict[str, dict[str, Any]],
    ssot: dict[str, Any],
    waived_ids: set[str],
) -> list[dict[str, Any]]:
    """Return CRITICAL fictional-timing violations independent of any LLM.

    When *every* behavioral contract carries ``cycle_model_waiver=true`` the IP
    is combinational / cycle-less, so the SSOT ``cycle_model`` must not declare
    cycle-level timing machinery. Each kind of fictional timing is reported as a
    distinct CRITICAL violation.
    """
    violations: list[dict[str, Any]] = []
    cm = _cycle_model(ssot)
    if not cm:
        return violations

    all_contracts_waived = bool(contracts) and set(contracts) == set(waived_ids)
    if not all_contracts_waived:
        # At least one contract has cycle semantics — the timing is (potentially)
        # justified; leave faithfulness to the LLM judge rather than guessing.
        return violations

    refs = sorted(waived_ids)

    def flag(kind: str, detail: str) -> None:
        violations.append({
            "severity": "critical",
            "kind": "fictional_timing",
            "contract_refs": refs,
            "subkind": kind,
            "detail": detail,
        })

    if _nonempty(cm.get("handshake_rules")):
        flag(
            "handshake",
            "cycle_model.handshake_rules declares a valid/ready handshake, but every "
            "behavioral contract is cycle_model_waiver=true (combinational): a cycle-waived "
            "IP has no handshake/backpressure timing",
        )
    if _nonempty(cm.get("ordering")):
        flag(
            "ordering",
            "cycle_model.ordering declares clock-edge / FSM-terminal ordering rules, but every "
            "behavioral contract is cycle_model_waiver=true (combinational): a cycle-waived IP "
            "has no multi-cycle ordering",
        )
    if _nonempty(cm.get("pipeline")):
        flag(
            "pipeline",
            "cycle_model.pipeline declares pipeline stages, but every behavioral contract is "
            "cycle_model_waiver=true (combinational): a cycle-waived IP is not pipelined",
        )
    if _nonempty(cm.get("backpressure")):
        flag(
            "backpressure",
            "cycle_model.backpressure is declared, but every behavioral contract is "
            "cycle_model_waiver=true (combinational): a cycle-waived IP cannot stall",
        )
    if _nonempty(cm.get("arbitration")):
        flag(
            "arbitration",
            "cycle_model.arbitration is declared, but every behavioral contract is "
            "cycle_model_waiver=true (combinational): a cycle-waived IP has no multi-cycle arbitration",
        )
    summary = _cycle_timing_summary(cm)
    if isinstance(summary["outstanding"], int) and summary["outstanding"] > 1:
        flag(
            "outstanding",
            f"cycle_model declares outstanding={summary['outstanding']} (>1), but every behavioral "
            "contract is cycle_model_waiver=true (combinational): a cycle-waived IP has at most one "
            "in-flight transaction",
        )
    if summary["multi_cycle_latency"]:
        flag(
            "latency",
            f"cycle_model.latency declares multi-cycle / unbounded latency {summary['multi_cycle_latency']}, "
            "but every behavioral contract is cycle_model_waiver=true (combinational): a cycle-waived IP "
            "resolves within a single cycle",
        )
    return violations


# --------------------------------------------------------------------------- #
# LLM judge
# --------------------------------------------------------------------------- #
_JUDGE_SYSTEM_PROMPT = (
    "You are a hardware verification judge for CYCLE-LEVEL timing. You are given ONE "
    "locked behavioral contract (a when->then decision table, a cycle_model_waiver flag, "
    "and any declared state_transitions / latency) and the cycle-model (CL) timing that is "
    "supposed to realise it: latency, handshake_rules, ordering, pipeline and outstanding. "
    "Decide whether the CL timing faithfully realises the contract.\n\n"
    "Rules:\n"
    "- FICTIONAL TIMING: if cycle_model_waiver=true the contract is combinational; the CL must "
    "have NO handshake/backpressure, NO multi-cycle ordering tied to an FSM, NO pipeline, "
    "outstanding<=1 and single-cycle (or zero) latency. Flag any such timing the contract does "
    "not require as a CRITICAL violation.\n"
    "- UNREALIZED TIMING: if the contract DOES require cycle behaviour (waiver=false, e.g. a "
    "latency bound, handshake or ordering), flag CL timing that is missing or contradicts the "
    "contract.\n"
    "- UNJUSTIFIED TIMING: flag CL timing (a handshake/ordering rule, a latency entry) that no "
    "contract justifies.\n\n"
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
        "latency": contract.get("latency"),
        "description": contract.get("description") or contract.get("intent"),
    }


def _cl_timing_payload(cm: dict[str, Any], contract_id: str, ssot: dict[str, Any]) -> dict[str, Any]:
    """CL timing relevant to one contract.

    Handshake/ordering/pipeline are global CL properties (the CL emitter models
    them IP-wide), so they are shown for every contract. Latency is keyed by
    transaction kind; we surface the entries for the contract's transactions plus
    the global default.
    """
    summary = _cycle_timing_summary(cm)
    fm = _function_model(ssot)
    txn_kinds = {
        str(tx.get("name") or tx.get("id"))
        for tx in _as_list(fm.get("transactions"))
        if isinstance(tx, dict) and contract_id in _transaction_contract_refs(tx)
    }
    latency = cm.get("latency") if isinstance(cm.get("latency"), dict) else {}
    contract_latency = {
        name: spec for name, spec in latency.items()
        if name in txn_kinds or name == "default"
    }
    return {
        "handshake_rules": summary["handshake_rules"],
        "ordering": summary["ordering"],
        "pipeline": summary["pipeline"],
        "backpressure": summary["backpressure"],
        "outstanding": summary["outstanding"],
        "contract_latency": contract_latency or None,
        "multi_cycle_latency": summary["multi_cycle_latency"],
    }


def _parse_judge_response(raw: str) -> dict[str, Any] | None:
    text = (raw or "").strip()
    if not text:
        return None
    if "```" in text:
        for chunk in text.split("```"):
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
    """Run the per-contract LLM judge over CL timing. Returns a structured block.

    ``status`` is one of ``pass`` (all faithful), ``fail`` (a critical violation),
    ``warning`` (non-critical only) or ``not_run`` (LLM unavailable / errored —
    never a silent pass).

    Each per-contract verdict is served from a content-keyed cache when available
    (``judge_verdict_cache``): an unchanged contract+timing reuses the stored
    verdict and makes NO LLM call (``cache_hit=True``), so determinism is
    structural and the CL stage no longer redundantly re-judges unchanged content.
    """
    cm = _cycle_model(ssot)
    per_contract: list[dict[str, Any]] = []
    violations: list[dict[str, Any]] = []
    blocked_reason = ""
    judged = 0

    for contract_id, contract in sorted(contracts.items()):
        waived = contract_id in waived_ids
        prompt_obj = {
            "behavioral_contract": _contract_payload(contract, waived),
            "cl_timing": _cl_timing_payload(cm, contract_id, ssot),
        }

        def judge_call(_cid: str = contract_id, _obj: dict[str, Any] = prompt_obj) -> dict[str, Any]:
            prompt = (
                "Judge whether the CL timing faithfully realises the locked behavioral "
                "contract below.\n\n" + json.dumps(_obj, indent=2, sort_keys=True)
            )
            try:
                response = llm_provider.complete(
                    stage="cl-model-gen",
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
                domain="cl",
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
        os.getenv("ATLAS_CL_SEMANTIC_JUDGE_MODEL")
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
def validate_cl_semantics(
    ip: str,
    root: Path,
    *,
    llm_provider: Any = None,
    model: str | None = None,
    use_llm: bool | None = None,
) -> dict[str, Any]:
    """Validate the CL model timing against locked behavioral contracts.

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
        "type": "cl_semantic_validation",
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

    if not _cycle_model(ssot):
        # No cycle_model section → no CL artifact → no fictional timing possible.
        return {**base, "status": "inactive", "passed": True,
                "reason": "ssot.cycle_model absent (no CL model emitted)"}

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
        "cycle_timing": _cycle_timing_summary(_cycle_model(ssot)),
        "deterministic_backstop": {
            "status": "fail" if any(
                str(v.get("severity")).lower() == "critical" for v in deterministic
            ) else "pass",
            "violations": deterministic,
        },
        "llm_judge": llm_block,
        "violations": critical,
        "reason": "; ".join(reasons) if reasons else "CL timing is semantically faithful to locked contracts",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ip")
    parser.add_argument("--root", default=".")
    parser.add_argument("--no-llm", action="store_true", help="run only the deterministic backstop")
    parser.add_argument("--model", default=None)
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    report = validate_cl_semantics(
        args.ip, root, model=args.model, use_llm=not args.no_llm
    )
    status = "PASS" if report.get("passed") else "FAIL"
    print(f"[validate_cl_semantics] {status} ip={args.ip} status={report.get('status')}")
    print(report.get("reason", ""))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
