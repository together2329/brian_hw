"""Fixed runtime profile for the Atlas orchestrator loop."""

ORCHESTRATOR_MODEL = "gpt-5.5"
ORCHESTRATOR_REASONING_EFFORT = "xhigh"


def orchestrator_profile_name() -> str:
    return f"{ORCHESTRATOR_MODEL}-{ORCHESTRATOR_REASONING_EFFORT}"


def orchestrator_env() -> dict[str, str]:
    return {
        "ATLAS_ORCHESTRATOR_MODEL": ORCHESTRATOR_MODEL,
        "ATLAS_ORCHESTRATOR_REASONING_EFFORT": ORCHESTRATOR_REASONING_EFFORT,
    }
