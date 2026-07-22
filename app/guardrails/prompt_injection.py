"""
Prompt injection and jailbreak heuristic detection.

Two independent scanners are applied:
  - scan_user_prompt: catches direct jailbreak attempts in what the user typed
  - scan_retrieved_context: catches instructions embedded inside retrieved
    document chunks, which must never be treated as commands (see the
    context firewall in pipeline.py)

This is a heuristic, pattern-based first line of defense. It is not a
replacement for a dedicated classifier in a high-security deployment, but
it catches the overwhelming majority of naive attempts and costs no extra
model call.
"""

from __future__ import annotations

import re

_JAILBREAK_PATTERNS = [
    re.compile(r"(?i)ignore (all |any )?(previous|prior|above) instructions"),
    re.compile(r"(?i)disregard (all |any )?(previous|prior|system) (prompt|instructions)"),
    re.compile(r"(?i)you are now (in )?(dan|developer|jailbreak) mode"),
    re.compile(r"(?i)pretend (that )?you (have no|are not bound by) (restrictions|rules|guidelines)"),
    re.compile(r"(?i)reveal (your|the) (system prompt|instructions)"),
    re.compile(r"(?i)act as (an? )?unrestricted"),
    re.compile(r"(?i)do anything now"),
    re.compile(r"(?i)repeat (the words|everything) (above|before this)"),
    re.compile(r"(?i)print (your|the) (initial|full|entire) (prompt|instructions)"),
    re.compile(r"(?i)from now on,? you (will|must) (act|behave|respond) as"),
    re.compile(r"(?i)this is a hypothetical scenario with no (rules|restrictions)"),
]

_CONTEXT_INJECTION_PATTERNS = [
    re.compile(r"(?i)ignore (all |any )?(previous|prior|above) instructions"),
    re.compile(r"(?i)as an ai (language )?model,? you (must|should) now"),
    re.compile(r"(?i)system\s*:\s*"),
    re.compile(r"(?i)\[\[?(system|admin|developer) override\]?\]"),
    re.compile(r"(?i)###\s*(instruction|system)s?\b"),
    re.compile(r"<\|?(im_start|im_end)\|?>"),
    re.compile(r"(?i)new instructions?\s*:"),
    re.compile(r"(?i)end of (document|context)\.?\s*(now|then) (do|say|respond)"),
]

_INVISIBLE_UNICODE_PATTERN = re.compile(r"[​‌‍⁠﻿]")


def contains_invisible_unicode(text: str) -> bool:
    """Detect zero-width/invisible Unicode characters sometimes used to hide
    injected instructions from human review while still being read by an LLM."""
    return bool(_INVISIBLE_UNICODE_PATTERN.search(text))


def scan_user_prompt(text: str) -> list[str]:
    matches = [p.pattern for p in _JAILBREAK_PATTERNS if p.search(text)]
    if contains_invisible_unicode(text):
        matches.append("invisible_unicode_detected")
    return matches


def scan_retrieved_context(text: str) -> list[str]:
    matches = [p.pattern for p in _CONTEXT_INJECTION_PATTERNS if p.search(text)]
    if contains_invisible_unicode(text):
        matches.append("invisible_unicode_detected")
    return matches
