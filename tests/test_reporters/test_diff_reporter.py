"""Tests for diff reporter."""

from __future__ import annotations

import json

import pytest

from ai_bom.models import (
    AIComponent,
    ComponentType,
    RiskAssessment,
    ScanResult,
    Severity,
    SourceLocation,
)
from ai_bom.reporters.diff_reporter import (
    compare_scans,
    format_diff_as_json,
    format_diff_as_markdown,
    format_diff_as_table,
    load_scan_from_file,
)


@pytest.fixture
def baseline_scan() -> ScanResult:
    """Create a baseline scan result."""
    return ScanResult(
        target_path="/test/project",
        components=[
            AIComponent(
                name="openai",
                type=ComponentType.llm_provider,
                provider="OpenAI",
                location=SourceLocation(file_path="app.py"),
                risk=RiskAssessment(score=30, severity=Severity.medium),
            ),
            AIComponent(
                name="langchain",
                type=ComponentType.agent_framework,
                provider="LangChain",
                location=SourceLocation(file_path="agent.py"),
                risk=RiskAssessment(score=20, severity=Severity.low),
            ),
        ],
    )


@pytest.fixture
def current_scan() -> ScanResult:
    """Create a current scan result with changes."""
    return ScanResult(
        target_path="/test/project",
        components=[
            AIComponent(
                name="openai",
                type=ComponentType.llm_provider,
                provider="OpenAI",
                location=SourceLocation(file_path="app.py"),
                risk=RiskAssessment(score=50, severity=Severity.high),  # Risk increased
            ),
            AIComponent(
                name="anthropic",
                type=ComponentType.llm_provider,
                provider="Anthropic",
                location=SourceLocation(file_path="app.py"),
                risk=RiskAssessment(score=25, severity=Severity.medium),  # New component
            ),
        ],
    )


def test_compare_scans_added_component(baseline_scan, current_scan):
    """Test detection of added components."""
    diff = compare_scans(baseline_scan, current_scan)
    assert len(diff.added_components) == 1
    assert diff.added_components[0]["name"] == "anthropic"
    assert diff.added_components[0]["provider"] == "Anthropic"


def test_compare_scans_removed_component(baseline_scan, current_scan):
    """Test detection of removed components."""
    diff = compare_scans(baseline_scan, current_scan)
    assert len(diff.removed_components) == 1
    assert diff.removed_components[0]["name"] == "langchain"
    assert diff.removed_components[0]["provider"] == "LangChain"


def test_compare_scans_modified_component(baseline_scan, current_scan):
    """Test detection of modified components with risk changes."""
    diff = compare_scans(baseline_scan, current_scan)
    assert len(diff.modified_components) == 1
    modified = diff.modified_components[0]
    assert modified["name"] == "openai"
    assert modified["old_risk_score"] == 30
    assert modified["new_risk_score"] == 50
    assert modified["old_severity"] == "medium"
    assert modified["new_severity"] == "high"


def test_compare_scans_risk_score_changes(baseline_scan, current_scan):
    """Test risk score changes tracking."""
    diff = compare_scans(baseline_scan, current_scan)
    assert len(diff.risk_score_changes) == 1
    change = diff.risk_score_changes[0]
    assert change["name"] == "openai"
    assert change["old"] == 30
    assert change["new"] == 50
    assert change["change"] == 20


def test_format_diff_as_table(baseline_scan, current_scan):
    """Test formatting diff as table."""
    diff = compare_scans(baseline_scan, current_scan)
    output = format_diff_as_table(diff)
    assert "SCAN COMPARISON REPORT" in output
    assert "ADDED COMPONENTS" in output
    assert "REMOVED COMPONENTS" in output
    assert "MODIFIED COMPONENTS" in output
    assert "anthropic" in output
    assert "langchain" in output
    assert "openai" in output


def test_format_diff_as_markdown(baseline_scan, current_scan):
    """Test formatting diff as markdown."""
    diff = compare_scans(baseline_scan, current_scan)
    output = format_diff_as_markdown(diff)
    assert "# Scan Comparison Report" in output
    assert "## Added Components" in output
    assert "## Removed Components" in output
    assert "## Modified Components" in output
    assert "**anthropic**" in output
    assert "**langchain**" in output


def test_format_diff_as_json(baseline_scan, current_scan):
    """Test formatting diff as JSON."""
    diff = compare_scans(baseline_scan, current_scan)
    output = format_diff_as_json(diff)
    data = json.loads(output)
    assert "summary" in data
    assert data["summary"]["added"] == 1
    assert data["summary"]["removed"] == 1
    assert data["summary"]["modified"] == 1
    assert len(data["added_components"]) == 1
    assert len(data["removed_components"]) == 1
    assert len(data["modified_components"]) == 1


def test_load_scan_from_file(tmp_path):
    """Test loading scan from JSON file."""
    scan = ScanResult(
        target_path="/test",
        components=[
            AIComponent(
                name="test",
                type=ComponentType.llm_provider,
                location=SourceLocation(file_path="test.py"),
            )
        ],
    )
    scan_file = tmp_path / "scan.json"
    scan_file.write_text(scan.model_dump_json())

    loaded = load_scan_from_file(scan_file)
    assert loaded.target_path == "/test"
    assert len(loaded.components) == 1
    assert loaded.components[0].name == "test"


def test_load_scan_from_file_not_found():
    """Test loading from non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        load_scan_from_file("/nonexistent/file.json")


def test_load_scan_cyclonedx_format_error(tmp_path):
    """Test that CycloneDX format raises error."""
    scan_file = tmp_path / "scan.json"
    scan_file.write_text(json.dumps({"bomFormat": "CycloneDX"}))

    with pytest.raises(ValueError, match="CycloneDX format not supported"):
        load_scan_from_file(scan_file)


def test_compare_scans_no_changes():
    """Test comparing identical scans."""
    scan = ScanResult(
        target_path="/test",
        components=[
            AIComponent(
                name="test",
                type=ComponentType.llm_provider,
                provider="OpenAI",
                location=SourceLocation(file_path="test.py"),
                risk=RiskAssessment(score=30, severity=Severity.medium),
            )
        ],
    )
    diff = compare_scans(scan, scan)
    assert len(diff.added_components) == 0
    assert len(diff.removed_components) == 0
    assert len(diff.modified_components) == 0


def test_compare_scans_empty():
    """Test comparing empty scans."""
    scan1 = ScanResult(target_path="/test1", components=[])
    scan2 = ScanResult(target_path="/test2", components=[])
    diff = compare_scans(scan1, scan2)
    assert len(diff.added_components) == 0
    assert len(diff.removed_components) == 0
    assert len(diff.modified_components) == 0
