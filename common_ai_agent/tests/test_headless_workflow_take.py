from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src import handoff_queue as hq
from src import headless_workflow as hw


class _FakeRunResult:
    def __init__(self, status: str) -> None:
        self.status = status
        self.stages: list = []

    def to_dict(self) -> dict:
        return {"status": self.status, "stages": []}


class _FakeRunner:
    def __init__(self, status: str = "pass") -> None:
        self._status = status
        self.calls: list = []

    def run(self, *, ip: str, requirement_path, stages):
        self.calls.append({"ip": ip, "stages": list(stages), "req": requirement_path})
        return _FakeRunResult(self._status)


def _seed_pending(ip_dir: Path, *, to_workflow: str = "rtl-gen", suffix: str = "EQ_A") -> dict:
    rec = {
        "schema": hq.SCHEMA,
        "handoff_id": hq.make_handoff_id(ip_dir.name, "sim-debug", to_workflow, suffix),
        "ip": ip_dir.name,
        "from_workflow": "sim-debug",
        "to_workflow": to_workflow,
        "scope": hq.make_scope(user_id="u", session_id="S", pipeline_run_id="P"),
        "reason": "FL-vs-RTL mismatch",
    }
    hq.write_pending(ip_dir, rec)
    return rec


def _run(args, runner: _FakeRunner) -> tuple[int, dict]:
    """Invoke _run_take with a captured-stdout fake runner; return (code, json)."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = hw._run_take(args, lambda: runner)
    return code, json.loads(buf.getvalue())


def test_take_with_no_pending_prints_none_available(tmp_path: Path) -> None:
    ip = "ip_a"
    (tmp_path / ip).mkdir()
    args = SimpleNamespace(root=str(tmp_path), ip=ip, workflow="rtl-gen", req="")

    runner = _FakeRunner(status="pass")
    code, payload = _run(args, runner)

    assert code == 0
    assert payload["status"] == "none_available"
    assert payload["workflow"] == "rtl-gen"
    assert runner.calls == []  # never invoked the workflow


def test_take_claims_runs_then_completes(tmp_path: Path) -> None:
    ip = "ip_b"
    ip_dir = tmp_path / ip
    ip_dir.mkdir()
    rec = _seed_pending(ip_dir)

    args = SimpleNamespace(root=str(tmp_path), ip=ip, workflow="rtl-gen", req="")
    runner = _FakeRunner(status="pass")
    code, payload = _run(args, runner)

    assert code == 0
    assert payload["status"] == "pass"
    assert payload["handoff_id"] == rec["handoff_id"]
    # Runner was called once with the canonical workflow stage.
    assert len(runner.calls) == 1
    assert runner.calls[0]["stages"] == ["rtl-gen"]
    # Handoff moved to done.
    found = hq.get(ip_dir, rec["handoff_id"])
    assert found is not None
    assert found[0] == "done"


def test_take_failure_releases_claim_back_to_pending(tmp_path: Path) -> None:
    ip = "ip_c"
    ip_dir = tmp_path / ip
    ip_dir.mkdir()
    rec = _seed_pending(ip_dir)

    args = SimpleNamespace(root=str(tmp_path), ip=ip, workflow="rtl-gen", req="")
    runner = _FakeRunner(status="fail")
    code, payload = _run(args, runner)

    assert code == 2
    assert payload["status"] == "fail"
    found = hq.get(ip_dir, rec["handoff_id"])
    assert found is not None
    assert found[0] == "pending"
    assert found[1]["released_at"]


def test_take_runner_exception_releases_claim(tmp_path: Path) -> None:
    ip = "ip_d"
    ip_dir = tmp_path / ip
    ip_dir.mkdir()
    rec = _seed_pending(ip_dir)

    class _BoomRunner:
        def run(self, **_):
            raise RuntimeError("provider blew up")

    args = SimpleNamespace(root=str(tmp_path), ip=ip, workflow="rtl-gen", req="")
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = hw._run_take(args, lambda: _BoomRunner())
    payload = json.loads(buf.getvalue())

    assert code == 2
    assert payload["status"] == "error"
    assert "provider blew up" in payload["error"]
    found = hq.get(ip_dir, rec["handoff_id"])
    assert found[0] == "pending"


def test_take_picks_oldest_pending_fifo(tmp_path: Path) -> None:
    ip = "ip_e"
    ip_dir = tmp_path / ip
    ip_dir.mkdir()

    scope = hq.make_scope(user_id="u", session_id="S", pipeline_run_id="P")
    older = {
        "schema": hq.SCHEMA,
        "handoff_id": hq.make_handoff_id(ip, "sim-debug", "rtl-gen", "OLDER"),
        "ip": ip,
        "from_workflow": "sim-debug",
        "to_workflow": "rtl-gen",
        "scope": dict(scope),
        "created_at": "2026-05-16T09:00:00Z",
    }
    newer = {
        "schema": hq.SCHEMA,
        "handoff_id": hq.make_handoff_id(ip, "sim-debug", "rtl-gen", "NEWER"),
        "ip": ip,
        "from_workflow": "sim-debug",
        "to_workflow": "rtl-gen",
        "scope": dict(scope),
        "created_at": "2026-05-16T12:00:00Z",
    }
    hq.write_pending(ip_dir, older)
    hq.write_pending(ip_dir, newer)

    args = SimpleNamespace(root=str(tmp_path), ip=ip, workflow="rtl-gen", req="")
    runner = _FakeRunner(status="pass")
    code, payload = _run(args, runner)

    assert code == 0
    assert payload["handoff_id"] == older["handoff_id"]
    # Older done, newer still pending.
    assert hq.get(ip_dir, older["handoff_id"])[0] == "done"
    assert hq.get(ip_dir, newer["handoff_id"])[0] == "pending"


def test_main_take_requires_workflow_flag(tmp_path: Path) -> None:
    ip = "ip_f"
    (tmp_path / ip).mkdir()
    with pytest.raises(SystemExit) as excinfo:
        hw.main([
            "--root", str(tmp_path),
            "--ip", ip,
            "--stages", "take",
            "--provider", "fake",
        ])
    assert excinfo.value.code != 0
