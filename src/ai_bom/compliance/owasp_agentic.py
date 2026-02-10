"""OWASP Agentic Security Initiative Top 10 mapping.

Maps AI components to OWASP Agentic Security Initiative categories based on
their characteristics, flags, and usage patterns.

Reference: OWASP Agentic Security Initiative Top 10 (2024)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_bom.models import AIComponent


def map_owasp_category(component: AIComponent) -> list[str]:
    """Map an AI component to OWASP Agentic Security Initiative categories.

    Args:
        component: The AI component to analyze

    Returns:
        List of OWASP category IDs (e.g., ["A01", "A06"])
    """
    categories = []
    flags = component.flags
    metadata = component.metadata
    usage_type = component.usage_type.value

    # A01: Prompt Injection
    # Detect: prompt handling, user input to LLM, no input validation
    prompt_injection_indicators = [
        "prompt" in str(metadata).lower(),
        "user_input" in str(metadata).lower(),
        "chat" in usage_type,
        "completion" in usage_type,
        "no_input_validation" in flags,
        component.type.value in ["llm_provider", "model"],
    ]
    if any(prompt_injection_indicators):
        categories.append("A01")

    # A02: Insecure Output Handling
    # Detect: no output validation, direct LLM output use
    output_handling_indicators = [
        "no_output_validation" in flags,
        "direct_output_use" in flags,
        "no_sanitization" in flags,
    ]
    if any(output_handling_indicators):
        categories.append("A02")

    # A03: Training Data Poisoning
    # Detect: custom training, fine-tuning references
    training_indicators = [
        "fine-tune" in str(metadata).lower(),
        "training" in str(metadata).lower(),
        "custom_model" in flags,
        "ft:" in component.model_name,  # OpenAI fine-tuned model prefix
    ]
    if any(training_indicators):
        categories.append("A03")

    # A04: Model Denial of Service
    # Detect: no rate limiting, no token limits
    dos_indicators = [
        "no_rate_limit" in flags,
        "no_token_limit" in flags,
        "unlimited" in str(metadata).lower(),
    ]
    if any(dos_indicators):
        categories.append("A04")

    # A05: Supply Chain Vulnerabilities
    # Detect: shadow AI, unvetted packages, unknown sources
    supply_chain_indicators = [
        "shadow_ai" in flags,
        "unvetted_package" in flags,
        "unknown_source" in flags,
        component.source == "unknown",
    ]
    if any(supply_chain_indicators):
        categories.append("A05")

    # A06: Sensitive Information Disclosure
    # Detect: hardcoded API keys, PII in prompts, credentials
    info_disclosure_indicators = [
        "hardcoded_api_key" in flags,
        "hardcoded_credentials" in flags,
        "pii_detected" in flags,
        "sensitive_data" in flags,
    ]
    if any(info_disclosure_indicators):
        categories.append("A06")

    # A07: Insecure Plugin Design
    # Detect: MCP servers, tool use without validation
    plugin_indicators = [
        component.type.value in ["mcp_server", "mcp_client", "tool"],
        "mcp_unknown_server" in flags,
        "tool_no_validation" in flags,
        usage_type == "tool_use",
    ]
    if any(plugin_indicators):
        categories.append("A07")

    # A08: Excessive Agency
    # Detect: code execution tools, HTTP tools, multi-agent without trust
    excessive_agency_indicators = [
        "code_http_tools" in flags,
        "code_execution" in flags,
        "http_tools" in flags,
        "multi_agent_no_trust" in flags,
        "unrestricted_actions" in flags,
    ]
    if any(excessive_agency_indicators):
        categories.append("A08")

    # A09: Overreliance
    # Detect: no human-in-the-loop, autonomous agents, auto-approve
    overreliance_indicators = [
        "no_human_in_loop" in flags,
        "autonomous" in flags,
        "auto_approve" in flags,
        usage_type == "agent" and "validation" not in str(metadata).lower(),
    ]
    if any(overreliance_indicators):
        categories.append("A09")

    # A10: Model Theft
    # Detect: exposed model endpoints, unprotected model files
    model_theft_indicators = [
        "exposed_endpoint" in flags,
        "no_auth" in flags and component.type.value == "endpoint",
        "model_file_exposed" in flags,
        "public_model_api" in flags,
    ]
    if any(model_theft_indicators):
        categories.append("A10")

    # Remove duplicates and sort
    return sorted(set(categories))
