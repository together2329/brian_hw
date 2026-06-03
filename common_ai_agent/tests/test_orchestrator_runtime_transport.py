from __future__ import annotations

from pathlib import Path


def test_thread_transport_selects_legacy_runner(tmp_path: Path, monkeypatch) -> None:
    from src.orchestrator import runner as runner_mod
    from src.orchestrator.runtime import get_orchestrator_runtime

    legacy_runner = object()
    calls: list[str] = []

    def fake_get_runner(db_path: str):
        calls.append(db_path)
        return legacy_runner

    monkeypatch.setenv("ATLAS_ORCHESTRATOR_TRANSPORT", "thread")
    monkeypatch.setattr(runner_mod, "get_runner", fake_get_runner)

    runtime = get_orchestrator_runtime(str(tmp_path / "atlas.db"), project_root=tmp_path)

    assert runtime is legacy_runner
    assert calls == [str(tmp_path / "atlas.db")]


def test_orchestrator_mode_defaults_to_ipc_transport(monkeypatch) -> None:
    from src.orchestrator.runtime import orchestrator_transport

    monkeypatch.delenv("ATLAS_ORCHESTRATOR_TRANSPORT", raising=False)
    monkeypatch.setenv("ATLAS_EXEC_MODE", "orchestrator")

    assert orchestrator_transport() == "ipc"
