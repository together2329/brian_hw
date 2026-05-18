import threading
import time

import pytest

from core.atlas_db import AtlasDB
from src.orchestrator.loop import OrchestratorLoop, RunOutcome
from src.orchestrator.runner import OrchestratorRunner


@pytest.fixture
def db(tmp_path):
    atlas = AtlasDB(str(tmp_path / "atlas.db"))
    atlas.init_db()
    yield atlas
    atlas.close()


class _ControlledLoop:
    """Test double that blocks on a condition until ``release()`` is called."""

    def __init__(self, db, ctx, initial_user_message=""):
        self.db = db
        self.ctx = ctx
        self.initial = initial_user_message
        self._release = threading.Event()
        self._started = threading.Event()
        self.outcome: RunOutcome | None = None

    def release(self):
        self._release.set()

    def started(self):
        return self._started.is_set()

    def run(self):
        self._started.set()
        self._release.wait(timeout=2)
        # Mark the underlying run completed so the runner cleans up.
        self.db.update_orchestrator_run(
            self.ctx.run_id, status="completed", final_state="completed", ended=True
        )
        self.outcome = RunOutcome(
            status="completed", final_state="completed", steps_taken=1
        )
        return self.outcome


class TestSubmitOrAttach:
    def test_first_call_starts_new_run(self, db):
        loops = []

        def factory(db_, ctx, initial):
            loop = _ControlledLoop(db_, ctx, initial)
            loops.append(loop)
            return loop

        runner = OrchestratorRunner(db, max_workers=2, loop_factory=factory)
        try:
            res = runner.submit_or_attach(
                user_id="u1",
                ip_id="ip1",
                ip_name="ipA",
                session_id="s1",
                message_text="run to green",
            )
            assert res.status == "started"
            assert res.run_id
            # Loop should be running, holding the slot.
            time.sleep(0.05)
            assert loops and loops[0].started()
            loops[0].release()
            runner.wait_for("u1", "ip1", timeout=2)
            run = db.get_orchestrator_run(res.run_id)
            assert run["status"] == "completed"
        finally:
            runner.shutdown(wait=True)

    def test_concurrent_call_is_appended(self, db):
        loops = []

        def factory(db_, ctx, initial):
            loop = _ControlledLoop(db_, ctx, initial)
            loops.append(loop)
            return loop

        runner = OrchestratorRunner(db, max_workers=2, loop_factory=factory)
        try:
            first = runner.submit_or_attach(
                user_id="u1",
                ip_id="ip1",
                ip_name="ipA",
                message_text="start",
            )
            time.sleep(0.05)
            second = runner.submit_or_attach(
                user_id="u1",
                ip_id="ip1",
                ip_name="ipA",
                message_text="and another thing",
            )
            assert second.status == "appended"
            assert second.run_id == first.run_id
            steps = db.list_orchestrator_steps(first.run_id)
            user_reply_steps = [s for s in steps if s["tool_name"] == "user_reply"]
            assert len(user_reply_steps) == 1
            assert user_reply_steps[0]["user_reply"] == "and another thing"
            loops[0].release()
            runner.wait_for("u1", "ip1", timeout=2)
        finally:
            runner.shutdown(wait=True)

    def test_different_ip_runs_independently(self, db):
        loops = []

        def factory(db_, ctx, initial):
            loop = _ControlledLoop(db_, ctx, initial)
            loops.append(loop)
            return loop

        runner = OrchestratorRunner(db, max_workers=3, loop_factory=factory)
        try:
            a = runner.submit_or_attach(
                user_id="u1", ip_id="ipA_id", ip_name="ipA", message_text="x"
            )
            b = runner.submit_or_attach(
                user_id="u1", ip_id="ipB_id", ip_name="ipB", message_text="y"
            )
            assert a.status == "started"
            assert b.status == "started"
            assert a.run_id != b.run_id
            time.sleep(0.05)
            for lp in loops:
                lp.release()
            runner.wait_for("u1", "ipA_id", timeout=2)
            runner.wait_for("u1", "ipB_id", timeout=2)
        finally:
            runner.shutdown(wait=True)

    def test_slot_freed_after_run_completes(self, db):
        loops = []

        def factory(db_, ctx, initial):
            loop = _ControlledLoop(db_, ctx, initial)
            loops.append(loop)
            return loop

        runner = OrchestratorRunner(db, max_workers=2, loop_factory=factory)
        try:
            first = runner.submit_or_attach(
                user_id="u1", ip_id="ip1", ip_name="ipA", message_text="first"
            )
            time.sleep(0.05)
            loops[0].release()
            runner.wait_for("u1", "ip1", timeout=2)
            # After completion, a new submit should start a fresh run.
            second = runner.submit_or_attach(
                user_id="u1", ip_id="ip1", ip_name="ipA", message_text="second"
            )
            assert second.status == "started"
            assert second.run_id != first.run_id
            time.sleep(0.05)
            loops[1].release()
            runner.wait_for("u1", "ip1", timeout=2)
        finally:
            runner.shutdown(wait=True)
