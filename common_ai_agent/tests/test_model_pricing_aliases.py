from __future__ import annotations


def test_active_pricing_prefers_explicit_deployment_alias_over_stale_env(monkeypatch):
    from lib.model_pricing import get_active_pricing

    monkeypatch.setenv("LLM_ACTIVE_BASE_NAME", "glm-5.1")

    price = get_active_pricing("soc-sol-gpt-5.4")

    assert price is not None
    assert price.input == 2.50
    assert price.cache == 0.25
    assert price.output == 15.00


def test_active_pricing_resolves_codex_and_sol_soc_aliases(monkeypatch):
    from lib.model_pricing import get_active_pricing

    monkeypatch.delenv("LLM_ACTIVE_BASE_NAME", raising=False)
    monkeypatch.delenv("LLM_BASE_NAME", raising=False)

    codex = get_active_pricing("gpt-5.3-codex")
    sol = get_active_pricing("sol-soc-gpt-5.4")

    assert codex is not None
    assert codex.input == 1.75
    assert codex.output == 14.00
    assert sol is not None
    assert sol.input == 2.50
    assert sol.output == 15.00


def test_active_pricing_uses_base_env_for_opaque_deployment(monkeypatch):
    from lib.model_pricing import get_active_pricing

    monkeypatch.setenv("LLM_ACTIVE_BASE_NAME", "gpt-5.4")

    price = get_active_pricing("soc-router-prod")

    assert price is not None
    assert price.input == 2.50
    assert price.output == 15.00
