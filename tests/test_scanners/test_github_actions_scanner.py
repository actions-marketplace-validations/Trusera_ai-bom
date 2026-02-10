"""Tests for GitHub Actions scanner."""


import pytest

from ai_bom.models import ComponentType
from ai_bom.scanners.github_actions_scanner import GitHubActionsScanner


@pytest.fixture
def scanner():
    """Create a GitHubActionsScanner instance."""
    return GitHubActionsScanner()


def test_scanner_registration():
    """Test that scanner is properly registered."""
    scanner = GitHubActionsScanner()
    assert scanner.name == "github-actions"
    assert scanner.description == "Scan GitHub Actions workflows for AI components"


def test_supports_workflow_file(tmp_path, scanner):
    """Test that scanner supports .github/workflows/*.yml files."""
    workflows_dir = tmp_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)
    workflow_file = workflows_dir / "test.yml"
    workflow_file.write_text("name: Test")

    assert scanner.supports(workflow_file)


def test_supports_workflow_directory(tmp_path, scanner):
    """Test that scanner supports directories with .github/workflows/."""
    workflows_dir = tmp_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)

    assert scanner.supports(tmp_path)


def test_not_supports_non_workflow_file(tmp_path, scanner):
    """Test that scanner does not support non-workflow files."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test")

    assert not scanner.supports(test_file)


def test_scan_openai_action(tmp_path, scanner):
    """Test detection of OpenAI-related GitHub Action."""
    workflows_dir = tmp_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)
    workflow_file = workflows_dir / "ai-review.yml"

    workflow_content = """
name: AI Code Review
on: [pull_request]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: openai/code-review@v1
        with:
          api-key: ${{ secrets.OPENAI_API_KEY }}
"""
    workflow_file.write_text(workflow_content)

    components = scanner.scan(tmp_path)

    assert len(components) >= 1
    openai_components = [c for c in components if "openai" in c.name.lower()]
    assert len(openai_components) >= 1

    comp = openai_components[0]
    assert comp.type == ComponentType.workflow
    assert comp.provider == "GitHub Actions"
    assert comp.source == "github-actions"
    assert "openai" in comp.metadata["action_reference"].lower()


def test_scan_anthropic_action(tmp_path, scanner):
    """Test detection of Anthropic-related GitHub Action."""
    workflows_dir = tmp_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)
    workflow_file = workflows_dir / "claude-review.yml"

    workflow_content = """
name: Claude Review
on: [pull_request]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: anthropic/claude-review@v2
"""
    workflow_file.write_text(workflow_content)

    components = scanner.scan(tmp_path)

    assert len(components) >= 1
    anthropic_components = [c for c in components if "anthropic" in c.name.lower()]
    assert len(anthropic_components) >= 1

    comp = anthropic_components[0]
    assert comp.type == ComponentType.workflow
    assert "anthropic" in comp.metadata["action_reference"].lower()


def test_scan_copilot_action(tmp_path, scanner):
    """Test detection of GitHub Copilot action."""
    workflows_dir = tmp_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)
    workflow_file = workflows_dir / "copilot.yml"

    workflow_content = """
name: Copilot Analysis
jobs:
  analyze:
    steps:
      - uses: github/copilot-analysis@v1
"""
    workflow_file.write_text(workflow_content)

    components = scanner.scan(tmp_path)

    assert len(components) >= 1
    copilot_components = [c for c in components if "copilot" in c.name.lower()]
    assert len(copilot_components) >= 1


def test_scan_hardcoded_api_key(tmp_path, scanner):
    """Test detection of hardcoded API key (security risk)."""
    workflows_dir = tmp_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)
    workflow_file = workflows_dir / "bad-practice.yml"

    workflow_content = """
name: Bad Practice
jobs:
  test:
    env:
      OPENAI_API_KEY: sk-proj-1234567890abcdef
    steps:
      - run: echo "test"
"""
    workflow_file.write_text(workflow_content)

    components = scanner.scan(tmp_path)

    assert len(components) >= 1
    api_key_components = [c for c in components if "API Key" in c.name]
    assert len(api_key_components) >= 1

    comp = api_key_components[0]
    assert comp.type == ComponentType.llm_provider
    assert comp.provider == "OpenAI"
    assert "hardcoded_api_key" in comp.flags
    assert comp.metadata["hardcoded"] is True


def test_scan_secret_api_key(tmp_path, scanner):
    """Test detection of API key from secrets (not hardcoded)."""
    workflows_dir = tmp_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)
    workflow_file = workflows_dir / "good-practice.yml"

    workflow_content = """
name: Good Practice
jobs:
  test:
    env:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
    steps:
      - run: echo "test"
