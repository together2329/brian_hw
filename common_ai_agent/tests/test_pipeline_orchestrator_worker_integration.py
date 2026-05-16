from __future__ import annotations

import json
import socket
import sys
import threading
import time
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterator

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))


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
    def __init__(self, name: str) -> None:
        self.name = name
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


@contextmanager
def _mock_worker(name: str) -> Iterator[tuple[str, _MockWorkerState]]:
    state = _MockWorkerState(name)

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
            self._json(200, {"run_id": state.add_run(payload)})

        def do_GET(self) -> None:  # noqa: N802 - stdlib handler hook
            if self.path.startswith("/status/"):
                run_id = self.path.rsplit("/", 1)[-1]
                state.status_hits.append(run_id)
                self._json(200, {"status": "completed", "iterations": 1})
                return
            if self.path.startswith("/result/"):
                run_id = self.path.rsplit("/", 1)[-1]
                state.result_hits.append(run_id)
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
    ) -> None:
        entry.status = "running"
        entry.started_at = time.time()
        entry.add_log("system", f"fake worker executing {workflow}", role="system")
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
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = TestClient(atlas_ui.create_app())
    reg = client.post("/api/auth/register", json={"username": "u", "password": "pw"})
    assert reg.status_code == 200, reg.text
    return client


def test_pipeline_dispatch_fans_out_to_other_worker_and_surfaces_handoff_state(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from src import handoff_queue as hq
    import atlas_api_jobs as jobs

    ip = "worker_pipe_ip"
    ip_dir = tmp_path / ip
    (ip_dir / "rtl").mkdir(parents=True)
    (ip_dir / "list").mkdir(parents=True)
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input logic clk, output logic done); assign done = clk; endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"../rtl/{ip}.sv\n", encoding="utf-8")

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
            assert payload["project_root"] == str(tmp_path)
            assert payload["source_root"].endswith("common_ai_agent")
            assert payload["ip"] == ip
            assert payload["session"].startswith(f"{ip}/pipeline/{dispatch_body['pipeline_id']}/")
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
    ip_dir = tmp_path / ip
    (ip_dir / "rtl").mkdir(parents=True)
    (ip_dir / "list").mkdir(parents=True)
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input logic clk, output logic done); assign done = clk; endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"../rtl/{ip}.sv\n", encoding="utf-8")

    with jobs._jobs_lock:
        jobs._jobs.clear()

    worker_calls: list[dict] = []
    with _agent_server_worker(monkeypatch, worker_calls) as rtl_url, _agent_server_worker(monkeypatch, worker_calls) as lint_url:
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
        for _ in range(20):
            jobs_resp = client.get("/api/jobs")
            assert jobs_resp.status_code == 200, jobs_resp.text
            rows = jobs_resp.json()["jobs"]
            if len(rows) == 2 and all(row["status"] == "completed" for row in rows):
                break
            time.sleep(0.1)

        assert {row["stage_id"] for row in rows} == {"rtl", "lint"}
        assert all(row["status"] == "completed" for row in rows)
        assert [call["workflow"] for call in worker_calls] == ["rtl-gen", "lint"]
        lint_call = worker_calls[1]
        assert lint_call["rtl_version_id"]
        assert lint_call["ip"] == ip
        assert lint_call["project_root"] == str(tmp_path)
        assert lint_call["session"].startswith(f"{ip}/pipeline/{dispatch.json()['pipeline_id']}/")
        assert "rtl_version_id:" in lint_call["context"]

    with jobs._jobs_lock:
        jobs._jobs.clear()


def test_full_ip_pipeline_can_complete_all_stages_across_two_workers(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs

    ip = "full_worker_pipe_ip"
    ip_dir = tmp_path / ip
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

        jobs_resp = client.get("/api/jobs")
        assert jobs_resp.status_code == 200, jobs_resp.text
        rows = jobs_resp.json()["jobs"]
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
