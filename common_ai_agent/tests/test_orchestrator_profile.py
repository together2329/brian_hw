import importlib


def test_orchestrator_default_effort_is_low(monkeypatch):
    monkeypatch.delenv("ATLAS_ORCHESTRATOR_REASONING_EFFORT", raising=False)

    import src.orchestrator.profile as profile

    profile = importlib.reload(profile)

    assert profile.ORCHESTRATOR_REASONING_EFFORT == "low"


def test_orchestrator_effort_env_override(monkeypatch):
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_REASONING_EFFORT", "high")

    import src.orchestrator.profile as profile

    profile = importlib.reload(profile)

    assert profile.ORCHESTRATOR_REASONING_EFFORT == "high"