"""
    workflow_file.write_text(workflow_content)

    components = scanner.scan(tmp_path)

    assert len(components) >= 1
    api_key_components = [c for c in components if "API Key" in c.name]
    assert len(api_key_components) >= 1

    comp = api_key_components[0]
    assert comp.provider == "Anthropic"
    assert "hardcoded_api_key" not in comp.flags
    assert comp.metadata.get("hardcoded", False) is False


def test_scan_multiple_ai_services(tmp_path, scanner):
    """Test detection of multiple AI services in one workflow."""
    workflows_dir = tmp_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)
    workflow_file = workflows_dir / "multi-ai.yml"

    workflow_content = """
name: Multi AI
env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  HUGGINGFACE_TOKEN: ${{ secrets.HF_TOKEN }}
jobs:
  test:
    steps:
      - uses: openai/gpt-review@v1
      - uses: actions/checkout@v3
"""
    workflow_file.write_text(workflow_content)

    components = scanner.scan(tmp_path)

    assert len(components) >= 3
    providers = {c.provider for c in components}
    assert "OpenAI" in providers
    assert "HuggingFace" in providers


def test_scan_global_env_vars(tmp_path, scanner):
    """Test detection of global-level environment variables."""
    workflows_dir = tmp_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)
    workflow_file = workflows_dir / "global-env.yml"

    workflow_content = """
name: Global Env
env:
  GOOGLE_AI_KEY: ${{ secrets.GOOGLE_AI_KEY }}
jobs:
  test:
    steps:
      - run: echo "test"
"""
    workflow_file.write_text(workflow_content)

    components = scanner.scan(tmp_path)

    assert len(components) >= 1
    google_components = [c for c in components if c.provider == "Google"]
    assert len(google_components) >= 1

    comp = google_components[0]
    assert comp.metadata["scope"] == "global"


def test_scan_yaml_extension(tmp_path, scanner):
    """Test scanning .yaml extension (not just .yml)."""
    workflows_dir = tmp_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)
    workflow_file = workflows_dir / "test.yaml"

    workflow_content = """
name: YAML Test
jobs:
  test:
    steps:
      - uses: copilot-test@v1
"""
    workflow_file.write_text(workflow_content)

    assert scanner.supports(workflow_file)
    components = scanner.scan(workflow_file)
    assert len(components) >= 1


def test_scan_action_version_parsing(tmp_path, scanner):
    """Test parsing of action version."""
    workflows_dir = tmp_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)
    workflow_file = workflows_dir / "version.yml"

    workflow_content = """
name: Version Test
jobs:
  test:
    steps:
      - uses: openai/gpt-action@v2.1.0
"""
    workflow_file.write_text(workflow_content)

    components = scanner.scan(tmp_path)

    assert len(components) >= 1
    comp = components[0]
    assert comp.version == "v2.1.0"


def test_scan_empty_workflow(tmp_path, scanner):
    """Test scanning empty or invalid workflow file."""
    workflows_dir = tmp_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)
    workflow_file = workflows_dir / "empty.yml"
    workflow_file.write_text("")

    components = scanner.scan(tmp_path)
    assert len(components) == 0


def test_scan_invalid_yaml(tmp_path, scanner):
    """Test scanning invalid YAML file."""
    workflows_dir = tmp_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)
    workflow_file = workflows_dir / "invalid.yml"
    workflow_file.write_text("{ invalid yaml content [")

    components = scanner.scan(tmp_path)
    # Should not crash, just return empty
    assert len(components) == 0


def test_provider_extraction_from_env(scanner):
    """Test provider extraction from environment variable names."""
    assert scanner._extract_provider_from_env("OPENAI_API_KEY") == "OpenAI"
    assert scanner._extract_provider_from_env("ANTHROPIC_KEY") == "Anthropic"
    assert scanner._extract_provider_from_env("HF_TOKEN") == "HuggingFace"
    assert scanner._extract_provider_from_env("COHERE_API_KEY") == "Cohere"
    assert scanner._extract_provider_from_env("GROQ_API_KEY") == "Groq"
    assert scanner._extract_provider_from_env("UNKNOWN_KEY") == "Unknown"


def test_action_reference_parsing(scanner):
    """Test action reference parsing."""
    name, version = scanner._parse_action_ref("actions/checkout@v3")
    assert name == "actions/checkout"
    assert version == "v3"

    name, version = scanner._parse_action_ref("openai/gpt-review")
    assert name == "openai/gpt-review"
    assert version == "latest"

    name, version = scanner._parse_action_ref("user/action@main")
    assert name == "user/action"
    assert version == "main"
