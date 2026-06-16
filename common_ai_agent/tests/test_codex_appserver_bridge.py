import asyncio
import json


def test_tool_only_turn_is_visible_and_persisted(tmp_path, monkeypatch):
    import core.codex_appserver_bridge as bridge

    conn = bridge._CodexConn(cwd=str(tmp_path))
    conn.thread_id = "thread-test"

    async def fake_call(method, params=None, timeout=bridge._CALL_TIMEOUT):
        assert method == "turn/start"
        assert params["threadId"] == "thread-test"
        assert params["input"] == [{"type": "text", "text": "inspect timer"}]
        conn._on_note(
            "item/completed",
            {
                "item": {
                    "type": "mcpToolCall",
                    "tool": "oag",
                    "result": {
                        "schema_version": "oag_tool_response.v1",
                        "ok": True,
                        "tool": "oag.inspect",
                        "result": {"ip": "timer_ip_codex", "validation": "partial"},
                    },
                }
            },
        )
        conn._on_note("turn/completed", {})
        return {}

    async def fake_get_conn(session_id, cwd=None):
        assert session_id == "user/default/timer_ip_codex/default"
        return conn

    events = []

    class Session:
        session_id = "default"

        def emit(self, msg_type, **payload):
            events.append((msg_type, payload))

    monkeypatch.setattr(conn, "_call", fake_call)
    monkeypatch.setattr(bridge, "_get_conn", fake_get_conn)
    transcript = tmp_path / "conversation.json"

    asyncio.run(
        bridge.run_codex_turn(
            Session(),
            "inspect timer",
            cwd=str(tmp_path),
            conn_key="user/default/timer_ip_codex/default",
            transcript_path=str(transcript),
        )
    )

    token_text = "".join(payload.get("text", "") for typ, payload in events if typ == "token")
    assert "Tool result (oag):" in token_text
    assert "oag_tool_response.v1" in token_text
    assert "timer_ip_codex" in token_text
    assert events[-3][0] == "flush"
    assert events[-2] == ("agent_state", {"running": False})
    assert events[-1] == ("done", {})

    rows = json.loads(transcript.read_text(encoding="utf-8"))
    assert rows[-2] == {"role": "user", "content": "inspect timer"}
    assert rows[-1]["role"] == "assistant"
    assert "Tool result (oag):" in rows[-1]["content"]
    assert "oag_tool_response.v1" in rows[-1]["content"]
