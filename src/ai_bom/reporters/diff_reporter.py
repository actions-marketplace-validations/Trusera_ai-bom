"""Diff reporter for comparing two scan results.

Compares two ScanResult objects or JSON files and shows differences in:
- Components added/removed
- Risk score changes
- New/resolved security findings
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai_bom.models import ScanResult


class DiffResult:
    """Container for scan comparison results."""

    def __init__(self) -> None:
        self.added_components: list[dict[str, Any]] = []
        self.removed_components: list[dict[str, Any]] = []
        self.modified_components: list[dict[str, Any]] = []
        self.risk_score_changes: list[dict[str, Any]] = []


def load_scan_from_file(file_path: str | Path) -> ScanResult:
    """Load a ScanResult from a JSON file.

    Args:
        file_path: Path to the JSON scan file

    Returns:
        ScanResult object

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is not valid JSON or missing required fields
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Scan file not found: {file_path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Handle both raw ScanResult JSON and CycloneDX format
    if "bomFormat" in data:
        raise ValueError("CycloneDX format not supported for diff. Use JSON scan output instead.")

    return ScanResult.model_validate(data)


def compare_scans(scan1: ScanResult, scan2: ScanResult) -> DiffResult:
    """Compare two scan results.

    Args:
        scan1: The first (baseline) scan result
        scan2: The second (current) scan result

    Returns:
        DiffResult containing the differences
    """
    result = DiffResult()

    # Build component maps by name+type for easier comparison
    scan1_map = {(c.name, c.type.value, c.provider): c for c in scan1.components}
    scan2_map = {(c.name, c.type.value, c.provider): c for c in scan2.components}

    scan1_keys = set(scan1_map.keys())
    scan2_keys = set(scan2_map.keys())

    # Find added components
    for key in scan2_keys - scan1_keys:
        component = scan2_map[key]
        result.added_components.append(
            {
                "name": component.name,
                "type": component.type.value,
                "provider": component.provider,
                "risk_score": component.risk.score,
                "severity": component.risk.severity.value,
                "location": component.location.file_path,
            }
        )

    # Find removed components
    for key in scan1_keys - scan2_keys:
        component = scan1_map[key]
        result.removed_components.append(
            {
                "name": component.name,
                "type": component.type.value,
                "provider": component.provider,
                "risk_score": component.risk.score,
                "severity": component.risk.severity.value,
                "location": component.location.file_path,
            }
        )

    # Find modified components (risk score changes)
    for key in scan1_keys & scan2_keys:
        comp1 = scan1_map[key]
        comp2 = scan2_map[key]

        if comp1.risk.score != comp2.risk.score or comp1.risk.severity != comp2.risk.severity:
            result.modified_components.append(
                {
                    "name": comp2.name,
                    "type": comp2.type.value,
                    "provider": comp2.provider,
                    "old_risk_score": comp1.risk.score,
                    "new_risk_score": comp2.risk.score,
                    "old_severity": comp1.risk.severity.value,
                    "new_severity": comp2.risk.severity.value,
                    "location": comp2.location.file_path,
                }
            )
            result.risk_score_changes.append(
                {
                    "name": comp2.name,
                    "change": comp2.risk.score - comp1.risk.score,
                    "old": comp1.risk.score,
                    "new": comp2.risk.score,
                }
            )

    return result


def format_diff_as_table(diff: DiffResult) -> str:
    """Format diff result as a text table.

    Args:
        diff: The diff result to format

    Returns:
        Formatted string table
    """
    lines = []
    lines.append("=" * 80)
    lines.append("SCAN COMPARISON REPORT")
    lines.append("=" * 80)
    lines.append("")

    # Summary
    lines.append("Summary:")
    lines.append(f"  Added:    {len(diff.added_components)} components")
    lines.append(f"  Removed:  {len(diff.removed_components)} components")
    lines.append(f"  Modified: {len(diff.modified_components)} components")
    lines.append("")

    # Added components
    if diff.added_components:
        lines.append("-" * 80)
        lines.append("ADDED COMPONENTS")
        lines.append("-" * 80)
        for comp in diff.added_components:
            lines.append(
                f"  + {comp['name']} ({comp['type']}) - "
                f"Risk: {comp['risk_score']} ({comp['severity'].upper()})"
            )
            lines.append(f"    Location: {comp['location']}")
        lines.append("")

    # Removed components
    if diff.removed_components:
        lines.append("-" * 80)
        lines.append("REMOVED COMPONENTS")
        lines.append("-" * 80)
        for comp in diff.removed_components:
            lines.append(
                f"  - {comp['name']} ({comp['type']}) - "
                f"Risk: {comp['risk_score']} ({comp['severity'].upper()})"
            )
            lines.append(f"    Location: {comp['location']}")
        lines.append("")

    # Modified components
    if diff.modified_components:
        lines.append("-" * 80)
        lines.append("MODIFIED COMPONENTS (Risk Score Changes)")
        lines.append("-" * 80)
        for comp in diff.modified_components:
            change = comp["new_risk_score"] - comp["old_risk_score"]
            direction = "increased" if change > 0 else "decreased"
            lines.append(
                f"  ~ {comp['name']} ({comp['type']}) - "
                f"Risk {direction}: {comp['old_risk_score']} -> {comp['new_risk_score']}"
            )
            lines.append(
                f"    Severity: {comp['old_severity'].upper()} -> {comp['new_severity'].upper()}"
            )
            lines.append(f"    Location: {comp['location']}")
        lines.append("")

    lines.append("=" * 80)
    return "\n".join(lines)


def format_diff_as_markdown(diff: DiffResult) -> str:
    """Format diff result as Markdown.

    Args:
        diff: The diff result to format

    Returns:
        Formatted Markdown string
    """
    lines = []
    lines.append("# Scan Comparison Report\n")

    # Summary
    lines.append("## Summary\n")
    lines.append(f"- **Added:** {len(diff.added_components)} components")
    lines.append(f"- **Removed:** {len(diff.removed_components)} components")
    lines.append(f"- **Modified:** {len(diff.modified_components)} components\n")

    # Added components
    if diff.added_components:
        lines.append("## Added Components\n")
        for comp in diff.added_components:
            lines.append(
                f"- **{comp['name']}** ({comp['type']}) - "
                f"Risk: {comp['risk_score']} ({comp['severity'].upper()})"
            )
            lines.append(f"  - Location: `{comp['location']}`")
        lines.append("")

    # Removed components
    if diff.removed_components:
        lines.append("## Removed Components\n")
        for comp in diff.removed_components:
            lines.append(
                f"- **{comp['name']}** ({comp['type']}) - "
                f"Risk: {comp['risk_score']} ({comp['severity'].upper()})"
            )
            lines.append(f"  - Location: `{comp['location']}`")
        lines.append("")

    # Modified components
    if diff.modified_components:
        lines.append("## Modified Components\n")
        for comp in diff.modified_components:
            change = comp["new_risk_score"] - comp["old_risk_score"]
            direction = "increased" if change > 0 else "decreased"
            emoji = ":warning:" if change > 0 else ":white_check_mark:"
            lines.append(
                f"- {emoji} **{comp['name']}** ({comp['type']}) - "
                f"Risk {direction}: {comp['old_risk_score']} → {comp['new_risk_score']}"
            )
            lines.append(
                f"  - Severity: {comp['old_severity'].upper()} → {comp['new_severity'].upper()}"
            )
            lines.append(f"  - Location: `{comp['location']}`")
        lines.append("")

    return "\n".join(lines)


def format_diff_as_json(diff: DiffResult) -> str:
    """Format diff result as JSON.

    Args:
        diff: The diff result to format

    Returns:
        JSON string
    """
    data = {
        "summary": {
            "added": len(diff.added_components),
            "removed": len(diff.removed_components),
            "modified": len(diff.modified_components),
        },
        "added_components": diff.added_components,
        "removed_components": diff.removed_components,
        "modified_components": diff.modified_components,
        "risk_score_changes": diff.risk_score_changes,
    }
    return json.dumps(data, indent=2)
