"""Central application configuration.

Reads environment variables only. Secrets must stay outside Git.
Per-user/provider OAuth credentials remain behind CredentialResolver.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _load_local_dotenv() -> None:
    """Load a local .env file without overriding explicit process variables.

    The application is often run directly with Uvicorn during local development.
    Docker Compose injects environment variables itself, so this loader only fills
    values that are not already present in the process environment.
    """
    env_file = Path(__file__).resolve().parents[2] / ".env"
    if not env_file.is_file():
        return

    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip()
        if not name or name in os.environ:
            continue

        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ[name] = value


_load_local_dotenv()


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
