"""Helpers for resolving the RTL top used by Atlas sim_debug.

The UI is scoped by an IP directory, but the actual elaboration top can come
from a cocotb manifest, SSOT, or VCD scope. Keep this logic outside
atlas_ui.py so hierarchy and trace routes make the same choice.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


_MODULE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*$")
_DUMP_TOP_RE = re.compile(r"^(?:iverilog_dump|atlas_iverilog_vcd_dump|.*_vcd_dump)$")


def _clean_module(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    text = text.split(".", 1)[0].strip()
    return text if _MODULE_RE.match(text) else ""


def _top_from_ssot_value(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("name", "module", "top", "id"):
            top = _clean_module(value.get(key))
            if top:
                return top
        return ""
    return _clean_module(value)


def _read_json_top(path: Path) -> str:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    if not isinstance(data, dict):
        return ""
    return _clean_module(data.get("top") or data.get("top_module"))


def _read_yaml_top(path: Path) -> str:
    try:
        import yaml
    except ImportError:
        return ""
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8", errors="replace")) or {}
    except Exception:
        return ""
    if not isinstance(data, dict):
        return ""
    return _top_from_ssot_value(data.get("top_module") or data.get("top"))


def _first_vcd_scope_top(scope: str) -> str:
    for part in str(scope or "").split("."):
        top = _clean_module(part)
        if top and not _DUMP_TOP_RE.match(top):
            return top
    return ""


def _candidate_paths(project_root: Path, ip: str, tail: str) -> list[Path]:
    clean = str(ip or "").strip().strip("/")
    if not clean:
        return []
    ip_leaf = Path(clean).name
    patterns = [
        f"{clean}/{tail}",
        f"{ip_leaf}/{tail}",
        f"common_ai_agent/{clean}/{tail}",
        f"common_ai_agent/{ip_leaf}/{tail}",
        f"common_ai_agent/*/{ip_leaf}/{tail}",
        f"*/{ip_leaf}/{tail}",
        f"*/*/{ip_leaf}/{tail}",
    ]
    out: list[Path] = []
    seen: set[str] = set()
    for pattern in patterns:
        for path in project_root.glob(pattern):
            try:
                resolved = path.resolve()
                resolved.relative_to(project_root.resolve())
            except (OSError, ValueError):
                continue
            key = resolved.as_posix()
            if key not in seen:
                seen.add(key)
                out.append(resolved)
    return out


def resolve_sim_debug_top(
    project_root: Path,
    *,
    ip: str = "",
    requested_top: str = "",
    vcd_scope: str = "",
) -> dict[str, Any]:
    """Resolve the RTL elaboration top for sim_debug routes.

    Precedence:
    1. Explicit non-IP top requested by the user/UI.
    2. cocotb tb_manifest.json top.
    3. SSOT top_module.name / top_module.
    4. First non-dump VCD scope.
    5. Requested top or IP leaf fallback.
    """

    root = project_root.resolve()
    ip_clean = str(ip or "").strip().strip("/")
    ip_leaf = Path(ip_clean).name
    requested = _clean_module(requested_top)
    scope_top = _first_vcd_scope_top(vcd_scope)

    manifest_top = ""
    manifest_path = ""
    for path in _candidate_paths(root, ip_clean, "tb/cocotb/tb_manifest.json"):
        manifest_top = _read_json_top(path)
        if manifest_top:
            manifest_path = path.relative_to(root).as_posix()
            break

    ssot_top = ""
    ssot_path = ""
    for path in _candidate_paths(root, ip_clean, "yaml/*.ssot.yaml"):
        ssot_top = _read_yaml_top(path)
        if ssot_top:
            ssot_path = path.relative_to(root).as_posix()
            break

    if requested and requested != ip_leaf:
        chosen = requested
        source = "request"
    elif manifest_top:
        chosen = manifest_top
        source = "tb_manifest"
    elif ssot_top:
        chosen = ssot_top
        source = "ssot"
    elif scope_top:
        chosen = scope_top
        source = "vcd_scope"
    else:
        chosen = requested or _clean_module(ip_leaf)
        source = "fallback"

    return {
        "top": chosen,
        "source": source,
        "requested_top": requested,
        "ip": ip_clean,
        "ip_leaf": ip_leaf,
        "vcd_scope_top": scope_top,
        "manifest_top": manifest_top,
        "manifest_path": manifest_path,
        "ssot_top": ssot_top,
        "ssot_path": ssot_path,
    }
