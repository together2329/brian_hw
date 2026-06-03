"""Task 5 — worker epoch fencing + stale-input hygiene.

Exercises the REAL SessionWorker stale-input methods (bound to a duck-typed
holder so no subprocess/LLM is needed), the manager's unconditional epoch
tagging in send_input, and the dual-marker DB helper. Wave-3 H7/H11.
"""

from __future__ import annotations

import os
import sys
import tempfile
import types
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.atlas_db import AtlasDB  # noqa: E402
import core.session_process_manager as spm  # noqa: E402
from core.session_process_manager import SessionProcessManager  # noqa: E402
from core.session_worker import (  # noqa: E402
    SessionWorker,
    _message_epoch,
    _worker_epoch_env,
)


def _runtime_db(tmp_path) -> AtlasDB:
    db = AtlasDB(str(tmp_path / "rt.db"), schema_set="runtime")
    db.init_db()
    return db


def _duck_worker(db: AtlasDB, session_id: str):
    """A minimal holder with the SessionWorker stale-input methods bound to it.

    Lets us drive the genuine fence logic without constructing the full agent.
    """
    w = types.SimpleNamespace()
    w.db = db
    w.session_id = session_id
    w.emitted = []
    w.emit = lambda t, p=None: w.emitted.append((t, p))

    def _ack(msg):
        mid = msg.get("id") or msg.get("msg_id")
        if mid is not None:
            db.acknowledge_message(mid)

    w.acknowledge = _ack
    for name in ("_is_stale_input", "_discard_stale_input", "fence_stale_startup_inputs", "poll_matching"):
        setattr(w, name, types.MethodType(getattr(SessionWorker, name), w))
    return w


# ── module helpers ──────────────────────────────────────────────

def test_message_epoch_and_env(monkeypatch):
    assert _message_epoch({"payload": {"worker_epoch": "E1"}}) == "E1"
    assert _message_epoch({"payload": {"text": "hi"}}) is None
    assert _message_epoch({"payload": None}) is None
    monkeypatch.delenv("ATLAS_SESSION_WORKER_EPOCH", raising=False)
    assert _worker_epoch_env() == ""
    monkeypatch.setenv("ATLAS_SESSION_WORKER_EPOCH", " E2 ")
    assert _worker_epoch_env() == "E2"


# ── fence_stale_startup_inputs ──────────────────────────────────

