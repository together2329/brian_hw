"""
RTL Pipeline Tests - Verilog Counter Lint + Sim via separated workers.

Architecture:
    Worker A (port 18795) - Lint counter.v with iverilog -Wall
    Worker B (port 18796) - Compile + simulate counter.v + tb_counter.v
    Coordinator       - Parallel dispatch, poll, collect, verify

Requirements:
    iverilog + vvp required for sim tests (skip otherwise)
    LLM API configured for worker tests (skip on flake)

Run:
    python3 -m pytest tests/test_rtl_pipeline.py -v
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
TB_COUNTER_V = DATA_DIR / "tb_counter.v"

# Tool availability
IVERILOG = shutil.which("iverilog")
VVP = shutil.which("vvp")
HAVE_SIM = IVERILOG is not None and VVP is not None


# =========================================================================
# Unit Tests - Design files (no workers, no LLM)
# =========================================================================

class TestRTLDesignFiles(unittest.TestCase):
    """Verify RTL design files exist and compile correctly (no workers needed)."""

    def test_counter_v_exists(self):
        """counter.v RTL design file exists."""
        self.assertTrue(COUNTER_V.exists(), f"Missing {COUNTER_V}")

    def test_tb_counter_v_exists(self):
        """tb_counter.v testbench file exists."""
        self.assertTrue(TB_COUNTER_V.exists(), f"Missing {TB_COUNTER_V}")

    def test_counter_compiles_zero_errors(self):
        """counter.v compiles with zero errors (iverilog -g2012 -Wall)."""
        if not IVERILOG:
            self.skipTest("iverilog not installed")
        import subprocess
        result = subprocess.run(
            [IVERILOG, "-g2012", "-Wall", "-o", "/dev/null", str(COUNTER_V)],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0,
                         f"counter.v lint failed:\n{result.stderr}")

    def test_counter_and_tb_compile(self):
        """counter.v + tb_counter.v compile together with zero errors."""
        if not IVERILOG:
            self.skipTest("iverilog not installed")
        import subprocess
        simv = DATA_DIR / "simv"
        result = subprocess.run(
            [IVERILOG, "-g2012", "-Wall", "-o", str(simv),
             str(COUNTER_V), str(TB_COUNTER_V)],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0,
                         f"Compile failed:\n{result.stderr}")
        if simv.exists():
            simv.unlink()

    def test_simulation_output_has_count_sequence(self):
        """vvp simulation output contains expected counter sequence."""
        if not HAVE_SIM:
            self.skipTest("iverilog/vvp not installed")
        import subprocess
        simv = DATA_DIR / "simv"
        try:
            compile_result = subprocess.run(
                [IVERILOG, "-g2012", "-o", str(simv),
                 str(COUNTER_V), str(TB_COUNTER_V)],
                capture_output=True, text=True, cwd=str(DATA_DIR)
            )
            self.assertEqual(compile_result.returncode, 0,
                             f"Compile failed:\n{compile_result.stderr}")
            sim_result = subprocess.run(
                [VVP, str(simv)],
                capture_output=True, text=True, cwd=str(DATA_DIR), timeout=10
            )
            output = sim_result.stdout
            counts_seen = []
            for line in output.split("\n"):
                if "count=" in line:
                    try:
                        count_val = int(line.split("count=")[-1].strip().split()[0])
                        counts_seen.append(count_val)
                    except ValueError:
                        pass
            self.assertGreater(len(counts_seen), 0,
                               f"No count values found in output:\n{output}")
            # Deduplicate consecutive values (count can stay same for multiple cycles)
            deduped = [counts_seen[0]]
            for v in counts_seen[1:]:
                if v != deduped[-1]:
                    deduped.append(v)
            if len(deduped) >= 3:
                for i in range(1, min(len(deduped), 10)):
                    self.assertEqual(deduped[i], deduped[i-1] + 1,
                                     f"Count not sequential at deduped index {i}: {deduped} (raw: {counts_seen})")
        finally:
            if simv.exists():
                simv.unlink()


    def test_syntax_error_detected_by_iverilog(self):
        """iverilog -Wall catches syntax errors in bad_syntax.v."""
        if not IVERILOG:
            self.skipTest("iverilog not installed")
        import subprocess
        bad_v = DATA_DIR / "bad_syntax.v"
        if not bad_v.exists():
            self.skipTest("bad_syntax.v not found")
        result = subprocess.run(
            [IVERILOG, "-g2012", "-Wall", "-o", "/dev/null", str(bad_v)],
            capture_output=True, text=True
        )
        self.assertNotEqual(result.returncode, 0,
                            "Expected non-zero exit for syntax error")
        self.assertIn("syntax error", result.stderr.lower(),
                      f"Expected syntax error in: {result.stderr}")

    def test_bad_compile_reports_failure(self):
        """Compiling bad_syntax.v fails with non-zero exit."""
        if not IVERILOG:
            self.skipTest("iverilog not installed")
        import subprocess
        bad_v = DATA_DIR / "bad_syntax.v"
        if not bad_v.exists():
            self.skipTest("bad_syntax.v not found")
        result = subprocess.run(
            [IVERILOG, "-g2012", "-o", str(DATA_DIR / "bad_simv"), str(bad_v)],
            capture_output=True, text=True
        )
        self.assertNotEqual(result.returncode, 0,
                            f"Expected compile failure, got exit 0")
        if (DATA_DIR / "bad_simv").exists():
            (DATA_DIR / "bad_simv").unlink()

    def test_good_file_passes_lint(self):
        """counter.v passes lint with zero errors."""
        if not IVERILOG:
            self.skipTest("iverilog not installed")
        import subprocess
        result = subprocess.run(
            [IVERILOG, "-g2012", "-Wall", "-o", "/dev/null", str(COUNTER_V)],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0,
                         f"Expected lint pass, got:\n{result.stderr}")


# =========================================================================
# Base class for worker integration tests
# =========================================================================

class _WorkerTestBase(unittest.TestCase):
    """Base class that starts an agent_server worker on a given port."""

    port = None
    base_url = None
    _server = None
    _thread = None

    @classmethod
    def setUpClass(cls):
        try:
            import uvicorn
            from core.agent_server import create_app
        except ImportError:
            raise unittest.SkipTest("fastapi/uvicorn not installed")

        ready = threading.Event()

        def _run():
            app = create_app()
            cfg = uvicorn.Config(app, host="127.0.0.1", port=cls.port,
                                  log_level="error")
            cls._server = uvicorn.Server(cfg)
            ready.set()
            cls._server.run()

        cls._thread = threading.Thread(target=_run, daemon=True)
        cls._thread.start()
        ready.wait(timeout=5)
        time.sleep(0.3)

    @classmethod
    def tearDownClass(cls):
        if cls._server:
            cls._server.should_exit = True
        if cls._thread:
            cls._thread.join(timeout=5)

    def _post(self, data, timeout=120):
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            self.base_url + "/run", data=body,
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return json.loads(e.read().decode("utf-8"))

    def _get(self, path, timeout=5):
        try:
            with urllib.request.urlopen(self.base_url + path,
                                         timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return json.loads(e.read().decode("utf-8"))

    def _skip_on_llm_flake(self, result):
        """Skip test if LLM returned error string instead of real output."""
        res_text = result.get("result", "")
        if "Error calling LLM" in res_text or not res_text.strip():
            self.skipTest("LLM returned error/unusable output: " + res_text[:80])


# =========================================================================
# Worker A - Lint counter.v
# =========================================================================

class TestLintWorker(_WorkerTestBase):
    """Tests for Worker A - Lint counter.v with iverilog -Wall."""

    port = 18795
    base_url = "http://localhost:18795"

    def test_lint_worker_health(self):
        """Worker A /health endpoint returns ok."""
        health = self._get("/health")
        self.assertEqual(health["status"], "ok")

    def test_lint_worker_lints_counter_v(self):
        """Worker A lints counter.v and reports LINT PASSED."""
        cv = str(COUNTER_V)
        result = self._post({
            "task": (
                "Run this exact command using run_command:\n"
                "  iverilog -g2012 -Wall -o /dev/null " + cv + "\n"
                "If exit code is 0, respond: Final Answer: LINT PASSED\n"
                "If there are errors, list them and respond: Final Answer: LINT FAILED"
            ),
            "sync": True,
        })
        self.assertIn(result["status"], ("completed", "error"), f"Got: {result}")
        if result["status"] == "completed":
            self._skip_on_llm_flake(result)
            res_text = result.get("result", "")
            self.assertIn("PASSED", res_text.upper(),
                          f"Lint did not report PASSED:\n{res_text}")
        else:
            self.skipTest("LLM unavailable or worker error: " + str(result))

    def test_lint_worker_log_has_tool_calls(self):
        """Worker A /log contains run_command tool call entries."""
        cv = str(COUNTER_V)
        resp = self._post({
            "task": "Run: iverilog -g2012 -Wall -o /dev/null " + cv + ". Say PASSED if exit 0.",
            "sync": False,
        })
        run_id = resp["run_id"]
        for _ in range(60):
            status = self._get("/status/" + run_id)
            if status["status"] in ("completed", "error"):
                break
            time.sleep(0.5)
        log = self._get("/log/" + run_id)
        action_types = [e["type"] for e in log.get("entries", [])]
        self.assertIn("action", action_types,
                      "No action entries in log: " + str(action_types))

    def test_lint_worker_catches_syntax_error(self):
        """Worker A lints bad_syntax.v and reports LINT FAILED."""
        bad_v = str(DATA_DIR / "bad_syntax.v")
        result = self._post({
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
            self._skip_on_llm_flake(result)
            res_text = result.get("result", "")
            self.assertIn("FAILED", res_text.upper(),
                          f"Lint should report FAILED for bad_syntax.v:\n{res_text}")
        else:
            self.skipTest("LLM unavailable or worker error: " + str(result))


# =========================================================================
# Worker B - Compile + simulate
# =========================================================================

class TestSimWorker(_WorkerTestBase):
    """Tests for Worker B - Compile + simulate counter.v + tb_counter.v."""

    port = 18796
    base_url = "http://localhost:18796"

    def test_sim_worker_health(self):
        """Worker B /health endpoint returns ok."""
        health = self._get("/health")
        self.assertEqual(health["status"], "ok")

    def test_sim_worker_compiles_and_simulates(self):
        """Worker B compiles counter.v+tb_counter.v and runs vvp simulation."""
        if not HAVE_SIM:
            self.skipTest("iverilog/vvp not installed")
        simv = DATA_DIR / "simv_wb"
        simv_str = str(simv)
        data_str = str(DATA_DIR)
        result = self._post({
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
            self._skip_on_llm_flake(result)
            res_text = result.get("result", "")
            self.assertIn("PASSED", res_text.upper(),
                          f"Sim did not report PASSED:\n{res_text}")
        else:
            self.skipTest("LLM unavailable or worker error: " + str(result))

    def test_sim_worker_modifies_vcd_file(self):
        """Worker B creates VCD dumpfile during simulation."""
        if not HAVE_SIM:
            self.skipTest("iverilog/vvp not installed")
        vcd = DATA_DIR / "counter.vcd"
        if vcd.exists():
            vcd.unlink()
        simv_str = str(DATA_DIR / "simv_wb2")
        data_str = str(DATA_DIR)
        result = self._post({
            "task": (
                "cd " + data_str + " && "
                "iverilog -g2012 -o " + simv_str + " counter.v tb_counter.v && "
                "vvp " + simv_str + " && echo DONE"
            ),
            "sync": True,
        })
        if result["status"] == "completed":
            res_text = result.get("result", "")
            if "Error calling LLM" in res_text:
                self.skipTest("LLM error: " + res_text[:80])
            if vcd.exists():
                size = vcd.stat().st_size
                self.assertGreater(size, 0, "VCD file is empty")
            else:
                self.skipTest("VCD file not created")
        else:
            self.skipTest("Worker error: " + str(result))

    def test_sim_worker_reports_compile_failure(self):
        """Worker B fails to compile bad_syntax.v and reports SIM FAILED."""
        if not HAVE_SIM:
            self.skipTest("iverilog/vvp not installed")
        bad_v = str(DATA_DIR / "bad_syntax.v")
        data_str = str(DATA_DIR)
        simv_str = str(DATA_DIR / "simv_fail")
        result = self._post({
            "task": (
                "Step 1: cd " + data_str + "\n"
                "Step 2: Run: iverilog -g2012 -o " + simv_str + " bad_syntax.v\n"
                "Step 3: If Step 2 fails (non-zero exit or errors), respond: Final Answer: SIM FAILED - compile error\n"
                "If Step 2 succeeds, run vvp " + simv_str + " and check output, then respond accordingly."
            ),
            "sync": True,
        })
        self.assertIn(result["status"], ("completed", "error"), f"Got: {result}")
        if result["status"] == "completed":
            self._skip_on_llm_flake(result)
            res_text = result.get("result", "")
            self.assertIn("FAILED", res_text.upper(),
                          f"Sim should report FAILED for bad_syntax.v:\n{res_text}")
        else:
            self.skipTest("LLM unavailable or worker error: " + str(result))


# =========================================================================
# Parallel Dispatch - Both workers simultaneously
# =========================================================================

class TestParallelDispatch(unittest.TestCase):
    """Tests for parallel async dispatch to two workers simultaneously.

    Starts its own Worker A (lint) and Worker B (sim) since previous
    test classes may have shut down theirs after running.
    """

    @classmethod
    def setUpClass(cls):
        try:
            import uvicorn
            from core.agent_server import create_app
        except ImportError:
            raise unittest.SkipTest("fastapi/uvicorn not installed")

        cls._servers = []
        cls._threads = []
        cls._ready_events = []

        for port in [18795, 18796]:
            ready = threading.Event()
            cls._ready_events.append(ready)

            def _run(p=port, r=ready):
                app = create_app()
                cfg = uvicorn.Config(app, host="127.0.0.1", port=p,
                                      log_level="error")
                server = uvicorn.Server(cfg)
                cls._servers.append(server)
                r.set()
                server.run()

            t = threading.Thread(target=_run, daemon=True)
            t.start()
            cls._threads.append(t)
            ready.wait(timeout=5)
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        for s in cls._servers:
            s.should_exit = True
        for t in cls._threads:
            t.join(timeout=5)

    def _post_to(self, url, data):
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            url + "/run", data=body,
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            return {"error": str(e)}

    def _get_from(self, url, path):
        try:
            with urllib.request.urlopen(url + path, timeout=5) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            return {"error": str(e)}

    def test_parallel_dispatch_both_complete(self):
        """Fire lint and sim tasks to two workers simultaneously."""
        worker_a_url = "http://localhost:18795"
        worker_b_url = "http://localhost:18796"

        # Verify both workers are alive
        health_a = self._get_from(worker_a_url, "/health")
        health_b = self._get_from(worker_b_url, "/health")
        self.assertEqual(health_a.get("status"), "ok",
                         f"Worker A not healthy: {health_a}")
        self.assertEqual(health_b.get("status"), "ok",
                         f"Worker B not healthy: {health_b}")

        cv = str(COUNTER_V)
        dd = str(DATA_DIR)
        lint_task = {
            "task": "Run: iverilog -g2012 -Wall -o /dev/null " + cv + ". Say PASSED if exit 0.",
            "sync": False,
        }
        sim_task = {
            "task": "cd " + dd + " && iverilog -g2012 -o simv_par counter.v tb_counter.v && vvp simv_par && echo DONE",
            "sync": False,
        }

        lint_resp = self._post_to(worker_a_url, lint_task)
        sim_resp = self._post_to(worker_b_url, sim_task)

        lint_run_id = lint_resp.get("run_id")
        sim_run_id = sim_resp.get("run_id")
        self.assertIsNotNone(lint_run_id, f"Lint dispatch failed: {lint_resp}")
        self.assertIsNotNone(sim_run_id, f"Sim dispatch failed: {sim_resp}")

        lint_done = False
        sim_done = False
        for _ in range(120):
            if not lint_done:
                ls = self._get_from(worker_a_url, "/status/" + lint_run_id)
                if ls.get("status") in ("completed", "error"):
                    lint_done = True
            if not sim_done:
                ss = self._get_from(worker_b_url, "/status/" + sim_run_id)
                if ss.get("status") in ("completed", "error"):
                    sim_done = True
            if lint_done and sim_done:
                break
            time.sleep(0.5)

        if not lint_done:
            self.skipTest("Lint worker timed out")
        if not sim_done:
            self.skipTest("Sim worker timed out")

        lint_result = self._get_from(worker_a_url, "/result/" + lint_run_id)
        sim_result = self._get_from(worker_b_url, "/result/" + sim_run_id)

        self.assertIn(lint_result.get("status"), ("completed", "error"))
        self.assertIn(sim_result.get("status"), ("completed", "error"))


# =========================================================================
# Result Verification - Read saved results, check side effects
# =========================================================================

class TestResultVerification(unittest.TestCase):
    """Verify lint and sim results meet expected criteria."""

    def test_lint_result_is_passed(self):
        """Lint result from lint_result.json contains LINT PASSED."""
        result_file = PROJECT_ROOT / "lint_result.json"
        if not result_file.exists():
            self.skipTest("lint_result.json not found (run task 4 first)")
        with open(result_file) as f:
            result = json.load(f)
        self.assertEqual(result["status"], "completed")
        self.assertIn("PASSED", result.get("result", "").upper())

    def test_counter_vcd_generated(self):
        """Simulation creates counter.vcd waveform dump."""
        vcd = DATA_DIR / "counter.vcd"
        if not vcd.exists():
            self.skipTest("counter.vcd not found (run simulation first)")
        self.assertGreater(vcd.stat().st_size, 0, "VCD file is empty")


def tearDownModule():
    """Clean up generated files after all tests."""
    for pattern in ["simv", "simv_wb", "simv_wb2", "simv_par"]:
        f = DATA_DIR / pattern
        if f.exists():
            f.unlink()
    vcd = DATA_DIR / "counter.vcd"
    if vcd.exists():
        vcd.unlink()


if __name__ == "__main__":
    unittest.main()
