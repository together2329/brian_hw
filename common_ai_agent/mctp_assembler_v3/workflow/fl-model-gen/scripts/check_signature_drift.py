#!/usr/bin/env python3
"""Detect drift in <ip>/model/model_signature.json against the last-known lock.

T2 enforcement helper. Downstream workers (rtl-gen, tb-gen, sim-debug,
syn, etc.) should call this on entry. If the signature has changed since
the last lock, the worker emits `[SSOT HANDOFF] golden_changed -> human`
and stops; human must approve and update the lock.

Usage (worker entry):
  python3 workflow/fl-model-gen/scripts/check_signature_drift.py <ip> --root .

Exit codes:
  0  — signature matches lock OR lock file missing (first run; lock created)
  1  — signature differs from lock; print diff details and exit
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


_HASH_KEYS = ("ssot_hash", "transactions_hash", "invariants_hash", "expressions_hash")


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _diff(prev: dict[str, Any], curr: dict[str, Any]) -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for k in _HASH_KEYS:
        a = str(prev.get(k, "<missing>"))
        b = str(curr.get(k, "<missing>"))
        if a != b:
            out.append((k, a, b))
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ip")
    parser.add_argument("--root", default=".")
    parser.add_argument("--update-lock", action="store_true",
                        help="Update lock to match current signature (use only after human approval)")
    parser.add_argument("--worker", default="<unknown>",
                        help="Worker name for the [SSOT HANDOFF] message")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    ip_dir = root / args.ip
    sig_path = ip_dir / "model" / "model_signature.json"
    lock_path = ip_dir / "model" / ".signature.lock"

    sig = _load_json(sig_path)
    if sig is None:
        print(f"[check_signature_drift] {args.ip}: model_signature.json missing — run emit_model_signature.py first",
              file=sys.stderr)
        return 1

    lock = _load_json(lock_path)
    if lock is None:
        # First run — establish lock
        lock_path.write_text(json.dumps({k: sig.get(k) for k in _HASH_KEYS} | {"ip": sig.get("ip")},
                                        indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"[check_signature_drift] {args.ip}: lock established (first run)")
        return 0

    diffs = _diff(lock, sig)
    if not diffs:
        print(f"[check_signature_drift] {args.ip}: signature OK (worker={args.worker})")
        return 0

    if args.update_lock:
        lock_path.write_text(json.dumps({k: sig.get(k) for k in _HASH_KEYS} | {"ip": sig.get("ip")},
                                        indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"[check_signature_drift] {args.ip}: lock updated by human-approved worker={args.worker}")
        for k, a, b in diffs:
            print(f"  {k}: {a[:16]}.. -> {b[:16]}..")
        return 0

    print(f"[SSOT HANDOFF] golden_changed -> human (ip={args.ip}, worker={args.worker})", file=sys.stderr)
    for k, a, b in diffs:
        print(f"  {k}: {a[:16]}.. -> {b[:16]}..", file=sys.stderr)
    print("  Resolution: review the SSOT change with a human; then re-run with --update-lock.",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
