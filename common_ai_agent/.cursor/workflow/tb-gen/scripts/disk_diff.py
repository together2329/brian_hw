#!/usr/bin/env python3
"""disk_diff.py — Python port of disk_diff.sh (rtl-gen / ssot-gen / tb-gen).

Inject a ground-truth disk diff into the agent's context after every write/run
tool call.  A snapshot of ``path size mtime`` for tracked-extension files is
stored under ``$TMPDIR`` and diffed against the previous snapshot.  The hook is
non-blocking (always exit 0).

Faithful port notes (bash-isms preserved):
  * Snapshot file: ``$TMPDIR/atlas_disk_snap_${ACTIVE_WORKSPACE:-default}.txt``
    (``$TMPDIR`` defaults to ``/tmp``).
  * The snapshot-building ``find ... | grep -E | head -2000 | xargs stat | sort``
    pipeline and the ``diff <(...) | grep -E '^[<>]'`` comparison are shelled
    out verbatim so the ``./`` find prefix, macOS ``stat -f "%N %z %m"`` format,
    traversal order, head cap and diff line ordering all match the ``.sh`` on
    whatever host runs it.  ``$WATCH`` is unquoted to keep the bash
    word-splitting of ``$WATCH_ROOTS``.
  * Output: the added/removed counts and an 8-line preview, then update the
    snapshot.  Always exit 0 (non-blocking hook).
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


# grep -E pattern over tracked file extensions (kept identical to the .sh).
_EXT_PATTERN = (
    r"\.(sv|v|vh|svh|yaml|yml|md|f|txt|log|json|sdc|upf|tcl|out|netlist|vcd)$"
)


def _collect(watch: str) -> str:
    """Build the sorted ``path size mtime`` snapshot, byte-identical to the .sh.

    Shelled out to the exact original pipeline so the ``./`` find prefix, the
    macOS ``stat -f "%N %z %m"`` format, the find traversal order and the
    ``head -2000`` cap all match the ``.sh`` on whatever host runs it.  ``$WATCH``
    is left unquoted on purpose to reproduce the bash word-splitting of
    ``$WATCH_ROOTS``.
    """
    cmd = (
        "find $WATCH "
        "-type f "
        r"""\( -path '*/.*' -o -path '*/node_modules/*' -o -path '*/__pycache__/*' \) -prune -o """
        "-type f -print 2>/dev/null "
        f"""| grep -E '{_EXT_PATTERN}' """
        "| head -2000 "
        '| xargs -I{} stat -f "%N %z %m" {} 2>/dev/null '
        "| sort"
    )
    proc = subprocess.run(
        ["/bin/sh", "-c", cmd],
        capture_output=True,
        text=True,
        env={**os.environ, "WATCH": watch},
    )
    return proc.stdout


def _diff_markers(prev_text: str, current_text: str) -> "list[str]":
    """Replicate ``diff <(echo "$PREV") <(echo "$CURRENT") | grep -E '^[<>]'``.

    Shelled out to the system ``diff`` so the normal-format ``<`` / ``>`` line
    ordering matches the ``.sh`` exactly (echo re-adds a trailing newline to the
    command-substitution-stripped values, hence the explicit ``+ "\\n"``).
    """
    # Process substitution requires bash (not POSIX sh); invoke bash directly.
    proc = subprocess.run(
        ["/bin/bash", "-c",
         'diff <(printf "%s\\n" "$PREV") <(printf "%s\\n" "$CUR") | grep -E "^[<>]"'],
        capture_output=True,
        text=True,
        env={**os.environ, "PREV": prev_text, "CUR": current_text},
    )
    return [line for line in proc.stdout.split("\n") if line]


def main() -> int:
    tmpdir = os.environ.get("TMPDIR", "/tmp")
    workspace = os.environ.get("ACTIVE_WORKSPACE", "default")
    snapshot = Path(tmpdir) / f"atlas_disk_snap_{workspace}.txt"

    watch = os.environ.get("ATLAS_DISK_WATCH", "./")

    # CURRENT=$(...) — command substitution strips trailing newlines.
    current = _collect(watch).rstrip("\n")

    if not snapshot.exists():
        # printf '%s\n' "$CURRENT" > "$SNAPSHOT"
        snapshot.write_text(current + "\n", encoding="utf-8")
        return 0

    # PREV=$(cat "$SNAPSHOT") — also strips trailing newlines.
    prev = snapshot.read_text(encoding="utf-8").rstrip("\n")

    diff = _diff_markers(prev, current)

    if not diff:
        print("[disk_diff] No tracked files changed since last tool call.")
    else:
        added = sum(1 for line in diff if line.startswith(">"))
        removed = sum(1 for line in diff if line.startswith("<"))
        print(
            f"[disk_diff] {added} file-states added/changed, "
            f"{removed} removed since last tool call:"
        )
        # echo "$DIFF" | head -8 | sed 's/^/  /'
        for line in diff[:8]:
            print(f"  {line}")
        if added > 8 or removed > 8:
            print("  … (output truncated)")

    snapshot.write_text(current + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
