"""
Integration & Unit Tests for Agent Server / Client

Tests:
  1. Unit tests: FastAPI endpoint handlers (health, run, status, result, log)
  2. Integration test: Commander dispatches tasks to 2 workers concurrently

Usage:
    pytest tests/test_agent_server.py -v
    # Or skip real-LLM tests:
    AGENT_SERVER_TEST_NO_LLM=1 pytest tests/test_agent_server.py -v
"""

import os
import sys
import json
import time
import threading
import unittest
import subprocess
import tempfile
import shutil
import http.server
import socketserver
from pathlib import Path
from contextlib import contextmanager

import pytest

# ── Path setup ───────────────────────────────────────────────────────────
_tests_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_tests_dir)
sys.path.insert(0, os.path.join(_project_root, 'src'))
sys.path.insert(0, _project_root)
sys.path.insert(0, os.path.join(_project_root, 'core'))


# ── Helpers ──────────────────────────────────────────────────────────────

def _has_api_key() -> bool:
    """Check if an LLM API key is configured (needed for real integration tests)."""
    try:
        import config
        return bool(getattr(config, 'API_KEY', ''))
    except Exception:
        return False


def _skip_if_no_api_key():
    """Return pytest skip marker if no API key, else return empty decorator."""
    if not _has_api_key() or os.environ.get('AGENT_SERVER_TEST_NO_LLM'):
        return pytest.mark.skip(reason="No LLM API key configured")
    return pytest.mark.skipif(False, reason="")


# ── Unit Tests: agent_server HTTP endpoints (FastAPI TestClient) ────────

