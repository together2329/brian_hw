#!/usr/bin/env python3
"""Split functional coverage plan into FL-only and CL-only plans, then regenerate union.

Outputs:
  <root>/<ip>/cov/fl_fcov_plan.json  — FL bins only
  <root>/<ip>/cov/cl_fcov_plan.json  — CL bins only (only when CL is triggered)
  <root>/<ip>/cov/fcov_plan.json     — union (FL + CL, dedup by id)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# SSOT loading
# ---------------------------------------------------------------------------

def _load_ssot(ip_dir: Path, ip: str) -> dict[str, Any]:
    path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    if not path.is_file():
        raise SystemExit(f"missing SSOT YAML: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"invalid SSOT YAML root: {path}")
    return data


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_name(raw: Any, fallback: str) -> str:
    text = str(raw or fallback).strip().lower()
    text = "".join(ch if ch.isalnum() else "_" for ch in text)
    while "__" in text:
        text = text.replace("__", "_")
    return text.strip("_") or fallback


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [{"name": key, "value": val} for key, val in value.items()]
    return [value]


def _dedup(bins: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for item in bins:
        if item["id"] in seen:
            continue
        seen.add(item["id"])
        unique.append(item)
    return unique


# ---------------------------------------------------------------------------
# CL trigger detection (mirrors emit_cycle_model.py logic)
# ---------------------------------------------------------------------------

def _cl_triggered(ssot: dict[str, Any]) -> bool:
    cm = ssot.get("cycle_model") if isinstance(ssot.get("cycle_model"), dict) else {}
    if cm.get("handshake_rules"):
        return True
    if cm.get("ordering"):
        return True
    if cm.get("arbitration"):
        return True
    outstanding = cm.get("outstanding")
    if isinstance(outstanding, (int, float)) and outstanding > 1:
        return True
    latency = cm.get("latency")
    if isinstance(latency, dict):
        for entry in latency.values():
            if isinstance(entry, dict) and entry.get("max_cycles") is None:
                return True
    synthesis = ssot.get("synthesis") if isinstance(ssot.get("synthesis"), dict) else {}
    ppa = synthesis.get("ppa_targets") if isinstance(synthesis.get("ppa_targets"), dict) else {}
    if ppa.get("frequency_mhz_min"):
        return True
    return False


# ---------------------------------------------------------------------------
# FL bin extraction
# ---------------------------------------------------------------------------

def _fl_bins(ssot: dict[str, Any]) -> list[dict[str, Any]]:
    bins: list[dict[str, Any]] = []

    # scenario bins — test_requirements.scenarios
    tr = ssot.get("test_requirements") if isinstance(ssot.get("test_requirements"), dict) else {}
    for idx, sc in enumerate(_as_list(tr.get("scenarios"))):
        if not isinstance(sc, dict):
            continue
        sid = str(sc.get("id") or f"SC{idx:02d}")
        bins.append({
            "id": f"{sid}_executed",
            "class": "scenario",
            "source": f"test_requirements.scenarios[{idx}]",
            "scenario": sid,
            "description": str(sc.get("name") or sc.get("expected") or sid),
        })

    # transaction_type bins — function_model.transactions
    fm = ssot.get("function_model") if isinstance(ssot.get("function_model"), dict) else {}
    for idx, tx in enumerate(fm.get("transactions") or []):
        if not isinstance(tx, dict):
            continue
        name = _safe_name(tx.get("name") or tx.get("id"), f"transaction_{idx}")
        bins.append({
            "id": f"function_{name}",
            "class": "transaction_type",
            "source": f"function_model.transactions[{idx}]",
            "description": str(tx.get("description") or tx.get("expected") or name),
        })

    # state_transition bins — fsm.*.transitions
    fsm = ssot.get("fsm") if isinstance(ssot.get("fsm"), dict) else {}
    fsm_blocks: list[tuple[str, Any]]
    if fsm and all(isinstance(v, dict) for v in fsm.values()):
        fsm_blocks = list(fsm.items())
    else:
        fsm_blocks = [("fsm", fsm)]
    for block_name, block in fsm_blocks:
        if not isinstance(block, dict):
            continue
        for idx, trn in enumerate(block.get("transitions") or []):
            if not isinstance(trn, dict):
                continue
            src = _safe_name(trn.get("from"), "from")
            dst = _safe_name(trn.get("to"), "to")
            bins.append({
                "id": f"fsm_{_safe_name(block_name, 'fsm')}_{src}_to_{dst}_{idx}",
                "class": "state_transition",
                "source": f"fsm.{block_name}.transitions[{idx}]",
                "description": str(trn.get("condition") or trn),
            })

    # error bins — error_handling.error_sources
    err = ssot.get("error_handling") if isinstance(ssot.get("error_handling"), dict) else {}
    for idx, src in enumerate(err.get("error_sources") or []):
        name = _safe_name(src.get("name") if isinstance(src, dict) else src, f"error_{idx}")
        bins.append({
            "id": f"error_{name}",
            "class": "error",
            "source": f"error_handling.error_sources[{idx}]",
            "description": str(src),
        })

    # invariant_violation bins — function_model.invariants
    for idx, inv in enumerate(fm.get("invariants") or []):
        if not isinstance(inv, dict):
            continue
        name = _safe_name(inv.get("name"), f"invariant_{idx}")
        bins.append({
            "id": f"invariant_{name}_violated",
            "class": "invariant_violation",
            "source": f"function_model.invariants[{idx}]",
            "description": str(inv.get("description") or inv.get("expression") or name),
        })

    return _dedup(bins)


# ---------------------------------------------------------------------------
# CL bin extraction
# ---------------------------------------------------------------------------

def _cl_bins(ssot: dict[str, Any]) -> list[dict[str, Any]]:
    bins: list[dict[str, Any]] = []
    cm = ssot.get("cycle_model") if isinstance(ssot.get("cycle_model"), dict) else {}

    # protocol_handshake bins — cycle_model.handshake_rules
    for idx, rule in enumerate(cm.get("handshake_rules") or []):
        if not isinstance(rule, dict):
            continue
        name = _safe_name(rule.get("name") or rule.get("id"), f"handshake_{idx}")
        bins.append({
            "id": f"cycle_{name}",
            "class": "protocol_handshake",
            "source": f"cycle_model.handshake_rules[{idx}]",
            "description": str(rule.get("description") or rule.get("predicate") or name),
        })

    # ordering bins — cycle_model.ordering
    for idx, item in enumerate(cm.get("ordering") or []):
        if not isinstance(item, dict):
            continue
        name = _safe_name(item.get("name") or item.get("id"), f"ordering_{idx}")
        bins.append({
            "id": f"ordering_{name}",
            "class": "ordering",
            "source": f"cycle_model.ordering[{idx}]",
            "description": str(item.get("description") or name),
        })

    # arbitration_decision bins — cycle_model.arbitration
    for idx, item in enumerate(cm.get("arbitration") or []):
        if not isinstance(item, dict):
            continue
        name = _safe_name(item.get("name") or item.get("id"), f"arbitration_{idx}")
        bins.append({
            "id": f"arbitration_{name}",
            "class": "arbitration_decision",
            "source": f"cycle_model.arbitration[{idx}]",
            "description": str(item.get("description") or name),
        })

    # latency_bin bins — cycle_model.latency (bucketize as <min, min, mid, max, >max)
    latency = cm.get("latency")
    if isinstance(latency, dict):
        for op_name, entry in latency.items():
            if not isinstance(entry, dict):
                continue
            min_c = entry.get("min_cycles")
            max_c = entry.get("max_cycles")
            safe_op = _safe_name(op_name, "op")
            source_ref = f"cycle_model.latency.{op_name}"

            # <min bucket — skip if min == 0
            if min_c is not None and min_c != 0:
                bins.append({
                    "id": f"latency_{safe_op}_lt_min",
                    "class": "latency_bin",
                    "source": source_ref,
                    "description": f"{op_name} latency < {min_c} cycles",
                    "bucket": "<min",
                    "threshold": min_c,
                })

            # min bucket
            if min_c is not None:
                bins.append({
                    "id": f"latency_{safe_op}_at_min",
                    "class": "latency_bin",
                    "source": source_ref,
                    "description": f"{op_name} latency == {min_c} cycles",
                    "bucket": "min",
                    "cycles": min_c,
                })

            # mid bucket — only when min and max are both set and differ
            if min_c is not None and max_c is not None and max_c > min_c:
                mid_c = (min_c + max_c) // 2
                bins.append({
                    "id": f"latency_{safe_op}_mid",
                    "class": "latency_bin",
                    "source": source_ref,
                    "description": f"{op_name} latency ~mid ({mid_c} cycles)",
                    "bucket": "mid",
                    "cycles": mid_c,
                })

            # max bucket
            if max_c is not None:
                bins.append({
                    "id": f"latency_{safe_op}_at_max",
                    "class": "latency_bin",
                    "source": source_ref,
                    "description": f"{op_name} latency == {max_c} cycles",
                    "bucket": "max",
                    "cycles": max_c,
                })

            # >max bucket — if max is null, emit unbounded instead
            if max_c is None:
                bins.append({
                    "id": f"latency_{safe_op}_unbounded",
                    "class": "latency_bin",
                    "source": source_ref,
                    "description": f"{op_name} latency unbounded (no max_cycles)",
                    "bucket": "unbounded",
                })
            else:
                bins.append({
                    "id": f"latency_{safe_op}_gt_max",
                    "class": "latency_bin",
                    "source": source_ref,
                    "description": f"{op_name} latency > {max_c} cycles",
                    "bucket": ">max",
                    "threshold": max_c,
                })

    # backpressure_event bins — cycle_model.backpressure
    for idx, item in enumerate(cm.get("backpressure") or []):
        if not isinstance(item, dict):
            continue
        name = _safe_name(item.get("name") or item.get("id"), f"backpressure_{idx}")
        bins.append({
            "id": f"backpressure_{name}",
            "class": "backpressure_event",
            "source": f"cycle_model.backpressure[{idx}]",
            "description": str(item.get("description") or name),
        })

    # outstanding_depth bins — cycle_model.outstanding
    outstanding = cm.get("outstanding")
    if isinstance(outstanding, (int, float)) and int(outstanding) >= 1:
        depth = int(outstanding)
        bins.append({
            "id": "outstanding_depth_1",
            "class": "outstanding_depth",
            "source": "cycle_model.outstanding",
            "description": f"1 outstanding transaction (min)",
            "depth": 1,
        })
        if depth > 1:
            bins.append({
                "id": f"outstanding_depth_{depth}",
                "class": "outstanding_depth",
                "source": "cycle_model.outstanding",
                "description": f"{depth} outstanding transactions (max)",
                "depth": depth,
            })

    return _dedup(bins)


# ---------------------------------------------------------------------------
# Plan builders
# ---------------------------------------------------------------------------

def _summary(bins: list[dict[str, Any]]) -> dict[str, Any]:
    by_class: dict[str, int] = {}
    for b in bins:
        cls = str(b.get("class") or "unknown")
        by_class[cls] = by_class.get(cls, 0) + 1
    return {"total_bins": len(bins), "by_class": by_class}


def _fl_plan(ip: str, bins: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "type": "fl_functional_coverage_plan",
        "ip": ip,
        "source": f"{ip}/yaml/{ip}.ssot.yaml",
        "planned_before_rtl": True,
        "level": "fl",
        "summary": _summary(bins),
        "bins": bins,
    }


def _cl_plan(ip: str, bins: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "type": "cl_functional_coverage_plan",
        "ip": ip,
        "source": f"{ip}/yaml/{ip}.ssot.yaml",
        "planned_before_rtl": True,
        "level": "cl",
        "summary": _summary(bins),
        "bins": bins,
    }


def _union_plan(ip: str, fl_bins: list[dict[str, Any]], cl_bins: list[dict[str, Any]]) -> dict[str, Any]:
    union_bins = _dedup(fl_bins + cl_bins)
    return {
        "schema_version": 1,
        "type": "functional_coverage_plan",
        "ip": ip,
        "source": f"{ip}/yaml/{ip}.ssot.yaml",
        "planned_before_rtl": True,
        "level": "union",
        "summary": _summary(union_bins),
        "bins": union_bins,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Split functional coverage into FL/CL plans and regenerate union view."
    )
    parser.add_argument("ip", help="IP name (must match <root>/<ip>/yaml/<ip>.ssot.yaml)")
    parser.add_argument("--root", default=".", help="Root directory containing IP folders")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    ip_dir = root / args.ip
    ssot = _load_ssot(ip_dir, args.ip)

    fl_bins = _fl_bins(ssot)
    triggered = _cl_triggered(ssot)
    cl_bins = _cl_bins(ssot) if triggered else []

    cov_dir = ip_dir / "cov"
    cov_dir.mkdir(parents=True, exist_ok=True)

    fl_plan = _fl_plan(args.ip, fl_bins)
    union_plan = _union_plan(args.ip, fl_bins, cl_bins)

    (cov_dir / "fl_fcov_plan.json").write_text(
        json.dumps(fl_plan, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )

    if triggered:
        cl_plan = _cl_plan(args.ip, cl_bins)
        (cov_dir / "cl_fcov_plan.json").write_text(
            json.dumps(cl_plan, indent=2, sort_keys=False) + "\n", encoding="utf-8"
        )
        print(f"[emit_dual_fcov] cl_fcov_plan.json written ({len(cl_bins)} bins)")

    (cov_dir / "fcov_plan.json").write_text(
        json.dumps(union_plan, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )

    print(
        f"[emit_dual_fcov] ip={args.ip} fl={len(fl_bins)} cl={len(cl_bins)} "
        f"union={len(union_plan['bins'])} cl_triggered={triggered}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
