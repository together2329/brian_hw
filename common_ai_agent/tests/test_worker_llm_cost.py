"""Verify that HeadlessWorkflowRunner._call_llm writes an llm_calls row
with cost_usd to atlas.db when a worker LLM call succeeds.
"""

from __future__ import annotations

import os
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from core.atlas_db import AtlasDB


@pytest.fixture
def db(tmp_path):
    atlas = AtlasDB(str(tmp_path / "atlas.db"))
    atlas.init_db()
    yield atlas
    atlas.close()


def _make_llm_response(cost_usd: float = 0.005, in_tok: int = 100, out_tok: int = 50, cache_tok: int = 10) -> Any:
    """Build a minimal LLMResponse-like object with usage populated."""
    return SimpleNamespace(
        stage="ssot-gen",
        model="test-model",
        raw_response='{"files": []}',
        parsed_artifacts=[],
        usage={
            "input": in_tok,
            "output": out_tok,
            "cache_read": cache_tok,
            "cost": {
                "usd": cost_usd,
                "pricing_per_1m": {"input": 3.0, "cache": 0.3, "output": 15.0},
            },
        },
        error="",
        status="ok",
    )


def test_call_llm_writes_llm_calls_row(db, tmp_path, monkeypatch):
    """_call_llm must insert one llm_calls row with cost_usd > 0."""
    from src.headless_workflow import HeadlessWorkflowRunner

    fake_response = _make_llm_response(cost_usd=0.0042)

    # Stub out the LLM provider so no real HTTP call is made.
    mock_provider = MagicMock()
    mock_provider.complete.return_value = fake_response
    mock_provider.available_reason.return_value = ""

    runner = HeadlessWorkflowRunner(root=tmp_path, model="test-model", llm_provider=mock_provider)

    db_path = str(tmp_path / "atlas.db")
    monkeypatch.setenv("ATLAS_SESSION_ID", "sess-test-001")
    monkeypatch.setenv("ATLAS_IP_ID", "ip-test-001")
    monkeypatch.setenv("ATLAS_WORKFLOW", "ssot-gen")
    monkeypatch.setenv("ATLAS_DB_PATH", db_path)

    context = {"ip": "test_ip", "requirement_text": "dummy requirement"}

    # Stub _stage_prompt so we don't need a real stage config.
    with patch.object(runner, "_stage_prompt", return_value=("sys", "usr")), \
         patch.object(runner, "_write_progress"), \
         patch.object(runner, "_write_heartbeat"), \
         patch.object(runner, "_write_llm_log"), \
         patch("builtins.open", side_effect=lambda *a, **kw: open(*a, **kw)):  # allow real file ops
        result = runner._call_llm("ssot-gen", "test_ip", context)

    assert result.status == "ok"

    rows = db._execute("SELECT * FROM llm_calls WHERE session_id = 'sess-test-001'").fetchall()
    assert len(rows) == 1, f"Expected 1 llm_calls row, got {len(rows)}"
    row = dict(rows[0])
    assert row["cost_usd"] == pytest.approx(0.0042, rel=1e-4)
    assert row["tokens_input"] == 100
    assert row["tokens_output"] == 50
    assert row["cache_read_tokens"] == 10
    assert row["ip_id"] == "ip-test-001"
    assert row["workflow"] == "ssot-gen"
    assert row["call_role"] == "worker"
    assert row["latency_ms"] > 0


def test_call_llm_records_zero_cost_gracefully(db, tmp_path, monkeypatch):
    """When pricing is unavailable (cost.usd == 0), the row is still written."""
    from src.headless_workflow import HeadlessWorkflowRunner

    fake_response = _make_llm_response(cost_usd=0.0)
    fake_response.usage = {"input": 50, "output": 20, "cache_read": 0}

    mock_provider = MagicMock()
    mock_provider.complete.return_value = fake_response
    mock_provider.available_reason.return_value = ""

    runner = HeadlessWorkflowRunner(root=tmp_path, model="test-model", llm_provider=mock_provider)

    db_path = str(tmp_path / "atlas.db")
    monkeypatch.setenv("ATLAS_SESSION_ID", "sess-zero-cost")
    monkeypatch.setenv("ATLAS_DB_PATH", db_path)
    monkeypatch.delenv("ATLAS_IP_ID", raising=False)
    monkeypatch.delenv("ATLAS_WORKFLOW", raising=False)

    context = {"ip": "ip_zero", "requirement_text": ""}

    with patch.object(runner, "_stage_prompt", return_value=("sys", "usr")), \
         patch.object(runner, "_write_progress"), \
         patch.object(runner, "_write_heartbeat"), \
         patch.object(runner, "_write_llm_log"):
        result = runner._call_llm("ssot-gen", "ip_zero", context)

    rows = db._execute("SELECT * FROM llm_calls WHERE session_id = 'sess-zero-cost'").fetchall()
    assert len(rows) == 1
    row = dict(rows[0])
    assert row["cost_usd"] == pytest.approx(0.0)
    assert row["ip_id"] == "ip_zero"


def test_call_llm_does_not_raise_when_db_missing(tmp_path, monkeypatch):
    """A bad DB path must not propagate — accounting errors are silenced."""
    from src.headless_workflow import HeadlessWorkflowRunner

    fake_response = _make_llm_response()
    mock_provider = MagicMock()
    mock_provider.complete.return_value = fake_response
    mock_provider.available_reason.return_value = ""

    runner = HeadlessWorkflowRunner(root=tmp_path, model="test-model", llm_provider=mock_provider)

    monkeypatch.setenv("ATLAS_DB_PATH", "/nonexistent/path/atlas.db")
    monkeypatch.setenv("ATLAS_SESSION_ID", "sess-bad-db")

    context = {"ip": "bad_ip"}

    with patch.object(runner, "_stage_prompt", return_value=("sys", "usr")), \
         patch.object(runner, "_write_progress"), \
         patch.object(runner, "_write_heartbeat"), \
         patch.object(runner, "_write_llm_log"):
        result = runner._call_llm("ssot-gen", "bad_ip", context)

    # Must still return the response even when DB write fails.
    assert result.status == "ok"


def test_agent_server_worker_reads_llm_token_globals_from_module():
    """Worker ReAct accounting must not import token ints by value."""
    source = (
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        + "/core/agent_server.py"
    )
    text = open(source, encoding="utf-8").read()

    assert "import src.llm_client as _worker_llm_client" in text
    assert "last_input_tokens, last_output_tokens" not in text
    assert 'getattr(_worker_llm_client, "last_input_tokens"' in text
    assert "emit_tool_fn=_worker_emit_tool_line" in text
    assert "emit_token_fn=_worker_emit_token" in text
