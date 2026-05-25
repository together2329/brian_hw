"""Production llm_call_fn streaming + llm_calls accounting.

Two gaps the bridge's prior ``_llm_call`` had:

1. ``react_loop`` expects a streaming generator
   (``llm_call_fn(messages, stop=None) -> generator``), but the prior
   implementation returned a plain string from ``call_llm_raw``. All bridge
   tests passed only because they supplied ``llm_caller=...`` to the loop
   constructor, which routes through ``_translate_caller_to_stream`` and
   bypasses ``_llm_call`` entirely. Real production traffic was broken.

2. ``llm_calls`` rows linked to ``orchestrator_run_id`` were never written
   — the wiki listed this as the remaining e2e accounting item.

These tests drive the production path (``_llm_caller is None``) with a
monkeypatched ``chat_completion_stream`` and assert:

- ``deps.llm_call_fn`` returns an iterator (generator), not a string.
- After the stream exhausts, exactly one ``llm_calls`` row exists with
  ``run_id == orchestrator_run_id`` and the token counts that the
  ``llm_client`` globals exposed.
"""

from __future__ import annotations

import pytest

from core.atlas_db import AtlasDB
from src.orchestrator.loop import OrchestratorContext
from src.orchestrator.react_bridge import (
    build_orchestrator_deps,
    register_live_event_emitter,
)
from src.orchestrator.runner import OrchestratorRunner


@pytest.fixture
def db(tmp_path):
    atlas = AtlasDB(str(tmp_path / "atlas.db"))
    atlas.init_db()
    yield atlas
    atlas.close()


@pytest.fixture
def runner(db):
    r = OrchestratorRunner(db, max_workers=1)
    yield r
    r.shutdown(wait=True)


@pytest.fixture
def ctx(db, runner, tmp_path):
    run = db.create_orchestrator_run(
        user_id="u1", ip_id="ip1", workspace_id="ws1", session_id="s1"
    )
    return OrchestratorContext(
        run_id=run["id"],
        user_id="u1",
        ip_id="ip1",
        ip_name="ipA",
        workspace_id="ws1",
        session_id="s1",
        project_root=tmp_path,
        runner=runner,
    )


class TestProductionLlmCall:
    def test_llm_call_fn_returns_a_generator(self, db, ctx, monkeypatch):
        """``react_loop`` iterates ``llm_call_fn(...)`` as a stream. The bridge's
        production ``_llm_call`` must therefore return an iterator, not a string.
        Without this, the streaming protocol breaks the moment a real LLM is wired.
        """
        emitted = []

        def fake_stream(messages, stop=None, model=None, tools=None, **_):
            # Mirror chat_completion_stream's globals contract.
            import src.llm_client as _llm
            _llm.last_input_tokens = 11
            _llm.last_output_tokens = 22
            _llm.last_cache_creation_tokens = 0
            _llm.last_cache_read_tokens = 0
            for chunk in ("hello ", "world", "\n"):
                emitted.append(chunk)
                yield chunk

        import src.llm_client as _llm
        monkeypatch.setattr(_llm, "chat_completion_stream", fake_stream)

        bridge = build_orchestrator_deps(ctx=ctx, runner=ctx.runner, db=db)
        stream = bridge.deps.llm_call_fn(
            messages=[{"role": "user", "content": "ping"}], stop=None,
        )
        # Must be an iterator — not a string.
        assert hasattr(stream, "__iter__") and not isinstance(stream, str)
        out = list(stream)
        assert out == ["hello ", "world", "\n"]

    def test_records_one_llm_call_row_with_orchestrator_run_id(
        self, db, ctx, monkeypatch
    ):
        """After the streaming generator exhausts, exactly one ``llm_calls``
        row exists with ``run_id`` equal to ``ctx.run_id`` so the UI/audit
        trail can correlate LLM spend back to the orchestrator run that
        caused it. Token counts come from ``llm_client`` module globals,
        the same convention production main.py reads.
        """

        def fake_stream(messages, stop=None, model=None, tools=None, **_):
            import src.llm_client as _llm
            _llm.last_input_tokens = 333
            _llm.last_output_tokens = 77
            _llm.last_cache_creation_tokens = 4
            _llm.last_cache_read_tokens = 5
            yield "ok"

        import src.llm_client as _llm
        monkeypatch.setattr(_llm, "chat_completion_stream", fake_stream)

        bridge = build_orchestrator_deps(ctx=ctx, runner=ctx.runner, db=db)
        # Drive the stream so the after-stream record fires.
        list(bridge.deps.llm_call_fn(
            messages=[{"role": "user", "content": "ping"}], stop=None,
        ))

        rows = db._fetchall(
            "SELECT run_id, tokens_input, tokens_output, cache_read_tokens, "
            "cache_write_tokens, workspace_id, ip_id, session_id "
            "FROM llm_calls WHERE run_id = ?",
            (ctx.run_id,),
        )
        assert len(rows) == 1
        row = dict(rows[0])
        assert row["tokens_input"] == 333
        assert row["tokens_output"] == 77
        assert row["cache_read_tokens"] == 5
        assert row["cache_write_tokens"] == 4
        assert row["workspace_id"] == "ws1"
        assert row["ip_id"] == "ip1"
        assert row["session_id"] == "s1"

    def test_streams_assistant_deltas_without_live_duplicate(
        self, db, ctx, monkeypatch
    ):
        """Assistant content should reach the browser during generation.

        The final assistant row is still written to DB for reconnect replay,
        but it must not emit a second live assistant bubble after deltas have
        already streamed.
        """

        def fake_stream(messages, stop=None, model=None, tools=None, **_):
            import src.llm_client as _llm
            _llm.last_input_tokens = 1
            _llm.last_output_tokens = 2
            _llm.last_cache_creation_tokens = 0
            _llm.last_cache_read_tokens = 0
            yield "hello "
            yield "world"

        events = []

        def emit(session_id, event):
            events.append((session_id, event))

        import src.llm_client as _llm
        monkeypatch.setattr(_llm, "chat_completion_stream", fake_stream)
        register_live_event_emitter(emit)
        try:
            bridge = build_orchestrator_deps(ctx=ctx, runner=ctx.runner, db=db)
            assert list(bridge.deps.llm_call_fn(
                messages=[{"role": "user", "content": "ping"}], stop=None,
            )) == ["hello ", "world"]
        finally:
            register_live_event_emitter(None)

        payloads = [event["payload"] for _sid, event in events]
        roles = [p["role"] for p in payloads]
        assert roles == ["assistant_delta", "assistant_delta"]
        assert "".join(p["content"] for p in payloads) == "hello world"

        messages = list(reversed(db.list_chat_messages(ctx.ip_id, limit=10)))
        assert [(m["payload"]["role"], m["payload"]["content"]) for m in messages] == [
            ("assistant", "hello world")
        ]
