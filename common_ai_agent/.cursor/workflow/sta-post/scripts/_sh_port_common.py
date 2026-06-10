#!/usr/bin/env python3
"""_sh_port_common.py — Shared helpers for the STA/STA-post .sh→.py ports.

These two helpers each replace a bash idiom repeated verbatim across the owned
scripts:

* ``load_pdk_env`` reproduces ``source ../../scripts/pdk_env.sh`` by delegating
  to the Python port ``workflow/scripts/pdk_env.py`` (``apply_pdk_env``), which
  implements the same dotenv + default resolution. This keeps the PDK-path logic
  in one place and removes the bash dependency.

* ``resolve_top`` reproduces the inlined ``TOP=$(python3 - ... <<PY)`` heredoc
  that write_sta_tcl.sh and write_sta_post_tcl.sh share byte-for-byte.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

# pdk_env.py lives at common_ai_agent/workflow/scripts/pdk_env.py. Each owning
# script sits at workflow/<stage>/scripts/<name>.py and resolves it relative to
# workflow/scripts/.
_PDK_ENV_PY = Path(__file__).resolve().parent.parent.parent / "scripts" / "pdk_env.py"

# Vars exported by pdk_env.py (its ``_EXPORT_KEYS``).
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


def _load_pdk_env_module():
    """Import workflow/scripts/pdk_env.py by file path (no package install)."""
    spec = importlib.util.spec_from_file_location("_pdk_env_port", _PDK_ENV_PY)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_pdk_env() -> dict[str, str]:
    """Resolve PDK vars via pdk_env.py and import them into os.environ.

    Mirrors ``[ -f "$PDK_ENV" ] && source "$PDK_ENV"``: pdk_env.py only fills
    unset/empty vars, so an explicit pre-existing export wins. Returns the
    resolved var map. A missing pdk_env.py is a no-op, matching the guarded
    ``[ -f ]`` source in every owning .sh.
    """
    resolved: dict[str, str] = {}
    if not _PDK_ENV_PY.is_file():
        return resolved

    mod = _load_pdk_env_module()
    if mod is None:  # pragma: no cover - defensive
        return resolved

    # resolve_pdk_env(base_env) honours already-set vars (only fills empties),
    # exactly like ``source pdk_env.sh``.
    resolved = mod.resolve_pdk_env(dict(os.environ))
    for key in _PDK_VARS:
        val = resolved.get(key, "")
        if not os.environ.get(key) and val:
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
