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
    prefixes = ("LLM_", "MODEL_NAME", "PDK", "SKY130_")
    for key in list(os.environ):
        if key.startswith(prefixes):
            monkeypatch.delenv(key, raising=False)


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
    saved = (tmp_path / ".config").read_text(encoding="utf-8")
    assert "REASONING_MODE=medium" in saved
    assert "REASONING_EFFORT=medium" in saved


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
