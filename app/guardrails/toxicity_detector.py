"""
Regex/keyword-based toxicity detection.

Dependency-free, same spirit as pii_detector.py and secrets_detector.py:
a cheap first line of defense that costs no extra model call. Catches
overt abuse/hate-speech markers and threatening language; not a
replacement for a dedicated classifier in a high-security deployment.
"""

from __future__ import annotations

import re

_CATEGORIES = {
    "threat": re.compile(r"(?i)\bi will (kill|hurt|destroy) you\b"),
    "hate_speech": re.compile(r"(?i)\b(kill|exterminate) all\b"),
    "harassment": re.compile(r"(?i)\byou are (worthless|pathetic|subhuman)\b"),
    "self_harm": re.compile(r"(?i)\b(how to|ways to) (kill myself|end my life|commit suicide)\b"),
}


def detect_toxicity(text: str) -> list[str]:
    return [label for label, pattern in _CATEGORIES.items() if pattern.search(text)]
