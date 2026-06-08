#!/usr/bin/env python3
"""Project the locked VCM requirement bundle into per-stage visible TODOs.

For a workflow stage (tb / sim / lint) this selects the obligations that stage
*owns* and emits one visible TODO per obligation, carrying the full
``requirement -> obligation -> contract_ref/structural_contract/behavioral_contract
-> ssot_anchor`` chain plus the ``evidence_plan`` pass_condition as criteria. A
final deterministic gate is added by the caller (the stage engine).

Stage-ownership rule is the SAME convention already enforced at signoff
(workflow/signoff/scripts/check_ip_signoff.py): an obligation belongs to stage S
iff ``owned_by_stage == S`` OR ``closure_stage == S`` OR ``S in required_stages``
(and ``granularity in {content, temporal}`` implies sim), plus any of its
contract_refs or behavioral_contract_refs declaring a ``stage_contracts[].stage
== S``.

Returns ``[]`` when no locked bundle exists so the caller keeps its existing
single-visible behaviour (back-compatible; not a new fallback layer).

The bundle shape mirrors src/atlas_req_export.load_req_bundle; it is re-read here
to keep this a standalone, dependency-free workflow script.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Obligation granularities that inherently require sim-stage evidence (VCM).
_SIM_GRANULARITIES = {"content", "temporal"}


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _doc_list(doc: Any, key: str) -> list[dict[str, Any]]:
    if isinstance(doc, dict):
        value = doc.get(key)
    elif isinstance(doc, list):
        value = doc
    else:
        value = None
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _str_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _short(text: str, limit: int = 80) -> str:
    text = " ".join(str(text or "").split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def load_bundle(ip: str, root: Path) -> dict[str, list[dict[str, Any]]]:
    """Read the locked req bundle for ``ip`` into id-keyed lists."""
    req = Path(root) / ip / "req"
    return {
        "requirements": _doc_list(_read_json(req / "requirements_index.json"), "requirements"),
        "obligations": _doc_list(_read_json(req / "obligations.json"), "obligations"),
        "contracts": _doc_list(_read_json(req / "contract_refs.json"), "contract_refs"),
        "structural": _doc_list(_read_json(req / "structural_contracts.json"), "contracts"),
        "behavioral": _doc_list(_read_json(req / "behavioral_contracts.json"), "contracts"),
        "evidence": _doc_list(_read_json(req / "evidence_plan.json"), "evidence_plan"),
    }


def _obligation_owns_stage(ob: dict[str, Any], stage: str, contract_by_id: dict[str, dict[str, Any]]) -> bool:
    """Canonical VCM stage-ownership rule (see module docstring)."""
    stages = _str_list(ob.get("required_stages"))
    owned = str(ob.get("owned_by_stage") or ob.get("closure_stage") or "").strip()
    gran = str(ob.get("granularity") or "").strip()
    if owned == stage or stage in stages:
        return True
    if stage == "sim" and gran in _SIM_GRANULARITIES:
        return True
    for cref_id in _str_list(ob.get("contract_refs")) + _str_list(ob.get("behavioral_contract_refs")):
        cref = contract_by_id.get(cref_id) or {}
        for sc in cref.get("stage_contracts") or []:
            if isinstance(sc, dict) and str(sc.get("stage") or "").strip() == stage:
                return True
    return False


def stage_obligation_todos(ip: str, stage: str, root: str | Path) -> list[dict[str, Any]]:
    """Return one visible-TODO dict per obligation that ``stage`` owns.

    Empty list when no locked bundle / no owned obligations (caller falls back to
    its current single-visible behaviour).
    """
    stage = str(stage or "").strip()
    bundle = load_bundle(ip, Path(root))
    obligations = bundle["obligations"]
    if not obligations:
        return []

    contracts = bundle["contracts"]
    behavioral = bundle["behavioral"]
    contract_by_id = {str(c.get("contract_ref_id")): c for c in contracts}
    for contract in behavioral:
        contract_id = str(contract.get("id") or contract.get("behavioral_contract_id") or contract.get("contract_ref_id") or "").strip()
        if contract_id:
            contract_by_id[contract_id] = contract
    ev_by_contract: dict[str, list[dict[str, Any]]] = {}
    for ev in bundle["evidence"]:
        ev_by_contract.setdefault(str(ev.get("contract_ref")), []).append(ev)
    req_by_ob: dict[str, list[str]] = {}
    for req in bundle["requirements"]:
        for ob_id in _str_list(req.get("obligation_refs")):
            req_by_ob.setdefault(ob_id, []).append(str(req.get("requirement_id")))
    structural_by_ob: dict[str, list[str]] = {}
    for contract in bundle["structural"]:
        struct_id = str(contract.get("id") or contract.get("contract_id") or "").strip()
        if not struct_id:
            continue
        for ob_id in _str_list(contract.get("obligations") or contract.get("obligation_refs")):
            structural_by_ob.setdefault(ob_id, []).append(struct_id)
    behavioral_by_ob: dict[str, list[str]] = {}
    for contract in behavioral:
        contract_id = str(contract.get("id") or contract.get("behavioral_contract_id") or contract.get("contract_ref_id") or "").strip()
        if not contract_id:
            continue
        for ob_id in _str_list(contract.get("obligations") or contract.get("obligation_refs")):
            behavioral_by_ob.setdefault(ob_id, []).append(contract_id)

    selected = [ob for ob in obligations if _obligation_owns_stage(ob, stage, contract_by_id)]
    selected.sort(key=lambda ob: str(ob.get("obligation_id")))
    total = len(selected)
    todos: list[dict[str, Any]] = []
    for index, ob in enumerate(selected, 1):
        ob_id = str(ob.get("obligation_id") or f"OBL_{index}")
        statement = str(ob.get("statement") or ob_id)
        crefs = _str_list(ob.get("contract_refs"))
        structural_refs = list(dict.fromkeys(_str_list(ob.get("structural_contract_refs")) + structural_by_ob.get(ob_id, [])))
        behavioral_refs = list(dict.fromkeys(_str_list(ob.get("behavioral_contract_refs")) + behavioral_by_ob.get(ob_id, [])))
        all_contract_refs = list(dict.fromkeys(crefs + behavioral_refs))
        anchors = [str(contract_by_id.get(c, {}).get("ssot_anchor") or "").strip() for c in all_contract_refs]
        anchors = [a for a in anchors if a]
        req_ids = req_by_ob.get(ob_id, [])
        gran = str(ob.get("granularity") or "").strip()
        pass_conditions: list[str] = []
        artifacts: list[str] = []
        for c in all_contract_refs + structural_refs:
            for ev in ev_by_contract.get(c, []):
                if str(ev.get("pass_condition") or "").strip():
                    pass_conditions.append(str(ev.get("pass_condition")).strip())
                if str(ev.get("artifact") or "").strip():
                    artifacts.append(str(ev.get("artifact")).strip())

        detail = [
            f"Obligation {ob_id} ({stage} stage; granularity={gran or 'n/a'}).",
            f"Requirement(s): {', '.join(req_ids) or 'n/a'}",
            f"Contract(s): {', '.join(crefs) or 'n/a'}",
            f"Structural contract(s): {', '.join(structural_refs) or 'n/a'}",
            f"Behavioral contract(s): {', '.join(behavioral_refs) or 'n/a'}",
        ]
        if anchors:
            detail.append(f"SSOT anchor: {', '.join(anchors)}")
        detail.append(statement)

        criteria = list(dict.fromkeys(pass_conditions)) or [
            f"Evidence for {ob_id} satisfies its contract pass condition",
        ]
        criteria.append(f"check_evidence_contract.py confirms {ob_id} is closed with fresh evidence")

        todos.append({
            "id": ob_id,
            "content": f"[gen-{stage} {index}/{total}] {_short(statement)}",
            "activeForm": f"Closing obligation {ob_id} for the {stage} stage",
            "detail": "\n".join(detail),
            "criteria": "\n".join(criteria),
            "priority": "high",
            "required_evidence": list(dict.fromkeys(artifacts)),
            "source_refs": list(dict.fromkeys(req_ids + [ob_id] + crefs + structural_refs + behavioral_refs + anchors)),
        })
    return todos


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Project locked req bundle into per-stage obligation TODOs.")
    ap.add_argument("ip")
    ap.add_argument("stage", help="tb | sim | lint")
    ap.add_argument("--root", default=".")
    ns = ap.parse_args(argv)
    todos = stage_obligation_todos(ns.ip, ns.stage, ns.root)
    json.dump({"ip": ns.ip, "stage": ns.stage, "count": len(todos), "todos": todos}, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
