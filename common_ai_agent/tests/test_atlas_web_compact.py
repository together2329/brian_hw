import json

from fastapi.testclient import TestClient

from src.atlas_ui import _clear_history_file, _compact_history_file, _compact_history_llm


def _register(client: TestClient, username: str) -> None:
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": "pw"},
    )
    assert response.status_code == 200, response.text


def test_web_compact_updates_local_conversation_file(tmp_path):
    history = tmp_path / ".session" / "brian" / "new_axi" / "default" / "conversation.json"
    messages = [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "first requirement"},
        {"role": "assistant", "content": "first answer"},
        {"role": "user", "content": "second requirement"},
        {"role": "assistant", "content": "second answer"},
        {"role": "user", "content": "current question"},
        {"role": "assistant", "content": "current answer"},
    ]
    history.parent.mkdir(parents=True)
    history.write_text(json.dumps(messages), encoding="utf-8")

    message, compacted = _compact_history_file(history, "COMPACT_HISTORY:keep=2")

    saved = json.loads(history.read_text(encoding="utf-8"))
    assert "Compacted local session history" in message
    assert compacted == saved
    assert [m["role"] for m in saved] == ["system", "system", "user", "assistant"]
    assert "first requirement" in saved[1]["content"]
    assert saved[-2]["content"] == "current question"
    assert saved[-1]["content"] == "current answer"


def test_web_compact_preserves_full_history_before_rewriting_conversation(tmp_path):
    history = tmp_path / ".session" / "brian" / "new_axi" / "default" / "conversation.json"
    messages = [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "first requirement"},
        {"role": "assistant", "content": "first answer"},
        {"role": "user", "content": "current question"},
        {"role": "assistant", "content": "current answer"},
    ]
    history.parent.mkdir(parents=True)
    history.write_text(json.dumps(messages), encoding="utf-8")

    _message, compacted = _compact_history_file(history, "COMPACT_HISTORY:keep=2")

    assert json.loads(history.read_text(encoding="utf-8")) == compacted
    assert json.loads(history.with_name("full_conversation.json").read_text(encoding="utf-8")) == messages


def test_web_compact_dry_run_does_not_write(tmp_path):
    history = tmp_path / "conversation.json"
    messages = [
        {"role": "user", "content": "old"},
        {"role": "assistant", "content": "old response"},
        {"role": "user", "content": "middle"},
        {"role": "assistant", "content": "middle response"},
        {"role": "user", "content": "new"},
    ]
    history.write_text(json.dumps(messages), encoding="utf-8")

    message, returned = _compact_history_file(history, "COMPACT_HISTORY:dry_run=true")

    assert message.startswith("Dry run:")
    assert returned == messages
    assert json.loads(history.read_text(encoding="utf-8")) == messages


def test_web_clear_keeps_requested_pairs(tmp_path):
    history = tmp_path / "conversation.json"
    messages = [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "old"},
        {"role": "assistant", "content": "old response"},
        {"role": "user", "content": "new"},
        {"role": "assistant", "content": "new response"},
    ]
    history.write_text(json.dumps(messages), encoding="utf-8")

    message, cleared = _clear_history_file(history, "CLEAR_HISTORY:1")

    assert "kept last 1 message pair" in message
    assert cleared == json.loads(history.read_text(encoding="utf-8"))
    assert cleared == [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "new"},
        {"role": "assistant", "content": "new response"},
    ]


def test_websocket_compact_slash_compacts_active_session_file(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    # No live LLM in the test env: force the deterministic local fallback so this
    # exercises the websocket → local-compaction plumbing without network flakiness.
    def _no_llm(*_a, **_k):
        raise RuntimeError("no-llm-in-test")
    monkeypatch.setattr(atlas_ui, "_compact_history_llm", _no_llm)

    session_id = "alice/ip_alpha/default"
    history = tmp_path / ".session" / "alice" / "ip_alpha" / "default" / "conversation.json"
    original_messages = [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "old"},
        {"role": "assistant", "content": "old response"},
        {"role": "user", "content": "new"},
    ]
    history.parent.mkdir(parents=True)
    history.write_text(json.dumps(original_messages), encoding="utf-8")

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    with client.websocket_connect(f"/ws/agent?session_id={session_id}") as ws:
        assert ws.receive_json()["type"] == "hello"
        ws.send_json({"type": "prompt", "text": "/compact --keep 1", "msg_id": "compact-1"})
        seen = []
        for _ in range(6):
            event = ws.receive_json()
            seen.append(event)
            if event.get("type") == "slash_output":
                break

    outputs = [event.get("text", "") for event in seen if event.get("type") == "slash_output"]
    assert outputs and "Compacted local session history" in outputs[-1]
    context_events = [event for event in seen if event.get("type") == "context"]
    assert context_events
    canonical_history = tmp_path / "alice" / "default" / ".session" / "ip_alpha" / "default" / "conversation.json"
    saved = json.loads(canonical_history.read_text(encoding="utf-8"))
    expected_used, expected_max = atlas_ui._history_context_usage(saved)
    assert context_events[-1]["used"] == expected_used
    assert context_events[-1]["max"] == expected_max
    assert json.loads(canonical_history.with_name("full_conversation.json").read_text(encoding="utf-8")) == original_messages


