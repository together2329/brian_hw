from __future__ import annotations

import json
import socket
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from typing import Iterator

import pytest
from fastapi.testclient import TestClient


# Phase 3 changed the contract of POST /api/pipeline/orchestrator/chat. The
# endpoint no longer dispatches synchronously from keyword parsing; it now
# spawns an LLM-driven orchestrator loop and returns {ok, run_id, status, ip}.
# Tests below were written against the legacy keyword-dispatch contract and
# need to be rewritten to drive the new async loop (stub LLM caller + poll
# GET /api/orchestrator/runs/{run_id}). Until they are rewritten they are
# skipped. The new contract is covered by tests/test_orchestrator_route.py.
_PHASE3_SKIP = pytest.mark.skip(
    reason=(
        "Phase 3 endpoint contract change: keyword-dispatch contract removed. "
        "Rewrite this test against the async runner contract; see "
        "tests/test_orchestrator_route.py for the new shape."
    )
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

_WORKFLOWS = [
    "SSOT_GEN", "FL_MODEL_GEN", "RTL_GEN", "LINT", "TB_GEN",
    "SIM", "COVERAGE", "SIM_DEBUG", "SYN", "STA", "PNR", "STA_POST",
    "CONTRACT_REFLECTION",
]


@pytest.fixture(autouse=True)
def _isolate_worker_env(monkeypatch):
    """Keep mock-worker tests independent of repo .env and live workers."""
    for suffix in _WORKFLOWS:
        for key in (
            f"ATLAS_WORKER_URL_{suffix}",
            f"ATLAS_{suffix}_WORKER_URL",
            f"WORKER_URL_{suffix}",
            f"ATLAS_WORKER_MODEL_{suffix}",
            f"ATLAS_{suffix}_MODEL",
            f"WORKER_MODEL_{suffix}",
            f"ATLAS_WORKER_REASONING_EFFORT_{suffix}",
            f"ATLAS_WORKER_REASONING_{suffix}",
            f"ATLAS_{suffix}_REASONING_EFFORT",
            f"ATLAS_{suffix}_EFFORT",
            f"WORKER_REASONING_EFFORT_{suffix}",
        ):
            monkeypatch.setenv(key, "")
    monkeypatch.setenv("WORKER_URL_DEFAULT", "http://127.0.0.1:9")
    monkeypatch.setenv("ATLAS_LAZY_WORKERS", "0")
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODEL", "")
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_REASONING_EFFORT", "")


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_port(port: int, timeout_s: float = 5.0) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.1)
            try:
                sock.connect(("127.0.0.1", port))
                return
            except OSError:
                time.sleep(0.05)
    raise RuntimeError(f"server did not bind port {port}")


class _MockWorkerState:
    def __init__(
        self,
        name: str,
        fail_workflows: set[str] | None = None,
        write_artifacts: bool = True,
    ) -> None:
        self.name = name
        self.fail_workflows = fail_workflows or set()
        self.write_artifacts = write_artifacts
        self.lock = threading.Lock()
        self.requests: list[dict] = []
        self.status_hits: list[str] = []
        self.result_hits: list[str] = []

    def add_run(self, payload: dict) -> str:
        with self.lock:
            run_id = f"{self.name}-run-{len(self.requests) + 1}"
            self.requests.append({"run_id": run_id, "payload": payload})
            return run_id

    def runs_for_workflow(self, workflow: str) -> list[dict]:
        with self.lock:
            return [
                item for item in self.requests
                if item.get("payload", {}).get("workflow") == workflow
            ]

    def workflow_for_run(self, run_id: str) -> str:
        with self.lock:
            for item in self.requests:
                if item.get("run_id") == run_id:
                    return str(item.get("payload", {}).get("workflow") or "")
        return ""


_VALID_RTL_MODULE = (
    "module {ip}(\n"
    "    input logic clk,\n"
    "    input logic rst_n,\n"
    "    output logic done\n"
    ");\n"
    "    logic done_q;\n"
    "    always @(posedge clk or negedge rst_n) begin\n"
    "        if (!rst_n) begin\n"
    "            done_q <= 1'b0;\n"
    "        end else begin\n"
    "            done_q <= 1'b1;\n"
    "        end\n"
    "    end\n"
    "    assign done = done_q;\n"
    "endmodule\n"
)


def _write_minimal_valid_ssot_rtl_fixture(ip_dir: Path, ip: str) -> None:
    """Write the smallest on-disk artifact set that the deterministic RTL
    completion-evidence contract accepts.

    This is the disk-artifact half of the positive-path fixture. It makes
    ``_rtl_current_completion_evidence_passes`` return True (valid filelist,
    placeholder-free RTL, passing compile + lint, a closed rtl_todo_plan gate)
    and writes a ``logs/stage_engine/ssot-rtl.json`` with ``status=pass``.

    IMPORTANT (verified against the production gate): the strict gate in
    ``_enforce_completion_evidence_gate`` calls ``_refresh_completed_stage_evidence``
    which re-runs the REAL ``WorkflowStageEngine.run_stage("ssot-rtl")`` and the
    real ``check_rtl_disk.sh`` disk validator against this fixture. With only a
    minimal SSOT (no function_model/cycle_model) the engine rewrites
    ``rtl/rtl_todo_plan.json`` to a blocked gate and the disk validator rejects a
    trivial module. So positive green tests MUST pair this fixture with the
    rtl recovery/failure monkeypatch (see ``_patch_rtl_gate_for_fixture``), the
    same pattern ``test_full_ip_pipeline_can_complete_all_stages_across_two_workers``
    already uses. All fixture files live under ``tmp_path``; never write into
    tracked IP directories.
    """
    def write(rel: str, text: str) -> None:
        path = ip_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    # SSOT with enough function_model/cycle_model shape that ssot-rtl does not
    # short-circuit to "SSOT not found" / "missing locked truth".
    write(
        f"yaml/{ip}.ssot.yaml",
        (
            f"ip: {ip}\n"
            "sections:\n"
            "  - name: interface\n"
            "    description: minimal valid fixture\n"
            "function_model:\n"
            "  summary: done asserts one cycle after reset deasserts\n"
            "cycle_model:\n"
            "  summary: single-cycle latency\n"
            "requirements:\n"
            "  - id: REQ_DONE\n"
            "    text: done must assert after reset\n"
        ),
    )
    write(f"rtl/{ip}.sv", _VALID_RTL_MODULE.format(ip=ip))
    # Local validators expect the filelist to reference the source with the
    # rtl/<ip>.sv path convention.
    write(f"list/{ip}.f", f"rtl/{ip}.sv\n")
    write("rtl/rtl_compile.json", '{"passed":true,"errors":0,"diagnostics":0,"returncode":0}\n')
    write("lint/dut_lint.json", '{"passed":true,"errors":0,"warnings":0,"pyslang":[],"verilator":[]}\n')
    write(
        "rtl/rtl_todo_plan.json",
        json.dumps(
            {
                "gate": {
                    "status": "pass",
                    "all_required_todos_pass": True,
                    "open_required_todos": 0,
                    "static_missing": 0,
                    "blocking_questions": 0,
                },
                "todo_completion": {
                    "all_required_todos_pass": True,
                    "open_required_tasks": 0,
                },
                "todos": [],
            }
        )
        + "\n",
    )
    write(
        "logs/stage_engine/ssot-rtl.json",
        json.dumps(
            {
                "stage": "ssot-rtl",
                "status": "pass",
                "headline": "[ssot-rtl] PASS: RTL evidence closed",
                "metadata": {
                    "rtl_todo_plan": {
                        "gate": {
                            "status": "pass",
                            "all_required_todos_pass": True,
                            "open_required_todos": 0,
                            "static_missing": 0,
                            "blocking_questions": 0,
                        }
                    }
                },
            }
        )
        + "\n",
    )


def _write_blocked_ssot_rtl_fixture(ip_dir: Path, ip: str, reason: str) -> None:
    """Write a stage-engine ``ssot-rtl.json`` with ``status=blocked`` plus a
    matching blocked rtl_todo_plan gate, simulating a stage that cannot proceed
    (e.g. missing locked truth / open human gate). Used by negative tests that
    assert the owning job becomes ``blocked`` (not ``error``)."""
    def write(rel: str, text: str) -> None:
        path = ip_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    write(f"rtl/{ip}.sv", _VALID_RTL_MODULE.format(ip=ip))
    write(f"list/{ip}.f", f"rtl/{ip}.sv\n")
    blocked_gate = {
        "status": "blocked",
        "all_required_todos_pass": False,
        "open_required_todos": 2,
        "static_missing": 0,
        "blocking_questions": 1,
    }
    write(
        "rtl/rtl_todo_plan.json",
        json.dumps({"gate": blocked_gate, "todos": []}) + "\n",
    )
    write(
        "logs/stage_engine/ssot-rtl.json",
        json.dumps(
            {
                "stage": "ssot-rtl",
                "status": "blocked",
                "headline": f"[ssot-rtl] blocked: {reason}",
                "metadata": {"rtl_todo_plan": {"gate": blocked_gate}},
            }
        )
        + "\n",
    )


def _patch_rtl_gate_for_fixture(monkeypatch, jobs_module, ip: str, tmp_path: Path) -> None:
    """Pair the on-disk valid fixture with the rtl recovery/failure monkeypatch
    so the strict gate's engine re-run cannot clobber the fixture into blocked.

    This mirrors ``test_full_ip_pipeline_can_complete_all_stages_across_two_workers``:
    the gate calls ``_refresh_completed_stage_evidence`` (real engine) before
    ``_job_artifact_failure``/``_job_artifact_recovery``; by stubbing the rtl
    failure to (False, "") and rtl recovery to (True, ...) the gate passes on the
    fixture evidence regardless of what the engine rewrites on disk. Non-rtl
    stages still run their real validators."""
    real_recovery = jobs_module._job_artifact_recovery
    real_failure = jobs_module._job_artifact_failure

    def _mock_recovery(job: dict, project_root: Path) -> tuple[bool, str]:
        stage = str(job.get("stage_id") or job.get("workflow") or "")
        workflow = str(job.get("workflow") or "")
        if stage == "rtl" or workflow == "rtl-gen":
            compile_path = tmp_path / ip / "rtl" / "rtl_compile.json"
            return compile_path.is_file(), "test mock validated artifact: rtl/rtl_compile.json"
        return real_recovery(job, project_root)

    def _mock_failure(job: dict, project_root: Path) -> tuple[bool, str]:
        stage = str(job.get("stage_id") or job.get("workflow") or "")
        workflow = str(job.get("workflow") or "")
        if stage == "rtl" or workflow == "rtl-gen":
            return False, ""
        return real_failure(job, project_root)

    monkeypatch.setattr(jobs_module, "_job_artifact_recovery", _mock_recovery)
    monkeypatch.setattr(jobs_module, "_job_artifact_failure", _mock_failure)


def _write_mock_stage_artifact(payload: dict) -> None:
    project_root = Path(str(payload.get("project_root") or ""))
    ip = str(payload.get("ip") or "").strip()
    if not project_root or not ip:
        return
    ip_dir = project_root / ip
    stage = str(payload.get("stage_id") or "").strip()
    workflow = str(payload.get("workflow") or "").strip()

    def write(rel: str, text: str) -> None:
        path = ip_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    if stage == "ssot" or workflow == "ssot-gen":
        write(f"yaml/{ip}.ssot.yaml", f"ip: {ip}\nrequirements: []\n")
    elif stage == "fl-model":
        write("model/fl_model_check.json", '{"status":"pass"}\n')
    elif stage == "cl-model":
        write("model/cl_model_check.json", '{"status":"pass"}\n')
    elif stage == "equivalence":
        write("verify/equivalence_goals.json", '{"status":"pass"}\n')
    elif stage == "rtl" or workflow == "rtl-gen":
        # Write the full minimal-valid RTL evidence set (Task 2) so the strict
        # completion-evidence gate accepts it. Paired with
        # _patch_rtl_gate_for_fixture in positive tests, since the gate's engine
        # re-run + check_rtl_disk.sh would otherwise clobber/reject a cheap fixture.
        _write_minimal_valid_ssot_rtl_fixture(ip_dir, ip)
    elif stage == "lint" or workflow == "lint":
        write("lint/dut_lint.json", '{"errors":0,"warnings":0,"pyslang":[],"verilator":[]}\n')
    elif stage == "tb" or workflow == "tb-gen":
        write("tb/run_tests.py", "def test_smoke():\n    assert True\n")
    elif stage == "sim" or workflow == "sim":
        write("sim/results.xml", '<testsuite tests="1" failures="0" errors="0"></testsuite>\n')
    elif stage == "coverage" or workflow == "coverage":
        write("cov/coverage.json", '{"status":"pass","line":100,"condition":100,"function":100}\n')
    elif stage == "sim-debug" or (workflow == "sim_debug" and stage != "goal-audit"):
        write("sim/mismatch_classification.json", '{"status":"pass","owner_workflow":""}\n')
        write("sim/source_tracking.json", '{"top":"dut","source_files":[]}\n')
    elif stage == "syn" or workflow == "syn":
        write("syn/out/synth.v", f"module {ip}; endmodule\n")
    elif stage == "sta" or workflow == "sta":
        write("sta/out/wns.json", '{"wns":0.1}\n')
    elif stage == "pnr" or workflow == "pnr":
        write("pnr/out/routed.v", f"module {ip}; endmodule\n")
    elif stage == "sta-post" or workflow == "sta-post":
        write("sta-post/out/wns.json", '{"wns":0.1}\n')
    elif stage == "contract-check" or workflow == "contract-reflection":
        write("signoff/contract_check.json", '{"status":"pass","summary":{"evidence_failed":0,"evidence_passed":1,"evidence_total":1,"reflection_failed":0,"reflection_passed":1,"reflection_total":1}}\n')
        write("signoff/evidence_contract_coverage.json", '{"status":"pass","summary":{"failed":0,"passed":1,"total":1}}\n')
        write("signoff/contract_reflection_coverage.json", '{"status":"pass","summary":{"failed":0,"passed":1,"total":1}}\n')
    elif stage == "goal-audit":
        write("sim/fl_rtl_goal_audit.json", '{"status":"pass","summary":{"blockers":[]}}\n')


@contextmanager
def _mock_worker(
    name: str,
    *,
    fail_workflows: set[str] | None = None,
    write_artifacts: bool = True,
) -> Iterator[tuple[str, _MockWorkerState]]:
    state = _MockWorkerState(name, fail_workflows=fail_workflows, write_artifacts=write_artifacts)

    class Handler(BaseHTTPRequestHandler):
        def _json(self, status: int, body: dict) -> None:
            data = json.dumps(body).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self) -> None:  # noqa: N802 - stdlib handler hook
            if self.path != "/run":
                self._json(404, {"error": "not found"})
                return
            size = int(self.headers.get("Content-Length") or "0")
            payload = json.loads(self.rfile.read(size).decode("utf-8") or "{}")
            if state.write_artifacts and str(payload.get("workflow") or "") not in state.fail_workflows:
                _write_mock_stage_artifact(payload)
            self._json(200, {"run_id": state.add_run(payload)})

        def do_GET(self) -> None:  # noqa: N802 - stdlib handler hook
            if self.path.startswith("/status/"):
                run_id = self.path.rsplit("/", 1)[-1]
                state.status_hits.append(run_id)
                workflow = state.workflow_for_run(run_id)
                status = "error" if workflow in state.fail_workflows else "completed"
                self._json(200, {"status": status, "iterations": 1})
                return
            if self.path.startswith("/result/"):
                run_id = self.path.rsplit("/", 1)[-1]
                state.result_hits.append(run_id)
                workflow = state.workflow_for_run(run_id)
                if workflow in state.fail_workflows:
                    self._json(200, {
                        "result": f"{name} failed {run_id}",
                        "files_modified": [],
                        "error": "mock failure",
                        "execution_time_ms": 10,
                    })
                    return
                self._json(200, {
                    "result": f"{name} completed {run_id}",
                    "files_modified": [],
                    "execution_time_ms": 10,
                })
                return
            self._json(404, {"error": "not found"})

        def log_message(self, *_args) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", _free_port()), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", state
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


