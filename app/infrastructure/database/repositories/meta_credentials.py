from __future__ import annotations

import json
from typing import Any

from cryptography.fernet import Fernet

from app.application.core_runtime import CredentialResolution, ExternalAccount
from app.config.settings import get_settings
from app.providers.meta.credentials import MetaCredentialContext


class PostgresMetaCredentialRepository:
    """Resolve the encrypted Threads credential for an authorized account."""

    provider = "threads"

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def resolve_authorized_credential(
        self, *, account: ExternalAccount
    ) -> CredentialResolution:
        query = """
            SELECT ac.credential_type, ac.encrypted_value, ac.expires_at, ac.scopes
            FROM account_credentials AS ac
            JOIN user_accounts AS ua ON ua.id = ac.user_account_id
            WHERE ac.user_account_id = %s
              AND ua.provider = %s
              AND ac.status = 'active'
            ORDER BY ac.updated_at DESC, ac.created_at DESC, ac.id::text
            LIMIT 1
        """
        with self._connection.cursor() as cursor:
            cursor.execute(query, [account.id, self.provider])
            row = cursor.fetchone()

        if not row:
            return CredentialResolution(status="oauth_required")

        try:
            key = get_settings().credential_encryption_key
            if not key:
                raise RuntimeError("credential_encryption_key_not_configured")
            payload = json.loads(
                Fernet(key.encode("ascii")).decrypt(row[1]).decode("utf-8")
            )
            access_token = payload.get("access_token")
            if not isinstance(access_token, str) or not access_token:
                raise ValueError("meta_access_token_missing")
        except Exception as exc:
            raise RuntimeError("meta_credential_resolution_failed") from exc

        return CredentialResolution(
            status="ready",
            credential_type=str(row[0]),
            expires_at=row[2],
            scopes=row[3],
            credential_context=MetaCredentialContext(access_token=access_token),
        )
