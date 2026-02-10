"""CSV reporter for AI-BOM scan results."""

from __future__ import annotations

import csv
import io

from ai_bom.models import ScanResult
from ai_bom.reporters.base import BaseReporter


class CSVReporter(BaseReporter):
    """Reporter that generates CSV tabular output."""

    def render(self, result: ScanResult) -> str:
        """Render scan result as CSV.

        Args:
            result: The scan result to render

        Returns:
            CSV formatted string with columns:
            name, type, provider, model_name, version, risk_score,
            severity, file_path, line_number, flags, source
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(
            [
                "name",
                "type",
                "provider",
                "model_name",
                "version",
                "risk_score",
                "severity",
                "file_path",
                "line_number",
                "flags",
                "source",
            ]
        )

        # Write component rows
        for component in result.components:
            writer.writerow(
                [
                    component.name,
                    component.type.value,
                    component.provider,
                    component.model_name,
                    component.version,
                    component.risk.score,
                    component.risk.severity.value,
                    component.location.file_path,
                    component.location.line_number if component.location.line_number else "",
                    ", ".join(component.flags) if component.flags else "",
                    component.source,
                ]
            )

        return output.getvalue()
