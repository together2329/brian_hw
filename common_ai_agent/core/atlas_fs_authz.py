"""Filesystem-read authorization for the multi-tenant ATLAS web API.

Single source of truth for "may user U read/write this path or IP?" so the
~40 content-serving endpoints (files, vcd, ssot, sim-debug, coverage, git, …)
do not each re-implement — or silently forget — the ownership check. Prior to
this module every such endpoint only confined its ``path``/``ip`` param to
``PROJECT_ROOT`` and did **zero** owner check, so any authenticated user could
read any other user's IP source, waveforms and ``.session`` conversation logs
(audit finding B1).

Design:

* The path -> resource-class mapping is **pure** and unit-testable
  (:func:`classify_segments`).
* The final allow/deny consults :class:`core.atlas_db.AtlasDB` ACLs
  (``can_user_access_ip`` / ``get_ip_block_by_name``) through an injected
  ``db`` handle, so this module has no hard dependency on a live DB.
* **Fail closed.** Anything we cannot positively authorize is denied. A DB
  error during the lookup denies (it is the authorization decision, so it must
  never fall through to allow).

The ownership model (verified against the schema):

* A top-level directory name **equals** ``ip_blocks.ip_name``; IP ownership is
  inherited from ``workspaces.owner_user_id`` plus ``ip_permissions`` grants
  (``AtlasDB.can_user_access_ip``). There is no ``ip_`` prefix convention —
  IP directory names are arbitrary.
* Per-user scratch lives under ``.session/<owner>/<ip>/<workflow>/...`` where
  ``<owner>`` is the normalized username.
* A curated set of shipped/infra roots (:data:`SHARED_ROOTS`) is shared across
  tenants and readable by any authenticated user.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Optional, Protocol

__all__ = [
    "SHARED_ROOTS",
    "SHARED_ROOT_FILES",
    "SESSION_ROOT",
    "AuthzDecision",
    "classify_segments",
    "authorize_ip",
    "authorize_path",
    "accessible_ip_names",
]

# Top-level roots that are shipped code / shared infrastructure — NOT per-user
# data. Readable by any authenticated user. This mirrors (and extends) the
# skip-set that ``/api/ip/list`` uses to decide what is "not a user IP".
SHARED_ROOTS = frozenset(
    {
        "doc",
        "rtl",
        "template",
        "lib",
        "pdk",
        "vendor",
        "ip_examples",
        "workflow",
        "src",
        "core",
        "frontend",
        "tests",
        "scripts",
        "evidence",
        "artifacts",
        "node_modules",
        "mcp",
        "tools",
        "src-tauri",
        "command_logs",
        "plans",
    }
)

# Individual project-root files that are shared config/docs (not user data).
# Single-segment reads that hit one of these are allowed; everything else at the
# root that is neither a registered IP nor a shared root is denied (fail closed).
SHARED_ROOT_FILES = frozenset(
    {
        "soc.ssot.yaml",
        "IP_SIGNOFF.md",
        "README.md",
        "readme.md",
    }
)

SESSION_ROOT = ".session"

# Sentinel used by callers (listing endpoints) to mean "no restriction".
ALL = None


class _DBLike(Protocol):
    """The minimal AtlasDB surface this module needs (for typing/tests)."""

    def get_ip_block_by_name(self, ip_name: str) -> Optional[dict]: ...

    def can_user_access_ip(
        self, ip_id: str, user_id: str, permission: str = ...
    ) -> bool: ...


@dataclass(frozen=True)
class AuthzDecision:
    """Result of an authorization check.

    ``allow`` is the only thing callers must branch on; ``status``/``reason``
    shape the deny response, and ``kind`` aids logging/tests.
    """

    allow: bool
    status: int = 200
    reason: str = ""
    kind: str = ""

    def __bool__(self) -> bool:  # convenience: `if decision:` == allowed
        return self.allow


def _segments(rel_path: str) -> list[str]:
    """Split a relative path into clean POSIX segments.

    Strips a leading ``/`` and any ``./`` noise. ``..`` segments are preserved
    so the caller can reject traversal explicitly.
    """
    raw = str(rel_path or "").strip().lstrip("/")
    parts: list[str] = []
    for part in PurePosixPath(raw).parts:
        if part in ("", "/", "."):
            continue
        parts.append(part)
    return parts


def classify_segments(parts: list[str]) -> str:
    """Classify a path (as clean segments) into a resource class.

    Returns one of: ``"escape"`` (traversal), ``"root"`` (empty / project root),
    ``"session"`` (under ``.session``), ``"shared"`` (a shared infra root or a
    shared root file), or ``"ip"`` (anything else — a candidate IP dir name).
    This function is pure and does not touch the DB or filesystem.
    """
    if any(p == ".." for p in parts):
        return "escape"
    if not parts:
        return "root"
    seg0 = parts[0]
    if seg0 == SESSION_ROOT:
        return "session"
    if seg0 in SHARED_ROOTS:
        return "shared"
    if len(parts) == 1 and seg0 in SHARED_ROOT_FILES:
        return "shared"
    return "ip"


def _ip_decision(
    ip_name: str,
    *,
    user_id: str,
    db: Any,
    permission: str,
    owned_ips: Optional[set] = None,
) -> AuthzDecision:
    """ACL decision for a single IP name. Fail closed on any DB error.

    Two ownership sources, mirroring ``/api/ip/list``:

    1. ``owned_ips`` — IPs the user owns via their ``.session/<owner>/<ip>/``
       namespace (resolved from ``db.list_sessions(user_id)`` by the caller).
       This is the PRIMARY multi-user model; an owner has full read+write, so a
       hit here allows any ``permission``.
    2. ``ip_blocks`` ACL (``can_user_access_ip``) — the sharing/grant layer for
       IPs explicitly shared with the user (also covers admin + workspace
       owner). Used for the requested ``permission`` rank.
    """
    name = str(ip_name or "").strip().strip("/")
    if not name:
        return AuthzDecision(False, 403, "missing ip", "ip")
    # (1) Session-namespace ownership — the primary model.
    if owned_ips is not None and name in owned_ips:
        return AuthzDecision(True, 200, "", "ip")
    # (2) Sharing/grant layer.
    try:
        row = db.get_ip_block_by_name(name) if db is not None else None
        if not row:
            # Not owned via a session and not a registered/shared IP -> we
            # cannot prove access -> deny (fail closed). This matches
            # /api/ip/list, which would not surface such an IP to the user.
            return AuthzDecision(False, 403, f"no access to {name!r}", "ip")
        ip_id = row.get("id") if isinstance(row, dict) else None
        if not ip_id:
            return AuthzDecision(False, 403, "ip has no id", "ip")
        if db.can_user_access_ip(ip_id, user_id, permission):
            return AuthzDecision(True, 200, "", "ip")
        return AuthzDecision(False, 403, f"no {permission} access to {name!r}", "ip")
    except Exception:
        # The ownership lookup IS the authorization decision: a failure must
        # DENY, never allow.
        return AuthzDecision(False, 403, "authorization unavailable", "ip")


def authorize_ip(
    ip_name: str,
    *,
    user_id: str,
    username: str = "",
    is_admin: bool = False,
    multi_user: bool = True,
    db: Any = None,
    permission: str = "view",
    owned_ips: Optional[set] = None,
) -> AuthzDecision:
    """Authorize access to a named IP (for ``ip=``-param endpoints).

    Order (fail closed): multi-user off -> allow; no identity -> 401; admin ->
    allow; shared root passed as ip -> allow; else ACL check (session ownership
    then ip_blocks grant).
    """
    if not multi_user:
        return AuthzDecision(True, 200, "", "multiuser_off")
    if not user_id or user_id == "default":
        return AuthzDecision(False, 401, "login required", "unauthenticated")
    if is_admin:
        return AuthzDecision(True, 200, "", "admin")
    name = str(ip_name or "").strip().strip("/")
    # A caller may pass a shared root (e.g. scope=rtl) through an ip-param.
    if name in SHARED_ROOTS:
        return AuthzDecision(True, 200, "", "shared")
    return _ip_decision(
        name, user_id=user_id, db=db, permission=permission, owned_ips=owned_ips
    )


def authorize_path(
    rel_path: str,
    *,
    user_id: str,
    username: str = "",
    is_admin: bool = False,
    multi_user: bool = True,
    db: Any = None,
    permission: str = "view",
    owned_ips: Optional[set] = None,
    owner_aliases: Optional[set] = None,
) -> AuthzDecision:
    """Authorize a read/write of a relative ``path`` for the given user.

    Order (each step fail-closed):

    1. multi-user disabled            -> ALLOW
    2. no identity / ``default``       -> DENY 401
    3. admin                           -> ALLOW
    4. traversal (``..``)              -> DENY 400
    5. empty (project root)            -> DENY 403  (root listing is not a single read)
    6. ``.session/<owner>/...``        -> ALLOW iff ``<owner> == username`` else 403
    7. shared root / shared root file  -> ALLOW
    8. IP dir                          -> session-ownership (``owned_ips``) then
                                          ip_blocks grant (``can_user_access_ip``)
    9. anything else                   -> DENY 403
    """
    if not multi_user:
        return AuthzDecision(True, 200, "", "multiuser_off")
    if not user_id or user_id == "default":
        return AuthzDecision(False, 401, "login required", "unauthenticated")
    if is_admin:
        return AuthzDecision(True, 200, "", "admin")

    parts = _segments(rel_path)
    kind = classify_segments(parts)

    if kind == "escape":
        return AuthzDecision(False, 400, "invalid path", "escape")
    if kind == "root":
        return AuthzDecision(False, 403, "root access not permitted", "root")
    if kind == "session":
        owner = parts[1] if len(parts) >= 2 else ""
        # Accept the bare username AND any alias (e.g. the per-model owner
        # "<user>__<model>" when ATLAS_SESSION_PER_MODEL is on, which is what
        # the on-disk .session/<owner>/ segment becomes).
        valid_owners = set(owner_aliases) if owner_aliases else set()
        if username:
            valid_owners.add(username)
        if owner and owner in valid_owners:
            return AuthzDecision(True, 200, "", "session")
        return AuthzDecision(False, 403, "session owner mismatch", "session")
    if kind == "shared":
        return AuthzDecision(True, 200, "", "shared")
    # kind == "ip": the leading segment is EITHER a top-level (legacy) IP dir
    # name, OR — in the multi-user workspace layout — the OWNER of a
    # workspace-rooted path ``<owner>/<workspace>/<ip>/...`` (the on-disk shape
    # produced by ``AtlasContext.ip_root`` = ``atlas_root/user_name/
    # workspace_session/ip_name``). A path under the caller's OWN owner segment
    # is their workspace; allow it — mirroring the ``.session/<owner>``
    # owner-match above. Without this, the gate misreads the owner segment as an
    # IP name, finds no ``ip_blocks`` row and fail-closes, so the owner cannot
    # read their own RTL source (e.g. the sim_debug source panel). A foreign
    # owner segment is NOT in ``valid_owners`` and still falls through to the IP
    # ACL, so cross-tenant access stays fail-closed.
    valid_owners = set(owner_aliases) if owner_aliases else set()
    if username:
        valid_owners.add(username)
    if parts[0] in valid_owners:
        return AuthzDecision(True, 200, "", "workspace")
    return _ip_decision(
        parts[0], user_id=user_id, db=db, permission=permission, owned_ips=owned_ips
    )


def accessible_ip_names(
    *,
    user_id: str,
    is_admin: bool,
    multi_user: bool,
    db: Any,
    permission: str = "view",
    owned_ips: Optional[set] = None,
) -> Optional[set[str]]:
    """Set of IP names the user may access, for filtering listing endpoints.

    Returns ``None`` when there is no restriction (multi-user off or admin) so
    callers can skip filtering entirely. Otherwise the union of session-owned
    IPs (``owned_ips``, the primary model) and ip_blocks grants. Fail closed:
    on a grant-lookup error the owned set is still returned (deny only the
    grant layer); shared roots are added by the caller, not here.
    """
    if not multi_user or is_admin:
        return ALL
    if not user_id or user_id == "default":
        return set()
    names: set[str] = set(owned_ips or set())
    try:
        rows = db.list_accessible_ip_blocks(user_id, permission)
        for row in rows or []:
            name = (row.get("ip_name") if isinstance(row, dict) else None) or ""
            if name:
                names.add(str(name))
    except Exception:
        pass
    return names
