from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))


def _make_client(tmp_path: Path, monkeypatch) -> TestClient:
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.setenv("ATLAS_EXEC_MODE", "orchestrator")
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "1")
    monkeypatch.setenv("ATLAS_SINGLE_MAIN_LOOP", "0")
    monkeypatch.setenv("ATLAS_WORKER_TRANSPORT", "ipc")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "SOURCE_ROOT", tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = TestClient(atlas_ui.create_app())
    reg = client.post("/api/auth/register", json={"username": "u", "password": "pw"})
    assert reg.status_code == 200, reg.text
    return client


def test_job_dispatch_uses_ipc_worker_address_and_command(tmp_path: Path, monkeypatch) -> None:
    import atlas_api_jobs as jobs

    with jobs._jobs_lock:
        jobs._jobs.clear()

    def fake_ipc_dispatch(job: dict) -> None:
        with jobs._jobs_lock:
            live = jobs._jobs[job["job_id"]]
            live["run_id"] = f"ipc-{job['job_id']}"
            live["status"] = "running"
            live["started_at"] = time.time()

    monkeypatch.setattr(jobs, "_dispatch_job_to_ipc_worker", fake_ipc_dispatch)

    (tmp_path / "ip_a").mkdir()
    client = _make_client(tmp_path, monkeypatch)
    resp = client.post("/api/job/dispatch", json={
        "workflow": "rtl-gen",
        "ip": "ip_a",
        "exec_mode": "orchestrator",
    })
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["worker_transport"] == "ipc"
    assert body["worker"].startswith("ipc://")
    assert ":5623" not in body["worker"]
    assert "atlas_worker_ipc" in body["worker_command"]
    assert "--port" not in body["worker_command"]


def test_dispatch_job_routes_ipc_without_http_urlopen(monkeypatch, tmp_path: Path) -> None:
    import urllib.request

    import atlas_api_jobs as jobs

    called: list[str] = []
    monkeypatch.setattr(jobs, "_dispatch_job_to_ipc_worker", lambda job: called.append(job["job_id"]))

    def fail_urlopen(*_args, **_kwargs):
        raise AssertionError("IPC dispatch must not call worker HTTP endpoints")

    monkeypatch.setattr(urllib.request, "urlopen", fail_urlopen)
    jobs._dispatch_job_to_worker({
        "job_id": "job-ipc",
        "worker": "ipc://u/orchestrator/rtl-gen",
        "worker_transport": "ipc",
        "workflow": "rtl-gen",
        "prompt": "run /ssot-rtl ip_a",
        "project_root": str(tmp_path),
    })

    assert called == ["job-ipc"]


def test_ipc_worker_paths_reject_symlinked_session_parent(tmp_path: Path) -> None:
    import atlas_api_jobs as jobs

    outside = tmp_path / "outside"
    outside.mkdir()
    os.symlink(outside, tmp_path / ".session", target_is_directory=True)
    paths = jobs._ipc_worker_paths(
        {"project_root": str(tmp_path), "job_id": "job-ipc"},
        "ipc-job-ipc",
    )

    with pytest.raises(ValueError, match="must not be a symlink"):
        jobs._prepare_ipc_worker_paths(paths, tmp_path)


def test_ipc_worker_paths_reject_symlinked_request_file(tmp_path: Path) -> None:
    import atlas_api_jobs as jobs

    paths = jobs._ipc_worker_paths(
        {"project_root": str(tmp_path), "job_id": "job-ipc"},
        "ipc-job-ipc",
    )
    paths["run_dir"].mkdir(parents=True)
    outside = tmp_path / "outside-request.json"
    outside.write_text("{}", encoding="utf-8")
    os.symlink(outside, paths["request"])

    with pytest.raises(ValueError, match="file must not be a symlink"):
        jobs._prepare_ipc_worker_paths(paths, tmp_path)


