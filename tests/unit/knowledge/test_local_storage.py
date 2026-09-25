"""\nCreated/Updated: 2026-09-24 20:32 GMT+7\nMain Function: Unit tests for local Knowledge asset storage safety and checksum enforcement.\n"""\n\nimport hashlib

import pytest

from app.domain.knowledge.source import KnowledgeAssetRef
from app.infrastructure.storage.local import LocalFileStorage


def asset(key="documents/google/file-1/report.pdf", content=b"hello"):
    return KnowledgeAssetRef(
        asset_type="document",
        file_name="report.pdf",
        mime_type="application/pdf",
        file_size=len(content),
        checksum=hashlib.sha256(content).hexdigest(),
        storage_backend="local",
        storage_key=key,
    )


def test_put_writes_binary_and_gets_it_back(tmp_path):
    storage = LocalFileStorage(tmp_path)
    value = b"hello"
    key = storage.put(asset(content=value), value)
    assert key == "documents/google/file-1/report.pdf"
    assert storage.exists(key)
    assert storage.get(key) == value


def test_put_rejects_checksum_mismatch(tmp_path):
    storage = LocalFileStorage(tmp_path)
    with pytest.raises(ValueError, match="checksum"):
        storage.put(asset(content=b"expected"), b"actual")


def test_storage_key_cannot_escape_root(tmp_path):
    storage = LocalFileStorage(tmp_path)
    with pytest.raises(ValueError, match="escapes|relative"):
        storage.get("../outside.bin")
