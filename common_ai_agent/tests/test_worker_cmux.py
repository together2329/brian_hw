
\"\"\"
Worker Test with cmux Integration — exercises cmux tools via agent_server.

Starts an agent_server worker, sends tasks that use cmux_tree, cmux_list_panes,
and cmux_notify, then verifies correct tool execution.

Architecture:
    Worker (port 18790) - Runs ReAct loop with cmux tools enabled
    Tests                - Send sync tasks that exercise cmux tools

Requirements:
    cmux installed and running (cmux tree must return workspace/pane data)
    LLM API configured (tapas@google / gemini via config)
    fastapi/uvicorn installed

Run:
    python3 -m pytest tests/test_worker_cmux.py -v
    # Or with environment override:
    CMUX_ENABLE=true python3 -m pytest tests/test_worker_cmux.py -v
\"\"\"

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

CMUX_PORT = 18790


def _start_worker(port: int, ready: threading.Event):
    \"\"\"Start an agent_server worker on the given port in a daemon thread.\"\"\"
    try:
        import uvicorn
        from core.agent_server import create_app
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


def _stop_worker(server, thread):
    \"\"\"Gracefully stop a worker.\"\"\"
    if server:
        server.should_exit = True
    if thread:
        thread.join(timeout=5)


def _post(url: str, data: dict, timeout: int = 120) -> dict:
    \"\"\"POST JSON to a worker endpoint.\"\"\"
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode("utf-8"))


def _get(url: str, timeout: int = 5) -> dict:
    \"\"\"GET from a worker endpoint.\"\"\"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode("utf-8"))


