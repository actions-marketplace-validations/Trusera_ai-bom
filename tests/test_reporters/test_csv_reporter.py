"""Tests for CSV reporter."""

import csv
import io

from ai_bom.models import (
    AIComponent,
    ComponentType,
    ScanResult,
    SourceLocation,
)
from ai_bom.reporters.csv_reporter import CSVReporter


class TestCSVReporter:
    """Test cases for CSV reporter."""

    def test_renders_valid_csv(self, multi_component_result):
        """Test that output is valid CSV format."""
        reporter = CSVReporter()
        output = reporter.render(multi_component_result)

        # Parse the CSV to ensure it's valid
        reader = csv.reader(io.StringIO(output))
        rows = list(reader)

        assert len(rows) > 0
        # Header + components
        assert len(rows) == len(multi_component_result.components) + 1

    def test_has_correct_headers(self, multi_component_result):
        """Test that CSV has correct column headers."""
        reporter = CSVReporter()
        output = reporter.render(multi_component_result)

        reader = csv.reader(io.StringIO(output))
        headers = next(reader)

        expected_headers = [
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

        assert headers == expected_headers

    def test_component_data_in_rows(self, multi_component_result):
        """Test that component data is correctly mapped to CSV rows."""
        reporter = CSVReporter()
        output = reporter.render(multi_component_result)

        reader = csv.reader(io.StringIO(output))
        next(reader)  # Skip header
        rows = list(reader)

        # Check first component
        first_component = multi_component_result.components[0]
        first_row = rows[0]

        assert first_row[0] == first_component.name
        assert first_row[1] == first_component.type.value
        assert first_row[2] == first_component.provider
        assert str(first_component.risk.score) in first_row[5]

    def test_empty_result(self):
        """Test rendering empty scan result."""
        result = ScanResult(target_path="/empty")
        result.build_summary()

        reporter = CSVReporter()
        output = reporter.render(result)

        reader = csv.reader(io.StringIO(output))
        rows = list(reader)

        # Should have header only
        assert len(rows) == 1

    def test_flags_formatted_correctly(self):
        """Test that flags are comma-separated in CSV."""
        result = ScanResult(target_path="/test")
        result.components.append(
            AIComponent(
                name="Test Component",
                type=ComponentType.llm_provider,
                provider="Test",
                location=SourceLocation(file_path="/test/file.py"),
                flags=["hardcoded_api_key", "shadow_ai", "deprecated_model"],
                source="code",
            )
        )
        result.build_summary()

        reporter = CSVReporter()
        output = reporter.render(result)

        reader = csv.reader(io.StringIO(output))
        next(reader)  # Skip header
        row = next(reader)

        # Flags should be in column 9
        assert "hardcoded_api_key, shadow_ai, deprecated_model" in row[9]

    def test_line_number_empty_when_none(self):
        """Test that line_number field is empty when None."""
        result = ScanResult(target_path="/test")
        result.components.append(
            AIComponent(
                name="Test Component",
                type=ComponentType.llm_provider,
                provider="Test",
                location=SourceLocation(file_path="/test/file.py", line_number=None),
                source="code",
            )
        )
        result.build_summary()

        reporter = CSVReporter()
        output = reporter.render(result)

        reader = csv.reader(io.StringIO(output))
        next(reader)  # Skip header
        row = next(reader)

        # Line number column should be empty
        assert row[8] == ""

    def test_write_to_file(self, multi_component_result, tmp_path):
        """Test writing CSV to file."""
        reporter = CSVReporter()
        path = tmp_path / "report.csv"
        reporter.write(multi_component_result, path)

        assert path.exists()
        content = path.read_text()

        # Verify it's valid CSV
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        assert len(rows) > 1  # Header + data
