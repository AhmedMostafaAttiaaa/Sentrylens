"""
Excessive-repetition detection.

Flags inputs dominated by one repeated token or a short repeated phrase -
a common padding/DoS pattern used to inflate context length, bury a
jailbreak instruction inside noise, or waste provider quota. Cheap and
dependency-free, same style as the other heuristic detectors here.
"""

from __future__ import annotations

import re
from collections import Counter

_WORD_PATTERN = re.compile(r"\S+")


def detect_excessive_repetition(text: str, min_length: int = 200, dominance_ratio: float = 0.4) -> bool:
    """Return True if a single word/token accounts for more than
    `dominance_ratio` of all tokens in a text at least `min_length` chars long."""
    if len(text) < min_length:
        return False

    words = _WORD_PATTERN.findall(text.lower())
    if len(words) < 20:
        return False

    counts = Counter(words)
    most_common_word, most_common_count = counts.most_common(1)[0]
    return (most_common_count / len(words)) >= dominance_ratio
