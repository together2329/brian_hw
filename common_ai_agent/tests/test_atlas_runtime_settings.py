import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))


def _clear_runtime_env(monkeypatch):
    prefixes = ("LLM_", "MODEL_NAME", "PDK", "SKY130_", "PROFILE_", "CURSOR_AGENT_", "CLAUDE_CLI_")
    for key in list(os.environ):
        if key.startswith(prefixes):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv("USE_OPENCODE_OAUTH", raising=False)


def test_reasoning_effort_endpoint_persists_config(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setattr(atlas_ui, "SOURCE_ROOT", tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    (tmp_path / ".config").write_text(
        "REASONING_MODE=xhigh\nREASONING_EFFORT=xhigh\n",
        encoding="utf-8",
    )

    client = TestClient(atlas_ui.create_app())
    login = client.post("/api/auth/register", json={"username": "u", "password": "pw"})
    assert login.status_code == 200, login.text
    response = client.post("/api/settings/reasoning-effort", json={"effort": "med"})

    assert response.status_code == 200, response.text
    assert response.json()["reasoning_effort"] == "medium"
    assert os.environ["REASONING_MODE"] == "medium"
    assert os.environ["REASONING_EFFORT"] == "medium"
    assert os.environ["GLM_THINKING_TYPE"] == "enabled"
    saved = (tmp_path / ".config").read_text(encoding="utf-8")
    assert "REASONING_MODE=medium" in saved
    assert "REASONING_EFFORT=medium" in saved
    assert "GLM_THINKING_TYPE=enabled" in saved


def test_model_endpoint_uses_non_empty_dropdown_slots(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui
    import src.config as config

    _clear_runtime_env(monkeypatch)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setattr(atlas_ui, "SOURCE_ROOT", tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join([
            "LLM_BASE_NAME=model-a",
            "LLM_BASE_NAME_2=model-b",
            "LLM_BASE_NAME_3=",
            "LLM_SELECTED_MODEL_KEY=LLM_BASE_NAME",
            "LLM_MODEL_NAME=model-a",
            "",
        ]),
        encoding="utf-8",
    )
    monkeypatch.setattr(config, "_env_search_paths", lambda: [env_path])
    config._ENV_MTIME_CACHE.clear()
    config.reload_env()

    client = TestClient(atlas_ui.create_app())
    login = client.post("/api/auth/register", json={"username": "u", "password": "pw"})
    assert login.status_code == 200, login.text

    health = client.get("/healthz")
    assert health.status_code == 200, health.text
    option_keys = [row["key"] for row in health.json()["model_options"]]
    assert option_keys == ["LLM_BASE_NAME", "LLM_BASE_NAME_2"]
    assert "label" not in health.json()["model_options"][0]

    response = client.post("/api/settings/model", json={"key": "LLM_BASE_NAME_2"})
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["model"] == "model-b"
    assert payload["selected_model_key"] == "LLM_BASE_NAME_2"
    assert os.environ["LLM_MODEL_NAME"] == "model-b"
    assert os.environ["MODEL_NAME"] == "model-b"
    assert os.environ["LLM_ACTIVE_BASE_NAME"] == "model-b"

    saved = env_path.read_text(encoding="utf-8")
    assert "LLM_BASE_NAME=model-a" in saved
    assert "LLM_BASE_NAME_2=model-b" in saved
    assert "LLM_SELECTED_MODEL_KEY=LLM_BASE_NAME_2" in saved
    assert "LLM_ACTIVE_BASE_NAME=model-b" in saved


def test_model_endpoint_uses_portable_catalog_profiles(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui
    import src.config as config

    _clear_runtime_env(monkeypatch)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setattr(atlas_ui, "SOURCE_ROOT", tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join([
            "USE_OPENCODE_OAUTH=false",
            "LLM_MODEL_NAME=glm-5.1",
            "LLM_BASE_URL=https://glm.example/v1",
            "LLM_API_KEY=glm-key",
            "PROFILE_kimi_BASE_URL=https://kimi.example/v1",
            "PROFILE_kimi_API_KEY=kimi-key",
            "PROFILE_kimi_MODEL=kimi-2.6",
            "PROFILE_deepseek_BASE_URL=https://deepseek.example/v1",
            "PROFILE_deepseek_API_KEY=deepseek-key",
            "PROFILE_deepseek_MODEL=deepseek-v4-pro",
            "LLM_MODEL_CATALOG=gpt-5.5,gpt-5.4,gpt-5.3-codex,kimi=profile:kimi,deepseek=profile:deepseek,glm-5.1,cursor=cursor-cli,claude=claude-cli:sonnet",
            "LLM_SELECTED_MODEL_KEY=model:glm-5.1",
            "",
        ]),
        encoding="utf-8",
    )
    monkeypatch.setattr(config, "_env_search_paths", lambda: [env_path])
    config._ENV_MTIME_CACHE.clear()
    config.reload_env()

    client = TestClient(atlas_ui.create_app())
    login = client.post("/api/auth/register", json={"username": "u", "password": "pw"})
    assert login.status_code == 200, login.text

    health = client.get("/healthz")
    assert health.status_code == 200, health.text
    options = health.json()["model_options"]
    option_keys = [row["key"] for row in options]
    assert option_keys[:8] == [
        "model:gpt-5.5",
        "model:gpt-5.4",
        "model:gpt-5.3-codex",
        "profile:kimi",
        "profile:deepseek",
        "model:glm-5.1",
        "model:cursor-cli",
        "model:claude-cli:sonnet",
    ]
    kimi = next(row for row in options if row["key"] == "profile:kimi")
    assert kimi["model"] == "kimi-2.6"
    assert kimi["label"] == "kimi"

    response = client.post("/api/settings/model", json={"key": "profile:kimi"})
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["model"] == "kimi-2.6"
    assert payload["selected_model_key"] == "profile:kimi"
    assert os.environ["LLM_PROFILE"] == "kimi"
    assert os.environ["LLM_MODEL_NAME"] == "kimi-2.6"
    assert os.environ["MODEL_NAME"] == "kimi-2.6"
    assert os.environ["LLM_BASE_URL"] == "https://kimi.example/v1"

    saved = env_path.read_text(encoding="utf-8")
    assert "LLM_SELECTED_MODEL_KEY=profile:kimi" in saved
    assert "LLM_PROFILE=kimi" in saved
    assert "LLM_ACTIVE_BASE_NAME=kimi-2.6" in saved
    assert "profile:kimi=kimi-2.6" not in saved

    response = client.post("/api/settings/model", json={"key": "model:claude-cli:sonnet"})
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["model"] == "claude-cli"
    assert os.environ["CLAUDE_CLI_ENABLE"] == "true"
    assert os.environ["CLAUDE_CLI_MODEL"] == "sonnet"
    assert os.environ["CURSOR_AGENT_ENABLE"] == "false"

    response = client.post("/api/settings/model", json={"key": "model:cursor-cli"})
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["model"] == "cursor-cli"
    assert os.environ["CURSOR_AGENT_ENABLE"] == "true"
    assert os.environ["CURSOR_AGENT_MODEL"] == "auto"
    assert os.environ["CLAUDE_CLI_ENABLE"] == "false"


def test_healthz_keeps_cli_model_override_over_stale_dropdown(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui
    import src.config as config

    _clear_runtime_env(monkeypatch)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("LLM_MODEL_NAME", "gpt-5.3-codex")
    monkeypatch.setenv("MODEL_NAME", "gpt-5.3-codex")
    monkeypatch.setenv("LLM_BASE_URL", "https://chatgpt.com/backend-api/codex")
    monkeypatch.setenv("LLM_RUNTIME_MODEL_OVERRIDE", "1")
    monkeypatch.setattr(atlas_ui, "SOURCE_ROOT", tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join([
            "LLM_BASE_NAME=glm-5.1",
            "LLM_MODEL_NAME=glm-5.1",
            "LLM_SELECTED_MODEL_KEY=LLM_BASE_NAME",
            "",
        ]),
        encoding="utf-8",
    )
    monkeypatch.setattr(config, "_env_search_paths", lambda: [env_path])
    config._ENV_MTIME_CACHE.clear()
    config._refresh_runtime_globals()

    client = TestClient(atlas_ui.create_app())
    response = client.get("/healthz")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["model"] == "gpt-5.3-codex"
    assert payload["base_model"] == "gpt-5.3-codex"
    assert os.environ["LLM_MODEL_NAME"] == "gpt-5.3-codex"


def test_config_resolves_pdk_paths_from_source_root(monkeypatch):
    import src.config as config

    _clear_runtime_env(monkeypatch)
    monkeypatch.setenv("PDK_ROOT", "pdk")
    config._resolve_pdk_env_defaults()

    pdk_root = Path(os.environ["PDK_ROOT"])
    assert pdk_root == PROJECT_ROOT / "pdk"
    assert Path(os.environ["PDK_LIB_PATH"]) == PROJECT_ROOT / "pdk" / "sky130" / "lib"
    assert Path(os.environ["SKY130_LIB"]).is_file()
    assert Path(os.environ["SKY130_TLEF"]).is_file()
    assert Path(os.environ["SKY130_LEF"]).is_file()
    assert Path(os.environ["SKY130_TRACKS"]).is_file()
    assert Path(os.environ["SKY130_RCX_RULES"]).is_file()
