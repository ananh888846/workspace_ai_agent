from __future__ import annotations

from typing import Any

from app.application.core_runtime import ExternalAccount


class PostgresPermissionRepository:
    """PostgreSQL authorization queries; never reads credential secrets."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def has_capability_permission(self, *, user_id: str, capability: str) -> bool:
        resource, separator, action = capability.partition(".")
        if not separator or not resource or not action:
            return False

        query = """
            SELECT EXISTS (
                SELECT 1
                FROM user_roles AS ur
                JOIN role_permissions AS rp
                  ON rp.role_id = ur.role_id
                JOIN permissions AS p
                  ON p.id = rp.permission_id
                WHERE ur.user_id = %s
                  AND p.resource = %s
                  AND p.action = %s
            )
        """
        with self._connection.cursor() as cursor:
            cursor.execute(query, [user_id, resource, action])
            row = cursor.fetchone()
        return bool(row and row[0])

    def has_account_access(
        self,
        *,
        organization_id: str,
        user_id: str,
        account: ExternalAccount,
        capability: str,
    ) -> bool:
        # Ownership is account access. A delegated account requires an
        # active, non-expired grant in the same organization.
        query = """
            SELECT EXISTS (
                SELECT 1
                FROM user_accounts AS ua
                JOIN organization_members AS om
                  ON om.organization_id = %s
                 AND om.user_id = ua.user_id
                 AND om.status = 'active'
                WHERE ua.id = %s
                  AND ua.user_id = %s
                  AND ua.status = 'active'
            )
            OR EXISTS (
                SELECT 1
                FROM user_accounts AS ua
                JOIN organization_members AS om_owner
                  ON om_owner.organization_id = %s
                 AND om_owner.user_id = ua.user_id
                 AND om_owner.status = 'active'
                JOIN account_grants AS ag
                  ON ag.user_account_id = ua.id
                 AND ag.owner_user_id = ua.user_id
                 AND ag.organization_id = om_owner.organization_id
                 AND ag.grantee_user_id = %s
                 AND ag.status = 'active'
                 AND (ag.starts_at IS NULL OR ag.starts_at <= CURRENT_TIMESTAMP)
                 AND (ag.expires_at IS NULL OR ag.expires_at > CURRENT_TIMESTAMP)
                 AND ag.revoked_at IS NULL
                WHERE ua.id = %s
                  AND ua.status = 'active'
            )
        """
        with self._connection.cursor() as cursor:
            cursor.execute(
                query,
                [
                    organization_id, account.id, user_id,
                    organization_id, user_id, account.id,
                ],
            )
            row = cursor.fetchone()
        return bool(row and row[0])

    def has_resource_access(
        self,
        *,
        organization_id: str,
        user_id: str,
        resource_id: str,
        action: str,
    ) -> bool:
        query = """
            SELECT EXISTS (
                SELECT 1
                FROM resource_permissions AS rp
                JOIN resources AS r
                  ON r.id = rp.resource_id
                 AND r.organization_id = %s
                JOIN organization_members AS om
                  ON om.organization_id = r.organization_id
                 AND om.user_id = rp.user_id
                 AND om.status = 'active'
                WHERE rp.resource_id = %s
                  AND rp.user_id = %s
                  AND rp.action = %s
                  AND rp.effect = 'allow'
                  AND (rp.expires_at IS NULL OR rp.expires_at > CURRENT_TIMESTAMP)
            )
        """
        with self._connection.cursor() as cursor:
            cursor.execute(query, [organization_id, resource_id, user_id, action])
            row = cursor.fetchone()
        return bool(row and row[0])
