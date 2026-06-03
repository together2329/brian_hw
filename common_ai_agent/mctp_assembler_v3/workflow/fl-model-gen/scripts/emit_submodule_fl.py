#!/usr/bin/env python3
"""Emit per-sub_module FL stubs that delegate to the top FunctionalModel.

Enables L2 (module-level) loop. For each entry under SSOT.sub_modules with
ownership=manifest and a non-empty `implements:` list, generate a thin
Python wrapper at <ip>/model/sub/<submodule>_fl.py that:
  1. imports the parent FunctionalModel,
  2. filters apply() to transactions whose IDs match the implements refs,
  3. exposes a per-module .observe_state() that returns only the state
     variables this module owns (per implements refs),
  4. records its own trace.

Usage:
  python3 workflow/fl-model-gen/scripts/emit_submodule_fl.py <ip> --root .
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


def _load_ssot(ip_dir: Path, ip: str) -> dict[str, Any]:
    path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    if not path.is_file():
        raise SystemExit(f"missing SSOT YAML: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _safe_id(text: str, fallback: str) -> str:
    out = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in (text or ""))
    while "__" in out:
        out = out.replace("__", "_")
    return out.strip("_") or fallback


def _impl_refs(module: dict[str, Any]) -> list[str]:
    refs = module.get("implements") or []
    if isinstance(refs, str):
        refs = [r.strip() for r in refs.replace(";", ",").split(",") if r.strip()]
    if isinstance(refs, dict):
        refs = list(refs.keys())
    if not isinstance(refs, list):
        refs = []
    return [str(r).strip() for r in refs if str(r).strip()]


def _ref_tokens(ref: str) -> list[str]:
    """Split a dotted ref into lowercase tokens, ignoring stub leaders like '.'."""
    return [t.strip().lower() for t in ref.replace("/", ".").split(".") if t.strip()]


def _name_tokens(name: str) -> list[str]:
    """Split an identifier into lowercase tokens by underscore."""
    return [t for t in name.lower().split("_") if t]


def _ref_matches_name(ref: str, name: str) -> bool:
    """Loose match: any non-trivial ref token appears in the name's tokens or vice versa."""
    if not name:
        return False
    name_l = name.lower()
    ref_tokens = _ref_tokens(ref)
    if not ref_tokens:
        return False
    if ref_tokens[-1] == name_l:
        return True
    name_l_tokens = _name_tokens(name)
    leaf = ref_tokens[-1]
    if leaf in name_l_tokens or any(leaf in nt or nt in leaf for nt in name_l_tokens):
        return True
    if name_l in leaf or leaf in name_l:
        return True
    return False


