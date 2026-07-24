"""
Guardrails pipeline.

Central place where every input/output safety check is composed. Routers
and services call this instead of individual detectors so the set of
active checks is controlled entirely by configuration
(configs/base.yaml -> guardrails).

Context firewall: retrieved document text is only ever scanned for
injected instructions - it is never executed, and any instruction-like
content found in it is stripped before the text is placed into the LLM
prompt. This is what "treat retrieved documents as data, not instructions"
means concretely in this codebase.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.config import Settings
from app.guardrails.input_validation import validate_input
from app.guardrails.output_validation import flag_possible_hallucination, validate_citations
from app.guardrails.pii_detector import detect_pii, redact_pii
from app.guardrails.repetition_detector import detect_excessive_repetition
from app.guardrails.prompt_injection import scan_retrieved_context, scan_user_prompt
from app.guardrails.secrets_detector import detect_secrets
from app.guardrails.toxicity_detector import detect_toxicity
from app.guardrails.url_safety import scan_for_suspicious_urls


@dataclass
class GuardrailReport:
    flags: list[str] = field(default_factory=list)
    sanitized_text: str | None = None
    blocked: bool = False


class GuardrailsPipeline:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings.guardrails

    def check_user_input(self, text: str) -> GuardrailReport:
        flags: list[str] = []
        blocked = False

        if self._settings.input_validation:
            flags.extend(validate_input(text, self._settings.max_input_chars))
            if "input_too_long" in flags or "null_byte_detected" in flags:
                blocked = True

            if detect_excessive_repetition(text):
                flags.append("excessive_repetition_detected")
                blocked = True

        if self._settings.prompt_injection_detection:
            injections = scan_user_prompt(text)
            if injections:
                flags.append("prompt_injection_detected")

            suspicious_urls = scan_for_suspicious_urls(text)
            flags.extend(f"suspicious_url:{kind}" for kind in suspicious_urls)

        if self._settings.pii_detection:
            pii_found = detect_pii(text)
            flags.extend(f"pii:{kind}" for kind in pii_found)

        if self._settings.toxicity_detection:
            toxicity_found = detect_toxicity(text)
            if toxicity_found:
                flags.extend(f"toxicity:{kind}" for kind in toxicity_found)
                blocked = True

        if self._settings.secrets_detection:
            secrets_found = detect_secrets(text)
            if secrets_found:
                flags.extend(f"secret:{kind}" for kind in secrets_found)
                blocked = True

        return GuardrailReport(flags=flags, sanitized_text=text, blocked=blocked)

    def sanitize_retrieved_context(self, chunks_text: list[str]) -> tuple[list[str], list[str]]:
        """Strip instruction-like content out of retrieved chunks before they
        are placed into the prompt. Returns (clean_chunks, flags)."""
        flags: list[str] = []
        clean_chunks: list[str] = []
        for text in chunks_text:
            if self._settings.prompt_injection_detection:
                matches = scan_retrieved_context(text)
                if matches:
                    flags.append("context_injection_detected")
                    for pattern in matches:
                        import re

                        text = re.sub(pattern, "[REMOVED_INSTRUCTION]", text)
            clean_chunks.append(text)
        return clean_chunks, flags

    def check_output(
        self, answer: str, citation_chunk_ids: list[str], retrieved_chunk_ids: set[str], had_context: bool
    ) -> GuardrailReport:
        flags: list[str] = []

        if self._settings.citation_validation:
            invalid = validate_citations(citation_chunk_ids, retrieved_chunk_ids)
            if invalid:
                flags.append("invalid_citation")

        if self._settings.hallucination_check:
            if flag_possible_hallucination(answer, had_context):
                flags.append("possible_hallucination")

        sanitized = answer
        if self._settings.pii_detection:
            pii_found = detect_pii(answer)
            if pii_found:
                flags.extend(f"output_pii:{kind}" for kind in pii_found)
                sanitized = redact_pii(answer)

        return GuardrailReport(flags=flags, sanitized_text=sanitized)
