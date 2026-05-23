"""Tests for _resolve_worker_url single-worker vs orchestrator routing."""
import importlib
import os
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


def _load_module():
    """Import atlas_api_jobs with minimal stub dependencies."""
    # Provide stubs for heavy deps that may not be installed in test env
    stubs = [
        "fastapi", "fastapi.responses", "fastapi.middleware.cors",
        "anthropic", "pydantic",
    ]
    for name in stubs:
        if name not in sys.modules:
            sys.modules[name] = types.ModuleType(name)
            # fastapi sub-attrs needed at module level
            if name == "fastapi":
                sys.modules[name].FastAPI = object
                sys.modules[name].Request = object
                sys.modules[name].HTTPException = Exception
            if name == "fastapi.responses":
                sys.modules[name].JSONResponse = dict
                sys.modules[name].StreamingResponse = object
            if name == "fastapi.middleware.cors":
                sys.modules[name].CORSMiddleware = object
    # Import the module under test
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "atlas_api_jobs",
        os.path.join(os.path.dirname(__file__), "..", "src", "atlas_api_jobs.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception:
        # If full exec fails due to missing deps, re-import normally
        import atlas_api_jobs as mod  # type: ignore
    return mod


try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    import src.atlas_api_jobs as _m
    _resolve_worker_url = _m._resolve_worker_url
    _DEFAULT_SINGLE_MAIN_LOOP_PORT = _m._DEFAULT_SINGLE_MAIN_LOOP_PORT
    _DEFAULT_WORKER_PORTS = _m._DEFAULT_WORKER_PORTS
except Exception:
    _m = None  # type: ignore
    _resolve_worker_url = None  # type: ignore
    _DEFAULT_SINGLE_MAIN_LOOP_PORT = 5601
    _DEFAULT_WORKER_PORTS = {}

SINGLE_PORT_URL = f"http://127.0.0.1:{_DEFAULT_SINGLE_MAIN_LOOP_PORT}"

ALL_WORKFLOWS = [
    "ssot-gen", "fl-model-gen", "rtl-gen", "lint", "tb-gen",
    "sim", "coverage", "sim_debug", "syn", "sta", "pnr", "sta-post",
    "chat", "atcdmac100",
]

ORCHESTRATOR_PORT_MAP = {
    "ssot-gen":     5621,
    "fl-model-gen": 5622,
    "rtl-gen":      5623,
    "lint":         5624,
    "tb-gen":       5625,
    "sim":          5626,
    "coverage":     5627,
    "sim_debug":    5628,
    "syn":          5629,
    "sta":          5630,
    "pnr":          5631,
    "sta-post":     5632,
}


@unittest.skipIf(_resolve_worker_url is None, "atlas_api_jobs could not be imported")
class TestSingleMainLoopEnvVar(unittest.TestCase):
    """With ATLAS_SINGLE_MAIN_LOOP=1, all workflows must resolve to port 5601."""

    def setUp(self):
        # Clear any per-workflow env vars that would override
        for wf in ALL_WORKFLOWS:
            suffix = wf.upper().replace("-", "_")
            for key in (
                f"ATLAS_WORKER_URL_{suffix}",
                f"ATLAS_{suffix}_WORKER_URL",
                f"WORKER_URL_{suffix}",
            ):
                os.environ.pop(key, None)
        os.environ.pop("WORKER_URL_DEFAULT", None)

    def tearDown(self):
        os.environ.pop("ATLAS_SINGLE_MAIN_LOOP", None)
        os.environ.pop("ATLAS_EXEC_MODE", None)
        os.environ.pop("ATLAS_ORCHESTRATOR_MODE", None)

    def test_all_14_workflows_route_to_5601(self):
        os.environ["ATLAS_SINGLE_MAIN_LOOP"] = "1"
        # Ensure orchestrator mode is NOT forced on
        os.environ.pop("ATLAS_ORCHESTRATOR_MODE", None)
        os.environ["ATLAS_EXEC_MODE"] = "single-worker"
        for wf in ALL_WORKFLOWS:
            with self.subTest(workflow=wf):
                url = _resolve_worker_url(wf)
                self.assertEqual(url, SINGLE_PORT_URL,
                                 f"workflow={wf!r} expected {SINGLE_PORT_URL}, got {url!r}")

    def test_empty_workflow_routes_to_5601(self):
        os.environ["ATLAS_SINGLE_MAIN_LOOP"] = "1"
        os.environ["ATLAS_EXEC_MODE"] = "single-worker"
        url = _resolve_worker_url("")
        self.assertEqual(url, SINGLE_PORT_URL)

    def test_truthy_values_route_to_5601(self):
        for val in ("1", "true", "yes", "on"):
            with self.subTest(val=val):
                os.environ["ATLAS_SINGLE_MAIN_LOOP"] = val
                os.environ["ATLAS_EXEC_MODE"] = "single-worker"
                url = _resolve_worker_url("ssot-gen")
                self.assertEqual(url, SINGLE_PORT_URL)


@unittest.skipIf(_resolve_worker_url is None, "atlas_api_jobs could not be imported")
class TestSingleWorkerExecMode(unittest.TestCase):
    """exec_mode='single-worker' detected at request time routes to 5601."""

    def setUp(self):
        for wf in ALL_WORKFLOWS:
            suffix = wf.upper().replace("-", "_")
            for key in (
                f"ATLAS_WORKER_URL_{suffix}",
                f"ATLAS_{suffix}_WORKER_URL",
                f"WORKER_URL_{suffix}",
            ):
                os.environ.pop(key, None)
        os.environ.pop("WORKER_URL_DEFAULT", None)
        os.environ.pop("ATLAS_SINGLE_MAIN_LOOP", None)

    def tearDown(self):
        os.environ.pop("ATLAS_EXEC_MODE", None)
        os.environ.pop("ATLAS_DEFAULT_EXEC_MODE", None)
        os.environ.pop("ATLAS_ORCHESTRATOR_MODE", None)

    def test_exec_mode_single_worker_routes_to_5601(self):
        os.environ["ATLAS_EXEC_MODE"] = "single-worker"
        os.environ.pop("ATLAS_ORCHESTRATOR_MODE", None)
        for wf in ["ssot-gen", "rtl-gen", "sim", "sta"]:
            with self.subTest(workflow=wf):
                url = _resolve_worker_url(wf)
                self.assertEqual(url, SINGLE_PORT_URL)


@unittest.skipIf(_resolve_worker_url is None, "atlas_api_jobs could not be imported")
class TestOrchestratorModePerWorkflowPorts(unittest.TestCase):
    """Without ATLAS_SINGLE_MAIN_LOOP, orchestrator mode uses per-workflow ports."""

    def setUp(self):
        for wf in ALL_WORKFLOWS:
            suffix = wf.upper().replace("-", "_")
            for key in (
                f"ATLAS_WORKER_URL_{suffix}",
                f"ATLAS_{suffix}_WORKER_URL",
                f"WORKER_URL_{suffix}",
            ):
                os.environ.pop(key, None)
        os.environ.pop("WORKER_URL_DEFAULT", None)
        os.environ.pop("ATLAS_SINGLE_MAIN_LOOP", None)

    def tearDown(self):
        os.environ.pop("ATLAS_EXEC_MODE", None)
        os.environ.pop("ATLAS_ORCHESTRATOR_MODE", None)

    def _set_orchestrator(self):
        os.environ["ATLAS_ORCHESTRATOR_MODE"] = "1"
        os.environ.pop("ATLAS_EXEC_MODE", None)

    def test_ssot_gen_resolves_to_5621(self):
        self._set_orchestrator()
        self.assertEqual(_resolve_worker_url("ssot-gen"), "http://127.0.0.1:5621")

    def test_fl_model_gen_resolves_to_5622(self):
        self._set_orchestrator()
        self.assertEqual(_resolve_worker_url("fl-model-gen"), "http://127.0.0.1:5622")

    def test_rtl_gen_resolves_to_5623(self):
        self._set_orchestrator()
        self.assertEqual(_resolve_worker_url("rtl-gen"), "http://127.0.0.1:5623")

    def test_lint_resolves_to_5624(self):
        self._set_orchestrator()
        self.assertEqual(_resolve_worker_url("lint"), "http://127.0.0.1:5624")

    def test_tb_gen_resolves_to_5625(self):
        self._set_orchestrator()
        self.assertEqual(_resolve_worker_url("tb-gen"), "http://127.0.0.1:5625")

    def test_sim_resolves_to_5626(self):
        self._set_orchestrator()
        self.assertEqual(_resolve_worker_url("sim"), "http://127.0.0.1:5626")

    def test_coverage_resolves_to_5627(self):
        self._set_orchestrator()
        self.assertEqual(_resolve_worker_url("coverage"), "http://127.0.0.1:5627")

    def test_sim_debug_resolves_to_5628(self):
        self._set_orchestrator()
        self.assertEqual(_resolve_worker_url("sim_debug"), "http://127.0.0.1:5628")

    def test_syn_resolves_to_5629(self):
        self._set_orchestrator()
        self.assertEqual(_resolve_worker_url("syn"), "http://127.0.0.1:5629")

    def test_sta_resolves_to_5630(self):
        self._set_orchestrator()
        self.assertEqual(_resolve_worker_url("sta"), "http://127.0.0.1:5630")

    def test_pnr_resolves_to_5631(self):
        self._set_orchestrator()
        self.assertEqual(_resolve_worker_url("pnr"), "http://127.0.0.1:5631")

    def test_sta_post_resolves_to_5632(self):
        self._set_orchestrator()
        self.assertEqual(_resolve_worker_url("sta-post"), "http://127.0.0.1:5632")

    def test_all_orchestrator_ports_match_map(self):
        self._set_orchestrator()
        for wf, port in ORCHESTRATOR_PORT_MAP.items():
            with self.subTest(workflow=wf):
                url = _resolve_worker_url(wf)
                self.assertEqual(url, f"http://127.0.0.1:{port}")

    def test_single_main_loop_zero_does_not_force_single_worker(self):
        self._set_orchestrator()
        os.environ["ATLAS_SINGLE_MAIN_LOOP"] = "0"
        self.assertEqual(_resolve_worker_url("ssot-gen"), "http://127.0.0.1:5621")

    def test_worker_url_default_overrides_builtin_orchestrator_ports(self):
        self._set_orchestrator()
        os.environ["WORKER_URL_DEFAULT"] = "http://127.0.0.1:9999"
        self.assertEqual(_resolve_worker_url("rtl-gen"), "http://127.0.0.1:9999")

    def test_per_workflow_url_overrides_worker_url_default(self):
        self._set_orchestrator()
        os.environ["WORKER_URL_DEFAULT"] = "http://127.0.0.1:9999"
        os.environ["WORKER_URL_RTL_GEN"] = "http://127.0.0.1:9988"
        self.assertEqual(_resolve_worker_url("rtl-gen"), "http://127.0.0.1:9988")


@unittest.skipIf(_resolve_worker_url is None, "atlas_api_jobs could not be imported")
class TestLazyWorkerStart(unittest.TestCase):
    def setUp(self):
        os.environ.pop("WORKER_URL_DEFAULT", None)
        os.environ.pop("WORKER_URL_RTL_GEN", None)
        os.environ["ATLAS_LAZY_WORKERS"] = "1"
        os.environ["ATLAS_EXEC_MODE"] = "orchestrator"
        os.environ["ATLAS_SINGLE_MAIN_LOOP"] = "0"
        _m._LAZY_WORKER_PROCS.clear()

    def tearDown(self):
        os.environ.pop("ATLAS_LAZY_WORKERS", None)
        os.environ.pop("ATLAS_EXEC_MODE", None)
        os.environ.pop("ATLAS_SINGLE_MAIN_LOOP", None)
        os.environ.pop("WORKER_URL_DEFAULT", None)
        os.environ.pop("WORKER_URL_RTL_GEN", None)
        _m._LAZY_WORKER_PROCS.clear()

    def _job(self, root: str, worker: str = "http://127.0.0.1:5623") -> dict:
        return {
            "job_id": "job-1",
            "worker": worker,
            "workflow": "rtl-gen",
            "session": "u/ip/rtl-gen",
            "project_root": root,
            "model": "gpt-5.3-codex",
            "reasoning_effort": "high",
        }

    def test_lazy_start_skips_spawn_if_worker_becomes_ready_before_lock(self):
        class _Proc:
            pid = 123

            def poll(self):
                return None

        with tempfile.TemporaryDirectory() as tmp:
            health = [
                {"status": "unreachable", "error": "refused"},
                {"status": "ok", "workflow": "rtl-gen", "model": "gpt-5.3-codex"},
            ]
            popen_calls = []

            def _popen(cmd, **kwargs):
                popen_calls.append((cmd, kwargs))
                return _Proc()

            with patch.object(_m, "_probe_worker_health", side_effect=health), \
                 patch.object(_m.subprocess, "Popen", side_effect=_popen):
                _m._ensure_lazy_worker(self._job(tmp))

            self.assertEqual(len(popen_calls), 0)

    def test_lazy_start_spawns_after_confirmed_unreachable_health(self):
        class _Proc:
            pid = 123

            def poll(self):
                return None

        with tempfile.TemporaryDirectory() as tmp:
            health = [
                {"status": "unreachable", "error": "refused"},
                {"status": "unreachable", "error": "refused"},
                {"status": "ok", "workflow": "rtl-gen", "model": "gpt-5.3-codex"},
            ]
            popen_calls = []

            def _popen(cmd, **kwargs):
                popen_calls.append((cmd, kwargs))
                return _Proc()

            with patch.object(_m, "_probe_worker_health", side_effect=health), \
                 patch.object(_m.subprocess, "Popen", side_effect=_popen):
                _m._ensure_lazy_worker(self._job(tmp))

            self.assertEqual(len(popen_calls), 1)
            cmd = popen_calls[0][0]
            self.assertIn("--workflow", cmd)
            self.assertIn("rtl-gen", cmd)
            self.assertIn("--model", cmd)
            self.assertIn("gpt-5.3-codex", cmd)

    def test_lazy_start_does_not_spawn_for_remote_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(_m, "_probe_worker_health", return_value={"status": "unreachable"}), \
                 patch.object(_m.subprocess, "Popen") as popen:
                _m._ensure_lazy_worker(self._job(tmp, worker="http://10.0.0.5:5623"))
            popen.assert_not_called()

    def test_lazy_start_rejects_existing_wrong_workflow(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(
                _m,
                "_probe_worker_health",
                return_value={"status": "ok", "workflow": "lint", "model": "gpt-5.3-codex"},
            ), patch.object(_m.subprocess, "Popen") as popen:
                with self.assertRaisesRegex(RuntimeError, "worker mismatch"):
                    _m._ensure_lazy_worker(self._job(tmp))
            popen.assert_not_called()

    def test_direct_dispatch_lazy_helper_resolves_alias(self):
        with tempfile.TemporaryDirectory() as tmp:
            jobs = []

            def _capture(job):
                jobs.append(job)

            with patch.object(_m, "_ensure_lazy_worker", side_effect=_capture):
                _m._ensure_lazy_worker_for_direct_dispatch(
                    "ssot-gen",
                    "ssot-gen",
                    tmp,
                )

            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0]["worker"], "http://127.0.0.1:5621")
            self.assertEqual(jobs[0]["workflow"], "ssot-gen")
            self.assertEqual(jobs[0]["session"], "direct/ssot-gen")
            self.assertEqual(jobs[0]["project_root"], tmp)


if __name__ == "__main__":
    unittest.main()