@contextmanager
def _agent_server_worker(monkeypatch, calls: list[dict]) -> Iterator[str]:
    import uvicorn
    from core import agent_server

    def fake_react_task(
        entry,
        task: str,
        model: str = "",
        todos=None,
        context: str = "",
        workflow: str = "",
        session_name: str = "",
        ip: str = "",
        rtl_version_id: str = "",
        project_root: str = "",
        artifact_versions=None,
        reasoning_effort: str = "",
        custom_system_prompt: str = "",
        custom_allowed_tools=None,
        custom_agent: str = "",
        custom_agent_owner_id: str = "",
    ) -> None:
        entry.status = "running"
        entry.started_at = time.time()
        entry.add_log("system", f"fake worker executing {workflow}", role="system")
        _write_mock_stage_artifact({
            "project_root": project_root,
            "ip": ip,
            "workflow": workflow,
            "stage_id": "lint" if workflow == "lint" else ("rtl" if workflow == "rtl-gen" else workflow),
        })
        calls.append({
            "run_id": entry.run_id,
            "workflow": workflow,
            "session": session_name,
            "ip": ip,
            "rtl_version_id": rtl_version_id,
            "project_root": project_root,
            "artifact_versions": artifact_versions or [],
            "context": context,
            "task": task,
        })
        entry.status = "completed"
        entry.finished_at = time.time()
        entry.result = {
            "run_id": entry.run_id,
            "status": "completed",
            "result": f"completed {workflow}",
            "files_modified": [],
            "error": "",
            "execution_time_ms": 1,
        }

    monkeypatch.setattr(agent_server, "_run_react_task", fake_react_task)
    monkeypatch.setattr(agent_server, "_PERSISTENCE_ENABLED", False)
    with agent_server._runs_lock:
        agent_server._runs.clear()

    port = _free_port()
    app = agent_server.create_app()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    _wait_for_port(port)
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        thread.join(timeout=5)
        with agent_server._runs_lock:
            agent_server._runs.clear()


