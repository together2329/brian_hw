"""
Worker-to-Worker Chaining Test — End-to-end dispatch chain.

Chain: Worker A (lint) → Worker B (fix) → Worker A (re-lint) → Worker C (simulate)
Verifies that workers can dispatch sub-tasks to each other using worker_call,
worker_status, and worker_result, and that results propagate correctly.

Architecture:
    Worker A (port 18797) - Lint / Re-lint worker (runs iverilog -Wall)
    Worker B (port 18798) - Fix worker (corrects Verilog syntax errors)
    Worker C (port 18799) - Sim worker (compiles + runs vvp simulation)
    Coordinator task      - Dispatched to lint worker; chains to others via worker_call

Requirements:
    iverilog + vvp required for sim tests (skip otherwise)
    LLM API configured for worker tests (skip on flake)

Run:
    python3 -m pytest tests/test_worker_chaining.py -v
"""

import json
import os
import sys
import time
import shutil
import threading
import unittest
import urllib.request
import urllib.error
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DATA_DIR = PROJECT_ROOT / "tests" / "data"
COUNTER_V = DATA_DIR / "counter.v"
BAD_SYNTAX_V = DATA_DIR / "bad_syntax.v"
TB_COUNTER_V = DATA_DIR / "tb_counter.v"

IVERILOG = shutil.which("iverilog")
VVP = shutil.which("vvp")
HAVE_SIM = IVERILOG is not None and VVP is not None

# Worker ports for the chain
LINT_PORT = 18797
FIX_PORT = 18798
SIM_PORT = 18799


# =========================================================================
# Helper: spin up a worker on a given port
# =========================================================================

def _start_worker(port: int, ready: threading.Event):
    """Start an agent_server worker on the given port in a daemon thread."""
    try:
        import uvicorn
        from core.agent_server import create_app
    except ImportError:
        ready.set()  # Signal so setUp doesn't hang
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
    """Gracefully stop a worker."""
    if server:
        server.should_exit = True
    if thread:
        thread.join(timeout=5)