def test_ipc_worker_paths_create_private_run_directories(tmp_path: Path) -> None:
    import atlas_api_jobs as jobs

    paths = jobs._ipc_worker_paths(
        {"project_root": str(tmp_path), "job_id": "job-ipc"},
        "ipc-job-ipc",
    )

    jobs._prepare_ipc_worker_paths(paths, tmp_path)

    for directory in (tmp_path / ".session", tmp_path / ".session" / "workers-ipc", paths["run_dir"]):
        assert directory.is_dir()
        assert (directory.stat().st_mode & 0o777) == 0o700


def test_ipc_worker_paths_reject_symlinked_run_dir(tmp_path: Path) -> None:
    import atlas_api_jobs as jobs

    paths = jobs._ipc_worker_paths(
        {"project_root": str(tmp_path), "job_id": "job-ipc"},
        "ipc-job-ipc",
    )
    outside = tmp_path / "outside-run"
    outside.mkdir()
    paths["run_dir"].parent.mkdir(parents=True)
    paths["run_dir"].symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="must not be a symlink"):
        jobs._prepare_ipc_worker_paths(paths, tmp_path)

    assert not list(outside.rglob("request.json"))


def test_ipc_worker_paths_reject_dot_segment_job_id(tmp_path: Path) -> None:
    import atlas_api_jobs as jobs

    paths = jobs._ipc_worker_paths(
        {"project_root": str(tmp_path), "job_id": ".."},
        "ipc-unsafe",
    )

    jobs._prepare_ipc_worker_paths(paths, tmp_path)

    assert paths["run_dir"].parent == tmp_path / ".session" / "workers-ipc"
    assert paths["run_dir"].name != ".."
    assert paths["request"].parent == paths["run_dir"]
    assert not (tmp_path / ".session" / "request.json").exists()


def test_ipc_global_limit_keeps_ready_job_queued(monkeypatch, tmp_path: Path) -> None:
    import atlas_api_jobs as jobs

    monkeypatch.setenv("ATLAS_IPC_WORKER_MAX_CONCURRENT", "1")
    monkeypatch.setenv("ATLAS_IPC_WORKER_MAX_PER_USER", "9")
    monkeypatch.setenv("ATLAS_IPC_WORKER_MAX_PER_WORKFLOW", "9")
    dispatched: list[str] = []
    monkeypatch.setattr(jobs, "_dispatch_job_to_ipc_worker", lambda job: dispatched.append(job["job_id"]))

    running = {
        "job_id": "running",
        "worker": "ipc://u/orchestrator/rtl-gen",
        "worker_transport": "ipc",
        "workflow": "rtl-gen",
        "status": "running",
        "db_user_id": "u",
    }
    queued = {
        "job_id": "queued",
        "worker": "ipc://u/orchestrator/sim",
        "worker_transport": "ipc",
        "workflow": "sim",
        "status": "queued",
        "db_user_id": "u",
        "project_root": str(tmp_path),
    }
    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs[running["job_id"]] = running
        jobs._jobs[queued["job_id"]] = queued

    jobs._start_job_when_worker_free(queued)

    assert dispatched == []
    assert queued["status"] == "queued"
    assert queued["queue_reason"] == "ipc_global_limit"
    snapshot = jobs.worker_runtime_snapshot(tmp_path)
    assert snapshot["ipc"]["limits"]["max_concurrent"] == 1
    assert snapshot["ipc"]["running_count"] == 1
    assert snapshot["ipc"]["queued_count"] == 1


