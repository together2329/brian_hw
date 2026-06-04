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
    captured: list[dict[str, object]] = []

    def _capture(job: dict[str, object]) -> None:
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
        "alice/default/uart/ssot-gen",
        "alice/default/uart/rtl-gen",
    ]
    assert all(job["project_root"] == str(tmp_path) for job in captured)


def test_warm_pool_adds_next_likely_workers_for_rtl_context(
    tmp_path: Path,
    monkeypatch,
) -> None:
    captured: list[dict[str, object]] = []
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
        "alice/default/uart/ssot-gen",
        "alice/default/uart/rtl-gen",
        "alice/default/uart/lint",
        "alice/default/uart/tb-gen",
    ]


def test_warm_pool_uses_workspace_session_for_worker_partition(
    tmp_path: Path,
    monkeypatch,
) -> None:
    captured: list[dict[str, object]] = []
    monkeypatch.setattr(jobs, "_ensure_lazy_worker", lambda job: captured.append(dict(job)))

    result = jobs.schedule_worker_warmup(
        ip="uart",
        owner="alice",
        db_user_id="uid-alice",
        workspace_session="alt",
        active_workflow="rtl-gen",
        project_root_value=tmp_path,
        reason="test",
        background=False,
    )

    assert result["workspace_session"] == "alt"
    assert [job["session"] for job in captured] == [
        "alice/alt/uart/ssot-gen",
        "alice/alt/uart/rtl-gen",
        "alice/alt/uart/lint",
        "alice/alt/uart/tb-gen",
    ]
    assert len({job["worker"] for job in captured}) == len(captured)
    assert all("alt" in str(job["worker_partition"]) for job in captured)


def test_warm_pool_derives_workspace_session_from_canonical_session(
    tmp_path: Path,
    monkeypatch,
) -> None:
    captured: list[dict[str, object]] = []
    monkeypatch.setattr(jobs, "_ensure_lazy_worker", lambda job: captured.append(dict(job)))

    result = jobs.schedule_worker_warmup(
        ip="uart",
        owner="alice",
        db_user_id="uid-alice",
        session_name="alice/branch2/uart/rtl-gen",
        active_workflow="rtl-gen",
        project_root_value=tmp_path,
        reason="test",
        background=False,
    )

    assert result["workspace_session"] == "branch2"
    assert captured[0]["session"] == "alice/branch2/uart/ssot-gen"


def test_direct_lazy_worker_dispatch_uses_active_workspace_session(
    tmp_path: Path,
    monkeypatch,
) -> None:
    captured: list[dict[str, object]] = []
    monkeypatch.setattr(jobs, "_ensure_lazy_worker", lambda job: captured.append(dict(job)))
    monkeypatch.setenv("ATLAS_ACTIVE_IP", "uart")
    monkeypatch.setenv("ATLAS_ACTIVE_SESSION", "alice/alt/uart/rtl-gen")

    jobs._ensure_lazy_worker_for_direct_dispatch(
        "http://127.0.0.1:6411",
        "rtl-gen",
        str(tmp_path),
    )

    assert captured[0]["session"] == "alice/alt/uart/rtl-gen"


def test_direct_lazy_worker_dispatch_derives_ip_from_active_session(
    tmp_path: Path,
    monkeypatch,
) -> None:
    captured: list[dict[str, object]] = []
    monkeypatch.setattr(jobs, "_ensure_lazy_worker", lambda job: captured.append(dict(job)))
    monkeypatch.delenv("ATLAS_ACTIVE_IP", raising=False)
    monkeypatch.setenv("ATLAS_ACTIVE_SESSION", "alice/alt/uart/orchestrator")

    jobs._ensure_lazy_worker_for_direct_dispatch(
        "http://127.0.0.1:6411",
        "rtl-gen",
        str(tmp_path),
    )

    assert captured[0]["session"] == "alice/alt/uart/rtl-gen"


def test_warm_pool_skips_without_real_ip(tmp_path: Path, monkeypatch) -> None:
    captured: list[dict[str, object]] = []
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
    captured: list[dict[str, object]] = []
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
