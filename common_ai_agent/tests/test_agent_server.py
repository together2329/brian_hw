"""
Integration tests for Common AI Agent ↔ Common AI Agent HTTP communication.

Tests cover:
1. Unit tests: agent_server endpoint handlers (no subprocess needed)
2. Unit tests: agent_client worker_call/status/result (mocked HTTP)
3. Integration test: 2 workers + 1 commander (subprocess, real HTTP)

Run:
    pytest tests/test_agent_server.py -v
    pytest tests/test_agent_server.py -v -k "unit"          # unit tests only (no LLM)
    pytest tests/test_agent_server.py -v -k "integration"   # full integration
"""

import json
import os
import sys
import time
import tempfile
import unittest
import threading
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "core"))
sys.path.insert(0, str(PROJECT_ROOT / "lib"))


# ============================================================
# Unit Tests — agent_server endpoint handlers
# ============================================================

class TestAgentServerUnit(unittest.TestCase):
    """Test agent_server.py internals without starting a real server."""

    def setUp(self):
        # Import server module
        from core import agent_server
        self.server_mod = agent_server
        # Clear any previous runs
        self.server_mod._runs.clear()

    def test_create_run_generates_run_id(self):
        entry = self.server_mod._create_run("test task", "test-model")
        self.assertTrue(entry.run_id.startswith("run_"))
        self.assertEqual(entry.task, "test task")
        self.assertEqual(entry.model, "test-model")
        self.assertEqual(entry.status, "pending")

    def test_get_run_returns_entry(self):
        entry = self.server_mod._create_run("test task")
        fetched = self.server_mod._get_run(entry.run_id)
        self.assertEqual(fetched.run_id, entry.run_id)

    def test_get_run_returns_none_for_unknown(self):
        fetched = self.server_mod._get_run("nonexistent")
        self.assertIsNone(fetched)

    def test_run_entry_log_append(self):
        entry = self.server_mod._create_run("test")
        entry.add_log("thought", "Need to read file")
        entry.add_log("action", "read_file(path='test.py')")
        self.assertEqual(len(entry.log), 2)
        self.assertEqual(entry.log[0]["type"], "thought")
        self.assertEqual(entry.log[1]["type"], "action")

    def test_run_entry_log_tail(self):
        entry = self.server_mod._create_run("test")
        for i in range(10):
            entry.add_log("info", f"entry {i}")
        tail = entry.get_log(tail=3)
        self.assertEqual(len(tail), 3)
        self.assertEqual(tail[0]["content"], "entry 7")

    def test_run_entry_log_since(self):
        entry = self.server_mod._create_run("test")
        for i in range(10):
            entry.add_log("info", f"entry {i}")
        since = entry.get_log(since=5)
        self.assertEqual(len(since), 5)
        self.assertEqual(since[0]["index"], 5)

    def test_create_app_returns_fastapi_app(self):
        try:
            from fastapi import FastAPI
        except ImportError:
            self.skipTest("fastapi not installed")
        app = self.server_mod.create_app()
        self.assertIsNotNone(app)

    def test_multiple_runs_dont_interfere(self):
        entry_a = self.server_mod._create_run("task A")
        entry_b = self.server_mod._create_run("task B")
        entry_a.add_log("info", "log for A")
        entry_b.add_log("info", "log for B")
        self.assertEqual(len(entry_a.log), 1)
        self.assertEqual(len(entry_b.log), 1)
        self.assertEqual(entry_a.log[0]["content"], "log for A")
        self.assertEqual(entry_b.log[0]["content"], "log for B")

    def test_run_entry_status_transitions(self):
        entry = self.server_mod._create_run("test")
        self.assertEqual(entry.status, "pending")
        entry.status = "running"
        entry.started_at = time.time()
        self.assertEqual(entry.status, "running")
        entry.status = "completed"
        entry.finished_at = time.time()
        self.assertEqual(entry.status, "completed")

    def test_producing_worker_counts_successful_write_observation(self):
        from core import react_loop

        entry = self.server_mod._create_run("write ssot")
        old_workflow = self.server_mod._SERVER_WORKFLOW
        old_persistence = self.server_mod._PERSISTENCE_ENABLED
        self.server_mod._SERVER_WORKFLOW = "ssot-gen"
        self.server_mod._PERSISTENCE_ENABLED = False

        def fake_run_react_agent_impl(*, messages, tracker, **_kwargs):
            tracker.current = 3
            return (
                messages
                + [
                    {
                        "role": "tool",
                        "name": "write_file",
                        "content": "Successfully wrote to 'demo_ip/yaml/demo_ip.ssot.yaml'.",
                    },
                    {"role": "assistant", "content": "Final Answer: [SSOT HANDOFF] done"},
                ],
                "normal",
            )

        try:
            with patch.object(react_loop, "run_react_agent_impl", side_effect=fake_run_react_agent_impl):
                self.server_mod._run_react_task(entry, "write ssot", model="test-model")
        finally:
            self.server_mod._SERVER_WORKFLOW = old_workflow
            self.server_mod._PERSISTENCE_ENABLED = old_persistence

        self.assertEqual(entry.status, "completed", entry.result)
        self.assertIn("demo_ip/yaml/demo_ip.ssot.yaml", entry.result["files_modified"])

    def test_worker_reports_final_answer_turn_as_iteration(self):
        from core import react_loop

        entry = self.server_mod._create_run("answer directly")
        old_workflow = self.server_mod._SERVER_WORKFLOW
        old_persistence = self.server_mod._PERSISTENCE_ENABLED
        self.server_mod._SERVER_WORKFLOW = ""
        self.server_mod._PERSISTENCE_ENABLED = False

        def fake_run_react_agent_impl(*, messages, tracker, **_kwargs):
            # Completion breaks before react_loop increments tracker.current.
            self.assertEqual(tracker.current, 0)
            return (
                messages
                + [
                    {"role": "assistant", "content": "Final Answer: direct done"},
                ],
                "normal",
            )

        try:
            with patch.object(react_loop, "run_react_agent_impl", side_effect=fake_run_react_agent_impl):
                self.server_mod._run_react_task(entry, "answer directly", model="test-model")
        finally:
            self.server_mod._SERVER_WORKFLOW = old_workflow
            self.server_mod._PERSISTENCE_ENABLED = old_persistence

        self.assertEqual(entry.status, "completed", entry.result)
        self.assertEqual(entry.result["iterations"], 1)

    def test_extract_direct_slash_commands_from_stage_driver_prompt(self):
        task = (
            "run /ssot-cycle-model demo_ip and /ssot-dual-fcov demo_ip; "
            "generate the SSOT-derived cycle model"
        )
        commands = self.server_mod._extract_direct_slash_commands(task)
        self.assertEqual(commands, ["/ssot-cycle-model demo_ip", "/ssot-dual-fcov demo_ip"])

    def test_slash_command_failure_detects_stage_blockers(self):
        self.assertTrue(
            self.server_mod._slash_command_failed("[RTL BLOCKED] rtl-gen waiting for LLM-authored RTL")
        )
        self.assertTrue(self.server_mod._slash_command_failed("[sim] FAIL missing results.xml"))
        self.assertFalse(self.server_mod._slash_command_failed('<testsuite failures="0"></testsuite>'))

    def test_direct_ssot_rtl_llm_blocker_continues_react_loop(self):
        from core.slash_commands import get_registry

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "demo_ip").mkdir()
            registry = get_registry()
            previous = registry.commands.get("ssot-rtl")

            def blocker_cmd(args: str) -> str:
                return (
                    "[RTL BLOCKED]\n"
                    "LLM_RTL_IMPLEMENTATION_REQUIRED\n"
                    "LLM-authored RTL evidence is missing or stale."
                )

            registry.register("ssot-rtl", blocker_cmd, "unit blocker command")
            entry = self.server_mod._create_run("run /ssot-rtl demo_ip")
            entry.status = "running"
            try:
                closed_run, output = self.server_mod._execute_direct_slash_commands(
                    entry,
                    ["/ssot-rtl demo_ip"],
                    project_root=str(root),
                    ip="demo_ip",
                )
            finally:
                if previous is not None:
                    registry.commands["ssot-rtl"] = previous
                else:
                    registry.unregister("ssot-rtl")

        self.assertFalse(closed_run)
        self.assertEqual(entry.status, "running")
        self.assertIsNone(entry.result)
        self.assertIn("LLM_RTL_IMPLEMENTATION_REQUIRED", output)

    def test_direct_ssot_rtl_repair_gate_continues_react_loop(self):
        from core.slash_commands import get_registry

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "demo_ip").mkdir()
            registry = get_registry()
            previous = registry.commands.get("ssot-rtl")

            def repair_cmd(args: str) -> str:
                return (
                    "[RTL RESULT] FAIL - LLM-authored RTL needs rtl-gen repair\n"
                    "open_required_todos=4\n"
                    "static_missing=1\n"
                    "next: queued rtl-gen repair with compile/lint diagnostics as evidence."
                )

            registry.register("ssot-rtl", repair_cmd, "unit repair command")
            entry = self.server_mod._create_run("run /ssot-rtl demo_ip")
            entry.status = "running"
            try:
                closed_run, output = self.server_mod._execute_direct_slash_commands(
                    entry,
                    ["/ssot-rtl demo_ip"],
                    project_root=str(root),
                    ip="demo_ip",
                )
            finally:
                if previous is not None:
                    registry.commands["ssot-rtl"] = previous
                else:
                    registry.unregister("ssot-rtl")

        self.assertFalse(closed_run)
        self.assertEqual(entry.status, "running")
        self.assertIsNone(entry.result)
        self.assertIn("LLM-authored RTL needs rtl-gen repair", output)

    def test_direct_slash_command_path_records_modified_files(self):
        from core.slash_commands import get_registry

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "demo_ip").mkdir()
            old_cwd = os.getcwd()
            os.chdir(root)
            registry = get_registry()

            def touch_cmd(args: str) -> str:
                ip = args.strip()
                out = root / ip / "model" / "touch.json"
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text('{"ok": true}\n', encoding="utf-8")
                return f"[touch] wrote {out.relative_to(root)}"

            registry.register("unit-touch", touch_cmd, "unit test command")
            entry = self.server_mod._create_run("run /unit-touch demo_ip")
            try:
                self.server_mod._execute_direct_slash_commands(
                    entry,
                    ["/unit-touch demo_ip"],
                    project_root=str(root),
                    ip="demo_ip",
                )
            finally:
                registry.unregister("unit-touch")
                os.chdir(old_cwd)

        self.assertEqual(entry.status, "completed", entry.result)
        self.assertIn("demo_ip/model/touch.json", entry.result["files_modified"])


