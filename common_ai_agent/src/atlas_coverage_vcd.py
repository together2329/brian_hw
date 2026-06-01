from __future__ import annotations

from pathlib import Path
from typing import NamedTuple


class VcdSelection(NamedTuple):
    relative_path: str
    error: str = ""

    @property
    def ok(self) -> bool:
        return bool(self.relative_path) and not self.error


def list_vcd_artifacts(project_root: Path, *roots: Path) -> list[str]:
    root_resolved = project_root.resolve()
    paths: list[str] = []
    seen: set[str] = set()
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.glob("**/*.vcd")):
            if not path.is_file():
                continue
            relative = _relative_to_root(path, root_resolved)
            if relative and relative not in seen:
                seen.add(relative)
                paths.append(relative)
    return paths


def select_vcd_artifact(project_root: Path, ip_dir: Path, requested: str) -> VcdSelection:
    raw = requested.strip()
    if not raw:
        return VcdSelection("")
    root_resolved = project_root.resolve()
    ip_resolved = ip_dir.resolve()
    candidate = Path(raw)
    resolved = (candidate if candidate.is_absolute() else root_resolved / candidate).resolve()
    try:
        resolved.relative_to(ip_resolved)
    except ValueError:
        return VcdSelection("", f"VCD path is outside active IP: {raw}")
    if resolved.suffix.lower() != ".vcd":
        return VcdSelection("", f"VCD path must end with .vcd: {raw}")
    if not resolved.is_file():
        return VcdSelection("", f"VCD path not found: {raw}")
    return VcdSelection(_relative_to_root(resolved, root_resolved))


def _relative_to_root(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root).as_posix()
    except ValueError:
        return ""