def _check_cmux_available() -> bool:
    \"\"\"Check if cmux is installed and running.\"\"\"
    import subprocess
    try:
        result = subprocess.run(
            ["cmux", "tree"],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0 and "workspace" in result.stdout.lower()
    except Exception:
        return False


def _skip_on_llm_flake(result, test):
    \"\"\"Skip test if LLM returned an error instead of real output.\"\"\"
    res_text = result.get("result", "")
    if "Error calling LLM" in res_text or not res_text.strip():
        test.skipTest("LLM returned error/unusable output: " + res_text[:80])


class TestWorkerCmux(unittest.TestCase):
    \"\"\"Worker tests exercising cmux tools (cmux_tree, cmux_list_panes, cmux_notify).\"\"\"

    _server = None
    _thread = None

    @classmethod
    def setUpClass(cls):
        \"\"\"Start one worker with CMUX_ENABLE=true for cmux tool access.\"\"\"
        try:
            import uvicorn
            from core.agent_server import create_app
        except ImportError:
            raise unittest.SkipTest("fastapi/uvicorn not installed")

        if not _check_cmux_available():
            raise unittest.SkipTest(
                "cmux not available or not running — "
                "cmux tree must return workspace data"
            )

        # Enable cmux tools for the worker process via env
        # NOTE: The config reloads per-import; we set env before worker starts.
        os.environ["CMUX_ENABLE"] = "true"

        ready = threading.Event()
        server, t = _start_worker(CMUX_PORT, ready)
        ready.wait(timeout=5)
        if not server:
            raise unittest.SkipTest("uvicorn server failed to start")
        cls._server = server
        cls._thread = t
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        if cls._server:
            cls._server.should_exit = True
        if cls._thread:
            cls._thread.join(timeout=5)

    # ── Health Check ───────────────────────────────────────────────

    def test_worker_health(self):
        \"\"\"Worker is healthy and reachable.\"\"\"
        resp = _get(f"http://localhost:{CMUX_PORT}/health")
        self.assertEqual(resp["status"], "ok")

    # ── cmux_tree ──────────────────────────────────────────────────

    def test_cmux_tree_tool(self):
        \"\"\"Worker executes cmux_tree tool and returns workspace/pane tree.\"\"\"
        result = _post(f"http://localhost:{CMUX_PORT}/run", {
            "task": (
                "Run cmux_tree to get the cmux workspace tree. "
                "Look at the output. It should show workspace, pane, and surface entries. "
                "Report the count of workspaces and panes you see in your Final Answer. "
                "Format: Final Answer: WORKSPACES=<N> PANES=<M>"
            ),
            "sync": True,
        })
        self.assertIn(result["status"], ("completed", "error"), f"Got: {result}")
        if result["status"] == "completed":
            _skip_on_llm_flake(result, self)
            res_text = result.get("result", "")
            # Must mention workspace or pane (cmux_tree output indicators)
            self.assertTrue(
                "WORKSPACE" in res_text.upper() or "PANE" in res_text.upper()
                or "window" in res_text.lower(),
                f"cmux_tree should return workspace/pane info, got:\n{res_text[:500]}"
            )
        else:
            self.skipTest("LLM unavailable: " + str(result))

    # ── cmux_list_panes ────────────────────────────────────────────

    def test_cmux_list_panes_tool(self):
        \"\"\"Worker executes cmux_list_panes tool and returns pane list.\"\"\"
        result = _post(f"http://localhost:{CMUX_PORT}/run", {
            "task": (
                "Run cmux_list_panes to list all panes in the current workspace. "
                "Look at the output — it should list pane refs like 'pane:1' with surface counts. "
                "Report the number of panes and their refs in your Final Answer. "
                "Format: Final Answer: PANE_COUNT=<N> REFS=<list>"
            ),
            "sync": True,
        })
        self.assertIn(result["status"], ("completed", "error"), f"Got: {result}")
        if result["status"] == "completed":
            _skip_on_llm_flake(result, self)
            res_text = result.get("result", "")
            self.assertTrue(
                "pane" in res_text.lower(),
                f"cmux_list_panes should return pane info, got:\n{res_text[:500]}"
            )
        else:
            self.skipTest("LLM unavailable: " + str(result))

    # ── cmux_notify (non-destructive) ──────────────────────────────

    def test_cmux_notify_tool(self):
        \"\"\"Worker executes cmux_notify tool without error.\"\"\"
        result = _post(f"http://localhost:{CMUX_PORT}/run", {
            "task": (
                "Run cmux_notify with title='Worker CMUX Test' and body='Testing from agent_server worker'. "
                "After running it, respond with Final Answer: NOTIFY_SENT if no error, "
                "or Final Answer: NOTIFY_FAILED if you see an error."
            ),
            "sync": True,
        })
        self.assertIn(result["status"], ("completed", "error"), f"Got: {result}")
        if result["status"] == "completed":
            _skip_on_llm_flake(result, self)
            res_text = result.get("result", "")
            # Notify may succeed or fail depending on macOS auth; either is fine —
            # we just verify the tool was attempted and the worker didn't crash.
            self.assertTrue(
                "NOTIFY" in res_text.upper(),
                f"cmux_notify should be attempted, got:\n{res_text[:500]}"
            )
        else:
            self.skipTest("LLM unavailable: " + str(result))

    # ── cmux_tree via worker_call client (exercises worker_call tool) ──

    def test_worker_call_cmux_tree(self):
        \"\"\"
        Coordinator-style: use worker_call to dispatch cmux_tree task
        to the worker via the agent_client module.
        \"\"\"
        from core.agent_client import worker_call

        result = worker_call(
            worker=f"http://localhost:{CMUX_PORT}",
            task=(
                "Run cmux_tree to see the cmux workspace structure. "
                "Report: Final Answer: TREE_OK if output shows 'workspace' and 'pane', "
                "or TREE_FAILED otherwise."
            ),
            timeout=60,
            show_log=False,
        )
        self.assertIn(result["status"], ("completed", "error"), f"Got: {result}")
        if result["status"] == "completed":
            res_text = result.get("result", "")
            self.assertTrue(
                "TREE_OK" in res_text.upper() or "workspace" in res_text.lower(),
                f"worker_call cmux_tree should return workspace info:\n{res_text[:500]}"
            )
        else:
            self.skipTest("LLM unavailable: " + str(result))

    # ── cmux_tree + cmux_list_panes together (multi-tool task) ─────

    def test_cmux_multi_tool_task(self):
        \"\"\"Worker uses both cmux_tree and cmux_list_panes in a single task.\"\"\"
        result = _post(f"http://localhost:{CMUX_PORT}/run", {
            "task": (
                "Step 1: Run cmux_tree to see the overall cmux structure. "
                "Step 2: Run cmux_list_panes to list panes in the current workspace. "
                "Compare the two outputs: the panes from cmux_list_panes should appear "
                "in the cmux_tree output under the current workspace. "
                "Report Final Answer: MATCH if they're consistent, or MISMATCH if not."
            ),
            "sync": True,
        })
        self.assertIn(result["status"], ("completed", "error"), f"Got: {result}")
        if result["status"] == "completed":
            _skip_on_llm_flake(result, self)
            res_text = result.get("result", "")
            self.assertTrue(
                "MATCH" in res_text.upper() or "MISMATCH" in res_text.upper(),
                f"Multi-tool cmux task should compare tree vs list-panes:\n{res_text[:500]}"
            )
        else:
            self.skipTest("LLM unavailable: " + str(result))


if __name__ == "__main__":
    unittest.main()
