"""
LlamaParse-backed parser.

LlamaParse is a paid cloud parsing service that gives much better layout
fidelity than the local parser (true reading order, table structure,
header/footer detection). This class is a thin, isolated adapter: it is
only instantiated when parsing.llamaparse.api_key is set in configuration,
and it degrades to raising a clear error otherwise so the factory can fall
back to LocalDocumentParser.

Kept dependency-free of the actual llama-parse SDK at import time so the
rest of the project runs without it installed; import happens lazily
inside parse().
"""

from __future__ import annotations

from pathlib import Path

from app.parsing.interfaces import DocumentParser, ParsedDocument, ParsedElement


class LlamaParseDocumentParser(DocumentParser):
    supported_extensions = {".pdf", ".docx", ".pptx"}

    def __init__(self, api_key: str, result_type: str = "markdown") -> None:
        if not api_key:
            raise ValueError("LlamaParse API key not configured")
        self._api_key = api_key
        self._result_type = result_type

    async def parse(self, file_path: str, document_id: str) -> ParsedDocument:
        try:
            from llama_parse import LlamaParse
        except ImportError as exc:
            raise RuntimeError(
                "llama-parse package is not installed. Install it or switch "
                "parsing.provider back to 'local' in configs/base.yaml."
            ) from exc

        parser = LlamaParse(api_key=self._api_key, result_type=self._result_type)
        documents = await parser.aload_data(file_path)

        elements: list[ParsedElement] = []
        for doc in documents:
            page = doc.metadata.get("page_number") if hasattr(doc, "metadata") else None
            elements.append(ParsedElement(kind="text", content=doc.text, page=page))

        return ParsedDocument(document_id=document_id, filename=Path(file_path).name, elements=elements)
