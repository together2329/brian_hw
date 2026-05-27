"""ATLAS execution-mode policy.

Keep the mode-derived decisions in one pure module so the UI shell,
pipeline API, worker resolver, and direct dispatch fallback agree on the
same topology.
"""

from __future__ import annotations

import os
from typing import Any, Mapping, MutableMapping, Sequence


EXEC_MODE_SINGLE = "single-worker"
EXEC_MODE_ORCHESTRATOR = "orchestrator"
EXEC_MODES = (EXEC_MODE_SINGLE, EXEC_MODE_ORCHESTRATOR)
SINGLE_WORKER_URL = "http://127.0.0.1:5601"

# Temporary UI lock for the exec-mode picker. While true, app.jsx
# (ATLAS_EXEC_MODE_LOCKED mirrors this) boots single-worker and disables the
# picker so users can't switch to orchestrator. The orchestrator code paths
# stay intact — an explicit ATLAS_ORCHESTRATOR_MODE / ATLAS_EXEC_MODE launch
# still selects it for deployments and tests — this only hides the choice in
# the UI. The fresh-launch default is single-worker regardless (see
# current_exec_mode). Flip both flags to re-expose the picker.
EXEC_MODE_LOCKED = True
LOCKED_EXEC_MODE = EXEC_MODE_SINGLE

_TRUTHY = {"1", "true", "yes", "on"}
_FALSY = {"", "0", "false", "no", "off"}

_EXEC_MODE_ALIASES = {
    "s": EXEC_MODE_SINGLE,
    "sw": EXEC_MODE_SINGLE,
    "main": EXEC_MODE_SINGLE,
    "single": EXEC_MODE_SINGLE,
    "single-worker": EXEC_MODE_SINGLE,
    "single worker": EXEC_MODE_SINGLE,
    "worker": EXEC_MODE_SINGLE,
    "serial": EXEC_MODE_SINGLE,
    "o": EXEC_MODE_ORCHESTRATOR,
    "orch": EXEC_MODE_ORCHESTRATOR,
    "orchestrator": EXEC_MODE_ORCHESTRATOR,
    "orchestrator-mode": EXEC_MODE_ORCHESTRATOR,
    "multi-worker": EXEC_MODE_ORCHESTRATOR,
    "multi worker": EXEC_MODE_ORCHESTRATOR,
}


def truthy_value(value: Any) -> bool:
    return str(value or "").strip().lower() in _TRUTHY


def falsy_value(value: Any) -> bool:
    return str(value or "").strip().lower() in _FALSY


def normalize_exec_mode(value: Any) -> str:
    mode = str(value or "").strip().lower().replace("_", "-")
    return _EXEC_MODE_ALIASES.get(mode, mode if mode in EXEC_MODES else "")


def current_exec_mode(
    env: Mapping[str, str] | None = None,
    *,
    default: str = EXEC_MODE_SINGLE,
) -> str:
    """Resolve the effective execution mode from environment-style values.

    Precedence is explicit orchestrator flag, explicit exec-mode values, then
    the single-main-loop compatibility flag, then the provided default (now
    single-worker). This preserves a posted run-policy value over stale legacy
    flags while still letting old `ATLAS_SINGLE_MAIN_LOOP=1` launches select
    single-worker. A fresh launch with nothing set resolves to single-worker.
    """

    source = os.environ if env is None else env
    if source.get("ATLAS_ORCHESTRATOR_MODE") is not None:
        return (
            EXEC_MODE_ORCHESTRATOR
            if truthy_value(source.get("ATLAS_ORCHESTRATOR_MODE"))
            else EXEC_MODE_SINGLE
        )
    explicit = normalize_exec_mode(source.get("ATLAS_EXEC_MODE"))
    if explicit:
        return explicit
    explicit = normalize_exec_mode(source.get("ATLAS_DEFAULT_EXEC_MODE"))
    if explicit:
        return explicit
    if truthy_value(source.get("ATLAS_SINGLE_MAIN_LOOP")):
        return EXEC_MODE_SINGLE
    return normalize_exec_mode(default) or EXEC_MODE_SINGLE


def initial_workflow_for_exec_mode(exec_mode: Any, explicit: Any = "") -> str:
    requested = str(explicit or "").strip().lower().replace("_", "-")
<<<<<<< Updated upstream
    if requested in {"orchestrator", "default", "ssot-gen"}:
=======
    if requested in {"default", "orchestrator", "ssot-gen"}:
>>>>>>> Stashed changes
        return requested
    return (
        "orchestrator"
        if normalize_exec_mode(exec_mode) == EXEC_MODE_ORCHESTRATOR
        else "default"
    )


def preserve_running_on_workflow_switch(exec_mode: Any) -> bool:
    return normalize_exec_mode(exec_mode) == EXEC_MODE_ORCHESTRATOR


def worker_url_strategy(exec_mode: Any) -> str:
    return (
        "workflow-workers"
        if normalize_exec_mode(exec_mode) == EXEC_MODE_ORCHESTRATOR
        else "single-main-loop"
    )


def allow_orchestrator_namespace(exec_mode: Any) -> bool:
    return normalize_exec_mode(exec_mode) == EXEC_MODE_ORCHESTRATOR


def _unique_truthy(values: Sequence[str]) -> set[str]:
    return {str(v or "").strip().rstrip("/") for v in values if str(v or "").strip()}


def schedule_for_exec_mode(
    exec_mode: Any,
    requested_schedule: Any = "auto",
    worker_urls: Sequence[str] = (),
) -> str:
    requested = str(requested_schedule or "auto").strip().lower()
    if requested in {"dag", "serial"}:
        return requested
    if normalize_exec_mode(exec_mode) == EXEC_MODE_SINGLE:
        return "serial"
    return "dag" if len(_unique_truthy(worker_urls)) > 1 else "serial"


def exec_policy_payload(
    exec_mode: Any = "",
    *,
    env: Mapping[str, str] | None = None,
    worker_urls: Sequence[str] = (),
) -> dict[str, Any]:
    mode = normalize_exec_mode(exec_mode) or current_exec_mode(env)
    return {
        "exec_mode": mode,
        "initial_workflow": initial_workflow_for_exec_mode(mode),
        "dispatch_schedule": schedule_for_exec_mode(mode, "auto", worker_urls),
        "worker_strategy": worker_url_strategy(mode),
        "single_worker_url": SINGLE_WORKER_URL,
        "preserve_running_on_workflow_switch": preserve_running_on_workflow_switch(mode),
        "allow_orchestrator_namespace": allow_orchestrator_namespace(mode),
    }


def apply_exec_mode_env(
    exec_mode: Any,
    env: MutableMapping[str, str] | None = None,
) -> dict[str, str]:
    mode = normalize_exec_mode(exec_mode)
    if not mode:
        raise ValueError("exec_mode must be single-worker or orchestrator")
    target = os.environ if env is None else env
    values = {
        "ATLAS_EXEC_MODE": mode,
        "ATLAS_DEFAULT_EXEC_MODE": mode,
        "ATLAS_ORCHESTRATOR_MODE": "1" if mode == EXEC_MODE_ORCHESTRATOR else "0",
        "ATLAS_SINGLE_MAIN_LOOP": "1" if mode == EXEC_MODE_SINGLE else "0",
    }
    for key, value in values.items():
        target[key] = value
    return values
