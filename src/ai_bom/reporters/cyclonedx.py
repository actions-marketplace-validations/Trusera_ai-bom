"""CycloneDX JSON reporter."""

from __future__ import annotations

import json

from ai_bom.models import ScanResult
from ai_bom.reporters.base import BaseReporter


class CycloneDXReporter(BaseReporter):
    """Reporter that outputs CycloneDX-compatible JSON format."""

    def render(self, result: ScanResult) -> str:
        """Render scan result as CycloneDX JSON.

        Args:
            result: The scan result to render

        Returns:
            JSON string in CycloneDX format
        """
        return json.dumps(result.to_cyclonedx(), indent=2)
