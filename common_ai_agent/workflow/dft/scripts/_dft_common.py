#!/usr/bin/env python3
"""_dft_common.py — shared helpers for the DFT script ports.

The bash DFT scripts have no sourced common library; each one independently does:

    PDK_ENV="$(cd "$(dirname "$0")/../.." && pwd -P)/scripts/pdk_env.sh"
    [ -f "${PDK_ENV}" ] && source "${PDK_ENV}"

i.e. each sources ``workflow/scripts/pdk_env.sh`` to populate the ``SKY130_*``
defaults.  ``load_pdk_env()`` here reproduces that resolution in Python (the same
dotenv + default logic pdk_env.sh implements) so the ``SKY130_LIB`` the DFT TCL
references resolves identically.  The remaining helpers are small shell-builtin
equivalents (`command -v`, `[ -r ]`) shared by the sibling ``*.py`` ports to
avoid drift; they are not a CLI.  (DFT wrappers take ``$1`` directly and have no
HOOK_CMD_ARGS handling, unlike the PnR wrappers.)
"""

from __future__ import annotations

import glob
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Mapping, MutableMapping, Optional


_PDK_ENV_DOTENV_KEYS = (
    "PDK_ROOT",
    "SKY130_PDK_ROOT",
    "PDK_LIB_PATH",
    "SKY130_LIB",
    "SKY130_TLEF",
    "SKY130_LEF",
    "SKY130_TRACKS",
    "SKY130_RCX_RULES",
)


def _pdk_env_root() -> Path:
    """common_ai_agent/ — two dirs above workflow/scripts/, == parents[3] here."""
    # This file: workflow/dft/scripts/_dft_common.py -> parents[3] == common_ai_agent/.
    return Path(__file__).resolve().parents[3]


def _pdk_env_abs(root: Path, value: str) -> str:
    if value.startswith("/"):
        return value
    return f"{root}/{value}"


def _strip_inline_comment(value: str) -> str:
    value = re.sub(r"\s#.*$", "", value)
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        value = value[1:-1]
    else:
        for quote in ('"', "'"):
            if value.endswith(quote):
                value = value[:-1]
            if value.startswith(quote):
                value = value[1:]
    return value


def _load_dotenv(env: MutableMapping[str, str], dotenv: Path) -> None:
    if not dotenv.is_file():
        return
    for raw in dotenv.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.lstrip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if key not in _PDK_ENV_DOTENV_KEYS:
            continue
        if env.get(key):
            continue
        env[key] = _strip_inline_comment(val)


def load_pdk_env(env: MutableMapping[str, str]) -> None:
    """Replicate ``source workflow/scripts/pdk_env.sh`` (fill SKY130_* defaults)."""
    root = _pdk_env_root()
    _load_dotenv(env, root / ".env")

    def resolve(key: str, default: str) -> None:
        cur = env.get(key)
        if not cur:
            env[key] = default
        elif not cur.startswith("/"):
            env[key] = _pdk_env_abs(root, cur)

    resolve("PDK_ROOT", f"{root}/pdk")
    resolve("SKY130_PDK_ROOT", f"{env['PDK_ROOT']}/sky130")
    resolve("PDK_LIB_PATH", f"{env['SKY130_PDK_ROOT']}/lib")

    cur_lib = env.get("SKY130_LIB")
    if not cur_lib:
        lib_path = env["PDK_LIB_PATH"]
        candidates = [
            f"{lib_path}/sky130_fd_sc_hd__ss_100C_1v40.lib",
            f"{lib_path}/sky130_fd_sc_hd__ss_n40C_1v40.lib",
        ]
        candidates += sorted(glob.glob(f"{lib_path}/*.lib"))
        for cand in candidates:
            if os.access(cand, os.R_OK):
                env["SKY130_LIB"] = cand
                break
    elif not cur_lib.startswith("/"):
        env["SKY130_LIB"] = _pdk_env_abs(root, cur_lib)

    resolve("SKY130_TLEF", f"{env['SKY130_PDK_ROOT']}/lef/sky130_fd_sc_hd.tlef")
    resolve("SKY130_LEF", f"{env['SKY130_PDK_ROOT']}/lef/sky130_fd_sc_hd_merged.lef")
    resolve("SKY130_TRACKS", f"{env['SKY130_PDK_ROOT']}/make_tracks.tcl")
    resolve("SKY130_RCX_RULES", f"{env['SKY130_PDK_ROOT']}/rcx_patterns.rules")


def run_embedded_py(script: str, args: "list[str]",
                    capture: bool = False) -> "subprocess.CompletedProcess":
    """Run an embedded python snippet exactly like the bash `python3 - "$@" <<'PY'`.

    Feeding the body on stdin (``python3 -``) makes the interpreter report
    ``File "<stdin>"`` in tracebacks, matching the bash heredoc form.  The leading
    newline is stripped so traceback line numbers line up with the bash heredoc.
    """
    return subprocess.run(
        [sys.executable, "-", *args],
        input=script.lstrip("\n"),
        capture_output=capture,
        text=True,
    )


def which(name: str, env: Optional[Mapping[str, str]] = None) -> Optional[str]:
    """`command -v <name>` for an executable on PATH (env-aware)."""
    if env is None:
        env = os.environ
    path = env.get("PATH", os.defpath)
    for directory in path.split(os.pathsep):
        if not directory:
            continue
        candidate = os.path.join(directory, name)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


def readable(path: str) -> bool:
    """`[ -r <path> ]`: non-empty path that exists and is readable."""
    return bool(path) and os.access(path, os.R_OK)
