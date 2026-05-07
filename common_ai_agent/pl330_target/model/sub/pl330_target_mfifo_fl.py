#!/usr/bin/env python3
"""Sub-module FL stub for pl330_target_mfifo (ip=pl330_target).

This file is generated. It delegates to the top FunctionalModel and exposes
only the slice of behavior owned by sub-module pl330_target_mfifo as declared in
SSOT.sub_modules[*].implements. Use this as the per-module scoreboard
oracle for L2 (module-level) equivalence checks.

implements refs:
[
  "function_model.state_variables.mfifo",
  "cycle_model.backpressure.mfifo_full"
]
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


_OWNED_TX_IDS = []
_OWNED_STATE_VARS = ['mfifo_count']


class SubmoduleFL:
    """Thin wrapper exposing only the slice owned by sub-module pl330_target_mfifo."""

    NAME = "pl330_target_mfifo"

    def __init__(self, params=None):
        self._fl = _FL(params)
        self._trace: list[dict] = []

    def reset(self):
        self._fl.reset()
        self._trace.clear()

    def apply(self, txn):
        kind = str((txn or {}).get("kind") or (txn or {}).get("transaction") or "").strip()
        if _OWNED_TX_IDS and kind not in _OWNED_TX_IDS:
            entry = {"submodule": self.NAME, "kind": kind, "skipped": True, "reason": "not_owned"}
            self._trace.append(entry)
            return {"resp": getattr(_FL, "RESP_OKAY", 0), "submodule": self.NAME, "skipped": True}
        result = self._fl.apply(txn)
        self._trace.append({"submodule": self.NAME, "kind": kind, "result_resp": result.get("resp")})
        return result

    def observe_state(self):
        if not _OWNED_STATE_VARS:
            return dict(self._fl.state)
        return {k: self._fl.state.get(k) for k in _OWNED_STATE_VARS}

    def trace(self):
        return list(self._trace)


def run_module_self_check():
    m = SubmoduleFL()
    m.reset()
    results = []
    for tid in (_OWNED_TX_IDS or []):
        results.append({
            "tx": tid,
            "result": m.apply({"kind": tid}),
        })
    return {
        "submodule": SubmoduleFL.NAME,
        "owned_tx": list(_OWNED_TX_IDS),
        "owned_state": list(_OWNED_STATE_VARS),
        "results": results,
        "trace_entries": len(m.trace()),
    }


if __name__ == "__main__":
    import json as _json
    print(_json.dumps(run_module_self_check(), indent=2))
