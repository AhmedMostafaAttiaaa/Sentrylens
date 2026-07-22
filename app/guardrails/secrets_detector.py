"""Regex-based secrets detection: API keys, tokens, private keys."""

from __future__ import annotations

import re

_PATTERNS = {
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "generic_api_key": re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}"),
    "private_key_block": re.compile(r"-----BEGIN (RSA |EC )?PRIVATE KEY-----"),
    "slack_token": re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"),
    "google_api_key": re.compile(r"AIza[0-9A-Za-z_\-]{35}"),
}


def detect_secrets(text: str) -> list[str]:
    found = []
    for label, pattern in _PATTERNS.items():
        if pattern.search(text):
            found.append(label)
    return found
