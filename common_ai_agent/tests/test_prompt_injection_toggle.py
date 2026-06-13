import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_prompt_injection_slash_command_toggles_runtime(monkeypatch):
    import config
    from core.slash_commands import SlashCommandRegistry

    monkeypatch.setenv("ATLAS_PROMPT_INJECTION", "true")
    monkeypatch.setenv("ENABLE_PROMPT_INJECTION", "true")
    monkeypatch.setattr(config, "ENABLE_PROMPT_INJECTION", True, raising=False)
    monkeypatch.setattr(config, "ATLAS_PROMPT_INJECTION", True, raising=False)

    registry = SlashCommandRegistry()
    result = registry.execute("/prompt-injection off")

    assert "disabled" in result
    assert os.environ["ATLAS_PROMPT_INJECTION"] == "false"
    assert os.environ["ENABLE_PROMPT_INJECTION"] == "false"
    assert config.ENABLE_PROMPT_INJECTION is False
    assert config.ATLAS_PROMPT_INJECTION is False

    result = registry.execute("/pinject on")
    assert "enabled" in result
    assert os.environ["ATLAS_PROMPT_INJECTION"] == "true"
    assert config.ENABLE_PROMPT_INJECTION is True


def test_workspace_prompt_patch_respects_prompt_injection_toggle():
    source = (ROOT / "src" / "main.py").read_text(encoding="utf-8")
    assert "prompt_injection_enabled(_cfg)" in source
    assert "return base" in source
    assert "merge_prompt(base, _ws_text, _ws_mode)" in source


def test_live_orchestrator_context_injector_respects_prompt_toggle():
    source = (ROOT / "core" / "orchestrator_inject.py").read_text(encoding="utf-8")
    assert "prompt_injection_enabled(config)" in source
    assert "if not _prompt_injection_enabled():" in source


def test_live_orchestrator_context_injector_noops_when_disabled(monkeypatch):
    import config
    from core.orchestrator_inject import build_orchestrator_inject_fn

    class ExplodingDB:
        def __getattr__(self, name):
            raise AssertionError(f"injector should not touch db while disabled: {name}")

    monkeypatch.setenv("ATLAS_PROMPT_INJECTION", "false")
    monkeypatch.setattr(config, "ENABLE_PROMPT_INJECTION", False, raising=False)
    monkeypatch.setattr(config, "ATLAS_PROMPT_INJECTION", False, raising=False)

    messages = [{"role": "system", "content": "BASE"}]
    inject = build_orchestrator_inject_fn(ExplodingDB(), bridge=None)
    inject(messages, "normal")

    assert messages == [{"role": "system", "content": "BASE"}]
