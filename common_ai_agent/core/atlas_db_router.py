"""Atlas runtime-DB router (Wave 1 / Unit A).

Single resolution point for "which SQLite file backs this work?" in the
control-vs-runtime split (see ``plans/atlas-runtime-db-100-users-v2.md`` §2.1).

Two databases conceptually:

* **Control DB** — the historical ``atlas.db``: users, sessions, workspaces,
  chat, workflow_runs, and the ``session_runtime_dbs`` manifest. Full schema.
* **Runtime DB** — one SQLite file per session at
  ``<runtime_root>/<session_uid[0:2]>/<session_uid>.db``: only the IPC + trace
  subset (session_queue / messages / parts / trace_events / llm_calls).

Mode selection (read at CALL time, never cached at import, so tests and a live
server can flip it without reimporting):

* ``ATLAS_RUNTIME_DB_MODE=central`` (DEFAULT) — every ``runtime_*`` returns the
  CONTROL path. Behavior-preserving: nothing is sharded yet. This is the safe
  phase the rollout starts in.
* ``ATLAS_RUNTIME_DB_MODE=session`` — per-session runtime paths.

Security / correctness invariants (plan §2.5, §2.11, R4/R15/R23):

* The runtime filename is derived ONLY from ``session_uid`` (a uuid4 hex with
  no path characters). Raw ``session_id`` (which may contain ``/``, ``..``,
  user text) NEVER touches the filesystem.
* ``session_uid`` is resolved-or-minted ONCE via the control DB and persisted,
  so the SAME ``session_id`` always yields the SAME path across retries
  (no re-mint -> no split-brain / double-delivery on spawn-retry).
* On EVERY open we recompute the expected path from ``session_uid`` + root and
  assert it is contained under ``Path(runtime_root).resolve()``; anything that
  would escape the root is rejected (traversal guard).
* If no ``session_uid`` is resolvable and minting is disallowed, we FAIL CLOSED.
  The ``sha256(session_id)[:24]`` derived-key fallback is allowed ONLY when
  ``ATLAS_RUNTIME_DB_ALLOW_DERIVED_KEY=1`` (a test seam, off by default).
"""

from __future__ import annotations

import hashlib
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from core.atlas_db import AtlasDB


# Hex chars are the only thing a legitimate session_uid / derived key contains.
_HEX_CHARS = set("0123456789abcdef")


def _truthy(value: Optional[str]) -> bool:
    return str(value or "").strip().lower() in ("1", "true", "yes", "on")


class RuntimeDBError(RuntimeError):
    """Router could not safely resolve a runtime DB path."""


@dataclass(frozen=True)
class RuntimeDBRoute:
    """Resolved routing decision for one session."""

    session_id: str
    session_uid: Optional[str]
    runtime_db_path: str
    mode: str  # "central" | "session"


