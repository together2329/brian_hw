#!/usr/bin/env python3
"""check_pyuvm_structure.py — verify cocotb backend is layered UVM-style TB.

Python port of check_pyuvm_structure.sh (an ENFORCED engine gate, label
``check_pyuvm_structure``).  This validator intentionally rejects partial
support-file drops and flat cocotb tests for SSOT TB work.  The default
/ssot-tb backend is pyuvm/cocotb, so the agent must produce executable
orchestration plus the UVM-style layers.

Hardening preserved 1:1 from the .sh:
  * The 8 structural keyword patterns are checked on COMMENT-STRIPPED source
    text (trailing ``# ...`` removed per line) so comment-only mentions do not
    satisfy the structural checks.
  * The pyuvm import / fallback-reason check stays on UNSTRIPPED text, because a
    documented "pyuvm unavailable" fallback reason legitimately lives in a
    comment.
  * Delegates to check_tb_python_compile.py (always) and
    check_scoreboard_events.py --source-check (only when
    verify/equivalence_goals.json exists).

grep semantics: each ``grep -Eiq`` over piped text succeeds if ANY line matches,
so the require_pattern checks here are evaluated per line, case-insensitively.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent

# POSIX [[:space:]] -> explicit whitespace class (no unicode surprises).
_WS = r"[ \t\n\r\f\v]"


def _eprint(msg: str) -> None:
    print(msg)


def _locate_ip() -> str:
    ip = os.environ.get("IP_NAME") or (sys.argv[1] if len(sys.argv) > 1 else "")
    if not ip:
        # Mirror: find . -maxdepth 3 -name '*.ssot.yaml' | sort -t/ -k2 | head -1
        #          | awk -F/ '{print $(NF-2)}'
        candidates = []
        for path in Path(".").glob("*/*/*.ssot.yaml"):
            candidates.append(str(path))
        for path in Path(".").glob("*/*.ssot.yaml"):
            candidates.append(str(path))
        for path in Path(".").glob("*.ssot.yaml"):
            candidates.append(str(path))
        # sort -t/ -k2: sort by the 2nd slash-separated field.
        def _key(p: str) -> str:
            parts = p.split("/")
            return parts[1] if len(parts) > 1 else ""

        candidates = sorted(set(candidates), key=_key)
        if candidates:
            parts = candidates[0].split("/")
            if len(parts) >= 3:
                ip = parts[-3]
    return ip


def _strip_comments(text: str) -> str:
    """Replicate sed 's/[[:space:]]*#.*$//' applied per line."""
    out_lines = []
    pat = re.compile(r"[ \t\n\r\f\v]*#.*$")
    for line in text.split("\n"):
        out_lines.append(pat.sub("", line))
    return "\n".join(out_lines)


# Inner POSIX class token -> raw char set (no surrounding brackets) so it can
# appear either standalone ([[:space:]] -> [<ws>]) or combined ([[:space:]_]).
_WS_CHARS = r" \t\n\r\f\v"


def _posix_to_py(pattern: str) -> str:
    """Translate POSIX bracket classes used by the .sh into Python regex.

    Only the [:space:] class appears in this gate's patterns, used both
    standalone ([[:space:]]) and combined with another char ([[:space:]_]).
    Translating at match time (rather than authoring time) lets the FAIL message
    echo the original .sh pattern text verbatim for output parity.
    """
    return pattern.replace("[:space:]", _WS_CHARS)


def _any_line_matches(text: str, pattern: str, ignorecase: bool) -> bool:
    flags = re.IGNORECASE if ignorecase else 0
    rx = re.compile(_posix_to_py(pattern), flags)
    for line in text.split("\n"):
        if rx.search(line):
            return True
    return False


def main() -> int:
    ip = _locate_ip()
    if not ip or not Path(ip).is_dir():
        _eprint("[check_pyuvm_structure] FAIL: cannot locate IP directory")
        return 1

    tb_dir = Path(ip) / "tb" / "cocotb"
    test = tb_dir / f"test_{ip}.py"
    runner = tb_dir / "test_runner.py"

    fail = 0
    for path in (test, runner):
        # [ ! -s "$path" ] : missing OR empty.
        if not (path.is_file() and path.stat().st_size > 0):
            _eprint(f"[check_pyuvm_structure] FAIL: missing or empty {path}")
            fail = 1

    if not tb_dir.is_dir():
        _eprint(f"[check_pyuvm_structure] FAIL: missing {tb_dir}")
        return 1

    # ALL_TEXT = concatenation of every top-level *.py file in TB_DIR.
    py_files = sorted(
        p for p in tb_dir.iterdir() if p.is_file() and p.name.endswith(".py")
    )
    parts = []
    for p in py_files:
        try:
            parts.append(p.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    # xargs -0 cat concatenates file contents back-to-back.
    all_text = "".join(parts)
    code_text = _strip_comments(all_text)

    # Patterns are the EXACT strings from the .sh require_pattern calls so the
    # FAIL message echoes them verbatim; _posix_to_py handles [[:space:]].
    checks = [
        ("transaction / sequence item", r"transaction|sequence[[:space:]_]*item|uvm_sequence_item"),
        ("sequence", r"class[[:space:]].*sequence|uvm_sequence|start_item|finish_item"),
        ("driver", r"class[[:space:]].*driver|uvm_driver|drive_"),
        ("monitor", r"class[[:space:]].*monitor|uvm_monitor|monitor_"),
        ("scoreboard", r"scoreboard|uvm_scoreboard|expected.*got|got.*expected"),
        ("coverage collector", r"coverage|coverpoint|functional_bins|coverage_bins"),
        ("environment", r"uvm_env|class[[:space:]].*env"),
        ("assertion failure path", r"raise[[:space:]]+AssertionError|assert[[:space:]][^=]"),
    ]
    for label, pattern in checks:
        if not _any_line_matches(code_text, pattern, ignorecase=True):
            _eprint(f"[check_pyuvm_structure] FAIL: missing {label} ({pattern})")
            fail = 1

    # pyuvm import / fallback check on UNSTRIPPED text.
    pyuvm_available = (
        subprocess.run(
            [sys.executable, "-c", "import pyuvm"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0
    )
    if pyuvm_available:
        usage_pat = r"(^|[ \t\n\r\f\v])(import pyuvm|from pyuvm import|uvm_test|uvm_env|uvm_component)"
        if not _any_line_matches(all_text, usage_pat, ignorecase=False):
            _eprint(
                "[check_pyuvm_structure] FAIL: pyuvm imports in this environment, "
                "but TB has no pyuvm component usage"
            )
            fail = 1
    else:
        fallback_pat = r"pyuvm.*unavailable|cocotb-native.*fallback|fallback.*pyuvm"
        if not _any_line_matches(all_text, fallback_pat, ignorecase=True):
            _eprint(
                "[check_pyuvm_structure] FAIL: pyuvm unavailable fallback reason "
                "is not documented in TB files"
            )
            fail = 1

    # Delegate: check_tb_python_compile.py "$IP" --root .
    compile_script = SCRIPT_DIR / "check_tb_python_compile.py"
    compile_proc = subprocess.run(
        [sys.executable, str(compile_script), ip, "--root", "."],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if compile_proc.returncode != 0:
        sys.stdout.write(compile_proc.stdout or "")
        _eprint("[check_pyuvm_structure] FAIL: Python syntax check failed")
        return 1

    # Delegate: check_scoreboard_events.py --source-check (only if goals exist).
    if (Path(ip) / "verify" / "equivalence_goals.json").is_file():
        sb_script = SCRIPT_DIR / "check_scoreboard_events.py"
        sb_proc = subprocess.run(
            [sys.executable, str(sb_script), ip, "--root", ".", "--source-check"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        # Both branches in the .sh print the captured output.
        sys.stdout.write(sb_proc.stdout or "")
        if sb_proc.returncode != 0:
            fail = 1

    if fail != 0:
        _eprint(
            "[check_pyuvm_structure] Disk reality is not a complete UVM-style "
            "cocotb environment."
        )
        return 1

    _eprint(
        f"[check_pyuvm_structure] PASS: layered pyuvm/cocotb structure exists for {ip}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