def test_ipc_user_and_workflow_limits_are_separate(monkeypatch, tmp_path: Path) -> None:
    import atlas_api_jobs as jobs

    monkeypatch.setenv("ATLAS_IPC_WORKER_MAX_CONCURRENT", "9")
    monkeypatch.setenv("ATLAS_IPC_WORKER_MAX_PER_USER", "1")
    monkeypatch.setenv("ATLAS_IPC_WORKER_MAX_PER_WORKFLOW", "1")
    dispatched: list[str] = []
    monkeypatch.setattr(jobs, "_dispatch_job_to_ipc_worker", lambda job: dispatched.append(job["job_id"]))

    running = {
        "job_id": "running",
        "worker": "ipc://u1/orchestrator/rtl-gen",
        "worker_transport": "ipc",
        "workflow": "rtl-gen",
        "status": "running",
        "db_user_id": "u1",
    }
    same_user = {
        "job_id": "same-user",
        "worker": "ipc://u1/orchestrator/sim",
        "worker_transport": "ipc",
        "workflow": "sim",
        "status": "queued",
        "db_user_id": "u1",
        "project_root": str(tmp_path),
    }
    same_workflow = {
        "job_id": "same-workflow",
        "worker": "ipc://u2/orchestrator/rtl-gen",
        "worker_transport": "ipc",
        "workflow": "rtl-gen",
        "status": "queued",
        "db_user_id": "u2",
        "project_root": str(tmp_path),
    }
    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs[running["job_id"]] = running
        jobs._jobs[same_user["job_id"]] = same_user
        jobs._jobs[same_workflow["job_id"]] = same_workflow

    jobs._start_job_when_worker_free(same_user)
    jobs._start_job_when_worker_free(same_workflow)

    assert dispatched == []
    assert same_user["queue_reason"] == "ipc_user_limit"
    assert same_workflow["queue_reason"] == "ipc_workflow_limit"


def test_ipc_dispatch_watcher_updates_job_from_response(tmp_path: Path, monkeypatch) -> None:
    import atlas_api_jobs as jobs

    monkeypatch.setattr(jobs, "_record_job_db_running", lambda job: None)
    finishes: list[tuple[str, str]] = []
    monkeypatch.setattr(
        jobs,
        "_finish_job_db_run",
        lambda job, status=None, error_summary=None: finishes.append((job["job_id"], status or job["status"])),
    )
    advances: list[str] = []
    monkeypatch.setattr(jobs, "_advance_pipeline_from", lambda job: advances.append(job["status"]))
    monkeypatch.setattr(jobs, "_enforce_completion_evidence_gate", lambda job, root: None)
    monkeypatch.setattr(jobs, "_ensure_stage_artifact_version_for_job", lambda job, root: None)

    class FakePopen:
        pid = 4242

        def __init__(self, cmd, **_kwargs):
            self.cmd = list(cmd)
            response = Path(self.cmd[self.cmd.index("--response") + 1])
            run_id = self.cmd[self.cmd.index("--run-id") + 1]
            response.parent.mkdir(parents=True, exist_ok=True)
            response.write_text(
                json.dumps({
                    "run_id": run_id,
                    "status": "completed",
                    "result": {
                        "run_id": run_id,
                        "status": "completed",
                        "result": "done",
                        "files_modified": ["ip_a/rtl/ip_a.sv"],
                        "files_examined": [],
                        "iterations": 2,
                    },
                    "entries": [
                        {"index": 0, "type": "task", "role": "user", "content": "run"}
                    ],
                }),
                encoding="utf-8",
            )

        def wait(self):
            return 0

        def poll(self):
            return None

    monkeypatch.setattr(jobs.subprocess, "Popen", FakePopen)

    job = {
        "job_id": "abc123",
        "run_id": "",
        "worker": "ipc://u/orchestrator/rtl-gen",
        "worker_transport": "ipc",
        "workflow": "rtl-gen",
        "stage_id": "rtl",
        "prompt": "run /ssot-rtl ip_a",
        "project_root": str(tmp_path),
        "source_root": str(PROJECT_ROOT),
        "session": "u/ip_a/rtl-gen",
        "model": "",
        "reasoning_effort": "",
        "toolchain": "",
        "run_mode": "engineering",
        "exec_mode": "orchestrator",
        "status": "pending",
        "started_at": 0.0,
    }
    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs[job["job_id"]] = job

    jobs._dispatch_job_to_ipc_worker(job)

    deadline = time.time() + 2.0
    while time.time() < deadline and not (
        job.get("status") == "completed" and finishes and advances
    ):
        time.sleep(0.01)

    assert job["status"] == "completed"
    assert job["run_id"] == "ipc-abc123"
    assert job["worker_pid"] == 4242
    assert job["files_modified"] == ["ip_a/rtl/ip_a.sv"]
    assert job["iterations"] == 2
    assert (tmp_path / str(job["worker_request_path"])).is_file()
    assert (tmp_path / str(job["worker_response_path"])).is_file()
    assert finishes[-1] == ("abc123", "completed")
    assert advances == ["completed"]


