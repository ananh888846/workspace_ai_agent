from __future__ import annotations

from typing import Any

from app.application.core_runtime import CredentialResolution, ExternalAccount


class PostgresCredentialRepository:
    """Kiểm tra credential của external account bằng PostgreSQL.

    Repository này chỉ được gọi sau khi Authorization = ALLOW.
    Giai đoạn này chỉ kiểm tra readiness và không trả encrypted_value.
    """

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def resolve_authorized_credential(
        self, *, account: ExternalAccount
    ) -> CredentialResolution:
        query = """
            SELECT
                credential_type,
                expires_at,
                scopes
            FROM account_credentials
            WHERE user_account_id = %s
              AND status = 'active'
              AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            ORDER BY updated_at DESC,
                     created_at DESC,
                     id::text
            LIMIT 1
        """

        with self._connection.cursor() as cursor:
            cursor.execute(query, [account.id])
            row = cursor.fetchone()

        if not row:
            return CredentialResolution(status="oauth_required")

        return CredentialResolution(
            status="ready",
            credential_type=str(row[0]),
            expires_at=row[1],
            scopes=row[2],
        )
