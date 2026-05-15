"""ATLAS workflow trace recording.

TraceRecorder writes one append-only event ledger and mirrors selected events
into existing projection tables such as workflow_todos, llm_calls, and
artifacts. The ledger is the stable audit trail; projections remain optimized
for UI/admin queries.
"""

from __future__ import annotations

import os
import json
import threading
from dataclasses import replace
from pathlib import Path
from typing import Any

from core.atlas_context import SessionContext
from core.atlas_db import AtlasDB


_TRUE_VALUES = {"1", "true", "yes", "on"}
_TRACE_RUNTIME = threading.local()


def push_trace_runtime(**fields: Any) -> dict[str, Any]:
    """Install per-thread trace fields for worker runs.

    HTTP workers may process multiple jobs in one process, so trace identity
    cannot rely only on process-wide environment variables. Env remains the
    fallback for CLI/headless runs.
    """
    previous = dict(getattr(_TRACE_RUNTIME, "fields", {}) or {})
    cleaned = {}
    for k, v in fields.items():
        if v is None:
            continue
        if isinstance(v, (dict, list, tuple)):
            cleaned[str(k)] = json.dumps(v, ensure_ascii=False)
        else:
            cleaned[str(k)] = str(v or "")
    merged = dict(previous)
    merged.update(cleaned)
    _TRACE_RUNTIME.fields = merged
    return previous


def pop_trace_runtime(previous: dict[str, Any] | None) -> None:
    _TRACE_RUNTIME.fields = dict(previous or {})


def _trace_value(name: str, default: str = "") -> str:
    fields = getattr(_TRACE_RUNTIME, "fields", {}) or {}
    if name in fields:
        return str(fields.get(name) or "")
    return str(os.environ.get(name) or default)


def _enabled_from_env() -> bool:
    return _trace_value("ATLAS_TRACE_ENABLE").strip().lower() in _TRUE_VALUES


def _as_notes(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, str):
        return [value] if value else []
    return [value]


def _item_value(item: Any, attr: str, default: Any = "") -> Any:
    if hasattr(item, attr):
        return getattr(item, attr)
    if isinstance(item, dict):
        return item.get(attr, default)
    return default


def _runtime_artifact_versions() -> list[dict[str, Any]]:
    raw = _trace_value("ATLAS_ACTIVE_ARTIFACT_VERSIONS")
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return []
    items: list[Any]
    if isinstance(parsed, dict):
        items = list(parsed.values())
    elif isinstance(parsed, list):
        items = parsed
    else:
        return []
    result: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        version_id = str(item.get("id") or item.get("artifact_version_id") or "").strip()
        if not version_id:
            continue
        result.append({
            "artifact_version_id": version_id,
            "role": str(item.get("role") or "input"),
            "required": bool(item.get("required", True)),
            "metadata": {
                "artifact_type": item.get("artifact_type") or item.get("type") or "",
                "version": item.get("version") or "",
                "source": "trace_runtime",
            },
        })
    return result