class AtlasDBRouter:
    """Resolve control vs per-session runtime DB paths.

    Envs are read at call time (not cached at construction) unless explicit
    overrides are passed to the constructor (used by tests). An explicit
    override always wins over the env for that router instance.
    """

    VALID_MODES = ("central", "session")

    def __init__(
        self,
        control_path: Optional[str] = None,
        runtime_root: Optional[str] = None,
        mode: Optional[str] = None,
    ) -> None:
        # Explicit overrides pin the value for this instance; otherwise resolve
        # lazily from env on each access so a test/live flip is observed.
        self._control_override = control_path
        self._runtime_root_override = runtime_root
        self._mode_override = mode

    # ---------- env / config resolution ----------

    def control_db_path(self) -> str:
        """Resolve the control DB path.

        Order: explicit override -> ATLAS_CONTROL_DB_PATH -> the default
        AtlasDB resolves today (ATLAS_DB_PATH / ~/.common_ai_agent/atlas.db).
        Reusing AtlasDB's own default keeps the control DB byte-identical to
        what existed before the split.
        """
        if self._control_override is not None:
            return self._control_override
        explicit = os.environ.get("ATLAS_CONTROL_DB_PATH")
        if explicit:
            return explicit
        # Reuse AtlasDB's default resolution exactly (ATLAS_DB_PATH or home).
        return os.environ.get("ATLAS_DB_PATH") or str(
            Path.home() / ".common_ai_agent" / "atlas.db"
        )

    def runtime_root(self) -> str:
        """Resolve the runtime-DB root directory.

        Order: explicit override -> ATLAS_RUNTIME_DB_ROOT -> ``<control-db-dir>/runtime``.
        """
        if self._runtime_root_override is not None:
            return self._runtime_root_override
        explicit = os.environ.get("ATLAS_RUNTIME_DB_ROOT")
        if explicit:
            return explicit
        return str(Path(self.control_db_path()).resolve().parent / "runtime")

    def mode(self) -> str:
        """Resolve the runtime mode ('central' default, or 'session')."""
        if self._mode_override is not None:
            value = self._mode_override
        else:
            value = os.environ.get("ATLAS_RUNTIME_DB_MODE") or "central"
        value = str(value).strip().lower()
        if value not in self.VALID_MODES:
            raise RuntimeDBError(
                f"invalid ATLAS_RUNTIME_DB_MODE={value!r}; "
                f"expected one of {self.VALID_MODES}"
            )
        return value

    def _allow_derived_key(self) -> bool:
        return _truthy(os.environ.get("ATLAS_RUNTIME_DB_ALLOW_DERIVED_KEY"))

    # ---------- control DB ----------

    def control_db(self) -> AtlasDB:
        """Open an AtlasDB on the control path (FULL schema)."""
        return AtlasDB(db_path=self.control_db_path(), schema_set="full")

    # ---------- session_uid resolution ----------

    def _resolve_session_uid(self, session_id: str, create: bool) -> Optional[str]:
        """Resolve (or, if allowed, mint) the session_uid for *session_id*.

        Resolution order against the CONTROL DB:
          1. Existing manifest row (fast path, already minted once).
          2. Existing session row (sessions.session_uid).
          3. If ``create``: mint a fresh uid (uuid4 hex). The DURABLE record is
             the manifest, written by ``runtime_route``; we only backfill
             ``sessions.session_uid`` (a safe single-column update) when a
             session row exists but lacks one. We deliberately do NOT call
             ``upsert_runtime_session`` here — it rewrites the entire sessions
             row (owner/ip/workflow/title/summary default to ''/None) and would
             BLANK an existing session's metadata.
          4. Derived-key fallback ``sha256(session_id)[:24]`` — ONLY when
             ATLAS_RUNTIME_DB_ALLOW_DERIVED_KEY=1 (test seam).

        Returns the uid, or None when nothing is resolvable and creation/derived
        fallback are both disallowed (the caller then FAILS CLOSED).
        """
        if not session_id:
            if self._allow_derived_key():
                return self._derived_key(session_id)
            return None

        control = self.control_db()

        # 1. manifest row (already resolved once).
        manifest = control.get_session_runtime_db(session_id)
        if manifest and manifest.get("session_uid"):
            return manifest["session_uid"]

        # 2. existing session row.
        sess = control.find_session(session_id)
        if sess and sess.get("session_uid"):
            return sess["session_uid"]

        # 3. resolve-or-mint ONCE (only if creation is allowed). Mint a fresh uid
        # WITHOUT mutating other session metadata. We do NOT call
        # upsert_runtime_session here: it unconditionally rewrites the whole
        # sessions row (owner/ip/workflow/title/summary default to ''/None) and
        # would BLANK an existing session's metadata (review LOW #1). The durable
        # uid record is the manifest, written by runtime_route(); here we only
        # backfill sessions.session_uid (a safe single-column update via
        # update_session, which SETs only the fields passed) when a session row
        # exists but lacks one. Determinism (R4) holds because the next call
        # resolves via the manifest fast-path (step 1).
        if create:
            uid = uuid.uuid4().hex
            if sess is not None:
                try:
                    control.update_session(session_id, session_uid=uid)
                except Exception:
                    pass
            return uid

        # 4. derived-key fallback (test seam only).
        if self._allow_derived_key():
            return self._derived_key(session_id)

        return None

    @staticmethod
    def _derived_key(session_id: str) -> str:
        """sha256(session_id)[:24] — deterministic, path-char-free.

        Used ONLY behind ATLAS_RUNTIME_DB_ALLOW_DERIVED_KEY for tests/sessions
        that have no minted uid yet. 24 hex chars is plenty of collision margin.
        """
        return hashlib.sha256(str(session_id).encode("utf-8")).hexdigest()[:24]

    # ---------- path computation + containment guard ----------

    @staticmethod
    def _is_safe_uid(session_uid: str) -> bool:
        """A safe uid is non-empty lowercase hex (no path chars whatsoever)."""
        if not session_uid:
            return False
        s = session_uid.lower()
        return len(s) >= 2 and all(ch in _HEX_CHARS for ch in s)

    def _expected_runtime_path(self, session_uid: str) -> str:
        """Compute + containment-check ``<root>/<uid[0:2]>/<uid>.db``.

        Recomputed on EVERY open (never trust a stored path). Rejects anything
        whose resolved path escapes ``Path(runtime_root).resolve()`` and any uid
        that is not pure hex (defense in depth — the uid should already be
        hex-only by construction).
        """
        if not self._is_safe_uid(session_uid):
            raise RuntimeDBError(
                f"unsafe session_uid for path derivation: {session_uid!r}"
            )
        uid = session_uid.lower()
        root = Path(self.runtime_root()).resolve()
        candidate = (root / uid[0:2] / f"{uid}.db").resolve()
        # Containment guard: candidate must be strictly under root.
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise RuntimeDBError(
                f"runtime path escapes root: {candidate} not under {root}"
            ) from exc
        return str(candidate)

    # ---------- public routing API ----------

    def runtime_route(self, session_id: str, create: bool = True) -> RuntimeDBRoute:
        """Resolve the full routing decision for *session_id*.

        central mode -> route.runtime_db_path == control path (uid may be None).
        session mode -> resolve uid (fail closed if none) + traversal-checked path.
        """
        mode = self.mode()
        if mode == "central":
            return RuntimeDBRoute(
                session_id=session_id,
                session_uid=None,
                runtime_db_path=self.control_db_path(),
                mode="central",
            )

        # session mode
        session_uid = self._resolve_session_uid(session_id, create=create)
        if not session_uid:
            raise RuntimeDBError(
                "session mode: no session_uid resolvable for "
                f"session_id={session_id!r} (create={create}); failing closed. "
                "Set ATLAS_RUNTIME_DB_ALLOW_DERIVED_KEY=1 only in tests."
            )
        runtime_path = self._expected_runtime_path(session_uid)
        # Persist/refresh the manifest so reads can find this file. We only
        # touch the manifest when creating (resolution-only callers stay R/O).
        if create:
            control = self.control_db()
            control.upsert_session_runtime_db(
                session_id=session_id,
                session_uid=session_uid,
                runtime_db_path=runtime_path,
            )
        return RuntimeDBRoute(
            session_id=session_id,
            session_uid=session_uid,
            runtime_db_path=runtime_path,
            mode="session",
        )

    def runtime_db_path(self, session_id: str, create: bool = True) -> str:
        """Return the runtime DB path for *session_id* (control path in central)."""
        return self.runtime_route(session_id, create=create).runtime_db_path

    def runtime_db(self, session_id: str, create: bool = True) -> AtlasDB:
        """Open an AtlasDB on the runtime path for *session_id*.

        central mode -> opens the control DB with the FULL schema (so the file
        keeps every table it already had). session mode -> opens the per-session
        runtime file with the RUNTIME-ONLY schema subset (5 tables), so the file
        does not materialize ~24 unused control tables.
        """
        route = self.runtime_route(session_id, create=create)
        if route.mode == "central":
            return AtlasDB(db_path=route.runtime_db_path, schema_set="full")
        # Only materialize the shard dir when actually opening to write
        # (create=True). A read-only resolve (create=False) must not have the
        # filesystem side effect of creating directories.
        if create:
            Path(route.runtime_db_path).parent.mkdir(parents=True, exist_ok=True)
        return AtlasDB(db_path=route.runtime_db_path, schema_set="runtime")
