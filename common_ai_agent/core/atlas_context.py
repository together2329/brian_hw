"""Explicit ATLAS runtime context.

This module keeps session/user/IP/workflow identity in one immutable object so
runtime code does not have to infer ownership from process-global environment
variables or the latest active WebSocket session.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import re
import uuid


_SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]*$")


def _safe_segment(value: object | None, default: str = "default") -> str:
    text = str(value or "").strip().strip("/")
    if not text:
        return default
    text = re.sub(r"[^A-Za-z0-9_.-]+", "_", text)
    text = text.strip("._-") or default
    if not re.match(r"^[A-Za-z]", text):
        text = f"{default}_{text}"
    return text


def _validated_segment(value: object, *, field_name: str) -> str:
    text = str(value)
    if "/" in text:
        raise ValueError(f"{field_name} must not contain '/'")
    if not _SAFE_SEGMENT_RE.fullmatch(text):
        raise ValueError(f"{field_name} must be a non-empty safe path segment")
    return text


@dataclass(frozen=True)
class SessionContext:
    """Immutable identity for one ATLAS execution scope."""

    user_id: str = ""
    username: str = ""
    session_id: str = ""
    owner: str = "default"
    workspace_id: str = ""
    workspace_name: str = ""
    ip_id: str = ""
    ip_name: str = "default"
    workflow: str = "default"
    run_id: str = ""
    stage_id: str = ""
    todo_id: str = ""
    rtl_version_id: str = ""
    project_root: Path | str = "."
    correlation_id: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "owner", _safe_segment(self.owner or self.username))
        object.__setattr__(self, "ip_name", _safe_segment(self.ip_name))
        object.__setattr__(self, "workflow", _safe_segment(self.workflow))
        object.__setattr__(self, "project_root", Path(self.project_root).resolve())
        if not self.correlation_id:
            object.__setattr__(self, "correlation_id", uuid.uuid4().hex)

    @classmethod
    def from_session_key(
        cls,
        session_key: str,
        *,
        user_id: str = "",
        username: str = "",
        session_id: str = "",
        workspace_id: str = "",
        workspace_name: str = "",
        ip_id: str = "",
        project_root: Path | str = ".",
        correlation_id: str = "",
    ) -> "SessionContext":
        parts = [_safe_segment(part) for part in str(session_key or "").split("/") if part]
        if len(parts) >= 3:
            owner, ip_name, workflow = parts[0], parts[1], parts[2]
        elif len(parts) == 2:
            owner = _safe_segment(username or "default")
            ip_name, workflow = parts
        elif len(parts) == 1:
            owner = _safe_segment(username or "default")
            ip_name = "default"
            workflow = parts[0]
        else:
            owner = _safe_segment(username or "default")
            ip_name = "default"
            workflow = "default"
        return cls(
            user_id=user_id,
            username=username,
            session_id=session_id,
            owner=owner,
            workspace_id=workspace_id,
            workspace_name=workspace_name,
            ip_id=ip_id,
            ip_name=ip_name,
            workflow=workflow,
            project_root=project_root,
            correlation_id=correlation_id,
        )

    @property
    def session_key(self) -> str:
        return f"{self.owner}/{self.ip_name}/{self.workflow}"

    @property
    def session_dir(self) -> Path:
        return Path(self.project_root) / ".session" / self.owner / self.ip_name / self.workflow

    def with_run(self, run_id: str) -> "SessionContext":
        return replace(self, run_id=run_id or "")

    def with_stage(self, stage_id: str) -> "SessionContext":
        return replace(self, stage_id=stage_id or "")

    def with_todo(self, todo_id: str) -> "SessionContext":
        return replace(self, todo_id=todo_id or "")

    def with_rtl_version(self, rtl_version_id: str) -> "SessionContext":
        return replace(self, rtl_version_id=rtl_version_id or "")

    def trace_fields(self) -> dict[str, str]:
        return {
            "session_id": self.session_id,
            "workspace_id": self.workspace_id,
            "ip_id": self.ip_id,
            "workflow": self.workflow,
            "run_id": self.run_id,
            "stage_id": self.stage_id,
            "todo_id": self.todo_id,
            "rtl_version_id": self.rtl_version_id,
            "actor_user_id": self.user_id,
            "correlation_id": self.correlation_id,
        }


@dataclass(frozen=True)
class AtlasContext:
    user_name: str
    workspace_session: str
    ip_name: str
    workflow: str
    atlas_root: Path | str = "."

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "user_name",
            _validated_segment(self.user_name, field_name="user_name"),
        )
        object.__setattr__(
            self,
            "workspace_session",
            _validated_segment(self.workspace_session, field_name="workspace_session"),
        )
        object.__setattr__(
            self,
            "ip_name",
            _validated_segment(self.ip_name, field_name="ip_name"),
        )
        object.__setattr__(
            self,
            "workflow",
            _validated_segment(self.workflow, field_name="workflow"),
        )
        object.__setattr__(self, "atlas_root", Path(self.atlas_root).resolve())

    @classmethod
    def from_session_key(
        cls,
        session_key: str,
        *,
        atlas_root: Path | str = ".",
    ) -> "AtlasContext":
        parts = str(session_key).split("/")
        if len(parts) != 4:
            raise ValueError("session_key must contain user/session/ip/workflow")
        user_name, workspace_session, ip_name, workflow = parts
        return cls(
            user_name=user_name,
            workspace_session=workspace_session,
            ip_name=ip_name,
            workflow=workflow,
            atlas_root=atlas_root,
        )

    @property
    def context_key(self) -> str:
        return (
            f"{self.user_name}/"
            f"{self.workspace_session}/"
            f"{self.ip_name}/"
            f"{self.workflow}"
        )

    @property
    def session_key(self) -> str:
        return self.context_key

    @property
    def workspace_root(self) -> Path:
        return Path(self.atlas_root) / self.user_name / self.workspace_session

    @property
    def project_root(self) -> Path:
        return self.workspace_root

    @property
    def ip_root(self) -> Path:
        return self.workspace_root / self.ip_name

    @property
    def session_dir(self) -> Path:
        return self.workspace_root / ".session" / self.ip_name / self.workflow

    def export_env(self) -> dict[str, str]:
        context_key = self.context_key
        workflow = self.workflow
        user_name = self.user_name
        workspace_root = str(self.workspace_root)
        ip_root = str(self.ip_root)
        session_dir = str(self.session_dir)
        return {
            "ATLAS_ROOT": str(self.atlas_root),
            "ATLAS_USER_NAME": user_name,
            "ATLAS_SESSION_ID": context_key,
            "ATLAS_WORKSPACE_ROOT": workspace_root,
            "ATLAS_WORKSPACE_SESSION": self.workspace_session,
            "ATLAS_ACTIVE_IP": self.ip_name,
            "ATLAS_ACTIVE_WORKFLOW": workflow,
            "ATLAS_DEFAULT_WORKFLOW": workflow,
            "ATLAS_WORKFLOW": workflow,
            "ATLAS_IP_ROOT": ip_root,
            "ATLAS_SESSION_DIR": session_dir,
            "ATLAS_CONTEXT_KEY": context_key,
            "ATLAS_PROJECT_ROOT": workspace_root,
            "ATLAS_ACTIVE_SESSION": context_key,
            "ATLAS_DEFAULT_SESSION_ID": user_name,
            "ATLAS_MEMORY_USER": user_name,
            "ACTIVE_WORKSPACE": workflow,
        }
