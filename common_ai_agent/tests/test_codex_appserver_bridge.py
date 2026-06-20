import asyncio
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_app_server_cmd_uses_codex_app_server(monkeypatch):
    import core.codex_appserver_bridge as bridge

    monkeypatch.setattr(bridge, "CODEX_BIN", "codex-test")
    monkeypatch.delenv("CODEX_BRIDGE_ENABLE_HOOKS", raising=False)
    monkeypatch.delenv("CODEX_BRIDGE_BYPASS_HOOK_TRUST", raising=False)

    assert bridge._app_server_cmd() == [
        "codex-test",
        "app-server",
        "--listen",
        "stdio://",
    ]


def test_app_server_cmd_can_enable_codex_hooks(monkeypatch):
    import core.codex_appserver_bridge as bridge

    monkeypatch.setattr(bridge, "CODEX_BIN", "codex-test")
    monkeypatch.setenv("CODEX_BRIDGE_ENABLE_HOOKS", "1")
    monkeypatch.delenv("CODEX_BRIDGE_BYPASS_HOOK_TRUST", raising=False)

    assert bridge._app_server_cmd() == [
        "codex-test",
        "app-server",
        "--enable",
        "hooks",
        "--enable",
        "plugin_hooks",
        "--enable",
        "plugins",
        "--listen",
        "stdio://",
    ]


def test_app_server_cmd_can_bypass_hook_trust_for_automation(monkeypatch):
    import core.codex_appserver_bridge as bridge

    monkeypatch.setattr(bridge, "CODEX_BIN", "codex-test")
    monkeypatch.setenv("CODEX_BRIDGE_ENABLE_HOOKS", "1")
    monkeypatch.setenv("CODEX_BRIDGE_BYPASS_HOOK_TRUST", "1")

    assert bridge._app_server_cmd() == [
        "codex-test",
        "--dangerously-bypass-hook-trust",
        "app-server",
        "--enable",
        "hooks",
        "--enable",
        "plugin_hooks",
        "--enable",
        "plugins",
        "--listen",
        "stdio://",
    ]


def test_app_server_cmd_trusts_thread_cwd(monkeypatch, tmp_path):
    import core.codex_appserver_bridge as bridge

    monkeypatch.setattr(bridge, "CODEX_BIN", "codex-test")
    monkeypatch.delenv("CODEX_BRIDGE_ENABLE_HOOKS", raising=False)
    monkeypatch.delenv("CODEX_BRIDGE_BYPASS_HOOK_TRUST", raising=False)

    assert bridge._app_server_cmd(str(tmp_path)) == [
        "codex-test",
        "app-server",
        "-c",
        f'projects."{tmp_path}".trust_level="trusted"',
        "--listen",
        "stdio://",
    ]


def test_app_server_env_forces_oag_mode_off_by_default(monkeypatch):
    import core.codex_appserver_bridge as bridge

    monkeypatch.setenv("OAG_MODE", "1")
    monkeypatch.delenv("CODEX_BRIDGE_OAG_MODE", raising=False)
    monkeypatch.delenv("CODEX_BRIDGE_HOME", raising=False)
    monkeypatch.delenv("CODEX_BRIDGE_RUNTIME_HOME", raising=False)
    monkeypatch.delenv("CODEX_HOME", raising=False)
    monkeypatch.delenv("CODEX_BRIDGE_OAG_ROOT", raising=False)
    monkeypatch.delenv("OAG_ROOT", raising=False)

    env = bridge._app_server_env()

    assert env["OAG_MODE"] == "0"


def test_app_server_env_honors_explicit_bridge_oag_override(monkeypatch):
    import core.codex_appserver_bridge as bridge

    monkeypatch.setenv("OAG_MODE", "0")
    monkeypatch.setenv("CODEX_BRIDGE_OAG_MODE", "1")

    env = bridge._app_server_env()

    assert env["OAG_MODE"] == "1"


