import importlib
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _reload_config(monkeypatch):
    for key in list(os.environ):
        if key.startswith(("LLM_", "PROFILE_", "MODEL_NAME", "CURSOR_AGENT_", "CLAUDE_CLI_")):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("USE_OPENCODE_OAUTH", "false")
    import config
    return importlib.reload(config)


def test_activate_cursor_cli_backend_sets_runtime_flags(monkeypatch):
    cfg = _reload_config(monkeypatch)

    assert cfg.activate_cli_backend("cursor-cli")

    assert cfg.CURSOR_AGENT_ENABLE is True
    assert cfg.CLAUDE_CLI_ENABLE is False
    assert cfg.CURSOR_AGENT_MODEL == "auto"
    assert cfg.MODEL_NAME == "cursor-cli"
    assert os.environ["CURSOR_AGENT_ENABLE"] == "true"
    assert os.environ["CLAUDE_CLI_ENABLE"] == "false"
    assert os.environ["ENABLE_NATIVE_TOOL_CALLS"] == "false"


def test_activate_claude_cli_backend_accepts_inline_model(monkeypatch):
    cfg = _reload_config(monkeypatch)

    assert cfg.activate_cli_backend("claude-cli:opus")

    assert cfg.CLAUDE_CLI_ENABLE is True
    assert cfg.CURSOR_AGENT_ENABLE is False
    assert cfg.CLAUDE_CLI_MODEL == "opus"
    assert cfg.MODEL_NAME == "claude-cli"
    assert os.environ["CLAUDE_CLI_ENABLE"] == "true"
    assert os.environ["CURSOR_AGENT_ENABLE"] == "false"


def test_llm_client_dispatches_to_claude_cli_backend(monkeypatch):
    _reload_config(monkeypatch)
    import config
    import src.llm_client as llm_client
    import src.claude_cli_backend as claude_backend

    monkeypatch.setattr(config, "CURSOR_AGENT_ENABLE", False)
    monkeypatch.setattr(config, "CLAUDE_CLI_ENABLE", True)
    monkeypatch.setattr(config, "CLAUDE_CLI_MODEL", "sonnet")
    monkeypatch.setattr(config, "CLAUDE_CLI_PERMISSION_MODE", "default")
    monkeypatch.setattr(config, "CLAUDE_CLI_TOOLS", "")
    monkeypatch.setattr(config, "CLAUDE_CLI_WORKSPACE", "")
    monkeypatch.setattr(config, "CLAUDE_CLI_NO_SESSION_PERSISTENCE", True)
    monkeypatch.setattr(config, "CLAUDE_CLI_OUTPUT_FORMAT", "json")
    monkeypatch.setattr(config, "CLAUDE_CLI_TIMEOUT_SEC", 300)

    seen = {}

    def fake_call(**kwargs):
        seen.update(kwargs)
        return "ok-from-claude-cli"

    monkeypatch.setattr(claude_backend, "claude_cli_call", fake_call)

    out = llm_client.call_llm_raw(messages=[{"role": "user", "content": "hi"}])

    assert out == "ok-from-claude-cli"
    assert seen["model"] == "sonnet"
    assert seen["permission_mode"] == "default"
    assert seen["tools"] == ""
    assert seen["output_format"] == "json"
    assert seen["timeout_sec"] == 300


def test_claude_cli_backend_parses_stream_delta_and_usage():
    import src.claude_cli_backend as backend

    class LC:
        last_input_tokens = 0
        last_output_tokens = 0

    chunk = {
        "type": "stream_event",
        "event": {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "OK"}},
    }
    assert backend._handle_chunk(chunk, LC) == "OK"

    usage_chunk = {
        "type": "result",
        "usage": {
            "input_tokens": 2,
            "cache_read_input_tokens": 3,
            "cache_creation_input_tokens": 5,
            "output_tokens": 7,
        },
    }
    assert backend._handle_chunk(usage_chunk, LC) is None
    assert LC.last_input_tokens == 10
    assert LC.last_output_tokens == 7


def test_claude_cli_backend_parses_json_result_usage():
    import src.claude_cli_backend as backend

    class LC:
        last_input_tokens = 0
        last_output_tokens = 0

    result = {
        "type": "result",
        "result": "OK",
        "usage": {
            "input_tokens": 2,
            "cache_read_input_tokens": 11,
            "cache_creation_input_tokens": 13,
            "output_tokens": 5,
        },
        "modelUsage": {"claude-sonnet-4-6": {"costUSD": 0.01}},
    }

    assert backend._handle_result_object(result, LC) == "OK"
    assert LC.last_input_tokens == 26
    assert LC.last_output_tokens == 5
    assert backend.last_claude_model == "claude-sonnet-4-6"
