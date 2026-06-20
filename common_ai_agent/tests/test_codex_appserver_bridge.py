import asyncio
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_app_server_cmd_uses_codex_app_server(monkeypatch):
    import core.codex_appserver_bridge as bridge

    monkeypatch.setattr(bridge, "CODEX_BIN", "codex-test")

    assert bridge._app_server_cmd() == [
        "codex-test",
        "app-server",
        "--listen",
        "stdio://",
    ]


def test_app_server_env_forces_oag_mode_off_by_default(monkeypatch):
    import core.codex_appserver_bridge as bridge

    monkeypatch.setenv("OAG_MODE", "1")
    monkeypatch.delenv("CODEX_BRIDGE_OAG_MODE", raising=False)

    env = bridge._app_server_env()

    assert env["OAG_MODE"] == "0"


def test_app_server_env_honors_explicit_bridge_oag_override(monkeypatch):
    import core.codex_appserver_bridge as bridge

    monkeypatch.setenv("OAG_MODE", "0")
    monkeypatch.setenv("CODEX_BRIDGE_OAG_MODE", "1")

    env = bridge._app_server_env()

    assert env["OAG_MODE"] == "1"


def test_atlas_codex_mode_dispatches_to_app_server_bridge():
    src = (PROJECT_ROOT / "src" / "atlas_ui.py").read_text(encoding="utf-8")

    assert 'if os.environ.get("CODEX_BRIDGE"):' in src
    assert "from core.codex_appserver_bridge import run_codex_turn" in src
    assert 'await _accept_handled("codex")' in src
    assert "run_codex_turn(" in src


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
