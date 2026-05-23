"""Runtime profile for the Atlas orchestrator loop.

Defaults to gpt-5.5 + low reasoning because the orchestrator is a routing
and status layer; workflow workers do the deeper implementation work. Both
values are env-overridable when an operator explicitly wants a slower,
deeper orchestration pass.
"""
import os

ORCHESTRATOR_MODEL = (
    os.environ.get("ATLAS_ORCHESTRATOR_MODEL", "").strip() or "gpt-5.5"
)
ORCHESTRATOR_REASONING_EFFORT = (
    os.environ.get("ATLAS_ORCHESTRATOR_REASONING_EFFORT", "").strip() or "low"
)


def orchestrator_profile_name() -> str:
    return f"{ORCHESTRATOR_MODEL}-{ORCHESTRATOR_REASONING_EFFORT}"


def orchestrator_env() -> dict[str, str]:
    return {
        "ATLAS_ORCHESTRATOR_MODEL": ORCHESTRATOR_MODEL,
        "ATLAS_ORCHESTRATOR_REASONING_EFFORT": ORCHESTRATOR_REASONING_EFFORT,
    }
