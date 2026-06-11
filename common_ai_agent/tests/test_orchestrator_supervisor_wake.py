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


def test_user_message_wake_consumed_once_per_runner(tmp_path: Path) -> None:
    from src.orchestrator.supervisor_wake import (
        FileBackedSupervisorRunner,
        append_wake_event,
    )

    wake_path = tmp_path / "wake.jsonl"
    runner = FileBackedSupervisorRunner(
        wake_path=wake_path,
        cancel_path=tmp_path / "cancel.json",
    )

    append_wake_event(
        wake_path,
        {"event_id": "evt-um", "type": "user_message", "message": "continue"},
    )

    first = runner.register_waker(
        run_id="run-1",
        user_id="user-1",
        ip_id="ip-1",
        user_message=True,
        after_seconds=0.5,
    )
    assert first.wait() == "user_message"
    runner.unregister_waker("run-1")

    # Same runner: the user_message has already been consumed, so a later
    # yield must not busy-loop-wake on it — it should time out instead.
    second = runner.register_waker(
        run_id="run-1",
        user_id="user-1",
        ip_id="ip-1",
        user_message=True,
        after_seconds=0.05,
    )
    assert second.wait() == "timer"


def test_unmatched_job_complete_not_consumed_by_other_waker(tmp_path: Path) -> None:
    from src.orchestrator.supervisor_wake import (
        FileBackedSupervisorRunner,
        append_wake_event,
    )

    wake_path = tmp_path / "wake.jsonl"
    runner = FileBackedSupervisorRunner(
        wake_path=wake_path,
        cancel_path=tmp_path / "cancel.json",
    )

    # A job_complete for "aaa" appears while a waker is only interested in
    # "bbb" and user_message. The job_complete must NOT be consumed.
    append_wake_event(
        wake_path,
        {
            "event_id": "evt-jc-aaa",
            "type": "job_complete",
            "job_id": "aaa",
            "status": "completed",
        },
    )
    append_wake_event(
        wake_path,
        {"event_id": "evt-um2", "type": "user_message", "message": "ping"},
    )

    first = runner.register_waker(
        run_id="run-1",
        user_id="user-1",
        ip_id="ip-1",
        job_ids={"bbb"},
        user_message=True,
        after_seconds=0.5,
    )
    assert first.wait() == "user_message"
    runner.unregister_waker("run-1")

    # A later waker filtering on "aaa" must still wake on the earlier
    # job_complete — it was never consumed (zombie-wait protection).
    second = runner.register_waker(
        run_id="run-1",
        user_id="user-1",
        ip_id="ip-1",
        job_ids={"aaa"},
        user_message=False,
        after_seconds=0.5,
    )
    assert second.wait() == "job_complete:aaa:completed"


def test_fresh_runner_sees_old_pending_events_once(tmp_path: Path) -> None:
    from src.orchestrator.supervisor_wake import (
        FileBackedSupervisorRunner,
        append_wake_event,
    )

    wake_path = tmp_path / "wake.jsonl"
    cancel_path = tmp_path / "cancel.json"

    append_wake_event(
        wake_path,
        {"event_id": "evt-old-um", "type": "user_message", "message": "resume"},
    )

    # Supervisor respawn: a brand-new runner starts with an empty consumed
    # set and may deliver the old pending user_message once (resume semantics).
    runner = FileBackedSupervisorRunner(wake_path=wake_path, cancel_path=cancel_path)
    first = runner.register_waker(
        run_id="run-1",
        user_id="user-1",
        ip_id="ip-1",
        user_message=True,
        after_seconds=0.5,
    )
    assert first.wait() == "user_message"
    runner.unregister_waker("run-1")

    # ...but only once: a second waker from that same fresh runner times out.
    second = runner.register_waker(
        run_id="run-1",
        user_id="user-1",
        ip_id="ip-1",
        user_message=True,
        after_seconds=0.05,
    )
    assert second.wait() == "timer"
