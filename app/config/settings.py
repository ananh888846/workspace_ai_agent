"""Central application configuration.

Reads environment variables only. Secrets must stay outside Git.
Per-user/provider OAuth credentials remain behind CredentialResolver.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


@dataclass(frozen=True)
class Settings:
    app_env: str = _env("APP_ENV", "development")
    app_host: str = _env("APP_HOST", "0.0.0.0")
    app_port: int = int(_env("APP_PORT", "8000"))

    database_url: str = _env("DATABASE_URL")
    qdrant_url: str = _env("QDRANT_URL", "http://localhost:6333")
    qdrant_collection: str = _env("QDRANT_COLLECTION", "knowledge_v1")

    ollama_base_url: str = _env("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_chat_model: str = _env("OLLAMA_CHAT_MODEL", "qwen2.5:1.5b")
    ollama_vision_model: str = _env("OLLAMA_VISION_MODEL", "qwen2.5vl:3b")
    ollama_embedding_model: str = _env(
        "OLLAMA_EMBEDDING_MODEL", "nomic-embed-text-v2-moe"
    )

    file_storage_driver: str = _env("FILE_STORAGE_DRIVER", "local")
    file_storage_path: str = _env("FILE_STORAGE_PATH", "./data/storage")

    google_credentials_file: str = _env("GOOGLE_CREDENTIALS_FILE", "./data/google/credentials.json")
    google_token_dir: str = _env("GOOGLE_TOKEN_DIR", "./data/google")
    google_client_id: str = _env("GOOGLE_CLIENT_ID")
    google_client_secret: str = _env("GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = _env(
        "GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback"
    )

    google_calendar_read_scope: str = _env(
        "GOOGLE_CALENDAR_READ_SCOPE",
        "https://www.googleapis.com/auth/calendar.readonly",
    )
    google_calendar_write_scope: str = _env(
        "GOOGLE_CALENDAR_WRITE_SCOPE",
        "https://www.googleapis.com/auth/calendar",
    )

    @property
    def google_oauth_configured(self) -> bool:
        return bool(self.google_client_id and self.google_client_secret)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
