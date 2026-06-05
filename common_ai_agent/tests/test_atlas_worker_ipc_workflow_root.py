from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

import pytest


def test_ipc_worker_prefers_ip_local_workflow_root(tmp_path: Path) -> None:
    module = importlib.import_module("core.atlas_context")
    project_root = tmp_path / "project"
    source_root = tmp_path / "source"
    ip_workflow = project_root / "spi_core" / "workflow"
    central_workflow = source_root / "workflow"
    (ip_workflow / "ssot-gen").mkdir(parents=True)
    (central_workflow / "ssot-gen").mkdir(parents=True)

    resolved = module.resolve_ip_workflow_root(
        str(project_root),
        str(source_root),
        "spi_core",
    )

    assert resolved == ip_workflow


def test_ipc_worker_uses_project_root_when_it_is_the_ip_root(tmp_path: Path) -> None:
    module = importlib.import_module("core.atlas_context")
    ip_root = tmp_path / "spi_core"
    source_root = tmp_path / "source"
    ip_workflow = ip_root / "workflow"
    central_workflow = source_root / "workflow"
    (ip_workflow / "ssot-gen").mkdir(parents=True)
    (central_workflow / "ssot-gen").mkdir(parents=True)

    resolved = module.resolve_ip_workflow_root(str(ip_root), str(source_root), "spi_core")

    assert resolved == ip_workflow


def test_ipc_worker_configure_env_overwrites_stale_ip_root(
    tmp_path: Path,
    monkeypatch,
) -> None:
    worker = importlib.import_module("src.atlas_worker_ipc")
    project_root = tmp_path / "alice" / "default"
    ip = "spi_core"
    monkeypatch.setenv("ATLAS_IP_ROOT", f"alice/default/{ip}")

    worker._configure_env({
        "project_root": str(project_root),
        "source_root": str(Path(__file__).resolve().parents[1]),
        "session": f"alice/default/{ip}/pipeline/01-rtl-gen",
        "ip": ip,
        "workflow": "rtl-gen",
        "exec_mode": "orchestrator",
    })

    assert Path(os.environ["ATLAS_IP_ROOT"]) == project_root / ip


def test_ipc_worker_configure_env_preserves_ip_root_project_root(
    tmp_path: Path,
    monkeypatch,
) -> None:
    worker = importlib.import_module("src.atlas_worker_ipc")
    ip = "spi_core"
    ip_root = tmp_path / "alice" / "default" / ip
    monkeypatch.setenv("ATLAS_IP_ROOT", f"alice/default/{ip}")

    worker._configure_env({
        "project_root": str(ip_root),
        "source_root": str(Path(__file__).resolve().parents[1]),
        "session": f"alice/default/{ip}/pipeline/01-rtl-gen",
        "ip": ip,
        "workflow": "rtl-gen",
        "exec_mode": "orchestrator",
    })

    assert Path(os.environ["ATLAS_IP_ROOT"]) == ip_root


def test_ipc_worker_configure_env_rejects_unsafe_ip(
    tmp_path: Path,
    monkeypatch,
) -> None:
    worker = importlib.import_module("src.atlas_worker_ipc")
    monkeypatch.delenv("ATLAS_IP_ROOT", raising=False)

    with pytest.raises(ValueError, match="invalid IPC ip"):
        worker._configure_env({
            "project_root": str(tmp_path / "alice" / "default"),
            "source_root": str(Path(__file__).resolve().parents[1]),
            "session": "alice/default/ipA/pipeline/01-rtl-gen",
            "ip": "../bob/default/ipA",
            "workflow": "rtl-gen",
            "exec_mode": "orchestrator",
        })

    assert "ATLAS_IP_ROOT" not in os.environ


def test_ipc_worker_configure_env_rejects_absolute_ip(
    tmp_path: Path,
    monkeypatch,
) -> None:
    worker = importlib.import_module("src.atlas_worker_ipc")
    monkeypatch.delenv("ATLAS_IP_ROOT", raising=False)

    with pytest.raises(ValueError, match="invalid IPC ip"):
        worker._configure_env({
            "project_root": str(tmp_path / "alice" / "default"),
            "source_root": str(Path(__file__).resolve().parents[1]),
            "session": "alice/default/ipA/pipeline/01-rtl-gen",
            "ip": "/tmp/ipA",
            "workflow": "rtl-gen",
            "exec_mode": "orchestrator",
        })

    assert "ATLAS_IP_ROOT" not in os.environ


def test_ipc_worker_validate_paths_rejects_symlinked_session_parent(tmp_path: Path) -> None:
    worker = importlib.import_module("src.atlas_worker_ipc")
    project_root = tmp_path / "project"
    project_root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    os.symlink(outside, project_root / ".session", target_is_directory=True)
    request_path = project_root / ".session" / "workers-ipc" / "job" / "request.json"
    response_path = project_root / ".session" / "workers-ipc" / "job" / "response.json"

    with pytest.raises(ValueError, match="must not be a symlink"):
        worker._validate_ipc_paths(
            request_path,
            response_path,
            {"project_root": str(project_root)},
        )


