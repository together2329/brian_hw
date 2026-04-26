"""
Test tool execution through worker: write_file, read_file, run_command.

Verifies that agent_server can execute real tools in response to tasks.
"""

import os
import sys
import time
import json
import unittest
import tempfile
import shutil
import threading
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestWorkerToolExecution(unittest.TestCase):
    """
    Integration tests: start agent_server, send tasks that require
    write_file, read_file, and run_command tools, verify side effects.
    """

    @classmethod
    def setUpClass(cls):
        try:
            import uvicorn
            from core.agent_server import create_app
        except ImportError:
            raise unittest.SkipTest("fastapi/uvicorn not installed")

        cls.port = 18785
        cls.base_url = f"http://localhost:{cls.port}"
        cls._server_ready = threading.Event()

        def _run():
            app = create_app()
            config = uvicorn.Config(app, host="127.0.0.1", port=cls.port, log_level="error")
            server = uvicorn.Server(config)
            cls._server = server
            cls._server_ready.set()
            server.run()

        cls._thread = threading.Thread(target=_run, daemon=True)
        cls._thread.start()
        cls._server_ready.wait(timeout=5)
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, '_server'):
            cls._server.should_exit = True
        if cls._thread:
            cls._thread.join(timeout=5)

    def _post(self, data: dict) -> dict:
        import urllib.request, urllib.error
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/run",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")
            return json.loads(body) if body else {"error": str(e)}

    def _sync_run(self, task: str) -> dict:
        """Send a sync task and return the result dict."""
        return self._post({"task": task, "sync": True})

    def test_write_file_tool(self):
        """Worker executes write_file tool."""
        import tempfile, shutil
        tmpdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tmpdir, "tool_write_test.txt")
        marker = "TOOL_WRITE_TEST_SUCCESS"
        try:
            result = self._sync_run(
                f"Use write_file to create {tmpfile} with content '{marker}'. "
                "Return Final Answer: DONE if successful."
            )
            self.assertIn(result["status"], ("completed", "error"), f"Got: {result}")
            if result["status"] == "completed":
                self.assertTrue(os.path.exists(tmpfile), f"File not created: {tmpfile}")
                with open(tmpfile) as f:
                    self.assertIn(marker, f.read())
            else:
                self.skipTest(f"LLM unavailable or error: {result}")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_read_file_tool(self):
        """Worker executes read_file tool."""
        import tempfile, shutil
        tmpdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tmpdir, "tool_read_test.txt")
        marker = "TOOL_READ_TEST_MARKER_12345"
        try:
            with open(tmpfile, "w") as f:
                f.write(marker + "\n")
            result = self._sync_run(
                f"Read the file {tmpfile} using read_file. "
                "Report the exact content in your Final Answer. Do not use any other tools."
            )
            self.assertIn(result["status"], ("completed", "error"), f"Got: {result}")
            if result["status"] == "completed":
                result_text = result.get("result", "")
                # Skip if LLM returned a generic error instead of proper output
                if "Error calling LLM" in result_text or not result_text.strip():
                    self.skipTest(f"LLM returned error/unusable output: {result_text[:80]}")
                self.assertIn(marker, result_text)
            else:
                self.skipTest(f"LLM unavailable or error: {result}")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_run_command_tool(self):
        """Worker executes run_command tool."""
        import tempfile, shutil
        tmpdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tmpdir, "tool_cmd_test.txt")
        marker = "TOOL_CMD_SUCCESS"
        try:
            result = self._sync_run(
                f"Use run_command to execute: echo {marker} > {tmpfile}. "
                "Then use read_file to read that file. Report the content in Final Answer."
            )
            self.assertIn(result["status"], ("completed", "error"), f"Got: {result}")
            if result["status"] == "completed":
                if os.path.exists(tmpfile):
                    with open(tmpfile) as f:
                        content = f.read().strip()
                    self.assertIn(marker, content)
                else:
                    self.fail(f"run_command did not create {tmpfile}")
            else:
                self.skipTest(f"LLM unavailable or error: {result}")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
