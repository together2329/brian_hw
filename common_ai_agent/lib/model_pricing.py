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
    # OpenAI
    "gpt-4o":   Pricing(input=2.50, cache=1.25, output=10.00),
    "gpt-4.1":  Pricing(input=2.00, cache=0.50, output=8.00),
}


def get_pricing(model_name: str) -> Optional[Pricing]:
    """Return Pricing for model_name by longest prefix match, or None if unknown."""
    import os
    name = model_name.lower().split("/")[-1]  # strip provider prefix
    # Custom flat pricing: all GLM models → $1/$0/$1 per 1M when CUSTOM_PRICE=true
    if os.getenv("CUSTOM_PRICE", "false").lower() == "true":
        if name.startswith("glm"):
            return Pricing(input=1.0, cache=0.0, output=1.0)
    best_key = ""
    best = None
    for key, pricing in _TABLE.items():
        if name.startswith(key) and len(key) > len(best_key):
            best_key = key
            best = pricing
    return best
