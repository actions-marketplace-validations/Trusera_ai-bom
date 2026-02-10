"""Tests for OWASP Agentic Security Initiative mapping."""

from __future__ import annotations

from ai_bom.compliance.owasp_agentic import map_owasp_category
from ai_bom.models import AIComponent, ComponentType, SourceLocation, UsageType


def test_a01_prompt_injection_chat_completion():
    """Test A01: Prompt Injection detection for chat/completion."""
    component = AIComponent(
        name="openai-client",
        type=ComponentType.llm_provider,
        usage_type=UsageType.completion,
        location=SourceLocation(file_path="test.py"),
    )
    categories = map_owasp_category(component)
    assert "A01" in categories


def test_a01_prompt_injection_with_user_input():
    """Test A01: Prompt Injection with user input metadata."""
    component = AIComponent(
        name="chatbot",
        type=ComponentType.model,
        usage_type=UsageType.agent,
        metadata={"user_input": True, "prompt_handling": "direct"},
        location=SourceLocation(file_path="test.py"),
    )
    categories = map_owasp_category(component)
    assert "A01" in categories


def test_a02_insecure_output_handling():
    """Test A02: Insecure Output Handling detection."""
    component = AIComponent(
        name="llm-handler",
        type=ComponentType.llm_provider,
        flags=["no_output_validation", "direct_output_use"],
        location=SourceLocation(file_path="test.py"),
    )
    categories = map_owasp_category(component)
    assert "A02" in categories


def test_a03_training_data_poisoning():
    """Test A03: Training Data Poisoning detection."""
    component = AIComponent(
        name="custom-model",
        type=ComponentType.model,
        model_name="ft:gpt-4-custom",
        metadata={"fine-tuning": True},
        flags=["custom_model"],
        location=SourceLocation(file_path="test.py"),
    )
    categories = map_owasp_category(component)
    assert "A03" in categories


def test_a04_model_denial_of_service():
    """Test A04: Model Denial of Service detection."""
    component = AIComponent(
        name="unlimited-api",
        type=ComponentType.endpoint,
        flags=["no_rate_limit", "no_token_limit"],
        location=SourceLocation(file_path="test.py"),
    )
    categories = map_owasp_category(component)
    assert "A04" in categories


def test_a05_supply_chain_vulnerabilities():
    """Test A05: Supply Chain Vulnerabilities detection."""
    component = AIComponent(
        name="shadow-ai",
        type=ComponentType.llm_provider,
        flags=["shadow_ai", "unvetted_package"],
        location=SourceLocation(file_path="test.py"),
    )
    categories = map_owasp_category(component)
    assert "A05" in categories


def test_a06_sensitive_information_disclosure():
    """Test A06: Sensitive Information Disclosure detection."""
    component = AIComponent(
        name="api-client",
        type=ComponentType.llm_provider,
        flags=["hardcoded_api_key", "hardcoded_credentials"],
        location=SourceLocation(file_path="test.py"),
    )
    categories = map_owasp_category(component)
    assert "A06" in categories


def test_a07_insecure_plugin_design_mcp():
    """Test A07: Insecure Plugin Design for MCP servers."""
    component = AIComponent(
        name="mcp-server",
        type=ComponentType.mcp_server,
        flags=["mcp_unknown_server"],
        location=SourceLocation(file_path="test.py"),
    )
    categories = map_owasp_category(component)
    assert "A07" in categories


def test_a07_insecure_plugin_design_tools():
    """Test A07: Insecure Plugin Design for tools."""
    component = AIComponent(
        name="tool",
        type=ComponentType.tool,
        usage_type=UsageType.tool_use,
        flags=["tool_no_validation"],
        location=SourceLocation(file_path="test.py"),
    )
    categories = map_owasp_category(component)
    assert "A07" in categories


def test_a08_excessive_agency():
    """Test A08: Excessive Agency detection."""
    component = AIComponent(
        name="code-executor",
        type=ComponentType.agent_framework,
        flags=["code_http_tools", "multi_agent_no_trust"],
        location=SourceLocation(file_path="test.py"),
    )
    categories = map_owasp_category(component)
    assert "A08" in categories


def test_a09_overreliance():
    """Test A09: Overreliance detection."""
    component = AIComponent(
        name="autonomous-agent",
        type=ComponentType.agent_framework,
        usage_type=UsageType.agent,
        flags=["no_human_in_loop", "autonomous"],
        location=SourceLocation(file_path="test.py"),
    )
    categories = map_owasp_category(component)
    assert "A09" in categories


def test_a10_model_theft():
    """Test A10: Model Theft detection."""
    component = AIComponent(
        name="exposed-api",
        type=ComponentType.endpoint,
        flags=["exposed_endpoint", "no_auth"],
        location=SourceLocation(file_path="test.py"),
    )
    categories = map_owasp_category(component)
    assert "A10" in categories


def test_multiple_categories():
    """Test component matching multiple OWASP categories."""
    component = AIComponent(
        name="risky-agent",
        type=ComponentType.llm_provider,  # LLM provider triggers A01
        usage_type=UsageType.agent,
        flags=[
            "hardcoded_api_key",  # A06
            "code_http_tools",  # A08
            "no_human_in_loop",  # A09
        ],
        location=SourceLocation(file_path="test.py"),
    )
    categories = map_owasp_category(component)
    assert "A01" in categories  # LLM provider + agent usage triggers A01
    assert "A06" in categories
    assert "A08" in categories
    assert "A09" in categories


def test_no_categories():
    """Test component with no OWASP category matches."""
    component = AIComponent(
        name="safe-component",
        type=ComponentType.container,
        location=SourceLocation(file_path="test.py"),
    )
    categories = map_owasp_category(component)
    assert len(categories) == 0


def test_categories_sorted_and_unique():
    """Test that categories are sorted and deduplicated."""
    component = AIComponent(
        name="test-component",
        type=ComponentType.llm_provider,
        usage_type=UsageType.completion,
        flags=["hardcoded_api_key"],
        location=SourceLocation(file_path="test.py"),
    )
    categories = map_owasp_category(component)
    # Should be sorted
    assert categories == sorted(categories)
    # Should have no duplicates
    assert len(categories) == len(set(categories))
