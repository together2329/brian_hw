"""
lib/model_pricing.py — Per-model token pricing (USD per 1M tokens)

Source: https://docs.z.ai/guides/overview/pricing
Update this file when pricing changes.
"""

from typing import Dict, NamedTuple, Optional


class Pricing(NamedTuple):
    input: float   # USD per 1M input tokens
    cache: float   # USD per 1M cached (read) tokens
    output: float  # USD per 1M output tokens


# Model prefix → pricing
# Matched by longest prefix of the active model name (case-insensitive).
_TABLE: Dict[str, Pricing] = {
    "glm-5.1": Pricing(input=1.40, cache=0.26, output=4.40),
    "glm-5":   Pricing(input=1.00, cache=0.20, output=3.20),
    "glm-4.7": Pricing(input=0.60, cache=0.11, output=2.20),
    "glm-4.6": Pricing(input=0.60, cache=0.11, output=2.20),
    "glm-4.5": Pricing(input=0.60, cache=0.11, output=2.20),
    # Anthropic
    "claude-opus-4":     Pricing(input=15.00, cache=1.50, output=75.00),
    "claude-sonnet-4":   Pricing(input=3.00,  cache=0.30, output=15.00),
    "claude-haiku-4":    Pricing(input=0.80,  cache=0.08, output=4.00),
    "claude-3-5-sonnet": Pricing(input=3.00,  cache=0.30, output=15.00),
    "claude-3-5-haiku":  Pricing(input=0.80,  cache=0.08, output=4.00),
    "claude-3-opus":     Pricing(input=15.00, cache=1.50, output=75.00),
    # OpenAI — short-context tier (≤200K input). Long-context tier (>200K)
    # is roughly 2x for input/cache and 1.5x for output but is not modeled
    # here yet (would need a Pricing schema extension); see comment block
    # below for the published long-context numbers.
    "gpt-5.5-pro":   Pricing(input=30.00, cache=0.00,  output=180.00),
    "gpt-5.5":       Pricing(input=5.00,  cache=0.50,  output=30.00),
    "gpt-5.4-pro":   Pricing(input=30.00, cache=0.00,  output=180.00),
    "gpt-5.4-mini":  Pricing(input=0.75,  cache=0.075, output=4.50),
    "gpt-5.4-nano":  Pricing(input=0.20,  cache=0.02,  output=1.25),
    "gpt-5.4":       Pricing(input=2.50,  cache=0.25,  output=15.00),
    "gpt-5.3-codex": Pricing(input=1.75,  cache=0.875, output=14.00),
    "gpt-5.1":       Pricing(input=1.25,  cache=0.625, output=10.00),
    "gpt-4o":        Pricing(input=2.50,  cache=1.25,  output=10.00),
    "gpt-4.1":       Pricing(input=2.00,  cache=0.50,  output=8.00),
    # OpenAI long-context (>200K input) reference — not yet wired into Pricing schema:
    #   gpt-5.5      input=10.00  cache=1.00  output=45.00
    #   gpt-5.5-pro  input=60.00  cache=0.00  output=270.00
    #   gpt-5.4      input=5.00   cache=0.50  output=22.50
    #   gpt-5.4-pro  input=60.00  cache=0.00  output=270.00
    #   gpt-5.4-mini long-context not offered
    #   gpt-5.4-nano long-context not offered
    # DeepSeek (75% limited-time discount pricing)
    "deepseek-v4-pro":  Pricing(input=0.435, cache=0.03625, output=0.87),
    "deepseek-v4-flash": Pricing(input=0.14, cache=0.028, output=0.28),
}


def get_pricing(model_name: str) -> Optional[Pricing]:
    """Return Pricing for model_name by longest prefix match, or None if unknown.

    LLM_BASE_MODEL env var, when set, overrides the passed-in model_name for
    pricing lookup. Use this when the runtime model alias (e.g. a vendor-
    specific deployment label) doesn't match a key in _TABLE but the
    underlying base model does — set LLM_BASE_MODEL to the base name
    (e.g. "deepseek-v4-pro") so cost figures stay correct on every LLM call.
    """
    import os
    base_override = os.getenv("LLM_BASE_MODEL", "").strip()
    lookup_name = base_override or (model_name or "")
    name = lookup_name.lower().split("/")[-1]  # strip provider prefix
    # Custom flat pricing: all GLM models → $1/$0/$1 per 1M when CUSTOM_PRICE=true
    if os.getenv("CUSTOM_PRICE", "false").lower() == "true":
        if name.startswith("glm"):
            return Pricing(input=1.0, cache=0.0, output=10.0)
    best_key = ""
    best = None
    for key, pricing in _TABLE.items():
        if name.startswith(key) and len(key) > len(best_key):
            best_key = key
            best = pricing
    return best


def get_active_pricing() -> Optional[Pricing]:
    """Resolve current model pricing without callers needing to know the
    name resolution rules. Honors LLM_BASE_MODEL env var first, then falls
    back to config.MODEL_NAME / LLM_MODEL_NAME (set from .env).
    """
    import os
    base = os.getenv("LLM_BASE_MODEL", "").strip()
    if base:
        return get_pricing(base)
    name = os.getenv("LLM_MODEL_NAME", "").strip()
    if not name:
        try:
            import config as _cfg  # type: ignore
            name = getattr(_cfg, "MODEL_NAME", "") or ""
        except Exception:
            name = ""
    return get_pricing(name) if name else None
