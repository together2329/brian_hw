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

import src.atlas_ui as atlas_ui


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


# ---------------------------------------------------------------------------
# AC-2 Approach A — ws_agent ack contract (atlas_ui.py)
#
# Root cause of the silent loss (per the AC-2 design) is the UNCONDITIONAL
# `agent_received` ack sent at atlas_ui.py:10027-10037 BEFORE delivery is
# known. backend.js keys its 3s/MAX_RETRIES retransmit on `agent_received`
# alone, so an up-front `agent_received` lies about delivery and disarms the
# only auto-retry — a dropped warmup/crash prompt is then lost.
#
# The fix moves `agent_received` so it is emitted ONLY on a real accept
# (alongside agent_accepted{ok:true}); a dropped prompt emits NO
# `agent_received` and only agent_accepted{ok:false}. The testable seam is a
# pure module-level helper `_prompt_ack_frames(...)` that encodes which WS
# frames are emitted for a given acceptance outcome, so the ordering/
# conditionality contract is verifiable without standing up the whole
# websocket closure.
# ---------------------------------------------------------------------------


def _frames(ok, **kwargs):
    return atlas_ui._prompt_ack_frames(
        msg_id="m-1",
        text_preview="hello",
        session_id="admin/spi_core/default",
        ok=ok,
        **kwargs,
    )


def test_ws_agent_does_not_send_agent_received_when_prompt_dropped():
    """When the prompt is NOT accepted by a live worker (delivered=False),
    NO `agent_received` frame may be emitted (so the transport-retry layer
    is NOT disarmed) and an `agent_accepted{ok:false}` IS emitted with the
    undelivered error — proving the silent-ack lie is gone."""
    frames = _frames(
        ok=False,
        queued=False,
        error="input was not delivered to the agent worker",
    )
    types = [f.get("type") for f in frames]

    assert "agent_received" not in types, (
        "a dropped prompt must NOT emit agent_received (it would disarm the "
        "frontend transport retry and silently lose the prompt)"
    )
    accepted = [f for f in frames if f.get("type") == "agent_accepted"]
    assert len(accepted) == 1
    assert accepted[0]["ok"] is False
    assert "input was not delivered" in accepted[0].get("error", "")
    assert accepted[0]["msg_id"] == "m-1"


def test_ws_agent_sends_agent_received_only_after_accept():
    """When the prompt IS genuinely accepted (delivered=True), exactly one
    `agent_received{msg_id}` AND an `agent_accepted{ok:true,msg_id}` are
    emitted (positive-path contract preserved)."""
    frames = _frames(ok=True, queued=True)
    types = [f.get("type") for f in frames]

    received = [f for f in frames if f.get("type") == "agent_received"]
    accepted = [f for f in frames if f.get("type") == "agent_accepted"]

    assert len(received) == 1, "accepted prompt must emit exactly one agent_received"
    assert received[0]["msg_id"] == "m-1"
    assert received[0]["session_id"] == "admin/spi_core/default"

    assert len(accepted) == 1
    assert accepted[0]["ok"] is True
    assert accepted[0]["msg_id"] == "m-1"

    # agent_received (transport ack) must precede agent_accepted (delivery
    # ack) so the client disarms transport retry before evaluating delivery.
    assert types.index("agent_received") < types.index("agent_accepted")


def test_ws_agent_handled_fastpath_emits_received_and_accepted():
    """Slash/bang fast-paths are real accepts (`_accept_handled`): they must
    also emit agent_received + agent_accepted{ok:true,handled=...}."""
    frames = atlas_ui._prompt_ack_frames(
        msg_id="m-2",
        text_preview="/plan",
        session_id="admin/spi_core/default",
        ok=True,
        handled="slash",
    )
    types = [f.get("type") for f in frames]
    assert types.count("agent_received") == 1
    accepted = [f for f in frames if f.get("type") == "agent_accepted"]
    assert len(accepted) == 1
    assert accepted[0]["ok"] is True
    assert accepted[0].get("handled") == "slash"
    assert accepted[0]["msg_id"] == "m-2"


def test_ws_agent_duplicate_is_acked_ok_true_and_dedup_marked():
    """A duplicate (already-seen msg_id) is a genuine accept (the original
    landed), so it is acked ok:true,duplicate WITH agent_received. The msg_id
    dedup (asserted at the bridge/WS layer) is what keeps the worker from
    double-running; the transport ack here is harmless re-disarm. The hard
    AC-2 requirement (no agent_received on a *dropped* prompt) is covered by
    test_ws_agent_does_not_send_agent_received_when_prompt_dropped."""
    frames = atlas_ui._prompt_ack_frames(
        msg_id="m-3",
        text_preview="hello",
        session_id="admin/spi_core/default",
        ok=True,
        duplicate=True,
        handled="duplicate",
    )
    accepted = [f for f in frames if f.get("type") == "agent_accepted"]
    assert len(accepted) == 1
    assert accepted[0]["duplicate"] is True
    assert accepted[0]["ok"] is True
    assert accepted[0].get("handled") == "duplicate"


def test_ws_agent_dropped_prompt_is_the_only_path_without_agent_received():
    """Contract invariant: agent_received is suppressed iff the prompt was
    NOT accepted (ok=False). Every accepted outcome (fresh, duplicate, slash
    fast-path) emits exactly one agent_received."""
    dropped = atlas_ui._prompt_ack_frames(
        msg_id="d", text_preview="x", session_id="s", ok=False,
        error="input was not delivered to the agent worker",
    )
    assert [f["type"] for f in dropped] == ["agent_accepted"]

    for kwargs in (
        {"ok": True, "queued": True},
        {"ok": True, "duplicate": True, "handled": "duplicate"},
        {"ok": True, "handled": "slash"},
    ):
        frames = atlas_ui._prompt_ack_frames(
            msg_id="a", text_preview="x", session_id="s", **kwargs
        )
        assert [f["type"] for f in frames].count("agent_received") == 1, kwargs