def test_ipc_dispatch_rejects_symlinked_session_parent(tmp_path: Path, monkeypatch) -> None:
    import atlas_api_jobs as jobs

    outside = tmp_path / "outside-session"
    outside.mkdir()
    (tmp_path / ".session").symlink_to(outside, target_is_directory=True)
    popen_calls: list[list[str]] = []
    monkeypatch.setattr(jobs.subprocess, "Popen", lambda cmd, **_kwargs: popen_calls.append(list(cmd)))
    monkeypatch.setattr(jobs, "_finish_job_db_run", lambda *_args, **_kwargs: None)
    job = {
        "job_id": "j-symlink",
        "worker": "ipc://u/orchestrator/rtl-gen",
        "worker_transport": "ipc",
        "workflow": "rtl-gen",
        "status": "pending",
        "attempt": 1,
        "max_attempts": 1,
        "project_root": str(tmp_path),
    }
    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs[job["job_id"]] = job

    jobs._dispatch_job_to_ipc_worker(job)

    assert popen_calls == []
    assert job["status"] == "error"
    assert ".session" in str(job["error"])
    assert not list(outside.rglob("request.json"))


def test_ipc_dispatch_rejects_symlinked_workers_parent(tmp_path: Path, monkeypatch) -> None:
    import atlas_api_jobs as jobs

    outside = tmp_path / "outside-workers"
    outside.mkdir()
    (tmp_path / ".session").mkdir()
    (tmp_path / ".session" / "workers-ipc").symlink_to(outside, target_is_directory=True)
    popen_calls: list[list[str]] = []
    monkeypatch.setattr(jobs.subprocess, "Popen", lambda cmd, **_kwargs: popen_calls.append(list(cmd)))
    monkeypatch.setattr(jobs, "_finish_job_db_run", lambda *_args, **_kwargs: None)
    job = {
        "job_id": "j-workers",
        "worker": "ipc://u/orchestrator/rtl-gen",
        "worker_transport": "ipc",
        "workflow": "rtl-gen",
        "status": "pending",
        "attempt": 1,
        "max_attempts": 1,
        "project_root": str(tmp_path),
    }
    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs[job["job_id"]] = job

    jobs._dispatch_job_to_ipc_worker(job)

    assert popen_calls == []
    assert job["status"] == "error"
    assert "workers-ipc" in str(job["error"])
    assert not list(outside.rglob("request.json"))


def test_worker_ipc_write_response_rejects_missing_parent(tmp_path: Path) -> None:
    from src.atlas_worker_ipc import _write_response

    response_path = tmp_path / ".session" / "workers-ipc" / "missing" / "response.json"

    with pytest.raises(ValueError, match="parent"):
        _write_response(response_path, {"status": "error"})

    assert not response_path.exists()


def test_worker_ipc_write_response_rejects_symlinked_response(tmp_path: Path) -> None:
    from src.atlas_worker_ipc import _write_response

    run_dir = tmp_path / ".session" / "workers-ipc" / "run"
    run_dir.mkdir(parents=True)
    outside = tmp_path / "outside-response.json"
    response_path = run_dir / "response.json"
    response_path.symlink_to(outside)

    with pytest.raises(ValueError, match="symlink"):
        _write_response(response_path, {"status": "error"})

    assert not outside.exists()


