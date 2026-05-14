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