# ============================================================
# Unit Tests — agent_client worker_call (mocked HTTP)
# ============================================================

class TestAgentClientUnit(unittest.TestCase):
    """Test agent_client.py with mocked HTTP calls."""

    def test_worker_call_handles_unreachable_worker(self):
        """worker_call returns error dict when worker is unreachable."""
        from core.agent_client import worker_call
        result = worker_call(
            worker="http://localhost:19999",  # nobody listening here
            task="test task",
            timeout=3,
            poll_interval=0.5,
            show_log=False,
        )
        self.assertEqual(result["status"], "error")
        self.assertIn("Failed to contact Worker", result["error"])

    def test_worker_status_handles_unreachable(self):
        """worker_status returns error dict when worker is unreachable."""
        from core.agent_client import worker_status
        result = worker_status(worker="http://localhost:19999", run_id="test")
        self.assertIn("error", result)

    def test_worker_result_handles_unreachable(self):
        """worker_result returns error dict when worker is unreachable."""
        from core.agent_client import worker_result
        result = worker_result(worker="http://localhost:19999", run_id="test")
        self.assertIn("error", result)

    def test_worker_call_with_mocked_server(self):
        """Test worker_call flow with mocked HTTP responses."""
        import core.agent_client as client_mod
        from core.agent_client import worker_call

        call_count = [0]

        def mock_urlopen(req, timeout=10):
            """Mock urllib.request.urlopen to simulate worker responses."""
            url = req.full_url if hasattr(req, 'full_url') else str(req)
            call_count[0] += 1

            # POST /run → return run_id
            if url.endswith("/run"):
                body = json.dumps({"run_id": "run_test123", "status": "pending"})
                resp = MagicMock()
                resp.read.return_value = body.encode()
                resp.__enter__ = lambda s: s
                resp.__exit__ = MagicMock(return_value=False)
                return resp

            # GET /status → first polls = running, later = completed
            if "/status/" in url:
                status_val = "running" if call_count[0] < 5 else "completed"
                body = json.dumps({
                    "run_id": "run_test123",
                    "status": status_val,
                    "log_entries": 5,
                    "elapsed_s": 3.0,
                })
                resp = MagicMock()
                resp.read.return_value = body.encode()
                resp.__enter__ = lambda s: s
                resp.__exit__ = MagicMock(return_value=False)
                return resp

            # GET /log → empty for now
            if "/log/" in url:
                body = json.dumps({"entries": [], "total_entries": 0})
                resp = MagicMock()
                resp.read.return_value = body.encode()
                resp.__enter__ = lambda s: s
                resp.__exit__ = MagicMock(return_value=False)
                return resp

            # GET /result → return final result
            if "/result/" in url:
                body = json.dumps({
                    "run_id": "run_test123",
                    "status": "completed",
                    "result": "hello.txt created",
                    "files_modified": ["hello.txt"],
                    "files_examined": [],
                    "iterations": 3,
                })
                resp = MagicMock()
                resp.read.return_value = body.encode()
                resp.__enter__ = lambda s: s
                resp.__exit__ = MagicMock(return_value=False)
                return resp

            raise Exception(f"Unexpected URL: {url}")

        # Patch at the module level where urlopen is used
        with patch("core.agent_client.urllib.request.urlopen", side_effect=mock_urlopen):
            result = worker_call(
                worker="http://localhost:8001",
                task="Write hello.txt",
                timeout=10,
                poll_interval=0.1,
                show_log=False,
            )

        self.assertEqual(result["status"], "completed", f"Got: {result}")
        self.assertEqual(result["result"], "hello.txt created")
        self.assertIn("hello.txt", result["files_modified"])


