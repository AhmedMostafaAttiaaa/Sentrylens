"""Selects the configured document parser, with local parser as safety net."""

from __future__ import annotations

import structlog

from app.core.config import Settings
from app.parsing.interfaces import DocumentParser
from app.parsing.local_parser import LocalDocumentParser

logger = structlog.get_logger(__name__)


def build_document_parser(settings: Settings) -> DocumentParser:
    if settings.parsing.provider == "llamaparse" and settings.parsing.llamaparse.api_key:
        from app.parsing.llamaparse_parser import LlamaParseDocumentParser

        try:
            return LlamaParseDocumentParser(
                api_key=settings.parsing.llamaparse.api_key,
                result_type=settings.parsing.llamaparse.result_type,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("llamaparse_init_failed_falling_back", error=str(exc))

    return LocalDocumentParser()
