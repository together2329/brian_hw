#!/usr/bin/env python3
"""Detect drift in <ip>/model/model_signature.json against the last-known lock.

T2 enforcement helper. Downstream workers (rtl-gen, tb-gen, sim-debug,
syn, etc.) should call this on entry. If the signature has changed since
the last lock, the worker emits `[SSOT HANDOFF] golden_changed -> human`
and stops; human must approve and update the lock.

INTEGRITY NOTE: the lock file <ip>/model/.signature.lock SHOULD BE GIT-TRACKED.
The lock is untracked by default, which means deleting it silently re-blesses
whatever signature is present as a brand-new "first run" with no human review.
For real tamper-resistance, commit the lock to version control and review lock
changes in code review. On first-run lock creation this script prints a
prominent RE-BLESS warning naming every locked hash so the bless is auditable,
and `--strict` refuses to silently re-bless (see below).

Usage (worker entry):
  python3 workflow/fl-model-gen/scripts/check_signature_drift.py <ip> --root .

Exit codes:
  0  — signature matches lock OR lock file missing (first run; lock created)
  1  — signature differs from lock; print diff details and exit
       (also: --strict and the lock is absent while a signature exists)
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


def _norm_hash(value: Any) -> str:
    """Canonicalize a hash slot so absent and explicit-null compare equal.

    A lock created from a signature that had no hash keys stores them as JSON
    ``null`` (Python ``None``). The current signature returns ``<missing>`` for
    the same absent key. Without this normalization ``str(None) != "<missing>"``
    produces a spurious drift (D-M1). Both "no hash" forms collapse to the same
    sentinel here.
    """
    if value is None:
        return "<missing>"
    return str(value)


def _diff(prev: dict[str, Any], curr: dict[str, Any]) -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for k in _HASH_KEYS:
        a = _norm_hash(prev.get(k))
        b = _norm_hash(curr.get(k))
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
    parser.add_argument("--strict", action="store_true",
                        help="Refuse to silently re-bless: exit 1 when the lock is absent but "
                             "a signature exists (enforcement callers should pass this).")
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
        # First run — the lock is absent while a signature exists. This is the
        # silent re-bless window: without a pre-existing tracked lock we cannot
        # tell a legitimate first run from a tampered signature with a deleted
        # lock. Under --strict, refuse; otherwise establish the lock but emit a
        # prominent, auditable RE-BLESS warning naming every locked hash.
        locked = {k: sig.get(k) for k in _HASH_KEYS}
        if args.strict:
            print(f"[check_signature_drift] {args.ip}: STRICT lock-integrity failure — "
                  f".signature.lock is absent but model_signature.json exists.", file=sys.stderr)
            print("  This would silently re-bless the current signature. Restore the git-tracked "
                  "lock, or re-run without --strict (after human review) to establish it.",
                  file=sys.stderr)
            for k in _HASH_KEYS:
                print(f"  would-lock {k}: {_norm_hash(locked.get(k))[:32]}", file=sys.stderr)
            return 1
        lock_path.write_text(json.dumps(locked | {"ip": sig.get("ip")},
                                        indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"[check_signature_drift] {args.ip}: lock established (first run)")
        print("  *** RE-BLESS WARNING ***: no prior lock existed, so the current signature is "
              "now trusted as golden. The lock is git-untracked by default — commit "
              f"{lock_path.name} and review it so this bless cannot happen silently.")
        for k in _HASH_KEYS:
            print(f"  locked {k}: {_norm_hash(locked.get(k))[:32]}")
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
