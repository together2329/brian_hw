"""Phase 3.5+ — orchestrator chat-message persistence.

The orchestrator's React loop yields two kinds of user-facing output:
1. Assistant content (the LLM's natural-language reply).
2. Tool calls (e.g. ``dispatch_workflow`` → "🚀 SSOT 실행 중 ...").

Both must land in ``chat_messages`` so the pipeline chat panel can render
them. These tests drive the loop with a fake LLM that emits content + a
tool call and assert ``db.list_chat_messages`` returns rows in order with
the right roles and rendered text.
"""

from __future__ import annotations

import pytest

from core.atlas_db import AtlasDB
from src.orchestrator import tools as orch_tools
from src.orchestrator.loop import OrchestratorContext
from src.orchestrator.react_bridge import OrchestratorReactLoop
from src.orchestrator.runner import OrchestratorRunner
from src.orchestrator.ui_formatter import format_tool_call


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
        user_id="u1", ip_id="ip1", session_id="s1"
    )
    return OrchestratorContext(
        run_id=run["id"],
        user_id="u1",
        ip_id="ip1",
        ip_name="ipA",
        session_id="s1",
        project_root=tmp_path,
        runner=runner,
    )


def _scripted(*responses):
    iterator = iter(responses)

    def caller(messages, tools):
        try:
            return next(iterator)
        except StopIteration:
            return {"content": "no more"}

    return caller


def _tool_call(name, **args):
    return {"tool_calls": [{"id": "call_x", "name": name, "arguments": args}]}


def _list_room_messages_chronological(db, ip_id):
    """list_chat_messages returns newest-first; reverse for chronological order."""
    return list(reversed(db.list_chat_messages(ip_id, limit=100)))


def _payload_of(row):
    payload = row.get("payload") or {}
    if isinstance(payload, str):
        import json
        payload = json.loads(payload)
    return payload


class TestAssistantContentPersists:
    def test_text_only_turn_writes_one_assistant_row(self, db, ctx):
        caller = _scripted({"content": "all good"})
        OrchestratorReactLoop(db, ctx, llm_caller=caller).run(max_steps=3)

        rows = _list_room_messages_chronological(db, ctx.ip_id)
        assistant_rows = [r for r in rows if _payload_of(r).get("role") == "assistant"]
        assert len(assistant_rows) == 1
        assert _payload_of(assistant_rows[0])["content"] == "all good"

    def test_empty_content_does_not_write_a_row(self, db, ctx, monkeypatch):
        monkeypatch.setattr(
            orch_tools, "_read_pipeline_state_bridge",
            lambda: lambda **kw: {"ok": True, "passed": ["ssot"], "failed": []},
        )
        # Tool-only turn (no content) followed by text turn that completes.
        caller = _scripted(
            _tool_call("read_pipeline_state", ip="ipA"),
            {"content": "done"},
        )
        OrchestratorReactLoop(db, ctx, llm_caller=caller).run(max_steps=5)

        rows = _list_room_messages_chronological(db, ctx.ip_id)
        assistant_rows = [r for r in rows if _payload_of(r).get("role") == "assistant"]
        # Only "done" — the tool-only turn produces no assistant chat row.
        assert [_payload_of(r)["content"] for r in assistant_rows] == ["done"]


class TestToolCallLabelsPersist:
    def test_dispatch_workflow_renders_label_row(self, db, ctx, monkeypatch):
        # Stub dispatch_workflow so the LLM-driven tool call doesn't really
        # spawn a worker — we only care that the label was persisted.
        monkeypatch.setattr(
            orch_tools, "_dispatch_workflow_bridge",
            lambda: lambda **kw: ({"ok": True, "dispatched": True}, "stub"),
            raising=False,
        )
        caller = _scripted(
            _tool_call("dispatch_workflow", workflow="ssot-gen", ip="pl330", model="glm-5.1"),
            {"content": "kicked off"},
        )
        OrchestratorReactLoop(db, ctx, llm_caller=caller).run(max_steps=5)

        rows = _list_room_messages_chronological(db, ctx.ip_id)
        tool_rows = [r for r in rows if _payload_of(r).get("role") == "tool"]
        assert len(tool_rows) >= 1
        rendered = _payload_of(tool_rows[0])["content"]
        # The formatter mentions the workflow, ip, and model.
        assert "ssot-gen" in rendered
        assert "pl330" in rendered
        assert "glm-5.1" in rendered

    def test_unknown_tool_falls_back_to_name_with_args(self):
        # Direct formatter test — pure helper, no DB.
        line = format_tool_call("some_new_tool", {"foo": "bar"})
        assert line.startswith("some_new_tool(")
        assert "foo=bar" in line


class TestOrderAndRoles:
    def test_tool_call_then_assistant_completion(self, db, ctx, monkeypatch):
        """The natural orchestrator flow: emit a tool call to dispatch work,
        then on the next LLM turn produce a natural-language reply that
        finalizes the run. Both must appear in chat_messages in order."""
        monkeypatch.setattr(
            orch_tools, "_dispatch_workflow_bridge",
            lambda: lambda **kw: ({"ok": True, "dispatched": True}, "stub"),
            raising=False,
        )

        caller = _scripted(
            _tool_call("dispatch_workflow", workflow="ssot-gen", ip="pl330", model="glm-5.1"),
            {"content": "ssot 작업을 시작했어요"},
        )
        OrchestratorReactLoop(db, ctx, llm_caller=caller).run(max_steps=5)

        rows = _list_room_messages_chronological(db, ctx.ip_id)
        observable = [r for r in rows
                      if _payload_of(r).get("role") in {"assistant", "tool"}]
        roles_seq = [_payload_of(r).get("role") for r in observable]
        # Expect: tool("dispatch..."), assistant("ssot 작업을 시작했어요")
        assert roles_seq == ["tool", "assistant"]

        texts = [_payload_of(r)["content"] for r in observable]
        assert "ssot-gen" in texts[0]
        assert "pl330" in texts[0]
        assert texts[1] == "ssot 작업을 시작했어요"
