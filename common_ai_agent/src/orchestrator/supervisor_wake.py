from __future__ import annotations

import json
import re
import time
import uuid
from pathlib import Path
from typing import Any, Optional, Set


TERMINAL_JOB_STATUSES = {"completed", "error", "cancelled", "blocked"}


def safe_run_id(run_id: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(run_id or "").strip())
    return safe or "run"


def supervisor_control_dir(project_root: Path | str, run_id: str) -> Path:
    return Path(project_root).resolve() / ".session" / "orchestrators-ipc" / safe_run_id(run_id)


def append_wake_event(path: Path | str, event: dict[str, Any]) -> dict[str, Any]:
    wake_path = Path(path)
    wake_path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(event)
    payload.setdefault("event_id", uuid.uuid4().hex)
    payload.setdefault("at", time.time())
    line = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    with wake_path.open("a", encoding="utf-8") as fh:
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
        supervisor_control_dir(project_root, run_id) / "wake.jsonl",
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
            if event_id and event_id in self._seen_event_ids:
                continue
            if event_id:
                self._seen_event_ids.add(event_id)
            reason = self._reason_for(event)
            if reason:
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
        )
        self._wakers[run_id] = waker
        return waker

    def unregister_waker(self, run_id: str) -> None:
        self._wakers.pop(run_id, None)
