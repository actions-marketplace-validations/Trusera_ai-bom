"""Enforcement mode for Trusera policy interceptor."""

from __future__ import annotations

from enum import Enum


class EnforcementMode(str, Enum):
    """Enforcement mode determines what happens when a policy violation is detected.

    - BLOCK: Raise ``PolicyViolationError`` and prevent the action.
    - WARN:  Log a warning and allow the action to proceed.
    - LOG:   Silently record the violation and allow the action.
    """

    BLOCK = "block"
    WARN = "warn"
    LOG = "log"

    @classmethod
    def from_string(cls, value: str) -> EnforcementMode:
        """Parse a string into an EnforcementMode (case-insensitive).

        Raises:
            ValueError: If the value is not a valid enforcement mode.
        """
        try:
            return cls(value.lower())
        except ValueError:
            valid = ", ".join(f"'{m.value}'" for m in cls)
            raise ValueError(
                f"Invalid enforcement mode: '{value}'. Must be one of {valid}"
            ) from None