class TestAgentServerEndpoints(unittest.TestCase):
    """Test agent_server FastAPI app endpoints in isolation."""

    @classmethod
    def setUpClass(cls):
        """Create the FastAPI test client once."""
        from core.agent_server import create_app, _runs, _runs_lock

        # Save existing global state so we can restore it later
        cls._original_runs = dict(_runs)
        cls._original_lock = _runs_lock
        cls.app = create_app()

    def setUp(self):
        """Clear the in-memory run store before each test."""
        from core.agent_server import _runs
        with _runs_lock if hasattr(self, '_runs_lock') else threading.Lock():
            _runs.clear()

    def test_health(self):
        """GET /health returns ok."""
        from fastapi.testclient import TestClient
        client = TestClient(self.app)
        resp = client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("runs", data)

    def test_run_creates_entry(self):
        """POST /run creates a run and returns run_id."""
        from fastapi.testclient import TestClient
        client = TestClient(self.app)
        resp = client.post("/run", json={"task": "Say hello"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("run_id", data)
        self.assertEqual(data["status"], "pending")
        # Verify it's in the store
        from core.agent_server import _get_run
        entry = _get_run(data["run_id"])
        self.assertIsNotNone(entry)
        self.assertEqual(entry.task, "Say hello")

    def test_run_missing_task(self):
        """POST /run without 'task' returns 400."""
        from fastapi.testclient import TestClient
        client = TestClient(self.app)
        resp = client.post("/run", json={"model": "gpt-5"})
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertIn("detail", data)

    def test_status_nonexistent(self):
        """GET /status/{id} for unknown run returns 404."""
        from fastapi.testclient import TestClient
        client = TestClient(self.app)
        resp = client.get("/status/nonexistent")
        self.assertEqual(resp.status_code, 404)

    def test_status_running(self):
        """GET /status/{id} for a known run returns status info."""
        from fastapi.testclient import TestClient
        from core.agent_server import _create_run
        entry = _create_run("Test task")
        entry.status = "running"
        entry.started_at = time.time()

        client = TestClient(self.app)
        resp = client.get(f"/status/{entry.run_id}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["run_id"], entry.run_id)
        self.assertEqual(data["status"], "running")
        self.assertIn("elapsed_s", data)

    def test_result_incomplete(self):
        """GET /result/{id} for running task returns status but no result."""
        from fastapi.testclient import TestClient
        from core.agent_server import _create_run
        entry = _create_run("Test task")
        entry.status = "running"

        client = TestClient(self.app)
        resp = client.get(f"/result/{entry.run_id}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "running")
        self.assertIn("message", data)

    def test_result_completed(self):
        """GET /result/{id} for completed task returns full result."""
        from fastapi.testclient import TestClient
        from core.agent_server import _create_run
        entry = _create_run("Test task")
        entry.status = "completed"
        entry.result = {
            "run_id": entry.run_id,
            "status": "completed",
            "result": "All done!",
            "files_modified": ["a.txt"],
            "files_examined": ["b.txt"],
            "iterations": 3,
        }

        client = TestClient(self.app)
        resp = client.get(f"/result/{entry.run_id}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "completed")
        self.assertEqual(data["result"], "All done!")
        self.assertEqual(data["files_modified"], ["a.txt"])
        self.assertEqual(data["iterations"], 3)

    def test_log_entries_returned(self):
        """GET /log/{id} returns log entries."""
        from fastapi.testclient import TestClient
        from core.agent_server import _create_run
        entry = _create_run("Test task")
        entry.add_log("task", "Write hello.txt")
        entry.add_log("thought", "I should create a file")
        entry.add_log("action", "write_file('hello.txt', 'hello')")
        entry.add_log("observation", "Successfully wrote file")

        client = TestClient(self.app)
        resp = client.get(f"/log/{entry.run_id}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["total_entries"], 4)
        self.assertEqual(len(data["entries"]), 4)
        self.assertEqual(data["entries"][0]["type"], "task")

    def test_log_tail_param(self):
        """GET /log/{id}?tail=2 returns only last 2 entries."""
        from fastapi.testclient import TestClient
        from core.agent_server import _create_run
        entry = _create_run("Test")
        for i in range(5):
            entry.add_log("thought", f"Thought {i}")

        client = TestClient(self.app)
        resp = client.get(f"/log/{entry.run_id}?tail=2")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data["entries"]), 2)
        self.assertEqual(data["entries"][0]["content"], "Thought 3")
        self.assertEqual(data["entries"][1]["content"], "Thought 4")

    def test_log_since_param(self):
        """GET /log/{id}?since=2 returns entries from index 2 onward."""
        from fastapi.testclient import TestClient
        from core.agent_server import _create_run
        entry = _create_run("Test")
        for i in range(5):
            entry.add_log("thought", f"Thought {i}")

        client = TestClient(self.app)
        resp = client.get(f"/log/{entry.run_id}?since=2")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data["entries"]), 3)  # indices 2, 3, 4
        self.assertEqual(data["entries"][0]["content"], "Thought 2")

    def test_health_counts_runs(self):
        """GET /health shows run count."""
        from fastapi.testclient import TestClient
        from core.agent_server import _create_run
        _create_run("Task A")
        _create_run("Task B")

        client = TestClient(self.app)
        resp = client.get("/health")
        data = resp.json()
        self.assertGreaterEqual(data["runs"], 2)


# ── Unit Tests: agent_client tool functions (no server needed) ──────────

class TestAgentClient(unittest.TestCase):
    """Test agent_client.py tool functions."""

    def _start_mock_server(self, handler_class):
        """
        Start a tiny HTTP server in a thread to test agent_client against.
        Returns (port, stop_fn, thread).
        """
        httpd = socketserver.TCPServer(("127.0.0.1", 0), handler_class)
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        return port, httpd.shutdown, thread

    def test_worker_status_makes_get(self):
        """worker_status makes GET /status/{run_id} and returns parsed JSON."""
        class MockHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if "/status/" in self.path:
                    body = json.dumps({"status": "completed", "elapsed_s": 5.2})
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(body.encode())
                else:
                    self.send_response(404)
                    self.end_headers()

        port, stop_fn, thread = self._start_mock_server(MockHandler)
        try:
            from core.agent_client import worker_status
            result = worker_status(f"http://127.0.0.1:{port}", "test123")
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["elapsed_s"], 5.2)
        finally:
            stop_fn()

    def test_worker_result_makes_get(self):
        """worker_result makes GET /result/{run_id} and returns parsed JSON."""
        class MockHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if "/result/" in self.path:
                    body = json.dumps({
                        "status": "completed",
                        "result": "Done!",
                        "files_modified": ["hello.txt"],
                        "iterations": 3,
                    })
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(body.encode())
                else:
                    self.send_response(404)
                    self.end_headers()

        port, stop_fn, thread = self._start_mock_server(MockHandler)
        try:
            from core.agent_client import worker_result
            result = worker_result(f"http://127.0.0.1:{port}", "test456")
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["files_modified"], ["hello.txt"])
            self.assertEqual(result["iterations"], 3)
        finally:
            stop_fn()

    def test_worker_call_blocks_and_returns(self):
        """worker_call POSTs /run, polls /status, returns /result."""
        call_count = [0]  # mutable counter for closures

        class MockHandler(http.server.BaseHTTPRequestHandler):
            def do_POST(self_):
                if "/run" in self_.path:
                    body = json.dumps({"run_id": "mock-run-abc"})
                    self_.send_response(200)
                    self_.send_header("Content-Type", "application/json")
                    self_.end_headers()
                    self_.wfile.write(body.encode())

            def do_GET(self_):
                if "/status/" in self_.path:
                    call_count[0] += 1
                    # Return "running" for first 2 polls, then "completed"
                    if call_count[0] <= 2:
                        body = json.dumps({"status": "running", "elapsed_s": 2})
                    else:
                        body = json.dumps({"status": "completed", "elapsed_s": 6})
                    self_.send_response(200)
                    self_.send_header("Content-Type", "application/json")
                    self_.end_headers()
                    self_.wfile.write(body.encode())
                elif "/result/" in self_.path:
                    body = json.dumps({
                        "status": "completed",
                        "result": "All done!",
                        "files_modified": ["a.txt"],
                        "iterations": 2,
                    })
                    self_.send_response(200)
                    self_.send_header("Content-Type", "application/json")
                    self_.end_headers()
                    self_.wfile.write(body.encode())
                else:
                    self_.send_response(404)
                    self_.end_headers()

        port, stop_fn, thread = self._start_mock_server(MockHandler)
        try:
            from core.agent_client import worker_call
            result = worker_call(
                f"http://127.0.0.1:{port}",
                task="Test task",
                show_log=False,
            )
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["result"], "All done!")
            self.assertEqual(result["files_modified"], ["a.txt"])
            # Should have polled at least 3 times
            self.assertGreaterEqual(call_count[0], 3)
        finally:
            stop_fn()

    def test_worker_call_unreachable_returns_error(self):
        """worker_call to an unreachable URL returns error dict, does NOT raise."""
        from core.agent_client import worker_call
        result = worker_call(
            "http://127.0.0.1:19999",  # nothing listening here
            task="Test",
            show_log=False,
        )
        self.assertEqual(result["status"], "error")
        self.assertIn("error", result)

    def test_worker_status_unreachable_returns_error(self):
        """worker_status to unreachable URL returns error dict."""
        from core.agent_client import worker_status
        result = worker_status("http://127.0.0.1:19999", "nonexistent")
        self.assertEqual(result.get("status"), "error")
        self.assertIn("error", result)


