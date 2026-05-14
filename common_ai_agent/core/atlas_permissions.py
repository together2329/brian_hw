"""Small permission-policy layer for ATLAS IP reuse/sharing."""

from __future__ import annotations

from typing import Any

from core.atlas_db import AtlasDB


class PermissionDenied(RuntimeError):
    """Raised when a user cannot perform an IP-scoped action."""


class PermissionPolicy:
    """Ranked permission checks over the existing AtlasDB ACL tables."""

    def __init__(self, db: AtlasDB):
        self.db = db

    def grant_ip_access(
        self,
        ip_id: str,
        grantee_user_id: str,
        permission: str,
        *,
        granted_by_user_id: str = "",
        expires_at: float | None = None,
    ) -> dict[str, Any]:
        return self.db.grant_ip_permission(
            ip_id,
            grantee_user_id,
            permission,
            granted_by_user_id=granted_by_user_id,
            expires_at=expires_at,
        )

    def can_view_ip(self, user_id: str, ip_id: str) -> bool:
        return self.db.can_user_access_ip(ip_id, user_id, "view")

    def can_import_ip(self, user_id: str, ip_id: str) -> bool:
        return self.db.can_user_access_ip(ip_id, user_id, "import")

    def can_write_ip(self, user_id: str, ip_id: str) -> bool:
        return self.db.can_user_access_ip(ip_id, user_id, "write")

    def can_admin_ip(self, user_id: str, ip_id: str) -> bool:
        return self.db.can_user_access_ip(ip_id, user_id, "admin")

    def require_ip_access(
        self,
        user_id: str,
        ip_id: str,
        permission: str = "view",
    ) -> dict[str, Any]:
        if not self.db.can_user_access_ip(ip_id, user_id, permission):
            raise PermissionDenied(
                f"user {user_id!r} lacks {permission!r} access to IP {ip_id!r}"
            )
        ip = self.db.get_ip_block(ip_id)
        if ip is None:
            raise PermissionDenied(f"IP {ip_id!r} does not exist")
        return ip

    # ---------- Chat / Orchestrator room access ----------

    GLOBAL_ROOM = "_global"

    def can_enter_global_room(self, user_id: str) -> bool:
        """Global chat is open to any user with at least one IP view grant or
        who owns at least one workspace. Plain logged-in-but-unattached users
        stay out so the global room reflects workspace participation."""
        user = self.db.get_user(user_id) if user_id else None
        if user and user.get("role") == "admin":
            return True
        owns = self.db._fetchone(
            "SELECT 1 FROM workspaces WHERE owner_user_id = ? LIMIT 1",
            (user_id,),
        )
        if owns is not None:
            return True
        granted = self.db._fetchone(
            """
            SELECT 1 FROM ip_permissions
             WHERE grantee_user_id = ?
               AND (expires_at IS NULL OR expires_at > ?)
             LIMIT 1
            """,
            (user_id, self.db._now()),
        )
        return granted is not None

    def can_enter_room(self, user_id: str, room: str) -> bool:
        """Boolean form of require_room_access; used to filter the rooms
        dropdown without raising."""
        if not user_id:
            return False
        if room == self.GLOBAL_ROOM:
            return self.can_enter_global_room(user_id)
        ip = self.db.get_ip_block_by_name(room)
        if ip is None:
            return False
        return self.db.can_user_access_ip(ip["id"], user_id, "view")

    def require_room_access(self, user_id: str, room: str) -> dict[str, Any]:
        """Raise PermissionDenied if a user cannot enter the chat room.

        Returns a context dict with the resolved ip row (None for the global
        room) so the caller does not need a second DB lookup."""
        if room == self.GLOBAL_ROOM:
            if not self.can_enter_global_room(user_id):
                raise PermissionDenied(
                    f"user {user_id!r} has no IP view grants — global room locked"
                )
            return {"room": room, "ip": None}
        ip = self.db.get_ip_block_by_name(room)
        if ip is None:
            raise PermissionDenied(f"unknown IP room {room!r}")
        if not self.db.can_user_access_ip(ip["id"], user_id, "view"):
            raise PermissionDenied(
                f"user {user_id!r} lacks 'view' access to IP {room!r}"
            )
        return {"room": room, "ip": ip}

    def list_accessible_rooms(self, user_id: str) -> list[dict[str, Any]]:
        """Rooms this user is allowed to enter — used to populate the
        OrchestratorPanel dropdown without leaking room names that 403.

        Admins see every IP. Non-admins see _global iff they qualify
        for it (own a workspace OR have ≥1 grant) plus every IP they
        own or were granted at view+."""
        rooms: list[dict[str, Any]] = []
        if self.can_enter_global_room(user_id):
            rooms.append({"name": self.GLOBAL_ROOM, "scope": "global", "ip_id": None})

        user = self.db.get_user(user_id) if user_id else None
        if user and user.get("role") == "admin":
            ip_rows = [dict(r) for r in self.db._fetchall(
                "SELECT * FROM ip_blocks ORDER BY ip_name"
            )]
        else:
            ip_rows = self.db.list_accessible_ip_blocks(user_id, "view")

        for ip in ip_rows:
            rooms.append({
                "name": ip["ip_name"],
                "scope": "ip",
                "ip_id": ip["id"],
                "ip_type": ip.get("ip_type"),
            })
        return rooms
