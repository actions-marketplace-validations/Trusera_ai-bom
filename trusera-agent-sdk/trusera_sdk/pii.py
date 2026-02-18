"""PII redaction utilities for Trusera SDK interceptor."""

from __future__ import annotations

import re
from typing import Any

# Compiled PII detection patterns
_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("EMAIL", re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")),
    ("PHONE", re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")),
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    (
        "CREDIT_CARD",
        re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
    ),
    ("IPV4", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
]


class PIIRedactor:
    """Redacts personally identifiable information from text and data structures.

    Detected patterns: email addresses, US phone numbers, SSNs,
    credit card numbers, and IPv4 addresses.

    The redactor replaces matches with ``[REDACTED_<TYPE>]`` tokens so that
    the type of PII is still visible in logs without exposing the actual value.
    """

    def __init__(self, extra_patterns: dict[str, str] | None = None) -> None:
        """Initialize with optional extra regex patterns.

        Args:
            extra_patterns: Mapping of label to regex string for custom PII
                            patterns (e.g. ``{"EMPLOYEE_ID": r"EMP-\\d{6}"}``).
        """
        self._patterns = list(_PATTERNS)
        if extra_patterns:
            for label, pattern_str in extra_patterns.items():
                self._patterns.append((label, re.compile(pattern_str)))

    def redact_text(self, text: str) -> str:
        """Replace all detected PII in *text* with redaction tokens."""
        for label, pattern in self._patterns:
            text = pattern.sub(f"[REDACTED_{label}]", text)
        return text

    def redact(self, data: Any) -> Any:
        """Recursively redact PII from dicts, lists, and strings."""
        if isinstance(data, str):
            return self.redact_text(data)
        if isinstance(data, dict):
            return {k: self.redact(v) for k, v in data.items()}
        if isinstance(data, (list, tuple)):
            redacted = [self.redact(item) for item in data]
            return type(data)(redacted)
        return data
