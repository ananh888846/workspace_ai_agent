from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from cryptography.fernet import Fernet
from google_auth_oauthlib.flow import Flow
from psycopg.types.json import Jsonb

from app.config.settings import get_settings
from app.infrastructure.database.connection import database_connection


@dataclass(frozen=True)
class GoogleOAuthState:
    """Trạng thái OAuth được mã hóa và ký để ràng buộc callback với account và user."""

    account_id: str
    user_id: str
    organization_id: str
    nonce: str
    issued_at: int


class GoogleOAuthService:
    """Quản lý Google OAuth và lưu credential đã mã hóa vào PostgreSQL."""

    def __init__(self) -> None:
        self._settings = get_settings()

    def _client_config(self) -> dict[str, Any]:
        if self._settings.google_client_id and self._settings.google_client_secret:
            return {
                "web": {
                    "client_id": self._settings.google_client_id,
                    "client_secret": self._settings.google_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            }

        path = Path(self._settings.google_credentials_file)
        if not path.is_file():
            raise RuntimeError("google_oauth_not_configured")
        return json.loads(path.read_text(encoding="utf-8"))

    def _fernet(self) -> Fernet:
        key = self._settings.google_credential_encryption_key
        if not key:
            raise RuntimeError("google_credential_encryption_key_not_configured")
        try:
            return Fernet(key.encode("ascii"))
        except Exception as exc:
            raise RuntimeError("google_credential_encryption_key_invalid") from exc

    def _sign_state(self, payload: dict[str, Any]) -> str:
        secret = self._settings.google_oauth_state_secret
        if not secret:
            raise RuntimeError("google_oauth_state_secret_not_configured")
        raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        signature = hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).digest()
        return base64.urlsafe_b64encode(raw + b"." + signature).decode("ascii")

    def _verify_state(self, state: str) -> GoogleOAuthState:
        secret = self._settings.google_oauth_state_secret
        if not secret:
            raise RuntimeError("google_oauth_state_secret_not_configured")
        try:
            decoded = base64.urlsafe_b64decode(state.encode("ascii"))
            raw, signature = decoded.rsplit(b".", 1)
            expected = hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).digest()
            if not hmac.compare_digest(signature, expected):
                raise ValueError
            payload = json.loads(raw.decode("utf-8"))
            issued_at = int(payload["issued_at"])
            if abs(int(time.time()) - issued_at) > 600:
                raise ValueError
            return GoogleOAuthState(
                account_id=str(UUID(payload["account_id"])),
                user_id=str(UUID(payload["user_id"])),
                organization_id=str(UUID(payload["organization_id"])),
                nonce=str(payload["nonce"]),
                issued_at=issued_at,
            )
        except Exception as exc:
            raise RuntimeError("google_oauth_state_invalid") from exc

    def authorization_url(
        self, *, account_id: str, user_id: str, organization_id: str, scopes: list[str]
    ) -> str:
        payload = {
            "account_id": str(UUID(account_id)),
            "user_id": str(UUID(user_id)),
            "organization_id": str(UUID(organization_id)),
            "nonce": secrets.token_urlsafe(24),
            "issued_at": int(time.time()),
        }
        state = self._sign_state(payload)
        flow = Flow.from_client_config(
            self._client_config(),
            scopes=scopes,
            redirect_uri=self._settings.google_redirect_uri,
        )
        url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
            state=state,
        )
        return url

    def handle_callback(self, *, code: str, state: str) -> GoogleOAuthState:
        oauth_state = self._verify_state(state)
        flow = Flow.from_client_config(
            self._client_config(),
            scopes=[
                self._settings.google_calendar_read_scope,
                self._settings.google_calendar_write_scope,
            ],
            redirect_uri=self._settings.google_redirect_uri,
        )
        flow.fetch_token(code=code)

        credentials = flow.credentials
        if not credentials.refresh_token and not credentials.token:
            raise RuntimeError("google_oauth_credential_missing")

        calendar_id = self._resolve_primary_calendar_id(credentials)
        encrypted_value = self._fernet().encrypt(
            json.dumps(
                {
                    "token": credentials.token,
                    "refresh_token": credentials.refresh_token,
                    "token_uri": credentials.token_uri,
                    "client_id": credentials.client_id,
                    "client_secret": credentials.client_secret,
                },
                separators=(",", ":"),
            ).encode("utf-8")
        )

        with database_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id
                    FROM user_accounts
                    WHERE id = %s
                      AND user_id = %s
                      AND provider = 'google'
                    """,
                    [oauth_state.account_id, oauth_state.user_id],
                )
                if cursor.fetchone() is None:
                    raise RuntimeError("oauth_account_not_found")

                cursor.execute(
                    """
                    UPDATE user_accounts
                    SET external_account_id = %s,
                        status = 'active',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    [calendar_id, oauth_state.account_id],
                )
                cursor.execute(
                    """
                    UPDATE account_credentials
                    SET status = 'revoked',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_account_id = %s
                      AND status = 'active'
                    """,
                    [oauth_state.account_id],
                )
                cursor.execute(
                    """
                    INSERT INTO account_credentials (
                        id, user_account_id, credential_type,
                        encrypted_value, expires_at, scopes, status,
                        created_at, updated_at
                    )
                    VALUES (
                        %s, %s, 'google_oauth',
                        %s, %s, %s, 'active',
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                    """,
                    [
                        str(uuid4()),
                        oauth_state.account_id,
                        encrypted_value,
                        credentials.expiry,
                        Jsonb(sorted(credentials.scopes or [])),
                    ],
                )
            connection.commit()

        return oauth_state

    @staticmethod
    def _resolve_primary_calendar_id(credentials: Any) -> str:
        try:
            from googleapiclient.discovery import build
            service = build(
                "calendar", "v3", credentials=credentials, cache_discovery=False
            )
            calendar = service.calendars().get(calendarId="primary").execute()
            calendar_id = calendar.get("id")
            if not calendar_id:
                raise RuntimeError("google_primary_calendar_id_missing")
            return str(calendar_id)
        except ImportError as exc:
            raise RuntimeError("google_calendar_dependency_missing") from exc
