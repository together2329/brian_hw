#!/usr/bin/env python3
"""run_full_lint.py — Verilator -Wall lint with project-specific waiver file.

Python port of run_full_lint.sh.

Usage:
  run_full_lint.py <ip> [--root .]

Pipeline:
  1. Locate <ip>/rtl/<ip>_lint.vlt waiver file.
  2. Run verilator --lint-only -Wall on full filelist.
  3. Exit non-zero if any warning slips through (Stable gate G_LINT_CLEAN).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _logical_pwd(root: str) -> str:
    """Replicate ``cd "$ROOT" && pwd`` (logical, symlink-preserving).

    ``pwd`` without ``-P`` prints ``$PWD``; the shell keeps $PWD as the logical
    path taken to reach the dir, so on macOS ``cd /tmp && pwd`` is ``/tmp`` not
    ``/private/tmp``. For an absolute root, normalize it directly. For a relative
    root, anchor on the shell's $PWD (logical cwd) and collapse '.'/'..' without
    touching symlinks, mirroring how the shell would print it after cd.
    """
    if os.path.isabs(root):
        return os.path.normpath(root)

    # bash trusts $PWD only when it is a valid alias of the real cwd; if $PWD is
    # stale (e.g. process spawned with a different cwd than the inherited $PWD),
    # ``cd . && pwd`` recomputes the physical path. Mirror that validation.
    pwd = os.environ.get("PWD", "")
    cwd = os.getcwd()
    if pwd and os.path.isabs(pwd):
        try:
            if os.path.realpath(pwd) == os.path.realpath(cwd):
                cwd = pwd  # logical alias is valid → keep it (preserves symlinks)
        except OSError:
            pass
    base = cwd if root in ("", ".") else os.path.join(cwd, root)
    return os.path.normpath(base)


def _resolve_top(ip_dir: str, ip: str) -> str:
    """Reproduce the inlined ``TOP=$(python3 - <<PY ... PY)`` heredoc.

    Prefer a wiring_only sub_module's file basename; else top_module.name; else
    the IP slug. The bash captures stderr to /dev/null (``2>/dev/null``) and the
    heredoc swallows yaml errors via bare exceptions, so a parse failure yields
    an empty TOP — which the caller then defaults to ``${IP}_wrapper``.
    """
    try:
        import yaml  # type: ignore

        d = yaml.safe_load(open(f"{ip_dir}/yaml/{ip}.ssot.yaml")) or {}
    except Exception:
        return ""

    try:
        for sm in d.get("sub_modules") or []:
            if isinstance(sm, dict) and sm.get("wiring_only"):
                nm = (sm.get("file") or "").split("/")[-1].replace(".sv", "").replace(
                    ".v", ""
                )
                if nm:
                    return nm
        return (d.get("top_module") or {}).get("name") or ip
    except Exception:
        return ""


def main(argv: list[str]) -> int:
    ip = ""
    root = "."
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--root":
            if i + 1 >= len(argv):
                # bash ``shift 2`` on a missing operand would error; emulate the
                # most common path where a value is present. Treat absence as
                # empty root to stay deterministic.
                root = ""
                i += 2
                continue
            root = argv[i + 1]
            i += 2
        elif a.startswith("-"):
            print(f"[run_full_lint] unknown flag: {a}", file=sys.stderr)
            return 2
        else:
            ip = a
            i += 1

    if not ip:
        print("usage: run_full_lint.py <ip> [--root .]", file=sys.stderr)
        return 2

    # bash: ROOT="$(cd "$ROOT" && pwd)" — a *logical* pwd that preserves symlinks
    # (e.g. keeps /tmp instead of /private/tmp on macOS). Build it from $PWD (the
    # shell's logical cwd) rather than os.getcwd()/realpath, which would resolve
    # symlinks and diverge from the .sh.
    root = _logical_pwd(root)
    ip_dir = f"{root}/{ip}"

    waiver = f"{ip_dir}/rtl/{ip}_lint.vlt"
    if not Path(waiver).is_file():
        print(f"[run_full_lint] missing waiver: {waiver}", file=sys.stderr)
        print("  See spi/rtl/spi_lint.vlt for template.", file=sys.stderr)
        return 1

    # Filelist or glob.
    sources: list[str] = []
    filelist = f"{ip_dir}/list/{ip}.f"
    if Path(filelist).is_file():
        for line in Path(filelist).read_text(encoding="utf-8", errors="replace").splitlines():
            # [[ -z "$line" || "$line" =~ ^# ]] && continue
            if not line or line.startswith("#"):
                continue
            sources.append(f"{ip_dir}/{line}")
    else:
        # ls "$IP_DIR"/rtl/*.sv "$IP_DIR"/rtl/*.v 2>/dev/null
        import glob as _glob

        listed = sorted(_glob.glob(f"{ip_dir}/rtl/*.sv")) + sorted(
            _glob.glob(f"{ip_dir}/rtl/*.v")
        )
        sources.extend(listed)

    top = _resolve_top(ip_dir, ip)
    if not top:
        top = f"{ip}_wrapper"

    lint_dir = f"{ip_dir}/lint"
    Path(lint_dir).mkdir(parents=True, exist_ok=True)
    log = f"{lint_dir}/verilator_lint.log"

    print(f"[run_full_lint] top: {top}")
    print(f"[run_full_lint] waiver: {waiver}")
    print(f"[run_full_lint] sources: {len(sources)}")
    sys.stdout.flush()

    cmd = [
        "verilator",
        "--lint-only",
        "-Wall",
        f"-I{ip_dir}/rtl",
        "--top-module",
        top,
        waiver,
        *sources,
    ]
    # verilator ... 2>&1 | tee "$LOG"  ; success branch on verilator's rc.
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    captured = proc.stdout or b""
    Path(log).write_bytes(captured)
    sys.stdout.flush()
    sys.stdout.buffer.write(captured)
    sys.stdout.buffer.flush()

    if proc.returncode == 0:
        print("")
        print("[run_full_lint] G_LINT_CLEAN: PASS")
        return 0

    log_text = Path(log).read_text(encoding="utf-8", errors="replace")
    nwarn = sum(
        1
        for ln in log_text.splitlines()
        if ln.startswith("%Warning") or ln.startswith("%Error")
    )
    print("")
    print(f"[run_full_lint] G_LINT_CLEAN: FAIL — {nwarn} warning(s)/error(s)")
    print(f"[run_full_lint] log: {log}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
