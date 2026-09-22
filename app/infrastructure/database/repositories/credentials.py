from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from cryptography.fernet import Fernet
from google.oauth2.credentials import Credentials

from app.application.core_runtime import CredentialResolution, ExternalAccount
from app.config.settings import get_settings
from app.providers.google.calendar.client import GoogleCredentialContext


class PostgresCredentialRepository:
    """Kiểm tra credential của external account bằng PostgreSQL.

    Credential hết hạn vẫn được giữ nếu còn refresh token để Google Auth có thể
    làm mới access token khi provider được gọi. Repository không đưa secret ra
    HTTP response.
    """

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def resolve_authorized_credential(
        self, *, account: ExternalAccount
    ) -> CredentialResolution:
        query = """
            SELECT
                credential_type,
                encrypted_value,
                expires_at,
                scopes
            FROM account_credentials
            WHERE user_account_id = %s
              AND status = 'active'
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

        try:
            key = get_settings().google_credential_encryption_key
            if not key:
                raise RuntimeError("google_credential_encryption_key_not_configured")
            payload = json.loads(
                Fernet(key.encode("ascii")).decrypt(row[1]).decode("utf-8")
            )
            expires_at = row[2]
            if expires_at is not None:
                if expires_at.tzinfo is not None:
                    expires_at = expires_at.astimezone(timezone.utc).replace(tzinfo=None)

            credentials = Credentials(
                token=payload.get("token"),
                refresh_token=payload.get("refresh_token"),
                token_uri=payload.get("token_uri"),
                client_id=payload.get("client_id"),
                client_secret=payload.get("client_secret"),
                scopes=row[3] or [],
                expiry=expires_at,
            )

            if (
                expires_at is not None
                and expires_at <= datetime.now(timezone.utc).replace(tzinfo=None)
                and not payload.get("refresh_token")
            ):
                return CredentialResolution(status="oauth_required")
        except Exception as exc:
            raise RuntimeError("google_credential_decrypt_failed") from exc

        return CredentialResolution(
            status="ready",
            credential_type=str(row[0]),
            expires_at=expires_at,
            scopes=row[3],
            credential_context=GoogleCredentialContext(credentials=credentials),
        )
