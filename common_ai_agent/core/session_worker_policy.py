"""Interactive session-worker policy (single-active-owner vs session-scoped).

A first-class policy object parsed once from the environment so implementers do
not infer behavior from scattered flags. See
``plans/single-active-session-worker-100-users.md`` (Environment Contract +
Wave-3 Residual Contracts).

Environment behavior:

* ``ATLAS_SESSION_WORKER_POLICY`` unset -> ``single-active-owner`` with cap 30.
* ``ATLAS_SESSION_WORKER_POLICY=session-scoped`` explicitly opts out to the
  historical unbounded session-scoped behavior unless a positive
  ``ATLAS_SESSION_WORKER_MAX_ACTIVE`` is also set.
* invalid policy value -> fall back to the strict default and surface
  ``.warning`` for diagnostics.

Capacity cap is enforced ONLY when strict mode is on OR
``ATLAS_SESSION_WORKER_MAX_ACTIVE`` is explicitly set by the operator.
``max_active <= 0`` means unbounded even in strict mode.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping, Optional

POLICY_SESSION_SCOPED = "session-scoped"
POLICY_SINGLE_ACTIVE_OWNER = "single-active-owner"
_VALID_POLICIES = frozenset({POLICY_SESSION_SCOPED, POLICY_SINGLE_ACTIVE_OWNER})

_TRUE = frozenset({"1", "true", "yes", "on"})

# Defaults match the Environment Contract block in the plan.
_DEFAULT_MAX_ACTIVE = 30
_DEFAULT_IDLE_TTL_SEC = 900.0
_DEFAULT_REAPER_INTERVAL_SEC = 15.0
_DEFAULT_STOP_ACK_SEC = 3.0
_DEFAULT_KILL_GRACE_SEC = 5.0


def _as_bool(raw: Any, default: bool) -> bool:
    if raw is None or not str(raw).strip():
        return default
    return str(raw).strip().lower() in _TRUE


def _as_number(raw: Any, default: float) -> float:
    try:
        if raw is None or not str(raw).strip():
            return default
        return float(str(raw).strip())
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class SessionWorkerPolicy:
    """Resolved interactive session-worker policy.

    ``cap_enabled`` is the single source of truth for "is the global admission cap
    active"; ``max_active <= 0`` always means unbounded (cap_enabled is False).
    """

    policy: str = POLICY_SESSION_SCOPED
    single_active_owner: bool = False
    cap_enabled: bool = False
    max_active: int = 0  # 0 / negative => unbounded
    idle_ttl_sec: float = _DEFAULT_IDLE_TTL_SEC
    reaper_interval_sec: float = _DEFAULT_REAPER_INTERVAL_SEC
    stop_ack_sec: float = _DEFAULT_STOP_ACK_SEC
    kill_grace_sec: float = _DEFAULT_KILL_GRACE_SEC
    reaper_enabled: bool = True
    warning: str = ""

    @classmethod
    def from_env(
        cls,
        env: Optional[Mapping[str, str]] = None,
        *,
        single_worker_per_owner: Optional[bool] = None,
    ) -> "SessionWorkerPolicy":
        """Build a policy from ``env`` (defaults to ``os.environ``).

        ``single_worker_per_owner`` is the legacy bridge constructor argument.
        Strict mode is now the default, so the flag is retained only for API
        compatibility. An explicit ``session-scoped`` policy still opts out.
        """
        env = os.environ if env is None else env
        warning = ""

        raw_policy = (env.get("ATLAS_SESSION_WORKER_POLICY") or "").strip().lower()
        if raw_policy == POLICY_SESSION_SCOPED:
            # Explicit opt-OUT of strict mode.
            resolved = POLICY_SESSION_SCOPED
        elif raw_policy == POLICY_SINGLE_ACTIVE_OWNER:
            resolved = POLICY_SINGLE_ACTIVE_OWNER
        elif raw_policy:
            # Invalid value -> fall back to the DEFAULT (strict) with a warning.
            warning = (
                f"invalid ATLAS_SESSION_WORKER_POLICY={raw_policy!r}; "
                f"using default {POLICY_SINGLE_ACTIVE_OWNER}"
            )
            resolved = POLICY_SINGLE_ACTIVE_OWNER
        else:
            # DEFAULT IS STRICT single-active-owner (changed 2026-06-03 by request:
            # "기본값도 strict"). Opt OUT with ATLAS_SESSION_WORKER_POLICY=
            # session-scoped. The legacy ATLAS_SINGLE_WORKER_PER_OWNER/_USER flags
            # and the single_worker_per_owner kwarg only ever selected strict, which
            # is now the default, so they are no-ops here (kept for API compat).
            _ = single_worker_per_owner  # legacy no-op (strict is default)
            resolved = POLICY_SINGLE_ACTIVE_OWNER

        single_active = resolved == POLICY_SINGLE_ACTIVE_OWNER

        raw_max = env.get("ATLAS_SESSION_WORKER_MAX_ACTIVE")
        max_explicit = raw_max is not None and str(raw_max).strip() != ""
        if single_active and not max_explicit:
            max_active = _DEFAULT_MAX_ACTIVE
        else:
            max_active = int(_as_number(raw_max, 0))

        # Cap is enforced in strict mode (default 30) OR when the operator set an
        # explicit positive MAX_ACTIVE in session-scoped mode. <=0 => unbounded.
        if single_active:
            cap_enabled = max_active > 0
        else:
            cap_enabled = bool(max_explicit and max_active > 0)

        return cls(
            policy=resolved,
            single_active_owner=single_active,
            cap_enabled=cap_enabled,
            max_active=max_active,
            idle_ttl_sec=_as_number(
                env.get("ATLAS_SESSION_WORKER_IDLE_TTL_SEC"), _DEFAULT_IDLE_TTL_SEC
            ),
            reaper_interval_sec=_as_number(
                env.get("ATLAS_SESSION_WORKER_REAPER_INTERVAL_SEC"),
                _DEFAULT_REAPER_INTERVAL_SEC,
            ),
            stop_ack_sec=_as_number(
                env.get("ATLAS_SESSION_WORKER_STOP_ACK_SEC"), _DEFAULT_STOP_ACK_SEC
            ),
            kill_grace_sec=_as_number(
                env.get("ATLAS_SESSION_WORKER_KILL_GRACE_SEC"), _DEFAULT_KILL_GRACE_SEC
            ),
            reaper_enabled=_as_bool(env.get("ATLAS_SESSION_WORKER_ENABLE_REAPER"), True),
            warning=warning,
        )

    # -- helpers ------------------------------------------------------------

    @property
    def is_strict(self) -> bool:
        return self.single_active_owner

    def cap_exceeded(self, active_count: int) -> bool:
        """True iff a NET-NEW spawn must be refused at the given active count.

        Always False when the cap is disabled or ``max_active <= 0`` (unbounded).
        Per Wave-3 contract H2/H3 the caller applies this ONLY on the net-new
        owner-slot branch; a same-owner replacement reserves its freed slot and is
        never asked.
        """
        if not self.cap_enabled or self.max_active <= 0:
            return False
        return active_count >= self.max_active

    def to_status_dict(self) -> dict[str, str | bool | int]:
        """Compact policy view for the ``/api/session/worker/status`` endpoint."""
        return {
            "policy": self.policy,
            "single_active_owner": self.single_active_owner,
            "cap_enabled": self.cap_enabled,
            "max_active": self.max_active,
        }