def test_ipc_worker_validate_paths_rejects_response_outside_worker_root(
    tmp_path: Path,
) -> None:
    worker = importlib.import_module("src.atlas_worker_ipc")
    project_root = tmp_path / "project"
    run_dir = project_root / ".session" / "workers-ipc" / "job"
    run_dir.mkdir(parents=True)
    request_path = run_dir / "request.json"
    response_path = tmp_path / "outside" / "response.json"

    with pytest.raises(ValueError, match="under .session"):
        worker._validate_ipc_paths(
            request_path,
            response_path,
            {"project_root": str(project_root)},
        )


def test_ipc_worker_main_does_not_write_error_response_outside_worker_root(
    tmp_path: Path,
) -> None:
    worker = importlib.import_module("src.atlas_worker_ipc")
    project_root = tmp_path / "project"
    run_dir = project_root / ".session" / "workers-ipc" / "job"
    run_dir.mkdir(parents=True)
    request_path = run_dir / "request.json"
    outside_response = tmp_path / "outside" / "response.json"
    outside_response.parent.mkdir()
    request_path.write_text(
        json.dumps({
            "project_root": str(project_root),
            "workflow": "rtl-gen",
            "ip": "demo_ip",
            "task": "run rtl",
        }),
        encoding="utf-8",
    )

    status = worker.main([
        "--request",
        str(request_path),
        "--response",
        str(outside_response),
        "--run-id",
        "job",
    ])

    assert status == 1
    assert not outside_response.exists()


def test_ipc_worker_write_response_rejects_symlinked_response(tmp_path: Path) -> None:
    worker = importlib.import_module("src.atlas_worker_ipc")
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    link = tmp_path / "response.json"
    os.symlink(outside, link)

    with pytest.raises(ValueError, match="must not be a symlink"):
        worker._write_response(link, {"status": "completed"})


def test_ipc_worker_write_response_rejects_path_without_session_root(tmp_path: Path) -> None:
    worker = importlib.import_module("src.atlas_worker_ipc")
    response_path = tmp_path / "outside" / "response.json"
    response_path.parent.mkdir()

    with pytest.raises(ValueError, match="under .session"):
        worker._write_response(response_path, {"status": "completed"})

    assert not response_path.exists()


def test_orchestrator_supervisor_configure_env_overwrites_stale_ip_root(
    tmp_path: Path,
    monkeypatch,
) -> None:
    supervisor = importlib.import_module("src.atlas_orchestrator_supervisor_ipc")
    project_root = tmp_path / "alice" / "default"
    ip = "spi_core"
    monkeypatch.setenv("ATLAS_IP_ROOT", f"alice/default/{ip}")

    supervisor._configure_env({
        "project_root": str(project_root),
        "source_root": str(Path(__file__).resolve().parents[1]),
        "session_id": f"alice/default/{ip}/orchestrator",
        "ip_name": ip,
        "ip_id": "ip-db-1",
    })

    assert Path(os.environ["ATLAS_IP_ROOT"]) == project_root / ip


def test_orchestrator_supervisor_configure_env_preserves_ip_root_project_root(
    tmp_path: Path,
    monkeypatch,
) -> None:
    supervisor = importlib.import_module("src.atlas_orchestrator_supervisor_ipc")
    ip = "spi_core"
    ip_root = tmp_path / "alice" / "default" / ip
    monkeypatch.setenv("ATLAS_IP_ROOT", f"alice/default/{ip}")

    supervisor._configure_env({
        "project_root": str(ip_root),
        "source_root": str(Path(__file__).resolve().parents[1]),
        "session_id": f"alice/default/{ip}/orchestrator",
        "ip_name": ip,
        "ip_id": "ip-db-1",
    })

    assert Path(os.environ["ATLAS_IP_ROOT"]) == ip_root


def test_orchestrator_supervisor_configure_env_rejects_unsafe_ip(
    tmp_path: Path,
    monkeypatch,
) -> None:
    supervisor = importlib.import_module("src.atlas_orchestrator_supervisor_ipc")
    monkeypatch.delenv("ATLAS_IP_ROOT", raising=False)

    with pytest.raises(ValueError, match="invalid IPC ip"):
        supervisor._configure_env({
            "project_root": str(tmp_path / "alice" / "default"),
            "source_root": str(Path(__file__).resolve().parents[1]),
            "session_id": "alice/default/ipA/orchestrator",
            "ip_name": "/tmp/ipA",
            "ip_id": "ip-db-1",
        })

    assert "ATLAS_IP_ROOT" not in os.environ


def test_orchestrator_supervisor_configure_env_rejects_relative_path_ip(
    tmp_path: Path,
    monkeypatch,
) -> None:
    supervisor = importlib.import_module("src.atlas_orchestrator_supervisor_ipc")
    monkeypatch.delenv("ATLAS_IP_ROOT", raising=False)

    with pytest.raises(ValueError, match="invalid IPC ip"):
        supervisor._configure_env({
            "project_root": str(tmp_path / "alice" / "default"),
            "source_root": str(Path(__file__).resolve().parents[1]),
            "session_id": "alice/default/ipA/orchestrator",
            "ip_name": "../bob/default/ipA",
            "ip_id": "ip-db-1",
        })

    assert "ATLAS_IP_ROOT" not in os.environ
