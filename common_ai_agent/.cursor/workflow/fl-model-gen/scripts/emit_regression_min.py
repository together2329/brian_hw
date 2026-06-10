#!/usr/bin/env python3
"""Bisect a failing transaction sequence down to a minimal reproducer.

L8 of the human-LLM authority manifest. Reads a JSONL stimulus file (each
line = one transaction dict for FunctionalModel.apply) and shrinks it to
the smallest sub-sequence that still triggers a failure when replayed
against the IP's pure-Python FunctionalModel.

Usage:
  python3 workflow/fl-model-gen/scripts/emit_regression_min.py <ip> \
      --seed <ip>/sim/<seed>.jsonl --root .
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not path.is_file():
        raise SystemExit(f"missing seed JSONL: {path}")
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            obj = json.loads(line)
        except Exception as exc:
            raise SystemExit(f"{path}:{line_no} invalid JSON: {exc}")
        if not isinstance(obj, dict):
            raise SystemExit(f"{path}:{line_no} expected JSON object per line")
        out.append(obj)
    return out


def _load_fl(ip_dir: Path) -> Any:
    fm_path = ip_dir / "model" / "functional_model.py"
    if not fm_path.is_file():
        raise SystemExit(f"missing FL: {fm_path}")
    spec = importlib.util.spec_from_file_location(f"_fl_{ip_dir.name}", fm_path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot import {fm_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _replay(fl_mod: Any, sequence: list[dict[str, Any]]) -> tuple[bool, str]:
    """Return (failed, reason). Failed means at least one txn returned RESP_SLVERR."""
    fl = fl_mod.FunctionalModel()
    fl.reset()
    SLVERR = getattr(fl_mod, "RESP_SLVERR", 2)
    for idx, txn in enumerate(sequence):
        try:
            result = fl.apply(dict(txn))
        except Exception as exc:
            return True, f"exception@{idx}: {type(exc).__name__}: {str(exc)[:80]}"
        if result.get("resp") == SLVERR:
            return True, f"slverr@{idx}: kind={result.get('kind') or txn.get('kind')}"
        if result.get("error"):
            return True, f"error_field@{idx}: {result.get('error')}"
    return False, "no_failure"


def _bisect(fl_mod: Any, sequence: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    """Greedy bisect: drop halves while failure persists."""
    failed, reason = _replay(fl_mod, sequence)
    if not failed:
        return sequence, [f"input does not fail: {reason}"]

    log: list[str] = [f"initial_fail: {reason} (n={len(sequence)})"]
    current = list(sequence)

    # Phase 1: split-halves until indivisible.
    progress = True
    while progress and len(current) > 1:
        progress = False
        mid = len(current) // 2
        first_half = current[:mid]
        second_half = current[mid:]
        f1, r1 = _replay(fl_mod, first_half) if first_half else (False, "empty")
        f2, r2 = _replay(fl_mod, second_half) if second_half else (False, "empty")
        if f1:
            current = first_half
            log.append(f"keep_first_half: {r1} (n={len(current)})")
            progress = True
        elif f2:
            current = second_half
            log.append(f"keep_second_half: {r2} (n={len(current)})")
            progress = True
        else:
            break

    # Phase 2: linear shrink — drop one txn at a time, keep failures.
    i = 0
    while i < len(current) and len(current) > 1:
        candidate = current[:i] + current[i + 1:]
        failed_c, reason_c = _replay(fl_mod, candidate)
        if failed_c:
            current = candidate
            log.append(f"drop_idx_{i}: {reason_c} (n={len(current)})")
        else:
            i += 1
    return current, log


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ip")
    parser.add_argument("--root", default=".")
    parser.add_argument("--seed", required=True, help="Path to JSONL stimulus file (relative to root or absolute)")
    parser.add_argument("--out", default=None, help="Output JSONL path (default <ip>/sim/min_repro.jsonl)")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    ip_dir = root / args.ip
    seed_path = (root / args.seed).resolve() if not Path(args.seed).is_absolute() else Path(args.seed).resolve()

    sequence = _load_jsonl(seed_path)
    if not sequence:
        raise SystemExit(f"seed JSONL is empty: {seed_path}")

    sys.path.insert(0, str(ip_dir / "model"))
    fl_mod = _load_fl(ip_dir)

    minimal, log = _bisect(fl_mod, sequence)

    sim_dir = ip_dir / "sim"
    sim_dir.mkdir(parents=True, exist_ok=True)
    out_path = Path(args.out).resolve() if args.out else sim_dir / "min_repro.jsonl"
    out_path.write_text("\n".join(json.dumps(t, sort_keys=True) for t in minimal) + "\n", encoding="utf-8")

    summary = {
        "schema_version": 1,
        "type": "regression_min_summary",
        "ip": args.ip,
        "seed": str(seed_path),
        "input_size": len(sequence),
        "minimal_size": len(minimal),
        "shrink_log": log,
        "output": str(out_path.relative_to(ip_dir)) if str(out_path).startswith(str(ip_dir)) else str(out_path),
    }
    summary_path = sim_dir / "min_repro_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(f"[emit_regression_min] {args.ip} input={len(sequence)} minimal={len(minimal)}")
    print(f"[emit_regression_min] wrote {out_path}")
    return 0 if minimal else 1


if __name__ == "__main__":
    raise SystemExit(main())