# ============================================================
# Integration Tests — Real HTTP server + client
# ============================================================

class TestAgentServerIntegration(unittest.TestCase):
    """
    Integration tests using a real FastAPI server in a background thread.
    Tests the full HTTP round-trip: client → server → response.
    """

    @classmethod
    def setUpClass(cls):
        """Start a test server in a background thread."""
        try:
            import uvicorn
            from core.agent_server import create_app
        except ImportError:
            raise unittest.SkipTest("fastapi/uvicorn not installed")

        cls.port = 18765  # Use a high port to avoid conflicts
        cls.base_url = f"http://localhost:{cls.port}"
        cls._server_thread = None
        cls._server_ready = threading.Event()

        def _run_server():
            app = create_app()
            config = uvicorn.Config(app, host="127.0.0.1", port=cls.port, log_level="error")
            server = uvicorn.Server(config)
            cls._server = server
            cls._server_ready.set()
            server.run()

        cls._server_thread = threading.Thread(target=_run_server, daemon=True)
        cls._server_thread.start()
        cls._server_ready.wait(timeout=5)

        # Give uvicorn a moment to bind the port
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        """Shut down the test server."""
        if hasattr(cls, '_server') and cls._server:
            cls._server.should_exit = True
        if cls._server_thread:
            cls._server_thread.join(timeout=5)

    def _get(self, path: str) -> dict:
        req = urllib.request.Request(f"{self.base_url}{path}")
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")
            return json.loads(body) if body else {"error": str(e)}

    def _post(self, path: str, data: dict) -> dict:
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")
            return json.loads(body) if body else {"error": str(e)}

    def test_health_endpoint(self):
        """GET /health returns ok."""
        result = self._get("/health")
        self.assertEqual(result["status"], "ok")

    def test_run_requires_task(self):
        """POST /run without task returns 400 error."""
        result = self._post("/run", {})
        self.assertIn("detail", result)  # FastAPI HTTPException has 'detail'

    def test_run_async_returns_run_id(self):
        """POST /run (sync=false) returns run_id immediately."""
        result = self._post("/run", {
            "task": "Write hello.txt with content 'hello world'",
            "sync": False,
        })
        self.assertIn("run_id", result)
        self.assertEqual(result["status"], "pending")

    def test_status_of_unknown_run_returns_404(self):
        """GET /status/unknown returns 404."""
        result = self._get("/status/run_nonexistent")
        self.assertIn("detail", result)

    def test_log_of_unknown_run_returns_404(self):
        """GET /log/unknown returns 404."""
        result = self._get("/log/run_nonexistent")
        self.assertIn("detail", result)

    def test_result_of_unknown_run_returns_404(self):
        """GET /result/unknown returns 404."""
        result = self._get("/result/run_nonexistent")
        self.assertIn("detail", result)

    def test_async_run_flow_status_then_result(self):
        """
        Full async flow: POST /run → poll /status → get /result.
        NOTE: The worker may not complete if no LLM API is configured,
        so we test the status transitions, not the final result content.
        """
        result = self._post("/run", {
            "task": "Simply respond with 'Hello World' as your final answer. Do not call any tools.",
            "sync": False,
        })
        self.assertIn("run_id", result)
        run_id = result["run_id"]

        # Poll status a few times
        for _ in range(3):
            status = self._get(f"/status/{run_id}")
            self.assertIn("status", status)
            self.assertIn(status["status"], ("pending", "running", "completed", "error"))
            if status["status"] in ("completed", "error"):
                break
            time.sleep(0.5)

        # Get result (may still be running if LLM not configured)
        result = self._get(f"/result/{run_id}")
        self.assertIn("run_id", result)
        self.assertIn("status", result)

    def test_log_endpoint_returns_entries(self):
        """GET /log/{run_id} returns log entries after starting a run."""
        result = self._post("/run", {
            "task": "Test log endpoint",
            "sync": False,
        })
        run_id = result["run_id"]

        # Wait a moment for the log to populate
        time.sleep(1)

        log = self._get(f"/log/{run_id}")
        self.assertIn("entries", log)
        self.assertIn("total_entries", log)
        self.assertIn("run_id", log)

    def test_log_tail_param(self):
        """GET /log/{run_id}?tail=1 returns at most 1 entry."""
        result = self._post("/run", {
            "task": "Test log tail",
            "sync": False,
        })
        run_id = result["run_id"]
        time.sleep(1)

        log = self._get(f"/log/{run_id}?tail=1")
        self.assertIn("entries", log)
        self.assertLessEqual(len(log["entries"]), 1)


