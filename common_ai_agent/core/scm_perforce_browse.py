from __future__ import annotations

from pathlib import Path
from typing import Final, Literal, NamedTuple, TypedDict

DEPOT_BROWSE_LIMIT: Final[int] = 1000
_DEPOT_FORBIDDEN: Final[tuple[str, ...]] = ("*", "...", "@", "#")


class LocalPaneEntry(TypedDict):
    path: str
    state: str
    kind: Literal["folder", "file"]


class DepotPaneEntry(TypedDict):
    path: str
    rev: str
    kind: Literal["folder", "file"]


class PaneBrowseScope(NamedTuple):
    local_dir: str
    depot_dir: str
    depot_pattern: str


def stream_root(branch: str) -> str:
    clean = str(branch or "").strip().rstrip("/")
    return f"{clean}/" if clean.startswith("//") else ""


def normalize_local_dir(base: Path, local_dir: str) -> str:
    text = str(local_dir or "").strip().strip("/")
    if not text:
        return ""
    candidate = base / text
    try:
        resolved = candidate.resolve()
        rel = resolved.relative_to(base.resolve())
    except (OSError, RuntimeError, ValueError):
        return ""
    clean = rel.as_posix().strip("/")
    return "" if clean == "." else clean


def normalize_depot_dir(depot_dir: str, branch: str) -> str:
    root = stream_root(branch)
    if not root:
        return ""
    text = str(depot_dir or "").strip()
    if not text:
        return root
    if any(token in text for token in _DEPOT_FORBIDDEN):
        return root
    clean = f"{text.rstrip('/')}/"
    if clean == f"{root.rstrip('/')}/":
        return root
    if not clean.startswith(root):
        return root
    parts = [part for part in clean[len(root):].split("/") if part]
    if any(part in (".", "..") for part in parts):
        return root
    return clean


def pane_browse_scope(base: Path, local_dir: str, depot_dir: str, branch: str) -> PaneBrowseScope:
    clean_local = normalize_local_dir(base, local_dir)
    clean_depot = normalize_depot_dir(depot_dir, branch)
    pattern = f"{clean_depot.rstrip('/')}/*" if clean_depot else ""
    return PaneBrowseScope(local_dir=clean_local, depot_dir=clean_depot, depot_pattern=pattern)


def local_entries(
    base: Path,
    local_dir: str,
    skip_dirs: frozenset[str],
    skip_files: frozenset[str],
) -> list[LocalPaneEntry]:
    current = base / local_dir if local_dir else base
    try:
        children = list(current.iterdir())
    except OSError:
        return []
    rows: list[LocalPaneEntry] = []
    for child in children:
        name = child.name
        if child.is_dir():
            if name in skip_dirs or name.startswith("."):
                continue
            rows.append({"path": _rel_path(child, base), "state": "", "kind": "folder"})
            continue
        if not child.is_file() or name in skip_files:
            continue
        rows.append({"path": _rel_path(child, base), "state": "new", "kind": "file"})
    rows.sort(key=lambda row: (row["kind"] != "folder", row["path"]))
    return rows


def depot_folder_entries(stdout: str) -> list[DepotPaneEntry]:
    rows: list[DepotPaneEntry] = []
    seen: set[str] = set()
    for raw in stdout.splitlines():
        text = raw.strip()
        if not text:
            continue
        path = f"{text.rstrip('/')}/"
        if path in seen:
            continue
        seen.add(path)
        rows.append({"path": path, "rev": "", "kind": "folder"})
    return rows


def depot_file_entries(records: list[dict[str, str]]) -> list[DepotPaneEntry]:
    rows: list[DepotPaneEntry] = []
    for rec in records:
        depot_file = rec.get("depotFile", "")
        head_rev = rec.get("headRev", "")
        head_action = rec.get("headAction", "")
        if not depot_file or not head_rev or head_action == "delete":
            continue
        rows.append({"path": depot_file, "rev": head_rev, "kind": "file"})
    return rows


def merge_depot_entries(folders: list[DepotPaneEntry], files: list[DepotPaneEntry]) -> list[DepotPaneEntry]:
    rows = [*folders, *files]
    rows.sort(key=lambda row: (row["kind"] != "folder", row["path"]))
    return rows


def _rel_path(path: Path, base: Path) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except (OSError, RuntimeError, ValueError):
        return path.name
