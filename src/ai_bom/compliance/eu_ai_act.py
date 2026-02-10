"""EU AI Act compliance checking.

Checks AI components against EU AI Act requirements including high-risk
categorization and transparency obligations.

Reference: EU Artificial Intelligence Act (2024)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_bom.models import AIComponent


# High-risk AI system categories from EU AI Act Annex III
HIGH_RISK_CATEGORIES = {
    "biometrics": [
        "biometric",
        "facial",
        "face_recognition",
        "emotion_detection",
        "identity_verification",
    ],
    "critical_infrastructure": [
        "infrastructure",
        "power_grid",
        "water_supply",
        "transportation",
    ],
    "education": [
        "education",
        "student_assessment",
        "student",
        "exam_scoring",
        "exam",
        "admission",
    ],
    "employment": [
        "recruitment",
        "hiring",
        "cv_screening",
        "performance_evaluation",
        "employment",
    ],
    "essential_services": [
        "credit_scoring",
        "creditworthiness",
        "insurance",
        "emergency_services",
    ],
    "law_enforcement": [
        "law_enforcement",
        "crime_prediction",
        "risk_assessment",
        "polygraph",
    ],
    "migration": [
        "migration",
        "asylum",
        "border_control",
        "visa",
    ],
    "justice": [
        "legal",
        "court",
        "judicial",
        "law_interpretation",
    ],
}


def _check_high_risk_category(component: AIComponent) -> list[str]:
    """Check if component falls into high-risk AI categories.

    Args:
        component: The AI component to check

    Returns:
        List of high-risk categories matched
    """
    matched_categories = []
    component_text = (
        f"{component.name} {component.metadata} {component.flags} {component.usage_type.value}"
    ).lower()

    for category, keywords in HIGH_RISK_CATEGORIES.items():
        if any(keyword in component_text for keyword in keywords):
            matched_categories.append(category)

    return matched_categories


def _check_transparency_requirements(component: AIComponent) -> list[str]:
    """Check Article 53 transparency requirements.

    Users must be informed when interacting with an AI system.

    Args:
        component: The AI component to check

    Returns:
        List of transparency gaps
    """
    gaps = []

    # Check if transparency/disclosure is mentioned
    has_transparency = any(
        keyword in str(component.metadata).lower()
        for keyword in ["disclosure", "transparency", "user_notification", "ai_notice"]
    )

    # For user-facing AI (chat, completion, image_gen), transparency is critical
    user_facing_types = ["completion", "agent", "image_gen", "speech"]
    if component.usage_type.value in user_facing_types and not has_transparency:
        gaps.append("Missing AI system disclosure to users (Article 53)")

    # Check for deepfake/synthetic content requirements
    if component.usage_type.value in ["image_gen", "speech"]:
        has_watermark = any(
            keyword in str(component.metadata).lower()
            for keyword in ["watermark", "synthetic_label", "ai_generated"]
        )
        if not has_watermark:
            gaps.append("Missing synthetic content labeling (Article 52)")

    return gaps


def check_eu_ai_act(components: list[AIComponent]) -> list[dict]:
    """Check AI components against EU AI Act requirements.

    Args:
        components: List of AI components to evaluate

    Returns:
        List of compliance findings, each containing:
        - component_id: The component ID
        - component_name: The component name
        - category: The compliance category (high_risk, transparency, etc.)
        - requirement: The specific requirement
        - status: Pass or Fail
        - details: Additional context
    """
    findings = []

    for component in components:
        # Check for high-risk categorization
        high_risk_cats = _check_high_risk_category(component)
        if high_risk_cats:
            findings.append(
                {
                    "component_id": component.id,
                    "component_name": component.name,
                    "category": "high_risk",
                    "requirement": f"Annex III - {', '.join(high_risk_cats)}",
                    "status": "Flag",
                    "details": (
                        "Component may constitute a high-risk AI system. "
                        "Additional requirements apply: conformity assessment, "
                        "technical documentation, logging, human oversight."
                    ),
                }
            )

        # Check transparency requirements
        transparency_gaps = _check_transparency_requirements(component)
        for gap in transparency_gaps:
            findings.append(
                {
                    "component_id": component.id,
                    "component_name": component.name,
                    "category": "transparency",
                    "requirement": gap,
                    "status": "Fail",
                    "details": (
                        "EU AI Act requires disclosure when users interact with AI systems."
                    ),
                }
            )

        # Check for prohibited AI practices (Article 5)
        prohibited_indicators = [
            "manipulation",
            "subliminal",
            "exploit_vulnerability",
            "social_scoring",
            "real_time_biometric",
        ]
        component_text = (f"{component.name} {component.metadata} {component.flags}").lower()

        if any(indicator in component_text for indicator in prohibited_indicators):
            findings.append(
                {
                    "component_id": component.id,
                    "component_name": component.name,
                    "category": "prohibited",
                    "requirement": "Article 5 - Prohibited AI Practices",
                    "status": "Critical",
                    "details": (
                        "Component may involve prohibited AI practices under EU AI Act. "
                        "These practices are banned in the EU."
                    ),
                }
            )

    return findings
