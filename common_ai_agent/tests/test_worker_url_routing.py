"""Tests for _resolve_worker_url single-worker vs orchestrator routing."""
import importlib
import os
import sys
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


if __name__ == "__main__":
    unittest.main()
