"""
Created/Updated: 2026-09-24 20:32 GMT+7
Main Function: Docling-backed document parser that normalizes supported files into Markdown text.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any


class DoclingDocumentParser:
    """Docling-backed parser implementing the provider-neutral parser seam.

    Docling is imported lazily so the Knowledge unit-test suite can exercise
    contracts without downloading/loading document-processing models.
    """

    def __init__(self, converter: Any | None = None) -> None:
        self._converter = converter

    @property
    def converter(self) -> Any:
        if self._converter is None:
            from docling.document_converter import DocumentConverter

            self._converter = DocumentConverter()
        return self._converter

    def parse(
        self,
        content: bytes,
        *,
        file_name: str,
        mime_type: str | None = None,
    ) -> str:
        if not content:
            return ""
        normalized_mime = (mime_type or "").lower()
        suffix = Path(file_name).suffix.lower()

        if normalized_mime in {"text/plain", "text/csv"} or suffix == ".txt":
            return content.decode("utf-8-sig")

        from docling.datamodel.base_models import DocumentStream, InputFormat

        if normalized_mime == "text/markdown" or suffix in {".md", ".markdown"}:
            result = self.converter.convert_string(
                content.decode("utf-8-sig"), InputFormat.MD, name=file_name
            )
        elif normalized_mime == "text/html" or suffix in {".html", ".htm"}:
            result = self.converter.convert_string(
                content.decode("utf-8-sig"), InputFormat.HTML, name=file_name
            )
        else:
            source = DocumentStream(name=file_name, stream=BytesIO(content))
            result = self.converter.convert(source)

        return result.document.export_to_markdown()
