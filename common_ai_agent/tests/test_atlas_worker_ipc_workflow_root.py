from __future__ import annotations

import importlib
from pathlib import Path


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