# ============================================================
# End-to-End Test — Commander sends tasks to 2 Workers
# ============================================================

class TestCommanderWorkerE2E(unittest.TestCase):
    """
    Full end-to-end test: Commander dispatches tasks to 2 workers
    using worker_call() and collects results.

    NOTE: This test requires:
    1. fastapi + uvicorn installed
    2. A working LLM API configured (LLM_BASE_URL + LLM_API_KEY)
    
    Skips automatically if dependencies are missing.
    """

    @classmethod
    def setUpClass(cls):
        try:
            import uvicorn
            from core.agent_server import create_app
        except ImportError:
            raise unittest.SkipTest("fastapi/uvicorn not installed")

        cls.ports = [18771, 18772]
        cls.base_urls = [f"http://localhost:{p}" for p in cls.ports]
        cls._servers = []
        cls._threads = []

        for port in cls.ports:
            ready = threading.Event()

            def _run(p=port, r=ready):
                app = create_app()
                cfg = uvicorn.Config(app, host="127.0.0.1", port=p, log_level="error")
                server = uvicorn.Server(cfg)
                cls._servers.append(server)
                r.set()
                server.run()

            t = threading.Thread(target=_run, daemon=True)
            t.start()
            ready.wait(timeout=5)
            cls._threads.append(t)

        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        for server in cls._servers:
            server.should_exit = True
        for t in cls._threads:
            t.join(timeout=5)

    def test_commander_dispatches_to_two_workers(self):
        """
        Commander sends simple tasks to Worker A and Worker B,
        collects results via worker_status and worker_result.
        """
        from core.agent_client import worker_call

        # Task A: respond without tools
        result_a = worker_call(
            worker=self.base_urls[0],
            task="Respond with exactly 'HELLO_FROM_WORKER_A' as your final answer. Do not call any tools.",
            timeout=60,
            poll_interval=1.0,
            show_log=True,
        )

        # Task B: respond without tools
        result_b = worker_call(
            worker=self.base_urls[1],
            task="Respond with exactly 'HELLO_FROM_WORKER_B' as your final answer. Do not call any tools.",
            timeout=60,
            poll_interval=1.0,
            show_log=True,
        )

        # Verify both completed (or errored gracefully)
        self.assertIn(result_a["status"], ("completed", "error"))
        self.assertIn(result_b["status"], ("completed", "error"))

        # If LLM is configured and returned non-empty result, check content
        if result_a["status"] == "completed":
            result_a_text = result_a.get("result", "")
            if result_a_text.strip():
                self.assertIn("HELLO_FROM_WORKER_A", result_a_text)
            else:
                self.skipTest(f"Worker A returned empty result (LLM flake): {result_a}")
        if result_b["status"] == "completed":
            result_b_text = result_b.get("result", "")
            if result_b_text.strip():
                self.assertIn("HELLO_FROM_WORKER_B", result_b_text)
            else:
                self.skipTest(f"Worker B returned empty result (LLM flake): {result_b}")

    def test_commander_uses_worker_status(self):
        """Test that worker_status can poll a running task."""
        from core.agent_client import worker_status

        # Start a task via direct HTTP POST
        url = f"{self.base_urls[0]}/run"
        body = json.dumps({"task": "Count from 1 to 5", "sync": False}).encode()
        req = urllib.request.Request(
            url, data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            run_resp = json.loads(resp.read().decode("utf-8"))

        run_id = run_resp["run_id"]

        # Poll status
        status = worker_status(worker=self.base_urls[0], run_id=run_id)
        self.assertIn("status", status)
        self.assertIn(status["status"], ("pending", "running", "completed", "error"))


if __name__ == "__main__":
    unittest.main()
