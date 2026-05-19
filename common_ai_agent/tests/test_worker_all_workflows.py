"""Regression tests for the `--all-workflows` workflow-agnostic worker.

Restores the May-12 (c59617fb4) single-main-loop pattern: ONE --serve worker
process accepts /run dispatches for any workflow, and each dispatch switches
the active workspace via _setup_workspace() before the next main-loop
iteration runs.

Verifies:
  - `/health` advertises `all_workflows: true` and omits the `workflow`
    binding when the worker is started in any-workflow mode.
  - `/run` accepts back-to-back dispatches with *different* workflows,
    instead of returning HTTP 403 the way a workflow-bound worker would.
  - Each dispatch calls `src.main._setup_workspace(workflow)` and updates
    `os.environ['ATLAS_WORKFLOW']` so the main loop transitions to the
    requested workflow's context.
  - The 403 mismatch gate stays intact for workers that were *not* started
    with `--all-workflows` (no regression on the existing F3 guard).
"""

from __future__ import annotations

import os
import unittest


class TestWorkerAllWorkflows(unittest.TestCase):
    def setUp(self):
        try:
            from fastapi.testclient import TestClient  # noqa: F401
            from core import agent_server as _srv
        except Exception as exc:  # pragma: no cover
            self.skipTest(f"fastapi missing: {exc}")
        from core import agent_server as srv

        self._srv = srv
        self._saved_workflow = srv._SERVER_WORKFLOW
        self._saved_any = srv._SERVER_ACCEPT_ANY_WORKFLOW
        self._saved_run_react_task = srv._run_react_task
        self._saved_atlas_workflow = os.environ.get("ATLAS_WORKFLOW")
        self._saved_active_workspace = os.environ.get("ACTIVE_WORKSPACE")

        self._setup_workspace_calls = []

        def _fake_run_react_task(entry, *_args, **_kwargs):
            import time

            entry.status = "completed"
            entry.started_at = entry.started_at or time.time()
            entry.finished_at = time.time()
            entry.result = {"run_id": entry.run_id, "status": "completed"}

        srv._run_react_task = _fake_run_react_task

        # Stub _setup_workspace on src.main so we don't actually load
        # workflow files in the test process.
        try:
            import src.main as _main_mod
        except Exception:  # pragma: no cover
            self.skipTest("src.main not importable")
        self._main_mod = _main_mod
        self._saved_setup_workspace = getattr(_main_mod, "_setup_workspace", None)

        def _fake_setup_workspace(name: str) -> None:
            self._setup_workspace_calls.append(name)

        _main_mod._setup_workspace = _fake_setup_workspace

    def tearDown(self):
        self._srv._SERVER_WORKFLOW = self._saved_workflow
        self._srv._SERVER_ACCEPT_ANY_WORKFLOW = self._saved_any
        self._srv._run_react_task = self._saved_run_react_task
        with self._srv._runs_lock:
            self._srv._runs.clear()
        if self._saved_setup_workspace is not None:
            self._main_mod._setup_workspace = self._saved_setup_workspace
        if self._saved_atlas_workflow is None:
            os.environ.pop("ATLAS_WORKFLOW", None)
        else:
            os.environ["ATLAS_WORKFLOW"] = self._saved_atlas_workflow
        if self._saved_active_workspace is None:
            os.environ.pop("ACTIVE_WORKSPACE", None)
        else:
            os.environ["ACTIVE_WORKSPACE"] = self._saved_active_workspace

    def _client(self, *, all_workflows: bool, workflow: str = ""):
        from fastapi.testclient import TestClient

        self._srv._SERVER_ACCEPT_ANY_WORKFLOW = bool(all_workflows)
        # Same precedence as serve(): --all-workflows clears the binding.
        self._srv._SERVER_WORKFLOW = "" if all_workflows else workflow
        app = self._srv.create_app()
        return TestClient(app)

    # ── /health ───────────────────────────────────────────────────────────

    def test_health_advertises_all_workflows_mode(self):
        client = self._client(all_workflows=True)
        resp = client.get("/health")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertTrue(body.get("all_workflows"))
        self.assertNotIn("workflow", body)  # no per-workflow binding

    def test_health_omits_all_workflows_when_off(self):
        client = self._client(all_workflows=False, workflow="rtl-gen")
        body = client.get("/health").json()
        self.assertNotIn("all_workflows", body)
        self.assertEqual(body.get("workflow"), "rtl-gen")

    # ── /run gate behavior ────────────────────────────────────────────────

    def test_run_accepts_any_workflow_when_all_workflows_on(self):
        """Sequential dispatches with different workflows succeed and each
        invokes _setup_workspace() with the requested workflow."""
        client = self._client(all_workflows=True)
        for wf in ("ssot-gen", "rtl-gen", "tb-gen"):
            resp = client.post(
                "/run",
                json={"task": "dummy", "workflow": wf, "sync": True},
            )
            self.assertEqual(
                resp.status_code, 200,
                msg=f"workflow={wf} unexpectedly rejected: "
                    f"{resp.status_code} {resp.text}")
            self.assertEqual(os.environ.get("ATLAS_WORKFLOW"), wf)
            self.assertEqual(os.environ.get("ACTIVE_WORKSPACE"), wf)

        self.assertEqual(
            self._setup_workspace_calls,
            ["ssot-gen", "rtl-gen", "tb-gen"],
            msg="each dispatch must call _setup_workspace(workflow) in order",
        )

    def test_run_back_to_back_different_workflows_state_clean(self):
        """After two dispatches with different workflows, env reflects the
        second one — no stale state bleeds through from the first."""
        client = self._client(all_workflows=True)
        r1 = client.post(
            "/run",
            json={"task": "first", "workflow": "ssot-gen", "sync": True},
        )
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(os.environ.get("ATLAS_WORKFLOW"), "ssot-gen")

        r2 = client.post(
            "/run",
            json={"task": "second", "workflow": "rtl-gen", "sync": True},
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(os.environ.get("ATLAS_WORKFLOW"), "rtl-gen")
        self.assertEqual(self._setup_workspace_calls, ["ssot-gen", "rtl-gen"])

    def test_run_regression_workflow_guard_still_fires_without_flag(self):
        """Without --all-workflows the existing F3 guard still rejects
        mismatched workflows with 403."""
        client = self._client(all_workflows=False, workflow="rtl-gen")
        resp = client.post(
            "/run",
            json={"task": "dummy", "workflow": "tb-gen", "sync": True},
        )
        self.assertEqual(resp.status_code, 403)
        # _setup_workspace must NOT be called in non-any-workflow mode.
        self.assertEqual(self._setup_workspace_calls, [])

    def test_run_omitted_workflow_skips_workspace_setup(self):
        """An /all-workflows worker that receives a dispatch with an empty
        workflow field should not crash and should not call _setup_workspace
        (no workflow to switch to)."""
        client = self._client(all_workflows=True)
        resp = client.post(
            "/run",
            json={"task": "dummy", "sync": True},
        )
        self.assertNotEqual(resp.status_code, 403)
        self.assertEqual(self._setup_workspace_calls, [])


if __name__ == "__main__":
    unittest.main()
