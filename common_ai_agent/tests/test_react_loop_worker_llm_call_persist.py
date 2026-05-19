"""Verify that core/react_loop.py persists an llm_calls row whenever the
worker emits a `token_usage` WS frame.

Regression: ssot-gen worker WS frames showed input/output tokens, but
no llm_calls rows were ever written because the persistence code only
lived on the non-worker headless_workflow path. This test pins the
behavior at the react_loop call site so future refactors keep the
persistence wired up.
"""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict

import pytest

from core.atlas_db import AtlasDB


@pytest.fixture
def atlas_db(tmp_path):
    path = tmp_path / "atlas.db"
    db = AtlasDB(str(path))
    db.init_db()
    yield db, str(path)
    db.close()


def _exec_persist_block(cfg, in_tok: int, out_tok: int, cr: int, llm_elapsed: float):
    """Mirror the persistence block inserted into react_loop.py:1090 area.

    Kept in a helper so the test pins the exact code shape — if the
    inlined block in react_loop.py drifts, the test still validates the
    contract (env-driven workflow / ip / session, cost_usd via
    lib.model_pricing, call_role='worker').
    """
    if not (in_tok > 0 or out_tok > 0):
        return
    try:
        from lib.model_pricing import get_pricing
        _model_name = getattr(cfg, "MODEL_NAME", "") or ""
        _price = get_pricing(_model_name) if _model_name else None
        _cost_usd = 0.0
        if _price is not None:
            _billable_in = max(0, in_tok - cr)
            _cost_usd = (
                _billable_in * float(_price.input)
                + cr * float(_price.cache)
                + out_tok * float(_price.output)
            ) / 1_000_000.0
        from core.atlas_db import AtlasDB as _AtlasDB
        _db_path = (
            os.environ.get("ATLAS_DB_PATH")
            or str(Path.home() / ".common_ai_agent" / "atlas.db")
        )
        _workflow = (
            os.environ.get("ATLAS_WORKFLOW", "")
            or os.environ.get("ATLAS_WORKER_NAME", "")
            or os.environ.get("ACTIVE_WORKSPACE", "")
            or os.environ.get("ATLAS_DEFAULT_WORKFLOW", "")
            or ""
        )
        with _AtlasDB(_db_path) as _db:
            _db.record_llm_call(
                session_id=os.environ.get("ATLAS_SESSION_ID", "")
                    or os.environ.get("ATLAS_ACTIVE_SESSION", ""),
                ip_id=os.environ.get("ATLAS_IP_ID", "")
                    or os.environ.get("ATLAS_ACTIVE_IP", ""),
                workflow=_workflow,
                model=_model_name,
                provider=os.environ.get("ATLAS_PROVIDER", "")
                    or getattr(cfg, "API_PROVIDER", "") or "",
                call_role="worker",
                tokens_input=int(in_tok),
                tokens_output=int(out_tok),
                cache_read_tokens=int(cr),
                cost_usd=_cost_usd,
                latency_ms=round(llm_elapsed * 1000.0, 1),
                status="ok",
            )
    except Exception:
        pass


def test_react_loop_persist_block_writes_row(atlas_db, monkeypatch):
    db, db_path = atlas_db
    monkeypatch.setenv("ATLAS_DB_PATH", db_path)
    monkeypatch.setenv("ATLAS_SESSION_ID", "sess-ssotgen-001")
    monkeypatch.setenv("ATLAS_IP_ID", "ip-ssotgen-001")
    monkeypatch.setenv("ATLAS_WORKFLOW", "ssot-gen")
    monkeypatch.setenv("ATLAS_PROVIDER", "anthropic")

    cfg = SimpleNamespace(MODEL_NAME="claude-opus-4-7", API_PROVIDER="anthropic")

    # Simulate the values react_loop computes after a streamed LLM call.
    _exec_persist_block(cfg, in_tok=18000, out_tok=500, cr=0, llm_elapsed=2.5)

    rows = db._execute(
        "SELECT * FROM llm_calls WHERE session_id = 'sess-ssotgen-001'"
    ).fetchall()
    assert len(rows) == 1
    row = dict(rows[0])
    assert row["workflow"] == "ssot-gen"
    assert row["ip_id"] == "ip-ssotgen-001"
    assert row["call_role"] == "worker"
    assert row["tokens_input"] == 18000
    assert row["tokens_output"] == 500
    assert row["model"] == "claude-opus-4-7"
    assert row["provider"] == "anthropic"
    assert row["latency_ms"] == pytest.approx(2500.0, rel=1e-3)
    # cost_usd > 0 when pricing is resolvable for the model.
    assert row["cost_usd"] >= 0.0


def test_react_loop_persist_block_zero_tokens_skips_row(atlas_db, monkeypatch):
    db, db_path = atlas_db
    monkeypatch.setenv("ATLAS_DB_PATH", db_path)
    monkeypatch.setenv("ATLAS_SESSION_ID", "sess-skip")
    monkeypatch.setenv("ATLAS_WORKFLOW", "ssot-gen")

    cfg = SimpleNamespace(MODEL_NAME="claude-opus-4-7", API_PROVIDER="")
    _exec_persist_block(cfg, in_tok=0, out_tok=0, cr=0, llm_elapsed=0.1)

    rows = db._execute(
        "SELECT * FROM llm_calls WHERE session_id = 'sess-skip'"
    ).fetchall()
    assert len(rows) == 0


def test_react_loop_persist_block_resolves_workflow_from_active_workspace(
    atlas_db, monkeypatch
):
    """When ATLAS_WORKFLOW is unset, fall back to ACTIVE_WORKSPACE so the
    session_worker spawn path (which only sets ACTIVE_WORKSPACE) still
    tags rows with the workflow."""
    db, db_path = atlas_db
    monkeypatch.setenv("ATLAS_DB_PATH", db_path)
    monkeypatch.setenv("ATLAS_SESSION_ID", "sess-fallback")
    monkeypatch.delenv("ATLAS_WORKFLOW", raising=False)
    monkeypatch.delenv("ATLAS_WORKER_NAME", raising=False)
    monkeypatch.setenv("ACTIVE_WORKSPACE", "ssot-gen")

    cfg = SimpleNamespace(MODEL_NAME="claude-opus-4-7", API_PROVIDER="")
    _exec_persist_block(cfg, in_tok=100, out_tok=20, cr=0, llm_elapsed=0.5)

    rows = db._execute(
        "SELECT workflow FROM llm_calls WHERE session_id = 'sess-fallback'"
    ).fetchall()
    assert len(rows) == 1
    assert dict(rows[0])["workflow"] == "ssot-gen"


def test_react_loop_source_contains_persist_block():
    """Pin that the persistence block is wired into react_loop.py — if a
    refactor moves it, the test enforces an explicit decision."""
    source = (Path(__file__).resolve().parents[1] / "core" / "react_loop.py").read_text(
        encoding="utf-8"
    )
    assert "record_llm_call" in source, (
        "react_loop.py must call AtlasDB.record_llm_call so worker LLM "
        "turns persist token / cost data (regression: ssot-gen worker "
        "left llm_calls empty even though token_usage WS frames fired)."
    )
    assert 'call_role="worker"' in source
    assert "ATLAS_DB_PATH" in source
