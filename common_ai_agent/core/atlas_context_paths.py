from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
import os
import re


_SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


def _validated_segment(value: object, *, field_name: str) -> str:
    text = str(value or "").strip()
    if "/" in text:
        raise ValueError(f"{field_name} must not contain '/'")
    if not _SAFE_SEGMENT_RE.fullmatch(text):
        raise ValueError(f"{field_name} must be a non-empty safe path segment")
    return text


def default_atlas_root(env: Mapping[str, str] | None = None) -> Path:
    values = env if env is not None else os.environ
    return Path(values.get("ATLAS_ROOT") or "~/ATLAS").expanduser().resolve()


def resolve_ip_workflow_root(
    project_root: Path | str,
    source_root: Path | str,
    ip_name: str = "",
) -> Path:
    project = Path(project_root).expanduser().resolve()
    source = Path(source_root).expanduser().resolve()
    ip = str(ip_name or "").strip()
    candidates: list[Path] = []
    if ip:
        candidates.append(project / ip / "workflow")
    candidates.append(project / "workflow")
    candidates.append(source / "workflow")
    for candidate in candidates:
        if (candidate / "ssot-gen").is_dir():
            return candidate.resolve()
    return candidates[0].resolve()


@dataclass(frozen=True)
class AtlasContext:
    user_name: str
    workspace_session: str
    ip_name: str
    workflow: str
    atlas_root: Path | str = "."
    legacy: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "user_name", _validated_segment(self.user_name, field_name="user_name"))
        object.__setattr__(self, "workspace_session", _validated_segment(self.workspace_session, field_name="workspace_session"))
        object.__setattr__(self, "ip_name", _validated_segment(self.ip_name, field_name="ip_name"))
        object.__setattr__(self, "workflow", _validated_segment(self.workflow, field_name="workflow"))
        object.__setattr__(self, "atlas_root", Path(self.atlas_root).expanduser().resolve())

    @classmethod
    def from_session_key(
        cls,
        session_key: str,
        *,
        atlas_root: Path | str = ".",
    ) -> "AtlasContext":
        parts = str(session_key or "").strip().strip("/").split("/")
        if len(parts) == 4:
            user_name, workspace_session, ip_name, workflow = parts
            return cls(user_name, workspace_session, ip_name, workflow, atlas_root)
        if len(parts) == 3:
            user_name, ip_name, workflow = parts
            return cls(user_name, "default", ip_name, workflow, atlas_root, legacy=True)
        raise ValueError("session_key must contain owner/ip/workflow or user/session/ip/workflow")

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "AtlasContext":
        values = env if env is not None else os.environ
        key = values.get("ATLAS_CONTEXT_KEY") or values.get("ATLAS_ACTIVE_SESSION") or ""
        if not key:
            user = values.get("ATLAS_USER_NAME") or values.get("ATLAS_DEFAULT_SESSION_ID") or "default"
            session = values.get("ATLAS_SESSION_ID") or values.get("ATLAS_WORKSPACE_SESSION") or "default"
            ip = values.get("ATLAS_ACTIVE_IP") or "default"
            workflow = values.get("ATLAS_ACTIVE_WORKFLOW") or values.get("ATLAS_DEFAULT_WORKFLOW") or "default"
            key = f"{user}/{session}/{ip}/{workflow}"
        return cls.from_session_key(key, atlas_root=default_atlas_root(values))

    @property
    def context_key(self) -> str:
        return f"{self.user_name}/{self.workspace_session}/{self.ip_name}/{self.workflow}"

    @property
    def legacy_session_key(self) -> str:
        return f"{self.user_name}/{self.ip_name}/{self.workflow}"

    @property
    def active_session_key(self) -> str:
        return self.legacy_session_key if self.legacy else self.context_key

    @property
    def session_key(self) -> str:
        return self.active_session_key

    @property
    def workspace_root(self) -> Path:
        if self.legacy:
            return Path(self.atlas_root)
        return Path(self.atlas_root) / self.user_name / self.workspace_session

    @property
    def project_root(self) -> Path:
        return self.workspace_root

    @property
    def ip_root(self) -> Path:
        return self.workspace_root / self.ip_name

    @property
    def workflow_root(self) -> Path:
        return self.ip_root / "workflow"

    @property
    def session_dir(self) -> Path:
        if self.legacy:
            return self.workspace_root / ".session" / self.user_name / self.ip_name / self.workflow
        return self.workspace_root / ".session" / self.ip_name / self.workflow

    def export_env(self) -> dict[str, str]:
        workspace_root = str(self.workspace_root)
        workflow = self.workflow
        return {
            "ATLAS_ROOT": str(self.atlas_root),
            "ATLAS_USER_NAME": self.user_name,
            "ATLAS_SESSION_ID": self.workspace_session,
            "ATLAS_WORKSPACE_ROOT": workspace_root,
            "ATLAS_WORKSPACE_SESSION": self.workspace_session,
            "ATLAS_ACTIVE_IP": self.ip_name,
            "ATLAS_ACTIVE_WORKFLOW": workflow,
            "ATLAS_DEFAULT_WORKFLOW": workflow,
            "ATLAS_WORKFLOW": workflow,
            "ATLAS_IP_ROOT": str(self.ip_root),
            "ATLAS_WORKFLOW_ROOT": str(self.workflow_root),
            "ATLAS_SESSION_DIR": str(self.session_dir),
            "ATLAS_CONTEXT_KEY": self.context_key,
            "ATLAS_PROJECT_ROOT": workspace_root,
            "ATLAS_ACTIVE_SESSION": self.active_session_key,
            "ATLAS_DEFAULT_SESSION_ID": self.user_name,
            "ATLAS_MEMORY_USER": self.user_name,
            "ACTIVE_WORKSPACE": workflow,
        }