def test_fence_drains_all_stale_keeps_current_and_untagged(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLAS_SESSION_WORKER_EPOCH", "E2")
    db = _runtime_db(tmp_path)
    s = "alice/ip/wf"
    for t in ("prompt", "interrupt", "answer", "stop"):
        db.enqueue_message(s, "in", t, {"worker_epoch": "E1"})
    db.enqueue_message(s, "in", "prompt", {"text": "untagged"})
    db.enqueue_message(s, "in", "prompt", {"text": "mine", "worker_epoch": "E2"})

    w = _duck_worker(db, s)
    fenced = w.fence_stale_startup_inputs()
    assert fenced == 4
    left = sorted(_message_epoch(m) or "untagged" for m in db.poll_messages(s, "in", since_id=None, limit=100))
    assert left == ["E2", "untagged"]
    # one stale_input_ignored emitted per fenced row
    assert sum(1 for t, _ in w.emitted if t == "stale_input_ignored") == 4


def test_fence_is_noop_without_env_epoch(tmp_path, monkeypatch):
    monkeypatch.delenv("ATLAS_SESSION_WORKER_EPOCH", raising=False)
    db = _runtime_db(tmp_path)
    s = "alice/ip/wf"
    db.enqueue_message(s, "in", "prompt", {"text": "x", "worker_epoch": "WHATEVER"})
    w = _duck_worker(db, s)
    assert w.fence_stale_startup_inputs() == 0  # fail-open: legacy untouched
    assert len(db.poll_messages(s, "in", since_id=None, limit=100)) == 1


def test_poll_matching_skips_stale_stop(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLAS_SESSION_WORKER_EPOCH", "E2")
    db = _runtime_db(tmp_path)
    s = "alice/ip/wf"
    db.enqueue_message(s, "in", "stop", {"worker_epoch": "E1"})  # stale
    w = _duck_worker(db, s)
    # A stale stop must NOT be returned (check_stop would otherwise trip).
    assert w.poll_matching(("stop",)) is None
    # current-epoch stop IS returned
    db.enqueue_message(s, "in", "stop", {"worker_epoch": "E2"})
    got = w.poll_matching(("stop",))
    assert got is not None and _message_epoch(got) == "E2"


# ── send_input unconditional tagging ────────────────────────────

def test_send_input_tags_payload_unconditionally(tmp_path, monkeypatch):
    db = _runtime_db(tmp_path)
    mgr = SessionProcessManager(db_path=str(tmp_path / "ctrl.db"))
    monkeypatch.setattr(mgr, "_get_runtime_db", lambda *a, **k: db)

    class _Fake:
        pid = 9
        def poll(self):  # alive
            return None

    mgr._processes["alice/ip/wf"] = {"proc": _Fake(), "started_at": 0.0, "worker_epoch": "EPCH"}

    caller_payload = {"text": "hi"}
    mid = mgr.send_input("alice/ip/wf", "prompt", caller_payload)
    assert mid is not None
    row = db.poll_messages("alice/ip/wf", "in", since_id=None, limit=10)[0]
    assert _message_epoch(row) == "EPCH"
    assert caller_payload == {"text": "hi"}  # caller dict NOT mutated

    # tagging is unconditional across the actionable types
    mgr.send_input("alice/ip/wf", "stop", {})
    stop_row = [m for m in db.poll_messages("alice/ip/wf", "in", since_id=None, limit=10)
               if m.get("msg_type") == "stop"][0]
    assert _message_epoch(stop_row) == "EPCH"


def test_send_input_does_not_tag_non_actionable_types(tmp_path, monkeypatch):
    db = _runtime_db(tmp_path)
    mgr = SessionProcessManager(db_path=str(tmp_path / "ctrl.db"))
    monkeypatch.setattr(mgr, "_get_runtime_db", lambda *a, **k: db)

    class _Fake:
        pid = 9
        def poll(self):
            return None

    mgr._processes["alice/ip/wf"] = {"proc": _Fake(), "started_at": 0.0, "worker_epoch": "EPCH"}
    mgr.send_input("alice/ip/wf", "token", {"text": "t"})
    row = [m for m in db.poll_messages("alice/ip/wf", "in", since_id=None, limit=10)
           if m.get("msg_type") == "token"][0]
    assert _message_epoch(row) is None  # only prompt/interrupt/answer/stop tagged


# ── DB helper variants ──────────────────────────────────────────

def test_mark_stale_before_epoch_keeps_incoming(tmp_path):
    db = _runtime_db(tmp_path)
    s = "alice/ip/wf"
    db.enqueue_message(s, "in", "stop", {"worker_epoch": "E1"})
    db.enqueue_message(s, "in", "interrupt", {"worker_epoch": "E1"})
    db.enqueue_message(s, "in", "prompt", {"worker_epoch": "E2"})
    n = db.mark_stale_session_inputs_delivered(s, before_epoch="E2", msg_types=["stop", "interrupt", "answer"])
    assert n == 2
    assert db.session_queue_depth(s).get("unprocessed") == 1  # only the E2 prompt
    assert [m.get("msg_type") for m in db.poll_messages(s, "in", since_id=None, limit=10)] == ["prompt"]


def test_mark_stale_all_when_no_before_epoch(tmp_path):
    db = _runtime_db(tmp_path)
    s = "alice/ip/wf"
    db.enqueue_message(s, "in", "stop", {"worker_epoch": "E1"})
    db.enqueue_message(s, "in", "prompt", {"text": "no epoch"})
    n = db.mark_stale_session_inputs_delivered(s)
    assert n == 2
    assert db.session_queue_depth(s).get("unprocessed") == 0
    assert db.poll_messages(s, "in", since_id=None, limit=10) == []
