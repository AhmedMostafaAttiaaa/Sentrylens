"""
Suspicious URL detection.

Flags URL shapes commonly used in phishing/malware delivery and in
prompt-injection payloads that try to get the model to fetch or
recommend a malicious link: raw-IP hosts, punycode/homograph domains,
known URL-shortener redirection, and credential-in-URL patterns.

Dependency-free, same style as pii_detector.py / secrets_detector.py.
"""

from __future__ import annotations

import re

_URL_PATTERN = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
_IP_HOST_PATTERN = re.compile(r"^https?://(\d{1,3}\.){3}\d{1,3}")
_PUNYCODE_PATTERN = re.compile(r"://(?:[^/]*\.)?xn--", re.IGNORECASE)
_CREDENTIALS_IN_URL_PATTERN = re.compile(r"://[^/@\s]+:[^/@\s]+@")
_SHORTENER_DOMAINS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "buff.ly",
}


def _flags_for_url(url: str) -> list[str]:
    flags = []
    if _IP_HOST_PATTERN.search(url):
        flags.append("ip_literal_url")
    if _PUNYCODE_PATTERN.search(url):
        flags.append("punycode_domain")
    if _CREDENTIALS_IN_URL_PATTERN.search(url):
        flags.append("credentials_in_url")
    host = re.sub(r"^https?://", "", url, flags=re.IGNORECASE).split("/")[0].split("@")[-1].lower()
    if host in _SHORTENER_DOMAINS:
        flags.append("url_shortener")
    return flags


def scan_for_suspicious_urls(text: str) -> list[str]:
    """Return the deduplicated set of suspicious-URL flags found in text."""
    found: set[str] = set()
    for url in _URL_PATTERN.findall(text):
        found.update(_flags_for_url(url))
    return sorted(found)
