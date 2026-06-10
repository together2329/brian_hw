#!/usr/bin/env python3
"""Emit the VCM spine as a graph document for interactive visualization.

Requirement -> Obligation -> Contract (CR/SC/BEH) -> Evidence -> Validation
nodes plus typed edges, with per-node status so a UI (React Flow tab,
task-tracked) can filter: locked requirements, closed contracts, open
evidence, validation pass/fail, free-text search.

Reads (all optional beyond the bundle):
  <ip>/req/{requirements_index,obligations,contract_refs,
            structural_contracts,behavioral_contracts,evidence_plan}.json
  <ip>/req/approval_manifest.json        (locked status)
  <ip>/req/contract_closure.json         (closure per contract)
  <ip>/req/ssot_validation.json          (to-ssot validation result)
  <ip>/model/fl_contract_check.json      (FL contract gate)
  <ip>/sim/scoreboard_events.jsonl       (sim evidence pass counts)

Writes <ip>/req/vcm_graph.json:
  {nodes: [{id, kind, label, status, data}], edges: [{source, target, kind}]}

Pure read-side reporter: never mutates authority artifacts.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _refs(entry: dict[str, Any], *keys: str) -> list[str]:
    for key in keys:
        raw = entry.get(key)
        if isinstance(raw, list):
            values = [str(v).strip() for v in raw if str(v).strip()]
            if values:
                return values
        elif isinstance(raw, str) and raw.strip():
            return [raw.strip()]
    return []


def build_graph(ip_dir: Path, ip: str) -> dict[str, Any]:
    req_dir = ip_dir / "req"
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, str]] = []

    def add_node(node_id: str, kind: str, label: str, status: str, data: dict[str, Any]) -> None:
        nodes[node_id] = {"id": node_id, "kind": kind, "label": label, "status": status, "data": data}

    def add_edge(src: str, dst: str, kind: str) -> None:
        edges.append({"source": src, "target": dst, "kind": kind})

    manifest = _read_json(req_dir / "approval_manifest.json") or {}
    locked = isinstance(manifest, dict) and manifest.get("status") == "requirements_locked"

    closure = _read_json(req_dir / "contract_closure.json") or {}
    closure_by_contract: dict[str, str] = {}
    for item in closure.get("contracts", []) if isinstance(closure, dict) else []:
        if isinstance(item, dict) and item.get("contract_ref"):
            closure_by_contract[str(item["contract_ref"])] = str(item.get("status") or "unknown")

    # --- requirements -------------------------------------------------------
    req_doc = _read_json(req_dir / "requirements_index.json") or {}
    for entry in req_doc.get("requirements", []) if isinstance(req_doc, dict) else []:
        if not isinstance(entry, dict):
            continue
        rid = str(entry.get("requirement_id") or "")
        if not rid:
            continue
        status = "locked" if locked else str(entry.get("status") or "draft")
        add_node(rid, "requirement", str(entry.get("title") or rid), status, {
            "statement": entry.get("statement") or "",
            "required": entry.get("required", True),
        })
        for ref in _refs(entry, "obligation_refs", "obligations", "obligation_ids"):
            add_edge(rid, ref, "requires")

    # --- obligations --------------------------------------------------------
    obl_doc = _read_json(req_dir / "obligations.json") or {}
    for entry in obl_doc.get("obligations", []) if isinstance(obl_doc, dict) else []:
        if not isinstance(entry, dict):
            continue
        oid = str(entry.get("obligation_id") or "")
        if not oid:
            continue
        add_node(oid, "obligation", oid, str(entry.get("status") or ("locked" if locked else "open")), {
            "statement": entry.get("statement") or "",
            "owned_by": entry.get("owned_by") or "",
            "closure_stage": entry.get("closure_stage") or "",
            "granularity": entry.get("granularity") or "",
        })
        for ref in _refs(entry, "requirement_refs", "requirements", "requirement_ids"):
            add_edge(ref, oid, "requires")
        for ref in _refs(entry, "contract_refs", "contracts", "contract_ref_ids"):
            add_edge(oid, ref, "contracted_by")
        for ref in _refs(entry, "structural_contract_refs", "structural_contracts"):
            add_edge(oid, ref, "contracted_by")
        for ref in _refs(entry, "behavioral_contract_refs", "behavioral_contracts"):
            add_edge(oid, ref, "contracted_by")

    # --- contracts (anchor refs + structural + behavioral) -------------------
    def contract_status(cid: str) -> str:
        return closure_by_contract.get(cid, "open")

    con_doc = _read_json(req_dir / "contract_refs.json") or {}
    for entry in con_doc.get("contract_refs", []) if isinstance(con_doc, dict) else []:
        if not isinstance(entry, dict):
            continue
        cid = str(entry.get("contract_ref_id") or "")
        if not cid:
            continue
        add_node(cid, "contract_ref", cid, contract_status(cid), {
            "kind": entry.get("kind") or "",
        })
        for ref in _refs(entry, "obligation_refs", "obligations", "obligation_ids"):
            add_edge(ref, cid, "contracted_by")
    for name, kind in (("structural_contracts.json", "structural_contract"),
                       ("behavioral_contracts.json", "behavioral_contract")):
        doc = _read_json(req_dir / name) or {}
        for entry in doc.get("contracts", []) if isinstance(doc, dict) else []:
            if not isinstance(entry, dict):
                continue
            cid = str(entry.get("id") or entry.get("contract_id") or "")
            if not cid:
                continue
            add_node(cid, kind, str(entry.get("title") or cid), contract_status(cid), {
                "ssot_anchor": entry.get("ssot_anchor") or "",
                "cycle_model_waiver": bool(entry.get("cycle_model_waiver")),
            })
            for ref in _refs(entry, "obligations", "obligation_refs"):
                add_edge(ref, cid, "contracted_by")

    # --- evidence ------------------------------------------------------------
    ev_doc = _read_json(req_dir / "evidence_plan.json") or {}
    for entry in ev_doc.get("evidence_plan", []) if isinstance(ev_doc, dict) else []:
        if not isinstance(entry, dict):
            continue
        eid = str(entry.get("evidence_id") or "")
        target = str(entry.get("contract_ref") or "")
        if not eid:
            continue
        artifact = str(entry.get("artifact") or "")
        exists = bool(artifact) and (ip_dir / artifact).exists()
        add_node(eid, "evidence", eid, "present" if exists else "planned", {
            "stage": entry.get("stage") or "",
            "artifact": artifact,
            "validator": entry.get("validator") or "",
            "pass_condition": entry.get("pass_condition") or "",
        })
        if target:
            add_edge(target, eid, "evidenced_by")

    # --- validation results ---------------------------------------------------
    validations: list[tuple[str, Path, str]] = [
        ("VAL_SSOT", req_dir / "ssot_validation.json", "to-ssot verify_ssot"),
        ("VAL_FL_CONTRACT", ip_dir / "model" / "fl_contract_check.json", "FL contract gate"),
        ("VAL_CONTRACT_CLOSURE", req_dir / "contract_closure.json", "bundle closure"),
    ]
    for vid, path, label in validations:
        doc = _read_json(path)
        if doc is None:
            continue
        if vid == "VAL_CONTRACT_CLOSURE" and isinstance(doc, dict):
            items = [i for i in doc.get("contracts", []) if isinstance(i, dict)]
            ok = bool(items) and all(str(i.get("status")) == "closed" for i in items)
        else:
            ok = bool(doc.get("ok", doc.get("passed", False))) if isinstance(doc, dict) else False
        add_node(vid, "validation", label, "pass" if ok else "fail", {
            "artifact": str(path.relative_to(ip_dir)),
        })
    sb = ip_dir / "sim" / "scoreboard_events.jsonl"
    if sb.is_file():
        rows = [json.loads(l) for l in sb.read_text(encoding="utf-8").splitlines() if l.strip()]
        passed = sum(1 for r in rows if r.get("passed"))
        add_node("VAL_SIM_SCOREBOARD", "validation", f"sim scoreboard {passed}/{len(rows)}",
                 "pass" if rows and passed == len(rows) else ("fail" if rows else "planned"),
                 {"artifact": "sim/scoreboard_events.jsonl", "passed": passed, "total": len(rows)})
    # validation nodes attach to every evidence node of their stage
    stage_to_val = {"sim": "VAL_SIM_SCOREBOARD", "ssot": "VAL_SSOT", "fl": "VAL_FL_CONTRACT"}
    for node in list(nodes.values()):
        if node["kind"] != "evidence":
            continue
        vid = stage_to_val.get(str(node["data"].get("stage") or "").lower())
        if vid and vid in nodes:
            add_edge(node["id"], vid, "validated_by")

    # drop dangling edges (refs to ids that never materialized stay visible as ghosts)
    for edge in edges:
        for end in ("source", "target"):
            node_id = edge[end]
            if node_id not in nodes:
                add_node(node_id, "ghost", node_id, "missing", {})

    return {
        "schema_version": 1,
        "type": "vcm_graph",
        "ip": ip,
        "locked": locked,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "counts": {
            kind: sum(1 for n in nodes.values() if n["kind"] == kind)
            for kind in ("requirement", "obligation", "contract_ref", "structural_contract",
                         "behavioral_contract", "evidence", "validation", "ghost")
        },
        "nodes": sorted(nodes.values(), key=lambda n: (n["kind"], n["id"])),
        "edges": edges,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit VCM spine graph for visualization.")
    parser.add_argument("ip")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    ip_dir = Path(args.root).resolve() / args.ip
    if not ip_dir.is_dir():
        print(f"[emit_vcm_graph] missing ip dir: {ip_dir}")
        return 1
    graph = build_graph(ip_dir, args.ip)
    out = ip_dir / "req" / "vcm_graph.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(graph, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    counts = " ".join(f"{k}={v}" for k, v in graph["counts"].items() if v)
    print(f"[emit_vcm_graph] {args.ip}: nodes={len(graph['nodes'])} edges={len(graph['edges'])} {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
