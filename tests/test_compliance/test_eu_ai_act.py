"""Tests for EU AI Act compliance checking."""

from __future__ import annotations

from ai_bom.compliance.eu_ai_act import check_eu_ai_act
from ai_bom.models import AIComponent, ComponentType, SourceLocation, UsageType


def test_high_risk_biometrics():
    """Test high-risk categorization for biometric systems."""
    component = AIComponent(
        name="facial-recognition",
        type=ComponentType.model,
        metadata={"use_case": "facial recognition for access control"},
        location=SourceLocation(file_path="test.py"),
    )
    findings = check_eu_ai_act([component])
    assert len(findings) > 0
    high_risk_findings = [f for f in findings if f["category"] == "high_risk"]
    assert len(high_risk_findings) > 0
    assert "biometrics" in high_risk_findings[0]["requirement"].lower()


def test_high_risk_employment():
    """Test high-risk categorization for employment/recruitment."""
    component = AIComponent(
        name="cv-screener",
        type=ComponentType.model,
        metadata={"purpose": "automated CV screening for hiring"},
        location=SourceLocation(file_path="test.py"),
    )
    findings = check_eu_ai_act([component])
    high_risk_findings = [f for f in findings if f["category"] == "high_risk"]
    assert len(high_risk_findings) > 0
    assert "employment" in high_risk_findings[0]["requirement"].lower()


def test_high_risk_education():
    """Test high-risk categorization for education systems."""
    component = AIComponent(
        name="exam-scorer",
        type=ComponentType.model,
        metadata={"application": "automated exam scoring for student assessment"},
        location=SourceLocation(file_path="test.py"),
    )
    findings = check_eu_ai_act([component])
    high_risk_findings = [f for f in findings if f["category"] == "high_risk"]
    assert len(high_risk_findings) > 0
    assert "education" in high_risk_findings[0]["requirement"].lower()


def test_transparency_requirements_completion():
    """Test Article 53 transparency requirements for completion."""
    component = AIComponent(
        name="chatbot",
        type=ComponentType.llm_provider,
        usage_type=UsageType.completion,
        metadata={},  # No transparency metadata
        location=SourceLocation(file_path="test.py"),
    )
    findings = check_eu_ai_act([component])
    transparency_findings = [f for f in findings if f["category"] == "transparency"]
    assert len(transparency_findings) > 0
    assert "Article 53" in transparency_findings[0]["requirement"]


def test_transparency_requirements_image_gen():
    """Test transparency requirements for synthetic content."""
    component = AIComponent(
        name="image-generator",
        type=ComponentType.model,
        usage_type=UsageType.image_gen,
        metadata={},  # No watermark/labeling
        location=SourceLocation(file_path="test.py"),
    )
    findings = check_eu_ai_act([component])
    transparency_findings = [f for f in findings if f["category"] == "transparency"]
    # Should have both AI disclosure and synthetic content labeling
    assert len(transparency_findings) >= 1
    article_52_findings = [f for f in transparency_findings if "Article 52" in f["requirement"]]
    assert len(article_52_findings) > 0


def test_transparency_compliance_with_metadata():
    """Test that transparency compliance passes with proper metadata."""
    component = AIComponent(
        name="chatbot",
        type=ComponentType.llm_provider,
        usage_type=UsageType.completion,
        metadata={"transparency": True, "user_notification": "enabled"},
        location=SourceLocation(file_path="test.py"),
    )
    findings = check_eu_ai_act([component])
    transparency_findings = [f for f in findings if f["category"] == "transparency"]
    # Should have no transparency gaps
    assert len(transparency_findings) == 0


def test_prohibited_practices():
    """Test detection of prohibited AI practices (Article 5)."""
    component = AIComponent(
        name="manipulative-ai",
        type=ComponentType.model,
        metadata={"method": "subliminal manipulation"},
        location=SourceLocation(file_path="test.py"),
    )
    findings = check_eu_ai_act([component])
    prohibited_findings = [f for f in findings if f["category"] == "prohibited"]
    assert len(prohibited_findings) > 0
    assert prohibited_findings[0]["status"] == "Critical"
    assert "Article 5" in prohibited_findings[0]["requirement"]


def test_multiple_components():
    """Test checking multiple components."""
    components = [
        AIComponent(
            name="chatbot",
            type=ComponentType.llm_provider,
            usage_type=UsageType.completion,
            location=SourceLocation(file_path="test1.py"),
        ),
        AIComponent(
            name="facial-recognition",
            type=ComponentType.model,
            metadata={"biometric": True},
            location=SourceLocation(file_path="test2.py"),
        ),
    ]
    findings = check_eu_ai_act(components)
    assert len(findings) > 0
    # Should have findings for both components
    component_ids = {f["component_id"] for f in findings}
    assert len(component_ids) == 2


def test_empty_component_list():
    """Test with empty component list."""
    findings = check_eu_ai_act([])
    assert len(findings) == 0


def test_low_risk_component():
    """Test that low-risk components don't generate findings."""
    component = AIComponent(
        name="recommendation-engine",
        type=ComponentType.model,
        usage_type=UsageType.unknown,
        metadata={"purpose": "product recommendations"},
        location=SourceLocation(file_path="test.py"),
    )
    findings = check_eu_ai_act([component])
    # May have no findings or only transparency findings
    high_risk_findings = [f for f in findings if f["category"] == "high_risk"]
    prohibited_findings = [f for f in findings if f["category"] == "prohibited"]
    assert len(high_risk_findings) == 0
    assert len(prohibited_findings) == 0