class TraceRecorder:
    """Write canonical workflow trace events for one explicit context."""

    def __init__(self, db: AtlasDB, context: SessionContext):
        self.db = db
        self.context = context

    def _attach_runtime_artifact_versions(self, run_id: str) -> None:
        for item in _runtime_artifact_versions():
            try:
                self.db.attach_run_artifact_version(
                    run_id,
                    item["artifact_version_id"],
                    stage_id=self.context.stage_id,
                    role=item["role"],
                    required=item["required"],
                    metadata=item["metadata"],
                )
            except Exception:
                continue

    @classmethod
    def from_env(cls) -> "TraceRecorder | None":
        if not _enabled_from_env():
            return None

        project_root = Path(_trace_value("ATLAS_PROJECT_ROOT") or Path.cwd()).resolve()
        db_path = _trace_value("ATLAS_TRACE_DB_PATH") or _trace_value("ATLAS_DB_PATH")
        db = AtlasDB(db_path) if db_path else AtlasDB()

        session_key = (
            _trace_value("ATLAS_ACTIVE_SESSION")
            or f"{_trace_value('ATLAS_DEFAULT_SESSION_ID', 'default')}/"
            f"{_trace_value('ATLAS_ACTIVE_IP', 'default')}/"
            f"{_trace_value('ATLAS_DEFAULT_WORKFLOW', 'default')}"
        )
        ctx = SessionContext.from_session_key(
            session_key,
            session_id=_trace_value("ATLAS_DB_SESSION_ID") or session_key,
            project_root=project_root,
            correlation_id=_trace_value("ATLAS_TRACE_CORRELATION_ID") or "",
        )

        workspace = db.upsert_workspace(
            project_root.name or "default",
            owner_user_id=ctx.owner,
            local_path=str(project_root),
        )
        ip = db.upsert_ip_block(workspace["id"], _trace_value("ATLAS_ACTIVE_IP") or ctx.ip_name)
        ctx = replace(
            ctx,
            workspace_id=workspace["id"],
            workspace_name=workspace["name"],
            ip_id=ip["id"],
            ip_name=ip["ip_name"],
            workflow=_trace_value("ATLAS_DEFAULT_WORKFLOW") or ctx.workflow,
            rtl_version_id=_trace_value("ATLAS_ACTIVE_RTL_VERSION_ID"),
        )

        run_id = _trace_value("ATLAS_ACTIVE_RUN_ID")
        if run_id:
            ctx = ctx.with_run(run_id)
        else:
            run = db.start_workflow_run(
                session_id=ctx.session_id or ctx.session_key,
                workspace_id=ctx.workspace_id,
                ip_id=ctx.ip_id,
                rtl_version_id=ctx.rtl_version_id,
                workflow=ctx.workflow,
                mode=_trace_value("ATLAS_TRACE_MODE") or "interactive",
                model_profile=_trace_value("ATLAS_MODEL_PROFILE") or "",
                reasoning_effort=_trace_value("ATLAS_REASONING_EFFORT") or "",
                trigger=_trace_value("ATLAS_TRACE_TRIGGER") or "todo_tool",
                input_summary=_trace_value("ATLAS_TRACE_INPUT_SUMMARY") or "",
            )
            runtime_fields = dict(getattr(_TRACE_RUNTIME, "fields", {}) or {})
            if runtime_fields:
                runtime_fields["ATLAS_ACTIVE_RUN_ID"] = run["id"]
                _TRACE_RUNTIME.fields = runtime_fields
            else:
                os.environ["ATLAS_ACTIVE_RUN_ID"] = run["id"]
            ctx = ctx.with_run(run["id"])
            recorder = cls(db, ctx)
            recorder._attach_runtime_artifact_versions(run["id"])
            recorder._record_event(
                "workflow_run.started",
                payload={"trigger": "todo_tool", "source": "env"},
                idempotency_key=f"run-start:{run['id']}",
            )
        recorder = cls(db, ctx)
        if run_id:
            recorder._attach_runtime_artifact_versions(run_id)
        return recorder

    def _existing_event(self, idempotency_key: str) -> dict[str, Any] | None:
        if not idempotency_key:
            return None
        rows = self.db.list_trace_events()
        for row in rows:
            if row.get("idempotency_key") == idempotency_key:
                return row
        return None

    def _record_event(
        self,
        event_type: str,
        *,
        payload: Any = None,
        todo_id: str = "",
        message_id: str = "",
        llm_call_id: str = "",
        artifact_id: str = "",
        causation_id: str = "",
        idempotency_key: str = "",
    ) -> dict[str, Any]:
        fields = self.context.trace_fields()
        if todo_id:
            fields["todo_id"] = todo_id
        return self.db.record_trace_event(
            event_type,
            payload=payload,
            session_id=fields["session_id"] or self.context.session_key,
            workspace_id=fields["workspace_id"],
            ip_id=fields["ip_id"],
            workflow=fields["workflow"],
            run_id=fields["run_id"],
            stage_id=fields["stage_id"],
            todo_id=fields["todo_id"],
            message_id=message_id,
            llm_call_id=llm_call_id,
            artifact_id=artifact_id,
            actor_user_id=fields["actor_user_id"],
            correlation_id=fields["correlation_id"],
            causation_id=causation_id,
            idempotency_key=idempotency_key,
        )

    def start_run(
        self,
        *,
        mode: str = "interactive",
        model_profile: str = "",
        reasoning_effort: str = "",
        trigger: str = "",
        input_summary: str = "",
        status: str = "running",
        idempotency_key: str = "",
    ) -> dict[str, Any]:
        run = self.db.start_workflow_run(
            session_id=self.context.session_id or self.context.session_key,
            workspace_id=self.context.workspace_id,
            ip_id=self.context.ip_id,
            rtl_version_id=self.context.rtl_version_id,
            workflow=self.context.workflow,
            mode=mode,
            model_profile=model_profile,
            reasoning_effort=reasoning_effort,
            trigger=trigger,
            input_summary=input_summary,
            status=status,
        )
        self.context = self.context.with_run(run["id"])
        self._attach_runtime_artifact_versions(run["id"])
        self._record_event(
            "workflow_run.started",
            payload={
                "mode": mode,
                "trigger": trigger,
                "input_summary": input_summary,
                "status": status,
            },
            idempotency_key=idempotency_key,
        )
        return run

    def upsert_todo(
        self,
        *,
        title: str,
        detail: str = "",
        criteria: str = "",
        notes: Any = None,
        status: str = "pending",
        source: str = "",
        owner_file: str = "",
        owner_module: str = "",
        source_refs: Any = None,
        evidence: Any = None,
        todo_id: str = "",
        idempotency_key: str = "",
    ) -> dict[str, Any]:
        todo = self.db.upsert_workflow_todo(
            self.context.run_id,
            title,
            detail=detail,
            criteria=criteria,
            notes=_as_notes(notes),
            status=status,
            source=source,
            owner_file=owner_file,
            owner_module=owner_module,
            source_refs=source_refs,
            evidence=evidence,
            todo_id=todo_id or None,
        )
        self._record_event(
            "todo.upserted",
            payload={
                "title": title,
                "detail": detail,
                "criteria": criteria,
                "status": status,
                "source": source,
            },
            todo_id=todo["id"],
            idempotency_key=idempotency_key,
        )
        return todo

    def record_todo_event(
        self,
        todo_id: str,
        status: str,
        *,
        reason: str = "",
        evidence: Any = None,
        idempotency_key: str = "",
    ) -> dict[str, Any]:
        existing = self._existing_event(idempotency_key)
        if existing is not None:
            return existing
        todo_event = self.db.record_todo_event(todo_id, status, reason=reason, evidence=evidence)
        return self._record_event(
            f"todo.{status}",
            payload={"reason": reason, "evidence": evidence, "todo_event_id": todo_event["id"]},
            todo_id=todo_id,
            idempotency_key=idempotency_key,
        )

    def record_todo_note(
        self,
        todo_id: str,
        note_text: str,
        *,
        idempotency_key: str = "",
    ) -> dict[str, Any]:
        existing = self._existing_event(idempotency_key)
        if existing is not None:
            return existing
        todos = self.db.list_workflow_todos(todo_id=todo_id)
        if not todos:
            raise ValueError(f"Unknown todo id: {todo_id}")
        todo = todos[0]
        notes = _as_notes(todo.get("notes"))
        if note_text:
            notes.append(note_text)
        self.db.upsert_workflow_todo(
            todo["run_id"],
            todo["title"],
            detail=todo.get("detail") or "",
            criteria=todo.get("criteria") or "",
            notes=notes,
            status=todo.get("status") or "pending",
            source=todo.get("source") or "",
            owner_file=todo.get("owner_file") or "",
            owner_module=todo.get("owner_module") or "",
            source_refs=todo.get("source_refs"),
            evidence=todo.get("evidence"),
            todo_id=todo_id,
        )
        return self._record_event(
            "todo.note",
            payload={"note": note_text},
            todo_id=todo_id,
            idempotency_key=idempotency_key,
        )

    def record_llm_call(
        self,
        *,
        todo_id: str = "",
        model: str = "",
        provider: str = "",
        tokens_input: int = 0,
        tokens_output: int = 0,
        tokens_reasoning: int = 0,
        cache_read_tokens: int = 0,
        cache_write_tokens: int = 0,
        cost_usd: float = 0.0,
        status: str = "ok",
        message_id: str = "",
        call_role: str = "primary",
        latency_ms: float | None = None,
        error_type: str = "",
        idempotency_key: str = "",
    ) -> dict[str, Any]:
        call = self.db.record_llm_call(
            session_id=self.context.session_id or self.context.session_key,
            message_id=message_id,
            run_id=self.context.run_id,
            stage_id=self.context.stage_id,
            todo_id=todo_id or self.context.todo_id,
            workspace_id=self.context.workspace_id,
            ip_id=self.context.ip_id,
            workflow=self.context.workflow,
            model=model,
            provider=provider,
            call_role=call_role,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            tokens_reasoning=tokens_reasoning,
            cache_read_tokens=cache_read_tokens,
            cache_write_tokens=cache_write_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            status=status,
            error_type=error_type,
        )
        self._record_event(
            "llm_call.completed" if status in {"ok", "completed", "success"} else "llm_call.failed",
            payload={
                "model": model,
                "provider": provider,
                "tokens_input": tokens_input,
                "tokens_output": tokens_output,
                "tokens_reasoning": tokens_reasoning,
                "cost_usd": cost_usd,
                "status": status,
            },
            todo_id=todo_id,
            message_id=message_id,
            llm_call_id=call["id"],
            idempotency_key=idempotency_key,
        )
        return call

    def register_artifact(
        self,
        *,
        todo_id: str = "",
        kind: str = "",
        path: str = "",
        storage_backend: str = "filesystem",
        sha256: str = "",
        size_bytes: int | None = None,
        git_commit: str = "",
        idempotency_key: str = "",
    ) -> dict[str, Any]:
        artifact = self.db.register_artifact(
            run_id=self.context.run_id,
            stage_id=self.context.stage_id,
            ip_id=self.context.ip_id,
            rtl_version_id=self.context.rtl_version_id,
            workflow=self.context.workflow,
            kind=kind,
            path=path,
            storage_backend=storage_backend,
            sha256=sha256,
            size_bytes=size_bytes,
            git_commit=git_commit,
        )
        self._record_event(
            "artifact.registered",
            payload={
                "kind": kind,
                "path": path,
                "storage_backend": storage_backend,
                "sha256": sha256,
                "size_bytes": size_bytes,
                "git_commit": git_commit,
            },
            todo_id=todo_id,
            artifact_id=artifact["id"],
            idempotency_key=idempotency_key,
        )
        return artifact

    def record_command(
        self,
        command: str,
        *,
        exit_code: int,
        stdout_tail: str = "",
        stderr_tail: str = "",
        todo_id: str = "",
        idempotency_key: str = "",
    ) -> dict[str, Any]:
        payload = {
            "command": command,
            "exit_code": exit_code,
            "stdout_tail": stdout_tail,
            "stderr_tail": stderr_tail,
        }
        if self.context.run_id:
            self.db.record_workflow_event(
                self.context.run_id,
                "command.completed" if exit_code == 0 else "command.failed",
                payload=payload,
                stage_id=self.context.stage_id,
            )
        return self._record_event(
            "command.completed" if exit_code == 0 else "command.failed",
            payload=payload,
            todo_id=todo_id,
            idempotency_key=idempotency_key,
        )

    def record_ask_user(
        self,
        *,
        flow_id: str,
        question: str = "",
        status: str = "opened",
        answer: Any = None,
        todo_id: str = "",
        idempotency_key: str = "",
    ) -> dict[str, Any]:
        return self._record_event(
            f"ask_user.{status}",
            payload={"flow_id": flow_id, "question": question, "answer": answer},
            todo_id=todo_id,
            idempotency_key=idempotency_key,
        )


