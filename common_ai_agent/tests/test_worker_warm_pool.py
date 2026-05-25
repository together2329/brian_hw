from __future__ import annotations

from pathlib import Path

import pytest

import src.atlas_api_jobs as jobs


@pytest.fixture(autouse=True)
def _reset_warm_pool(monkeypatch):
    monkeypatch.setenv("ATLAS_EXEC_MODE", "orchestrator")
    monkeypatch.setenv("ATLAS_SINGLE_MAIN_LOOP", "0")
    monkeypatch.setenv("ATLAS_LAZY_WORKERS", "1")
    monkeypatch.setenv("ATLAS_WORKER_WARM_POOL", "1")
    monkeypatch.setenv("ATLAS_WORKFLOW_WORKER_PER_USER", "1")
    monkeypatch.setenv("ATLAS_WORKFLOW_WORKER_PORT_BASE", "6400")
    monkeypatch.setenv("ATLAS_WORKFLOW_WORKER_PORT_SPAN", "200")
    for key in (
        "WORKER_URL_DEFAULT",
        "WORKER_URL_SSOT_GEN",
        "WORKER_URL_RTL_GEN",
        "WORKER_URL_LINT",
        "WORKER_URL_TB_GEN",
        "WORKER_URL_SIM",
        "ATLAS_WORKER_WARM_ALWAYS",
    ):
        monkeypatch.delenv(key, raising=False)
    with jobs._WARM_WORKER_LOCK:
        jobs._WARM_WORKER_INFLIGHT.clear()
    with jobs._LAZY_WORKER_LOCK:
        jobs._LAZY_WORKER_PROCS.clear()
        jobs._LAZY_WORKER_LAST_BUSY.clear()
    jobs._SESSION_WORKER_PORTS.clear()
    jobs._SESSION_WORKER_KEYS_BY_PORT.clear()
    yield
    with jobs._WARM_WORKER_LOCK:
        jobs._WARM_WORKER_INFLIGHT.clear()
    with jobs._LAZY_WORKER_LOCK:
        jobs._LAZY_WORKER_PROCS.clear()
        jobs._LAZY_WORKER_LAST_BUSY.clear()
    jobs._SESSION_WORKER_PORTS.clear()
    jobs._SESSION_WORKER_KEYS_BY_PORT.clear()


def test_warm_pool_schedules_common_workers_for_active_ip(
    tmp_path: Path,
    monkeypatch,
) -> None:
    captured: list[dict] = []

    def _capture(job: dict) -> None:
        captured.append(dict(job))

    monkeypatch.setattr(jobs, "_ensure_lazy_worker", _capture)

    result = jobs.schedule_worker_warmup(
        ip="uart",
        owner="alice",
        db_user_id="uid-alice",
        active_workflow="orchestrator",
        project_root_value=tmp_path,
        reason="test",
        background=False,
    )

    assert result["enabled"] is True
    assert [item["workflow"] for item in result["scheduled"]] == ["ssot-gen", "rtl-gen"]
    assert [job["workflow"] for job in captured] == ["ssot-gen", "rtl-gen"]
    assert [job["session"] for job in captured] == [
        "alice/uart/ssot-gen",
        "alice/uart/rtl-gen",
    ]
    assert all(job["project_root"] == str(tmp_path) for job in captured)


def test_warm_pool_adds_next_likely_workers_for_rtl_context(
    tmp_path: Path,
    monkeypatch,
) -> None:
    captured: list[dict] = []
    monkeypatch.setattr(jobs, "_ensure_lazy_worker", lambda job: captured.append(dict(job)))

    result = jobs.schedule_worker_warmup(
        ip="uart",
        owner="alice",
        db_user_id="uid-alice",
        active_workflow="rtl-gen",
        project_root_value=tmp_path,
        reason="test",
        background=False,
    )

    workflows = [item["workflow"] for item in result["scheduled"]]
    assert workflows == ["ssot-gen", "rtl-gen", "lint", "tb-gen"]
    assert [job["session"] for job in captured] == [
        "alice/uart/ssot-gen",
        "alice/uart/rtl-gen",
        "alice/uart/lint",
        "alice/uart/tb-gen",
    ]


def test_warm_pool_skips_without_real_ip(tmp_path: Path, monkeypatch) -> None:
    captured: list[dict] = []
    monkeypatch.setattr(jobs, "_ensure_lazy_worker", lambda job: captured.append(dict(job)))

    result = jobs.schedule_worker_warmup(
        ip="default",
        owner="alice",
        db_user_id="uid-alice",
        active_workflow="orchestrator",
        project_root_value=tmp_path,
        reason="test",
        background=False,
    )

    assert result == {"enabled": True, "reason": "no_active_ip", "scheduled": []}
    assert captured == []


def test_warm_pool_requires_explicit_enable(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("ATLAS_WORKER_WARM_POOL", raising=False)
    captured: list[dict] = []
    monkeypatch.setattr(jobs, "_ensure_lazy_worker", lambda job: captured.append(dict(job)))

    result = jobs.schedule_worker_warmup(
        ip="uart",
        owner="alice",
        db_user_id="uid-alice",
        active_workflow="orchestrator",
        project_root_value=tmp_path,
        reason="test",
        background=False,
    )

    assert result == {"enabled": False, "reason": "disabled", "scheduled": []}
    assert captured == []