def test_ipc_job_log_streams_stdout_before_response(tmp_path: Path, monkeypatch) -> None:
    import atlas_api_jobs as jobs

    client = _make_client(tmp_path, monkeypatch)
    log_path = tmp_path / ".session" / "workers-ipc" / "j1" / "worker.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        "booting worker\nreading mctp/yaml/mctp.ssot.yaml\n",
        encoding="utf-8",
    )
    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs["j1"] = {
            "job_id": "j1",
            "run_id": "ipc-j1",
            "worker": "ipc://u/orchestrator/ssot-gen",
            "worker_transport": "ipc",
            "workflow": "ssot-gen",
            "status": "running",
            "project_root": str(tmp_path),
            "worker_log_path": ".session/workers-ipc/j1/worker.log",
            "worker_response_path": ".session/workers-ipc/j1/response.json",
            "user_id": "u",
        }

    resp = client.get("/api/job/j1/log?since=1")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["source"] == "ipc-stdout"
    assert body["worker_log_pending"] is True
    assert [entry["content"] for entry in body["entries"]] == [
        "reading mctp/yaml/mctp.ssot.yaml"
    ]
    with jobs._jobs_lock:
        assert jobs._jobs["j1"]["worker_log_entries"] == 2


def test_ipc_job_log_uses_job_project_root_and_user_scope(tmp_path: Path, monkeypatch) -> None:
    import atlas_api_jobs as jobs

    client = _make_client(tmp_path, monkeypatch)
    user_root = tmp_path / "u" / "default"
    log_path = user_root / ".session" / "workers-ipc" / "j-user" / "worker.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("worker booted in user root\n", encoding="utf-8")
    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs["j-user"] = {
            "job_id": "j-user",
            "run_id": "ipc-j-user",
            "worker": "ipc://u/orchestrator/ssot-gen",
            "worker_transport": "ipc",
            "workflow": "ssot-gen",
            "status": "running",
            "project_root": str(user_root),
            "worker_log_path": ".session/workers-ipc/j-user/worker.log",
            "worker_response_path": ".session/workers-ipc/j-user/response.json",
            "user_id": "u",
        }
        jobs._jobs["j-other"] = {
            "job_id": "j-other",
            "run_id": "ipc-j-other",
            "worker": "ipc://other/orchestrator/ssot-gen",
            "worker_transport": "ipc",
            "workflow": "ssot-gen",
            "status": "running",
            "project_root": str(user_root),
            "worker_log_path": ".session/workers-ipc/j-user/worker.log",
            "worker_response_path": ".session/workers-ipc/j-user/response.json",
            "user_id": "other",
        }

    visible = client.get("/api/job/j-user/log")
    forbidden = client.get("/api/job/j-other/log")

    assert visible.status_code == 200, visible.text
    body = visible.json()
    assert body["source"] == "ipc-stdout"
    assert body["log_path"] == ".session/workers-ipc/j-user/worker.log"
    assert [entry["content"] for entry in body["entries"]] == ["worker booted in user root"]
    assert forbidden.status_code == 403, forbidden.text


def test_ipc_job_log_groups_stdout_tool_events(tmp_path: Path, monkeypatch) -> None:
    import atlas_api_jobs as jobs

    client = _make_client(tmp_path, monkeypatch)
    log_path = tmp_path / ".session" / "workers-ipc" / "j2" / "worker.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        "\n".join([
            "THOUGHT (4)",
            "┃ Checking files",
            '⏺ Read(path="counter/yaml/counter.ssot.yaml")',
            "⎿  2 lines",
            "│ 1 top_module:",
            "│ 2   name: counter",
        ]) + "\n",
        encoding="utf-8",
    )
    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs["j2"] = {
            "job_id": "j2",
            "run_id": "ipc-j2",
            "worker": "ipc://u/orchestrator/ssot-gen",
            "worker_transport": "ipc",
            "workflow": "ssot-gen",
            "status": "running",
            "project_root": str(tmp_path),
            "worker_log_path": ".session/workers-ipc/j2/worker.log",
            "worker_response_path": ".session/workers-ipc/j2/response.json",
            "started_at": 1716400006,
            "user_id": "u",
        }

    resp = client.get("/api/job/j2/log")

    assert resp.status_code == 200, resp.text
    entries = resp.json()["entries"]
    assert [entry["type"] for entry in entries] == ["log", "action", "observation"]
    assert entries[0]["content"] == "THOUGHT (4)\nChecking files"
    assert entries[1]["tool"] == "Read"
    assert entries[2]["role"] == "tool"
    assert "│ 1 top_module:" in entries[2]["content"]
    assert "│ 2   name: counter" in entries[2]["content"]


