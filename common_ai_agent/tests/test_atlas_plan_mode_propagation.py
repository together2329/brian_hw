"""Plan-mode propagation across the web-server -> session-worker boundary.

Regression coverage for the Atlas plan-mode gate bug: in the Atlas web UI the
agent runs in a separate ``core.session_worker`` subprocess, so a ``/plan``
toggle handled in the web-server process never reached the worker (its env was
frozen at spawn and the prompt envelope carried only ``{"text": ...}``). The
worker therefore always ran in NORMAL mode and drove todos straight to
``in_progress`` without waiting for plan approval. The Textual TUI was immune
because it runs the loop in the same process that flips ``PLAN_MODE``.

The fix carries the mode on each prompt envelope:
  1. atlas_multiuser._send_process_input_for_session stamps plan mode onto a
     prompt payload WHEN plan mode is active (normal prompts stay minimal).
  2. session_worker.SessionWorker.input() applies it to the worker process env
     (and a key-absent prompt RESETS to normal), so core/tools.py's PLAN_MODE
     gate and main.chat_loop's agent_mode reconcile both see the right mode.

These are the two halves of the channel that was missing.
"""

import os
import queue
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.atlas_multiuser import _MultiUserBridge
from core.session_worker import SessionWorker

SESSION = "alice/spi_core/rtl-gen"


@pytest.fixture(autouse=True)
def _restore_mode_env():
    """The code under test (worker.input) writes PLAN_MODE / AGENT_MODE_OVERRIDE
    on the *process* env, which pytest's monkeypatch does not roll back when the
    var was absent before the test. Snapshot + restore so plan state never leaks
    into other test modules (e.g. tools.py gate tests)."""
    keys = ("PLAN_MODE", "AGENT_MODE_OVERRIDE", "_PLAN_TODO_WRITE_COUNT")
    saved = {k: os.environ.get(k) for k in keys}
    try:
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


class _CaptureManager:
    """Minimal process-manager stub that records send_input payloads."""

    def __init__(self):
        self.sent = []

    def is_alive(self, session_id):
        return True

    def latest_output_id(self, session_id):
        return None

    def send_input(self, session_id, msg_type, payload=None):
        self.sent.append((session_id, msg_type, payload))
        return f"msg-{len(self.sent)}"


def _bridge_with_capture():
    bridge = _MultiUserBridge(single_user=False, use_processes=True)
    mgr = _CaptureManager()
    bridge._process_manager = mgr
    bridge._ensure_session(SESSION)
    return bridge, mgr


# --------------------------------------------------------------------------- #
# (1) Envelope: the prompt carries plan mode only when plan mode is active.
# --------------------------------------------------------------------------- #


def test_prompt_envelope_carries_plan_mode_when_active(monkeypatch):
    """A prompt submitted while plan mode is active stamps plan_mode/agent_mode
    onto the worker envelope (so the worker can gate todo execution)."""
    monkeypatch.setenv("PLAN_MODE", "true")
    monkeypatch.setenv("AGENT_MODE_OVERRIDE", "plan_q")

    bridge, mgr = _bridge_with_capture()
    bridge._send_process_input_for_session(SESSION, "prompt", {"text": "build X"}, spawn=False)

    assert mgr.sent, "prompt was not delivered"
    payload = mgr.sent[-1][2]
    assert payload["text"] == "build X"
    assert payload["plan_mode"] == "true"
    assert payload["agent_mode"] == "plan_q"


def test_prompt_envelope_converts_plan_confirm_to_normal_execution(monkeypatch):
    """The web-server side must not enqueue bare `y` as plan feedback.

    This is the path the browser uses: the UI can still show PLAN when the user
    presses y, so producer-side conversion protects old and new child workers.
    """
    monkeypatch.setenv("PLAN_MODE", "true")
    monkeypatch.setenv("AGENT_MODE_OVERRIDE", "plan_q")

    bridge, mgr = _bridge_with_capture()
    bridge._send_process_input_for_session(SESSION, "prompt", {"text": "y"}, spawn=False)

    payload = mgr.sent[-1][2]
    assert payload["text"].startswith("Confirmed. Execute all tasks in order.")
    assert "Start now: todo_update(index=1, status='in_progress')" in payload["text"]
    assert payload["plan_mode"] == "false"
    assert payload["agent_mode"] == "normal"
    assert os.environ.get("PLAN_MODE") == "false"
    assert os.environ.get("AGENT_MODE_OVERRIDE") == "normal"

    outbox = []
    session = bridge._ensure_session(SESSION)
    while True:
        try:
            outbox.append(session._outbox.get_nowait())
        except queue.Empty:
            break
    assert any(
        row.get("type") == "mode_change" and row.get("mode") == "normal"
        for row in outbox
    )


def test_prompt_envelope_is_minimal_when_normal(monkeypatch):
    """A normal-mode prompt carries NO mode key — the envelope stays byte
    identical to the historical contract (no bloat, key-absence == normal)."""
    monkeypatch.delenv("PLAN_MODE", raising=False)
    monkeypatch.setenv("AGENT_MODE_OVERRIDE", "normal")

    bridge, mgr = _bridge_with_capture()
    bridge._send_process_input_for_session(SESSION, "prompt", {"text": "go"}, spawn=False)

    payload = mgr.sent[-1][2]
    assert payload == {"text": "go"}


