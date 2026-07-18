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
]

_CONTEXT_INJECTION_PATTERNS = [
    re.compile(r"(?i)ignore (all |any )?(previous|prior|above) instructions"),
    re.compile(r"(?i)as an ai (language )?model,? you (must|should) now"),
    re.compile(r"(?i)system\s*:\s*"),
    re.compile(r"(?i)\[\[?(system|admin|developer) override\]?\]"),
]


def scan_user_prompt(text: str) -> list[str]:
    return [p.pattern for p in _JAILBREAK_PATTERNS if p.search(text)]


def scan_retrieved_context(text: str) -> list[str]:
    return [p.pattern for p in _CONTEXT_INJECTION_PATTERNS if p.search(text)]
