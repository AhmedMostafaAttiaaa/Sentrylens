"""Regex-based PII detection.

Deliberately dependency-free so it always runs, even in minimal
deployments. Detects the most common PII shapes; for stricter compliance
needs, swap in a dedicated model (for example Presidio) behind the same
interface.
"""

from __future__ import annotations

import re

_PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "phone": re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
}


def detect_pii(text: str) -> list[str]:
    found = []
    for label, pattern in _PATTERNS.items():
        if pattern.search(text):
            found.append(label)
    return found


def redact_pii(text: str) -> str:
    redacted = text
    for label, pattern in _PATTERNS.items():
        redacted = pattern.sub(f"[REDACTED_{label.upper()}]", redacted)
    return redacted
