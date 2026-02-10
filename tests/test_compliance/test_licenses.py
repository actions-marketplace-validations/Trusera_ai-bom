"""Tests for license compliance checking."""

from __future__ import annotations

from ai_bom.compliance.licenses import check_license_compliance
from ai_bom.models import AIComponent, ComponentType, SourceLocation


def test_restrictive_license_llama():
    """Test detection of Llama 2 restrictive license."""
    component = AIComponent(
        name="llama-model",
        type=ComponentType.model,
        model_name="llama-2-7b",
        location=SourceLocation(file_path="test.py"),
    )
    findings = check_license_compliance([component])
    assert len(findings) > 0
    assert findings[0]["license"] == "LLAMAV2"
    assert findings[0]["license_type"] == "restrictive"
    assert "700M users" in findings[0]["restriction"]


def test_restrictive_license_stable_diffusion():
    """Test detection of Stable Diffusion OpenRAIL license."""
    component = AIComponent(
        name="sd-model",
        type=ComponentType.model,
        model_name="stable-diffusion-v1-5",
        location=SourceLocation(file_path="test.py"),
    )
    findings = check_license_compliance([component])
    assert len(findings) > 0
    assert findings[0]["license"] == "OPENRAIL"
    assert findings[0]["license_type"] == "restrictive"


def test_permissive_license_mistral():
    """Test detection of Mistral permissive license."""
    component = AIComponent(
        name="mistral-model",
        type=ComponentType.model,
        model_name="mistral-7b-instruct",
        location=SourceLocation(file_path="test.py"),
    )
    findings = check_license_compliance([component])
    assert len(findings) > 0
    assert findings[0]["license"] == "Apache-2.0"
    assert findings[0]["license_type"] == "permissive"


def test_permissive_license_phi():
    """Test detection of Microsoft Phi MIT license."""
    component = AIComponent(
        name="phi-model",
        type=ComponentType.model,
        model_name="phi-2",
        location=SourceLocation(file_path="test.py"),
    )
    findings = check_license_compliance([component])
    assert len(findings) > 0
    assert findings[0]["license"] == "MIT"
    assert findings[0]["license_type"] == "permissive"


def test_unknown_license():
    """Test handling of unknown license."""
    component = AIComponent(
        name="unknown-model",
        type=ComponentType.model,
        model_name="custom-model-v1",
        location=SourceLocation(file_path="test.py"),
    )
    findings = check_license_compliance([component])
    assert len(findings) > 0
    assert findings[0]["license"] == "Unknown"
    assert findings[0]["license_type"] == "unknown"
    assert "Verify model license" in findings[0]["recommendation"]


def test_license_from_metadata():
    """Test extracting license from metadata."""
    component = AIComponent(
        name="custom-model",
        type=ComponentType.model,
        metadata={"license": "GPL"},
        location=SourceLocation(file_path="test.py"),
    )
    findings = check_license_compliance([component])
    assert len(findings) > 0
    assert findings[0]["license"] == "GPL"
    assert findings[0]["license_type"] == "restrictive"


def test_non_model_component_skipped():
    """Test that non-model components are skipped."""
    component = AIComponent(
        name="docker-container",
        type=ComponentType.container,
        location=SourceLocation(file_path="test.py"),
    )
    findings = check_license_compliance([component])
    assert len(findings) == 0


def test_llm_provider_checked():
    """Test that LLM providers are checked."""
    component = AIComponent(
        name="openai-client",
        type=ComponentType.llm_provider,
        model_name="gpt-4",
        location=SourceLocation(file_path="test.py"),
    )
    findings = check_license_compliance([component])
    # Should have a finding (likely unknown since we don't specify OpenAI's license)
    assert len(findings) > 0


def test_multiple_components():
    """Test checking multiple components."""
    components = [
        AIComponent(
            name="llama",
            type=ComponentType.model,
            model_name="llama-2-13b",
            location=SourceLocation(file_path="test1.py"),
        ),
        AIComponent(
            name="mistral",
            type=ComponentType.model,
            model_name="mistral-7b",
            location=SourceLocation(file_path="test2.py"),
        ),
    ]
    findings = check_license_compliance(components)
    assert len(findings) == 2
    licenses = {f["license"] for f in findings}
    assert "LLAMAV2" in licenses
    assert "Apache-2.0" in licenses


def test_empty_component_list():
    """Test with empty component list."""
    findings = check_license_compliance([])
    assert len(findings) == 0


def test_codellama_license():
    """Test CodeLlama uses same license as Llama."""
    component = AIComponent(
        name="codellama",
        type=ComponentType.model,
        model_name="codellama-7b",
        location=SourceLocation(file_path="test.py"),
    )
    findings = check_license_compliance([component])
    assert len(findings) > 0
    assert findings[0]["license"] == "LLAMAV2"
