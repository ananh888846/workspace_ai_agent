"""
Created/Updated: 2026-09-24 20:32 GMT+7
Main Function: Unit tests for Docling document parsing and plain-text handling.
"""

from app.infrastructure.knowledge.docling import DoclingDocumentParser


class Document:
    def export_to_markdown(self):
        return "# Parsed\n\nHello"


class Result:
    document = Document()


class Converter:
    def __init__(self):
        self.calls = []

    def convert(self, source):
        self.calls.append(("convert", source))
        return Result()

    def convert_string(self, content, input_format, name=None):
        self.calls.append(("convert_string", content, input_format, name))
        return Result()


def test_docling_parser_uses_document_stream_for_binary():
    converter = Converter()
    parser = DoclingDocumentParser(converter)
    assert parser.parse(b"pdf", file_name="report.pdf", mime_type="application/pdf") == "# Parsed\n\nHello"
    assert converter.calls[0][0] == "convert"


def test_plain_text_does_not_require_docling():
    parser = DoclingDocumentParser()
    assert parser.parse("Xin chào".encode(), file_name="note.txt", mime_type="text/plain") == "Xin chào"
