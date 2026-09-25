"""\nCreated/Updated: 2026-09-24 20:32 GMT+7\nMain Function: Local filesystem storage for Knowledge assets with path-safety and checksum validation.\n"""\n\n"""\nCreated/Updated: 2026-09-24 20:32 GMT+7\nMain Function: Knowledge subsystem implementation or verification code for the Workspace AI Agent.\n"""\n\nfrom __future__ import annotations

import hashlib
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from app.domain.knowledge.source import KnowledgeAssetRef


class LocalFileStorage:
    """Filesystem-backed Knowledge asset storage.

    PostgreSQL stores only the logical storage reference; this adapter owns
    binary bytes. storage_key is always resolved beneath the configured root.
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _safe_path(self, storage_key: str) -> Path:
        if not storage_key or Path(storage_key).is_absolute():
            raise ValueError("storage_key must be a non-empty relative path")
        candidate = (self.root / storage_key).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("storage_key escapes storage root") from exc
        return candidate

    def put(self, asset: KnowledgeAssetRef, content: bytes) -> str:
        if hashlib.sha256(content).hexdigest() != asset.checksum:
            raise ValueError("asset checksum does not match content")
        target = self._safe_path(asset.storage_key)
        target.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(dir=target.parent, delete=False) as tmp:
            tmp.write(content)
            tmp.flush()
            os.fsync(tmp.fileno())
            temporary = Path(tmp.name)
        temporary.replace(target)
        return asset.storage_key

    def get(self, storage_key: str) -> bytes:
        return self._safe_path(storage_key).read_bytes()

    def exists(self, storage_key: str) -> bool:
        return self._safe_path(storage_key).is_file()
