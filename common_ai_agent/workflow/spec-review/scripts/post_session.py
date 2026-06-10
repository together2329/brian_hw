#!/usr/bin/env python3
"""post_session.py — Python port of post_session.sh (spec-review).

Save a spec-review session summary on session end.  The summary directory is
``$BENCHMARK_LOG/sessions`` (note: BENCHMARK_LOG is treated as a *directory*
here, matching the bash original) and the file name is
``session_<YYYYmmdd_HHMMSS>.txt``.

The ``Date`` line uses the local ``date`` default format (``%a %b %e %H:%M:%S
%Z %Y``) to match ``$(date)``.
"""

from __future__ import annotations

import os
import time
from pathlib import Path


def main() -> int:
    # RESULTS_DIR="${BENCHMARK_LOG}/sessions"
    benchmark_log = os.environ.get("BENCHMARK_LOG", "")
    results_dir = Path(f"{benchmark_log}/sessions")
    results_dir.mkdir(parents=True, exist_ok=True)

    stamp = time.strftime("%Y%m%d_%H%M%S")
    summary_file = results_dir / f"session_{stamp}.txt"

    workspace = os.environ.get("HOOK_WORKSPACE", "")
    todo_index = os.environ.get("HOOK_TODO_INDEX", "")
    todo_content = os.environ.get("HOOK_TODO_CONTENT", "")
    # $(date) default format, e.g. "Tue Jun 10 12:34:56 KST 2026".
    date_str = time.strftime("%a %b %e %H:%M:%S %Z %Y")

    lines = [
        "=== Spec Review Session ===",
        f"Workspace : {workspace}",
        f"Date      : {date_str}",
        f"Todo      : {todo_index} — {todo_content}",
        "",
    ]
    summary_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Session log saved to: {summary_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
