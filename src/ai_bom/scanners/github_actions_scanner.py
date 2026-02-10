"""GitHub Actions scanner for AI-BOM: Detects AI components in GitHub Actions workflows."""

from __future__ import annotations

from pathlib import Path

import yaml

from ai_bom.models import AIComponent, ComponentType, SourceLocation, UsageType
from ai_bom.scanners.base import BaseScanner


class GitHubActionsScanner(BaseScanner):
    """Scanner for GitHub Actions workflows to detect AI components.

    Detects AI usage in:
    - GitHub Actions workflows (.github/workflows/*.yml, *.yaml)
    - AI-related actions (uses: references)
    - AI API key environment variables

    Identifies AI actions like copilot, ai-review, ai-test, and API integrations.
    """

    name = "github-actions"
    description = "Scan GitHub Actions workflows for AI components"

    # Known AI-related GitHub Actions
    AI_ACTIONS = [
        "github/copilot",
        "copilot",
        "openai",
        "anthropic",
        "ai-review",
        "ai-test",
        "ai-pr-reviewer",
        "code-review-gpt",
        "gpt-review",
        "claude-review",
        "llm-review",
        "semantic-release",
        "ai-commit",
        "ai-changelog",
        "huggingface",
        "langchain",
        "autogpt",
    ]

    # AI API key environment variable patterns
    AI_ENV_VARS = [
        "OPENAI_API_KEY",
        "OPENAI_KEY",
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_KEY",
        "CLAUDE_API_KEY",
        "HUGGINGFACE_TOKEN",
        "HF_TOKEN",
        "COHERE_API_KEY",
        "MISTRAL_API_KEY",
        "GOOGLE_AI_KEY",
        "GOOGLE_API_KEY",
        "VERTEX_AI_KEY",
        "REPLICATE_API_TOKEN",
        "TOGETHER_API_KEY",
        "GROQ_API_KEY",
        "DEEPSEEK_API_KEY",
        "XAI_API_KEY",
    ]

    def supports(self, path: Path) -> bool:
        """Check if this scanner should run on the given path.

        Args:
            path: Directory or file path to check

        Returns:
            True if path is a GitHub Actions workflow or contains workflows
        """
        if path.is_file():
            # Check if file is in .github/workflows/ directory
            parts = path.parts
            if ".github" in parts and "workflows" in parts:
                filename = path.name.lower()
                return filename.endswith(".yml") or filename.endswith(".yaml")
            return False

        # For directories, check if .github/workflows/ exists
        if path.is_dir():
            workflows_dir = path / ".github" / "workflows"
            return workflows_dir.exists() and workflows_dir.is_dir()

        return False

    def scan(self, path: Path) -> list[AIComponent]:
        """Scan GitHub Actions workflows for AI components.

        Args:
            path: Directory or file path to scan

        Returns:
            List of detected AI components with metadata
        """
        components: list[AIComponent] = []

        if path.is_file():
            # Scan single workflow file
            if self.supports(path):
                components.extend(self._scan_workflow(path))
        else:
            # Scan directory for workflow files
            workflows_dir = path / ".github" / "workflows"
            if workflows_dir.exists():
                for workflow_file in workflows_dir.glob("*.y*ml"):
                    if workflow_file.is_file():
                        components.extend(self._scan_workflow(workflow_file))

        return components

    def _scan_workflow(self, file_path: Path) -> list[AIComponent]:
        """Parse a GitHub Actions workflow file and extract AI components.

        Args:
            file_path: Path to the workflow file

        Returns:
            List of AI components found in the workflow
        """
        components: list[AIComponent] = []

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            data = yaml.safe_load(content)

            if not isinstance(data, dict):
                return components

            workflow_name = data.get("name", file_path.stem)

            # Scan jobs for AI actions
            jobs = data.get("jobs", {})
            if not isinstance(jobs, dict):
                return components

            for job_name, job_config in jobs.items():
                if not isinstance(job_config, dict):
                    continue

                steps = job_config.get("steps", [])
                if not isinstance(steps, list):
                    continue

                # Check each step
                for step_idx, step in enumerate(steps, start=1):
                    if not isinstance(step, dict):
                        continue

                    # Check for 'uses:' field referencing AI actions
                    uses = step.get("uses", "")
                    if isinstance(uses, str) and uses:
                        # Extract action name/reference
                        action_ref = uses.strip()

                        # Check if it matches any AI action pattern
                        for ai_action in self.AI_ACTIONS:
                            if ai_action.lower() in action_ref.lower():
                                # Parse action owner/name and version
                                action_name, version = self._parse_action_ref(action_ref)

                                component = AIComponent(
                                    name=f"{action_name} (GitHub Action)",
                                    type=ComponentType.workflow,
                                    version=version,
                                    provider="GitHub Actions",
                                    location=SourceLocation(
                                        file_path=str(file_path.resolve()),
                                        line_number=None,
                                        context_snippet=(
                                            f"Workflow: {workflow_name},"
                                            f" Job: {job_name},"
                                            f" Step {step_idx}"
                                        ),
                                    ),
                                    usage_type=UsageType.orchestration,
                                    source="github-actions",
                                    metadata={
                                        "workflow_name": workflow_name,
                                        "job_name": job_name,
                                        "step_number": step_idx,
                                        "action_reference": action_ref,
                                        "step_name": step.get("name", ""),
                                    },
                                )
                                components.append(component)
                                break

                # Check for AI environment variables in job
                components.extend(
                    self._check_env_vars(
                        job_config, file_path, workflow_name, job_name
                    )
                )

            # Check for global environment variables
            components.extend(
                self._check_env_vars(data, file_path, workflow_name, "global")
            )

        except yaml.YAMLError:
            # YAML parse error, skip this file
            pass
        except (OSError, UnicodeDecodeError):
            # File read error, skip
            pass

        return components

    def _parse_action_ref(self, action_ref: str) -> tuple[str, str]:
        """Parse GitHub Action reference into name and version.

        Args:
            action_ref: GitHub Action reference (e.g., "actions/checkout@v3")

        Returns:
            Tuple of (action_name, version)
        """
        # Remove comments
        if "#" in action_ref:
            action_ref = action_ref.split("#")[0].strip()

        # Split by @ to separate name and version/ref
        if "@" in action_ref:
            parts = action_ref.split("@", 1)
            action_name = parts[0].strip()
            version = parts[1].strip()
        else:
            action_name = action_ref.strip()
            version = "latest"

        return action_name, version

    def _check_env_vars(
        self,
        config: dict,
        file_path: Path,
        workflow_name: str,
        scope: str,
    ) -> list[AIComponent]:
        """Check for AI-related environment variables in workflow config.

        Args:
            config: Workflow or job configuration dictionary
            file_path: Path to workflow file
            workflow_name: Name of the workflow
            scope: Scope of env vars (job name or "global")

        Returns:
            List of AI components representing detected API keys
        """
        components: list[AIComponent] = []

        env = config.get("env", {})
        if not isinstance(env, dict):
            return components

        # Check each environment variable
        for env_var_name, env_var_value in env.items():
            env_var_name_upper = str(env_var_name).upper()

            # Check if it matches any AI API key pattern
            for ai_env_pattern in self.AI_ENV_VARS:
                if ai_env_pattern in env_var_name_upper:
                    # Determine provider from env var name
                    provider = self._extract_provider_from_env(env_var_name_upper)

                    # Check if value is hardcoded (security risk)
                    is_hardcoded = not (
                        isinstance(env_var_value, str)
                        and (
                            env_var_value.startswith("${{")
                            or "secrets." in str(env_var_value).lower()
                        )
                    )

                    metadata: dict = {
                        "workflow_name": workflow_name,
                        "scope": scope,
                        "env_var_name": env_var_name,
                    }

                    if is_hardcoded:
                        metadata["hardcoded"] = True

                    component = AIComponent(
                        name=f"{provider} API Key",
                        type=ComponentType.llm_provider,
                        version="",
                        provider=provider,
                        location=SourceLocation(
                            file_path=str(file_path.resolve()),
                            line_number=None,
                            context_snippet=f"Workflow: {workflow_name}, Scope: {scope}",
                        ),
                        usage_type=UsageType.unknown,
                        source="github-actions",
                        metadata=metadata,
                    )

                    # Add security flag if hardcoded
                    if is_hardcoded:
                        component.flags.append("hardcoded_api_key")

                    components.append(component)
                    break

        return components

    def _extract_provider_from_env(self, env_var_name: str) -> str:
        """Extract provider name from environment variable name.

        Args:
            env_var_name: Environment variable name (uppercase)

        Returns:
            Provider name
        """
        if "OPENAI" in env_var_name:
            return "OpenAI"
        if "ANTHROPIC" in env_var_name or "CLAUDE" in env_var_name:
            return "Anthropic"
        if "HUGGING" in env_var_name or "HF_" in env_var_name:
            return "HuggingFace"
        if "COHERE" in env_var_name:
            return "Cohere"
        if "MISTRAL" in env_var_name:
            return "Mistral"
        if "GOOGLE" in env_var_name or "VERTEX" in env_var_name:
            return "Google"
        if "REPLICATE" in env_var_name:
            return "Replicate"
        if "TOGETHER" in env_var_name:
            return "Together"
        if "GROQ" in env_var_name:
            return "Groq"
        if "DEEPSEEK" in env_var_name:
            return "DeepSeek"
        if "XAI" in env_var_name:
            return "xAI"

        return "Unknown"