# ── Integration Tests (real LLM workers) ───────────────────────────────

class TestRealWorkerIntegration(unittest.TestCase):
    """
    Integration test: Commander dispatches tasks to 2 worker agents.

    Starts 2 agent servers on dynamic ports, sends simple file-creation
    tasks to both concurrently, and verifies the output files.
    """

    @classmethod
    def setUpClass(cls):
        """Check for API key; skip if absent."""
        if not _has_api_key() or os.environ.get('AGENT_SERVER_TEST_NO_LLM'):
            raise unittest.SkipTest("LLM API key required")

        cls.workers = []
        cls.worker_ports = []
        cls.temp_dir = tempfile.mkdtemp(prefix="agent_server_test_")

        # Start 2 worker servers on dynamic ports
        for i in range(2):
            port = cls._find_free_port()
            cls.worker_ports.append(port)
            proc = subprocess.Popen(
                [
                    sys.executable, "-u",
                    os.path.join(_project_root, "src", "main.py"),
                    "--serve", "--port", str(port),
                    "--workspace", cls.temp_dir,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=_project_root,
                env={**os.environ, "AGENT_SERVER_TEST_MODE": "1"},
            )
            cls.workers.append(proc)

        # Wait for servers to be ready (poll /health)
        deadline = time.time() + 30
        for port in cls.worker_ports:
            import urllib.request
            import urllib.error
            url = f"http://127.0.0.1:{port}/health"
            while time.time() < deadline:
                try:
                    req = urllib.request.Request(url, headers={"Accept": "application/json"})
                    with urllib.request.urlopen(req, timeout=3) as resp:
                        data = json.loads(resp.read().decode())
                        if data.get("status") == "ok":
                            break
                except Exception:
                    time.sleep(0.5)
            else:
                cls._cleanup()
                raise RuntimeError(f"Worker on port {port} did not become healthy")

    @classmethod
    def _cleanup(cls):
        """Kill all worker processes and remove temp dir."""
        for proc in cls.workers:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                proc.kill()
        cls.workers.clear()
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    @classmethod
    def tearDownClass(cls):
        """Cleanup after all tests."""
        cls._cleanup()

    @staticmethod
    def _find_free_port() -> int:
        """Find a free TCP port."""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    def test_two_workers_concurrently(self):
        """Commander sends file-creation tasks to 2 workers concurrently."""
        from core.agent_client import worker_call

        worker_a = f"http://127.0.0.1:{self.worker_ports[0]}"
        worker_b = f"http://127.0.0.1:{self.worker_ports[1]}"

        # Run both tasks in parallel using threads
        results = {}

        def call_a():
            results["a"] = worker_call(
                worker_a,
                task="Write a file named hello.txt containing the word 'hello'",
                show_log=False,
                timeout=120,
            )

        def call_b():
            results["b"] = worker_call(
                worker_b,
                task="Write a file named world.txt containing the word 'world'",
                show_log=False,
                timeout=120,
            )

        t_a = threading.Thread(target=call_a, daemon=True)
        t_b = threading.Thread(target=call_b, daemon=True)
        t_a.start()
        t_b.start()
        t_a.join(timeout=130)
        t_b.join(timeout=130)

        # Verify both completed
        self.assertEqual(results.get("a", {}).get("status"), "completed",
                         f"Worker A failed: {results.get('a')}")
        self.assertEqual(results.get("b", {}).get("status"), "completed",
                         f"Worker B failed: {results.get('b')}")

        # Verify output files were created
        import glob
        all_files = glob.glob(os.path.join(self.temp_dir, "**", "hello.txt"), recursive=True)
        self.assertTrue(all_files, f"hello.txt not found in {self.temp_dir}")
        content = Path(all_files[0]).read_text()
        self.assertIn("hello", content.lower())

        all_files = glob.glob(os.path.join(self.temp_dir, "**", "world.txt"), recursive=True)
        self.assertTrue(all_files, f"world.txt not found in {self.temp_dir}")
        content = Path(all_files[0]).read_text()
        self.assertIn("world", content.lower())

        # Verify worker_call returns files_modified
        self.assertIn("hello.txt", str(results["a"].get("files_modified", [])))
        self.assertIn("world.txt", str(results["b"].get("files_modified", [])))

    def test_worker_status_live(self):
        """worker_status and worker_result work against a live worker."""
        from core.agent_client import worker_call, worker_status, worker_result

        worker = f"http://127.0.0.1:{self.worker_ports[0]}"

        # Submit a simple task
        result = worker_call(
            worker,
            task="Create a file named integration_test.txt with content 'integration ok'",
            show_log=False,
            timeout=60,
        )

        self.assertEqual(result["status"], "completed")

        # Check result endpoint directly
        run_id = result.get("run_id", "")
        self.assertTrue(run_id)

        status_resp = worker_status(worker, run_id)
        self.assertIn(status_resp.get("status"), ("completed", "error"))

        result_resp = worker_result(worker, run_id)
        self.assertIn(result_resp["status"], ("completed", "error"))


# ── Runner ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Run unit tests first (no LLM needed)
    print("\n" + "=" * 70)
    print("Unit Tests — Agent Server Endpoints + Client Tools")
    print("=" * 70)
    unittest.main(verbosity=2, exit=False)

    # Then try integration tests
    print("\n" + "=" * 70)
    print("Integration Tests — 2-Worker Commander")
    print("=" * 70)
    pytest.main([__file__, "-v", "-k", "TestRealWorkerIntegration", "--tb=short"])