def test_web_compact_llm_uses_compressor(tmp_path):
    """The LLM path runs compress_history and persists its result. compress_fn is
    injected here so we test the web plumbing without a live LLM."""
    history = tmp_path / "conversation.json"
    messages = [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "old requirement"},
        {"role": "assistant", "content": "old answer"},
        {"role": "user", "content": "recent"},
        {"role": "assistant", "content": "recent answer"},
    ]
    history.write_text(json.dumps(messages), encoding="utf-8")

    captured = {}

    def fake_compress(msgs, **kwargs):
        captured.update(kwargs)
        return [
            {"role": "system", "content": "system prompt"},
            {"role": "system", "content": "[AI summary of 3 older messages]"},
            {"role": "user", "content": "recent"},
            {"role": "assistant", "content": "recent answer"},
        ]

    message, compacted = _compact_history_llm(
        history, "COMPACT_HISTORY:keep=2", compress_fn=fake_compress
    )

    saved = json.loads(history.read_text(encoding="utf-8"))
    assert "AI summary" in message
    assert compacted == saved
    assert captured["force"] is True and captured["keep_recent"] == 2 and captured["dry_run"] is False
    assert "[AI summary of 3 older messages]" in saved[1]["content"]
    assert saved[-1]["content"] == "recent answer"


def test_web_compact_llm_preserves_full_history_before_rewriting_conversation(tmp_path):
    history = tmp_path / "conversation.json"
    messages = [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "old requirement"},
        {"role": "assistant", "content": "old answer"},
        {"role": "user", "content": "recent"},
    ]
    history.write_text(json.dumps(messages), encoding="utf-8")

    def fake_compress(_msgs, **_kwargs):
        return [
            {"role": "system", "content": "system prompt"},
            {"role": "system", "content": "[AI summary]"},
            {"role": "user", "content": "recent"},
        ]

    _message, compacted = _compact_history_llm(
        history, "COMPACT_HISTORY:keep=1", compress_fn=fake_compress
    )

    assert json.loads(history.read_text(encoding="utf-8")) == compacted
    assert json.loads(history.with_name("full_conversation.json").read_text(encoding="utf-8")) == messages


def test_web_compact_llm_returns_emitted_textual_output(tmp_path):
    history = tmp_path / "conversation.json"
    history.write_text(
        json.dumps([
            {"role": "system", "content": "system prompt"},
            {"role": "user", "content": "old"},
            {"role": "assistant", "content": "old answer"},
            {"role": "user", "content": "recent"},
        ]),
        encoding="utf-8",
    )

    textual_output = "## Compression Summary\n\n- preserved exactly\n\n---\n\n## Stats\n\n- Messages: 4 -> 3\n"

    def fake_compress(msgs, **kwargs):
        kwargs["emit_fn"](textual_output)
        return [
            {"role": "system", "content": "system prompt\nsummary"},
            {"role": "assistant", "content": "old answer"},
            {"role": "user", "content": "recent"},
        ]

    message, _compacted = _compact_history_llm(
        history, "COMPACT_HISTORY:keep=1", compress_fn=fake_compress
    )

    assert message == textual_output.rstrip()


def test_web_compact_llm_dry_run_does_not_write(tmp_path):
    history = tmp_path / "conversation.json"
    messages = [
        {"role": "user", "content": "a"},
        {"role": "assistant", "content": "b"},
        {"role": "user", "content": "c"},
    ]
    history.write_text(json.dumps(messages), encoding="utf-8")

    def fake_compress(msgs, **kwargs):
        return [{"role": "system", "content": "summary"}, {"role": "user", "content": "c"}]

    message, compacted = _compact_history_llm(
        history, "COMPACT_HISTORY:dry_run=true", compress_fn=fake_compress
    )

    assert "Dry run" in message
    # dry-run must NOT write
    assert json.loads(history.read_text(encoding="utf-8")) == messages
