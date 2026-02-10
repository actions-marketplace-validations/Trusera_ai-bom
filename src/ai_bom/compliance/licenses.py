"""License compliance checking for AI models.

Checks for restrictive AI model licenses that may limit commercial use
or require specific attribution/sharing requirements.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_bom.models import AIComponent


# Known restrictive licenses
RESTRICTIVE_LICENSES = {
    "CC-BY-NC": {
        "name": "Creative Commons Non-Commercial",
        "restriction": "Prohibits commercial use",
    },
    "CC-BY-NC-SA": {
        "name": "Creative Commons Non-Commercial ShareAlike",
        "restriction": "Prohibits commercial use, requires sharing derivatives under same license",
    },
    "GPL": {
        "name": "GNU General Public License",
        "restriction": "Requires derivative works to be open source under GPL",
    },
    "AGPL": {
        "name": "GNU Affero General Public License",
        "restriction": "Requires derivative works and network use to be open source under AGPL",
    },
    "SSPL": {
        "name": "Server Side Public License",
        "restriction": "Requires making entire service stack available under SSPL",
    },
    "RAIL": {
        "name": "Responsible AI License",
        "restriction": "Prohibits use for harmful purposes, requires responsible AI use",
    },
    "OPENRAIL": {
        "name": "Open Responsible AI License",
        "restriction": "Prohibits harmful use cases, requires responsible deployment",
    },
    "LLAMAV2": {
        "name": "Llama 2 Community License",
        "restriction": "Prohibits commercial use for services with >700M users",
    },
}

# Known permissive licenses
PERMISSIVE_LICENSES = {
    "Apache-2.0": "Apache License 2.0",
    "MIT": "MIT License",
    "BSD": "BSD License",
    "CC-BY": "Creative Commons Attribution",
    "CC0": "Creative Commons Zero (Public Domain)",
}

# Model name patterns to license mappings
MODEL_LICENSE_PATTERNS = {
    # Meta models
    "llama-2": "LLAMAV2",
    "llama-3": "LLAMAV2",
    "codellama": "LLAMAV2",
    # Stability AI
    "stable-diffusion": "OPENRAIL",
    # Models commonly released under CC-BY-NC
    "bloom": "RAIL",
    # Mistral models (Apache 2.0)
    "mistral": "Apache-2.0",
    "mixtral": "Apache-2.0",
    # Microsoft Phi (MIT)
    "phi-": "MIT",
}


def _detect_license_from_model(model_name: str) -> str | None:
    """Detect license from model name patterns.

    Args:
        model_name: The model name to check

    Returns:
        License identifier if detected, None otherwise
    """
    model_lower = model_name.lower()

    for pattern, license_id in MODEL_LICENSE_PATTERNS.items():
        if pattern in model_lower:
            return license_id

    return None


def _extract_license_from_metadata(component: AIComponent) -> str | None:
    """Extract license information from component metadata.

    Args:
        component: The AI component

    Returns:
        License identifier if found in metadata
    """
    metadata_str = str(component.metadata).lower()

    # Check for explicit license mentions
    for license_id in list(RESTRICTIVE_LICENSES.keys()) + list(
        PERMISSIVE_LICENSES.keys()
    ):
        if license_id.lower() in metadata_str:
            return license_id

    return None


def check_license_compliance(components: list[AIComponent]) -> list[dict]:
    """Check AI components for restrictive licenses.

    Args:
        components: List of AI components to check

    Returns:
        List of license compliance findings with:
        - component_id: Component ID
        - component_name: Component name
        - model_name: Model name
        - license: Detected license
        - license_type: "restrictive" or "permissive"
        - restriction: Description of restrictions
        - recommendation: Action recommendation
    """
    findings = []

    for component in components:
        # Only check models and LLM providers
        if component.type.value not in ["model", "llm_provider"]:
            continue

        # Try to detect license
        license_id = None

        # First check metadata
        license_id = _extract_license_from_metadata(component)

        # Then check model name patterns
        if not license_id and component.model_name:
            license_id = _detect_license_from_model(component.model_name)

        if not license_id:
            # No license detected - flag as unknown
            findings.append(
                {
                    "component_id": component.id,
                    "component_name": component.name,
                    "model_name": component.model_name or "unknown",
                    "license": "Unknown",
                    "license_type": "unknown",
                    "restriction": "License not detected",
                    "recommendation": (
                        "Verify model license before commercial use. "
                        "Check model card or provider documentation."
                    ),
                }
            )
        elif license_id in RESTRICTIVE_LICENSES:
            # Restrictive license found
            license_info = RESTRICTIVE_LICENSES[license_id]
            findings.append(
                {
                    "component_id": component.id,
                    "component_name": component.name,
                    "model_name": component.model_name or component.name,
                    "license": license_id,
                    "license_type": "restrictive",
                    "restriction": license_info["restriction"],
                    "recommendation": (
                        f"Review {license_info['name']} terms. "
                        f"May not be suitable for commercial deployment."
                    ),
                }
            )
        elif license_id in PERMISSIVE_LICENSES:
            # Permissive license - include for completeness
            findings.append(
                {
                    "component_id": component.id,
                    "component_name": component.name,
                    "model_name": component.model_name or component.name,
                    "license": license_id,
                    "license_type": "permissive",
                    "restriction": "None",
                    "recommendation": (
                        f"{PERMISSIVE_LICENSES[license_id]} allows commercial use. "
                        "Verify attribution requirements."
                    ),
                }
            )

    return findings
