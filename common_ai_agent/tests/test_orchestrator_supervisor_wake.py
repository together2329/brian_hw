from __future__ import annotations

import time
from pathlib import Path


def test_waker_reads_user_message_event(tmp_path: Path) -> None:
    from src.orchestrator.supervisor_wake import FileBackedWaker, append_wake_event

    wake_path = tmp_path / "wake.jsonl"
    waker = FileBackedWaker(
        wake_path=wake_path,
        cancel_path=tmp_path / "cancel.json",
        run_id="run-1",
        user_id="user-1",
        ip_id="ip-1",
        user_message=True,
        after_seconds=0.5,
    )

    append_wake_event(
        wake_path,
        {"event_id": "evt-1", "type": "user_message", "message": "continue"},
    )

    assert waker.wait() == "user_message"


def test_waker_reads_job_complete_event(tmp_path: Path) -> None:
    from src.orchestrator.supervisor_wake import FileBackedWaker, append_wake_event

    wake_path = tmp_path / "wake.jsonl"
    waker = FileBackedWaker(
        wake_path=wake_path,
        cancel_path=tmp_path / "cancel.json",
        run_id="run-1",
        user_id="user-1",
        ip_id="ip-1",
        job_ids={"job-1"},
        user_message=False,
        after_seconds=0.5,
    )

    append_wake_event(
        wake_path,
        {
            "event_id": "evt-2",
            "type": "job_complete",
            "job_id": "job-1",
            "status": "completed",
        },
    )

    assert waker.wait() == "job_complete:job-1:completed"


def test_waker_timer_reason_matches_existing_contract(tmp_path: Path) -> None:
    from src.orchestrator.supervisor_wake import FileBackedWaker

    waker = FileBackedWaker(
        wake_path=tmp_path / "wake.jsonl",
        cancel_path=tmp_path / "cancel.json",
        run_id="run-1",
        user_id="user-1",
        ip_id="ip-1",
        user_message=False,
        after_seconds=0.01,
    )

    started = time.monotonic()
    assert waker.wait() == "timer"
    assert time.monotonic() - started < 0.5
