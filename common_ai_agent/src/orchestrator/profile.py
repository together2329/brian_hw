"""Runtime profile for the Atlas orchestrator loop.

Defaults to gpt-5.5 + xhigh (deepest reasoning) but both are env-
overridable so an operator can trade quality for latency without a code
change. xhigh makes even a "Hi" take 20-40s; set
ATLAS_ORCHESTRATOR_REASONING_EFFORT=low (or medium) for a snappy chat.
"""
import os

ORCHESTRATOR_MODEL = (
    os.environ.get("ATLAS_ORCHESTRATOR_MODEL", "").strip() or "gpt-5.5"
)
ORCHESTRATOR_REASONING_EFFORT = (
    os.environ.get("ATLAS_ORCHESTRATOR_REASONING_EFFORT", "").strip() or "xhigh"
)


def orchestrator_profile_name() -> str:
    return f"{ORCHESTRATOR_MODEL}-{ORCHESTRATOR_REASONING_EFFORT}"


def orchestrator_env() -> dict[str, str]:
    return {
        "ATLAS_ORCHESTRATOR_MODEL": ORCHESTRATOR_MODEL,
        "ATLAS_ORCHESTRATOR_REASONING_EFFORT": ORCHESTRATOR_REASONING_EFFORT,
    }
