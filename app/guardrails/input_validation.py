"""Basic structural validation applied to every incoming user message."""

from __future__ import annotations


def validate_input(text: str, max_chars: int) -> list[str]:
    issues = []
    if not text or not text.strip():
        issues.append("empty_input")
    if len(text) > max_chars:
        issues.append("input_too_long")
    if "\x00" in text:
        issues.append("null_byte_detected")
    return issues