def _projected_transactions(refs: list[str], all_tx: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    refs_under_tx = [r for r in refs if "transactions" in _ref_tokens(r)]
    for tx in all_tx:
        if not isinstance(tx, dict):
            continue
        tid = str(tx.get("id") or "").strip()
        tname = str(tx.get("name") or "").strip()
        for ref in refs_under_tx:
            if (tid and _ref_matches_name(ref, tid)) or (tname and _ref_matches_name(ref, tname)):
                if tid:
                    out.append(tid)
                break
    return out


def _projected_state_vars(refs: list[str], all_state: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    refs_under_state = [r for r in refs if "state_variables" in _ref_tokens(r) or "state" in _ref_tokens(r)]
    for sv in all_state:
        if not isinstance(sv, dict):
            continue
        sname = str(sv.get("name") or "").strip()
        if not sname:
            continue
        for ref in refs_under_state:
            if _ref_matches_name(ref, sname):
                out.append(sname)
                break
    return out


_PROTOCOL_TOKENS = {
    "handshake_rules", "ordering", "arbitration", "backpressure",
    "pipeline", "latency", "fsm", "registers", "register_list",
}


def _projected_protocols(refs: list[str]) -> list[str]:
    out: list[str] = []
    for ref in refs:
        toks = set(_ref_tokens(ref))
        if toks & _PROTOCOL_TOKENS:
            out.append(ref)
    return out


def _stub_source(ip: str, submod: str, refs: list[str], tx_ids: list[str], state_vars: list[str]) -> str:
    return f'''#!/usr/bin/env python3
"""Sub-module FL stub for {submod} (ip={ip}).

This file is generated. It delegates to the top FunctionalModel and exposes
only the slice of behavior owned by sub-module {submod} as declared in
SSOT.sub_modules[*].implements. Use this as the per-module scoreboard
oracle for L2 (module-level) equivalence checks.

implements refs:
{json.dumps(refs, indent=2)}
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure parent FunctionalModel is importable when run standalone.
_HERE = Path(__file__).resolve().parent
_MODEL_DIR = _HERE.parent
if str(_MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(_MODEL_DIR))

try:
    from .functional_model import FunctionalModel as _FL
except ImportError:
    from functional_model import FunctionalModel as _FL


_OWNED_TX_IDS = {tx_ids!r}
_OWNED_STATE_VARS = {state_vars!r}


class SubmoduleFL:
    """Thin wrapper exposing only the slice owned by sub-module {submod}."""

    NAME = "{submod}"

    def __init__(self, params=None):
        self._fl = _FL(params)
        self._trace: list[dict] = []

    def reset(self):
        self._fl.reset()
        self._trace.clear()

    def apply(self, txn):
        kind = str((txn or {{}}).get("kind") or (txn or {{}}).get("transaction") or "").strip()
        if _OWNED_TX_IDS and kind not in _OWNED_TX_IDS:
            entry = {{"submodule": self.NAME, "kind": kind, "skipped": True, "reason": "not_owned"}}
            self._trace.append(entry)
            return {{"resp": getattr(_FL, "RESP_OKAY", 0), "submodule": self.NAME, "skipped": True}}
        result = self._fl.apply(txn)
        self._trace.append({{"submodule": self.NAME, "kind": kind, "result_resp": result.get("resp")}})
        return result

    def observe_state(self):
        if not _OWNED_STATE_VARS:
            return dict(self._fl.state)
        return {{k: self._fl.state.get(k) for k in _OWNED_STATE_VARS}}

    def trace(self):
        return list(self._trace)


def run_module_self_check():
    m = SubmoduleFL()
    m.reset()
    results = []
    for tid in (_OWNED_TX_IDS or []):
        results.append({{
            "tx": tid,
            "result": m.apply({{"kind": tid}}),
        }})
    return {{
        "submodule": SubmoduleFL.NAME,
        "owned_tx": list(_OWNED_TX_IDS),
        "owned_state": list(_OWNED_STATE_VARS),
        "results": results,
        "trace_entries": len(m.trace()),
    }}


if __name__ == "__main__":
    import json as _json
    print(_json.dumps(run_module_self_check(), indent=2))
'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ip")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    ip_dir = root / args.ip
    ssot = _load_ssot(ip_dir, args.ip)

    sub_modules = ssot.get("sub_modules") or []
    if not isinstance(sub_modules, list):
        sub_modules = []
    fm = ssot.get("function_model") if isinstance(ssot.get("function_model"), dict) else {}
    all_tx = fm.get("transactions") or []
    all_state = fm.get("state_variables") or []

    sub_dir = ip_dir / "model" / "sub"
    sub_dir.mkdir(parents=True, exist_ok=True)
    init_path = sub_dir / "__init__.py"
    if not init_path.exists():
        init_path.write_text("# Generated sub-module FL package\n", encoding="utf-8")

    emitted: list[dict[str, Any]] = []
    for module in sub_modules:
        if not isinstance(module, dict):
            continue
        name = str(module.get("name") or "").strip()
        if not name:
            continue
        ownership = str(module.get("ownership") or "manifest").lower()
        if ownership != "manifest":
            continue
        refs = _impl_refs(module)
        if not refs:
            continue
        tx_ids = _projected_transactions(refs, all_tx)
        state_vars = _projected_state_vars(refs, all_state)
        protocol_refs = _projected_protocols(refs)
        if not tx_ids and not state_vars and not protocol_refs:
            continue
        sub_id = _safe_id(name, "submod")
        out_path = sub_dir / f"{sub_id}_fl.py"
        out_path.write_text(_stub_source(args.ip, sub_id, refs, tx_ids, state_vars), encoding="utf-8")
        emitted.append({
            "submodule": sub_id,
            "file": str(out_path.relative_to(ip_dir)),
            "owned_tx": tx_ids,
            "owned_state": state_vars,
            "owned_protocol_refs": protocol_refs,
            "implements": refs,
        })

    summary = {
        "schema_version": 1,
        "type": "submodule_fl_summary",
        "ip": args.ip,
        "sub_modules_total": sum(1 for m in sub_modules if isinstance(m, dict)),
        "submodule_fl_emitted": len(emitted),
        "emitted": emitted,
    }
    (sub_dir / "submodule_fl.summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(f"[emit_submodule_fl] {args.ip} sub_modules_total={summary['sub_modules_total']} emitted={len(emitted)}")
    for ent in emitted:
        print(f"  + {ent['submodule']}  (tx={len(ent['owned_tx'])}, state={len(ent['owned_state'])})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
