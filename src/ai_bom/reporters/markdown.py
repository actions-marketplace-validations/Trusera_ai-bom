"""GitHub-Flavored Markdown reporter."""
from __future__ import annotations

from ai_bom.models import ScanResult
from ai_bom.reporters.base import BaseReporter


class MarkdownReporter(BaseReporter):
    """Reporter that generates GitHub-Flavored Markdown."""

    def render(self, result: ScanResult) -> str:
        """Render scan result as GFM-compatible markdown.

        Args:
            result: The scan result to render

        Returns:
            Markdown formatted string
        """
        lines = []
        lines.append("# AI Bill of Materials Report")
        lines.append("")
        lines.append(f"**Target:** `{result.target_path}`")
        lines.append(f"**Scan Date:** {result.scan_timestamp}")
        lines.append(f"**AI-BOM Version:** {result.ai_bom_version}")
        lines.append("")

        # Summary table
        lines.append("## Summary")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Total Components | {result.summary.total_components} |")
        lines.append(f"| Files Scanned | {result.summary.total_files_scanned} |")
        lines.append(
            f"| Highest Risk | {result.summary.highest_risk_score}/100 |"
        )
        lines.append("")

        # Component type breakdown
        if result.summary.by_type:
            lines.append("### Components by Type")
            lines.append("")
            lines.append("| Type | Count |")
            lines.append("|------|-------|")
            for type_name, count in sorted(result.summary.by_type.items()):
                lines.append(f"| {type_name} | {count} |")
            lines.append("")

        # Risk distribution with ASCII bars
        lines.append("### Risk Distribution")
        lines.append("")
        severity_emojis = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
        }
        for sev in ["critical", "high", "medium", "low"]:
            count = result.summary.by_severity.get(sev, 0)
            emoji = severity_emojis.get(sev, "⚪")
            bar_length = min(count, 20)  # Cap at 20 for readability
            bar = "█" * bar_length + "░" * max(0, 10 - bar_length)
            lines.append(f"- {emoji} **{sev.title()}**: {bar} ({count})")
        lines.append("")

        # n8n section (conditional)
        if result.n8n_workflows:
            lines.append("## n8n Workflows")
            lines.append("")
            lines.append(
                "| Workflow | Trigger | AI Nodes | Agent Chains |"
            )
            lines.append("|----------|---------|----------|--------------|")
            for wf in result.n8n_workflows:
                lines.append(
                    f"| {wf.workflow_name} | {wf.trigger_type} | "
                    f"{len(wf.nodes)} | {len(wf.agent_chains)} |"
                )
            lines.append("")
            lines.append("### Workflow Details")
            lines.append("")
            for wf in result.n8n_workflows:
                lines.append(f"#### {wf.workflow_name}")
                lines.append(f"- **Trigger:** {wf.trigger_type}")
                lines.append(f"- **AI Nodes:** {len(wf.nodes)}")
                if wf.nodes:
                    lines.append("  - " + ", ".join(wf.nodes))
                lines.append(f"- **Agent Chains:** {len(wf.agent_chains)}")
                lines.append("")

        # Findings table
        lines.append("## Components")
        lines.append("")
        if result.components:
            lines.append(
                "| # | Component | Type | Provider | Risk | Severity | Location | Flags |"
            )
            lines.append(
                "|---|-----------|------|----------|------|----------|----------|-------|"
            )
            for i, comp in enumerate(
                sorted(result.components, key=lambda c: c.risk.score, reverse=True),
                1,
            ):
                flags = ", ".join(comp.flags[:3]) if comp.flags else "-"
                # Add emoji for severity
                severity_emoji = severity_emojis.get(comp.risk.severity.value, "⚪")
                location = comp.location.file_path
                if comp.location.line_number:
                    location += f":{comp.location.line_number}"

                lines.append(
                    f"| {i} | {comp.name} | {comp.type.value} | {comp.provider} | "
                    f"{comp.risk.score} | {severity_emoji} {comp.risk.severity.value} | "
                    f"`{location}` | {flags} |"
                )
            lines.append("")
        else:
            lines.append("No AI components detected.")
            lines.append("")

        # Detailed findings by severity
        if result.components:
            lines.append("## Detailed Findings")
            lines.append("")
            for severity in ["critical", "high", "medium", "low"]:
                severity_components = [
                    c
                    for c in result.components
                    if c.risk.severity.value == severity
                ]
                if severity_components:
                    emoji = severity_emojis.get(severity, "⚪")
                    lines.append(f"### {emoji} {severity.title()} Risk Components")
                    lines.append("")
                    for comp in sorted(
                        severity_components,
                        key=lambda c: c.risk.score,
                        reverse=True,
                    ):
                        lines.append(f"#### {comp.name}")
                        lines.append(f"- **Type:** {comp.type.value}")
                        lines.append(f"- **Provider:** {comp.provider}")
                        lines.append(f"- **Risk Score:** {comp.risk.score}/100")
                        lines.append(
                            f"- **Location:** `{comp.location.file_path}`"
                        )
                        if comp.location.line_number:
                            lines.append(
                                f"  - Line: {comp.location.line_number}"
                            )
                        if comp.flags:
                            lines.append(f"- **Flags:** {', '.join(comp.flags)}")
                        if comp.version:
                            lines.append(f"- **Version:** {comp.version}")
                        if comp.metadata:
                            lines.append("- **Metadata:**")
                            for key, value in comp.metadata.items():
                                lines.append(f"  - {key}: {value}")
                        lines.append("")

        # Recommendations based on top risk factors
        lines.append("## Recommendations")
        lines.append("")
        all_flags = set()
        for comp in result.components:
            all_flags.update(comp.flags)

        recommendations = {
            "hardcoded_api_key": "🔑 Move API keys to environment variables or a secrets manager",
            "shadow_ai": "👻 Declare all AI dependencies in project dependency files",
            "deprecated_model": "⏰ Upgrade to current model versions",
            "webhook_no_auth": "🔓 Add authentication to n8n webhook triggers",
            "code_http_tools": "🛠️ Restrict agent tool access to necessary operations only",
            "mcp_unknown_server": "🌐 Verify and whitelist MCP server endpoints",
            "multi_agent_no_trust": "🤝 Implement trust boundaries between AI agents",
            "no_auth": "🔐 Add authentication to AI-facing endpoints",
            "unpinned_model": "📌 Pin model versions for reproducibility",
            "no_rate_limit": "⚡ Implement rate limiting to prevent abuse",
            "unencrypted_secrets": "🔒 Encrypt sensitive configuration data",
            "public_endpoint": "🌍 Restrict AI endpoints to authorized networks",
        }

        found_recs = False
        for flag, rec in recommendations.items():
            if flag in all_flags:
                lines.append(f"- {rec}")
                found_recs = True

        if not found_recs:
            lines.append("✅ No specific recommendations — good job!")

        lines.append("")

        # Security best practices
        lines.append("## Security Best Practices")
        lines.append("")
        lines.append("1. **API Key Management**")
        lines.append(
            "   - Store all API keys in environment variables or secrets managers"
        )
        lines.append("   - Rotate keys regularly")
        lines.append("   - Use separate keys for dev/staging/production")
        lines.append("")
        lines.append("2. **Model Versioning**")
        lines.append("   - Pin specific model versions in production")
        lines.append("   - Test model updates in staging before deploying")
        lines.append("   - Document model behavior changes")
        lines.append("")
        lines.append("3. **Agent Security**")
        lines.append("   - Implement authentication between agents")
        lines.append("   - Validate all agent inputs and outputs")
        lines.append("   - Monitor agent behavior for anomalies")
        lines.append("")
        lines.append("4. **Dependency Management**")
        lines.append("   - Keep AI libraries up to date")
        lines.append("   - Scan dependencies for vulnerabilities")
        lines.append("   - Document all AI components in your BOM")
        lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append(
            "*Generated by [AI-BOM](https://github.com/trusera/ai-bom) by "
            "[Trusera](https://trusera.dev)*"
        )
        lines.append("")
        lines.append(
            "**Secure agent-to-agent communication with Trusera** → "
            "[trusera.dev](https://trusera.dev)"
        )

        return "\n".join(lines)