def record_todo_tool_event_from_env(
    index: int,
    item: Any,
    status: str,
    *,
    reason: str = "",
    note_text: str = "",
) -> bool:
    """Best-effort bridge from the existing todo tool into the trace DB."""
    try:
        recorder = TraceRecorder.from_env()
        if recorder is None:
            return False
        title = str(_item_value(item, "content", "") or f"todo {index}")
        detail = str(_item_value(item, "detail", "") or "")
        criteria = str(_item_value(item, "criteria", "") or "")
        notes = _as_notes(_item_value(item, "notes", []))
        todo_id = f"{recorder.context.run_id}:todo:{index}"
        existing_todos = recorder.db.list_workflow_todos(todo_id=todo_id)
        mirrored_status = str(_item_value(item, "status", "") or "")
        if existing_todos:
            mirrored_status = str(existing_todos[0].get("status") or mirrored_status or status)
        else:
            mirrored_status = mirrored_status or status
        recorder.upsert_todo(
            title=title,
            detail=detail,
            criteria=criteria,
            notes=notes,
            status=mirrored_status,
            source="todo_tool",
            todo_id=todo_id,
            idempotency_key=f"todo-tool:{recorder.context.run_id}:{index}:upsert",
        )
        if status == "note":
            recorder.record_todo_note(
                todo_id,
                note_text,
                idempotency_key=f"todo-tool:{recorder.context.run_id}:{index}:note:{note_text}",
            )
        else:
            recorder.record_todo_event(
                todo_id,
                status,
                reason=reason,
                idempotency_key=f"todo-tool:{recorder.context.run_id}:{index}:{status}:{reason}",
            )
        return True
    except Exception:
        return False
