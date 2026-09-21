from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import psycopg

from app.config.settings import get_settings


@contextmanager
def database_connection() -> Iterator[Any]:
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not configured")
    connection = psycopg.connect(settings.database_url)
    try:
        yield connection
    finally:
        connection.close()
