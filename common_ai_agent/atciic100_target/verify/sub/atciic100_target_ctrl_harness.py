#!/usr/bin/env python3
"""Module-level L2 harness for atciic100_target_ctrl (ip=atciic100_target).

Loads the sub-module FL, runs each owned transaction, and prints a JSON
summary. Designed to be invoked from cocotb (replace the print with a
scoreboard hook) or from a regression script.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


_HERE = Path(__file__).resolve().parent
_IP_ROOT = _HERE.parent.parent
_MODEL_SUB = _IP_ROOT / "model" / "sub"
sys.path.insert(0, str(_MODEL_SUB))


def main():
    from atciic100_target_ctrl_fl import SubmoduleFL, run_module_self_check
    self_check = run_module_self_check()
    sb_rows = []
    fl = SubmoduleFL()
    fl.reset()
    for tid in self_check["owned_tx"]:
        result = fl.apply({"kind": tid, "scenario_id": f"L2_{tid}"})
        sb_rows.append({
            "submodule": SubmoduleFL.NAME,
            "tx": tid,
            "expected_resp": result.get("resp"),
            "expected_state": fl.observe_state(),
        })
    summary = {
        "submodule": SubmoduleFL.NAME,
        "harness_kind": "L2_module",
        "self_check": self_check,
        "scoreboard_rows": sb_rows,
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