def test_prompt_envelope_preserves_image_attachments(monkeypatch):
    monkeypatch.delenv("PLAN_MODE", raising=False)
    monkeypatch.setenv("AGENT_MODE_OVERRIDE", "normal")

    bridge, mgr = _bridge_with_capture()
    images = [{"image_url": "data:image/png;base64,aGVsbG8=", "detail": "high"}]
    bridge._send_process_input_for_session(
        SESSION, "prompt", {"text": "inspect", "images": images}, spawn=False
    )

    payload = mgr.sent[-1][2]
    assert payload == {"text": "inspect", "images": images}


def test_non_prompt_messages_never_get_mode_keys(monkeypatch):
    """Only prompts carry mode; control messages (stop/interrupt) do not."""
    monkeypatch.setenv("PLAN_MODE", "true")
    monkeypatch.setenv("AGENT_MODE_OVERRIDE", "plan_q")

    bridge, mgr = _bridge_with_capture()
    bridge._send_process_input_for_session(SESSION, "stop", {}, spawn=False)

    assert mgr.sent[-1][1] == "stop"
    assert "plan_mode" not in (mgr.sent[-1][2] or {})


# --------------------------------------------------------------------------- #
# (2) Worker side: input() applies the envelope mode to THIS process's env,
#     which is exactly what core/tools.py:todo_update gates on (PLAN_MODE).
# --------------------------------------------------------------------------- #


def test_worker_input_applies_plan_mode_from_envelope(tmp_path, monkeypatch):
    """A plan-tagged prompt flips the worker process into plan mode, so the
    tools.py PLAN_MODE gate (os.environ['PLAN_MODE'] == 'true') engages."""
    monkeypatch.delenv("PLAN_MODE", raising=False)
    monkeypatch.delenv("AGENT_MODE_OVERRIDE", raising=False)

    worker = SessionWorker(SESSION, str(tmp_path / "atlas.db"))
    try:
        worker.db.enqueue_message(
            SESSION, "in", "prompt",
            {"text": "design a uart", "plan_mode": "true", "agent_mode": "plan_q"},
        )
        text = worker.input("> ")
    finally:
        worker.close()

    assert text == "design a uart"
    # This is the exact condition core/tools.py:todo_update checks before it
    # allows a todo to move to in_progress.
    assert os.environ.get("PLAN_MODE") == "true"
    assert os.environ.get("AGENT_MODE_OVERRIDE") == "plan_q"


def test_worker_input_plan_confirm_y_switches_to_normal_execution(tmp_path, monkeypatch):
    """`y` on a plan-confirm prompt must execute, not become plan feedback.

    The browser sends `y` while its PLAN pill is still active, so the envelope
    is still plan_mode=true. The worker must convert that boundary event into
    the normal execution instruction before main/react_loop sees it.
    """
    monkeypatch.setenv("PLAN_MODE", "true")
    monkeypatch.setenv("AGENT_MODE_OVERRIDE", "plan_q")

    worker = SessionWorker(SESSION, str(tmp_path / "atlas.db"))
    try:
        worker.db.enqueue_message(
            SESSION, "in", "prompt",
            {"text": "y", "plan_mode": "true", "agent_mode": "plan_q"},
        )
        text = worker.input("> ")
    finally:
        worker.close()

    assert text.startswith("Confirmed. Execute all tasks in order.")
    assert "Start now: todo_update(index=1, status='in_progress')" in text
    assert os.environ.get("PLAN_MODE") == "false"
    assert os.environ.get("AGENT_MODE_OVERRIDE") == "normal"


def test_worker_input_resets_to_normal_on_keyless_prompt(tmp_path, monkeypatch):
    """A normal prompt (no mode key) RESETS a worker that a prior unconfirmed
    plan turn left in plan mode — otherwise a stale PLAN_MODE would wrongly gate
    the normal turn."""
    # Simulate a worker left in plan mode by a previous turn.
    monkeypatch.setenv("PLAN_MODE", "true")
    monkeypatch.setenv("AGENT_MODE_OVERRIDE", "plan_q")

    worker = SessionWorker(SESSION, str(tmp_path / "atlas.db"))
    try:
        worker.db.enqueue_message(SESSION, "in", "prompt", {"text": "just do it"})
        text = worker.input("> ")
    finally:
        worker.close()

    assert text == "just do it"
    assert os.environ.get("PLAN_MODE") == "false"
    assert os.environ.get("AGENT_MODE_OVERRIDE") == "normal"


def test_worker_input_plan_false_envelope_is_normal(tmp_path, monkeypatch):
    """An explicit plan_mode='false' envelope is treated as normal."""
    monkeypatch.setenv("PLAN_MODE", "true")
    monkeypatch.setenv("AGENT_MODE_OVERRIDE", "plan_q")

    worker = SessionWorker(SESSION, str(tmp_path / "atlas.db"))
    try:
        worker.db.enqueue_message(
            SESSION, "in", "prompt",
            {"text": "run", "plan_mode": "false", "agent_mode": "normal"},
        )
        worker.input("> ")
    finally:
        worker.close()

    assert os.environ.get("PLAN_MODE") == "false"
    assert os.environ.get("AGENT_MODE_OVERRIDE") == "normal"
