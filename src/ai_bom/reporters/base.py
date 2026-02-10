"""Base reporter abstract class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ai_bom.models import ScanResult


class BaseReporter(ABC):
    """Abstract base class for all reporters."""

    @abstractmethod
    def render(self, result: ScanResult) -> str:
        """Render scan result to string format.

        Args:
            result: The scan result to render

        Returns:
            Formatted string representation
        """
        ...

    def write(self, result: ScanResult, path: str | Path) -> None:
        """Write rendered result to file.

        Args:
            result: The scan result to render
            path: Output file path
        """
        content = self.render(result)
        Path(path).write_text(content, encoding="utf-8")