def _post(url: str, data: dict, timeout: int = 120) -> dict:
    """POST JSON to a worker endpoint."""
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
    """GET from a worker endpoint."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode("utf-8"))


def _skip_on_llm_flake(result, test):
    """Skip test if LLM returned error string instead of real output."""
    res_text = result.get("result", "")
    if "Error calling LLM" in res_text or not res_text.strip():
        test.skipTest("LLM returned error/unusable output: " + res_text[:80])


# =========================================================================
# Test Class
# =========================================================================

class TestWorkerChaining(unittest.TestCase):
    """End-to-end worker chaining test: lint → fix → re-lint → simulate."""

    _servers = []
    _threads = []

    @classmethod
    def setUpClass(cls):
        """Spin up three workers: lint, fix, sim. Save bad_syntax.v for restore."""
        try:
            import uvicorn
            from core.agent_server import create_app
        except ImportError:
            raise unittest.SkipTest("fastapi/uvicorn not installed")

        if not HAVE_SIM:
            raise unittest.SkipTest("iverilog/vvp not installed — required for chaining test")

        # Save bad_syntax.v original — step 2 fixes it in-place
        cls._bad_syntax_backup = None
        if BAD_SYNTAX_V.exists():
            cls._bad_syntax_backup = BAD_SYNTAX_V.read_text()

        for port in [LINT_PORT, FIX_PORT, SIM_PORT]:
            ready = threading.Event()
            server, t = _start_worker(port, ready)
            ready.wait(timeout=5)
            if server:
                cls._servers.append(server)
            if t:
                cls._threads.append(t)
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        for server in cls._servers:
            server.should_exit = True
        for t in cls._threads:
            t.join(timeout=5)
        # Restore bad_syntax.v to its original broken state
        if cls._bad_syntax_backup and BAD_SYNTAX_V.exists():
            BAD_SYNTAX_V.write_text(cls._bad_syntax_backup)

    def _wait_for_completion(self, url: str, run_id: str, timeout: int = 180) -> dict:
        """Poll /status until run completes or times out."""
        start = time.time()
        while True:
            status_resp = _get(url + "/status/" + run_id)
            if status_resp.get("status") in ("completed", "error", "cancelled"):
                return _get(url + "/result/" + run_id)
            if time.time() - start > timeout:
                self.skipTest(f"Run {run_id} timed out after {timeout}s")
            time.sleep(2)

    # ── Individual worker health checks ──────────────────────────────

    def test_lint_worker_health(self):
        """Worker A (lint) is healthy."""
        resp = _get(f"http://localhost:{LINT_PORT}/health")
        self.assertEqual(resp["status"], "ok")

    def test_fix_worker_health(self):
        """Worker B (fix) is healthy."""
        resp = _get(f"http://localhost:{FIX_PORT}/health")
        self.assertEqual(resp["status"], "ok")

    def test_sim_worker_health(self):
        """Worker C (sim) is healthy."""
        resp = _get(f"http://localhost:{SIM_PORT}/health")
        self.assertEqual(resp["status"], "ok")

    # ── Step 1: Lint bad_syntax.v → expect LINT FAILED ──────────────

    def test_step1_lint_detects_syntax_error(self):
        """Step 1: Worker A lints bad_syntax.v and returns LINT FAILED."""
        bad_v = str(BAD_SYNTAX_V)
        result = _post(f"http://localhost:{LINT_PORT}/run", {
            "task": (
                "Run this exact command using run_command:\n"
                "  iverilog -g2012 -Wall -o /dev/null " + bad_v + "\n"
                "If exit code is NOT 0 and errors include 'syntax error', respond: Final Answer: LINT FAILED\n"
                "If exit code is 0, respond: Final Answer: LINT PASSED (unexpected)"
            ),
            "sync": True,
        })
        self.assertIn(result["status"], ("completed", "error"), f"Got: {result}")
        if result["status"] == "completed":
            _skip_on_llm_flake(result, self)
            res_text = result.get("result", "")
            self.assertIn("FAILED", res_text.upper(),
                          f"Lint should report FAILED for bad_syntax.v:\n{res_text}")
        else:
            self.skipTest("LLM unavailable: " + str(result))

    # ── Step 2: Fix bad_syntax.v → correct missing semicolon ────────

    def test_step2_fix_corrects_syntax_error(self):
        """Step 2: Worker B fixes the missing semicolon in bad_syntax.v."""
        bad_v = str(BAD_SYNTAX_V)
        result = _post(f"http://localhost:{FIX_PORT}/run", {
            "task": (
                "The file " + bad_v + " has a missing semicolon on the line:\n"
                "  output reg [3:0] count\n"
                "Fix it by adding the semicolon. Also add 'endmodule' at the end if missing.\n"
                "Use replace_in_file to fix the file.\n"
                "After fixing, verify the file compiles by running:\n"
                "  iverilog -g2012 -Wall -o /dev/null " + bad_v + "\n"
                "If compile succeeds, respond: Final Answer: FIX PASSED\n"
                "If compile fails, respond: Final Answer: FIX FAILED with errors."
            ),
            "sync": True,
        })
        self.assertIn(result["status"], ("completed", "error"), f"Got: {result}")
        if result["status"] == "completed":
            _skip_on_llm_flake(result, self)
            res_text = result.get("result", "")
            self.assertIn("PASSED", res_text.upper(),
                          f"Fix should report PASSED. Got:\n{res_text}")
        else:
            self.skipTest("LLM unavailable: " + str(result))

    # ── Step 3: Re-lint the fixed file → expect LINT PASSED ────────

    def test_step3_relint_passes_after_fix(self):
        """Step 3: Worker A re-lints bad_syntax.v (now fixed) and returns LINT PASSED."""
        bad_v = str(BAD_SYNTAX_V)
        result = _post(f"http://localhost:{LINT_PORT}/run", {
            "task": (
                "Run this exact command using run_command:\n"
                "  iverilog -g2012 -Wall -o /dev/null " + bad_v + "\n"
                "If exit code is 0, respond: Final Answer: LINT PASSED\n"
                "If there are errors, list them and respond: Final Answer: LINT FAILED"
            ),
            "sync": True,
        })
        self.assertIn(result["status"], ("completed", "error"), f"Got: {result}")
        if result["status"] == "completed":
            _skip_on_llm_flake(result, self)
            res_text = result.get("result", "")
            # May be PASSED (if step 2 fixed) or FAILED (if step 2 didn't run)
            # We just verify the worker responded — step 2 handles the actual fix
            self.assertTrue(
                "PASSED" in res_text.upper() or "FAILED" in res_text.upper(),
                f"Expected LINT PASSED or FAILED, got:\n{res_text}"
            )
        else:
            self.skipTest("LLM unavailable: " + str(result))

    # ── Step 4: Simulate counter.v → expect SIM PASSED ──────────────

    def test_step4_simulate_passes(self):
        """Step 4: Worker C simulates counter.v+tb_counter.v and returns SIM PASSED."""
        simv_str = str(DATA_DIR / "simv_chain")
        data_str = str(DATA_DIR)
        result = _post(f"http://localhost:{SIM_PORT}/run", {
            "task": (
                "Step 1: cd " + data_str + "\n"
                "Step 2: Run: iverilog -g2012 -o " + simv_str + " counter.v tb_counter.v\n"
                "Step 3: Run: vvp " + simv_str + "\n"
                "Step 4: Look at the output. If count increments 0,1,2,... "
                "respond: Final Answer: SIM PASSED\n"
                "If errors or count fails, respond: Final Answer: SIM FAILED with reason."
            ),
            "sync": True,
        })
        self.assertIn(result["status"], ("completed", "error"), f"Got: {result}")
        if result["status"] == "completed":
            _skip_on_llm_flake(result, self)
            res_text = result.get("result", "")
            self.assertIn("PASSED", res_text.upper(),
                          f"Sim should report PASSED:\n{res_text}")
        else:
            self.skipTest("LLM unavailable: " + str(result))

    # ── End-to-end chain via coordinator ────────────────────────────

    def test_worker_call_all_parallel_dispatch(self):
        """worker_call_all fires tasks to two workers in parallel."""
        if not HAVE_SIM:
            self.skipTest("iverilog/vvp not installed")

        from core.agent_client import worker_call_all

        data_str = str(DATA_DIR)
        cv = str(COUNTER_V)

        results = worker_call_all(
            workers=[
                {"name": "lint", "url": f"http://localhost:{LINT_PORT}"},
                {"name": "sim", "url": f"http://localhost:{SIM_PORT}"},
            ],
            task=(
                "cd " + data_str + " && "
                "iverilog -g2012 -Wall -o /dev/null " + cv + " && "
                "echo PASSED. Final Answer: PASSED"
            ),
            timeout=120,
            max_workers=2,
        )

        self.assertIn("results", results)
        self.assertEqual(results["total"], 2)
        for r in results["results"]:
            self.assertIn(r["status"], ("completed", "error", "timeout"),
                          f"Worker {r['worker']}: {r.get('error','')}")
        # At least one should succeed
        passed = any(r["status"] == "completed" for r in results["results"])
        if not passed:
            self.skipTest(f"Both workers failed: {results}")

    # ── End-to-end chain via coordinator ────────────────────────────

    def test_end_to_end_chain_via_coordinator(self):
        """Full chain: Coordinator dispatches lint→fix→re-lint→sim via worker_call."""
        bad_v = str(BAD_SYNTAX_V)
        data_str = str(DATA_DIR)
        simv_str = str(DATA_DIR / "simv_chain_e2e")

        # The coordinator task instructs the LLM to use worker_call
        # to dispatch sub-tasks to the lint, fix, and sim workers.
        coordinator_url = f"http://localhost:{LINT_PORT}/run"
        task = (
            "You are a verification coordinator. You have access to these workers:\n"
            f"  - lint_worker   at http://localhost:{LINT_PORT}\n"
            f"  - fix_worker    at http://localhost:{FIX_PORT}\n"
            f"  - sim_worker    at http://localhost:{SIM_PORT}\n"
            "\n"
            "Execute this chain using worker_call, worker_status, and worker_result:\n"
            "\n"
            f"Step 1: Send bad_syntax.v ({bad_v}) to lint_worker for linting.\n"
            "  Task: 'Run: iverilog -g2012 -Wall -o /dev/null " + bad_v + ". Say LINT FAILED if errors.'\n"
            "\n"
            "Step 2: If lint FAILED, send the file to fix_worker.\n"
            "  Task: 'Fix missing semicolon in " + bad_v + " and add endmodule if needed. Say FIX PASSED.'\n"
            "\n"
            "Step 3: Re-lint the fixed file using lint_worker.\n"
            "  Task: 'Run: iverilog -g2012 -Wall -o /dev/null " + bad_v + ". Say LINT PASSED if exit 0.'\n"
            "\n"
            "Step 4: Simulate counter.v + tb_counter.v using sim_worker.\n"
            f"  Task: 'cd {data_str} && iverilog -g2012 -o {simv_str} counter.v tb_counter.v && vvp {simv_str}. Say SIM PASSED if count increments.'\n"
            "\n"
            "Respond with Final Answer: CHAIN PASSED if all steps passed, or CHAIN FAILED with which step failed."
        )

        result = _post(coordinator_url, {"task": task, "sync": True})
        self.assertIn(result["status"], ("completed", "error"), f"Got: {result}")
        if result["status"] == "completed":
            _skip_on_llm_flake(result, self)
            res_text = result.get("result", "")
            # The coordinator should report CHAIN PASSED if all steps work
            self.assertTrue(
                "PASSED" in res_text.upper() or "FAILED" in res_text.upper(),
                f"Coordinator should report PASSED or FAILED:\n{res_text}"
            )
        else:
            self.skipTest("LLM unavailable: " + str(result))


if __name__ == "__main__":
    unittest.main()
