from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_session_cache_key_fits_codex_backend_limit(monkeypatch):
    from src.opencode_backend import get_session_cache_key

    raw = (
        "mctp_v7_user_1780494316/mctp_assembler_scratch_v7/"
        "pipeline/08ac2466957a/01-ssot-gen"
    )
    monkeypatch.setenv("ATLAS_SESSION_ID", raw)
    monkeypatch.delenv("OPENCODE_CACHE_KEY", raising=False)
    monkeypatch.delenv("LLM_SESSION_ID", raising=False)

    key = get_session_cache_key()

    assert len(key) <= 64
    assert key != raw


def test_session_cache_key_keeps_long_user_namespaces_distinct(monkeypatch):
    from src.opencode_backend import get_session_cache_key

    first = (
        "mctp_v7_user_1780494316/mctp_assembler_scratch_v7/"
        "pipeline/08ac2466957a/01-ssot-gen"
    )
    second = (
        "mctp_v7_user_1780494316/mctp_assembler_scratch_v7/"
        "pipeline/08ac2466957a/02-fl-model-gen"
    )
    monkeypatch.delenv("OPENCODE_CACHE_KEY", raising=False)
    monkeypatch.delenv("LLM_SESSION_ID", raising=False)

    monkeypatch.setenv("ATLAS_SESSION_ID", first)
    first_key = get_session_cache_key()
    monkeypatch.setenv("ATLAS_SESSION_ID", second)
    second_key = get_session_cache_key()

    assert first_key != second_key
    assert len(first_key) <= 64
    assert len(second_key) <= 64
