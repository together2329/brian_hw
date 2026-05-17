"""Regression tests for the worker `/run` workflow guard.

Closes the multi-user-worker-conflicts F3 ("wrong-workflow acceptance") and
verifies that:

  - A worker started with `--workflow=rtl-gen` exposes its binding via
    `/health` so the dispatcher can verify before posting `/run`.
  - A `/run` whose request body asks for a different workflow is rejected
    with HTTP 403.
  - A `/run` whose request body omits `workflow` (or matches) is accepted.
"""

from __future__ import annotations

import unittest


class TestWorkerWorkflowGuard(unittest.TestCase):
    def setUp(self):
        try:
            from fastapi.testclient import TestClient  # noqa: F401
            from core import agent_server as _srv
        except Exception as exc:  # pragma: no cover
            self.skipTest(f"fastapi missing: {exc}")
        from core import agent_server as srv

        self._srv = srv
        self._saved_workflow = srv._SERVER_WORKFLOW

    def tearDown(self):
        self._srv._SERVER_WORKFLOW = self._saved_workflow

    def _client_with_binding(self, workflow: str):
        from fastapi.testclient import TestClient

        self._srv._SERVER_WORKFLOW = workflow
        app = self._srv.create_app()
        return TestClient(app)

    def test_health_exposes_workflow_binding(self):
        client = self._client_with_binding("rtl-gen")
        resp = client.get("/health")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body.get("workflow"), "rtl-gen")
        self.assertEqual(body.get("status"), "ok")

    def test_health_omits_workflow_when_unbound(self):
        client = self._client_with_binding("")
        resp = client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn("workflow", resp.json())

    def test_run_rejects_mismatched_workflow(self):
        client = self._client_with_binding("rtl-gen")
        resp = client.post(
            "/run",
            json={"task": "do something", "workflow": "tb-gen", "sync": False},
        )
        self.assertEqual(resp.status_code, 403)
        self.assertIn("rtl-gen", resp.json().get("detail", ""))
        self.assertIn("tb-gen", resp.json().get("detail", ""))

    def test_run_accepts_matching_workflow(self):
        client = self._client_with_binding("rtl-gen")
        resp = client.post(
            "/run",
            json={
                "task": "do something",
                "workflow": "rtl-gen",
                "sync": False,
            },
        )
        # The request body is otherwise legal; the run starts (or is queued)
        # but is not 403. We accept any non-403 status as evidence the guard
        # did not fire.
        self.assertNotEqual(resp.status_code, 403)

    def test_run_accepts_empty_workflow_when_bound(self):
        client = self._client_with_binding("rtl-gen")
        resp = client.post(
            "/run",
            json={"task": "do something", "sync": False},
        )
        # Empty/missing `workflow` is intentionally not rejected so existing
        # un-namespaced callers keep working; the guard fires only when the
        # caller explicitly asks for a different workflow.
        self.assertNotEqual(resp.status_code, 403)


if __name__ == "__main__":
    unittest.main()