def _make_client(tmp_path: Path, monkeypatch) -> TestClient:
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_ADMIN_AUTH_MODE", "db")
    monkeypatch.setenv("ATLAS_ADMIN_LOGIN_REQUIRED", "1")
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.delenv("ATLAS_LOCAL_ADMIN", raising=False)
    monkeypatch.delenv("ATLAS_ADMIN_BYPASS", raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = TestClient(atlas_ui.create_app())
    reg = client.post("/api/auth/register", json={"username": "u", "password": "pw"})
    assert reg.status_code == 200, reg.text
    return client


def _make_unauthenticated_client(tmp_path: Path, monkeypatch) -> TestClient:
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_ADMIN_AUTH_MODE", "db")
    monkeypatch.setenv("ATLAS_ADMIN_LOGIN_REQUIRED", "1")
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.delenv("ATLAS_LOCAL_ADMIN", raising=False)
    monkeypatch.delenv("ATLAS_ADMIN_BYPASS", raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    return TestClient(atlas_ui.create_app())


def test_pipeline_state_and_progress_debug_reject_unauthenticated_multiuser_scope(
    tmp_path: Path,
    monkeypatch,
) -> None:
    client = _make_unauthenticated_client(tmp_path, monkeypatch)

    state_resp = client.get("/api/pipeline/state?ip=unauth_ip&workspace_session=alt")
    progress_resp = client.get("/api/pipeline/progress-debug?ip=unauth_ip&workspace_session=alt")

    assert state_resp.status_code == 401
    assert progress_resp.status_code == 401


def test_handoff_routes_reject_unauthenticated_multiuser_scope(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from src import handoff_queue as hq

    ip = "handoff_unauth_ip"
    ip_dir = tmp_path / ip
    ip_dir.mkdir()
    record = {
        "schema": hq.SCHEMA,
        "handoff_id": hq.make_handoff_id(ip, "sim-debug", "rtl-gen", "BLOCK"),
        "ip": ip,
        "from_workflow": "sim-debug",
        "to_workflow": "rtl-gen",
        "scope": hq.make_scope(user_id="u", session_id=f"u/alt/{ip}/orchestrator", pipeline_run_id="P"),
    }
    hq.write_pending(ip_dir, record)
    client = _make_unauthenticated_client(tmp_path, monkeypatch)

    list_resp = client.get(f"/api/handoff/list?ip={ip}&workflow=rtl-gen&workspace_session=alt")
    save_resp = client.post(
        "/api/handoff/save",
        json={
            "ip": ip,
            "from_workflow": "sim-debug",
            "to_workflow": "rtl-gen",
            "workspace_session": "alt",
            "session_id": f"u/alt/{ip}/orchestrator",
        },
    )
    take_resp = client.post(
        "/api/handoff/take",
        json={
            "ip": ip,
            "workflow": "rtl-gen",
            "workspace_session": "alt",
            "session_id": f"u/alt/{ip}/orchestrator",
        },
    )

    assert list_resp.status_code == 401
    assert save_resp.status_code == 401
    assert take_resp.status_code == 401
    assert hq.get(ip_dir, record["handoff_id"])[0] == "pending"


def test_pipeline_state_hides_ownerless_legacy_db_runs_from_scoped_user(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from core.atlas_db import AtlasDB

    client = _make_client(tmp_path, monkeypatch)
    ip = "ownerless_legacy_state_ip"
    scoped_root = tmp_path / "u" / "alt"
    with AtlasDB(str(tmp_path / "atlas.db")) as db:
        workspace = db.upsert_workspace("alt", owner_user_id="", local_path=str(scoped_root))
        ip_row = db.upsert_ip_block(workspace["id"], ip)
        run = db.start_workflow_run(
            session_id=f"legacy/alt/{ip}/ssot-gen",
            workspace_id=str(workspace["id"] or ""),
            ip_id=str(ip_row["id"] or ""),
            workflow="ssot-gen",
            status="running",
        )
        db.finish_workflow_run(run["id"], status="error", error_summary="legacy leaked state")

    resp = client.get(f"/api/pipeline/state?ip={ip}&workspace_session=alt")

    assert resp.status_code == 200, resp.text
    stage = resp.json()["stages"]["ssot"]
    assert stage["state"] != "failed"
    assert "legacy leaked state" not in json.dumps(resp.json())


def test_pipeline_state_hides_foreign_rtl_version_from_scoped_user(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from core.atlas_db import AtlasDB

    client = _make_client(tmp_path, monkeypatch)
    ip = "foreign_rtl_state_ip"
    foreign_root = tmp_path / "bob" / "alt"

    with AtlasDB(str(tmp_path / "atlas.db")) as db:
        bob = db.ensure_user_by_username("bob")
        workspace = db.upsert_workspace(
            "alt",
            owner_user_id=str(bob["id"] or ""),
            local_path=str(foreign_root),
        )
        ip_row = db.upsert_ip_block(workspace["id"], ip)
        db.register_rtl_version(
            ip_id=str(ip_row["id"] or ""),
            workspace_id=str(workspace["id"] or ""),
            version="foreign-rtl-v001",
            rtl_root=str(foreign_root / ip / "rtl"),
        )

    resp = client.get(f"/api/pipeline/state?ip={ip}&workspace_session=alt")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body.get("rtl_version_id") in (None, "")
    assert "foreign-rtl-v001" not in json.dumps(body)


def test_pipeline_dispatch_fans_out_to_other_worker_and_surfaces_handoff_state(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from src import handoff_queue as hq
    import atlas_api_jobs as jobs

    ip = "worker_pipe_ip"
    user_workspace_root = tmp_path / "u" / "default"
    ip_dir = user_workspace_root / ip
    # Minimal valid SSOT/RTL evidence so the strict completion gate accepts the
    # rtl stage (Task 2). Paired with _patch_rtl_gate_for_fixture below.
    _write_minimal_valid_ssot_rtl_fixture(ip_dir, ip)

    handoff = {
        "schema": hq.SCHEMA,
        "handoff_id": hq.make_handoff_id(ip, "sim-debug", "rtl-gen", "EQ_READBACK"),
        "ip": ip,
        "from_workflow": "sim-debug",
        "to_workflow": "rtl-gen",
        "scope": hq.make_scope(user_id="u", session_id="S", pipeline_run_id="P"),
        "reason": "scoreboard mismatch needs RTL repair",
        "goal_ids": ["EQ_READBACK"],
    }
    hq.write_pending(ip_dir, handoff)

    with jobs._jobs_lock:
        jobs._jobs.clear()

    _patch_rtl_gate_for_fixture(monkeypatch, jobs, ip, user_workspace_root)

    with _mock_worker("rtl") as (rtl_url, rtl_worker), _mock_worker("other") as (other_url, other_worker):
        monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "1")
        monkeypatch.setenv("WORKER_URL_DEFAULT", rtl_url)
        monkeypatch.setenv("WORKER_URL_RTL_GEN", rtl_url)
        monkeypatch.setenv("WORKER_URL_LINT", other_url)
        monkeypatch.setenv("WORKER_URL_TB_GEN", other_url)
        monkeypatch.setenv("WORKER_URL_SYN", other_url)

        client = _make_client(tmp_path, monkeypatch)
        state_before = client.get(f"/api/pipeline/state?ip={ip}").json()
        assert state_before["orchestrator"]["enabled"] is True
        assert state_before["orchestrator"]["pending_handoffs"] == 1
        assert state_before["handoffs_by_workflow"]["rtl-gen"]["latest"]["handoff_id"] == handoff["handoff_id"]

        dispatch = client.post("/api/pipeline/dispatch", json={
            "ip": ip,
            "model": "gpt-5.3-codex",
            "schedule": "auto",
            "stages": ["rtl", "lint", "tb", "syn"],
        })
        assert dispatch.status_code == 200, dispatch.text
        dispatch_body = dispatch.json()
        assert dispatch_body["schedule"] == "dag"
        assert [job["stage_id"] for job in dispatch_body["jobs"]] == ["rtl", "lint", "tb", "syn"]

        jobs_resp = client.get("/api/jobs")
        assert jobs_resp.status_code == 200, jobs_resp.text
        job_rows = jobs_resp.json()["jobs"]
        assert {row["stage_id"] for row in job_rows} == {"rtl", "lint", "tb", "syn"}
        assert all(row["status"] == "completed" for row in job_rows)

        assert len(rtl_worker.runs_for_workflow("rtl-gen")) == 1
        assert len(other_worker.runs_for_workflow("lint")) == 1
        assert len(other_worker.runs_for_workflow("tb-gen")) == 1
        assert len(other_worker.runs_for_workflow("syn")) == 1
        assert len(other_worker.status_hits) == 3
        assert len(other_worker.result_hits) == 3

        for item in other_worker.requests:
            payload = item["payload"]
            assert payload["project_root"] == str(user_workspace_root)
            assert payload["source_root"].endswith("common_ai_agent")
            assert payload["ip"] == ip
            assert payload["session"].startswith(f"u/default/{ip}/pipeline/{dispatch_body['pipeline_id']}/")
            assert "rtl_version_id" in payload, payload
            assert "rtl_version_id:" in payload["context"]
            assert "write_boundary: only modify files under" in payload["task"]

    with jobs._jobs_lock:
        jobs._jobs.clear()


def test_pipeline_dispatch_can_drive_real_agent_server_worker_endpoints(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs

    ip = "real_worker_pipe_ip"
    user_workspace_root = tmp_path / "u" / "default"
    ip_dir = user_workspace_root / ip
    # Minimal valid SSOT/RTL evidence created before dispatch so the strict
    # completion gate accepts the rtl stage (Task 5). The agent-server worker
    # re-writes the same valid evidence after /run via _write_mock_stage_artifact.
    _write_minimal_valid_ssot_rtl_fixture(ip_dir, ip)

    with jobs._jobs_lock:
        jobs._jobs.clear()

    _patch_rtl_gate_for_fixture(monkeypatch, jobs, ip, user_workspace_root)

    worker_calls: list[dict] = []
    with _agent_server_worker(monkeypatch, worker_calls) as rtl_url, _agent_server_worker(monkeypatch, worker_calls) as lint_url:
        # Orchestrator mode so the DAG schedule fans out across owner workers
        # (single-worker mode routes everything to the single-main-loop port).
        monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "1")
        monkeypatch.setenv("WORKER_URL_DEFAULT", rtl_url)
        monkeypatch.setenv("WORKER_URL_RTL_GEN", rtl_url)
        monkeypatch.setenv("WORKER_URL_LINT", lint_url)

        client = _make_client(tmp_path, monkeypatch)
        dispatch = client.post("/api/pipeline/dispatch", json={
            "ip": ip,
            "model": "gpt-5.3-codex",
            "schedule": "auto",
            "stages": ["rtl", "lint"],
        })
        assert dispatch.status_code == 200, dispatch.text
        assert dispatch.json()["schedule"] == "dag"

        rows = []
        # _refresh_tracked_jobs rate-limits worker polls to one per 1.5s per
        # job, and the worker executor's thread may take a tick to fire — give
        # the dispatch enough room to round-trip through pending→running→completed.
        for _ in range(50):
            jobs_resp = client.get("/api/jobs")
            assert jobs_resp.status_code == 200, jobs_resp.text
            rows = jobs_resp.json()["jobs"]
            if len(rows) == 2 and all(row["status"] == "completed" for row in rows):
                break
            time.sleep(0.2)

        assert {row["stage_id"] for row in rows} == {"rtl", "lint"}
        assert all(row["status"] == "completed" for row in rows), [
            {
                "stage_id": row.get("stage_id"),
                "status": row.get("status"),
                "error": row.get("error"),
                "run_id": row.get("run_id"),
                "worker": row.get("worker"),
            }
            for row in rows
        ]
        assert [call["workflow"] for call in worker_calls] == ["rtl-gen", "lint"]
        lint_call = worker_calls[1]
        assert lint_call["rtl_version_id"]
        assert lint_call["ip"] == ip
        assert lint_call["project_root"] == str(user_workspace_root)
        assert lint_call["session"].startswith(f"u/default/{ip}/pipeline/{dispatch.json()['pipeline_id']}/")
        assert "rtl_version_id:" in lint_call["context"]

    with jobs._jobs_lock:
        jobs._jobs.clear()


def test_multiuser_pipeline_dispatch_scopes_worker_sessions_by_owner(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs

    ip = "shared_pipe_ip"
    (tmp_path / ip / "rtl").mkdir(parents=True)
    user_workspace_root = tmp_path / "u" / "default"
    (user_workspace_root / ip / "rtl").mkdir(parents=True)

    with jobs._jobs_lock:
        jobs._jobs.clear()

    with _mock_worker("rtl") as (rtl_url, rtl_worker):
        monkeypatch.setenv("ATLAS_MULTI_USER", "1")
        monkeypatch.setenv("WORKER_URL_RTL_GEN", rtl_url)

        client = _make_client(tmp_path, monkeypatch)
        dispatch = client.post("/api/pipeline/dispatch", json={
            "ip": ip,
            "schedule": "auto",
            "stages": ["rtl"],
        })

        assert dispatch.status_code == 200, dispatch.text
        dispatch_body = dispatch.json()
        pipeline_id = dispatch_body["pipeline_id"]
        assert dispatch_body["pipeline_run_id"] == pipeline_id
        assert dispatch_body["user_id"] == "u"
        assert dispatch_body["jobs"][0]["pipeline_run_id"] == pipeline_id
        assert dispatch_body["jobs"][0]["user_id"] == "u"
        assert len(rtl_worker.runs_for_workflow("rtl-gen")) == 1
        payload = rtl_worker.requests[0]["payload"]
        assert payload["session"].startswith(f"u/default/{ip}/pipeline/{pipeline_id}/")
        assert payload["pipeline_id"] == pipeline_id
        assert payload["pipeline_run_id"] == pipeline_id
        assert payload["user_id"] == "u"
        assert payload["stage_id"] == "rtl"
        assert payload["project_root"] == str(user_workspace_root)
        assert payload["scope_path"] == ip
        assert (user_workspace_root / ip / "rtl" / "rtl_compile.json").is_file()
        assert not (tmp_path / ip / "rtl" / "rtl_compile.json").exists()
        jobs_resp = client.get("/api/jobs")
        assert jobs_resp.status_code == 200, jobs_resp.text
        rows = jobs_resp.json()["jobs"]
        assert len(rows) == 1
        assert rows[0]["status"] == "completed"
        assert rows[0]["project_root"] == str(user_workspace_root)

    with jobs._jobs_lock:
        jobs._jobs.clear()


def test_job_dispatch_uses_session_root_in_single_user_desktop_mode(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs
    import src.atlas_ui as atlas_ui

    ip = "desktop_ip"
    source_root = tmp_path / "source-root"
    atlas_root = tmp_path / "atlas-root"
    workspace_root = atlas_root / "brian" / "s2"
    (workspace_root / ip / "yaml").mkdir(parents=True)
    (workspace_root / ip / "yaml" / f"{ip}.ssot.yaml").write_text(
        f"ip: {ip}\nsections:\n  - name: interface\n",
        encoding="utf-8",
    )
    source_root.mkdir()

    with jobs._jobs_lock:
        jobs._jobs.clear()

    try:
        with _mock_worker("ssot") as (ssot_url, ssot_worker):
            monkeypatch.setenv("ATLAS_MULTI_USER", "0")
            monkeypatch.setenv("ATLAS_ADMIN_LOGIN_REQUIRED", "0")
            monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
            monkeypatch.setenv("ATLAS_ROOT", str(atlas_root))
            monkeypatch.setenv("WORKER_URL_SSOT_GEN", ssot_url)
            monkeypatch.chdir(source_root)
            monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", source_root)

            client = TestClient(atlas_ui.create_app())
            response = client.post(
                "/api/job/dispatch",
                json={
                    "workflow": "ssot-gen",
                    "ip": ip,
                    "workspace_session": "s2",
                    "session_id": "brian/s2/desktop_ip/default",
                    "user_name": "brian",
                    "prompt": "desktop scoped ssot check",
                },
            )

            assert response.status_code == 200, response.text
            body = response.json()
            assert body["session"] == "brian/s2/desktop_ip/ssot-gen"
            assert body["session_dir"] == ".session/desktop_ip/ssot-gen"
            assert body["scope_path"] == ip
            assert len(ssot_worker.runs_for_workflow("ssot-gen")) == 1
            payload = ssot_worker.requests[0]["payload"]
            assert payload["session"] == "brian/s2/desktop_ip/ssot-gen"
            assert payload["project_root"] == str(workspace_root)
            assert (workspace_root / ".session" / ip / "ssot-gen").is_dir()
            assert not (workspace_root / ".session" / "brian" / "s2" / ip / "ssot-gen").exists()
            assert not (source_root / ".session" / ip / "ssot-gen").exists()
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()


def test_multiuser_new_ip_dispatch_uses_user_workspace_without_existing_ip_dir(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs

    ip = "new_user_ssot_ip"
    user_workspace_root = tmp_path / "u" / "default"

    with jobs._jobs_lock:
        jobs._jobs.clear()

    with _mock_worker("ssot") as (ssot_url, ssot_worker):
        monkeypatch.setenv("ATLAS_MULTI_USER", "1")
        monkeypatch.setenv("WORKER_URL_SSOT_GEN", ssot_url)

        client = _make_client(tmp_path, monkeypatch)
        dispatch = client.post("/api/pipeline/dispatch", json={
            "ip": ip,
            "schedule": "auto",
            "stages": ["ssot"],
        })

        assert dispatch.status_code == 200, dispatch.text
        assert len(ssot_worker.runs_for_workflow("ssot-gen")) == 1
        payload = ssot_worker.requests[0]["payload"]
        assert payload["project_root"] == str(user_workspace_root)
        assert (user_workspace_root / ip / "yaml" / f"{ip}.ssot.yaml").is_file()
        assert not (tmp_path / ip).exists()

    with jobs._jobs_lock:
        jobs._jobs.clear()


def test_multiuser_pipeline_state_reads_user_workspace_artifacts(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs

    ip = "state_user_ip"
    user_workspace_root = tmp_path / "u" / "default"
    ssot_path = user_workspace_root / ip / "yaml" / f"{ip}.ssot.yaml"
    ssot_path.parent.mkdir(parents=True)
    ssot_path.write_text(
        f"ip: {ip}\nsections:\n  - name: locked_truth\n    description: user scoped\n",
        encoding="utf-8",
    )

    with jobs._jobs_lock:
        jobs._jobs.clear()

    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    client = _make_client(tmp_path, monkeypatch)
    state = client.get(f"/api/pipeline/state?ip={ip}")

    assert state.status_code == 200, state.text
    payload = state.json()
    assert payload["stages"]["ssot"]["top"].startswith(f"yaml/{ip}.ssot.yaml")
    assert "1 sect" in payload["stages"]["ssot"]["top"]
    assert not (tmp_path / ip).exists()


def test_ipc_completion_gate_prefers_job_project_root_over_env_ip_root(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs
    from src.headless_workflow import _structured_ssot_yaml

    monkeypatch.setenv("ATLAS_WORKFLOW_ROOT", str(PROJECT_ROOT / "workflow"))
    monkeypatch.setenv("ATLAS_RUN_MODE", "engineering")
    poison_ip_root = tmp_path / "poison_ip_root"
    poison_ip_root.mkdir()
    monkeypatch.setenv("ATLAS_IP_ROOT", str(poison_ip_root))

    user_root = tmp_path / "alice" / "default"
    ip = "user_scoped_ssot_ip"
    ssot_path = user_root / ip / "yaml" / f"{ip}.ssot.yaml"
    ssot_path.parent.mkdir(parents=True, exist_ok=True)
    ssot_path.write_text(
        _structured_ssot_yaml(ip, "AXI lite counter"),
        encoding="utf-8",
    )

    response_path = user_root / ".session" / "workers-ipc" / "job-ssot" / "response.json"
    response_path.parent.mkdir(parents=True, exist_ok=True)
    response_path.write_text(
        json.dumps(
            {
                "run_id": "ipc-job-ssot",
                "status": "completed",
                "result": {
                    "status": "completed",
                    "result": "SSOT PASS",
                    "files_modified": [f"{ip}/yaml/{ip}.ssot.yaml"],
                    "iterations": 1,
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    proc = subprocess.Popen([sys.executable, "-c", ""])
    job = {
        "job_id": "job-ssot",
        "run_id": "ipc-job-ssot",
        "status": "running",
        "worker": "ipc://alice/user_scoped_ssot_ip/orchestrator/ssot-gen",
        "worker_transport": "ipc",
        "workflow": "ssot-gen",
        "stage_id": "ssot",
        "ip": ip,
        "project_root": str(user_root),
        "run_mode": "engineering",
        "started_at": time.time(),
    }
    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs["job-ssot"] = job
    try:
        jobs._watch_ipc_worker("job-ssot", "ipc-job-ssot", response_path, proc)
        with jobs._jobs_lock:
            live = dict(jobs._jobs["job-ssot"])
        assert live["status"] == "completed"
        assert live.get("error") in ("", None)
        assert "validated artifact" in str(live.get("evidence_summary") or "")
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()

    with jobs._jobs_lock:
        jobs._jobs.clear()


def test_refresh_recovers_terminal_missing_evidence_job_from_user_project_root(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs
    from src.headless_workflow import _structured_ssot_yaml

    monkeypatch.setenv("ATLAS_WORKFLOW_ROOT", str(PROJECT_ROOT / "workflow"))
    monkeypatch.setenv("ATLAS_RUN_MODE", "engineering")
    monkeypatch.setenv("ATLAS_IP_ROOT", str(tmp_path / "wrong_global_ip_root"))

    user_root = tmp_path / "alice" / "default"
    ip = "user_scoped_recovered_ssot_ip"
    ssot_path = user_root / ip / "yaml" / f"{ip}.ssot.yaml"
    ssot_path.parent.mkdir(parents=True, exist_ok=True)
    ssot_path.write_text(
        _structured_ssot_yaml(ip, "AXI lite counter"),
        encoding="utf-8",
    )

    job = {
        "job_id": "job-recover-ssot",
        "run_id": "ipc-job-recover-ssot",
        "status": "error",
        "worker": "ipc://alice/user_scoped_recovered_ssot_ip/orchestrator/ssot-gen",
        "worker_transport": "ipc",
        "workflow": "ssot-gen",
        "stage_id": "ssot",
        "ip": ip,
        "project_root": str(user_root),
        "run_mode": "engineering",
        "started_at": time.time(),
        "finished_at": time.time(),
        "error": "missing required evidence for ssot; worker reported completed but no stage artifact was found",
        "result_summary": "worker reported SSOT PASS",
    }
    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs["job-recover-ssot"] = job
    try:
        _snapshot, changed = jobs._refresh_tracked_jobs(user_root)
        with jobs._jobs_lock:
            live = dict(jobs._jobs["job-recover-ssot"])
        assert changed is True
        assert live["status"] == "completed"
        assert live.get("error") in ("", None)
        assert "validated artifact" in str(live.get("evidence_summary") or "")
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()


def test_refresh_uses_job_project_root_when_request_root_differs(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs
    from src.headless_workflow import _structured_ssot_yaml

    monkeypatch.setenv("ATLAS_WORKFLOW_ROOT", str(PROJECT_ROOT / "workflow"))
    monkeypatch.setenv("ATLAS_RUN_MODE", "engineering")

    request_root = tmp_path
    user_root = tmp_path / "alice" / "default"
    ip = "request_root_differs_ssot_ip"
    ssot_path = user_root / ip / "yaml" / f"{ip}.ssot.yaml"
    ssot_path.parent.mkdir(parents=True, exist_ok=True)
    ssot_path.write_text(
        _structured_ssot_yaml(ip, "AXI lite counter"),
        encoding="utf-8",
    )

    job = {
        "job_id": "job-recover-request-root-differs",
        "run_id": "ipc-job-recover-request-root-differs",
        "status": "error",
        "worker": "ipc://alice/request_root_differs_ssot_ip/orchestrator/ssot-gen",
        "worker_transport": "ipc",
        "workflow": "ssot-gen",
        "stage_id": "ssot",
        "ip": ip,
        "project_root": str(user_root),
        "run_mode": "engineering",
        "started_at": time.time(),
        "finished_at": time.time(),
        "error": "missing required evidence for ssot; worker reported completed but no stage artifact was found",
    }
    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs[job["job_id"]] = job
    try:
        _snapshot, changed = jobs._refresh_tracked_jobs(request_root)
        with jobs._jobs_lock:
            live = dict(jobs._jobs[job["job_id"]])
        assert changed is True
        assert live["status"] == "completed"
        assert live.get("error") in ("", None)
        assert "validated artifact" in str(live.get("evidence_summary") or "")
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()


def test_refresh_filter_does_not_recover_other_users_missing_evidence_job(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs
    from src.headless_workflow import _structured_ssot_yaml

    monkeypatch.setenv("ATLAS_WORKFLOW_ROOT", str(PROJECT_ROOT / "workflow"))
    monkeypatch.setenv("ATLAS_RUN_MODE", "engineering")

    ip = "shared_recovery_ip"
    alice_root = tmp_path / "alice" / "default"
    bob_root = tmp_path / "bob" / "default"
    for root in (alice_root, bob_root):
        ssot_path = root / ip / "yaml" / f"{ip}.ssot.yaml"
        ssot_path.parent.mkdir(parents=True, exist_ok=True)
        ssot_path.write_text(
            _structured_ssot_yaml(ip, "AXI lite counter"),
            encoding="utf-8",
        )

    base_job = {
        "run_id": "ipc-shared-recovery",
        "status": "error",
        "worker_transport": "ipc",
        "workflow": "ssot-gen",
        "stage_id": "ssot",
        "ip": ip,
        "run_mode": "engineering",
        "started_at": time.time(),
        "finished_at": time.time(),
        "error": "missing required evidence for ssot; worker reported completed but no stage artifact was found",
    }
    alice_job = {
        **base_job,
        "job_id": "alice-job",
        "user_id": "alice",
        "project_root": str(alice_root),
    }
    bob_job = {
        **base_job,
        "job_id": "bob-job",
        "user_id": "bob",
        "project_root": str(bob_root),
    }
    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs["alice-job"] = alice_job
        jobs._jobs["bob-job"] = bob_job
    try:
        _snapshot, changed = jobs._refresh_tracked_jobs(
            alice_root,
            job_filter=lambda job: job.get("user_id") == "alice",
        )
        with jobs._jobs_lock:
            live_alice = dict(jobs._jobs["alice-job"])
            live_bob = dict(jobs._jobs["bob-job"])
        assert changed is True
        assert live_alice["status"] == "completed"
        assert live_bob["status"] == "error"
        assert "evidence_summary" not in live_bob
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()


def test_pipeline_dispatch_refresh_does_not_recover_other_users_missing_evidence_job(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs

    monkeypatch.setenv("ATLAS_RUN_MODE", "engineering")

    alice_ip = "shared_dispatch_recovery_ip"
    alice_root = tmp_path / "alice" / "default"
    fl_check_path = alice_root / alice_ip / "model" / "fl_model_check.json"
    fl_check_path.parent.mkdir(parents=True, exist_ok=True)
    fl_check_path.write_text('{"status":"pass"}\n', encoding="utf-8")

    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs["alice-job"] = {
            "job_id": "alice-job",
            "run_id": "ipc-alice-hidden-recovery",
            "status": "error",
            "worker_transport": "ipc",
            "workflow": "fl-model-gen",
            "stage_id": "fl-model",
            "ip": alice_ip,
            "user_id": "alice",
            "db_user_id": "alice-db",
            "project_root": str(alice_root),
            "run_mode": "engineering",
            "started_at": time.time(),
            "finished_at": time.time(),
            "error": "missing required evidence for fl-model; worker reported completed but no stage artifact was found",
        }

    try:
        with _mock_worker("ssot") as (ssot_url, _ssot_worker):
            monkeypatch.setenv("WORKER_URL_SSOT_GEN", ssot_url)
            client = _make_client(tmp_path, monkeypatch)
            response = client.post("/api/pipeline/dispatch", json={
                "ip": alice_ip,
                "schedule": "auto",
                "stages": ["ssot"],
            })
        assert response.status_code == 200, response.text
        with jobs._jobs_lock:
            live_alice = dict(jobs._jobs["alice-job"])
        assert live_alice["status"] == "error"
        assert "evidence_summary" not in live_alice
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()


def test_api_jobs_scopes_same_user_jobs_by_workspace_session(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs

    client = _make_client(tmp_path, monkeypatch)
    ip = "shared_workspace_jobs_ip"
    now = time.time()
    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs["default-job"] = {
            "job_id": "default-job",
            "run_id": "ipc-default-job",
            "status": "completed",
            "worker_transport": "ipc",
            "workflow": "ssot-gen",
            "stage_id": "ssot",
            "ip": ip,
            "user_id": "u",
            "project_root": str(tmp_path / "u" / "default"),
            "started_at": now,
            "finished_at": now,
        }
        jobs._jobs["alt-job"] = {
            "job_id": "alt-job",
            "run_id": "ipc-alt-job",
            "status": "completed",
            "worker_transport": "ipc",
            "workflow": "ssot-gen",
            "stage_id": "ssot",
            "ip": ip,
            "user_id": "u",
            "project_root": str(tmp_path / "u" / "alt"),
            "started_at": now + 1,
            "finished_at": now + 1,
        }
    try:
        default_resp = client.get("/api/jobs")
        alt_resp = client.get("/api/jobs?workspace_session=alt")

        assert default_resp.status_code == 200, default_resp.text
        assert alt_resp.status_code == 200, alt_resp.text
        assert {job["job_id"] for job in default_resp.json()["jobs"]} == {"default-job"}
        assert {job["job_id"] for job in alt_resp.json()["jobs"]} == {"alt-job"}
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()


def test_pipeline_state_scopes_same_user_running_jobs_by_workspace_session(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs

    client = _make_client(tmp_path, monkeypatch)
    ip = "shared_workspace_state_ip"
    now = time.time()
    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs["default-state-job"] = {
            "job_id": "default-state-job",
            "run_id": "ipc-default-state-job",
            "status": "running",
            "worker_transport": "ipc",
            "workflow": "ssot-gen",
            "stage_id": "ssot",
            "ip": ip,
            "user_id": "u",
            "project_root": str(tmp_path / "u" / "default"),
            "started_at": now,
        }
        jobs._jobs["alt-state-job"] = {
            "job_id": "alt-state-job",
            "run_id": "ipc-alt-state-job",
            "status": "running",
            "worker_transport": "ipc",
            "workflow": "ssot-gen",
            "stage_id": "ssot",
            "ip": ip,
            "user_id": "u",
            "project_root": str(tmp_path / "u" / "alt"),
            "started_at": now + 1,
        }
    try:
        default_resp = client.get(f"/api/pipeline/state?ip={ip}")
        alt_resp = client.get(f"/api/pipeline/state?ip={ip}&workspace_session=alt")

        assert default_resp.status_code == 200, default_resp.text
        assert alt_resp.status_code == 200, alt_resp.text

        def running_ids(payload) -> set[str]:
            stages = payload.get("stages") or {}
            ssot = stages.get("ssot") if isinstance(stages, dict) else {}
            raw_history = ssot.get("history") if isinstance(ssot, dict) else []
            history = raw_history if isinstance(raw_history, list) else []
            return {
                str(item["run_id"])
                for item in history
                if isinstance(item, dict) and item.get("run_id")
            }

        assert running_ids(default_resp.json()) == {"ipc-default-state-job"}
        assert running_ids(alt_resp.json()) == {"ipc-alt-state-job"}
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()


def test_pipeline_state_uses_request_workspace_rtl_version(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from core.atlas_db import AtlasDB

    client = _make_client(tmp_path, monkeypatch)
    ip = "shared_rtl_version_ip"
    with AtlasDB(str(tmp_path / "atlas.db")) as db:
        user = db.get_user_by_username("u")
        assert user is not None
        default_workspace = db.upsert_workspace(
            "default",
            owner_user_id=user["id"],
            local_path=str(tmp_path / "u" / "default"),
        )
        alt_workspace = db.upsert_workspace(
            "alt",
            owner_user_id=user["id"],
            local_path=str(tmp_path / "u" / "alt"),
        )
        default_ip = db.upsert_ip_block(default_workspace["id"], ip)
        alt_ip = db.upsert_ip_block(alt_workspace["id"], ip)
        db.register_rtl_version(
            ip_id=default_ip["id"],
            workspace_id=default_workspace["id"],
            version="default-v1",
            rtl_root=f"{ip}/rtl",
            filelist_path=f"{ip}/list/{ip}.f",
        )
        db.register_rtl_version(
            ip_id=alt_ip["id"],
            workspace_id=alt_workspace["id"],
            version="alt-v1",
            rtl_root=f"{ip}/rtl",
            filelist_path=f"{ip}/list/{ip}.f",
        )

    resp = client.get(f"/api/pipeline/state?ip={ip}&workspace_session=alt")

    assert resp.status_code == 200, resp.text
    assert resp.json()["rtl_version_id"] == "alt-v1"


def test_pipeline_progress_debug_scopes_same_user_jobs_by_workspace_session(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs

    client = _make_client(tmp_path, monkeypatch)
    ip = "shared_progress_debug_ip"
    now = time.time()
    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs["default-progress-job"] = {
            "job_id": "default-progress-job",
            "run_id": "ipc-default-progress-job",
            "status": "running",
            "worker_transport": "ipc",
            "workflow": "ssot-gen",
            "stage_id": "ssot",
            "ip": ip,
            "user_id": "u",
            "project_root": str(tmp_path / "u" / "default"),
            "started_at": now,
        }
        jobs._jobs["alt-progress-job"] = {
            "job_id": "alt-progress-job",
            "run_id": "ipc-alt-progress-job",
            "status": "running",
            "worker_transport": "ipc",
            "workflow": "ssot-gen",
            "stage_id": "ssot",
            "ip": ip,
            "user_id": "u",
            "project_root": str(tmp_path / "u" / "alt"),
            "started_at": now + 1,
        }
    try:
        default_resp = client.get(f"/api/pipeline/progress-debug?ip={ip}")
        alt_resp = client.get(f"/api/pipeline/progress-debug?ip={ip}&workspace_session=alt")

        assert default_resp.status_code == 200, default_resp.text
        assert alt_resp.status_code == 200, alt_resp.text

        def active_job_ids(payload) -> set[str]:
            worker = payload.get("worker") if isinstance(payload, dict) else {}
            active = worker.get("active") if isinstance(worker, dict) else []
            return {
                str(item["job_id"])
                for item in active
                if isinstance(item, dict) and item.get("job_id")
            }

        assert active_job_ids(default_resp.json()) == {"default-progress-job"}
        assert active_job_ids(alt_resp.json()) == {"alt-progress-job"}
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()


def test_same_user_other_workspace_job_log_and_cancel_are_forbidden(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs

    client = _make_client(tmp_path, monkeypatch)
    alt_root = tmp_path / "u" / "alt"
    session = "u/alt/shared_workspace_log_ip/ssot-gen"
    conversation = alt_root / ".session" / session / "conversation.json"
    conversation.parent.mkdir(parents=True, exist_ok=True)
    conversation.write_text(
        json.dumps([{"role": "assistant", "content": "alt workspace secret log"}]),
        encoding="utf-8",
    )
    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs["alt-log-job"] = {
            "job_id": "alt-log-job",
            "run_id": "ipc-alt-log-job",
            "status": "running",
            "worker": "ipc://u/shared_workspace_log_ip/orchestrator/ssot-gen",
            "worker_transport": "ipc",
            "workflow": "ssot-gen",
            "stage_id": "ssot",
            "ip": "shared_workspace_log_ip",
            "user_id": "u",
            "project_root": str(alt_root),
            "session": session,
            "started_at": time.time(),
        }
    try:
        default_log = client.get("/api/job/alt-log-job/log")
        default_cancel = client.post("/api/job/alt-log-job/cancel")
        with jobs._jobs_lock:
            after_default = dict(jobs._jobs["alt-log-job"])

        assert default_log.status_code == 403
        assert default_cancel.status_code == 403
        assert after_default["status"] == "running"

        alt_log = client.get("/api/job/alt-log-job/log?workspace_session=alt")
        alt_cancel = client.post("/api/job/alt-log-job/cancel?workspace_session=alt")

        assert alt_log.status_code == 200, alt_log.text
        assert "alt workspace secret log" in json.dumps(alt_log.json())
        assert alt_cancel.status_code == 200, alt_cancel.text
        with jobs._jobs_lock:
            assert jobs._jobs["alt-log-job"]["status"] == "cancelled"
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()


def test_jobs_clear_only_removes_completed_jobs_visible_to_workspace(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs

    client = _make_client(tmp_path, monkeypatch)
    ip = "shared_workspace_clear_ip"
    now = time.time()
    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs["default-done"] = {
            "job_id": "default-done",
            "run_id": "run-default-done",
            "status": "completed",
            "workflow": "ssot-gen",
            "stage_id": "ssot",
            "ip": ip,
            "user_id": "u",
            "project_root": str(tmp_path / "u" / "default"),
            "started_at": now,
        }
        jobs._jobs["alt-done"] = {
            "job_id": "alt-done",
            "run_id": "run-alt-done",
            "status": "completed",
            "workflow": "ssot-gen",
            "stage_id": "ssot",
            "ip": ip,
            "user_id": "u",
            "project_root": str(tmp_path / "u" / "alt"),
            "started_at": now + 1,
        }
        jobs._jobs["alt-running"] = {
            "job_id": "alt-running",
            "run_id": "run-alt-running",
            "status": "running",
            "workflow": "rtl-gen",
            "stage_id": "rtl",
            "ip": ip,
            "user_id": "u",
            "project_root": str(tmp_path / "u" / "alt"),
            "started_at": now + 2,
        }
        jobs._jobs["other-done"] = {
            "job_id": "other-done",
            "run_id": "run-other-done",
            "status": "completed",
            "workflow": "ssot-gen",
            "stage_id": "ssot",
            "ip": ip,
            "user_id": "other",
            "project_root": str(tmp_path / "other" / "alt"),
            "started_at": now + 3,
        }
    try:
        resp = client.post("/api/jobs/clear?workspace_session=alt")
        assert resp.status_code == 200, resp.text
        with jobs._jobs_lock:
            remaining = set(jobs._jobs.keys())
        assert remaining == {"default-done", "alt-running", "other-done"}
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()


def test_dispatch_does_not_dedupe_against_same_user_other_workspace_job(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs

    ip = "shared_workspace_dispatch_ip"
    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs["default-running-job"] = {
            "job_id": "default-running-job",
            "run_id": "ipc-default-running-job",
            "status": "running",
            "worker_transport": "ipc",
            "workflow": "ssot-gen",
            "stage_id": "ssot",
            "ip": ip,
            "user_id": "u",
            "project_root": str(tmp_path / "u" / "default"),
            "started_at": time.time(),
        }
    try:
        with _mock_worker("ssot") as (ssot_url, ssot_worker):
            monkeypatch.setenv("WORKER_URL_SSOT_GEN", ssot_url)
            client = _make_client(tmp_path, monkeypatch)
            response = client.post("/api/pipeline/dispatch", json={
                "ip": ip,
                "workspace_session": "alt",
                "schedule": "auto",
                "stages": ["ssot"],
            })

            assert response.status_code == 200, response.text
            payload = response.json()
            assert payload.get("deduped") is not True
            assert len(ssot_worker.runs_for_workflow("ssot-gen")) == 1
            assert ssot_worker.requests[0]["payload"]["project_root"] == str(tmp_path / "u" / "alt")
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()


def test_job_dispatch_does_not_dedupe_against_other_user_legacy_job(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs

    ip = "cross_user_legacy_dedupe_ip"
    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs["bob-running-job"] = {
            "job_id": "bob-running-job",
            "run_id": "ipc-bob-running-job",
            "status": "running",
            "worker_transport": "ipc",
            "workflow": "ssot-gen",
            "stage_id": "ssot",
            "ip": ip,
            "user_id": "bob",
            "db_user_id": "",
            "project_root": str(tmp_path / "u" / "default"),
            "started_at": time.time(),
        }
    try:
        with _mock_worker("ssot") as (ssot_url, ssot_worker):
            monkeypatch.setenv("WORKER_URL_SSOT_GEN", ssot_url)
            client = _make_client(tmp_path, monkeypatch)
            response = client.post("/api/job/dispatch", json={
                "workflow": "ssot-gen",
                "ip": ip,
            })

            assert response.status_code == 200, response.text
            payload = response.json()
            assert payload.get("deduped") is not True
            assert payload.get("job_id") != "bob-running-job"
            assert {job.get("job_id") for job in payload.get("existing_jobs", [])} != {"bob-running-job"}
            assert len(ssot_worker.runs_for_workflow("ssot-gen")) == 1
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()


def test_active_job_conflicts_excludes_ownerless_legacy_jobs_for_username_scope(
    tmp_path: Path,
) -> None:
    import atlas_api_jobs as jobs

    ip = "ownerless_legacy_dedupe_ip"
    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs["legacy-ownerless-job"] = {
            "job_id": "legacy-ownerless-job",
            "run_id": "ipc-legacy-ownerless-job",
            "status": "running",
            "worker_transport": "ipc",
            "workflow": "ssot-gen",
            "stage_id": "ssot",
            "ip": ip,
            "user_id": "",
            "db_user_id": "",
            "project_root": str(tmp_path / "u" / "default"),
            "started_at": time.time(),
        }
    try:
        username_scoped = jobs._active_job_conflicts(
            ip=ip,
            stage_ids=["ssot"],
            workflows=["ssot-gen"],
            user_id="u",
            db_user_id="",
            project_root=tmp_path / "u" / "default",
        )
        legacy_scope = jobs._active_job_conflicts(
            ip=ip,
            stage_ids=["ssot"],
            workflows=["ssot-gen"],
            user_id="",
            db_user_id="",
            project_root=tmp_path / "u" / "default",
        )

        assert username_scoped == []
        assert [job["job_id"] for job in legacy_scope] == ["legacy-ownerless-job"]
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()


def test_handoff_routes_use_authenticated_workspace_session_root(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from src import handoff_queue as hq

    ip = "handoff_workspace_root_ip"
    legacy_ip_dir = tmp_path / ip
    scoped_ip_dir = tmp_path / "u" / "alt" / ip
    legacy_ip_dir.mkdir(parents=True)
    scoped_ip_dir.mkdir(parents=True)
    client = _make_client(tmp_path, monkeypatch)
    session_id = f"u/alt/{ip}/orchestrator"
    pipeline_run_id = "pipe-alt-handoff"

    save_resp = client.post("/api/handoff/save", json={
        "ip": ip,
        "from_workflow": "sim-debug",
        "to_workflow": "rtl-gen",
        "reason": "workspace scoped handoff",
        "suffix": "ALT",
        "workspace_session": "alt",
        "session_id": session_id,
        "pipeline_run_id": pipeline_run_id,
    })

    assert save_resp.status_code == 200, save_resp.text
    handoff_id = save_resp.json()["handoff_id"]
    assert (scoped_ip_dir / "handoff" / "pending" / f"{handoff_id}.json").is_file()
    assert not (legacy_ip_dir / "handoff").exists()

    list_resp = client.get(
        f"/api/handoff/list?ip={ip}&workflow=rtl-gen&"
        "workspace_session=alt&"
        f"session_id={session_id}&pipeline_run_id={pipeline_run_id}"
    )
    assert list_resp.status_code == 200, list_resp.text
    assert [row["handoff_id"] for row in list_resp.json()["pending"]] == [handoff_id]

    state_resp = client.get(f"/api/pipeline/state?ip={ip}&workspace_session=alt")
    assert state_resp.status_code == 200, state_resp.text
    assert state_resp.json()["orchestrator"]["pending_handoffs"] == 1

    take_resp = client.post("/api/handoff/take", json={
        "ip": ip,
        "workflow": "rtl-gen",
        "workspace_session": "alt",
        "session_id": session_id,
        "pipeline_run_id": pipeline_run_id,
    })
    assert take_resp.status_code == 200, take_resp.text
    assert take_resp.json()["handoff"]["handoff_id"] == handoff_id
    assert hq.get(scoped_ip_dir, handoff_id)[0] == "claimed"


def test_orchestrator_bridge_handoff_uses_session_owner_for_request_scope(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from core.atlas_db import AtlasDB
    from src import handoff_queue as hq
    from src.orchestrator import react_bridge

    ip = "bridge_handoff_scope_ip"
    scoped_ip_dir = tmp_path / "u" / "alt" / ip
    scoped_ip_dir.mkdir(parents=True)
    client = _make_client(tmp_path, monkeypatch)
    session_id = f"u/alt/{ip}/orchestrator"
    pipeline_run_id = "pipe-bridge-handoff"
    with AtlasDB(str(tmp_path / "atlas.db")) as db:
        user = db.get_user_by_username("u") or {}

    class _Budget:
        def attempt(self, name: str) -> dict[str, bool]:
            return {"allowed": True}

        def reset(self, name: str) -> None:
            return None

        def snapshot(self) -> dict[str, object]:
            return {}

    class _Collector:
        def __init__(self) -> None:
            self.rows: list[dict[str, object]] = []

        def append(self, **row: object) -> None:
            self.rows.append(row)

    ctx = SimpleNamespace(
        run_id="orch-handoff-run",
        user_id=str(user.get("id") or ""),
        ip_id=ip,
        ip_name=ip,
        session_id=session_id,
        project_root=tmp_path / "u" / "alt",
        runner=None,
        user_seed="",
    )
    bound = react_bridge._bind_orchestrator_tools(
        ctx=ctx,
        runner=None,
        db=None,
        collector=_Collector(),
        budgets=_Budget(),
    )
    bound["write_handoff"](
        "",
        pre_parsed_kwargs={
            "workflow": "rtl-gen",
            "reason": "bridge handoff",
            "payload": {"note": "x"},
            "pipeline_run_id": pipeline_run_id,
        },
    )

    pending_files = list((scoped_ip_dir / "handoff" / "pending").glob("*.json"))
    assert len(pending_files) == 1
    record = json.loads(pending_files[0].read_text(encoding="utf-8"))
    assert record["scope"]["user_id"] == "u"

    list_resp = client.get(
        f"/api/handoff/list?ip={ip}&workflow=rtl-gen&"
        "workspace_session=alt&"
        f"session_id={session_id}&pipeline_run_id={pipeline_run_id}"
    )
    assert list_resp.status_code == 200, list_resp.text
    assert [row["handoff_id"] for row in list_resp.json()["pending"]] == [record["handoff_id"]]

    state_resp = client.get(f"/api/pipeline/state?ip={ip}&workspace_session=alt")
    assert state_resp.status_code == 200, state_resp.text
    assert state_resp.json()["orchestrator"]["pending_handoffs"] == 1

    take_resp = client.post("/api/handoff/take", json={
        "ip": ip,
        "workflow": "rtl-gen",
        "workspace_session": "alt",
        "session_id": session_id,
        "pipeline_run_id": pipeline_run_id,
    })
    assert take_resp.status_code == 200, take_resp.text
    assert take_resp.json()["handoff"]["handoff_id"] == record["handoff_id"]
    assert hq.get(scoped_ip_dir, record["handoff_id"])[0] == "claimed"


def test_job_dispatch_http_worker_partition_includes_workspace_session(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs

    monkeypatch.setenv("ATLAS_WORKER_TRANSPORT", "http")
    monkeypatch.setenv("ATLAS_WORKFLOW_WORKER_PER_SESSION", "1")
    with jobs._SESSION_WORKER_PORT_LOCK:
        jobs._SESSION_WORKER_PORTS.clear()
        jobs._SESSION_WORKER_KEYS_BY_PORT.clear()
    client = _make_client(tmp_path, monkeypatch)
    ip = "workspace_partition_ip"
    try:
        default_resp = client.post("/api/job/dispatch", json={
            "workflow": "ssot-gen",
            "ip": ip,
        })
        alt_resp = client.post("/api/job/dispatch", json={
            "workflow": "ssot-gen",
            "ip": ip,
            "workspace_session": "alt",
        })

        assert default_resp.status_code == 502, default_resp.text
        assert alt_resp.status_code == 502, alt_resp.text
        with jobs._jobs_lock:
            created = [
                dict(job)
                for job in jobs._jobs.values()
                if job.get("ip") == ip and job.get("workflow") == "ssot-gen"
            ]
        assert len(created) == 2
        sessions = {str(job.get("session") or "") for job in created}
        workers = {str(job.get("worker") or "") for job in created}
        partitions = {str(job.get("worker_partition") or "") for job in created}
        assert sessions == {f"u/default/{ip}/ssot-gen", f"u/alt/{ip}/ssot-gen"}
        assert len(workers) == 2
        assert len(partitions) == 2
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()
        with jobs._SESSION_WORKER_PORT_LOCK:
            jobs._SESSION_WORKER_PORTS.clear()
            jobs._SESSION_WORKER_KEYS_BY_PORT.clear()


def test_job_dispatch_rejects_explicit_session_for_another_user(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs

    client = _make_client(tmp_path, monkeypatch)
    ip = "explicit_session_ip"
    with jobs._jobs_lock:
        jobs._jobs.clear()
    try:
        response = client.post("/api/job/dispatch", json={
            "workflow": "rtl-gen",
            "ip": ip,
            "workspace_session": "alt",
            "session": f"bob/alt/{ip}/rtl-gen",
        })

        assert response.status_code == 403, response.text
        assert "session owner/workspace mismatch" in response.text
        with jobs._jobs_lock:
            assert not [
                job for job in jobs._jobs.values()
                if job.get("ip") == ip and job.get("workflow") == "rtl-gen"
            ]
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()


def test_dispatch_many_rejects_explicit_session_for_another_workspace(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs

    client = _make_client(tmp_path, monkeypatch)
    ip = "explicit_many_session_ip"
    with jobs._jobs_lock:
        jobs._jobs.clear()
    try:
        response = client.post("/api/jobs/dispatch_many", json={
            "workspace_session": "alt",
            "jobs": [
                {
                    "workflow": "tb-gen",
                    "ip": ip,
                    "session": f"u/default/{ip}/tb-gen",
                }
            ],
        })

        assert response.status_code == 207, response.text
        payload = response.json()
        assert payload["jobs"] == []
        assert payload["errors"] == [{"index": 0, "error": "session owner/workspace mismatch"}]
        with jobs._jobs_lock:
            assert not [
                job for job in jobs._jobs.values()
                if job.get("ip") == ip and job.get("workflow") == "tb-gen"
            ]
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()


def test_job_dispatch_rejects_symlinked_workspace_root(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs

    target = tmp_path / "bob" / "default"
    link = tmp_path / "u" / "alt"
    target.mkdir(parents=True)
    link.parent.mkdir(parents=True)
    link.symlink_to(target, target_is_directory=True)

    client = _make_client(tmp_path, monkeypatch)
    ip = "symlink_workspace_ip"
    with jobs._jobs_lock:
        jobs._jobs.clear()
    try:
        response = client.post("/api/job/dispatch", json={
            "workflow": "rtl-gen",
            "ip": ip,
            "workspace_session": "alt",
        })

        assert response.status_code == 403, response.text
        assert "workspace root symlink not allowed" in response.text
        with jobs._jobs_lock:
            assert not [
                job for job in jobs._jobs.values()
                if job.get("ip") == ip and job.get("workflow") == "rtl-gen"
            ]
        assert not (target / ".session").exists()
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()


def test_rootless_legacy_job_is_not_visible_cancelled_or_deduped_from_scoped_workspace(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs

    client = _make_client(tmp_path, monkeypatch)
    ip = "rootless_workspace_ip"
    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs["legacy-rootless"] = {
            "job_id": "legacy-rootless",
            "run_id": "ipc-legacy-rootless",
            "status": "running",
            "worker_transport": "ipc",
            "workflow": "ssot-gen",
            "stage_id": "ssot",
            "ip": ip,
            "user_id": "u",
            "started_at": time.time(),
        }
    try:
        jobs_resp = client.get("/api/jobs?workspace_session=alt")
        cancel_resp = client.post("/api/job/legacy-rootless/cancel?workspace_session=alt")
        with _mock_worker("ssot") as (ssot_url, ssot_worker):
            monkeypatch.setenv("WORKER_URL_SSOT_GEN", ssot_url)
            dispatch_resp = client.post("/api/job/dispatch", json={
                "workflow": "ssot-gen",
                "ip": ip,
                "workspace_session": "alt",
            })

        assert jobs_resp.status_code == 200, jobs_resp.text
        assert "legacy-rootless" not in {job["job_id"] for job in jobs_resp.json()["jobs"]}
        assert cancel_resp.status_code == 403
        assert dispatch_resp.status_code == 200, dispatch_resp.text
        assert dispatch_resp.json().get("deduped") is not True
        assert len(ssot_worker.runs_for_workflow("ssot-gen")) == 1
        with jobs._jobs_lock:
            assert jobs._jobs["legacy-rootless"]["status"] == "running"
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()


def test_multiuser_job_log_and_cancel_reject_other_user(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs

    client = _make_client(tmp_path, monkeypatch)
    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs["bob-job"] = {
            "job_id": "bob-job",
            "run_id": "ipc-bob-job",
            "status": "running",
            "worker": "ipc://bob/shared/orchestrator/ssot-gen",
            "worker_transport": "ipc",
            "workflow": "ssot-gen",
            "stage_id": "ssot",
            "ip": "shared_log_ip",
            "user_id": "bob",
            "project_root": str(tmp_path / "bob" / "default"),
            "started_at": time.time(),
        }
    try:
        log_resp = client.get("/api/job/bob-job/log")
        cancel_resp = client.post("/api/job/bob-job/cancel")
        with jobs._jobs_lock:
            live = dict(jobs._jobs["bob-job"])
        assert log_resp.status_code == 403
        assert cancel_resp.status_code == 403
        assert live["status"] == "running"
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()


def test_orchestrator_dispatch_workflow_tool_creates_pipeline_job(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs
    from core import tools

    ip = "tool_dispatch_ip"
    (tmp_path / ip / "rtl").mkdir(parents=True)

    with jobs._jobs_lock:
        jobs._jobs.clear()

    with _mock_worker("rtl") as (rtl_url, rtl_worker):
        monkeypatch.setenv("ATLAS_MULTI_USER", "1")
        monkeypatch.setenv("ATLAS_ACTIVE_SESSION", f"u/{ip}/orchestrator")
        monkeypatch.setenv("ATLAS_ACTIVE_IP", ip)
        monkeypatch.setenv("WORKER_URL_RTL_GEN", rtl_url)

        _make_client(tmp_path, monkeypatch)
        raw = tools.dispatch_workflow(
            workflow="rtl-gen",
            ip=ip,
            reason="owner=rtl_bug from sim_debug",
        )
        result = json.loads(raw)

        assert result["ok"] is True
        assert result["source"] == "dispatch_workflow_tool"
        assert result["ip"] == ip
        assert result["user_id"] == "u"
        assert result["pipeline_run_id"] == result["pipeline_id"]
        assert result["jobs"][0]["workflow"] == "rtl-gen"
        assert result["jobs"][0]["pipeline_run_id"] == result["pipeline_id"]
        assert len(rtl_worker.runs_for_workflow("rtl-gen")) == 1
        payload = rtl_worker.requests[0]["payload"]
        assert payload["session"].startswith(f"u/default/{ip}/pipeline/{result['pipeline_id']}/")
        assert payload["pipeline_run_id"] == result["pipeline_id"]
        assert payload["user_id"] == "u"
        assert payload["model"] == "gpt-5.3-codex"
        assert "run /ssot-rtl" in payload["task"]
        assert "owner=rtl_bug" in payload["task"]

    with jobs._jobs_lock:
        jobs._jobs.clear()


def test_orchestrator_dispatch_workflow_tool_uses_payload_session_owner(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs
    from core import tools
    from core.atlas_db import AtlasDB

    ip = "tool_payload_owner_ip"
    (tmp_path / ip / "rtl").mkdir(parents=True)

    with jobs._jobs_lock:
        jobs._jobs.clear()

    with _mock_worker("rtl") as (rtl_url, rtl_worker):
        monkeypatch.setenv("ATLAS_MULTI_USER", "1")
        monkeypatch.delenv("ATLAS_ACTIVE_SESSION", raising=False)
        monkeypatch.delenv("ATLAS_ACTIVE_USER", raising=False)
        monkeypatch.setenv("WORKER_URL_RTL_GEN", rtl_url)

        _make_client(tmp_path, monkeypatch)
        with AtlasDB(str(tmp_path / "atlas.db")) as db:
            owner = db.ensure_user_by_username("happy2")

        raw = tools.dispatch_workflow(
            workflow="rtl-gen",
            ip=ip,
            payload={
                "db_user_id": owner["id"],
                "orchestrator_session_id": f"happy2/default/{ip}/orchestrator",
            },
            reason="dispatch from current orchestrator session",
        )
        result = json.loads(raw)

        assert result["ok"] is True
        assert result["user_id"] == "happy2"
        assert result["db_user_id"] == owner["id"]
        assert len(rtl_worker.runs_for_workflow("rtl-gen")) == 1
        payload = rtl_worker.requests[0]["payload"]
        assert payload["session"].startswith(f"happy2/default/{ip}/pipeline/{result['pipeline_id']}/")
        assert payload["user_id"] == "happy2"
        assert payload["db_user_id"] == owner["id"]

        with AtlasDB(str(tmp_path / "atlas.db")) as db:
            run = db._fetchone(
                """
                SELECT s.user_id AS session_user_id,
                       w.owner_user_id AS workspace_owner_user_id
                  FROM workflow_runs r
                  JOIN sessions s ON s.id = r.session_id
                  JOIN workspaces w ON w.id = r.workspace_id
                 WHERE r.workflow = ?
                 ORDER BY r.started_at DESC
                 LIMIT 1
                """,
                ("rtl-gen",),
            )
        assert run is not None
        assert run["session_user_id"] == owner["id"]
        assert run["workspace_owner_user_id"] == owner["id"]

    with jobs._jobs_lock:
        jobs._jobs.clear()


def test_orchestrator_dispatch_workflow_tool_rejects_spoofed_session_owner(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs
    from core import tools
    from core.atlas_db import AtlasDB

    ip = "tool_spoofed_session_ip"

    with jobs._jobs_lock:
        jobs._jobs.clear()

    with _mock_worker("rtl") as (rtl_url, rtl_worker):
        monkeypatch.setenv("ATLAS_MULTI_USER", "1")
        monkeypatch.delenv("ATLAS_ACTIVE_SESSION", raising=False)
        monkeypatch.delenv("ATLAS_ACTIVE_USER", raising=False)
        monkeypatch.setenv("WORKER_URL_RTL_GEN", rtl_url)

        _make_client(tmp_path, monkeypatch)
        with AtlasDB(str(tmp_path / "atlas.db")) as db:
            owner = db.ensure_user_by_username("alice")

        raw = tools.dispatch_workflow(
            workflow="rtl-gen",
            ip=ip,
            payload={
                "db_user_id": owner["id"],
                "orchestrator_session_id": f"bob/alt/{ip}/orchestrator",
            },
            reason="spoof another owner",
        )
        result = json.loads(raw)

        assert result["ok"] is False
        assert "session owner/workspace mismatch" in result["error"]
        assert rtl_worker.runs_for_workflow("rtl-gen") == []

    with jobs._jobs_lock:
        jobs._jobs.clear()


def test_orchestrator_dispatch_workflow_tool_uses_payload_workspace_session(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs
    from core import tools
    from core.atlas_db import AtlasDB

    ip = "tool_payload_workspace_ip"

    with jobs._jobs_lock:
        jobs._jobs.clear()

    with _mock_worker("rtl") as (rtl_url, rtl_worker):
        monkeypatch.setenv("ATLAS_MULTI_USER", "1")
        monkeypatch.delenv("ATLAS_ACTIVE_SESSION", raising=False)
        monkeypatch.delenv("ATLAS_ACTIVE_USER", raising=False)
        monkeypatch.setenv("WORKER_URL_RTL_GEN", rtl_url)

        _make_client(tmp_path, monkeypatch)
        with AtlasDB(str(tmp_path / "atlas.db")) as db:
            owner = db.ensure_user_by_username("happy_alt")

        raw = tools.dispatch_workflow(
            workflow="rtl-gen",
            ip=ip,
            payload={
                "db_user_id": owner["id"],
                "orchestrator_session_id": f"happy_alt/alt/{ip}/orchestrator",
            },
            reason="dispatch from alt workspace",
        )
        result = json.loads(raw)

        assert result["ok"] is True
        assert len(rtl_worker.runs_for_workflow("rtl-gen")) == 1
        payload = rtl_worker.requests[0]["payload"]
        assert payload["session"].startswith(f"happy_alt/alt/{ip}/pipeline/{result['pipeline_id']}/")
        assert payload["project_root"] == str(tmp_path / "happy_alt" / "alt")

    with jobs._jobs_lock:
        jobs._jobs.clear()


def test_read_pipeline_state_tool_scopes_same_user_jobs_by_workspace_session(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs
    from core import tools
    from core.atlas_db import AtlasDB

    ip = "tool_read_workspace_ip"
    now = time.time()
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_ACTIVE_SESSION", f"u/default/{ip}/orchestrator")
    _make_client(tmp_path, monkeypatch)
    with AtlasDB(str(tmp_path / "atlas.db")) as db:
        user = db.get_user_by_username("u")
        assert user is not None
        db_user_id = str(user["id"] or "")
    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs["default-tool-state-job"] = {
            "job_id": "default-tool-state-job",
            "run_id": "ipc-default-tool-state-job",
            "status": "running",
            "worker_transport": "ipc",
            "workflow": "ssot-gen",
            "stage_id": "ssot",
            "ip": ip,
            "user_id": "u",
            "db_user_id": db_user_id,
            "project_root": str(tmp_path / "u" / "default"),
            "started_at": now,
        }
        jobs._jobs["alt-tool-state-job"] = {
            "job_id": "alt-tool-state-job",
            "run_id": "ipc-alt-tool-state-job",
            "status": "running",
            "worker_transport": "ipc",
            "workflow": "ssot-gen",
            "stage_id": "ssot",
            "ip": ip,
            "user_id": "u",
            "db_user_id": db_user_id,
            "project_root": str(tmp_path / "u" / "alt"),
            "started_at": now + 1,
        }
    try:
        monkeypatch.setenv("ATLAS_ACTIVE_SESSION", f"u/default/{ip}/orchestrator")

        raw = tools.read_pipeline_state(ip=ip, scope=f"u/alt/{ip}/orchestrator")
        result = json.loads(raw)

        assert result["project_root"] == str(tmp_path / "u" / "alt")
        assert {job["job_id"] for job in result["active_jobs"]} == {"alt-tool-state-job"}
        assert result["stages"]["ssot"]["active_jobs"][0]["job_id"] == "alt-tool-state-job"
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()


def test_orchestrator_read_pipeline_state_tool_uses_db_user_id_visibility(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs
    from src.orchestrator import tools as orch_tools

    ip = "tool_read_db_user_workspace_ip"
    now = time.time()
    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs["default-db-tool-state-job"] = {
            "db_user_id": "u-db",
            "job_id": "default-db-tool-state-job",
            "project_root": str(tmp_path / "u" / "default"),
            "run_id": "ipc-default-db-tool-state-job",
            "stage_id": "ssot",
            "started_at": now,
            "status": "running",
            "user_id": "u",
            "worker_transport": "ipc",
            "workflow": "ssot-gen",
            "ip": ip,
        }
        jobs._jobs["alt-db-tool-state-job"] = {
            "db_user_id": "u-db",
            "job_id": "alt-db-tool-state-job",
            "project_root": str(tmp_path / "u" / "alt"),
            "run_id": "ipc-alt-db-tool-state-job",
            "stage_id": "ssot",
            "started_at": now + 1,
            "status": "running",
            "user_id": "u",
            "worker_transport": "ipc",
            "workflow": "ssot-gen",
            "ip": ip,
        }
    try:
        monkeypatch.setenv("ATLAS_MULTI_USER", "1")
        _make_client(tmp_path, monkeypatch)

        result, _summary = orch_tools.read_pipeline_state(
            ip=ip,
            scope=f"u/alt/{ip}/orchestrator",
            db_user_id="u-db",
        )

        assert result["project_root"] == str(tmp_path / "u" / "alt")
        assert {job["job_id"] for job in result["active_jobs"]} == {"alt-db-tool-state-job"}
        assert result["stages"]["ssot"]["active_jobs"][0]["job_id"] == "alt-db-tool-state-job"
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()


def test_orchestrator_custom_rtl_prompt_keeps_ssot_rtl_driver(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs
    from core import tools

    ip = "tool_dispatch_rtl_prompt_ip"
    (tmp_path / ip / "rtl").mkdir(parents=True)

    with jobs._jobs_lock:
        jobs._jobs.clear()

    with _mock_worker("rtl") as (rtl_url, rtl_worker):
        monkeypatch.setenv("ATLAS_MULTI_USER", "1")
        monkeypatch.setenv("ATLAS_ACTIVE_SESSION", f"u/{ip}/orchestrator")
        monkeypatch.setenv("ATLAS_ACTIVE_IP", ip)
        monkeypatch.setenv("WORKER_URL_RTL_GEN", rtl_url)

        _make_client(tmp_path, monkeypatch)
        raw = tools.dispatch_workflow(
            workflow="rtl-gen",
            ip=ip,
            prompt="equivalence is done; generate dma rtl and continue",
            reason="advance after equivalence",
        )
        result = json.loads(raw)

        assert result["ok"] is True
        payload = rtl_worker.requests[0]["payload"]
        assert payload["task"].index("run /ssot-rtl") < payload["task"].index(
            "equivalence is done"
        )
        assert "[Orchestrator worker instruction]" in payload["task"]

    with jobs._jobs_lock:
        jobs._jobs.clear()


def test_orchestrator_rtl_prompt_mentions_driver_without_command_still_prepends_driver(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs
    from core import tools

    ip = "tool_dispatch_rtl_driver_prose_ip"
    (tmp_path / ip / "rtl").mkdir(parents=True)

    with jobs._jobs_lock:
        jobs._jobs.clear()

    with _mock_worker("rtl") as (rtl_url, rtl_worker):
        monkeypatch.setenv("ATLAS_MULTI_USER", "1")
        monkeypatch.setenv("ATLAS_ACTIVE_SESSION", f"u/{ip}/orchestrator")
        monkeypatch.setenv("ATLAS_ACTIVE_IP", ip)
        monkeypatch.setenv("WORKER_URL_RTL_GEN", rtl_url)

        _make_client(tmp_path, monkeypatch)
        raw = tools.dispatch_workflow(
            workflow="rtl-gen",
            ip=ip,
            prompt=(
                "Regenerate RTL using slash command /ssot-rtl equivalent; "
                "prior artifact was stale."
            ),
            reason="advance after ssot repair",
        )
        result = json.loads(raw)

        assert result["ok"] is True
        payload = rtl_worker.requests[0]["payload"]
        assert "run /ssot-rtl" in payload["task"]
        assert payload["task"].index("run /ssot-rtl") < payload["task"].index(
            "Regenerate RTL"
        )

    with jobs._jobs_lock:
        jobs._jobs.clear()


def test_orchestrator_dispatch_worker_prompt_includes_chat_context(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs
    from core import tools
    from core.atlas_db import AtlasDB

    ip = "dma_prompt_ip"
    (tmp_path / ip / "rtl").mkdir(parents=True)

    with jobs._jobs_lock:
        jobs._jobs.clear()

    with _mock_worker("ssot") as (ssot_url, ssot_worker):
        monkeypatch.setenv("ATLAS_MULTI_USER", "1")
        monkeypatch.setenv("ATLAS_ACTIVE_SESSION", f"u/{ip}/orchestrator")
        monkeypatch.setenv("ATLAS_ACTIVE_IP", ip)
        monkeypatch.setenv("WORKER_URL_SSOT_GEN", ssot_url)

        _make_client(tmp_path, monkeypatch)
        with AtlasDB(str(tmp_path / "atlas.db")) as db:
            workspace = db.upsert_workspace(tmp_path.name or "default", owner_user_id="u", local_path=str(tmp_path))
            ip_row = db.upsert_ip_block(workspace["id"], ip, ssot_path=f"{ip}/yaml/{ip}.ssot.yaml")
            db.record_chat_message(
                ip_row["id"],
                "u",
                "make dma from scratch with apb psel penable pwrite paddr pwdata prdata pready pslverr and ctrl status src dst length irq registers",
                workspace_id=workspace["id"],
            )

        raw = tools.dispatch_workflow(
            workflow="ssot-gen",
            ip=ip,
            reason="retry ssot from orchestrator chat",
        )
        result = json.loads(raw)

        assert result["ok"] is True
        payload = ssot_worker.requests[0]["payload"]
        assert "[ATLAS_PIPELINE_SSOT_DIRECT_WRITE]" in payload["task"]
        assert "[Orchestrator chat context]" in payload["task"]
        assert "apb psel penable" in payload["task"]
        assert "ctrl status src dst length irq registers" in payload["task"]

    with jobs._jobs_lock:
        jobs._jobs.clear()


def test_orchestrator_worker_status_exposes_default_model_bindings(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs

    client = _make_client(tmp_path, monkeypatch)

    resp = client.get("/api/orchestrator/workers?ip=model_bind_ip")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["orchestrator"]["model"] == jobs.ORCHESTRATOR_MODEL
    assert body["orchestrator"]["reasoning_effort"] == jobs.ORCHESTRATOR_REASONING_EFFORT
    models = {item["workflow"]: item["model"] for item in body["workers"]}
    defaults = {item["workflow"]: item["default_model"] for item in body["workers"]}
    assert models["ssot-gen"] == "gpt-5.5"
    assert models["rtl-gen"] == "gpt-5.3-codex"
    assert models["tb-gen"] == "deepseek"
    assert models["sim_debug"] == "kimi"
    assert models["lint"] == "deepseek"
    assert defaults == models
    toolchains = {item["workflow"]: item.get("toolchain") for item in body["workers"]}
    assert toolchains["lint"] == "pyslang + verilator"
    assert toolchains["coverage"] == "verilator coverage + VCD"
    assert toolchains["contract-reflection"] == "deterministic contract validators"


def test_job_dispatch_keeps_llm_model_separate_from_lint_toolchain(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs

    ip = "lint_model_ip"
    (tmp_path / ip / "rtl").mkdir(parents=True)

    with jobs._jobs_lock:
        jobs._jobs.clear()

    with _mock_worker("lint") as (lint_url, lint_worker):
        monkeypatch.setenv("WORKER_URL_LINT", lint_url)
        client = _make_client(tmp_path, monkeypatch)

        resp = client.post("/api/job/dispatch", json={
            "workflow": "lint",
            "ip": ip,
        })

        assert resp.status_code == 200, resp.text
        body = resp.json()
        # lint workflow's LLM model default flipped to "deepseek" — see
        # _WORKER_MODEL_DEFAULTS in atlas_api_jobs.py and the matching
        # passing assertion in test_orchestrator_worker_status_exposes_default_model_bindings.
        assert body["model"] == "deepseek"
        assert body["toolchain"] == "pyslang + verilator"
        assert "--model deepseek" in body["worker_command"]
        assert "pyslang" not in body["worker_command"]
        assert len(lint_worker.runs_for_workflow("lint")) == 1
        payload = lint_worker.requests[0]["payload"]
        assert payload["model"] == "deepseek"
        assert payload["toolchain"] == "pyslang + verilator"

    with jobs._jobs_lock:
        jobs._jobs.clear()


def test_orchestrator_chat_smoke_dispatches_worker_evidence_and_db_run(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs
    from core.atlas_db import AtlasDB
    from src.orchestrator.loop import RunOutcome
    from src.orchestrator import runner as runner_mod
    from src.orchestrator import tools as orch_tools
    from src.orchestrator.runner import OrchestratorRunner

    ip = "orch_smoke_ip"
    (tmp_path / ip / "rtl").mkdir(parents=True)
    with jobs._jobs_lock:
        jobs._jobs.clear()

    smoke_errors = []

    class _SmokeLoop:
        def __init__(self, db, ctx, message):
            self.db = db
            self.ctx = ctx
            self.message = message

        def run(self):
            try:
                result, _summary = orch_tools.dispatch_workflow(
                    workflow="lint",
                    ip=ip,
                    reason="smoke test dispatch",
                    orchestrator_run_id=self.ctx.run_id,
                )
                assert result["ok"] is True
                jobs._refresh_tracked_jobs(tmp_path)
                self.db.update_orchestrator_run(
                    self.ctx.run_id,
                    status="completed",
                    final_state="completed",
                    ended=True,
                )
                return RunOutcome(status="completed", final_state="completed", steps_taken=1)
            except Exception as exc:
                smoke_errors.append(repr(exc))
                self.db.update_orchestrator_run(
                    self.ctx.run_id,
                    status="error",
                    final_state=repr(exc),
                    ended=True,
                )
                raise

    with _mock_worker("lint") as (worker_url, worker):
        monkeypatch.setenv("WORKER_URL_LINT", worker_url)
        monkeypatch.setenv("ATLAS_ORCHESTRATOR_TRANSPORT", "thread")
        client = _make_client(tmp_path, monkeypatch)
        db = AtlasDB(str(tmp_path / "atlas.db"))
        runner = OrchestratorRunner(
            db,
            max_workers=1,
            loop_factory=lambda db_, ctx, msg: _SmokeLoop(db_, ctx, msg),
        )
        runner_mod.set_runner_for_test(runner)
        try:
            resp = client.post("/api/pipeline/orchestrator/chat", json={
                "ip": ip,
                "message": "run lint smoke",
            })
            assert resp.status_code == 200, resp.text
            body = resp.json()
            assert body["model"] == jobs.ORCHESTRATOR_MODEL
            assert body["reasoning_effort"] == jobs.ORCHESTRATOR_REASONING_EFFORT

            with runner._lock:
                active_futures = [entry[1] for entry in runner._active.values()]
            if active_futures:
                active_futures[0].result(timeout=5)
            assert not smoke_errors
            run_row = db.get_orchestrator_run(body["run_id"])
            assert run_row is not None
            assert run_row["status"] == "completed"

            for _ in range(30):
                detail = client.get(
                    f"/api/orchestrator/runs/{body['run_id']}?ip={ip}&workspace_session=default"
                )
                assert detail.status_code == 200, detail.text
                if detail.json()["run"]["status"] == "completed":
                    break
                time.sleep(0.1)
            else:
                raise AssertionError("orchestrator smoke run did not complete")

            assert len(worker.runs_for_workflow("lint")) == 1
            workspace_root = tmp_path / "u" / "default"
            assert worker.requests[0]["payload"]["project_root"] == str(workspace_root)
            assert (workspace_root / ip / "lint" / "dut_lint.json").is_file()
            assert not (tmp_path / ip / "lint" / "dut_lint.json").exists()
            rows = db._fetchall(
                "SELECT workflow, status, model_profile FROM workflow_runs WHERE workflow = ?",
                ("lint",),
            )
            assert rows
            run = db._row_to_dict(rows[-1], "workflow_runs")
            assert run["status"] == "completed"
            assert run["model_profile"] == "deepseek"
        finally:
            runner.shutdown(wait=False)
            runner_mod.set_runner_for_test(None)
            db.close()
            with jobs._jobs_lock:
                jobs._jobs.clear()


def test_full_ip_pipeline_can_complete_all_stages_across_two_workers(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs

    # _job_artifact_recovery for ssot calls workflow/ssot-gen/scripts/check_ssot_disk.sh
    # against project_root. Symlink the real workflow dir so the validator script
    # is reachable in the test sandbox.
    (tmp_path / "workflow").symlink_to(PROJECT_ROOT / "workflow", target_is_directory=True)

    ip = "full_worker_pipe_ip"
    user_workspace_root = tmp_path / "u" / "default"
    ip_dir = user_workspace_root / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "rtl").mkdir(parents=True)
    (ip_dir / "list").mkdir(parents=True)
    (ip_dir / "tb").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        f"ip: {ip}\nsections:\n  - name: interface\n    description: smoke\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input logic clk, output logic done); assign done = clk; endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"../rtl/{ip}.sv\n", encoding="utf-8")
    (ip_dir / "tb" / "run_tests.py").write_text("def test_smoke(): pass\n", encoding="utf-8")

    expected_stage_ids = [stage["id"] for stage in jobs._PIPELINE_STAGES]
    expected_workflows = [stage["workflow"] for stage in jobs._PIPELINE_STAGES]

    with jobs._jobs_lock:
        jobs._jobs.clear()

    real_recovery = jobs._job_artifact_recovery
    real_failure = jobs._job_artifact_failure

    def _mock_recovery(job: dict, project_root: Path) -> tuple[bool, str]:
        stage = str(job.get("stage_id") or job.get("workflow") or "")
        workflow = str(job.get("workflow") or "")
        if stage == "ssot" or workflow == "ssot-gen":
            ssot_path = user_workspace_root / ip / "yaml" / f"{ip}.ssot.yaml"
            return ssot_path.is_file(), f"test mock validated artifact: {ip}/yaml/{ip}.ssot.yaml"
        if stage == "rtl" or workflow == "rtl-gen":
            compile_path = user_workspace_root / ip / "rtl" / "rtl_compile.json"
            return compile_path.is_file(), "test mock validated artifact: rtl/rtl_compile.json"
        return real_recovery(job, project_root)

    def _mock_failure(job: dict, project_root: Path) -> tuple[bool, str]:
        stage = str(job.get("stage_id") or job.get("workflow") or "")
        workflow = str(job.get("workflow") or "")
        if stage == "rtl" or workflow == "rtl-gen":
            return False, ""
        return real_failure(job, project_root)

    monkeypatch.setattr(jobs, "_job_artifact_recovery", _mock_recovery)
    monkeypatch.setattr(jobs, "_job_artifact_failure", _mock_failure)

    with _mock_worker("author") as (author_url, author_worker), _mock_worker("verify") as (verify_url, verify_worker):
        monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "1")
        monkeypatch.setenv("WORKER_URL_DEFAULT", author_url)
        monkeypatch.setenv("WORKER_URL_RTL_GEN", author_url)
        for env_name in (
            "WORKER_URL_LINT",
            "WORKER_URL_TB_GEN",
            "WORKER_URL_SIM",
            "WORKER_URL_COVERAGE",
            "WORKER_URL_SIM_DEBUG",
            "WORKER_URL_CONTRACT_REFLECTION",
            "WORKER_URL_SYN",
            "WORKER_URL_STA",
            "WORKER_URL_PNR",
            "WORKER_URL_STA_POST",
        ):
            monkeypatch.setenv(env_name, verify_url)

        client = _make_client(tmp_path, monkeypatch)
        dispatch = client.post("/api/pipeline/dispatch", json={
            "ip": ip,
            "model": "gpt-5.3-codex",
            "schedule": "auto",
        })
        assert dispatch.status_code == 200, dispatch.text
        body = dispatch.json()
        assert body["schedule"] == "dag"
        assert [job["stage_id"] for job in body["jobs"]] == expected_stage_ids

        # DAG dispatch spawns next stages as their dependencies complete, and
        # each spawn requires one /api/jobs round-trip to discover it. Poll
        # until every stage hits "completed" or until the budget expires.
        rows = []
        deadline = time.time() + 30
        while time.time() < deadline:
            jobs_resp = client.get("/api/jobs")
            assert jobs_resp.status_code == 200, jobs_resp.text
            rows = jobs_resp.json()["jobs"]
            if (
                len(rows) == len(expected_stage_ids)
                and all(row["status"] == "completed" for row in rows)
            ):
                break
            time.sleep(0.2)
        assert len(rows) == len(expected_stage_ids)
        assert {row["stage_id"] for row in rows} == set(expected_stage_ids)
        assert all(row["status"] == "completed" for row in rows)

        all_requests = author_worker.requests + verify_worker.requests
        assert len(all_requests) == len(expected_stage_ids)
        dispatched_workflows = [item["payload"]["workflow"] for item in all_requests]
        assert sorted(dispatched_workflows) == sorted(expected_workflows)
        assert author_worker.requests
        assert verify_worker.requests

        sim_runs = [
            item["payload"] for item in verify_worker.requests
            if item["payload"]["workflow"] == "sim"
        ]
        assert len(sim_runs) == 1
        sim_payload = sim_runs[0]
        artifact_types = {item["artifact_type"] for item in sim_payload["artifact_versions"]}
        assert {"ssot", "rtl", "tb"}.issubset(artifact_types)
        assert "ssot:" in sim_payload["context"]
        assert "rtl:" in sim_payload["context"]
        assert "tb:" in sim_payload["context"]

    with jobs._jobs_lock:
        jobs._jobs.clear()


def test_pipeline_dispatch_persists_db_identity_for_admin_sessions(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs
    from core.atlas_db import AtlasDB

    ip = "db_identity_ip"
    ip_dir = tmp_path / ip
    # Valid SSOT/RTL evidence so the strict completion gate accepts rtl and the
    # pipeline reaches completed (this test asserts DB status == completed).
    _write_minimal_valid_ssot_rtl_fixture(ip_dir, ip)

    with jobs._jobs_lock:
        jobs._jobs.clear()

    _patch_rtl_gate_for_fixture(monkeypatch, jobs, ip, tmp_path)

    with _mock_worker("pipeline") as (worker_url, _worker):
        # Orchestrator mode (global env) so worker URL resolution uses
        # WORKER_URL_DEFAULT instead of the single-main-loop port.
        monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "1")
        monkeypatch.setenv("ATLAS_ADMIN_USERS", "u")
        monkeypatch.setenv("WORKER_URL_DEFAULT", worker_url)
        client = _make_client(tmp_path, monkeypatch)

        dispatch = client.post("/api/pipeline/dispatch", json={
            "ip": ip,
            "stages": ["rtl", "lint"],
            "schedule": "auto",
            "exec_mode": "orchestrator",
        })
        assert dispatch.status_code == 200, dispatch.text
        pipeline_id = dispatch.json()["pipeline_id"]

        rows = []
        for _ in range(20):
            jobs_resp = client.get("/api/jobs")
            assert jobs_resp.status_code == 200, jobs_resp.text
            rows = jobs_resp.json()["jobs"]
            if len(rows) == 2 and all(row["status"] == "completed" for row in rows):
                break
            time.sleep(0.1)

        assert {row["stage_id"] for row in rows} == {"rtl", "lint"}
        assert all(row["pipeline_run_id"] == pipeline_id for row in rows)
        assert all(row["workflow_run_id"] for row in rows)
        assert len({row["db_session_id"] for row in rows}) == 1

        with AtlasDB(str(tmp_path / "atlas.db")) as db:
            run_rows = db._fetchall(
                """
                SELECT id, workflow, status, model_profile, session_id, workspace_id, ip_id
                  FROM workflow_runs
                 ORDER BY started_at ASC
                """
            )
            assert [row["workflow"] for row in run_rows] == ["rtl-gen", "lint"]
            assert {row["status"] for row in run_rows} == {"completed"}
            # rtl-gen defaults to gpt-5.3-codex, lint defaults to deepseek
            # (see _WORKER_MODEL_DEFAULTS in atlas_api_jobs.py).
            assert [row["model_profile"] for row in run_rows] == ["gpt-5.3-codex", "deepseek"]
            assert len({row["session_id"] for row in run_rows}) == 1
            sessions = db.list_all_sessions()
            assert len(sessions) == 1
            assert sessions[0]["ip"] == ip
            assert sessions[0]["pipeline_run_id"] == pipeline_id
            rtl_versions = db._fetchall("SELECT workspace_id, ip_id FROM rtl_versions")
            assert len(rtl_versions) == 1
            assert rtl_versions[0]["workspace_id"] == run_rows[0]["workspace_id"]
            assert rtl_versions[0]["ip_id"] == run_rows[0]["ip_id"]
            attached = db._fetchall(
                "SELECT role FROM run_artifact_versions WHERE run_id = ?",
                (run_rows[0]["id"],),
            )
            assert [row["role"] for row in attached] == ["output"]

        admin = client.get("/api/admin/sessions")
        assert admin.status_code == 200, admin.text
        admin_sessions = admin.json()["sessions"]
        assert admin_sessions[0]["ip"] == ip
        assert admin_sessions[0]["pipeline_run_id"] == pipeline_id

    with jobs._jobs_lock:
        jobs._jobs.clear()


def test_pipeline_dependency_failure_blocks_downstream_and_records_db_status(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs
    from core.atlas_db import AtlasDB

    ip = "blocked_dependency_ip"
    (tmp_path / ip / "rtl").mkdir(parents=True)

    with jobs._jobs_lock:
        jobs._jobs.clear()

    with _mock_worker("pipeline", fail_workflows={"rtl-gen"}) as (worker_url, _worker):
        # Orchestrator mode (global env) so worker URL resolution uses
        # WORKER_URL_DEFAULT instead of the single-main-loop port. The dispatch
        # body exec_mode alone does not flip _resolve_worker_url's env read.
        monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "1")
        monkeypatch.setenv("WORKER_URL_DEFAULT", worker_url)
        client = _make_client(tmp_path, monkeypatch)

        dispatch = client.post("/api/pipeline/dispatch", json={
            "ip": ip,
            "stages": ["rtl", "lint"],
            "schedule": "auto",
            "exec_mode": "orchestrator",
        })
        assert dispatch.status_code == 200, dispatch.text
        pipeline_id = dispatch.json()["pipeline_id"]

        rows = []
        for _ in range(20):
            jobs_resp = client.get("/api/jobs")
            assert jobs_resp.status_code == 200, jobs_resp.text
            rows = jobs_resp.json()["jobs"]
            by_stage = {row["stage_id"]: row for row in rows}
            if by_stage.get("rtl", {}).get("status") == "error" and by_stage.get("lint", {}).get("status") == "blocked":
                break
            time.sleep(0.1)

        by_stage = {row["stage_id"]: row for row in rows}
        assert by_stage["rtl"]["status"] == "error"
        assert by_stage["lint"]["status"] == "blocked"
        assert by_stage["lint"]["error"] == "blocked by rtl-gen error"
        assert all(row["pipeline_run_id"] == pipeline_id for row in rows)

        with AtlasDB(str(tmp_path / "atlas.db")) as db:
            run_rows = db._fetchall(
                "SELECT workflow, status, error_summary FROM workflow_runs ORDER BY started_at ASC"
            )
            assert [(row["workflow"], row["status"]) for row in run_rows] == [
                ("rtl-gen", "error"),
                ("lint", "blocked"),
            ]
            assert run_rows[1]["error_summary"] == "blocked by rtl-gen error"

    with jobs._jobs_lock:
        jobs._jobs.clear()


def test_worker_completion_without_stage_evidence_is_not_marked_green(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs
    from core.atlas_db import AtlasDB

    ip = "missing_evidence_ip"
    (tmp_path / ip).mkdir(parents=True)

    with jobs._jobs_lock:
        jobs._jobs.clear()

    # Isolate the gate's pure "missing required evidence" branch: stub the
    # stage-engine refresh so it does NOT run the real ssot-rtl engine (which,
    # against an SSOT-less tmp fixture, would short-circuit to a blocked
    # ssot-rtl.json and reclassify this as `blocked`). With no engine run and no
    # worker-written artifact, _job_artifact_recovery fails and the gate emits
    # `error: missing required evidence for rtl`. The gate itself is unchanged;
    # the engine helper just needs the real workflow/ scripts + a real SSOT,
    # which is not the unit under test here. The dedicated stage-engine-blocked
    # contract is covered by test_worker_reported_completed_with_blocked_*.
    monkeypatch.setattr(jobs, "_refresh_completed_stage_evidence", lambda job, pr: None)

    with _mock_worker("pipeline", write_artifacts=False) as (worker_url, _worker):
        monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "1")
        monkeypatch.setenv("WORKER_URL_DEFAULT", worker_url)
        client = _make_client(tmp_path, monkeypatch)

        dispatch = client.post("/api/pipeline/dispatch", json={
            "ip": ip,
            "stages": ["rtl", "lint"],
            "schedule": "auto",
            "exec_mode": "orchestrator",
        })
        assert dispatch.status_code == 200, dispatch.text
        pipeline_id = dispatch.json()["pipeline_id"]

        rows = []
        for _ in range(20):
            jobs_resp = client.get("/api/jobs")
            assert jobs_resp.status_code == 200, jobs_resp.text
            rows = jobs_resp.json()["jobs"]
            by_stage = {row["stage_id"]: row for row in rows}
            if by_stage.get("rtl", {}).get("status") == "error" and by_stage.get("lint", {}).get("status") == "blocked":
                break
            time.sleep(0.1)

        by_stage = {row["stage_id"]: row for row in rows}
        assert by_stage["rtl"]["status"] == "error"
        assert "missing required evidence for rtl" in by_stage["rtl"]["error"]
        assert by_stage["lint"]["status"] == "blocked"
        assert all(row["pipeline_run_id"] == pipeline_id for row in rows)

        state = client.get(f"/api/pipeline/state?ip={ip}")
        assert state.status_code == 200, state.text
        assert state.json()["stages"]["rtl"]["state"] == "failed"

        with AtlasDB(str(tmp_path / "atlas.db")) as db:
            run_rows = db._fetchall(
                "SELECT workflow, status, error_summary FROM workflow_runs ORDER BY started_at ASC"
            )
            assert [(row["workflow"], row["status"]) for row in run_rows] == [
                ("rtl-gen", "error"),
                ("lint", "blocked"),
            ]
            assert "missing required evidence for rtl" in run_rows[0]["error_summary"]

    with jobs._jobs_lock:
        jobs._jobs.clear()


def test_worker_reported_completed_with_blocked_stage_engine_blocks_downstream(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Task 4 + Task 1 #3: when the worker reports `completed` but the
    deterministic stage engine explicitly reports the owning stage as
    `blocked` (e.g. ssot-rtl cannot proceed without locked truth / a human
    gate), the owning job must become `blocked` (NOT `error`), downstream
    pending jobs must become `blocked`, and the DB rows must mirror both."""
    import atlas_api_jobs as jobs
    from core.atlas_db import AtlasDB

    ip = "blocked_engine_ip"
    ip_dir = tmp_path / "u" / "default" / ip
    ip_dir.mkdir(parents=True)

    with jobs._jobs_lock:
        jobs._jobs.clear()

    # Simulate the real ssot-rtl engine reporting blocked: write the blocked
    # stage log + todo gate and stamp job['stage_evidence_status']='blocked',
    # which is exactly what WorkflowStageEngine.run_stage('ssot-rtl') does when
    # it can't proceed. This drives the gate's blocked branch without needing
    # the real workflow/ scripts. The gate itself is unchanged.
    def _blocked_refresh(job: dict, pr) -> None:
        stage = str(job.get("stage_id") or job.get("workflow") or "")
        workflow = str(job.get("workflow") or "")
        if stage == "rtl" or workflow == "rtl-gen":
            _write_blocked_ssot_rtl_fixture(ip_dir, ip, "SSOT not found")
            job["stage_evidence_status"] = "blocked"
            job["stage_evidence_summary"] = "[ssot-rtl] blocked: SSOT not found"

    monkeypatch.setattr(jobs, "_refresh_completed_stage_evidence", _blocked_refresh)

    with _mock_worker("pipeline") as (worker_url, _worker):
        monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "1")
        monkeypatch.setenv("WORKER_URL_DEFAULT", worker_url)
        client = _make_client(tmp_path, monkeypatch)

        dispatch = client.post("/api/pipeline/dispatch", json={
            "ip": ip,
            "stages": ["rtl", "lint"],
            "schedule": "auto",
            "exec_mode": "orchestrator",
        })
        assert dispatch.status_code == 200, dispatch.text
        pipeline_id = dispatch.json()["pipeline_id"]

        rows = []
        for _ in range(20):
            jobs_resp = client.get("/api/jobs")
            assert jobs_resp.status_code == 200, jobs_resp.text
            rows = jobs_resp.json()["jobs"]
            by_stage = {row["stage_id"]: row for row in rows}
            if by_stage.get("rtl", {}).get("status") == "blocked" and by_stage.get("lint", {}).get("status") == "blocked":
                break
            time.sleep(0.1)

        by_stage = {row["stage_id"]: row for row in rows}
        assert by_stage["rtl"]["status"] == "blocked", by_stage.get("rtl")
        assert "stage evidence failed" in by_stage["rtl"]["error"]
        assert by_stage["lint"]["status"] == "blocked"
        assert all(row["pipeline_run_id"] == pipeline_id for row in rows)

        # Pipeline state must preserve blocked distinctly from failed.
        state = client.get(f"/api/pipeline/state?ip={ip}")
        assert state.status_code == 200, state.text
        assert state.json()["stages"]["rtl"]["state"] == "blocked"

        with AtlasDB(str(tmp_path / "atlas.db")) as db:
            run_rows = db._fetchall(
                "SELECT workflow, status FROM workflow_runs ORDER BY started_at ASC"
            )
            assert [(row["workflow"], row["status"]) for row in run_rows] == [
                ("rtl-gen", "blocked"),
                ("lint", "blocked"),
            ]

    with jobs._jobs_lock:
        jobs._jobs.clear()


def test_rtl_stage_evidence_gate_rejects_placeholder_sources(tmp_path: Path) -> None:
    import atlas_api_jobs as jobs

    ip = "placeholder_rtl_ip"
    ip_dir = tmp_path / ip
    (ip_dir / "rtl").mkdir(parents=True)
    (ip_dir / "list").mkdir(parents=True)
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input logic clk);\n// TBD: datapath\nendmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\n", encoding="utf-8")
    # The placeholder gate only fires once the stage has actually run, proven by
    # a verdict artifact (rtl/rtl_compile.json or logs/stage_engine/ssot-rtl.json);
    # otherwise a fresh create_ip scaffold (which carries a TODO/placeholder)
    # would read as failed before rtl-gen ever ran. Write the verdict here so the
    # placeholder check is reached.
    (ip_dir / "rtl" / "rtl_compile.json").write_text(
        '{"errors":0,"diagnostics":0,"returncode":0}\n', encoding="utf-8"
    )

    failed, reason = jobs._job_artifact_failure(
        {"ip": ip, "workflow": "rtl-gen", "stage_id": "rtl"},
        tmp_path,
    )

    assert failed is True
    assert "placeholder RTL markers" in reason


def test_rtl_scaffold_without_verdict_is_not_marked_failed(tmp_path: Path) -> None:
    """Mirror of the placeholder gate's lower bound (Task 1 #4): a fresh
    create_ip scaffold carries a TODO/placeholder rtl/<ip>.sv + list/<ip>.f but
    NO verdict artifact (no rtl_compile.json / ssot-rtl.json). The gate must NOT
    flag it as failed, so a brand-new IP does not read rtl=failed before rtl-gen
    ever runs."""
    import atlas_api_jobs as jobs

    ip = "scaffold_only_rtl_ip"
    ip_dir = tmp_path / ip
    (ip_dir / "rtl").mkdir(parents=True)
    (ip_dir / "list").mkdir(parents=True)
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input logic clk);\n// TODO: implement\nendmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\n", encoding="utf-8")

    failed, reason = jobs._job_artifact_failure(
        {"ip": ip, "workflow": "rtl-gen", "stage_id": "rtl"},
        tmp_path,
    )

    assert failed is False, reason


@_PHASE3_SKIP
def test_orchestrator_chat_run_to_green_dispatches_workers_and_records_chat(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs
    from core.atlas_db import AtlasDB

    ip = "chat_green_ip"
    (tmp_path / ip / "yaml").mkdir(parents=True)
    (tmp_path / ip / "rtl").mkdir(parents=True)
    (tmp_path / ip / "tb").mkdir(parents=True)

    with jobs._jobs_lock:
        jobs._jobs.clear()

    with _mock_worker("orch") as (worker_url, worker):
        monkeypatch.setenv("WORKER_URL_DEFAULT", worker_url)
        client = _make_client(tmp_path, monkeypatch)

        resp = client.post("/api/pipeline/orchestrator/chat", json={
            "ip": ip,
            "message": "SPI IP 하나 run to green 해줘",
            "exec_mode": "orchestrator",
        })
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["ok"] is True
        assert body["action"] == "dispatch"
        assert body["ip"] == ip
        assert body["pipeline_run_id"] == body["pipeline_id"]
        assert "pipeline_run_id=" in body["reply"]
        assert [job["stage_id"] for job in body["jobs"]] == [stage["id"] for stage in jobs._PIPELINE_STAGES]

        rows = []
        for _ in range(30):
            jobs_resp = client.get("/api/jobs")
            assert jobs_resp.status_code == 200, jobs_resp.text
            rows = jobs_resp.json()["jobs"]
            if len(rows) == len(jobs._PIPELINE_STAGES) and all(row["status"] == "completed" for row in rows):
                break
            time.sleep(0.1)

        assert len(rows) == len(jobs._PIPELINE_STAGES)
        by_stage = {row["stage_id"]: row for row in rows}
        assert by_stage["ssot"]["model"] == "gpt-5.5"
        assert by_stage["rtl"]["model"] == "gpt-5.3-codex"
        assert by_stage["tb"]["model"] == "deepseek"
        assert by_stage["lint"]["toolchain"] == "pyslang + verilator"
        assert by_stage["coverage"]["toolchain"] == "verilator coverage + VCD"
        assert by_stage["sim-debug"]["model"] == "kimi"
        assert by_stage["contract-check"]["toolchain"] == "deterministic contract validators"
        assert all(row["pipeline_run_id"] == body["pipeline_id"] for row in rows)
        assert all(row["user_id"] == "u" for row in rows)
        assert worker.requests
        assert all(req["payload"]["user_id"] == "u" for req in worker.requests)
        assert all(req["payload"]["pipeline_run_id"] == body["pipeline_id"] for req in worker.requests)

        with AtlasDB(str(tmp_path / "atlas.db")) as db:
            ip_rows = db._fetchall("SELECT id FROM ip_blocks WHERE ip_name = ?", (ip,))
            assert ip_rows
            events = [
                db._row_to_dict(row, "trace_events")
                for row in db._fetchall(
                    "SELECT * FROM trace_events WHERE ip_id = ? ORDER BY created_at ASC",
                    (ip_rows[0]["id"],),
                )
            ]
            assert any(event["event_type"] == "chat_message" for event in events)
            assert any(event["event_type"] == "chat_response" for event in events)
            assert sum(1 for event in events if event["event_type"] == "workflow_dispatch") == len(jobs._PIPELINE_STAGES)

        status = client.post("/api/pipeline/orchestrator/chat", json={
            "ip": ip,
            "message": "status?",
        })
        assert status.status_code == 200, status.text
        assert status.json()["action"] == "status"
        assert "completed" in status.json()["reply"]

    with jobs._jobs_lock:
        jobs._jobs.clear()


@_PHASE3_SKIP
def test_orchestrator_chat_dedupes_active_ip_stage(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs

    ip = "dedupe_chat_ip"
    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs["active-rtl"] = {
            "job_id": "active-rtl",
            "run_id": "worker-run-1",
            "worker": "http://127.0.0.1:9",
            "workflow": "rtl-gen",
            "stage_id": "rtl",
            "ip": ip,
            "status": "running",
            "session": f"u/{ip}/pipeline/existing/05-rtl-gen",
            "pipeline_id": "existing",
            "pipeline_run_id": "existing",
            "user_id": "u",
            "_last_polled": time.time(),
        }

    client = _make_client(tmp_path, monkeypatch)
    resp = client.post("/api/pipeline/orchestrator/chat", json={
        "ip": ip,
        "message": "run to green",
        "exec_mode": "orchestrator",
    })
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ok"] is True
    assert body["deduped"] is True
    assert body["status"] == "already_running"
    assert body["existing_jobs"][0]["job_id"] == "active-rtl"

    with jobs._jobs_lock:
        assert list(jobs._jobs) == ["active-rtl"]
        jobs._jobs.clear()


@_PHASE3_SKIP
def test_orchestrator_chat_korean_spi_create_prompt_runs_full_pipeline(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs
    from core.atlas_db import AtlasDB

    with jobs._jobs_lock:
        jobs._jobs.clear()

    with _mock_worker("spi-create") as (worker_url, worker):
        monkeypatch.setenv("WORKER_URL_DEFAULT", worker_url)
        client = _make_client(tmp_path, monkeypatch)

        resp = client.post("/api/pipeline/orchestrator/chat", json={
            "message": "SPI IP 하나 만들어줘",
            "exec_mode": "orchestrator",
        })
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["ok"] is True
        assert body["action"] == "dispatch"
        assert body["ip"] == "SPI"
        assert body["pipeline_run_id"] == body["pipeline_id"]
        assert [job["stage_id"] for job in body["jobs"]] == [stage["id"] for stage in jobs._PIPELINE_STAGES]

        state_data = {}
        for _ in range(60):
            state_resp = client.get("/api/pipeline/state?ip=SPI")
            assert state_resp.status_code == 200, state_resp.text
            state_data = state_resp.json()
            stage_states = [
                state_data["stages"][stage["id"]]["state"]
                for stage in jobs._PIPELINE_STAGES
            ]
            if all(state == "passed" for state in stage_states):
                break
            time.sleep(0.1)

        assert all(
            state_data["stages"][stage["id"]]["state"] == "passed"
            for stage in jobs._PIPELINE_STAGES
        ), state_data
        assert (tmp_path / "SPI" / "yaml" / "SPI.ssot.yaml").exists()
        assert (tmp_path / "SPI" / "rtl" / "SPI.sv").exists()
        assert (tmp_path / "SPI" / "sim" / "results.xml").exists()
        assert len(worker.requests) == len(jobs._PIPELINE_STAGES)
        assert all(req["payload"]["ip"] == "SPI" for req in worker.requests)
        assert all("SPI IP 하나 만들어줘" in req["payload"]["task"] for req in worker.requests)
        assert all(req["payload"]["pipeline_run_id"] == body["pipeline_id"] for req in worker.requests)

        status = client.post("/api/pipeline/orchestrator/chat", json={
            "message": "SPI IP 상태?",
        })
        assert status.status_code == 200, status.text
        assert status.json()["action"] == "status"
        assert "completed" in status.json()["reply"]

        with AtlasDB(str(tmp_path / "atlas.db")) as db:
            ip_rows = db._fetchall("SELECT id FROM ip_blocks WHERE ip_name = ?", ("SPI",))
            assert ip_rows
            events = [
                db._row_to_dict(row, "trace_events")
                for row in db._fetchall(
                    "SELECT * FROM trace_events WHERE ip_id = ? ORDER BY created_at ASC",
                    (ip_rows[0]["id"],),
                )
            ]
            assert any(
                event["event_type"] == "chat_message"
                and event["payload"].get("content") == "SPI IP 하나 만들어줘"
                for event in events
            )
            assert sum(1 for event in events if event["event_type"] == "workflow_dispatch") == len(jobs._PIPELINE_STAGES)

    with jobs._jobs_lock:
        jobs._jobs.clear()


@_PHASE3_SKIP
def test_pipeline_state_poll_advances_run_to_green_without_jobs_endpoint(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs
    from core.atlas_db import AtlasDB

    ip = "state_poll_green_ip"
    (tmp_path / ip).mkdir(parents=True)

    with jobs._jobs_lock:
        jobs._jobs.clear()

    with _mock_worker("statepoll") as (worker_url, worker):
        monkeypatch.setenv("WORKER_URL_DEFAULT", worker_url)
        client = _make_client(tmp_path, monkeypatch)

        resp = client.post("/api/pipeline/orchestrator/chat", json={
            "ip": ip,
            "message": "run to green",
            "exec_mode": "orchestrator",
        })
        assert resp.status_code == 200, resp.text
        pipeline_id = resp.json()["pipeline_id"]

        state_data = {}
        for _ in range(20):
            state_resp = client.get(f"/api/pipeline/state?ip={ip}")
            assert state_resp.status_code == 200, state_resp.text
            state_data = state_resp.json()
            states = [
                state_data["stages"][stage["id"]]["state"]
                for stage in jobs._PIPELINE_STAGES
            ]
            if all(state == "passed" for state in states):
                break
            time.sleep(0.1)

        assert state_data["rtl_version_id"] == "rtl-v001"
        assert all(
            state_data["stages"][stage["id"]]["state"] == "passed"
            for stage in jobs._PIPELINE_STAGES
        )
        assert len(worker.status_hits) == len(jobs._PIPELINE_STAGES)
        assert len(worker.result_hits) == len(jobs._PIPELINE_STAGES)

        with AtlasDB(str(tmp_path / "atlas.db")) as db:
            run_rows = db._fetchall(
                "SELECT status, input_summary FROM workflow_runs ORDER BY started_at ASC"
            )
            assert len(run_rows) == len(jobs._PIPELINE_STAGES)
            assert {row["status"] for row in run_rows} == {"completed"}
            assert all(pipeline_id in row["input_summary"] for row in run_rows)

    with jobs._jobs_lock:
        jobs._jobs.clear()


@_PHASE3_SKIP
def test_three_team_members_run_orchestrated_ips_without_identity_mixing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs
    import src.atlas_ui as atlas_ui
    from core.atlas_db import AtlasDB

    with jobs._jobs_lock:
        jobs._jobs.clear()

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_ADMIN_AUTH_MODE", "db")
    monkeypatch.setenv("ATLAS_ADMIN_LOGIN_REQUIRED", "1")
    monkeypatch.setenv("ATLAS_ADMIN_USERS", "lead")
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.setenv("ATLAS_TRACE_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.delenv("ATLAS_LOCAL_ADMIN", raising=False)
    monkeypatch.delenv("ATLAS_ADMIN_BYPASS", raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    lead = TestClient(app)
    users = {
        "alice": (TestClient(app), "team_spi"),
        "bob": (TestClient(app), "team_uart"),
        "carol": (TestClient(app), "team_dma"),
    }

    lead_reg = lead.post("/api/auth/register", json={"username": "lead", "password": "pw"})
    assert lead_reg.status_code == 200, lead_reg.text
    assert lead_reg.json()["user"]["role"] == "admin"

    for username, (client, _ip) in users.items():
        reg = client.post("/api/auth/register", json={"username": username, "password": "pw"})
        assert reg.status_code == 200, reg.text
        assert reg.json()["user"]["role"] == "user"

    with _mock_worker("team") as (worker_url, worker):
        monkeypatch.setenv("WORKER_URL_DEFAULT", worker_url)

        pipelines: dict[str, str] = {}
        for username, (client, ip) in users.items():
            resp = client.post("/api/pipeline/orchestrator/chat", json={
                "ip": ip,
                "message": f"{ip} IP run to green",
                "exec_mode": "orchestrator",
            })
            assert resp.status_code == 200, resp.text
            body = resp.json()
            assert body["action"] == "dispatch"
            assert body["user_id"] == username
            assert body["ip"] == ip
            pipelines[ip] = body["pipeline_id"]

        state_by_ip: dict[str, dict] = {}
        for _username, (client, ip) in users.items():
            state_data = {}
            for _ in range(60):
                state_resp = client.get(f"/api/pipeline/state?ip={ip}")
                assert state_resp.status_code == 200, state_resp.text
                state_data = state_resp.json()
                stage_states = [
                    state_data["stages"][stage["id"]]["state"]
                    for stage in jobs._PIPELINE_STAGES
                ]
                if all(state == "passed" for state in stage_states):
                    break
                time.sleep(0.1)
            state_by_ip[ip] = state_data

        for username, (_client, ip) in users.items():
            state_data = state_by_ip[ip]
            assert state_data["ip"] == ip
            assert all(
                state_data["stages"][stage["id"]]["state"] == "passed"
                for stage in jobs._PIPELINE_STAGES
            ), f"{username}/{ip} did not reach green: {state_data}"

        expected_jobs = len(users) * len(jobs._PIPELINE_STAGES)
        assert len(worker.requests) == expected_jobs
        for req in worker.requests:
            payload = req["payload"]
            ip = payload["ip"]
            username = next(name for name, (_client, candidate_ip) in users.items() if candidate_ip == ip)
            assert payload["user_id"] == username
            assert payload["pipeline_run_id"] == pipelines[ip]
            assert payload["session"].startswith(f"{username}/{ip}/pipeline/{pipelines[ip]}/")

        with AtlasDB(str(tmp_path / "atlas.db")) as db:
            db_users = {
                row["username"]: row["id"]
                for row in db._fetchall("SELECT id, username FROM users")
            }
            assert {"lead", *users.keys()}.issubset(db_users)

            run_rows = db._fetchall(
                """
                SELECT r.workflow, r.status, r.model_profile, r.input_summary,
                       s.user_id AS session_user_id,
                       w.owner_user_id AS workspace_owner_user_id,
                       i.ip_name
                  FROM workflow_runs r
                  JOIN sessions s ON s.id = r.session_id
                  JOIN workspaces w ON w.id = r.workspace_id
                  JOIN ip_blocks i ON i.id = r.ip_id
                 ORDER BY r.started_at ASC
                """
            )
            assert len(run_rows) == expected_jobs

            runs_by_ip: dict[str, list[dict]] = {}
            for row in run_rows:
                runs_by_ip.setdefault(row["ip_name"], []).append(dict(row))
            assert set(runs_by_ip) == {ip for _client, ip in users.values()}

            for username, (_client, ip) in users.items():
                rows = runs_by_ip[ip]
                summaries = [json.loads(row["input_summary"] or "{}") for row in rows]
                assert len(rows) == len(jobs._PIPELINE_STAGES)
                assert {row["status"] for row in rows} == {"completed"}
                assert {row["session_user_id"] for row in rows} == {db_users[username]}
                assert {row["workspace_owner_user_id"] for row in rows} == {db_users[username]}
                assert {summary["user_id"] for summary in summaries} == {username}
                assert {summary["ip"] for summary in summaries} == {ip}
                assert {summary["pipeline_run_id"] for summary in summaries} == {pipelines[ip]}
                assert {summary["exec_mode"] for summary in summaries} == {"orchestrator"}
                assert [row["workflow"] for row in rows] == [
                    stage["workflow"] for stage in jobs._PIPELINE_STAGES
                ]
                assert rows[0]["model_profile"] == "deepseek"
                assert any(row["model_profile"] == "gpt-5.3-codex" for row in rows)
                assert any(row["model_profile"] == "kimi" for row in rows)
                assert any(row["model_profile"] == "glm-5.1" for row in rows)

            artifact_rows = db._fetchall(
                """
                SELECT i.ip_name, w.owner_user_id, av.artifact_type, av.primary_path
                  FROM artifact_versions av
                  JOIN ip_blocks i ON i.id = av.ip_id
                  JOIN workspaces w ON w.id = av.workspace_id
                 ORDER BY av.created_at ASC
                """
            )
            artifacts_by_ip: dict[str, list[dict]] = {}
            for row in artifact_rows:
                artifacts_by_ip.setdefault(row["ip_name"], []).append(dict(row))
            assert set(artifacts_by_ip) == {ip for _client, ip in users.values()}
            for username, (_client, ip) in users.items():
                artifacts = artifacts_by_ip[ip]
                assert {row["owner_user_id"] for row in artifacts} == {db_users[username]}
                assert {row["artifact_type"] for row in artifacts} >= {"ssot", "rtl", "tb"}
                assert all((row["primary_path"] or "").startswith(f"{ip}/") for row in artifacts)

            trace_rows = db._fetchall(
                """
                SELECT te.event_type, te.actor_user_id, i.ip_name
                  FROM trace_events te
                  JOIN ip_blocks i ON i.id = te.ip_id
                 WHERE te.event_type IN ('chat_message', 'chat_response', 'workflow_dispatch')
                """
            )
            trace_by_ip: dict[str, list[dict]] = {}
            for row in trace_rows:
                trace_by_ip.setdefault(row["ip_name"], []).append(dict(row))
            for username, (_client, ip) in users.items():
                events = trace_by_ip[ip]
                assert {event["actor_user_id"] for event in events} == {db_users[username]}
                assert any(event["event_type"] == "chat_message" for event in events)
                assert any(event["event_type"] == "chat_response" for event in events)
                assert sum(
                    1 for event in events if event["event_type"] == "workflow_dispatch"
                ) == len(jobs._PIPELINE_STAGES)

        admin = lead.get("/api/admin/sessions")
        assert admin.status_code == 200, admin.text
        admin_sessions = admin.json()["sessions"]
        session_by_pipeline = {
            row["pipeline_run_id"]: row
            for row in admin_sessions
            if row.get("pipeline_run_id") in set(pipelines.values())
        }
        assert set(session_by_pipeline) == set(pipelines.values())
        for username, (_client, ip) in users.items():
            session = session_by_pipeline[pipelines[ip]]
            assert session["owner_username"] == username
            assert session["ip"] == ip
            assert session["workflow"] == jobs._PIPELINE_STAGES[-1]["workflow"]
            assert session["latest_workflow_status"] == "completed"

    with jobs._jobs_lock:
        jobs._jobs.clear()
