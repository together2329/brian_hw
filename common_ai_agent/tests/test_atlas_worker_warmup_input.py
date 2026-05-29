"""AC-2 worker-warmup hardening (backend-only).

These tests encode the silent-loss contract for prompts dispatched to a
session worker that is *not yet alive* (crash-at-startup / spawn-fail
subset). The durable DB session_queue already retains a prompt for a worker
that is booting-but-alive; the remaining gap is the ``is_alive() == False``
gate in ``SessionProcessManager.send_input`` (session_process_manager.py:408)
that rejects the enqueue and makes ``send_input`` return ``None``.

Mechanism recap (from the AC-2 design):
- ``send_input`` returns ``None`` when ``is_alive()`` is False; the message is
  never enqueued.
- ``_send_process_input_for_session`` (atlas_multiuser.py) then reports the
  prompt as undelivered. The frontend retransmit layer has already been
  disarmed by the unconditional ``agent_received`` ack, so the prompt is lost.

Backend fix under test: a tiny respawn-and-re-enqueue safety net in
``_send_process_input_for_session`` for ``prompt``/``interrupt`` inputs — when
the first ``send_input`` returns ``None`` after a spawn, respawn once and retry
``send_input`` before giving up. The DB queue (durable buffer) then retains the
message until ``chat_loop`` drains it. ``msg_id`` dedup must remain intact so a
retry that races the first delivery cannot double-submit.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.atlas_multiuser import _MultiUserBridge
from core.session_process_manager import SessionProcessManager


def _drain(session):
    events = []
    while True:
        try:
            events.append(session._outbox.get_nowait())
        except Exception:
            break
    return events


def test_send_input_returns_none_when_not_alive_gate(monkeypatch):
    """Unit: send_input() must reject when the worker is not alive and must
    NOT enqueue anything (session_process_manager.py:408-409)."""
    manager = SessionProcessManager(db_path=":memory:")
    monkeypatch.setattr(manager, "is_alive", lambda session_id: False)

    enqueue_calls = []

    class _ExplodingDB:
        def enqueue_message(self, *args, **kwargs):  # pragma: no cover - must not run
            enqueue_calls.append((args, kwargs))
            return "should-not-happen"

        def close(self):
            pass

    monkeypatch.setattr(manager, "_get_db", lambda: _ExplodingDB())

    msg_id = manager.send_input("admin/spi_core/default", "prompt", {"text": "hi"})

    assert msg_id is None
    assert enqueue_calls == []


def test_prompt_to_warming_worker_is_enqueued_durably_and_delivered_once_alive():
    """A prompt to a worker that is alive immediately after spawn() (booting,
    queue not yet drained) is RETAINED in the durable DB queue: send_input
    returns a real msg_id and submit_prompt_for_session returns True."""

    class FakeManager:
        def __init__(self):
            self.live = set()
            self.spawned = []
            self.sent = []

        def is_alive(self, session_id):
            return session_id in self.live

        def latest_output_id(self, session_id):
            return None

        def spawn(self, session_id):
            self.spawned.append(session_id)
            self.live.add(session_id)  # alive immediately, still warming
            return True

        def send_input(self, session_id, msg_type, payload=None):
            # Worker is alive: the durable queue retains the message.
            if session_id not in self.live:
                return None
            self.sent.append((session_id, msg_type, payload))
            return f"queued-{len(self.sent)}"

    bridge = _MultiUserBridge(single_user=False, use_processes=True)
    fake = FakeManager()
    bridge._process_manager = fake

    delivered = bridge.submit_prompt_for_session("admin/spi_core/default", "hello")

    assert delivered is True
    assert fake.spawned == ["admin/spi_core/default"]
    assert fake.sent == [("admin/spi_core/default", "prompt", {"text": "hello"})]


def test_respawn_retry_net_redelivers_after_startup_crash():
    """Crash-at-startup subset: the worker is dead at the first send_input
    gate (send_input -> None), then a respawn brings it back. The backend
    safety net must respawn once + retry send_input and end delivered=True
    (NOT silently lost)."""

    class FakeManager:
        def __init__(self):
            self.spawned = []
            self.sent = []
            self.alive = False  # crashed-at-startup: dead at first gate

        def is_alive(self, session_id):
            return self.alive

        def latest_output_id(self, session_id):
            return None

        def spawn(self, session_id):
            self.spawned.append(session_id)
            # Each respawn yields a healthy process.
            self.alive = True
            return True

        def send_input(self, session_id, msg_type, payload=None):
            # First spawn's worker crashed -> dead at the gate.
            if not self.alive:
                return None
            self.sent.append((session_id, msg_type, payload))
            return f"queued-{len(self.sent)}"

        def cleanup_zombies(self):
            return []

    bridge = _MultiUserBridge(single_user=False, use_processes=True)
    fake = FakeManager()
    bridge._process_manager = fake
    # First spawn produces a worker that crashes before send_input runs.
    fake.alive = False

    # Simulate: spawn() in submit makes alive True, but the worker dies
    # immediately so the first send_input gate fails. We model that by
    # toggling alive False right after the initial spawn.
    real_spawn = fake.spawn
    spawn_count = {"n": 0}

    def crashing_then_healthy_spawn(session_id):
        spawn_count["n"] += 1
        real_spawn(session_id)
        if spawn_count["n"] == 1:
            # crash immediately after the first spawn
            fake.alive = False
        return True

    fake.spawn = crashing_then_healthy_spawn

    delivered = bridge.submit_prompt_for_session("admin/spi_core/default", "hi")

    assert delivered is True, "respawn-retry net must redeliver after a startup crash"
    assert spawn_count["n"] >= 2, "expected one respawn after the startup crash"
    assert fake.sent == [("admin/spi_core/default", "prompt", {"text": "hi"})], (
        "the prompt must be delivered exactly once after respawn"
    )


def test_prompt_to_crashed_at_startup_worker_when_respawn_also_fails_reports_not_delivered():
    """If even the respawn cannot revive the worker, the prompt must NOT be
    acked-as-delivered (delivered=False) so the client can retry. The
    acceptance ack carries ok:false (worker_exited + error emitted)."""

    class FakeManager:
        def __init__(self):
            self.spawned = []

        def is_alive(self, session_id):
            return False  # never alive, even after respawn

        def latest_output_id(self, session_id):
            return None

        def spawn(self, session_id):
            self.spawned.append(session_id)
            return True

        def send_input(self, session_id, msg_type, payload=None):
            return None

        def cleanup_zombies(self):
            return list(self.spawned)

    bridge = _MultiUserBridge(single_user=False, use_processes=True)
    fake = FakeManager()
    bridge._process_manager = fake

    delivered = bridge.submit_prompt_for_session("admin/spi_core/default", "hi")

    assert delivered is False
    # The net must have tried to respawn at least once before giving up.
    assert len(fake.spawned) >= 2
    session = bridge.get_session("admin/spi_core/default")
    events = _drain(session)
    assert any(event.get("type") == "worker_exited" for event in events)
    assert any(
        event.get("type") == "error"
        and "input was not delivered" in event.get("message", "")
        for event in events
    )


def test_live_worker_prompt_path_is_unchanged_no_extra_respawn():
    """Regression guard: a normal prompt to a healthy worker still delivers
    once with a single spawn and a single send_input (no spurious respawn)."""

    class FakeManager:
        def __init__(self):
            self.spawned = []
            self.sent = []

        def is_alive(self, session_id):
            return True

        def latest_output_id(self, session_id):
            return None

        def spawn(self, session_id):
            self.spawned.append(session_id)
            return True

        def send_input(self, session_id, msg_type, payload=None):
            self.sent.append((session_id, msg_type, payload))
            return "queued-1"

    bridge = _MultiUserBridge(single_user=False, use_processes=True)
    fake = FakeManager()
    bridge._process_manager = fake

    delivered = bridge.submit_prompt_for_session("admin/spi_core/default", "go")

    assert delivered is True
    assert fake.spawned == ["admin/spi_core/default"]
    assert fake.sent == [("admin/spi_core/default", "prompt", {"text": "go"})]
