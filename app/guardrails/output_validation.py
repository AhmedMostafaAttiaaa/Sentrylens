"""
Output-side guardrails: citation validation and a lightweight
hallucination heuristic.

Citation validation checks that every citation referenced in the answer
corresponds to a chunk_id that was actually part of the retrieved context
(never a fabricated source).

The hallucination heuristic flags answers that make confident, specific
claims (numbers, dates, proper nouns) with no supporting retrieved context
at all - a cheap signal, not a proof, that the model may be answering from
parametric memory rather than the provided documents.
"""

from __future__ import annotations

import re

_SPECIFIC_CLAIM_PATTERN = re.compile(r"\b\d{4}\b|\$\d+|\b\d+%\b")


def validate_citations(citation_chunk_ids: list[str], retrieved_chunk_ids: set[str]) -> list[str]:
    return [cid for cid in citation_chunk_ids if cid not in retrieved_chunk_ids]


def flag_possible_hallucination(answer: str, had_context: bool) -> bool:
    if had_context:
        return False
    return bool(_SPECIFIC_CLAIM_PATTERN.search(answer))
