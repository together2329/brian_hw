"""Regression tests for /api/pipeline/orchestrator/chat IP token parsing.

When the chat message body spells out an IP token (e.g. `run ssot for foo_test`),
the handler must prefer that IP over the dropdown `ip` field in the request
body. Verified end-to-end against the real DB — the resulting
`orchestrator_runs.ip_id` must resolve to the message-derived `ip_blocks` row,
not the dropdown one.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.orchestrator import runner as runner_mod
from src.orchestrator.runner import SubmitOutcome


class _StubRunner:
    """Captures submit_or_attach kwargs without firing the real LLM loop."""

    def __init__(self):
        self.calls = []
        self._counter = 0

    def submit_or_attach(self, **kwargs):
        self.calls.append(kwargs)
        self._counter += 1
        return SubmitOutcome(run_id=f"stub-run-{self._counter}", status="started")

    def shutdown(self, wait=False):
        pass


def _make_client(tmp_path: Path, monkeypatch) -> TestClient:
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_ADMIN_AUTH_MODE", "db")
    monkeypatch.setenv("ATLAS_ADMIN_LOGIN_REQUIRED", "1")
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_TRANSPORT", "thread")
    monkeypatch.delenv("ATLAS_LOCAL_ADMIN", raising=False)
    monkeypatch.delenv("ATLAS_ADMIN_BYPASS", raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = TestClient(atlas_ui.create_app())
    reg = client.post(
        "/api/auth/register", json={"username": "validator", "password": "pw"}
    )
    assert reg.status_code == 200, reg.text
    return client


@pytest.fixture
def stub_runner(monkeypatch):
    stub = _StubRunner()
    runner_mod.set_runner_for_test(stub)
    monkeypatch.setattr(runner_mod, "get_runner", lambda db_path: stub)
    yield stub
    runner_mod.set_runner_for_test(None)


def test_message_body_ip_token_overrides_dropdown_ip(
    tmp_path, monkeypatch, stub_runner
):
    """`run ssot for foo_test` + body ip=bar_baz must persist foo_test."""
    client = _make_client(tmp_path, monkeypatch)
    resp = client.post(
        "/api/pipeline/orchestrator/chat",
        json={"message": "run ssot for foo_test", "ip": "bar_baz"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ok"] is True
    assert body["ip"] == "foo_test"

    # The runner must have been called with ip_name=foo_test, and the ip_id
    # must resolve to the foo_test ip_blocks row in the real DB (no mocks).
    assert len(stub_runner.calls) == 1
    call = stub_runner.calls[0]
    assert call["ip_name"] == "foo_test"

    from core.atlas_db import AtlasDB

    with AtlasDB(str(tmp_path / "atlas.db")) as db:
        ip_row = db.get_ip_block_by_name("foo_test")
        assert ip_row is not None, "foo_test ip_blocks row should exist"
        assert call["ip_id"] == ip_row["id"]
        # The dropdown ip must NOT have been used.
        bar_row = db.get_ip_block_by_name("bar_baz")
        assert bar_row is None, (
            "dropdown ip bar_baz must not have been upserted "
            "when the message named foo_test"
        )


def test_ip_equals_token_in_message_overrides_dropdown(
    tmp_path, monkeypatch, stub_runner
):
    client = _make_client(tmp_path, monkeypatch)
    resp = client.post(
        "/api/pipeline/orchestrator/chat",
        json={"message": "kick off ip=alpha_one now", "ip": "fallback_ip"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["ip"] == "alpha_one"
    assert stub_runner.calls[0]["ip_name"] == "alpha_one"


def test_on_token_in_message_overrides_dropdown(tmp_path, monkeypatch, stub_runner):
    client = _make_client(tmp_path, monkeypatch)
    resp = client.post(
        "/api/pipeline/orchestrator/chat",
        json={"message": "build on beta_two please", "ip": "fallback_ip"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["ip"] == "beta_two"


def test_message_without_ip_token_falls_back_to_dropdown(
    tmp_path, monkeypatch, stub_runner
):
    """When the message has no extractable IP token, the dropdown `ip` wins."""
    client = _make_client(tmp_path, monkeypatch)
    resp = client.post(
        "/api/pipeline/orchestrator/chat",
        json={"message": "create ipA and run to green", "ip": "ipA"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["ip"] == "ipA"
    assert stub_runner.calls[0]["ip_name"] == "ipA"
