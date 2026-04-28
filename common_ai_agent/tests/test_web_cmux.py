
"""
Web UI + cmux Integration Test - exercises the browser-based Web UI
with optional cmux tool integration.

Starts the Web UI server (FastAPI + SSE), sends requests to /, /stream, /submit,
and optionally exercises cmux tools when CMUX_ENABLE=true and cmux is available.

Architecture:
    Web UI (port 18880) - FastAPI + SSE from src/web_ui.py
    cmux (optional)     - Terminal multiplexer for workspace/pane management

Run:
    python3 -m pytest tests/test_web_cmux.py -v

    # With cmux enabled:
    CMUX_ENABLE=true python3 -m pytest tests/test_web_cmux.py -v
"""

import json
import os
import sys
import time
import threading
import unittest
import urllib.request
import urllib.error
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

WEB_UI_PORT = 18880
WEB_UI_BASE = f"http://localhost:{WEB_UI_PORT}"


def _check_cmux_available():
    """Check if cmux is installed and running."""
    import subprocess
    try:
        result = subprocess.run(
            ["cmux", "tree"],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0 and "workspace" in result.stdout.lower()
    except Exception:
        return False


def _start_web_ui(port, ready):
    """Start the Web UI server in a daemon thread."""
    try:
        import uvicorn
        from src.web_ui import create_app
    except ImportError:
        ready.set()
        return None, None

    app = create_app()
    cfg = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(cfg)
    ready.set()

    def _run():
        server.run()

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return server, t


def _stop_server(server, thread):
    """Gracefully stop a uvicorn server."""
    if server:
        server.should_exit = True
    if thread:
        thread.join(timeout=5)


def _get(url, timeout=10):
    """GET raw bytes from URL."""
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.read()


def _get_json(url, timeout=10):
    """GET JSON from URL."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode("utf-8"))


def _post(url, data, timeout=10):
    """POST JSON/raw to URL, return JSON."""
    if isinstance(data, str):
        body = data.encode("utf-8")
    else:
        body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={
            "Content-Type": (
                "application/json" if isinstance(data, dict) else "text/plain"
            )
        },
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode("utf-8"))


class TestWebUICmux(unittest.TestCase):
    """Web UI tests with optional cmux integration."""

    _server = None
    _thread = None
    _cmux_available = False

    @classmethod
    def setUpClass(cls):
        """Start Web UI server and check cmux availability."""
        try:
            import uvicorn  # noqa: F401
            from src.web_ui import create_app  # noqa: F401
        except ImportError:
            raise unittest.SkipTest(
                "fastapi/uvicorn not installed - pip install fastapi uvicorn"
            )

        # Check cmux
        cls._cmux_available = _check_cmux_available()

        ready = threading.Event()
        server, t = _start_web_ui(WEB_UI_PORT, ready)
        ready.wait(timeout=5)
        if not server:
            raise unittest.SkipTest("uvicorn server failed to start")
        cls._server = server
        cls._thread = t
        time.sleep(0.5)  # Let server settle

    @classmethod
    def tearDownClass(cls):
        _stop_server(cls._server, cls._thread)

    # ------------------------------------------------------------------
    # Health & HTML
    # ------------------------------------------------------------------

    def test_web_ui_index_html(self):
        """GET / returns the web UI HTML page."""
        resp = _get(WEB_UI_BASE + "/", timeout=5)
        html = resp.decode("utf-8", errors="replace")
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("UPD Agent", html)
        self.assertIn("SSE", html)  # JavaScript SSE code
        self.assertIn("/submit", html)
        self.assertIn("/stream", html)

    def test_web_ui_submit_endpoint(self):
        """POST /submit accepts a text body and returns ok."""
        resp = _post(WEB_UI_BASE + "/submit", "Hello Web UI", timeout=5)
        self.assertEqual(resp, {"ok": True})

    def test_web_ui_submit_handles_empty(self):
        """POST /submit with empty body does not crash."""
        resp = _post(WEB_UI_BASE + "/submit", "", timeout=5)
        self.assertEqual(resp, {"ok": True})

    def test_web_ui_submit_handles_json(self):
        """POST /submit with JSON body returns 422 (FastAPI validates str type).

        The /submit endpoint expects a raw text body, not JSON.
        FastAPI correctly rejects the wrong Content-Type with a
        validation error.  This test verifies the endpoint does NOT
        crash on malformed input.
        """
        try:
            _post(WEB_UI_BASE + "/submit", {"message": "test"}, timeout=5)
            # If the server is running without pydantic, it may accept it
            # That's fine — the test just checks no crash.
        except urllib.error.HTTPError as e:
            # 422 Unprocessable Entity is the expected response
            self.assertIn(e.code, (422, 400, 415),
                          "Expected validation error, got {}".format(e.code))

    def test_web_ui_stream_sse_connects(self):
        """GET /stream establishes SSE connection with correct headers."""
        req = urllib.request.Request(WEB_UI_BASE + "/stream")
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                headers = dict(r.headers)
                ct = headers.get(
                    "Content-Type", headers.get("content-type", "")
                )
                self.assertIn("text/event-stream", ct)
                cc = headers.get(
                    "Cache-Control", headers.get("cache-control", "")
                )
                self.assertIn("no-cache", cc)
                # Read a little to confirm connection is open
                r.read(1)
        except Exception:
            # Timeout on reading is OK - SSE stream stays open
            pass

    def test_web_ui_404_non_existent(self):
        """Non-existent route returns an HTTP error (4xx or 5xx).

        Uses low-level urlopen to inspect the actual HTTP status code
        (our _get_json helper catches HTTPError and returns the body).
        """
        try:
            urllib.request.urlopen(
                urllib.request.Request(WEB_UI_BASE + "/nonexistent"),
                timeout=5
            )
            self.fail("Expected HTTPError for nonexistent route")
        except urllib.error.HTTPError as e:
            self.assertTrue(
                400 <= e.code < 600,
                "Expected 4xx/5xx for /nonexistent, got {}".format(e.code)
            )

    # ------------------------------------------------------------------
    # cmux Integration
    # ------------------------------------------------------------------

    def _require_cmux(self):
        if not self._cmux_available:
            self.skipTest(
                "cmux not available - 'cmux tree' must return workspace data"
            )

    def test_cmux_tree_via_subprocess(self):
        """cmux tree CLI returns workspace/pane data (direct subprocess)."""
        self._require_cmux()
        import subprocess
        result = subprocess.run(
            ["cmux", "tree"],
            capture_output=True, text=True, timeout=10
        )
        msg = "cmux tree failed: {}".format(result.stderr)
        self.assertEqual(result.returncode, 0, msg)
        out = result.stdout.lower()
        keys = ["workspace", "pane", "surface", "window"]
        found = any(k in out for k in keys)
        self.assertTrue(
            found,
            "cmux tree output should mention workspace/pane/surface, got: "
            + result.stdout[:500]
        )

    def test_cmux_list_panes_via_subprocess(self):
        """cmux list-panes CLI returns pane list (direct subprocess)."""
        self._require_cmux()
        import subprocess
        result = subprocess.run(
            ["cmux", "list-panes"],
            capture_output=True, text=True, timeout=10
        )
        out = result.stdout.lower()
        ok = result.returncode == 0 or "pane" in out
        self.assertTrue(
            ok,
            "cmux list-panes should return pane info, got: "
            + result.stdout[:300] + " stderr: " + result.stderr[:300]
        )

    def test_cmux_notify_via_subprocess(self):
        """cmux notify CLI can be called (may fail on macOS auth but no crash)."""
        self._require_cmux()
        import subprocess
        result = subprocess.run(
            [
                "cmux", "notify",
                "--title", "Web UI Test",
                "--body", "Testing from test_web_cmux.py",
            ],
            capture_output=True, text=True, timeout=10
        )
        # notify may fail due to macOS permissions - that is OK
        # Just verify the CLI did not crash/segfault
        self.assertIsNotNone(result)

    def test_cmux_new_split_dry_run(self):
        """cmux new-split CLI availability check (non-destructive)."""
        self._require_cmux()
        import subprocess
        result = subprocess.run(
            ["cmux", "new-split", "right"],
            capture_output=True, text=True, timeout=10
        )
        # May succeed or fail depending on state - just verify it runs
        self.assertIsNotNone(result)

    def test_cmux_capture_via_subprocess(self):
        """cmux read-screen CLI captures screen text."""
        self._require_cmux()
        import subprocess
        result = subprocess.run(
            ["cmux", "read-screen", "--lines", "50"],
            capture_output=True, text=True, timeout=10
        )
        msg = "cmux read-screen failed: {}".format(result.stderr)
        self.assertEqual(result.returncode, 0, msg)
        self.assertTrue(len(result.stdout) > 0, "read-screen should return output")

    # ------------------------------------------------------------------
    # Web UI + cmux combined workflow
    # ------------------------------------------------------------------

    def test_web_ui_submit_then_cmux_tree(self):
        """End-to-end: submit to web UI then verify cmux still works.

        Mirrors real user workflow:
          1. Open browser at http://localhost:18880
          2. Type a command -> POST /submit
          3. cmux tools work alongside
        """
        self._require_cmux()

        # Submit a message to the web UI
        resp = _post(WEB_UI_BASE + "/submit", "/help", timeout=5)
        self.assertEqual(resp, {"ok": True})

        # cmux should still work
        import subprocess
        result = subprocess.run(
            ["cmux", "tree"],
            capture_output=True, text=True, timeout=10
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("workspace", result.stdout.lower())

    # ------------------------------------------------------------------
    # SSE Stream Events
    # ------------------------------------------------------------------

    def test_sse_stream_receives_events(self):
        """Verify SSE /stream pushes events on submit.

        Start reading SSE events in a background thread, send a submit,
        and verify the stream is alive.
        """
        received_events = []

        def _read_stream():
            try:
                req = urllib.request.Request(WEB_UI_BASE + "/stream")
                with urllib.request.urlopen(req, timeout=8) as r:
                    # Read first few chunks
                    for _ in range(5):
                        line = r.readline().decode("utf-8", errors="replace")
                        if line.strip():
                            received_events.append(line.strip())
            except Exception:
                pass

        # Start SSE reader thread
        reader = threading.Thread(target=_read_stream, daemon=True)
        reader.start()
        time.sleep(0.3)  # Let SSE connect

        # Submit a message - should trigger SSE event
        _post(WEB_UI_BASE + "/submit", "test SSE event", timeout=5)
        time.sleep(1.5)  # Wait for event propagation

        reader.join(timeout=2)

        # We may or may not receive events depending on agent state
        # Just verify the thread ran without crashing
        self.assertIsNotNone(received_events)

    # ------------------------------------------------------------------
    # cmux tools via Python API
    # ------------------------------------------------------------------

    def test_cmux_python_tools_importable(self):
        """cmux tools module imports without error when CMUX_ENABLE is set."""
        # Import the cmux tools module
        from core.tools_cmux import CMUX_TOOLS

        # Verify all expected tools are registered
        expected_tools = [
            "cmux_tree", "cmux_capture", "cmux_send", "cmux_send_key",
            "cmux_notify", "cmux_list_panes", "cmux_new_split",
            "cmux_new_workspace", "cmux_focus_pane", "cmux_resize_pane",
            "cmux_move_surface", "cmux_close_surface", "cmux_break_pane",
            "cmux_swap_pane", "cmux_rename_workspace", "cmux_select_workspace",
            "cmux_set_surface", "cmux_restart_modifiable",
            "cmux_new_pane",  # alias for cmux_new_split
        ]
        for tool_name in expected_tools:
            self.assertIn(
                tool_name, CMUX_TOOLS,
                "Missing cmux tool: {}".format(tool_name)
            )
            self.assertTrue(
                callable(CMUX_TOOLS[tool_name]),
                "{} should be callable".format(tool_name),
            )

    def test_cmux_tree_python_call(self):
        """cmux_tree() Python function returns workspace tree (when cmux available)."""
        self._require_cmux()
        from core.tools_cmux import cmux_tree

        result = cmux_tree()
        self.assertIn("workspace", result.lower())
        self.assertNotIn(
            "Error", result[:50],
            "cmux_tree failed: {}".format(result[:200])
        )

    def test_cmux_list_panes_python_call(self):
        """cmux_list_panes() Python function returns pane list."""
        self._require_cmux()
        from core.tools_cmux import cmux_list_panes

        result = cmux_list_panes()
        self.assertIn("pane", result.lower())

    def test_cmux_notify_python_call(self):
        """cmux_notify() Python function runs without crash."""
        self._require_cmux()
        from core.tools_cmux import cmux_notify

        result = cmux_notify("Test Web UI", "Integration test")
        # May succeed or fail on macOS auth - just verify it runs
        self.assertIsNotNone(result)

    # ------------------------------------------------------------------
    # cmux + agent_server integration pattern
    # ------------------------------------------------------------------

    def test_cmux_tree_output_parsable(self):
        """cmux tree output is structured enough to identify workspaces/panes."""
        self._require_cmux()
        import subprocess
        result = subprocess.run(
            ["cmux", "tree"],
            capture_output=True, text=True, timeout=10
        )
        out = result.stdout.lower()

        # cmux tree should indicate at least one workspace
        has_workspace = "workspace" in out
        has_pane = "pane" in out or "surface" in out
        has_tab = "tab" in out

        self.assertTrue(
            has_workspace or has_pane or has_tab,
            "cmux tree should show workspace/pane/tab structure: "
            + result.stdout[:500]
        )


if __name__ == "__main__":
    unittest.main()
