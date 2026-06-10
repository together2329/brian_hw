#!/usr/bin/env python3
"""pdk_env.py — Resolve bundled PDK paths, independent of cwd.

Python port of ``pdk_env.sh`` for native-Windows portability and so that the
sibling ``*.py`` ports (auto_syn.py, run_yosys.py, ...) can reuse the exact same
PDK-path resolution that the shell pipeline gets by ``source``-ing
``pdk_env.sh``.

Sourcing semantics replicated here
----------------------------------
``source pdk_env.sh`` mutates the *caller's* environment.  It:

1. Loads a whitelisted set of PDK keys from ``<repo>/.env`` — but only keys that
   are not already set in the environment (``[ -z "${!key:-}" ] || continue``).
2. Resolves each PDK variable, applying a default when unset and converting a
   relative value to an absolute path under the repo root.
3. Exports the resolved variables.

The shell ``SKY130_LIB`` default *globs* ``${PDK_LIB_PATH}/*.lib`` after two
preferred corners; this port reproduces the same ordering and glob expansion
(sorted, matching shell ``*`` lexical order) and picks the first *readable*
candidate.

Usage
-----
As a module::

    from pdk_env import resolve_pdk_env, apply_pdk_env
    env = resolve_pdk_env()            # dict of resolved PDK vars (no mutation)
    apply_pdk_env(os.environ)          # mutate os.environ in place (like source)

As a CLI (prints ``KEY=VALUE`` export lines, matching what a ``source`` would
leave in the environment)::

    python3 pdk_env.py            # KEY=value lines
    python3 pdk_env.py --export   # export KEY="value" lines (eval-able in sh)
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
from pathlib import Path

# Keys the shell whitelists when reading .env, in declaration order.
_DOTENV_KEYS = (
    "PDK_ROOT",
    "SKY130_PDK_ROOT",
    "PDK_LIB_PATH",
    "SKY130_LIB",
    "SKY130_TLEF",
    "SKY130_LEF",
    "SKY130_TRACKS",
    "SKY130_RCX_RULES",
)

# Keys exported by the shell, in the order it exports them.
_EXPORT_KEYS = (
    "PDK_ROOT",
    "SKY130_PDK_ROOT",
    "PDK_LIB_PATH",
    "SKY130_LIB",
    "SKY130_TLEF",
    "SKY130_LEF",
    "SKY130_TRACKS",
    "SKY130_RCX_RULES",
)


def repo_root() -> Path:
    """``$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)``.

    This file lives at ``<repo>/workflow/scripts/pdk_env.py``; the shell anchors
    on ``workflow/scripts/`` and climbs two levels to the repo root.
    """
    return Path(__file__).resolve().parent.parent.parent


def _abs(value: str, root: Path) -> str:
    """``_pdk_env_abs`` — leave absolute paths alone, root-relative otherwise."""
    if not value:
        return value
    if value.startswith("/"):
        return value
    return str(root / value)


def _strip_inline_comment(value: str) -> str:
    """Mirror the shell ``sed 's/[[:space:]]#.*$//'`` on dotenv values.

    Removes a trailing ``<whitespace>#...`` comment, then surrounding
    whitespace, then one layer of matching single or double quotes.
    """
    # Strip ``<space>#...`` to end-of-line (shell uses [[:space:]]#).
    out = []
    i = 0
    n = len(value)
    while i < n:
        ch = value[i]
        if ch == "#" and i > 0 and value[i - 1] in " \t":
            break
        out.append(ch)
        i += 1
    stripped = "".join(out).strip()
    # Remove one layer of matching quotes (shell strips a trailing then leading
    # quote of each kind; for a normally-quoted value this unwraps it).
    if stripped.endswith('"'):
        stripped = stripped[:-1]
    if stripped.startswith('"'):
        stripped = stripped[1:]
    if stripped.endswith("'"):
        stripped = stripped[:-1]
    if stripped.startswith("'"):
        stripped = stripped[1:]
    return stripped


def load_dotenv(env_file: Path, base_env: dict[str, str]) -> dict[str, str]:
    """``_pdk_env_load_dotenv`` — return whitelisted keys absent from base_env.

    Only keys in ``_DOTENV_KEYS`` that are *unset or empty* in ``base_env`` are
    returned (the shell's ``[ -z "${!key:-}" ] || continue``).  Lines may use a
    leading ``export `` and a trailing inline comment.
    """
    found: dict[str, str] = {}
    if not env_file.is_file():
        return found
    text = env_file.read_text(encoding="utf-8", errors="replace")
    # ``while IFS= read -r line || [ -n "$line" ]`` reads all lines incl. a final
    # unterminated one; ``splitlines`` covers both.
    for raw in text.splitlines():
        line = raw.lstrip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        if "=" not in line:
            # ``key=${line%%=*}`` / ``val=${line#*=}`` both equal the whole line
            # when no '='; key would not be a whitelisted PDK key, so skip.
            continue
        key = line.split("=", 1)[0].strip()
        val = line.split("=", 1)[1]
        if key not in _DOTENV_KEYS:
            continue
        if base_env.get(key):
            # Already set & non-empty in the environment — shell skips it.
            continue
        found[key] = _strip_inline_comment(val)
    return found


def resolve_pdk_env(
    base_env: dict[str, str] | None = None,
    root: Path | None = None,
) -> dict[str, str]:
    """Resolve all PDK vars exactly as ``source pdk_env.sh`` would.

    Returns only the keys the shell exports, with values resolved against
    ``base_env`` (defaults to ``os.environ``) and the repo root.  Does not
    mutate ``base_env``.
    """
    if base_env is None:
        base_env = dict(os.environ)
    if root is None:
        root = repo_root()

    # Step 1: overlay whitelisted .env keys that aren't already set.
    env = dict(base_env)
    for key, val in load_dotenv(root / ".env", base_env).items():
        env[key] = val

    def cur(key: str) -> str:
        return env.get(key, "") or ""

    # PDK_ROOT
    if not cur("PDK_ROOT"):
        env["PDK_ROOT"] = str(root / "pdk")
    elif not cur("PDK_ROOT").startswith("/"):
        env["PDK_ROOT"] = _abs(cur("PDK_ROOT"), root)

    # SKY130_PDK_ROOT
    if not cur("SKY130_PDK_ROOT"):
        env["SKY130_PDK_ROOT"] = str(Path(cur("PDK_ROOT")) / "sky130")
    elif not cur("SKY130_PDK_ROOT").startswith("/"):
        env["SKY130_PDK_ROOT"] = _abs(cur("SKY130_PDK_ROOT"), root)

    # PDK_LIB_PATH
    if not cur("PDK_LIB_PATH"):
        env["PDK_LIB_PATH"] = str(Path(cur("SKY130_PDK_ROOT")) / "lib")
    elif not cur("PDK_LIB_PATH").startswith("/"):
        env["PDK_LIB_PATH"] = _abs(cur("PDK_LIB_PATH"), root)

    # SKY130_LIB — default globs PDK_LIB_PATH for first readable .lib.
    if not cur("SKY130_LIB"):
        lib_path = cur("PDK_LIB_PATH")
        candidates = [
            str(Path(lib_path) / "sky130_fd_sc_hd__ss_100C_1v40.lib"),
            str(Path(lib_path) / "sky130_fd_sc_hd__ss_n40C_1v40.lib"),
        ]
        # ``"${PDK_LIB_PATH}"/*.lib`` — shell sorts glob results lexically.
        candidates.extend(sorted(glob.glob(str(Path(lib_path) / "*.lib"))))
        for cand in candidates:
            if os.access(cand, os.R_OK) and Path(cand).is_file():
                env["SKY130_LIB"] = cand
                break
        else:
            # No readable lib: the shell leaves SKY130_LIB unset; an unmatched
            # glob also stays literal, but no readable file means the loop never
            # assigns. Mirror "unset" with empty string.
            env.setdefault("SKY130_LIB", "")
    elif not cur("SKY130_LIB").startswith("/"):
        env["SKY130_LIB"] = _abs(cur("SKY130_LIB"), root)

    # SKY130_TLEF
    if not cur("SKY130_TLEF"):
        env["SKY130_TLEF"] = str(
            Path(cur("SKY130_PDK_ROOT")) / "lef" / "sky130_fd_sc_hd.tlef"
        )
    elif not cur("SKY130_TLEF").startswith("/"):
        env["SKY130_TLEF"] = _abs(cur("SKY130_TLEF"), root)

    # SKY130_LEF
    if not cur("SKY130_LEF"):
        env["SKY130_LEF"] = str(
            Path(cur("SKY130_PDK_ROOT")) / "lef" / "sky130_fd_sc_hd_merged.lef"
        )
    elif not cur("SKY130_LEF").startswith("/"):
        env["SKY130_LEF"] = _abs(cur("SKY130_LEF"), root)

    # SKY130_TRACKS
    if not cur("SKY130_TRACKS"):
        env["SKY130_TRACKS"] = str(Path(cur("SKY130_PDK_ROOT")) / "make_tracks.tcl")
    elif not cur("SKY130_TRACKS").startswith("/"):
        env["SKY130_TRACKS"] = _abs(cur("SKY130_TRACKS"), root)

    # SKY130_RCX_RULES
    if not cur("SKY130_RCX_RULES"):
        env["SKY130_RCX_RULES"] = str(
            Path(cur("SKY130_PDK_ROOT")) / "rcx_patterns.rules"
        )
    elif not cur("SKY130_RCX_RULES").startswith("/"):
        env["SKY130_RCX_RULES"] = _abs(cur("SKY130_RCX_RULES"), root)

    return {key: env.get(key, "") for key in _EXPORT_KEYS}


def apply_pdk_env(
    target_env: dict[str, str] | None = None,
    root: Path | None = None,
) -> dict[str, str]:
    """Mutate ``target_env`` (default ``os.environ``) like ``source pdk_env.sh``.

    Returns the resolved PDK dict.
    """
    if target_env is None:
        target_env = os.environ
    resolved = resolve_pdk_env(dict(target_env), root)
    for key, val in resolved.items():
        target_env[key] = val
    return resolved


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve bundled PDK paths.")
    parser.add_argument(
        "--export",
        action="store_true",
        help="emit eval-able 'export KEY=\"value\"' lines",
    )
    args = parser.parse_args(argv)

    resolved = resolve_pdk_env()
    for key in _EXPORT_KEYS:
        val = resolved.get(key, "")
        if args.export:
            print(f'export {key}="{val}"')
        else:
            print(f"{key}={val}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
