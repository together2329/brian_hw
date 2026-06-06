from __future__ import annotations

import fnmatch
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Final, List, Optional, Set, Tuple, Union


JsonValue = Union[None, bool, int, float, str, List["JsonValue"], Dict[str, "JsonValue"]]
LOCKED_TRUTH_GLOBS: Final[Tuple[str, ...]] = (
    "req/*_requirements.md",
    "req/requirements_index.json",
    "req/obligations.json",
    "req/contract_refs.json",
    "req/evidence_plan.json",
    "req/locked_truth.md",
    "req/source_references.md",
    "req/approval_manifest.json",
)
LOCKED_STATUSES: Final[Set[str]] = {"approved", "locked", "all_locked", "requirements_locked"}
LOCKED_REQUIREMENT_STATUSES: Final[Set[str]] = {"approved", "locked"}
UNLOCKED_STATUSES: Final[Set[str]] = {"draft", "pending", "rejected", "unapproved", "unlocked"}
DISABLE_VALUES: Final[Set[str]] = {"0", "false", "no", "off", "disabled"}


@dataclass(frozen=True)
class LockedTruthSnapshot:
    active: bool
    ip_dir: Optional[Path]
    files: Dict[str, bytes]


@dataclass(frozen=True)
class LockedTruthRestoreResult:
    active: bool
    modified_paths: Tuple[str, ...]
    restored_paths: Tuple[str, ...]


def snapshot_locked_truth(project_root: Union[str, Path], ip: str) -> LockedTruthSnapshot:
    if _guard_disabled():
        return LockedTruthSnapshot(active=False, ip_dir=None, files={})
    root = Path(project_root).resolve()
    ip_dir = _safe_ip_dir(root, ip)
    if ip_dir is None or not _lock_active(ip_dir):
        return LockedTruthSnapshot(active=False, ip_dir=ip_dir, files={})
    files: Dict[str, bytes] = {}
    for rel_path in _current_locked_rel_paths(ip_dir):
        path = ip_dir / rel_path
        try:
            files[rel_path] = path.read_bytes()
        except OSError:
            continue
    return LockedTruthSnapshot(active=True, ip_dir=ip_dir, files=files)


def is_locked_truth_active(project_root: Union[str, Path], ip: str) -> bool:
    return snapshot_locked_truth(project_root, ip).active


def restore_locked_truth_if_changed(snapshot: LockedTruthSnapshot) -> LockedTruthRestoreResult:
    if not snapshot.active or snapshot.ip_dir is None:
        return LockedTruthRestoreResult(active=False, modified_paths=(), restored_paths=())
    current = set(_current_locked_rel_paths(snapshot.ip_dir))
    expected = set(snapshot.files)
    modified: list[str] = []
    restored: list[str] = []
    for rel_path in sorted(current | expected):
        path = snapshot.ip_dir / rel_path
        original = snapshot.files.get(rel_path)
        if original is None:
            modified.append(_display_path(snapshot.ip_dir, rel_path))
            try:
                path.unlink()
                restored.append(_display_path(snapshot.ip_dir, rel_path))
            except FileNotFoundError:
                continue
            continue
        try:
            current_bytes = path.read_bytes()
        except OSError:
            current_bytes = None
        if current_bytes == original:
            continue
        modified.append(_display_path(snapshot.ip_dir, rel_path))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(original)
        restored.append(_display_path(snapshot.ip_dir, rel_path))
    return LockedTruthRestoreResult(
        active=True,
        modified_paths=tuple(modified),
        restored_paths=tuple(restored),
    )


def locked_truth_write_error(project_root: Union[str, Path], ip: str, candidate_path: str) -> Optional[str]:
    if _guard_disabled():
        return None
    root = Path(project_root).resolve()
    ip_dir = _safe_ip_dir(root, ip)
    if ip_dir is None or not _lock_active(ip_dir):
        return None
    rel_path = _candidate_locked_rel_path(root, ip_dir, candidate_path)
    if rel_path is None:
        return None
    return (
        "Error: locked truth is approved; refusing to modify "
        f"{_display_path(ip_dir, rel_path)}. Unlock or re-approve the requirement "
        "before changing locked truth."
    )


def locked_truth_violation_message(paths: Tuple[str, ...]) -> str:
    joined = ", ".join(paths)
    return f"locked truth modified and restored: {joined}"


def _guard_disabled() -> bool:
    value = os.getenv("ATLAS_LOCKED_TRUTH_GUARD", "true").strip().lower()
    return value in DISABLE_VALUES


def _safe_ip_dir(root: Path, ip: str) -> Optional[Path]:
    raw_ip = str(ip or "").strip()
    if not raw_ip:
        return None
    candidate = (root / raw_ip).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


def _lock_active(ip_dir: Path) -> bool:
    manifest = ip_dir / "req" / "approval_manifest.json"
    if not manifest.is_file():
        return False
    try:
        raw = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    except OSError:
        return False
    if not isinstance(raw, dict):
        return False
    status_raw = raw.get("status")
    status = status_raw.strip().lower() if isinstance(status_raw, str) else ""
    if status in UNLOCKED_STATUSES:
        return False
    requirements = raw.get("requirements")
    if isinstance(requirements, list):
        return _all_required_requirements_locked(requirements)
    return status in LOCKED_STATUSES


def _all_required_requirements_locked(requirements: List[JsonValue]) -> bool:
    found_required = False
    for entry in requirements:
        if not isinstance(entry, dict):
            return True
        required_raw = entry.get("required")
        if required_raw is False:
            continue
        found_required = True
        status_raw = entry.get("status")
        status = status_raw.strip().lower() if isinstance(status_raw, str) else ""
        if status not in LOCKED_REQUIREMENT_STATUSES:
            return False
    return found_required


def _current_locked_rel_paths(ip_dir: Path) -> Tuple[str, ...]:
    found: Set[str] = set()
    for pattern in LOCKED_TRUTH_GLOBS:
        for path in ip_dir.glob(pattern):
            if not path.is_file():
                continue
            try:
                found.add(path.relative_to(ip_dir).as_posix())
            except ValueError:
                continue
    return tuple(sorted(found))


def _candidate_locked_rel_path(root: Path, ip_dir: Path, candidate_path: str) -> Optional[str]:
    raw = str(candidate_path or "").strip()
    if not raw:
        return None
    path = Path(raw)
    candidates = [path.resolve()] if path.is_absolute() else [(root / path).resolve(), (ip_dir / path).resolve()]
    for candidate in candidates:
        try:
            rel_path = candidate.relative_to(ip_dir).as_posix()
        except ValueError:
            continue
        if _locked_rel_path(rel_path):
            return rel_path
    return None


def _locked_rel_path(rel_path: str) -> bool:
    return any(fnmatch.fnmatch(rel_path, pattern) for pattern in LOCKED_TRUTH_GLOBS)


def _display_path(ip_dir: Path, rel_path: str) -> str:
    return f"{ip_dir.name}/{rel_path}"