def test_app_server_env_uses_external_oag_pack_without_replacing_codex_home(monkeypatch, tmp_path):
    import core.codex_appserver_bridge as bridge

    pack = tmp_path / "ontology_ip_agent"
    pack_home = pack / ".codex"
    pack_home.mkdir(parents=True)
    (pack_home / "mcp.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("CODEX_BRIDGE_HOME", str(pack_home))
    monkeypatch.setenv("CODEX_BRIDGE_OAG_ROOT", str(pack))
    monkeypatch.setenv("OAG_MODE", "1")
    monkeypatch.delenv("CODEX_BRIDGE_OAG_MODE", raising=False)
    monkeypatch.delenv("CODEX_BRIDGE_RUNTIME_HOME", raising=False)
    monkeypatch.delenv("CODEX_HOME", raising=False)

    env = bridge._app_server_env(str(tmp_path / "ip"))

    assert "CODEX_HOME" not in env
    assert env["OAG_ROOT"] == str(pack)
    assert env["OAG_IP_DIR"] == str(tmp_path / "ip")
    assert env["MCP_CONFIG_PATH"] == str(pack_home / "mcp.json")
    assert env["OAG_ACTOR_SURFACE"] == "codex-appserver"
    assert env["OAG_MODE"] == "0"


def test_app_server_env_can_override_runtime_codex_home(monkeypatch, tmp_path):
    import core.codex_appserver_bridge as bridge

    runtime_home = tmp_path / ".codex-runtime"
    monkeypatch.setenv("CODEX_BRIDGE_RUNTIME_HOME", str(runtime_home))

    env = bridge._app_server_env()

    assert env["CODEX_HOME"] == str(runtime_home)


def test_app_server_env_resolves_bridge_pack_home_relative_to_repo(monkeypatch):
    import core.codex_appserver_bridge as bridge

    monkeypatch.setenv("CODEX_BRIDGE_HOME", "../../ontology_ip_agent/.codex")
    monkeypatch.setenv("CODEX_BRIDGE_OAG_ROOT", "../../ontology_ip_agent")
    monkeypatch.delenv("CODEX_BRIDGE_RUNTIME_HOME", raising=False)
    monkeypatch.delenv("CODEX_HOME", raising=False)
    monkeypatch.delenv("OAG_ROOT", raising=False)

    env = bridge._app_server_env()

    assert "CODEX_HOME" not in env
    assert env["MCP_CONFIG_PATH"] == str(
        (PROJECT_ROOT / "../../ontology_ip_agent/.codex/mcp.json").resolve()
    )
    assert env["OAG_ROOT"] == str((PROJECT_ROOT / "../../ontology_ip_agent").resolve())


def test_stage_dot_codex_copies_runtime_pack(monkeypatch, tmp_path):
    import core.codex_appserver_bridge as bridge

    pack = tmp_path / "ontology_ip_agent" / ".codex"
    (pack / "hooks").mkdir(parents=True)
    (pack / "scripts").mkdir(parents=True)
    (pack / "skills" / "oag-ip-workflow").mkdir(parents=True)
    (pack / "hooks.json").write_text("{}", encoding="utf-8")
    (pack / "hooks" / "probe.py").write_text("print('hook')\n", encoding="utf-8")
    (pack / "scripts" / "probe.py").write_text("print('script')\n", encoding="utf-8")
    (pack / "skills" / "oag-ip-workflow" / "SKILL.md").write_text("skill\n", encoding="utf-8")
    (pack / "assets").mkdir()
    (pack / "assets" / "large.bin").write_text("not copied\n", encoding="utf-8")
    cwd = tmp_path / "workspace" / "ip"
    monkeypatch.setenv("CODEX_BRIDGE_HOME", str(pack))
    monkeypatch.setenv("CODEX_BRIDGE_STAGE_DOT_CODEX", "1")

    bridge._stage_dot_codex(str(cwd))

    staged = cwd / ".codex"
    assert not staged.is_symlink()
    assert (staged / "hooks.json").read_text(encoding="utf-8") == "{}"
    assert (staged / "hooks" / "probe.py").read_text(encoding="utf-8") == "print('hook')\n"
    assert (staged / "skills" / "oag-ip-workflow" / "SKILL.md").read_text(encoding="utf-8") == "skill\n"
    assert not (staged / "assets").exists()
    assert (cwd / "scripts").is_symlink()
    assert (cwd / "scripts" / "probe.py").read_text(encoding="utf-8") == "print('script')\n"
    assert (staged / bridge._STAGED_DOT_CODEX_MARKER).read_text(encoding="utf-8") == str(pack)


def test_stage_dot_codex_does_not_replace_existing(monkeypatch, tmp_path):
    import core.codex_appserver_bridge as bridge

    pack = tmp_path / "ontology_ip_agent" / ".codex"
    pack.mkdir(parents=True)
    (pack / "hooks.json").write_text("{}", encoding="utf-8")
    cwd = tmp_path / "workspace"
    existing = cwd / ".codex"
    existing.mkdir(parents=True)
    (existing / "local.txt").write_text("keep", encoding="utf-8")
    monkeypatch.setenv("CODEX_BRIDGE_HOME", str(pack))
    monkeypatch.setenv("CODEX_BRIDGE_STAGE_DOT_CODEX", "1")

    bridge._stage_dot_codex(str(cwd))

    assert not existing.is_symlink()
    assert (existing / "local.txt").read_text(encoding="utf-8") == "keep"


def test_ensure_thread_cwd_trusted_appends_project_config(monkeypatch, tmp_path):
    import core.codex_appserver_bridge as bridge

    codex_home = tmp_path / "home" / ".codex"
    codex_home.mkdir(parents=True)
    config = codex_home / "config.toml"
    config.write_text('[mcp_servers.test]\ncommand = "true"\n', encoding="utf-8")
    cwd = tmp_path / "workspace" / "ip"
    monkeypatch.setenv("CODEX_BRIDGE_RUNTIME_HOME", str(codex_home))
    monkeypatch.setenv("CODEX_BRIDGE_TRUST_THREAD_CWD", "1")

    bridge._ensure_thread_cwd_trusted(str(cwd))
    bridge._ensure_thread_cwd_trusted(str(cwd))

    text = config.read_text(encoding="utf-8")
    header = f'[projects."{cwd}"]'
    assert text.count(header) == 1
    assert f'{header}\ntrust_level = "trusted"' in text


def test_extract_hook_additional_context_uses_codex_hook_contract():
    import core.codex_appserver_bridge as bridge

    raw = "\n".join(
        [
            '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"ctx one"}}',
            "not json",
            '{"hookSpecificOutput":{"additionalContext":"ctx two"}}',
        ]
    )

    assert bridge._extract_hook_additional_context(raw) == "ctx one\n\nctx two"


def test_run_turn_passes_oag_hook_context(monkeypatch, tmp_path):
    import core.codex_appserver_bridge as bridge

    conn = bridge._CodexConn(cwd=str(tmp_path))
    conn.thread_id = "thread-test"

    async def fake_hook_context(cwd, text):
        assert cwd == str(tmp_path)
        assert text == "review rtl"
        return "OAG injected context"

    async def fake_call(method, params=None, timeout=bridge._CALL_TIMEOUT):
        assert method == "turn/start"
        assert params == {
            "threadId": "thread-test",
            "input": [{"type": "text", "text": "review rtl"}],
            "additionalContext": {
                "oag": {"kind": "application", "value": "OAG injected context"}
            },
        }
        conn._on_note("turn/completed", {})
        return {}

    events = []
    monkeypatch.setattr(bridge, "_oag_user_prompt_context", fake_hook_context)
    monkeypatch.setattr(conn, "_call", fake_call)

    asyncio.run(conn.run_turn("review rtl", lambda typ, **payload: events.append((typ, payload))))

    assert events[-3][0] == "flush"
    assert events[-2] == ("agent_state", {"running": False})
    assert events[-1] == ("done", {})


def test_atlas_codex_mode_dispatches_to_app_server_bridge():
    src = (PROJECT_ROOT / "src" / "atlas_ui.py").read_text(encoding="utf-8")

    assert 'if _truthy_env(os.environ.get("CODEX_BRIDGE")):' in src
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


def test_subagent_lane_events_from_collab_spawn():
    """A collabAgentToolCall spawn_agent item maps to one `spawn` lane event
    keyed by the spawned (receiver) thread id, carrying the task prompt and the
    target agent's running status."""
    import core.codex_appserver_bridge as bridge

    item = {
        "type": "collabAgentToolCall",
        "tool": "spawnAgent",
        "senderThreadId": "main-thread",
        "receiverThreadIds": ["sub-1"],
        "prompt": "implement RTL for timer_ip",
        "agentsStates": {"sub-1": {"status": "running"}},
    }
    evs = bridge._subagent_lane_events(item, True, "main-thread")
    assert len(evs) == 1
    ev = evs[0]
    assert ev["agent_id"] == "sub-1"
    assert ev["parent_id"] == "main-thread"
    assert ev["kind"] == "spawn"
    assert ev["status"] == "running"
    assert "implement RTL for timer_ip" in ev["text"]


def test_subagent_lane_events_from_activity():
    """A subAgentActivity item maps to a lane status event keyed by the agent
    thread id, labelled with the agent path."""
    import core.codex_appserver_bridge as bridge

    item = {
        "type": "subAgentActivity",
        "kind": "started",
        "agentThreadId": "sub-2",
        "agentPath": "oag-rtl-implementation-agent",
    }
    evs = bridge._subagent_lane_events(item, True, "main-thread")
    assert len(evs) == 1
    ev = evs[0]
    assert ev["agent_id"] == "sub-2"
    assert ev["label"] == "oag-rtl-implementation-agent"
    assert ev["kind"] == "status"
    assert ev["status"] == "running"


def test_run_turn_routes_subagent_thread_to_lane_not_main(tmp_path, monkeypatch):
    """A nested subagent thread is surfaced via `subagent` lane events: its
    nickname is captured from thread/started, its streamed reply routes to the
    lane (NOT the main token feed), and its nested turn/completed does NOT end
    the parent turn — only the main thread's turn/completed does."""
    import core.codex_appserver_bridge as bridge

    # py3.9: an earlier asyncio.run() in the suite resets the event-loop policy
    # to None, so _CodexConn()'s asyncio.Lock() (built outside a running loop)
    # would raise "no current event loop". Install a fresh loop first.
    asyncio.set_event_loop(asyncio.new_event_loop())
    conn = bridge._CodexConn(cwd=str(tmp_path))
    conn.thread_id = "main-thread"

    async def fake_call(method, params=None, timeout=bridge._CALL_TIMEOUT):
        assert method == "turn/start"
        # subagent thread announces itself with a human nickname + role
        conn._on_note("thread/started", {"thread": {
            "id": "sub-1", "parentThreadId": "main-thread",
            "agentNickname": "RTL Implementation",
            "agentRole": "oag-rtl-implementation-agent"}})
        # subagent streams its own reply on its own thread id
        conn._on_note("item/agentMessage/delta",
                      {"threadId": "sub-1", "delta": "working on RTL"})
        # subagent's nested turn ends -> must NOT flush the parent turn
        conn._on_note("turn/completed",
                      {"threadId": "sub-1", "turnId": "sub-turn"})
        # main agent emits text + ends its turn
        conn._on_note("item/agentMessage/delta",
                      {"threadId": "main-thread", "delta": "all done"})
        conn._on_note("turn/completed",
                      {"threadId": "main-thread", "turnId": "main-turn"})
        return {"turn": {"id": "main-turn"}}

    async def fake_get_conn(session_id, cwd=None):
        return conn

    events = []

    class Session:
        session_id = "default"

        def emit(self, msg_type, **payload):
            events.append((msg_type, payload))

    monkeypatch.setattr(conn, "_call", fake_call)
    monkeypatch.setattr(bridge, "_get_conn", fake_get_conn)

    asyncio.run(bridge.run_codex_turn(
        Session(), "build timer", cwd=str(tmp_path), conn_key="k"))

    sub = [p for t, p in events if t == "subagent"]
    # nickname captured into the lane label
    assert any(p["agent_id"] == "sub-1" and "RTL Implementation" in p["label"]
               for p in sub)
    # subagent reply routed to its lane as a message
    assert any(p["kind"] == "message" and p["agent_id"] == "sub-1"
               and "working on RTL" in p["text"] for p in sub)
    # main token feed is NOT polluted by subagent text
    main_tokens = "".join(p.get("text", "") for t, p in events if t == "token")
    assert "working on RTL" not in main_tokens
    assert "all done" in main_tokens
    # the turn ended cleanly exactly once (driven by the MAIN thread)
    assert events[-1] == ("done", {})
    assert ("agent_state", {"running": False}) in events


def test_subagent_lane_events_skip_parent_thread():
    """A spawn's `item/started` phase has no child thread id yet, so
    _collab_agent_ids falls back to the sender (= the parent). That must NOT
    produce a lane keyed to main — otherwise it pollutes the synthesized Main
    row in the UI (observed live against codex 0.141.0)."""
    import core.codex_appserver_bridge as bridge

    started_no_child = {
        "type": "collabAgentToolCall",
        "tool": "spawnAgent",
        "senderThreadId": "main-thread",
        "receiverThreadIds": [],   # child thread not assigned yet
        "prompt": "do work",
    }
    assert bridge._subagent_lane_events(started_no_child, True, "main-thread") == []
    # subAgentActivity keyed to the parent thread is likewise not a lane.
    activity_on_main = {
        "type": "subAgentActivity", "kind": "started",
        "agentThreadId": "main-thread", "agentPath": "x",
    }
    assert bridge._subagent_lane_events(activity_on_main, True, "main-thread") == []
