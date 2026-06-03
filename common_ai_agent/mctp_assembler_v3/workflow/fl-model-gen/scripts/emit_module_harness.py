#!/usr/bin/env python3
"""Emit per-sub_module cocotb-style harnesses for L2 module-level loop.

For each <ip>/model/sub/<submod>_fl.py emitted by emit_submodule_fl.py,
write <ip>/verify/sub/<submod>_harness.py — a thin script that loads the
sub-module FL, runs the owned transactions, and prints a JSON summary
suitable for ingestion into a module-level scoreboard.

Usage:
  python3 workflow/fl-model-gen/scripts/emit_module_harness.py <ip> --root .
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _harness_source(ip: str, submod: str) -> str:
    return f'''#!/usr/bin/env python3
"""Module-level L2 harness for {submod} (ip={ip}).

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
    from {submod}_fl import SubmoduleFL, run_module_self_check
    self_check = run_module_self_check()
    sb_rows = []
    fl = SubmoduleFL()
    fl.reset()
    for tid in self_check["owned_tx"]:
        result = fl.apply({{"kind": tid, "scenario_id": f"L2_{{tid}}"}})
        sb_rows.append({{
            "submodule": SubmoduleFL.NAME,
            "tx": tid,
            "expected_resp": result.get("resp"),
            "expected_state": fl.observe_state(),
        }})
    summary = {{
        "submodule": SubmoduleFL.NAME,
        "harness_kind": "L2_module",
        "self_check": self_check,
        "scoreboard_rows": sb_rows,
    }}
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ip")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    ip_dir = root / args.ip
    sub_summary = ip_dir / "model" / "sub" / "submodule_fl.summary.json"
    if not sub_summary.is_file():
        raise SystemExit(f"missing submodule summary — run emit_submodule_fl.py first: {sub_summary}")

    summary = json.loads(sub_summary.read_text(encoding="utf-8"))
    emitted = summary.get("emitted") or []

    out_dir = ip_dir / "verify" / "sub"
    out_dir.mkdir(parents=True, exist_ok=True)

    written: list[str] = []
    for ent in emitted:
        submod = ent["submodule"]
        out_path = out_dir / f"{submod}_harness.py"
        out_path.write_text(_harness_source(args.ip, submod), encoding="utf-8")
        written.append(str(out_path.relative_to(ip_dir)))

    h_summary = {
        "schema_version": 1,
        "type": "module_harness_summary",
        "ip": args.ip,
        "harness_files": written,
        "harnesses_total": len(written),
    }
    (out_dir / "module_harness.summary.json").write_text(json.dumps(h_summary, indent=2) + "\n", encoding="utf-8")
    print(f"[emit_module_harness] {args.ip} wrote {len(written)} harness files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
