from __future__ import annotations

import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any, Optional, Set


TERMINAL_JOB_STATUSES = {"completed", "error", "cancelled", "blocked"}


def safe_run_id(run_id: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(run_id or "").strip())
    if safe in {".", ".."}:
        return "run"
    return safe or "run"


def supervisor_control_dir(project_root: Path | str, run_id: str) -> Path:
    return Path(project_root).resolve() / ".session" / "orchestrators-ipc" / safe_run_id(run_id)


def _prepare_job_complete_wake_path(project_root: Path | str, run_id: str) -> Path:
    root = Path(project_root).resolve()
    control = supervisor_control_dir(root, run_id)
    for directory in (root / ".session", root / ".session" / "orchestrators-ipc", control):
        if directory.is_symlink():
            raise ValueError(f"supervisor wake path must not be a symlink: {directory}")
        directory.mkdir(parents=True, exist_ok=True)
        resolved = directory.resolve()
        if resolved != root and root not in resolved.parents:
            raise ValueError(f"supervisor wake path escapes project root: {directory}")
        try:
            directory.chmod(0o700)
        except OSError:
            pass
    wake_path = control / "wake.jsonl"
    if wake_path.is_symlink():
        raise ValueError(f"supervisor wake path must not be a symlink: {wake_path}")
    return wake_path


def append_wake_event(path: Path | str, event: dict[str, Any]) -> dict[str, Any]:
    wake_path = Path(path)
    wake_path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(event)
    payload.setdefault("event_id", uuid.uuid4().hex)
    payload.setdefault("at", time.time())
    line = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(wake_path, flags, 0o600)
    with os.fdopen(fd, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    return payload


def append_user_message_wake(
    wake_path: Path | str,
    *,
    message: str,
    chat_message_id: str = "",
) -> dict[str, Any]:
    return append_wake_event(
        wake_path,
        {
            "type": "user_message",
            "message": message,
            "chat_message_id": chat_message_id,
        },
    )


def append_job_complete_wake(
    project_root: Path | str,
    *,
    run_id: str,
    job_id: str,
    status: str,
) -> bool:
    if not run_id or not job_id or status not in TERMINAL_JOB_STATUSES:
        return False
    append_wake_event(
        _prepare_job_complete_wake_path(project_root, run_id),
        {"type": "job_complete", "job_id": job_id, "status": status},
    )
    return True


class FileBackedWaker:
    def __init__(
        self,
        *,
        wake_path: Path | str,
        cancel_path: Path | str,
        run_id: str,
        user_id: str,
        ip_id: str,
        job_ids: Optional[Set[str]] = None,
        user_message: bool = True,
        after_seconds: Optional[float] = None,
        poll_interval: float = 0.025,
        consumed_event_ids: Optional[Set[str]] = None,
    ) -> None:
        self.wake_path = Path(wake_path)
        self.cancel_path = Path(cancel_path)
        self.run_id = run_id
        self.user_id = user_id
        self.ip_id = ip_id
        self.job_ids = set(job_ids or ())
        self.user_message = user_message
        self.after_seconds = after_seconds
        self.poll_interval = poll_interval
        self._offset = 0
        self._seen_event_ids: set[str] = set()
        # Shared across all wakers of the same runner (supervisor process
        # lifetime). An event_id lands here only once a waker MATCHES it and
        # returns it as a wake reason, so a later waker won't re-fire on the
        # same already-handled event (busy-loop fix). Unmatched events are
        # never added here, so a job_complete for job X appended while a waker
        # filtered on job Y still wakes a LATER waker filtering on X.
        self._consumed_event_ids: set[str] = (
            consumed_event_ids if consumed_event_ids is not None else set()
        )
        self._forced_reason = ""

    def wake(self, reason: str) -> None:
        self._forced_reason = str(reason or "unknown")

    def wait(self) -> str:
        deadline = (
            time.monotonic() + float(self.after_seconds)
            if self.after_seconds and self.after_seconds > 0
            else None
        )
        while True:
            if self._forced_reason:
                return self._forced_reason
            if self.cancel_path.exists():
                return "cancelled"
            reason = self._read_next_reason()
            if reason:
                return reason
            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return "timer"
                time.sleep(min(self.poll_interval, remaining))
            else:
                time.sleep(self.poll_interval)

    def _read_next_reason(self) -> str:
        try:
            with self.wake_path.open("r", encoding="utf-8") as fh:
                fh.seek(self._offset)
                lines = fh.readlines()
                self._offset = fh.tell()
        except FileNotFoundError:
            return ""
        for line in lines:
            try:
                event = json.loads(line)
            except Exception:
                continue
            event_id = str(event.get("event_id") or "")
            if event_id and (
                event_id in self._seen_event_ids
                or event_id in self._consumed_event_ids
            ):
                continue
            if event_id:
                self._seen_event_ids.add(event_id)
            reason = self._reason_for(event)
            if reason:
                # Only mark as consumed across the runner when THIS waker's
                # filter matched. Unmatched events stay deliverable to a
                # later waker with a different filter.
                if event_id:
                    self._consumed_event_ids.add(event_id)
                return reason
        return ""

    def _reason_for(self, event: dict[str, Any]) -> str:
        event_type = str(event.get("type") or "")
        if event_type == "user_message" and self.user_message:
            return "user_message"
        if event_type == "job_complete":
            job_id = str(event.get("job_id") or "")
            if job_id in self.job_ids:
                status = str(event.get("status") or "")
                return f"job_complete:{job_id}:{status}".rstrip(":")
        if event_type == "timer":
            return str(event.get("reason") or "timer")
        return ""


class FileBackedSupervisorRunner:
    def __init__(self, *, wake_path: Path | str, cancel_path: Path | str) -> None:
        self.wake_path = Path(wake_path)
        self.cancel_path = Path(cancel_path)
        self._wakers: dict[str, FileBackedWaker] = {}
        # Shared by every waker this runner registers. The runner lives for the
        # supervisor process lifetime, so a user_message (or any matched event)
        # consumed by one yield_run won't busy-loop-wake every subsequent one.
        # A fresh runner (supervisor respawn) starts empty and may re-deliver
        # one old pending event once (intentional resume semantics).
        self.consumed_event_ids: set[str] = set()

    def register_waker(
        self,
        run_id: str,
        user_id: str,
        ip_id: str,
        job_ids: Optional[Set[str]] = None,
        user_message: bool = True,
        after_seconds: Optional[float] = None,
    ) -> FileBackedWaker:
        waker = FileBackedWaker(
            wake_path=self.wake_path,
            cancel_path=self.cancel_path,
            run_id=run_id,
            user_id=user_id,
            ip_id=ip_id,
            job_ids=job_ids,
            user_message=user_message,
            after_seconds=after_seconds,
            consumed_event_ids=self.consumed_event_ids,
        )
        self._wakers[run_id] = waker
        return waker

    def unregister_waker(self, run_id: str) -> None:
        self._wakers.pop(run_id, None)
