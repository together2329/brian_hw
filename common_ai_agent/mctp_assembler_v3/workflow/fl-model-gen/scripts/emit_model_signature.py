#!/usr/bin/env python3
"""Emit a deterministic SHA-256-based signature of the SSOT-derived golden model.

Downstream workers use this signature to detect silent semantic changes in the
functional model without re-running full equivalence checks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# SSOT loading (mirrors emit_fl_model.py::_load_ssot)
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
# Canonicalization helpers
# ---------------------------------------------------------------------------

def _canon(obj: Any) -> str:
    """Return a deterministic JSON string for any object."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def _sha256(text: str) -> str:
    """Return lowercase hex SHA-256 of a UTF-8-encoded string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _as_list(value: Any) -> list[Any]:
    """Coerce a value to list; dict becomes list of name/value items."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [{"name": k, "value": v} for k, v in value.items()]
    return [value]


def _rule_items(section: Any) -> list[dict[str, Any]]:
    """Normalise output_rules / state_updates to a flat list of dicts."""
    items: list[dict[str, Any]] = []
    if isinstance(section, dict):
        for k, v in section.items():
            items.append({"name": k, "value": v})
    elif isinstance(section, list):
        for entry in section:
            if isinstance(entry, dict):
                items.append(entry)
            else:
                items.append({"value": entry})
    return items


# ---------------------------------------------------------------------------
# Hash computation
# ---------------------------------------------------------------------------

def _hash_ssot(ssot: dict[str, Any]) -> str:
    return _sha256(_canon(ssot))


def _hash_transactions(ssot: dict[str, Any]) -> str:
    fm = ssot.get("function_model") if isinstance(ssot.get("function_model"), dict) else {}
    txs = _as_list(fm.get("transactions"))
    if not txs:
        return _sha256("")
    parts = [_canon(tx) for tx in txs]
    return _sha256("\n".join(parts))


def _hash_invariants(ssot: dict[str, Any]) -> str:
    fm = ssot.get("function_model") if isinstance(ssot.get("function_model"), dict) else {}
    invariants = fm.get("invariants")
    if invariants is None:
        return _sha256("")
    return _sha256(_canon(invariants))


def _hash_expressions(ssot: dict[str, Any]) -> str:
    fm = ssot.get("function_model") if isinstance(ssot.get("function_model"), dict) else {}
    txs = _as_list(fm.get("transactions"))
    exprs: list[str] = []
    for tx in txs:
        if not isinstance(tx, dict):
            continue
        # sample_condition of the transaction itself
        sc = tx.get("sample_condition")
        if sc is not None:
            exprs.append(str(sc))
        # output_rules: extract expr / expression / value fields
        for item in _rule_items(tx.get("output_rules")):
            for field in ("expr", "expression", "value"):
                val = item.get(field)
                if val is not None:
                    exprs.append(str(val))
        # state_updates: extract expr / expression / value fields
        for item in _rule_items(tx.get("state_updates")):
            for field in ("expr", "expression", "value"):
                val = item.get(field)
                if val is not None:
                    exprs.append(str(val))
    exprs.sort()
    return _sha256("\n".join(exprs))


# ---------------------------------------------------------------------------
# Payload construction
# ---------------------------------------------------------------------------

def _build_payload(ip: str, ssot: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "type": "model_signature",
        "ip": ip,
        "ssot_hash": _hash_ssot(ssot),
        "transactions_hash": _hash_transactions(ssot),
        "invariants_hash": _hash_invariants(ssot),
        "expressions_hash": _hash_expressions(ssot),
    }


def _write_signature(out_path: Path, payload: dict[str, Any]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# --check mode
# ---------------------------------------------------------------------------

def _check_signature(ip: str, ip_dir: Path, ssot: dict[str, Any]) -> int:
    sig_path = ip_dir / "model" / "model_signature.json"
    if not sig_path.is_file():
        raise SystemExit(f"[emit_model_signature] signature file not found: {sig_path}")

    existing: dict[str, Any] = json.loads(sig_path.read_text(encoding="utf-8"))
    current = _build_payload(ip, ssot)

    # Compare all fields
    diffs: list[str] = []
    all_keys = set(existing.keys()) | set(current.keys())
    for key in sorted(all_keys):
        old_val = existing.get(key)
        new_val = current.get(key)
        if old_val != new_val:
            diffs.append(f"  {key}: {old_val!r} -> {new_val!r}")

    if not diffs:
        print(f"[emit_model_signature] {ip} signature OK")
        return 0

    print(f"[emit_model_signature] {ip} signature DRIFT")
    for line in diffs:
        print(line)
    return 1


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit or verify the SHA-256-based model signature for an IP.",
    )
    parser.add_argument("ip", help="IP folder name (e.g. smbus)")
    parser.add_argument(
        "--root",
        default=".",
        help="Workspace root directory (default: .)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Read existing model_signature.json and verify; exit 0 if OK, 1 if drift.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    ip_dir = root / args.ip

    ssot = _load_ssot(ip_dir, args.ip)

    if args.check:
        return _check_signature(args.ip, ip_dir, ssot)

    payload = _build_payload(args.ip, ssot)
    out_path = ip_dir / "model" / "model_signature.json"
    _write_signature(out_path, payload)
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
