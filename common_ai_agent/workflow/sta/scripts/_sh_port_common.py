#!/usr/bin/env python3
"""_sh_port_common.py — Shared helpers for the STA/STA-post .sh→.py ports.

These two helpers each replace a bash idiom repeated verbatim across the owned
scripts:

* ``load_pdk_env`` reproduces ``source ../../scripts/pdk_env.sh`` — it runs the
  canonical bash resolver in a subshell and imports the exported PDK vars into
  ``os.environ`` exactly as the bash ``source`` would. Reusing the real shell
  script (rather than re-porting 100 lines of path logic) guarantees identical
  SKY130_LIB resolution and keeps the .sh as the single source of truth.

* ``resolve_top`` reproduces the inlined ``TOP=$(python3 - ... <<PY)`` heredoc
  that write_sta_tcl.sh and write_sta_post_tcl.sh share byte-for-byte.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

# pdk_env.sh lives at common_ai_agent/workflow/scripts/pdk_env.sh. Each owning
# script sits at workflow/<stage>/scripts/<name>.sh and resolves it as
# "$(cd "$(dirname "$0")/../.." && pwd -P)/scripts/pdk_env.sh", i.e.
# workflow/scripts/pdk_env.sh.
_PDK_ENV = Path(__file__).resolve().parent.parent.parent / "scripts" / "pdk_env.sh"

# Vars exported by pdk_env.sh (see its trailing ``export`` lines).
_PDK_VARS = (
    "PDK_ROOT",
    "SKY130_PDK_ROOT",
    "PDK_LIB_PATH",
    "SKY130_LIB",
    "SKY130_TLEF",
    "SKY130_LEF",
    "SKY130_TRACKS",
    "SKY130_RCX_RULES",
)


def load_pdk_env() -> dict[str, str]:
    """Source pdk_env.sh and import its exported vars into os.environ.

    Bash form: ``[ -f "$PDK_ENV" ] && source "$PDK_ENV"``. Returns the resolved
    var map for convenience. If the script is missing this is a no-op, matching
    the guarded ``[ -f ]`` source in every owning .sh.
    """
    resolved: dict[str, str] = {}
    if not _PDK_ENV.is_file():
        return resolved

    # Run the real resolver, then print each exported var NUL-delimited so values
    # containing spaces/newlines survive. ``source`` keeps already-set vars
    # (pdk_env.sh only sets when empty), so the current environment is inherited.
    printf_chain = " ".join(
        f'printf "{name}=%s\\0" "${{{name}:-}}";' for name in _PDK_VARS
    )
    script = f'source "{_PDK_ENV}"; {printf_chain}'
    try:
        out = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            check=False,
        ).stdout
    except OSError:
        return resolved

    for field in out.split(b"\0"):
        if not field:
            continue
        try:
            text = field.decode("utf-8", errors="replace")
        except Exception:
            continue
        key, _, val = text.partition("=")
        if key in _PDK_VARS:
            resolved[key] = val
            # Mirror ``source`` semantics: pdk_env.sh only fills empty vars, so an
            # explicit pre-existing export must win. Only set when currently unset
            # or empty.
            if not os.environ.get(key):
                if val:
                    os.environ[key] = val
    return resolved


def resolve_top(ip: str, ssot_path: str) -> str:
    """Replicate the shared ``TOP=$(python3 - <<PY ...)`` heredoc.

    Reads top_module/top from the SSOT yaml (dict or string), else the IP's
    basename. Trailing/leading whitespace stripped, exactly as the bash form's
    ``print(str(...).strip())``.
    """
    try:
        import yaml  # type: ignore

        doc = yaml.safe_load(
            Path(ssot_path).read_text(encoding="utf-8", errors="replace")
        ) or {}
    except Exception:
        doc = {}

    top = doc.get("top_module") or doc.get("top") if isinstance(doc, dict) else None
    if isinstance(top, dict):
        top = top.get("name") or top.get("module")
    return str(top or Path(ip).name).strip()