def test_ipc_timeout_retries_same_job_id_after_killing_attempt(tmp_path: Path, monkeypatch) -> None:
    import atlas_api_jobs as jobs

    monkeypatch.setenv("ATLAS_IPC_WORKER_TIMEOUT_SEC", "0.01")
    monkeypatch.setenv("ATLAS_IPC_WORKER_MAX_ATTEMPTS", "2")
    retries: list[tuple[str, int]] = []
    monkeypatch.setattr(jobs, "_record_job_db_retry", lambda job, reason: retries.append((reason, job["attempt"])))
    drains: list[str] = []
    monkeypatch.setattr(jobs, "_drain_ready_worker_queue", lambda: drains.append("drain"))
    finishes: list[str] = []
    monkeypatch.setattr(jobs, "_finish_job_db_run", lambda job, status=None, error_summary=None: finishes.append(status or job["status"]))

    class TimeoutProc:
        pid = 9001

        def __init__(self):
            self.terminated = False
            self.killed = False

        def wait(self, timeout=None):
            if timeout is not None:
                raise subprocess.TimeoutExpired(cmd="worker", timeout=timeout)
            return -15

        def poll(self):
            return -15 if self.terminated or self.killed else None

        def terminate(self):
            self.terminated = True

        def kill(self):
            self.killed = True

    job = {
        "job_id": "retryme",
        "run_id": "ipc-retryme",
        "worker": "ipc://u/orchestrator/rtl-gen",
        "worker_transport": "ipc",
        "workflow": "rtl-gen",
        "status": "running",
        "attempt": 1,
        "max_attempts": 2,
        "project_root": str(tmp_path),
    }
    proc = TimeoutProc()
    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs[job["job_id"]] = job
    with jobs._IPC_WORKER_LOCK:
        jobs._IPC_WORKER_PROCS[job["run_id"]] = proc

    jobs._watch_ipc_worker(job["job_id"], "ipc-retryme", tmp_path / "missing-response.json", proc)

    assert proc.terminated is True
    assert job["job_id"] == "retryme"
    assert job["status"] == "queued"
    assert job["attempt"] == 2
    assert job["retry_count"] == 1
    assert job["previous_run_ids"] == ["ipc-retryme"]
    assert job["run_id"] == ""
    assert retries and retries[-1][1] == 2
    assert drains == ["drain"]
    assert finishes == []


def test_ipc_stale_watcher_cannot_finish_newer_attempt(tmp_path: Path, monkeypatch) -> None:
    import atlas_api_jobs as jobs

    monkeypatch.setattr(jobs, "_finish_job_db_run", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(jobs, "_advance_pipeline_from", lambda *_args, **_kwargs: None)
    response = tmp_path / "response.json"
    response.write_text(json.dumps({"status": "completed", "result": {"result": "old"}}), encoding="utf-8")

    class DoneProc:
        pid = 7007

        def wait(self, timeout=None):
            return 0

        def poll(self):
            return 0

    job = {
        "job_id": "samejob",
        "run_id": "ipc-samejob-r2",
        "worker": "ipc://u/orchestrator/rtl-gen",
        "worker_transport": "ipc",
        "workflow": "rtl-gen",
        "status": "running",
        "attempt": 2,
        "project_root": str(tmp_path),
    }
    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs[job["job_id"]] = job

    jobs._watch_ipc_worker(job["job_id"], "ipc-samejob", response, DoneProc())

    assert job["status"] == "running"
    assert job["run_id"] == "ipc-samejob-r2"
    assert job.get("result_summary") in (None, "")
