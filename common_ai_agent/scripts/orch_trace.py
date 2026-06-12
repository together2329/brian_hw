#!/usr/bin/env python3
"""Replay one orchestrator run as a step-by-step decision trace.

Usage:
  python3 scripts/orch_trace.py <run_id>
  python3 scripts/orch_trace.py <run_id> --root /path/to/project/root
  python3 scripts/orch_trace.py <run_id> --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.orchestrator.trace import DEFAULT_DB, build_trace, format_trace  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("run_id")
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--root", help="project root containing .session/orchestrators-ipc/<run_id>")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--wake", type=int, default=5, help="wake.jsonl tail lines when --root is provided")
    ap.add_argument("--json", action="store_true", help="emit machine-readable trace")
    ns = ap.parse_args()

    db_path = Path(ns.db).expanduser()
    if not db_path.is_file():
        print(f"error: DB not found: {db_path}", file=sys.stderr)
        return 2
    root = Path(ns.root).resolve() if ns.root else None
    trace = build_trace(
        ns.run_id,
        db_path=db_path,
        project_root=root,
        limit=ns.limit,
        wake_limit=ns.wake,
    )
    if not trace.get("run") and not trace.get("steps"):
        print(f"error: run not found: {ns.run_id}", file=sys.stderr)
        return 1
    if ns.json:
        print(json.dumps(trace, indent=2, sort_keys=True))
    else:
        print(format_trace(trace), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
